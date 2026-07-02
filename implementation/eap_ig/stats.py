"""Statistics for the baseline gate: bootstrap CIs, Wilson binomial CI (rate metrics,
P0-4), paired-seed significance + effect size (P0-2), rank/linear correlation (H5)."""
from __future__ import annotations

import numpy as np
from scipy import stats as _ss


def bootstrap_ci(values, n_boot: int = 10000, alpha: float = 0.05, seed: int = 0):
    """Percentile bootstrap CI for the mean. Returns (mean, lo, hi)."""
    v = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    means = v[idx].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(v.mean()), float(lo), float(hi)


def wilson_ci(successes: int, n: int, z: float = 1.96):
    """Wilson score interval for a binomial rate (P0-4)."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return float(p), float(max(0.0, centre - half)), float(min(1.0, centre + half))


def paired_test(a, b):
    """Paired comparison of two candidates over a shared seed/example set (P0-2).
    Returns p_value (paired t) and effect_size (Cohen's d_z) + Cliff's delta."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    diff = a - b
    if np.allclose(diff, 0):
        return {"p_value": 1.0, "effect_size": 0.0, "cliffs_delta": 0.0,
                "mean_diff": 0.0, "test": "paired_t"}
    t_res = _ss.ttest_rel(a, b)
    d_z = float(diff.mean() / (diff.std(ddof=1) + 1e-12))
    # Cliff's delta
    gt = sum(1 for x in a for y in b if x > y)
    lt = sum(1 for x in a for y in b if x < y)
    cliffs = (gt - lt) / (len(a) * len(b))
    return {"p_value": float(t_res.pvalue), "effect_size": d_z,
            "cliffs_delta": float(cliffs), "mean_diff": float(diff.mean()),
            "test": "paired_t"}


def correlate(x: dict, y: dict):
    """Pearson + Spearman correlation of two score dicts over shared keys (H5)."""
    keys = [k for k in x if k in y]
    xv = np.array([x[k] for k in keys]); yv = np.array([y[k] for k in keys])
    pear = _ss.pearsonr(xv, yv)
    spear = _ss.spearmanr(xv, yv)
    return {"pearson_r": float(pear.statistic), "pearson_p": float(pear.pvalue),
            "spearman_r": float(spear.statistic), "spearman_p": float(spear.pvalue),
            "n": len(keys)}
