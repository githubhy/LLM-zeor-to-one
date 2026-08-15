"""Appendix C: the two approximations that circuit discovery quietly relies on.

Two panels. Fully deterministic -- closed forms only, no rng at all.

THE SETUP. A patching experiment measures how a metric m moves when an activation
is replaced. Write the metric as a saturating readout of a logit, which is what it
always is in practice because the metric is a logit difference through a softmax:

    m(delta) = sigma( z0 + g * delta ),        sigma(z) = 1/(1+e^{-z})

with z0 the clean operating point and g the sensitivity of the logit to the
patched component.

(left) ACTIVATION PATCHING vs ATTRIBUTION PATCHING. Activation patching evaluates
m exactly and costs one forward pass per component. Attribution patching replaces
it with a first-order expansion around the clean point, costing ONE backward pass
for all components at once:

    Delta_m_exact  = sigma(z0 + g*delta) - sigma(z0)
    Delta_m_linear = sigma'(z0) * g * delta,        sigma'(z0) = sigma(z0)(1-sigma(z0))

The saving is what makes attribution patching usable at scale; the price is the
second-order remainder. At z0 = -0.4, g = 1.1 the relative error runs

    delta = 0.1 -> 1.0% ;  0.5 -> 2.9% ;  1.0 -> 1.0% ;  2.0 -> 15.7% ;  4.0 -> 82.0%

Note the error is NOT monotone in delta: sigma is convex below its inflection and
concave above, so at z0 = -0.4 the linear approximation crosses the exact curve
near delta ~ 0.36 and the signed error changes sign there. What is monotone, and
what matters, is that once the readout saturates the approximation fails badly --
82% at delta = 4. The honest reading is that attribution patching is a screening
instrument valid near the operating point, not a substitute for the exact
intervention on large effects.

(right) WHY SINGLE-COMPONENT EFFECTS DO NOT ADD. Patch two components with
sensitivities gA, gB and displacements dA, dB. Because sigma is nonlinear,

    Delta_m(A,B)  !=  Delta_m(A) + Delta_m(B)

and the gap is a genuine interaction term, not an error:

    interaction = [sigma(z0+gA*dA+gB*dB) - sigma(z0)] - [sigma(z0+gA*dA) - sigma(z0)]
                                                      - [sigma(z0+gB*dB) - sigma(z0)]

At gA = 1.1, gB = 0.9 the interaction is -1.2% of the joint effect at dA=dB=0.5,
-13.3% at 1.0, -49.9% at 2.0, and -77.2% at 3.0. It is NEGATIVE throughout: the
components are SUB-additive, so adding up singleton ablation effects
systematically OVERSTATES what the pair does together. Any greedy circuit search
that scores components one at a time and sums, or that thresholds on singleton
importance, inherits this bias -- and it grows precisely in the regime where the
components matter most.

This is a property of the saturating readout alone. It requires no interaction in
the network's own computation: two perfectly independent components still fail to
add, because the metric they are read through is nonlinear. That distinction --
interaction in the MEASUREMENT versus interaction in the MECHANISM -- is the one a
circuit claim has to separate, and it is the first-principles form of the 2026
multiple-mediator critique the survey cites.

NOTHING HERE IS MEASURED FROM A MODEL. z0, g, gA, gB are parameters of the
closed form, chosen to put the clean point in the sensitive region of the sigmoid
where patching experiments are actually run. No model was run and none is claimed.

Outputs:
  appendix-c-patching-approximation.svg
  appendix-c-patching-approximation.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
# Byte-reproducible SVG: fix the salt matplotlib uses to generate element ids,
# and drop the wall-clock <dc:date> at savefig (see metadata= below). Without both,
# re-running an UNCHANGED generator rewrites every id and the date, producing a
# multi-hundred-line diff in which a real change would be invisible.
matplotlib.rcParams["svg.hashsalt"] = "appendix-c-patching-approximation"
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
STEM = "appendix-c-patching-approximation"

Z0, G = -0.4, 1.1          # clean operating point and single-component sensitivity
GA, GB = 1.1, 0.9          # two-component sensitivities

sigma = lambda z: 1.0 / (1.0 + np.exp(-z))
dsigma = lambda z: sigma(z) * (1.0 - sigma(z))

# ---------------------------------------------------------------- panel (left)
delta = np.linspace(0.0, 4.5, 400)
exact = sigma(Z0 + G * delta) - sigma(Z0)
linear = dsigma(Z0) * G * delta
with np.errstate(divide="ignore", invalid="ignore"):
    rel = np.where(np.abs(exact) > 1e-9, np.abs(linear - exact) / np.abs(exact), np.nan)

MARKS = [0.1, 0.5, 1.0, 2.0, 4.0]
mark_rows = []
for d in MARKS:
    e = float(sigma(Z0 + G * d) - sigma(Z0))
    l = float(dsigma(Z0) * G * d)
    mark_rows.append({"delta": d, "exact": round(e, 6), "first_order": round(l, 6),
                      "rel_error": round(abs(l - e) / abs(e), 4)})

# --------------------------------------------------------------- panel (right)
dd = np.linspace(0.0, 3.5, 400)
dmA = sigma(Z0 + GA * dd) - sigma(Z0)
dmB = sigma(Z0 + GB * dd) - sigma(Z0)
dmAB = sigma(Z0 + GA * dd + GB * dd) - sigma(Z0)
inter = dmAB - (dmA + dmB)

INTER_MARKS = [0.5, 1.0, 2.0, 3.0]
inter_rows = []
for d in INTER_MARKS:
    a = float(sigma(Z0 + GA * d) - sigma(Z0))
    b = float(sigma(Z0 + GB * d) - sigma(Z0))
    ab = float(sigma(Z0 + GA * d + GB * d) - sigma(Z0))
    inter_rows.append({"d": d, "joint": round(ab, 6), "sum_of_singles": round(a + b, 6),
                       "interaction": round(ab - (a + b), 6),
                       "interaction_frac_of_joint": round((ab - (a + b)) / ab, 4)})

# ------------------------------------------------------------------ rendering
fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.3))

axL.plot(delta, exact, lw=2.2, color="#1f77b4", label=r"activation patching (exact)")
axL.plot(delta, linear, lw=2.0, color="#d62728", ls="--", label=r"attribution patching (1st order)")
axL.set_xlabel(r"patch displacement $\delta$")
axL.set_ylabel(r"$\Delta m$")
axL.set_title(rf"(a) the first-order approximation and its price   ($z_0={Z0}$, $g={G}$)", fontsize=10.5)
axL.legend(fontsize=8.6, frameon=False, loc="upper left")
axL.grid(alpha=.25, lw=.5)
ax2 = axL.twinx()
ax2.plot(delta, 100 * rel, lw=1.4, color="0.45", ls=":")
ax2.set_ylabel("relative error (%)", color="0.45", fontsize=9)
ax2.tick_params(axis="y", labelcolor="0.45", labelsize=8)
ax2.set_ylim(0, 120)
for r in mark_rows:
    ax2.plot([r["delta"]], [100 * r["rel_error"]], "o", ms=4.5, color="0.45")
ax2.annotate(f"{mark_rows[-1]['rel_error']:.0%}", (4.0, 100 * mark_rows[-1]["rel_error"]),
             textcoords="offset points", xytext=(-30, 4), fontsize=8.5, color="0.35")

axR.plot(dd, dmAB, lw=2.2, color="#1f77b4", label=r"joint patch $\Delta m(A,B)$")
axR.plot(dd, dmA + dmB, lw=2.0, color="#d62728", ls="--", label=r"sum of singles $\Delta m(A)+\Delta m(B)$")
axR.fill_between(dd, dmAB, dmA + dmB, color="#d62728", alpha=.12)
axR.set_xlabel(r"displacement $\delta_A=\delta_B=\delta$")
axR.set_ylabel(r"$\Delta m$")
axR.set_title(rf"(b) components are sub-additive   ($g_A={GA}$, $g_B={GB}$)", fontsize=10.5)
axR.legend(fontsize=8.6, frameon=False, loc="upper left")
axR.grid(alpha=.25, lw=.5)
for r in inter_rows[1:]:
    axR.annotate(f"{r['interaction_frac_of_joint']:+.0%}", (r["d"], r["joint"]),
                 textcoords="offset points", xytext=(4, -13), fontsize=8.2, color="#d62728")

fig.tight_layout()
fig.savefig(HERE / f"{STEM}.svg", metadata={"Date": None})

data = {
    "constants": {"z0": Z0, "g": G, "gA": GA, "gB": GB,
                  "deterministic": True, "rng_used": False},
    "closed_forms": {
        "exact": "Delta_m = sigma(z0 + g*delta) - sigma(z0)",
        "first_order": "Delta_m ~= sigma'(z0) * g * delta,  sigma'(z0)=sigma(z0)(1-sigma(z0))",
        "interaction": "Delta_m(A,B) - Delta_m(A) - Delta_m(B)",
        "sign_change_note": "signed first-order error changes sign near the sigmoid inflection (delta ~ 0.36 at z0=-0.4); the plotted relative error is |.| and is therefore non-monotone",
    },
    "panel_a_first_order_error": mark_rows,
    "panel_b_interaction": inter_rows,
    "reading": "interaction is negative throughout: summing singleton ablation effects OVERSTATES the joint effect, and the bias grows with effect size",
}
(HERE / f"{STEM}.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

print(f"wrote {STEM}.svg / .json")
for r in mark_rows:
    print(f"  delta={r['delta']:<4} exact={r['exact']:+.4f} linear={r['first_order']:+.4f} rel.err={r['rel_error']:.1%}")
for r in inter_rows:
    print(f"  d={r['d']:<4} joint={r['joint']:+.4f} sum={r['sum_of_singles']:+.4f} interaction={r['interaction_frac_of_joint']:+.1%}")
