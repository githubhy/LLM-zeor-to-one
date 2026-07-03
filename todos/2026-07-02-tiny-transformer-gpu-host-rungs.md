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

## What is left

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

## Refs

- Plan §3 (rungs), §6 (stretch); decision `2026-07-02-05`.
- Separate: `todos/2026-07-01-gpt2-training-reproduction.md` (124M from scratch).
- Study manifest: `artifacts/induction-tiny/study-manifest.json`.
