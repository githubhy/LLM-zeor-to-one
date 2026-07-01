"""Tiny-transformer induction-study model, drawn in the Figure C.1 style.

Three-panel zoom (whole model -> one decoder block -> one attention head), matching
surveys/llms-for-coding/figures/appendix-c-anatomy.py: light-alpha rounded boxes,
semantic colors (blue embed / purple attention / green FFN / grey norm+IO / amber
unembed), grey dashed residual skips into white '+' circles. Config = the plan's
primary induction model: L=2, h=4, d=128, d_k=d_v=32, d_ff=512, |V|=64, T=256.

Outputs: tiny-transformer-anatomy.svg
"""
import pathlib
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE = pathlib.Path(__file__).resolve().parent

# palette + style copied from Figure C.1 (appendix-c-anatomy.py)
EMB_C, ATT_C, FFN_C, NORM_C, OUT_C = "#2563eb", "#7c3aed", "#16a34a", "#6b7280", "#d97706"
EDGE, SKIP_C = "#374151", "#9ca3af"


def box(ax, x, y, w, h, fc, title, sub=None, tfs=8.6, sfs=7.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                fc=fc, ec=EDGE, lw=1.0, alpha=0.20))
    ax.text(x + w / 2, y + h * (0.60 if sub else 0.5), title, ha="center", va="center", fontsize=tfs)
    if sub:
        ax.text(x + w / 2, y + h * 0.24, sub, ha="center", va="center", fontsize=sfs, color=EDGE)


def up(ax, x, y0, y1, c=EDGE, lw=1.1):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=11, color=c, lw=lw))


def add_circle(ax, x, y):
    ax.add_patch(Circle((x, y), 0.26, fc="white", ec=EDGE, lw=1.1))
    ax.text(x, y, "+", ha="center", va="center", fontsize=11)


fig = plt.figure(figsize=(13.0, 6.4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.05, 1.1], wspace=0.16)
axM, axB, axA = (fig.add_subplot(gs[i]) for i in range(3))
for a in (axM, axB, axA):
    a.set_xlim(0, 10); a.set_ylim(0, 10); a.axis("off")

# ---- Panel M: whole model (bottom -> top) ---------------------------------
axM.set_title("Whole model", fontsize=10.5)
cx = 5.0
box(axM, 2.2, 0.5, 5.6, 0.9, NORM_C, r"input tokens  $x_1\dots x_T$")
up(axM, cx, 1.4, 1.8)
box(axM, 2.2, 1.8, 5.6, 1.0, EMB_C, r"Embedding  $\mathbf{h}^0=E[x]+P$", r"$E:|\mathcal{V}|{\times}d,\ P:T{\times}d$")
up(axM, cx, 2.8, 3.3)
box(axM, 1.7, 3.3, 6.6, 1.5, ATT_C, r"Decoder block  $\times L$", r"masked attention $+$ FFN (zoom $\rightarrow$)")
up(axM, cx, 4.8, 5.3)
box(axM, 2.2, 5.3, 5.6, 0.9, NORM_C, r"final LayerNorm")
up(axM, cx, 6.2, 6.7)
box(axM, 2.2, 6.7, 5.6, 1.0, OUT_C, r"Unembedding  $W_U:d{\times}|\mathcal{V}|$", r"logits $=\mathbf{h}^F W_U$")
up(axM, cx, 7.7, 8.2)
box(axM, 2.2, 8.2, 5.6, 1.1, NORM_C, r"softmax $\to p$", r"cross-entropy loss $\mathcal{L}$")
axM.text(0.1, 9.7, r"$L{=}2,\ h{=}4,\ d{=}128,\ d_k{=}32,\ |\mathcal{V}|{=}64,\ T{=}256$", fontsize=7.2, color=EDGE)

# ---- Panel B: one decoder block -------------------------------------------
axB.set_title("One decoder block", fontsize=10.5)
bx = 5.0
box(axB, 2.4, 0.5, 5.2, 0.8, NORM_C, r"$\mathbf{h}^{\ell}$ (residual stream in)")
up(axB, bx, 1.3, 1.7)
box(axB, 2.4, 1.7, 5.2, 0.7, NORM_C, r"LayerNorm", tfs=8.0)
up(axB, bx, 2.4, 2.7)
box(axB, 2.4, 2.7, 5.2, 1.0, ATT_C, r"Masked Multi-Head Attention", r"$h{=}4$ heads (zoom $\rightarrow$)", tfs=8.4)
add_circle(axB, bx, 4.1); up(axB, bx, 3.7, 3.84)
axB.add_patch(FancyArrowPatch((1.4, 0.9), (1.4, 4.1), arrowstyle="-", color=SKIP_C, lw=1.1, ls="--"))
axB.add_patch(FancyArrowPatch((1.4, 4.1), (bx - 0.26, 4.1), arrowstyle="-|>", mutation_scale=10, color=SKIP_C, lw=1.1))
axB.text(1.2, 2.5, "residual", rotation=90, fontsize=6.8, color=SKIP_C, ha="center", va="center")
up(axB, bx, 4.36, 4.9)
box(axB, 2.4, 4.9, 5.2, 0.7, NORM_C, r"LayerNorm", tfs=8.0)
up(axB, bx, 5.6, 6.0)
box(axB, 2.4, 6.0, 5.2, 1.0, FFN_C, r"FFN (GELU MLP)", r"$d_{ff}{=}512$", tfs=8.4)
add_circle(axB, bx, 7.5); up(axB, bx, 7.0, 7.24)
axB.add_patch(FancyArrowPatch((1.4, 4.1), (1.4, 7.5), arrowstyle="-", color=SKIP_C, lw=1.1, ls="--"))
axB.add_patch(FancyArrowPatch((1.4, 7.5), (bx - 0.26, 7.5), arrowstyle="-|>", mutation_scale=10, color=SKIP_C, lw=1.1))
up(axB, bx, 7.76, 8.3)
box(axB, 2.4, 8.3, 5.2, 0.8, NORM_C, r"$\mathbf{h}^{\ell+1}$ (out $\to$ next block)")

# ---- Panel A: one attention head ------------------------------------------
axA.set_title("One attention head", fontsize=10.5)
ax = 5.0
box(axA, 2.5, 0.4, 5.0, 0.7, NORM_C, r"$\mathbf{x}$ (LayerNorm'd)", tfs=8.0)
up(axA, ax, 1.1, 1.5)
box(axA, 2.5, 1.5, 5.0, 0.9, ATT_C, r"$\mathbf{q},\mathbf{k},\mathbf{v}=W_Q\mathbf{x},W_K\mathbf{x},W_V\mathbf{x}$", r"$d_k{=}d_v{=}32$", tfs=8.0)
up(axA, ax, 2.4, 2.8)
box(axA, 2.5, 2.8, 5.0, 0.9, ATT_C, r"$S=\mathbf{q}^{\top}\mathbf{k}/\sqrt{d_k}$", r"causal mask $(j{>}i\to-\infty)$", tfs=8.0)
up(axA, ax, 3.7, 4.1)
box(axA, 2.5, 4.1, 5.0, 0.8, ATT_C, r"$A=\mathrm{softmax}_{\mathrm{row}}(S)$", tfs=8.0)
up(axA, ax, 4.9, 5.3)
box(axA, 2.5, 5.3, 5.0, 0.8, ATT_C, r"$\mathbf{o}=\sum_j A_{ij}\mathbf{v}_j$", tfs=8.0)
up(axA, ax, 6.1, 6.5)
box(axA, 2.5, 6.5, 5.0, 0.9, ATT_C, r"concat $h$ heads $\cdot\,W_O\to\Delta\mathbf{x}$", tfs=8.0)
axA.text(5.0, 7.9, r"circuits: $M=W_Q^{\top}W_K$,  $W_{OV}=W_O W_V$", ha="center", fontsize=7.0, color=EDGE)
axA.text(5.0, 7.45, r"(detailed in Appendix A)", ha="center", fontsize=6.8, color=SKIP_C)

# figure-level zoom connectors (as in Figure C.1)
fig.text(0.345, 0.5, r"$\Rightarrow$", fontsize=20, color=SKIP_C, ha="center", va="center")
fig.text(0.66, 0.5, r"$\Rightarrow$", fontsize=20, color=SKIP_C, ha="center", va="center")

fig.savefig(HERE / "tiny-transformer-anatomy.svg", bbox_inches="tight")
fig.savefig(pathlib.Path(tempfile.gettempdir()) / "tiny-transformer-anatomy-QA.png",
            dpi=120, bbox_inches="tight")  # QA only, not committed
print("wrote tiny-transformer-anatomy.svg")
