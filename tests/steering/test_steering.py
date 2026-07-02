"""Steering harness invariants (Track A3)."""
import os
import pytest
import torch

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@pytest.fixture(scope="session")
def steerer():
    from implementation.steering.core import Steerer, SteerConfig
    torch.manual_seed(0)
    return Steerer(SteerConfig(layer=6, device="cpu", seed=0))


def test_concept_tokens_single(steerer):
    assert len(steerer.pos_ids) >= 8 and len(steerer.neg_ids) >= 8


def test_diff_in_means_raises_sentiment(steerer):
    """Adding the diff-in-means vector should raise positive-sentiment success above 0."""
    vec = steerer.diff_in_means_vector()
    r0 = steerer.evaluate("diff_in_means", 0.0, vec=vec)
    r1 = steerer.evaluate("diff_in_means", 4.0, vec=vec)
    assert abs(r0["success"]) < 1e-4                  # alpha=0 => no change
    assert r1["success"] > 0.5 and r1["kl"] > r0["kl"]  # steering works, at a coherence cost


def test_evaluate_returns_per_prompt(steerer):
    r = steerer.evaluate("prompting", 0.0)
    assert len(r["success_per"]) == 10                # one per neutral prompt (for bootstrap CI)


def test_sae_clamp_setup_returns_feature(steerer):
    sae, fidx = steerer.sae_clamp_setup(steps=300)
    assert 0 <= fidx < sae.cfg.d_sae
