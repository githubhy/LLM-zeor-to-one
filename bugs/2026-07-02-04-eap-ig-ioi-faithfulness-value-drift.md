---
id: 2026-07-02-04
title: MI-RIS handoff todo mis-stated EAP-IG's IOI faithfulness result (memory drift vs Hanna et al. 2024)
severity: med
status: fixed
date: 2026-07-02
component: todos / handoff-provenance / citation-integrity
plan: docs/eap-ig-faithfulness-implementation-study.md
---

## Symptom
`todos/2026-07-01-mechinterp-ris-handoff.md` (candidate 2) and the survey §15.2 handoff framed
the EAP-IG study hypothesis as: *"EAP-IG lifts IOI circuit faithfulness from ~0% toward the
exact-patching curve (Hanna et al. [41])."* Taken at face value this would have set the A2 study's
pre-registered H1 to "EAP ≈ 0 on IOI, EAP-IG repairs it" — a Quantitative hypothesis with a wrong
predicted magnitude and wrong task attribution.

## Root cause
Value recalled from memory, not read from the source (the exact failure mode
`.claude/rules/citation-integrity.md` guards against). Reading the acquired PDF
(`download/hanna-eap-ig-faithfulness-2024.pdf`, COLM 2024, §4.3 + Fig 3) shows:
- **IOI**: EAP *and* EAP-IG circuits **both plateau at ~0.6** normalized faithfulness, *both* below
  activation-patching (which reaches >0.8). On IOI the EAP→EAP-IG gap is small — EAP-IG ≈ EAP.
- The "**EAP finds a completely unfaithful circuit ... EAP yields circuits with many parentless
  heads pruned to nothing**" catastrophe — the ~0% story — is **SVA (subject-verb agreement)**, not
  IOI (§4.3). The essential input-embed→MLP0 edge is scored by EAP-IG but missed by EAP.
- The EAP-IG advantage is **large on SVA and Capital-Country (≥0.2)**, **~0.1 on Greater-Than**, and
  **≈0 on IOI**.

So the handoff conflated SVA's dramatic EAP failure with IOI, and mis-stated the IOI magnitude.

## Fix
- Corrected the handoff todo's candidate-2 framing to the paper-accurate spectrum (SVA is the
  trademark EAP failure; IOI shows EAP-IG ≈ EAP at ~0.6; Greater-Than ~0.1 gap).
- The A2 study (`docs/eap-ig-faithfulness-implementation-study.md`) pre-registers hypotheses matching
  the actual paper: IOI H1 = *both plateau ~0.6, gap small* (a reproduction success is EAP-IG ≈ EAP
  on IOI, **not** a large lift); SVA H3 = EAP catastrophic-until-large-n, repaired by EAP-IG; the
  headline discriminators are SVA + Greater-Than, not IOI.
- Commit SHA: (this branch `study/ris-program-2026-07-02`).

## Regression test
none — provenance/authoring defect, not code. Guarded going forward by pre-registering the A2
hypotheses against values read from the acquired PDF (citation-integrity), and by the study's
theory-as-predictor overlay (`sim-report-completeness`) which would flag a residual against the
paper's published curve.

## Refs
- Source: `download/hanna-eap-ig-faithfulness-2024.pdf` §3 (Eq 1, 3), §4.2 (faithfulness metric),
  §4.3 (Fig 3 results), §4.4 (Fig 4 correlation).
- Rule: `.claude/rules/citation-integrity.md`. Related decision `2026-07-02-04`.
- Handoff: `todos/2026-07-01-mechinterp-ris-handoff.md`.
