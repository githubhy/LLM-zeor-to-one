"""Figure H.2 — the scale sweep: nine orders of magnitude, one architecture.

Left: total vs active parameters across the five models, log scale — from the
203-parameter toy to DeepSeek-V3's 671B, with the active count diverging from the
total only at the MoE frontier. Right: the trained context length over the same
models, from 3 tokens to 128K. The point of the pair: every axis of "scale" grew
by orders of magnitude while the core computation (Appendices C-G) stayed fixed.

Sourced: Toy (C, defined); GPT-2 XL 1.5B / 1024 ctx [61]; Llama 7B 6.7B / 4096
[65,63]; Llama 70B / 4096 [63]; DeepSeek-V3 671B total, 37B active, 128K ctx [64].

Output: appendix-h-scale-sweep.svg / .json
"""
import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

models = ["Toy", "GPT-2 XL", "Llama 7B", "Llama 70B", "DeepSeek-V3"]
total = [203, 1.542e9, 6.7e9, 70e9, 671e9]
active = [203, 1.542e9, 6.7e9, 70e9, 37e9]
context = [3, 1024, 4096, 4096, 128000]

data = {"models": models, "total_params": total, "active_params": active, "context": context}
with open(HERE / "appendix-h-scale-sweep.json", "w") as f:
    json.dump(data, f, indent=1)

TOT, ACT, CTX, EDGE = "#c4b5fd", "#6d28d9", "#0891b2", "#374151"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8))
x = np.arange(len(models))

ax1.plot(x, total, "o-", color=ACT, lw=1.8, ms=8, mfc=TOT, mec=ACT, mew=1.8,
         label="total params (capacity)")
ax1.plot(x, active, "s--", color=ACT, lw=1.4, ms=6, mfc="white", mec=ACT,
         label="active params / token")
ax1.set_yscale("log")
for i, (t, a) in enumerate(zip(total, active)):
    lab = f"{t:.0f}" if t < 1e3 else (f"{t/1e9:.1f}B" if t >= 1e9 else f"{t/1e6:.0f}M")
    ax1.text(i, t * 1.7, lab, ha="center", fontsize=8.0, color=ACT, fontweight="bold")
ax1.annotate("MoE splits\ntotal from active", xy=(4, 37e9), xytext=(2.3, 6e9),
             fontsize=8.0, color="#dc2626",
             arrowprops=dict(arrowstyle="-|>", color="#dc2626", lw=1.0))
ax1.set_xticks(x); ax1.set_xticklabels(models, fontsize=8.4, rotation=12)
ax1.set_ylabel("parameters (log scale)", fontsize=9.2)
ax1.set_ylim(50, 5e12)
ax1.set_title("Capacity: 203 → 671B (9 orders)", fontsize=10)
ax1.grid(axis="y", alpha=0.25, which="both"); ax1.legend(fontsize=8, loc="upper left")

ax2.plot(x, context, "D-", color=CTX, lw=1.8, ms=7, mfc="white", mec=CTX, mew=1.8)
ax2.set_yscale("log")
for i, c in enumerate(context):
    lab = f"{c}" if c < 1000 else f"{c//1000}K"
    ax2.text(i, c * 1.6, lab, ha="center", fontsize=8.0, color=CTX, fontweight="bold")
ax2.set_xticks(x); ax2.set_xticklabels(models, fontsize=8.4, rotation=12)
ax2.set_ylabel("trained context length (log scale)", fontsize=9.2)
ax2.set_ylim(2, 5e5)
ax2.set_title("Context: 3 → 128K tokens", fontsize=10)
ax2.grid(axis="y", alpha=0.25, which="both")

fig.tight_layout()
fig.savefig(HERE / "appendix-h-scale-sweep.svg", bbox_inches="tight")
print("wrote appendix-h-scale-sweep.svg")
