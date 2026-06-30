"""Why the QK and OV circuits co-adapt (Appendix A, section A.11, final paragraph).

Two panels, deterministic (fixed numeric constants; no rng needed). Column-vector
convention, matching the rest of Appendix A.

The score-gradient identity of Equation (13) is

    dL/ds_im = a_im * delta_i^T (v_m - o_i),     delta_i = dL/do_i,  o_i = sum_j a_ij v_j (Eq 2)

and because a_im > 0 (a softmax weight), sign(dL/ds_im) = sign(delta_i^T (v_m - o_i)).
Gradient descent (s <- s - eta * dL/ds) therefore RAISES s_im -- attends more to key m --
exactly when delta_i^T (v_m - o_i) < 0, i.e. when pulling the output toward v_m has a
component along the descent direction -delta_i and so reduces the loss.

(left, schematic) The training loop the identity closes: the QK circuit M routes
("where to look"), the OV circuit W_OV fetches ("what to bring"), the output incurs a
loss, and the backprop gradient delta_i splits into two symmetric teaching signals that
feed back into M and W_OV -- so the head is meaningful only as the pair (M, W_OV), never
as the four raw matrices W_Q, W_K, W_V, W_O. This is the optimizer's training loop across steps, NOT a
per-token recursive LMS/RLS update (cf. A.6, which notes attention's adaptation is a
closed-form function of the current input).

(right, computed) The sign condition read geometrically in the head's output space (here
d_v = 2 for plottability; the half-space split is dimension-independent). For a
representative loss gradient delta_i, the hyperplane through o_i with normal delta_i
splits the value points into an attend-more half (the -delta_i side, delta_i^T(v-o_i) < 0,
green -> raise s_ij) and an attend-less half (red -> lower s_ij). o_i is the softmax-weighted
mean of the values (inside their convex hull). The five computed signed dots are printed.

CAVEAT (the paragraph states this explicitly): this descent identity shows the two
circuits CO-ADAPT; it does NOT prove training converges to the specific low-rank routing
(A.8) or copy / induction (A.9) circuits. Those are what a head can implement and, for
induction heads, are observed empirically (A.9), not guaranteed by this identity. The
figure shows one step's sign rule and the coupling, never a trajectory or a built circuit.

Outputs:
  qkv-coadaptation.svg
  qkv-coadaptation.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Polygon

HERE = pathlib.Path(__file__).resolve().parent

# macOS Accelerate / NumPy 2.x raises spurious FP flags inside BLAS matmul;
# the printed results are exact (verified), so silence these non-errors.
np.seterr(divide="ignore", over="ignore", invalid="ignore")

# ---------------------------------------------------------------------------
# Computation (Panel B): the sign condition delta_i^T (v_j - o_i), fixed constants.
# ---------------------------------------------------------------------------
V = np.array([[2.3, 1.6], [-1.8, 1.9], [1.4, -2.0], [-2.1, -1.3], [0.4, 2.6]])
s = np.array([0.9, 0.2, 1.1, -0.3, 0.4])             # raw scores
a = np.exp(s - s.max()); a = a / a.sum()             # softmax weights (all > 0, sum 1)
o = a @ V                                            # output = weighted mean (Eq 2)
delta = np.array([0.85, -0.55])                      # a representative loss gradient dL/do_i
d = (V - o) @ delta                                  # signed dots delta^T (v_j - o)

assert a.min() > 0, "softmax weights must be positive (o_i strictly inside the hull)"

data = {
    "values_V": V.tolist(),
    "scores_s": s.tolist(),
    "softmax_weights_a": [round(float(x), 3) for x in a],
    "output_o_i": [round(float(x), 3) for x in o],
    "loss_gradient_delta_i": delta.tolist(),
    "signed_dots_d_j": [round(float(x), 2) for x in d],
    "attend_more_keys": [int(j + 1) for j in range(len(d)) if d[j] < 0],   # raise s_ij
    "attend_less_keys": [int(j + 1) for j in range(len(d)) if d[j] > 0],   # lower s_ij
    "d_v_plotting": 2,
}
with open(HERE / "qkv-coadaptation.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== FIGURE ====================================
QK_C, OV_C, OUT_C, LOSS_C = "#7c3aed", "#16a34a", "#2563eb", "#6b7280"
EDGE, MORE_C, LESS_C, GUIDE = "#374151", "#16a34a", "#dc2626", "#6b7280"

fig = plt.figure(figsize=(13.0, 5.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.32, 1.0], wspace=0.16)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# ---- Panel A: the co-adaptation training loop (schematic) -----------------
ax1.set_xlim(0, 12); ax1.set_ylim(0, 10); ax1.axis("off")
ax1.set_title(r"The training loop co-adapts the pair $(M,\,W_{OV})$ — not the four raw matrices",
              fontsize=10.5)


def box(x, y, w, h, fc, title, sub):
    ax1.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04",
                                 fc=fc, ec=EDGE, lw=1.0, alpha=0.20))
    ax1.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=9.0)
    if sub:
        ax1.text(x + w / 2, y + h * 0.22, sub, ha="center", va="center",
                 fontsize=7.4, style="italic", color=EDGE)


def arrow(p, q, color=GUIDE, lw=1.0, rad=0.0):
    ax1.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12,
                                  color=color, lw=lw,
                                  connectionstyle=f"arc3,rad={rad}"))


# forward arc (top): M -> W_OV -> o_i -> L
box(0.5, 7.3, 2.7, 1.5, QK_C, r"QK circuit $M{=}W_Q^{\top}W_K$", "where to look")
box(4.1, 7.3, 2.7, 1.5, OV_C, r"OV circuit $W_{OV}{=}W_O W_V$", "what to bring")
box(7.7, 7.45, 2.2, 1.2, OUT_C, r"$\mathbf{o}_i{=}\sum_j a_{ij}\mathbf{v}_j$", "(Eq 2)")
box(10.3, 7.45, 1.4, 1.2, LOSS_C, r"loss $L$", "")

arrow((3.2, 8.05), (4.1, 8.05))
ax1.text(3.65, 8.42, r"pattern $a_{ij}$", ha="center", va="center", fontsize=7.4)
arrow((6.8, 8.05), (7.7, 8.05))
ax1.text(7.25, 8.42, r"fetch $\mathbf{v}_j$", ha="center", va="center", fontsize=7.4)
arrow((9.9, 8.05), (10.3, 8.05))

# backward arc: L -> split node, then two teaching signals back to M and W_OV
split = (5.7, 3.6)
ax1.add_patch(FancyArrowPatch((11.0, 7.45), (split[0] + 0.45, split[1]),
                              arrowstyle="-|>", mutation_scale=12, color=EDGE, lw=1.3,
                              connectionstyle="arc3,rad=-0.28"))
ax1.text(9.1, 5.0, r"backprop  $\boldsymbol{\delta}_i{=}\partial L/\partial\mathbf{o}_i$  (Eq 12)",
         ha="center", va="center", fontsize=7.6, color=EDGE)
ax1.add_patch(Circle(split, 0.45, fc="#fff7ed", ec=LESS_C, lw=1.3))
ax1.text(split[0], split[1], r"$\boldsymbol{\delta}_i$", ha="center", va="center", fontsize=9.5)

# teaching signal 1 -> M (purple, bold)
ax1.add_patch(FancyArrowPatch((split[0] - 0.3, split[1] + 0.3), (1.85, 7.3),
                              arrowstyle="-|>", mutation_scale=13, color=QK_C, lw=1.8,
                              connectionstyle="arc3,rad=0.25"))
ax1.text(1.2, 5.0,
         "train $M$: raise $s_{im}$\n" r"when $\boldsymbol{\delta}_i^{\top}(\mathbf{v}_m{-}\mathbf{o}_i){<}0$" "\n(Eq 13)",
         ha="center", va="center", fontsize=7.3, color=QK_C,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=QK_C, alpha=0.9))

# teaching signal 2 -> W_OV (green, bold)
ax1.add_patch(FancyArrowPatch((split[0] + 0.15, split[1] + 0.35), (5.45, 7.3),
                              arrowstyle="-|>", mutation_scale=13, color=OV_C, lw=1.8,
                              connectionstyle="arc3,rad=-0.18"))
ax1.text(7.0, 5.0,
         "train $W_{OV}$: make the\nfetched content helpful\nunder the current pattern",
         ha="center", va="center", fontsize=7.3, color=OV_C,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=OV_C, alpha=0.9))

# dashed enclosure: (M, W_OV) are the pair
ax1.add_patch(FancyBboxPatch((0.32, 7.05), 6.7, 2.0, boxstyle="round,pad=0.02",
                             fill=False, ec=EDGE, lw=1.1, ls="--"))
ax1.text(3.67, 6.78, r"each conditioned on the other — meaningful only as the pair $(M,\,W_{OV})$",
         ha="center", va="center", fontsize=7.6, color=EDGE)

# A.6 closed-form (not recursive LMS) footnote
ax1.text(6.0, 1.95,
         "the optimizer's training loop across steps — not a per-token recursive LMS/RLS update (cf. A.6)",
         ha="center", va="center", fontsize=7.0, style="italic", color=GUIDE)

# ---- Panel B: the sign condition as a half-space (computed) ----------------
ax2.set_xlim(-3.3, 3.3); ax2.set_ylim(-3.1, 3.3); ax2.set_aspect("equal")
ax2.set_title(r"$\mathrm{sign}\!\left(\partial L/\partial s_{ij}\right)=\mathrm{sign}\,\boldsymbol{\delta}_i^{\top}(\mathbf{v}_j{-}\mathbf{o}_i)$  ($a_{ij}{>}0$, Eq 13)",
              fontsize=9.6)

# half-plane shading from the computed sign field
gx, gy = np.meshgrid(np.linspace(-3.3, 3.3, 220), np.linspace(-3.1, 3.3, 220))
Z = (gx - o[0]) * delta[0] + (gy - o[1]) * delta[1]
ax2.contourf(gx, gy, Z, levels=[Z.min() - 1, 0, Z.max() + 1],
             colors=[MORE_C, LESS_C], alpha=0.10)

# convex hull (dotted) — shows o_i is the weighted mean, an interior point
ang = np.argsort(np.arctan2(V[:, 1] - V[:, 1].mean(), V[:, 0] - V[:, 0].mean()))
ax2.add_patch(Polygon(V[ang], closed=True, fill=False, ec=GUIDE, ls=":", lw=1.0))

# hyperplane line through o, perpendicular to delta
perp = np.array([-delta[1], delta[0]]); perp = perp / np.linalg.norm(perp)
p0, p1 = o - 5 * perp, o + 5 * perp
ax2.plot([p0[0], p1[0]], [p0[1], p1[1]], color=EDGE, lw=1.4)
lab = o + 2.35 * perp                                  # a point on the line, inside the panel
ax2.text(lab[0], lab[1], r"$\boldsymbol{\delta}_i^{\top}(\mathbf{v}{-}\mathbf{o}_i){=}0$",
         fontsize=7.0, color=EDGE, ha="left", va="bottom", rotation=39,
         bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))

# value points, colored by sign; triangles encode raise/lower
for j in range(len(V)):
    more = d[j] < 0
    ax2.scatter(*V[j], s=120, color=(MORE_C if more else LESS_C), alpha=0.85,
                edgecolor=EDGE, lw=0.8, zorder=3)
    ax2.scatter(*V[j], marker=("^" if more else "v"), s=34, color="white", zorder=4)
    dx = 0.18 if V[j, 0] >= o[0] else -0.18
    ax2.annotate(rf"$\mathbf{{v}}_{j+1}\ (d{{=}}{d[j]:+.2f})$",
                 V[j], xytext=(V[j, 0] + dx, V[j, 1] + 0.30),
                 fontsize=7.0, ha=("left" if dx > 0 else "right"),
                 color=(MORE_C if more else LESS_C),
                 bbox=dict(boxstyle="round,pad=0.18", fc="white",
                           ec=(MORE_C if more else LESS_C), alpha=0.85))

# output o_i (star) and gradient arrows
ax2.scatter(*o, marker="*", s=300, color="black", zorder=5)
ax2.annotate(r"$\mathbf{o}_i{=}\sum_j a_{ij}\mathbf{v}_j$", o, xytext=(o[0] + 0.2, o[1] - 0.5),
             fontsize=7.6, ha="left")
ax2.add_patch(FancyArrowPatch(o, o + delta, arrowstyle="-|>", mutation_scale=13,
                              color=LESS_C, lw=1.8, zorder=5))
ax2.text(o[0] + delta[0] + 0.05, o[1] + delta[1], r"$\boldsymbol{\delta}_i$",
         color=LESS_C, fontsize=9.0, ha="left", va="center")
ax2.add_patch(FancyArrowPatch(o, o - delta, arrowstyle="-|>", mutation_scale=11,
                              color=LESS_C, lw=1.1, ls="--", zorder=5))
ax2.text(o[0] - delta[0] - 0.05, o[1] - delta[1], r"$-\boldsymbol{\delta}_i$",
         color=LESS_C, fontsize=8.0, ha="right", va="center")

# side labels for the two half-planes
ax2.text(-3.1, 3.05, "attend-more  ($d{<}0$): raise $s_{ij}$", fontsize=7.6, color=MORE_C,
         ha="left", va="top", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=MORE_C, alpha=0.85))
ax2.text(3.1, -2.9, "attend-less  ($d{>}0$): lower $s_{ij}$", fontsize=7.6, color=LESS_C,
         ha="right", va="bottom", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=LESS_C, alpha=0.85))
ax2.grid(alpha=0.25)
ax2.set_xlabel(r"head output space  ($d_v$; here $d_v{=}2$)", fontsize=8.5)

# ---- shared caveat banner -------------------------------------------------
fig.text(0.5, 0.015,
         "Co-adaptation, not convergence: this one-step identity does not build the low-rank routing (A.8) or "
         "copy/induction (A.9) circuits — those are implementable and, for induction heads, empirically observed (A.9).",
         ha="center", va="bottom", fontsize=7.8, color=EDGE,
         bbox=dict(boxstyle="round,pad=0.4", fc="#fffbeb", ec=GUIDE, lw=1.0))

fig.subplots_adjust(left=0.02, right=0.99, top=0.92, bottom=0.11)
fig.savefig(HERE / "qkv-coadaptation.svg", bbox_inches="tight")
print("wrote qkv-coadaptation.svg / .json")
print(f"  softmax a = {np.round(a,3).tolist()} (sum {a.sum():.3f}, min {a.min():.3f})")
print(f"  o_i = {np.round(o,3).tolist()}  (inside hull)")
print(f"  signed dots d_j = {np.round(d,2).tolist()}")
print(f"  attend-more (raise) keys = {data['attend_more_keys']}, attend-less (lower) = {data['attend_less_keys']}")
