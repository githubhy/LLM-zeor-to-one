// @ts-check
// T6 Part A: anchor-landing clears the sticky reader topbar. In immersive
// (reader/focus) the fixed 44px #reader-topbar would occlude a deep-link /
// palette / outline landing, so every in-content landing target carries
// scroll-margin-top: var(--chrome-top). Docs/classic have no top chrome, so
// --chrome-top is ~0 there. Port base 7350 (new suite; never renumber bases).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { seedSettings } = require('./helpers/layout');

let port = 7350;
const nextPort = () => port++;

const DOC = `# Landing Doc

Intro paragraph.

## Target Heading

Body under the target heading.

A numbered equation <a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

is referenced as equation [(1)](#eq-1).
`;

function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

test('reader mode: a heading clears the topbar (scroll-margin-top >= 56px)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1440, height: 900 });   // desktop reader default
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Landing Doc');
    await expect(page.locator('html')).toHaveClass(/immersive/);
    const sm = await page.evaluate(() => {
      const h = document.querySelector('#content h2');
      return parseFloat(getComputedStyle(h).scrollMarginTop);
    });
    expect(sm).toBeGreaterThanOrEqual(56);
  } finally { stopServer(server, dir); }
});

test('reader mode: an equation anchor clears the topbar (scroll-margin-top >= 56px)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Landing Doc');
    const sm = await page.evaluate(() => {
      const a = document.querySelector('#content [id^="eq-"]');
      return parseFloat(getComputedStyle(a).scrollMarginTop);
    });
    expect(sm).toBeGreaterThanOrEqual(56);
  } finally { stopServer(server, dir); }
});

test('docs mode: a heading uses ~0 scroll-margin-top (no top chrome)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Landing Doc');
    await expect(page.locator('html')).not.toHaveClass(/immersive/);
    const sm = await page.evaluate(() => {
      const h = document.querySelector('#content h2');
      return parseFloat(getComputedStyle(h).scrollMarginTop);
    });
    expect(sm).toBeLessThan(8);
  } finally { stopServer(server, dir); }
});

// Behavioral: scrollToAnchor must land the target at the top (block:'start',
// honoring scroll-margin-top), not centre it. The CSS-only tests above pass even
// with block:'center' (which ignores scroll-margin-top), so this guards the JS.
const DEEP_DOC = `# Landing Doc

Jump to [the deep section](#deep-section).

` + Array.from({ length: 50 }, (_, i) => `Filler paragraph ${i} lorem ipsum dolor sit amet.`).join('\n\n')
  + `

## Deep Section

Body under the deep section.

` + Array.from({ length: 25 }, (_, i) => `Tail filler ${i} lorem ipsum.`).join('\n\n') + '\n';

test('docs mode: navigating to a deep heading lands it at the top, not centred', async ({ page }) => {
  const p = nextPort();
  const dir = createFixtureDir({ 'doc.md': DEEP_DOC });
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });   // --chrome-top ~0, no top bar
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Landing Doc');
    await page.click('#content a[href="#deep-section"]');
    // Wait for the smooth scroll to SETTLE (two consecutive reads agree), not a
    // fixed delay — the ~2000px animation outlasts a naive timeout, and the
    // resting position is what discriminates the fix from the bug.
    await page.waitForFunction(() => {
      const t = document.getElementById('deep-section').getBoundingClientRect().top;
      const settled = window.__pt !== undefined && Math.abs(window.__pt - t) < 0.5;
      window.__pt = t;
      return settled;
    }, null, { timeout: 4000, polling: 100 });
    const top = await page.evaluate(() =>
      Math.round(document.getElementById('deep-section').getBoundingClientRect().top));
    // block:'start' + chrome-top~0 -> rests at the top (~0); block:'center' would
    // rest at ~viewport/2 (450), failing this bound — that is the regression gate.
    expect(top).toBeGreaterThanOrEqual(-4);
    expect(top).toBeLessThan(80);
  } finally { stopServer(server, dir); }
});
