"""Frozen-dataclass configs for the SAE frontier study (RIS implementation rule).

Every knob is typed, defaulted, validated at construction, and JSON-serializable so
that a stored config + seed + env block fully reproduces a run (P1-3 / P2-2).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Literal

Variant = Literal["relu", "gated", "topk", "jumprelu"]
VARIANTS: tuple[Variant, ...] = ("relu", "gated", "topk", "jumprelu")


@dataclass(frozen=True)
class SAEConfig:
    """Configuration for one SAE candidate. `variant` selects the architecture."""
    variant: Variant
    d_model: int
    expansion: int = 4               # d_sae = expansion * d_model
    seed: int = 0
    dtype: Literal["float32", "float64"] = "float32"
    # sparsity controls (variant-specific; unused ones are ignored)
    l1_coeff: float = 1e-3           # ReLU / Gated L1 weight (lambda); JumpReLU L0 weight
    k: int = 16                      # TopK exact active count
    k_aux: int = 64                  # TopK AuxK dead-latent count
    aux_coeff: float = 1.0 / 32.0    # TopK AuxK loss weight (Gao et al.)
    jumprelu_init_threshold: float = 0.1
    dead_steps_threshold: int = 200  # TopK: steps-without-firing before "dead"

    @property
    def d_sae(self) -> int:
        return self.expansion * self.d_model

    def __post_init__(self) -> None:
        if self.variant not in VARIANTS:
            raise ValueError(f"variant must be one of {VARIANTS}, got {self.variant!r}")
        if self.d_model <= 0 or self.expansion <= 0:
            raise ValueError("d_model and expansion must be positive")
        if self.variant == "topk" and not (0 < self.k <= self.d_sae):
            raise ValueError(f"topk k={self.k} must be in (0, d_sae={self.d_sae}]")
        if self.l1_coeff < 0 or self.aux_coeff < 0:
            raise ValueError("coefficients must be non-negative")

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["d_sae"] = self.d_sae
        return d


@dataclass(frozen=True)
class SyntheticConfig:
    """Toy-Models-of-Superposition data generator (survey Appendix B.1)."""
    n_features: int = 128            # ground-truth feature count (n)
    d_model: int = 32                # bottleneck dimension (m < n)
    feature_prob: float = 0.05       # P(feature active) = 1 - sparsity
    importance_decay: float = 0.99   # I_i = decay**i
    n_samples: int = 8192
    seed: int = 0

    def __post_init__(self) -> None:
        if not (self.d_model < self.n_features):
            raise ValueError("superposition requires d_model < n_features")
        if not (0.0 < self.feature_prob <= 1.0):
            raise ValueError("feature_prob must be in (0, 1]")


@dataclass(frozen=True)
class TrainConfig:
    lr: float = 3e-4
    steps: int = 2000
    batch_size: int = 512
    seed: int = 0
    resample_dead: bool = True

    def __post_init__(self) -> None:
        if self.steps <= 0 or self.batch_size <= 0:
            raise ValueError("steps and batch_size must be positive")
