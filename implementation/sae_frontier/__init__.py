"""SAE fidelity–sparsity frontier — reference implementation.

Four SAE candidates (ReLU+L1, Gated, TopK, JumpReLU) with a uniform interface, a
synthetic-superposition oracle substrate, real-model (GPT-2) activations, a shared
metric set, oracle checks, and a deterministic trainer. See
docs/sae-frontier-implementation-study.md.
"""
from __future__ import annotations

from .config import SAEConfig, SyntheticConfig, TrainConfig, VARIANTS
from .saes import build_sae, SAE, ReLUSAE, GatedSAE, TopKSAE, JumpReLUSAE
from .synthetic import generate, generate_orthonormal, SyntheticData
from .train import train_sae
from . import metrics, oracle, registry

__all__ = [
    "SAEConfig", "SyntheticConfig", "TrainConfig", "VARIANTS",
    "build_sae", "SAE", "ReLUSAE", "GatedSAE", "TopKSAE", "JumpReLUSAE",
    "generate", "generate_orthonormal", "SyntheticData", "train_sae",
    "metrics", "oracle", "registry",
]
