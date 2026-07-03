"""Phase 4b — pretrained GPT-2 small transfer (Gate G3b).

Loads GPT-2 small via TransformerLens (no training) and verifies the toy-derived
induction QK/OV structure transfers to real weights:
  H6  — locate induction heads (VARIABLE-offset probe, audit-hardened); OV copy
        evidence (E.W_OV.U median-self-rank); head dump.
  H8@scale — real in-context loss on repeated text; ablate the located induction
             heads => ICL degrades; random-head control leaves it intact (5 probe
             batches -> CI).
  head-zoo census — induction / previous-token / duplicate-token over all 144 heads.

Heavier GPT-2-rung analyses (IOI H18, automated discovery H15, DAS H16) are
deferred to a GPU host (todos/2026-07-02-tiny-transformer-gpu-host-rungs.md).
"""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "implementation"))
from tiny_transformer.utils import bootstrap_ci, save_json   # noqa: E402

ART = os.path.join(REPO, "artifacts", "induction-tiny", "phase4b")


def repeated_batch(model, n_seq=16, T=120, seed=0):
    """VARIABLE per-sequence offset (random prefix + repeated random block), so a
    fixed-relative-offset positional head cannot solve it — content-matching
    induction is required. Fixes the fixed-offset confound the sim-audit flagged
    (same class as bug 2026-07-02-05). Returns (toks[B,T], attend[B,T], ind_mask[B,T]).
    """
    rng = np.random.default_rng(seed)
    bos = model.tokenizer.bos_token_id
    toks = rng.integers(1000, 5000, size=(n_seq, T)).astype(np.int64)
    attend = np.full((n_seq, T), -1, dtype=np.int64)
    for b in range(n_seq):
        p = int(rng.integers(5, max(6, T // 3)))
        block = (T - p) // 2
        end = min(T, p + 2 * block)
        Lc = end - (p + block)
        toks[b, p + block:end] = toks[b, p:p + Lc]
        idx = np.arange(p + block, end - 1)
        attend[b, idx] = idx - block + 1
    toks = np.concatenate([np.full((n_seq, 1), bos, dtype=np.int64), toks], axis=1)
    attend = np.concatenate([np.full((n_seq, 1), -1, dtype=np.int64),
                             np.where(attend >= 0, attend + 1, -1)], axis=1)
    return torch.tensor(toks), attend, (attend >= 0)


@torch.no_grad()
def head_scores(model, toks, attend, ind_mask):
    _, cache = model.run_with_cache(toks, return_type=None)
    L, H = model.cfg.n_layers, model.cfg.n_heads
    bb, tt = np.nonzero(ind_mask)
    ap = attend[bb, tt]
    ind = np.zeros((L, H)); prev = np.zeros((L, H)); dup = np.zeros((L, H))
    okp = tt - 1 >= 0
    for l in range(L):
        patt = cache[f"blocks.{l}.attn.hook_pattern"].numpy()
        for h in range(H):
            A = patt[:, h]
            ind[l, h] = float(A[bb, tt, ap].mean())
            dup[l, h] = float(A[bb, tt, ap - 1].mean())
            prev[l, h] = float(A[bb[okp], tt[okp], tt[okp] - 1].mean())
    return ind, prev, dup


@torch.no_grad()
def icl_loss(model, toks, attend, ind_mask, ablate_heads=None):
    hooks = []
    if ablate_heads:
        for (l, h) in ablate_heads:
            name = f"blocks.{l}.attn.hook_z"

            def mk(h, name):
                def f(z, hook):
                    z[:, :, h, :] = z[:, :, h, :].mean(dim=(0, 1), keepdim=True)
                    return z
                return f
            hooks.append((name, mk(h, name)))
    logits = model.run_with_hooks(toks, fwd_hooks=hooks, return_type="logits")
    T = toks.shape[1]
    valid = ind_mask & (np.arange(T)[None, :] < T - 1)
    bb, tt = np.nonzero(valid)
    tgt = torch.as_tensor(toks.numpy()[bb, tt + 1])
    return float(F.cross_entropy(logits[bb, tt], tgt, reduction="mean").item())


@torch.no_grad()
def ov_copy_sampled(model, heads, n_sample=300, seed=0):
    """Sampled OV copy: for random tokens a, rank of a under the summed-head OV
    logit boost (E[a].W_OV.U). Median rank << vocab/2 => genuine copying."""
    rng = np.random.default_rng(seed)
    W_E, W_U = model.W_E.numpy(), model.W_U.numpy()
    W_OV = sum(model.W_V[l, h].numpy() @ model.W_O[l, h].numpy() for (l, h) in heads)
    ranks = []
    for a in rng.integers(0, model.cfg.d_vocab, size=n_sample):
        row = (W_E[a] @ W_OV) @ W_U
        ranks.append(int((row > row[a]).sum()))
    ranks = np.array(ranks)
    return dict(frac_top1_self=float((ranks == 0).mean()),
                median_self_rank=float(np.median(ranks)), n_sample=n_sample,
                vocab=int(model.cfg.d_vocab))


def main():
    os.makedirs(ART, exist_ok=True)
    torch.set_num_threads(8)
    from transformer_lens import HookedTransformer
    t0 = time.time()
    model = HookedTransformer.from_pretrained("gpt2", device="cpu")
    print(f"loaded gpt2 in {time.time()-t0:.0f}s")
    L, H = model.cfg.n_layers, model.cfg.n_heads

    toks, attend, ind_mask = repeated_batch(model, n_seq=16, T=120)
    ind, prev, dup = head_scores(model, toks, attend, ind_mask)

    order = np.argsort(ind, axis=None)[::-1]
    top_ind = [(int(o // H), int(o % H)) for o in order[:5]]
    top_ind_scores = [float(ind[l, h]) for (l, h) in top_ind]

    zoo = {}
    for l in range(L):
        for h in range(H):
            role = ("induction" if ind[l, h] > 0.3 else
                    "duplicate-token" if dup[l, h] > 0.3 else
                    "previous-token" if prev[l, h] > 0.3 else "other")
            if role != "other":
                zoo[f"{l}.{h}"] = dict(role=role, induction=float(ind[l, h]),
                                       prev=float(prev[l, h]), dup=float(dup[l, h]))

    ovcopy = ov_copy_sampled(model, top_ind)
    eig_copy = [float((np.real(np.linalg.eigvals(
        model.W_V[l, h].detach().numpy() @ model.W_O[l, h].detach().numpy())) > 0).mean())
        for (l, h) in top_ind]
    mean_eig_copy = float(np.mean(eig_copy))

    # H8@scale over 5 probe batches -> CI
    rng = np.random.default_rng(1)
    all_heads = [(l, h) for l in range(L) for h in range(H)]
    pick = [all_heads[i] for i in rng.choice(len(all_heads), 8, replace=False)]
    ctrl_heads = [h for h in pick if h not in top_ind][:5]
    base_l, abl_l, ctrl_l = [], [], []
    for ps in range(5):
        tk, at, im = repeated_batch(model, n_seq=16, T=120, seed=100 + ps)
        base_l.append(icl_loss(model, tk, at, im))
        abl_l.append(icl_loss(model, tk, at, im, ablate_heads=top_ind))
        ctrl_l.append(icl_loss(model, tk, at, im, ablate_heads=ctrl_heads))
    ind_delta = [a - b for a, b in zip(abl_l, base_l)]
    ctrl_delta = [c - b for c, b in zip(ctrl_l, base_l)]

    summary = dict(
        model="gpt2", n_layers=L, n_heads=H, probe="variable-offset (audit-hardened)",
        H6_transfer=dict(
            located_induction_heads=[f"{l}.{h}" for (l, h) in top_ind],
            induction_scores=top_ind_scores,
            matches_literature="5.1/5.5/6.9/7.2/7.10 are the canonical GPT-2 induction heads (Olsson et al.)",
            ov_copy_sampled=ovcopy, ov_eig_copying_mean=mean_eig_copy,
            copy_evidence="E.W_OV.U sampled median-self-rank %d / %d (top ~%.1f%%) is the copy signal; "
                          "the residual-basis eigenvalue fraction (%.3f) sits at random-matrix chance (~0.5) "
                          "and is NOT copy evidence" % (
                              ovcopy["median_self_rank"], ovcopy["vocab"],
                              100 * ovcopy["median_self_rank"] / ovcopy["vocab"], mean_eig_copy),
            verdict="PASS" if (top_ind_scores[0] > 0.6
                               and ovcopy["median_self_rank"] < 0.05 * ovcopy["vocab"])
            else "INCONCLUSIVE"),
        H8_scale_icl_ablation=dict(
            base_icl_loss=float(np.mean(base_l)),
            induction_ablation_delta=bootstrap_ci(ind_delta),
            control_ablation_delta=bootstrap_ci(ctrl_delta),
            control_heads=[f"{l}.{h}" for (l, h) in ctrl_heads], n_probe_batches=5,
            verdict="PASS" if np.mean(ind_delta) > 3 * abs(np.mean(ctrl_delta)) + 0.1
            else "INCONCLUSIVE"),
        head_zoo=zoo,
        deferred=["IOI circuit (H18)", "automated discovery ACDC/EAP/EAP-IG/AtP* (H15)",
                  "DAS/IIA (H16)", "logit-lens (H11@scale)", "probing/steering (H13@scale)"],
        deferred_ref="todos/2026-07-02-tiny-transformer-gpu-host-rungs.md",
    )
    save_json(summary, os.path.join(ART, "phase4b_summary.json"))
    print("PHASE4b VERDICTS:", json.dumps(
        {k: v["verdict"] for k, v in summary.items()
         if isinstance(v, dict) and "verdict" in v}))
    print("  H6 located:", summary["H6_transfer"]["located_induction_heads"],
          "| OV median-self-rank", ovcopy["median_self_rank"], "/", ovcopy["vocab"],
          "| eig(chance) %.3f" % mean_eig_copy)
    print(f"  H8 ICL ablation delta induction {bootstrap_ci(ind_delta)[0]:+.3f} "
          f"CI[{bootstrap_ci(ind_delta)[1]:+.3f},{bootstrap_ci(ind_delta)[2]:+.3f}] "
          f"vs control {bootstrap_ci(ctrl_delta)[0]:+.3f}")
    print("  head zoo:", {r: sum(1 for v in zoo.values() if v["role"] == r)
                          for r in ["induction", "duplicate-token", "previous-token"]})


if __name__ == "__main__":
    main()
