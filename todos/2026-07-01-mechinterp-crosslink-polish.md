---
slug: mechinterp-crosslink-polish
date_filed: 2026-07-01
status: closed
---

**Resolution (2026-07-01).** Ran `/cross-link` on the survey: extract (79 sections) → candidates
(19 at cosine ≥ 0.15) → 1-batch Sonnet judge → apply. Judge kept **13/19**, rejecting the 6
redundant/backwards appendix↔main pairs; **12 landed** (1 dropped on an anchor-not-found, the
weakest E.1→Q.5 derivation→FAQ link). New links: main-section→Appendix-Q reader-Q&A back-links
(§3.1→Q.2, §7.4→Q.6, §12.2→Q.3, §10.1→Q.8, §8.3→Q.4) + assertion→derivation forward links
(§7.5→E.3, §9.1→A.3, §2.1→A.4, §2.4→B.2, §5.1→C.1, §10.3→D.3, §Q.4→C.3). Survey now carries 230
valid cross-links; `/check-survey` green. Residual 14 advisory candidates (cosine ≥ 0.15) triaged
as redundant with existing forward-links / low-value — not deferred work.

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
