"""Greedy edge-circuit search (Hanna 2024 App E) + recursive prune.

Greedy ADDS edges backward from the logits: start with the logits node; repeatedly take the
highest-|score| edge whose CHILD node is already in the circuit, add it and its parent. This
never orphans an edge from the output (unlike top-n-by-|score|, Syed), which is exactly why it
beats top-n on SVA (Hanna p.6, p.18). Then recursively prune nodes/edges with no parent or no
child (Hanna p.7) — the step that prunes EAP's SVA circuits to near-nothing at small n.
"""
from __future__ import annotations

import heapq
from collections import defaultdict


def child_node(slot: str) -> str:
    """Owning node of a destination slot."""
    if slot == "logits":
        return "logits"
    if slot.endswith((".q", ".k", ".v")):
        return slot.rsplit(".", 1)[0]          # a{l}.h{h}.s -> a{l}.h{h}
    if slot.endswith(".in"):
        return slot[:-3]                        # m{l}.in -> m{l}
    raise ValueError(slot)


def greedy_circuit(edge_scores: dict[tuple, float], n: int) -> set[tuple]:
    """Build an n-edge circuit greedily (App E). Returns the set of in-circuit edges."""
    by_child = defaultdict(list)                # node -> [(|score|, idx, edge, parent)]
    for i, ((u, v), s) in enumerate(edge_scores.items()):
        by_child[child_node(v)].append((-abs(s), i, (u, v), u))

    C_V = {"logits"}
    C_E: set = set()
    pool: list = []
    pushed = set()

    def push_node(node):
        if node in pushed:
            return
        pushed.add(node)
        for item in by_child.get(node, ()):
            heapq.heappush(pool, item)

    push_node("logits")
    while len(C_E) < n and pool:
        _, _, edge, parent = heapq.heappop(pool)
        if edge in C_E:
            continue
        C_E.add(edge)
        if parent not in C_V:
            C_V.add(parent)
            push_node(parent)
    return C_E


def prune(edges: set[tuple]) -> set[tuple]:
    """Recursively drop edges whose parent has no parent (and isn't `embed`) or whose child has
    no child (and isn't `logits`) — Hanna p.7. Iterates to a fixpoint."""
    edges = set(edges)
    changed = True
    while changed:
        changed = False
        parents = defaultdict(set)
        children = defaultdict(set)
        for (u, v) in edges:
            cn = child_node(v)
            children[u].add(cn)
            parents[cn].add(u)
        for (u, v) in list(edges):
            cn = child_node(v)
            u_orphan = (u != "embed") and (len(parents[u]) == 0)
            cn_childless = (cn != "logits") and (len(children[cn]) == 0)
            if u_orphan or cn_childless:
                edges.discard((u, v))
                changed = True
    return edges
