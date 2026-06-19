---
id: 2026-06-19-01
title: "LLM-anatomy deep-dive: scope and shape (Appendices C–H)"
status: accepted
date: 2026-06-19
plan: plans/2026-06-19-llm-anatomy-appendix-series.md
---

## Context

User asked for new chapters: a deep survey of LLM structure from the most basic
LLM to the largest, each with detailed anatomy from model top-structure to a
single neuron, end-to-end first-principles math with no step missing, deep
intuition per module, and many diagrams. I proposed a plan and surfaced four
scoping forks; the user chose, then said "go end-to-end automatically unless you
genuinely need my help."

## Decision

Build an appendix series (`appendix-c…appendix-h`) inside the existing
`llms-for-coding` survey, organized *scale-primary* (one chapter per model size,
toy → frontier MoE), with full forward + backward + optimizer math, covering
general frontier models in addition to the already-sourced code LLMs. Honor "no
step missing" without 5x duplication by deriving every invariant in full in the
toy chapter (C) and cross-linking it from D–G, which fully re-derive only their
distinctive components.

## Alternatives considered

- *Standalone new survey* — rejected: loses integration with Appendix A and
  duplicates `references.md`.
- *Main-text Part after section 3* — rejected: forces renumbering every later
  section and a corpus-wide cross-reference migration.
- *Hybrid (anatomy-once + scaling chapter)* — not chosen by the user; would have
  avoided repetition but the user wanted a complete anatomy per scale rung.
- *Verbatim full derivations in every chapter* — rejected as the default: ~5x
  bloat with no added rigor; cross-linking invariants to C is the rigorous
  equivalent (every step derived once and reachable). Revisit if the user wants
  literal inlining.

## Consequences

- Enables a self-contained, comparable anatomy at each rung; appendices add to
  `order.json` before `references.md` and to `index.md`; no main-text renumber.
- Requires acquiring frontier/method papers (task #26) under citation-integrity.
- Large multi-increment build; one chapter per increment, each gated + committed.
  Tracked by tasks #25–#32; first concrete output is the Appendix C calibration
  chapter, reviewed before D–H roll out.

## Refs

- plan `plans/2026-06-19-llm-anatomy-appendix-series.md`; tasks #25–#32.
- conversation log `prompts/2026-06-17-viewer-sync.md`.
- builds on Appendix A (attention anatomy) and section A.13 (concrete dimensions).
