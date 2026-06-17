// @ts-check
// Redesign 03: Reader shell on mobile (spec section 5). At ≤768px the viewer
// is always reader — a five-slot bottom toolbar plus a drag-handle bottom
// sheet built on the SAME #app.drawer-open machinery as desktop reader mode
// (and the retired Plan-04 drawer). Toolbar/pane wiring basics are pinned in
// pwa-responsive.spec.js; this pack covers sheet geometry, drag, auto-hide,
// and settings reachability.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// Base distinct from reader-shell.spec.js (5900). NOT 6000: Chromium's
// restricted-port list blocks 6000 (X11) with net::ERR_UNSAFE_PORT.
let portCounter = 6100;
function nextPort() { return portCounter++; }

const DOC = `# Mobile Doc

## Section One

${'Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod.\n\n'.repeat(40)}
## Section Two

${'Tempor incididunt ut labore et dolore magna aliqua ut enim ad minim.\n\n'.repeat(40)}
`;

async function boot(page, port, opts = {}) {
  const dir = createFixtureDir(opts.files || { 'doc.md': DOC });
  const server = await startServer(dir, port);
  await page.setViewportSize(opts.viewport || { width: 390, height: 844 });
  await page.goto(`http://localhost:${port}?file=${opts.file || 'doc.md'}`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { dir, server };
}

test('T2: closed sheet is visibility-hidden; open sheet is a bottom sheet covering ~75%', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    // Closed: hidden — this also removes the retired drawer's latent
    // off-canvas tab stops (the desktop QR fix's mobile counterpart).
    await expect(page.locator('#sidebar')).toBeHidden();

    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#sidebar')).toBeVisible();
    await expect(page.locator('#sheet-handle')).toBeVisible();
    // Poll until the slide-in transition settles: top edge near 25% depth.
    await expect.poll(async () => {
      const b = await page.locator('#sidebar').boundingBox();
      return b ? Math.round(b.y) : null;
    }).toBeLessThanOrEqual(Math.round(844 * 0.30));
    const b = await page.locator('#sidebar').boundingBox();
    expect(b.width).toBeGreaterThanOrEqual(389);                 // full width
    expect(b.height).toBeGreaterThanOrEqual(Math.round(844 * 0.70)); // ~75dvh
    expect(Math.round(b.y + b.height)).toBeGreaterThanOrEqual(843);  // bottom-anchored

    // Esc closes; the sheet leaves the accessibility tree again.
    await page.keyboard.press('Escape');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#sidebar')).toBeHidden();
  } finally { stopServer(server, dir); }
});

test('T2: search slot opens the command palette (mobile-bar: search = command entry)', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    // The mobile search slot now opens the command palette (a top-level modal),
    // not the off-canvas sidebar search box (mobile Adaptive Reader Bar T2).
    await page.locator('#mobile-toolbar [data-mt="search"]').click();
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#cmd-input')).toBeFocused();
  } finally { stopServer(server, dir); }
});

test('T2: tapping a noted footnote ref opens the sheet on the note entry (mobile)', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port, {
    files: {
      'ref-click.md': '# Test fixture\n\nLead ==yellow:noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
    },
    file: 'ref-click.md',
  });
  try {
    await page.waitForLoadState('networkidle');
    await page.locator('sup.footnote-ref a').first().click();
    // Pre-fix: the highlights tab activated invisibly inside the closed
    // sheet and the tap read as a no-op (decision 2026-06-12-03 item 3
    // scoped the fix to desktop; Plan 03 owns this width).
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('.highlights-entry.hl-note-expanded')).toBeVisible();
  } finally { stopServer(server, dir); }
});

// Drag the handle vertically with the mouse (Playwright mouse events emit
// pointer events with pointerType "mouse"; the controller is pointer-typed
// so touch and mouse share the same path). The sheet's slide/detent
// transitions run 0.2–0.25s and toBeVisible passes at transition START
// (the visibility flip is synchronous by design), so first poll until the
// handle's position settles on-screen — otherwise the pointerdown lands
// where the handle WAS mid-slide and the drag is a silent no-op.
async function dragHandle(page, dy) {
  const handle = page.locator('#sheet-handle');
  let prev = -1;
  await expect.poll(async () => {
    const b = await handle.boundingBox();
    const cur = b ? Math.round(b.y) : -1;
    const settled = cur >= 0 && cur < 844 && cur === prev;
    prev = cur;
    return settled;
  }).toBe(true);
  const hb = await handle.boundingBox();
  const x = hb.x + hb.width / 2;
  const y = hb.y + hb.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x, y + dy, { steps: 8 });
  await page.mouse.up();
}

test('T3: dragging the handle down dismisses the sheet', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#sidebar')).toBeVisible();
    await dragHandle(page, 250);
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
    await expect(page.locator('#sidebar')).toBeHidden();
    // The drag's inline transform must not leak into the next open.
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect.poll(async () => {
      const b = await page.locator('#sidebar').boundingBox();
      return b ? Math.round(b.y) : null;
    }).toBeLessThanOrEqual(Math.round(844 * 0.30));
  } finally { stopServer(server, dir); }
});

test('T3: drag up expands to the full detent; drag down from full returns to 75%; small drags snap back', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#sidebar')).toBeVisible();

    // Expand: drag up past the threshold.
    await dragHandle(page, -120);
    await expect(page.locator('#sidebar')).toHaveClass(/sheet-full/);
    await expect.poll(async () => {
      const b = await page.locator('#sidebar').boundingBox();
      return b ? Math.round(b.height) : null;
    }).toBeGreaterThanOrEqual(780);

    // Collapse: a big downward drag from full returns to the resting detent
    // (it does NOT dismiss — detents step one at a time).
    await dragHandle(page, 150);
    await expect(page.locator('#sidebar')).not.toHaveClass(/sheet-full/);
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect.poll(async () => {
      const b = await page.locator('#sidebar').boundingBox();
      return b ? Math.round(b.height) : null;
    }).toBeLessThanOrEqual(660);

    // Sub-threshold drag snaps back without changing anything.
    await dragHandle(page, 40);
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('#sidebar')).not.toHaveClass(/sheet-full/);
  } finally { stopServer(server, dir); }
});

test('T4: toolbar auto-hides on scroll-down, returns on scroll-up', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForFunction(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    // The toolbar is actually off-screen, not merely class-flagged.
    await expect.poll(async () => {
      const b = await page.locator('#mobile-toolbar').boundingBox();
      return b ? Math.round(b.y) : null;
    }).toBeGreaterThanOrEqual(844);
    await page.evaluate(() => window.scrollTo({ top: 700, behavior: 'instant' }));
    await page.waitForFunction(() => !document.documentElement.classList.contains('reader-chrome-hidden'));
  } finally { stopServer(server, dir); }
});

test('T4: tap at the bottom edge reveals the hidden toolbar', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForFunction(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    await page.mouse.click(195, 838); // inside the 48px bottom band
    await page.waitForFunction(() => !document.documentElement.classList.contains('reader-chrome-hidden'));
  } finally { stopServer(server, dir); }
});

test('T4: short documents never hide the toolbar', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port, {
    files: { 'short.md': '# Short\n\nOne paragraph only.' },
    file: 'short.md',
  });
  try {
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    expect(has).toBe(false);
  } finally { stopServer(server, dir); }
});

test('T4: chrome state is frozen while the sheet is open', async ({ page }) => {
  const port = nextPort();
  const { dir, server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#sidebar')).toBeVisible();
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'instant' }));
    await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'instant' }));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => document.documentElement.classList.contains('reader-chrome-hidden'));
    expect(has).toBe(false);
  } finally { stopServer(server, dir); }
});

test('T5: settings panel scrolls inside the sheet on a short landscape viewport', async ({ page }) => {
  const port = nextPort();
  // 740×360 landscape phone — todos/2026-06-12-settings-panel-scroll-mobile.md acceptance.
  const { dir, server } = await boot(page, port, { viewport: { width: 740, height: 360 } });
  try {
    await page.locator('#mobile-toolbar [data-mt="aa"]').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    // Pre-fix the Typography radios sit below the sheet's clipped bottom
    // with no scrollable ancestor — check() cannot reach them.
    const serif = page.locator('input[name="content-font"][value="serif"]');
    await serif.check();
    await expect(serif).toBeChecked();
  } finally { stopServer(server, dir); }
});
