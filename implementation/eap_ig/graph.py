"""Circuit construction over the node graph: top-n by |score| (Hanna footnote 7 —
absolute score keeps negatively-important components). Node granularity, so a "circuit"
is a node set; the complement is ablated to corrupt in faithfulness.py."""
from __future__ import annotations


def rank_nodes(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda u: abs(scores[u]), reverse=True)


def top_n_circuit(scores: dict[str, float], n: int) -> set[str]:
    return set(rank_nodes(scores)[:max(0, n)])
