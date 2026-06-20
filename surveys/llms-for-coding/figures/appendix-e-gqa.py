"""Figure E.4 — the MHA / GQA / MQA spectrum and the KV-cache it saves.

Left: head-sharing schematic — H=8 query heads mapped to G key/value heads, for
G=8 (MHA), G=2 (GQA), G=1 (MQA). Right: the per-token KV-cache memory, which scales
with G not H, so GQA at G=8 on an H=32 model cuts the cache 4x and MQA 32x.

GQA: Ainslie et al. 2023, used by Llama-2 34B/70B [63]; the KV-cache argument ties
to the serving-cost analysis of the main survey (Section 3.5.1).

Output: appendix-e-gqa.svg
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
Q_C, KV_C, EDGE = "#2563eb", "#dc2626", "#374151"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6),
                               gridspec_kw={"width_ratios": [1.5, 1.0]})

# --- left: head-sharing schematic ---
ax1.set_xlim(0, 12); ax1.set_ylim(0, 10); ax1.axis("off")
ax1.set_title("Query heads share key/value heads (H = 8 query heads)", fontsize=9.6)
H = 8
configs = [("MHA  (G=8)", 8, 9.2), ("GQA  (G=2)", 2, 6.0), ("MQA  (G=1)", 1, 2.8)]
xq = np.linspace(1.2, 6.0, H)
for name, G, y in configs:
    # query heads (top row of this band)
    for i, x in enumerate(xq):
        ax1.add_patch(plt.Rectangle((x - 0.22, y + 0.25), 0.44, 0.5, fc=Q_C,
                      ec=EDGE, lw=0.6))
    # kv heads (bottom row), G of them spread under the queries
    xkv = np.linspace(1.2, 6.0, G) if G > 1 else np.array([3.6])
    for x in xkv:
        ax1.add_patch(plt.Rectangle((x - 0.30, y - 1.05), 0.60, 0.5, fc=KV_C,
                      ec=EDGE, lw=0.6))
    # mapping lines query -> its kv group
    grp = H // G
    for i, x in enumerate(xq):
        kv = i // grp
        ax1.plot([x, xkv[kv]], [y + 0.25, y - 0.55], color="#9ca3af", lw=0.7, zorder=0)
    ax1.text(7.2, y - 0.15, name, fontsize=8.6, fontweight="bold", color=EDGE)
    ax1.text(10.8, y - 0.15, f"cache $\\propto$ {G}", fontsize=8.0, color=KV_C, ha="right")
ax1.add_patch(plt.Rectangle((9.0, 0.4), 0.4, 0.45, fc=Q_C, ec=EDGE, lw=0.6))
ax1.text(9.5, 0.62, "query head", fontsize=7.6, va="center", color=EDGE)
ax1.add_patch(plt.Rectangle((9.0, -0.2), 0.4, 0.45, fc=KV_C, ec=EDGE, lw=0.6))
ax1.text(9.5, 0.02, "K/V head (cached)", fontsize=7.6, va="center", color=EDGE)

# --- right: KV-cache memory vs G for an H=32 model ---
labels = ["MHA\nG=32", "GQA\nG=8", "MQA\nG=1"]
G = np.array([32, 8, 1])
ratio = G / 32.0
colors = ["#9ca3af", "#7c3aed", "#16a34a"]
bars = ax2.bar(range(3), ratio, color=colors, edgecolor=EDGE, width=0.62)
for i, r in enumerate(ratio):
    ax2.text(i, r + 0.02, f"{r*100:.0f}%\n({1/r:.0f}$\\times$)" if r > 0 else "",
             ha="center", va="bottom", fontsize=8.0, color=EDGE, fontweight="bold")
ax2.set_xticks(range(3)); ax2.set_xticklabels(labels, fontsize=8.4)
ax2.set_ylabel("KV-cache per token  (fraction of MHA)", fontsize=8.6)
ax2.set_title("Cache scales with $G$, not $H$ (here $H{=}32$)", fontsize=9.4)
ax2.set_ylim(0, 1.15); ax2.grid(axis="y", alpha=0.25)

fig.tight_layout()
fig.savefig(HERE / "appendix-e-gqa.svg", bbox_inches="tight")
print("wrote appendix-e-gqa.svg")
