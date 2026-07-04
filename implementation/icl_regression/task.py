"""In-context linear-regression task + closed-form classical learners (H9).

Task (Garg et al. 2022, §3, scaled): draw a teacher w ~ N(0, I_d) per task, inputs
x_i ~ N(0, I_d), targets y_i = w . x_i (+ noise in the noisy variant). The model sees the
in-context prompt and predicts y for a fresh query x. All generators are pure functions of an
explicit np.random.Generator (determinism; mirrors tiny_transformer/data.py's contract).

Two token layouts, each faithful to the source it serves:
- INTERLEAVED (Garg / Part B, `make_regression_batch` -> `interleave`): tokens
  [x_1, y_1, x_2, y_2, ..., x_k, y_k] in R^{d+1}; x-token = [x_i, 0], y-token = [0, y_i]. The
  model predicts y_i at each x-token position from the preceding pairs -> loss over all
  prefixes, causal.
- CONCATENATED (von Oswald / Part A, `construction.py`): a single token e_j = (x_j, y_j). Not
  built here; see construction.py.

Closed-form learners (fit on the first k in-context examples, predict the query):
min-norm OLS, ridge(lambda), and j-step batch gradient descent from w0=0. These are the
"explicit online learner" overlays H9 compares the model against.
"""
from __future__ import annotations

import contextlib

import numpy as np

X_SLOT = "x"   # token type tags (documentation only; layout is by nonzero slot)
Y_SLOT = "y"


@contextlib.contextmanager
def _quiet_blas():
    """Suppress spurious Apple Accelerate/vecLib FPE flags on matmul/lstsq/solve (finite
    inputs -> finite outputs; numpy-on-macOS-arm64 quirk). Correctness is covered by the G1
    tests (OLS recovers w; ridge->OLS; GD->OLS)."""
    with np.errstate(divide="ignore", over="ignore", under="ignore", invalid="ignore"):
        yield


def make_regression_batch(rng: np.random.Generator, batch: int, n_points: int, x_dim: int,
                          noise_std: float = 0.0):
    """Draw `batch` linear-regression tasks with `n_points` in-context (x, y) pairs.

    Returns (X, y, w):
      X : (batch, n_points, x_dim)  float64 inputs  x_i ~ N(0, I_d)
      y : (batch, n_points)         float64 targets y_i = w . x_i (+ N(0, noise_std^2))
      w : (batch, x_dim)            float64 teachers w ~ N(0, I_d)
    """
    w = rng.standard_normal((batch, x_dim))
    X = rng.standard_normal((batch, n_points, x_dim))
    y = np.einsum("bkd,bd->bk", X, w)
    if noise_std > 0:
        y = y + noise_std * rng.standard_normal((batch, n_points))
    return X, y, w


def interleave(X: np.ndarray, y: np.ndarray):
    """Interleaved token stream for the transformer (Part B).

    From X (B, k, d) and y (B, k) build tokens (B, 2k, d+1):
      position 2i   = x-token = [x_i, 0]      (model predicts y_i here)
      position 2i+1 = y-token = [0..0, y_i]
    Returns (tokens, x_positions) where x_positions indexes the query (x-token) slots whose
    read-out target is y. targets[:, i] = y[:, i] aligns with tokens[:, 2i].
    """
    B, k, d = X.shape
    tok = np.zeros((B, 2 * k, d + 1), dtype=np.float64)
    tok[:, 0::2, :d] = X          # x-tokens carry x in the first d slots
    tok[:, 1::2, d] = y           # y-tokens carry y in the last slot
    x_positions = np.arange(0, 2 * k, 2)
    return tok, x_positions


# --------------------------------------------------------------------------------------------
# Closed-form classical learners. Each fits on the first k examples (X_ctx, y_ctx) and predicts
# for query x_q. Vectorized over a batch of tasks.
# --------------------------------------------------------------------------------------------
def ols_predict(X_ctx: np.ndarray, y_ctx: np.ndarray, x_q: np.ndarray):
    """Minimum-norm ordinary least squares (Garg's optimal baseline). w_hat = X^+ y.

    X_ctx (B, k, d), y_ctx (B, k), x_q (B, d) -> yhat (B,). k may be < d (under-determined:
    lstsq returns the minimum-norm solution)."""
    B = X_ctx.shape[0]
    yhat = np.empty(B)
    with _quiet_blas():
        for b in range(B):
            w_hat, *_ = np.linalg.lstsq(X_ctx[b], y_ctx[b], rcond=None)
            yhat[b] = x_q[b] @ w_hat
    return yhat


def ridge_predict(X_ctx: np.ndarray, y_ctx: np.ndarray, x_q: np.ndarray, lam: float):
    """Ridge regression w_hat = (X^T X + lam I)^-1 X^T y. Bayes-optimal for noisy targets at
    lam = sigma^2 / tau^2 (Akyürek 2023 min-Bayes-risk ridge)."""
    B, k, d = X_ctx.shape
    yhat = np.empty(B)
    eye = np.eye(d)
    with _quiet_blas():
        for b in range(B):
            Xb = X_ctx[b]
            w_hat = np.linalg.solve(Xb.T @ Xb + lam * eye, Xb.T @ y_ctx[b])
            yhat[b] = x_q[b] @ w_hat
    return yhat


def gd_predict(X_ctx: np.ndarray, y_ctx: np.ndarray, x_q: np.ndarray, steps: int, lr: float):
    """`steps`-step batch gradient descent on the in-context MSE from w0 = 0 (the von Oswald
    comparator). Loss L(w) = (1/2k) ||X w - y||^2, grad = (1/k) X^T (X w - y). This (1/2k)
    convention (no factor of 2 in the gradient) matches construction.py's `eta`, so
    gd_predict(lr=eta) equals construction.k_step_via_construction(eta) exactly."""
    B, k, d = X_ctx.shape
    w = np.zeros((B, d))
    for _ in range(steps):
        resid = np.einsum("bkd,bd->bk", X_ctx, w) - y_ctx          # (B, k)
        grad = (1.0 / k) * np.einsum("bkd,bk->bd", X_ctx, resid)   # (B, d)
        w = w - lr * grad
    return np.einsum("bd,bd->b", x_q, w)


def normalized_spd(pred_a: np.ndarray, pred_b: np.ndarray) -> float:
    """Akyürek-style normalized squared prediction difference between two predictors:
    E[(a - b)^2] / E[b^2]. 0 = identical predictions; the H9 agreement metric (lower = the
    model tracks learner b more closely). b is the reference (classical learner)."""
    num = float(np.mean((pred_a - pred_b) ** 2))
    den = float(np.mean(pred_b ** 2))
    return num / (den + 1e-12)
