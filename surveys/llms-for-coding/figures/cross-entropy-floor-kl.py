"""Cross-entropy = irreducible entropy floor H(p) + KL(p||q): the loss
cannot reach zero.

Section 3.1, Eq (2) and the "why the data's own entropy cancels" note.
For a fixed true categorical p over a small alphabet, a model q_lambda
improves from a poor initial guess (lambda=0) toward the data (lambda=1):

  q_lambda = (1 - lambda) * q_poor + lambda * p.

As the model approaches the data, KL(p || q_lambda) -> 0 and the
cross-entropy H(p, q_lambda) descends to the irreducible floor H(p) --
never to zero.  The shaded band is the avoidable KL excess; the floor is
the data's own entropy (its intrinsic unpredictability), the part of the
loss that training can never remove.  This is the discrete analogue of an
estimator's irreducible noise floor: you drive the model mismatch (KL) to
zero, never the source's own uncertainty.

All quantities are computed exactly from p and q_lambda.  No randomness.

Outputs:
  cross-entropy-floor-kl.svg
  cross-entropy-floor-kl.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

# Fixed skewed true next-token distribution over 6 symbols, and a poor
# initial model that is roughly its reverse (high mass on rare symbols).
p = np.array([0.45, 0.25, 0.15, 0.08, 0.05, 0.02])
q_poor = np.array([0.02, 0.05, 0.08, 0.15, 0.25, 0.45])


def entropy(d):
    d = d[d > 0]
    return -np.sum(d * np.log2(d))


def cross_entropy(p, q):
    return -np.sum(p * np.log2(q))


def kl(p, q):
    m = p > 0
    return np.sum(p[m] * np.log2(p[m] / q[m]))


lam = np.linspace(0.0, 1.0, 400)
H_floor = entropy(p)
CE = np.array([cross_entropy(p, (1 - L) * q_poor + L * p) for L in lam])
KLv = np.array([kl(p, (1 - L) * q_poor + L * p) for L in lam])

data = {
    "p": p.tolist(),
    "q_poor": q_poor.tolist(),
    "lambda": lam.tolist(),
    "cross_entropy": CE.tolist(),
    "kl": KLv.tolist(),
    "H_floor": float(H_floor),
}
with open(HERE / "cross-entropy-floor-kl.json", "w") as f:
    json.dump(data, f, indent=1)

fig, ax = plt.subplots(figsize=(6.2, 4.0))
ax.fill_between(lam, H_floor, CE, color="#dc2626", alpha=0.15,
                label="KL excess (avoidable, shrinks to 0)")
ax.fill_between(lam, 0, H_floor, color="#16a34a", alpha=0.12,
                label=r"entropy floor $H(p_{data})$ (irreducible)")
ax.plot(lam, CE, color="#2563eb", lw=2.4,
        label=r"cross-entropy $H(p_{data}, p_\theta)$")
ax.axhline(H_floor, color="#16a34a", lw=1.5, ls="--")
ax.annotate(f"floor $H(p_{{data}})$ = {H_floor:.2f} bits\nloss stops here, not at 0",
            (0.30, H_floor), textcoords="offset points", xytext=(6, 10),
            fontsize=8.5, color="#15803d")

ax.set_xlabel(r"model improves  ($\lambda$: a poor model $\to$ $p_{data}$)")
ax.set_ylabel("bits / token")
ax.set_title("Cross-entropy = irreducible floor + KL", fontsize=11)
ax.set_xlim(0, 1)
ax.set_ylim(0, cross_entropy(p, q_poor) * 1.05)
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "cross-entropy-floor-kl.svg")
print(f"wrote cross-entropy-floor-kl.svg / .json  (H_floor={H_floor:.4f} bits, "
      f"CE_start={cross_entropy(p, q_poor):.4f})")
