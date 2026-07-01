"""Shared experiment harness: sweep grids + one train-and-evaluate call.

Every candidate is trained and scored through `train_eval` with the same data and the
same metric set (P2-1). The per-variant sweep traces the fidelity–sparsity frontier by
varying only that variant's sparsity control (lambda for relu/gated/jumprelu, k for topk).
"""
from __future__ import annotations

import time

import torch

from .config import SAEConfig, TrainConfig
from .metrics import explained_variance, feature_recovery, l0, shrinkage_ratio
from .saes import build_sae
from .train import train_sae

# Operating points per variant — each yields a different L0 (the frontier x-axis).
SWEEPS: dict[str, list[dict]] = {
    "relu": [{"l1_coeff": v} for v in (0.05, 0.1, 0.2, 0.4, 0.8)],
    "gated": [{"l1_coeff": v} for v in (0.05, 0.1, 0.2, 0.4, 0.8)],
    "jumprelu": [{"l1_coeff": v} for v in (0.02, 0.05, 0.1, 0.4, 0.8)],
    "topk": [{"k": v} for v in (2, 4, 8, 16, 32)],
}
VARIANTS = ("relu", "gated", "topk", "jumprelu")


def train_eval(variant: str, op: dict, seed: int, X: torch.Tensor,
               true_features: torch.Tensor | None, d_model: int, expansion: int,
               steps: int) -> dict:
    cfg = SAEConfig(variant=variant, d_model=d_model, expansion=expansion, seed=seed, **op)
    sae = build_sae(cfg)
    t0 = time.perf_counter()
    out = train_sae(sae, X, TrainConfig(steps=steps, seed=seed))
    train_s = time.perf_counter() - t0
    with torch.no_grad():
        f = sae.encode(X)
        x_hat, _ = sae(X)
    rec = {
        "variant": variant, "seed": seed, "op": op,
        "l0": l0(f),
        "ev": explained_variance(X, x_hat),
        "shrinkage": shrinkage_ratio(sae, X),
        "n_dead": out["n_dead"],
        "final_loss": out["final_loss"],
        "train_s": train_s,
    }
    if true_features is not None:
        fr = feature_recovery(sae.W_dec.detach(), true_features)
        rec["mmcs"] = fr["mmcs_true_to_learned"]
        rec["frac_recovered"] = fr["frac_true_recovered_0.9"]
    return rec
