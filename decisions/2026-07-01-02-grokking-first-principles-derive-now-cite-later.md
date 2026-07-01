---
id: 2026-07-01-02
title: Add a first-principles grokking treatment (survey §C.8 + plan H7), derive-now / cite-later
status: accepted
date: 2026-07-01
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

The user noticed grokking was in the plan (a stretch "second circuit" task) but never derived in the survey, and asked to (1) fold a grokking subsection into the survey with the "why" expanded in **full first-principles detail**, and (2) expand the plan's grokking task into a defined study.

Constraint: `references.md` holds no grokking paper ([59]/[60] cover the circuits/induction framework, both `(web)`). Writing the standard grokking attributions (Power 2022, Nanda 2023, Varma 2023, Liu/Omnigrok 2022, Wei 2022, Schaeffer 2023) would be new external citations — forbidden from memory by the citation-integrity rule — and acquiring all of them via `source-fetch` is a large, uncertain detour that the *derivation itself* does not need.

## Decision

Write the survey §C.8 as a **self-contained first-principles derivation** with **no external citations**, and defer the empirical-attribution citations to a tracked `source-fetch` pass. The derivation covers: the generalizing circuit is a Fourier multiplication (embedding as rotations → product-to-sum → readout by the roots-of-unity / Dirichlet-kernel resonance, so it is correct on all p² pairs); the delay is a minimum-norm-interpolant selection under weight decay (on the zero-train-loss manifold the dynamics reduce to the weight-decay gradient, which favors the low-norm Fourier circuit over the high-norm lookup table — predicting the weight-decay dependence rather than asserting it); and a Fourier-concentration progress measure that rises before the validation jump. A "Provenance" note in §C.8 states the deferral explicitly. In the plan, add hypothesis H7 and a grokking second-circuit sub-study (progress-measures protocol + weight-decay ablation).

## Alternatives considered

- **Source-fetch the grokking papers first, then write with citations** — rejected as the up-front path: a large, uncertain acquisition the self-contained derivation does not depend on. It is the *follow-up* (tracked todo), consistent with decision `2026-06-17-02`'s "derive everything first-principles so no claim rests on a citation."
- **Write with from-memory author-year citations** — rejected: a direct citation-integrity violation (the exact failure the rule guards against).
- **Note-only / lighter fold** — rejected: the user asked for full first-principles detail, which is `full`-mode with a real derivation (8 numbered equations).

## Consequences

- **Survey:** §C.8 added to `appendix-c-toy-transformer.md` (Equations 11–18, appended at file end so they extend the tag sequence rather than cascading earlier equations) + an inline Note at §C.5. All renumber/validate gates green (18 sequential tags, 90 markers survey-wide, 0 errors).
- **Plan:** H7 + a rung-applicability line + a defined grokking sub-study in §6 + refs.
- **Open item:** §C.8 is derivation-complete but citation-incomplete until the `source-fetch` pass runs — tracked in `todos/2026-07-01-source-fetch-grokking-citations.md`. Do not treat §C.8 as delivery-signed-off until that todo closes.

## Refs

- Survey: `surveys/llms-for-coding/appendix-c-toy-transformer.md` §C.8 (+ §C.5 Note).
- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md` (H7, §6 sub-study).
- Deferred: `todos/2026-07-01-source-fetch-grokking-citations.md`.
- Conversation log: `prompts/2026-07-01-tiny-transformer-progressive-build.md` (Conversations 6–7).
