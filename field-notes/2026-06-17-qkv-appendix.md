# Field Notes — 2026-06-17 — Q/K/V first-principles appendix

## Context

Authored Appendix A ("Query, Key, and Value from First Principles", 12 sections
+ 4 numerical figures) into `surveys/llms-for-coding/` and ran a 5-arm
adversarial review workflow (`wf_7fba1273-8b7`). The math was verified correct
(numerically + finite-difference) by the review, but three quality issues were
caught and fixed inline. Capturing them because they share a theme — the gap
between "looks right" and "is precise" in a figure-bearing math derivation.

## Issues found and resolved

- **Figure A.2 caption asserted a wrong number (near-miss).** The caption said
  the `√d_k`-scaled softmax peak weight holds "near the uniform value `1/16`"
  (≈0.0625). The regenerated JSON shows the scaled peak is flat at ~0.25 across
  all `d_k` — the dotted `1/16` line is the *uniform floor*, not the curve. The
  peak weight of a near-uniform softmax over 16 keys is ~0.25, not `1/16`. The
  qualitative claim (width-invariance) was right; the number was wrong and
  contradicted the figure's own plotted curve. Caught by the figure-consistency
  reviewer cross-checking each caption number against the regenerated JSON.
  Fixed to "~0.25, flat across `d_k`, above the `1/16` floor." No bug filed —
  caught and fixed before delivery. *Why missed:* the number was written from
  the mental model ("near uniform") instead of read off the generator output.

- **Eq (12) collapsed a multi-line step under a no-skipped-steps mandate.** The
  softmax-score gradient reduction from `Σ_j (δ_i v_jᵀ) a_ij (δ_jm − a_im)` to
  `a_im δ_i (v_m − o_i)ᵀ` was a single `=`, and the chain-rule bridge
  `∂L/∂a_ij = δ_i v_jᵀ` was implicit. The user explicitly required no skipped
  steps. Fixed by inserting the bridge sentence and two intermediate equation
  lines. *Why missed:* it is the densest algebra in the appendix, easy to write
  as one line because the author already "sees" the collapse.

- **A.11 title/roadmap overclaimed.** "Why Training Drives the Matrices There"
  promised convergence to the A.8–A.9 routing/copy structures, but the gradient
  identity only proves the QK and OV circuits *co-adapt*. Retitled to "Why the
  QK and OV Circuits Co-Adapt" and added a sentence distinguishing
  constructible/empirical structure from what the descent argument proves. *Why
  missed:* the title was written to match the section's *motivation*, not its
  *theorem*.

## Patterns / lessons

- A figure-bearing math appendix needs two dedicated review passes that paid off
  here: (1) **caption-number vs regenerated-JSON** consistency — every numeric
  claim in a caption must be read off the generator's output, never the mental
  model; (2) **densest-step expansion** — point a reviewer at the single most
  compressed derivation (here a softmax-Jacobian → gradient collapse) and demand
  the intermediate lines.
- Section titles should state what the section *proves*, not what *motivates*
  it; "drives/causes/proves" verbs in a title invite an overclaim.
- These were the two highest-value arms of the review workflow; worth making
  them standard for any survey section that pairs derivations with generated
  figures. See decision `2026-06-17-02` (citation scoping for the same appendix).
