---
id: 2026-07-04-01
title: Regenerate the corrected H15 stats block via a deterministic --refresh-stats mode, not a full re-run
status: accepted
date: 2026-07-04
plan: plans/2026-07-03-h15-automated-discovery.md
---

## Context

The audit-driven fix for bug `2026-07-03-02` (pseudo-replicated faithfulness p) changed the
faithfulness significance from the pooled per-example unit (n=160, p=5.3e-29) to the honest
seed-level unit (n=5, p=0.024) and split the `pairwise` block into `faith_ref_seedlevel__`
(gated) + `faith_ref_pooled__` (descriptor). The committed baseline artifact
(`artifacts/induction-discovery/baseline/summary.json`, produced on MPS) still carried the old
single-key pooled-headline form, so the artifact did not match the corrected report.

To reconcile them, the artifact's `pairwise` block had to be regenerated. Reality intervened:

- The MPS re-run **stalled** — ~30 min wall / ~30 min CPU with zero seed output — confirming the
  field-note lesson that this hooked, small-batch, many-forward workload is MPS-pathological.
- The CPU re-run was healthy but **slow**: a single seed's full protocol (157-forward
  `exact_patch` scan + faithfulness across 7 circuit sizes × 4 candidates) did not finish in
  ~17 min; the full 5-seed loop projected to **~45–75 min**.
- Crucially, the run is **deterministic** (fixed seeds): a full re-run would reproduce a
  byte-identical `methods` block and `faith.npz`, and the *only* thing it would change is the
  representation of the `pairwise` faith test — which is a pure function of the already-persisted
  `faith.npz`. The recovery block on disk already carried the audit-added `spearman_vs_oracle`
  and the correct config provenance (0.35 / 5 seeds / 30 / 32).

## Decision

Extract the pairwise+verdict construction into shared `build_pairwise` / `compute_verdict`
helpers and expose a `python -m implementation.induction_discovery.run --refresh-stats` mode that
recomputes **only** the `pairwise` block and verdict from the persisted `summary.json` +
`faith.npz` (deterministic, pure-numpy, zero forward passes), then kill the slow re-run and use
`--refresh-stats` to regenerate the corrected artifact. The seed-level unit is recovered by
reshaping the persisted per-example faith array `(#seeds·#examples,)` → `(#seeds, #examples)` and
taking the per-seed mean — the same operation the auditor used to independently verify p=0.024.

## Alternatives considered

- **Let the full CPU re-run finish (~45–75 min).** Rejected: it burns ~1 h of compute to
  recompute byte-identical values under determinism, against an impatient "full speed" directive,
  for a cosmetic block-representation change. Reproducibility is preserved by the mode's docstring
  + §12 note asserting equivalence.
- **Hand-edit the JSON `pairwise` block.** Rejected: violates the "regenerate every number from a
  command" invariant (`sim-report-completeness`); a manual edit has no provenance and can drift
  from the code path that a reader would re-run.
- **Duplicate the pairwise/verdict expressions inside `refresh_stats`.** Rejected in favour of
  the shared-helper extraction so `main()` and the refresh path cannot diverge (a silent drift
  would be exactly the class of defect the audit just caught).

## Consequences

- Enables: sub-second regeneration of the significance block whenever the statistical unit or
  test changes, without redoing attribution — the reason `faith.npz` is persisted in the first
  place. `main()` and `refresh_stats()` share one definition of the block.
- Provenance nuance: the committed `summary.json`'s `pairwise` block was written by
  `--refresh-stats` on CPU over an MPS-produced `faith.npz`; stats are device-independent, and a
  clean `python -m …run` reproduces the identical block. Documented in report §12
  ("Compute provenance") and bug `2026-07-03-02` Fix.
- Forecloses nothing; the full `run.py` path is unchanged and remains the canonical from-scratch
  reproduce command.

## Refs

- Bug `bugs/2026-07-03-02-pseudoreplicated-faithfulness-pvalue.md` (the fix this decision
  regenerates the artifact for).
- Decision `decisions/2026-07-03-01-h15-node-granularity-standalone-report.md` (parent scoping).
- Code `implementation/induction_discovery/run.py` (`build_pairwise`, `compute_verdict`,
  `refresh_stats`, `--refresh-stats`); report `docs/h15-automated-discovery-study.md` §12.
- Field notes `field-notes/2026-07-03-h15-automated-discovery.md`; conversation log
  `prompts/2026-07-03-mac-handoff-orientation.md` Conversation 4.
