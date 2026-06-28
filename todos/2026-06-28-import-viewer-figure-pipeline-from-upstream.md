---
slug: import-viewer-figure-pipeline-from-upstream
date_filed: 2026-06-28
status: closed
---

**Resolution (2026-06-28).** All three viewer non-config deltas imported, re-adapted, and green:
- **figure-pipeline subsystem** (upstream `c0595cb`): `viewer/lib/figure-pipeline.js` (new), the
  `viewer.js` progressive-enhancement + chip + palette + settings wiring, `serve.js` `/artifacts/`
  asset-route upgrade (this repo was two changes behind — also gained the bug-2026-06-25-01
  `/figures/` deep-path support), `settings-store.js` `figureStyle` key, `index.html` settings group
  + script tag, `.gitignore` `.claude/.tmp/`. The embedded demo `SPEC` was re-domained
  pitch→LLM (scaled dot-product attention pipeline) across `figure-pipeline.js`, the unit test, and
  the e2e spec. Tests: `figure-pipeline.test.js` + `figure-style-setting.test.js` (unit, 12) and
  `figure-style.spec.js` + `figure-asset-serving.spec.js` (e2e, 9) all pass; full unit suite 298/298.
- **sionna viewer gates** (upstream `942cda0` + `7377c89`): scroll-containment
  (`overscroll-behavior:contain` ×10 in `style.css` + `trapRegionScroll`/`setupScrollTraps` in
  `viewer.js`) and anchor-landing (`scrollToAnchor` `block:'center'`→`'start'`), plus the
  `scroll-containment.spec.js` (new) and the behavioral extension of `anchor-landing.spec.js`.

Registered figure: `FIGURE_REGISTRY = { 'pipeline-figure': true }` + sibling `spec.json` convention.
See `decisions/2026-06-28-03-import-viewer-figure-pipeline-and-sionna-gates.md`.

# Import viewer (non-config) deltas from upstream main: figure-pipeline.js + sionna viewer test gates

## Context

The 2026-06-28 `/sync-upstream` (inbound) covers only **config paths** (`CLAUDE.md`,
`AGENTS.md`, `.claude`, `viewer/tools`, `.githooks`, `scripts`, `requirements.txt`). Upstream
`origin/main` (9b118d3) advanced via two merged sibling PRs whose changes are in `viewer/`
(application code), **out of the config-sync scope**, so they were NOT imported:

- **`viewer/lib/figure-pipeline.js`** (upstream PR #14, from pitch-perfector) — a spec-driven
  figure renderer + style switcher: a marked `![alt](fig.png "id")` is progressively enhanced
  into a live, reflowing, style-switchable block-diagram figure (colour-academic / monochrome
  / minimal / swimlane / static-image), driven by a `figureStyle` setting (settings sheet,
  inline chip, palette commands); GitHub/no-JS keep the PNG fallback. Plus `viewer/serve.js`
  serving deep-path `.html/.pdf/.json` under `artifacts/` + figures, and its unit/e2e tests.
- **sionna viewer regression gates** (upstream PR #13, commits `942cda0` + `7377c89`) — the
  generic viewer fixes + regression tests synced from the `sionna` sibling.

This repo lacks `viewer/lib/figure-pipeline.js` entirely.

## What is left

- Decide whether to import the figure-pipeline subsystem (it is a real, generic viewer
  capability) and the sionna viewer gates via a **viewer wholesale-sync** (the mechanism in
  `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md`), re-adapting any domain
  examples LLM-ward and registering figures via `FIGURE_REGISTRY` + per-figure `spec.json`.
- If imported, port the accompanying unit + e2e tests and run them green.

## Acceptance

Either: `viewer/lib/figure-pipeline.js` + `serve.js` artifacts route + tests imported,
re-adapted, and green here; OR a decision recorded to keep the viewer behind upstream on this
subsystem (close as wontfix with reason).

## Refs

- Upstream `origin/main` 9b118d3 (PRs #13, #14 merged); commits `c0595cb`, `942cda0`, `7377c89`.
- `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md` (the viewer-sync mechanism).
- `decisions/2026-06-28-01-catch-up-import-from-pitch-perfector.md`.
- `.claude/upstream-sync.json` (config mark = 9b118d3; this is the non-config remainder).
