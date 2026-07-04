"""G1 gate for the H9 in-context-regression study.

Covers the load-bearing correctness claims: the von Oswald linear-attention = GD-step identity
(Part A, exact), the closed-form learners (OLS/ridge/GD), task determinism + token layout, the
agreement metric, and a trained-model smoke test. Pure-math tests are exact; the model test is
a tiny fast smoke.
"""
import warnings

import numpy as np
import pytest

from implementation.icl_regression import task as T
from implementation.icl_regression import construction as C


# ---- Part A: von Oswald construction = one GD step (exact) ---------------------------------
@pytest.mark.parametrize("W0kind", ["zero", "rand"])
def test_vonoswald_identity_machine_precision(W0kind):
    rng = np.random.default_rng(1)
    d, N = 8, 10
    X, y, _ = T.make_regression_batch(rng, 1, N, d)
    x_q = rng.standard_normal(d)
    W0 = np.zeros(d) if W0kind == "zero" else rng.standard_normal(d)
    with warnings.catch_warnings():
        warnings.simplefilter("error")           # spurious Accelerate FPE must stay suppressed
        diff = C.identity_max_abs_diff(X[0], y[0], x_q, W0=W0, eta=0.4)
    assert diff < 1e-10, f"identity residual {diff:.2e} not at machine precision"


def test_kstep_construction_equals_gd_predict():
    """K sequential constructed steps (threaded W) == task.gd_predict (shared 1/2N convention)."""
    rng = np.random.default_rng(2)
    d, N = 6, 12
    X, y, _ = T.make_regression_batch(rng, 1, N, d)
    x_q = rng.standard_normal(d)
    for K in (1, 3, 5, 10):
        a = C.k_step_via_construction(X[0], y[0], x_q, steps=K, eta=0.2)
        b = T.gd_predict(X[:1, :N], y[:1, :N], x_q[None], steps=K, lr=0.2)[0]
        assert abs(a - b) < 1e-9, f"K={K}: construction vs gd_predict diff {abs(a-b):.2e}"


def test_linear_self_attention_finite():
    rng = np.random.default_rng(3)
    d, N = 5, 8
    X, y, _ = T.make_regression_batch(rng, 1, N, d)
    WK, WQ, WV, P = C.vonoswald_weights(d, np.zeros(d), eta=0.3, N=N)
    E = np.zeros((N, d + 1)); E[:, :d] = X[0]; E[:, d] = y[0]
    out = C.linear_self_attention(E, WK, WQ, WV, P)
    assert np.isfinite(out).all()


# ---- Closed-form learners -----------------------------------------------------------------
def test_ols_recovers_w_noiseless():
    """Noiseless, n >= d: OLS recovers the teacher exactly."""
    rng = np.random.default_rng(4)
    d = 8
    X, y, w = T.make_regression_batch(rng, 16, 20, d)
    xq = rng.standard_normal((16, d))
    pred = T.ols_predict(X, y, xq)
    true = np.einsum("bd,bd->b", xq, w)
    assert np.max(np.abs(pred - true)) < 1e-8


def test_ridge_approaches_ols_as_lambda_small():
    rng = np.random.default_rng(5)
    d = 6
    X, y, _ = T.make_regression_batch(rng, 8, 20, d)
    xq = rng.standard_normal((8, d))
    ols = T.ols_predict(X, y, xq)
    ridge_small = T.ridge_predict(X, y, xq, lam=1e-8)
    assert np.max(np.abs(ridge_small - ols)) < 1e-4


def test_gd_converges_to_ols():
    rng = np.random.default_rng(6)
    d = 5
    X, y, _ = T.make_regression_batch(rng, 4, 20, d)
    xq = rng.standard_normal((4, d))
    ols = T.ols_predict(X, y, xq)
    gd = T.gd_predict(X, y, xq, steps=3000, lr=0.05)
    assert np.max(np.abs(gd - ols)) < 1e-4


# ---- Task determinism + token layout ------------------------------------------------------
def test_task_determinism():
    a = T.make_regression_batch(np.random.default_rng(0), 4, 10, 8)
    b = T.make_regression_batch(np.random.default_rng(0), 4, 10, 8)
    for u, v in zip(a, b):
        assert np.array_equal(u, v)


def test_interleave_layout():
    rng = np.random.default_rng(7)
    X, y, _ = T.make_regression_batch(rng, 2, 5, 3)
    tok, xpos = T.interleave(X, y)
    assert tok.shape == (2, 10, 4)
    assert list(xpos) == [0, 2, 4, 6, 8]
    # x-tokens (even) carry x in first d slots, zero in y-slot; y-tokens (odd) carry y in last slot
    assert np.allclose(tok[:, 0::2, :3], X)
    assert np.allclose(tok[:, 0::2, 3], 0.0)
    assert np.allclose(tok[:, 1::2, 3], y)
    assert np.allclose(tok[:, 1::2, :3], 0.0)


def test_normalized_spd_properties():
    a = np.array([1.0, 2.0, 3.0])
    assert T.normalized_spd(a, a) < 1e-12          # identical -> 0
    assert T.normalized_spd(a + 1.0, a) > 0         # different -> positive


# ---- Trained-model smoke (tiny/fast) ------------------------------------------------------
def test_model_trains_and_forward_shape():
    import torch
    from implementation.icl_regression.model import (ICLModelConfig, ICLTrainConfig,
                                                     ICLRegressionTransformer, train)
    torch.manual_seed(0)
    m = ICLRegressionTransformer(ICLModelConfig(x_dim=4, d_model=32, n_layers=1, n_heads=2,
                                                d_mlp=64, max_points=10, seed=0))
    tok = torch.zeros(2, 20, 5)
    assert m(tok).shape == (2, 20)                  # (B, T=2k); x-position read-out is in train()
    hist = train(m, ICLTrainConfig(steps=200, batch=32, lr=1e-3, warmup=50,
                                   eval_every=100, seed=0), device="cpu", log=lambda s: None)
    assert hist["train_mse"][-1] < hist["train_mse"][0]    # loss decreases
