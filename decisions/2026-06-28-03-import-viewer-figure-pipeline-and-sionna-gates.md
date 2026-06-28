---
id: 2026-06-28-03
title: Import the viewer figure-pipeline subsystem + sionna scroll/anchor gates from upstream
status: accepted
date: 2026-06-28
plan: null
---

## Context

The 2026-06-28 inbound `/sync-upstream` covered only config paths; upstream `origin/main`
(9b118d3) carried viewer **application-code** deltas left out of scope and filed as
`todos/2026-06-28-import-viewer-figure-pipeline-from-upstream.md`. The user then asked to
**finish** that deferral. Three upstream changes were involved:

- `c0595cb` — spec-driven figure renderer (`viewer/lib/figure-pipeline.js`) + the `viewer.js`
  progressive-enhancement / chip / palette / settings wiring, the `serve.js` `/artifacts/`
  asset-route extension, the `settings-store.js` `figureStyle` key, `index.html`, `.gitignore`,
  and 4 test files. (The hooks half of `c0595cb` was already imported in the inbound sync.)
- `942cda0` + `7377c89` — two generic "sionna" viewer fixes (scroll-containment via
  `overscroll-behavior:contain` + a `trapRegionScroll` wheel trap; anchor-landing via
  `scrollToAnchor` `block:'center'`→`'start'`) and their regression specs.

Two realities shaped the port: (1) this repo's `viewer.js`/`serve.js` have **diverged** from
upstream (local multi-span-highlight fix; the repo was also two changes behind on `serve.js`,
lacking even the bug-2026-06-25-01 `/figures/` deep-path support), so a wholesale file copy was
out — hunks had to be applied at stable anchors. (2) `figure-pipeline.js` and its tests embed a
**demo figure SPEC** that was pitch/audio-domain (`Frame-F0 selection`, `x[n]/audio`, `note events`).

## Decision

Port all three deltas by **applying the upstream hunks at anchors** (not wholesale copy),
re-domaining the embedded demo SPEC pitch→LLM to the **scaled dot-product attention pipeline**
(QKV projection → Scores → Scaled-softmax [highlighted] → Weighted-sum → Output-projection;
input `x/tokens` → output `context`), consistently across `figure-pipeline.js`, the unit test, and
the e2e spec. `serve.js` got the full current upstream asset-route block (closing the two-change gap
in one edit). The sionna `style.css` hunk applied cleanly (in-sync base); `anchor-landing.spec.js`
was upgraded to the `7377c89` version (its first 82 lines were identical; only the behavioral
`block:'start'` test was appended).

## Alternatives considered

- **Wholesale-copy the upstream viewer files** — rejected: clobbers this repo's local
  multi-span-highlight fix and any LLM retargeting; the divergence is real, anchors are the safe unit.
- **Keep the demo SPEC pitch-domain** — rejected: leaves MIR leakage (`Frame-F0`, `audio`) in a
  shipped viewer file; the `/sync-upstream` contract is to re-domain examples, never carry them.
- **Split the sionna gates into a residual todo, close only figure-pipeline** — rejected: they live
  in the same todo, are small, domain-clean, and apply to in-sync anchors; finishing them gives a
  clean, residual-free close, which is what "finish the deferral" means.
- **Skip the `serve.js` two-change catch-up** — rejected: the figure e2e fixtures serve `spec.json`
  from an `/artifacts/` path, so the asset-route upgrade is load-bearing for the tests.

## Consequences

- Enables: spec-driven, style-switchable figures in the viewer (register an id in `FIGURE_REGISTRY`
  + ship a sibling `spec.json`); no-overscroll-chaining chrome regions; topbar-clearing anchor jumps.
- Verification: full unit suite **298/298**; e2e **figure-style 5/5, figure-asset-serving 4/4,
  anchor-landing 4/4, scroll-containment 2/2** (one combined-run `page.goto` timeout on a pre-existing
  CSS-only test proved flaky — passed on isolated re-run). Leakage-clean.
- Follow-up: none. The viewer non-config import todo is closed with no residual.

## Refs

- Upstream commits `c0595cb`, `942cda0`, `7377c89` (data-channel-receiver `origin/main` 9b118d3).
- `todos/2026-06-28-import-viewer-figure-pipeline-from-upstream.md` (closed).
- `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md` (the viewer-sync precedent).
- `decisions/2026-06-28-01` (the catch-up import that deferred this).
