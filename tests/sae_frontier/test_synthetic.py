import torch

import sae_frontier as sf
from sae_frontier.config import SyntheticConfig


def test_shapes_and_superposition():
    cfg = SyntheticConfig(n_features=100, d_model=20, n_samples=1000, seed=1)
    data = sf.generate(cfg)
    assert data.x.shape == (1000, 20)
    assert data.true_features.shape == (20, 100)
    assert data.codes.shape == (1000, 100)
    assert cfg.d_model < cfg.n_features  # superposition regime


def test_true_features_unit_norm():
    data = sf.generate(SyntheticConfig(n_features=64, d_model=16, seed=2))
    norms = data.true_features.norm(dim=0)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)


def test_sparsity_matches_feature_prob():
    cfg = SyntheticConfig(n_features=200, d_model=16, feature_prob=0.1, n_samples=4000, seed=3)
    data = sf.generate(cfg)
    empirical = (data.codes > 0).float().mean().item()
    assert abs(empirical - cfg.feature_prob) < 0.02


def test_x_equals_codes_times_dict():
    cfg = SyntheticConfig(n_features=50, d_model=12, seed=4)
    data = sf.generate(cfg)
    recon = data.codes @ data.true_features.t()
    assert torch.allclose(recon, data.x, atol=1e-5)


def test_deterministic():
    a = sf.generate(SyntheticConfig(seed=7))
    b = sf.generate(SyntheticConfig(seed=7))
    assert torch.equal(a.x, b.x)
