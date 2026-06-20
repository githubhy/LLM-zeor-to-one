"""Figure E.1 — the GPT-2 block vs the modern (Llama-family) dense block.

Two pre-norm decoder blocks side by side, same skeleton (residual stream + two
sublayers), with the FOUR substitutions of the modern dense block highlighted:
LayerNorm -> RMSNorm, learned positions -> RoPE (inside attention), full MHA ->
grouped-query attention, GELU MLP -> SwiGLU MLP. Schematic only (no data).

Sourced architecture facts: Llama uses pre-norm RMSNorm, SwiGLU, and RoPE
[65, Sec 2.2]; Llama 2 adds GQA for the larger sizes [63].

Output: appendix-e-block.svg
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent

SAME = "#e5e7eb"      # unchanged piece
NEW = "#7c3aed"       # changed piece (modern)
OLD = "#6b7280"       # the GPT-2 piece
EDGE = "#374151"
RES = "#2563eb"       # residual stream


def box(ax, x, y, w, h, text, fc, tc="white", fs=8.5, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
                       linewidth=1.1, edgecolor=EDGE, facecolor=fc, linestyle=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold", zorder=5)


def column(ax, x0, title, norm_lbl, attn_lbl, mlp_lbl, norm_fc, attn_fc, mlp_fc):
    w = 2.6
    ax.text(x0 + w / 2, 9.55, title, ha="center", va="center", fontsize=10.5,
            fontweight="bold", color=EDGE)
    # residual stream spine
    xc = x0 + w / 2
    ax.plot([xc, xc], [0.3, 9.0], color=RES, lw=2.2, zorder=1)
    ax.text(xc - 0.04, 0.12, "residual stream", ha="center", va="top", fontsize=7.2,
            color=RES, style="italic")
    # --- attention sublayer ---
    box(ax, x0, 1.2, w, 0.7, norm_lbl, norm_fc)
    box(ax, x0, 2.2, w, 0.9, attn_lbl, attn_fc, fs=8.0)
    # add node
    ax.add_patch(plt.Circle((xc, 3.55), 0.16, fc="white", ec=EDGE, lw=1.1, zorder=4))
    ax.text(xc, 3.55, "+", ha="center", va="center", fontsize=11, zorder=5)
    # --- mlp sublayer ---
    box(ax, x0, 4.6, w, 0.7, norm_lbl, norm_fc)
    box(ax, x0, 5.6, w, 0.9, mlp_lbl, mlp_fc, fs=8.0)
    ax.add_patch(plt.Circle((xc, 6.95), 0.16, fc="white", ec=EDGE, lw=1.1, zorder=4))
    ax.text(xc, 6.95, "+", ha="center", va="center", fontsize=11, zorder=5)
    # arrows: norm->sublayer->add, and the skip bypass
    a = dict(arrowstyle="-|>", color=EDGE, lw=1.0, mutation_scale=11)
    ax.add_patch(FancyArrowPatch((xc, 1.9), (xc, 2.2), **a))
    ax.add_patch(FancyArrowPatch((xc, 3.1), (xc, 3.39), **a))
    ax.add_patch(FancyArrowPatch((xc, 5.3), (xc, 5.6), **a))
    ax.add_patch(FancyArrowPatch((xc, 6.5), (xc, 6.79), **a))


fig, ax = plt.subplots(figsize=(11.5, 7.4))
ax.set_xlim(0, 11.5); ax.set_ylim(0, 10); ax.axis("off")

column(ax, 0.6, "GPT-2 block (App. D)",
       "LayerNorm", "Multi-Head\nAttention", "GELU MLP\n($d\\to4d\\to d$)",
       SAME, OLD, OLD)
column(ax, 8.3, "Modern dense block (Llama, App. E)",
       "RMSNorm", "GQA  +  RoPE", "SwiGLU MLP\n($d\\to\\frac{8}{3}d\\to d$)",
       NEW, NEW, NEW)

# center "what changed" ledger
cx = 5.55
ax.text(cx, 9.55, "four substitutions", ha="center", fontsize=9.6,
        fontweight="bold", color=NEW)
changes = [
    (8.0, "GELU MLP", "SwiGLU MLP", "gated, $\\frac{8}{3}d$ wide"),
    (6.5, "full MHA", "grouped-query", "share K,V across heads"),
    (5.0, "learned pos.", "RoPE", "rotate Q,K by position"),
    (3.6, "LayerNorm", "RMSNorm", "drop the mean re-centering"),
]
for y, old, new, why in changes:
    ax.annotate("", xy=(8.2, y), xytext=(3.3, y),
                arrowprops=dict(arrowstyle="-|>", color=NEW, lw=1.3, mutation_scale=13,
                                connectionstyle="arc3,rad=0.0"))
    ax.text(cx, y + 0.22, f"{old}  →  {new}", ha="center", fontsize=8.2,
            color=NEW, fontweight="bold")
    ax.text(cx, y - 0.2, why, ha="center", fontsize=7.2, color=EDGE, style="italic")

ax.text(cx, 1.7, "skeleton unchanged:\npre-norm, residual stream,\nsame forward/backward/Adam\n(App. C–D)",
        ha="center", va="center", fontsize=7.8, color=EDGE,
        bbox=dict(boxstyle="round,pad=0.4", fc="#f3f4f6", ec=EDGE, lw=0.8))

fig.tight_layout()
fig.savefig(HERE / "appendix-e-block.svg", bbox_inches="tight")
print("wrote appendix-e-block.svg")
