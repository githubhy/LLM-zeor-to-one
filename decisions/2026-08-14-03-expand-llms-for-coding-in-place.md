---
id: 2026-08-14-03
title: Run max-mode deep-research-survey as an in-place expansion of llms-for-coding, with depth concentrated on the code-specific spine
status: accepted
date: 2026-08-14
---

## Context

`/deep-research-survey max mode on Large Language Models for Code: From Codex to Agentic
Software Engineering` was invoked. The requested title is **verbatim the H1 of an existing
survey**, `surveys/llms-for-coding/index.md`, so the invocation is ambiguous between
"produce a new survey" and "run the workflow over the one that exists."

Measurement at commit `1d8f017` decided it:

| Layer | Words | Equations |
|---|---|---|
| Body, 16 sections excluding section 3 | ~11,900 | **0** |
| Appendices A–I | 379 KB | hundreds |

The body is well-cited prose carrying essentially no mathematics; the appendix stack is deep
but derives the *general* transformer, not code. Against the Survey Rules'
"first-principles derivation for every method included," the body fails. Separately, the
section the title advertises — agentic software engineering — was the thinnest in the
document (795 words) and its frontier evidence was 2024-era, in a survey being run on
2026-08-14.

## Decision

Expand in place, and concentrate the max-mode depth budget on the **code-specific and
agentic spine** rather than spreading it evenly: seven `headline` sections, six
`load-bearing`, five `supporting`, with the new code-specific mathematics in a dedicated
**Appendix J** that the body cross-references.

The user confirmed all three axes at the P0-3 gate (depth allocation, evidence-refresh
scope, derivation placement) before any evidence budget was spent.

## Alternatives considered

- **Create a new survey directory.** Rejected outright. It would duplicate the title, split
  `references.md`, strand the 87 already-acquired sources, and trip the crosslink
  coverage/reachability gates. The survey exists; the question was only how to improve it.
- **Even depth across all 16 body sections.** Rejected on R-GOV's own grounds: depth is
  scored as a coverage fraction over load-bearing items, never prose volume, and spreading
  the budget evenly is the documented "added length, not judged quality" failure. A tight
  survey that fully treats its headline methods must score above a bloated one that
  half-treats everything.
- **Agentic + evaluation only.** Rejected as too narrow — it would have left the training
  half of the survey (FIM, RLVR, test-time compute) with the same zero-equation problem that
  motivated the run.
- **Inline derivations in each body section.** Rejected: body files would pass the wide-mode
  200 KB split threshold and the prose spine would be broken up by long algebra. The repo's
  existing surveys already converged on a dedicated derivations appendix.
- **Reporting 2026 SWE-bench leaderboard figures.** Rejected on evidence quality. Two
  independent search passes returned figures disagreeing with each other for the *same*
  leaderboard, and the authoritative pages render their tables in JavaScript. The survey
  states the measurement problem instead — including that at least three denominators
  circulate for "SWE-bench Verified" — which is a more durable contribution than a number
  that would be stale within a month. Tracked in `todos/2026-08-14-llms-for-coding-followups.md`.
- **Reporting the multi-agent coding results.** Rejected. Every ablation located was produced
  by the team proposing the method, which is exactly the baseline-scrutiny deficit
  `sim-report-completeness`'s `[opt:SIM-BASELINE]` names; one system reports two mutually
  inconsistent figures for its own resolve rate. Section 12.7 states the question is open
  rather than reporting numbers that a handicapped control would inflate.

## Consequences

- **Enables** the body to carry mathematics for the first time: Appendix J derives the
  pass@k estimator, the FIM permutation argument, GRPO's baseline lemma, and the
  sample-and-select scaling law, each cross-linked from the section that depends on it.
- **Surfaced a high-severity citation error** in pre-existing content (`bugs/2026-08-14-01`):
  a two-column results table read as a before/after pair, with two of four numbers appearing
  nowhere in the source. Found by accident, which is the finding — it means the pre-existing
  body's ~180 citation markers have never been audited. A `citation-audit` pass is now the
  top item in the follow-ups todo.
- **Corrected a deferral made earlier in the same session.** The missing top-level `sec-N`
  anchors were filed as a todo on the assumption the fix cascaded every paragraph anchor;
  checking how the two healthy surveys actually do it showed an anchor-only marking with no
  cascade at all. Fixed and closed rather than deferred
  (`todos/2026-08-14-top-level-section-anchors.md`).
- **Forecloses** nothing. The unexpanded `load-bearing` sections keep their collected
  evidence in `_scratch/max-c*.md`, unconsumed but preserved, so a later pass starts from
  evidence rather than from search.
- **Obliges** the follow-ups todo to be worked before this survey is called complete: four
  `load-bearing` sections were labelled but not expanded, and one evidence cluster carries an
  explicit coverage-gap marker.

## Refs

- `surveys/llms-for-coding/_scratch/00-max-mode-outline.md` — the persisted brief and
  depth-tier allocation (the Phase-5 drift-diff's left-hand side).
- `reports/2026-08-14-llms-for-coding-max-mode-expansion.md` — the Phase-5 report.
- `bugs/2026-08-14-01-rlef-citation-values-wrong.md`.
- `todos/2026-08-14-llms-for-coding-followups.md`,
  `todos/2026-08-14-top-level-section-anchors.md` (closed).
- `decisions/2026-08-14-02-viewer-content-roots.md` — the prior decision this session.
