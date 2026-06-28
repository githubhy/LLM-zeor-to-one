"""The parameters in one attention head: a 'two-rail' block-diagram schematic (Appendix A, A.1).

A single panel, fully deterministic, no randomness (a structural schematic, not a
measurement).  Column-vector convention, matching the rest of Appendix A.

The head is drawn as TWO color-coded circuits, the spatial form of the collapse the
appendix proves next:

  QK circuit (indigo, top rail) -- routing, "where to look":
      x_i,x_j --> [W_Q],[W_K] --> q_i,k_j --> score q.k/sqrt(d_k) --> causal softmax --> a_ij
  OV circuit (emerald, bottom rail) -- content, "what to bring":
      x_j --> [W_V] --> v_j --> weighted sum  o_i = sum_j a_ij v_j --> [W_O] --> Delta x_i

The a_ij weights couple the two rails (top -> bottom); an amber arc carries the residual
skip x_i to the final add.  The FOUR learned matrices W_Q,W_K,W_V,W_O are the only
parameters (W_Q,W_K form M = W_Q^T W_K, A.2; W_V,W_O form W_OV = W_O W_V, A.3);
q,k,v,o are computed intermediates.  Shapes are symbolic (d, d_k, d_v); concrete
magnitudes are tabled in A.13.

Per-head parameter count, derived from the shapes shown:
  |W_Q| + |W_K| + |W_V| + |W_O| = 2 d_k d + 2 d_v d = 2 d (d_k + d_v).
For the base Transformer (d=512, d_k=d_v=64; ref 54) that is 2*512*128 = 131,072.

Outputs:
  qkv-head-parameters.svg
  qkv-head-parameters.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Provenance / regeneration data (symbolic shapes + one sourced instantiation).
# ---------------------------------------------------------------------------
d_base, dk_base, dv_base = 512, 64, 64                    # base Transformer (ref 54)
params_per_head = 2 * d_base * dk_base + 2 * d_base * dv_base
data = {
    "convention": "column-vector, single attention head (Appendix A, A.1)",
    "shapes": {
        "x": "R^d", "W_Q": "R^{d_k x d}", "W_K": "R^{d_k x d}",
        "W_V": "R^{d_v x d}", "q": "R^{d_k}", "k": "R^{d_k}",
        "v": "R^{d_v}", "o": "R^{d_v}", "W_O": "R^{d x d_v}", "delta_x": "R^d",
    },
    "circuits": {"QK": "M = W_Q^T W_K (A.2)", "OV": "W_OV = W_O W_V (A.3)"},
    "param_count_per_head": "2*d*d_k + 2*d*d_v = 2 d (d_k + d_v)",
    "base_transformer": {
        "d": d_base, "d_k": dk_base, "d_v": dv_base, "h": 8,
        "params_per_head": params_per_head,
        "source": "ref 54 (Vaswani et al. 2017); magnitudes tabled in A.13",
    },
}
with open(HERE / "qkv-head-parameters.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== STYLE =====================================
BG    = "#fbfcfe"
QK    = "#eef0fe"; QK_E = "#6366f1"; QK_D = "#4338ca"     # indigo: QK circuit
OV    = "#e9f9f1"; OV_E = "#10b981"; OV_D = "#047857"     # emerald: OV circuit
NODE  = "#f1f5f9"; NODE_E = "#cbd5e1"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
SKIP  = "#f59e0b"                                         # amber: residual skip
BUS   = "#eef2ff"; BUS_E = "#a5b4fc"


def panel(ax, x, y, w, h, fc, ec, label, lblcolor):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.22",
                                fc=fc, ec=ec, lw=1.3, alpha=0.95, zorder=1))
    ax.text(x + 0.34, y + h - 0.34, label, ha="left", va="top",
            fontsize=10.5, color=lblcolor, fontweight="bold", zorder=6)


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
        ax.text(cx, cy + h * 0.20, line1, ha="center", va="center", fontsize=fs, color=INK, zorder=5)
        ax.text(cx, cy - h * 0.27, line2, ha="center", va="center", fontsize=7.6, color=MUTE, zorder=5)
    else:
        ax.text(cx, cy, line1, ha="center", va="center", fontsize=fs, color=INK, zorder=5)


def arrow(ax, p0, p1, *, color=INK, lw=1.7, rad=0.0, ls="-", mut=15, z=3):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=mut,
                                 lw=lw, color=color, linestyle=ls, shrinkA=4,
                                 shrinkB=4, connectionstyle=f"arc3,rad={rad}", zorder=z))


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
ax.text(0.3, 9.16, r"four learned matrices $W_Q,W_K,W_V,W_O$ map the residual stream "
        r"through two circuits; $\mathbf{q},\mathbf{k},\mathbf{v},\mathbf{o}$ are computed, not stored",
        fontsize=9.5, color=MUTE, ha="left")

# circuit panels
panel(ax, 2.7, 5.05, 9.0, 2.95, QK, QK_E, r"QK circuit  ·  routing — where to look", QK_D)
panel(ax, 2.7, 0.45, 11.2, 2.95, OV, OV_E, r"OV circuit  ·  content — what to bring", OV_D)

# residual-stream input
card(ax, 1.35, 4.4, 1.9, 2.2, r"$\mathbf{x}_i,\mathbf{x}_j$", r"$\in\mathbb{R}^{d}$",
     BUS, BUS_E, namec=QK_D, fs=13)
lbl(ax, 1.35, 5.15, "residual stream", color=INK, fs=8.6, weight="bold")

# QK rail: W_Q / W_K -> score -> softmax -> a
yqk = 6.5
card(ax, 4.15, 7.05, 1.5, 0.95, r"$W_Q$", r"$\mathbb{R}^{d_k\times d}$", "white", QK_E, namec=QK_D, fs=12)
card(ax, 4.15, 5.85, 1.5, 0.95, r"$W_K$", r"$\mathbb{R}^{d_k\times d}$", "white", QK_E, namec=QK_D, fs=12)
node(ax, 6.85, yqk, 2.0, 1.15, r"$\dfrac{\mathbf{q}_i^{\top}\mathbf{k}_j}{\sqrt{d_k}}$", "score", fs=12)
node(ax, 9.75, yqk, 2.0, 1.15, r"softmax$_{j\leq i}$", r"causal $\Rightarrow a_{ij}$", fs=10)
arrow(ax, (2.30, 4.75), (3.40, 7.05), color=FAINT, lw=1.2, rad=0.18)
arrow(ax, (2.30, 4.55), (3.40, 5.85), color=FAINT, lw=1.2, rad=-0.10)
arrow(ax, (4.90, 7.05), (5.85, yqk + 0.18), color=QK_E, rad=-0.12)
arrow(ax, (4.90, 5.85), (5.85, yqk - 0.18), color=QK_E, rad=0.12)
lbl(ax, 5.45, 7.08, r"$\mathbf{q}_i$", color=QK_D, fs=9)
lbl(ax, 5.45, 5.68, r"$\mathbf{k}_j$", color=QK_D, fs=9)
arrow(ax, (7.85, yqk), (8.75, yqk), color=MUTE)

# OV rail: W_V -> weighted sum -> o -> W_O
yov = 1.9
card(ax, 4.15, yov, 1.5, 1.0, r"$W_V$", r"$\mathbb{R}^{d_v\times d}$", "white", OV_E, namec=OV_D, fs=12)
node(ax, 9.75, yov, 2.25, 1.2, r"$\sum_{j\leq i} a_{ij}\mathbf{v}_j$", r"head output $\mathbf{o}_i\in\mathbb{R}^{d_v}$", fs=11)
card(ax, 12.55, yov, 1.5, 1.0, r"$W_O$", r"$\mathbb{R}^{d\times d_v}$", "white", OV_E, namec=OV_D, fs=12)
arrow(ax, (2.30, 4.05), (3.40, yov + 0.10), color=FAINT, lw=1.2, rad=-0.16)
arrow(ax, (4.90, yov), (8.62, yov), color=OV_E)
lbl(ax, 6.7, yov + 0.34, r"$\mathbf{v}_j\in\mathbb{R}^{d_v}$", color=OV_D, fs=8.6)
arrow(ax, (10.88, yov), (11.80, yov), color=OV_E)
lbl(ax, 11.34, yov + 0.32, r"$\mathbf{o}_i$", color=OV_D, fs=9)

# a_ij couples the rails (top -> bottom)
arrow(ax, (9.75, yqk - 0.62), (9.75, yov + 0.62), color=MUTE, lw=1.5, ls=(0, (4, 2)))
lbl(ax, 10.18, 4.2, r"$a_{ij}$ weights", color=MUTE, fs=8.2, ha="left")

# output projection -> residual add (top-right); residual skip wraps over the top
addc = (15.2, 8.45)
ax.add_patch(Circle(addc, 0.46, fc="white", ec=INK, lw=1.8, zorder=5))
ax.text(addc[0], addc[1], r"$+$", ha="center", va="center", fontsize=18, zorder=6)

# sublayer output Delta x_i rises on the clear right margin into the add
ax.add_patch(FancyArrowPatch((13.30, yov), (addc[0], addc[1] - 0.46),
             arrowstyle="-|>", mutation_scale=15, lw=1.7, color=OV_E,
             connectionstyle="angle,angleA=0,angleB=90,rad=20", shrinkA=4, shrinkB=4, zorder=3))
lbl(ax, 14.92, 3.15, r"$\Delta\mathbf{x}_i=W_O\mathbf{o}_i$", color=OV_D, fs=8.6, ha="right")
lbl(ax, 14.92, 2.77, r"$\in\mathbb{R}^{d}$", color=MUTE, fs=7.6, ha="right")

# elegant amber residual skip: rises left of the panels, runs along the top into the add
ax.add_patch(FancyArrowPatch((1.35, 5.55), (addc[0] - 0.46, addc[1]),
             arrowstyle="-|>", mutation_scale=15, lw=1.8, color=SKIP,
             connectionstyle="angle,angleA=90,angleB=0,rad=20", shrinkA=4, shrinkB=4, zorder=3))
lbl(ax, 8.0, 8.74, r"residual skip  $\mathbf{x}_i$", color="#b45309", fs=8.6, style="italic")

# merged residual-stream output
ax.add_patch(FancyArrowPatch((addc[0] + 0.46, addc[1]), (16.2, addc[1]),
             arrowstyle="-|>", mutation_scale=15, lw=1.6, color=INK,
             shrinkA=4, shrinkB=4, zorder=3))
lbl(ax, 16.15, 8.05, r"$\mathbf{x}_i+\Delta\mathbf{x}_i$", color=INK, fs=8.4, ha="right")

# footer: parameter budget
ax.plot([0.3, 16.1], [0.18, 0.18], color="#e2e8f0", lw=1.0, zorder=0)
ax.text(0.3, -0.18, r"Per head: $|W_Q|{+}|W_K|{+}|W_V|{+}|W_O| = 2d(d_k{+}d_v)$ "
        r"parameters  —  base Transformer $(d{=}512,\,d_k{=}d_v{=}64)$: "
        r"$2{\cdot}512{\cdot}128 = 131{,}072$ per head",
        fontsize=8.6, color=MUTE, ha="left", va="center")

fig.savefig(HERE / "qkv-head-parameters.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-head-parameters.svg and .json; params/head (base) =", params_per_head)
