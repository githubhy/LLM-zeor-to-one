---
slug: mechinterp-ris-handoff
date_filed: 2026-07-01
status: closed
---

**Update 2026-07-02.** **ALL THREE candidates now have studies** (offline GPT-2-small scope,
decision 2026-07-02-04):
- Candidate 1 (SAE frontier) **COMPLETE** → `sae-frontier` (G1–G4 PASS; TopK recommended) +
  Track-C extension `sae-frontier-ext` (BatchTopK/Matryoshka red-team refuted).
- Candidate 2 (EAP-IG faithfulness) **COMPLETE** → `eap-ig-faithfulness`
  (`docs/eap-ig-faithfulness-implementation-study.md`; G1/G2/G3/G4/REPORT PASS; EAP-IG > EAP
  +0.224 p=3.6e-34, ρ=0.92 vs 0.46). Followups `todos/2026-07-02-eap-ig-followups.md`; the earlier
  "IOI ~0%" framing was a memory drift → bug 2026-07-02-04.
- Candidate 3 (steering head-to-head) **COMPLETE** → `steering-headtohead`
  (`docs/steering-headtohead-study.md`; G1 PASS; SAE-clamp worst reproduces AxBench, diff-in-means >
  prompting flipped — metric/model-dependent). Followups `todos/2026-07-02-steering-followups.md`.

This handoff is now **closed** (status below → all candidates addressed).

# Mechanistic-interpretability survey → reference-implementation-study handoff

## Context
The `mechanistic-interpretability` survey (branch `survey/mechanistic-interpretability`,
§15.2 open-problems-and-roadmap) names three study-ready reproduction candidates, each with
a baseline-to-beat and a prior-reported predicted margin. Filed here per the Todo Capture /
deferred-tracking rule so the handoff is durably tracked, not just named in prose.

## What is left
Run a `reference-implementation-study` (or `method-eval` viability gate first) on one or more:

1. **SAE architecture on the fidelity–sparsity frontier** — Gemma 2 2B, one site (via Gemma
   Scope [ref 65]). Baseline: ReLU SAE at matched L0. Hypothesis (Quantitative): JumpReLU/TopK
   Pareto-dominate ReLU; loss-recovered gap grows with dictionary width (Gao [11], Rajamanoharan
   [12]). Settles: reproduces the L1-shrinkage-fix claim on an open suite.
2. **Attribution vs. exact patching faithfulness** — IOI + Greater-Than + SVA on GPT-2 small.
   Baseline: plain EAP. Hypothesis (paper-accurate, read from `download/hanna-eap-ig-faithfulness-2024.pdf`
   §4.3, Fig 3 — the earlier "EAP-IG lifts IOI from ~0%" framing was a memory drift, see
   bug `2026-07-02-04`): the EAP→EAP-IG faithfulness gap is **large on SVA** (EAP finds a
   completely-unfaithful, pruned-to-nothing circuit until n≈1000; EAP-IG repairs it via the essential
   embed→MLP0 edge) and Capital-Country (≥0.2), **~0.1 on Greater-Than**, and **≈0 on IOI** (both EAP
   and EAP-IG plateau ~0.6, below activation-patching's >0.8). Activation-patching is the ground-truth
   oracle both scores approximate. Settles: quantifies the first-order linearization error, the IG fix,
   and its task-dependence.
3. **Steering head-to-head** — prompting vs. difference-in-means vs. SAE-feature clamp on Gemma 2
   2B/9B. Baseline: prompting. Hypothesis: prompting ≥ diff-in-means ≥ naive SAE steering at
   matched coherence (AxBench [66]). Settles: replicates the SAE-debate result on a fixed harness.

## Acceptance
A Phase-6 reproduction report under `reports/` (per `sim-report-completeness`) with: pre-registered
Quantitative hypotheses, the analytic/prior-reported prediction overlaid on measured points with
residuals, CIs on every result, and a reconciled verdict for at least one candidate. Downstream
gaps → new `todos/`.

## Refs
- Survey: `surveys/mechanistic-interpretability/open-problems-and-roadmap.md` §15.2 (+ §12.2 debate).
- Skills: `reference-implementation-study`, `method-eval`, `sim-audit`.
- Sources (in `download/`): gao-topk-saes-2024, rajamanoharan-jumprelu-saes-2024,
  hanna-eap-ig-faithfulness-2024, wu-axbench-2025, lieberum-gemma-scope-2024.
