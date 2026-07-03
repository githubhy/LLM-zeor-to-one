"""Shared helpers: seeding, numerics with named safety floors, CIs, JSON IO."""
from __future__ import annotations

import json
import math
import os

import numpy as np

# Named numerical-safety floors (RIS Implementation Rule).
EPS_SOFTMAX = 1e-9
EPS_LN = 1e-5
EPS_LOG = 1e-12


def set_seed(seed: int):
    import random
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except Exception:
        pass


def softmax_np(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (e.sum(axis=axis, keepdims=True) + EPS_SOFTMAX)


def wilson_ci(k: int, n: int, z: float = 1.96):
    """Wilson score interval for a binomial proportion. Returns (p, lo, hi)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def bootstrap_ci(vals, n_boot: int = 10000, seed: int = 0, alpha: float = 0.05):
    """Percentile bootstrap CI of the mean. Returns (mean, lo, hi)."""
    vals = np.asarray(vals, dtype=float)
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    r = np.random.default_rng(seed)
    idx = r.integers(0, vals.size, size=(n_boot, vals.size))
    means = vals[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(vals.mean()), float(lo), float(hi))


def _json_default(o):
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def save_json(obj, path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def load_json(path: str):
    with open(path) as f:
        return json.load(f)
