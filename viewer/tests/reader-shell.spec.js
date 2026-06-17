// @ts-check
// Redesign 02: Reader layout mode on desktop (spec sections 3-4). Classic
// mode must render today's UI; everything new is scoped to
// html[data-chrome="reader"] at >768px.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 5900; // base distinct from settings-groups.spec.js (5700) and theme-typography.spec.js (5800)
function nextPort() { return portCounter++; }

const DOC = `# Reader Doc

## Section One

${'Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod.\n\n'.repeat(30)}
## Section Two

${'Tempor incididunt ut labore et dolore magna aliqua ut enim ad minim.\n\n'.repeat(30)}
`;

async function boot(page, port, opts = {}) {
  const dir = createFixtureDir({ 'doc.md': DOC });
  const server = await startServer(dir, port);
  if (opts.layout) {
    await page.addInitScript((layout) => {
      localStorage.setItem('viewer.settings.v1', JSON.stringify({ layout }));
    }, opts.layout);
  }
  await page.goto(`http://localhost:${port}?file=doc.md`);
  await expect(page.locator('#content h1')).toHaveText('Reader Doc');
  return { dir, server };
}

test('T1: desktop defaults to reader layout and the attribute persists', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'reader');
    // Switch to classic via the settings radio; attribute + persistence.
    // In reader mode the Aa top-bar button is the settings entry (the docked
    // gear is off-canvas) — it opens the dedicated #settings-sheet.
    await page.locator('#rt-aa').click();
    await page.locator('input[name="chrome-mode"][value="docs"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
  } finally { await stopServer(server); }
});

test('T1: classic layout renders the docked desktop shell (behavioral parity)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    const sb = page.locator('#sidebar');
    await expect(sb).toBeVisible();
    const box = await sb.boundingBox();
    expect(box.x).toBe(0); // docked, not off-canvas
    await expect(page.locator('#sidebar-toggle')).toBeVisible();
  } finally { await stopServer(server); }
});

test('T2: reader mode hides the docked sidebar and toggle; panes open as overlay sheets', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    // Sidebar off-canvas, toggle hidden, content centered (no left margin).
    await expect(page.locator('#sidebar-toggle')).toBeHidden();
    const sbBox = await page.locator('#sidebar').boundingBox();
    expect(sbBox === null || sbBox.x < 0 || sbBox.x + sbBox.width <= 0).toBeTruthy();
    const ml = await page.evaluate(() => getComputedStyle(document.getElementById('content')).marginLeft);
    expect(parseFloat(ml)).toBeGreaterThan(40); // auto-centered, not var(--sidebar-w)-pinned
    // Drawer-open machinery works at desktop width in reader mode.
    // Poll: the sheet inherits the base 0.2s slide transition.
    await page.evaluate(() => { document.getElementById('app').classList.add('drawer-open'); });
    await expect.poll(async () => (await page.locator('#sidebar').boundingBox()).x).toBe(0);
    // Esc closes it (guard generalized beyond mqlNarrow).
    await page.keyboard.press('Escape');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
  } finally { await stopServer(server); }
});

test('T2: keyboard shortcuts drive the overlay sheet in reader mode', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    // Ctrl+B toggles the sheet (not the invisible .collapsed state).
    await page.keyboard.press('Control+b');
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await page.keyboard.press('Control+b');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    // Ctrl+Shift+O opens the sheet on the outline pane.
    await page.keyboard.press('Control+Shift+o');
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
  } finally { await stopServer(server); }
});

test('T2: classic mode keeps the collapse behavior (no overlay)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    await page.locator('#sidebar-toggle').click();
    await expect(page.locator('#sidebar')).toHaveClass(/collapsed/);
    await page.locator('#sidebar-toggle').click();
    await expect(page.locator('#sidebar')).not.toHaveClass(/collapsed/);
  } finally { await stopServer(server); }
});

test('T3: reader top bar shows the file breadcrumb; Aa opens the sheet with settings; theme button cycles', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#reader-topbar')).toBeVisible();
    await expect(page.locator('#reader-crumb')).toHaveText('doc.md');
    await page.locator('#rt-theme').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'sepia');
    await page.locator('#rt-theme').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await page.locator('#rt-aa').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
  } finally { await stopServer(server); }
});

test('T3: classic mode never shows the top bar', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    await expect(page.locator('#reader-topbar')).toBeHidden();
  } finally { await stopServer(server); }
});

test('T4: pill buttons open the matching pane as a sheet; pct tracks scroll', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#reader-pill')).toBeVisible();
    await page.locator('[data-pill="outline"]').click();
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await page.keyboard.press('Escape');
    // Pct updates with scroll (converge like the progress spec).
    await page.evaluate(() => window.scrollTo({ top: 1e9, behavior: 'instant' }));
    await page.waitForFunction(() => {
      const t = document.getElementById('pill-pct')?.textContent || '';
      return parseInt(t, 10) >= 99;
    });
  } finally { await stopServer(server); }
});

test('T4: classic mode never shows the pill', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    await expect(page.locator('#reader-pill')).toBeHidden();
  } finally { await stopServer(server); }
});

test('T5: chrome hides on scroll-down, returns on scroll-up, never hides when content fits', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForFunction(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    // Reveal via repeated upward nudges, not a one-shot scroll: under CPU
    // load Chromium can drop the rAF tick for a single synthetic scroll
    // (flaked twice under brew-upgrade / orphan-process load). Real users
    // self-heal on the next scroll event; the poll mirrors that. Converges
    // even if nudges hit the top — y < 60 always reveals.
    await expect.poll(async () => {
      await page.evaluate(() => window.scrollBy({ top: -60, behavior: 'instant' }));
      return page.evaluate(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    }).toBe(false);
  } finally { await stopServer(server); }
});

test('T5: classic mode never gets the chrome-hidden class', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    expect(has).toBe(false);
  } finally { await stopServer(server); }
});

test('T6: rail fill tracks scroll; click jumps; legacy top bar hidden in reader; rail honors the progress setting', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#reader-rail')).toBeVisible();
    await expect(page.locator('#reading-progress')).toBeHidden();
    await page.evaluate(() => window.scrollTo({ top: 1e9, behavior: 'instant' }));
    await page.waitForFunction(() => {
      const h = parseFloat(document.getElementById('reader-rail-fill').style.height || '0');
      return h >= 99;
    });
    // Click near the top quarter of the rail jumps the scroll position up.
    const rail = page.locator('#reader-rail');
    const box = await rail.boundingBox();
    await page.mouse.click(box.x + box.width / 2, box.y + box.height * 0.25);
    await page.waitForFunction(() => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      return window.scrollY < max * 0.5;
    });
    // Progress setting hides the rail too.
    await page.locator('#rt-aa').click();
    await page.locator('#setting-reading-progress').uncheck();
    await expect(page.locator('#reader-rail')).toBeHidden();
  } finally { await stopServer(server); }
});

test('T6: classic keeps the legacy top progress bar and no rail', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    await expect(page.locator('#reading-progress')).toBeAttached();
    await expect(page.locator('#reader-rail')).toBeHidden();
  } finally { await stopServer(server); }
});

// ── Quality-review regressions (redesign 02 QR) ─────────────────────────────

test('redesign 05: Ctrl+K opens the command palette in reader mode (was: open sheet + focus search)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    // Ctrl+K now opens the top-level command palette, not the sidebar sheet
    // (redesign 05). The QR off-canvas-focus concern this test originally
    // pinned is moot for a modal that lives outside the transformed sidebar;
    // the sidebar search box stays reachable by click / the mobile search slot.
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#cmd-input')).toBeFocused();
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#search-input')).not.toBeFocused();
  } finally { await stopServer(server); }
});

test('QR: Ctrl+Shift+O reopens the sheet on the outline pane even when outline is already active', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+Shift+O');
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('#outline-list')).toBeVisible();
    // Close the sheet; activeTab stays 'outline'. Reopening must show the
    // OUTLINE pane, not toggle to files (pre-fix behavior).
    await page.keyboard.press('Escape');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await page.keyboard.press('Control+Shift+O');
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('#outline-list')).toBeVisible();
  } finally { await stopServer(server); }
});

test('QR: clicking a noted footnote ref opens the sheet on the note entry in reader mode', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'ref-click.md': '# Test fixture\n\nLead ==yellow:noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=ref-click.md`);
    await page.waitForLoadState('networkidle');
    await page.locator('sup.footnote-ref a').first().click();
    // Pre-fix: the highlights tab activated invisibly inside the off-canvas
    // sidebar and the click read as a no-op.
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('.highlights-entry.hl-note-expanded')).toBeVisible();
  } finally { stopServer(server, dir); }
});

test('classic: #sidebar-toggle exposes collapse state via aria (redesign 04 — byte-identity bar retired)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { layout: 'classic' });
  try {
    const toggle = page.locator('#sidebar-toggle');
    // The pre-redesign UI exposed no ARIA state; behavioral parity does not
    // require preserving the gap (spec section 6 — parity of affordances).
    expect(await toggle.getAttribute('aria-controls')).toBe('sidebar');
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await toggle.click();
    await expect(page.locator('#sidebar')).toHaveClass(/collapsed/);
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
    // Ctrl+B shares the same mutation point.
    await page.keyboard.press('Control+b');
    await expect(page.locator('#sidebar')).not.toHaveClass(/collapsed/);
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  } finally { await stopServer(server); }
});

test('classic: switching reader → classic stamps the toggle aria (mode-switch path)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port); // boots reader (default)
  try {
    await page.locator('#rt-aa').click();
    await page.locator('input[name="chrome-mode"][value="docs"]').check();
    await expect(page.locator('#sidebar-toggle')).toBeVisible();
    await expect(page.locator('#sidebar-toggle')).toHaveAttribute('aria-expanded', 'true');
  } finally { await stopServer(server); }
});

test('QR: theme radios track the top-bar cycle button', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#rt-theme').click(); // light -> sepia
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'sepia');
    await page.locator('#rt-aa').click(); // open sheet with settings panel
    await expect(page.locator('input[name="theme"][value="sepia"]')).toBeChecked();
    await expect(page.locator('input[name="theme"][value="light"]')).not.toBeChecked();
  } finally { await stopServer(server); }
});

test('QR: print media hides all reader chrome and drops the top-bar content padding', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.emulateMedia({ media: 'print' });
    const vis = await page.evaluate(() => ({
      topbar: getComputedStyle(document.getElementById('reader-topbar')).display,
      pill: getComputedStyle(document.getElementById('reader-pill')).display,
      rail: getComputedStyle(document.getElementById('reader-rail')).display,
      legacy: getComputedStyle(document.getElementById('reading-progress')).display,
      contentPadTop: getComputedStyle(document.getElementById('content')).paddingTop,
    }));
    expect(vis.topbar).toBe('none');
    expect(vis.pill).toBe('none');
    expect(vis.rail).toBe('none');
    expect(vis.legacy).toBe('none');
    expect(parseFloat(vis.contentPadTop)).toBe(0);
  } finally { await stopServer(server); }
});

test('QR: closed sheet is visibility-hidden (no invisible tab stops); open sheet is visible', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#sidebar')).toBeHidden();
    await page.locator('#reader-pill [data-pill="files"]').click();
    await expect(page.locator('#sidebar')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#sidebar')).toBeHidden();
  } finally { await stopServer(server); }
});

test('QR: mobile sheet settings hide the desktop Layout group', async ({ page }) => {
  const port = nextPort();
  await page.setViewportSize({ width: 390, height: 844 });
  const { server } = await boot(page, port);
  try {
    // The hamburger is retired (redesign 03) — the Aa toolbar slot is the
    // mobile path to the settings panel.
    await page.locator('#mobile-toolbar [data-mt="aa"]').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await expect(page.locator('#settings-group-layout')).toBeHidden();
    // A visible sibling group proves the panel itself rendered.
    await expect(page.locator('input[name="theme"][value="light"]')).toBeVisible();
  } finally { await stopServer(server); }
});

// ── Review w9d47hl9a #4: #sidebar-tabs WAI-ARIA roving tabindex + arrow nav ────
// The left sidebar's Files/Outline/Highlights tablist gets the same roving
// tabindex + arrow-key keyboard model as #rp-segs: exactly one tab in the Tab
// order (the selected one, tabindex=0), the rest tabindex=-1; Arrow keys (and
// Home/End) move selection + focus + activate, with wrap-around. Clicks unchanged.

test('T2: #sidebar-tabs is a roving tablist — Arrow keys move selection + focus + activate', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);   // reader default
  try {
    // Open the drawer so the sidebar tabs are visible/focusable.
    await page.keyboard.press('Control+b');
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);

    const roving = async () => await page.evaluate(() =>
      Array.from(document.querySelectorAll('#sidebar-tabs .sidebar-tab')).map((b) => b.tabIndex));
    // Files is the default-active tab → it alone is in the Tab order.
    expect(await roving()).toEqual([0, -1, -1]);
    await expect(page.locator('.sidebar-tab[data-tab="files"]')).toHaveAttribute('aria-selected', 'true');

    // ArrowRight: files → outline (selection + focus + activation).
    await page.locator('.sidebar-tab[data-tab="files"]').focus();
    await page.keyboard.press('ArrowRight');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('outline');
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveAttribute('aria-selected', 'true');
    expect(await roving()).toEqual([-1, 0, -1]);

    // ArrowRight → highlights; ArrowRight again wraps to files.
    await page.keyboard.press('ArrowRight');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('highlights');
    await page.keyboard.press('ArrowRight');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('files');   // wrap

    // ArrowLeft wraps the other way, Home/End jump to the ends.
    await page.keyboard.press('ArrowLeft');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('highlights');
    await page.keyboard.press('Home');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('files');
    await page.keyboard.press('End');
    expect(await page.evaluate(() => document.activeElement?.dataset?.tab)).toBe('highlights');

    // Click still switches and re-rovs the tabindex.
    await page.locator('.sidebar-tab[data-tab="files"]').click();
    expect(await roving()).toEqual([0, -1, -1]);
  } finally { await stopServer(server); }
});
