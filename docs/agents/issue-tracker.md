# Issue tracker: GitHub Issues (intake) + in-repo records (record of record)

This repo runs **two surfaces with one rule**. They are not duplicates — they hold
different stages of the same lifecycle, and every fact lives in exactly one of them plus
a link to the other.

- **GitHub Issues** — the **intake and triage** surface. Where a request, report, or idea
  arrives and gets evaluated. Repo: `githubhy/LLM-zeor-to-one` (public, Issues enabled).
  Use the `gh` CLI; it infers the repo from `git remote -v` inside a clone.
- **`todos/`, `bugs/`, `decisions/`, `field-notes/`** — the **durable record of record**.
  Governed by `CLAUDE.md` (Todo / Decision / Bug / Field-note Capture) and **mechanically
  gated** by `viewer/tools/check-record-ids.py` in `.githooks/pre-push` at severity
  `error`: id uniqueness, `INDEX.md` row/file consistency, frontmatter-id agreement, and
  resolvability of every qualified `bugs/<id>` / `decisions/<id>` reference.

## Why two, and why this split

The in-repo records are the load-bearing half: 60+ records, cross-session, gated, and
required by `CLAUDE.md`. They are what a future session reads to answer *"what did we say
we'd come back to?"*. What they lack is an **intake surface** — a place for a request to
land before anyone has decided it is a todo, a bug, or nothing.

GitHub Issues fills exactly that gap and nothing more. Treating it as a second record of
record is the failure this repo's own `AGENTS.md` warns about: *a second hand-maintained
copy of a ruleset drifts silently — that is a property of copies.* So an issue is
**transient**; the record it graduates into is **permanent**.

## The lifecycle

| Stage | Lives in | Written by |
|---|---|---|
| Request / report / idea arrives | GitHub Issue, labelled `needs-triage` | `to-tickets`, external reporters, you |
| Triage | GitHub labels (see `triage-labels.md`) | `triage` |
| Accepted, work deferred | `todos/YYYY-MM-DD-<slug>.md` + an `INDEX.md` row | `CLAUDE.md` Todo Capture |
| Accepted, it is a defect | `bugs/YYYY-MM-DD-NN-<slug>.md` + an `INDEX.md` row | `CLAUDE.md` Bug Capture |
| A judgment call was made | `decisions/YYYY-MM-DD-NN-<slug>.md` | `CLAUDE.md` Decision Capture |
| Resolved in-session, worth a retrospective | `field-notes/YYYY-MM-DD-<slug>.md` | `CLAUDE.md` Field Notes |

**Graduation is the only way an issue leaves the queue** (other than `wontfix`). When an
issue is accepted, create its record, cross-link both directions, then close the issue.

## The cross-link rule (non-negotiable)

A fact never lives in both places unlinked.

- The **issue body** carries the record path, e.g. `Record: todos/2026-01-01-some-slug.md`.
- The **record's `Refs` section** carries the issue URL.

Both directions must resolve. This is what keeps the two surfaces from drifting, and it is
the same discipline `check-record-ids.py` already enforces inside the record set.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for
  multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`
  with appropriate `--label` and `--state` filters.
- **Comment**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."` — the comment names the record it
  graduated into, or states why it is `wontfix`.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as
feature requests; `/triage` reads this flag.)_

## When a skill says "publish to the issue tracker"

Create a **GitHub issue**. It is intake; it has not been decided yet.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`. If the work has already graduated, follow the
`Record:` line to the in-repo record — that is the current truth, not the issue body.

## When a skill says "record this deferral / bug / decision"

Write the **in-repo record** per `CLAUDE.md`, not an issue. These are conclusions, not
requests. `CLAUDE.md`'s capture rules are unconditional: *"a handoff or 'next step' named
only in a report, survey, plan, or chat — but not filed under `todos/` — does not count as
tracked."* An issue does not satisfy that either.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: an issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog
  body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the
  sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in
  the map body and put `Part of #<map>` at the top of the child body. Labels:
  `wayfinder:<type>` (`research` / `prototype` / `grilling` / `task`).
- **Blocking**: GitHub's native issue dependencies. Add an edge with
  `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`,
  where `<blocker-db-id>` is the blocker's numeric **database id**
  (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, *not* the `#number` or `node_id`).
  Where dependencies aren't available, fall back to a `Blocked by: #<n>` line at the top of
  the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children, drop any with an open blocker or an
  assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`.
- **Resolve**: comment the answer, close the issue, then append a context pointer to the
  map's Decisions-so-far — and, if the outcome is durable, graduate it into a record.

Wayfinder maps are working state, so they may live entirely on GitHub. Any *conclusion*
a map reaches still graduates into `decisions/` or `todos/`.
