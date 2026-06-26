---
id: 2026-06-26-01
title: Adapt /sync-upstream command from pitch-perfector; anchor high-water mark at the bootstrap-date upstream SHA
status: accepted
date: 2026-06-26
---

## Context

This repo's `.claude` harness was bootstrapped 2026-06-13 by porting from
`../data-channel-receiver` (telecom/3GPP) and retargeting it to LLM/AI surveys,
but it had no mechanism to pull subsequent upstream harness-config fixes. The
sibling repo `../pitch-perfector` (also bootstrapped from the same upstream,
retargeted to MIR) had already solved this with a `/sync-upstream` command plus a
`.claude/upstream-sync.json` high-water mark. The user asked to adapt that command
here. Two judgment calls were not pre-decided: (a) what to use as the
`last_synced_commit` baseline, and (b) whether to model it as a command vs a skill.

## Decision

Port pitch-perfector's `/sync-upstream` as a repo command
(`.claude/commands/sync-upstream.md`, matching this repo's command convention),
remapping the domain mapping table MIR → LLM/AI and the leakage grep to wireless
terms. Anchor `last_synced_commit` at `7c3a3bf` — the last upstream commit on or
before the 2026-06-13 bootstrap date — so the first real run replays the full
post-bootstrap config backlog (314 upstream commits in range).

## Alternatives considered

- **Baseline = current upstream HEAD (`5d485d7`).** Rejected: would silently skip
  every harness fix made upstream since the bootstrap — the opposite of the point.
- **Baseline = a precise "bootstrap SHA" recorded at port time.** Rejected: none
  was recorded in 2026-06-13; the last-commit-≤-bootstrap-date SHA is the
  best-justified, reproducible proxy and errs safe (replays a little extra, never
  skips).
- **Model as a skill, not a command.** Rejected: the upstream artifact is a
  command, this repo already uses `.claude/commands/*.md`, and the workflow is an
  imperative procedure, not a discipline rule needing pressure-tested guidance.
- **RED-baseline pressure-test per writing-skills Iron Law.** Rejected as N/A: this
  is a 1:1 port of a proven procedural command, verified by its own step-3 gate
  (leakage grep + `py_compile` + `json.tool`), not a novel behavior skill.

## Consequences

- Enables `/sync-upstream [--dry-run | <range>]`; registered in `CLAUDE.md`
  Commands catalog and discoverable as a skill.
- First run faces a 314-commit backlog — expect to triage in batches; `--dry-run`
  first.
- The step-3 leakage grep already caught residual bootstrap leakage in
  `viewer/tools/` docstrings → filed `todos/2026-06-26-clean-residual-wireless-leakage-in-viewer-tools.md`.
- This repo (unlike pitch-perfector) has the full toolchain ported; only
  `check-footnote-refs.py` / `crosslink.py` remain as graceful-degradation entries.

## Refs

- `.claude/commands/sync-upstream.md`, `.claude/upstream-sync.json`.
- Memory: `claude-infra-ported-from-data-channel-receiver`.
- Related: `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md`; todo `2026-06-26-clean-residual-wireless-leakage-in-viewer-tools`.
- Conversation log: `prompts/2026-06-26-adapt-sync-upstream-skill.md`.
