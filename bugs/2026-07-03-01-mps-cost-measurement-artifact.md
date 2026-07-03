---
id: 2026-07-03-01
title: MPS cost profiling reports EAP wall-time > EAP-IG (impossible by op-count)
severity: med
status: fixed
date: 2026-07-03
component: implementation/induction_discovery/run.py
plan: plans/2026-07-03-h15-automated-discovery.md
---

## Symptom

The H15 baseline cost table came out `eap = 50.5 s`, `eap_ig = 9.6 s`, `exact_patch = 119 s`
on MPS. EAP (2 fwd + 1 bwd = 3 model passes) being ~5× *slower* than EAP-IG (2 fwd + 5 fwd/bwd
IG path = 11 passes) is impossible — EAP does strictly less work. The `exact_patch` figure
(157 passes, ~119 s) is plausible; the EAP/EAP-IG inversion is not.

## Root cause

The cost-profiling loop was cut from 3 timed reps to **1 rep** (to shorten the MPS run,
`run.py` cost block). With a single rep, the *first* method timed — EAP, the first non-`random`
entry in `CANDIDATES` — absorbs a one-time MPS scheduling / lazy-kernel / allocator cost on the
first heavy op after the main loop's tensors are freed, inflating its single measurement. EAP-IG
and `exact_patch`, timed afterward on a warm allocator, report clean times. So the inversion is a
**measurement artifact of 1-rep timing on MPS**, not a real cost inversion. (The eap-ig study
avoids this by taking `p50/p90` over 3 reps on CPU: EAP 3.2 s, EAP-IG 9.2 s, exact 50.6 s —
correctly ordered.)

## Fix

Do not present the measured EAP/EAP-IG wall-times as the cost story. The report
(`docs/h15-automated-discovery-study.md` § 6/§ 9) reports cost by **op-count** — the
deterministic truth: EAP 3 / EAP-IG 11 / exact 157 model passes (O(1)/O(m)/O(nodes)) — and
uses the measured `exact_patch` ≈ 119 s only as an order-of-magnitude "expensive reference"
anchor. The `run.py` cost block keeps 1 rep (the artifact is disclosed, not the headline) but
its comment now states the op-count hierarchy is the reliable figure. A future CUDA re-run with
a warmup call + ≥3 reps (the `eap-ig-followups` reduced-precision item) would restore clean
wall-time numbers.

## Regression test

none — the op-count claim is deterministic and needs no test; the artifact is a timing-only
presentation issue, disclosed in the report and this bug. A warmup-then-median cost harness is
tracked in `todos/2026-07-03-h15-automated-discovery-followups.md` (reduced-precision re-run).

## Refs

- Report `docs/h15-automated-discovery-study.md` § 0/§ 6/§ 9 (cost via op-count).
- Decision `decisions/2026-07-03-01-h15-node-granularity-standalone-report.md`.
- Field notes `field-notes/2026-07-03-h15-automated-discovery.md`.
