---
id: 2026-07-01-04
title: Add a full per-head role census across seeds (H4b) to the tiny-transformer plan, not just induction-head index tracking
status: accepted
date: 2026-07-01
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

The reviewer asked whether the plan retrains the MHA across seeds to see "what
kind of attention a head focuses on." The plan already retrains across ≥5 seeds
(Phase 3) and tracks head-role seed-dependence — but **only for the induction
head** (H4: "the induction-head index permutes while the circuit recurs"). It had
no step classifying what *every* head attends to (previous-token, induction,
positional/diagonal, first-token/BOS sink, diffuse) or asking which of those
*roles* recur across seeds vs which *indices* permute — i.e. a full per-head role
census. The required TransformerLens attention-pattern capture (Phase 2) makes
such a census nearly free.

## Decision

Add a **head-role census** as first-class scope. New hypothesis **H4b**
(Quantitative): across seeds the full per-head role census recurs up to
permutation — a fixed pattern-statistic battery classifies every head, the *set*
of roles is seed-stable (each seed grows a layer-1 previous-token head and a
layer-2 induction head), and the head *index* holding each role permutes. Wired
into Phase 4 (toy/from-scratch census with a seed × head → role matrix and a
permutation-invariant recurrence measure), Phase 4b (a single-model real-GPT-2
census over the full head zoo, cross-checked against the published taxonomy — no
retraining), Phase-1 metrics, §4 figures (a seed × head role heatmap), and §6
stretch (at-scale). H4 is left intact as the narrower induction-index claim.

## Alternatives considered

- **Leave it at H4 (induction head only).** Rejected: the reviewer's question is
  about *every* head; the narrow claim answers only a slice.
- **Promote H4 to Quantitative instead of adding H4b.** Rejected: H4 is
  inherently a categorical permutation claim about one role; the census is the
  Quantitative object (role frequencies + recurrence), so a distinct H4b is
  cleaner than overloading H4.
- **Census on the toy rung only.** Rejected: the interesting head zoo
  (duplicate-token, name-mover, attention-sink) only appears at GPT-2 scale, so a
  Phase-4b real-model census is added — but as a single-model census (GPT-2 is
  loaded, not retrained), not a seed study.
- **Free-form per-head inspection without a fixed battery.** Rejected: a fixed,
  named statistic battery makes the census reproducible and the recurrence claim
  falsifiable.

## Consequences

- **Enables:** a reproducible "what does each head do, and is it seed-stable"
  map — the general form of the induction-index result — at near-zero new
  compute (reuses the required attention-pattern capture).
- **Adds scope:** two analysis bullets (Phase 4 + Phase 4b), one figure, one
  metric, one hypothesis; no new training path.
- **Forecloses nothing;** H4 and the induction spine are unchanged.
- Real-model census stays citation-safe: head-role labels read out at analysis
  time and cross-checked against the published taxonomy, never asserted from
  memory.

## Refs

- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md` §2 (H4b), §3
  Phase 1/4/4b, §4, §6, and the Rung-applicability + ladder-table cells.
- Prior plan decisions: `decisions/2026-07-01-01` (GPT-2 ladder),
  `decisions/2026-07-01-03` (ICL fold).
- Survey anchors: §A.10 (a layer is a sum of h distinct low-rank circuits;
  Figure A.10 per-head routing dissimilarity), §A.11 (co-adaptation).
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md`.
