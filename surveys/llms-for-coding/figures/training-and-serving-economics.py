"""The two economics of §3.5: where training compute goes, and how serving is made cheap.

Two panels. Deterministic (fixed constants + closed-form arrays; no rng).

(left, SOURCED) Training tokens per stage, log scale. For a single model the
training compute is C ~= 6 * N * D (params x tokens), so at fixed N the
per-stage COMPUTE ratio equals the per-stage TOKEN ratio — which is why a tokens
axis reads directly as "where the compute goes." DeepSeek-Coder reports both of
its stages in tokens from one paper: pretraining (from scratch) 2 trillion tokens
vs instruction-tuning (SFT) 2 billion tokens — a 1000x gap. Faint reference dots
show the pattern is general across open code LLMs (Qwen2.5-Coder 5.5T, StarCoder2
3.3-4.3T pretraining; Code Llama ~5B instruction tokens). The third stage,
RL/preference alignment, is the honest gap: it is smaller still and rarely
reported in tokens at all (DeepSeek-Coder has no RL stage; Qwen2.5-Coder's DPO
data size is not reported). CodeRL's executable-reward RL, for instance, runs
over ~1e4 APPS problems — a count of problems, not a token budget.

All token values are STATED in the cited papers (no FLOP figure is invented):
  DeepSeek-Coder [10]  pretraining 2T tokens (abstract); SFT 2B tokens (sec 3.7).
  Qwen2.5-Coder [11]   5.5T pretraining tokens (Table 1 "# Trained Tokens").
  StarCoder2    [9]    3.3-4.3T tokens (abstract).
  Code Llama    [6]    ~5B instruction-tuning tokens (sec 2.6).
  CodeRL        [19]   APPS = 10,000 problems (sec 4.2) for the RL stage.

(right, ANALYTICAL) Serving cost vs generation length T, counted in transformer
"block-passes" (one token passed once through the stack). Generating T tokens
WITHOUT a KV cache reprocesses the growing prefix every step: token t costs t
block-passes, so the total is sum_{t=1}^T t = T(T+1)/2 = O(T^2). WITH a KV cache
each new token costs ONE block pass (it attends to the cached keys/values of the
prefix instead of recomputing them), so the total is T = O(T). At T = 8192 that
is 33,558,528 vs 8192 block-passes, a ~4097x reduction; the ratio is (T+1)/2.
(The per-token attention-to-past term is O(t) either way; the cache removes the
prefix RECOMPUTATION, which is exactly what "one block pass rather than
reprocessing the whole prefix" names.)

Outputs:
  training-and-serving-economics.svg
  training-and-serving-economics.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent
np.seterr(divide="ignore", over="ignore", invalid="ignore")

# ---------------------------------------------------------------------------
# Panel A data (SOURCED, tokens). Values STATED in the cited papers.
# ---------------------------------------------------------------------------
DSC_PRETRAIN = 2e12     # DeepSeek-Coder pretraining, 2T tokens         [10]
DSC_SFT = 2e9           # DeepSeek-Coder instruction tuning, 2B tokens  [10]
QWEN_PRETRAIN = 5.5e12  # Qwen2.5-Coder pretraining, 5.5T tokens        [11]
SC2_PRETRAIN_HI = 4.3e12  # StarCoder2 pretraining upper bound          [9]
SC2_PRETRAIN_LO = 3.3e12  # StarCoder2 pretraining lower bound          [9]
CL_SFT = 5e9            # Code Llama instruction tuning, ~5B tokens     [6]
ratio_train = DSC_PRETRAIN / DSC_SFT   # = 1000

# ---------------------------------------------------------------------------
# Panel B data (ANALYTICAL): cumulative block-passes to generate T tokens.
# ---------------------------------------------------------------------------
T = np.arange(1, 16385)
cached = T.astype(float)                       # one block pass per new token
uncached = T * (T + 1) / 2.0                   # reprocess the t-token prefix each step
T_mark = 8192
unc_mark = T_mark * (T_mark + 1) / 2.0         # 33,558,528
cac_mark = float(T_mark)                        # 8192
ratio_serve = unc_mark / cac_mark               # = (T+1)/2 = 4096.5

data = {
    "panel_a_tokens": {
        "DeepSeek-Coder_pretraining": DSC_PRETRAIN, "DeepSeek-Coder_SFT": DSC_SFT,
        "pretrain_over_SFT_ratio": ratio_train,
        "Qwen2.5-Coder_pretraining": QWEN_PRETRAIN,
        "StarCoder2_pretraining_range": [SC2_PRETRAIN_LO, SC2_PRETRAIN_HI],
        "CodeLlama_SFT": CL_SFT,
        "alignment_note": "CodeRL RL over 10000 APPS problems (problems, not tokens); DeepSeek-Coder has no RL stage; Qwen DPO data not reported",
    },
    "panel_b_blockpasses": {
        "T_mark": T_mark, "uncached_total": unc_mark, "cached_total": cac_mark,
        "ratio": ratio_serve, "ratio_formula": "(T+1)/2",
    },
}
with open(HERE / "training-and-serving-economics.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== FIGURE ====================================
PRE_C, SFT_C, ALIGN_C, REF_C, EDGE = "#7c3aed", "#16a34a", "#dc2626", "#6b7280", "#374151"
CACHE_C, NOCACHE_C = "#16a34a", "#dc2626"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.0))

# ---- Panel A: training tokens per stage (log scale, sourced) --------------
ax1.set_yscale("log")
ax1.bar(0, DSC_PRETRAIN, width=0.55, color=PRE_C, alpha=0.85, edgecolor=EDGE, zorder=3)
ax1.bar(1, DSC_SFT, width=0.55, color=SFT_C, alpha=0.85, edgecolor=EDGE, zorder=3)
ax1.text(0, DSC_PRETRAIN * 1.5, "2T", ha="center", va="bottom", fontsize=9.5, color=PRE_C, fontweight="bold")
ax1.text(1, DSC_SFT * 1.5, "2B", ha="center", va="bottom", fontsize=9.5, color=SFT_C, fontweight="bold")

# cross-model reference dots (pattern is general) — all STATED values
ax1.scatter([0, 0], [QWEN_PRETRAIN, SC2_PRETRAIN_HI], marker="D", s=26, color=REF_C, zorder=4)
ax1.annotate("Qwen2.5-Coder 5.5T [11]", (0, QWEN_PRETRAIN), xytext=(0.32, QWEN_PRETRAIN),
             fontsize=6.8, color=REF_C, va="center")
ax1.annotate("StarCoder2 3.3–4.3T [9]", (0, SC2_PRETRAIN_HI), xytext=(0.32, SC2_PRETRAIN_HI * 0.86),
             fontsize=6.8, color=REF_C, va="center")
ax1.scatter([1], [CL_SFT], marker="D", s=26, color=REF_C, zorder=4)
ax1.annotate("Code Llama ~5B [6]", (1, CL_SFT), xytext=(1.30, CL_SFT),
             fontsize=6.8, color=REF_C, va="center")

# 1000x bracket between pretraining and SFT
ax1.annotate("", xy=(0, DSC_PRETRAIN), xytext=(0, DSC_SFT),
             arrowprops=dict(arrowstyle="<->", color=EDGE, lw=1.1))
ax1.text(0.04, np.sqrt(DSC_PRETRAIN * DSC_SFT), r"$\mathbf{1000\times}$",
         fontsize=11, color=EDGE, ha="left", va="center",
         bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=EDGE, alpha=0.9))

# alignment: honest annotation, NOT a token bar
ax1.annotate("", xy=(2, 6e8), xytext=(2, 3e9),
             arrowprops=dict(arrowstyle="-|>", color=ALIGN_C, lw=1.4, ls="--"))
ax1.text(2, 5e8,
         "RL / preference: smaller still,\nrarely reported in tokens\n(CodeRL RL $\\approx 10^4$ problems [19])",
         ha="center", va="top", fontsize=6.9, color=ALIGN_C)

ax1.set_xticks([0, 1, 2])
ax1.set_xticklabels(["Pretraining\n(next-token + FIM)", "SFT\n(instruction)", "Alignment\n(RL / preference)"],
                    fontsize=8.0)
ax1.set_xlim(-0.6, 2.7)
ax1.set_ylim(1e8, 2e13)
ax1.set_ylabel("training tokens  (log scale)", fontsize=9)
ax1.set_title("Almost all training compute is pretraining\n(DeepSeek-Coder [10]; tokens $\\Rightarrow$ compute at fixed $N$)",
              fontsize=9.8)
ax1.grid(True, axis="y", alpha=0.25, which="both")

# ---- Panel B: KV-cache serving cost (analytical, log-log) -----------------
ax2.loglog(T, uncached, color=NOCACHE_C, lw=2.0,
           label=r"no cache: $\sum_{t=1}^{T} t = T(T{+}1)/2 = O(T^2)$")
ax2.loglog(T, cached, color=CACHE_C, lw=2.0,
           label=r"KV cache: $T = O(T)$  (one block pass / token)")
ax2.fill_between(T, cached, uncached, color=NOCACHE_C, alpha=0.06)
ax2.axvline(T_mark, color=EDGE, ls=":", lw=1.0)
ax2.annotate(rf"at $T={T_mark}$: {unc_mark/1e6:.1f}M vs {int(cac_mark)}" "\n"
             rf"$\Rightarrow$ ~{ratio_serve:.0f}$\times$ fewer  (ratio $=(T{{+}}1)/2$)",
             xy=(T_mark, unc_mark), xytext=(60, unc_mark * 1.4),
             fontsize=7.6, color=EDGE,
             arrowprops=dict(arrowstyle="-|>", color=EDGE, lw=1.0),
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=EDGE, alpha=0.9))
ax2.text(1.2, 4e7, "per token: reprocess the\n$t$-token prefix  vs  one block pass",
         fontsize=7.4, color=REF_C, va="top")
ax2.set_xlabel("tokens generated,  $T$", fontsize=9)
ax2.set_ylabel("cumulative block-passes", fontsize=9)
ax2.set_title("KV cache turns serving from $O(T^2)$ into $O(T)$", fontsize=9.8)
ax2.grid(True, alpha=0.25, which="both")
ax2.legend(fontsize=7.8, loc="lower right")

fig.tight_layout()
fig.savefig(HERE / "training-and-serving-economics.svg", bbox_inches="tight")
print("wrote training-and-serving-economics.svg / .json")
print(f"  Panel A: pretrain {DSC_PRETRAIN:.0e} / SFT {DSC_SFT:.0e} = {ratio_train:.0f}x")
print(f"  Panel B: at T={T_mark}, uncached={unc_mark:.0f}, cached={cac_mark:.0f}, ratio={ratio_serve:.1f}x")
