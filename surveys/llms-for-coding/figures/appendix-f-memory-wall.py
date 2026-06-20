"""Figure F.2 — the memory wall: why a 70B trains across many devices.

Training state per parameter, derived from mixed-precision Adam (Appendix C.4 keeps
a first and second moment per weight): 2 bytes bf16 weights + 2 bytes bf16 grads +
4 bytes fp32 master + 4 bytes Adam m + 4 bytes Adam v = 16 bytes/param. Inference
needs only the 2-byte weights (+ KV cache). The figure stacks those components for
7B and 70B against a single 80 GB accelerator line; 70B training (~1.1 TB) sits far
above it, so the model's state must be sharded across many devices.

All arithmetic (no external source): byte counts follow from the Adam definition.

Output: appendix-f-memory-wall.svg / .json
"""
import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

# bytes per parameter for mixed-precision Adam training
comp = [("bf16 weights", 2, "#2563eb"),
        ("bf16 grads", 2, "#0891b2"),
        ("fp32 master", 4, "#7c3aed"),
        ("Adam $m$", 4, "#db2777"),
        ("Adam $v$", 4, "#f59e0b")]
bytes_per_param = sum(c[1] for c in comp)   # 16
N = {"7B": 6.7e9, "70B": 70.0e9}
GPU = 80.0   # GB, one current accelerator (illustrative round figure)

mem = {k: {c[0]: c[1] * v / 1e9 for c in comp} for k, v in N.items()}
infer = {k: 2 * v / 1e9 for k, v in N.items()}
data = {"bytes_per_param_train": bytes_per_param,
        "train_GB": {k: round(16 * v / 1e9) for k, v in N.items()},
        "infer_GB": {k: round(2 * v / 1e9) for k, v in N.items()},
        "gpu_GB": GPU}
with open(HERE / "appendix-f-memory-wall.json", "w") as f:
    json.dump(data, f, indent=1)

fig, ax = plt.subplots(figsize=(9.2, 5.4))
labels = ["7B\ntrain", "7B\ninfer", "70B\ntrain", "70B\ninfer"]
xpos = [0, 1, 2.4, 3.4]

# training stacks
for sz, x in [("7B", 0), ("70B", 2.4)]:
    bot = 0
    for name, b, color in comp:
        h = b * N[sz] / 1e9
        ax.bar(x, h, bottom=bot, width=0.7, color=color, edgecolor="white", lw=0.6,
               label=name if sz == "7B" else None, zorder=3)
        bot += h
    ax.text(x, bot + 18, f"{bot:.0f} GB\n($16N$)", ha="center", va="bottom",
            fontsize=8.4, fontweight="bold", color="#374151")
# inference bars
for sz, x in [("7B", 1), ("70B", 3.4)]:
    h = 2 * N[sz] / 1e9
    ax.bar(x, h, width=0.7, color="#9ca3af", edgecolor="#374151", lw=0.8, zorder=3)
    ax.text(x, h + 18, f"{h:.0f} GB\n($2N$)", ha="center", va="bottom", fontsize=8.0,
            color="#374151")

ax.axhline(GPU, color="#dc2626", lw=1.6, ls="--", zorder=4)
ax.text(3.9, GPU + 8, f"one {GPU:.0f} GB device", color="#dc2626", fontsize=8.4,
        ha="right", fontweight="bold")
ax.annotate("70B training state\n$\\approx$ 14 devices",
            xy=(2.4, 1120), xytext=(0.7, 980), fontsize=8.4, color="#374151",
            arrowprops=dict(arrowstyle="-|>", color="#374151", lw=1.0))

ax.set_xticks(xpos); ax.set_xticklabels(labels, fontsize=8.8)
ax.set_ylabel("memory (GB)", fontsize=9.5)
ax.set_ylim(0, 1260)
ax.set_title("The memory wall: training state is $16N$ bytes (Adam, §C.4), inference $2N$",
             fontsize=10)
ax.legend(fontsize=8, loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.09))
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()
fig.savefig(HERE / "appendix-f-memory-wall.svg", bbox_inches="tight")
print("wrote appendix-f-memory-wall.svg")
print("  train GB:", data["train_GB"], " infer GB:", data["infer_GB"])
