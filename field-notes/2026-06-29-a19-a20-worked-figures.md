# Field Notes — 2026-06-29 — §A.19/§A.20 worked-example figures

## Context

Authored §A.19/§A.20 (one-/two-layer attention worked examples) for
`appendix-a-qkv-first-principles.md`, with two new deterministic compute+figure
scripts (`qkv-one-layer-forward`, `qkv-two-layer-trace`) and embedded numeric
results that the prose cites.

## Issues found and resolved

- **Degenerate value rows in the one-layer example.** The first `W_V` choice made
  value rows 1–2 identical (a coincidence of the integer weights), so the
  one-layer output could not distinguish attending position 1 vs 2 —
  pedagogically weak though not wrong. Swapped `W_V` to a permutation giving
  distinct value rows that is also visibly different from `W_Q`. Caught by reading
  the script's printed `V` before rendering. No-todo because fixed in the same
  pass.
- **Three figure-label collisions, invisible in source.** PNG rasterization
  (cairosvg absent → `runpy` the script then `plt.gcf().savefig(png)` to the
  scratchpad) revealed: (a) the one-layer "mask + softmax" arrow label overlapping
  the `√d_k` superscript of the S-box title; (b) the two-layer green "match"
  annotation overlapping the pos-1/pos-2 one-hot blocks; (c) the two-layer
  panel-3 "OV copies…" subtitle colliding with the `0.96` bar-value label. Fixed by
  raising the label, relocating the annotation below the blocks and reconnecting
  the match arrow to the two highlighted A-slots, and raising the panel-3 ylim and
  titles. All resolved inline.

## Patterns / lessons

- The "render to PNG and actually look" step keeps paying off — every one of these
  was invisible in the SVG/source and obvious in the raster (the same lesson as
  the §A.9 figures). Treat it as a required step of figure authoring, not an
  afterthought.
- For worked-example figures, print and eyeball the underlying numbers *before*
  drawing — a degenerate weight choice produces a correct-but-uninformative figure
  that no layout check would catch.
- `cairosvg` is not installed in this environment; `runpy.run_path(script)` then
  `plt.gcf().savefig(png, bbox_inches="tight")` is the working SVG→PNG inspection
  path.
