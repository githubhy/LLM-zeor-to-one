---
name: harness-harvest
description: >
  Turn a session's persisted learnings (field-notes/, bugs/, todos/, decisions/,
  the conversation log, and live context) into the RIGHT harness changes across
  every layer — skill, script/tool, command, hook, rule, config — with honesty
  triage, mechanism verification, the .claude/skill-options.json toggle-registry
  for default-on corrections, and a recurrence bar before creating anything new.
  Use at the end of a substantial session, or when asked to "turn what we learned
  into skill/harness updates" — the cross-layer, artifact-driven counterpart to
  skill-improvement (which improves ONE skill via a flag-lattice).
---

# Harness Harvest

Promote what a session *learned* into what the harness *does*, so the same friction
does not recur — routing each learning to the layer that fits (a script for a
mechanical recurring pain, a rule for a convention, a config toggle for a default,
a new skill only when the pattern is proven). Born from the 2026-07-04
a long survey-authoring session (see the session conversation log,
`field-notes/2026-07-04-chest-survey-verification.md`), which produced the
`normalize-survey` tool, the `.claude/skill-options.json` registry, five toggleable
options, and two skill/rule updates.

This skill is deliberately **thin**: it orchestrates existing machinery
(`skill-improvement`, the capture conventions, `normalize-survey`) under a fixed set
of guardrails. It is NOT a license to edit shared infrastructure freely.

## Core principles (non-negotiable)

- **Honesty filter first.** Most session "learnings" are marginal. Keep only those
  that are real, generalizable, and would prevent a *recurring* problem. Drop padding;
  say so. A harvest that changes nothing is a valid outcome.
- **Verify the mechanism before you encode it.** Test the fix on a fixture before
  writing it into a skill. The strongest 2026-07-04 result was *deleting* a hand-rolled
  workaround (`add_secmarkers.py`) after a 2-file test proved the official
  `renumber-sections --init` already did the job. **Prefer removing a workaround to
  adding a tool.**
- **Right layer, minimum footprint.** Match each learning to the cheapest sufficient
  layer (table below). Do not create a skill when a script, rule, or config toggle
  fits. New skills dilute the selection surface every future run reasons over.
- **Recurrence bar for anything NEW.** Before a new skill or tool, `grep` `field-notes/`
  + `bugs/` for the pattern. A NEW SKILL needs the *workflow* to have recurred ~2–3×
  (not just the friction). A NEW SCRIPT/TOOL needs the *friction* to recur and be
  mechanizable (the `normalize-survey` bar: 53 files mentioned the renumber/marker pain).
  N=1 → file a `todos/` to revisit, don't build.
- **Additive + reversible; default-off for anything risky.** Default-on *corrections*
  are registered in `.claude/skill-options.json` with `[opt:<ID>]` markers so they can
  be flipped off. *Additive* skill features go through `skill-improvement`'s
  default-off flag-lattice. Never silently change a baseline behavior.
- **Confirm before irreversible / shared-infra edits.** Editing a skill, rule, hook,
  or `CLAUDE.md` affects every future run. Surface the plan; get a nod for anything
  that isn't a pure additive toggle.

## Layer-routing decision table

| The learning is… | Route to | Toggle mechanism |
|---|---|---|
| a recurring, mechanical fix-sequence (do X then Y in order) | a **script/tool** (`viewer/tools/*.py`) + a `/command` | n/a (invoke or don't) |
| a workflow / gotcha correction inside one skill | **that skill's SKILL.md/addenda**, via `skill-improvement` if additive | `.claude/skill-options.json` if a default-on correction |
| a convention that spans skills/rules | a **rule** (`.claude/rules/*.md`) or a `CLAUDE.md` line | `.claude/skill-options.json` |
| a default (severity, scope, on/off) | a **config toggle** (`.claude/*`) | the config file itself |
| a genuinely new, recurred workflow | a **new skill** (only past the recurrence bar) | its own flag-lattice |
| a mechanical check that can gate | a **hook** step — but a *gate*, never an auto-mutator (cross-file fixes need whole-dir context) | severity config |

## Workflow (thin)

1. **Harvest.** Read this session's `field-notes/`, `bugs/`, `todos/`, `decisions/`, the
   conversation log, and the live context. List candidate learnings verbatim.
2. **Triage (honesty filter).** For each: is it real or padding? Generalizable or
   one-off? Drop the marginal ones explicitly. For survivors, `grep` prior `field-notes/`
   + `bugs/` to measure recurrence (this decides new-vs-update).
3. **Classify.** Assign each survivor a layer via the table above and a stable ID.
4. **Verify the mechanism.** Reproduce/fix on a fixture; confirm the official tool
   doesn't already do it (delete-the-workaround check).
5. **Route + implement.** Apply the change at the chosen layer — targeted edits, a new
   script, a `skill-improvement` cycle, or (past the bar) a new skill. Present the plan
   and confirm before touching shared infra.
6. **Make it toggleable.** Register default-on corrections in `.claude/skill-options.json`
   with `[opt:<ID>]` markers at each point of use; additive features get their own flag.
7. **Verify no regression.** Re-run the relevant gate (e.g. `normalize-survey` /
   `check-survey` for survey tooling); confirm the change lands clean and is idempotent.
8. **Record.** Write a `field-notes/` (or `decisions/` for a real judgment call) entry for
   the harness change and update the conversation log. File a `todos/` for anything held
   below the recurrence bar.

## Anti-patterns (the guardrails, restated)

- **Skill-from-N=1.** Creating a skill on a pattern's first appearance. → `todos/` instead.
- **Add-when-you-should-delete.** Building a tool that duplicates an official one. → test first.
- **Auto-mutating hook.** Running a whole-dir `--init` per file-write. → keep hooks as gates.
- **Silent baseline change.** A "default-on improvement" with no toggle and no confirm.
- **Padding harvest.** Encoding every session note as a change to look productive. → honesty filter.

## When NOT to use

A single-issue session (log it); a session whose learnings are already fully captured in
`bugs/`/`todos/`/`decisions/` with no promotion needed; or when the only candidate is a
one-off with no recurrence — file a `todos/` and stop.

## Composes with

- `skill-improvement` — the rigorous single-skill flag-lattice cycle (Phase-5 route for
  additive skill features; harness-harvest calls it, doesn't replace it).
- `.claude/skill-options.json` — the toggle registry for default-on corrections.
- `normalize-survey` / `check-survey` — the verify gate for survey-tooling changes.
- The capture conventions (`CLAUDE.md`: Field Notes / Bug / Todo / Decision Capture) —
  harvest reads their output and closes the loop by *promoting* it into the harness.
