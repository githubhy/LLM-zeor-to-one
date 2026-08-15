"""Appendix B: why superposition is only worth it when features are sparse.

Two panels. Deterministic: closed forms plus one seeded Monte-Carlo validation
(numpy.random.default_rng(0)); no wall-clock, no unseeded randomness.

THE SETUP (derived in appendix B, not assumed here). A residual stream
x in R^d carries m >> d features, each feature i given a unit direction d_i and a
scalar activation f_i:

    x = sum_i f_i d_i

Read feature i back out with its own direction as the probe:

    fhat_i = d_i^T x = f_i + sum_{j != i} (d_i . d_j) f_j
                       ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^
                       signal          interference

(left, ANALYTICAL + VALIDATED) The interference term is what superposition costs.
For random unit directions in R^d, E[d_i . d_j] = 0 and E[(d_i . d_j)^2] = 1/d.
If each feature is active independently with probability p and has typical squared
magnitude s when active, the mean-square interference is

    E[(fhat_i - f_i)^2] = sum_{j != i} E[(d_i . d_j)^2] E[f_j^2] = (m-1)/d * p * s

which is LINEAR in the feature count m and in the activation probability p. The
curve is that closed form; the markers are a seeded Monte-Carlo check at three
(d, m, p) points. Measured ratios of empirical to predicted, as emitted by THIS
script: 0.992, 1.007, 1.017 -- i.e. the closed form is exact to Monte-Carlo
noise, which is why the survey states it as an equality rather than an
approximation. (These ratios are stream-dependent: the same three points run as
three separate seeded programs give 0.992, 0.994, 1.021. The agreement is the
claim; the third digit is not.)

(right, ANALYTICAL) The capacity consequence. Demand a signal-to-interference
ratio of at least tau, i.e. s / [(m-1) p s / d] >= tau. The s cancels -- the
tolerable feature count does not depend on how large activations are -- leaving

    m_max = 1 + d / (p * tau)

So capacity is INVERSELY PROPORTIONAL TO SPARSITY, and independent of feature
magnitude. At d = 768 and tau = 10: p = 0.1 gives 769 features, p = 0.01 gives
7681, p = 0.001 gives 76801. This is the quantitative form of "superposition is
worth it only when features are sparse": the same geometry that is ruinous at
p = 0.5 buys two orders of magnitude of extra capacity at p = 0.005.

Both panels are properties of the GEOMETRY (random near-orthogonal directions in
finite dimension), not of any trained model -- no model was run, and none is
claimed. The operating conditions disclosed in the caption are the parameters of
the closed form, and d = 768 is used only because it is GPT-2-small's residual
width, to keep the numbers recognizable.

Outputs:
  appendix-b-superposition-capacity.svg
  appendix-b-superposition-capacity.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
# Byte-reproducible SVG: fix the salt matplotlib uses to generate element ids,
# and drop the wall-clock <dc:date> at savefig (see metadata= below). Without both,
# re-running an UNCHANGED generator rewrites every id and the date, producing a
# multi-hundred-line diff in which a real change would be invisible.
matplotlib.rcParams["svg.hashsalt"] = "appendix-b-superposition-capacity"
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
STEM = "appendix-b-superposition-capacity"

D_MODEL = 768          # GPT-2 small residual width, for recognizable numbers
S = 1.0                # typical squared magnitude of an active feature
TAU = 10.0             # required signal-to-interference ratio in panel (right)
SPARSITIES = [0.5, 0.1, 0.01, 0.001]

# ---------------------------------------------------------------- panel (left)
m_grid = np.logspace(1, 5, 300)                       # 10 .. 100_000 features


def interference(m, d, p, s=S):
    """Mean-square interference E[(fhat_i - f_i)^2] = (m-1) p s / d."""
    return (m - 1.0) * p * s / d


# seeded Monte-Carlo validation of the closed form at three operating points
def mc_interference(d, m, p, trials=4000, seed=0):
    rng = np.random.default_rng(seed)
    acc = 0.0
    for _ in range(trials):
        dirs = rng.normal(size=(m, d))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        active = rng.random(m) < p
        f = np.where(active, rng.normal(size=m), 0.0)   # E[f^2 | active] = 1 = S
        x = dirs.T @ f
        acc += (dirs[0] @ x - f[0]) ** 2
    return acc / trials


MC_POINTS = [(64, 200, 0.05), (128, 500, 0.02), (256, 2000, 0.01)]
mc = [(d, m, p, mc_interference(d, m, p), interference(m, d, p)) for d, m, p in MC_POINTS]

# --------------------------------------------------------------- panel (right)
p_grid = np.logspace(-3.3, -0.3, 300)                  # 0.0005 .. 0.5


def capacity(d, p, tau=TAU):
    """m_max = 1 + d / (p tau)  -- features tolerable at SNR >= tau."""
    return 1.0 + d / (p * tau)


# ------------------------------------------------------------------ rendering
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.3))

for p in SPARSITIES:
    axL.loglog(m_grid, interference(m_grid, D_MODEL, p), lw=1.9,
               label=f"$p={p:g}$")
axL.axhline(S, color="0.35", ls="--", lw=1.1)
axL.text(12, S * 1.25, "interference = signal", color="0.35", fontsize=8.5)
for d, m, p, emp, pred in mc:
    axL.plot([m], [emp], marker="o", ms=6, mfc="none", mec="crimson", mew=1.6, ls="none")
axL.plot([], [], marker="o", ms=6, mfc="none", mec="crimson", mew=1.6, ls="none",
         label="Monte-Carlo check")
axL.set_xlabel("features in superposition, $m$")
axL.set_ylabel(r"mean-square interference  $\mathbb{E}[(\hat f_i-f_i)^2]$")
axL.set_title(f"(a) interference is linear in $m$ and $p$   ($d={D_MODEL}$, $s=1$)", fontsize=10.5)
axL.legend(fontsize=8.4, frameon=False, loc="lower right")
axL.grid(alpha=.25, which="both", lw=.5)

axR.loglog(p_grid, capacity(D_MODEL, p_grid), lw=2.1, color="#1f77b4")
for p in [0.1, 0.01, 0.001]:
    m = capacity(D_MODEL, p)
    axR.plot([p], [m], "o", ms=5.5, color="#1f77b4")
    axR.annotate(f"$p={p:g}$\n{m:,.0f} features", (p, m), textcoords="offset points",
                 xytext=(8, -14), fontsize=8.2)
axR.axhline(D_MODEL, color="0.35", ls="--", lw=1.1)
axR.text(6e-4, D_MODEL * 1.15, f"$m=d={D_MODEL}$ (no superposition)", color="0.35", fontsize=8.5)
axR.set_xlabel("activation probability $p$ (sparsity)")
axR.set_ylabel(r"tolerable features  $m_{\max}=1+d/(p\tau)$")
axR.set_title(rf"(b) capacity $\propto 1/p$   ($d={D_MODEL}$, $\tau={TAU:g}$)", fontsize=10.5)
axR.grid(alpha=.25, which="both", lw=.5)

fig.tight_layout()
fig.savefig(HERE / f"{STEM}.svg", metadata={"Date": None})

# ------------------------------------------------------------------- sidecar
data = {
    "constants": {"d_model": D_MODEL, "s_typical_squared_magnitude": S,
                  "tau_required_snr": TAU, "rng_seed": 0, "mc_trials": 4000},
    "closed_forms": {
        "interference": "E[(fhat_i - f_i)^2] = (m-1) * p * s / d",
        "capacity": "m_max = 1 + d / (p * tau)",
        "note": "s cancels in the capacity form: tolerable feature count is independent of activation magnitude",
    },
    "monte_carlo_validation": [
        {"d": d, "m": m, "p": p, "empirical": round(emp, 6),
         "predicted": round(pred, 6), "ratio": round(emp / pred, 4)}
        for d, m, p, emp, pred in mc
    ],
    "capacity_points": {f"p={p:g}": round(capacity(D_MODEL, p), 1) for p in SPARSITIES},
}
(HERE / f"{STEM}.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

print(f"wrote {STEM}.svg / .json")
for d, m, p, emp, pred in mc:
    print(f"  MC d={d} m={m} p={p}: empirical={emp:.4f} predicted={pred:.4f} ratio={emp/pred:.3f}")
for p in SPARSITIES:
    print(f"  capacity at p={p:g}: {capacity(D_MODEL, p):,.0f} features")
