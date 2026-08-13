---
id: 2026-08-13-01
title: run_phase3.py resume key ignores CFG — a reduced-config seed is silently reused as a full-config one
severity: high
status: open
date: 2026-08-13
component: implementation/tiny_transformer
---

## Symptom

`run_phase3.py` resumes by filename existence:

```python
def _seed_path(n_layers, seed):
    return os.path.join(ART, f"seed_{n_layers}L_{seed}.json")
...
todo = [j for j in jobs if not os.path.exists(_seed_path(*j))]
```

The key is `(n_layers, seed)`. **`CFG` is not in it** — but `CFG` is what
distinguishes the reduced CPU pass from the full-scale run:

```python
CFG = dict(n_ctx=64, batch=128, steps=800, eval_every=50, threads=14)
```

So the moment `CFG` is edited to the plan's headline config (`n_ctx=256`,
`batch=256`, 20k steps) and the script is re-run over the same artifact
directory, every seed already trained at the reduced config is reported
`skip (already done)` and silently retained.

`aggregate()` then globs `seed_*.json`, pools whatever it finds, and stamps the
summary with a single `config=CFG` field naming the **full** config:

```python
summary = dict(config=CFG, n_seeds_2L=len(acc2), ...)
```

The result is a `phase3_summary.json` that claims 5 seeds at `n_ctx=256`/20k steps
while some or all were trained at `n_ctx=64`/800 steps. Nothing errors, nothing
warns, and the artifact looks complete. Reproducer: run at the reduced config, edit
`CFG`, re-run — observe `skip (already done)` and a full-config summary built from
reduced-config seeds.

## Root cause

Resume identity was derived from the **job** (`layers:seed`) rather than from the
*(job, config)* pair that actually determines the artifact's contents. That was
sound while `CFG` was a fixed module constant — the reduced pass was the only pass
that existed — and it silently becomes wrong the first time the config is treated
as a variable, which is precisely the reduced → full-scale transition the study
defers to a GPU host.

The deeper shape: the config **is** recorded, faithfully, inside each seed record
(`rec = dict(..., config=CFG, ...)`), so the information needed to detect the
mismatch is on disk. Nothing reads it back. `aggregate()` discards it — it copies
every key **except** `history` into `per_seed`, so each seed's own `config` does
survive into the summary, while the top-level `config=CFG` asserts the current
one over all of them. A reader takes the top-level field.

This is the silent-wrong-output class: the number reproduces exactly on every
re-run, because the number was never the problem — the story attached to it was
(`.claude/rules/calibration-residuals.md` check 6).

## Fix

Not yet applied. Two changes, both small:

1. **Put the config in the resume identity.** Either hash `CFG` into the filename
   (`seed_{n_layers}L_{seed}_{cfghash}.json`) or read the existing record's
   `config` and treat a mismatch as not-done. The second is preferable: it keeps
   filenames stable and makes the check explicit rather than implicit in a hash.
2. **Make `aggregate()` refuse a heterogeneous pool.** It already has each seed's
   `config` in hand; assert they are identical and equal to `CFG`, and fail loudly
   otherwise. Related: `H1_pass` is currently computed from whatever seeds exist,
   so a 1-seed pool yields a verdict — gate on the expected seed count too.

## Regression test

None yet. Required before the fix lands, and it must be RED first
(`[opt:PLAN-REDFIRST]`): train one seed at config A, mutate `CFG` to config B,
re-run, and assert the seed is retrained rather than skipped — plus an
`aggregate()` case asserting a mixed pool raises rather than summarising.

## Refs

- Found by the resumability audit mandated as the precondition of
  `todos/2026-07-02-tiny-transformer-gpu-host-rungs.md` (the road's first topic).
- `decisions/2026-08-13-01-learning-road.md` — why that precondition exists.
- Sibling findings from the same audit, tracked in
  `todos/2026-08-13-phase3-resumability-hardening.md`: no intra-run checkpointing
  (per-seed resume granularity), and no Rung-2 implementation.
- `.claude/rules/calibration-residuals.md` check 6 — reproducibility is not
  verification.
- `prompts/2026-08-12-upstream-sync.md` Conversation 7.
