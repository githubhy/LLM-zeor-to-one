---
id: 2026-06-29-01
title: Cross-platform viewer launcher (serve-viewer.sh/.ps1) — auto-install deps + default content root
status: accepted
date: 2026-06-29
plan: n/a (direct request)
---

## Context

Running `node viewer/serve.js -p 3500` from a fresh clone crashes with
`Error: Cannot find module 'ws'`: `viewer/` declares `ws`/`chokidar`/`ignore` in
`package.json` and `serve.js` hard-`require`s `ws` at module load, but
`viewer/node_modules` had never been installed (the documented `cd viewer && npm
install` step was skipped). The user asked for a *cross-platform* script to solve
this. Two adjacent ambiguities surfaced: (a) even with deps installed, the bare
`-p 3500` form has no content root and `serve.js` aborts with "no content roots";
(b) install mechanism (`npm install` vs `npm ci`).

## Decision

Add a paired `scripts/serve-viewer.sh` + `scripts/serve-viewer.ps1` launcher
(matching the repo's existing `install-git-hooks.{sh,ps1}` convention) that:
(1) installs `viewer/` deps on first run, keyed on `node_modules/ws` as the
canary (`npm ci` when a lockfile is present, else `npm install`); (2) detects
whether the caller named a content root (positional dir/file, `--root`, or
`--config`) and, if not, defaults to serving the repo's `surveys/` directory so a
bare `-p <port>` invocation works; (3) forwards all other args verbatim and
leaves CWD untouched so relative paths resolve exactly as `serve.js` documents.

## Alternatives considered

- **Pure pass-through wrapper (no default root).** Rejected: the user's literal
  `-p 3500` command would still fail with "no content roots" — only half the
  problem solved.
- **A root-level `npm` script / Makefile.** Rejected: `npm run` needs an
  installed npm context and a Makefile isn't native on Windows; the `.sh`/`.ps1`
  pair is the established cross-platform idiom here.
- **Default to one specific survey (e.g. `surveys/llms-for-coding`).** Rejected:
  opinionated and rot-prone; `content-source.js` walks subdirectories
  recursively, so `surveys/` cleanly surfaces all three surveys.
- **`npm ci` unconditionally.** Rejected as the sole path: `npm ci` requires a
  lockfile; fall back to `npm install` when absent.

## Consequences

- The user's exact `-p 3500` workflow now works on first run on both platforms
  (verified: HTTP 200 on a probe port via both launchers).
- `serve.js`'s own contract is unchanged; the default-root behavior lives only in
  the wrappers. Calling `serve.js` directly still requires an explicit root.
- GUIDE.md updated (Install tip, Quick Start launcher block, troubleshooting row
  for the `ws` error). No `todos/` follow-up.

## Refs

- Files: `scripts/serve-viewer.sh`, `scripts/serve-viewer.ps1`, `viewer/GUIDE.md`
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 1
- Convention precedent: `scripts/install-git-hooks.{sh,ps1}`
