"""Metrics, task generation, and statistics unit tests (no model needed except tasks)."""
import numpy as np
import torch

from implementation.eap_ig import metrics as M
from implementation.eap_ig import stats as S


def test_normalized_faithfulness_anchors():
    assert M.normalized_faithfulness(5.0, 5.0, 1.0) == 1.0   # m=b -> 1
    assert M.normalized_faithfulness(1.0, 5.0, 1.0) == 0.0   # m=b' -> 0
    assert abs(M.normalized_faithfulness(3.0, 5.0, 1.0) - 0.5) < 1e-9


def test_logit_diff_shapes():
    logits = torch.zeros(2, 4, 10)
    logits[0, 2, 7] = 3.0; logits[0, 2, 1] = 1.0
    li = torch.tensor([2, 2]); pos = torch.tensor([7, 0]); neg = torch.tensor([1, 0])
    d = M.logit_diff(logits, li, pos, neg)
    assert d.shape == (2,) and abs(d[0].item() - 2.0) < 1e-6


def test_wilson_ci_bounds():
    p, lo, hi = S.wilson_ci(8, 10)
    assert 0.0 <= lo <= p <= hi <= 1.0 and abs(p - 0.8) < 1e-9
    p0, lo0, hi0 = S.wilson_ci(0, 10)
    assert lo0 == 0.0 and hi0 > 0.0            # lower bound stays in [0,1] unlike Wald


def test_bootstrap_ci_covers_mean():
    v = np.arange(100.0)
    m, lo, hi = S.bootstrap_ci(v, n_boot=2000, seed=0)
    assert lo < m < hi and abs(m - 49.5) < 1e-9


def test_paired_test_detects_shift():
    rng = np.random.default_rng(0)
    a = rng.normal(1.0, 0.5, 40); b = a - 0.4          # a consistently > b
    r = S.paired_test(a, b)
    assert r["p_value"] < 0.01 and r["effect_size"] > 0 and r["mean_diff"] > 0


def test_correlate_perfect():
    x = {"a": 1.0, "b": 2.0, "c": 3.0}; y = {"a": 2.0, "b": 4.0, "c": 6.0}
    r = S.correlate(x, y)
    assert abs(r["pearson_r"] - 1.0) < 1e-9 and r["n"] == 3


def test_tasks_generate(model):
    from implementation.eap_ig.config import TaskConfig
    from implementation.eap_ig.tasks import build_task
    for task in ("ioi", "greater_than", "sva"):
        batch = build_task(model.tok, TaskConfig(task=task, n_examples=6, seed=0))
        assert batch.clean_ids.shape[0] == 6
        assert not torch.equal(batch.clean_ids, batch.corrupt_ids)
        m = batch.metric(model.model(batch.clean_ids, attention_mask=batch.attn_mask).logits)
        assert m.mean().item() > 0.0     # clean elicits the behavior
