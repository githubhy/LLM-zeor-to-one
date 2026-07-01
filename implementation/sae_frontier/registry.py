"""Single candidate / data / metric registry (P2-1 contract).

Every candidate is built through `build_candidate`, every substrate through `DATA`, and
every score through `METRICS`. No candidate may smuggle in its own loader or metric.
"""
from __future__ import annotations

from .config import SAEConfig
from .saes import build_sae
from .synthetic import generate as _generate_synthetic
from . import metrics as _m

CANDIDATES = ("relu", "gated", "topk", "jumprelu")

METRICS = {
    "l0": _m.l0,
    "explained_variance": _m.explained_variance,
    "normalized_mse": _m.normalized_mse,
    "loss_recovered": _m.loss_recovered,
    "feature_recovery": _m.feature_recovery,
    "shrinkage_ratio": _m.shrinkage_ratio,
}


def build_candidate(cfg: SAEConfig):
    if cfg.variant not in CANDIDATES:
        raise KeyError(f"unknown candidate {cfg.variant!r}; must be one of {CANDIDATES}")
    return build_sae(cfg)


def get_data(source: str, cfg):
    if source == "synthetic":
        return _generate_synthetic(cfg)
    if source == "activations":
        from .activations import harvest_activations  # lazy: needs transformers
        return harvest_activations(cfg)
    raise KeyError(f"unknown data source {source!r}")
