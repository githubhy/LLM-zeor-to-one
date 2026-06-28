'use strict';

// Asset route — deep-path interactive figure artifacts. A figure .html/.pdf/.json
// that lives under a `figures/` OR `artifacts/` directory but is linked from a
// survey far away (so its URL normalizes to /sim/.../figures/foo.html or
// /artifacts/.../foo.html, NOT /figures/foo.html) must be served just like its
// sibling .png. Regression for bug 2026-06-25-01: the asset route only
// whitelisted image extensions + a /figures/ prefix, so a deep-path figure .html
// fell through to 404 while its .png sibling served fine. The /artifacts/ prefix
// was added so clones that store generated figures under artifacts/ work too.
// Port base 7700 (new suite; never renumber existing bases).

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let port = 7700;
const nextPort = () => port++;

function figureFixture() {
  return createFixtureDir({
    'doc.md': '# Doc\n\n![png](sim/x/tools/figures/fig.png)\n\n[html](sim/x/tools/figures/fig.html)\n',
    'sim/x/tools/figures/fig.html': '<!doctype html><title>interactive</title><body>SURFACE-OK</body>',
    'sim/x/tools/figures/fig.png': 'PNG-BYTES-PLACEHOLDER',
    'sim/x/tools/figures/data.json': '{"ok": true}',
    // artifacts/ deep paths are served too (same gate, second prefix).
    'artifacts/study/fig.html': '<!doctype html><title>interactive</title><body>ARTIFACTS-OK</body>',
    'sim/x/tools/other.html': '<title>not a figure</title>',
  });
}

test('deep-path figure .html under figures/ is served (200 text/html)', async ({ page }) => {
  const dir = figureFixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    const res = await page.request.get(`http://localhost:${p}/sim/x/tools/figures/fig.html`);
    expect(res.status()).toBe(200);
    expect(res.headers()['content-type']).toContain('text/html');
    expect(await res.text()).toContain('SURFACE-OK');
  } finally {
    await stopServer(server, dir);
  }
});

test('deep-path figure .html under artifacts/ is served (200 text/html)', async ({ page }) => {
  const dir = figureFixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    const res = await page.request.get(`http://localhost:${p}/artifacts/study/fig.html`);
    expect(res.status()).toBe(200);
    expect(res.headers()['content-type']).toContain('text/html');
    expect(await res.text()).toContain('ARTIFACTS-OK');
  } finally {
    await stopServer(server, dir);
  }
});

test('its sibling .png and .json under figures/ are served too (control)', async ({ page }) => {
  const dir = figureFixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    const png = await page.request.get(`http://localhost:${p}/sim/x/tools/figures/fig.png`);
    expect(png.status()).toBe(200);
    expect(png.headers()['content-type']).toContain('image/png');
    const json = await page.request.get(`http://localhost:${p}/sim/x/tools/figures/data.json`);
    expect(json.status()).toBe(200);
  } finally {
    await stopServer(server, dir);
  }
});

test('a non-figure/non-artifacts .html elsewhere stays unreachable (scope held)', async ({ page }) => {
  const dir = figureFixture();
  const p = nextPort();
  const server = await startServer(dir, p);
  try {
    // Same dir tree, but not under a figures/ or artifacts/ segment → the asset
    // route must NOT open it (the fix is scoped, not a blanket "serve any .html").
    const res = await page.request.get(`http://localhost:${p}/sim/x/tools/other.html`);
    expect(res.status()).toBe(404);
  } finally {
    await stopServer(server, dir);
  }
});
