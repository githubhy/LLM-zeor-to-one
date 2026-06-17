'use strict';

// Phase 1 — .viewerignore matcher wired through serve.js. The matcher applies
// in MULTI-ROOT mode only (decision 2026-06-14-03: single-root serve is strictly
// byte-identical to legacy and does NOT prune the expanded noise set). This
// proves the built-in noise-folder defaults (dist/, node_modules/) flow through
// the shared matcher into a multi-root /api/files, AND that a single-root serve
// stays byte-identical (serves dist/ markdown). Custom .viewerignore pattern
// semantics are covered by tests/unit/viewerignore.test.js. Port base 7610.

const path = require('path');
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let port = 7610;
const nextPort = () => port++;

test('multi-root: built-in noise dirs (dist/, node_modules/) are pruned from /api/files', async ({ page }) => {
  const dir = createFixtureDir({
    'root/index.md': '# Index',
    'root/sub/chapter.md': '# Chapter',
    'root/dist/baked.md': '# Baked copy (noise)',
    'root/node_modules/pkg/readme.md': '# Dependency (noise)',
  });
  const p = nextPort();
  const server = await startServer(dir, p, { extraArgs: ['--root', path.join(dir, 'root')] });
  try {
    const { files } = await (await page.request.get(`http://localhost:${p}/api/files`)).json();
    expect(files).toContain('root/index.md');
    expect(files).toContain('root/sub/chapter.md');
    expect(files.some((f) => f.includes('dist/'))).toBe(false);
    expect(files.some((f) => f.includes('node_modules/'))).toBe(false);
  } finally {
    await stopServer(server, dir);
  }
});

test('single-root is byte-identical: dist/ markdown is SERVED, only legacy skips apply', async ({ page }) => {
  const dir = createFixtureDir({
    'index.md': '# Index',
    'dist/baked.md': '# Baked (served — user pointed here)',
    'node_modules/pkg/readme.md': '# Dependency (legacy skip)',
  });
  const p = nextPort();
  const server = await startServer(dir, p); // lone positional → id='' → no matcher
  try {
    const { files } = await (await page.request.get(`http://localhost:${p}/api/files`)).json();
    expect(files).toContain('index.md');
    expect(files).toContain('dist/baked.md'); // NOT pruned (byte-identical to main)
    expect(files.some((f) => f.startsWith('node_modules/'))).toBe(false); // legacy skip
  } finally {
    await stopServer(server, dir);
  }
});
