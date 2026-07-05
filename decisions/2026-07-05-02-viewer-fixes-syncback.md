---
id: 2026-07-05-02
title: "Sync-back the three viewer fixes to upstream on an isolated worktree branch (not the stale sync-from-llm-zero-to-one)"
status: accepted
date: 2026-07-05
plan: (/sync-upstream --back — todos/2026-07-05-land-viewer-fixes-upstream-via-back-sync)
---

## Context

Executing `/sync-upstream --back` for the three viewer fixes from backlog #3
(EISDIR guard, multi-span highlight, T12 e2e robustness; downstream commit
`b8346d5`). Two realities complicated the standard `--back` flow:

1. The upstream working copy (`../data-channel-receiver`) is on the owner's active
   feature branch `wcm-tdl-cdl-calibration` with uncommitted WIP (a modified
   prompts file + ~37 untracked telecom-research files). Committing into it, or
   `git switch`-ing that dirty tree, would entangle the owner's work.
2. The canonical branch name `sync-from-llm-zero-to-one` **already exists** with 6
   unmerged commits from a prior sync-back (the enrich-equation command) and is
   not on origin — reusing/resetting it would destroy that prior work.

## Decision

Prepared the sync-back in an **isolated git worktree off upstream `main`**
(scratchpad path), on a **new, distinctly-named branch
`sync-viewer-fixes-from-llm-zero-to-one`** — leaving the owner's dirty feature-branch
tree and the stale `sync-from-llm-zero-to-one` branch completely untouched. Copied
the 5 fixed files in (verified upstream `main == wcm-tdl-cdl-calibration` on all 5,
so the fixes apply cleanly on main), **stripped HERE provenance** (downstream bug
IDs `2026-06-17-01`/`2026-06-19-01`, todo `citation-t12-e2e-timeout`, and the
LLM-domain §A.11/Kronecker example in the highlight-spec comment → neutral math
example), and committed `444aeb0d` with subject carrying `from llm-zero-to-one`
(the inbound skip-guard key). The 28 affected specs pass on the branch off main.

Held for explicit user go-ahead per the `--back` safety rule (separate
`FenLinger/data-channel-receiver` remote); **on go-ahead (2026-07-05) pushed and
opened PR #36** — https://github.com/FenLinger/data-channel-receiver/pull/36.

## Alternatives considered

- **Commit into the current feature branch / reset `sync-from-llm-zero-to-one`.**
  Rejected: entangles the owner's WIP / destroys the prior enrich-equation
  sync-back's 6 unmerged commits.
- **`git switch -c` in the main (dirty) working tree.** Rejected: carries the
  owner's uncommitted changes onto the new branch; the worktree isolates cleanly.
- **Keep the byte-identical downstream comments (with bug IDs) upstream.** Rejected:
  R1 requires stripping HERE provenance; dangling downstream bug IDs reference
  records that do not exist in upstream's `bugs/`. Code stays convergent; only
  comment provenance differs (expected, symmetric to the inbound genericization).

## Consequences

- A clean 1-commit branch ready to push + PR against upstream `main` on go-ahead.
- On merge: advance `.claude/upstream-sync.json` high-water mark past it (R4) so the
  next INBOUND run does not re-detect the round-trip; the `from llm-zero-to-one`
  subject filter is the backstop.
- The disk edits in the main upstream working tree (`wcm-tdl-cdl-calibration`) are
  now redundant with this branch; they can be reverted once the PR lands (noted in
  the todo).

## Refs

- `todos/2026-07-05-land-viewer-fixes-upstream-via-back-sync.md` (this executes it)
- downstream commit `b8346d5`; bugs `2026-06-17-01`, `2026-06-19-01`
- upstream branch `sync-viewer-fixes-from-llm-zero-to-one` @ `444aeb0d`
- `.claude/commands/sync-upstream.md` (Reverse R0–R4)
