// @ts-check
// Settings sheet isolation: settings is its own top-level modal (#settings-sheet),
// a sibling of #cmd-palette / #peek-popover — fully decoupled from the #sidebar
// tab container. All four entries (docked gear, #rt-aa, mobile 'aa' slot, palette
// '>settings') open the SAME sheet; the sheet inerts the background and owns the
// keyboard (Esc / outside-tap / close-button dismiss). See
// docs/superpowers/specs/2026-06-13-settings-sheet-isolation-design.md.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 7200;   // base distinct from every other spec (see grep in plan)
function nextPort() { return portCounter++; }

const FIXTURE = {
  'order.json': JSON.stringify(['index.md', 'chap-a.md']),
  'index.md':  '# Index\n\n## S One\n\nBody one.\n\n## S Two\n\nBody two.',
  'chap-a.md': '# Chapter A\n\n## A.1 First\n\nBody A.',
};

// ── Classic (docked gear is the entry) ───────────────────────────────────────
test('classic: the docked gear opens #settings-sheet; Esc / outside / close-button dismiss', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  await pinClassicLayout(page);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    const sheet = page.locator('#settings-sheet');
    await expect(sheet).toBeHidden();

    // Gear opens the sheet (a real top-level surface, not an in-sidebar panel).
    await page.locator('#settings-btn').click();
    await expect(sheet).toBeVisible();
    await expect(page.locator('#settings-btn')).toHaveAttribute('aria-expanded', 'true');
    // Background is inert while the modal is open.
    await expect(page.locator('#content')).toHaveAttribute('inert', '');

    // Esc dismisses.
    await page.keyboard.press('Escape');
    await expect(sheet).toBeHidden();
    await expect(page.locator('#settings-btn')).toHaveAttribute('aria-expanded', 'false');
    await expect(page.locator('#content')).not.toHaveAttribute('inert', /.*/);

    // Re-open, dismiss by clicking the dim backdrop (outside the box).
    await page.locator('#settings-btn').click();
    await expect(sheet).toBeVisible();
    await page.mouse.click(5, 5);                        // top-left corner = dim area
    await expect(sheet).toBeHidden();

    // Re-open, dismiss via the close button.
    await page.locator('#settings-btn').click();
    await expect(sheet).toBeVisible();
    await page.locator('#settings-close').click();
    await expect(sheet).toBeHidden();
  } finally { stopServer(server, dir); }
});

// ── Settings ⟂ tabs (the decoupling pin) ─────────────────────────────────────
test('classic: opening/closing settings never touches the content-tab state', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  await pinClassicLayout(page);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    // Make outline the active tab.
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);

    // Open settings — tabs must be untouched (no co-display, no stale overlay).
    await page.locator('#settings-btn').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);

    // Close settings — still on outline.
    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-sheet')).toBeHidden();
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toHaveClass(/active/);
    await expect(page.locator('#file-list')).toHaveClass(/tab-hidden/);
  } finally { stopServer(server, dir); }
});

// ── Reader (Aa top-bar button is the entry) ──────────────────────────────────
test('reader: #rt-aa opens #settings-sheet WITHOUT opening the drawer; aria toggles', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader is the desktop default
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'reader');

    await page.locator('#rt-aa').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);  // settings ≠ the sidebar drawer
    await expect(page.locator('#rt-aa')).toHaveAttribute('aria-expanded', 'true');
    await expect(page.locator('#rt-aa')).toHaveAttribute('aria-haspopup', 'dialog');

    // A control inside the sheet still live-applies (theme).
    await page.locator('input[name="theme"][value="dark"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-sheet')).toBeHidden();
    await expect(page.locator('#rt-aa')).toHaveAttribute('aria-expanded', 'false');
  } finally { stopServer(server, dir); }
});

// ── Mobile (the 'aa' toolbar slot is the entry) ──────────────────────────────
test('mobile: the aa slot opens the sheet, lights its pill, and hides the desktop Layout group', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  await page.setViewportSize({ width: 390, height: 844 });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    await page.locator('#mobile-toolbar [data-mt="aa"]').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await expect(page.locator('#settings-group-layout')).toBeHidden();   // desktop-only
    await expect(page.locator('input[name="theme"][value="light"]')).toBeVisible();
    // The background (the toolbar the modal covers) is inert while open.
    await expect(page.locator('#mobile-toolbar')).toHaveAttribute('inert', '');
    // The aa slot's pill tracks the settings sheet (not a content tab).
    await expect(page.locator('#mobile-toolbar [data-mt="aa"]')).toHaveClass(/mt-active/);
    await expect(page.locator('#mobile-toolbar [data-mt="aa"]')).toHaveAttribute('aria-current', 'true');

    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-sheet')).toBeHidden();
    await expect(page.locator('#mobile-toolbar')).not.toHaveAttribute('inert', /.*/);   // inert cleared
    await expect(page.locator('#mobile-toolbar [data-mt="aa"]')).not.toHaveClass(/mt-active/);
  } finally { stopServer(server, dir); }
});

// ── Palette command opens the same surface ───────────────────────────────────
test('palette: ">settings" opens #settings-sheet', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader desktop
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>settings');
    await page.keyboard.press('Enter');
    await expect(page.locator('#cmd-palette')).toBeHidden();
    await expect(page.locator('#settings-sheet')).toBeVisible();
  } finally { stopServer(server, dir); }
});

// ── Review hardening (adversarial review wf_5640db88) ────────────────────────

test('focus returns to the docked gear on dismiss (classic)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  await pinClassicLayout(page);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.locator('#settings-btn').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-btn')).toBeFocused();
  } finally { stopServer(server, dir); }
});

test('focus returns to the Aa button on dismiss (reader)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader desktop
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.locator('#rt-aa').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#rt-aa')).toBeFocused();
  } finally { stopServer(server, dir); }
});

// The opener can be hidden by an in-sheet layout switch: reader→classic hides
// #reader-topbar (and #rt-aa). closeSettings() must not focus() the now-hidden
// opener (a silent no-op that strands focus on <body>) — it falls back to a
// still-visible settings entry (the docked gear).
test('reader→classic from inside the sheet: close refocuses a visible control, not <body>', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader desktop
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.locator('#rt-aa').click();                // opener is #rt-aa
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await page.locator('input[name="chrome-mode"][value="docs"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('#rt-aa')).toBeHidden();   // the saved opener is now display:none
    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-sheet')).toBeHidden();
    const activeId = await page.evaluate(() => document.activeElement && document.activeElement.id);
    expect(activeId).toBe('settings-btn');               // fell back to the docked gear, not <body>
  } finally { stopServer(server, dir); }
});

test('an open settings sheet owns the keyboard: Ctrl+B and Ctrl+K do not act behind it', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader desktop
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.locator('#rt-aa').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await page.keyboard.press('Control+b');              // would toggle the drawer
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await page.keyboard.press('Control+k');              // would open the palette
    await expect(page.locator('#cmd-palette')).toBeHidden();
    await expect(page.locator('#settings-sheet')).toBeVisible();   // sheet unaffected
  } finally { stopServer(server, dir); }
});

test('reader: background is inert while the sheet is open and cleared on close', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);                 // reader desktop
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.locator('#rt-aa').click();
    await expect(page.locator('#content')).toHaveAttribute('inert', '');
    await expect(page.locator('#reader-pill')).toHaveAttribute('inert', '');
    await page.keyboard.press('Escape');
    await expect(page.locator('#content')).not.toHaveAttribute('inert', /.*/);
    await expect(page.locator('#reader-pill')).not.toHaveAttribute('inert', /.*/);
  } finally { stopServer(server, dir); }
});

test('mobile sheet has no slide-up animation under prefers-reduced-motion', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir(FIXTURE);
  await page.setViewportSize({ width: 390, height: 844 });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await page.emulateMedia({ reducedMotion: 'reduce' });   // re-evaluates media queries live
    const reduced = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
    expect(reduced).toBe(true);                          // sanity: the emulation is active
    await page.locator('#mobile-toolbar [data-mt="aa"]').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    const anim = await page.locator('#settings-sheet-box').evaluate((el) => getComputedStyle(el).animationName);
    expect(anim).toBe('none');
  } finally { stopServer(server, dir); }
});
