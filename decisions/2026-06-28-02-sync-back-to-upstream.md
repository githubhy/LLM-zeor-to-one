---
id: 2026-06-28-02
title: Outbound sync-back to data-channel-receiver — /enrich-equation only (PR #15)
status: accepted
date: 2026-06-28
plan: null
---

## Context

The user asked for an outbound sync (`/sync-upstream --back`) and authorized "Push + open
PR". The reverse flow's R0 discovery classifies every generic-surface diff between here and
upstream `../data-channel-receiver`, keeping only **SYNC-BACK** candidates (generic
improvements that ORIGINATED here that upstream lacks).

R0 finding (evidence-based, per the "diagnose by reading, not pattern-matching" rule):
this repo's entire config-touching git history is `chore(sync)` / `Port … from
data-channel-receiver` / `Bootstrap` — it is a **consumer**, not an originator. A sampled
`viewer/tools/lint-math.py` diff was pure genericization (a docstring example path; upstream
bug-IDs genericized into prose) → SKIP-genericization. The capabilities imported this session
from pitch-perfector are **SKIP-not-ours** (they originated in a sibling, reach upstream via
its own `--back`/PR #14, not ours). The one genuine exception: **`enrich-equation.md`** —
here-only (absent from upstream and from pitch-perfector), authored here (commit `cc760e7`),
generic in mechanism (single-equation, no-cascade derivation expansion).

## Decision

Sync back **only** `enrich-equation.md`, with its one LLM worked-example genericized to a
neutral ratio-derivative (quotient/chain-rule) example. Prepared on a **separate git
worktree** off `origin/main` (so upstream's current dirty `sync-from-pitch-perfector`
checkout was never touched), staged the single file, committed with the subject template
`feat: … from llm-zero-to-one` (so upstream's inbound skip-guard keys on it), pushed branch
`sync-from-llm-zero-to-one`, and opened **PR #15** with a Provenance section linking back to
this repo's records by reference (no audit-trail docs copied). Verified all referenced paths
exist on upstream `main`; the upstream pre-push gate passed clean.

## Alternatives considered

- **Open no PR (nothing genuinely originated here)** — the honest R0 finding was "one
  candidate". Given the user's explicit "Push + open PR" authorization AND a real (if small)
  candidate, syncing the one candidate honors the intent. Rejected "skip entirely".
- **Sync back more (viewer/tools, hooks, rules diffs)** — rejected: all classified
  SKIP-genericization / SKIP-domain / SKIP-not-ours; pushing them would re-domain upstream's
  own files or re-export a sibling's work.
- **Prepare-only, stop before push** — the user explicitly chose "Push + open PR" over this.
- **Branch off the current upstream checkout** (`sync-from-pitch-perfector`, dirty) — rejected;
  used a clean worktree off `origin/main` to avoid disturbing pitch-perfector's WIP.

## Consequences

- PR #15 (`FenLinger/data-channel-receiver`) is open for the maintainer to accept/decline.
- `pending_sync_back` recorded in `.claude/upstream-sync.json`; **after the PR merges**,
  advance `last_synced_commit` to the post-merge upstream HEAD (round-trip hygiene). The
  `from llm-zero-to-one` inbound filter is the backstop.
- enrich-equation overlaps upstream's broader `/enrich`; positioned in the PR as the focused
  single-equation complement — the maintainer decides on merge.

## Refs

- PR: https://github.com/FenLinger/data-channel-receiver/pull/15 (branch `sync-from-llm-zero-to-one`).
- Feature origin: commit `cc760e7` (this repo). Sibling precedent: upstream PR #14 (pitch-perfector), #13 (sionna).
- `decisions/2026-06-28-01-catch-up-import-from-pitch-perfector.md` (the inbound half).
- `.claude/commands/sync-upstream.md` Reverse section (R0–R4).
- Conversation log: `prompts/2026-06-28-harness-sync-pitch-perfector.md`.
