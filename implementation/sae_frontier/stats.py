"""Aggregation + paired significance (P0-2). All study metrics are continuous
(EV, L0, feature-recovery, shrinkage) — no Bernoulli rate metric — so P0-4's binomial
path is n/a here (recorded explicitly in the summary)."""
from __future__ import annotations

import numpy as np
from scipy import stats


def aggregate(values) -> dict:
    a = np.asarray(values, dtype=float)
    n = len(a)
    m = float(a.mean())
    sd = float(a.std(ddof=1)) if n > 1 else 0.0
    if n > 2 and sd > 0:
        lo, hi = stats.t.interval(0.95, n - 1, loc=m, scale=sd / np.sqrt(n))
    else:
        lo, hi = m, m
    return {"mean": m, "std": sd, "ci95_lo": float(lo), "ci95_hi": float(hi), "n": n}


def interp_at(points: list[tuple[float, float]], x_target: float) -> float:
    """Interpolate y at x_target from (x, y) points (sorted by x); clamps at ends."""
    pts = sorted(points)
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    return float(np.interp(x_target, xs, ys))


def paired_test(a, b) -> dict:
    """Paired t-test + Wilcoxon signed-rank + paired effect size (Cohen's d_z)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = a - b
    n = len(a)
    t_p = float(stats.ttest_rel(a, b).pvalue) if n > 1 else 1.0
    try:
        w_p = float(stats.wilcoxon(a, b).pvalue) if n > 1 and np.any(d != 0) else 1.0
    except ValueError:
        w_p = 1.0
    dz = float(d.mean() / (d.std(ddof=1) + 1e-12)) if n > 1 else 0.0
    return {"mean_diff": float(d.mean()), "t_pvalue": t_p, "wilcoxon_pvalue": w_p, "cohens_dz": dz}
