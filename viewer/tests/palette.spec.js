// @ts-check
// Redesign 05: command palette (Cmd/Ctrl+K). A top-level modal (#cmd-palette,
// z 1200) independent of the sidebar drawer. Modes by input prefix: default =
// files (+ trailing full-text runner), '#' = headings, '>' = commands.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// Port base 6300 — clear of every existing spec. NB 6000 is Chromium
// ERR_UNSAFE_PORT (X11 reserved); 6100 is reader-shell-mobile.spec.js.
let portCounter = 6300;
function nextPort() { return portCounter++; }

const DOC_A = `# Doc A

## Alpha Section

The alpha section mentions quasar physics at length.
${'Lorem ipsum dolor sit amet consectetur adipiscing elit.\n\n'.repeat(20)}
## Beta Section

The beta section also discusses the quasar jet.
${'Tempor incididunt ut labore et dolore magna aliqua.\n\n'.repeat(20)}
`;
const DOC_B = `# Doc B

Doc B is about a distant quasar and its redshift.
`;
const DOC_C = `# Doc C

Doc C has unrelated content.
`;

const FILES = { 'doc-a.md': DOC_A, 'doc-b.md': DOC_B, 'doc-c.md': DOC_C };

async function boot(page, port, opts = {}) {
  const dir = createFixtureDir(FILES);
  const server = await startServer(dir, port);
  if (opts.layout) {
    await page.addInitScript((layout) => {
      localStorage.setItem('viewer.settings.v1', JSON.stringify({ layout }));
    }, opts.layout);
  }
  await page.goto(`http://localhost:${port}?file=doc-a.md`);
  await expect(page.locator('#content h1')).toHaveText('Doc A');
  return { dir, server };
}

// ── Task 2: shell — open/close, Ctrl+K rebind, opener button ────────────────

test('Ctrl+K opens the palette and focuses its input; Esc closes', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#cmd-palette')).toBeHidden();
    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#cmd-input')).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(page.locator('#cmd-palette')).toBeHidden();
  } finally { await stopServer(server); }
});

test('Ctrl+K no longer just focuses the sidebar search box', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-input')).toBeFocused();
    await expect(page.locator('#search-input')).not.toBeFocused();
  } finally { await stopServer(server); }
});

test('the top-bar opener button opens the palette (reader)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#rt-palette').click();
    await expect(page.locator('#cmd-palette')).toBeVisible();
  } finally { await stopServer(server); }
});

test('clicking the dim backdrop (not the box) closes the palette', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await page.locator('#cmd-palette').click({ position: { x: 5, y: 5 } }); // dim margin
    await expect(page.locator('#cmd-palette')).toBeHidden();
  } finally { await stopServer(server); }
});

// ── Task 3: file quick-open (default mode) ──────────────────────────────────

test('default mode fuzzy-opens a file; Enter loads it and closes the palette', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                  // boots doc-a.md
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('docb');             // fuzzy → doc-b.md
    const first = page.locator('#cmd-results .pal-item').first();
    await expect(first).toContainText('doc-b.md');
    await page.keyboard.press('Enter');
    await expect(page.locator('#cmd-palette')).toBeHidden();
    await expect(page.locator('#content h1')).toContainText('Doc B'); // doc-b loaded
  } finally { await stopServer(server); }
});

test('default mode arrow-navigates results', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');                    // empty query → all files
    await expect(page.locator('#cmd-results .pal-item').first()).toHaveClass(/sel/);
    await page.keyboard.press('ArrowDown');
    await expect(page.locator('#cmd-results .pal-item').nth(1)).toHaveClass(/sel/);
  } finally { await stopServer(server); }
});

// ── Task 4: heading jump (# mode) ───────────────────────────────────────────

test('# mode jumps to a heading in the current file', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                  // doc-a.md: Alpha/Beta headings
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('#beta');
    const first = page.locator('#cmd-results .pal-item').first();
    await expect(first).toContainText('Beta');
    await page.keyboard.press('Enter');
    await expect(page.locator('#cmd-palette')).toBeHidden();
    // scrollToAnchor flashes .anchor-highlight on the target heading (persists).
    await expect(page.locator('#content h2:has-text("Beta")')).toHaveClass(/anchor-highlight/);
  } finally { await stopServer(server); }
});

// ── Task 5: command mode (> ) — actions, cloud gating, shortcuts ─────────────

test('> mode toggles theme', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>theme dark');       // → "Theme: Dark"
    await expect(page.locator('#cmd-results .pal-item').first()).toContainText('Dark');
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  } finally { await stopServer(server); }
});

test('> mode toggles immersive (reader → docs) on desktop', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                   // reader default, desktop viewport
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>toggle immersive');
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
  } finally { await stopServer(server); }
});

test('> mode open settings reveals the panel', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>settings');
    await page.keyboard.press('Enter');
    await expect(page.locator('#settings-sheet')).toBeVisible();
  } finally { await stopServer(server); }
});

test('> mode: copy-citation with no selection toasts a hint', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>copy citation');
    await page.keyboard.press('Enter');
    await expect(page.locator('#reload-toast')).toContainText('Select text first');
  } finally { await stopServer(server); }
});

test('> mode: push/pull absent under local backend; shortcuts are listed', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>annotations');
    await expect(page.locator('#cmd-results')).not.toContainText('Push annotations');
    await page.locator('#cmd-input').fill('>shortcut');
    await expect(page.locator('#cmd-results')).toContainText('Ctrl+K');
  } finally { await stopServer(server); }
});

// ── Task 6: full-text search routing (default-mode trailing runner) ─────────

test('default mode routes full-text search into the sidebar index', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                  // doc-a/doc-b both contain "quasar"
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('quasar');
    const runner = page.locator('#cmd-results .pal-search');
    await expect(runner).toContainText('Search');
    await runner.click();
    await expect(page.locator('#cmd-palette')).toBeHidden();
    // doSearch() rendered hits into the (now-open) sidebar results.
    await expect(page.locator('#search-results .search-hit').first()).toBeVisible();
    await expect(page.locator('#search-input')).toHaveValue('quasar');
  } finally { await stopServer(server); }
});

// ── Task 7: review-hardening (adversarial review weqs70hun) ─────────────────

test('an open palette owns the keyboard — Ctrl+B does not toggle the drawer behind it', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                  // reader desktop
  try {
    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await page.keyboard.press('Control+b');                    // would toggle the drawer pre-fix
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#cmd-palette')).toBeVisible();  // palette unaffected
  } finally { await stopServer(server); }
});

test('> mode: toggle-layout is absent on mobile (classic is desktop-only)', async ({ page }) => {
  const port = nextPort();
  await page.setViewportSize({ width: 600, height: 800 });     // forced-mobile-reader
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>toggle layout');
    await expect(page.locator('#cmd-results')).not.toContainText('Toggle layout');
  } finally { await stopServer(server); }
});

// ── Task T6: palette as a cross-reference index ─────────────────────────────
// A doc carrying numbered equations and a reference list so the '#' index can
// surface heading / Eq. (N) / [N] rows for technical-reader jumps.
const XREF_DOC = `# Cross Ref Doc

## Gamma Section

Inline cite to <a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

is referenced as equation [(1)](#eq-1).

${'Body filler line for the gamma section.\n\n'.repeat(15)}

## Delta Section

A second equation <a id="eq-2"></a>

$$
z = a t^2 \\tag{2}
$$

and a citation [[1]](#ref-1).

${'Body filler line for the delta section.\n\n'.repeat(15)}

## References

<a id="ref-1"></a>
[1] Shannon, C. A Mathematical Theory of Communication. 1948.
`;

async function bootXref(page, port) {
  const dir = createFixtureDir({ ...FILES, 'xref.md': XREF_DOC });
  const server = await startServer(dir, port);
  await page.goto(`http://localhost:${port}?file=xref.md`);
  await expect(page.locator('#content h1')).toHaveText('Cross Ref Doc');
  return { dir, server };
}

test('# index lists headings with level hints (H1/H2)', async ({ page }) => {
  const port = nextPort();
  const { server } = await bootXref(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('#section');
    // Heading rows carry an H<level> hint in .pal-hint.
    const gamma = page.locator('#cmd-results .pal-item.pal-heading', { hasText: 'Gamma' });
    await expect(gamma).toHaveCount(1);
    await expect(gamma.locator('.pal-hint')).toHaveText('H2');
  } finally { await stopServer(server); }
});

test('# index lists Eq. (N) rows that navigate to #eq-N when run', async ({ page }) => {
  const port = nextPort();
  const { server } = await bootXref(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('#eq 2');
    const eqRow = page.locator('#cmd-results .pal-item', { hasText: 'Eq. (2)' });
    await expect(eqRow.first()).toBeVisible();
    await eqRow.first().click();
    await expect(page.locator('#cmd-palette')).toBeHidden();
    // scrollToAnchor flashes .anchor-highlight on the eq-2 anchor's parent block.
    await expect(page).toHaveURL(/#eq-2$/);
    const flashed = await page.evaluate(() =>
      !!document.querySelector('#content .anchor-highlight'));
    expect(flashed).toBe(true);
  } finally { await stopServer(server); }
});

test('# index lists reference rows ([N] text) that navigate to #ref-N', async ({ page }) => {
  const port = nextPort();
  const { server } = await bootXref(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('#shannon');
    const refRow = page.locator('#cmd-results .pal-item', { hasText: 'Shannon' });
    await expect(refRow.first()).toBeVisible();
    await expect(refRow.first()).toContainText('[1]');
    await refRow.first().click();
    await expect(page.locator('#cmd-palette')).toBeHidden();
    await expect(page).toHaveURL(/#ref-1$/);
  } finally { await stopServer(server); }
});

test('? / shortcuts command opens a keyboard cheat-sheet', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    // '?' is a dedicated shortcut prefix listing the cheat-sheet.
    await page.locator('#cmd-input').fill('?');
    const sheet = page.locator('#shortcut-cheatsheet');
    // Selecting the shortcuts entry reveals the cheat-sheet overlay.
    const entry = page.locator('#cmd-results .pal-item', { hasText: 'Keyboard shortcuts' });
    await expect(entry.first()).toBeVisible();
    await entry.first().click();
    await expect(sheet).toBeVisible();
    await expect(sheet).toContainText('Ctrl+K');
    await page.keyboard.press('Escape');
    await expect(sheet).toBeHidden();
  } finally { await stopServer(server); }
});

// ── Review w9d47hl9a #2: the aria-modal cheat-sheet inerts the background ─────

test('the keyboard cheat-sheet inerts the background while open, clears on close', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('?');
    await page.locator('#cmd-results .pal-item', { hasText: 'Keyboard shortcuts' }).first().click();
    const sheet = page.locator('#shortcut-cheatsheet');
    await expect(sheet).toBeVisible();

    // Background #app siblings (e.g. #content, #sidebar) are inert; the sheet is
    // NOT — so a Tab cannot escape the aria-modal dialog into the live document.
    const inertState = await page.evaluate(() => {
      const sheetEl = document.getElementById('shortcut-cheatsheet');
      const content = document.getElementById('content');
      return {
        contentInert: content.hasAttribute('inert'),
        sheetInert: sheetEl.hasAttribute('inert'),
      };
    });
    expect(inertState.contentInert).toBe(true);
    expect(inertState.sheetInert).toBe(false);

    // Closing clears the inert state on every sibling.
    await page.locator('#shortcut-cheatsheet .sc-close').click();
    await expect(sheet).toBeHidden();
    expect(await page.evaluate(() => document.getElementById('content').hasAttribute('inert'))).toBe(false);
  } finally { await stopServer(server); }
});

test('immersive focus-mode command shows its keyboard shortcut hint', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                   // desktop reader
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>focus mode');
    // The focus-mode immersive toggle carries its real ⌘⇧F binding in .pal-hint.
    const row = page.locator('#cmd-results .pal-item', { hasText: 'focus mode' });
    await expect(row.first()).toBeVisible();
    await expect(row.first()).toContainText('immersive');
    await expect(row.first().locator('.pal-hint')).toContainText('F');
  } finally { await stopServer(server); }
});

