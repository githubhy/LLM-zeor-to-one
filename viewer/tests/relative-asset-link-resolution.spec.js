// @ts-check
// Client-side relative ASSET-LINK resolution — the complement of the server-side
// asset route covered in figure-asset-serving.spec.js.
//
// A markdown LINK to a relative asset — e.g. [alt](figures/fig.svg) — inside a doc
// that lives in a SUBDIR (surveys/s/doc.md) must have its href rewritten to the
// doc-dir-absolute /surveys/s/figures/fig.svg, exactly like an embedded image's
// src is. The viewer is an SPA served at root with the doc loaded via ?file=, so a
// LEFT-RELATIVE href resolves against the root URL → /figures/fig.svg → 404.
//
// Regression for the alt-figure-link bug: the Figure A.1 caption linked
// `figures/qkv-head-parameters-alt.svg`; clicking it hit /figures/...svg (404)
// while the embedded image (whose src IS rewritten) served fine. fixRelativePaths()
// now rewrites a[href] like img[src], leaving .md links (in-app navigation),
// #anchors, and scheme (http:/mailto:/…) links alone.

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 7800;
const nextPort = () => portCounter++;

function fixture() {
  return createFixtureDir({
    'surveys/s/doc.md': [
      '# Doc',
      '',
      '[svg link](figures/fig.svg)',
      '',
      '[other doc](other.md)',
      '',
      '[deep doc](sub/n.md#sec-x)',
      '',
      '[external](https://example.com/x.svg)',
      '',
      '![img](figures/fig.svg)',
    ].join('\n'),
    'surveys/s/figures/fig.svg':
      '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><title>SVG-OK</title></svg>',
    'surveys/s/other.md': '# Other\n',
  });
}

test('relative asset link in a subdir doc is rewritten to the doc dir and serves 200', async ({ page }) => {
  const dir = fixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    await page.goto(`http://localhost:${p}/?file=surveys/s/doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');

    // The .svg link href is rewritten to the doc-dir absolute path...
    const link = page.locator('#content a', { hasText: 'svg link' }).first();
    await expect(link).toHaveAttribute('href', '/surveys/s/figures/fig.svg');
    // ...and that URL actually serves the asset (the bug was a 404 at /figures/...).
    const res = await page.request.get(`http://localhost:${p}/surveys/s/figures/fig.svg`);
    expect(res.status()).toBe(200);
    expect(await res.text()).toContain('SVG-OK');

    // Control: the embedded image src is rewritten the same way (pre-existing).
    await expect(page.locator('#content img').first()).toHaveAttribute('src', '/surveys/s/figures/fig.svg');
  } finally {
    stopServer(server, dir);
  }
});

test('.md links and external links are left untouched (not prefixed)', async ({ page }) => {
  const dir = fixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    await page.goto(`http://localhost:${p}/?file=surveys/s/doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');

    // .md links → left relative for in-app SPA navigation.
    await expect(page.locator('#content a', { hasText: 'other doc' }).first())
      .toHaveAttribute('href', 'other.md');
    await expect(page.locator('#content a', { hasText: 'deep doc' }).first())
      .toHaveAttribute('href', 'sub/n.md#sec-x');
    // External scheme link → untouched.
    await expect(page.locator('#content a', { hasText: 'external' }).first())
      .toHaveAttribute('href', 'https://example.com/x.svg');
  } finally {
    stopServer(server, dir);
  }
});
