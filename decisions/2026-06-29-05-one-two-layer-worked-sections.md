---
id: 2026-06-29-05
title: Fill the one-/two-layer "written out in full" gap as §A.19+§A.20 worked examples (not a new appendix)
status: accepted
date: 2026-06-29
plan: n/a (direct request, after an opinion turn the user accepted)
---

## Context

The user asked whether a separate appendix deriving one- and two-layer attention
from first principles (heavy no-step-missing math, intuitions, diagrams) was a
good idea. A coverage survey showed Appendix A already derives attention from
first principles (single head §A.2–§A.8 → one-layer multi-head §A.10 → two-layer
composition §A.9/§A.18) and Appendix C already gives a no-step-missing end-to-end
forward+backward pass of a full toy transformer. The genuine gap was a single,
isolated, numbers-in → numbers-out forward pass of ONE attention layer and then
TWO stacked, traced explicitly — a flavor neither A's circuit-algebra nor C's
full-block pass provides.

## Decision

Fill the gap as two worked-example sections appended at the end of Appendix A —
§A.19 "One Attention Layer, Written Out in Full" and §A.20 "Two Layers Stacked:
the Same Computation, Composed" — each with a deterministic compute+figure
(Figure A.12, A.13), rather than creating a new appendix.

## Alternatives considered

- **A new standalone appendix.** Rejected: would duplicate Appendix A (the
  first-principles derivation) and Appendix C (the explicit pass), fragment the
  attention story, and cost new `order.json` / `init-doc` scaffolding plus its own
  renumber / validate / cross-link surface.
- **One combined section A.19.** Rejected in favor of two: a one-layer pass and a
  two-layer composition trace are distinct units; the appendix uses flat, focused
  2-level sections, so two read and navigate better. Both append at the end →
  cascade-free.
- **Symbolic-only derivation.** Rejected: the user asked for concrete,
  no-step-missing math; a numeric worked example (with the softmax as the only
  decimals) is the strongest realization, and every value is computed by a
  committed script per the Diagram Rules.

## Consequences

- Appendix A now runs A.1–A.20; equations (21)–(28) and figures A.12/A.13 added,
  all at the file end so nothing cascades — section numbers, equation tags (new
  are highest), and (hand-numbered) figure numbers all extend rather than shift.
- Two new figure scripts (`qkv-one-layer-forward`, `qkv-two-layer-trace`) with
  companion `.json`; every cited value is reproducible.
- Citations: reused [60] (Olsson 2022, verified this session) for the
  in-context-learning tie; the mechanics are derived inline. No new bib entries.
- New cross-link targets (an explicit one-/two-layer pass) for future links from
  §A.9/§A.10/§A.18 and Appendix C.

## Refs

- Files: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.19/§A.20;
  `figures/qkv-one-layer-forward.{py,svg,json}`, `qkv-two-layer-trace.{py,svg,json}`
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversations 7–8
- Field note: `field-notes/2026-06-29-a19-a20-worked-figures.md`
- Related: decision `2026-06-29-04` (A.18 composition — the algebra these sections
  trace); decision `2026-06-28-05` (figure-renumber cascade precedent)
