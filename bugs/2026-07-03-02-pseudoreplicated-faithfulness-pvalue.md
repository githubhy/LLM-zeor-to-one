---
id: 2026-07-03-02
title: Faithfulness significance pseudo-replicated (pooled per-example p=5e-29 instead of seed-level p=0.02)
severity: med
status: fixed
date: 2026-07-03
component: implementation/induction_discovery/run.py
plan: plans/2026-07-03-h15-automated-discovery.md
---

## Symptom

The H15 baseline reported "EAP-IG more faithful than EAP (Δ+0.109, p=5.3e-29)". The p-value
overstates significance by ~27 orders of magnitude: the honest seed-level test gives p=0.024.
Surfaced by the pre-sign-off adversarial audit (stats + confound lenses, both CONFIRMED).

## Root cause

`run.py` fed the faithfulness paired test the **pooled per-example** faithfulness values
(`faith_pool[m][REF]`, length 160 = 5 seeds × 32 examples) to `ttest_rel` as if they were 160
independent pairs. But the top-20 circuit is computed **once per seed** (`scores[m]` per seed),
so all 32 examples within a seed share the *same* circuit — the independent unit of analysis is
the seed, not the example. Effective n=5, not 160. Recomputed at the seed level (paired t over
the 5 per-seed mean faithfulness values): t=3.52, **p=0.024**, mean_diff=0.109, per-seed diffs
[0.155, 0.155, 0.000, 0.079, 0.156] — one seed is a near-tie. The two *other* pairwise tests
(AUROC, corr-to-exact) were already correctly at the seed level, so the error was inconsistent.

The PASS verdict is unaffected: the gate is `faith_gap_p < 0.05`, and 0.024 < 0.05 still clears
it — but the reported significance was wrong.

## Fix

`run.py`: track per-seed mean faithfulness at the operating point (`faith_ref_seed`), add a
seed-level paired test `faith_ref_seedlevel__eap_ig_vs_eap`, and **gate the verdict on the
seed-level p**. The pooled per-example test is retained as `faith_ref_pooled__…` but explicitly
labeled an effect-size descriptor (d_z), not a significance claim. Report (`docs/h15-…` §0/§6)
now headlines the seed-level p=0.024 and discloses the near-tie seed. The `build_pairwise` /
`compute_verdict` logic was extracted into shared helpers and exposed as a new
`run.py --refresh-stats` mode that recomputes **only** the pairwise block + verdict from the
persisted `faith.npz` (deterministic, no forward passes); the corrected artifact was
regenerated this way rather than by a ~1 h full re-run that would produce byte-identical values
(decision `2026-07-04-01`). Verified against the artifact: seed-level p=0.0244, mean_diff=+0.109,
per-seed diffs [0.155, 0.155, 0.000, 0.079, 0.156]; pooled p=5.27e-29 (descriptor).

## Regression test

none added — the fix is a choice-of-statistical-unit correction, verified by direct
recomputation from the persisted `artifacts/induction-discovery/baseline/faith.npz` (seed-level
p=0.024 reproduced independently by the auditor and by the fix). A generic "cluster-robust test"
utility is out of scope for this study.

## Refs

- Report `docs/h15-automated-discovery-study.md` §0/§6 (seed-level p headlined).
- Audit workflow (stats + confound lenses); field notes `field-notes/2026-07-03-h15-automated-discovery.md`.
- Sibling `bugs/2026-07-03-01-mps-cost-measurement-artifact.md` (same study, cost measurement).
