---
id: 2026-06-28-06
title: Broaden /sync-upstream inbound scope to include the viewer application
status: accepted
date: 2026-06-28
plan: none (direct user request)
---

## Context

`/sync-upstream` inbound was **config-path scoped** — `CLAUDE.md`, `AGENTS.md`, `.claude/**`,
`viewer/tools/**`, `.githooks/**`, `scripts/**`, `requirements.txt` — and **deliberately
excluded** the viewer *application* code (`viewer/serve.js`, `viewer.js`, `lib/**`, `style.css`,
`index.html`, tests). Viewer app code was handled by a *separate* mechanism: the "viewer
wholesale sync" (`decisions/2026-06-17-01`) and ad-hoc imports (`decisions/2026-06-28-03`
figure-pipeline). This asymmetry is why yesterday's config sync did not carry the serve.js
serving-folder expansion (it came via the separate figure-pipeline import). The outbound
`--back` sweep, by contrast, already listed viewer app paths — so the two directions were
asymmetric on viewer.

The user asked to "put all viewer related things into the /sync-upstream skill."

## Decision

Fold the **whole viewer app** into the inbound scope via a single `viewer` pathspec
(`viewer/**`; gitignored `node_modules/`, `test-results/`, `.viewer-highlights/` auto-excluded
from the tracked-file diff). The viewer *framework* (server, client JS, `lib/**`, styles, PWA,
test harness) is domain-agnostic and applies **directly** like `viewer/tools/`; only **embedded
content** (demo SPECs, test fixtures, deploy identifiers) is re-adapted, and **local divergences
are preserved via surgical seam edits** (never wholesale overwrite). The previously-separate
wholesale-sync is demoted to a bootstrap/recovery fallback. Added a "Viewer application code"
handling subsection, a `node --check` + `npm --prefix viewer test` / playwright gate, and
extended the leakage grep to `viewer/` (excluding `node_modules`/`vendor`/`test-results`).

## Alternatives considered

- **Keep viewer app out; rely on the separate wholesale-sync.** Rejected: the user asked to
  fold it in, and the asymmetry (outbound already swept viewer) was a latent trap — an inbound
  run silently skipped real viewer deltas (the serve.js gap was a concrete instance).
- **Enumerate a hand-picked subset of viewer files.** Rejected: brittle (misses new files like a
  future `lib/*.js`); `viewer/**` minus gitignored is the clean, future-proof boundary.
- **Auto-overwrite viewer files from upstream.** Rejected: clobbers local divergences (e.g. the
  multi-span-highlight fix) and domain-adapted fixtures/demos — the exact failure the surgical
  seam-edit rule prevents.

## Consequences

- Viewer app deltas are now caught incrementally by `/sync-upstream` (one mechanism, symmetric
  with `--back`), not a forgotten separate step.
- The leakage grep + viewer test suite gate viewer ports; a viewer delta is not "ported" until
  tests are green here with re-adapted fixtures.
- Other infrastructure paths remain **out of scope pending the user's decision** — tracked in
  `todos/2026-06-28-sync-upstream-scope-candidates.md` (CI `.github/workflows` + `.claude-sync.yml`,
  `.gitignore`, `.viewerignore`, `viewer.content.json`/`manifest.json`, `bench/`, top-level `tools/`).

## Refs

- `.claude/commands/sync-upstream.md` (intro, §1 scope, §2 viewer-app subsection, §3 gate, §4 commit msg)
- `CLAUDE.md` (sync-upstream catalog entry); `.claude/upstream-sync.json` (note)
- Supersedes the viewer-exclusion premise of `decisions/2026-06-17-01` (wholesale-sync now fallback)
  and the closed `todos/2026-06-28-import-viewer-figure-pipeline-from-upstream.md`
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 8)
