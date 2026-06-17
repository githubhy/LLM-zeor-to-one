# Fix serve.js /api/md/<empty-or-dir> EISDIR crash (upstream + re-sync)

status: open

## Context

During the 2026-06-17 viewer sync from `../data-channel-receiver`, the
boot-smoke verification surfaced a real defect (bug `2026-06-17-01`): a single
malformed `GET /api/md/` (empty id) — or any `/api/md/<id>` resolving to a
directory — passes the handler's `fs.existsSync` 404 guard (directories
exist), then `readUtf8WithRevision` calls `fs.readFileSync(dir, 'utf8')` which
throws an uncaught `EISDIR`, **terminating the dev-server process**. Reproduced
live. The code is synced verbatim from upstream, so the defect exists in
`../data-channel-receiver/viewer/serve.js` too.

User decision (this session): **defer** the fix rather than patch locally or
edit upstream now, to keep this repo's `serve.js` byte-convergent with upstream
(per decision `2026-06-17-01`'s convergence policy — viewer code fixes land
upstream first, then re-sync).

## What is left

1. In `../data-channel-receiver/viewer/serve.js`, tighten the `/api/md/`
   handler: treat a non-regular-file target as 404 (e.g.
   `if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) → 404`),
   and/or wrap `readUtf8WithRevision` (≈`serve.js:208-211`) in try/catch
   returning 404/500 instead of throwing.
2. Add a regression test in upstream `viewer/tests/`: `GET /api/md/` and
   `GET /api/md/<dir>` return 404 and the server stays alive for a subsequent
   request.
3. Re-sync `serve.js` (and the new test) into this repo via the same
   `rsync` flow used on 2026-06-17; re-run `/check-survey`-equivalent + a boot
   smoke to confirm green.

## Acceptance

- `GET /api/md/` and `GET /api/md/<dir>` → HTTP 404, **server process survives**
  and serves a subsequent request.
- Regression test present in `viewer/tests/` and passing on both repos.
- This repo's `viewer/serve.js` remains byte-identical to upstream's.

## Refs

- bug `bugs/2026-06-17-01-serve-api-md-eisdir-crash.md`
- decision `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md`
- conversation log `prompts/2026-06-17-viewer-sync.md` (Conversation 1)
