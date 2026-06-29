"""One attention layer, written out in full (Appendix A, A.19).

A single causal self-attention head computed end to end on a concrete toy input,
so every number in the section is real, not illustrative. The figure shows the
dataflow with tensor shapes (left) and the resulting causal attention matrix as a
lower-triangular heatmap with its actual softmax weights (right).

Convention: A.1's column form -- tokens are COLUMNS of X in R^{d x T};
W_Q,W_K in R^{d_k x d}; W_V in R^{d_v x d}; W_O in R^{d x d_v}; q_i = W_Q x_i.

Pipeline (one head, no LayerNorm shown -- isolated to expose the attention math):
    X (d x T)
      -> Q = W_Q X,  K = W_K X,  V = W_V X        (d_k x T)
      -> S = Q^T K / sqrt(d_k)                     (T x T)
      -> causal mask (j <= i), then softmax rows   -> A (T x T)
      -> O = V A^T                                  (d_v x T)
      -> dX = W_O O                                 (d x T)
      -> H = X + dX   (residual)                    (d x T)

Deterministic (fixed integer weights; no RNG). Outputs:
  qkv-one-layer-forward.svg
  qkv-one-layer-forward.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

HERE = pathlib.Path(__file__).resolve().parent

# =============================== THE COMPUTATION ===========================
# A.1 column convention: T=3 tokens are the COLUMNS of X (d=4); head dim d_k=d_v=2.
# Integer weights chosen so Q,K,V are integer; the softmax makes the only decimals.
d, d_k, T = 4, 2, 3
X = np.array([[1.0, 0.0, 1.0],
              [0.0, 1.0, 1.0],
              [1.0, 0.0, 1.0],
              [0.0, 1.0, 1.0]])                      # d x T (4x3); columns = tokens
W_Q = np.array([[1, 0, 1, 0], [0, 1, 0, 1]], dtype=float)   # d_k x d (2x4)
W_K = np.array([[1, 0, 1, 0], [0, 1, 0, 1]], dtype=float)   # d_k x d (2x4)
W_V = np.array([[0, 1, 0, 1], [1, 0, 1, 0]], dtype=float)   # d_v x d (2x4)
W_O = np.array([[1, 0], [0, 1], [1, 0], [0, 1]], dtype=float)  # d x d_v (4x2)

Q = W_Q @ X                                          # d_k x T (2x3), columns q_i
K = W_K @ X
Vv = W_V @ X
S_scaled = (Q.T @ K) / np.sqrt(d_k)                  # T x T (3x3); S_ij = q_i . k_j / sqrt(d_k)
mask = np.triu(np.ones((T, T), dtype=bool), k=1)     # True above diagonal -> masked
S_masked = np.where(mask, -np.inf, S_scaled)
A = np.exp(S_masked - np.nanmax(S_masked, axis=1, keepdims=True))
A = np.where(mask, 0.0, A)
A = A / A.sum(axis=1, keepdims=True)                 # T x T, row i = query
O = Vv @ A.T                                         # d_v x T (2x3), columns o_i
dX = W_O @ O                                         # d x T (4x3), columns W_O o_i
H = X + dX                                           # d x T (4x3)

data = {
    "convention": "A.1 column form: tokens are columns of X (d x T); W_Q,W_K in R^{d_k x d}; W_O in R^{d x d_v}.",
    "dims": {"d": d, "d_k": d_k, "d_v": d_k, "T": T},
    "X": X.tolist(), "W_Q": W_Q.tolist(), "W_K": W_K.tolist(),
    "W_V": W_V.tolist(), "W_O": W_O.tolist(),
    "Q": Q.tolist(), "K": K.tolist(), "V": Vv.tolist(),
    "S_scaled": np.round(S_scaled, 4).tolist(),
    "A": np.round(A, 4).tolist(), "O": np.round(O, 4).tolist(),
    "dX": np.round(dX, 4).tolist(), "H": np.round(H, 4).tolist(),
    "note": "causal single-head attention; A = softmax row-wise over j<=i; H = X + W_O (V A^T).",
}
with open(HERE / "qkv-one-layer-forward.json", "w") as f:
    json.dump(data, f, indent=1)

print("Q=\n", Q, "\nK=\n", K, "\nV=\n", Vv)
print("S/sqrt(dk)=\n", np.round(S_scaled, 3))
print("A=\n", np.round(A, 3))
print("O=\n", np.round(O, 3), "\nH=\n", np.round(H, 3))

# =============================== STYLE =====================================
BG    = "#fbfcfe"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
QK_E  = "#6366f1"; QK_D = "#4338ca"        # indigo: scores / QK
VAL_E = "#f59e0b"; VAL_D = "#b45309"       # amber: values
OV_E  = "#10b981"; OV_D = "#047857"        # emerald: output / residual

def stage(ax, cx, cy, w, h, title, shape, ec, *, fc="white"):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.10",
                 fc=fc, ec=ec, lw=1.7, zorder=4))
    ax.text(cx, cy + 0.16, title, ha="center", va="center",
            fontsize=9.4, color=INK, fontweight="bold", zorder=5)
    ax.text(cx, cy - 0.20, shape, ha="center", va="center",
            fontsize=8.0, color=MUTE, zorder=5, family="monospace")

def arrow(ax, p0, p1, *, color=MUTE, lw=1.6, label=None, lx=0.0, ly=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=13,
                 lw=lw, color=color, shrinkA=2, shrinkB=2, zorder=3))
    if label:
        ax.text((p0[0] + p1[0]) / 2 + lx, (p0[1] + p1[1]) / 2 + ly, label,
                ha="center", va="center", fontsize=7.8, color=color,
                fontstyle="italic", zorder=6)

# =============================== FIGURE ====================================
fig = plt.figure(figsize=(12.6, 5.4))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(1, 2, width_ratios=[1.95, 1.0], wspace=0.16)
axL = fig.add_subplot(gs[0, 0]); axR = fig.add_subplot(gs[0, 1])
for ax in (axL, axR):
    ax.set_facecolor(BG)

# ---- left: dataflow -------------------------------------------------------
axL.set_xlim(0, 12.4); axL.set_ylim(0, 5.2); axL.axis("off")
axL.text(0.2, 4.92, "One attention layer, end to end",
         fontsize=13.2, color=INK, fontweight="bold", ha="left")
axL.text(0.2, 4.55, r"single causal head, A.1 column convention; $T=3$, $d=4$, "
         r"$d_k=2$ (tokens are columns of $X$; the softmax makes the only decimals)",
         fontsize=8.6, color=MUTE, ha="left")

row_y = 3.2
stage(axL, 1.2, row_y, 1.6, 1.0, r"$X$", "d x T (4x3)", OV_D)
stage(axL, 4.0, row_y, 1.9, 1.0, r"$Q,K,V=W_{\!*}X$", "d_k x T (2x3)", QK_D)
stage(axL, 7.1, row_y, 2.1, 1.0, r"$S=Q^\top K/\sqrt{d_k}$", "T x T (3x3)", QK_D)
stage(axL, 10.4, row_y, 1.9, 1.0, r"$A=\mathrm{softmax}$", "T x T (3x3)", QK_E, fc="#eef0fe")

low_y = 1.1
stage(axL, 10.4, low_y, 1.9, 1.0, r"$O=VA^\top$", "d_v x T (2x3)", VAL_D, fc="#fef6e6")
stage(axL, 7.1, low_y, 2.1, 1.0, r"$\Delta X=W_O O$", "d x T (4x3)", OV_D, fc="#e9f9f1")
stage(axL, 3.5, low_y, 2.4, 1.0, r"$H=X+\Delta X$", "d x T (4x3)", OV_E, fc="#e9f9f1")

arrow(axL, (2.0, row_y), (3.05, row_y), label="project", ly=0.26, color=QK_D)
arrow(axL, (4.95, row_y), (6.05, row_y), label="score", ly=0.26, color=QK_D)
arrow(axL, (8.15, row_y), (9.45, row_y), label="mask + softmax", ly=0.55, color=QK_E)
arrow(axL, (10.4, row_y - 0.5), (10.4, low_y + 0.5), label="weight V", lx=1.05, color=VAL_D)
arrow(axL, (9.45, low_y), (8.15, low_y), label="write", ly=0.26, color=OV_D)
arrow(axL, (6.05, low_y), (4.7, low_y), label="add", ly=0.26, color=OV_D)
# residual skip from X down to the add
axL.add_patch(FancyArrowPatch((1.2, row_y - 0.5), (3.5, low_y + 0.5),
              arrowstyle="-|>", mutation_scale=13, lw=1.5, color=OV_E,
              linestyle=(0, (4, 3)), connectionstyle="arc3,rad=-0.25",
              shrinkA=2, shrinkB=2, zorder=3))
axL.text(1.6, 2.0, "residual\nskip", ha="center", va="center",
         fontsize=7.8, color=OV_D, fontstyle="italic", zorder=6)

# ---- right: the causal attention matrix A ---------------------------------
axR.set_xlim(-0.7, T + 0.2); axR.set_ylim(-0.9, T + 0.7); axR.axis("off")
axR.text((T - 1) / 2.0, T + 0.42, r"causal attention matrix $A$",
         fontsize=11.0, color=INK, fontweight="bold", ha="center")
axR.text((T - 1) / 2.0, T + 0.02, r"row $i$ = query, col $j$ = key; masked for $j>i$",
         fontsize=8.0, color=MUTE, ha="center")
for i in range(T):
    yy = T - 1 - i
    for j in range(T):
        masked = j > i
        val = A[i, j]
        fc = "#f1f5f9" if masked else plt.cm.Blues(0.18 + 0.7 * val)
        axR.add_patch(Rectangle((j - 0.5, yy - 0.5), 1, 1, fc=fc,
                      ec="#cbd5e1", lw=1.0, zorder=2))
        if masked:
            axR.text(j, yy, "·", ha="center", va="center",
                     fontsize=12, color=FAINT, zorder=3)
        else:
            axR.text(j, yy, f"{val:.2f}", ha="center", va="center",
                     fontsize=9.6, color=(INK if val < 0.6 else "white"),
                     fontweight="bold", zorder=3)
    axR.text(-0.62, yy, f"$i={i+1}$", ha="right", va="center",
             fontsize=8.2, color=MUTE)
for j in range(T):
    axR.text(j, -0.66, f"$j={j+1}$", ha="center", va="center",
             fontsize=8.2, color=MUTE)
axR.text((T - 1) / 2.0, -1.02, "each row sums to 1; mass on the diagonal-and-below",
         fontsize=7.6, color=FAINT, ha="center", fontstyle="italic")

fig.savefig(HERE / "qkv-one-layer-forward.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-one-layer-forward.svg / .json")
