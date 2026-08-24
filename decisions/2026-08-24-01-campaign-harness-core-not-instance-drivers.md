---
id: 2026-08-24-01
title: Port the campaign harness's generic core, not its instance verification drivers
status: accepted
date: 2026-08-24
plan: .claude/commands/sync-upstream.md (inbound, step 2)
---

## Context

The 2026-08-24 inbound sync (`cedfccb2..24cfca29`) brought upstream's campaign-lifecycle
harness — 17 new files under `viewer/tools/`, two new rules, a registry, four severity
toggles and a `/campaign` command. The previous sync's mark note recorded these as "NOT
imported because they are upstream BRANCH-only, not on main"; they have since landed on
main, so they were in scope this time.

The harness is not uniform. Reading the import graph and the hardcoded paths split it
cleanly in two:

- a **generic core** — the descriptor schema gate, the stage state machine, the failure
  ledger, the denominator self-report (`campaign_common.Scope`), the basis enum, the
  pre-registration commit-order verifier, and the coverage / lineage / ledger gates. All
  stdlib-only, all parameterized, all degrade gracefully on an empty registry.
- an **instance verification driver** — `campaign_run.py`, `campaign_wake.py`,
  `campaign_verify.py`, `campaign_independent.py`, `build-ledger.py`, plus upstream's
  top-level `tools/campaign_cli.py` and the `/campaign` command that fronts them. These
  hardcode `artifacts/nr-pdsch-demod/conformance-case-register.json`, a spec-mirror path
  list, and a schema of `measured_snr_db` / `margin_db` / reference-performance fields.
  `campaign_run.py` additionally imports `tools/sync_campaign_results.py`, which the sync
  command declares out of scope.

## Decision

Port the generic core (12 files + 2 rules + the registry + toggles); do not port the four
instance drivers, the per-campaign ledger builder, the CLI, or the `/campaign` command.
Wire the core into `.githooks/pre-push` behind existence guards so it is a no-op until the
first campaign registers.

## Alternatives considered

- **Port everything, re-domaining the register schema.** Rejected: there is no register
  here to re-domain *against*. Inventing `measured_accuracy` / `margin_points` fields and a
  conformance-case register to match would be authoring a schema nobody uses and calling it
  a port — the "invention is not omission" failure `check-campaign.py::_check_stages` warns
  about, committed at the level of a whole subsystem.
- **Port nothing until a campaign exists here.** Rejected: it inverts the point. The rules
  say a campaign must be executed against a machine-readable descriptor *from the start*;
  a harness that arrives after the first campaign is the "plan that depends on being
  remembered" the rule exists to prevent. The core is opt-in and costs nothing idle.
- **Port the CLI but not the drivers.** Rejected: three of its six subcommands (`verify`,
  `sync`, `run`) drive exactly the unported files. A front door whose handle comes off is
  worse than no front door.

## Consequences

- `.claude/campaigns` ships **empty**, matching the established local pattern for
  `.claude/rollup-pages` and `.claude/program-manifests`.
- Four gates REFUSE (exit 2 — "no verdict", not a pass) on every push. They are wired
  through a `run_advisory_gate` helper that treats exit 1 as failure and exit 2 as a loud
  advisory, so the REFUSE is visible without blocking. Collapsing the two exits is what
  lets a blind gate read as agreement, which `campaign_common.Scope` exists to prevent.
- `check-ledger.py` reads each campaign's own `ledger_builder` from its descriptor, so the
  absent builder degrades to "campaign declares no ledger_builder — skipped" rather than a
  dangling reference.
- The first campaign here must supply its own ledger builder and, if it wants one, its own
  verification driver. Tracked in `todos/2026-08-24-upstream-sync-followups.md`.
- The `BASES` enum was re-domained from the RAN4/RAN5 requirement ladder to the LLM
  published-value ladder (`reference-performance` / `published-value` / `published-mean` /
  `harness-baseline`), matching `.claude/rules/sim-report-completeness.md`
  `[opt:SIM-REQBASIS]`. It is the one piece of the core that could not be ported verbatim,
  because its member names *are* domain.

## Refs

- `.claude/rules/campaign-execution.md`, `.claude/rules/campaign-lifecycle.md`
- `viewer/tools/campaign_common.py::BASES`, `.githooks/pre-push` (campaign block)
- `.claude/upstream-sync.json` (mark advanced to 24cfca29)
- `prompts/2026-08-24-upstream-sync.md`
