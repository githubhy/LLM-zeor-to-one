# Deferred-Item Tracking Rule

Loaded on demand by `CLAUDE.md`. Read this file before signing off any
task — plan, report, review, audit, survey, or implementation — that **defers**
work: anything punted, documented-but-not-applied, or marked "out of scope /
follow-up / later pass / recommend (not applied) / deferred".

## The rule

**When a task defers a batch of actionable items, open a tracking todo under
`todos/` before you sign off.** A "batch" is two or more deferred items — or even
one if it is load-bearing (a correctness/security gap, or a blocked sub-task).

A deferral that lives only in a report's prose or a chat summary is **not
tracked**: reports get superseded, chats get compacted, branches get merged and
forgotten. `todos/` is the single durable place a future session looks for "what
did we say we'd come back to?" — so deferred work is never lost between sessions.

## What counts as a deferral (open a todo)

- "documented, not applied" / "deferred to a later pass" / "follow-up"
- "out of MVP scope" / "recommend (not applied)" for actionable work
- a blocked or skipped sub-task in a plan / implementation report
- "further study warranted" / "production default" with the work not done
  (also flagged by `sim-report-completeness`)
- a known limitation you intend to fix but didn't this pass

## What does NOT need a todo

- Items **triaged as by-design or false-alarm** — a non-issue is not deferred
  work. Record the triage reason in the report, not a todo.
- Work you **complete in the same task** (no deferral).
- A single trivial follow-up the next reader cannot miss — though when in doubt,
  write the todo (it is cheap insurance).

## `todos/` format

One markdown file per deferred batch, named `todos/YYYY-MM-DD-<slug>.md` (the date
the deferral was made; matches the repo's dated-artifact convention used by
`bugs/`, `field-notes/`, `plans/`). This repo's `## Todo Capture` convention governs
the file shape — YAML frontmatter plus self-contained body sections:

```markdown
---
slug: <short-slug>
date_filed: 2026-06-21
status: open            # open | in-progress | closed
---

# <short title>

## Context
<why this is deferred, what was done around it>

## What is left
- <concrete action>
- <concrete action>

## Acceptance
<how to know it's done>

## Refs
<plan section, commit SHA, report path>
```

Add one row per todo file to `todos/INDEX.md`, the append-only master index:
`date | slug | title | status (open / in-progress / closed) | one-line hook`.
No item content in the index — the row is a pointer, the file holds the detail.

## Closing the loop

When you pick a deferred item up, set its file to `status: in-progress` and update
`INDEX.md`. When it is resolved, set `status: closed`, append a `**Resolution.**`
line, and update `INDEX.md`; closed todos stay on disk as the audit trail. A report
that says "deferred (tracked in `todos/<file>`)" is complete; a report that says
"deferred" with no `todos/` pointer is **not** — fixing that is the whole point of
this rule.

## Cross-references

- `sim-report-completeness.md` — already mandates "prioritised gaps → `todos/`"
  (§ 11 Roadmap) and forbids "further study warranted" without a named `todos/`
  action; this rule generalises that `todos/` convention to every deferring task
  and defines the file format.
- `workflow.md` — the plan / report / implementation workflow this rule
  front-stops at sign-off.
- `CLAUDE.md` `## Todo Capture` — the section this rule front-stops; the
  `todos/INDEX.md` schema and status transitions above mirror it exactly.
