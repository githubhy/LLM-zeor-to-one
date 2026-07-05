---
id: 2026-06-17-01
title: "serve.js /api/md/<empty-or-dir> crashes the whole server process (unhandled EISDIR)"
severity: med
status: fixed
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

Applied 2026-07-05 (on the Mac host, where `../data-channel-receiver` is checked
out — the blocker in `todos/2026-07-03-blocked-backlog-consolidated.md`). The
`/api/md/` 404 guard now requires a regular file:

```js
if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
  res.writeHead(404); res.end('Not found'); return;
}
```

Any directory (or empty-id) target now returns a clean 404 instead of reaching
`fs.readFileSync(dir)` → EISDIR. Because the handler was byte-identical in both
copies, the same edit was applied in place to **both** `viewer/serve.js` and
`../data-channel-receiver/viewer/serve.js` (a surgical same-edit rather than a
wholesale re-sync, which would have clobbered the local `artifacts/` figure-asset
divergence). The handler region is now byte-convergent across the two repos; the
only remaining serve.js divergence is the intended local `artifacts/` addition.
Commit: (this session).

## Regression test

`viewer/tests/multiroot-serve.spec.js` — new case "a directory (or empty)
markdown id returns 404 and does NOT crash the server (EISDIR guard)": `GET
/api/md/roota/sub` (a real dir in the fixture) and `GET /api/md/` both return
404, then a normal `GET /api/md/roota/a.md` still 200s (server survived).
**Proven red-without-fix**: with the `isFile()` check removed, the `roota/sub`
request throws (server crashed) — the test fails exactly at that request.
Added to both repos' spec (byte-convergent). All 10 multiroot-serve tests pass.

## Refs

- Surfaced by the boot-smoke arm of the verify-viewer-sync workflow
  (run `wf_78b6042c-f19`), then reproduced by hand.
- decision `2026-06-17-01` (viewer wholesale sync; upstream-convergence policy).
- conversation log `prompts/2026-06-17-viewer-sync.md` (Conversation 1).
