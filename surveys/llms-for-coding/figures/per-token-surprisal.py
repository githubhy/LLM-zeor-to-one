"""Per-token cross-entropy loss is surprisal:  bits = -log2 p(true token).

Section 3.1 (LLMs-for-coding survey).  The per-token contribution to the
cross-entropy / NLL loss of Eq (2) is  -log p(x_t | x_<t)  evaluated at the
token that actually occurred.  Plotted in bits ( -log2 p ) against the
probability p the model assigned to that realized token.

  p -> 1 : the model was confident AND correct          -> ~0 bits of loss.
  p -> 0 : the model starved the true token of mass      -> the loss explodes.

This is the discrete-alphabet analogue of an AR model's innovation: the
"surprise" (information content) of the realized symbol under the model's
predictive distribution.  Averaging it over positions gives L(theta).

All values are exact (a closed-form curve).  No randomness.

Outputs:
  per-token-surprisal.svg
  per-token-surprisal.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

p = np.linspace(0.01, 1.0, 500)
bits = -np.log2(p)

# Reference points; p=0.7 ~ the 'a' token in `def add(a, b): return `.
marks = [0.7, 0.25, 0.05]

data = {
    "p": p.tolist(),
    "bits": bits.tolist(),
    "marks": {f"{m}": float(-np.log2(m)) for m in marks},
}
with open(HERE / "per-token-surprisal.json", "w") as f:
    json.dump(data, f, indent=1)

fig, ax = plt.subplots(figsize=(6.2, 4.0))
ax.plot(p, bits, color="#2563eb", lw=2.4)
ax.fill_between(p, bits, color="#2563eb", alpha=0.07)

for m in marks:
    b = -np.log2(m)
    ax.plot([m], [b], "o", color="#dc2626", ms=5, zorder=5)
    ax.annotate(f"p = {m:g}  ->  {b:.2f} bits",
                (m, b), textcoords="offset points", xytext=(9, 5),
                fontsize=8.5, color="#374151")

ax.annotate("confident & correct\n(p -> 1, loss -> 0)",
            (1.0, 0.0), textcoords="offset points", xytext=(-118, 26),
            fontsize=8.5, color="#16a34a",
            arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.0))
ax.annotate("truth starved of mass\n(p -> 0, loss -> infinity)",
            (0.05, -np.log2(0.05)), textcoords="offset points", xytext=(36, -6),
            fontsize=8.5, color="#b91c1c")

ax.set_xlabel("probability the model gave the realized next token,  p")
ax.set_ylabel(r"per-token loss (bits) $= -\log_2 p$")
ax.set_title("The per-token loss is surprisal", fontsize=11)
ax.set_xlim(0, 1.02)
ax.set_ylim(0, 6.9)
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "per-token-surprisal.svg")
print("wrote per-token-surprisal.svg / .json")
