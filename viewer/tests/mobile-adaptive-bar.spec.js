// @ts-check
// Mobile Adaptive Reader Bar (≤768px): position rail (summon + label cycle),
// search→command-palette, selection-morph (docked annotation bar), sheet motion.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// 7100 base — NOT 7000 (macOS AirPlay Receiver / Control Center binds :7000),
// same class of hazard as the 6000 X11 reserved port.
let portCounter = 7100;
function nextPort() { return portCounter++; }

const DOC = `# Mobile Bar

## Alpha

${'Body line of the alpha section.\n\n'.repeat(40)}## Beta

${'More body in the beta section.\n\n'.repeat(40)}`;

async function boot(page, port, files = { 'doc.md': DOC }) {
  const dir = createFixtureDir(files);
  const server = await startServer(dir, port);
  await page.setViewportSize({ width: 390, height: 740 });   // mobile portrait
  await page.goto(`http://localhost:${port}?file=doc.md`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { dir, server };
}

// ── Task 1: position rail ───────────────────────────────────────────────────

test('rail is visible and tapping it summons the bar + shows a label', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#mobile-rail')).toBeHidden();     // hidden while the bar is shown
    await page.mouse.wheel(0, 700);                             // scroll down → chrome hides
    await expect(page.locator('html')).toHaveClass(/reader-chrome-hidden/);
    await expect(page.locator('#mobile-rail')).toBeVisible();    // immersive → the rail appears
    await page.locator('#mobile-rail').click();
    await expect(page.locator('html')).not.toHaveClass(/reader-chrome-hidden/);   // summoned
    await expect(page.locator('#mobile-rail-label')).toHaveClass(/show/);          // position label shown
    await expect(page.locator('#mobile-rail-label')).not.toBeEmpty();
  } finally { await stopServer(server); }
});

// ── Task 2: search slot → command palette ───────────────────────────────────

test('mobile search slot opens the command palette', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="search"]').click();
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#cmd-input')).toBeFocused();
  } finally { await stopServer(server); }
});

// ── Task 3: selection morph (docked annotation bar) ─────────────────────────

test('selecting text morphs the bar into a docked annotation toolbar', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': '# Sel\n\nThe quick brown fox jumps over the lazy dog.\n' });
  try {
    await page.evaluate(() => {
      const p = document.querySelector('#content p'); const tn = p.firstChild;
      const sel = window.getSelection(); sel.removeAllRanges();
      const r = document.createRange(); r.setStart(tn, 4); r.setEnd(tn, 20); sel.addRange(r);
      const rect = p.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: rect.left + 20, clientY: rect.bottom + 2, bubbles: true }));
    });
    const tb = page.locator('#hl-toolbar');
    await expect(tb).toBeVisible();
    await expect(tb).toHaveClass(/docked/);                        // docked, not floating
    const box = await tb.boundingBox();
    expect(box.x).toBeLessThanOrEqual(1);                          // full-width, left edge
    await page.locator('#hl-toolbar .hl-swatch').first().click();  // write a highlight
    await expect(page.locator('#content mark')).toBeVisible();
    // Applying morphs the bar back to navigation (hideToolbar clears the state).
    await expect(tb).not.toHaveClass(/docked/);
    await expect(page.locator('body')).not.toHaveClass(/annotating/);
  } finally { await stopServer(server); }
});

// ── Task 4: sheet detents + emerge-from-origin motion ───────────────────────

test('a sheet opens from a slot and closes (motion does not break open/close)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('#sidebar')).toBeVisible();
    // Dismiss via Esc (the backdrop's centre is covered by the 75dvh sheet, so a
    // default backdrop click is intercepted — Esc is the established dismiss).
    await page.keyboard.press('Escape');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
  } finally { await stopServer(server); }
});

test('reduced-motion: a sheet still opens and closes (emerge falls back to slide)', async ({ page }) => {
  const port = nextPort();
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const { server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#app')).toHaveClass(/drawer-open/);
    await expect(page.locator('#sidebar')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#app')).not.toHaveClass(/drawer-open/);
  } finally { await stopServer(server); }
});

// ── Task 5: active-state pill ───────────────────────────────────────────────

test('the open slot shows an active-state pill; closing clears it', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#mobile-toolbar [data-mt="files"]').click();
    await expect(page.locator('#mobile-toolbar [data-mt="files"]')).toHaveClass(/mt-active/);
    await page.keyboard.press('Escape');
    await expect(page.locator('#mobile-toolbar [data-mt="files"]')).not.toHaveClass(/mt-active/);
  } finally { await stopServer(server); }
});
