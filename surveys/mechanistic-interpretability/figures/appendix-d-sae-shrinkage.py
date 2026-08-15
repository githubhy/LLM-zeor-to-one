"""Appendix D: the L1 shrinkage bias, and what each SAE variant does about it.

Two panels. Fully deterministic -- closed forms only, no rng at all.

THE PROBLEM (derived in appendix D.1). A sparse autoencoder reconstructs an
activation x from a sparse code f and a decoder dictionary, trained on

    L = || x - xhat ||^2  +  lambda * || f ||_1

The L1 term is doing two jobs at once: it decides WHICH features fire, and it is
subtracted from HOW MUCH they fire. The second job is unwanted. Isolate one
feature with true coefficient a and unit decoder direction; the per-feature
problem is

    min_{f >= 0}  (a - f)^2 + lambda * f
    d/df = -2(a - f) + lambda = 0   =>   f* = a - lambda/2      (for a > lambda/2)
                                          f* = 0                (otherwise)

so the recovered magnitude is SOFT-THRESHOLDED: every active feature is reported
lambda/2 too small, no matter how large it truly is. That is the shrinkage bias.
It is a *bias*, not noise -- it does not average away over features or over data,
and it is exactly why a plain ReLU SAE systematically under-reconstructs.

(left) The four activation rules as maps from pre-activation to reported
magnitude, at lambda = 0.6 (so the shrinkage is 0.3) and threshold theta = 0.5:
  ReLU + L1   f = max(0, pi) - lambda/2   -- fires early, always reports low
  JumpReLU    f = pi * H(pi - theta)      -- fires late, reports exactly
  TopK        f = pi if pi in top-k       -- no penalty term at all
  Gated       detection and magnitude are separate paths, so the L1 lands on the
              gate only; above threshold the magnitude path is unbiased
The gap between the ReLU line and the identity is the bias; the JumpReLU, TopK
and Gated lines lie ON the identity above their thresholds, which is the whole
point of those variants.

(right) The consequence for reconstruction, as a function of how many features
are active. With n_active features each shrunk by lambda/2, the squared
reconstruction error contributed by shrinkage alone is

    E_shrink = n_active * (lambda/2)^2

which grows LINEARLY in the number of active features and QUADRATICALLY in
lambda. The three curves are lambda in {0.2, 0.6, 1.2}.

TWO HYPOTHESES THIS PANEL NEEDS, both stronger than they look. (i) Adding the
per-feature errors in quadrature assumes the ACTIVE decoder columns are mutually
ORTHOGONAL -- unit norm is not enough. Under merely-incoherent columns the cross
terms add a correction growing with the number of active PAIRS, i.e.
quadratically in n_active against the plotted linear term, so these lines are a
LOWER BOUND on the true shrinkage cost and the gap widens to the right.
(ii) The "quadratic in lambda" reading holds at FIXED n_active. Raising lambda
buys sparsity precisely BY reducing n_active, so the two factors of the product
move in opposite directions: this panel isolates one factor of the
fidelity-sparsity tradeoff, it does not trace the frontier.

NOTHING HERE IS MEASURED FROM A MODEL. Both panels are properties of the
objective, and lambda / theta / k are the objective's own hyperparameters, chosen
here only to make the geometry legible. No trained SAE was run and none is
claimed; the survey cites measured frontier positions separately.

Outputs:
  appendix-d-sae-shrinkage.svg
  appendix-d-sae-shrinkage.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
# Byte-reproducible SVG: fix the salt matplotlib uses to generate element ids,
# and drop the wall-clock <dc:date> at savefig (see metadata= below). Without both,
# re-running an UNCHANGED generator rewrites every id and the date, producing a
# multi-hundred-line diff in which a real change would be invisible.
matplotlib.rcParams["svg.hashsalt"] = "appendix-d-sae-shrinkage"
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
STEM = "appendix-d-sae-shrinkage"

LAMBDA = 0.6           # L1 coefficient -> shrinkage of LAMBDA/2 = 0.3
THETA = 0.5            # JumpReLU / Gated threshold
LAMBDAS_R = [0.2, 0.6, 1.2]

pi = np.linspace(-0.2, 2.0, 500)                 # pre-activation

relu_l1 = np.maximum(0.0, np.maximum(0.0, pi) - LAMBDA / 2.0)
jumprelu = np.where(pi > THETA, pi, 0.0)
topk = np.where(pi > THETA, pi, 0.0)             # same shape once selected; no penalty
gated = np.where(pi > THETA, pi, 0.0)            # magnitude path unpenalised

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.3))

axL.plot(pi, np.maximum(pi, 0.0), color="0.55", ls=":", lw=1.4, label="identity (unbiased)")
axL.plot(pi, relu_l1, lw=2.2, color="#d62728", label=r"ReLU + L1  ($f=\max(0,\pi)-\lambda/2$)")
axL.plot(pi, jumprelu, lw=2.0, color="#1f77b4", label=r"JumpReLU  ($f=\pi\,H(\pi-\theta)$)")
axL.plot(pi, gated + 0.012, lw=1.6, color="#2ca02c", ls="--", label="Gated / TopK (offset to show)")
# the shrinkage gap
axL.annotate("", xy=(1.6, 1.6), xytext=(1.6, 1.6 - LAMBDA / 2),
             arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.3))
axL.text(1.64, 1.6 - LAMBDA / 4, rf"bias $=\lambda/2={LAMBDA/2:g}$", color="#d62728", fontsize=9)
axL.axvline(THETA, color="0.7", lw=.9, ls="--")
axL.text(THETA + .03, -0.14, r"$\theta$", color="0.5", fontsize=9)
axL.set_xlabel(r"pre-activation $\pi$")
axL.set_ylabel(r"reported magnitude $f$")
axL.set_title(rf"(a) shrinkage is a bias, not noise   ($\lambda={LAMBDA:g}$, $\theta={THETA:g}$)", fontsize=10.5)
axL.legend(fontsize=8.2, frameon=False, loc="upper left")
axL.grid(alpha=.25, lw=.5)

n_act = np.arange(1, 101)
for lam in LAMBDAS_R:
    axR.plot(n_act, n_act * (lam / 2.0) ** 2, lw=2.0, label=rf"$\lambda={lam:g}$")
axR.set_xlabel("active features per token, $n_{\\mathrm{active}}$")
axR.set_ylabel(r"shrinkage-only squared error  $n_{\mathrm{active}}(\lambda/2)^2$")
axR.set_title(r"(b) cost is linear in $n_{\mathrm{active}}$, quadratic in $\lambda$", fontsize=10.5)
axR.legend(fontsize=8.6, frameon=False)
axR.grid(alpha=.25, lw=.5)

fig.tight_layout()
fig.savefig(HERE / f"{STEM}.svg", metadata={"Date": None})

data = {
    "constants": {"lambda_panel_a": LAMBDA, "theta": THETA,
                  "lambdas_panel_b": LAMBDAS_R, "deterministic": True, "rng_used": False},
    "closed_forms": {
        "soft_threshold_solution": "f* = a - lambda/2 for a > lambda/2, else 0",
        "shrinkage_bias": "lambda/2, independent of the true magnitude a",
        "shrinkage_only_error": "E_shrink = n_active * (lambda/2)^2",
    },
    "bias_at_lambda": {f"lambda={lam:g}": lam / 2.0 for lam in LAMBDAS_R + [LAMBDA]},
    "shrinkage_error_at_n_active_32": {
        f"lambda={lam:g}": round(32 * (lam / 2.0) ** 2, 4) for lam in LAMBDAS_R
    },
    "variant_behaviour_above_threshold": {
        "ReLU+L1": "biased low by lambda/2 at every magnitude",
        "JumpReLU": "unbiased; threshold is non-differentiable, trained with a straight-through estimator",
        "TopK": "unbiased; no penalty term, sparsity imposed by selection",
        "Gated": "unbiased; L1 applies to the detection path only",
    },
}
(HERE / f"{STEM}.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

print(f"wrote {STEM}.svg / .json")
print(f"  shrinkage bias at lambda={LAMBDA:g}: {LAMBDA/2:g}")
for lam in LAMBDAS_R:
    print(f"  shrinkage-only error at n_active=32, lambda={lam:g}: {32*(lam/2)**2:.4f}")
