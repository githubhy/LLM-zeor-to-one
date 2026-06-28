---
id: 2026-06-28-01
title: Relative asset links (e.g. a link to figures/*.svg) 404 in the viewer SPA — href not rewritten to the doc dir
severity: med
status: fixed
date: 2026-06-28
component: viewer (viewer.js client render)
plan: none
---

## Symptom

The Figure A.1 caption in `appendix-a-qkv-first-principles.md` links the alternative view as
`[canonical scaled-dot-product-attention block](figures/qkv-head-parameters-alt.svg)`. Clicking
it in the viewer navigated to `http://localhost:6500/figures/qkv-head-parameters-alt.svg` → **404**.

Reproduced via curl against the running dev server:

```
404  /figures/qkv-head-parameters-alt.svg                              # root /figures/ — 404
404  /figures/qkv-head-parameters.svg                                  # same, even the main figure
200  /surveys/llms-for-coding/figures/qkv-head-parameters-alt.svg      # the real served path
200  /surveys/llms-for-coding/figures/qkv-head-parameters.svg
```

The *embedded* figure renders fine; only the markdown *link* to an asset 404s.

## Root cause

The viewer is an SPA served at root with the doc loaded via `?file=<path>.md`, so any relative
URL in the rendered DOM resolves against the **root** page URL. `fixRelativePaths()` (viewer.js)
rewrote embedded image `src` to the doc-dir-absolute `/${dir}/${src}` (which is why images work)
but did **not** rewrite anchor `href`s. A relative asset link therefore stayed relative
(`figures/x.svg`) and the browser resolved it to `/figures/x.svg`. serve.js's `/figures/` asset
route then calls `assetPathFor('figures/x.svg')`, which probes `<assetRoot>/figures/x.svg` for
each root — none match, because the file lives at `surveys/llms-for-coding/figures/x.svg`. → 404.
The click handler only intercepts `#`, `.md`, and `http(s):` links, so the asset link fell
through to default (broken) navigation. The same gap existed in `renderSplitContent()` (the
compare pane). Surfaced by the Figure A.1 alt-view link added in this session.

## Fix

Extend `fixRelativePaths()` and `renderSplitContent()` to rewrite relative `a[href]` to
`/${dir}/${href}` — symmetric with the existing `img[src]` rewrite — for links that are not
`#`-anchors, not already absolute, not scheme links (`http:`/`mailto:`/…), and not `.md` (those
stay relative for the SPA's in-app navigation). Markdown source is untouched, so GitHub's own
relative-link resolution still works. Commit SHA: <pending>.

## Regression test

`viewer/tests/relative-asset-link-resolution.spec.js` (new, 2 tests): (1) a relative `figures/*.svg`
link in a subdir doc is rewritten to `/surveys/s/figures/fig.svg` and that URL serves 200, and the
embedded image src is rewritten the same way (control); (2) `.md` links and external links are left
untouched. Both pass. A grep confirmed no existing test asserts a relative non-`.md` href that the
change would alter. Broader link/render sweep (38 tests across heading-anchor-and-secref, citation,
figure-asset-serving, multiroot-serve): 35 passed; the 3 failures are unrelated to this change — the
two heading-anchor "Bug B" tests passed on isolated re-run (load-induced flake), and `citation T12`
(a `page.goto` 30 s "load" timeout, base port 5100) fails **identically with this fix stashed out**,
proving it pre-existing / environmental (tracked in `todos/2026-06-28-citation-t12-e2e-timeout.md`),
not a regression.

## Refs

- Fix: `viewer/viewer.js` (`fixRelativePaths`, `renderSplitContent`)
- Test: `viewer/tests/relative-asset-link-resolution.spec.js`
- Introduced by: the Figure A.1 alt-view link (this session's Conversation 6); the runtime-resolution
  caveat was flagged at the time (validate-refs does not check non-`.md` asset links).
- Related: the server-side asset route `figure-asset-serving.spec.js` / serve.js asset gate.
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 10).
