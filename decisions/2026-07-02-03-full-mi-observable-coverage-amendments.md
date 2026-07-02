---
id: 2026-07-02-03
title: Structure the full-MI-observable coverage amendments as hypotheses H10–H19 + §6 scope exclusions, anchored to already-acquired sources
status: accepted
date: 2026-07-02
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

The 2026-07-02 coverage audit (`reports/2026-07-02-mi-observable-coverage-audit.md`,
Workflow `mi-observable-coverage-audit`, 305 agents) found the tiny-transformer
induction plan covered ~20/146 MI observables — 63 in-scope gaps (12 amendment
bundles) and 63 legitimately out-of-scope. User: "apply all amendments." Two
choices the audit did not pre-decide: (1) how to fold 12 bundles into the plan's
hypothesis/phase structure; (2) whether the new bundles are source-gated (like H9)
or can be written now.

## Decision

Add 10 new pre-registered hypotheses **H10–H19** (causal attribution / patching +
validation metrics; layer-wise decode; composition census; representation-level;
self-repair; automated discovery; DAS/IIA; privileged basis; IOI promoted from
stretch; interpretability-illusion robustness) to §2, plus operational touchpoints in Phase-2 tooling/tests,
Phase-4/4b steps, §4 figures, §5 anchors, and §6 sub-studies (Bundles E/G/H/K/L)
+ a grokking metric-completion rider (Bundle I) + an explicit
out-of-scope-exclusions paragraph. Anchor every new external reference to the
**already-acquired** `download/` sources and the verified appendix-i sections
(§I.1–§I.9); do **not** source-gate them (unlike H9) — the papers are in-repo —
except the one genuinely-unacquired item (auto-interp, Bundle-K stretch), which
stays source-gated. Specific reported values are source-verified at execution per
citation-integrity.

## Alternatives considered

- **Fold all bundles into phase steps, no new hypotheses.** Rejected — the
  audit's items are testable claims; pre-registration as Quantitative hypotheses
  is the plan's own discipline (§2) and lets `sim-report-completeness` score
  PASS/FAIL per item.
- **Source-gate all new bundles like H9.** Rejected — a `download/` inventory
  showed ~every needed method paper is already acquired (ACDC, EAP, EAP-IG, AtP*,
  Hydra, self-repair, path-patching, DAS/boundless-DAS, probes+control-tasks,
  grokking progress measures, IOI, greater-than, copy-suppression, successor,
  interpretability illusions); gating would falsely block executable work. Only
  auto-interp is unacquired.
- **Split coverage into a follow-on plan.** Rejected — the observables belong to
  the same induction / GPT-2 study; scattering them loses the ground-truth
  cross-checks (e.g. automated discovery validated against the §A.9 manual
  circuit; DAS agreeing with the OV-copy circuit up to gauge).

## Consequences

- The plan now claims full MI-observable coverage with explicit scope exclusions;
  it grew 183→229 lines, lint-clean, hypotheses H1–H19 contiguous. Two adversarial verification passes (Workflows `mi-plan-amendment-verify` + `-reverify`) confirm **13/13 bundles concretely wired** (hypothesis or §6 sub-study + operational touchpoint).
- Enables the induction claim to be *validated* (patching + faithfulness /
  completeness / minimality + self-repair bounding the ablation deltas), not just
  structurally matched — hardening H3/H8.
- Adversarial verification via Workflow `mi-plan-amendment-verify` confirms each
  bundle is concretely wired (hypothesis + operational touchpoint), not
  name-dropped.
- Follow-up: execution-time `source-fetch` of the auto-interp reference; the study
  is still awaiting implementation approval. Tracked in
  `todos/2026-07-02-mi-plan-observable-coverage-gaps.md`.

## Refs

- Plan §2 (H10–H19), §3 Phases 2/4/4b, §4–§6.
- Report `reports/2026-07-02-mi-observable-coverage-audit.md`.
- `todos/2026-07-02-mi-plan-observable-coverage-gaps.md`; conversation log
  `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 62–63.
