"""Figure G.2 — MoE decouples capacity (total params) from compute (active params).

For dense models, every parameter is active on every token, so total = active and
the forward cost (~2N FLOPs/token) rises with capacity. MoE breaks the tie: only a
few experts fire per token, so total parameters can grow far past the active count
that sets per-token compute. Sourced totals/actives: dense 7B and 70B (App. E-F);
DeepSeek-Coder-V2 236B/21B active [43]; DeepSeek-V3 671B/37B active [64].

Output: appendix-g-decoupling.svg / .json
"""
import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

models = ["Dense\n7B", "Dense\n70B", "DS-Coder-V2\n236B (MoE)", "DeepSeek-V3\n671B (MoE)"]
total = np.array([7.0, 70.0, 236.0, 671.0])
active = np.array([7.0, 70.0, 21.0, 37.0])
frac = active / total

data = {"models": models, "total_B": total.tolist(), "active_B": active.tolist(),
        "active_fraction": [round(float(x), 3) for x in frac]}
with open(HERE / "appendix-g-decoupling.json", "w") as f:
    json.dump(data, f, indent=1)

TOT, ACT, EDGE = "#c4b5fd", "#6d28d9", "#374151"
fig, ax = plt.subplots(figsize=(9.6, 5.3))
x = np.arange(len(models)); w = 0.4
ax.bar(x - w / 2, total, w, color=TOT, edgecolor=EDGE, label="total params (capacity)")
ax.bar(x + w / 2, active, w, color=ACT, edgecolor=EDGE, label="active params / token (compute)")
ax.set_yscale("log")
for i in range(len(models)):
    ax.text(i - w / 2, total[i] * 1.1, f"{total[i]:.0f}B", ha="center", va="bottom",
            fontsize=8.2, color=EDGE)
    ax.text(i + w / 2, active[i] * 1.1, f"{active[i]:.0f}B", ha="center", va="bottom",
            fontsize=8.2, color=ACT, fontweight="bold")
    if frac[i] < 1:
        ax.text(i, 3.2, f"only {frac[i]*100:.0f}%\nactive", ha="center", fontsize=7.8,
                color="#dc2626", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(models, fontsize=8.6)
ax.set_ylabel("parameters, billions (log scale)", fontsize=9.5)
ax.set_ylim(3, 1100)
ax.set_title("MoE: capacity grows to 671B while per-token compute stays at 37B", fontsize=10.2)
ax.legend(fontsize=8.4, loc="upper left")
ax.grid(axis="y", alpha=0.25, which="both")

fig.tight_layout()
fig.savefig(HERE / "appendix-g-decoupling.svg", bbox_inches="tight")
print("wrote appendix-g-decoupling.svg")
print("  active fraction:", [f"{x*100:.0f}%" for x in frac])
