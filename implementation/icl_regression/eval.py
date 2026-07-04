"""In-context evaluation: per-example-count error curves for the model and the classical
learners, plus the model-vs-learner agreement (Akyürek normalized SPD). Shared by run.py.

For a batch of tasks with k in-context examples, the model's running prediction at x-token
position i (preds_model[:, i]) is its prediction of y_i having seen examples 0..i-1. At each
context length n (= i examples used), we fit OLS / ridge / j-step GD on the first n examples,
predict x_n, and compare (i) error-to-truth and (ii) agreement to the model's prediction.
"""
from __future__ import annotations

import numpy as np

from .task import ols_predict, ridge_predict, gd_predict, normalized_spd


def learner_curves(X: np.ndarray, y: np.ndarray, preds_model: np.ndarray, *,
                   ridge_lam: float, gd_steps: int, gd_lr: float):
    """Per-context-length curves. X (B, k, d), y (B, k), preds_model (B, k).

    Returns a dict of length-(k-1) arrays indexed by n = 1..k-1:
      ns, mse_{model,ols,ridge,gd}, spd_model_vs_{ols,ridge,gd}  (normalized SPD, lower=closer).
    """
    B, k, d = X.shape
    ns = list(range(1, k))
    out = {"ns": ns, "mse_model": [], "mse_ols": [], "mse_ridge": [], "mse_gd": [],
           "spd_model_vs_ols": [], "spd_model_vs_ridge": [], "spd_model_vs_gd": []}
    for n in ns:
        Xc, yc, xq, tgt = X[:, :n], y[:, :n], X[:, n], y[:, n]
        mp = preds_model[:, n]
        ols = ols_predict(Xc, yc, xq)
        ridge = ridge_predict(Xc, yc, xq, ridge_lam)
        gd = gd_predict(Xc, yc, xq, gd_steps, gd_lr)
        out["mse_model"].append(float(np.mean((mp - tgt) ** 2)))
        out["mse_ols"].append(float(np.mean((ols - tgt) ** 2)))
        out["mse_ridge"].append(float(np.mean((ridge - tgt) ** 2)))
        out["mse_gd"].append(float(np.mean((gd - tgt) ** 2)))
        out["spd_model_vs_ols"].append(normalized_spd(mp, ols))
        out["spd_model_vs_ridge"].append(normalized_spd(mp, ridge))
        out["spd_model_vs_gd"].append(normalized_spd(mp, gd))
    return out


def delta_norm_at(curves: dict, n: int, learner: str = "ols") -> float:
    """Normalized model-vs-learner deviation at context length n (the H9-B statistic).
    learner in {ols, ridge, gd}. Returns spd_model_vs_<learner>[n]."""
    idx = curves["ns"].index(n)
    return curves[f"spd_model_vs_{learner}"][idx]


def best_learner_at(curves: dict, n: int) -> str:
    """Which classical learner the model tracks closest at context length n (min SPD)."""
    idx = curves["ns"].index(n)
    cands = {"ols": curves["spd_model_vs_ols"][idx],
             "ridge": curves["spd_model_vs_ridge"][idx],
             "gd": curves["spd_model_vs_gd"][idx]}
    return min(cands, key=cands.get)
