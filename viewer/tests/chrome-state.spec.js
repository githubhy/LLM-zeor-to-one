// @ts-check
// Adaptive Reading Shell (2026-06-14) — the immersive<->non-immersive toggle
// and the Focus state. Port base 7310.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let port = 7310;
const nextPort = () => port++;

const DOC = `# Doc One

A body paragraph with some content to scroll.

## Section Two

More body text.
`;
function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

async function boot(page, p) {
  const dir = fixture();
  const server = await startServer(dir, p);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`http://localhost:${p}/?file=doc.md`);
  await expect(page.locator('#content h1')).toHaveText('Doc One');
  return { server, dir };
}

test('#rt-mode exits immersive (reader -> docs): docked sidebar, no topbar', async ({ page }) => {
  const p = nextPort();
  const { server, dir } = await boot(page, p);             // reader default
  try {
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'reader');
    await expect(page.locator('#reader-topbar')).toBeVisible();
    await page.locator('#rt-mode').click();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('html')).not.toHaveClass(/immersive/);
    await expect(page.locator('#sidebar')).toBeVisible();   // docked
    await expect(page.locator('#reader-topbar')).toBeHidden();
  } finally { stopServer(server, dir); }
});

test('Ctrl+Shift+F enters Focus (topbar + pill hidden, rail visible) and toggles back', async ({ page }) => {
  const p = nextPort();
  const { server, dir } = await boot(page, p);
  try {
    await page.keyboard.press('Control+Shift+KeyF');
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'focus');
    await expect(page.locator('html')).toHaveClass(/immersive/);
    await expect(page.locator('#reader-topbar')).toBeHidden();
    await expect(page.locator('#reader-pill')).toBeHidden();
    await expect(page.locator('#reader-rail')).toBeVisible();
    await page.keyboard.press('Control+Shift+KeyF');
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'reader');
    await expect(page.locator('#reader-topbar')).toBeVisible();
  } finally { stopServer(server, dir); }
});

test('palette "Toggle immersive" flips reader -> docs', async ({ page }) => {
  const p = nextPort();
  const { server, dir } = await boot(page, p);
  try {
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>toggle immersive');
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
  } finally { stopServer(server, dir); }
});

test('R7: switching chrome from the settings sheet closes the sheet', async ({ page }) => {
  const p = nextPort();
  const { server, dir } = await boot(page, p);
  try {
    await page.locator('#rt-aa').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();
    await page.locator('input[name="chrome-mode"][value="docs"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('#settings-sheet')).toBeHidden();   // R7
  } finally { stopServer(server, dir); }
});

test('#rt-mode is a one-way command button (no aria-pressed) that switches to docs', async ({ page }) => {
  // Review w9d47hl9a #5: #rt-mode is NOT a toggle — it is only visible in
  // reader/focus chrome and always sends chrome→docs, so a toggle's aria-pressed
  // would be permanently 'true' and misleading. It carries a command aria-label
  // and no aria-pressed. (Consciously replaces the old aria-pressed-toggle test —
  // we keep the behavioural coverage: clicking it switches to docs.)
  const p = nextPort();
  const { server, dir } = await boot(page, p);
  try {
    const mode = page.locator('#rt-mode');
    await expect(mode).toBeVisible();                                  // reader chrome
    await expect(mode).not.toHaveAttribute('aria-pressed', /.*/);      // no aria-pressed at all
    await expect(mode).toHaveAttribute('aria-label', /Docs/);          // command label, mentions Docs
    await mode.click();                                                // the command: → docs
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
  } finally { stopServer(server, dir); }
});
