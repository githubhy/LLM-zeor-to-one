import math

import torch

import sae_frontier as sf
from sae_frontier import metrics as M


def test_l0_counts():
    f = torch.tensor([[1.0, 0.0, 2.0], [0.0, 0.0, 3.0]])
    assert M.l0(f) == 1.5


def test_explained_variance_bounds():
    x = torch.randn(100, 8)
    assert abs(M.explained_variance(x, x) - 1.0) < 1e-6            # perfect
    zero = x.mean(dim=0, keepdim=True).expand_as(x)
    assert abs(M.explained_variance(x, zero)) < 1e-6              # mean predictor -> ~0


def test_normalized_mse_complements_ev():
    x = torch.randn(50, 5)
    xh = x + 0.1 * torch.randn_like(x)
    assert abs(M.normalized_mse(x, xh) - (1.0 - M.explained_variance(x, xh))) < 1e-9


def test_loss_recovered_formula():
    # orig=2, recon=2.5, zero=6 -> (6-2.5)/(6-2) = 0.875
    assert abs(M.loss_recovered(2.0, 2.5, 6.0) - 0.875) < 1e-9
    assert abs(M.loss_recovered(2.0, 2.0, 6.0) - 1.0) < 1e-9      # perfect recon
    assert abs(M.loss_recovered(2.0, 6.0, 6.0)) < 1e-9           # recon == zero -> 0


def test_feature_recovery_identity():
    G = torch.eye(8)[:, :5]                        # 5 orthonormal true atoms in R^8
    rec = M.feature_recovery(G.clone(), G.clone())
    assert rec["mmcs_true_to_learned"] > 0.999
    assert rec["frac_true_recovered_0.9"] == 1.0


def test_shrinkage_ratio_is_finite():
    """G1 smoke test: the shrinkage metric returns a finite, positive ratio for a
    trained SAE (the H2 mechanism itself is confirmed with proper statistics + a
    theory overlay in Phase 3, not asserted on an under-trained G1 model)."""
    from sae_frontier.config import SAEConfig, TrainConfig
    data = sf.generate_orthonormal(d_model=16, n_features=12, feature_prob=0.15, n_samples=2048, seed=0)
    s = sf.build_sae(SAEConfig(variant="relu", d_model=16, expansion=4, seed=0, l1_coeff=0.05))
    sf.train_sae(s, data.x, TrainConfig(steps=300, seed=0))
    r = M.shrinkage_ratio(s, data.x)
    assert not math.isnan(r) and r > 0 and math.isfinite(r)


def test_soft_threshold_prediction():
    """H2 mechanism as a clean closed form (survey Eq D-2): the ReLU+L1 per-feature
    objective (f* - a)^2 + lam*a is minimized at a* = max(f* - lam/2, 0) — soft
    thresholding — whereas an unpenalized objective is minimized at a* = f* (no shrink)."""
    for f_star, lam in [(1.0, 0.2), (0.5, 0.3), (2.0, 0.1)]:
        a = torch.linspace(0, f_star + 0.5, 20001)
        l1_loss = (f_star - a) ** 2 + lam * a
        a_l1 = a[l1_loss.argmin()].item()
        assert abs(a_l1 - max(f_star - lam / 2, 0.0)) < 1e-2      # soft-threshold shrink
        a_plain = a[((f_star - a) ** 2).argmin()].item()
        assert abs(a_plain - f_star) < 1e-2                      # no penalty -> no shrink
