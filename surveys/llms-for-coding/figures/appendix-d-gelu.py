"""GELU vs ReLU: the one nonlinearity GPT-2 changes from the toy.

Appendix D. The toy (Appendix C) used ReLU; the GPT family uses the Gaussian Error
Linear Unit, GELU(x) = x * Phi(x) with Phi the standard-normal CDF. Left: the two
activations. Right: their derivatives — ReLU' is a hard step (0 or 1), GELU' is the
smooth gate Phi(x) + x*phi(x), which is slightly negative for moderately negative x
(GELU dips below zero near x ~ -0.75) and exceeds 1 for moderately positive x. The
smoothness gives a nonzero, position-dependent gradient even for inputs the hard
ReLU would have killed.

Analytical (no rng); GELU and its exact derivative are closed form.

Outputs:
  appendix-d-gelu.svg
  appendix-d-gelu.json
"""
import json
import pathlib

import numpy as np
from numpy import exp, sqrt, pi
from math import erf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

x = np.linspace(-4, 4, 801)
Phi = 0.5 * (1 + np.vectorize(erf)(x / sqrt(2)))     # standard normal CDF
phi = np.exp(-x ** 2 / 2) / sqrt(2 * pi)             # standard normal pdf
gelu = x * Phi
gelu_d = Phi + x * phi                               # exact derivative
relu = np.maximum(x, 0.0)
relu_d = (x > 0).astype(float)

gelu_min_x = float(x[np.argmin(gelu)])               # ~ -0.75
data = {
    "gelu_min_x": gelu_min_x, "gelu_min": float(gelu.min()),
    "gelu_deriv_min": float(gelu_d.min()), "gelu_deriv_max": float(gelu_d.max()),
}
with open(HERE / "appendix-d-gelu.json", "w") as f:
    json.dump(data, f, indent=1)

GELU_C, RELU_C, EDGE = "#7c3aed", "#6b7280", "#374151"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.5))

ax1.plot(x, gelu, color=GELU_C, lw=2.0, label=r"GELU$(x)=x\,\Phi(x)$")
ax1.plot(x, relu, color=RELU_C, lw=1.6, ls="--", label=r"ReLU$(x)=\max(x,0)$")
ax1.axhline(0, color=EDGE, lw=0.6); ax1.axvline(0, color=EDGE, lw=0.6)
ax1.scatter([gelu_min_x], [gelu.min()], color=GELU_C, s=24, zorder=5)
ax1.annotate(rf"dips to {gelu.min():.2f} at $x{{\approx}}{gelu_min_x:.2f}$",
             (gelu_min_x, gelu.min()), xytext=(-3.8, 1.2), fontsize=7.4, color=GELU_C,
             arrowprops=dict(arrowstyle="-|>", color=GELU_C, lw=0.9))
ax1.set_xlabel("$x$", fontsize=9); ax1.set_ylabel("activation", fontsize=9)
ax1.set_title("GELU is a smooth gate; ReLU is a hard one", fontsize=9.8)
ax1.grid(alpha=0.25); ax1.legend(fontsize=8, loc="upper left")

ax2.plot(x, gelu_d, color=GELU_C, lw=2.0, label=r"GELU$'(x)=\Phi(x)+x\,\phi(x)$")
ax2.plot(x, relu_d, color=RELU_C, lw=1.6, ls="--", label=r"ReLU$'(x)=\mathbb{1}[x>0]$")
ax2.axhline(0, color=EDGE, lw=0.6); ax2.axvline(0, color=EDGE, lw=0.6)
ax2.set_xlabel("$x$", fontsize=9); ax2.set_ylabel("derivative", fontsize=9)
ax2.set_title(r"The gradient: ReLU is $\{0,1\}$; GELU is smooth (and overshoots)", fontsize=9.4)
ax2.grid(alpha=0.25); ax2.legend(fontsize=8, loc="upper left")

fig.tight_layout()
fig.savefig(HERE / "appendix-d-gelu.svg", bbox_inches="tight")
print("wrote appendix-d-gelu.svg / .json")
print(f"  GELU min {gelu.min():.3f} at x={gelu_min_x:.3f}; GELU' range [{gelu_d.min():.2f},{gelu_d.max():.2f}]")
