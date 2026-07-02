---
slug: fix-prepush-hook-wiring
date_filed: 2026-07-02
status: open
---

# Re-wire the pre-push gate so validation AND git-lfs both run

## Context

The documented pre-push validation gate is dormant: `core.hooksPath` is unset and
`.git/hooks/pre-push` is git-lfs's hook (see bug `2026-07-02-03`). Setting
`core.hooksPath .githooks` as `CLAUDE.md` describes would fix validation but
break LFS upload, because `.githooks/pre-push` does not chain
`git lfs pre-push`. The two gates currently cannot coexist.

## What is left

- Make `.githooks/pre-push` delegate to git-lfs — add `git lfs pre-push "$@"`
  (guarded by a `command -v git-lfs` check, mirroring the stock git-lfs hook) so
  LFS objects still upload when the validation hook is the active one.
- Then activate `git config core.hooksPath .githooks` and confirm a real push
  both uploads pending LFS blobs and runs the validators (block on error).
- Mirror the delegation in `scripts/install-git-hooks.sh` / `.ps1` (the
  copy-installer path) so both wiring mechanisms stay consistent.
- Consider a guard/test asserting the active pre-push hook runs both.
- Note the git-bash `python3`/`python` Store-stub issue: the hook uses `python3`
  (exit 49 against the stub) — document (or shim) the real interpreter so the
  gate does not silently no-op on a fresh Windows clone.

## Acceptance

A `git push` on a clone set up per the README both (a) uploads pending LFS
objects and (b) runs the survey-wide validators, blocking on error.
`core.hooksPath` is set and the documented state matches reality.

## Refs

- Bug `2026-07-02-03`; `CLAUDE.md` "Validation Hooks"; `.githooks/pre-push`;
  `scripts/install-git-hooks.sh`.
