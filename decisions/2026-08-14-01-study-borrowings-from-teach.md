---
id: 2026-08-14-01
title: Borrow retrieval practice, a prerequisite gate, and a re-pitch hatch into /study
status: accepted
date: 2026-08-14
---

## Context

`/study` shipped 2026-08-13 (`decisions/2026-08-13-02`, commit `fd52bd2`) with a
deterministic frontier detector and a session command. The reader then asked what the
installed `mattpocock-skills` plugin had that was worth borrowing. Two of its 35 skills
were relevant: `productivity/teach` and `productivity/wait-what`.

`teach` carries one idea this repo had reached independently and one it had not.

- **Reached independently:** *"fluency can give the user an illusory sense of mastery, but
  storage strength is the real goal."* That is precisely the corpus-vs-reader split
  measured in `docs/reader-frontier-2026-08-13.md` — but the repo had the *diagnosis*
  without the *remedy*. `teach` names the remedy (retrieval practice, spacing,
  interleaving — desirable difficulty), and `/study` as shipped had none of it: it
  recorded new questions and never revisited an old one.
- **Not reached:** every lesson must sit in the learner's **zone of proximal development**,
  computed from their record. `study-frontier.py` ranked by interrogation density alone,
  and its live output put `appendix-i-mechanistic-interpretability.md` **second** on a menu
  for a reader measured at L1-engaged, L2-thin. That is a defect, not a preference: the
  tool was confidently pointing two rungs up, and the command says *never pick the menu by
  feel*, so it would have been followed.

## Decision

Take three borrowings, reject the rest.

1. **Retrieval practice opens the session** — `study-frontier.py --recall`, oldest fold
   first, answered from memory before the file is reopened. Spacing is automatic because
   sessions are days apart and the queue is age-ordered.
2. **A prerequisite gate on the menu**, as *data*: `.claude/study-prereqs` (glob → rung)
   plus `.claude/study-reader-rung`. A document more than one rung above the reader is held
   back; the "+1" is the ZPD.
3. **`/wait-what`** — a re-pitch hatch, adapted near-verbatim (it already assumed a
   `CONTEXT.md`, which this repo now has).

**The gate keys on prerequisite depth, not on the capability ladder.** This is the
substantive design call. The obvious move — reuse the L0–L7 ladder from
`docs/development-timeline.md` — is wrong, because that ladder tracks *depth of engagement
with the same object*, not difficulty: L3 ("the system around the model") is a **different
axis** from L2, not a harder one, so ladder-gating would have hidden body sections that are
perfectly readable at L1. The map therefore answers a different question — *what must a
reader already hold for this document to pay off* — informed by the ladder, not dictated by
it.

## Alternatives considered

- **Gate as a declared judgment overlay in the command**, like the existing criticality
  overlay — rejected. The command already carries one overlay, and a second unfalsifiable
  "use judgment" instruction is where drift lives; the whole reason the menu is computed is
  that judgment drifts toward the convenient. Data in a `.claude/` file is auditable, is
  diffable, and matches the repo's existing toggle convention.
- **Gate on the capability ladder rung** — rejected on the axis argument above. Recorded
  because it is the plausible-looking option and was the first proposal made in-session.
- **Hide held-back documents silently** — rejected; "explicit n/a beats silent absence"
  (`.claude/rules/figure-operating-conditions.md`). A suppressed menu that does not say it
  suppressed is a `check` that cannot be distinguished from "nothing there", the same
  failure `crosslink.py check` refuses.
- **Random fold selection for recall** — rejected in favour of oldest-first: age *is* the
  spacing interval, and determinism keeps the queue reproducible across a session.
- **Quiz generation / learning-record files / HTML lessons** (also in `teach`) — rejected.
  Quizzes were already rejected 2026-08-13 (the agent would set and grade against answers
  the corpus wrote); learning records duplicate `decisions/` + the fold record; HTML lessons
  would fork content away from the survey corpus and the viewer.
- **`teach`'s "never trust your parametric knowledge"** — already covered, and more
  strictly, by `.claude/rules/citation-integrity.md`. Nothing to add.
- **A compressed SP↔transformer reference document** (`teach`: *"lessons will rarely be
  revisited, reference documents will be"*) — deferred, not rejected. It is a synthesis and
  will be better written from more folded material. Filed as
  `todos/2026-08-14-sp-transformer-reference.md`.

## Consequences

- **Enables** the first measurement of storage strength in the session loop; the recall
  queue is a standing instrument, not a one-off like the 2026-08-13 extraction.
- **Obliges** upkeep: `.claude/study-reader-rung` must move when the ladder moves, or the
  menu silently narrows to a rung the reader has left. Noted in the command.
- **Found and fixed a live defect** in the prereq map itself on first run: first-match-wins
  meant the `llms-for-coding/*.md` catch-all swallowed the specific `appendix-i` rule and
  the document the gate exists to hold back leaked through at L2. Catch-alls are now last,
  with the incident recorded inline. Not filed as a bug — it was authored and fixed in the
  same turn, and the diff is the explanation.
- **Forecloses** nothing; `--all` and `--reader-rung` bypass the gate for any session that
  wants the full list.

## Refs

- `viewer/tools/study-frontier.py`, `viewer/tools/test_study_frontier.py` (14 tests).
- `.claude/study-prereqs`, `.claude/study-reader-rung`, `.claude/commands/wait-what.md`.
- `.claude/commands/study.md` §1–2, `CONTEXT.md` "How a study session runs".
- `decisions/2026-08-13-02-study-session-operating-model.md` — the model this refines.
- `docs/reader-frontier-2026-08-13.md` — the measurement both borrowings answer.
- Upstream source: `mattpocock-skills` v1.2.3, `productivity/teach`, `productivity/wait-what`.
