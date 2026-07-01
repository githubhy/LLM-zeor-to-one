---
id: 2026-07-01-01
title: Augment the tiny-transformer induction study with a toy→real GPT-2 ladder (pretrained, not trained)
status: accepted
date: 2026-07-01
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

The plan's original goal was a from-scratch *tiny*-transformer induction study that verifies Appendix-A's QK/OV circuit math (a mechanism microscope). Mid-review the user asked to change the goal to "finally understand the GPT-2 model."

Two problems with that as stated: (1) "understand GPT-2" wholesale is not a bounded deliverable — the interpretability community has worked on GPT-2 small for years without "finishing" it; (2) training GPT-2 small (124M) from scratch is not laptop-feasible — a 16 GB laptop needs ~3 weeks at ~1 TFLOP/s effective (memory fits in ~2 GB; compute is the wall). The full accounting is in `wikis/laptop-scale-training-feasibility.md`.

The user was offered two forks — replace-vs-augment and train-vs-load — and chose **augment**. The train-vs-load fork was then resolved by the feasibility analysis (load).

## Decision

Augment (not replace) the toy study with a **three-rung toy→real ladder**: toy (~0.17M, from scratch) → mini-GPT-2 (~10M, from scratch, small vocab) → pretrained GPT-2 small (124M, weights loaded, **not trained**). Verify Appendix-A's QK/OV structure at each rung; the pretrained rung tests *transfer* to real weights (new hypothesis H6, new Phase 4b / gate G3b). The bounded GPT-2 goal is "reverse-engineer GPT-2 small's induction circuit + verify Appendix-A QK/OV on real weights" (stretch: the IOI circuit), not "understand GPT-2" wholesale. Framework: first-party core (reuse the Appendix-C toy) plus TransformerLens for the pretrained-GPT-2 rung.

## Alternatives considered

- **Replace the toy with GPT-2-small interp only** — rejected: loses the closed-form ground truth (H3 has no hand-built target on a real model) and the training-emergence story (H2 phase change, H4 seed-permutation). The toy is the only rung you can *verify* against a hand-built circuit.
- **Replace with GPT-2 architecture reproduction (nanoGPT forward pass)** — rejected as the primary framing: it is an engineering reproduction, lighter on the circuit/mechanism content the survey drives. Kept as a verification step inside rung 3 (logit parity vs a reference implementation).
- **Train GPT-2 124M from scratch on the laptop** — rejected: ~3 weeks wall-clock; memory would fit but compute does not. Deferred to a rented-GPU follow-on (see todo).
- **Keep the literal, unbounded "understand GPT-2" goal** — rejected: not a bounded deliverable; narrowed to the induction-circuit transfer above.

## Consequences

- **Enables:** real-model validation of Appendix-A (a stronger survey contribution than a toy alone); keeps the emergence story cheap (rungs 1–2); stays laptop-native end to end.
- **Adds to the plan:** hypothesis H6 (transfer) + a rung-applicability note; a three-rung config table; a mini-GPT-2 bullet in Phase 3; a new Phase 4b (pretrained GPT-2, gate G3b); resolved §8 decisions 1–2.
- **Forecloses (for now):** watching the induction phase change at real 124M scale — that needs a training reproduction, deferred to `todos/2026-07-01-gpt2-training-reproduction.md`.
- **New dependency:** TransformerLens on the analysis path for the GPT-2 rung.
- Citation hygiene reminder carried into the plan: GPT-2 induction-head indices are read out of the model at analysis time, never asserted from memory.

## Refs

- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md` (§1 ladder paragraph, H6, Phase 4b, §8).
- Feasibility: `wikis/laptop-scale-training-feasibility.md`.
- Deferred: `todos/2026-07-01-gpt2-training-reproduction.md`.
- Conversation log: `prompts/2026-07-01-tiny-transformer-progressive-build.md` (Conversations 2–3).
