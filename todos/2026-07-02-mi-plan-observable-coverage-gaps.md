---
slug: mi-plan-observable-coverage-gaps
date_filed: 2026-07-02
status: closed
---

# Close the MI-observable coverage gaps in the tiny-transformer induction plan

## Context

A multi-agent coverage audit (`reports/2026-07-02-mi-observable-coverage-audit.md`,
Workflow `mi-observable-coverage-audit`, 305 agents) checked
`plans/2026-06-30-tiny-transformer-induction-study.md` against a 146-observable
rubric of *all* MI observables (built from `surveys/mechanistic-interpretability/`
+ `appendix-i`). Verdict: **20 covered / 21 partial / 105 missing**; of the
non-covered, **63 in-scope gaps** (collapse to 12 amendment bundles) and **63
legitimately out-of-scope** (owned by the SAE-frontier study, the steering/editing
inventory, superposition toy-models). The plan is a strong weight-space QK/OV +
induction + grokking microscope but is missing the activation/path-patching +
circuit-metric apparatus, the decode-lens family, representation probing/steering,
head-zoo/IOI completion, and automated circuit discovery. Amendments are NOT yet
landed (this was a read-only review; the plan is still awaiting approval).

## What is left

Apply the 12 amendment bundles (report §3 / §5), priority order:

1. **A — bidirectional activation patching + effect metrics** (clean/corrupt
   pairs, IE/TE, logit-diff, causal-tracing heatmap). Highest leverage.
2. **B — circuit-validation metrics** (faithfulness / completeness / minimality
   + causal scrubbing / resample ablation / edge+path patching).
3. **C — decode lens + full DLA** (logit lens, tuned lens, residual-decomposition
   check, per-component DLA, direct-path + QK bigram baselines).
4. **F — self-repair / Hydra check** (hardens H8's single-ablation claims) +
   head-zoo scoring (duplicate-token / copy-suppression / successor) + promote
   IOI from stretch to committed + cross-corpus illusion check.
5. **D** Q/V-composition scores · **E** probing/selectivity/steering/directional
   ablation · **G** automated discovery (ACDC/EAP/EAP-IG/AtP) · **I** grokking
   metric completion (restricted/excluded loss, 3-phase, angle-addition,
   matched-filter).
6. **H** DAS/IIA · **J** privileged-basis + MLP-neuron · **K** max-activating /
   auto-interp · **L** greater-than circuit (stretch).
7. **Scope-exclusion paragraph** in plan §6/§7 naming the OOS families (SAE /
   dictionary → SAE-frontier study; steering/editing → steering inventory;
   superposition toy-models → appendix-B) so absence is explicit, not silent.

**Source-gate (hard):** bundles E, F, G, H, and K's auto-interp need a
`source-fetch` pass before any external anchor is written (citation-integrity),
mirroring the H9 gate — AtP*/EAP-IG/ACDC/IOI/copy-suppression/self-repair refs.

## Acceptance

The plan carries hypotheses/phase-steps/metrics/figures for every in-scope
bundle (A–L) OR an explicit scope-exclusion note for anything left out; a re-run
of the coverage audit reports 0 unaddressed in-scope gaps; all new external
anchors traced to acquired sources.

## Refs

- Report: `reports/2026-07-02-mi-observable-coverage-audit.md`.
- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md`.
- Related handoff todo: `todos/2026-07-01-mechinterp-ris-handoff.md` (EAP-IG is a
  named candidate — bundle G).
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 62.

## Resolution

**Resolution (2026-07-02).** All 12 amendment bundles applied to the plan (user: "apply all amendments"): added pre-registered hypotheses **H10–H19** to §2, operational touchpoints in Phase-2 tooling/tests, Phase-4/4b steps, §4 figures, and §5 anchors; §6 sub-studies (Bundles E/G/H/K/L); a grokking metric-completion rider (Bundle I); and an explicit out-of-scope-exclusions paragraph. Plan grew 183→229 lines, lint-clean, H1–H19 contiguous. Adversarially verified in two passes (Workflows `mi-plan-amendment-verify` → 10/13, then `-reverify` after fixing the F / L / SCOPE gaps → **13/13 bundles concretely wired**: hypothesis or §6 sub-study + operational touchpoint). New external anchors point at already-acquired `download/` sources + verified appendix-i §I.x sections; not source-gated (unlike H9) except the one unacquired auto-interp paper (Bundle-K stretch). Decision `2026-07-02-03`. Residuals (study-execution, not plan-coverage): source-fetch the auto-interp reference before executing Bundle-K auto-interp, and source-verify specific reported values at execution per citation-integrity. The plan itself remains awaiting implementation approval.
