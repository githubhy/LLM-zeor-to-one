"""Single candidate / task / metric registry (P2-1 contract). Every candidate is scored
through `build_scorer`, every task through `get_task`, every metric name lives in METRICS.
No candidate smuggles in its own loader or metric — the baseline reports an identical metric
key-set for all four candidates."""
from __future__ import annotations

from .attribution import score_nodes
from .config import AttrConfig, TaskConfig
from .tasks import build_task

CANDIDATES = ("random", "eap", "eap_ig", "exact_patch")

# The uniform metric key-set every candidate reports in the baseline summary (P2-1).
METRIC_KEYS = ("auc_faithfulness", "faith_at_ref", "recovery_rate", "corr_to_exact_pearson")


def build_scorer(cfg: AttrConfig):
    if cfg.method not in CANDIDATES:
        raise KeyError(f"unknown candidate {cfg.method!r}; must be one of {CANDIDATES}")
    return lambda M, batch: score_nodes(M, batch, cfg)


def get_task(M, cfg: TaskConfig):
    return build_task(M.tok, cfg)
