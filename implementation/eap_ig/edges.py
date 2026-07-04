"""Edge-level graph for EAP/EAP-IG (Hanna et al. 2024, q/k/v-split; Syed et al. 2023 App F).

An EDGE (u -> v) connects an upstream SOURCE node u (which writes an additive contribution to
the residual stream) to a downstream DESTINATION input-slot v (which reads the residual stream).
For GPT-2-small this graph has exactly 32,491 edges (Hanna p.1), reproducible only with the q/k/v
split of each attention head into three separate destination slots.

Sources (157): `embed`, `a{l}.h{h}` (144), `m{l}` (12).
Destinations (445): `a{l}.h{h}.{q,k,v}` (432), `m{l}.in` (12), `logits` (1).

Connectivity: edge (u -> v) exists iff u WRITES strictly before v READS, respecting intra-layer
order (a layer's attention writes before that layer's MLP reads; the heads of a layer are parallel
and do not connect to each other). Ordering is encoded by integer write/read positions on a
4-slots-per-layer scale: attn-in = 4L+1, attn-out = 4L+2, mlp-in = 4L+3, mlp-out = 4L+4.
"""
from __future__ import annotations

SLOTS = ("q", "k", "v")


def source_nodes(n_layer: int, n_head: int) -> list[str]:
    names = ["embed"]
    for l in range(n_layer):
        names += [f"a{l}.h{h}" for h in range(n_head)]
        names.append(f"m{l}")
    return names


def dest_slots(n_layer: int, n_head: int) -> list[str]:
    slots = []
    for l in range(n_layer):
        for h in range(n_head):
            slots += [f"a{l}.h{h}.{s}" for s in SLOTS]
        slots.append(f"m{l}.in")
    slots.append("logits")
    return slots


def _write_pos(u: str, n_layer: int) -> int:
    if u == "embed":
        return 0
    if u.startswith("a"):                       # a{l}.h{h}  -> attn-out of layer l
        l = int(u[1:].split(".")[0])
        return 4 * l + 2
    if u.startswith("m"):                        # m{l}       -> mlp-out of layer l
        l = int(u[1:])
        return 4 * l + 4
    raise ValueError(u)


def _read_pos(v: str, n_layer: int) -> int:
    if v == "logits":
        return 4 * n_layer + 10                  # after every layer
    if v.endswith((".q", ".k", ".v")):          # a{l}.h{h}.{slot} -> attn-in of layer l
        l = int(v[1:].split(".")[0])
        return 4 * l + 1
    if v.endswith(".in"):                        # m{l}.in -> mlp-in of layer l
        l = int(v[1:].split(".")[0])
        return 4 * l + 3
    raise ValueError(v)


def upstream_sources(v: str, n_layer: int, n_head: int) -> list[str]:
    """Sources causally upstream of destination slot v (write strictly before v reads)."""
    rp = _read_pos(v, n_layer)
    return [u for u in source_nodes(n_layer, n_head) if _write_pos(u, n_layer) < rp]


def edges(n_layer: int, n_head: int) -> list[tuple[str, str]]:
    """All (source, dest-slot) edges in the graph."""
    out = []
    for v in dest_slots(n_layer, n_head):
        for u in upstream_sources(v, n_layer, n_head):
            out.append((u, v))
    return out


def edge_count(n_layer: int, n_head: int, split_qkv: bool = True) -> int:
    """Edge count. split_qkv=True gives Hanna's 32,491 for GPT-2-small; False (single head input)
    gives 11,611 — the difference the q/k/v split is load-bearing for."""
    if split_qkv:
        return len(edges(n_layer, n_head))
    # single-input-per-head variant: collapse q/k/v to one slot per head
    total = 0
    for v in dest_slots(n_layer, n_head):
        if v.endswith(".k") or v.endswith(".v"):
            continue                             # count each head's input once
        total += len(upstream_sources(v, n_layer, n_head))
    return total


def head_slot(v: str):
    """Parse a dest slot 'a{l}.h{h}.{s}' -> (l, h, s) or None if not an attn slot."""
    if v.endswith((".q", ".k", ".v")):
        body, s = v.rsplit(".", 1)
        l = int(body[1:].split(".")[0])
        h = int(body.split(".h")[1])
        return l, h, s
    return None
