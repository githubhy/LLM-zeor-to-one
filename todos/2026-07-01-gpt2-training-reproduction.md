---
slug: gpt2-training-reproduction
date_filed: 2026-07-01
status: open
---

# Reproduce GPT-2 (124M) training from scratch at real scale

## Context

The tiny-transformer induction study (decision `2026-07-01-01`) augments to a toy→real ladder but **loads** pretrained GPT-2 small rather than training it, because a 16 GB laptop needs ~3 weeks to train 124M from scratch (feasibility: `wikis/laptop-scale-training-feasibility.md`; memory fits in ~2 GB, compute is the wall). Consequently the induction-head phase change / emergence is only observed at the toy (~0.17M) and mini-GPT-2 (~10M) rungs, never at real 124M scale.

## What is left

- Provision compute (rented multi-GPU, e.g. 8×A100 for ~hours, on the order of tens of dollars) or an equivalent cloud budget.
- Reproduce GPT-2 124M training (e.g. nanoGPT / llm.c on OpenWebText or FineWeb), checkpointing densely enough to catch the induction-head phase change.
- Run the head-dump + circuit-match analysis across training checkpoints to test H2 (phase change) and H4 (seed-permutation) at 124M scale.

## Acceptance

- A training-loss + in-context-loss curve for 124M exhibiting the induction phase change, with head dumps before/after the knee.
- Circuit-match-to-theory (QK previous-token concentration, OV copying score) tracked across checkpoints.
- A report section (or appendix) comparing emergence at 0.17M / 10M / 124M.

## Refs

- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md` (Phase 4b, rung 3).
- Decision: `decisions/2026-07-01-01-augment-tiny-transformer-study-with-gpt2-ladder.md`.
- Feasibility: `wikis/laptop-scale-training-feasibility.md`.
