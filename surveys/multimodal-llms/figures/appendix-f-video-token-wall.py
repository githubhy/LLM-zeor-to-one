"""Appendix F.5: the video token-budget wall, and what each lever actually buys.

Two panels. Fully deterministic -- closed forms only, no rng at all, nothing
measured from a model.

THE EQUATION (appendix F, Eq. 9). Sampling a clip to F frames and encoding each
frame into N_v^frame patch tokens costs

    N_video = F * N_v^frame = F * (H*W / P^2)

so the budget is a product of three independent levers: the sampling rate (which
sets F), the per-frame token count (set by resolution H*W and patch size P, and
reducible by spatial merging), and any hard cap imposed on the product.

(left) N_video against clip length, for five configurations the survey cites, on
log-log axes, with four context-window reference lines. The point of the panel is
that the model curves are STRAIGHT LINES OF SLOPE 1 in log-log -- the budget is
LINEAR in duration -- while the context is a HORIZONTAL line. Two lines of
different slope always cross, so the wall is structural: it is not a matter of
buying a bigger context, only of moving the crossing point to the right. The
three annotated points are the survey's worked rows (30 s, 5 min, 2 h).

(right) What lever 3 (a hard cap on the product, Qwen2-VL's 16384) costs. If the
TOTAL is fixed and the rate is fixed, then per-frame tokens must fall as 1/t:

    N_per_frame(t) = N_cap / (rate * t)

That curve is plotted against the per-frame counts the encoders actually produce.
The cap does not fail loudly -- it degrades silently, and the panel shows the
duration at which it crosses below each usable per-frame count.

TWO BASIS DECLARATIONS, both load-bearing (repo rule: a quantity measurable on
two bases declares which).
  (i) "128k context" is read DECIMAL here (128,000 tokens), matching the survey
      prose. The binary reading (131,072) changes the 2-hour overshoot from 64.8x
      to 63.3x. Neither is wrong; quoting one while computing the other is.
  (ii) Video-LLaVA's 8 frames is a fixed BUDGET, not a rate, so its curve is
      FLAT. Every other curve here is a genuine frames-per-second rate. Plotting
      them on one axis is the point (the flat line is what "8 frames" really
      means at 2 hours), but they are not the same kind of quantity.

WHAT THIS FIGURE IS NOT. No model was run, nothing here is measured, and no
benchmark score appears. Both panels are arithmetic on Eq. 9 with published
encoder parameters substituted in. Per-frame counts are derived as (H/P)^2 from
each model's own stated resolution and patch size; the merge factors and the
16384 cap are quoted from the cited papers.

Outputs:
  appendix-f-video-token-wall.svg
  appendix-f-video-token-wall.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
# Byte-reproducible SVG: fix the salt matplotlib uses to generate element ids,
# and drop the wall-clock <dc:date> at savefig (see metadata= below). Without both,
# re-running an UNCHANGED generator rewrites every id and the date, producing a
# multi-hundred-line diff in which a real change would be invisible. (bugs/2026-08-15-03)
matplotlib.rcParams["svg.hashsalt"] = "appendix-f-video-token-wall"
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
STEM = "appendix-f-video-token-wall"

P = 14                      # ViT patch size, CLIP-L/14 lineage
TOK_336 = (336 // P) ** 2   # 576 tokens for a 336-px frame
TOK_224 = (224 // P) ** 2   # 256 tokens for a 224-px frame
MERGE = 4                   # Qwen2-VL: adjacent 2x2 tokens merged into one
RATE = 2.0                  # Qwen2-VL samples video at two frames per second
CAP = 16384                 # Qwen2-VL: total tokens per video limited to 16384
VIDEO_LLAVA_FRAMES = 8      # Video-LLaVA: 8 frames uniformly sampled, fixed
QWEN_PER_FRAME_224 = 66     # 256 -> 64 merged + 2 boundary tokens, as stated

# Context windows. DECIMAL basis (see docstring): 128k means 128,000 tokens.
CONTEXTS = [("8k", 8_000), ("32k", 32_000), ("128k", 128_000), ("1M", 1_000_000)]

MARKS = [(30.0, "30 s"), (300.0, "5 min"), (7200.0, "2 h")]

t = np.logspace(0, np.log10(7200.0), 400)     # 1 s .. 2 h


def n_video(seconds, tokens_per_frame, rate):
    """Eq. 9 with F = rate * duration."""
    return rate * seconds * tokens_per_frame


CONFIGS = [
    ("336 px, no merge, 2 fps  (survey's worked row)", TOK_336, RATE, "#d62728", 2.4, "-"),
    ("224 px, no merge, 2 fps", TOK_224, RATE, "#ff7f0e", 1.9, "-"),
    (f"336 px, 2$\\times$2 merge ({TOK_336 // MERGE} tok/frame), 2 fps",
     TOK_336 // MERGE, RATE, "#1f77b4", 1.9, "-"),
]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.2, 4.6))

for label, tpf, rate, color, lw, ls in CONFIGS:
    axL.plot(t, n_video(t, tpf, rate), lw=lw, ls=ls, color=color, label=label)

# Lever 1 taken to its limit: a FIXED frame budget is a horizontal line.
axL.plot(t, np.full_like(t, VIDEO_LLAVA_FRAMES * TOK_224), lw=1.8, ls="--", color="#2ca02c",
         label=f"8 frames fixed, 224 px  = {VIDEO_LLAVA_FRAMES * TOK_224:,} tok (no rate at all)")
# Lever 3: cap the product.
axL.plot(t, np.minimum(n_video(t, TOK_336, RATE), CAP), lw=1.8, ls=":", color="#9467bd",
         label=f"336 px, 2 fps, capped at {CAP:,} tok")

for name, ctx in CONTEXTS:
    axL.axhline(ctx, color="0.62", lw=0.9, ls="-.")
    axL.text(1.15, ctx * 1.14, f"{name} context", color="0.42", fontsize=7.6)

for x, name in MARKS:
    axL.axvline(x, color="0.85", lw=0.8)
    axL.text(x * 1.06, 2.2e7, name, color="0.5", fontsize=7.6, rotation=90, va="top")

for x, _ in MARKS:
    y = n_video(x, TOK_336, RATE)
    axL.plot([x], [y], "o", ms=4.6, color="#d62728", zorder=5)
    axL.annotate(f"{y:,.0f}", xy=(x, y), xytext=(-4, 7), textcoords="offset points",
                 fontsize=7.8, color="#d62728", ha="right")

axL.set_xscale("log")
axL.set_yscale("log")
axL.set_xlabel("clip length (seconds, log)")
axL.set_ylabel("$N_{\\mathrm{video}}$ (tokens, log)")
axL.set_title("(a) the budget is linear in duration; the context is not", fontsize=10.5)
axL.legend(fontsize=7.4, frameon=False, loc="lower right")
axL.grid(alpha=.22, lw=.5, which="both")
axL.set_ylim(1, 3e7)

per_frame = CAP / (RATE * t)
axR.plot(t, per_frame, lw=2.4, color="#9467bd",
         label=f"per-frame budget under a {CAP:,}-token cap at {RATE:g} fps")

for y, name, color in [(TOK_336, "336 px, no merge (576)", "#d62728"),
                       (TOK_224, "224 px, no merge (256)", "#ff7f0e"),
                       (TOK_336 // MERGE, f"336 px, 2$\\times$2 merge ({TOK_336 // MERGE})", "#1f77b4"),
                       (QWEN_PER_FRAME_224, f"Qwen2-VL 224 px merged ({QWEN_PER_FRAME_224})", "#2ca02c")]:
    axR.axhline(y, color=color, lw=1.0, ls="--", alpha=.75)
    axR.text(1.15, y * 1.13, name, color=color, fontsize=7.4)
    cross = CAP / (RATE * y)          # duration at which the cap falls below y
    if t[0] <= cross <= t[-1]:
        axR.plot([cross], [y], "v", ms=5.0, color=color, zorder=5)

for x, name in MARKS:
    y = CAP / (RATE * x)
    axR.plot([x], [y], "o", ms=4.6, color="#9467bd", zorder=5)
    axR.annotate(f"{y:,.3g}", xy=(x, y), xytext=(10, 9), textcoords="offset points",
                 fontsize=7.8, color="#9467bd", ha="left")

axR.axhline(1.0, color="0.55", lw=0.9, ls=":")
axR.text(1.15, 1.06, "1 token/frame", color="0.42", fontsize=7.4)
axR.set_xscale("log")
axR.set_yscale("log")
axR.set_xlabel("clip length (seconds, log)")
axR.set_ylabel("tokens available per frame (log)")
axR.set_title("(b) a hard cap does not fail loudly -- it starves each frame", fontsize=10.5)
axR.legend(fontsize=7.6, frameon=False, loc="upper right")
axR.grid(alpha=.22, lw=.5, which="both")
axR.set_ylim(0.5, 3e3)

fig.tight_layout()
fig.savefig(HERE / f"{STEM}.svg", metadata={"Date": None})

two_hour = n_video(7200.0, TOK_336, RATE)
data = {
    "provenance": {
        "equation": "N_video = F * N_v^frame = F * (H*W / P^2)  (appendix F, Eq. 9)",
        "nothing_measured": True,
        "deterministic": True,
        "rng_used": False,
        "note": "closed-form arithmetic on published encoder parameters; no model was run",
    },
    "basis_declarations": {
        "context_window_units": "DECIMAL (128k = 128,000 tokens), matching the survey prose",
        "binary_alternative": {"128Ki": 131072,
                               "two_hour_overshoot_binary": round(two_hour / 131072, 2)},
        "video_llava_8_frames": "a fixed frame BUDGET, not a sampling rate; its curve is flat",
    },
    "constants": {
        "patch_size_P": P,
        "tokens_per_frame_336px": TOK_336,
        "tokens_per_frame_224px": TOK_224,
        "spatial_merge_factor": MERGE,
        "sampling_rate_fps": RATE,
        "total_token_cap": CAP,
        "video_llava_fixed_frames": VIDEO_LLAVA_FRAMES,
        "qwen2vl_stated_per_frame_224px": QWEN_PER_FRAME_224,
    },
    "worked_rows_336px_2fps": {
        name: {"seconds": x, "frames": int(RATE * x), "N_video": int(n_video(x, TOK_336, RATE))}
        for x, name in MARKS
    },
    "two_hour_overshoot_vs_context": {
        name: round(two_hour / ctx, 2) for name, ctx in CONTEXTS
    },
    "per_frame_budget_under_cap": {
        name: round(CAP / (RATE * x), 2) for x, name in MARKS
    },
    "cap_falls_below_per_frame_count_at_seconds": {
        "336px_576": round(CAP / (RATE * TOK_336), 2),
        "224px_256": round(CAP / (RATE * TOK_224), 2),
        "336px_merged_144": round(CAP / (RATE * (TOK_336 // MERGE)), 2),
        "qwen2vl_66": round(CAP / (RATE * QWEN_PER_FRAME_224), 2),
    },
    "lever_accounting_at_two_hours": {
        "baseline_N_video": int(two_hour),
        "lever2_2x2_merge_factor": MERGE,
        "after_lever2": int(two_hour / MERGE),
        "still_over_128k_decimal_after_lever2": round((two_hour / MERGE) / 128_000, 2),
        "conclusion": "no single lever closes the gap; lever 2 buys 4x against a 64.8x shortfall",
    },
}
(HERE / f"{STEM}.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

print(f"wrote {STEM}.svg / .json")
for x, name in MARKS:
    print(f"  {name:>6}: N_video = {n_video(x, TOK_336, RATE):>12,.0f}"
          f"   per-frame under cap = {CAP / (RATE * x):>8.2f}")
print(f"  2-hour overshoot: " + ", ".join(
    f"{name} {two_hour / ctx:.2f}x" for name, ctx in CONTEXTS))
