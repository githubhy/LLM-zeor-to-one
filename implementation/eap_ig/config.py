"""Frozen-dataclass configs (RIS implementation rule): every knob typed, defaulted,
validated, JSON-serializable so a stored config + seed + env reproduces a run."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Literal

Method = Literal["eap", "eap_ig", "exact_patch", "random"]
METHODS: tuple[Method, ...] = ("eap", "eap_ig", "exact_patch", "random")

Task = Literal["ioi", "greater_than", "sva"]
TASKS: tuple[Task, ...] = ("ioi", "greater_than", "sva")

Ablation = Literal["corrupt", "zero", "mean"]


@dataclass(frozen=True)
class ModelConfig:
    name: str = "gpt2"                 # GPT-2-small, 124M, cached
    device: str = "cpu"               # deterministic; MPS optional
    dtype: Literal["float32", "float16", "bfloat16"] = "float32"

    def __post_init__(self) -> None:
        if self.dtype not in ("float32", "float16", "bfloat16"):
            raise ValueError(f"bad dtype {self.dtype!r}")


@dataclass(frozen=True)
class TaskConfig:
    task: Task
    n_examples: int = 200
    seed: int = 0
    max_len: int = 32

    def __post_init__(self) -> None:
        if self.task not in TASKS:
            raise ValueError(f"task must be one of {TASKS}, got {self.task!r}")
        if self.n_examples <= 0:
            raise ValueError("n_examples must be positive")


@dataclass(frozen=True)
class AttrConfig:
    """One edge-scoring candidate."""
    method: Method
    m_ig: int = 5                      # IG integration steps (Hanna: m=5)
    seed: int = 0                      # for `random`

    def __post_init__(self) -> None:
        if self.method not in METHODS:
            raise ValueError(f"method must be one of {METHODS}, got {self.method!r}")
        if self.method == "eap_ig" and self.m_ig < 1:
            raise ValueError("m_ig must be >= 1")

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class CircuitConfig:
    """Build a circuit of `n_edges` top-|score| edges; ablate the complement."""
    n_edges: int = 200
    ablation: Ablation = "corrupt"
    prune: bool = True                 # drop parentless/childless nodes (Hanna §4.2)

    def __post_init__(self) -> None:
        if self.n_edges < 0:
            raise ValueError("n_edges must be >= 0")
