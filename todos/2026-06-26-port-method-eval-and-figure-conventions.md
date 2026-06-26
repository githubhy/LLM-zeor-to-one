# Consider porting upstream `method-eval` skill + `figure-operating-conditions.md`

status: open

## Context

During the 2026-06-26 full upstream sync (branch `sync/upstream-2026-06-26`), the
re-adapted `deep-research-survey` skill (batch 1) referenced two upstream harness
components that are **not in the `7c3a3bf..HEAD` delta** — they predate the
high-water mark and were never ported at the 2026-06-13 bootstrap:

- **`method-eval` skill** — used by the optional "method-search register" in
  `addenda/phase-2.md` (R-SURVEY) to score method-viability dossiers.
- **`figure-operating-conditions.md`** — figure-convention rule referenced by the
  R-SURVEY FIGURES artifact and the "explicit n/a beats silent absence" principle.

To avoid dangling references, both were **genericized** in the port ("a dedicated
method-evaluation pass", "the figure operating-conditions conventions"). The
methodology still reads correctly, but the richer upstream capability is absent.

## What is left

Decide whether to port (re-adapt telecom→LLM) the `method-eval` skill and
`figure-operating-conditions.md` from `../data-channel-receiver`, then restore the
specific references in `addenda/phase-2.md` (lines ~16, ~64, ~82).

## Acceptance

Either: both components ported + adapted + referenced by name in `phase-2.md` and
leakage-clean; OR a decision recorded to keep them generic (close as wontfix).

## Refs

- Branch `sync/upstream-2026-06-26`, batch 1 (`deep-research-survey` skill).
- `.claude/commands/sync-upstream.md`; decision `2026-06-26-01`.
- Conversation log: `prompts/2026-06-26-adapt-sync-upstream-skill.md`.
