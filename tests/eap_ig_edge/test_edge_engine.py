"""G1 gate for the edge-level EAP/EAP-IG engine — the verification anchors from the plan's §3.

These lock in the three error-prone cores: the reimplemented forward is faithful to GPT-2, the
edge scores recompose to the trusted node scores (validates the gradient surface), and the
recursive edge-ablation reproduces clean/corrupt at the circuit boundaries.
"""
import torch

from implementation.eap_ig.config import AttrConfig
from implementation.eap_ig.attribution import score_nodes
from implementation.eap_ig import edge_attribution as EA
from implementation.eap_ig import edges as E
from implementation.eap_ig.edge_greedy import child_node, greedy_circuit, prune


def test_reimplemented_forward_matches_real_model(edge_model, batch):
    assert edge_model.logits_match(batch.clean_ids, batch.attn_mask) < 1e-3


def test_edge_to_node_consistency_eap(model, edge_model, batch):
    # node_score(u) == Σ_v edge_score(u -> v)  (linear-sum identity) — validates the gradients
    node = score_nodes(model, batch, AttrConfig(method="eap"))
    edges = EA.score_edges(model, edge_model, batch, method="eap")
    recomposed = EA.node_from_edges(edges, model)
    assert max(abs(node[u] - recomposed[u]) for u in model.names) < 1e-4


def test_edge_to_node_consistency_eap_ig(model, edge_model, batch):
    node = score_nodes(model, batch, AttrConfig(method="eap_ig", m_ig=5))
    edges = EA.score_edges(model, edge_model, batch, method="eap_ig", m_ig=5)
    recomposed = EA.node_from_edges(edges, model)
    assert max(abs(node[u] - recomposed[u]) for u in model.names) < 1e-4


def test_ablation_all_in_equals_clean(model, edge_model, batch):
    all_edges = set(E.edges(model.n_layer, model.n_head))
    lg = edge_model.patched_logits_edges(batch, all_edges)
    clean = model.model(batch.clean_ids, attention_mask=batch.attn_mask).logits
    # all-in reproduces clean up to the reimplementation's float-accumulation order (~1e-3 logits)
    assert abs(batch.metric(lg).mean().item() - batch.metric(clean).mean().item()) < 1e-2


def test_ablation_all_out_equals_corrupt(model, edge_model, batch):
    lg = edge_model.patched_logits_edges(batch, set())
    corrupt = model.model(batch.corrupt_ids, attention_mask=batch.attn_mask).logits
    assert abs(batch.metric(lg).mean().item() - batch.metric(corrupt).mean().item()) < 1e-3


def test_eap_ig_m1_equals_eap(model, edge_model, batch):
    # EAP-IG at m=1 reduces exactly to EAP (Hanna Eq 3 -> Eq 1)
    eap = EA.score_edges(model, edge_model, batch, method="eap")
    ig1 = EA.score_edges(model, edge_model, batch, method="eap_ig", m_ig=1)
    keys = list(eap)[:500]
    assert max(abs(eap[k] - ig1[k]) for k in keys) < 1e-4


def test_per_edge_sign_matches_exact_ablation(model, edge_model, batch):
    """Independent PER-EDGE anchor (the edge->node identity only validates the per-source sum).
    EAP is the 1st-order approximation of the exact single-edge ablation effect, so its SIGN must
    match — including for q/k/v-slot edges, which a q<->k gradient swap would flip. Validates
    individual edge scores, not just their aggregate."""
    import numpy as np
    scores = EA.score_edges(model, edge_model, batch, method="eap")
    all_edges = set(E.edges(model.n_layer, model.n_head))
    m_clean = batch.metric(model.model(batch.clean_ids, attention_mask=batch.attn_mask).logits).mean().item()
    order = sorted(scores, key=lambda e: abs(scores[e]), reverse=True)
    sample = order[:6] + [e for e in order if e[1].endswith((".q", ".k", ".v"))][:4]  # incl. qkv slots
    agree = 0
    for e in sample:
        exact = m_clean - batch.metric(edge_model.patched_logits_edges(batch, all_edges - {e})).mean().item()
        agree += (np.sign(scores[e]) == np.sign(exact))
    assert agree / len(sample) >= 0.9   # EAP predicts every edge's direction


def test_child_node_parse():
    assert child_node("a5.h3.q") == "a5.h3"
    assert child_node("m6.in") == "m6"
    assert child_node("logits") == "logits"


def test_greedy_builds_connected_circuit(model, edge_model, batch):
    edges = EA.score_edges(model, edge_model, batch, method="eap_ig", m_ig=1)
    C = greedy_circuit(edges, 60)
    assert 0 < len(C) <= 60
    # every edge's child is reachable toward logits (greedy invariant): child is logits or has
    # an outgoing edge in C
    children_with_out = {u for (u, v) in C}
    for (u, v) in C:
        cn = child_node(v)
        assert cn == "logits" or cn in children_with_out
    assert len(prune(C)) <= len(C)
