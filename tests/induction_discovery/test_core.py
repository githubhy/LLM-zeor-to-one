"""G1 gate — H15 automated-discovery core invariants.

Run: PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 pytest tests/induction_discovery -q
"""
import numpy as np
import torch

from implementation.induction_discovery import oracle as O
from implementation.induction_discovery import discover as D
from implementation.induction_discovery.task import build_induction


# ---- pure-unit tests (no model) ------------------------------------------------

def test_prefix_mask_targets_follower():
    """For BOS+block*4 (L=3), the prefix mask must point a query to the position right
    AFTER an earlier copy of its own token, and never at BOS (index 0)."""
    L, R = 3, 4
    T = 1 + L * R                      # BOS + 12
    m = O._prefix_mask(T, L, R)
    # query at index 4 (repeat 2, token == index 1's token): earlier copy at 1, follower at 2
    assert m[4, 2] and not m[4, 1]
    # query at index 7 (repeat 3): earlier copies at 4 and 1 -> followers at 5 and 2
    assert m[7, 5] and m[7, 2]
    assert not m[:, 0].any()           # never attend to BOS
    assert not m.diagonal().any()      # never self


def test_prev_token_mask():
    m = O._prev_token_mask(5)
    assert all(m[i, i - 1] for i in range(1, 5))
    assert m.sum() == 4


def test_build_induction_is_minimal_pair():
    """clean and corrupt differ at exactly one index (the first-copy follower, index L),
    share the query token, and answer ids are read off that follower slot."""
    import types
    tok = types.SimpleNamespace(eos_token_id=50256)
    L = 6
    b = build_induction(tok, n_examples=4, seed=0, block_len=L)
    assert b.clean_ids.shape == b.corrupt_ids.shape
    assert b.clean_ids.shape[1] == 2 * L
    diff = (b.clean_ids != b.corrupt_ids)
    assert torch.equal(diff.sum(1), torch.full((4,), 1))       # exactly one differing token
    assert (diff.nonzero()[:, 1] == L).all()                   # ... at the follower index L
    assert torch.equal(b.clean_ids[:, -1], b.corrupt_ids[:, -1])  # same query token
    assert torch.equal(b.pos_ids, b.clean_ids[:, L])           # pos = clean follower
    assert torch.equal(b.neg_ids, b.corrupt_ids[:, L])         # neg = corrupt follower
    assert (b.last_idx == 2 * L - 1).all()


def test_build_induction_deterministic():
    import types
    tok = types.SimpleNamespace(eos_token_id=50256)
    a = build_induction(tok, n_examples=4, seed=1, block_len=8)
    c = build_induction(tok, n_examples=4, seed=1, block_len=8)
    d = build_induction(tok, n_examples=4, seed=2, block_len=8)
    assert torch.equal(a.clean_ids, c.clean_ids)
    assert not torch.equal(a.clean_ids, d.clean_ids)


def test_auroc_and_recovery_perfect_and_floor():
    """A method whose |scores| equal the oracle -> AUROC 1, recovery@k 1; a constant
    method -> AUROC 0.5."""
    prefix = {f"a0.h{h}": (1.0 if h < 3 else 0.0) for h in range(10)}
    oset = [f"a0.h{h}" for h in range(3)]
    perfect = {**{f"a0.h{h}": (1.0 if h < 3 else 0.0) for h in range(10)}, "m0": 0.0, "embed": 0.0}
    exact = perfect
    r = D.recovery_metrics(perfect, prefix, oset, exact)
    assert r["auroc_vs_oracle_set"] == 1.0
    assert r["recovery_at_k"] == 1.0
    flat = {**{f"a0.h{h}": 0.5 for h in range(10)}, "m0": 0.0, "embed": 0.0}
    assert abs(D._auroc(D.head_abs_scores(flat), set(oset)) - 0.5) < 1e-9


# ---- model-backed invariants ---------------------------------------------------

def test_eap_ig_m1_equals_eap_on_induction(model, induction_batch):
    """EAP-IG at m=1 == EAP (single interp point = clean gradient) on the induction task."""
    from implementation.eap_ig.attribution import score_eap, score_eap_ig
    s_eap = score_eap(model, induction_batch)
    s_ig1 = score_eap_ig(model, induction_batch, m_ig=1)
    md = max(abs(s_eap[u] - s_ig1[u]) for u in model.names)
    assert md < 1e-4, md


def test_faithfulness_anchors_on_induction(model, induction_batch):
    """Full circuit -> faithfulness 1; empty circuit -> 0 (Hanna anchors), on induction."""
    from implementation.eap_ig.faithfulness import baselines, faith_curve
    from implementation.eap_ig.attribution import score_nodes
    from implementation.eap_ig.config import AttrConfig
    b, bp = baselines(model, induction_batch)
    sc = score_nodes(model, induction_batch, AttrConfig(method="eap_ig", m_ig=5))
    fc = faith_curve(model, induction_batch, sc, [0, len(model.names)], b, bp)
    assert abs(float(fc[len(model.names)].mean()) - 1.0) < 1e-3      # full circuit
    assert abs(float(fc[0].mean()) - 0.0) < 1e-3                     # empty circuit


def test_induction_task_is_learnable(model, induction_batch):
    """The clean full-model logit-diff must strongly favor the induction continuation:
    a sanity anchor that GPT-2 actually does induction on this task."""
    b, bp = __import__("implementation.eap_ig.faithfulness", fromlist=["baselines"]).baselines(
        model, induction_batch)
    assert b > 5.0 and bp < 0.0        # clean predicts pos; corrupt flips toward neg


def test_oracle_recovers_canonical_cluster(eager):
    """The prefix-matching oracle must rank GPT-2-small's canonical induction heads
    (5.1/5.5/6.9/7.2/7.10) in the top handful."""
    model, tok = eager
    sc = O.per_head_scores(model, tok, n_examples=8, block_len=20, n_repeats=4, seed=0,
                           device="cpu")["prefix"]
    top8 = set(sorted(sc, key=lambda h: sc[h], reverse=True)[:8])
    canonical = {"a5.h5", "a7.h10", "a5.h1", "a6.h9", "a7.h2"}
    assert len(canonical & top8) >= 4, sorted(top8)
    assert max(sc.values()) > 5 * np.median(list(sc.values()))     # discriminative
