import pytest
import torch

import sae_frontier as sf
from sae_frontier import registry
from sae_frontier.config import SAEConfig, SyntheticConfig


def test_all_candidates_build_through_registry():
    """P2-1: every candidate resolves through the single registry entry point."""
    for v in registry.CANDIDATES:
        s = registry.build_candidate(SAEConfig(variant=v, d_model=16))
        assert isinstance(s, sf.SAE)
    assert set(registry.CANDIDATES) == set(sf.VARIANTS)


def test_unknown_candidate_rejected():
    import types
    with pytest.raises(KeyError):
        registry.build_candidate(types.SimpleNamespace(variant="not-a-variant"))


def test_metric_registry_complete():
    for key in ("l0", "explained_variance", "normalized_mse", "loss_recovered",
                "feature_recovery", "shrinkage_ratio"):
        assert key in registry.METRICS and callable(registry.METRICS[key])


def test_data_registry_synthetic():
    data = registry.get_data("synthetic", SyntheticConfig(n_features=32, d_model=8, seed=0))
    assert data.x.shape[1] == 8


def test_data_registry_unknown():
    with pytest.raises(KeyError):
        registry.get_data("nope", None)
