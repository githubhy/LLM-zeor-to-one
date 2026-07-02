"""Track-C extension study: do the adaptive-count SAEs (BatchTopK, Matryoshka) beat exact-k
TopK on the fidelity–sparsity frontier — the parent study's red-team prediction (Sec. 10),
which said they win on heavy-tailed / DENSE activations? Plus a clean orthonormal shrinkage
curve (H2) with the new AdaptiveJumpReLU. Extends implementation/sae_frontier; artifacts under
artifacts/sae-frontier-ext/."""
from __future__ import annotations

import numpy as np
import torch

from .config import SAEConfig, SyntheticConfig, TrainConfig
from .synthetic import generate, generate_orthonormal
from .saes import build_sae
from .saes_ext import build_ext
from .metrics import explained_variance, feature_recovery, l0, shrinkage_ratio
from .train import train_sae
from .utils import set_determinism
from implementation.eap_ig.utils import REPO_ROOT, save_json, save_npz, environment, git_commit

STUDY = "sae-frontier-ext"
SEEDS = (0, 1, 2)
KS = (4, 8, 16)
STEPS = 1200
SUBSTRATES = {"sparse": 0.05, "dense": 0.25}       # feature activation probability
EXACT_VS_ADAPTIVE = ("topk", "batchtopk", "matryoshka")


def _train_eval(variant, k, seed, X, true_feats, d_model):
    if variant in ("topk",):
        sae = build_sae(SAEConfig(variant="topk", d_model=d_model, seed=seed, k=k))
    else:
        sae = build_ext(variant, d_model=d_model, seed=seed, k=k)
    train_sae(sae, X, TrainConfig(steps=STEPS, seed=seed))
    with torch.no_grad():
        f = sae.encode(X)
        x_hat, _ = sae(X)
    fr = feature_recovery(sae.W_dec.detach(), true_feats)
    return {"l0": l0(f), "ev": explained_variance(X, x_hat), "mmcs": fr["mmcs_true_to_learned"]}


def main() -> None:
    set_determinism(0)
    d_model = 32
    # ---- head-to-head across substrates ----
    frontier = {s: {v: {} for v in EXACT_VS_ADAPTIVE} for s in SUBSTRATES}
    for sname, fp in SUBSTRATES.items():
        data = generate(SyntheticConfig(n_features=128, d_model=d_model, feature_prob=fp,
                                        n_samples=6000, seed=0))
        X, T = data.x, data.true_features
        for v in EXACT_VS_ADAPTIVE:
            for k in KS:
                recs = [_train_eval(v, k, s, X, T, d_model) for s in SEEDS]
                frontier[sname][v][k] = {
                    "l0_mean": float(np.mean([r["l0"] for r in recs])),
                    "ev_mean": float(np.mean([r["ev"] for r in recs])),
                    "ev_std": float(np.std([r["ev"] for r in recs])),
                    "mmcs_mean": float(np.mean([r["mmcs"] for r in recs])),
                }

    # red-team verdict: EV of adaptive vs exact TopK at matched k, per substrate
    verdict = {}
    for sname in SUBSTRATES:
        verdict[sname] = {}
        for v in ("batchtopk", "matryoshka"):
            gaps = [frontier[sname][v][k]["ev_mean"] - frontier[sname]["topk"][k]["ev_mean"] for k in KS]
            verdict[sname][f"{v}_vs_topk_mean_ev_gap"] = float(np.mean(gaps))

    # ---- orthonormal shrinkage curve (H2): ReLU shrinks, TopK/JumpReLU/Adaptive ~ unbiased ----
    od = generate_orthonormal(d_model=32, n_features=24, feature_prob=0.1, n_samples=4096, seed=0)
    shrink = {}
    for v in ("relu", "topk", "jumprelu"):
        sae = build_sae(SAEConfig(variant=v, d_model=32, seed=0, k=8, l1_coeff=0.1))
        train_sae(sae, od.x, TrainConfig(steps=STEPS, seed=0))
        shrink[v] = shrinkage_ratio(sae, od.x)
    sae_a = build_ext("adaptive_jumprelu", d_model=32, seed=0, k=8, l1_coeff=0.1)
    train_sae(sae_a, od.x, TrainConfig(steps=STEPS, seed=0))
    shrink["adaptive_jumprelu"] = shrinkage_ratio(sae_a, od.x)

    summary = {"study": STUDY, "seeds": list(SEEDS), "ks": list(KS), "steps": STEPS,
               "substrates": {k: {"feature_prob": v} for k, v in SUBSTRATES.items()},
               "methods": {v: {"metrics": {"frontier_ev_at_k8": frontier["dense"][v][8]["ev_mean"],
                                           "frontier_mmcs_at_k8": frontier["dense"][v][8]["mmcs_mean"]}}
                           for v in EXACT_VS_ADAPTIVE},
               "frontier": frontier, "redteam_verdict": verdict,
               "orthonormal_shrinkage": shrink}
    base = REPO_ROOT / "artifacts" / STUDY
    save_json(base / "baseline" / "summary.json", summary)
    save_npz(base / "baseline" / "frontier.npz",
             **{f"ev__{s}__{v}": np.array([frontier[s][v][k]["ev_mean"] for k in KS])
                for s in SUBSTRATES for v in EXACT_VS_ADAPTIVE})
    save_json(base / "study-manifest.json", {
        "study": STUDY, "environment": environment(), "git_commit": git_commit(),
        "iterations": [{"phase": 3, "note": "ext frontier: topk vs batchtopk vs matryoshka + orthonormal shrinkage",
                        "redteam_verdict": verdict, "shrinkage": shrink}]})
    print("red-team verdict (EV gap vs TopK, +=adaptive better):")
    for s in SUBSTRATES:
        print(f"  {s}: {verdict[s]}")
    print("orthonormal shrinkage ratio (<1=shrinks, ~1=unbiased):",
          {k: round(v, 3) for k, v in shrink.items()})


if __name__ == "__main__":
    main()
