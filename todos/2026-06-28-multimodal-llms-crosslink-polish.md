---
slug: multimodal-llms-crosslink-polish
date_filed: 2026-06-28
status: open
---

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
