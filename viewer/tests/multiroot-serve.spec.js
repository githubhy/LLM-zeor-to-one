'use strict';

// Phase 2 — multi-root serving (`--root A --root B`). Namespaced /api/files,
// per-root markdown fetch, per-root sandbox (no cross-root escape), per-root
// sidecar resolution. Port base 7600 (new suite; never renumber existing bases).

const path = require('path');
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let port = 7600;
const nextPort = () => port++;

// Two roots as sibling subdirs of one temp dir so the ids are predictable
// (basename = 'roota' / 'rootb').
function twoRootFixture() {
  const dir = createFixtureDir({
    'roota/a.md': '# Doc A',
    'roota/sub/deep.md': '# Deep A',
    'rootb/b.md': '# Doc B',
    'rootb/dist/noise.md': '# noise (should be pruned)',
  });
  return {
    dir,
    extraArgs: ['--root', path.join(dir, 'roota'), '--root', path.join(dir, 'rootb')],
  };
}

test('/api/files returns schema 2, the roots array, and namespaced files', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    const res = await page.request.get(`http://localhost:${p}/api/files`);
    const json = await res.json();
    expect(json.schema).toBe(2);
    expect(json.roots).toEqual([
      { id: 'roota', label: 'roota' },
      { id: 'rootb', label: 'rootb' },
    ]);
    expect(json.files).toContain('roota/a.md');
    expect(json.files).toContain('roota/sub/deep.md');
    expect(json.files).toContain('rootb/b.md');
    // .viewerignore built-in default prunes dist/ inside a root too.
    expect(json.files).not.toContain('rootb/dist/noise.md');
  } finally {
    await stopServer(server, dir);
  }
});

test('a markdown file in either root is fetchable by its namespaced id', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    const a = await page.request.get(`http://localhost:${p}/api/md/roota/a.md`);
    expect(a.ok()).toBeTruthy();
    expect(await a.text()).toContain('Doc A');
    const b = await page.request.get(`http://localhost:${p}/api/md/rootb/b.md`);
    expect(b.ok()).toBeTruthy();
    expect(await b.text()).toContain('Doc B');
    // Unknown namespace → 404.
    const x = await page.request.get(`http://localhost:${p}/api/md/nope/x.md`);
    expect(x.status()).toBe(404);
  } finally {
    await stopServer(server, dir);
  }
});

test('sandbox: namespace isolation + escape above all roots are rejected (404)', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    // Namespace isolation: b.md belongs to rootb, so it is NOT reachable via
    // root A's namespace (each root resolves only its own files).
    const iso = await page.request.get(`http://localhost:${p}/api/md/roota/b.md`);
    expect(iso.status()).toBe(404);
    // A `..` chain that escapes ABOVE every declared root resolves to no root
    // (rootForFile returns null) → 404. (`%2e%2e` so it survives to the server;
    // an in-bounds `..` that normalizes to another valid root file is benign by
    // design — the sandbox only forbids escaping the declared root set.)
    const esc = await page.request.get(`http://localhost:${p}/api/md/roota/%2e%2e/%2e%2e/outside.txt`);
    expect(esc.status()).toBe(404);
  } finally {
    await stopServer(server, dir);
  }
});

test('an old flat ?file= id resolves to its namespaced doc and rewrites the URL', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    // Bookmark pre-dating namespacing: ?file=a.md (now roota/a.md).
    await page.goto(`http://localhost:${p}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc A');
    await expect
      .poll(() => new URL(page.url()).searchParams.get('file'))
      .toBe('roota/a.md');
  } finally {
    await stopServer(server, dir);
  }
});

test('multi-root sidebar groups by root (outer .root-group per root, namespaced entries)', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    await page.goto(`http://localhost:${p}/`);
    await expect(page.locator('.root-group[data-root="roota"]')).toHaveCount(1);
    await expect(page.locator('.root-group[data-root="rootb"]')).toHaveCount(1);
    await expect(page.locator('.root-group[data-root="roota"] .file-entry[data-file="roota/a.md"]')).toHaveCount(1);
    await expect(page.locator('.root-group[data-root="rootb"] .file-entry[data-file="rootb/b.md"]')).toHaveCount(1);
    // the inner per-folder subgroup (roota/sub) nests under the root group
    await expect(page.locator('.root-group[data-root="roota"] .dir-group[data-dir="roota/sub"]')).toHaveCount(1);
  } finally {
    await stopServer(server, dir);
  }
});

test('single-root sidebar has NO .root-group (per-folder grouping unchanged)', async ({ page }) => {
  const dir = createFixtureDir({ 'sub/a.md': '# A', 'b.md': '# B' });
  const p = nextPort();
  const server = await startServer(dir, p); // lone positional → id='' (compat)
  try {
    await page.goto(`http://localhost:${p}/`);
    await expect(page.locator('.dir-group[data-dir="sub"]')).toHaveCount(1);
    await expect(page.locator('.root-group')).toHaveCount(0);
  } finally {
    await stopServer(server, dir);
  }
});

test('outline "All" (workspace) scope lists files across roots; lazy-expands on click (#3/#6)', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    await pinClassicLayout(page); // docs chrome → sidebar outline tab is clickable
    await page.goto(`http://localhost:${p}/?file=roota/a.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc A');
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    // Workspace ("All") scope is offered only in multi-root for the outline pane.
    const allBtn = page.locator('#outline-list .pane-scope-btn[data-scope="workspace"]');
    await expect(allBtn).toHaveCount(1);
    await allBtn.click();
    // A sibling from the OTHER root renders collapsed + lazy (no entries yet —
    // the ~hundreds-of-files workspace is not bulk-fetched).
    const grp = page.locator('.outline-file-group[data-file="rootb/b.md"]');
    await expect(grp).toHaveClass(/collapsed/);
    await expect(grp.locator('.outline-entry')).toHaveCount(0);
    // Expanding it lazily fetches + builds just that file's headings.
    await grp.locator('.outline-file-sep').click();
    await expect(grp).not.toHaveClass(/collapsed/);
    await expect(grp.locator('.outline-entry')).toHaveCount(1);
  } finally {
    await stopServer(server, dir);
  }
});

test('multi-root Folder scope groups root-level flat files together (folderOf2 fix, review #2)', async ({ page }) => {
  const dir = createFixtureDir({
    'roota/x.md': '# X',
    'reports/r1.md': '# R1\n\n## R1a',
    'reports/r2.md': '# R2',
  });
  const extraArgs = ['--root', path.join(dir, 'roota'), '--root', path.join(dir, 'reports')];
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    await pinClassicLayout(page);
    await page.goto(`http://localhost:${p}/?file=reports/r1.md`);
    await expect(page.locator('#content h1')).toHaveText('R1');
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    // Folder scope (default) on a flat root-level file shows BOTH reports files
    // as sibling groups — not just the current file as a singleton.
    await expect(page.locator('.outline-file-group[data-file="reports/r1.md"]')).toHaveCount(1);
    await expect(page.locator('.outline-file-group[data-file="reports/r2.md"]')).toHaveCount(1);
  } finally {
    await stopServer(server, dir);
  }
});

test('per-root sidecar: /api/highlights resolves for each root (no 404)', async ({ page }) => {
  const { dir, extraArgs } = twoRootFixture();
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs });
  try {
    const a = await page.request.get(`http://localhost:${p}/api/highlights/roota/a.md`);
    expect(a.ok()).toBeTruthy();
    expect((await a.json()).file).toBe('roota/a.md');
    const b = await page.request.get(`http://localhost:${p}/api/highlights/rootb/b.md`);
    expect(b.ok()).toBeTruthy();
    expect((await b.json()).file).toBe('rootb/b.md');
  } finally {
    await stopServer(server, dir);
  }
});
