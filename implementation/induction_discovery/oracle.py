"""Per-head induction oracle: Olsson et al. (2022) prefix-matching + previous-token scores.

The H15 ground truth is a *computable* per-head score, not a memorized head list — no
acquired source names GPT-2-small's induction heads (Olsson names only GPT-2-XL 21.20 and
GPT-Neo 12.0; verified against download/olsson-induction-heads-2022.pdf). We reproduce
Olsson's "(3) Head activation evaluators" (p58 of the acquired PDF):

  Prefix matching: "Generate a sequence of 25 random tokens, excluding the most common and
  the least common tokens. Repeat this sequence 4 times and prepend a 'start of sequence'
  token. Compute the attention pattern. The prefix matching score is the average of all
  attention pattern entries attending from a given token back to the tokens that [are]
  preceded [by] the same token in earlier repeats."  (Olsson 2022, App. (3))

  i.e. for a query token at position p, the induction target is the position immediately
  FOLLOWING an earlier occurrence of the same token (the token "induction would suggest
  comes next", Olsson p5). The 2022-09-20 erratum (PDF p48) corrected the main-text
  "preceded/followed" wording; the follower direction is the validated one (it recovers the
  canonical GPT-2-small cluster 5.5/7.10/6.9/5.1/7.2).

  Previous token: "the average of ... attention pattern entries attending from token i to
  token i-1."  (Olsson uses a training-distribution example; we use the same repeated-random
  sequences — a disclosed proxy, valid because prev-token heads attend i->i-1 content-freely.)

Attentions require an eager-attention model (sdpa does not expose per-head weights), so this
module loads its own GPT-2 (attn_implementation="eager"), independent of the eap_ig hook
engine which needs no attentions.
"""
from __future__ import annotations

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast


def load_eager(name: str = "gpt2", device: str = "cpu", dtype: str = "float32"):
    """GPT-2 with eager attention so output_attentions returns real per-head weights."""
    dt = {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[dtype]
    tok = GPT2TokenizerFast.from_pretrained(name)
    model = GPT2LMHeadModel.from_pretrained(name, torch_dtype=dt,
                                            attn_implementation="eager").to(device).eval()
    return model, tok


def _repeated_random_batch(rng, n_examples, block_len, n_repeats, bos_id, id_lo, id_hi):
    """(B, T) = [BOS] + block*n_repeats, block = block_len distinct random ids in [lo,hi)."""
    seqs = []
    for _ in range(n_examples):
        block = rng.choice(np.arange(id_lo, id_hi), size=block_len, replace=False)
        seq = np.concatenate([[bos_id], np.tile(block, n_repeats)])
        seqs.append(seq)
    return torch.tensor(np.stack(seqs), dtype=torch.long)


def _prefix_mask(T: int, block_len: int, n_repeats: int) -> torch.Tensor:
    """Boolean (T,T): entry [p, t]=True iff t is the follower of an earlier copy of token p,
    i.e. t = p - k*block_len + 1 for some k>=1, with t>=1 (exclude the BOS at index 0)."""
    m = torch.zeros(T, T, dtype=torch.bool)
    for p in range(1, T):
        for k in range(1, n_repeats):
            t = p - k * block_len + 1
            if 1 <= t < T and t <= p:            # causal + not BOS
                m[p, t] = True
    return m


def _prev_token_mask(T: int) -> torch.Tensor:
    m = torch.zeros(T, T, dtype=torch.bool)
    idx = torch.arange(1, T)
    m[idx, idx - 1] = True
    return m


@torch.no_grad()
def per_head_scores(model, tok, *, n_examples=50, block_len=25, n_repeats=4,
                    seed=0, id_lo=1000, id_hi=40000, device="cpu"):
    """Return {'prefix': {head: score}, 'prev': {head: score}} over all attention heads.

    Vectorized: each attention tensor is (B, H, T, T); a fixed (T,T) mask selects the
    qualifying entries and we take the mean over batch + qualifying (p,t) pairs (Olsson's
    "average of all attention pattern entries")."""
    rng = np.random.default_rng(seed)
    bos = tok.eos_token_id
    ids = _repeated_random_batch(rng, n_examples, block_len, n_repeats, bos, id_lo, id_hi).to(device)
    T = ids.shape[1]
    out = model(ids, output_attentions=True)
    attns = out.attentions                       # tuple[n_layer] of (B, H, T, T)
    if attns is None or attns[0] is None:
        raise RuntimeError("model returned no attentions — load with attn_implementation='eager'")

    pref_mask = _prefix_mask(T, block_len, n_repeats).to(device)
    prev_mask = _prev_token_mask(T).to(device)
    n_pref = int(pref_mask.sum().item())
    n_prev = int(prev_mask.sum().item())

    prefix, prev = {}, {}
    n_layer = len(attns)
    n_head = attns[0].shape[1]
    for l in range(n_layer):
        a = attns[l].float()                     # (B, H, T, T)
        pref = (a * pref_mask).sum(dim=(2, 3)) / n_pref   # (B, H)
        pv = (a * prev_mask).sum(dim=(2, 3)) / n_prev     # (B, H)
        pref = pref.mean(0)                       # (H,)
        pv = pv.mean(0)
        for h in range(n_head):
            prefix[f"a{l}.h{h}"] = float(pref[h].item())
            prev[f"a{l}.h{h}"] = float(pv[h].item())
    return {"prefix": prefix, "prev": prev}


def induction_head_set(prefix_scores: dict, threshold: float) -> list[str]:
    """Oracle positive set: heads whose prefix-matching score exceeds `threshold`.
    (The headline recovery metrics — Spearman rho, AUROC — use the continuous score and are
    threshold-free; the set only defines recovery@k and the AUROC positive class.)"""
    return sorted((h for h, s in prefix_scores.items() if s >= threshold),
                  key=lambda h: prefix_scores[h], reverse=True)


def compute_oracle(cfg) -> dict:
    """Multi-seed oracle with per-seed scores (for CIs). cfg carries model + protocol knobs."""
    model, tok = load_eager(cfg.model_name, cfg.device, cfg.dtype)
    per_seed = []
    for s in cfg.oracle_seeds:
        per_seed.append(per_head_scores(
            model, tok, n_examples=cfg.oracle_n_examples, block_len=cfg.block_len,
            n_repeats=cfg.n_repeats, seed=s, id_lo=cfg.id_lo, id_hi=cfg.id_hi, device=cfg.device))
    # mean across seeds
    heads = list(per_seed[0]["prefix"].keys())
    prefix_mean = {h: float(np.mean([ps["prefix"][h] for ps in per_seed])) for h in heads}
    prev_mean = {h: float(np.mean([ps["prev"][h] for ps in per_seed])) for h in heads}
    del model
    return {"prefix": prefix_mean, "prev": prev_mean, "per_seed": per_seed,
            "induction_set": induction_head_set(prefix_mean, cfg.oracle_threshold)}
