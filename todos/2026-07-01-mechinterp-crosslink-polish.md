---
slug: mechinterp-crosslink-polish
date_filed: 2026-07-01
status: open
---

# Mechanistic-interpretability survey — cross-link polish pass

## Context
The `mechanistic-interpretability` survey was authored with dense deliberate cross-linking
(218 valid intra-survey `secxref`/`secref` links; `/check-survey` green). A sign-off
`crosslink.py check` at cosine ≥ 0.15 (advisory, non-blocking; the survey is not yet in
`.claude/crosslink-scope`) surfaced 19 additional candidate links — mostly section↔appendix
and main-section→Q&A back-links. Deferred to avoid churning a green gate; these are
enrichment, not correctness. Mirrors the `multimodal-llms-crosslink-polish` precedent.

## What is left
Run `/cross-link` scoped to `surveys/mechanistic-interpretability` (or `crosslink.py
candidates|apply`) and land the high-value subset. The clearest wins (main narrative → anchored
Q&A):
- §3.1 → Q.2 (decodable ≠ used); §7.4 → Q.6 (editing ≠ storage); §10.1 → Q.8 (faithfulness
  non-robustness); §12.2 → Q.3 (why SAEs "failed"); §8.3 → Q.4 (why freeze attention).
- Section → derivation-appendix forward links not already present (e.g. §7.5 → E.3, §5.1 → C.1).
Skip the reverse-direction duplicates already covered by the "Derivations for §X" appendix headers.
Optionally add `surveys/mechanistic-interpretability` to `.claude/crosslink-scope` so the gate
tracks it going forward.

## Acceptance
`crosslink.py check` high-value gaps cleared or explicitly triaged; no link-spam (apply is
idempotent, one link per target per file); `/check-survey` still green.

## Refs
- Survey dir: `surveys/mechanistic-interpretability/` (order.json, 24 files).
- Rule: `.claude/rules/cross-linking.md`; skill: `.claude/skills/cross-link/SKILL.md`.
- Candidate list: `crosslink.py check surveys/mechanistic-interpretability --min-score 0.15`.
