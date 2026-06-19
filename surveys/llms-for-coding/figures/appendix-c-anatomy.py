"""Anatomy of the toy transformer: whole model -> one block -> one neuron.

Appendix C. A three-stage zoom answering "top structure to a single neuron" for
the toy model (V=3, d=4, T=3, 1 head, d_ff=8, 1 block). Schematic (matplotlib
patches); the head internals are detailed in Appendix A, so this figure zooms the
whole-model -> block -> FFN-neuron axis and cross-references the head there.

Outputs:
  appendix-c-anatomy.svg
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

HERE = pathlib.Path(__file__).resolve().parent

EMB_C, ATT_C, FFN_C, NORM_C, OUT_C = "#2563eb", "#7c3aed", "#16a34a", "#6b7280", "#d97706"
EDGE, SKIP_C = "#374151", "#9ca3af"

fig = plt.figure(figsize=(13.0, 6.2))
gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.05, 1.15], wspace=0.16)
axM, axB, axN = (fig.add_subplot(gs[i]) for i in range(3))
for a in (axM, axB, axN):
    a.set_xlim(0, 10); a.set_ylim(0, 10); a.axis("off")


def box(ax, x, y, w, h, fc, title, sub=None, tfs=8.6, sfs=7.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                fc=fc, ec=EDGE, lw=1.0, alpha=0.20))
    ax.text(x + w / 2, y + h * (0.60 if sub else 0.5), title, ha="center", va="center", fontsize=tfs)
    if sub:
        ax.text(x + w / 2, y + h * 0.24, sub, ha="center", va="center", fontsize=sfs, color=EDGE)


def up(ax, x, y0, y1, c=EDGE, lw=1.1):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=11, color=c, lw=lw))


# ---- Panel M: whole model (bottom -> top) ---------------------------------
axM.set_title("Whole model", fontsize=10.5)
cx = 5.0
box(axM, 2.2, 0.5, 5.6, 0.9, NORM_C, r"input tokens  $x=[0,1,2]$")
up(axM, cx, 1.4, 1.8)
box(axM, 2.2, 1.8, 5.6, 1.0, EMB_C, r"Embedding  $\mathbf{h}^0=E[x]+P$", r"$E:V{\times}d,\ P:T{\times}d$")
up(axM, cx, 2.8, 3.3)
box(axM, 1.7, 3.3, 6.6, 1.5, ATT_C, r"Decoder block  $\times L$", r"attention $+$ FFN (zoom $\rightarrow$)")
up(axM, cx, 4.8, 5.3)
box(axM, 2.2, 5.3, 5.6, 0.9, NORM_C, r"final LayerNorm")
up(axM, cx, 6.2, 6.7)
box(axM, 2.2, 6.7, 5.6, 1.0, OUT_C, r"Unembedding  $W_U:d{\times}V$", r"logits $=\mathbf{h}^F W_U$")
up(axM, cx, 7.7, 8.2)
box(axM, 2.2, 8.2, 5.6, 1.1, NORM_C, r"softmax $\to p$", r"cross-entropy loss $\mathcal{L}$")
axM.text(0.2, 9.7, r"$d{=}4,\ T{=}3,\ V{=}3$", fontsize=7.6, color=EDGE)

# ---- Panel B: one decoder block -------------------------------------------
axB.set_title("One decoder block", fontsize=10.5)
bx = 5.0
box(axB, 2.4, 0.5, 5.2, 0.8, NORM_C, r"$\mathbf{h}^0$ (residual stream in)")
up(axB, bx, 1.3, 1.7)
box(axB, 2.4, 1.7, 5.2, 0.7, NORM_C, r"LayerNorm", tfs=8.0)
up(axB, bx, 2.4, 2.7)
box(axB, 2.4, 2.7, 5.2, 1.0, ATT_C, r"Self-Attention (1 head)", r"detailed in Appendix A", tfs=8.4)
# residual add 1
axB.add_patch(Circle((bx, 4.1), 0.26, fc="white", ec=EDGE, lw=1.1)); axB.text(bx, 4.1, "+", ha="center", va="center", fontsize=11)
up(axB, bx, 3.7, 3.84)
axB.add_patch(FancyArrowPatch((1.4, 0.9), (1.4, 4.1), arrowstyle="-", color=SKIP_C, lw=1.1, ls="--"))
axB.add_patch(FancyArrowPatch((1.4, 4.1), (bx - 0.26, 4.1), arrowstyle="-|>", mutation_scale=10, color=SKIP_C, lw=1.1))
axB.text(1.2, 2.5, "residual", rotation=90, fontsize=6.8, color=SKIP_C, ha="center", va="center")
up(axB, bx, 4.36, 4.9)
box(axB, 2.4, 4.9, 5.2, 0.7, NORM_C, r"LayerNorm", tfs=8.0)
up(axB, bx, 5.6, 6.0)
box(axB, 2.4, 6.0, 5.2, 1.0, FFN_C, r"FFN (ReLU MLP)", r"zoom $\rightarrow$", tfs=8.4)
axB.add_patch(Circle((bx, 7.5), 0.26, fc="white", ec=EDGE, lw=1.1)); axB.text(bx, 7.5, "+", ha="center", va="center", fontsize=11)
up(axB, bx, 7.0, 7.24)
axB.add_patch(FancyArrowPatch((1.4, 4.1), (1.4, 7.5), arrowstyle="-", color=SKIP_C, lw=1.1, ls="--"))
axB.add_patch(FancyArrowPatch((1.4, 7.5), (bx - 0.26, 7.5), arrowstyle="-|>", mutation_scale=10, color=SKIP_C, lw=1.1))
up(axB, bx, 7.76, 8.3)
box(axB, 2.4, 8.3, 5.2, 0.8, NORM_C, r"$\mathbf{h}^2$ (out $\to$ next block)")

# ---- Panel N: the FFN, down to one neuron ---------------------------------
axN.set_title("The FFN, down to one neuron", fontsize=10.5)
# input units (d=4)
for i in range(4):
    axN.add_patch(Circle((1.2, 2.0 + i * 1.7), 0.26, fc=NORM_C, ec=EDGE, lw=0.8, alpha=0.5))
axN.text(1.2, 9.2, r"$\mathbf{f}_{in}\in\mathbb{R}^{d=4}$", ha="center", fontsize=7.8)
# hidden units (d_ff=8)
hy = [0.7 + i * 1.18 for i in range(8)]
for i, y in enumerate(hy):
    hl = (i == 4)
    axN.add_patch(Circle((5.0, y), 0.30 if hl else 0.24,
                         fc=(FFN_C if hl else "#d1fae5"), ec=(EDGE if hl else SKIP_C),
                         lw=(1.4 if hl else 0.7), alpha=(0.95 if hl else 0.6), zorder=3))
axN.text(5.0, 10.0, r"$d_{ff}=8$ hidden units (ReLU)", ha="center", fontsize=7.8)
# output units (d=4)
for i in range(4):
    axN.add_patch(Circle((8.8, 2.0 + i * 1.7), 0.26, fc=NORM_C, ec=EDGE, lw=0.8, alpha=0.5))
axN.text(8.8, 9.2, r"$\mathbf{f}_{out}\in\mathbb{R}^{d=4}$", ha="center", fontsize=7.8)
# highlighted neuron k=5: W1 row in, W2 column out
for i in range(4):
    axN.add_patch(FancyArrowPatch((1.46, 2.0 + i * 1.7), (4.72, hy[4]), arrowstyle="-",
                                  color=FFN_C, lw=1.3, alpha=0.8, zorder=2))
for i in range(4):
    axN.add_patch(FancyArrowPatch((5.30, hy[4]), (8.54, 2.0 + i * 1.7), arrowstyle="-|>",
                                  mutation_scale=8, color=FFN_C, lw=1.3, alpha=0.8, zorder=2))
# faint other connections (a few)
for i in range(4):
    for j in [0, 2, 6]:
        axN.add_patch(FancyArrowPatch((1.46, 2.0 + i * 1.7), (4.76, hy[j]), arrowstyle="-",
                                      color=SKIP_C, lw=0.4, alpha=0.25, zorder=1))
axN.annotate("one neuron $k$:\n" r"$g_k=\mathrm{ReLU}(W_1[:,k]^\top\mathbf{f}_{in}+b_{1,k})$" "\n"
             r"writes $g_k\,W_2[k,:]$ to the output",
             (5.0, hy[4]), xytext=(2.2, 5.6 + 0.0), fontsize=7.0, color=EDGE, ha="left",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=FFN_C, alpha=0.95),
             arrowprops=dict(arrowstyle="-|>", color=FFN_C, lw=1.0))
axN.text(5.0, 0.0, r"$W_1:d{\times}d_{ff}$ (rows in) $\cdot$ ReLU $\cdot$ $W_2:d_{ff}{\times}d$ (cols out)",
         ha="center", fontsize=7.2, color=EDGE)

# zoom connectors between panels (figure-level)
fig.text(0.345, 0.5, r"$\Rightarrow$", fontsize=20, color=SKIP_C, ha="center", va="center")
fig.text(0.66, 0.5, r"$\Rightarrow$", fontsize=20, color=SKIP_C, ha="center", va="center")

fig.savefig(HERE / "appendix-c-anatomy.svg", bbox_inches="tight")
fig.savefig("/tmp/appendix-c-anatomy-QA.png", dpi=120, bbox_inches="tight")  # QA only
print("wrote appendix-c-anatomy.svg")
