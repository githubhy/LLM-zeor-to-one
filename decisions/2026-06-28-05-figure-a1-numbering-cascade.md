---
id: 2026-06-28-05
title: Number the new §A.1 head block-diagram as Figure A.1 and cascade A.1–A.8 → A.2–A.9
status: accepted
date: 2026-06-28
plan: none (direct authoring request)
---

## Context

The user asked for a block diagram in `appendix-a-qkv-first-principles.md` §A.1
("Setup and Notation") illustrating the parameters in one attention head. Appendix A
numbers its figures **sequentially** (`Figure A.1`…`Figure A.8`), and the number is
independent of the owning section — e.g. `Figure A.1` lives in §A.2, `Figure A.3` in
§A.5. §A.1 had no figure. There is **no figure-renumber script** (unlike equations /
sections / paragraphs): the `**Figure A.N.**` labels and every in-prose `Figure A.N`
reference are plain hardcoded text. The figures' clickable landmark anchors are keyed
to the *section* (`sec-A.2-figure-a`), not the figure number, so anchors are unaffected
by a number change; SVG filenames are likewise unaffected.

A figure added to §A.1 must take a number, which forced a choice with a real
blast-radius tradeoff.

## Decision

Number the new schematic **Figure A.1** (correct reading-order position) and cascade the
existing `Figure A.1`–`A.8` up by one to `A.2`–`A.9`, including the one cross-file
reference in `appendix-b-kernel-regression-family.md` (`Figure A.3` → `Figure A.4`). The
cascade was done as an atomic Python pass replacing `Figure A.{n}`→`A.{n+1}` in
**descending** `n` so no created label collided with an unprocessed original.

## Alternatives considered

- **Figure A.0 (no cascade).** Zero churn, self-contained, and a defensible "orientation
  schematic before the analysis figures" framing. Rejected: `Figure A.0` reads as a typo
  to most readers and breaks the clean 1..N sequence; avoiding correct numbering to dodge
  a mechanical rename is the tail wagging the dog.
- **Figure A.9 (append at the end of the sequence, no cascade).** Also zero churn.
  Rejected: a figure that is physically first (in §A.1) but numbered last is actively
  confusing on a second read.
- **A figure-renumber script + marker system** (mirroring equations/sections). Rejected
  as over-engineering for a one-off insertion; the per-task cost of one descending text
  pass is far below building and maintaining a marker subsystem nothing else needs (YAGNI).

## Consequences

- Figures now read in document order (A.1 = the setup schematic). Clean and conventional.
- Blast radius was bounded and verified: 13 label/reference bumps in appendix-a + 2 in
  appendix-b; `validate-refs` (32 image refs, 114 .md links), section/paragraph/equation
  `--check`, bare-refs, and citation-sources all green; each `**Figure A.N.**` appears
  exactly once for N = 1..9.
- A future figure inserted mid-appendix will hit the same no-script manual-cascade cost.
  Not worth pre-solving now; if it recurs often, revisit a `<!-- fig:N -->` marker scheme
  (explicitly **not** built here — see Alternatives).
- New `Figure A.1` content is fully cross-linked (Eq (1)/(2), §A.2/§A.3/§A.13, cite [54]);
  no new cross-link gaps introduced.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` (§A.1, `sec-A.1-figure-a`)
- Figure script: `surveys/llms-for-coding/figures/qkv-head-parameters.py` (+ `.svg`, `.json`)
- Cross-file ref updated: `surveys/llms-for-coding/appendix-b-kernel-regression-family.md`
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 4)
