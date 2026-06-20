"""Figure E.3 — SwiGLU: the SiLU gate and the gated MLP.

Left: SiLU(x)=x*sigma(x) and its derivative vs ReLU/GELU — the smooth self-gate
that replaces the activation. Right: a schematic of the SwiGLU MLP, two parallel
projections (gate + up) multiplied elementwise then projected down, with the 8/3 d
hidden width that keeps the parameter count equal to a 4d GELU MLP.

SwiGLU: Shazeer 2020, used by Llama with hidden width (2/3)*4d = 8/3 d [65, Sec 2.2].

Output: appendix-e-swiglu.svg
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from math import erf

HERE = pathlib.Path(__file__).resolve().parent
SILU_C, RELU_C, GELU_C, EDGE = "#7c3aed", "#9ca3af", "#2563eb", "#374151"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6))

# --- left: SiLU vs ReLU vs GELU, plus SiLU' ---
x = np.linspace(-5, 4, 601)
sig = 1 / (1 + np.exp(-x))
silu = x * sig
silu_d = sig + x * sig * (1 - sig)
relu = np.maximum(x, 0)
gelu = x * 0.5 * (1 + np.vectorize(erf)(x / np.sqrt(2)))
ax1.plot(x, silu, color=SILU_C, lw=2.2, label=r"SiLU$(x)=x\,\sigma(x)$")
ax1.plot(x, gelu, color=GELU_C, lw=1.4, ls="--", label="GELU (App. D)")
ax1.plot(x, relu, color=RELU_C, lw=1.2, ls=":", label="ReLU (App. C)")
ax1.plot(x, silu_d, color="#16a34a", lw=1.3, alpha=0.9,
         label=r"SiLU$'(x)=\sigma+x\sigma(1-\sigma)$")
ax1.axhline(0, color="#cbd5e1", lw=0.8); ax1.axvline(0, color="#cbd5e1", lw=0.8)
mn = silu.min(); mnx = x[np.argmin(silu)]
ax1.scatter([mnx], [mn], color=SILU_C, s=22, zorder=5)
ax1.annotate(f"min ${mn:.2f}$ at $x{{\\approx}}{mnx:.2f}$", (mnx, mn),
             xytext=(-4.8, 1.5), fontsize=7.2, color=SILU_C,
             arrowprops=dict(arrowstyle="-|>", color=SILU_C, lw=0.8))
ax1.set_xlabel("$x$", fontsize=9); ax1.set_ylabel("value", fontsize=9)
ax1.set_title("SiLU/Swish: a smooth self-gate", fontsize=9.6)
ax1.grid(alpha=0.25); ax1.legend(fontsize=7.3, loc="upper left")

# --- right: SwiGLU MLP schematic ---
ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
ax2.set_title("SwiGLU MLP: gate $\\odot$ up, then down", fontsize=9.6)


def b(x0, y0, w, h, t, fc, fs=8.2, tc="white"):
    ax2.add_patch(FancyBboxPatch((x0, y0), w, h,
                  boxstyle="round,pad=0.02,rounding_size=0.06",
                  lw=1.1, edgecolor=EDGE, facecolor=fc))
    ax2.text(x0 + w / 2, y0 + h / 2, t, ha="center", va="center",
             fontsize=fs, color=tc, fontweight="bold")


arr = dict(arrowstyle="-|>", color=EDGE, lw=1.1, mutation_scale=12)
b(0.3, 4.4, 1.5, 1.1, "$\\mathbf{x}$\n($d$)", "#e5e7eb", tc=EDGE)
# two parallel projections
b(2.7, 6.4, 1.9, 1.1, "gate $W_g$\n($d\\to\\frac{8}{3}d$)", "#7c3aed")
b(2.7, 2.4, 1.9, 1.1, "up $W_u$\n($d\\to\\frac{8}{3}d$)", "#2563eb")
b(5.0, 6.4, 1.3, 1.1, "SiLU", "#16a34a")
ax2.add_patch(plt.Circle((6.95, 5.0), 0.34, fc="white", ec=EDGE, lw=1.2, zorder=4))
ax2.text(6.95, 5.0, "$\\odot$", ha="center", va="center", fontsize=13, zorder=5)
b(7.7, 4.4, 1.9, 1.1, "down $W_d$\n($\\frac{8}{3}d\\to d$)", "#374151")
ax2.add_patch(FancyArrowPatch((1.8, 5.2), (2.7, 6.6), **arr))
ax2.add_patch(FancyArrowPatch((1.8, 4.7), (2.7, 3.2), **arr))
ax2.add_patch(FancyArrowPatch((4.6, 6.95), (5.0, 6.95), **arr))
ax2.add_patch(FancyArrowPatch((6.3, 6.6), (6.75, 5.35), **arr))
ax2.add_patch(FancyArrowPatch((4.6, 3.0), (6.7, 4.7), **arr))
ax2.add_patch(FancyArrowPatch((7.3, 5.0), (7.7, 5.0), **arr))
ax2.text(5.0, 1.3, "width $\\frac{8}{3}d$ (not $4d$) keeps the 3-matrix\n"
                   "SwiGLU param count equal to the 2-matrix GELU MLP",
         ha="center", fontsize=7.4, color=EDGE,
         bbox=dict(boxstyle="round,pad=0.35", fc="#f3f4f6", ec=EDGE, lw=0.7))

fig.tight_layout()
fig.savefig(HERE / "appendix-e-swiglu.svg", bbox_inches="tight")
print("wrote appendix-e-swiglu.svg")
