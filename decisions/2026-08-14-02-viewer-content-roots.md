---
id: 2026-08-14-02
title: Add viewer.content.json with a locally-curated root list
status: accepted
date: 2026-08-14
---

## Context

`viewer/serve.js` has supported multi-root content config since the viewer was ported —
`loadContentConfig()` walks up from cwd looking for `viewer.content.json`, and with no
config and no positional argument it exits with *"no content roots"*. The file itself was
never ported: `/sync-upstream` listed it under **still out of scope**, reasoning that the
root list is domain-specific.

That reasoning was right about the *contents* and wrong about the *file*. The consequence
was an imported-but-unused feature: the viewer had to be started against the repo root,
which serves every directory including the records-style audit trail, and gives no labels.

Asked directly ("where is viewer.content.json?") during a study session, which is how the
gap surfaced.

## Decision

Add `viewer.content.json` with a root list curated for **this** repo: `surveys`, `wikis`,
`docs`, `reports`, `plans`, `field-notes`, `bench`.

Excluded, and why:

- **`prompts/` `todos/` `decisions/` `bugs/`** — records-style. They are an audit trail
  read through git and their `INDEX.md` files, not reader prose. This mirrors upstream's
  own exclusion.
- **`implementation/`** — code, not prose.
- `download/` `temp/` `node_modules/` `viewer/` — already excluded by `serve.js`'s
  built-in defaults; listing them would be noise.

`plans/` is included where upstream excludes it: upstream's cut is "records-style dirs
out", and `plans/` here has no `INDEX.md`, no ID scheme, and is prose that gets re-read.

## Alternatives considered

- **Copy upstream's file** — rejected outright; its roots include `proposals/` and
  `theories/`, which do not exist here, and `serve.js` calls `usageExit` on a missing
  config root, so it would not have started.
- **Leave it absent and keep passing a directory** — rejected. It is the status quo, it
  serves the capture directories to the reader, and it leaves a supported `serve.js` code
  path permanently dead.
- **Include `implementation/`** — rejected. Eight code packages; any prose in them is
  README-shaped and reachable from the reports that cite it.

## Consequences

- `node viewer/serve.js` with no arguments now works and serves 7 labelled, namespaced
  roots. Verified: all 7 resolve at startup.
- **Obliges a sync-rule change, made in the same turn.** `/sync-upstream` said this file
  was out of scope; left alone, the next inbound sync would have re-asserted that against
  a file that now exists. It is now listed with `.gitignore` / `.viewerignore` as a
  **surgical-merge** target: port schema changes, never upstream's root list.
- A new content directory is not served until it is added here — the cost of curation.
  Acceptable: the file is 15 lines and the failure is loud (`usageExit`), not silent.

## Refs

- `viewer.content.json`, `viewer/serve.js:62-104` (`loadContentConfig`, root resolution).
- `.claude/commands/sync-upstream.md` — the out-of-scope list this decision amends.
- `.viewerignore` — the within-root exclude list this file names via `ignoreFile`.
