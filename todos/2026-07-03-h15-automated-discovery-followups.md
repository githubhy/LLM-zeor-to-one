---
slug: h15-automated-discovery-followups
date_filed: 2026-07-03
status: open
---

# H15 automated-discovery — follow-on work

## Context

The H15 automated-circuit-discovery sub-study (`docs/h15-automated-discovery-study.md`,
`implementation/induction_discovery/`) closed H15 at the **GPT-2-small rung, node
granularity**: EAP / EAP-IG recover the induction-head set (Olsson prefix-matching oracle)
and are rank-consistent with exact patching. Decision `2026-07-03-01` scoped it to node-level
head recovery with a computed oracle; several pre-registered facets were deliberately left out
of this pass and are tracked here.

## What is left

- **Edge-level attribution (the literal §A.9 K-*edge*).** The reused `eap_ig` engine is
  node-level only — it has no per-(source,dest) edge score. Recovering the prev-token→induction
  *composition edge* (not just the two head *nodes*) needs a new edge-scoring layer. This is the
  gap between "recovered the induction heads" and "recovered the K-edge up to gauge".
- **ACDC and AtP / AtP\*.** The plan named ACDC (KL-threshold pruning) and attribution patching
  with the QK-recompute correction (AtP\*); this pass ran only EAP and EAP-IG. Add them for the
  full "automated discovery" method set and a 4-way recovery comparison.
- **Toy-rung H15.** Run the same recovery protocol on the trained toy 2-layer model
  (`artifacts/induction-tiny/`) — expected to localize *weakly* (the study's §10 distributed-circuit
  finding), which is itself the informative contrast with the sharp GPT-2 rung.
- **Reduced-precision attribution compute.** Only float32 was run; fp16/bf16 forward+backward
  attribution drift (the `eap-ig-followups` item) applies here too on a CUDA host.
- **Gemma-2 / larger substrate.** Whether the recovery story holds where induction is more
  distributed (mirrors `sae-frontier-followups` / `steering-followups` Gemma asks).
- **Fully-jittered baseline (design out the positional confound, not just control it).** The
  §10 robustness control jitters the *task* offset but the Olsson oracle still uses a fixed
  period-25 repeat; promote the jittered task to the primary baseline and add a variable-period
  oracle so neither side carries the fixed-offset structure (audit-surfaced, `bugs/` n/a — it
  is a robustness upgrade, not a defect).
- **Cluster-robust / hierarchical faithfulness test.** The seed-level paired test (n=5) is the
  honest unit but low-powered; a mixed-effects model over (seed, example) would use the data
  more efficiently without pseudo-replication (`bugs/2026-07-03-02`).

## Acceptance

An edge-level + ACDC/AtP\* re-run reproduces the prev-token→induction composition edge (not just
the head nodes) up to gauge, and the toy-rung run documents the weak-vs-sharp localization
contrast; or a documented reason each cannot be closed at commodity scale.

## Refs

- Study `docs/h15-automated-discovery-study.md`; code `implementation/induction_discovery/`.
- Decision `decisions/2026-07-03-01-h15-node-granularity-standalone-report.md`.
- Parent `docs/tiny-transformer-induction-study.md` §11; plan `plans/2026-06-30-tiny-transformer-induction-study.md:37,151`.
- Sibling `todos/2026-07-02-eap-ig-followups.md` (edge-level graph + greedy search there too).
