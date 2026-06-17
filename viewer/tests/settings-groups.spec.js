// @ts-check
// Settings panel — theme, typography, and font groups wiring
// ─────────────────────────────────────────────────────────────────────────────
// Coverage:
//   G1  Theme radios -> html[data-theme] attribute and meta theme-color tint
//   G2  Theme change persists across reload (settings store roundtrip)
//   G3  Font-scale slider -> --font-scale CSS custom property
//   G4  Line-height slider -> --content-lh CSS custom property
//   G5  Content-max slider -> --content-max CSS custom property
//   G6  Typography settings persist across reload
//   G7  Font-family radio -> --content-font CSS custom property (serif sets it,
//       sans removes it)
//   G8  Font-family setting persists across reload
//
// Each test uses its own server+port so they can run in parallel if the
// Playwright config ever switches to workers > 1.

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 5700;
function nextPort() { return portCounter++; }

// Panel reached via the docked-sidebar gear — pin classic layout (see
// helpers/layout.js; merge-write keeps G2/G6/G8 persistence intact).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

const FIXTURE = {
  'order.json': JSON.stringify(['index.md']),
  'index.md': '# Settings Groups Test\n\nBody paragraph.\n',
};

const SETTINGS_KEY = 'viewer.settings.v1';

// ─────────────────────────────────────────────────────────────────────────────
// G1 — Theme radios -> html[data-theme] + meta[name="theme-color"] tint
// ─────────────────────────────────────────────────────────────────────────────
test('G1: theme radios update html[data-theme] and meta theme-color', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Default: light — no data-theme attribute on <html>
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.*/);

    // Open settings panel
    await page.locator('#settings-btn').click();

    // Switch to dark
    await page.locator('input[name="theme"][value="dark"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    const darkTint = await page.evaluate(() =>
      document.querySelector('meta[name="theme-color"]')?.getAttribute('content')
    );
    expect(darkTint).toBe('#1a1d23');

    // Switch to sepia
    await page.locator('input[name="theme"][value="sepia"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'sepia');
    const sepiaTint = await page.evaluate(() =>
      document.querySelector('meta[name="theme-color"]')?.getAttribute('content')
    );
    expect(sepiaTint).toBe('#8a5a2b');

    // Switch back to light — data-theme removed
    await page.locator('input[name="theme"][value="light"]').check();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.*/);
    const lightTint = await page.evaluate(() =>
      document.querySelector('meta[name="theme-color"]')?.getAttribute('content')
    );
    expect(lightTint).toBe('#2563EB');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G2 — Theme setting persists across reload
// ─────────────────────────────────────────────────────────────────────────────
test('G2: theme setting persists across reload', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Switch to sepia via the settings panel
    await page.locator('#settings-btn').click();
    await page.locator('input[name="theme"][value="sepia"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'sepia');

    // Verify localStorage stored the value
    const stored = await page.evaluate((key) => {
      try { return JSON.parse(localStorage.getItem(key) || '{}').theme; }
      catch (e) { return null; }
    }, SETTINGS_KEY);
    expect(stored).toBe('sepia');

    // Reload and check the FOUC guard restored data-theme before JS ran,
    // and that after JS init the radio is correctly checked.
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'sepia');

    await page.locator('#settings-btn').click();
    await expect(page.locator('input[name="theme"][value="sepia"]')).toBeChecked();
    await expect(page.locator('input[name="theme"][value="light"]')).not.toBeChecked();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G3 — Font-scale slider -> --font-scale CSS custom property
// ─────────────────────────────────────────────────────────────────────────────
test('G3: font-scale slider updates --font-scale custom property', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Read default --font-scale (expect "1")
    const defaultScale = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--font-scale').trim()
    );
    expect(defaultScale).toBe('1');

    // Move the slider to 1.1 via JS dispatch
    await page.locator('#settings-btn').click();
    await page.locator('#setting-font-scale').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '1.1';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    const newScale = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--font-scale').trim()
    );
    expect(parseFloat(newScale)).toBeCloseTo(1.1, 2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G4 — Line-height slider -> --content-lh CSS custom property
// ─────────────────────────────────────────────────────────────────────────────
test('G4: line-height slider updates --content-lh custom property', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Default --content-lh should be 1.7
    const defaultLh = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--content-lh').trim()
    );
    expect(parseFloat(defaultLh)).toBeCloseTo(1.7, 2);

    await page.locator('#settings-btn').click();
    await page.locator('#setting-line-height').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '1.9';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    const newLh = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--content-lh').trim()
    );
    expect(parseFloat(newLh)).toBeCloseTo(1.9, 2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G5 — Measure slider -> --measure-ch CSS custom property
// ─────────────────────────────────────────────────────────────────────────────
test('G5: measure slider updates --measure-ch custom property', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Default --measure-ch should be 66ch
    const defaultMax = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--measure-ch').trim()
    );
    expect(defaultMax).toBe('66ch');

    await page.locator('#settings-btn').click();
    await page.locator('#setting-measure-ch').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '72';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    const newMax = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--measure-ch').trim()
    );
    expect(newMax).toBe('72ch');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G6 — Typography settings (fontScale, lineHeight, contentMax) persist across reload
// ─────────────────────────────────────────────────────────────────────────────
test('G6: typography settings persist across reload', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    await page.locator('#settings-btn').click();

    // Set fontScale to 1.2
    await page.locator('#setting-font-scale').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '1.2';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    // Set lineHeight to 1.8
    await page.locator('#setting-line-height').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '1.8';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    // Set measureCh to 72
    await page.locator('#setting-measure-ch').evaluate((el) => {
      (/** @type {HTMLInputElement} */ (el)).value = '72';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    // Verify stored
    const stored = await page.evaluate((key) => {
      try { return JSON.parse(localStorage.getItem(key) || '{}'); }
      catch (e) { return {}; }
    }, SETTINGS_KEY);
    expect(parseFloat(stored.fontScale)).toBeCloseTo(1.2, 2);
    expect(parseFloat(stored.lineHeight)).toBeCloseTo(1.8, 2);
    expect(stored.measureCh).toBe(72);

    // Reload and verify CSS properties restored
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    const scale = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--font-scale').trim()
    );
    expect(parseFloat(scale)).toBeCloseTo(1.2, 2);

    const lh = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--content-lh').trim()
    );
    expect(parseFloat(lh)).toBeCloseTo(1.8, 2);

    const max = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--measure-ch').trim()
    );
    expect(max).toBe('72ch');

    // And verify slider values reflect the stored settings
    await page.locator('#settings-btn').click();
    const scaleVal = await page.locator('#setting-font-scale').inputValue();
    expect(parseFloat(scaleVal)).toBeCloseTo(1.2, 2);
    const lhVal = await page.locator('#setting-line-height').inputValue();
    expect(parseFloat(lhVal)).toBeCloseTo(1.8, 2);
    const maxVal = await page.locator('#setting-measure-ch').inputValue();
    expect(parseInt(maxVal, 10)).toBe(72);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G7 — Font-family radio -> --content-font CSS custom property
//      serif sets it; sans removes it (falls back to CSS default)
// ─────────────────────────────────────────────────────────────────────────────
test('G7: content-font radios update --content-font custom property', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Default (sans): --content-font should not be set (empty string)
    const defaultFont = await page.evaluate(() =>
      document.documentElement.style.getPropertyValue('--content-font')
    );
    expect(defaultFont).toBe('');

    await page.locator('#settings-btn').click();

    // Switch to serif
    await page.locator('input[name="content-font"][value="serif"]').check();
    const serifFont = await page.evaluate(() =>
      document.documentElement.style.getPropertyValue('--content-font')
    );
    expect(serifFont).toContain('serif');
    expect(serifFont.length).toBeGreaterThan(0);

    // Switch back to sans — property removed
    await page.locator('input[name="content-font"][value="sans"]').check();
    const sansFont = await page.evaluate(() =>
      document.documentElement.style.getPropertyValue('--content-font')
    );
    expect(sansFont).toBe('');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// G8 — Font-family setting persists across reload
// ─────────────────────────────────────────────────────────────────────────────
test('G8: font-family setting persists across reload', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    // Set to serif
    await page.locator('#settings-btn').click();
    await page.locator('input[name="content-font"][value="serif"]').check();

    // Verify stored
    const stored = await page.evaluate((key) => {
      try { return JSON.parse(localStorage.getItem(key) || '{}').fontFamily; }
      catch (e) { return null; }
    }, SETTINGS_KEY);
    expect(stored).toBe('serif');

    // Reload and verify --content-font was restored
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Settings Groups Test');

    const font = await page.evaluate(() =>
      document.documentElement.style.getPropertyValue('--content-font')
    );
    expect(font).toContain('serif');
    expect(font.length).toBeGreaterThan(0);

    // Radio should reflect serif selection
    await page.locator('#settings-btn').click();
    await expect(page.locator('input[name="content-font"][value="serif"]')).toBeChecked();
    await expect(page.locator('input[name="content-font"][value="sans"]')).not.toBeChecked();
  } finally {
    stopServer(server, dir);
  }
});
