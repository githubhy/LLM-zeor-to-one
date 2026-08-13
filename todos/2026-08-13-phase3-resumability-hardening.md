---
slug: phase3-resumability-hardening
date_filed: 2026-08-13
status: open
---

# Phase-3 resumability hardening — the first topic's precondition work

## Context

`decisions/2026-08-13-01` made a resumability audit of
`implementation/tiny_transformer/run_phase3.py` the precondition of the road's first
topic: at ~5 USD a billing slice, a driver that cannot resume at zero recompute cannot
be run inside the budget at all. The audit ran 2026-08-13. This file is its output.

**One half of the precondition already passes.** Single-writer-per-checkpoint is
satisfied by construction: each job writes its own `seed_{L}L_{seed}.json` and
`model_{L}L_{seed}.pt`, with no shared file and no read-modify-write. Parallelising
across seeds on a multi-GPU host is therefore safe as-is — the hazard
`.claude/rules/workflow.md` warns about (two live writers on one checkpoint) does not
exist here. The `from multiprocessing import Pool` import is dead, left over from the
switch to a sequential loop.

The other half does not pass, in three ways.

## What is left

### 1. Config-blind resume key — `bugs/2026-08-13-01` (high, silent wrong output)

Resume keys on `(n_layers, seed)` and ignores `CFG`, so the reduced → full-scale
config change silently reuses reduced-config seeds and `aggregate()` labels the pooled
summary with the current config. Full symptom, root cause, proposed fix and the
RED-first regression test are in the bug record. **Fix this first** — it is the only
finding that produces a wrong artifact rather than a slow one, and it fires on exactly
the transition this topic is.

### 2. No intra-run checkpointing — resume granularity is a whole seed

`train_toy` (`model.py`) has **no checkpoint write anywhere in its loop**. The history
dict accumulates in memory and the only persistence is `save_json` + `torch.save` in
`train_seed`, *after* `train_toy` returns. A kill mid-seed loses the entire seed.

At the reduced config (800 steps) that is a few minutes and nobody noticed. At the
plan's headline config (`n_ctx=256`, `batch=256`, 20k steps) a single seed is the
dominant unit of work, and losing one to a torn-down instance loses most of a billing
slice. This is the literal failure the precondition exists to prevent.

Needed: periodic state persistence inside the loop (model + optimizer + RNG state +
step + history-so-far, at an interval independent of `eval_every`), plus a resume path
that reloads it and continues. Note the RNG requirement — restoring weights without
restoring `rng` / `eval_rng` / torch RNG state resumes onto a different data stream,
which is a *silent* determinism break, not a crash.

### 3. Rung 2 has no implementation

The audit's largest finding, and it re-scopes the topic. `build_toy` is the **only**
model factory in the package, and all four `PRESETS` are toy-scale (`d_model=128`,
`d_vocab=64`, attention-only or a 512-wide MLP) — the ~0.17M rung. `data.py` generates
**only synthetic** batches (`make_induction_batch`, `make_corrupt_batch`,
`make_modadd_data`); there is no text corpus loader, no tokenizer, and no
`tiny-shakespeare` path anywhere in `implementation/`.

So Rung 2 (the ~10M mini-GPT-2 from scratch) is not "run the existing code at a bigger
config." It needs a new model preset with MLPs at real width, a real-text data
pipeline, and a training entry point. That is bring-up work, and it is **local, unpaid
work** — it must be done and tested on CPU at tiny scale before any compute is rented,
or the rented hours get spent debugging.

### 4. GPU determinism disclosure (small, do it with 2)

`train_toy`'s docstring claims "Deterministic given seeds". True on CPU — seeding is
clean (`torch.manual_seed`, `np.random.default_rng`, a separate `eval_rng`, no
wall-clock). Not guaranteed on GPU: attention and reduction kernels are not
bit-reproducible by default (`.claude/rules/workflow.md`). Either set
`torch.use_deterministic_algorithms` on the GPU path or amend the claim to
"deterministic within kernel tolerance" and state the tolerance — do not let a CPU-true
docstring travel silently onto a GPU host.

### 5. `aggregate()` publishes from a partial pool (med, do it with 1)

`H1_pass` is computed from whatever `seed_*.json` files exist, so a 1-seed pool yields
a verdict. `n_seeds_2L` discloses the count but nothing gates on it. Assert the
expected seed count before emitting a verdict.

## Acceptance

- `bugs/2026-08-13-01` closed with its RED-first regression test green.
- A killed run at the full config resumes and completes with **zero recomputed steps**,
  demonstrated by a log whose progress counter is strictly increasing across the kill.
- Resumed-vs-uninterrupted runs agree (bit-identical on CPU; within a stated tolerance
  on GPU), proving RNG state was restored and not just weights.
- A Rung-2 model + data path exists and trains end-to-end on CPU at a deliberately tiny
  setting, before any compute is rented.
- `aggregate()` refuses a heterogeneous or short seed pool.

## Refs

- `bugs/2026-08-13-01-phase3-resume-key-ignores-config.md`.
- `todos/2026-07-02-tiny-transformer-gpu-host-rungs.md` — the topic this gates.
- `decisions/2026-08-13-01-learning-road.md` — why the precondition precedes spend.
- `.claude/rules/workflow.md` (flush-and-resume, one writer per checkpoint, seeding),
  `.claude/rules/reset-durability.md` (checkpoint-mtime staleness as the death signal).
- `prompts/2026-08-12-upstream-sync.md` Conversation 7.
