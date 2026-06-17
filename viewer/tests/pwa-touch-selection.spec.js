// @ts-check
// Task 7 (Plan 04, iOS PWA Viewer): iOS touch selection-toolbar.
//
// These tests run under touch emulation at iPhone-12 dimensions and exercise
// the selectionchange-driven toolbar show path, the catch-22 hide fix (a stray
// tap to dismiss the native selection-callout must NOT nuke the toolbar while a
// non-collapsed selection persists), and the safe-area-aware position clamps.
//
// IMPORTANT: headless Chromium under `hasTouch` cannot reproduce the *real* iOS
// system selection-callout (magnifier / Copy / Define), VoiceOver, or finger
// ergonomics. What it CAN verify is the JS contract: selectionchange shows the
// toolbar from the selection rect, the toolbar lands inside the viewport, and
// the guarded pointerdown predicate keeps it alive across a neutral tap. The
// device-only behaviors are listed in the Task 9 manual checklist.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4960;
function nextPort() { return portCounter++; }

const VW = 390;
const VH = 844;
// Allow a small slack for sub-pixel rounding + safe-area margins.
const SLACK = 1;

test.use({ hasTouch: true, viewport: { width: VW, height: VH } });

// Long body so a selection near the top has a sensible rect and the toolbar
// has somewhere to clamp to.
const BODY =
  '# Touch\n\n' +
  'This is a long paragraph of selectable body text that spans enough width ' +
  'to give the selection a real bounding rectangle for the toolbar to anchor ' +
  'against on a narrow touch viewport. The quick brown fox jumps over the lazy ' +
  'dog while we test the iOS selection toolbar behaviour end to end.\n';

/**
 * Programmatically select a sub-range of the first paragraph's first text node
 * and fire a `selectionchange` (the iOS-path trigger), with clientX/clientY = 0
 * to emulate the native-callout-active state where mouse coords are unusable.
 */
async function selectViaSelectionChange(page, startOff, endOff) {
  await page.evaluate(({ s, e }) => {
    const p = document.querySelector('#content p');
    const tn = p.firstChild;
    const sel = window.getSelection();
    sel.removeAllRanges();
    const r = document.createRange();
    r.setStart(tn, s);
    r.setEnd(tn, e);
    sel.addRange(r);
    // iOS callout-active: clientX/clientY are 0 — the show path must use the
    // selection rect, not the (absent) pointer coordinates.
    document.dispatchEvent(new Event('selectionchange', { bubbles: false }));
  }, { s: startOff, e: endOff });
}

// ─────────────────────────────────────────────────────────────────────────────
// 1) selectionchange shows the toolbar, positioned inside the viewport.
// ─────────────────────────────────────────────────────────────────────────────
test('selectionchange shows the toolbar inside the viewport (no clientX/Y)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'touch.md': BODY });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=touch.md`);
    await expect(page.locator('#content p')).toBeVisible();

    await selectViaSelectionChange(page, 5, 40);
    // selectionchange listener is debounced ~120ms.
    const toolbar = page.locator('#hl-toolbar');
    await expect(toolbar).toHaveClass(/visible/, { timeout: 2000 });

    const box = await toolbar.boundingBox();
    expect(box).not.toBeNull();
    expect(box.x).toBeGreaterThanOrEqual(-SLACK);
    expect(box.y).toBeGreaterThanOrEqual(-SLACK);
    expect(box.x + box.width).toBeLessThanOrEqual(VW + SLACK);
    expect(box.y + box.height).toBeLessThanOrEqual(VH + SLACK);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 2) Catch-22 fix: a neutral tap (callout-dismiss) while a non-collapsed
//    selection persists must NOT hide the toolbar.
// ─────────────────────────────────────────────────────────────────────────────
test('neutral tap does not hide the toolbar while a non-collapsed selection persists', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'touch.md': BODY });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=touch.md`);
    await expect(page.locator('#content p')).toBeVisible();

    await selectViaSelectionChange(page, 5, 40);
    const toolbar = page.locator('#hl-toolbar');
    await expect(toolbar).toHaveClass(/visible/, { timeout: 2000 });

    // Simulate the system selection-callout dismissal tap: a pointerdown on a
    // neutral region that is NOT inside #hl-toolbar, while the selection is
    // still non-collapsed. The guarded predicate must keep the toolbar alive.
    await page.evaluate(() => {
      // Tap target: the content paragraph (inside the selected content area),
      // which is the realistic place the callout-dismiss tap lands.
      const target = document.querySelector('#content p');
      target.dispatchEvent(new PointerEvent('pointerdown', {
        bubbles: true, clientX: 50, clientY: 200,
      }));
    });
    // Give any (buggy) hide a chance to run.
    await page.waitForTimeout(200);
    await expect(toolbar).toHaveClass(/visible/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 3) A genuine outside tap with the selection collapsed DOES hide the toolbar
//    (the guard must not become a toolbar that never closes).
// ─────────────────────────────────────────────────────────────────────────────
test('outside tap with collapsed selection still hides the toolbar', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'touch.md': BODY });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=touch.md`);
    await expect(page.locator('#content p')).toBeVisible();

    await selectViaSelectionChange(page, 5, 40);
    const toolbar = page.locator('#hl-toolbar');
    await expect(toolbar).toHaveClass(/visible/, { timeout: 2000 });

    // Collapse the selection, then tap outside the content (chrome/empty space).
    await page.evaluate(() => {
      window.getSelection().removeAllRanges();
      document.body.dispatchEvent(new PointerEvent('pointerdown', {
        bubbles: true, clientX: 5, clientY: 5,
      }));
    });
    await page.waitForTimeout(100);
    await expect(toolbar).not.toHaveClass(/visible/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 4) savedRange survives show→tap: applying a color after the toolbar shows
//    via selectionchange still writes to source (selection not lost on touch).
// ─────────────────────────────────────────────────────────────────────────────
test('color applies from a selectionchange-shown toolbar (savedRange intact)', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'apply.md': '# Apply\n\nThe quick brown fox jumps over the lazy dog.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=apply.md`);
    await expect(page.locator('#content p')).toBeVisible();

    // Select "brown" (chars 10..15) via the iOS selectionchange path.
    await selectViaSelectionChange(page, 10, 15);
    const toolbar = page.locator('#hl-toolbar');
    await expect(toolbar).toHaveClass(/visible/, { timeout: 2000 });

    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(200);

    const res = await request.get(`http://localhost:${port}/api/md/apply.md`);
    const txt = await res.text();
    expect(txt).toContain('==orange: brown==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 6) Debounce-dismiss regression: hiding during the 120ms debounce window must
//    cancel the pending show so the toolbar does NOT reappear after the timer
//    fires. Reproduces the bug where Escape/scroll/tap-away during the window
//    let the timer fire and re-pop the toolbar (selection still non-collapsed).
// ─────────────────────────────────────────────────────────────────────────────
test('toolbar does not reappear after dismissal during the debounce window', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'touch.md': BODY });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=touch.md`);
    await expect(page.locator('#content p')).toBeVisible();

    // Kick off a selection (starts the 120ms debounce timer) but immediately
    // dismiss via hideToolbar() — BEFORE the debounce fires — so the timer is
    // pending when the dismiss runs. Also collapse the selection so that any
    // native selectionchange the browser fires after removeAllRanges does not
    // re-arm the timer (collapsed selection is ignored by the debounced handler).
    await page.evaluate(({ s, e }) => {
      const p = document.querySelector('#content p');
      const tn = p.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, s);
      r.setEnd(tn, e);
      sel.addRange(r);
      // Dispatch selectionchange to start the debounce timer.
      document.dispatchEvent(new Event('selectionchange', { bubbles: false }));
      // Immediately dismiss: Escape fires hideToolbar() which must cancel the
      // pending timer. We also collapse the selection so any follow-on native
      // selectionchange (from removeAllRanges) produces a collapsed selection
      // that the debounced handler ignores.
      sel.removeAllRanges();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    }, { s: 5, e: 40 });

    // Wait longer than the 120ms debounce window to give any leaky timer a
    // chance to fire, then assert the toolbar is still hidden.
    await page.waitForTimeout(250);
    const toolbar = page.locator('#hl-toolbar');
    await expect(toolbar).not.toHaveClass(/visible/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 5) Touch target sizing: at narrow width, swatches/buttons are >=40px.
// ─────────────────────────────────────────────────────────────────────────────
test('touch targets are at least 40px at narrow width', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'touch.md': BODY });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=touch.md`);
    await expect(page.locator('#content p')).toBeVisible();

    await selectViaSelectionChange(page, 5, 40);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/, { timeout: 2000 });

    const swatch = page.locator('#hl-toolbar .hl-swatch').first();
    const sBox = await swatch.boundingBox();
    expect(sBox.width).toBeGreaterThanOrEqual(40 - SLACK);
    expect(sBox.height).toBeGreaterThanOrEqual(40 - SLACK);
  } finally {
    stopServer(server, dir);
  }
});
