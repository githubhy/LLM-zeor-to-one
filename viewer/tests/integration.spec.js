// @ts-check
// Redesign 07 (integration pass): the per-feature specs pin CLASSIC layout, so
// this exercises highlights/notes/citation in READER mode (spec section 10
// "both modes") plus the cross-feature interactions the per-plan gates never
// covered together (peek×palette, peek×theme, layout-switch×highlights).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// Port base 6700 — clear of every spec (6000 X11; 6300 palette; 6500 peeks).
let portCounter = 6700;
function nextPort() { return portCounter++; }

async function boot(page, port, files, settings) {
  const dir = createFixtureDir(files);
  const server = await startServer(dir, port);
  await page.addInitScript((s) => {
    localStorage.setItem('viewer.settings.v1', JSON.stringify(s));
  }, Object.assign({ layout: 'reader' }, settings || {}));
  const first = Object.keys(files)[0];
  await page.goto(`http://localhost:${port}?file=${first}`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { dir, server };
}

const EQ_DOC = `# Peek Integration

The line <a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

is referenced: see [(1)](#eq-1) above.
${'Filler line to allow scrolling.\n\n'.repeat(30)}
`;

test('reader mode: add a note to a highlight (flow works in both modes)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': '# Reader\n\nLead ==yellow:test== tail.\n' });
  try {
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'reader');
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    // Collapsed-selection-in-mark + mouseup → recolor toolbar (notes.spec.js recipe).
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-yellow');
      const tn = mk.firstChild;
      const sel = window.getSelection(); sel.removeAllRanges();
      const r = document.createRange(); r.setStart(tn, 2); r.setEnd(tn, 2); sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true }));
    });
    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    await page.locator('.hl-note-btn').click();
    await page.locator('#note-popover textarea.np-body').fill('reader mode note body');
    await page.locator('#note-popover .np-save').click();
    await expect(page.locator('sup.footnote-ref')).toBeVisible();
  } finally { await stopServer(server); }
});

test('reader mode: copy citation from a selection', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port,
    { 'doc.md': '# Cite\n\nThe quick brown fox jumps over the lazy dog.\n' },
    { citationMode: 'local' });
  try {
    await page.evaluate(() => {
      const p = document.querySelector('#content p'); const tn = p.firstChild;
      const sel = window.getSelection(); sel.removeAllRanges();
      const r = document.createRange(); r.setStart(tn, 4); r.setEnd(tn, 20); sel.addRange(r);
      const rect = p.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: rect.left + 20, clientY: rect.bottom + 2, bubbles: true }));
    });
    await page.evaluate(() => { window.__clip = null; navigator.clipboard.writeText = async (t) => { window.__clip = t; }; navigator.clipboard.write = null; });
    await expect(page.locator('#hl-toolbar')).toBeVisible();
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });
    const clip = await page.evaluate(() => window.__clip);
    expect(clip).toMatch(/^>/);                // markdown blockquote citation
  } finally { await stopServer(server); }
});

test('switching layout reader→classic preserves the highlight + content', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': '# Keep\n\nLead ==yellow:keepme== tail.\n' });
  try {
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    // Switch layout via the settings radio (the path a user takes): in reader
    // mode the Aa top-bar button opens the dedicated #settings-sheet.
    await page.locator('#rt-aa').click();
    await page.locator('input[name="chrome-mode"][value="docs"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('mark.hl-yellow')).toBeVisible();              // highlight survived
    await expect(page.locator('#content h1')).toHaveText('Keep');
  } finally { await stopServer(server); }
});

test('opening the command palette dismisses an open peek', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': EQ_DOC });
  try {
    await page.locator('#content a[href="#eq-1"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-palette')).toBeVisible();
    await expect(page.locator('#peek-popover')).toBeHidden();                // peek superseded
  } finally { await stopServer(server); }
});

test('a peek renders legibly in dark theme', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': EQ_DOC }, { theme: 'dark' });
  try {
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await page.locator('#content a[href="#eq-1"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await expect(page.locator('#peek-popover .katex')).toBeVisible();        // equation rendered in dark
  } finally { await stopServer(server); }
});
