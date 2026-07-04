"""H9 follow-on — von Oswald et al. (2023) §A.9: softmax self-attention vs the one-GD-step update.

The MECHANISM (Eq 14-21 of the source, read from
`download/vonoswald-transformers-icl-gradient-descent-2023.pdf`):

A softmax attention weight Taylor-expands (their Eq 16) as
    softmax(K^T q_j)_i = e^{x_i . W_KQ x_j} / sum_i' e^{x_i' . W_KQ x_j}
                      ~= (1 + x_i . W_KQ x_j) / sum_i' (1 + x_i' . W_KQ x_j).
The leading `1` is a query-independent ADDITIVE OFFSET (their Eq 17). A SINGLE head is stuck with
it, so it cannot match the linear-attention GD construction (their Fig 12a). TWO heads with
sign-reversed score matrices (W_{1,KQ} = -W_{2,KQ}) and opposite output signs (P_2 V_2 = -P_1 V_1)
subtract the two `1`s away (their Eq 19-20), leaving the pure linear score `2 beta x_i . x_j`
(their Eq 21) -> the GD construction, EXACTLY under their stated assumption that `PV subsumes the
softmax denominator and is the same for each head` (equal-denominator idealization).

This module reproduces that as two objects, mirroring H9-A (construction.py):
  * `two_head_ideal_predict` -- the IDEALIZED construction (Eq 16 linearization + equal-denominator
    assumption). Equals `construction.gd_step_prediction` to MACHINE PRECISION for every beta. The
    mechanism, provably (analog of H9-A's 1e-15 identity).
  * `single_head_predict` / `two_head_predict` -- the HONEST full softmax (real exp, real per-head
    denominators). The single head keeps an O(1) offset (Eq 17); the honest two head cancels it to a
    small O(1/N) CENTERING FLOOR `(eta/N) s_bar (sum_i v_i)` -- exactly the unequal-denominator term
    the paper's assumption idealizes away -> reproduces Fig 12's "good but not as precise as linear".

Scope note (a deliberate, documented conformance choice): the softmax runs over the N CONTEXT
tokens (the sum in their Eq 14), isolating the Eq-16 offset mechanism. A full-sequence softmax would
add a query-self term orthogonal to the offset argument; that behavioral variant is the (optional)
trained leg, not this constructive core.

All functions are pure functions of their inputs (determinism) and use the concatenated token layout
e_j = (x_j, y_j) with value v_i = y_i - W0 . x_i, sharing construction.gd_step_prediction's (1/2N)
loss convention so a single `eta` means the same GD step everywhere.
"""
from __future__ import annotations

import contextlib

import numpy as np

from . import construction as C


@contextlib.contextmanager
def _quiet_blas():
    """Suppress spurious Apple Accelerate/vecLib FPE flags on matmul (finite in -> finite out;
    numpy-on-macOS-arm64 quirk). Finiteness is asserted at each public entry point."""
    with np.errstate(divide="ignore", over="ignore", under="ignore", invalid="ignore"):
        yield


def softmax(z: np.ndarray) -> np.ndarray:
    """Numerically stable softmax over the last axis (subtract max). Rows sum to 1."""
    z = np.asarray(z, dtype=np.float64)
    zmax = z.max(axis=-1, keepdims=True)
    e = np.exp(z - zmax)
    return e / e.sum(axis=-1, keepdims=True)


def _scores(X: np.ndarray, x_q: np.ndarray) -> np.ndarray:
    """Raw dot-product scores s_i = x_i . x_q over the N context tokens (the W_KQ = I construction,
    matching construction.vonoswald_weights). Shape (N,)."""
    with _quiet_blas():
        return X @ x_q


def _values(X: np.ndarray, y: np.ndarray, W0: np.ndarray) -> np.ndarray:
    """Value y-part v_i = y_i - W0 . x_i (construction.py's W_V). Shape (N,)."""
    with _quiet_blas():
        return y - X @ W0


def single_head_predict(X, y, x_q, W0, beta, c):
    """One HONEST softmax head's query prediction: W0.x_q + c * sum_i softmax(beta s)_i v_i.

    beta = score scale (inverse temperature); c = output scale (last diag of P W_V). This is the
    construction of Fig 12a -- it carries the irreducible Eq-17 offset and cannot match GD."""
    s = _scores(X, x_q)
    v = _values(X, y, W0)
    alpha = softmax(beta * s)
    out = float(W0 @ x_q) + c * float(alpha @ v)
    assert np.isfinite(out), "non-finite single-head prediction"
    return out


def two_head_predict(X, y, x_q, W0, beta, c):
    """Two HONEST softmax heads with sign-reversed scores (beta, -beta) and opposite output signs
    (+c, -c): W0.x_q + c[ sum_i softmax(beta s)_i v_i - sum_i softmax(-beta s)_i v_i ].

    This is Eq 18 with the paper's P_2 V_2 = -P_1 V_1. The two `1`-offsets cancel; a small
    O(1/N) centering floor (unequal per-head denominators) remains -- see `centering_term`."""
    s = _scores(X, x_q)
    v = _values(X, y, W0)
    diff = softmax(beta * s) - softmax(-beta * s)
    out = float(W0 @ x_q) + c * float(diff @ v)
    assert np.isfinite(out), "non-finite two-head prediction"
    return out


def two_head_ideal_predict(X, y, x_q, W0, beta, eta):
    """The IDEALIZED two-head construction: Eq-16 linearization (e^z -> 1+z) with the paper's
    equal-denominator assumption (both heads normalized by N). Then the head difference is

        [(1 + beta s_i)/N] - [(1 - beta s_i)/N] = 2 beta s_i / N   (exactly),

    and with the matched output scale c = eta/(2 beta) the update is (eta/N) sum_i s_i v_i =
    the one-GD-step update. Hence this EQUALS construction.gd_step_prediction to machine precision
    FOR EVERY beta (the identity is beta-independent). Reproduces Eq 19-21 as executable math."""
    s = _scores(X, x_q)
    v = _values(X, y, W0)
    N = len(y)
    c = eta / (2.0 * beta)
    a_plus = (1.0 + beta * s) / N
    a_minus = (1.0 - beta * s) / N
    out = float(W0 @ x_q) + c * float((a_plus - a_minus) @ v)
    assert np.isfinite(out), "non-finite idealized two-head prediction"
    return out


def matched_scale(beta: float, eta: float) -> float:
    """The two-head output scale c that maps the linear head-difference onto the eta-GD step:
    2 c beta = eta  =>  c = eta / (2 beta)."""
    return eta / (2.0 * beta)


# --------------------------------------------------------------------------------------------
# Diagnostics that pin the mechanism to the source's Eq 17 (offset) and the honest-vs-ideal gap.
# --------------------------------------------------------------------------------------------
def offset_term(X, y, x_q, W0, beta, c) -> float:
    """The Eq-17 additive offset a single head cannot remove: the query-INDEPENDENT part of its
    update, c * (1/Z) sum_i v_i with Z = sum_i e^{beta s_i}. (Linearize softmax numerator to
    1 + beta s: the `1` contributes this constant.) Its magnitude vs the GD signal is why the
    single head fails."""
    s = _scores(X, x_q)
    v = _values(X, y, W0)
    Z = float(np.exp(beta * s - (beta * s).max()).sum()) * np.exp((beta * s).max())
    return c * float(v.sum()) / Z


def centering_term(X, y, x_q, W0, eta) -> float:
    """The predicted O(1/N) honest-two-head residual (the unequal-denominator effect the paper's
    equal-denominator assumption drops): -(eta/N) * s_bar * sum_i v_i, with s_bar = mean_i s_i.

    Derived (small-beta) from softmax(+/-beta s)_i ~= (1 +/- beta(s_i - s_bar))/N, so the honest
    head-difference is 2 beta (s_i - s_bar)/N instead of the ideal 2 beta s_i/N; the extra
    -2 beta s_bar/N, times c = eta/(2 beta), times sum_i v_i, gives this beta-INDEPENDENT term."""
    s = _scores(X, x_q)
    v = _values(X, y, W0)
    N = len(y)
    return -(eta / N) * float(s.mean()) * float(v.sum())
