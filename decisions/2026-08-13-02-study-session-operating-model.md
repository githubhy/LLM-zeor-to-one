---
id: 2026-08-13-02
title: Study sessions run read-ask-fold with the reader choosing, not reader-as-author
status: accepted
date: 2026-08-13
---

## Context

`docs/reader-frontier-2026-08-13.md` measured the reader column of the capability ladder
from the question record and found the leak: **zero subject-matter questions across the
last three sessions** (21 conversations), the exact window in which eleven studies were
executed under an explicit *"go ahead end-to-end automatically"* mandate. The conclusion
drawn there — that the **execution mode is the mechanism**, because a mandate removing the
turn boundary removes the question surface with it — is not in dispute and this record does
not revisit it.

What was in dispute is the remedy. The agent proposed **inverting the role contract**: for
topic work the reader authors code, derivations and notes, and the agent reviews. The
reader rejected it — *"me authoring is much less effective"* — and proposed instead: the
agent offers a topic menu each session, the reader picks one or substitutes their own, and
then reads, asks, folds, and experiments with the agent's help.

## Decision

Adopt the reader's model. A study session is **read-ask-fold with the reader choosing**;
the agent writes, the reader asks. One guardrail only: **a session that produces zero folds
did not happen.** Menu items are drawn from the measured frontier (appendices D–I first,
then L2, then L4), never from what is convenient to explain. Autonomous end-to-end mode
stays correct for harness work and is out of bounds inside a topic-month.

## Alternatives considered

- **Reader-as-author, agent-as-reviewer** (the agent's own prior recommendation) —
  rejected, and rejected by the reader's own data rather than by preference. The single
  most productive learning session in the record (2026-06-29: **28** subject-matter
  questions, three times any other session) was pure read-ask-fold with the agent doing all
  the writing. The proposal would have replaced the one mode empirically shown to move the
  frontier with a slower mode that merely *resembles* ownership. **Authoring is a proxy for
  engagement; the real variable is who holds the thread** — and the reader holds it by
  choosing and asking, whoever operates the keyboard.
- **Three guardrails** (question quota per session, dedicated question log, agent forbidden
  to answer before the reader attempts) — rejected as over-engineering. Only one metric was
  ever shown to track frontier movement, so only one guardrail is earned. A quota is also
  gameable and measures volume, which was never the deficiency.
- **`appendix-q` as a general quiz** — rejected earlier in the same session and recorded
  here for completeness: it is skill-synthesised, so it measures the corpus a second time.
  Retained only as a targeted probe of appendices D–I.
- **Status quo (autonomous mode inside topic work)** — rejected; it is the measured cause.

## Consequences

- **Enables** a session rhythm that costs the reader no authoring overhead while preserving
  the turn boundary by construction, since the reader drives.
- **Obliges the agent** to open study sessions with a frontier-drawn menu, and to treat a
  fold-free session as a signal rather than a success.
- **Forecloses** autonomous end-to-end execution inside a topic-month — including for
  Topic 1, whose named risk is precisely that it could be run that way and close with the
  corpus advancing and the reader not.
- **Follow-up:** none deferred. The model is in `CONTEXT.md` and takes effect immediately.
- Creating a survey mid-session remains allowed when a question demands one — consistent
  with *pulled on demand* in `decisions/2026-08-13-01`, not a re-opening of it.

## Refs

- `CONTEXT.md` — "How a study session runs", the operative text.
- `docs/reader-frontier-2026-08-13.md` — the measurement this decision answers.
- `decisions/2026-08-13-01-learning-road.md` — the road this operates inside; unchanged.
- `.claude/skills/survey-explainer-fold/SKILL.md` — the instrument the pulse check uses.
- `prompts/2026-08-12-upstream-sync.md` Conversation 9.
