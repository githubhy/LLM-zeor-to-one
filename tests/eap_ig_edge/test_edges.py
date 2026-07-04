"""Edge-graph structural gate (Hanna et al. 2024 q/k/v-split, 32,491 edges for GPT-2-small).

Locks in the foundation of the edge-level EAP build (plan 2026-07-04-eap-ig-edge-level). The
gradient surface, scorer, recursive edge-ablation, and greedy search build on this graph.
"""
from implementation.eap_ig import edges as E

NL, NH = 12, 12   # GPT-2-small


def test_source_and_dest_counts():
    assert len(E.source_nodes(NL, NH)) == 157         # embed + 144 heads + 12 MLPs
    assert len(E.dest_slots(NL, NH)) == 445           # 144*3 q/k/v + 12 MLP.in + 1 logits


def test_edge_count_32491_with_split():
    assert E.edge_count(NL, NH, split_qkv=True) == 32491
    assert len(E.edges(NL, NH)) == 32491


def test_edge_count_11611_without_split():
    # the q/k/v split is load-bearing: collapsing to one input per head gives 11,611
    assert E.edge_count(NL, NH, split_qkv=False) == 11611


def test_upstream_causal_counts():
    assert len(E.upstream_sources("a0.h0.q", NL, NH)) == 1        # embed only
    assert len(E.upstream_sources("a5.h3.q", NL, NH)) == 1 + 13 * 5   # 66
    assert len(E.upstream_sources("m0.in", NL, NH)) == 13
    assert len(E.upstream_sources("m11.in", NL, NH)) == 13 * 12       # 156
    assert len(E.upstream_sources("logits", NL, NH)) == 157


def test_qkv_slots_share_upstream():
    # q, k, v of the same head read the same residual point -> identical upstream set
    q = E.upstream_sources("a5.h3.q", NL, NH)
    k = E.upstream_sources("a5.h3.k", NL, NH)
    v = E.upstream_sources("a5.h3.v", NL, NH)
    assert q == k == v


def test_no_intra_layer_head_to_head_edges():
    bad = [(u, v) for u, v in E.edges(NL, NH)
           if u.startswith("a") and v.startswith("a")
           and u[1:].split(".")[0] == v[1:].split(".")[0]]
    assert bad == []


def test_head_slot_parse():
    assert E.head_slot("a5.h3.q") == (5, 3, "q")
    assert E.head_slot("m6.in") is None
    assert E.head_slot("logits") is None
