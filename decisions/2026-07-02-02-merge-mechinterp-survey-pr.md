---
id: 2026-07-02-02
title: Merge the mechanistic-interpretability survey PR (#1) via rebase; delete branch
status: accepted
date: 2026-07-02
plan: (none — operational)
---

## Context

PR #1 (`survey/mechanistic-interpretability` → `main`) is a purely-additive
deliverable (9771 insertions, 0 deletions): a complete 24-file standalone
mechanistic-interpretability survey plus an SAE fidelity–sparsity
reference-implementation study, 63 LFS PDFs, and supporting records. GitHub
reported it `MERGEABLE` / `CLEAN` against `origin/main`; the PR body documents a
green `/check-survey` (8 checks) and a 10-verifier citation audit. The user asked
to merge it to main. The repo allows all three merge methods
(`merge_commit`/`rebase`/`squash` all `true`); its history is strictly linear
(no merge bubbles); the PR carries 4 distinct, richly-messaged commits (survey ·
cross-link polish · 13th cross-link · SAE study).

This PR is a *different* body of work from the uncommitted
`surveys/llms-for-coding/appendix-i-mechanistic-interpretability.md` (the
`mi-coverage-gaps` appendix thread) sitting in the working tree — that was left
untouched.

## Decision

Rebase-merge on GitHub: `gh pr merge 1 --rebase --delete-branch`. This preserves
the 4 commits and keeps `main` linear, and deletes the merged remote branch.
Merge tip on `origin/main`: `82cf6cb`.

## Alternatives considered

- **Squash.** Rejected — collapses 4 genuinely-distinct logical units (survey /
  cross-link / SAE study) into one commit, losing granular history that the
  repo's rich-commit convention otherwise preserves.
- **Merge commit.** Rejected — introduces a merge bubble the repo's strictly
  linear history has never carried.
- **Local `git merge` into main.** Rejected — the working tree was dirty with a
  concurrent session's uncommitted files and untracked `download/*.pdf` that
  overlap the PR's now-tracked PDFs; a local merge would refuse or clobber them.
  A server-side merge leaves the local tree untouched.

## Consequences

- `origin/main` advanced to `82cf6cb`; the `survey/mechanistic-interpretability`
  branch is deleted.
- Local `main` was `[ahead 6, behind 4]` at merge time. **Reconciled the same
  session** (user go-ahead): stash-preserve → `git rebase origin/main` (replay
  the 6 local commits onto `82cf6cb`) → union-resolve the two INDEX conflicts →
  pop; `main` is now `[ahead 6]`, behind 0, linear, with all concurrent-session
  + untracked work preserved. Closed in
  `todos/2026-07-02-reconcile-local-main-post-mechinterp-merge.md`.
- Forecloses nothing; the merge is purely additive.

## Refs

- PR #1 (merge commit `82cf6cb`, merged 2026-07-02).
- `todos/2026-07-02-reconcile-local-main-post-mechinterp-merge.md`.
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 58.
