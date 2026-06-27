# Phase 1: Scope & branch

## Goal
Understand the target skill exactly, and (in `full` mode) set up an isolated workspace.

## Steps
- Read the target skill in full: `SKILL.md`, every `phases/*` / reference file, and any
  companion script (validators, gate-checkers). Write a short anatomy note (what each phase
  does, where the gates/enforcement are, what the deliverable is).
- Confirm the skill's KIND — does it produce prose (survey), code+experiments (implementation
  study), or something else? The verification regime in Phase 5 depends on this.
- `full` mode: cut a branch `skill-analysis/<target>`; create `bench/<target>/PROGRESS.md`
  (10-stage tracker) so the run survives compaction.
- `quick` mode: work in place; a lightweight tracker is optional.

## Deliverable
An anatomy note + (full) a branch + tracker. Record the active mode (`quick`/`full`).
