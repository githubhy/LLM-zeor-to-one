import pytest
import torch

import sae_frontier as sf
from sae_frontier.config import SAEConfig


VARIANTS = sf.VARIANTS


def _sae(variant, **kw):
    kw.setdefault("k", 8)
    cfg = SAEConfig(variant=variant, d_model=16, expansion=4, seed=0, dtype="float64", **kw)
    return sf.build_sae(cfg), cfg


@pytest.mark.parametrize("variant", VARIANTS)
def test_forward_shapes(variant):
    sae, cfg = _sae(variant)
    x = torch.randn(32, cfg.d_model, dtype=torch.float64)
    x_hat, telem = sae(x)
    assert x_hat.shape == x.shape
    assert telem["f"].shape == (32, cfg.d_sae)
    assert telem["l0"] >= 0


@pytest.mark.parametrize("variant", VARIANTS)
def test_encode_nonnegative(variant):
    sae, cfg = _sae(variant)
    x = torch.randn(32, cfg.d_model, dtype=torch.float64)
    assert sae.encode(x).min().item() >= -1e-9


@pytest.mark.parametrize("variant", VARIANTS)
def test_decode_zero_is_bias(variant):
    sae, cfg = _sae(variant)
    z = torch.zeros(4, cfg.d_sae, dtype=torch.float64)
    assert torch.allclose(sae.decode(z), sae.b_dec.expand(4, -1), atol=1e-10)


@pytest.mark.parametrize("variant", VARIANTS)
def test_loss_returns_scalar_and_parts(variant):
    sae, cfg = _sae(variant)
    x = torch.randn(32, cfg.d_model, dtype=torch.float64)
    total, parts = sae.loss(x)
    assert total.ndim == 0 and torch.isfinite(total)
    assert "recon" in parts and parts["recon"] >= 0


def test_topk_exact_sparsity():
    sae, cfg = _sae("topk", k=5)
    x = torch.randn(64, cfg.d_model, dtype=torch.float64)
    active = (sae.encode(x) > 0).sum(dim=1)
    assert active.max().item() <= 5


def test_jumprelu_passthrough_no_shrink():
    sae, cfg = _sae("jumprelu")
    x = torch.randn(64, cfg.d_model, dtype=torch.float64)
    pre = torch.relu(sae.preactivation(x))
    f = sae.encode(x)
    on = pre > sae.theta
    assert torch.allclose(f[on], pre[on], atol=1e-12)      # survivors unshrunk
    assert f[~on].abs().max().item() < 1e-12               # below-threshold zeroed


def test_gated_gate_closes():
    sae, cfg = _sae("gated")
    x = torch.randn(64, cfg.d_model, dtype=torch.float64)
    pi_gate, _ = sae._paths(x)
    f = sae.encode(x)
    assert f[pi_gate <= 0].abs().max().item() < 1e-12


@pytest.mark.parametrize("bad", [
    dict(variant="nope", d_model=16),
    dict(variant="topk", d_model=16, expansion=1, k=100),   # k > d_sae
    dict(variant="relu", d_model=0),
    dict(variant="relu", d_model=16, l1_coeff=-1.0),
])
def test_config_validation(bad):
    with pytest.raises(ValueError):
        SAEConfig(**bad)


@pytest.mark.parametrize("variant", VARIANTS)
def test_gradients_flow(variant):
    """Every trainable parameter must receive a gradient (catches dead STE / detached paths)."""
    sae, cfg = _sae(variant)
    x = torch.randn(48, cfg.d_model, dtype=torch.float64)
    total, _ = sae.loss(x)
    total.backward()
    for name, p in sae.named_parameters():
        assert p.grad is not None, f"{variant}:{name} got no gradient"
        assert torch.isfinite(p.grad).all(), f"{variant}:{name} non-finite grad"
