"""Same skeleton, different weights: the equivalent kernel of each method.

Appendix B.  Every member predicts at a query x* as a weighted sum of the
SAME stored responses,

    yhat(x*) = sum_i w_i(x*) y_i .

This figure makes the *weight vector* w(x*) visible.  For one fixed query x*
on the shared dataset of `kernel-family-fits.py`, it stems w_i(x*) over the
data locations x_i for four members, exposing exactly which property of basic
kernel regression each one relaxes:

  (NW)   Nadaraya-Watson  -- weights non-negative, sum to 1, local bell.
  (kNN)  k-NN             -- k equal positive spikes (1/k), zero elsewhere.
  (GP)   Gaussian process -- the EQUIVALENT-kernel weights (K+sn^2 I)^{-1} k(x*)
                             are signed and oscillate (negative side-lobes),
                             and need NOT sum to 1.
  (RBF)  RBF network      -- effective data weights routed THROUGH m centers,
                             Phi (Phi^T Phi)^{-1} phi(x*); signed and broad.

Punchline: basic kernel regression is the member whose weights are
non-negative, normalized, and local; each relative relaxes one of those.
Deterministic (fixed seed); regenerates the same data as kernel-family-fits.py.

Outputs:
  kernel-family-weights.svg
  kernel-family-weights.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
np.seterr(divide="ignore", over="ignore", invalid="ignore")

rng = np.random.default_rng(0)


def f_true(x):
    return np.sin(1.5 * x) + 0.3 * x


n = 40
noise = 0.25
xt = np.sort(rng.uniform(-3.0, 3.0, size=n))
yt = f_true(xt) + noise * rng.standard_normal(n)

xq = 0.8                      # the query whose weight vector we dissect

# --- NW Gaussian weights (non-negative, normalized) -------------------------
h = 0.45
wn = np.exp(-(xq - xt) ** 2 / (2 * h ** 2))
wn = wn / wn.sum()

# --- k-NN weights (k equal spikes) ------------------------------------------
k = 5
wk = np.zeros(n)
wk[np.argsort(np.abs(xq - xt))[:k]] = 1.0 / k

# --- GP equivalent-kernel weights: yhat(x*) = k(x*)^T (K+sn^2 I)^{-1} y ------
ell, sf, sn = 0.6, 1.0, noise


def rbf_cov(a, b):
    return sf ** 2 * np.exp(-(a[:, None] - b[None, :]) ** 2 / (2 * ell ** 2))


K = rbf_cov(xt, xt)
Ky = K + sn ** 2 * np.eye(n)
ks_q = rbf_cov(np.array([xq]), xt).ravel()
wg = np.linalg.solve(Ky, ks_q)            # signed equivalent weights

# --- RBF effective data weights through m centers ---------------------------
m = 8
centers = np.linspace(-3.0, 3.0, m)
sig = 0.6
ridge = 1e-6


def design(x):
    return np.exp(-(x[:, None] - centers[None, :]) ** 2 / (2 * sig ** 2))


Phi = design(xt)
phi_q = design(np.array([xq])).ravel()
# yhat(x*) = phi(x*)^T (Phi^T Phi + rI)^{-1} Phi^T y  =  wr^T y
wr = Phi @ np.linalg.solve(Phi.T @ Phi + ridge * np.eye(m), phi_q)

# consistency: w^T y must reproduce each estimator's prediction at x*
pred = {"nw": float(wn @ yt), "knn": float(wk @ yt),
        "gp": float(wg @ yt), "rbf": float(wr @ yt)}

series = [
    ("Nadaraya–Watson", wn, "#2563eb"),
    (f"$k$-NN ($k={k}$)", wk, "#dc2626"),
    ("Gaussian process", wg, "#16a34a"),
    (f"RBF network (${m}$ centers)", wr, "#7c3aed"),
]

summary = {}
for name, w, _ in series:
    summary[name] = {"sum": float(w.sum()), "min": float(w.min()),
                     "max": float(w.max()), "has_negative": bool(w.min() < -1e-9)}

with open(HERE / "kernel-family-weights.json", "w") as fp:
    json.dump({"query": xq, "n": n, "predictions": pred, "weights": summary},
              fp, indent=1)

fig, axes = plt.subplots(2, 2, figsize=(10.6, 6.8), sharex=True)
for ax, (name, w, color) in zip(axes.ravel(), series):
    ax.axhline(0, color="#9ca3af", lw=0.8, zorder=1)
    ax.axvline(xq, color="#6b7280", lw=1.0, ls=":", zorder=1, label=r"query $x^\ast$")
    ml, sl, bl = ax.stem(xt, w, basefmt=" ")
    plt.setp(sl, color=color, lw=1.3)
    plt.setp(ml, color=color, markersize=3.2)
    neg = "  (has negative weights)" if w.min() < -1e-9 else ""
    ax.set_title(rf"{name}:  $\sum_i w_i = {w.sum():.3f}$,  "
                 rf"$\min_i w_i = {w.min():+.2f}${neg}", fontsize=9.2)
    ax.legend(fontsize=7.6, loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.18)
    ax.set_xlabel("data location $x_i$")
    ax.set_ylabel("weight $w_i(x^\\ast)$")
for ax in axes[0, :]:
    ax.set_xlabel("")

fig.suptitle(rf"Weights placed on each datum to predict at $x^\ast={xq}$:  "
             "same $\\sum_i w_i\\,y_i$, four very different $w$", fontsize=11, y=1.0)
fig.tight_layout(rect=(0, 0, 1, 0.98))
fig.savefig(HERE / "kernel-family-weights.svg", bbox_inches="tight")
print("wrote kernel-family-weights.svg / .json")
print(f"  query x* = {xq}; predictions reproduced from w^T y:")
for kk in pred:
    print(f"    {kk:4s}: {pred[kk]:+.3f}")
for name, w, _ in series:
    print(f"  {name:28s} sum {w.sum():+.3f}  min {w.min():+.3f}  max {w.max():+.3f}")
