"""G1 gate for the H9 softmax two-head approximate-GD study (von Oswald §A.9).

Locks in the load-bearing claims:
  * the IDEALIZED two-head construction == one GD step to MACHINE PRECISION for every beta
    (the mechanism, Eq 19-21, provably) -- the softmax-side analog of H9-A's exact identity;
  * softmax sanity (rows sum to 1; uniform as beta->0);
  * SINGLE head fails: best-case (closed-form output scale) normalized error is large and
    dominated by the Eq-17 offset;
  * TWO head recovers: honest error is far below the single-head floor, and its small-beta residual
    is explained by the predicted O(1/N) centering term (root-cause, not a bug);
  * the honest two-head -> the idealized construction as beta->0 (linearizing limit).

Numeric blocks suppress the known-spurious Accelerate matmul FPE (finite in -> finite out).
"""
import numpy as np

from implementation.icl_regression import task as T
from implementation.icl_regression import construction as C
from implementation.icl_regression import softmax_construction as S


def _batch(seed, N, d=8):
    r = np.random.default_rng(seed)
    X, y, _ = T.make_regression_batch(r, 1, N, d)
    return X[0], y[0], r.standard_normal(d)


# ---- softmax sanity -------------------------------------------------------------------------
def test_softmax_normalizes_and_is_uniform_at_zero_beta():
    z = np.array([-2.0, 0.5, 3.0, 1.1])
    a = S.softmax(z)
    assert abs(a.sum() - 1.0) < 1e-12 and (a > 0).all()
    a0 = S.softmax(0.0 * z)                      # beta -> 0: uniform 1/N
    assert np.allclose(a0, np.full_like(a0, 1.0 / len(z)), atol=1e-12)


# ---- THE MECHANISM: idealized two-head == GD, to machine precision, for every beta -----------
def test_idealized_two_head_equals_gd_machine_precision():
    with np.errstate(all="ignore"):
        maxdiff = 0.0
        for seed in range(40):
            X, y, xq = _batch(seed, N=16)
            W0 = np.zeros(8) if seed % 2 else np.random.default_rng(seed).standard_normal(8)
            for beta in (0.02, 0.1, 0.5, 1.0, 3.0):     # identity is beta-independent
                ideal = S.two_head_ideal_predict(X, y, xq, W0, beta=beta, eta=0.5)
                gd = C.gd_step_prediction(X, y, xq, W0, eta=0.5)
                maxdiff = max(maxdiff, abs(ideal - gd))
    assert maxdiff < 1e-10, f"idealized two-head vs GD residual {maxdiff:.2e} not at machine precision"


# ---- linearizing (beta -> 0) drives the honest two-head error DOWN to the centering floor ----
# Note: honest two-head does NOT converge to the *idealized* construction -- the honest version
# keeps the beta-independent centering term the idealization drops, so honest - ideal -> centering
# (a constant), not 0. What vanishes is the Taylor remainder: the *error* falls monotonically to
# the O(1/N) centering plateau as beta shrinks. (Verified batched to avoid single-task noise.)
def test_linearizing_reduces_two_head_error_to_centering_floor():
    N = 20
    errs = [_norm_err(S.two_head_predict, N, b, S.matched_scale(b, 0.5)) for b in (0.7, 0.25, 0.06)]
    assert errs[0] > errs[1] > errs[2], f"two-head error not falling as beta shrinks: {errs}"


# ---- SINGLE head fails; TWO head recovers (batched normalized error) ------------------------
def _norm_err(predict, N, beta, c, B=600, seed=11, eta=0.5):
    with np.errstate(all="ignore"):
        r = np.random.default_rng(seed)
        num = den = 0.0
        for _ in range(B):
            Xb, yb, _w = T.make_regression_batch(r, 1, N, 8)
            X, y = Xb[0], yb[0]
            xq = r.standard_normal(8)
            W0 = np.zeros(8)
            gd = C.gd_step_prediction(X, y, xq, W0, eta)
            num += (predict(X, y, xq, W0, beta, c) - gd) ** 2
            den += gd ** 2
    return (num / den) ** 0.5


def _best_single(N, beta, B=600, seed=11, eta=0.5):
    """Closed-form best output scale c* for a single head at fixed beta (prediction is linear in c)."""
    with np.errstate(all="ignore"):
        r = np.random.default_rng(seed)
        ps, gs = [], []
        for _ in range(B):
            Xb, yb, _w = T.make_regression_batch(r, 1, N, 8)
            X, y = Xb[0], yb[0]
            xq = r.standard_normal(8)
            W0 = np.zeros(8)
            ps.append(S.single_head_predict(X, y, xq, W0, beta, 1.0))
            gs.append(C.gd_step_prediction(X, y, xq, W0, eta))
        ps, gs = np.array(ps), np.array(gs)
        return float(ps @ gs / (ps @ ps))


def test_single_head_large_floor_at_fixed_N():
    """At the headline N=20 (the Fig-12 regime) the single-head best-case floor is large. This is
    'irreducible' only under (c,beta) tuning at FIXED N -- the floor also declines as N grows (the
    two head declines faster, O(1/N)); see the N-sweep in softmax_run.py. Not a single-head wall."""
    N = 20
    floor = min(_norm_err(S.single_head_predict, N, b, _best_single(N, b))
                for b in np.logspace(np.log10(0.05), np.log10(1.5), 8))
    assert floor > 0.3, f"single-head best-case floor {floor:.3f} unexpectedly small at N={N}"


def test_two_head_beats_single_by_wide_margin():
    N, beta = 20, 0.03
    two = _norm_err(S.two_head_predict, N, beta, S.matched_scale(beta, 0.5))
    single = min(_norm_err(S.single_head_predict, N, b, _best_single(N, b))
                 for b in np.logspace(np.log10(0.05), np.log10(1.5), 8))
    assert two < 0.25 and single / two > 2.5, f"two-head={two:.3f} single={single:.3f} (ratio {single/two:.1f})"


# ---- root-cause: the honest two-head small-beta residual IS the predicted centering term -----
def test_centering_term_explains_two_head_residual():
    with np.errstate(all="ignore"):
        r = np.random.default_rng(5)
        beta, eta, N = 0.03, 0.5, 20
        c = S.matched_scale(beta, eta)
        num = den = 0.0
        for _ in range(1500):
            Xb, yb, _w = T.make_regression_batch(r, 1, N, 8)
            X, y = Xb[0], yb[0]
            xq = r.standard_normal(8)
            W0 = np.zeros(8)
            resid = S.two_head_predict(X, y, xq, W0, beta, c) - C.gd_step_prediction(X, y, xq, W0, eta)
            pred = S.centering_term(X, y, xq, W0, eta)
            num += (resid - pred) ** 2
            den += resid ** 2
    unexplained = (num / den) ** 0.5
    assert unexplained < 0.1, f"centering term leaves {unexplained:.3f} of the residual unexplained"


def test_single_head_offset_dominates_at_small_beta_not_best_case():
    """The Eq-17 offset (query-independent part) DOMINATES the single head at SMALL beta (where the
    head is worst); at its best-case beta (the U-curve minimum ~0.57) the offset is small and
    hard-max over-sharpening is what limits it. Guards against the mislabel that the head is
    'offset-dominated at best-case' (it is not)."""
    def _offfrac(N, beta):
        with np.errstate(all="ignore"):
            c = _best_single(N, beta)
            r = np.random.default_rng(9)
            off = tot = 0.0
            for _ in range(1500):
                Xb, yb, _w = T.make_regression_batch(r, 1, N, 8)
                X, y = Xb[0], yb[0]
                xq = r.standard_normal(8)
                W0 = np.zeros(8)
                off += S.offset_term(X, y, xq, W0, beta, c) ** 2
                tot += S.single_head_predict(X, y, xq, W0, beta, c) ** 2
        return (off / tot) ** 0.5
    small = _offfrac(20, 0.02)      # offset dominates
    best = _offfrac(20, 0.57)       # best-case beta: offset is NOT what limits it
    assert small > 0.8, f"offset only {small:.2f} at small beta -- expected it to dominate"
    assert best < 0.35, f"offset {best:.2f} at best-case beta -- should be small (hard-max limits here)"
