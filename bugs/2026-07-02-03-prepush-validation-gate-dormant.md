---
id: 2026-07-02-03
title: Pre-push validation gate dormant — git-lfs hook holds .git/hooks/pre-push, core.hooksPath unset
severity: med
status: fixed
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

**Fixed 2026-07-03.** Rewrote `.githooks/pre-push` to (a) chain
`git lfs pre-push "$@"` up front (guarded by `command -v git-lfs`) so LFS objects
still upload when this hook is the active pre-push hook, and (b) auto-detect a
working python (`python3` → `python` → `py -3`) — git-bash's `python3` is the
Store stub, so without this the validators silently no-op on Windows. Then set
`git config core.hooksPath .githooks`. Because `core.hooksPath` makes git read
`.githooks/pre-push` directly, a later `git lfs install` overwriting
`.git/hooks/pre-push` no longer disables validation (the original failure mode is
structurally closed). The install-git-hooks copy-installer needs no change — it
copies the now-self-contained hook.

## Regression test

A live `git push` with `core.hooksPath=.githooks` runs both `git lfs pre-push`
(LFS upload) and the survey validators (verified). Standalone dry-run:
`bash .githooks/pre-push origin <url> < /dev/null` — LFS no-ops on empty stdin,
validators run, exit 0.

## Refs

- Discovered: conversation log `prompts/2026-06-29-viewer-serve-launcher.md`
  Conversation 60.
- Fix todo: `todos/2026-07-02-fix-prepush-hook-wiring.md`.
- `CLAUDE.md` "Validation Hooks" (documents `core.hooksPath .githooks` as the
  active wiring); `.githooks/pre-push`; `scripts/install-git-hooks.sh`.
