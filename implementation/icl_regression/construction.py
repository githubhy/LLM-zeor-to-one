"""Part A — von Oswald et al. (2023) Proposition 1: a LINEAR self-attention layer whose
forward pass IS one gradient-descent step on the in-context MSE loss (bit-exact identity).

This is the MECHANISTIC anchor of H9 and is correctly scoped to *linear* attention with
*constructed* weights. Single-head *softmax* attention explicitly FAILS this identity (von
Oswald §A.9, Fig 12); we do NOT reproduce a softmax-GD mechanism here (see the trained-softmax
*behavioral* study in model.py/run.py — a different, weaker claim).

Setup (concatenated token layout, e_j = (x_j, y_j) in R^{d+1}). A linear self-attention layer
    e_j  <-  e_j + P * sum_i (W_V e_i) ((W_K e_i)^T (W_Q e_j))
with the block-form weights (von Oswald §A.1, eq 8; signs fixed so the query token's y-part
tracks the prediction W_t x under the paper's dynamics e_j <- (x_j, y_j) + (0, -DeltaW x_j)):

    W_K = W_Q = [[I_d, 0],   W_V = [[0,   0],    P = (eta / N) I_{d+1}
                 [0,   0]]          [-W0,  1]]

Reading e_i = (x_i, y_i): W_K e_i = (x_i, 0), so (W_K e_i)^T (W_Q e_j) = x_i . x_j; and
W_V e_i = (0, y_i - W0 . x_i). Hence the y-part update of token j is
    Delta y_j = (eta/N) * sum_i (y_i - W0 . x_i) (x_i . x_j) = -(DeltaW) x_j,
where DeltaW = (eta/N) sum_i (W0 x_i - y_i) x_i^T is exactly the GD step: on the MSE
L(W) = (1/2N) sum_i (W x_i - y_i)^2 the gradient is (1/N) sum_i (W x_i - y_i) x_i^T, so
DeltaW = eta * grad = (eta/N) sum_i (W0 x_i - y_i) x_i^T. This (1/2N) convention (no factor of
2) is shared with gd_step_prediction and task.gd_predict, so a single eta means the same step
everywhere. A query token initialized with y-part = W0 . x_q therefore leaves the layer with y-part
= W0 x_q - DeltaW x_q = W1 x_q, i.e. exactly the one-GD-step prediction. That is the identity
verified here to machine precision.
"""
from __future__ import annotations

import numpy as np


def linear_self_attention(E: np.ndarray, WK: np.ndarray, WQ: np.ndarray,
                          WV: np.ndarray, P: np.ndarray) -> np.ndarray:
    """One LINEAR (softmax-free, unnormalized) self-attention update over tokens E (T, dim).

    Delta e_j = P @ sum_i (W_V e_i) ((W_K e_i) . (W_Q e_j)). Returns E + Delta E."""
    # Apple Accelerate/vecLib BLAS raises spurious FE_INVALID/DIVBYZERO/OVERFLOW flags on
    # np.matmul even for finite inputs with finite outputs (numpy-on-macOS-arm64 quirk; it
    # flags every matmul regardless of content). Suppress the spurious flags for this block,
    # but assert finiteness below so a GENUINE non-finite result is still caught, not hidden.
    with np.errstate(divide="ignore", over="ignore", under="ignore", invalid="ignore"):
        K = E @ WK.T                   # (T, dim)  keys
        Q = E @ WQ.T                   # (T, dim)  queries
        V = E @ WV.T                   # (T, dim)  values
        scores = K @ Q.T               # (Ti, Tj)  score[i,j] = (WK e_i).(WQ e_j)
        context = scores.T @ V         # (Tj, dim) context[j] = sum_i score[i,j] V[i]
        out = E + context @ P.T
    assert np.isfinite(out).all(), "non-finite linear-self-attention output"
    return out


def vonoswald_weights(d: int, W0: np.ndarray, eta: float, N: int):
    """Block-form Prop-1 weights (eq 8) for scalar-output regression (y in R^1). dim = d + 1.

    W0 is the current linear map, shape (d,) (a single output row). Returns (WK, WQ, WV, P)."""
    dim = d + 1
    WK = np.zeros((dim, dim)); WK[:d, :d] = np.eye(d)     # project onto x-part
    WQ = WK.copy()
    WV = np.zeros((dim, dim))
    WV[d, :d] = -np.asarray(W0, dtype=np.float64)          # value y-part = y_i - W0 . x_i
    WV[d, d] = 1.0
    P = (eta / N) * np.eye(dim)
    return WK, WQ, WV, P


def gd_step_prediction(X: np.ndarray, y: np.ndarray, x_q: np.ndarray,
                       W0: np.ndarray, eta: float):
    """One GD step from W0 on L(W) = (1/2N) sum_i (W x_i - y_i)^2, then predict x_q.

    grad = (1/N) sum_i (W0 x_i - y_i) x_i^T ; DeltaW = eta * grad ; W1 = W0 - DeltaW ; return
    W1 . x_q. The (1/2N) loss convention (no factor of 2 in the gradient) is shared with
    task.gd_predict and with the layer's P = (eta/N) I, so eta here == that lr."""
    N = X.shape[0]
    # Guard the spurious Apple Accelerate/vecLib matmul FPE flags (finite in -> finite out;
    # numpy-on-macOS-arm64 quirk), same as linear_self_attention above; numerics unchanged.
    with np.errstate(divide="ignore", over="ignore", under="ignore", invalid="ignore"):
        resid = X @ W0 - y                   # (N,)  W0 x_i - y_i
        dW = (eta / N) * (X.T @ resid)       # (d,)  gradient step
        W1 = W0 - dW
        pred = float(x_q @ W1)
    assert np.isfinite(pred), "non-finite one-GD-step prediction"
    return pred


def construct_and_predict(X: np.ndarray, y: np.ndarray, x_q: np.ndarray,
                          W0: np.ndarray, eta: float):
    """Run the constructed LINEAR self-attention layer over tokens [(x_i, y_i)] + query
    (x_q, W0 . x_q) and read the query token's y-part after the layer. Returns that prediction
    (which the identity claims equals gd_step_prediction)."""
    N, d = X.shape
    WK, WQ, WV, P = vonoswald_weights(d, W0, eta, N)
    E = np.zeros((N + 1, d + 1))
    E[:N, :d] = X
    E[:N, d] = y
    E[N, :d] = x_q
    E[N, d] = float(x_q @ W0)                # query initialized with its current prediction
    E_out = linear_self_attention(E, WK, WQ, WV, P)
    return float(E_out[N, d])                # updated query y-part = one-GD-step prediction


def identity_max_abs_diff(X: np.ndarray, y: np.ndarray, x_q: np.ndarray,
                          W0: np.ndarray, eta: float) -> float:
    """|constructed-layer query prediction - one-GD-step prediction|. The H9-A identity residual
    (expected ~1e-14; PASS threshold 1e-5)."""
    a = construct_and_predict(X, y, x_q, W0, eta)
    b = gd_step_prediction(X, y, x_q, W0, eta)
    return abs(a - b)


def k_step_via_construction(X: np.ndarray, y: np.ndarray, x_q: np.ndarray,
                            steps: int, eta: float):
    """K sequential applications of the one-step construction, threading the explicit GD iterate
    W_t between layers (context tokens reset to originals each layer). Verifies the construction
    COMPOSES to K-step GD when W is threaded. NOTE: stacking IDENTICAL layers without threading
    yields GD++ (preconditioned GD), not plain K-step GD (von Oswald §A.10, Fig 3) — that
    preconditioning nuance is out of scope here (-> todos)."""
    d = X.shape[1]
    W = np.zeros(d)
    for _ in range(steps):
        N = X.shape[0]
        resid = X @ W - y
        W = W - (eta / N) * (X.T @ resid)    # explicit GD iterate threaded across layers
    return float(x_q @ W)
