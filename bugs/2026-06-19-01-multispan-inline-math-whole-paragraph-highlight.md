---
id: 2026-06-19-01
title: "Highlighting a span that starts inside inline math and crosses a second math span highlights the whole paragraph"
severity: med
status: fixed
date: 2026-06-19
component: viewer/viewer.js
plan: (viewer sync from data-channel-receiver)
---

## Symptom

In the reader, selecting and highlighting the span
`$\delta_{jm}$ the Kronecker delta (1 when $j=m$, else 0)` in
`surveys/llms-for-coding/appendix-a-qkv-first-principles.md` section A.11 (the
eq-(11) lead-in) highlights the **entire paragraph** instead of just the selected text.
Reproduces for any selection that starts *inside* an inline-math span and ends
in plain text *after* at least one additional inline-math span.

## Root cause

`applyHighlight()` classifies the selection (viewer.js ~4380-4431). For a
selection whose start is inside a katex span and whose end is outside
(`startKatex && !endKatex`), it counts the katex spans in the selection; when
more than one is spanned (`_nKatexM > 1`) it set `type = 'SIDECAR'`. The sidecar
backend stores a `block-range` segment (`sidecarSegmentsFromRange`), i.e. it
paints whole blocks by source line — so the whole paragraph lights up.

That sidecar route was a deliberate workaround (bug `2026-06-02-04`): the
single-math `MIXED_MATH_TEXT` handler (Step 5M) only reconstructs one math span,
so a multi-span selection produced a "Could not locate highlight in source"
toast; whole-block highlighting was chosen as the lesser evil. But the workaround
used the wrong handler. The multi-span `PLAIN_SPANNING_MATH` handler (Step 5P)
already reconstructs a precise source span across *every* spanned inline math,
and when the range starts inside the first katex its `plainHead` range collapses
to `''` (the end-before-start rule), so `selStart` correctly anchors at that
math's source offset. The sibling branch `!startKatex && endKatex` with
`nKatex > 1` was already routed to Step 5P — the `startKatex` branch routing to
sidecar was the inconsistency.

## Fix

In the `startKatex && !endKatex`, `_nKatexM > 1` branch, route to
`type = 'PLAIN_SPANNING_MATH'` (set `blockEl = startBlock`) instead of
`'SIDECAR'`. Step 5P then writes a precise `==color: …==` inline highlight that
begins at the first spanned math and ends at the plain-text tail, covering the
inter-math text and the second math span — not the whole paragraph. Confirmed
empirically: no "Could not locate" toast, no page errors, no sidecar entry, and
a precise `==blue: …==` wrap in source. Commit: (uncommitted at time of writing).

This is synced-from-upstream code; `../data-channel-receiver/viewer/viewer.js`
carries the identical branch and the identical bug. Per the upstream-convergence
policy (decision `2026-06-17-01`), the durable fix belongs upstream first, then
re-synced — the local fix here should be ported back to keep the two copies
convergent. Tracked in `todos/2026-06-19-port-multispan-highlight-fix-upstream.md`.

## Regression test

`viewer/tests/highlights-resolve-inline-math.spec.js` — the existing bug
`2026-06-02-04` test (which asserted the whole-block sidecar fallback) was
repurposed to assert the new precise behavior: a selection that starts inside
the first inline-math span and ends after a second span now writes a precise
`==blue: …==` inline wrap (`Edge-wise ` stays outside the open, ` gives the
bound.` stays outside the close), with no sidecar entry. Test renamed and
re-pointed at this bug id; the 7-math-span Step 5P test continues to pass.

## Refs

- viewer.js classification branch (`applyHighlight`, the `startKatex && !endKatex`
  multi-span case) and Step 5P `PLAIN_SPANNING_MATH` handler.
- Supersedes the sidecar workaround of bug `2026-06-02-04` for this case.
- decision `2026-06-17-01` (viewer wholesale sync; upstream-convergence policy).
- todo `2026-06-19-port-multispan-highlight-fix-upstream` (port to upstream).
- conversation log `prompts/2026-06-17-viewer-sync.md`.
