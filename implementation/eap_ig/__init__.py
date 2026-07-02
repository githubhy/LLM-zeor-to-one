"""EAP / EAP-IG circuit-faithfulness reference implementation (study eap-ig-faithfulness).

Reproduces Hanna, Pezzelle & Belinkov (COLM 2024), "Have Faith in Faithfulness",
on GPT-2-small at head+MLP node granularity over the additive residual stream.

Public surface is the P2-1 registry (`registry.CANDIDATES`, `registry.METRICS`,
`registry.build_scorer`, `registry.get_task`). No candidate smuggles its own loader/metric.
"""
from __future__ import annotations

__all__ = ["config", "tasks", "metrics", "model", "graph", "attribution",
           "faithfulness", "registry", "stats", "oracle", "manifest"]
