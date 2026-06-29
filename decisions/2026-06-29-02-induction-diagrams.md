---
id: 2026-06-29-02
title: Add two §A.9 induction-head diagrams (two-layer circuit + Eq-9 anatomy)
status: accepted
date: 2026-06-29
plan: n/a (direct request)
---

## Context

After a Q&A clarifying what "one layer" means in §A.9 ("An Induction Head, Built
by Hand"), the user asked to "add diagrams to illustrate the ideas." §A.9 already
had Figure A.7 (the *behavioral* bar charts: attention peak + predicted token).
The two ideas without a diagram were (a) the **two-layer composition** — the very
"one layer earlier" / K-composition point just discussed — and (b) the
**`(M, W_OV)` one-hot matchers** of Equation (9). Figures have no auto-renumber
script (cf. decision 2026-06-28-05), so adding figures forces a manual cascade.

## Decision

Add two matplotlib→SVG schematics in §A.9 (reusing the house `panel`/`card`/
`arrow` idiom and indigo-QK / amber-prev / emerald-OV palette), each with a
companion `.json` (Diagram Rules): `qkv-induction-two-layer` (Figure A.8 — the
cross-layer circuit, with the K-composition link and the "one layer earlier"
bracket) and `qkv-induction-anatomy` (Figure A.9 — Equation 9 drawn literally as
two one-hot block matchers). Both are appended **after** Figure A.7 so A.7 keeps
its number; the only cascade is the two later captions A.8→A.10, A.9→A.11 (no
external "Figure A.8/A.9" refs exist). The two-layer figure runs the same
hand-built head as Figure A.7 so its annotated weight (0.91) and prediction
(A, 0.88) are computed, not asserted.

## Alternatives considered

- **One combined diagram.** Rejected: the user asked for "diagrams" (plural), and
  one figure mixing cross-layer composition and matrix anatomy was visibly busy.
- **Insert before Figure A.7** (mechanism-before-result order). Rejected: would
  also renumber A.7 and enlarge the cascade for no real gain; A.7's behavioral
  view reads fine first, with the two schematics as "two further views."
- **Plain-text / ASCII description instead of figures.** Rejected: the survey's
  convention is generated SVG figures with persisted data and numbered captions.

## Consequences

- Figure labels now run A.1–A.11 in reading order; `validate-refs` 0/0 (34 image
  refs valid), lint/section/paragraph `--check` clean, no crosslink gaps.
- New stable anchors `sec-A.9-figure-b` / `sec-A.9-figure-c` (section-local b/c
  indexing, decoupled from the cascading display number).
- Captions disclose the schematic operating conditions (hand-built, no training,
  vocab {A..F}, stream, β/γ, computed-and-deterministic numbers) per the
  figure-operating-conditions rule.

## Refs

- Files: `surveys/llms-for-coding/figures/qkv-induction-two-layer.{py,svg,json}`,
  `qkv-induction-anatomy.{py,svg,json}`, `appendix-a-qkv-first-principles.md`
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 3
- Related: decision `2026-06-28-05` (figure-renumber cascade precedent)
