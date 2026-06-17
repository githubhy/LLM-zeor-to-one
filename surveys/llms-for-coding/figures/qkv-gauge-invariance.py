"""The query/key matrices are not observable: only M = W_Q W_K^T is.

Appendix A, section A.4 (gauge freedom).  The attention pattern depends on
W_Q and W_K ONLY through the product M = W_Q W_K^T.  For any invertible
R in GL(d_k), the reparametrization

    W_Q -> W_Q R ,   W_K -> W_K R^{-T}

leaves M unchanged (W_Q R)(W_K R^{-T})^T = W_Q R R^{-1} W_K^T = W_Q W_K^T,
hence leaves the entire causal attention matrix A unchanged.  We demonstrate
this numerically: a random GL(d_k) gauge transform moves the raw matrices by a
large relative amount, yet the attention matrix is identical to machine
precision.  Individual W_Q, W_K carry d_k^2 unobservable gauge degrees of
freedom; the trained matrices you inspect are one arbitrary representative.

Deterministic (fixed seed); no Monte-Carlo.

Outputs:
  qkv-gauge-invariance.svg
  qkv-gauge-invariance.json
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

d, dk, T = 24, 4, 9
rng = np.random.default_rng(7)

X = rng.standard_normal((T, d))
WQ = rng.standard_normal((d, dk))
WK = rng.standard_normal((d, dk))

# A well-conditioned random gauge R in GL(d_k).
while True:
    R = rng.standard_normal((dk, dk))
    if abs(np.linalg.det(R)) > 0.5 and np.linalg.cond(R) < 20:
        break
Rinv = np.linalg.inv(R)

WQ2 = WQ @ R
WK2 = WK @ Rinv.T          # so WK2^T = R^{-1} WK^T  =>  WQ2 WK2^T = WQ WK^T


def causal_attention(Wq, Wk):
    S = (X @ Wq) @ (X @ Wk).T / np.sqrt(dk)
    mask = np.tril(np.ones((T, T), dtype=bool))
    S = np.where(mask, S, -np.inf)
    S = S - S.max(axis=1, keepdims=True)
    E = np.exp(S)
    return E / E.sum(axis=1, keepdims=True)


A = causal_attention(WQ, WK)
A2 = causal_attention(WQ2, WK2)

M = WQ @ WK.T
M2 = WQ2 @ WK2.T

rel_change_WQ = float(np.linalg.norm(WQ2 - WQ) / np.linalg.norm(WQ))
rel_change_WK = float(np.linalg.norm(WK2 - WK) / np.linalg.norm(WK))
attn_maxabsdiff = float(np.max(np.abs(A - A2)))
M_maxabsdiff = float(np.max(np.abs(M - M2)))

data = {
    "d": d, "d_k": dk, "T": T,
    "det_R": float(np.linalg.det(R)), "cond_R": float(np.linalg.cond(R)),
    "rel_change_WQ": rel_change_WQ, "rel_change_WK": rel_change_WK,
    "M_maxabsdiff": M_maxabsdiff, "attn_maxabsdiff": attn_maxabsdiff,
}
with open(HERE / "qkv-gauge-invariance.json", "w") as f:
    json.dump(data, f, indent=1)

fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.7))
common = dict(cmap="viridis", vmin=0, vmax=1, aspect="auto")

im0 = axes[0].imshow(A, **common)
axes[0].set_title(r"$A$ from $(W_Q, W_K)$", fontsize=10.5)
im1 = axes[1].imshow(A2, **common)
axes[1].set_title(r"$A'$ from $(W_Q R,\ W_K R^{-\top})$", fontsize=10.5)
for ax in axes[:2]:
    ax.set_xlabel("key position $j$")
axes[0].set_ylabel("query position $i$")
fig.colorbar(im1, ax=axes[:2], fraction=0.046, pad=0.04, label="attention weight")

diff = np.abs(A - A2)
im2 = axes[2].imshow(diff, cmap="magma", aspect="auto")
axes[2].set_title(r"$|A - A'|$  (machine $\varepsilon$)", fontsize=10.5)
axes[2].set_xlabel("key position $j$")
cb = fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
cb.formatter.set_powerlimits((0, 0))

fig.suptitle(
    rf"Random GL($d_k$) gauge moves $W_Q,W_K$ by ~{100*rel_change_WQ:.0f}%, "
    rf"but $A$ is unchanged (max $|\Delta|$ = {attn_maxabsdiff:.0e})",
    fontsize=11, y=1.02)
fig.savefig(HERE / "qkv-gauge-invariance.svg", bbox_inches="tight")
print("wrote qkv-gauge-invariance.svg / .json")
print(f"  rel change ||WQ'-WQ||/||WQ|| = {rel_change_WQ:.3f}, "
      f"||WK'-WK||/||WK|| = {rel_change_WK:.3f}")
print(f"  max|M-M'|   = {M_maxabsdiff:.2e}")
print(f"  max|A-A'|   = {attn_maxabsdiff:.2e}  (attention identical to machine precision)")
