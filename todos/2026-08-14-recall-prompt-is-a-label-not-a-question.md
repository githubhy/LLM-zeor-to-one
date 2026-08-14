---
slug: recall-prompt-is-a-label-not-a-question
date_filed: 2026-08-14
status: open
---

# `study-frontier.py --recall` serves a label, not a question

## Context

Found while *using* the retrieval-practice feature shipped hours earlier the same day
(`decisions/2026-08-14-01`), in the first `/study` session that ran with it. Promised to the
reader at the time and filed here rather than derailing the session.

`--recall` selects the corpus's oldest fold and prints its bold **lead** as the prompt. The
lead is the fold's title, written to sit *next to its host paragraph*. Lifted out of that
paragraph and served cold, days or weeks later, it frequently has no referent.

The live instance: the oldest fold in the corpus (55 days) is in
`surveys/llms-for-coding/language-models-from-first-principles.md:165`, and the prompt served
was:

> why this is $O(T)$, not $O(T^2)$

"**this**" has no antecedent once the surrounding paragraph is gone. The reader answered "I
don't even know what this is about" — and that is at least partly a **measurement artifact**,
not a clean storage-strength signal. A recall prompt that cannot be understood cannot
distinguish "forgot the answer" from "cannot tell which question is being asked."

This matters more than a cosmetic nit because the whole point of the feature is to measure
storage strength honestly. `.claude/rules/calibration-residuals.md` check 6 is explicit: check
the rig's preconditions before believing a result, *especially* on the easy case. A blank
reader looks like a strong finding and is the exact shape a broken rig produces.

## What is left

- Decide what the prompt should be. Options, roughly in increasing cost:
  1. **Include the host anchor's section heading** — cheap, already available from the
     paragraph anchor slug, and would have rendered the example as
     "*Attention cost — why this is O(T), not O(T²)*", which is answerable.
  2. **Serve the lead plus the first sentence of the fold's host paragraph** as context,
     withholding the fold body (which is the answer).
  3. **Store an explicit question field** at fold time — the cleanest, but it changes the
     `survey-explainer-fold` contract and cannot retrofit the 23 existing folds.

  Option 1 retrofits every existing fold with no authoring change and is the recommended
  starting point.
- Re-run `--recall` over the existing folds and read the prompts as a reader would. The
  defect was invisible until the feature was used against a real corpus; it will stay
  invisible to any check that only asserts a prompt was produced.
- Consider whether `rank_recall` should skip folds whose lead contains an unresolved
  demonstrative ("this", "that", "it") with no other noun — a cheap heuristic that would have
  caught this exact case.

## Acceptance

- `python viewer/tools/study-frontier.py --recall 5` prints five prompts that are each
  answerable without opening the source file.
- A test asserts the prompt for a fold whose lead begins with a demonstrative carries its
  section context.

## Refs

- `viewer/tools/study-frontier.py` — `collect_folds` (extracts `lead` via `LEAD_RE`),
  `rank_recall`, and the `--recall` CLI branch.
- `decisions/2026-08-14-01-study-borrowings-from-teach.md` — the decision that shipped the
  feature; this is the first field defect found in it.
- `.claude/rules/calibration-residuals.md` check 6 — the rig-vs-signal split this is an
  instance of.
- `prompts/2026-08-12-upstream-sync.md` Conversation 12 — the session where it surfaced.
