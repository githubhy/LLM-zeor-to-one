"""The QK circuit is a low-rank bilinear form; its SVD is the routing rule.

Appendix A, section A.8 (reading a trained head).  Two facts, made numerical.

(left) M = W_Q W_K^T is d x d but has rank at most d_k (it is a product through
a d_k-dimensional bottleneck).  Its singular-value spectrum therefore shows a
hard cliff: exactly d_k non-negligible values, the rest at machine zero.  The
head compares tokens in a d_k-dimensional subspace, not the full residual space.

(right) Each singular triple (sigma_r, u_r, w_r) of M is a routing rule:
score(i,j) = x_i M x_j^T = sum_r sigma_r (x_i . u_r)(x_j . w_r), so the head
sends attention FROM positions whose residual has mass on u_r TO positions with
mass on w_r.  We build a rank-1 routing circuit M = c * u w^T with orthonormal
u, w, give each of L key tokens a controlled alignment g_j = x_j . w, point the
query along u, and confirm the resulting attention weight is a monotone
(softmax-of-linear) function of the key's w-alignment g_j -- i.e. M literally
routes u-queries onto w-keys.  Asymmetry u != w makes the routing directed.

Deterministic (fixed seed).

Outputs:
  qkv-lowrank-routing.svg
  qkv-lowrank-routing.json
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

d, dk = 64, 8
rng = np.random.default_rng(3)

# --- left panel: rank cliff of M = W_Q W_K^T ---
WQ = rng.standard_normal((d, dk))
WK = rng.standard_normal((d, dk))
M = WQ @ WK.T
sv = np.linalg.svd(M, compute_uv=False)

# --- right panel: a rank-1 routing circuit M = c u w^T ---
u = rng.standard_normal(d); u /= np.linalg.norm(u)
w = rng.standard_normal(d)
w -= (w @ u) * u                 # make w orthogonal to u (directed: u != w)
w /= np.linalg.norm(w)
c = 6.0                          # routing strength (sets softmax temperature)
Mr = c * np.outer(u, w)

L = 24
g = np.linspace(-1.0, 1.0, L)    # intended key alignment along w
# Each key token = g_j * w plus small isotropic noise; g_meas is the realized
# w-alignment after noise (what the routing actually sees).
keys = np.outer(g, w) + 0.05 * rng.standard_normal((L, d))
g_meas = keys @ w
q = u.copy()                     # query aligned with u

scores = (q @ Mr @ keys.T) / np.sqrt(dk)
scores = scores - scores.max()
attn = np.exp(scores)
attn /= attn.sum()

data = {
    "d": d, "d_k": dk,
    "singular_values": [float(s) for s in sv],
    "n_above_1e-8": int((sv > 1e-8).sum()),
    "routing_strength_c": c, "L": L,
    "key_w_alignment": [float(x) for x in g_meas],
    "attention_weight": [float(a) for a in attn],
}
with open(HERE / "qkv-lowrank-routing.json", "w") as f:
    json.dump(data, f, indent=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.0))

idx = np.arange(1, len(sv) + 1)
ax1.semilogy(idx, np.maximum(sv, 1e-18), "o-", color="#7c3aed", lw=1.6, ms=4)
ax1.axvline(dk + 0.5, color="#dc2626", ls="--", lw=1.2,
            label=fr"rank cliff at $d_k={dk}$")
ax1.set_xlabel(r"singular-value index $r$")
ax1.set_ylabel(r"singular value $\sigma_r$ of $M$  (log)")
ax1.set_title(r"$M = W_Q W_K^\top$ has rank $\leq d_k$", fontsize=10.5)
ax1.grid(True, alpha=0.25, which="both")
ax1.legend(fontsize=8.5)

order = np.argsort(g_meas)
ax2.plot(g_meas[order], attn[order], "o-", color="#16a34a", lw=1.8, ms=4)
ax2.axhline(1.0 / L, color="#6b7280", ls=":", lw=1.0,
            label=f"uniform = 1/{L}")
ax2.set_xlabel(r"key's alignment with $w$:  $g_j = x_j \cdot w$")
ax2.set_ylabel("attention weight from the $u$-query")
ax2.set_title(r"rank-1 $M=c\,u w^\top$ routes $u$-queries onto $w$-keys",
              fontsize=10.5)
ax2.grid(True, alpha=0.25)
ax2.legend(fontsize=8.5, loc="upper left")

fig.tight_layout()
fig.savefig(HERE / "qkv-lowrank-routing.svg")
print("wrote qkv-lowrank-routing.svg / .json")
print(f"  singular values (top {dk+2}): {[round(float(s),2) for s in sv[:dk+2]]}")
print(f"  # singular values > 1e-8: {int((sv>1e-8).sum())} (= d_k = {dk})")
print(f"  attention on most-aligned key = {attn.max():.3f}, "
      f"on least-aligned = {attn.min():.4f} (uniform={1/L:.4f})")
