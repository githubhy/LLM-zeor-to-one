"""Attention is Nadaraya-Watson kernel regression with a learned metric M.

Appendix A, section A.5.  Column-vector convention.  Equation (6):

  o_i = ( sum_j kappa(i,j) v_j ) / ( sum_j kappa(i,j) ),
  kappa(i,j) = exp( x_i^T M x_j / sqrt(d_k) ).

The output is a kernel-weighted average of the value "responses" v_j -- exactly
a Nadaraya-Watson estimator -- whose kernel is the exponential of a bilinear
form, with the learned matrix M as the metric.  Two panels:

(left)  A toy 2-D feature plane.  Tokens x_j are points coloured by a scalar
        value response v_j; for one query x_q the attention weights
        a_j = softmax_j(x_q^T M x_j / sqrt(d_k)) are shown as marker size, and
        the output o = sum_j a_j v_j is the kernel-weighted average they
        produce.  Because the score x_q^T M x_j is *linear* in x_j, the weight
        grows along the M x_q direction -- attention weights by ALIGNMENT in the
        learned M-metric, not by proximity.

(right) Why this is NOT a Gaussian RBF.  Along a ray x(t) = x_q + t * u through
        the query, the (unnormalized) attention kernel exp(x_q^T M x(t)/sqrt(d_k))
        GROWS monotonically with alignment, whereas a Gaussian RBF
        exp(-||x(t)-x_q||^2 / 2 l^2) PEAKS at the query (t = 0) and decays.  The
        softmax denominator of Equation (6), not a fixed bandwidth, supplies the
        normalization.

M is taken symmetric positive definite here (the "inner product in the M-metric"
case of A.5); its anisotropy is the learned geometry.  Deterministic (fixed seed).

Outputs:
  qkv-kernel-regression.svg
  qkv-kernel-regression.json
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

d, dk, N = 2, 2, 40
rng = np.random.default_rng(8)


def softmax(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# Tokens in a 2-D feature plane; scalar value response is a smooth (linear)
# latent function of position, so the "responses" are easy to read as colour.
Xtok = rng.uniform(-2.2, 2.2, size=(N, d))          # rows are token vectors
v = 1.5 * Xtok[:, 0] - 0.5 * Xtok[:, 1]             # value responses v_j (scalar)

# Learned metric M: symmetric positive definite, anisotropic (rotated).
theta = 0.6
R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
M = R @ np.diag([2.6, 0.45]) @ R.T                  # SPD, eigvals 2.6 and 0.45

xq = np.array([1.3, 0.7])                           # query
scores = (Xtok @ (M @ xq)) / np.sqrt(dk)            # s_j = x_q^T M x_j / sqrt(d_k)  (symmetric M)
a = softmax(scores)                                 # attention weights (the kernel)
o = float(a @ v)                                    # output = kernel-weighted average
entropy = float(-(a * np.log(a + 1e-12)).sum())     # nats; uniform = ln N
v_mean = float(v.mean())                            # plain (unweighted) mean for contrast

# Panel B: kernel vs Gaussian RBF along the alignment ray u = M x_q / ||M x_q||.
u = (M @ xq) / np.linalg.norm(M @ xq)
t = np.linspace(-2.5, 2.5, 400)
Xray = xq[None, :] + t[:, None] * u[None, :]
k_att = np.exp((Xray @ (M @ xq)) / np.sqrt(dk))
k_att /= k_att.max()
ell = 1.0
k_rbf = np.exp(-np.sum((Xray - xq) ** 2, axis=1) / (2 * ell ** 2))

data = {
    "d": d, "d_k": dk, "N": N,
    "M": M.tolist(), "M_eigvals": np.linalg.eigvalsh(M).tolist(),
    "query": xq.tolist(),
    "output_o": o, "value_mean": v_mean,
    "attention_entropy_nats": entropy, "uniform_entropy_nats": float(np.log(N)),
    "max_weight": float(a.max()),
}
with open(HERE / "qkv-kernel-regression.json", "w") as f:
    json.dump(data, f, indent=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.3))

sizes = 20 + 460 * (a / a.max())
sc = ax1.scatter(Xtok[:, 0], Xtok[:, 1], c=v, s=sizes, cmap="viridis",
                 edgecolors="white", linewidths=0.4, zorder=2)
ax1.scatter([xq[0]], [xq[1]], marker="*", s=320, color="#dc2626",
            edgecolors="black", linewidths=0.6, zorder=3, label="query $\\mathbf{x}_q$")
# arrow along the alignment direction M x_q
ax1.annotate("", xy=xq + 1.3 * u, xytext=xq,
             arrowprops=dict(arrowstyle="-|>", color="#dc2626", lw=1.6))
ax1.text(*(xq + 1.45 * u), r"$M\mathbf{x}_q$", color="#dc2626", fontsize=9)
ax1.set_xlabel("feature dim 1"); ax1.set_ylabel("feature dim 2")
ax1.set_title(r"$\mathbf{o} = \sum_j a_j \mathbf{v}_j$: kernel-weighted average"
              "\n" rf"(marker size $\propto a_j$; output $o$ = {o:.2f} vs plain mean {v_mean:.2f})",
              fontsize=9.5)
ax1.legend(fontsize=8.5, loc="lower left")
ax1.grid(True, alpha=0.2)
cb = fig.colorbar(sc, ax=ax1, fraction=0.046, pad=0.04)
cb.set_label("value response $v_j$", fontsize=9)

ax2.plot(t, k_att, color="#2563eb", lw=2.2,
         label=r"attention $\exp(\mathbf{x}_q^\top M\,\mathbf{x}(t)/\sqrt{d_k})$")
ax2.plot(t, k_rbf, color="#16a34a", lw=2.2, ls="--",
         label=r"Gaussian RBF $\exp(-\|\mathbf{x}(t)-\mathbf{x}_q\|^2/2\ell^2)$")
ax2.axvline(0, color="#6b7280", lw=1.0, ls=":", label=r"query ($t=0$)")
ax2.set_xlabel(r"position along the alignment ray  $\mathbf{x}(t)=\mathbf{x}_q + t\,\mathbf{u}$")
ax2.set_ylabel("kernel value (each normalized to its max)")
ax2.set_title("Grows with alignment, not a bump at the query", fontsize=9.5)
ax2.legend(fontsize=8.0, loc="upper left")
ax2.grid(True, alpha=0.25)

fig.tight_layout()
fig.savefig(HERE / "qkv-kernel-regression.svg")
print("wrote qkv-kernel-regression.svg / .json")
print(f"  M eigenvalues = {[round(x,2) for x in np.linalg.eigvalsh(M)]} (SPD, anisotropic)")
print(f"  output o = {o:.3f}  (plain mean of v = {v_mean:.3f}); max weight = {a.max():.3f}")
print(f"  attention entropy = {entropy:.2f} nats (uniform = {np.log(N):.2f})")
print(f"  attention kernel along ray: {k_att[0]:.3f} -> {k_att[-1]:.3f} (monotone up); "
      f"RBF peak at t=0 = {k_rbf[len(t)//2]:.3f}")
