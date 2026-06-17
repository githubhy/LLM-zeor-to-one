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
