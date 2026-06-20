"""Figure H.1 — the architecture-choices matrix across the five models.

Each row is one design axis (normalization, position, activation, attention, FFN);
each column one model from the toy to DeepSeek-V3. Cells are colour-coded by era —
classic (LayerNorm / learned / ReLU / MHA / dense), the GELU intermediate, the
modern dense choices (RMSNorm / RoPE / SwiGLU / GQA), and the frontier ones
(MoE / MLA). The pattern is accretion: the core never changes, refinements stack
from the bottom-left to the top-right.

Sourced per the chapter cells: Toy (C, defined), GPT-2 XL [61], Llama 7B/70B
[65,63], DeepSeek-V3 [64].

Output: appendix-h-choices.svg
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

models = ["Toy\n(C)", "GPT-2 XL\n(D)", "Llama 7B\n(E)", "Llama 70B\n(F)", "DeepSeek-V3\n(G)"]
rows = ["Normalization", "Position", "Activation", "Attention", "Feed-forward"]
cells = [
    ["LayerNorm", "LayerNorm", "RMSNorm", "RMSNorm", "RMSNorm"],
    ["learned", "learned", "RoPE", "RoPE", "RoPE"],
    ["ReLU", "GELU", "SwiGLU", "SwiGLU", "SwiGLU"],
    ["MHA", "MHA", "MHA", "GQA", "MLA"],
    ["dense", "dense", "dense", "dense", "MoE"],
]
# era colour per value
CLASSIC, MID, MODERN, FRONTIER = "#e5e7eb", "#bfdbfe", "#a78bfa", "#34d399"
era = {"LayerNorm": CLASSIC, "learned": CLASSIC, "ReLU": CLASSIC, "MHA": CLASSIC, "dense": CLASSIC,
       "GELU": MID,
       "RMSNorm": MODERN, "RoPE": MODERN, "SwiGLU": MODERN, "GQA": MODERN,
       "MoE": FRONTIER, "MLA": FRONTIER}

fig, ax = plt.subplots(figsize=(11.0, 5.0))
nC, nR = len(models), len(rows)
for r in range(nR):
    for c in range(nC):
        v = cells[r][c]
        y = nR - 1 - r
        ax.add_patch(plt.Rectangle((c, y), 0.96, 0.92, fc=era[v], ec="#374151", lw=0.8))
        ax.text(c + 0.48, y + 0.46, v, ha="center", va="center", fontsize=9,
                color="#1f2937", fontweight="bold")
ax.set_xlim(-0.05, nC); ax.set_ylim(-0.05, nR + 0.05)
ax.set_xticks([c + 0.48 for c in range(nC)]); ax.set_xticklabels(models, fontsize=9)
ax.set_yticks([nR - 1 - r + 0.46 for r in range(nR)]); ax.set_yticklabels(rows, fontsize=9.5)
ax.xaxis.tick_top()
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)

# legend
import matplotlib.patches as mp
handles = [mp.Patch(fc=CLASSIC, ec="#374151", label="classic"),
           mp.Patch(fc=MID, ec="#374151", label="GELU (intermediate)"),
           mp.Patch(fc=MODERN, ec="#374151", label="modern dense (E)"),
           mp.Patch(fc=FRONTIER, ec="#374151", label="frontier (G)")]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.16),
          ncol=4, fontsize=8.5, frameon=False)
ax.set_title("Accretion, not redesign: the same five axes, refined left-to-right",
             fontsize=11, pad=26)

fig.tight_layout()
fig.savefig(HERE / "appendix-h-choices.svg", bbox_inches="tight")
print("wrote appendix-h-choices.svg")
