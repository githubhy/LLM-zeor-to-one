"""B2 baseline: MLP-projector vs Q-Former connector across token budgets q, on frozen SigLIP
features. Measures color (coarse) + shape (detail) accuracy with Wilson CIs; tests whether the
learned Q-Former pooling preserves detail at low q better than avg-pool+MLP (survey §3.3)."""
from __future__ import annotations

import numpy as np
import torch

from .core import gen_dataset, extract_features, train_eval
from implementation.eap_ig.stats import wilson_ci
from implementation.eap_ig.utils import REPO_ROOT, save_json, save_npz, environment, git_commit

STUDY = "connector-ablation"
QS = (1, 4, 16, 64)
SEEDS = (0, 1, 2)


def _features(device):
    cache = REPO_ROOT / "artifacts" / STUDY / "features.npz"
    if cache.is_file():
        z = np.load(cache)
        return (torch.tensor(z["ftr"]), torch.tensor(z["cytr"]), torch.tensor(z["sytr"]),
                torch.tensor(z["fte"]), torch.tensor(z["cyte"]), torch.tensor(z["syte"]))
    imgs_tr, cy_tr, sy_tr = gen_dataset(n_per_combo=20, seed=0)
    imgs_te, cy_te, sy_te = gen_dataset(n_per_combo=8, seed=1)
    ftr = extract_features(imgs_tr, device=device)
    fte = extract_features(imgs_te, device=device)
    save_npz(cache, ftr=ftr.numpy(), cytr=cy_tr.numpy(), sytr=sy_tr.numpy(),
             fte=fte.numpy(), cyte=cy_te.numpy(), syte=sy_te.numpy())
    return ftr, cy_tr, sy_tr, fte, cy_te, sy_te


def main() -> None:
    ftr, cy_tr, sy_tr, fte, cy_te, sy_te = _features(device="cpu")
    n_te = fte.shape[0]
    grid = {"mlp": {}, "qformer": {}}
    for kind in ("mlp", "qformer"):
        for q in QS:
            runs = [train_eval(kind, q, ftr, cy_tr, sy_tr, fte, cy_te, sy_te, seed=s) for s in SEEDS]
            col = np.mean([r["color_acc"] for r in runs]); sh = np.mean([r["shape_acc"] for r in runs])
            _, clo, chi = wilson_ci(int(round(col * n_te)), n_te)
            _, slo, shi = wilson_ci(int(round(sh * n_te)), n_te)
            grid[kind][q] = {"color_acc": float(col), "color_ci95": [clo, chi],
                             "shape_acc": float(sh), "shape_ci95": [slo, shi],
                             "shape_std": float(np.std([r["shape_acc"] for r in runs])),
                             "n_params": runs[0]["n_params"]}

    # verdicts: detail (shape) gap Q-Former - MLP at each q; does detail need more q than color?
    detail_gap = {q: grid["qformer"][q]["shape_acc"] - grid["mlp"][q]["shape_acc"] for q in QS}
    summary = {
        "study": STUDY, "n_test": n_te, "q_budgets": list(QS), "seeds": list(SEEDS),
        "eval": "synthetic color(4) + shape(3) classification on frozen SigLIP features",
        "methods": {
            "mlp": {"metrics": {"color_acc_at_q16": grid["mlp"][16]["color_acc"],
                                "shape_acc_at_q16": grid["mlp"][16]["shape_acc"]}},
            "qformer": {"metrics": {"color_acc_at_q16": grid["qformer"][16]["color_acc"],
                                    "shape_acc_at_q16": grid["qformer"][16]["shape_acc"]}},
        },
        "grid": grid, "detail_gap_qformer_minus_mlp": detail_gap,
    }
    base = REPO_ROOT / "artifacts" / STUDY
    save_json(base / "baseline" / "summary.json", summary)
    save_npz(base / "baseline" / "curves.npz",
             q=np.array(QS),
             mlp_color=np.array([grid["mlp"][q]["color_acc"] for q in QS]),
             mlp_shape=np.array([grid["mlp"][q]["shape_acc"] for q in QS]),
             qf_color=np.array([grid["qformer"][q]["color_acc"] for q in QS]),
             qf_shape=np.array([grid["qformer"][q]["shape_acc"] for q in QS]))
    save_json(base / "study-manifest.json", {
        "study": STUDY, "environment": environment(), "git_commit": git_commit(),
        "iterations": [{"phase": 3, "note": "connector ablation MLP vs Q-Former across token budgets",
                        "detail_gap": detail_gap}]})
    print("q:            " + " ".join(f"{q:6d}" for q in QS))
    for kind in ("mlp", "qformer"):
        print(f"{kind:8s} color:" + " ".join(f"{grid[kind][q]['color_acc']:6.2f}" for q in QS))
        print(f"{kind:8s} shape:" + " ".join(f"{grid[kind][q]['shape_acc']:6.2f}" for q in QS))
    print("detail gap (qformer-mlp, shape):", {q: round(detail_gap[q], 3) for q in QS})


if __name__ == "__main__":
    main()
