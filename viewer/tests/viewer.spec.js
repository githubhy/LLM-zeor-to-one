// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

// Each test gets its own port to avoid collisions
let portCounter = 4100;
function nextPort() { return portCounter++; }

// Pre-redesign suite: navigation, search, and note-marker flows drive the
// docked sidebar — pin classic layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

async function getDocumentRevision(request, url) {
  const res = await request.get(url);
  expect(res.ok()).toBe(true);
  const etag = res.headers()['etag'];
  expect(typeof etag).toBe('string');
  return etag;
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.1 — Rapid navigation race: stale responses must not win
// ─────────────────────────────────────────────────────────────────────────────
test('rapid navigation always renders the last-clicked file', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md': '# File A\n\nContent of file A.',
    'b.md': '# File B\n\nContent of file B.',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}`);
    await expect(page.locator('#content h1')).toBeVisible();

    // Delay responses to a.md so it always finishes after b.md
    await page.route('**/api/md/a.md', async (route) => {
      await new Promise(r => setTimeout(r, 500));
      await route.continue();
    });

    // Click a.md then immediately b.md
    await page.locator('.file-entry', { hasText: 'a' }).click();
    await page.locator('.file-entry', { hasText: 'b' }).click();

    // Wait long enough for the delayed a.md to arrive
    await page.waitForTimeout(1000);

    // Content must be file B
    await expect(page.locator('#content')).toContainText('Content of file B');
    // URL must reference b.md
    expect(page.url()).toContain('file=b.md');
    // Sidebar active entry must be b
    await expect(page.locator('.file-entry.active')).toHaveAttribute('data-file', 'b.md');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.2 — No duplicate link navigation after repeated renders
// ─────────────────────────────────────────────────────────────────────────────
test('repeated renders do not multiply link-click behaviour', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md': '# A\n\n[Go to B](b.md)',
    'b.md': '# B\n\nHello from B.',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');

    // Simulate many re-renders by reloading the same file repeatedly
    for (let i = 0; i < 10; i++) {
      await page.locator('.file-entry', { hasText: 'a' }).click();
      await expect(page.locator('#content h1')).toHaveText('A');
    }

    // Count fetch requests triggered by clicking the link once
    const fetchUrls = [];
    page.on('request', (req) => {
      if (req.url().includes('/api/md/')) fetchUrls.push(req.url());
    });

    await page.locator('#content a').first().click();
    await expect(page.locator('#content')).toContainText('Hello from B');

    // Exactly one fetch for b.md (not many)
    const bFetches = fetchUrls.filter(u => u.includes('b.md'));
    expect(bFetches.length).toBe(1);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.3 — Server survives write failure
// ─────────────────────────────────────────────────────────────────────────────
test('failed PUT returns error and server stays alive', async ({ request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'test.md': '# Test\n',
  });
  const server = await startServer(dir, port);

  try {
    const baseUrl = `http://localhost:${port}/api/md/test.md`;
    const etag = await getDocumentRevision(request, baseUrl);

    // Make the file unwritable
    const filePath = path.join(dir, 'test.md');
    fs.chmodSync(filePath, 0o444);
    // Also make directory unwritable so .tmp creation fails
    fs.chmodSync(dir, 0o555);

    const putRes = await request.put(baseUrl, {
      data: '# Modified\n',
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': etag,
      },
    });
    // Should be a 403 or 500, not a crash
    expect(putRes.ok()).toBe(false);
    expect([403, 500]).toContain(putRes.status());

    // Restore permissions for cleanup
    fs.chmodSync(dir, 0o755);
    fs.chmodSync(filePath, 0o644);

    // Server should still serve GET requests
    const getRes = await request.get(baseUrl);
    expect(getRes.ok()).toBe(true);
    expect(await getRes.text()).toContain('# Test');
  } finally {
    // Ensure permissions are restored before cleanup
    try { fs.chmodSync(dir, 0o755); } catch {}
    try { fs.chmodSync(path.join(dir, 'test.md'), 0o644); } catch {}
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.4 — Reconnect does not multiply focus-refresh behaviour
// ─────────────────────────────────────────────────────────────────────────────
test('multiple WS reconnects produce only one focus-refresh', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nOriginal content.',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('#content')).toContainText('Original content');

    // Simulate multiple reconnects by calling connectWS several times
    // connectWS is in global scope of the viewer
    await page.evaluate(() => {
      // @ts-ignore
      if (typeof connectWS === 'function') {
        // @ts-ignore
        connectWS(); connectWS(); connectWS();
      }
    });

    // Intercept /api/md/ requests to count them
    const refreshUrls = [];
    await page.route('**/api/md/**', async (route) => {
      refreshUrls.push(route.request().url());
      await route.continue();
    });

    // Trigger visibilitychange (simulate tab focus)
    await page.evaluate(() => {
      document.dispatchEvent(new Event('visibilitychange'));
      Object.defineProperty(document, 'visibilityState', { value: 'visible', writable: true });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    await page.waitForTimeout(500);

    // Should be at most 2 refreshes (the two visibilitychange events),
    // NOT 6+ (which would happen if each connectWS added a listener)
    expect(refreshUrls.length).toBeLessThanOrEqual(2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.5 — Local edit rerenders immediately even without live reload
// ─────────────────────────────────────────────────────────────────────────────
test('local edit rerenders immediately with WebSocket down', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'edit.md': '# Before\n\nOriginal text.',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=edit.md`);
    await expect(page.locator('#content')).toContainText('Original text');

    // Close the WebSocket so live-reload cannot trigger
    await page.evaluate(() => {
      // Find and close all WebSocket instances by overriding the constructor
      // @ts-ignore
      if (window._testWsClosed) return;
      const origWS = window.WebSocket;
      // Close existing sockets
      // @ts-ignore
      window.WebSocket = function(...args) {
        const ws = new origWS(...args);
        ws.addEventListener('open', () => ws.close());
        return ws;
      };
      // @ts-ignore
      window._testWsClosed = true;
    });
    await page.waitForTimeout(300);

    // PUT new content directly
    const newContent = '# After\n\nUpdated text.';
    const putRes = await request.put(`http://localhost:${port}/api/md/edit.md`, {
      data: newContent,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': await getDocumentRevision(request, `http://localhost:${port}/api/md/edit.md`),
      },
    });
    expect(putRes.status()).toBe(204);

    // Call applyLocalSourceUpdate from page context to simulate the write flow
    await page.evaluate((content) => {
      // @ts-ignore
      if (typeof applyLocalSourceUpdate === 'function') {
        // @ts-ignore
        applyLocalSourceUpdate('edit.md', content);
      }
    }, newContent);

    // DOM should update immediately
    await expect(page.locator('#content')).toContainText('Updated text');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 4.6 — Oversized PUT returns 413
// ─────────────────────────────────────────────────────────────────────────────
test('oversized PUT returns 413', async ({ request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'big.md': '# Big\n',
  });
  const server = await startServer(dir, port);

  try {
    const baseUrl = `http://localhost:${port}/api/md/big.md`;
    const etag = await getDocumentRevision(request, baseUrl);
    // Send a body larger than 10 MB
    const bigBody = 'x'.repeat(11 * 1024 * 1024);
    const res = await request.put(baseUrl, {
      data: bigBody,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': etag,
      },
    });
    expect(res.status()).toBe(413);

    // Server should still be alive
    const getRes = await request.get(baseUrl);
    expect(getRes.ok()).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

test('/api/md/ rejects paths inside the .viewer-highlights sidecar directory', async ({ request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nBody.\n',
  });
  // Seed a sidecar JSON the way the server itself would — the /api/md/ route
  // must refuse to read or overwrite it.
  const sidecarDir = path.join(dir, '.viewer-highlights');
  fs.mkdirSync(sidecarDir, { recursive: true });
  const sidecarPath = path.join(sidecarDir, 'doc.md.json');
  const originalSidecar = JSON.stringify({ version: 1, file: 'doc.md', highlights: [] }, null, 2);
  fs.writeFileSync(sidecarPath, originalSidecar, 'utf8');

  const server = await startServer(dir, port);

  try {
    const sidecarUrl = `http://localhost:${port}/api/md/.viewer-highlights/doc.md.json`;

    // GET must 404 — the sidecar tree is not addressable via /api/md/.
    const getRes = await request.get(sidecarUrl);
    expect(getRes.status()).toBe(404);

    // PUT must 404 — and the on-disk sidecar must remain untouched.
    const putRes = await request.put(sidecarUrl, {
      data: 'corrupt\n',
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': '"whatever"',
      },
    });
    expect(putRes.status()).toBe(404);
    expect(fs.readFileSync(sidecarPath, 'utf8')).toBe(originalSidecar);

    // The legitimate markdown route still works.
    const okRes = await request.get(`http://localhost:${port}/api/md/doc.md`);
    expect(okRes.ok()).toBe(true);
    expect(await okRes.text()).toContain('# Doc');
  } finally {
    stopServer(server, dir);
  }
});

test('stale If-Match write returns 409 conflict', async ({ request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'conflict.md': '# Conflict\n\nInitial.\n',
  });
  const server = await startServer(dir, port);

  try {
    const baseUrl = `http://localhost:${port}/api/md/conflict.md`;
    const staleRevision = await getDocumentRevision(request, baseUrl);

    const firstWrite = await request.put(baseUrl, {
      data: '# Conflict\n\nFirst write.\n',
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': staleRevision,
      },
    });
    expect(firstWrite.status()).toBe(204);
    const newRevision = firstWrite.headers()['etag'];
    expect(newRevision).toBeTruthy();
    expect(newRevision).not.toBe(staleRevision);

    const staleWrite = await request.put(baseUrl, {
      data: '# Conflict\n\nStale write.\n',
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'If-Match': staleRevision,
      },
    });
    expect(staleWrite.status()).toBe(409);
    expect(staleWrite.headers()['etag']).toBe(newRevision);

    const current = await request.get(baseUrl);
    expect(current.ok()).toBe(true);
    expect(await current.text()).toContain('First write.');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Back-navigation regression tests
//
// Guard against the scroll-restoration bug fixed in viewer.js:
//   1. loadFile snapshots window.scrollY into history state BEFORE the
//      innerHTML replacement clamps it.
//   2. popstate's cross-file branch calls scrollToStable(targetScrollY) so
//      the pop lands exactly where the user clicked.
//   3. renderSeq cancels stale scrollToAnchor callbacks from a previous
//      render — otherwise a late setTimeout from the outgoing page would
//      hijack the restored scroll when the new page reuses the anchor id.
// ─────────────────────────────────────────────────────────────────────────────
function tallFiller(prefix, count) {
  const out = [];
  for (let i = 0; i < count; i++) {
    out.push(`${prefix} paragraph ${i} — filler line to give the rendered page measurable vertical height for scroll-restore tests.`);
    out.push('');
  }
  return out.join('\n');
}

async function scrollLinkIntoView(page, hrefSub) {
  await page.evaluate((sub) => {
    const a = [...document.querySelectorAll('a')].find(x =>
      (x.getAttribute('href') || '').includes(sub));
    if (!a) throw new Error(`link matching "${sub}" not found`);
    a.scrollIntoView({ behavior: 'instant', block: 'center' });
  }, hrefSub);
}

async function clickLinkSynthetic(page, hrefSub) {
  await page.evaluate((sub) => {
    const a = [...document.querySelectorAll('a')].find(x =>
      (x.getAttribute('href') || '').includes(sub));
    if (!a) throw new Error(`link matching "${sub}" not found`);
    a.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
  }, hrefSub);
}

test('back after cross-file link click restores exact scroll position', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-pre', 40) +
      '\n\n[Jump to B target](b.md#target)\n\n' +
      tallFiller('A-post', 40),
    'b.md':
      '# Page B\n\n' + tallFiller('B-pre', 60) +
      '\n\n<a id="target"></a>\n**Target on B**\n\n' +
      tallFiller('B-post', 60),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    await scrollLinkIntoView(page, 'b.md#target');
    await page.waitForTimeout(300); // scroll-save debounce
    const origScroll = await page.evaluate(() => window.scrollY);
    expect(origScroll).toBeGreaterThan(100);

    await clickLinkSynthetic(page, 'b.md#target');
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=b.md');
    expect(page.url()).toContain('#target');

    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);

    expect(page.url()).toContain('file=a.md');
    const backScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backScroll - origScroll)).toBeLessThanOrEqual(10);
  } finally {
    stopServer(server, dir);
  }
});

test('back after cross-file click with colliding anchor id does not hijack scroll', async ({ page }) => {
  // Both files define id="shared". Without the renderSeq guard, a late
  // scrollToAnchor('shared') scheduled by the outgoing page's render would
  // fire on the newly-restored page's DOM and yank scroll onto the wrong
  // "shared" element.
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-top', 15) +
      '\n\n<a id="shared"></a>\n**Local shared on A (wrong target)**\n\n' +
      tallFiller('A-mid', 20) +
      '\n\n[Cross-file shared](b.md#shared)\n\n' +
      tallFiller('A-bot', 40),
    'b.md':
      '# Page B\n\n' + tallFiller('B-pre', 50) +
      '\n\n<a id="shared"></a>\n**Target shared on B**\n\n' +
      tallFiller('B-post', 50),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    await scrollLinkIntoView(page, 'b.md#shared');
    await page.waitForTimeout(300);
    const origScroll = await page.evaluate(() => window.scrollY);

    // Note the position of A's own "shared" element so we can prove that
    // back-navigation did NOT land there.
    const localSharedY = await page.evaluate(() => {
      const el = document.getElementById('shared');
      return el ? el.getBoundingClientRect().top + window.scrollY : null;
    });
    expect(localSharedY).not.toBeNull();
    expect(Math.abs(origScroll - localSharedY)).toBeGreaterThan(200);

    await clickLinkSynthetic(page, 'b.md#shared');
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=b.md');

    await page.goBack({ waitUntil: 'domcontentloaded' });
    // Wait past the 300 ms setTimeout window inside renderToContent AND
    // scrollToStable's 600 ms loop so any stale callback would have fired.
    await page.waitForTimeout(1200);

    expect(page.url()).toContain('file=a.md');
    const backScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backScroll - origScroll)).toBeLessThanOrEqual(10);
    // And it definitely did not snap to A's own #shared element.
    expect(Math.abs(backScroll - localSharedY)).toBeGreaterThan(100);
  } finally {
    stopServer(server, dir);
  }
});

test('forward after back restores the scroll position recorded on the forward page', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-pre', 40) +
      '\n\n[Jump to B target](b.md#target)\n\n' +
      tallFiller('A-post', 40),
    'b.md':
      '# Page B\n\n' + tallFiller('B-pre', 60) +
      '\n\n<a id="target"></a>\n**Target on B**\n\n' +
      tallFiller('B-post', 60),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    await scrollLinkIntoView(page, 'b.md#target');
    await page.waitForTimeout(300);
    const origA = await page.evaluate(() => window.scrollY);

    await clickLinkSynthetic(page, 'b.md#target');
    // Allow smooth-scroll + scroll-save debounce to settle so B's history
    // entry has its scrollY saved.
    await page.waitForTimeout(1500);
    const stateB = await page.evaluate(() => history.state);
    expect(typeof stateB.scrollY).toBe('number');
    const expectedB = stateB.scrollY;

    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=a.md');
    const backScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backScroll - origA)).toBeLessThanOrEqual(10);

    await page.goForward({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=b.md');
    const fwdScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(fwdScroll - expectedB)).toBeLessThanOrEqual(10);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Same-file anchor link back-navigation
//
// Exercises the popstate `file === currentFile` branch which uses
// scrollToInstant(targetScrollY). Without scroll-save into the outgoing
// entry, back from an in-page anchor click would land at scrollY=0 (or at
// the anchor) instead of where the user clicked from.
// ─────────────────────────────────────────────────────────────────────────────
test('back after same-file anchor click restores prior scroll position', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-pre', 30) +
      '\n\n[Jump down](#deep)\n\n' +
      tallFiller('A-mid', 60) +
      '\n\n<a id="deep"></a>\n**Deep target**\n\n' +
      tallFiller('A-post', 30),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    // Scroll the in-page anchor link into view (somewhere around the middle).
    await scrollLinkIntoView(page, '#deep');
    await page.waitForTimeout(300); // let scroll-save debounce flush
    const origScroll = await page.evaluate(() => window.scrollY);
    expect(origScroll).toBeGreaterThan(100);

    await clickLinkSynthetic(page, '#deep');
    // Wait for smooth scroll to complete and the scroll-save debounce to
    // record the deep position into the new entry.
    await page.waitForTimeout(1200);
    expect(page.url()).toContain('#deep');
    const deepScroll = await page.evaluate(() => window.scrollY);
    // The anchor jumped us somewhere different from the click origin.
    expect(Math.abs(deepScroll - origScroll)).toBeGreaterThan(200);

    await page.goBack({ waitUntil: 'domcontentloaded' });
    // popstate same-file branch is synchronous (no re-render); allow a
    // very short window for the instant scroll to apply.
    await page.waitForTimeout(150);

    const backScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backScroll - origScroll)).toBeLessThanOrEqual(10);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Scroll-save debouncer persists scrollY into history.state
//
// The global scroll listener writes window.scrollY into history.state on a
// 150 ms debounce. Back-navigation depends on this snapshot being up to
// date — verify it directly here so a regression in the listener wiring
// shows up immediately, separately from the cross-file integration tests.
// ─────────────────────────────────────────────────────────────────────────────
test('scroll-save debouncer writes scrollY into history.state', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md': '# Page A\n\n' + tallFiller('A', 80),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    // Initial scrollY should be 0 (or close to it); state should already
    // carry a numeric scrollY from the initial 'replace' branch in loadFile.
    const initialState = await page.evaluate(() => history.state);
    expect(typeof initialState.scrollY).toBe('number');

    // Scroll to a known offset (instant — bypass CSS smooth scroll so the
    // debouncer sees the final scrollY immediately) and wait past the
    // 150 ms debounce window.
    await page.evaluate(() => window.scrollTo({ top: 1234, left: 0, behavior: 'instant' }));
    await page.waitForTimeout(400);

    const afterState = await page.evaluate(() => history.state);
    const liveY = await page.evaluate(() => window.scrollY);
    expect(liveY).toBe(1234);
    expect(typeof afterState.scrollY).toBe('number');
    // Allow ±5 px slack for browser pixel rounding.
    expect(Math.abs(afterState.scrollY - 1234)).toBeLessThanOrEqual(5);
    // The current file pointer must be carried through the debouncer write.
    expect(afterState.file).toBe('a.md');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// overflow-anchor: none on the html element
//
// Browser scroll-anchoring would otherwise drift the restored scroll
// position when KaTeX or images change layout heights after the initial
// paint. The CSS rule must reach the document element as a computed style.
// ─────────────────────────────────────────────────────────────────────────────
test('html element disables browser scroll-anchoring', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md': '# Page A\n\nShort.',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    const oa = await page.evaluate(() =>
      getComputedStyle(document.documentElement).overflowAnchor
    );
    expect(oa).toBe('none');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Initial load seeds history.state with a numeric scrollY
//
// loadFile's pushHistory==='replace' branch is what bootstraps the very
// first history entry. If the seed forgot scrollY, the first popstate
// after a forward navigation would have nothing to restore.
// ─────────────────────────────────────────────────────────────────────────────
test('initial load seeds history.state with file, anchor, and scrollY', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n<a id="mark"></a>\n**Mark**\n\n' + tallFiller('A', 40),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md#mark`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    const state = await page.evaluate(() => history.state);
    expect(state).not.toBeNull();
    expect(state.file).toBe('a.md');
    expect(state.anchor).toBe('mark');
    expect(typeof state.scrollY).toBe('number');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Three-file chain: A → B → C, then back-back, restoring each origin
//
// Two consecutive cross-file pops in a row exercise the same code paths
// twice in close succession. A bug where renderSeq or scroll-snapshot
// state leaks across the first pop into the second would surface here.
// ─────────────────────────────────────────────────────────────────────────────
test('back-back through a three-file chain restores each scroll origin', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-pre', 35) +
      '\n\n[Go to B](b.md#tb)\n\n' +
      tallFiller('A-post', 35),
    'b.md':
      '# Page B\n\n' + tallFiller('B-pre', 35) +
      '\n\n<a id="tb"></a>**B target**\n\n' +
      tallFiller('B-mid', 35) +
      '\n\n[Go to C](c.md#tc)\n\n' +
      tallFiller('B-post', 35),
    'c.md':
      '# Page C\n\n' + tallFiller('C-pre', 50) +
      '\n\n<a id="tc"></a>**C target**\n\n' +
      tallFiller('C-post', 50),
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    await scrollLinkIntoView(page, 'b.md#tb');
    await page.waitForTimeout(300);
    const yA = await page.evaluate(() => window.scrollY);
    expect(yA).toBeGreaterThan(100);

    await clickLinkSynthetic(page, 'b.md#tb');
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=b.md');

    await scrollLinkIntoView(page, 'c.md#tc');
    await page.waitForTimeout(300);
    const yB = await page.evaluate(() => window.scrollY);
    expect(yB).toBeGreaterThan(100);

    await clickLinkSynthetic(page, 'c.md#tc');
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=c.md');

    // First back: C → B at yB
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(900);
    expect(page.url()).toContain('file=b.md');
    const backB = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backB - yB)).toBeLessThanOrEqual(15);

    // Second back: B → A at yA
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(900);
    expect(page.url()).toContain('file=a.md');
    const backA = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backA - yA)).toBeLessThanOrEqual(15);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Edge case: forward page is too short to scroll
//
// When B's content fits in the viewport, B's saved scrollY is 0. The
// snapshot-before-innerHTML fix is what makes A's nonzero scroll survive
// into A's history entry — without it, the post-render scrollY read in
// updateURL would clamp to 0 and overwrite A's correct value.
// ─────────────────────────────────────────────────────────────────────────────
test('back from a non-scrollable forward page restores prior scroll', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md':
      '# Page A\n\n' + tallFiller('A-pre', 50) +
      '\n\n[Go to short B](b.md)\n\n' +
      tallFiller('A-post', 50),
    // Deliberately tiny so window.scrollY on B is forced to 0.
    'b.md': '# Page B\n\nThis page is intentionally short.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    await scrollLinkIntoView(page, 'b.md');
    await page.waitForTimeout(300);
    const yA = await page.evaluate(() => window.scrollY);
    expect(yA).toBeGreaterThan(200);

    await clickLinkSynthetic(page, 'b.md');
    await page.waitForTimeout(800);
    expect(page.url()).toContain('file=b.md');
    const yB = await page.evaluate(() => window.scrollY);
    expect(yB).toBe(0);

    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(900);
    expect(page.url()).toContain('file=a.md');
    const backScroll = await page.evaluate(() => window.scrollY);
    expect(Math.abs(backScroll - yA)).toBeLessThanOrEqual(10);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Search scope — folder mode restricts results to the current folder
// ─────────────────────────────────────────────────────────────────────────────
test('search in folder scope returns only current-folder hits', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md', 'beta/b1.md']),
    'alpha/a1.md': '# A1\n\nA paragraph mentioning unicornberry here.\n',
    'alpha/a2.md': '# A2\n\nAnother unicornberry sighting.\n',
    'beta/b1.md':  '# B1\n\nA totally different unicornberry, in beta.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    // Switch to Outline tab and confirm folder mode (default).
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="folder"]'))
      .toHaveAttribute('aria-pressed', 'true');

    await page.locator('#search-input').fill('unicornberry');
    await expect(page.locator('.search-hit')).toHaveCount(2);
    const files = await page.locator('.search-hit').evaluateAll(els => els.map(e => e.dataset.file));
    expect(files.every(f => f.startsWith('alpha/'))).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Search scope — file mode restricts results to the current file
// ─────────────────────────────────────────────────────────────────────────────
test('search in file scope returns only current-file hits', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md']),
    'alpha/a1.md': '# A1\n\nA1 contains the unicornberry token.\n',
    'alpha/a2.md': '# A2\n\nA2 also contains unicornberry.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    // Outline tab → switch its scope to file
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await page.locator('#outline-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');

    await page.locator('#search-input').fill('unicornberry');
    await expect(page.locator('.search-hit')).toHaveCount(1);
    await expect(page.locator('.search-hit').first()).toHaveAttribute('data-file', 'alpha/a1.md');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Search scope — workspace mode groups in-folder vs out-of-folder hits
// ─────────────────────────────────────────────────────────────────────────────
test('workspace search renders in-folder hits, then divider, then other folders', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md', 'beta/b1.md', 'gamma/g1.md']),
    'alpha/a1.md': '# A1\n\nThe ocelotwidget is here.\n',
    'alpha/a2.md': '# A2\n\nAnother ocelotwidget.\n',
    'beta/b1.md':  '# B1\n\nocelotwidget in beta.\n',
    'gamma/g1.md': '# G1\n\nocelotwidget in gamma.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    // Files tab is the default landing tab → workspace scope.
    await page.locator('.sidebar-tab[data-tab="files"]').click();

    await page.locator('#search-input').fill('ocelotwidget');
    await expect(page.locator('.search-hit')).toHaveCount(4);

    // First two hits are alpha (current folder).
    const firstTwo = await page.locator('.search-hit').evaluateAll(els =>
      els.slice(0, 2).map(e => e.dataset.file));
    expect(firstTwo.every(f => f.startsWith('alpha/'))).toBe(true);

    // Exactly one divider, sitting between the alpha hits and the others.
    await expect(page.locator('#search-results .search-sep')).toHaveCount(1);

    // After the divider come the out-of-folder hits (beta + gamma).
    const order = await page.locator('#search-results > *').evaluateAll(els =>
      els.map(e => e.classList.contains('search-sep') ? 'sep' : e.dataset.file));
    const sepIdx = order.indexOf('sep');
    expect(sepIdx).toBeGreaterThan(0);
    expect(order.slice(0, sepIdx).every(f => f.startsWith('alpha/'))).toBe(true);
    expect(order.slice(sepIdx + 1).every(f => !f.startsWith('alpha/'))).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Search click — jump to the matched line, not the file top
// ─────────────────────────────────────────────────────────────────────────────
test('clicking a search hit scrolls to the matched line', async ({ page }) => {
  const port = nextPort();
  // Build a file with the match well below the fold so scrollY > 0 is unambiguous.
  const filler = Array.from({ length: 200 }, (_, i) => `Line ${i + 1} of filler.`).join('\n');
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['big.md']),
    'big.md': `# Big\n\n${filler}\n\nThe quokkasprocket appears far down.\n${filler}\n`,
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=big.md`);
    await expect(page.locator('#content h1')).toHaveText('Big');

    // Sanity: page starts at top.
    expect(await page.evaluate(() => window.scrollY)).toBe(0);

    await page.locator('#search-input').fill('quokkasprocket');
    await expect(page.locator('.search-hit')).toHaveCount(1);
    await page.locator('.search-hit').first().click();

    // After the click resolves, the matched paragraph should be in view —
    // i.e. window.scrollY must have moved off zero.
    await expect.poll(() => page.evaluate(() => window.scrollY), { timeout: 5000 })
      .toBeGreaterThan(50);

    // Search box clears after the click.
    await expect(page.locator('#search-input')).toHaveValue('');
    await expect(page.locator('.search-hit')).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Search click — cross-folder result navigates and switches active folder
// ─────────────────────────────────────────────────────────────────────────────
test('clicking an out-of-folder search hit navigates to the new file', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'beta/b1.md']),
    'alpha/a1.md': '# A1\n\nUnique a-text only here.\n',
    'beta/b1.md':  '# B1\n\nThe lemurspoon is in beta.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    // Files tab → workspace scope; query a term that lives only in beta.
    await page.locator('.sidebar-tab[data-tab="files"]').click();
    await page.locator('#search-input').fill('lemurspoon');
    await expect(page.locator('.search-hit')).toHaveCount(1);
    await page.locator('.search-hit').first().click();

    // currentFile / URL switched to beta
    await expect(page.locator('#content h1')).toHaveText('B1');
    expect(page.url()).toContain('file=beta%2Fb1.md');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// /api/files honors per-subfolder order.json
// ─────────────────────────────────────────────────────────────────────────────
test('subfolder order.json controls file order within that subfolder', async ({ request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    // No top-level order.json → walk falls through to per-folder logic.
    // The subfolder has its OWN order.json that overrides alphabetical.
    'top.md': '# Top\n',
    'sub/order.json': JSON.stringify(['gamma.md', 'alpha.md', 'beta.md']),
    'sub/alpha.md': '# A\n',
    'sub/beta.md':  '# B\n',
    'sub/gamma.md': '# G\n',
    'sub/delta.md': '# D (not in order.json — should appear after, alphabetically)\n',
  });
  const server = await startServer(dir, port);
  try {
    const res = await request.get(`http://localhost:${port}/api/files`);
    expect(res.ok()).toBe(true);
    const data = await res.json();
    const subFiles = data.files.filter(f => f.startsWith('sub/'));
    // gamma → alpha → beta (per order.json), then delta (alphabetical fallback for unlisted).
    expect(subFiles).toEqual([
      'sub/gamma.md',
      'sub/alpha.md',
      'sub/beta.md',
      'sub/delta.md',
    ]);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Live-rescope: typing a query, then toggling scope, re-runs the search
// ─────────────────────────────────────────────────────────────────────────────
test('toggling pane scope re-runs an active search query', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md']),
    'alpha/a1.md': '# A1\n\nThe unicornberry is here in a1.\n',
    'alpha/a2.md': '# A2\n\nA second unicornberry in a2.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('#outline-list .pane-scope-btn[aria-pressed="true"][data-scope="folder"]')).toBeVisible();

    // Type the query while in folder mode → both files match
    await page.locator('#search-input').fill('unicornberry');
    await expect(page.locator('.search-hit')).toHaveCount(2);

    // Switch Outline scope to file → search must re-run, results narrow to current file
    await page.locator('#outline-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('.search-hit')).toHaveCount(1);
    await expect(page.locator('.search-hit').first()).toHaveAttribute('data-file', 'alpha/a1.md');

    // Toggle back to folder → results widen again, no need to retype
    await page.locator('#outline-list .pane-scope-btn[data-scope="folder"]').click();
    await expect(page.locator('.search-hit')).toHaveCount(2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Live-rescope: switching the active sidebar tab also re-runs the search
// ─────────────────────────────────────────────────────────────────────────────
test('switching sidebar tab re-runs an active search query', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md', 'beta/b1.md']),
    'alpha/a1.md': '# A1\n\nThe unicornberry sits in a1.\n',
    'alpha/a2.md': '# A2\n\nAnother unicornberry in a2.\n',
    'beta/b1.md':  '# B1\n\nBeta also has unicornberry.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');

    // Outline tab + folder default → 2 hits in alpha/, 0 elsewhere
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await page.locator('#search-input').fill('unicornberry');
    await expect(page.locator('.search-hit')).toHaveCount(2);

    // Switch to Files tab → workspace scope; re-run picks up beta too
    await page.locator('.sidebar-tab[data-tab="files"]').click();
    await expect(page.locator('.search-hit')).toHaveCount(3);

    // Switch back to Outline → narrows back to 2
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('.search-hit')).toHaveCount(2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// In ring mode, clicking the color dot must toggle the note body expand,
// since the inline ✎ icon is hidden and the dot is now the visible marker.
// ─────────────────────────────────────────────────────────────────────────────
test('ring-mode: clicking the color dot toggles note body expand', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['m.md']),
    'm.md':
      '# Marker\n\nA ==yellow: phrase==[^note-m-1] with a note.\n\n' +
      '[^note-m-1]: A note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=m.md`);
    await expect(page.locator('#content h1')).toHaveText('Marker');

    // Switch to ring mode.
    await page.locator('#settings-btn').click();
    await page.locator('input[name="note-marker"][value="ring"]').check();
    await page.keyboard.press('Escape');            // close the settings sheet (gear is behind the modal)

    // Open Highlights tab.
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    const noted = page.locator('.hl-entry.has-note').first();
    await expect(noted).toHaveCount(1);
    await expect(noted).not.toHaveClass(/hl-note-expanded/);

    // Click the color dot on the noted entry → expand.
    await noted.locator('.hl-entry-dot').click();
    await expect(noted).toHaveClass(/hl-note-expanded/);

    // Click again → collapse.
    await noted.locator('.hl-entry-dot').click();
    await expect(noted).not.toHaveClass(/hl-note-expanded/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Note marker style is settable from the settings panel: icon vs ring
// ─────────────────────────────────────────────────────────────────────────────
test('note-marker setting toggles between icon and ring treatments', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['m.md']),
    'm.md':
      '# Marker test\n\nA ==yellow: phrase==[^note-m-1] with a note.\n\n' +
      '[^note-m-1]: A note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=m.md`);
    await expect(page.locator('#content h1')).toHaveText('Marker test');

    // Open Highlights tab so the noted entry is in the DOM
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('#highlights-list .hl-entry.has-note')).toHaveCount(1);

    // Default is "icon" — html element carries note-marker-icon class, the
    // .hl-note-icon span is visible.
    await expect(page.locator('html')).toHaveClass(/note-marker-icon/);
    await expect(page.locator('.hl-entry.has-note .hl-note-icon')).toBeVisible();

    // Open settings panel and switch to "ring"
    await page.locator('#settings-btn').click();
    await page.locator('input[name="note-marker"][value="ring"]').check();

    await expect(page.locator('html')).toHaveClass(/note-marker-ring/);
    await expect(page.locator('.hl-entry.has-note .hl-note-icon')).toBeHidden();

    // The .hl-entry-dot of the noted entry now has a non-default outline /
    // box-shadow (the ring). Verify some non-zero shadow is set.
    const shadow = await page.locator('.hl-entry.has-note .hl-entry-dot').evaluate(el =>
      getComputedStyle(el).boxShadow
    );
    expect(shadow).not.toBe('none');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Citation refs render with a distinguishing pill background so they're not
// visually confused with footnote-ref superscripts.
// ─────────────────────────────────────────────────────────────────────────────
test('citation refs ([N] -> #ref-N) get an accent pill background', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['index.md']),
    'index.md':
      `# Doc\n\nA citation here <!-- cite:1 --> [[1]](#ref-1) plus a note ref ` +
      `==yellow: phrase==[^note-doc-1].\n\n` +
      `<a id="ref-1"></a>\n[1] Reference body.\n\n` +
      `[^note-doc-1]: A note body.\n`,
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');

    // The citation link has a non-transparent background (the pill).
    const citeBg = await page.locator('a[href="#ref-1"]').first().evaluate(el =>
      getComputedStyle(el).backgroundColor
    );
    expect(citeBg).not.toBe('rgba(0, 0, 0, 0)');
    expect(citeBg).not.toBe('transparent');

    // The footnote ref does NOT inherit the pill — it stays unstyled (transparent).
    const fnBg = await page.locator('sup.footnote-ref a').first().evaluate(el =>
      getComputedStyle(el).backgroundColor
    );
    expect(fnBg === 'rgba(0, 0, 0, 0)' || fnBg === 'transparent').toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Document title reflects the current file (H1 if present, else filename)
// ─────────────────────────────────────────────────────────────────────────────
test('document title is set from H1 on file load', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['intro.md', 'no-h1.md']),
    'intro.md': '# A Custom Title\n\nBody.',
    'no-h1.md': 'Body without an H1.',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=intro.md`);
    await expect(page.locator('#content h1')).toHaveText('A Custom Title');
    await expect(page).toHaveTitle(/A Custom Title/);

    // Navigating to a file without an H1 falls back to the filename.
    await page.evaluate(() => history.pushState(null, '', '?file=no-h1.md'));
    await page.locator('a, .file-entry').filter({ hasText: 'no-h1' }).first().click();
    await expect(page).toHaveTitle(/no-h1/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Footnote-ref click for a NOTED highlight should NOT scroll the document
// to the footnote definition (the note handler scrolls the sidebar instead).
// ─────────────────────────────────────────────────────────────────────────────
test('clicking a noted footnote ref does not scroll document to def', async ({ page }) => {
  const port = nextPort();
  const filler = Array.from({ length: 200 }, (_, i) => `Filler line ${i}.`).join('\n\n');
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['x.md']),
    'x.md':
      `# X\n\n` +
      `An ==yellow: important phrase==[^note-x-1] worth a note.\n\n` +
      filler + `\n\n` +
      `[^note-x-1]: This is the note body.\n`,
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=x.md`);
    await expect(page.locator('#content h1')).toHaveText('X');

    // Position the page so the note ref is in view but well above the footnote def.
    await page.evaluate(() => window.scrollTo(0, 0));
    const ref = page.locator('a[href="#fn1"]').first();
    await ref.scrollIntoViewIfNeeded();
    const beforeY = await page.evaluate(() => window.scrollY);

    await ref.click();
    await page.waitForTimeout(800);
    const afterY = await page.evaluate(() => window.scrollY);

    // Document scroll must NOT have jumped to the bottom (footnote def is at end).
    // A small change is fine; the regression we're guarding against is a multi-
    // thousand-px jump to land on the auto-generated footnotes section.
    expect(Math.abs(afterY - beforeY)).toBeLessThan(200);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Clear-button (X) inside the search input — hidden when empty, clears on click
// ─────────────────────────────────────────────────────────────────────────────
test('search input has a clear button that empties the query', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['a.md']),
    'a.md': '# A\n\nThe unicornberry word lives here.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');

    const clearBtn = page.locator('#search-clear');

    // Initially hidden because input is empty.
    await expect(clearBtn).toBeHidden();

    // Type a query → clear button appears, results render
    await page.locator('#search-input').fill('unicornberry');
    await expect(clearBtn).toBeVisible();
    await expect(page.locator('.search-hit')).toHaveCount(1);

    // Click clear → input empties, results vanish, button hides again
    await clearBtn.click();
    await expect(page.locator('#search-input')).toHaveValue('');
    await expect(page.locator('.search-hit')).toHaveCount(0);
    await expect(clearBtn).toBeHidden();
    // Focus returns to input so the user can immediately retype.
    await expect(page.locator('#search-input')).toBeFocused();
  } finally {
    stopServer(server, dir);
  }
});
