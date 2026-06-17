---
id: 2026-06-17-01
title: "serve.js /api/md/<empty-or-dir> crashes the whole server process (unhandled EISDIR)"
severity: med
status: open
date: 2026-06-17
component: viewer/serve.js
plan: (viewer sync from data-channel-receiver)
---

## Symptom

A single malformed request to the markdown API kills the entire dev server
process. Reproduced live on the synced viewer:

```
$ node viewer/serve.js surveys/llms-for-coding -p 4601 &
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4601/api/md/index.md   # 200, fine
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4601/api/md/            # 502, and...
# server process exits:
Error: EISDIR: illegal operation on a directory, read
    at Object.readFileSync (node:fs:436:20)
    at readUtf8WithRevision (viewer/serve.js:209:19)
    at Server.<anonymous> (viewer/serve.js:584:23)
```

After the request the process is dead (`kill -0` fails) — every subsequent
request to the viewer fails until it is manually restarted. Any request whose
`/api/md/<id>` resolves to a directory (empty id, or a sub-path that is a
directory inside a content root) triggers it.

## Root cause

In the `/api/md/` handler the 404 guard checks existence but not file-type:

```js
const file = pathname.slice('/api/md/'.length);   // '' for /api/md/
const filePath = markdownPathFor(file);           // resolves to the content-root DIRECTORY
if (!filePath || !fs.existsSync(filePath)) { 404 } // dir EXISTS → guard passes
const current = readUtf8WithRevision(filePath);    // fs.readFileSync(dir,'utf8') → EISDIR throws
```

`readUtf8WithRevision` (`serve.js:208-211`) calls `fs.readFileSync` with no
`try/catch`, and the request handler does not wrap the call, so the exception
propagates to the top of the event loop and Node exits. The surface symptom
(a 502 on one request) hides the real mechanism (the listener died). This is
upstream code — the whole `serve.js` was synced from
`../data-channel-receiver/viewer`, and the defect exists there too.

## Fix

Not yet applied. Minimal fix: tighten the guard to require a regular file
(`!fs.statSync(filePath).isFile()` → 404) and/or wrap `readUtf8WithRevision`
in try/catch returning a 404/500 instead of throwing. Because `serve.js` is
synced verbatim from upstream, the durable fix belongs in
`../data-channel-receiver/viewer/serve.js` first, then re-synced here, to keep
the two copies convergent (see decision `2026-06-17-01`). **Deferred** by user
direction (2026-06-17) — tracked in `todos/2026-06-17-fix-serve-api-md-eisdir-crash.md`.

## Regression test

none yet — when fixed, add a viewer e2e/unit case: `GET /api/md/` and
`GET /api/md/<dir>` must return 404 (not 200/502) and the server must stay
alive for a subsequent request. Upstream `tests/` is now present and is the
natural home for it.

## Refs

- Surfaced by the boot-smoke arm of the verify-viewer-sync workflow
  (run `wf_78b6042c-f19`), then reproduced by hand.
- decision `2026-06-17-01` (viewer wholesale sync; upstream-convergence policy).
- conversation log `prompts/2026-06-17-viewer-sync.md` (Conversation 1).
