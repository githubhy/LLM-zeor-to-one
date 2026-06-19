---
date: 2026-06-19
slug: port-multispan-highlight-fix-upstream
status: open
---

# Port the multi-span inline-math highlight fix to the upstream viewer

## Context

Bug `2026-06-19-01`: highlighting a selection that starts inside an inline-math
span and ends in plain text after a second math span highlighted the whole
paragraph (it was routed to the whole-block sidecar backend). Fixed locally in
`viewer/viewer.js` by routing that case (`startKatex && !endKatex`,
`_nKatexM > 1`) to the `PLAIN_SPANNING_MATH` handler instead of `SIDECAR`, which
produces a precise inline `==color: …==` highlight.

`viewer/viewer.js` here is synced from `../data-channel-receiver/viewer/viewer.js`,
which carries the **identical** classification branch and therefore the
identical bug (confirmed: upstream lines ~4489-4491 also set `type = 'SIDECAR'`
for this case). Per the upstream-convergence policy (decision `2026-06-17-01`),
viewer fixes should live upstream first, then be re-synced, to keep the two
copies convergent.

## What is left

1. Apply the same classification change in
   `../data-channel-receiver/viewer/viewer.js` (route the
   `startKatex && !endKatex`, `_nKatexM > 1` branch to `PLAIN_SPANNING_MATH`,
   set `blockEl = startBlock`).
2. Port the regression-test update in
   `viewer/tests/highlights-resolve-inline-math.spec.js` (the bug
   `2026-06-02-04` test, now repurposed to assert the precise inline highlight)
   to the upstream test suite.
3. Re-sync upstream → here if any other drift exists, or simply confirm the two
   `viewer.js` copies agree on this branch.

## Acceptance

- Upstream `viewer.js` routes the multi-span start-in-katex case to
  `PLAIN_SPANNING_MATH`; upstream `highlights-resolve-inline-math.spec.js`
  asserts the precise-highlight behavior and passes.
- The local and upstream copies agree on this branch (no divergence introduced).

## Refs

- bug `2026-06-19-01-multispan-inline-math-whole-paragraph-highlight`.
- decision `2026-06-17-01` (viewer wholesale sync; upstream-convergence policy).
- conversation log `prompts/2026-06-17-viewer-sync.md`.
