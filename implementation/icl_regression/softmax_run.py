"""H9 softmax two-head approximate-GD study (von Oswald §A.9).

Reproduces §A.9's single-vs-two-head contrast constructively (deterministic; no training):
  * the IDEALIZED two-head construction reproduces one GD step to machine precision (mechanism);
  * a SINGLE honest softmax head has a large normalized-error floor at fixed N (irreducible under
    (c,beta) tuning) -- offset-dominated at small beta (Eq 17), hard-max-limited at its best-case;
  * TWO honest sign-reversed heads cut that error several-fold, down to a small O(1/N) CENTERING
    floor (the unequal-denominator term the paper's assumption idealizes away) -- "good but not as
    precise as linear" (Fig 12). BOTH floors decline with context length N (the single head's more
    slowly, crossing the 0.30 mark near N~=160-240); the two-head's O(1/N) rate is what makes the
    single/two ratio WIDEN with N -- a convergence-rate advantage, not a single-head wall.

Run:  PYTHONPATH=$PWD python3 -m implementation.icl_regression.softmax_run
Emits artifacts/icl-regression-softmax/summary.json (+ per-example arrays for the figure).
"""
from __future__ import annotations

import platform

import numpy as np

from implementation.tiny_transformer.utils import save_json
from implementation.icl_regression import task as T
from implementation.icl_regression import construction as C
from implementation.icl_regression import softmax_construction as S

STUDY = "icl-regression-softmax"
ART = "artifacts/icl-regression-softmax"

D = 8
ETA = 0.5
N_HEADLINE = 20
BETAS = tuple(np.logspace(np.log10(0.02), np.log10(2.0), 12))
N_GRID = (10, 20, 40, 80, 160)
B_SWEEP = 2000        # tasks per (beta) / (N) cell
B_DIAG = 2000         # tasks for the verification diagnostics
SEED = 1
N_BOOT = 10000


def _tasks(seed, N, B):
    """A fixed batch of B regression tasks (W0 = 0): arrays X (B,N,d), y (B,N), xq (B,d)."""
    r = np.random.default_rng(seed)
    X, y, _w = T.make_regression_batch(r, B, N, D)
    xq = r.standard_normal((B, D))
    return X, y, xq


def _gd(X, y, xq):
    W0 = np.zeros(D)
    return np.array([C.gd_step_prediction(X[b], y[b], xq[b], W0, ETA) for b in range(len(X))])


def _pred(fn, X, y, xq, beta, c):
    W0 = np.zeros(D)
    return np.array([fn(X[b], y[b], xq[b], W0, beta, c) for b in range(len(X))])


def _boot_ratio_ci(num_per, den_per, seed=0):
    """Bootstrap 95% CI of the normalized RMSE sqrt(sum num / sum den) over examples."""
    r = np.random.default_rng(seed)
    n = len(num_per)
    idx = r.integers(0, n, size=(N_BOOT, n))
    vals = np.sqrt(num_per[idx].sum(1) / den_per[idx].sum(1))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def _single_best(X, y, xq, gd, beta):
    """Closed-form best output scale c* for a single head at beta (prediction linear in c), plus the
    per-example (err_num, den) at c* for bootstrap. Returns (c_star, err, num_per, den_per)."""
    ps = _pred(S.single_head_predict, X, y, xq, beta, 1.0)   # unit-scale head output (W0.xq = 0)
    with np.errstate(all="ignore"):                          # spurious Accelerate matmul FPE
        c = float(ps @ gd / (ps @ ps))
    num = (c * ps - gd) ** 2
    den = gd ** 2
    return c, float(np.sqrt(num.sum() / den.sum())), num, den


def _two_head(X, y, xq, gd, beta):
    c = S.matched_scale(beta, ETA)
    p = _pred(S.two_head_predict, X, y, xq, beta, c)
    num = (p - gd) ** 2
    den = gd ** 2
    return c, float(np.sqrt(num.sum() / den.sum())), num, den


def _floor_over_beta(N, B, betas):
    """Single-head best-case floor (min over beta) and honest two-head best (min over beta) at N."""
    X, y, xq = _tasks(SEED, N, B)
    gd = _gd(X, y, xq)
    sb = [_single_best(X, y, xq, gd, b) for b in betas]
    th = [_two_head(X, y, xq, gd, b) for b in betas]
    i_s = int(np.argmin([e for _, e, _, _ in sb]))
    i_t = int(np.argmin([e for _, e, _, _ in th]))
    return sb[i_s], th[i_t]


def _verification():
    """The three anchors, measured (not prose): idealized identity, centering explains the residual,
    offset dominates the single head."""
    with np.errstate(all="ignore"):
        # 1) idealized two-head == GD to machine precision, every beta + W0 kind
        maxd = 0.0
        r = np.random.default_rng(3)
        for _ in range(200):
            X, y, _w = T.make_regression_batch(r, 1, 16, D)
            xq = r.standard_normal(D)
            W0 = r.standard_normal(D) if _ % 2 else np.zeros(D)
            for b in (0.02, 0.1, 1.0, 3.0):
                maxd = max(maxd, abs(S.two_head_ideal_predict(X[0], y[0], xq, W0, b, ETA)
                                     - C.gd_step_prediction(X[0], y[0], xq, W0, ETA)))
        # 2) centering term explains the honest two-head small-beta residual
        X, y, xq = _tasks(5, N_HEADLINE, B_DIAG)
        gd = _gd(X, y, xq)
        beta = 0.03
        c = S.matched_scale(beta, ETA)
        p = _pred(S.two_head_predict, X, y, xq, beta, c)
        resid = p - gd
        cent = np.array([S.centering_term(X[b], y[b], xq[b], np.zeros(D), ETA) for b in range(len(X))])
        cent_unexpl = float(np.sqrt(((resid - cent) ** 2).sum() / (resid ** 2).sum()))
        # 3) offset fraction of the single head, measured at TWO honest operating points: the
        #    Eq-17 offset DOMINATES at small beta (where the single head is worst, ~0.99); at the
        #    single head's actual best-case beta (the U-curve minimum) the offset is small (~0.17)
        #    and hard-max over-sharpening is what limits it. So the single head's failure is a
        #    small-beta-offset / large-beta-sharpening tradeoff, not a pure offset at best-case.
        def _offfrac(beta):
            c, _, _, _ = _single_best(X, y, xq, gd, beta)
            off = np.array([S.offset_term(X[b], y[b], xq[b], np.zeros(D), beta, c) for b in range(len(X))])
            tot = _pred(S.single_head_predict, X, y, xq, beta, c)
            return float(np.sqrt((off ** 2).sum() / (tot ** 2).sum()))
        beta_best = float(min(BETAS, key=lambda b: _single_best(X, y, xq, gd, b)[1]))
        off_small = _offfrac(0.02)
        off_best = _offfrac(beta_best)
    return {"idealized_identity_maxabs": float(maxd), "centering_unexplained_frac": cent_unexpl,
            "single_offset_fraction_small_beta": off_small,
            "single_offset_fraction_best_beta": off_best,
            "single_best_beta": beta_best,
            "note": "idealized two-head reproduces GD to machine precision (mechanism); the honest "
                    "two-head residual is the centering term (root cause, O(1/N)); the single head "
                    "is offset-dominated at SMALL beta (~0.99), while at its best-case beta the "
                    "offset is ~0.17 and hard-max over-sharpening limits it."}


def main():
    print(f"[{STUDY}] d={D} eta={ETA} N_headline={N_HEADLINE} B={B_SWEEP} betas={len(BETAS)} "
          f"N_grid={N_GRID}")
    verification = _verification()
    print(f"verification: idealized_identity={verification['idealized_identity_maxabs']:.2e}  "
          f"centering_unexplained={verification['centering_unexplained_frac']:.3f}  "
          f"offset_frac(small_beta)={verification['single_offset_fraction_small_beta']:.3f}  "
          f"offset_frac(best_beta={verification['single_best_beta']:.2f})="
          f"{verification['single_offset_fraction_best_beta']:.3f}")

    # ---- beta sweep at the headline N -------------------------------------------------------
    X, y, xq = _tasks(SEED, N_HEADLINE, B_SWEEP)
    gd = _gd(X, y, xq)
    betas = list(map(float, BETAS))
    single, two, ideal = [], [], []
    for i, b in enumerate(betas):
        cs, es, ns, ds = _single_best(X, y, xq, gd, b)
        ct, et, nt, dt = _two_head(X, y, xq, gd, b)
        arr = np.array([S.two_head_ideal_predict(X[j], y[j], xq[j], np.zeros(D), b, ETA)
                        for j in range(len(X))])
        ei = float(np.sqrt(((arr - gd) ** 2).mean()))
        single.append({"c_star": cs, "err": es, "err_ci": _boot_ratio_ci(ns, ds, seed=100 + i)})
        two.append({"c": ct, "err": et, "err_ci": _boot_ratio_ci(nt, dt, seed=200 + i)})
        ideal.append({"err_absrms": ei})
        print(f"  beta={b:6.3f}  single_best_err={es:.4f}  two_head_err={et:.4f}  ideal_rms={ei:.1e}")

    # ---- N sweep: floors + ratio (asymptotic-only evidence) ---------------------------------
    n_sweep = {"N": [], "single_floor": [], "single_floor_ci": [], "two_floor": [],
               "two_floor_ci": [], "ratio": [], "two_floor_x_N": []}
    for N in N_GRID:
        (cs, es, ns, ds), (ct, et, nt, dt) = _floor_over_beta(N, B_SWEEP, betas)
        n_sweep["N"].append(N)
        n_sweep["single_floor"].append(es)
        n_sweep["single_floor_ci"].append(_boot_ratio_ci(ns, ds, seed=300 + N))
        n_sweep["two_floor"].append(et)
        n_sweep["two_floor_ci"].append(_boot_ratio_ci(nt, dt, seed=400 + N))
        n_sweep["ratio"].append(es / et)
        n_sweep["two_floor_x_N"].append(et * N)
        print(f"  N={N:4d}  single_floor={es:.4f}  two_floor={et:.4f}  ratio={es/et:5.1f}  "
              f"two*N={et*N:.3f}")

    # ---- verdict ----------------------------------------------------------------------------
    hi = N_GRID.index(N_HEADLINE)
    single_floor = n_sweep["single_floor"][hi]
    two_floor = n_sweep["two_floor"][hi]
    exact = verification["idealized_identity_maxabs"] < 1e-10
    # NOTE: single_head_fails is a FIXED-N (headline N=20) statement -- the paper's Fig-12 regime.
    # The single-head floor also declines with N (see single_floor_declines below), crossing 0.30
    # near N~=160-240; asymptotically both heads recover, the two head at the faster O(1/N) rate.
    fails = single_floor > 0.3
    recovers = two_floor < 0.25 and (single_floor / two_floor) > 2.5
    explained = verification["centering_unexplained_frac"] < 0.1
    # asymptotic-only: two-head floor strictly shrinks across the N grid (O(1/N))
    asymptotic = all(n_sweep["two_floor"][i + 1] < n_sweep["two_floor"][i]
                     for i in range(len(N_GRID) - 1))
    # honesty diagnostic: the single-head floor ALSO declines with N (both recover; ratio widens
    # because the two head does so faster). Disclosed so the asymptotic story is not one-sided.
    single_floor_declines = all(n_sweep["single_floor"][i + 1] < n_sweep["single_floor"][i]
                                for i in range(len(N_GRID) - 1))
    verdict = {
        "exact_idealized_identity": bool(exact),
        "single_head_fails": bool(fails),
        "single_head_fails_scope": "fixed N = %d (Fig-12 regime); floor also declines with N" % N_HEADLINE,
        "two_head_recovers": bool(recovers),
        "centering_floor_explained": bool(explained),
        "asymptotic_only": bool(asymptotic),
        "single_floor_declines_with_N": bool(single_floor_declines),
        "single_floor_headline": single_floor,
        "two_floor_headline": two_floor,
        "ratio_headline": single_floor / two_floor,
        "reproduced": bool(exact and fails and recovers and explained and asymptotic),
    }
    summary = {
        "study": STUDY,
        "config": {"d": D, "eta": ETA, "N_headline": N_HEADLINE, "betas": betas,
                   "N_grid": list(N_GRID), "B": B_SWEEP, "seed": SEED, "n_boot": N_BOOT},
        "verification": verification,
        "beta_sweep": {"beta": betas, "single_best": single, "two_head": two, "two_ideal": ideal},
        "n_sweep": n_sweep,
        "verdict": verdict,
        "env": {"python": platform.python_version(), "numpy": np.__version__,
                "platform": platform.platform()},
    }
    save_json(summary, f"{ART}/summary.json")
    print(f"\nverdict: {verdict}")
    return summary


if __name__ == "__main__":
    main()
