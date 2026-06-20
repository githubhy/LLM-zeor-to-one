"""GPT-2 at four scales: sourced dimensions and where the parameters live.

Appendix D. Left: the four GPT-2 sizes as reported in the paper's Table 2 (params,
layers, d_model). Right: the parameter budget split into embeddings vs the L
transformer blocks, computed from the same dimensions with the standard accounting
(embedding = (V+T_ctx)*d with tied unembedding; per block ~ 12 d^2 = 4 d^2 attention
+ 8 d^2 FFN). The point of the right panel: the token-embedding share collapses as
the model scales (blocks grow as L*d^2, embeddings only as V*d), so a big model is
almost entirely its blocks.

Sourced [61] (Radford et al. 2019, Table 2): params 117M/345M/762M/1542M, layers
12/24/36/48, d_model 768/1024/1280/1600; vocab V=50257, context T_ctx=1024.
The computed totals (124M..1.56B) track the paper's stated 117M..1542M to a few
percent; the residual is the paper's embedding/bias counting convention.

Outputs:
  appendix-d-gpt2-sizes.svg
  appendix-d-gpt2-sizes.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

V, T_CTX = 50257, 1024
names = ["small", "medium", "large", "XL"]
params_paper = np.array([117e6, 345e6, 762e6, 1542e6])   # STATED, Table 2 [61]
L = np.array([12, 24, 36, 48])
d = np.array([768, 1024, 1280, 1600])

emb = (V + T_CTX) * d                       # token (tied) + positional
blocks = L * 12 * d.astype(float) ** 2      # ~12 d^2 per block (4 attn + 8 ffn)
total_formula = emb + blocks
emb_frac = emb / total_formula

data = {
    "sizes": names, "params_paper": params_paper.tolist(), "layers": L.tolist(),
    "d_model": d.tolist(), "vocab": V, "context": T_CTX,
    "embedding_params": emb.tolist(), "block_params": blocks.tolist(),
    "total_formula": total_formula.tolist(),
    "embedding_fraction": [round(float(x), 3) for x in emb_frac],
}
with open(HERE / "appendix-d-gpt2-sizes.json", "w") as f:
    json.dump(data, f, indent=1)

EMB_C, BLK_C, EDGE, ACC = "#2563eb", "#7c3aed", "#374151", "#16a34a"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8))

# --- left: sourced sizes (params log-bars; L and d annotated) ---
xpos = np.arange(4)
ax1.bar(xpos, params_paper, width=0.6, color=ACC, alpha=0.85, edgecolor=EDGE, zorder=3)
ax1.set_yscale("log")
for i in range(4):
    ax1.text(i, params_paper[i] * 1.25, f"{params_paper[i]/1e6:.0f}M",
             ha="center", va="bottom", fontsize=8.5, color=ACC, fontweight="bold")
    ax1.text(i, params_paper[i] * 0.5, f"$L{{=}}{L[i]}$\n$d{{=}}{d[i]}$",
             ha="center", va="top", fontsize=7.6, color="white")
ax1.set_xticks(xpos); ax1.set_xticklabels(names, fontsize=9)
ax1.set_ylim(5e7, 3e9)
ax1.set_ylabel("parameters (log scale)", fontsize=9)
ax1.set_title(r"GPT-2's four sizes (Table 2 [61]); $V{=}50257,\ T_{ctx}{=}1024$", fontsize=9.8)
ax1.grid(True, axis="y", alpha=0.25, which="both")

# --- right: parameter budget — embeddings vs blocks (computed) ---
ax2.bar(xpos, emb / 1e6, width=0.6, color=EMB_C, alpha=0.85, edgecolor=EDGE, label="embeddings $(V{+}T_{ctx})\\,d$")
ax2.bar(xpos, blocks / 1e6, width=0.6, bottom=emb / 1e6, color=BLK_C, alpha=0.85, edgecolor=EDGE,
        label=r"$L$ blocks $\approx L\cdot 12 d^2$")
for i in range(4):
    ax2.text(i, total_formula[i] / 1e6 + 25, f"{total_formula[i]/1e6:.0f}M",
             ha="center", va="bottom", fontsize=7.8, color=EDGE)
    ax2.text(i, emb[i] / 2e6, f"{emb_frac[i]*100:.0f}%", ha="center", va="center",
             fontsize=7.4, color="white")
ax2.set_xticks(xpos); ax2.set_xticklabels(names, fontsize=9)
ax2.set_ylabel("parameters (millions)", fontsize=9)
ax2.set_title("Where the parameters live: embedding share falls 32% → 5%", fontsize=9.6)
ax2.grid(True, axis="y", alpha=0.25)
ax2.legend(fontsize=7.8, loc="upper left")

fig.tight_layout()
fig.savefig(HERE / "appendix-d-gpt2-sizes.svg", bbox_inches="tight")
print("wrote appendix-d-gpt2-sizes.svg / .json")
print("  embedding fraction:", [f"{x*100:.0f}%" for x in emb_frac])
print("  formula totals (M):", [f"{x/1e6:.0f}" for x in total_formula], "vs paper",
      [f"{x/1e6:.0f}" for x in params_paper])
