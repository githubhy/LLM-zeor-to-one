# Conversation Log — 2026-06-29 — session: viewer-serve-launcher

## Conversation 1
- **Request**: Add a cross-platform script to fix `node viewer/serve.js -p 3500` crashing with `Error: Cannot find module 'ws'`.
- **Actions**: Diagnosed root cause — `viewer/node_modules` never installed (serve.js hard-requires `ws`). Added paired launchers `scripts/serve-viewer.sh` + `scripts/serve-viewer.ps1` (matching `install-git-hooks.{sh,ps1}` convention) that auto-install viewer deps on first run (canary = `node_modules/ws`; `npm ci` if lockfile else `npm install`), and default the content root to `surveys/` when none is given so a bare `-p <port>` works. Updated `viewer/GUIDE.md` (Install tip, Quick Start launcher block, troubleshooting row). Filed decision `2026-06-29-01`.
- **Result**: Verified end-to-end on both platforms — PowerShell launcher → HTTP 200 on :3598; bash launcher → HTTP 200 on :3597; `ws` installed; `node_modules` gitignored. Working tree adds only the two scripts (+ docs/decision/log).
- **Findings**: `serve.js` needs a content root and the repo ships no `viewer.content.json`, so even after the `ws` fix the user's bare `-p 3500` would hit "no content roots" — the launcher's default-to-`surveys/` closes that gap. `content-source.js` walks subdirs recursively, so `surveys/` surfaces all three surveys.

<!-- LOG-END -->
