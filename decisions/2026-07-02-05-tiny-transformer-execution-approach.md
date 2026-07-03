---
id: 2026-07-02-05
title: Tiny-transformer study execution — torch model for the toy + GPT-2 rungs (numpy Appendix-C toy as the hand-derived-math reference), background install, MVP scope
status: accepted
date: 2026-07-02
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

User: "implement the plan" (ultracode on). Environment probe of this Windows host:
Python 3.13 with numpy/scipy/matplotlib/pandas/pytest present, but **torch,
transformer_lens, transformers, datasets, einops, sklearn all MISSING, no GPU, 18
CPU cores, 796 GB free**. The plan makes TransformerLens the required analysis
dependency (§8.1, "load our trained toy models into a HookedTransformer") and
reuses the pure-numpy Appendix-C toy as a math-faithful reference (§8.1); §8.5
keeps the correctness-critical core sequential. The prior SAE-frontier study
(decision 2026-07-02-01) targeted a Mac/MPS host — heavy compute is not assumed to
run on this box.

## Decision

1. **The 2-layer induction model is implemented in torch** (once the background
   install lands): robust autograd (no hand-derived multi-head / 2-layer backprop
   bugs), CPU-fast, and loadable into a TransformerLens `HookedTransformer` so the
   toy gets the *same* activation-cache / hook / ablation / patching analysis path
   as GPT-2 — exactly §8.1's intent.
2. **The verified pure-numpy Appendix-C toy is the hand-derived-math H5 reference**
   (`surveys/llms-for-coding/figures/appendix-c-toy-transformer.py`, gradient-check
   rel-err 1.6e-9). A finite-difference gradient check on the torch induction model
   confirms its forward/backward independently (H5 at the induction scale).
3. **Install torch/TransformerLens/transformers/datasets/einops/sklearn in the
   background** (global Python, CPU wheels) — enables both the torch toy model and
   Rung 3 (pretrained GPT-2 small).
4. **MVP scope this session: Rung 1 (toy, fully) + Rung 3 (pretrained GPT-2, as
   compute allows).** Defer **Rung 2 (mini-GPT-2 ~10M from scratch —
   CPU-prohibitive without a GPU)** and full-scale sweeps to a GPU host, tracked in
   `todos/`.
5. **Global pip install** (reversible via `pip uninstall`), not a venv — avoids
   per-subprocess activation across the many `python` calls the harness makes.

## Alternatives considered

- **Hand-derive numpy multi-head / 2-layer backprop for the toy training core.**
  Rejected — high bug risk at this scale, slower CPU training, and it forgoes the
  TransformerLens uniformity (same hook path for toy and GPT-2) that §8.1 wants.
  The hand-derived *math* is still verified — by the single-block Appendix-C toy
  (item 2), which is the actual H5 artifact.
- **venv / conda.** Rejected — global install is reversible and simpler for the
  study's many python subprocesses.
- **Ask the user to choose scope / host.** Rejected — the repo's execution model is
  autonomous (CLAUDE.md: "Plan execution stays autonomous… every judgment-call
  decision is persisted under ./decisions/"). Installing pip packages + bounded CPU
  compute are reversible, not the risky-irreversible class that warrants a pause.

## Consequences

- While the install runs, build the torch-agnostic scaffolding (config, data, utils,
  weight-space circuit math). Model + training + analysis land once torch is in.
- Rung 1 (Phases 2–3, most of Phase 4, Phase 5) is completable in-session on CPU;
  Rung 3 (Phase 4b) unlocks after the install; Rung 2 + full-scale H10–H19 deferred.
- Follow-ups → `todos/`: mini-GPT-2 rung on a GPU host; the auto-interp source-fetch
  (already noted in the plan) before Bundle-K auto-interp.

## Refs

- Plan §8 (open decisions), §8.1 (framework), §8.5 (execution mode).
- Env probe + background install `bgvvl2x4c` (Conversation 65); tasks #1–#6.
- `decisions/2026-07-02-03` (the coverage amendments this executes).
