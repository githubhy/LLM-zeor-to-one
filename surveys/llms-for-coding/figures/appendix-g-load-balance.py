"""Figure G.3 — load balancing: routing collapse vs a balanced router.

Left: without a balancing mechanism the router collapses — a few experts win almost
all tokens and the rest are never trained (dead), wasting the model's capacity.
Right: DeepSeek-V3's auxiliary-loss-free bias b_i nudges the top-k selection toward
even utilization, so every expert sees roughly its fair share (here 1/256 of tokens
times 8 active = the dashed target). Illustrative distributions (synthetic), with
the per-expert target load drawn from the sourced N_r=256, K_r=8 config [64].

Output: appendix-g-load-balance.svg
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
rng = np.random.default_rng(3)

Nr, Kr = 64, 8                              # show 64 experts for legibility (V3 uses 256)
target = Kr / Nr                            # mean fraction of tokens each expert sees

# collapsed: a few experts dominate (power-law-ish), many near zero
collapse = rng.pareto(1.1, Nr) + 0.02
collapse = collapse / collapse.sum() * Kr
# balanced: tight around the target
balanced = target + rng.normal(0, target * 0.18, Nr)
balanced = np.clip(balanced, 0, None)
balanced = balanced / balanced.sum() * Kr

COLL, BAL, TGT, EDGE = "#dc2626", "#16a34a", "#374151", "#374151"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.4), sharey=True)
xx = np.arange(Nr)

ax1.bar(xx, collapse, color=COLL, edgecolor="none", width=0.9)
ax1.axhline(target, color=TGT, ls="--", lw=1.2)
ax1.set_title("Routing collapse: a few experts win, most are dead", fontsize=9.6)
ax1.set_xlabel("expert index", fontsize=8.8)
ax1.set_ylabel("share of tokens routed", fontsize=8.8)
dead = int((collapse < 0.2 * target).sum())
ax1.text(0.97, 0.92, f"{dead}/{Nr} experts ~dead", transform=ax1.transAxes,
         ha="right", fontsize=8.0, color=COLL, fontweight="bold")
ax1.text(Nr * 0.5, target * 1.15, "fair-share target", fontsize=7.4, color=TGT)

ax2.bar(xx, balanced, color=BAL, edgecolor="none", width=0.9)
ax2.axhline(target, color=TGT, ls="--", lw=1.2)
ax2.set_title("Balanced (auxiliary-loss-free bias $b_i$): even utilization", fontsize=9.6)
ax2.set_xlabel("expert index", fontsize=8.8)
ax2.text(0.97, 0.92, "all experts trained", transform=ax2.transAxes,
         ha="right", fontsize=8.0, color=BAL, fontweight="bold")

fig.suptitle("Why the router needs balancing (target = $K_r/N_r$, here 8/64)", fontsize=10.2, y=1.02)
fig.tight_layout()
fig.savefig(HERE / "appendix-g-load-balance.svg", bbox_inches="tight")
print("wrote appendix-g-load-balance.svg")
