"""Model builder (HookedTransformer) + first-party torch training loop + metrics.

The model architecture is TransformerLens's HookedTransformer (standard,
GPT-2-compatible, full hook/cache access = the uniform analysis path with the
pretrained-GPT-2 rung, per plan §8.1). The training loop below is first-party
(a plain torch AdamW loop) — TransformerLens supplies the forward + hooks, not
the optimization. The hand-derived fwd/bwd/AdamW *math* is verified separately by
the numpy Appendix-C toy (H5 reference); a finite-difference gradient check
(tests) confirms this model's forward/backward.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from transformer_lens import HookedTransformer, HookedTransformerConfig

from .config import ModelConfig, TrainConfig
from .data import IGNORE, make_induction_batch


def build_toy(mcfg: ModelConfig, device: str = "cpu") -> HookedTransformer:
    """Map our ModelConfig -> a HookedTransformer (learned abs pos, pre-norm LN)."""
    hcfg = HookedTransformerConfig(
        n_layers=mcfg.n_layers,
        n_heads=mcfg.n_heads,
        d_model=mcfg.d_model,
        d_head=mcfg.d_head,
        d_mlp=mcfg.d_mlp if mcfg.use_mlp else None,
        attn_only=not mcfg.use_mlp,
        act_fn=(mcfg.act_fn if mcfg.use_mlp else None),
        d_vocab=mcfg.d_vocab,
        n_ctx=mcfg.n_ctx,
        normalization_type="LN" if mcfg.pre_norm else "LNPre",
        positional_embedding_type="standard",
        seed=mcfg.seed,
        device=device,
        init_weights=True,
    )
    return HookedTransformer(hcfg)


def masked_ce(logits, targets):
    """Next-token cross-entropy, ignoring positions with target==IGNORE (Eq 11)."""
    B, T, V = logits.shape
    return F.cross_entropy(logits.reshape(B * T, V), targets.reshape(B * T),
                           ignore_index=IGNORE)


@torch.no_grad()
def loss_by_position(model, toks, targets):
    """Mean cross-entropy per token position -> (T,) curve (the in-context loss,
    H2/H8): it drops where the induction-solvable copied region begins."""
    t = torch.as_tensor(toks, device=model.cfg.device)
    y = torch.as_tensor(targets, device=model.cfg.device)
    logits = model(t)
    B, T, V = logits.shape
    ce = F.cross_entropy(logits.reshape(B * T, V), y.reshape(B * T),
                         ignore_index=IGNORE, reduction="none").reshape(B, T)
    valid = (y != IGNORE).float()
    return ((ce * valid).sum(0) / valid.sum(0).clamp(min=1)).cpu().numpy()


@torch.no_grad()
def induction_loss(model, toks, targets, ind_mask):
    """Mean cross-entropy at induction query positions (the ICL score, H8)."""
    t = torch.as_tensor(toks, device=model.cfg.device)
    y = torch.as_tensor(targets, device=model.cfg.device)
    logits = model(t)
    B, T, V = logits.shape
    ce = F.cross_entropy(logits.reshape(B * T, V), y.reshape(B * T),
                         ignore_index=IGNORE, reduction="none").reshape(B, T)
    m = torch.as_tensor(ind_mask, device=model.cfg.device) & (y != IGNORE)
    return float(ce[m].mean().item())


@torch.no_grad()
def induction_accuracy(model, toks, targets, ind_mask):
    """Argmax next-token accuracy at induction positions -> (correct, total)."""
    t = torch.as_tensor(toks, device=model.cfg.device)
    pred = model(t).argmax(-1).cpu().numpy()
    m = ind_mask & (targets != IGNORE)
    return int((pred[m] == targets[m]).sum()), int(m.sum())


@torch.no_grad()
def head_attention_scores(model, toks, ind_mask, attend_pos):
    """Per-head attention diagnostics averaged over induction query positions:
      - prev_token[l,h] = mean A[t, t-1]           (previous-token head)
      - induction[l,h]  = mean A[t, attend_pos[t]] (prefix-match + copy head)
    Uses the per-sequence attend positions (variable offset)."""
    t = torch.as_tensor(toks, device=model.cfg.device)
    _, cache = model.run_with_cache(t, return_type=None)
    L, H = model.cfg.n_layers, model.cfg.n_heads
    bb, tt = np.nonzero(ind_mask)
    ap = attend_pos[bb, tt]
    ok = ap >= 0
    bb, tt, ap = bb[ok], tt[ok], ap[ok]
    pk = tt - 1
    okp = pk >= 0
    prev = np.zeros((L, H)); ind = np.zeros((L, H))
    for l in range(L):
        patt = cache[f"blocks.{l}.attn.hook_pattern"].cpu().numpy()  # (B,H,T,T)
        for h in range(H):
            A = patt[:, h]
            ind[l, h] = float(A[bb, tt, ap].mean())
            prev[l, h] = float(A[bb[okp], tt[okp], pk[okp]].mean())
    return prev, ind


def train_toy(model, tcfg: TrainConfig, *, n_ctx=None, d_vocab=None,
              eval_batch=None, log=print):
    """First-party AdamW training on the induction task. Returns a history dict of
    per-eval metrics. Deterministic given seeds."""
    n_ctx = n_ctx or model.cfg.n_ctx
    d_vocab = d_vocab or model.cfg.d_vocab
    eval_batch = eval_batch or tcfg.eval_batch
    torch.manual_seed(tcfg.seed)
    rng = np.random.default_rng(tcfg.seed)
    eval_rng = np.random.default_rng(10_000 + tcfg.seed)

    opt = torch.optim.AdamW(model.parameters(), lr=tcfg.lr,
                            betas=(tcfg.beta1, tcfg.beta2),
                            weight_decay=tcfg.weight_decay)

    def lr_at(step):
        if tcfg.warmup_steps and step < tcfg.warmup_steps:
            return tcfg.lr * (step + 1) / tcfg.warmup_steps
        return tcfg.lr

    hist = {"step": [], "train_loss": [], "ind_acc": [], "ind_loss": [],
            "loss_by_pos": [], "induction_score": [], "prev_token_score": []}

    for step in range(tcfg.n_steps + 1):
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        toks, tgt, ind, _ = make_induction_batch(rng, tcfg.batch_size, n_ctx, d_vocab)
        t = torch.as_tensor(toks, device=model.cfg.device)
        y = torch.as_tensor(tgt, device=model.cfg.device)
        loss = masked_ce(model(t), y)
        opt.zero_grad()
        loss.backward()
        if tcfg.grad_clip:
            torch.nn.utils.clip_grad_norm_(model.parameters(), tcfg.grad_clip)
        opt.step()

        if step % tcfg.eval_every == 0 or step == tcfg.n_steps:
            et, ey, ei, eap = make_induction_batch(eval_rng, eval_batch, n_ctx, d_vocab)
            lbp = loss_by_position(model, et, ey)
            iloss = induction_loss(model, et, ey, ei)
            c, n = induction_accuracy(model, et, ey, ei)
            prev, indm = head_attention_scores(model, et, ei, eap)
            acc = c / max(1, n)
            hist["step"].append(step)
            hist["train_loss"].append(float(loss.item()))
            hist["ind_acc"].append(acc)
            hist["ind_loss"].append(iloss)
            hist["loss_by_pos"].append(lbp.tolist())
            hist["induction_score"].append(float(indm.max()))
            hist["prev_token_score"].append(float(prev.max()))
            log(f"step {step:6d} | loss {loss.item():.4f} | ind_acc {acc:.3f} "
                f"| ind_loss {iloss:.4f} | max induction {indm.max():.3f} "
                f"| max prev-token {prev.max():.3f}")
    return hist
