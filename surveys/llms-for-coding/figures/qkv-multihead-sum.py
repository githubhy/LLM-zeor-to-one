"""A layer is a sum of h low-rank circuit pairs (Appendix A, section A.10).

Two panels, two independent seeds, fully deterministic.  Column-vector
convention, matching the rest of Appendix A.

(left) The fan-out / sum-back dataflow of Eq. (10).  One shared residual-stream
vector x_i is read by h = 8 heads in parallel; each head ell is a circuit PAIR
-- a QK routing operator M^(ell) = W_Q^(ell)T W_K^(ell) (rank <= d_k) feeding a
causal softmax pattern a^(ell), which weights an OV content map
W_OV^(ell) = W_O^(ell) W_V^(ell) (rank <= d_v) -- and the h per-head writes
o^(ell) SUM into one update Delta x_i.  The block identity behind this is EXACT,
not an approximation:  W^O [o^(1);...;o^(h)] = sum_ell W_O^(ell) o^(ell), where
W^O = [W_O^(1) ... W_O^(h)] is the output projection cut into h horizontal
d x d_v blocks.  We witness the exactness numerically: for a RANDOM W^O
(d_model=512, h=8, d_v=64) the max abs difference between concatenate-then-project
and the sum of per-head slices is ~1e-14 (machine epsilon).  This is a check of
the algebra -- it holds for ANY W^O -- not an empirical property of trained
weights.

(right) Plurality made numerical, plus the conserved budget.  Eight INDEPENDENT
QK circuits M^(ell) (separate random draws; "independent" per A.10, NOT
orthogonal or disjoint by construction), each genuinely rank <= d_k, read ONE
shared token stream X and route it to DIFFERENT positions.  The 8x8 matrix is the
pairwise routing dissimilarity -- the total-variation distance between heads'
causal attention rows, averaged over query positions -- exactly 0 on the diagonal
(a head routes identically to itself) and large off-diagonal (heads route
differently), yet never reaching 1 (the heads are not disjoint).  The top strip
tiles the conserved budget h*d_k = 8*64 = 512 = d_model: the eight heads occupy
one full-width head's parameter/width budget.

Demo scale for the right panel is d=64, dk=8, T=9 purely for plottability; the
grounded base-Transformer dims (d_model=512, d_k=d_v=64, h=8; ref 54) appear in
the left panel and the budget strip.  The X-scaling 0.22 is a legibility choice
only -- it softens otherwise near-one-hot patterns into a readable graded regime;
the "heads route differently" conclusion strengthens at scale 1.0.

Outputs:
  qkv-multihead-sum.svg
  qkv-multihead-sum.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

HERE = pathlib.Path(__file__).resolve().parent

# macOS Accelerate / NumPy 2.x raises spurious FP flags inside BLAS matmul;
# the printed results are exact (verified), so silence these non-errors.
np.seterr(divide="ignore", over="ignore", invalid="ignore")

# ---------------------------------------------------------------------------
# Computation 1 (Panel A witness): the block identity is EXACT for ANY W^O.
#   W^O [o^(1);...;o^(h)]  ==  sum_ell W_O^(ell) o^(ell)
# ---------------------------------------------------------------------------
d_model, h, dv = 512, 8, 64
rngA = np.random.default_rng(10)
WO = rngA.standard_normal((d_model, h * dv))         # output projection d x (h*dv)
o_stack = rngA.standard_normal((h * dv,))            # stacked per-head outputs
lhs = WO @ o_stack                                   # concatenate-then-project
rhs = np.zeros(d_model)
for l in range(h):                                   # sum of per-head slices
    rhs += WO[:, l * dv:(l + 1) * dv] @ o_stack[l * dv:(l + 1) * dv]
additivity_maxabsdiff = float(np.max(np.abs(lhs - rhs)))

# ---------------------------------------------------------------------------
# Computation 2 (Panel B): h independent low-rank QK circuits route ONE shared
# stream to DIFFERENT positions.  Routing dissimilarity = mean causal-row TV.
# ---------------------------------------------------------------------------
d, dk, hB, T = 64, 8, 8, 9             # reduced demo scale (grounded dims at left)
X_SCALE = 0.22                         # legibility only (softens near-one-hot rows)
rngB = np.random.default_rng(7)
X = rngB.standard_normal((T, d)) * X_SCALE


def causal_softmax_rows(M):
    S = (X @ M @ X.T) / np.sqrt(dk)             # T x T scores
    mask = np.tril(np.ones((T, T), dtype=bool))
    S = np.where(mask, S, -np.inf)
    S = S - S.max(axis=1, keepdims=True)
    E = np.where(mask, np.exp(S), 0.0)
    return E / E.sum(axis=1, keepdims=True)


patterns, ranks = [], []
for l in range(hB):
    WQ = rngB.standard_normal((dk, d))
    WK = rngB.standard_normal((dk, d))
    M = WQ.T @ WK                               # rank <= dk
    ranks.append(int(np.linalg.matrix_rank(M)))
    patterns.append(causal_softmax_rows(M))

D = np.zeros((hB, hB))
for a in range(hB):
    for b in range(hB):
        tv = [0.5 * np.sum(np.abs(patterns[a][i, :i + 1] - patterns[b][i, :i + 1]))
              for i in range(1, T)]             # skip i=0 (trivially identical)
        D[a, b] = float(np.mean(tv))

offdiag = D[~np.eye(hB, dtype=bool)]
offdiag_mean, offdiag_min, offdiag_max = (float(offdiag.mean()),
                                          float(offdiag.min()),
                                          float(offdiag.max()))
diag_maxabs = float(np.abs(np.diag(D)).max())

data = {
    "panel_a": {
        "d_model": d_model, "h": h, "d_v": dv,
        "additivity_maxabsdiff": additivity_maxabsdiff,
        "budget": {"h": h, "d_k": dv, "h_times_dk": h * dv, "d_model": d_model},
    },
    "panel_b": {
        "demo_d": d, "demo_d_k": dk, "h": hB, "T": T, "X_scale": X_SCALE,
        "circuit_ranks": ranks,
        "dissim_diag_maxabs": diag_maxabs,
        "dissim_offdiag_mean": offdiag_mean,
        "dissim_offdiag_min": offdiag_min,
        "dissim_offdiag_max": offdiag_max,
    },
}
with open(HERE / "qkv-multihead-sum.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== FIGURE ====================================
PALETTE = ["#7c3aed", "#16a34a", "#dc2626", "#2563eb",
           "#d97706", "#0891b2", "#db2777", "#65a30d"]      # one color per head
QK_C, OV_C, EDGE, GUIDE = "#7c3aed", "#16a34a", "#374151", "#6b7280"

fig = plt.figure(figsize=(12.6, 5.2))
gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1.0], wspace=0.30)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# ---- Panel A: fan-out / sum-back dataflow schematic -----------------------
ax1.set_xlim(0, 12.4); ax1.set_ylim(0, 10); ax1.axis("off")
ax1.set_title(r"A layer $=$ a bank of $h$ low-rank circuit pairs, summed (Eq. 10)",
              fontsize=10.5)

# residual-stream input bus
ax1.add_patch(FancyBboxPatch((0.45, 3.0), 1.55, 4.8, boxstyle="round,pad=0.05",
                             fc="#eef2ff", ec=GUIDE, lw=1.2))
ax1.text(1.22, 6.0, "residual\nstream", ha="center", va="center", fontsize=8.3)
ax1.text(1.22, 5.05, r"$\mathbf{x}_i\in\mathbb{R}^{d}$", ha="center", va="center", fontsize=9.5)
ax1.text(1.22, 4.1, r"$d_{\mathrm{model}}{=}512$", ha="center", va="center", fontsize=7.2)

lane_y = [7.9, 6.3, 3.1]                  # ell = 1, 2, 8 ;  ellipsis ~ 4.7
lane_lbl = [r"$\ell{=}1$", r"$\ell{=}2$", r"$\ell{=}8$"]
lane_pal = [0, 1, 7]
qk_x, ov_x, bw, bh = 3.0, 5.6, 1.7, 1.0
sum_x, sum_y = 9.0, 5.4

for k, (yc, lab) in enumerate(zip(lane_y, lane_lbl)):
    col = PALETTE[lane_pal[k]]
    ax1.add_patch(Rectangle((2.45, yc - bh / 2 - 0.14), 5.85, bh + 0.28,
                            fc=col, ec="none", alpha=0.08))
    ax1.add_patch(FancyBboxPatch((qk_x, yc - bh / 2), bw, bh, boxstyle="round,pad=0.04",
                                 fc=QK_C, ec=EDGE, lw=0.9, alpha=0.20))
    ax1.text(qk_x + bw / 2, yc + 0.17, r"$M^{(\ell)}$", ha="center", va="center", fontsize=10.5)
    ax1.text(qk_x + bw / 2, yc - 0.28, r"QK, rank $\leq d_k$", ha="center", va="center", fontsize=7.0)
    ax1.add_patch(FancyBboxPatch((ov_x, yc - bh / 2), bw, bh, boxstyle="round,pad=0.04",
                                 fc=OV_C, ec=EDGE, lw=0.9, alpha=0.20))
    ax1.text(ov_x + bw / 2, yc + 0.17, r"$W_{OV}^{(\ell)}$", ha="center", va="center", fontsize=10.5)
    ax1.text(ov_x + bw / 2, yc - 0.28, r"OV, rank $\leq d_v$", ha="center", va="center", fontsize=7.0)
    ax1.text(2.34, yc, lab, ha="right", va="center", fontsize=8.5)
    ax1.add_patch(FancyArrowPatch((2.0, 5.4), (qk_x, yc), arrowstyle="-|>",
                                  mutation_scale=10, color=GUIDE, lw=0.8))
    ax1.add_patch(FancyArrowPatch((qk_x + bw, yc), (ov_x, yc), arrowstyle="-|>",
                                  mutation_scale=9, color=EDGE, lw=0.9))
    ax1.text((qk_x + bw + ov_x) / 2, yc + 0.31, r"$a^{(\ell)}$", ha="center", va="center", fontsize=8.5)
    ax1.add_patch(FancyArrowPatch((ov_x + bw, yc), (sum_x - 0.5, sum_y), arrowstyle="-|>",
                                  mutation_scale=10, color=GUIDE, lw=0.8))

ax1.text(qk_x + bw / 2, 4.7, r"$\vdots$", ha="center", va="center", fontsize=15)
ax1.text(ov_x + bw / 2, 4.7, r"$\vdots$", ha="center", va="center", fontsize=15)
ax1.text(7.05, 4.7, r"$h{=}8$ heads,  $d_k{=}d_v{=}64$", ha="left", va="center", fontsize=7.6)

ax1.add_patch(Circle((sum_x, sum_y), 0.5, fc="#fff7ed", ec="#dc2626", lw=1.3))
ax1.text(sum_x, sum_y, r"$\sum_{\ell=1}^{h}$", ha="center", va="center", fontsize=10)
ax1.add_patch(FancyBboxPatch((10.25, sum_y - 0.6), 1.95, 1.2, boxstyle="round,pad=0.05",
                             fc="#eef2ff", ec=GUIDE, lw=1.2))
ax1.add_patch(FancyArrowPatch((sum_x + 0.5, sum_y), (10.25, sum_y), arrowstyle="-|>",
                              mutation_scale=12, color=GUIDE, lw=1.6))
ax1.text(11.22, sum_y + 0.12, r"$\Delta\mathbf{x}_i$", ha="center", va="center", fontsize=11)
ax1.text(11.22, sum_y - 0.34, "write back", ha="center", va="center", fontsize=7.0)

ax1.text(4.3, 1.42,
         r"$a^{(\ell)}_{ij}=\mathrm{softmax}_j\left(\mathbf{x}_i^{\top} M^{(\ell)}\mathbf{x}_j/\sqrt{d_k}\right)$  (causal)"
         "\n"
         r"$M^{(\ell)}{=}W_Q^{(\ell)\top}W_K^{(\ell)}$,    $W_{OV}^{(\ell)}{=}W_O^{(\ell)}W_V^{(\ell)}$",
         ha="center", va="center", fontsize=7.4)
ax1.text(9.3, 2.0,
         "concat-then-project $=$\nsum of per-head slices\n(exact, not an approximation):\n"
         rf"max$|\,\cdot\,|={additivity_maxabsdiff:.1e}$",
         ha="center", va="center", fontsize=6.9,
         bbox=dict(boxstyle="round", fc="white", ec=GUIDE, alpha=0.95))
ax1.text(4.3, 0.4,
         r"one head $=$ one learned matched filter (A.6);  a layer $=$ a bank of $h$, summed",
         ha="center", va="center", fontsize=7.6, style="italic", color=GUIDE)

# ---- Panel B: routing-dissimilarity matrix + conserved-budget inset -------
im = ax2.imshow(D, cmap="magma", vmin=0, vmax=1, aspect="auto")
ax2.set_xticks(range(hB)); ax2.set_yticks(range(hB))
ax2.set_xticklabels(range(1, hB + 1), fontsize=8)
ax2.set_yticklabels(range(1, hB + 1), fontsize=8)
ax2.set_xlabel(r"head $\ell'$", fontsize=9)
ax2.set_ylabel(r"head $\ell$", fontsize=9)
cb = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
cb.set_label("routing dissimilarity (TV):  0 = identical,  1 = disjoint", fontsize=7.4)
cb.ax.tick_params(labelsize=7.0)

# header + conserved-budget tiling strip, just above the heatmap
ax2.text(0.5, 1.42, r"$h$ independent rank-$\leq d_k$ heads route one stream differently",
         transform=ax2.transAxes, ha="center", va="center", fontsize=8.6)
axb = ax2.inset_axes([0.0, 1.17, 1.0, 0.11])
axb.set_xlim(0, d_model); axb.set_ylim(0, 1); axb.axis("off")
for l in range(h):
    axb.add_patch(Rectangle((l * dv, 0), dv, 1, fc=PALETTE[l], ec="white", lw=0.8, alpha=0.85))
ax2.text(0.5, 1.07,
         r"and tile one budget:  $h\,d_k = 8\times 64 = 512 = d_{\mathrm{model}}$  (one full-width head)",
         transform=ax2.transAxes, ha="center", va="center", fontsize=7.0, color=GUIDE)

# caveats, below the heatmap
ax2.text(0.0, -0.22,
         rf"diagonal $=0$;   off-diag mean $\approx {offdiag_mean:.2f}$,  max $\approx {offdiag_max:.2f}<1$"
         "\n(route differently; not orthogonal by construction, not disjoint)."
         "\nOne shared stream $X$ ($T{=}9$); QK routing only — the OV write/sum is at left.",
         transform=ax2.transAxes, ha="left", va="top", fontsize=6.9, color="#374151")

fig.savefig(HERE / "qkv-multihead-sum.svg", bbox_inches="tight")
print("wrote qkv-multihead-sum.svg / .json")
print(f"  Panel A: additivity max|diff| = {additivity_maxabsdiff:.3e} (machine eps)")
print(f"  Panel B: circuit ranks = {ranks} (all should equal d_k = {dk})")
print(f"  Panel B: dissim diag max|.| = {diag_maxabs:.1e}; off-diag mean {offdiag_mean:.3f} "
      f"(min {offdiag_min:.3f}, max {offdiag_max:.3f})")
