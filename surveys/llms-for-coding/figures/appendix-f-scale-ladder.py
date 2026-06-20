"""Figure F.1 — the Llama dense ladder: scale is (d, H, L), nothing else.

Left: parameters across the four Llama sizes (log bars) with each size's width d,
head count H, and depth L annotated — the only dimensions that change. Right: the
width-to-depth aspect ratio d/L, which stays in a narrow band (~100-128) as the
model scales, i.e. depth grows roughly in step with width.

Sourced [65, Table 2]: 7B (d4096,H32,L32), 13B (5120,40,40), 33B (6656,52,60),
65B (8192,64,80). Llama-2 70B [63] shares the 65B width/depth and adds GQA.

Output: appendix-f-scale-ladder.svg / .json
"""
import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

names = ["7B", "13B", "33B", "65B"]
params = np.array([6.7e9, 13.0e9, 32.5e9, 65.2e9])      # [65, Table 2]
d = np.array([4096, 5120, 6656, 8192])
H = np.array([32, 40, 52, 64])
L = np.array([32, 40, 60, 80])
aspect = d / L

data = {"sizes": names, "params": params.tolist(), "d": d.tolist(),
        "H": H.tolist(), "L": L.tolist(), "aspect_d_over_L": aspect.round(1).tolist()}
with open(HERE / "appendix-f-scale-ladder.json", "w") as f:
    json.dump(data, f, indent=1)

ACC, ASP, EDGE = "#2563eb", "#7c3aed", "#374151"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.7),
                               gridspec_kw={"width_ratios": [1.5, 1.0]})

xp = np.arange(4)
ax1.bar(xp, params, width=0.6, color=ACC, alpha=0.85, edgecolor=EDGE, zorder=3)
ax1.set_yscale("log")
for i in range(4):
    ax1.text(i, params[i] * 1.22, f"{params[i]/1e9:.1f}B", ha="center", va="bottom",
             fontsize=8.6, color=ACC, fontweight="bold")
    ax1.text(i, params[i] * 0.62, f"$d{{=}}{d[i]}$\n$H{{=}}{H[i]}$\n$L{{=}}{L[i]}$",
             ha="center", va="top", fontsize=7.4, color="white")
ax1.set_xticks(xp); ax1.set_xticklabels(names, fontsize=9)
ax1.set_ylim(2.2e9, 1.2e11)
ax1.set_ylabel("parameters (log scale)", fontsize=9)
ax1.set_title(r"The Llama ladder: only $d,H,L$ change [65]", fontsize=9.8)
ax1.grid(True, axis="y", alpha=0.25, which="both")

ax2.plot(xp, aspect, "o-", color=ASP, lw=1.8, ms=7, mfc="white", mec=ASP, mew=1.6)
for i in range(4):
    ax2.text(i, aspect[i] + 3, f"{aspect[i]:.0f}", ha="center", fontsize=8.2,
             color=ASP, fontweight="bold")
ax2.set_xticks(xp); ax2.set_xticklabels(names, fontsize=9)
ax2.set_ylim(80, 145)
ax2.set_ylabel("aspect ratio  $d / L$", fontsize=9)
ax2.set_title("Width/depth stays in a narrow band", fontsize=9.6)
ax2.grid(alpha=0.25)
ax2.axhspan(100, 128, color=ASP, alpha=0.08)

fig.tight_layout()
fig.savefig(HERE / "appendix-f-scale-ladder.svg", bbox_inches="tight")
print("wrote appendix-f-scale-ladder.svg")
print("  aspect d/L:", aspect.round(1).tolist())
