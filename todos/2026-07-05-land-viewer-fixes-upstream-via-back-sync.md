---
slug: land-viewer-fixes-upstream-via-back-sync
date_filed: 2026-07-05
status: in-progress
---

**Update 2026-07-05.** `/sync-upstream --back` prepared the branch
`sync-viewer-fixes-from-llm-zero-to-one` (@ `444aeb0d`) off upstream `main` in an
isolated worktree — 1 commit, 5 files, HERE provenance stripped, 28 affected specs
green on the branch. See decision `2026-07-05-02`.

**Pushed + PR opened 2026-07-05 (user go-ahead):** branch pushed to
`FenLinger/data-channel-receiver`; **PR #36** —
https://github.com/FenLinger/data-channel-receiver/pull/36. Remaining (R4, blocked
on the owner merging): (1) advance `.claude/upstream-sync.json` `last_synced_commit`
past the merge so the next INBOUND run doesn't re-detect the round-trip (the
`from llm-zero-to-one` subject filter is the backstop); (2) revert the now-redundant
disk edits in the owner's `wcm-tdl-cdl-calibration` working tree; (3) close this
todo. Stays `in-progress` until the PR merges.

# Land the three viewer fixes upstream via /sync-upstream --back

## Context

Backlog item #3 (2026-07-05) applied three viewer fixes to BOTH this repo and the
upstream `../data-channel-receiver/viewer/` copies, per the upstream-convergence
policy (decision `2026-06-17-01`, "viewer fixes land upstream first, then
re-sync"):

- `serve.js` — `/api/md/` isFile() EISDIR guard (bug `2026-06-17-01`).
- `viewer.js` — multi-span inline-math highlight branch SIDECAR→PLAIN_SPANNING_MATH
  (bug `2026-06-19-01`).
- `citation.spec.js` — T12 goto hardened to `domcontentloaded` + content wait.
- `multiroot-serve.spec.js` — new EISDIR regression test.
- `highlights-resolve-inline-math.spec.js` — repurposed precise-highlight assertion.

The **downstream** side is committed + pushed here (`b8346d5`). The **upstream**
edits are applied **on disk** (the two copies are byte-convergent now, so a future
inbound `/sync-upstream` will not reintroduce the bugs), but they are **NOT
committed** in `../data-channel-receiver`: that checkout is on an active feature
branch (`wcm-tdl-cdl-calibration`, remote `FenLinger/data-channel-receiver`) with
the owner's unrelated in-progress work (a modified `prompts/...conformance-review`
+ ~37 untracked telecom-research files). Committing into that branch would mix a
downstream-originated fix into someone else's WIP.

## What is left

1. Run `/sync-upstream --back` — it discovers generic improvements made HERE,
   strips LLM/AI provenance, branches `sync-from-llm-zero-to-one` off upstream
   `main` (NOT the active feature branch), and (on go-ahead) opens a PR to
   upstream carrying these five viewer-file deltas.
2. Alternatively, if the owner prefers, hand them the five-file patch to land on
   their own schedule.
3. Once landed upstream + merged, the disk edits in `../data-channel-receiver`
   become redundant with its history — no further action.

## Acceptance

The five viewer-file fixes exist in upstream `main` history (via the `--back` PR or
an equivalent owner-landed commit), and the two repos' viewer copies agree on these
branches with clean provenance (no uncommitted downstream-originated edits left
dangling in the upstream working tree).

## Refs

- this repo commit `b8346d5`; decision `2026-06-17-01` (convergence policy).
- bugs `2026-06-17-01`, `2026-06-19-01`; todos (closed) `fix-serve-api-md-eisdir-crash`,
  `port-multispan-highlight-fix-upstream`, `citation-t12-e2e-timeout`.
- `.claude/commands/sync-upstream.md` (`--back` outbound flow).
