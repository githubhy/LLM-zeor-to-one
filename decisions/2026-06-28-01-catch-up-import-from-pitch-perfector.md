---
id: 2026-06-28-01
title: Full-parity catch-up import of harness config from sibling repo pitch-perfector
status: accepted
date: 2026-06-28
plan: null
---

## Context

Three repos share one Claude research harness, all bootstrapped from the upstream
template `../data-channel-receiver` (telecom/3GPP): `pitch-perfector` (MIR/pitch),
`sionna` (a wireless sibling), and this repo `llm-zero-to-one` (LLM/AI). `pitch-perfector`
had evolved its harness furthest — notably a **two-directional `/sync-upstream`** (`--back`)
plus several generic capabilities this repo lacked. The user asked to "sync /sync-upstream
from ../pitch-perfector" and then run an inbound + outbound sync, and chose **full parity**
(largest scope) when asked.

A structural diff (pitch-perfector vs here) surfaced: a two-directional sync-upstream
command; commands `bg`, `refine-plan`, `review-plan`, `add-reference`, `enrich`,
`add-dataset`; skills `method-eval`, `skill-improvement`; rule `figure-operating-conditions`;
hook `log-turn-telemetry.py`; scripts `notify.sh` + `compose-notify-msg.py`,
`install-git-hooks.{sh,ps1}`. Agents (`evidence-collector`, `survey-enricher`, `viewer-dev`)
also differed but were not in the agreed scope.

## Decision

Port the full generic surface, re-adapting MIR→LLM where domain-coupled, and re-adapt the
three domain-instantiated items (`add-dataset`→eval benchmarks, `figure-operating-conditions`
→LLM figure disclosure, `method-eval`→LLM candidate-method eval). Several judgment calls
within:

- **Skip-guard re-domained.** The two-directional command's round-trip skip-guard and
  outbound branch were keyed to **`from llm-zero-to-one`** (this repo's own outbound tag),
  not pitch-perfector's `from pitch-perfector` — so a sibling's sync-back remains a
  legitimate inbound delta here.
- **Datasets use the existing `local:` tag, not a new `dataset:` tag.** This repo's
  `citation-integrity.md` defines `local:/spec:/web/abstract-only`; `add-dataset` registers
  benchmarks under `download/datasets/` with the strong `(local: download/datasets/<path>)`
  form, so `check-citation-sources.py` validates them without a new tag class.
- **`method-eval` repositioned, agents genericized.** Framed as a fast viability gate
  UPSTREAM of the existing `reference-implementation-study`, complementary to `sim-audit`;
  the MIR `survey-enricher` agentType reference was dropped (this repo has no agents).
- **`install-git-hooks` kept as an alternative.** This repo's active pre-push wiring is
  `core.hooksPath .githooks`; the copy-installer is documented as an alternative, not a
  replacement (no regression).
- **Telemetry wired locally only.** `log-turn-telemetry.py` wired as an async Stop hook in
  the gitignored `settings.local.json` via `py-launcher.sh`; the personal ntfy curl endpoint
  was NOT copied; `notify.sh` left flag-gated/off.
- **`skill-improvement` ported via a Sonnet subagent** (mechanical 13-file tree, explicit
  rubric), verified independently (leakage-clean, py/json compile).
- **Stale toolchain note fixed.** The command's "crosslink.py / check-footnote-refs.py not
  yet ported" note was stale (both present) — updated to "toolchain complete".

This also resolved the open todo `2026-06-26-port-method-eval-and-figure-conventions`
(both components now ported and referenced by name in `deep-research-survey/addenda/phase-2`,
`sim-audit`, `sim-report-completeness`).

## Alternatives considered

- **Port only the `/sync-upstream` command** (literal reading) — rejected: the user chose
  full parity; the command alone leaves the rest of the gap.
- **Generic-only, defer the 3 domain items** — rejected for the same reason; the domain
  re-adaptation is the higher-value part and integrates with existing skills/rules.
- **Add a `dataset:` source tag** — rejected (YAGNI): `local:` already covers in-repo
  datasets and is checker-validated; a new tag would need `check-citation-sources.py` changes.
- **Port the 3 agents too** — deferred (not in agreed scope); references genericized,
  tracked in `todos/2026-06-28-port-pitch-perfector-agents.md`.

## Consequences

- Harness is at parity with pitch-perfector on the generic surface; `/sync-upstream` is now
  two-directional. Enables the outbound sync-back (see `decisions/2026-06-28-02`).
- Viewer (non-config) gaps vs upstream main (`figure-pipeline.js`, sionna viewer test gates)
  remain — tracked in `todos/2026-06-28-import-viewer-figure-pipeline-from-upstream.md`.
- 3 pitch-perfector agents un-ported — tracked in `todos/2026-06-28-port-pitch-perfector-agents.md`.

## Refs

- `decisions/2026-06-28-02-sync-back-to-upstream.md` (the outbound half).
- `decisions/2026-06-26-01` (the original sync-upstream adaptation), `2026-06-27-01` (pre-push gate).
- `.claude/upstream-sync.json` (mark advanced to origin/main 9b118d3).
- Conversation log: `prompts/2026-06-28-harness-sync-pitch-perfector.md`.
- Closed todo: `todos/2026-06-26-port-method-eval-and-figure-conventions.md`.
