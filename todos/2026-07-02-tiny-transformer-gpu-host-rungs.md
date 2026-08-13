---
slug: tiny-transformer-gpu-host-rungs
date_filed: 2026-07-02
status: open
---

# Tiny-transformer study — compute-heavy rungs deferred to a GPU host

## Context

Per decision `2026-07-02-05`, the tiny-transformer study is being implemented on a
no-GPU Windows laptop (18 CPU cores). Rung 1 (the toy) runs in-session on CPU; the
compute-heavy pieces below are impractical on CPU and are deferred to a GPU host.

**Selected as the first topic** (2026-08-13, `decisions/2026-08-13-01`). Status stays
`open` until the precondition below is started — selection is not execution. Rung 2 is
also the agreed *shrink* of `todos/2026-07-01-gpt2-training-reproduction.md`: the
question is whether the induction phase change appears below 124M, and this is the
cheapest scale that can answer it. A negative result is itself the finding.

## What is left

- **PRECONDITION — resumability audit, before any compute is rented.**
  `implementation/tiny_transformer/run_phase3.py` must checkpoint densely enough that a
  killed billing slice resumes at **zero recompute**, with **exactly one writer per
  checkpoint file** (`.claude/rules/workflow.md`; `.claude/rules/reset-durability.md`).
  The rented host is a **compute worker, not a repo clone** — inputs in, checkpoints
  out, every commit made locally. A driver that cannot resume cannot run inside a
  per-experiment budget, so this precedes all spend. Cheap audit on any resumed
  artifact: the progress counter in its log must be strictly increasing.
- **Rung 2 — mini-GPT-2 (~10M) from scratch** on tiny-shakespeare (small vocab):
  the emergence bridge between the toy and pretrained GPT-2 (plan §3 Phase-3 rung 2,
  §6 stretch). CPU-prohibitive.
- **Full-scale Rung-1 Phase 3/4** at the plan's headline config (`n_ctx=256`,
  `batch=256`, ~20k steps, ≥5 seeds) — the in-session pass uses a reduced
  `n_ctx=96 / 2500 steps` config to fit CPU wall-clock. Re-run at full scale for the
  final numbers.
- Any **GPT-2-rung analyses too slow on CPU** at scale (large ACDC sweeps, DAS
  training loops over many positions) — run on GPU if the CPU pass is too slow.
- **Auto-interp (Bundle K stretch)** needs a `source-fetch` of the auto-interp
  reference before any external claim (already noted in the plan and the coverage
  todo).

## Acceptance

Rung 2 trained + analyzed; full-scale Rung-1 numbers reproduced; results folded
into the Phase-6 report with the CPU-pass results superseded/compared.

**Topic-level exit condition** (`decisions/2026-08-13-01`): the topic is not finished
when the report has verdicts — it is finished when **the survey sections that raised the
question cite these measurements in place of the claim they currently cite**. Two named
targets, both already anchored:

- `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` **[§A.22] Claim 2** —
  "co-emergence, the induction phase change (empirical, testable)", currently resting on
  reference [60]. It already specifies the exact experiment: *"overlay the
  ICL-score-versus-step curve on an induction-head-strength-versus-step curve and see
  whether they turn on together."* That overlay, from this study's own run, is the
  deliverable that closes the claim.
- `surveys/mechanistic-interpretability/circuits-across-models.md` **[§9.1]** — the
  Olsson universality claim (reference [80]), whose phase-change signature is currently
  cited rather than measured here.

A **negative** result closes the topic just as well, and is written into the same two
places: if the phase change does not appear at ~10M, Claim 2 gains a measured
scale-boundary it does not currently have.

## Refs

- Plan §3 (rungs), §6 (stretch); decision `2026-07-02-05`.
- Separate: `todos/2026-07-01-gpt2-training-reproduction.md` (124M from scratch).
- Study manifest: `artifacts/induction-tiny/study-manifest.json`.
