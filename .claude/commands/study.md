Run a study session: $ARGUMENTS

The session pattern settled in `decisions/2026-08-13-02` and defined in `CONTEXT.md`
("How a study session runs"). **The reader asks; the agent writes.** The reader holds the
thread by choosing and asking — not by operating the keyboard.

## Argument parsing

`$ARGUMENTS` is optional and may be any of:

- *(empty)* — open with a computed menu and wait for the pick.
- a **document or topic** ("appendix D", "the memory wall", "h9", `surveys/…/appendix-g-moe.md`) — skip the menu, start there. **A reader-named topic always wins over the menu**; the menu exists to break ties, not to gatekeep.
- a **question** ("why is the KV cache O(T)?") — skip the menu, answer it, fold it.
- `--close` — run only the closing step (pulse check + log) for a session already in progress.

## 0. Guardrails (read before starting)

- **Autonomous end-to-end mode is OUT OF BOUNDS inside a topic-month.** It is the measured cause of the leak (`docs/reader-frontier-2026-08-13.md`: zero subject-matter questions across the 21 conversations in which eleven studies were executed). Never propose "go ahead end-to-end automatically" here, and if the reader asks for it, say what it costs before complying.
- **Do not batch answers.** One question, one answer, one fold. The turn boundary is the mechanism being protected.
- **Answer at the asked depth, then stop.** Volunteering the next three things pre-empts the next question, which is the artifact this session exists to produce.

## 1. Open with RETRIEVAL PRACTICE

```bash
python viewer/tools/study-frontier.py --recall 1
```

Put the question to the reader and **wait for their answer before opening the file**.
This costs two minutes and is the only part of the session that measures *storage*
strength rather than *fluency* — answering with the corpus open feels like mastery and
is not the same thing (`decisions/2026-08-14-01`). The queue is oldest-first, so spacing
is automatic.

Then grade it honestly and briefly: what came back, what did not. **A blank is
information, not a failure** — a fold the reader cannot reconstruct is a better menu
item than anything the density ranking will produce, and it may be taken as the
session's topic on the spot. Do not turn this into a quiz round: one fold, one answer,
move on.

## 2. Then a COMPUTED menu

```bash
python viewer/tools/study-frontier.py --top 8
```

The tool ranks by *interrogation density* — folds per section, least-read first — because a
`> **Note —**` fold is a recorded question (`survey-explainer-fold` only fires on a real
one). **Never pick the menu by feel**; that drifts toward whatever is easy to explain,
which is exactly what `decisions/2026-08-13-02` forbids.

The menu is gated to the **zone of proximal development**: `.claude/study-prereqs` holds
the rung each document presumes, and anything more than one rung above
`.claude/study-reader-rung` is held back and reported as a count. So the `pre` column is
already accounted for — do not re-apply it by eye, and do not reach into the held-back
list without saying why. **Keep the reader rung current**: when the ladder in
`docs/development-timeline.md` moves, that one-word file moves with it, or the menu
silently narrows to a rung the reader has left.

Then add **one** judgment overlay the tool cannot compute, and say you are adding it:
*criticality to the current topic*. A document that is a prerequisite for the active
topic-month (see `docs/development-timeline.md`) is worth surfacing even at a lower rank —
e.g. `appendix-d-gpt2.md` while Topic 1's Rung 2 is being built.

Present at most 4 options, one line of *why this one* each, and mark the recommendation.
Then stop and wait. The reader may substitute anything.

## 3. The loop

Repeat until the reader stops:

1. **Read together.** Load the section. Quote what it actually says rather than paraphrasing from memory — the reader is checking your claim against the text in front of them.
2. **The reader asks.** Answer at first principles, no skipped steps, per `.claude/rules/math-authoring.md`. When the answer rests on an external source, `.claude/rules/citation-integrity.md` applies in full — never cite from memory, and say so when a source is not held.
3. **Fold it.** Invoke `survey-explainer-fold` (modes: `full` / `note-only` / `prose`; ask only if genuinely ambiguous — the reader's last few folds are the best default). The fold is the session's durable output. **Name one primary source in it** — the single best thing to go read, from `references.md` / `download/` (acquire via `source-fetch` if it is not held). One, chosen; not the citation list the survey already carries. A fold that answers without pointing anywhere leaves the reader dependent on the answer.
4. **Watch for the escalations** and name them when they appear:
   - the question needs a *number* the corpus does not have → an **experiment**. **Write the reader's prediction down before the run** — a value, a range, and the reason — into the fold or the `todos/` entry *first*. An experiment run without a prior prediction collects data; one run against a prediction tests understanding, and it is the only instrument for L6 (*predict and falsify*), the rung neither column has started. Then scope it to the ~5 USD envelope and run it, or file the `todos/` entry carrying the prediction.
   - the question exposes a *missing derivation* → `/enrich-equation` or `/enrich`.
   - the question exposes a *missing area* → a new survey is allowed mid-session (`pulled on demand` in `decisions/2026-08-13-01`); do not treat it as scope creep.
   - the question is *about a study report* (`docs/*-study.md`, which has no fold instrument) → retro-audit it instead: what did it find, what would falsify it, does it survive a population split (`.claude/rules/calibration-residuals.md` check 6)?

**Prefer the reader's own frame.** The strongest questions in this repo's history were
signal-processing unifications the reader generated unprompted — matched filter, adaptive
filter, log-likelihood ratio, whitening. When an answer has a clean SP reading, lead with
it.

**When an answer does not land, `/wait-what` is the escape hatch** — a re-pitch in
Simplified Technical English using `CONTEXT.md`'s vocabulary, not a longer answer. Offer
it once if an explanation visibly misses; do not re-explain unprompted.

## 4. Close

```bash
python viewer/tools/study-frontier.py --since <session-start-ref>
```

Exit 1 means **zero folds were added — the session did not happen** (the one guardrail).
That is a signal to report honestly, not a failure to hide or to paper over by
manufacturing a fold. State it and note what to do differently.

Then:

- Log the session per `CLAUDE.md` Conversation Logging — **the questions asked are the payload**, not the files changed. Future sessions measure the frontier from this record (`docs/reader-frontier-2026-08-13.md`), so a vague `**Request**` line degrades the instrument.
- Run the validation sweep on anything edited: `python viewer/tools/renumber-paragraphs.py <file>`, then `/check-survey <survey>` if sections or equations moved.
- Name the next thread — the question this session opened and did not close.
- File `todos/` for anything deferred (`.claude/rules/deferred-tracking.md`).

## What this command is not

- **Not a curriculum.** It has no syllabus and no completion state; it surfaces the least-interrogated frontier and the reader chooses.
- **Not a quiz.** The reader asks the questions. An instrument that has the agent both setting and grading questions measures the corpus, not the reader.
- **Not a survey generator.** `deep-research-survey` owns that, and is invoked *from* a session when a question demands it — never as the session's default move.
