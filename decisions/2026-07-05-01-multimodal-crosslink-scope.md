---
id: 2026-07-05-01
title: "Multimodal cross-link polish via explicit-path /cross-link, NOT by extending the shared crosslink-scope"
status: accepted
date: 2026-07-05
plan: (infra/viewer cleanup — backlog item #3)
---

## Context

Closing `todos/2026-06-28-multimodal-llms-crosslink-polish`. The todo's note said
the pass "needs scope-extension" — i.e. add `surveys/multimodal-llms` to
`.claude/crosslink-scope` so the gate would detect its gaps. On inspection,
`.claude/crosslink-scope` is documented as **ONE corpus group** ("Multi-group
support is a future extension"; "Keeping unrelated surveys out avoids cross-survey
false-positive candidates"). Adding `surveys/multimodal-llms` to the same group as
the existing `surveys/llms-for-coding` would make the gate compute TF-IDF
candidates *across* the two unrelated surveys — manufacturing exactly the
cross-survey false positives the single-group design warns against.

## Decision

Run the `/cross-link` pipeline scoped to the **explicit path**
`surveys/multimodal-llms` (a one-shot polish), and **do not** modify
`.claude/crosslink-scope`. `crosslink.py extract|candidates|apply` accept an
explicit corpus path and scope intra-survey correctly, so the shared gate config
is untouched. Of 30 pre-filtered candidates, a 2-batch Sonnet judge kept 19; 18
applied cleanly (1 anchor-not-found); after a quality pass I removed 1 orphaned
stacked link and moved 2 links out of emphasis spans → **17 links landed**. The
residual 18 gaps the check still reports are all ≤ 0.196 cosine (judge-rejected
topical overlap) or reverse-direction duplicates of applied links → triaged
low-value, satisfying the todo acceptance.

## Alternatives considered

- **Add `surveys/multimodal-llms` to `.claude/crosslink-scope`.** Rejected: single
  group → cross-survey false-positive candidates on every push; the gate would
  advisory-spam unrelated llms-for-coding↔multimodal pairs. Correct ongoing-gate
  coverage needs multi-group support first (deferred).
- **Hand-place only the todo's named forward-refs, skip the tool.** Rejected: the
  deterministic `apply` (syntax + dedup + idempotency) is the whole value of the
  tool; hand-authoring secxref syntax re-introduces the error class the tool
  removes. Kept the tool; hand-tuned only the 3 awkward placements it produced.
- **Keep all 18 automated links as-is.** Rejected: 2 landed inside emphasis spans
  (`*many images (§F.3)*`) and 1 was an orphan stacked parenthetical — below the
  survey's prose bar. Cleaned the 3; kept the 15 clean ones.

## Consequences

- The multimodal-llms survey gains 17 high-value cross-links (155→172 total),
  bidirectionally navigable; body→appendix forward-refs the todo named (§6.3→E.3,
  §4.13→E.2, §3.4→C.3, §7.1/7.2→F.2/F.3, §4.11→D.1) are now clickable.
- The pre-push gate still scans only `surveys/llms-for-coding` — multimodal-llms is
  NOT under ongoing gate maintenance. Ongoing coverage awaits multi-group scope
  support; not filed as a new todo (the survey is complete and densely linked — a
  one-shot polish is the right disposition, per the todo's "polish, not correctness
  gap" framing).
- Judge cost: 2 Sonnet agents, ~267K tokens (the agents opened source files to
  verify anchors — pricier than the cheap-snippet design intends, acceptable for a
  one-shot). Noted for future runs: constrain the judge to snippets only.

## Refs

- `todos/2026-06-28-multimodal-llms-crosslink-polish.md` (closed by this)
- `.claude/rules/cross-linking.md` (Tier-2 on-demand apply; single-group scope)
- `.claude/skills/cross-link/SKILL.md`; `viewer/tools/crosslink.py`
- conversation log `prompts/2026-07-03-mac-handoff-orientation.md`
