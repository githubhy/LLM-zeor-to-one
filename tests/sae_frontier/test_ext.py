"""Track-C extension candidates: BatchTopK, Matryoshka, AdaptiveJumpReLU.
Includes the bug-2026-07-02-01 regression: the STE threshold must respond to the sparsity
penalty (the fixed-bandwidth JumpReLU was gradient-starved / bandwidth-conditional)."""
import torch

from implementation.sae_frontier.config import SyntheticConfig, TrainConfig
from implementation.sae_frontier.synthetic import generate
from implementation.sae_frontier.saes_ext import build_ext
from implementation.sae_frontier.train import train_sae


def _data(seed=0, fp=0.1, n=2000, d=16):
    return generate(SyntheticConfig(n_features=64, d_model=d, feature_prob=fp,
                                    n_samples=n, seed=seed))


def test_batchtopk_avg_l0_near_k():
    d = _data(n=512)
    sae = build_ext("batchtopk", d_model=16, seed=0, k=8)
    f = sae.encode(d.x)
    avg_l0 = (f > 0).sum(1).float().mean().item()
    assert 6.0 <= avg_l0 <= 10.0, avg_l0            # BatchTopK averages k across the batch


def test_batchtopk_variable_per_example_sparsity():
    """The point of BatchTopK: per-example L0 VARIES (unlike exact-k TopK)."""
    d = _data(n=512)
    sae = build_ext("batchtopk", d_model=16, seed=0, k=8)
    per_ex = (sae.encode(d.x) > 0).sum(1).float()
    assert per_ex.std().item() > 0.0                # not a constant k per row


def test_matryoshka_nested_prefix_losses():
    d = _data(n=512)
    sae = build_ext("matryoshka", d_model=16, seed=0, k=8)
    _, parts = sae.loss(d.x)
    prefixes = [p for p in parts if p.startswith("recon_")]
    assert len(prefixes) == 3                       # nested reconstruction at 3 prefix sizes


def test_adaptive_jumprelu_theta_responds_to_sparsity():
    """Bug 2026-07-02-01 regression: L0 must drop under a stronger sparsity penalty
    (the fixed-bandwidth STE was gradient-starved on O(1) activations and never sparsified)."""
    d = _data(n=2000)
    l0s = []
    for l1 in (0.02, 0.5):
        sae = build_ext("adaptive_jumprelu", d_model=16, seed=0, k=8, l1_coeff=l1)
        train_sae(sae, d.x, TrainConfig(steps=1500, seed=0))   # needs enough steps for theta to move
        l0s.append((sae.encode(d.x) > 0).sum(1).float().mean().item())
    # theta is NOT gradient-starved (the bug): stronger penalty gives meaningfully lower L0
    assert l0s[0] - l0s[1] > 1.0, l0s
