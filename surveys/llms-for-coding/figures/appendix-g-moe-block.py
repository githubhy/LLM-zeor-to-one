"""Figure G.1 — the dense SwiGLU FFN vs the DeepSeekMoE FFN.

Left: the dense block of Appendix E — one SwiGLU MLP, always on, every token pays
for all of it. Right: the MoE FFN — a router scores the token against N_r=256
routed experts, the top K_r=8 run (plus 1 always-on shared expert), and their
outputs are combined by normalized gating values. The token touches 9 of 257
experts, so capacity (total experts) and compute-per-token (active experts)
decouple. Schematic; counts sourced from DeepSeek-V3 [64].

Output: appendix-g-moe-block.svg
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent
DENSE, ROUTE, SEL, SHARE, EDGE, RT = "#6b7280", "#cbd5e1", "#7c3aed", "#16a34a", "#374151", "#dc2626"


def box(ax, x, y, w, h, t, fc, fs=8.0, tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                 lw=1.0, edgecolor=EDGE, facecolor=fc))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold")


fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.2, 5.6),
                               gridspec_kw={"width_ratios": [1.0, 2.0]})
arr = dict(arrowstyle="-|>", color=EDGE, lw=1.1, mutation_scale=12)

# --- left: dense ---
axL.set_xlim(0, 4); axL.set_ylim(0, 10); axL.axis("off")
axL.set_title("Dense FFN (App. E)", fontsize=10, fontweight="bold")
box(axL, 1.0, 4.6, 2.0, 1.0, "token $\\mathbf{u}$", "#e5e7eb", tc=EDGE)
box(axL, 0.7, 2.4, 2.6, 1.2, "SwiGLU MLP\n(always on)", DENSE, fs=8.6)
box(axL, 1.0, 0.5, 2.0, 1.0, "output", "#e5e7eb", tc=EDGE)
axL.add_patch(FancyArrowPatch((2.0, 4.6), (2.0, 3.6), **arr))
axL.add_patch(FancyArrowPatch((2.0, 2.4), (2.0, 1.5), **arr))
axL.text(2.0, 6.0, "every token pays\nfor all $N$ params", ha="center", fontsize=7.8,
         color=RT, style="italic")

# --- right: MoE ---
axR.set_xlim(0, 12); axR.set_ylim(0, 10); axR.axis("off")
axR.set_title("DeepSeekMoE FFN [64]: top-8 of 256 routed + 1 shared", fontsize=10, fontweight="bold")
box(axR, 0.3, 4.5, 1.6, 1.0, "token $\\mathbf{u}$", "#e5e7eb", tc=EDGE)
box(axR, 2.4, 4.5, 1.7, 1.0, "router\n$s_i=\\sigma(\\mathbf{e}_i^\\top\\mathbf{u})$", "#1f2937", fs=7.6)
axR.add_patch(FancyArrowPatch((1.9, 5.0), (2.4, 5.0), **arr))

# expert grid: 4 rows x 8 cols = 32 shown, label as 256; highlight 8 selected
x0, y0, ew, eh, gap = 4.6, 6.6, 0.52, 0.42, 0.12
sel = {(0, 1), (0, 5), (1, 3), (1, 7), (2, 0), (2, 4), (3, 2), (3, 6)}
for r in range(4):
    for c in range(8):
        x = x0 + c * (ew + gap); y = y0 - r * (eh + gap)
        fc = SEL if (r, c) in sel else ROUTE
        axR.add_patch(plt.Rectangle((x, y), ew, eh, fc=fc, ec=EDGE, lw=0.5))
axR.text(x0 + 4 * (ew + gap), y0 + 0.7, "256 routed experts (only top-8 active, in purple)",
         ha="center", fontsize=8.0, color=EDGE)
axR.add_patch(FancyArrowPatch((4.1, 5.0), (4.55, 6.0), **arr))

# shared expert
box(axR, 4.7, 1.7, 1.8, 0.9, "shared expert\n(always on)", SHARE, fs=7.4)
# combine node
axR.add_patch(plt.Circle((9.4, 4.8), 0.42, fc="white", ec=EDGE, lw=1.2, zorder=4))
axR.text(9.4, 4.8, "$\\Sigma g_i$", ha="center", va="center", fontsize=11, zorder=5)
box(axR, 10.4, 4.3, 1.4, 1.0, "output", "#e5e7eb", tc=EDGE)
axR.add_patch(FancyArrowPatch((8.7, 5.6), (9.1, 5.1), **arr))     # from experts
axR.add_patch(FancyArrowPatch((6.5, 2.1), (9.15, 4.5), **arr))   # from shared
axR.add_patch(FancyArrowPatch((9.82, 4.8), (10.4, 4.8), **arr))
axR.text(9.4, 3.0, "$\\mathbf{o}=\\sum_{s}\\mathrm{FFN}^{(s)}+\\sum_{i\\in\\mathrm{top}\\text{-}8} g_i\\,\\mathrm{FFN}_i^{(r)}$",
         ha="center", fontsize=8.4, color=EDGE,
         bbox=dict(boxstyle="round,pad=0.3", fc="#f3f4f6", ec=EDGE, lw=0.7))

fig.tight_layout()
fig.savefig(HERE / "appendix-g-moe-block.svg", bbox_inches="tight")
print("wrote appendix-g-moe-block.svg")
