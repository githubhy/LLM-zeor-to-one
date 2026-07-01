"""Synthetic superposition testbed (survey Appendix B.1) — the ground-truth oracle (S1).

Generates activations that ARE a known sparse combination of `n_features` unit-norm
atoms living in a `d_model`-dimensional space (`d_model < n_features` → superposition).
Because the true dictionary is known, this substrate uniquely licenses the
feature-recovery and true-shrinkage metrics that no real-model study can measure.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .config import SyntheticConfig
from .utils import rng


@dataclass
class SyntheticData:
    x: torch.Tensor              # (n_samples, d_model)  the superposed activations
    true_features: torch.Tensor  # (d_model, n_features) unit-norm ground-truth atoms
    codes: torch.Tensor          # (n_samples, n_features) the true sparse codes
    importance: torch.Tensor     # (n_features,) I_i = decay**i


def generate(cfg: SyntheticConfig, dtype: torch.dtype = torch.float32) -> SyntheticData:
    r = rng(cfg.seed)
    n, m = cfg.n_features, cfg.d_model
    # ground-truth dictionary: random directions, unit-norm columns (near-orthogonal since n>m)
    G = r.standard_normal((m, n))
    G /= np.linalg.norm(G, axis=0, keepdims=True) + 1e-8
    importance = cfg.importance_decay ** np.arange(n)
    # sparse codes: each feature active w.p. feature_prob, magnitude ~ U(0,1)
    active = (r.random((cfg.n_samples, n)) < cfg.feature_prob).astype(np.float64)
    mag = r.random((cfg.n_samples, n))
    codes = active * mag
    x = codes @ np.ascontiguousarray(G.T)  # (n_samples, m); ascontiguous silences a numpy-2/Accelerate false matmul warning
    to = lambda a: torch.tensor(a, dtype=dtype)
    return SyntheticData(
        x=to(x), true_features=to(G), codes=to(codes), importance=to(importance)
    )


def generate_orthonormal(d_model: int, n_features: int, feature_prob: float = 0.1,
                         n_samples: int = 4096, seed: int = 0,
                         dtype: torch.dtype = torch.float32) -> SyntheticData:
    """Controlled substrate for the H2 shrinkage mechanism: ORTHONORMAL atoms
    (`n_features <= d_model`), so reconstruction is exact and the per-feature
    least-squares magnitude decouples — the regime where the survey Eq D-2
    soft-threshold `max(f* - lambda, 0)` prediction is exact.
    """
    if n_features > d_model:
        raise ValueError("orthonormal atoms require n_features <= d_model")
    r = rng(seed)
    Q, _ = np.linalg.qr(r.standard_normal((d_model, d_model)))
    G = np.ascontiguousarray(Q[:, :n_features])          # (d_model, n_features), orthonormal cols
    active = (r.random((n_samples, n_features)) < feature_prob).astype(np.float64)
    mag = r.random((n_samples, n_features))
    codes = active * mag
    x = codes @ np.ascontiguousarray(G.T)
    to = lambda a: torch.tensor(a, dtype=dtype)
    return SyntheticData(x=to(x), true_features=to(G), codes=to(codes),
                         importance=to(np.ones(n_features)))
