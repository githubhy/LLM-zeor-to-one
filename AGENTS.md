# AGENTS.md

## Core Role

Act as a Staff LLM/AI Research Engineer. Maintain that level of technical rigor in
analysis, design, and implementation.

## The authoritative instruction set is `CLAUDE.md`

**Read [CLAUDE.md](./CLAUDE.md) in full and follow it.** It is the single source of truth for
how work is done in this repo, and it governs — among other things — conventions this file
used to restate and no longer does:

- **Conversation logging** — one log file per *session*
  (`prompts/YYYY-MM-DD-<session-slug>.md`), not per day.
- **Todo / Decision / Bug / Field-note capture** — every deferred item, judgment call,
  non-trivial bug, and same-session retrospective gets a durable record. This is the repo's
  audit trail; work that skips it is not tracked.
- **The survey workflow** — `surveys/<slug>/` layout, `order.json` + `references.md`, the
  `viewer/tools/` toolchain, `/check-survey` as the sign-off gate and `/normalize-survey` as
  its write-mode twin.
- **Git hooks** — `git config core.hooksPath .githooks` installs the pre-commit and pre-push
  gates (`scripts/install-git-hooks.sh` does this idempotently and sets the exec bit). A push
  runs survey-wide validation; a failing check is fixed, not bypassed.
- **Agent fan-out** — deliberate per-fan-out model selection, and the sizing /
  failure-diagnosis discipline for subagents.
- **Rules loaded on demand** — `.claude/rules/*.md` hold the detailed rules (math authoring,
  citation integrity, cross-linking, report completeness, calibration-residual attribution,
  reset durability, and more). Read the relevant one *before* doing matching work; several are
  enforced by hooks that will block edits.

## Why this file does not restate those rules

A second hand-maintained copy of a large ruleset drifts silently — that is a property of
copies, not of any one instance. Upstream measured it: its `AGENTS.md` still instructed agents
to keep **one log file per day**, a convention `CLAUDE.md` had already retired *because two
parallel sessions collided on a shared day file*, and it omitted the capture conventions
entirely. An agent following it would have reintroduced an already-fixed bug and produced no
audit trail at all.

It is the same reason the git hooks are wired through `core.hooksPath` rather than copied into
`.git/hooks/`: a copy is a snapshot, and it drifts. So this file is deliberately a pointer —
the rules live in exactly one place, and it is `CLAUDE.md`.

If you are an agent that does not load `CLAUDE.md` automatically, load it now before doing
anything else in this repository.
