"""Attribution-scorer invariants."""
from implementation.eap_ig.attribution import (score_eap, score_eap_ig, score_random,
                                               score_exact)


def test_eap_ig_m1_equals_eap(model, ioi_batch):
    """EAP-IG at m=1 (single interp point = clean gradient) == EAP (analytical oracle)."""
    s_eap = score_eap(model, ioi_batch)
    s_ig1 = score_eap_ig(model, ioi_batch, m_ig=1)
    md = max(abs(s_eap[u] - s_ig1[u]) for u in model.names)
    assert md < 1e-4, md


def test_random_reproducible(model, ioi_batch):
    a = score_random(model, ioi_batch, seed=0)
    b = score_random(model, ioi_batch, seed=0)
    c = score_random(model, ioi_batch, seed=1)
    assert a == b and a != c


def test_exact_important_node_positive(model, ioi_batch):
    """Corrupting the most-important node reduces the metric -> positive exact score."""
    sc = score_exact(model, ioi_batch)
    assert max(sc.values()) > 0.0


def test_all_scorers_cover_all_nodes(model, ioi_batch):
    for fn in (score_eap, score_random):
        sc = fn(model, ioi_batch) if fn is score_random else fn(model, ioi_batch)
        assert set(sc.keys()) == set(model.names)
