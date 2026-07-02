---
id: 2026-07-02-03
title: Pre-push validation gate dormant — git-lfs hook holds .git/hooks/pre-push, core.hooksPath unset
severity: med
status: open
date: 2026-07-02
component: git-hooks / validation
plan: (none — infra)
---

## Symptom

`CLAUDE.md` documents the survey-wide pre-push validation gate
(`.githooks/pre-push`) as **active**, wired via
`git config core.hooksPath .githooks`. In this clone it does not run on
`git push`:

- `git config --show-origin --get-all core.hooksPath` → **unset** (all scopes).
- `.git/hooks/pre-push` exists but is the stock **git-lfs** hook
  (`git lfs pre-push "$@"`), dated 2026-06-29 — not the validation gate.

So a `git push` uploads LFS objects (git-lfs hook fires) but never runs
`validate-refs` / renumber `--check` / bare-refs / crosslink. Discovered while
pushing the Appendix I + local-main-reconcile commits (2026-07-02); the push was
validated manually instead (all 4 survey dirs green).

## Root cause

Two mutually-exclusive claimants on the single pre-push slot:

1. `git lfs install` (run ~2026-06-29) wrote git-lfs's hook to
   `.git/hooks/pre-push`, overwriting whatever was there (including a
   copy-installed validation hook, if `scripts/install-git-hooks.sh` had ever
   placed one).
2. `core.hooksPath` — the documented wiring that would point git at
   `.githooks/` — is unset, so `.githooks/pre-push` is never consulted.

Deeper design conflict: **the two gates cannot both run as currently written.**
`.githooks/pre-push` does *not* chain `git lfs pre-push`, so naively "fixing" the
config with `git config core.hooksPath .githooks` would make git read the
validation hook and **silently stop uploading LFS objects on push** — trading a
dormant validation gate for broken LFS transfer (pointers pushed without their
blobs). That is why this push deliberately left `core.hooksPath` unset and
validated by hand.

## Fix

Deferred — re-wiring is a design choice, tracked in
`todos/2026-07-02-fix-prepush-hook-wiring.md`. Sketch: make `.githooks/pre-push`
chain `git lfs pre-push "$@"` (guarded by a `command -v git-lfs` check, as the
stock git-lfs hook does) so both LFS upload and validation run, then set
`core.hooksPath .githooks`. Until then, run `/check-survey` (or the manual
validators, invoked with the real `…/Python313/python.exe`, since git-bash
`python3` is the Store stub) before every push.

## Regression test

none yet — will be a hook-presence assertion once the wiring is fixed (verify a
`git push` invokes both `git lfs pre-push` and the survey validators).

## Refs

- Discovered: conversation log `prompts/2026-06-29-viewer-serve-launcher.md`
  Conversation 60.
- Fix todo: `todos/2026-07-02-fix-prepush-hook-wiring.md`.
- `CLAUDE.md` "Validation Hooks" (documents `core.hooksPath .githooks` as the
  active wiring); `.githooks/pre-push`; `scripts/install-git-hooks.sh`.
