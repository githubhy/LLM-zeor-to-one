---
slug: multimodal-llms-crosslink-polish
date_filed: 2026-06-28
status: closed
---

**Resolution.** 2026-07-05. Ran the `/cross-link` pipeline scoped to the explicit
path `surveys/multimodal-llms` (NOT by extending `.claude/crosslink-scope` — single
group would create cross-survey false positives; see decision `2026-07-05-01`). 30
pre-filtered candidates → 2-batch Sonnet judge kept 19 → 18 applied (1
anchor-not-found) → **17 landed** after a quality pass (removed 1 orphan stacked
link, moved 2 links out of emphasis spans). The named body→appendix forward-refs
are now clickable (§6.3→E.3, §4.13→E.2, §3.4→C.3, §7.1/7.2→F.2/F.3, §4.11→D.1);
155→172 total links; validate-refs 0 errors, lint 0/0 across all 7 edited files.
Residual `crosslink.py check` candidates are all ≤ 0.196 (judge-rejected topical
overlap + reverse-direction duplicates of applied links) → triaged low-value per
the acceptance. Ongoing gate coverage for multimodal-llms is left for multi-group
scope support (not re-filed — survey is complete and densely linked).

# Multimodal-LLMs survey — cross-link polish pass

## Context
The `surveys/multimodal-llms/` survey was authored with dense inline cross-linking
(155 `secxref` cross-file links at sign-off — every section forward/back-references its
related sections). At Phase-5 sign-off, `crosslink.py check surveys/multimodal-llms`
reported a set of additional candidate links, all **low cosine (≤ 0.187)**. The highest-value
of these are body→appendix *forward* references that were written as prose ("Appendix C/D/E/F")
because the appendix section anchors did not exist yet when the body sections were authored;
the reverse direction (appendix→body) is already clickable `secxref`. The survey is therefore
bidirectionally navigable; this is a polish pass, not a correctness gap.

## What is left
Run `/cross-link surveys/multimodal-llms` (Tier-2 judged apply) to clear the reported
candidates, or manually convert the body→appendix prose forward-references to clickable
`secxref` (e.g. §4.5 "Appendix C", §4.11/§6.1 "Appendix D", §4.12/§4.13 "Appendix E",
§7 "Appendix F"). The full candidate list is reproducible with
`python3 viewer/tools/crosslink.py check surveys/multimodal-llms`.

## Acceptance
`crosslink.py check surveys/multimodal-llms` reports no candidates above the high-value
threshold, or the remaining ones are triaged as genuinely low-value in a follow-up note.

## Refs
- `.claude/rules/cross-linking.md` (Tier-2 on-demand apply; the "file a todo" sign-off allowance)
- survey sign-off commit series (§0–§13 + appendices A–F/Q)
- `prompts/2026-06-28-multimodal-llms-survey.md`
