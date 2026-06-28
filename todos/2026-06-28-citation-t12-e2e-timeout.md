---
slug: citation-t12-e2e-timeout
date_filed: 2026-06-28
status: open
---

# Investigate pre-existing citation T12 e2e timeout (page.goto "load" never settles)

## Context

While regression-testing the asset-link fix (`bugs/2026-06-28-01`), the viewer e2e test
`viewer/tests/citation.spec.js:452` — "T12: settings panel radio persists citation mode to
localStorage and survives reload" — failed with `Test timeout of 30000ms exceeded` at
`page.goto('http://localhost:<port>?file=doc.md', waiting until "load")` (base port 5100).
It fails **identically with the asset-link fix stashed out**, so it is *not* a regression from
that change — it is pre-existing, and most likely environmental (seen under local load from
repeated back-to-back Playwright runs + a dev server already bound on :6500). The two
heading-anchor "Bug B" tests that also failed in the same sweep passed on isolated re-run
(load-induced flake).

## What is left

- Reproduce on a clean machine / single-spec run with no other server bound; confirm whether
  it is purely environmental (resource/load) or a real defect (e.g. the `load` event never
  firing for this fixture, a missing slash in `http://localhost:${port}?file=doc.md` vs the
  `/?file=` form other specs use, or a settings-panel asset that stalls `load`).
- If real: fix the test (or the viewer) so `load` settles; if environmental only: consider
  `waitUntil: 'domcontentloaded'` or raising the per-nav timeout for this spec.

## Acceptance

`npx playwright test citation.spec.js -g "T12"` passes deterministically in a clean run; root
cause recorded (env vs defect).

## Refs

- `viewer/tests/citation.spec.js:452`
- `bugs/2026-06-28-01-viewer-relative-asset-links-404.md` (Regression test section)
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 10)
