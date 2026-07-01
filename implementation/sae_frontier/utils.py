"""Shared helpers for the SAE fidelity–sparsity frontier study.

Numerical-safety floors, deterministic seeding, and content hashing (used by the
P0-1 determinism gate). Pure functions only — no hidden state.
"""
from __future__ import annotations

import hashlib
import os
import random

import numpy as np
import torch

# --- numerical-safety floors (named constants; RIS implementation rule) ---
EPS_DIV = 1e-12          # generic division floor
EPS_NORM = 1e-8          # unit-norm / cosine floor
EPS_VAR = 1e-8           # explained-variance denominator floor
STE_BANDWIDTH = 0.1      # JumpReLU straight-through-estimator kernel half-width (eps),
#                          sized for O(1) activations so the threshold receives gradient
#                          (a too-small eps starves theta of gradient -> a stuck, dense SAE).


def set_determinism(seed: int) -> None:
    """Seed every RNG this study touches. Verified, not assumed (P0-1)."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def rng(seed: int) -> np.random.Generator:
    """A local numpy Generator — never the global singleton (workflow.md rule)."""
    return np.random.default_rng(seed)


def tensor_hash(t: torch.Tensor) -> str:
    """Stable content hash of a tensor's bytes — the P0-1 determinism fingerprint."""
    a = t.detach().to("cpu").contiguous().numpy()
    return hashlib.sha256(a.tobytes() + str(a.shape).encode() + str(a.dtype).encode()).hexdigest()[:16]


def unit_normalize(w: torch.Tensor, dim: int) -> torch.Tensor:
    """Row/column unit-normalize with a norm floor (decoder-atom normalization)."""
    return w / (w.norm(dim=dim, keepdim=True) + EPS_NORM)
