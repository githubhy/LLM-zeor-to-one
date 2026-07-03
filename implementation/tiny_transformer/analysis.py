"""Phase-4 mechanistic-interpretability analysis on trained toy models.

All analyses operate on saved HookedTransformer weights via forward passes + hooks
(no training). Covers the toy-rung observables: circuit-match (H3), role census
(H4b), set-based patching + necessity (H10), decode-lens + DLA (H11), Q/K/V
composition (H12), probing + selectivity (H13), self-repair (H14), privileged
basis (H17), and the rank-cliff theory overlay (§A.8).

Note (toy scale): at h=4 / L=2 induction is DISTRIBUTED — all top-layer heads
become induction heads and all L0 heads feed K-composition — so the "circuit" is a
head SET, single-head ablation is only a lower bound (self-repair, H14), and subset
faithfulness/completeness/minimality are demonstrated at the GPT-2 rung (Phase 4b)
where the circuit is a genuine subset.
"""
from __future__ import annotations

import os

import numpy as np
import torch

from . import circuits as C
from .config import model_config
from .data import make_corrupt_batch, make_induction_batch
from .model import build_toy, head_attention_scores

ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "artifacts", "induction-tiny")


def load_model(n_layers, seed, n_ctx=64, d_vocab=64, phase="phase3"):
    mcfg = model_config("induction", n_layers=n_layers, n_ctx=n_ctx, seed=seed)
    m = build_toy(mcfg)
    m.load_state_dict(torch.load(os.path.join(ART, phase, f"model_{n_layers}L_{seed}.pt"),
                                 map_location="cpu"))
    m.eval()
    return m


def eval_batch(n_ctx=64, d_vocab=64, batch=256, seed=12345):
    return make_induction_batch(np.random.default_rng(seed), batch, n_ctx, d_vocab)


# ---------- role census (H4b) ----------

def _diag_score(patt, offset):
    B, T, _ = patt.shape
    vals = [patt[:, t, t - offset].mean() for t in range(offset, T)]
    return float(np.mean(vals)) if vals else 0.0


@torch.no_grad()
def role_census(model, batch):
    toks, tgt, ind, ap = batch
    prev, indm = head_attention_scores(model, toks, ind, ap)
    _, cache = model.run_with_cache(torch.as_tensor(toks), return_type=None)
    L, H = model.cfg.n_layers, model.cfg.n_heads
    out = {}
    for l in range(L):
        patt = cache[f"blocks.{l}.attn.hook_pattern"].cpu().numpy()
        for h in range(H):
            A = patt[:, h]
            s = dict(prev_token=float(prev[l, h]), induction=float(indm[l, h]),
                     bos=float(A[:, :, 0].mean()), diag=_diag_score(A, 1),
                     entropy=float((-(A * np.log(A + 1e-12)).sum(-1)).mean()))
            if s["induction"] > 0.30:
                role = "induction"
            elif s["prev_token"] > 0.25:
                role = "previous-token"
            elif s["diag"] > 0.30:
                role = "positional"
            elif s["bos"] > 0.50:
                role = "bos-sink"
            else:
                role = "diffuse"
            out[(l, h)] = dict(role=role, **s)
    return out


def identify_head_sets(model, census, ind_thresh=0.30):
    """Distributed circuit as SETS: induction set = top-layer heads above threshold;
    feeder set = all L0 heads (they collectively supply K-composition)."""
    top = model.cfg.n_layers - 1
    ind_set = [k for k in census if k[0] == top and census[k]["induction"] > ind_thresh]
    if not ind_set:
        ind_set = [max(census, key=lambda k: census[k]["induction"])]
    top_ind = max(ind_set, key=lambda k: census[k]["induction"])
    feeder_set = [k for k in census if k[0] == 0]
    top_prev = max(feeder_set, key=lambda k: census[k]["prev_token"])
    return dict(ind_set=ind_set, top_ind=top_ind, feeder_set=feeder_set,
                top_prev=top_prev)


# ---------- circuit-match (H3) ----------

@torch.no_grad()
def circuit_match(model, sets):
    top_ind, ind_set, top_prev = sets["top_ind"], sets["ind_set"], sets["top_prev"]
    W_E, W_U = model.W_E.numpy(), model.W_U.numpy()
    li, hi = top_ind
    WV, WO = model.W_V[li, hi].numpy(), model.W_O[li, hi].numpy()
    WQ, WK = model.W_Q[li, hi].numpy(), model.W_K[li, hi].numpy()
    W_OV_top, eig = C.ov_circuit(WV, WO)
    fp, mass = C.copying_score(eig)
    diag_top = C.copying_score_diag(W_E, W_OV_top, W_U)
    # aggregate copy over the induction set (sum of their OV maps = layer's copy)
    W_OV_set = sum(model.W_V[l, h].numpy() @ model.W_O[l, h].numpy()
                   for (l, h) in ind_set)
    diag_set = C.copying_score_diag(W_E, W_OV_set, W_U)
    _, s = C.qk_circuit(WQ, WK)
    return dict(top_induction_head=list(top_ind), n_induction_heads=len(ind_set),
                top_prev_head=list(top_prev),
                ov_copying_frac_positive=fp, ov_copying_mass=mass,
                copy_diag_top_head=diag_top, copy_diag_induction_set=diag_set,
                qk_effective_rank=C.effective_rank(s), d_head=model.cfg.d_head,
                rank_cliff_holds=bool(C.effective_rank(s) <= model.cfg.d_head))


# ---------- composition (H12) ----------

@torch.no_grad()
def composition_scores(model, sets):
    """Mean K/Q/V composition from the feeder set (L0) into the induction set (L1);
    expect K-composition dominant (§A.18)."""
    agg = {"K": [], "Q": [], "V": []}
    for (lp, hp) in sets["feeder_set"]:
        W_ov_prev = model.W_V[lp, hp].numpy() @ model.W_O[lp, hp].numpy()
        for (li, hi) in sets["ind_set"]:
            for name, W in [("K", model.W_K[li, hi].numpy()),
                            ("Q", model.W_Q[li, hi].numpy()),
                            ("V", model.W_V[li, hi].numpy())]:
                agg[name].append(C.composition_score(W_ov_prev, W))
    out = {k: float(np.mean(v)) for k, v in agg.items()}
    out["dominant"] = max(("K", "Q", "V"), key=lambda k: out[k])
    return out


# ---------- patching + necessity (H10) ----------

def _ind_acc(logits, toks, ind, ap):
    pred = logits.detach().argmax(-1).numpy()
    bb, tt = np.nonzero(ind)
    tgt = np.array([toks[b, ap[b, t]] for b, t in zip(bb, tt)])
    return float(np.mean(pred[bb, tt] == tgt))


def _ind_metric(logits, toks, ind, ap):
    lg = logits.detach()[np.nonzero(ind)[0], np.nonzero(ind)[1]].numpy()
    bb, tt = np.nonzero(ind)
    tgt = np.array([toks[b, ap[b, t]] for b, t in zip(bb, tt)])
    correct = lg[np.arange(len(bb)), tgt]
    lg2 = lg.copy(); lg2[np.arange(len(bb)), tgt] = -np.inf
    return float(np.mean(correct - lg2.max(1)))


def _z_hooks(heads, mode, cache_clean=None):
    hooks = []
    for (l, h) in heads:
        name = f"blocks.{l}.attn.hook_z"

        def make(h, name):
            def hook(z, hook):
                if mode == "zero":
                    z[:, :, h, :] = 0.0
                elif mode == "mean":
                    z[:, :, h, :] = z[:, :, h, :].mean(dim=(0, 1), keepdim=True)
                elif mode == "patch":
                    z[:, :, h, :] = cache_clean[name][:, :, h, :]
                return z
            return hook
        hooks.append((name, make(h, name)))
    return hooks


@torch.no_grad()
def patching(model, batch, sets, census):
    toks, tgt, ind, ap = batch
    t = torch.as_tensor(toks)
    ind_set, feeder_set, top_ind = sets["ind_set"], sets["feeder_set"], sets["top_ind"]
    all_heads = [(l, h) for l in range(model.cfg.n_layers)
                 for h in range(model.cfg.n_heads)]
    chance = 1.0 / model.cfg.d_vocab
    base = model(t)
    base_acc = _ind_acc(base, toks, ind, ap)

    def abl(heads):
        return _ind_acc(model.run_with_hooks(t, fwd_hooks=_z_hooks(heads, "mean")),
                        toks, ind, ap)

    # least-important head (lowest max diagnostic score) = proper specificity control
    def importance(k):
        c = census[k]
        return max(c["induction"], c["prev_token"], c["diag"])
    ctrl = min(all_heads, key=importance)

    # clean/corrupt IE/TE on the induction set (logit-diff metric)
    rng = np.random.default_rng(777)
    corrupt, q = make_corrupt_batch(rng, toks, ind, model.cfg.d_vocab)
    qmask = np.zeros_like(ind); qmask[np.arange(len(q)), q] = True; qmask &= ind
    tc = torch.as_tensor(corrupt)
    _, cache_clean = model.run_with_cache(t, return_type=None)
    clean_md = _ind_metric(base, toks, qmask, ap)
    corrupt_md = _ind_metric(model(tc), corrupt, qmask, ap)
    patched = model.run_with_hooks(tc, fwd_hooks=_z_hooks(ind_set, "patch", cache_clean))
    ie = _ind_metric(patched, corrupt, qmask, ap) - corrupt_md
    te = clean_md - corrupt_md

    return dict(
        base_ind_acc=base_acc, chance=chance,
        acc_ablate_induction_set=abl(ind_set),
        acc_ablate_feeder_set=abl(feeder_set),
        acc_ablate_single_top=abl([top_ind]),
        acc_ablate_control=abl([ctrl]), control_head=list(ctrl),
        necessity_induction_set_drop=base_acc - abl(ind_set),
        necessity_feeder_set_drop=base_acc - abl(feeder_set),
        single_head_drop=base_acc - abl([top_ind]),
        control_drop=base_acc - abl([ctrl]),
        total_effect=te, indirect_effect_set=ie,
        ie_over_te=float(ie / te) if abs(te) > 1e-9 else None,
        note="distributed circuit: single-head ablation is a lower bound (H14); "
             "subset faithfulness/completeness/minimality at the GPT-2 rung (Phase 4b)",
    )


# ---------- self-repair / Hydra (H14) ----------

@torch.no_grad()
def self_repair(model, batch, sets):
    toks, tgt, ind, ap = batch
    t = torch.as_tensor(toks)
    ind_set = sets["ind_set"]
    base = _ind_acc(model(t), toks, ind, ap)

    def drop(heads):
        return base - _ind_acc(
            model.run_with_hooks(t, fwd_hooks=_z_hooks(heads, "mean")), toks, ind, ap)
    singles = {f"{l}L{h}": drop([(l, h)]) for (l, h) in ind_set}
    joint = drop(ind_set)
    sum_singles = sum(singles.values())
    return dict(single_drops=singles, sum_of_single_drops=sum_singles,
                joint_drop=joint, redundancy=float(sum_singles - joint),
                note="joint << sum(singles) => heavy redundancy / self-repair")


# ---------- decode-lens (H11) ----------

@torch.no_grad()
def logit_lens(model, batch):
    toks, tgt, ind, ap = batch
    _, cache = model.run_with_cache(torch.as_tensor(toks), return_type=None)
    bb, tt = np.nonzero(ind)
    tgt_ids = np.array([toks[b, ap[b, s]] for b, s in zip(bb, tt)])
    stages = [("resid_pre_0", cache["blocks.0.hook_resid_pre"])]
    for l in range(model.cfg.n_layers):
        stages.append((f"resid_post_{l}", cache[f"blocks.{l}.hook_resid_post"]))
    res = {}
    for name, resid in stages:
        lens = model.unembed(model.ln_final(resid)).detach().numpy()[bb, tt]
        order = np.argsort(-lens, axis=1)
        rank = np.array([int(np.where(order[i] == tgt_ids[i])[0][0])
                         for i in range(len(bb))])
        res[name] = dict(mean_correct_rank=float(rank.mean()),
                         top1_acc=float((rank == 0).mean()))
    return res


# ---------- probing + selectivity (H13) ----------

def probing(model, batch):
    from sklearn.linear_model import LogisticRegression
    toks, tgt, ind, ap = batch
    _, cache = model.run_with_cache(torch.as_tensor(toks), return_type=None)
    B, T = toks.shape
    y = ind.reshape(-1).astype(int)
    rng = np.random.default_rng(0)
    yshuf = rng.permutation(y)
    out = {}
    for l in range(model.cfg.n_layers):
        X = cache[f"blocks.{l}.hook_resid_post"].cpu().numpy().reshape(B * T, -1)
        idx = rng.permutation(len(X)); tr, te = idx[:len(X) // 2], idx[len(X) // 2:]
        a = LogisticRegression(max_iter=500).fit(X[tr], y[tr]).score(X[te], y[te])
        c = LogisticRegression(max_iter=500).fit(X[tr], yshuf[tr]).score(X[te], yshuf[te])
        out[f"resid_post_{l}"] = dict(probe_acc=float(a), control_acc=float(c),
                                      selectivity=float(a - c))
    return out


@torch.no_grad()
def privileged_basis(model, batch):
    return dict(note="attention-only: residual-basis invariance holds by construction; "
                     "the post-GELU privileged-basis contrast (H17) runs on the +MLP variant",
                has_mlp=model.cfg.d_mlp is not None)
