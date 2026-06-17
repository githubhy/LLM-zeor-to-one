"""The query-key collapse: one asymmetric d x d bilinear form governs the pattern.

Appendix A, section A.2.  Column-vector convention.  The per-token query and
key vectors q_i = W_Q x_i, k_j = W_K x_j are intermediates; their dot product
collapses to a single bilinear form,

  s_ij = q_i^T k_j / sqrt(d_k) = x_i^T (W_Q^T W_K) x_j / sqrt(d_k) = x_i^T M x_j / sqrt(d_k),

so the entire T x T score pattern is a function of M = W_Q^T W_K alone.  Two
facts this figure makes visible:

(left)  The raw score matrix S (S_ij = x_i^T M x_j / sqrt(d_k)) -- the pattern M
        governs.  Computed via the d_k-dimensional q,k path and via the d x d
        matrix M, the two agree to machine precision (the collapse is exact).

(right) M is generally NOT symmetric: scattering each off-diagonal entry M_ab
        against its mirror M_ba shows the points spread off the y = x line, so
        x_i^T M x_j != x_j^T M x_i.  The comparison is directed -- the feature a
        token advertises as a key differs from the feature it requests as a
        query -- which is why the score matrix S on the left is itself
        asymmetric.  (M is also rank <= d_k; that bottleneck is Figure A.4.)

Deterministic (fixed seed).

Outputs:
  qkv-qk-collapse.svg
  qkv-qk-collapse.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

# macOS Accelerate / NumPy 2.x raises spurious FP flags inside BLAS matmul;
# the printed results are exact (verified), so silence these non-errors.
np.seterr(divide="ignore", over="ignore", invalid="ignore")

d, dk, T = 24, 3, 12
rng = np.random.default_rng(5)

# Column-vector convention: tokens are the columns of X; W_Q, W_K are d_k x d.
X = rng.standard_normal((d, T))
WQ = rng.standard_normal((dk, d))
WK = rng.standard_normal((dk, d))
M = WQ.T @ WK                       # d x d, rank <= d_k

# The collapse, both ways.
S_M = (X.T @ M @ X) / np.sqrt(dk)                 # via the d x d form
Q = WQ @ X                                        # d_k x T  (per-token queries)
K = WK @ X
S_qk = (Q.T @ K) / np.sqrt(dk)                    # via the d_k path
collapse_maxdiff = float(np.max(np.abs(S_M - S_qk)))

# Asymmetry of M.
off = ~np.eye(d, dtype=bool)
Mab = M[off]
Mba = M.T[off]
asym_ratio = float(np.linalg.norm(M - M.T) / np.linalg.norm(M + M.T))
score_asym = float(np.max(np.abs(S_M - S_M.T)))   # the pattern is asymmetric too
rank = int(np.linalg.matrix_rank(M, tol=1e-8))

data = {
    "d": d, "d_k": dk, "T": T,
    "rank_M": rank,
    "collapse_maxdiff": collapse_maxdiff,
    "asymmetry_ratio": asym_ratio,
    "score_asymmetry_maxabs": score_asym,
}
with open(HERE / "qkv-qk-collapse.json", "w") as f:
    json.dump(data, f, indent=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2))

vmax = np.max(np.abs(S_M))
im = ax1.imshow(S_M, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
ax1.set_title(r"scores $s_{ij} = \mathbf{x}_i^\top M \mathbf{x}_j / \sqrt{d_k}$",
              fontsize=10.5)
ax1.set_xlabel("key position $j$")
ax1.set_ylabel("query position $i$")
fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)

lim = np.max(np.abs(M)) * 1.05
ax2.axline((0, 0), slope=1, color="#6b7280", lw=1.0, ls="--",
           label=r"$M_{ab} = M_{ba}$ (symmetric)")
ax2.scatter(Mab, Mba, s=8, alpha=0.35, color="#2563eb", edgecolors="none")
ax2.set_xlim(-lim, lim); ax2.set_ylim(-lim, lim)
ax2.set_aspect("equal")
ax2.set_xlabel(r"$M_{ab}$")
ax2.set_ylabel(r"$M_{ba}$")
ax2.set_title(rf"$M \neq M^\top$: directed comparison"
              "\n" rf"(asymmetry $\|M-M^\top\|/\|M+M^\top\|$ = {asym_ratio:.2f})",
              fontsize=10.5)
ax2.grid(True, alpha=0.25)
ax2.legend(fontsize=8.5, loc="upper left")

fig.suptitle(
    rf"The QK collapse: one $d\times d$ form $M=W_Q^\top W_K$ "
    rf"(rank {rank}) governs the whole pattern "
    rf"(q,k path matches to {collapse_maxdiff:.0e})",
    fontsize=10.5, y=1.02)
fig.savefig(HERE / "qkv-qk-collapse.svg", bbox_inches="tight")
print("wrote qkv-qk-collapse.svg / .json")
print(f"  rank(M) = {rank} (= d_k = {dk});  collapse max|S_qk - S_M| = {collapse_maxdiff:.2e}")
print(f"  asymmetry ratio ||M-M^T||/||M+M^T|| = {asym_ratio:.3f};  "
      f"score asymmetry max|S-S^T| = {score_asym:.3f}")
