// @ts-check
// Auto theme (prefers-color-scheme) + density presets (redesign T5).
// Auto resolves the EFFECTIVE theme from the system at runtime and tracks
// system changes live; density presets are ORTHOGONAL to body typography —
// they tune only chrome/navigation/outline/marks/code density via
// --ui-density-lh, never the prose --content-lh / --font-scale / --measure-ch.
// Port base 7320 (new suite; never renumber existing bases).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { seedSettings } = require('./helpers/layout');

let port = 7320;
const nextPort = () => port++;

const DOC = `# Quantization

Intro paragraph one with ==yellow: a marked phrase== inside it for the Marks pane.

## Section A

Body under section A.

\`\`\`
some fenced code so #content pre exists
\`\`\`
`;

function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

// In this repo, prefers-color-scheme media queries re-evaluate live: call
// emulateMedia AFTER goto + content-load, then assert.
test('T5: auto theme resolves the effective theme from the system and follows it live', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { theme: 'auto' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');

    // System reports dark → data-theme reflects the EFFECTIVE dark theme,
    // NOT the literal 'auto'. The stored setting remains 'auto'.
    await page.emulateMedia({ colorScheme: 'dark' });
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    const stored1 = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}').theme);
    expect(stored1).toBe('auto');

    // Flip the system to light → data-theme drops to light (attribute removed
    // for light, per applyTheme), and the stored setting still says 'auto'.
    // The change handler runs a microtask after emulateMedia, so poll.
    await page.emulateMedia({ colorScheme: 'light' });
    await expect.poll(() =>
      page.evaluate(() => document.documentElement.getAttribute('data-theme'))
    ).toBeNull();
    const stored2 = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}').theme);
    expect(stored2).toBe('auto');
  } finally {
    stopServer(server, dir);
  }
});

test('T5: the Auto radio reflects the stored auto theme (data-theme is light/dark, not auto)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    // Seed chrome:'docs' so the docked settings gear (#settings-btn) is visible.
    await seedSettings(page, { theme: 'auto', chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');

    // Open settings (the docked gear is the always-available entry in docs).
    await page.locator('#settings-btn').click();
    const auto = page.locator('input[name="theme"][value="auto"]');
    await expect(auto).toHaveCount(1);
    await expect(auto).toBeChecked();
    // The light/sepia/dark radios are NOT checked even though data-theme may
    // resolve to one of them — the radios track the STORED value (auto).
    await expect(page.locator('input[name="theme"][value="light"]')).not.toBeChecked();
    await expect(page.locator('input[name="theme"][value="dark"]')).not.toBeChecked();
  } finally {
    stopServer(server, dir);
  }
});

test('T5: density presets tune --ui-density-lh but leave the prose --content-lh untouched', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    // Seed chrome:'docs' so the docked settings gear (#settings-btn) is visible.
    await seedSettings(page, { density: 'compact', chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');

    // Compact applies the html.density-compact class and a tighter UI lh.
    await expect(page.locator('html')).toHaveClass(/density-compact/);
    const compact = await page.evaluate(() => ({
      ui: getComputedStyle(document.documentElement).getPropertyValue('--ui-density-lh').trim(),
      content: getComputedStyle(document.documentElement).getPropertyValue('--content-lh').trim(),
    }));
    expect(parseFloat(compact.ui)).toBeCloseTo(1.25, 2);
    // Body prose line-height is the slider default (1.7), untouched by density.
    expect(parseFloat(compact.content)).toBeCloseTo(1.7, 2);

    // Switch to spacious via the settings radio → --ui-density-lh loosens but
    // --content-lh is still the prose default.
    await page.locator('#settings-btn').click();
    await page.locator('input[name="density-mode"][value="spacious"]').check();
    await expect(page.locator('html')).toHaveClass(/density-spacious/);
    const spacious = await page.evaluate(() => ({
      ui: getComputedStyle(document.documentElement).getPropertyValue('--ui-density-lh').trim(),
      content: getComputedStyle(document.documentElement).getPropertyValue('--content-lh').trim(),
    }));
    expect(parseFloat(spacious.ui)).toBeGreaterThan(parseFloat(compact.ui));
    expect(parseFloat(spacious.content)).toBeCloseTo(1.7, 2);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #8/#22: FOUC guard resolves theme:auto pre-paint ─────────

test('FOUC: theme:auto on a dark OS stamps data-theme=dark before first paint', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    // The OS reports dark BEFORE navigation, so the inline head guard (which runs
    // synchronously before first paint) must resolve auto→dark via matchMedia
    // and stamp data-theme=dark — no light flash, no waiting for the module JS.
    await page.emulateMedia({ colorScheme: 'dark' });
    await seedSettings(page, { theme: 'auto' });
    await page.setViewportSize({ width: 1440, height: 900 });
    // Pause module JS so we observe the PRE-PAINT (guard-only) DOM state: the
    // attribute must already be present from the inline guard, not applyTheme().
    await page.route('**/viewer.js', () => {});   // never resolves → module never loads
    await page.goto(`http://localhost:${p}/?file=doc.md`, { waitUntil: 'commit' }).catch(() => {});
    await expect.poll(() =>
      page.evaluate(() => document.documentElement.getAttribute('data-theme'))
    ).toBe('dark');
    // The browser-chrome tint also flips to the dark surface pre-paint.
    const tint = await page.evaluate(() =>
      document.querySelector('meta[name="theme-color"]')?.getAttribute('content'));
    expect(tint).toBe('#1a1d23');
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #10: FOUC guard stamps the density class pre-paint ───────

test('FOUC: density:compact stamps html.density-compact before first paint', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { density: 'compact' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.route('**/viewer.js', () => {});   // block the module → guard-only state
    await page.goto(`http://localhost:${p}/?file=doc.md`, { waitUntil: 'commit' }).catch(() => {});
    await expect.poll(() =>
      page.evaluate(() => document.documentElement.classList.contains('density-compact'))
    ).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #21: cycling the theme from 'auto' is deterministic ──────

test('theme cycle from auto advances from the effective theme (never lands on the visible theme)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    // Auto on a LIGHT OS → effective theme is light. The OLD code did
    // THEME_CYCLE[(indexOf('auto')+1)%3] = THEME_CYCLE[0] = 'light', i.e. it
    // "advanced" auto straight back to the theme the user already sees (a no-op
    // jump that loses the auto preference). The fix cycles from the EFFECTIVE
    // theme, so light → sepia: cycling must ADVANCE, not reset to the visible one.
    await page.emulateMedia({ colorScheme: 'light' });
    await seedSettings(page, { theme: 'auto' });   // reader default → #rt-theme top-bar button visible
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');
    await expect.poll(() =>   // auto→light: data-theme attribute is removed for light
      page.evaluate(() => document.documentElement.getAttribute('data-theme'))).toBeNull();

    // Cycle once: effective light → sepia (NOT light). This is the assertion the
    // old indexOf(-1) reset would fail.
    await page.locator('#rt-theme').click();
    const stored = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}').theme);
    expect(stored).toBe('sepia');
    // Continuing the cycle is the normal sepia → dark ring.
    await page.locator('#rt-theme').click();
    expect(await page.evaluate(() =>
      JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}').theme)).toBe('dark');
  } finally {
    stopServer(server, dir);
  }
});
