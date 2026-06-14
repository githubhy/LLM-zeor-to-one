"""Law of large numbers: the empirical NLL converges to the cross-entropy.

Section 3.1, Eq (2) -- the `approx` step.  Tokens are drawn i.i.d. from a
true categorical p; a fixed (imperfect) model q scores them.  The running
per-token average

  -(1/T) * sum_{t<=T} log2 q(x_t)

is the empirical estimate L(theta).  It converges to the population
cross-entropy  H(p, q) = -sum_i p_i log2 q_i  as the corpus size T grows --
this is exactly the empirical-mean / LLN step of Eq (2), which holds when
the corpus is drawn i.i.d. from p (or is a stationary-ergodic stream).
Several seeds show the Monte-Carlo scatter narrowing like 1/sqrt(T).

The horizontal target H(p, q) is exact; the running curves are seeded
(seeds 0..5) so the figure regenerates identically.

Outputs:
  lln-empirical-nll.svg
  lln-empirical-nll.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

p = np.array([0.45, 0.25, 0.15, 0.08, 0.05, 0.02])   # true source
q = np.array([0.38, 0.22, 0.18, 0.12, 0.06, 0.04])   # fixed imperfect model
V = len(p)
CE = float(-np.sum(p * np.log2(q)))                  # population cross-entropy

Tmax = 50000
n_seeds = 6
runs = []
for s in range(n_seeds):
    rng = np.random.default_rng(s)
    draws = rng.choice(V, size=Tmax, p=p)
    surprisal = -np.log2(q[draws])
    runs.append((np.cumsum(surprisal) / np.arange(1, Tmax + 1)))

data = {
    "p": p.tolist(), "q": q.tolist(), "cross_entropy": CE,
    "Tmax": Tmax, "n_seeds": n_seeds,
    "final_estimates": [float(r[-1]) for r in runs],
}
with open(HERE / "lln-empirical-nll.json", "w") as f:
    json.dump(data, f, indent=1)

# Plot a log-spaced subset of points (the x-axis is logarithmic, so this is
# visually identical to plotting all 50000 and keeps the SVG small).
plot_idx = np.unique(np.geomspace(1, Tmax, 700).astype(int)) - 1
T_plot = plot_idx + 1
fig, ax = plt.subplots(figsize=(6.2, 4.0))
for r in runs:
    ax.plot(T_plot, r[plot_idx], color="#2563eb", lw=0.8, alpha=0.45)
ax.axhline(CE, color="#dc2626", lw=2.0,
           label=fr"cross-entropy $H(p,q)$ = {CE:.3f} bits")
ax.set_xscale("log")
ax.set_xlabel("corpus size  T  (tokens, log scale)")
ax.set_ylabel(r"empirical NLL  $-\frac{1}{T}\sum_t \log_2 q(x_t)$  (bits)")
ax.set_title("The empirical loss converges to the cross-entropy (LLN)",
             fontsize=11)
ax.set_xlim(1, Tmax)
ax.set_ylim(CE - 1.6, CE + 2.2)
ax.legend(fontsize=8.5, loc="upper right")
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "lln-empirical-nll.svg")
print(f"wrote lln-empirical-nll.svg / .json  (CE={CE:.4f} bits, "
      f"final={[round(float(r[-1]), 3) for r in runs]})")
