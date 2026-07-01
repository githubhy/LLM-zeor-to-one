---
slug: mechinterp-ris-handoff
date_filed: 2026-07-01
status: in-progress
---

**Update 2026-07-02.** Candidate 1 (SAE fidelity–sparsity frontier) **COMPLETE** via
`reference-implementation-study` → study `sae-frontier` (`docs/sae-frontier-implementation-study.md`;
gates G1–G4 PASS; H1–H4 confirmed; **TopK recommended**). Scoped to synthetic-oracle + GPT-2-small
(decision 2026-07-02-01); Gemma-scale port + more in `todos/2026-07-02-sae-frontier-followups.md`.
Candidates 2 (EAP-IG faithfulness) and 3 (steering head-to-head) remain open.

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
2. **Attribution vs. exact patching faithfulness** — IOI + Greater-Than on GPT-2 small. Baseline:
   plain EAP. Hypothesis: EAP-IG lifts IOI circuit faithfulness from ~0% toward the exact-patching
   curve (Hanna et al. [41]). Settles: quantifies the first-order linearization error and the IG fix.
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
