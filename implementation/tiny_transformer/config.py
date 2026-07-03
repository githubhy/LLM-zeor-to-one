"""Frozen-dataclass configs (RIS Implementation Rule: typed, defaulted, stored)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ModelConfig:
    """Architecture, in the Appendix-A symbols of §A.10/§A.13.

    Primary induction config = the plan's Phase-1 table:
    L=2, h=4, d=128, d_k=d_v=32, T=256, |V|=64, attention-only.
    """
    n_layers: int = 2
    n_heads: int = 4
    d_model: int = 128
    d_head: int = 32              # d_k = d_v
    d_mlp: int | None = None      # None => attention-only (the §A.8/§A.9 setting)
    d_vocab: int = 64
    n_ctx: int = 256
    act_fn: str = "relu"          # "relu" | "gelu"
    normalization: str = "LN"     # "LN" | "LNPre" | None-ish "none"
    pre_norm: bool = True
    tie_embed: bool = False
    init_scale: float = 0.02
    seed: int = 0

    @property
    def use_mlp(self) -> bool:
        return self.d_mlp is not None

    def __post_init__(self):
        # §A.10: a layer is a sum of h distinct low-rank circuits; d = h·d_k.
        if self.d_model != self.n_heads * self.d_head:
            raise ValueError(
                f"d_model={self.d_model} must equal n_heads*d_head="
                f"{self.n_heads * self.d_head} (§A.10)"
            )


@dataclass(frozen=True)
class TrainConfig:
    lr: float = 1e-3
    beta1: float = 0.9
    beta2: float = 0.98
    weight_decay: float = 0.0
    batch_size: int = 256
    n_steps: int = 20000
    eval_every: int = 250
    eval_batch: int = 512
    grad_clip: float = 1.0
    warmup_steps: int = 200
    seed: int = 0
    task: str = "induction"       # "induction" | "modadd"
    device: str = "cpu"
    dtype: str = "float32"


# The plan's Phase-1 configuration table, as ready-to-use presets.
PRESETS = {
    "induction": dict(n_layers=2, n_heads=4, d_model=128, d_head=32, d_mlp=None,
                      d_vocab=64, n_ctx=256),
    "induction_mlp": dict(n_layers=2, n_heads=4, d_model=128, d_head=32, d_mlp=512,
                          d_vocab=64, n_ctx=256),
    "induction_1layer": dict(n_layers=1, n_heads=4, d_model=128, d_head=32,
                             d_mlp=None, d_vocab=64, n_ctx=256),
    "modadd": dict(n_layers=1, n_heads=4, d_model=128, d_head=32, d_mlp=512,
                   d_vocab=114, n_ctx=3),   # p=113, vocab=p+1 ('=' token)
}


def model_config(preset: str = "induction", **overrides) -> ModelConfig:
    base = dict(PRESETS[preset])
    base.update(overrides)
    return ModelConfig(**base)


def save_config(cfg, path: str):
    with open(path, "w") as f:
        json.dump(asdict(cfg), f, indent=1, default=str)
