---
slug: appendix-a-crosslink-candidates
date_filed: 2026-06-30
status: open
---

# appendix-a — pre-existing cross-link candidates surfaced during the §A.21 fold

## Context

While folding the "what are the logits" answer into §A.21 (the `full`
survey-explainer-fold), the Stop/`crosslink.py check --changed` gate flagged
three advisory, low-cosine cross-link candidates. They are **not** from the new
§A.21 (which already links §A.1/§A.9/§A.11/§A.20) — they are pre-existing gaps in
§A.5 and §A.13, surfaced only because the whole `appendix-a` file counts as
"changed." Left out of scope for the logits fold; tracked here per the
cross-linking sign-off rule.

## What is left

Evaluate (keep/skip) and, if kept, insert via `/cross-link` with the correct
directional `secxref` syntax:

- `appendix-a §A.5` → `appendix-b §B.6` (cosine 0.242) — attention-as-kernel-regression ↔ the kernel-regression-family appendix; the most plausible of the three.
- `appendix-a §A.5` → `appendix-b §B.7` (cosine 0.131).
- `appendix-a §A.13` → `appendix-e §E.5` (cosine 0.124) — concrete-dimensions ↔ modern-dense anatomy.

## Acceptance

Each candidate is judged keep/skip via `/cross-link`; kept links are applied
with the `secxref` cross-file form and validate-refs stays clean. (These are
advisory `warn`-severity, below any block-score, so they do not gate a push.)

## Refs

- Detector: `crosslink.py check surveys/llms-for-coding --changed`
- Rule: `.claude/rules/cross-linking.md` (Tier-2 on-demand insertion)
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 31
