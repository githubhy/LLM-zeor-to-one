---
id: 2026-07-02-05
title: Induction task had a fixed-offset positional shortcut — a 1-layer model solved it, defeating H1
severity: high
status: fixed
date: 2026-07-02
component: implementation/tiny_transformer/data.py
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Symptom

The Phase-1 H1 sanity check (a 1-layer attention-only model should FAIL synthetic
induction; a 2-layer one should succeed, §A.18) failed: BOTH a 2-layer and a
1-layer attention-only model reached induction accuracy 1.000, with a high
"induction score" (~0.95) even at 1 layer. H1 would have been falsely refuted and
the task would have been non-diagnostic for the entire induction study.

## Root cause

The first `make_induction_batch` built each sequence as a random FIRST HALF
followed by an EXACT COPY at a FIXED offset (T/2). With learned absolute
positional embeddings, a single attention head can then attend at a FIXED RELATIVE
OFFSET (query t → key t−T/2+1) purely from position — a "positional copy" head —
and copy the value, with NO content matching and NO previous-token composition.
So a 1-layer model solves the fixed-offset task via a positional shortcut. This is
exactly the confound the induction literature and appendix-c §C.10 warn about
(positional/memorization shortcut vs genuine induction); the task did not isolate
the two-layer previous-token → induction K-composition mechanism.

## Fix

Rewrote `make_induction_batch` to use a **variable per-sequence offset**: a
random-length prefix followed by a repeated random block, so the repeat offset
(and absolute position) differ every sequence. No fixed relative-offset head
works; genuine content-matching induction is required. The generator now also
returns per-query `attend_pos` (the position an induction head should attend to),
used by the attention-score metrics. Re-verified: 2-layer `ind_acc` 0.985
(induction score 0.799; a previous-token head 0.374 emerges in L0), 1-layer
`ind_acc` 0.137 (induction score 0.072) — H1 now holds (2L ≫ 1L). Commit: pending.

## Regression test

`tests/tiny_transformer/test_core.py::test_variable_offset` (asserts the repeat
offset varies across sequences) and `::test_induction_data_property` (asserts the
target at each induction query equals the token at `attend_pos`). The full
training-level H1 (2L ≫ 1L accuracy) is re-confirmed in Phase 3.

## Refs

- Plan H1 (§A.18); appendix-c §C.10 (positional / memorization confounds).
- decision `2026-07-02-05` (execution approach); conversation log Conversation 65.
