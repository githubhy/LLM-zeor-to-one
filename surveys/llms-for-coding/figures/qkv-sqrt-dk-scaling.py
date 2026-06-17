"""Why attention divides by sqrt(d_k): logit variance and softmax saturation.

Appendix A, section A.7 (and the 1/sqrt(d_k) remark of section 3.3).  This is
Vaswani et al. (2017) footnote 4 made numerical, plus the second-moment
derivation of A.7.

Two panels:

(left) For q, k drawn iid N(0,1) in R^{d_k}, the raw score q . k = sum_l q_l k_l
has mean 0 and variance d_k, so its standard deviation grows like sqrt(d_k).
Dividing by sqrt(d_k) holds the standard deviation at 1 regardless of head
width.  We plot both, with the sqrt(d_k) reference curve.

(right) The consequence for the softmax.  For a query against L INDEPENDENT
candidate keys (no planted signal -- pure background), the UNSCALED logits are
N(0, d_k), so as d_k grows the largest one runs away and the softmax becomes
spuriously confident: its peak weight tends to 1 on a purely random key -- the
saturated, vanishing-gradient regime Vaswani et al. warn about.  The
sqrt(d_k)-SCALED logits are N(0, 1) at every width, so the softmax is
d_k-invariant: its peak weight stays near 1/L and gradients stay alive.  The
scaling fixes the temperature to the noise floor instead of letting it grow
with head width.

Everything is seeded (numpy default_rng) so the figure regenerates identically.

Outputs:
  qkv-sqrt-dk-scaling.svg
  qkv-sqrt-dk-scaling.json
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

dks = [4, 8, 16, 32, 64, 128, 256]
N = 40000          # Monte-Carlo samples per d_k for the variance panel
L = 16             # candidate keys per query for the saturation panel
trials = 4000      # queries averaged per d_k for the saturation panel


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


raw_std, scaled_std = [], []
peak_unscaled, peak_scaled = [], []
ent_unscaled, ent_scaled = [], []

for dk in dks:
    rng = np.random.default_rng(dk)            # per-width seed -> reproducible

    # --- variance panel: std of a single dot product ---
    Q = rng.standard_normal((N, dk))
    K = rng.standard_normal((N, dk))
    dots = np.einsum("nd,nd->n", Q, K)
    raw_std.append(float(dots.std()))
    scaled_std.append(float((dots / np.sqrt(dk)).std()))

    # --- saturation panel: softmax over L INDEPENDENT keys (pure background) ---
    q = rng.standard_normal((trials, dk))
    keys = rng.standard_normal((trials, L, dk))        # no planted signal
    logits = np.einsum("td,tld->tl", q, keys)          # raw q . k ~ N(0, d_k)
    a_un = softmax(logits, axis=1)
    a_sc = softmax(logits / np.sqrt(dk), axis=1)
    peak_unscaled.append(float(a_un.max(axis=1).mean()))
    peak_scaled.append(float(a_sc.max(axis=1).mean()))
    ent_unscaled.append(float((-(a_un * np.log2(a_un + 1e-12)).sum(axis=1)).mean()))
    ent_scaled.append(float((-(a_sc * np.log2(a_sc + 1e-12)).sum(axis=1)).mean()))

data = {
    "d_k": dks, "N": N, "L": L, "trials": trials,
    "raw_std": raw_std, "scaled_std": scaled_std,
    "sqrt_dk": [float(np.sqrt(dk)) for dk in dks],
    "softmax_peak_unscaled": peak_unscaled, "softmax_peak_scaled": peak_scaled,
    "softmax_entropy_bits_unscaled": ent_unscaled,
    "softmax_entropy_bits_scaled": ent_scaled,
    "uniform_entropy_bits": float(np.log2(L)),
}
with open(HERE / "qkv-sqrt-dk-scaling.json", "w") as f:
    json.dump(data, f, indent=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0))

ax1.plot(dks, raw_std, "o-", color="#dc2626", lw=2.0, ms=5,
         label=r"std of raw  $q\cdot k$")
ax1.plot(dks, [np.sqrt(dk) for dk in dks], "--", color="#dc2626", lw=1.0,
         alpha=0.6, label=r"$\sqrt{d_k}$ (theory)")
ax1.plot(dks, scaled_std, "s-", color="#2563eb", lw=2.0, ms=5,
         label=r"std of scaled  $q\cdot k/\sqrt{d_k}$")
ax1.axhline(1.0, color="#2563eb", ls="--", lw=1.0, alpha=0.6, label="1 (theory)")
ax1.set_xscale("log", base=2)
ax1.set_xlabel(r"head width  $d_k$")
ax1.set_ylabel("standard deviation of the score")
ax1.set_title("Raw scores grow like $\\sqrt{d_k}$; scaling fixes them", fontsize=10.5)
ax1.grid(True, alpha=0.25)
ax1.legend(fontsize=8.0, loc="upper left")

ax2.plot(dks, peak_unscaled, "o-", color="#dc2626", lw=2.0, ms=5,
         label="unscaled softmax")
ax2.plot(dks, peak_scaled, "s-", color="#2563eb", lw=2.0, ms=5,
         label=r"scaled by $1/\sqrt{d_k}$")
ax2.set_xscale("log", base=2)
ax2.set_ylim(0, 1.0)
ax2.set_xlabel(r"head width  $d_k$")
ax2.axhline(1.0 / L, color="#6b7280", ls=":", lw=1.0, label=f"uniform = 1/{L}")
ax2.set_ylabel("mean peak softmax weight  (over %d random keys)" % L)
ax2.set_title("Unscaled softmax saturates on noise as $d_k$ grows", fontsize=10.5)
ax2.grid(True, alpha=0.25)
ax2.legend(fontsize=8.5, loc="center right")

fig.tight_layout()
fig.savefig(HERE / "qkv-sqrt-dk-scaling.svg")
print("wrote qkv-sqrt-dk-scaling.svg / .json")
print(f"  raw_std    = {[round(s,2) for s in raw_std]}")
print(f"  scaled_std = {[round(s,3) for s in scaled_std]}")
print(f"  peak unscaled = {[round(p,3) for p in peak_unscaled]}")
print(f"  peak scaled   = {[round(p,3) for p in peak_scaled]}")
print(f"  d_k=64: raw_std={raw_std[dks.index(64)]:.2f} (sqrt64={np.sqrt(64):.2f}), "
      f"peak_unscaled={peak_unscaled[dks.index(64)]:.3f}, "
      f"peak_scaled={peak_scaled[dks.index(64)]:.3f}")
