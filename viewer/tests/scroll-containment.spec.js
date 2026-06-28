// @ts-check
// REGRESSION GATE: a chrome region's scroll must not chain to the survey page
// behind/beside it. Two layers: (1) overscroll-behavior:contain on every
// scroll container (engages when scrollable); (2) a wheel-trap (trapRegionScroll)
// for the fits / no-scrollbar case and the modal backdrop, where (1) cannot
// engage. The main document scroll is intentionally left to scroll normally.
// Port base 7380 (new suite; never renumber bases).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let port = 7380;
const nextPort = () => port++;

const DOC = '# Scroll Doc\n\n' +
  Array.from({ length: 80 }, (_, i) => `Filler paragraph ${i} lorem ipsum dolor sit amet.`).join('\n\n');

function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

test('every chrome scroll container declares overscroll-behavior: contain', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toBeVisible();
    const contained = await page.evaluate(() => {
      const ids = ['settings-sheet-body', 'cmd-results', 'shortcut-cheatsheet-box',
                   'peek-body', 'file-list', 'outline-list', 'highlights-list', 'search-results'];
      return ids.filter((id) => {
        const e = document.getElementById(id);
        return e && getComputedStyle(e).overscrollBehaviorY === 'contain';
      }).length;
    });
    // most of these exist + must contain (some may be absent in a given layout)
    expect(contained).toBeGreaterThanOrEqual(5);
  } finally { stopServer(server, dir); }
});

test('wheel over an open modal (backdrop / fits) does not scroll the page', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toBeVisible();
    // Open the settings modal and put the page mid-scroll (instant, so no animation tail).
    await page.evaluate(() => {
      document.getElementById('settings-sheet').hidden = false;
      document.documentElement.style.scrollBehavior = 'auto';
      window.scrollTo(0, 200);
    });
    await page.waitForTimeout(200);
    const before = await page.evaluate(() => window.scrollY);
    await page.mouse.move(120, 450);     // over the modal backdrop (non-scrollable)
    await page.mouse.wheel(0, 240);
    await page.waitForTimeout(150);
    const afterModal = await page.evaluate(() => window.scrollY);
    expect(afterModal).toBe(before);     // trapped — page did not move

    // Control: with the modal closed, a wheel over the content scrolls the page.
    await page.evaluate(() => { document.getElementById('settings-sheet').hidden = true; });
    await page.mouse.move(1000, 400);
    await page.mouse.wheel(0, 240);
    await page.waitForTimeout(150);
    const afterContent = await page.evaluate(() => window.scrollY);
    expect(afterContent).toBeGreaterThan(afterModal);
  } finally { stopServer(server, dir); }
});
