// @ts-check
'use strict';

/**
 * Publish-smoke: end-to-end test that proves a PUBLISHED bundle renders
 * read-only via CloudBackend, served by a plain static file server (no
 * serve.js / no app server).
 *
 * Test layout:
 *  - beforeAll: create fixture survey dir, run publish.js, start plain
 *    static http server rooted at the dist dir.
 *  - test: navigate to /?file=sample.md, assert CloudBackend active,
 *    math rendered, heading rendered, and figure loaded.
 *  - afterAll: close server, rm tmp dirs.
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

// ─── port allocation ──────────────────────────────────────────────────────────
// Use a range far from the existing tests (which start at 4100) to avoid
// port-reuse flake when running the full suite in parallel.
let portCounter = 5600;
function nextPort() { return portCounter++; }

// ─── minimal valid 1×1 red PNG ────────────────────────────────────────────────
// Pre-encoded so the test has zero external dependencies and a deterministic
// PNG header/IEND that browsers accept. naturalWidth === 1 after decode.
const TINY_PNG_B64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADklEQVQI12P4z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg==';

// ─── MIME map for plain static server ─────────────────────────────────────────
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md':   'text/markdown; charset=utf-8',
  '.png':  'image/png',
  '.woff2':'font/woff2',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.webmanifest': 'application/manifest+json',
};

/**
 * Start a plain static file server rooted at `root`.
 * Maps `/` → `index.html`; 404 for missing files.
 * Guards against path-traversal by stripping `..` segments.
 * @param {string} root - absolute path to serve from
 * @param {number} port
 * @returns {Promise<http.Server>}
 */
function startStaticServer(root, port) {
  const server = http.createServer((req, res) => {
    // Decode and strip query / fragment
    let pathname = req.url || '/';
    try { pathname = decodeURIComponent(pathname.split('?')[0].split('#')[0]); } catch { pathname = '/'; }

    // Normalise to `index.html` for root
    if (pathname === '/' || pathname === '') pathname = '/index.html';

    // Guard against path traversal: resolve and verify still under root
    const candidate = path.resolve(root, pathname.replace(/^\/+/, ''));
    if (!candidate.startsWith(root + path.sep) && candidate !== root) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }

    fs.readFile(candidate, (err, data) => {
      if (err) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      const ext = path.extname(candidate).toLowerCase();
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });

  return new Promise((resolve, reject) => {
    server.listen(port, '127.0.0.1', () => resolve(server));
    server.on('error', reject);
  });
}

// ─── shared state set up in beforeAll ─────────────────────────────────────────
const PORT = nextPort();
let staticServer = /** @type {http.Server|null} */ (null);
let fixtureSurveyDir = /** @type {string|null} */ (null);
let distDir = /** @type {string|null} */ (null);

const viewerDir = path.resolve(__dirname, '..');

test.beforeAll(async () => {
  // ── 1. Create fixture survey dir ────────────────────────────────────────────
  fixtureSurveyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'publish-smoke-fixture-'));
  distDir          = fs.mkdtempSync(path.join(os.tmpdir(), 'publish-smoke-dist-'));

  // Markdown that exercises the renderer: heading, inline math, figure ref.
  const mdContent = [
    '# Hello World',
    '',
    'Inline math: $E=mc^2$.',
    '',
    '![A box figure](figures/box.png)',
    '',
  ].join('\n');
  fs.writeFileSync(path.join(fixtureSurveyDir, 'sample.md'), mdContent, 'utf8');

  // Write a minimal valid 1×1 PNG so the browser reports naturalWidth > 0.
  const figuresDir = path.join(fixtureSurveyDir, 'figures');
  fs.mkdirSync(figuresDir, { recursive: true });
  fs.writeFileSync(path.join(figuresDir, 'box.png'), Buffer.from(TINY_PNG_B64, 'base64'));

  // Optional order.json (helps the sidebar but is not required for the test).
  fs.writeFileSync(
    path.join(fixtureSurveyDir, 'order.json'),
    JSON.stringify(['sample.md']),
    'utf8',
  );

  // ── 2. Run publish.js ────────────────────────────────────────────────────────
  const result = spawnSync(
    process.execPath,
    ['publish.js', '--target', fixtureSurveyDir, '--out', distDir],
    { cwd: viewerDir, encoding: 'utf8' },
  );
  if (result.status !== 0) {
    throw new Error(
      `publish.js exited with code ${result.status}.\n` +
      `stdout: ${result.stdout}\nstderr: ${result.stderr}`,
    );
  }

  // ── 3. Assert required dist artefacts exist ──────────────────────────────────
  const required = ['index.html', 'viewer.js', 'style.css', 'files.json', 'content/sample.md'];
  for (const rel of required) {
    const abs = path.join(distDir, rel);
    if (!fs.existsSync(abs)) throw new Error(`publish output missing: ${rel}`);
  }

  // ── 4. Start plain static server ────────────────────────────────────────────
  staticServer = await startStaticServer(distDir, PORT);
});

test.afterAll(async () => {
  if (staticServer) {
    await new Promise((resolve) => staticServer.close(resolve));
    staticServer = null;
  }
  if (fixtureSurveyDir) {
    try { fs.rmSync(fixtureSurveyDir, { recursive: true, force: true }); } catch {}
    fixtureSurveyDir = null;
  }
  if (distDir) {
    try { fs.rmSync(distDir, { recursive: true, force: true }); } catch {}
    distDir = null;
  }
});

// ─── PWA artefacts test ───────────────────────────────────────────────────────
test('published bundle includes PWA manifest, icons, and correct head tags', () => {
  // Manifest exists.
  const manifestPath = path.join(distDir, 'manifest.webmanifest');
  if (!fs.existsSync(manifestPath)) throw new Error('dist/manifest.webmanifest missing');

  // Icons exist.
  const iconFiles = ['icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-512-maskable.png'];
  for (const rel of iconFiles) {
    const abs = path.join(distDir, rel);
    if (!fs.existsSync(abs)) throw new Error(`dist/${rel} missing`);
  }

  // index.html contains required PWA head tags.
  const html = fs.readFileSync(path.join(distDir, 'index.html'), 'utf8');
  if (!html.includes('rel="manifest"')) throw new Error('index.html missing rel="manifest"');
  if (!html.includes('viewport-fit=cover')) throw new Error('index.html missing viewport-fit=cover');
  if (!html.includes('theme-color')) throw new Error('index.html missing theme-color meta');
});

// ─── service-worker artefacts test ───────────────────────────────────────────
test('published bundle includes service worker with precache header', () => {
  // dist/sw.js must exist.
  const swPath = path.join(distDir, 'sw.js');
  if (!fs.existsSync(swPath)) throw new Error('dist/sw.js missing');

  const swSrc = fs.readFileSync(swPath, 'utf8');

  // First line must be the injected header.
  if (!swSrc.startsWith('self.__VERSION=')) {
    throw new Error('dist/sw.js does not start with self.__VERSION= header');
  }

  // Precache list must include a vendor JS and files.json.
  const headerLine = swSrc.split('\n')[0];
  if (!headerLine.includes('vendor/katex.min.js')) {
    throw new Error('dist/sw.js precache list missing vendor/katex.min.js');
  }
  if (!headerLine.includes('"files.json"')) {
    throw new Error('dist/sw.js precache list missing files.json');
  }
});

// ─── main smoke test ──────────────────────────────────────────────────────────
test('published bundle renders a survey read-only via CloudBackend', async ({ page }) => {
  // Collect console 404s for KaTeX font diagnostics (nice-to-have).
  const font404s = /** @type {string[]} */ ([]);
  page.on('response', (res) => {
    if (res.status() === 404 && res.url().includes('/vendor/fonts/')) {
      font404s.push(res.url());
    }
  });

  // Navigate to the published bundle.
  await page.goto(`http://127.0.0.1:${PORT}/?file=sample.md`);

  // ── Assert CloudBackend active ────────────────────────────────────────────
  const backendKind = await page.evaluate(() =>
    window.VIEWER_CONFIG && window.VIEWER_CONFIG.backend,
  );
  expect(backendKind).toBe('cloud');

  // ── Assert heading rendered ───────────────────────────────────────────────
  await expect(page.locator('#content h1, main h1').first()).toHaveText('Hello World');

  // ── Assert KaTeX math rendered ────────────────────────────────────────────
  await expect(page.locator('.katex').first()).toBeVisible();

  // ── Assert figure loaded ──────────────────────────────────────────────────
  // Wait for the image to be present in the DOM first (the file load is async).
  await expect(page.locator('main img, #content img').first()).toBeVisible({ timeout: 10_000 });

  // Now assert it actually decoded — naturalWidth > 0 means the browser
  // fetched and decoded the image bytes successfully.
  const imgLoaded = await page.evaluate(() => {
    const img = document.querySelector('main img, #content img');
    return !!img && img.complete && img.naturalWidth > 0;
  });

  if (!imgLoaded) {
    // Surface diagnostic information before failing.
    const imgSrc = await page.evaluate(() => {
      const img = document.querySelector('main img, #content img');
      return img ? img.getAttribute('src') : '(no img element found)';
    });
    const imgComplete = await page.evaluate(() => {
      const img = document.querySelector('main img, #content img');
      return img ? { complete: img.complete, naturalWidth: img.naturalWidth } : null;
    });
    throw new Error(
      `Figure did NOT load. img.src="${imgSrc}", ` +
      `complete=${imgComplete && imgComplete.complete}, ` +
      `naturalWidth=${imgComplete && imgComplete.naturalWidth}. ` +
      `This indicates a figure-path layout bug in the publisher — ` +
      `the browser's requested URL does not match the file's location under dist/.`,
    );
  }
  expect(imgLoaded).toBe(true);

  // ── (nice-to-have) Assert no KaTeX font 404s ─────────────────────────────
  // Give fonts a moment to resolve before checking.
  await page.waitForTimeout(500);
  if (font404s.length > 0) {
    // Non-fatal: report as a warning rather than a hard failure.
    // KaTeX font paths are a deployment concern, not a publisher correctness issue.
    console.warn(`[publish-smoke] KaTeX font 404s detected:\n  ${font404s.join('\n  ')}`);
  }
  expect(font404s).toHaveLength(0);
});
