// @ts-check
// Mobile reader shell (redesign 03): at ≤768px the viewer is ALWAYS reader —
// a five-slot bottom toolbar (#mobile-toolbar) opens the sidebar panes as a
// sheet on the same #app.drawer-open machinery. The Plan-04 hamburger + left
// slide-over drawer this file used to pin are retired; per spec section 9
// these assertions are consciously REWRITTEN here, not deleted. Sheet
// geometry / drag / auto-hide coverage lives in reader-shell-mobile.spec.js.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 4900;
function nextPort() { return portCounter++; }

const FIXTURE = {
  'order.json': JSON.stringify(['index.md', 'chap-a.md']),
  'index.md':  '# Index\n\n## Welcome\n\nHello world.',
  'chap-a.md': '# Chapter A\n\n## A.1 First\n\nBody.',
};

test('mobile: bottom toolbar replaces the hamburger; slots open the matching pane', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    // Hamburger retired; the five-slot toolbar is the only opener.
    await expect(page.locator('#sidebar-toggle')).toBeHidden();
    await expect(page.locator('#mobile-toolbar')).toBeVisible();
    await expect(page.locator('#mobile-toolbar [data-mt]')).toHaveCount(5);

    // Closed by default.
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#drawer-backdrop')).toBeHidden();

    // Outline slot opens the sheet on the outline pane over a backdrop.
    await page.locator('#mobile-toolbar [data-mt="outline"]').click();
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await expect(page.locator('#outline-list')).toBeVisible();
    await expect(page.locator('#drawer-backdrop')).toBeVisible();

    // Backdrop tap dismisses. Position is geometry-agnostic: the top-right
    // corner is outside BOTH the T1 interim left drawer and the T2 bottom
    // sheet, so this test survives the Task-2 geometry conversion unchanged.
    await page.locator('#drawer-backdrop').click({ position: { x: 380, y: 30 } });
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#drawer-backdrop')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

test('mobile: search slot opens the sheet and focuses the search input; file open closes', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    // The search slot now opens the command palette (mobile Adaptive Reader Bar
    // T2 — search = the command entry), not the off-canvas sidebar search box.
    await page.locator('#mobile-toolbar [data-mt="search"]').click();
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#cmd-input')).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(page.locator('#cmd-palette')).toBeHidden();

    // Files slot opens its pane; opening a file closes the sheet.
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await page.locator('.file-entry[data-file="chap-a.md"]').click();
    await expect(page.locator('#content h1')).toHaveText('Chapter A');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#drawer-backdrop')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

test('wide viewport, classic: docked sidebar, no backdrop, no mobile toolbar', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1200, height: 800 });
    await pinClassicLayout(page);
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    const app      = page.locator('#app');
    const sidebar  = page.locator('#sidebar');
    const backdrop = page.locator('#drawer-backdrop');
    const content  = page.locator('#content');

    await expect(page.locator('#mobile-toolbar')).toBeHidden();
    await expect(app).not.toHaveClass(/drawer-open/);
    const box = await sidebar.boundingBox();
    expect(box).not.toBeNull();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.width).toBeGreaterThan(0);
    await expect(backdrop).toBeHidden();
    const ml = await content.evaluate(el => parseFloat(getComputedStyle(el).marginLeft) || 0);
    expect(ml).toBeGreaterThan(100);

    // Toggle still performs the desktop dock/collapse (no drawer-open class).
    await page.locator('#sidebar-toggle').click();
    await expect(app).not.toHaveClass(/drawer-open/);
    await expect(sidebar).toHaveClass(/collapsed/);
    await expect(backdrop).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

test('wide viewport, reader: desktop pill present, mobile toolbar absent', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await expect(page.locator('#reader-pill')).toBeVisible();
    await expect(page.locator('#mobile-toolbar')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});
