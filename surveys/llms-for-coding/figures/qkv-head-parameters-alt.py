"""The parameters in one attention head: 'canonical attention-block' view (Appendix A, A.1).

Alternative rendering of `qkv-head-parameters.py` (the shipped 'two-rail' diagram).
Same head, same parameters; here the attention math is grouped into one familiar
'scaled dot-product attention' centerpiece, flanked by the three input projections
and the output projection.  Fully deterministic, no randomness.  Linked from the
Figure A.1 caption as the alternative view.

  x_i,x_j --> [W_Q],[W_K],[W_V] --> q,k,v --> | scaled dot-product attention |
              (input projections)              |  a_ij = softmax(q.k/sqrt dk)  |
                                               |  o_i  = sum_j a_ij v_j        |
                                                        --> [W_O] --> Delta x_i --(+)
  residual skip x_i wraps over the top into the add.

Per-head parameter count (from the shapes shown): 2 d_k d + 2 d_v d = 2 d (d_k + d_v);
base Transformer (d=512, d_k=d_v=64; ref 54) = 131,072.

Outputs:
  qkv-head-parameters-alt.svg
  qkv-head-parameters-alt.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE = pathlib.Path(__file__).resolve().parent

d_base, dk_base, dv_base = 512, 64, 64
params_per_head = 2 * d_base * dk_base + 2 * d_base * dv_base
with open(HERE / "qkv-head-parameters-alt.json", "w") as f:
    json.dump({
        "view": "canonical scaled-dot-product-attention block",
        "alt_of": "qkv-head-parameters.svg",
        "param_count_per_head": "2*d*d_k + 2*d*d_v = 2 d (d_k + d_v)",
        "base_transformer": {"d": d_base, "d_k": dk_base, "d_v": dv_base,
                             "params_per_head": params_per_head,
                             "source": "ref 54; magnitudes in A.13"},
    }, f, indent=1)

# =============================== STYLE =====================================
BG    = "#fbfcfe"
QK    = "#eef0fe"; QK_E = "#6366f1"; QK_D = "#4338ca"
OV    = "#e9f9f1"; OV_E = "#10b981"; OV_D = "#047857"
NODE  = "#f1f5f9"; NODE_E = "#cbd5e1"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
SKIP  = "#f59e0b"
BUS   = "#eef2ff"; BUS_E = "#a5b4fc"


def card(ax, cx, cy, w, h, name, shape, fc, ec, *, namec=INK, fs=14, shadow=True):
    box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.14",
                         fc=fc, ec=ec, lw=1.7, zorder=4)
    if shadow:
        box.set_path_effects([pe.withSimplePatchShadow(
            offset=(2.6, -2.6), shadow_rgbFace=FAINT, alpha=0.30)])
    ax.add_patch(box)
    ax.text(cx, cy + h * 0.16, name, ha="center", va="center",
            fontsize=fs, color=namec, fontweight="bold", zorder=5)
    if shape:
        ax.text(cx, cy - h * 0.27, shape, ha="center", va="center",
                fontsize=8.0, color=MUTE, zorder=5)


def node(ax, cx, cy, w, h, line1, line2=None, *, fc=NODE, ec=NODE_E, fs=10):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.2, zorder=4))
    if line2:
        ax.text(cx, cy + h * 0.22, line1, ha="center", va="center", fontsize=fs, color=INK, zorder=5)
        ax.text(cx, cy - h * 0.28, line2, ha="center", va="center", fontsize=7.6, color=MUTE, zorder=5)
    else:
        ax.text(cx, cy, line1, ha="center", va="center", fontsize=fs, color=INK, zorder=5)


def arrow(ax, p0, p1, *, color=INK, lw=1.7, rad=0.0, ls="-", mut=15, z=3, cs=None):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=mut,
                                 lw=lw, color=color, linestyle=ls, shrinkA=4, shrinkB=4,
                                 connectionstyle=cs or f"arc3,rad={rad}", zorder=z))


def lbl(ax, x, y, s, *, color=MUTE, fs=8.2, ha="center", style="normal", weight="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color,
            fontstyle=style, fontweight=weight, zorder=6)


# =============================== FIGURE ====================================
fig, ax = plt.subplots(figsize=(13.4, 6.6))
fig.patch.set_facecolor("white")
ax.set_facecolor(BG)
ax.set_xlim(0, 16.4); ax.set_ylim(0, 10.0); ax.axis("off")

ax.text(0.3, 9.62, "The parameters in one attention head",
        fontsize=14, color=INK, fontweight="bold", ha="left")
ax.text(0.3, 9.16, r"three input projections feed scaled dot-product attention; "
        r"an output projection writes the result back",
        fontsize=9.5, color=MUTE, ha="left")

# input bus
card(ax, 1.3, 4.45, 1.8, 3.8, "", "", BUS, BUS_E)
lbl(ax, 1.3, 5.75, "residual", color=INK, fs=9, weight="bold")
lbl(ax, 1.3, 5.40, "stream", color=INK, fs=9, weight="bold")
lbl(ax, 1.3, 4.55, r"$\mathbf{x}_i$", color=QK_D, fs=13)
lbl(ax, 1.3, 3.80, r"$\mathbf{x}_j$", color=QK_D, fs=13)
lbl(ax, 1.3, 3.05, r"$\in\mathbb{R}^{d}$", color=MUTE, fs=8.2)

# input projections
px = 4.25
card(ax, px, 6.45, 1.7, 1.0, r"$W_Q$", r"$\mathbb{R}^{d_k\times d}$", "white", QK_E, namec=QK_D, fs=12)
card(ax, px, 4.95, 1.7, 1.0, r"$W_K$", r"$\mathbb{R}^{d_k\times d}$", "white", QK_E, namec=QK_D, fs=12)
card(ax, px, 2.80, 1.7, 1.0, r"$W_V$", r"$\mathbb{R}^{d_v\times d}$", "white", OV_E, namec=OV_D, fs=12)
lbl(ax, px, 7.35, "input projections", color=MUTE, fs=8.6, style="italic")
arrow(ax, (2.20, 4.95), (px - 0.85, 6.45), color=FAINT, lw=1.2, rad=0.12)
arrow(ax, (2.20, 4.55), (px - 0.85, 4.95), color=FAINT, lw=1.2)
arrow(ax, (2.20, 4.05), (px - 0.85, 2.80), color=FAINT, lw=1.2, rad=-0.12)

# centerpiece: scaled dot-product attention
ax.add_patch(FancyBboxPatch((6.05, 1.95), 4.55, 5.2,
             boxstyle="round,pad=0.02,rounding_size=0.22",
             fc="#f8fafc", ec="#64748b", lw=1.5, zorder=2))
ax.text(8.32, 6.78, "scaled dot-product attention", ha="center",
        fontsize=10.2, color=INK, fontweight="bold", zorder=5)
node(ax, 8.32, 5.35, 3.85, 1.3,
     r"$a_{ij}=\mathrm{softmax}_{j\leq i}\left(\mathbf{q}_i^{\top}\mathbf{k}_j/\sqrt{d_k}\right)$",
     "attention weights (causal)", fc="white", ec=QK_E, fs=10.5)
node(ax, 8.32, 3.15, 3.85, 1.3,
     r"$\mathbf{o}_i=\sum_{j\leq i} a_{ij}\,\mathbf{v}_j$",
     r"head output $\in\mathbb{R}^{d_v}$", fc="white", ec=OV_E, fs=11.5)
arrow(ax, (8.32, 4.70), (8.32, 3.80), color=MUTE, lw=1.4)

arrow(ax, (px + 0.85, 6.45), (6.05, 5.75), color=QK_E, rad=-0.10)
lbl(ax, 5.80, 6.40, r"$\mathbf{q}_i$", color=QK_D, fs=9)
arrow(ax, (px + 0.85, 4.95), (6.05, 5.20), color=QK_E)
lbl(ax, 5.80, 5.30, r"$\mathbf{k}_j$", color=QK_D, fs=9)
arrow(ax, (px + 0.85, 2.80), (6.05, 3.00), color=OV_E, rad=0.10)
lbl(ax, 5.80, 2.78, r"$\mathbf{v}_j$", color=OV_D, fs=9)

# output projection
card(ax, 12.2, 3.15, 1.7, 1.1, r"$W_O$", r"$\mathbb{R}^{d\times d_v}$", "white", OV_E, namec=OV_D, fs=12)
lbl(ax, 12.2, 4.25, "output projection", color=MUTE, fs=8.6, style="italic")
arrow(ax, (10.60, 3.15), (11.35, 3.15), color=OV_E)
lbl(ax, 10.98, 3.46, r"$\mathbf{o}_i$", color=OV_D, fs=9)

# residual add (top-right) + clean top-routed skip + right-margin output riser
addc = (15.2, 8.45)
ax.add_patch(Circle(addc, 0.46, fc="white", ec=INK, lw=1.8, zorder=5))
ax.text(addc[0], addc[1], r"$+$", ha="center", va="center", fontsize=18, zorder=6)
arrow(ax, (13.05, 3.15), (addc[0], addc[1] - 0.46), color=OV_E,
      cs="angle,angleA=0,angleB=90,rad=20")
lbl(ax, 14.92, 4.0, r"$\Delta\mathbf{x}_i=W_O\mathbf{o}_i$", color=OV_D, fs=8.6, ha="right")
lbl(ax, 14.92, 3.62, r"$\in\mathbb{R}^{d}$", color=MUTE, fs=7.6, ha="right")
arrow(ax, (1.3, 6.40), (addc[0] - 0.46, addc[1]), color=SKIP, lw=1.8,
      cs="angle,angleA=90,angleB=0,rad=20")
lbl(ax, 8.0, 8.74, r"residual skip  $\mathbf{x}_i$", color="#b45309", fs=8.6, style="italic")
arrow(ax, (addc[0] + 0.46, addc[1]), (16.2, addc[1]), color=INK, lw=1.6)
lbl(ax, 16.15, 8.05, r"$\mathbf{x}_i+\Delta\mathbf{x}_i$", color=INK, fs=8.4, ha="right")

# footer
ax.plot([0.3, 16.1], [1.05, 1.05], color="#e2e8f0", lw=1.0, zorder=0)
ax.text(0.3, 0.62, r"$W_Q,W_K$ form the QK circuit $M=W_Q^{\top}W_K$;  "
        r"$W_V,W_O$ form the OV circuit $W_{OV}=W_OW_V$  —  "
        r"$2d(d_k{+}d_v)$ params/head $(=131{,}072$ for $d{=}512,\,d_k{=}d_v{=}64)$",
        fontsize=8.5, color=MUTE, ha="left", va="center")

fig.savefig(HERE / "qkv-head-parameters-alt.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-head-parameters-alt.svg and .json")
