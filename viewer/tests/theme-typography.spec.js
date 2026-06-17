// @ts-check
// Redesign 01: themes + typography on the current layout (spec sections 3/7).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 5800;
function nextPort() { return portCounter++; }

// Theme/typography controls reached via the docked-sidebar gear — pin
// classic layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

// Minimal valid 1×1 PNG (same constant used in publish-smoke.spec.js)
const TINY_PNG_B64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADklEQVQI12P4z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg==';

const DOC = `# Theme Doc

Body text with inline $x^2$ math.

$$
y = \\sum_{k=0}^{N} x_k \\tag{1}
$$

\`\`\`mermaid
graph TD; A-->B;
\`\`\`

![fig](fig.png)
`;

function makeFixture() {
  return createFixtureDir({
    'doc.md': DOC,
    'fig.png': Buffer.from(TINY_PNG_B64, 'base64'),
  });
}

async function openSettings(page) {
  await page.locator('#settings-btn').click();        // classic-pinned suite: docked gear
  await expect(page.locator('#settings-sheet')).toBeVisible();
}

test('theme switch applies, persists across reload, and updates meta theme-color', async ({ page }) => {
  const port = nextPort();
  const dir = makeFixture();
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Theme Doc');
    await openSettings(page);
    await page.locator('input[name="theme"][value="dark"]').check();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    const metaColor = await page.getAttribute('meta[name="theme-color"]', 'content');
    expect(metaColor).toBe('#1a1d23');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  } finally {
    stopServer(server, dir);
  }
});

test('dark theme: KaTeX inherits text color and images are dimmed', async ({ page }) => {
  const port = nextPort();
  const dir = makeFixture();
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await page.waitForFunction(() => document.querySelectorAll('#content .katex').length > 0);
    await openSettings(page);
    await page.locator('input[name="theme"][value="dark"]').check();
    const { katexColor, bodyColor, imgFilter } = await page.evaluate(() => ({
      katexColor: getComputedStyle(document.querySelector('#content .katex')).color,
      bodyColor: getComputedStyle(document.querySelector('#content')).color,
      imgFilter: getComputedStyle(document.querySelector('#content img')).filter,
    }));
    expect(katexColor).toBe(bodyColor);
    expect(imgFilter).toContain('brightness');
  } finally {
    stopServer(server, dir);
  }
});

test('theme switch re-renders mermaid with the matching theme', async ({ page }) => {
  const port = nextPort();
  const dir = makeFixture();
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await page.waitForSelector('#content div.mermaid[data-processed="true"] svg');

    // Extract the default-theme fill colour on the first SVG node rect so we
    // can verify the re-render actually applied the dark mermaid palette (not
    // just changed unique IDs). Mermaid embeds theme-specific CSS inside
    // <defs><style> in the SVG; the default theme gives nodes a light fill
    // (e.g. #ffffde / #f4f4f4 family), while the dark theme uses a dark
    // background fill (e.g. #1f2020 / #333 family) via its own class rules.
    const beforeFill = await page.evaluate(() => {
      const rect = document.querySelector('#content div.mermaid svg .node rect, #content div.mermaid svg rect');
      return rect ? getComputedStyle(rect).fill : '';
    });

    await openSettings(page);
    await page.locator('input[name="theme"][value="dark"]').check();
    // Wait for the re-render cycle to complete (rethemeMermaid removes
    // data-processed then re-runs renderMermaidDiagrams which re-adds it).
    await page.waitForSelector('#content div.mermaid[data-processed="true"] svg');

    // Assert the node fill changed: a regression in mermaidInitOptions()'s
    // `theme === 'dark' ? 'dark' : 'default'` mapping (the config-revert hazard
    // documented in that function's comment) would leave the fill unchanged.
    const afterFill = await page.evaluate(() => {
      const rect = document.querySelector('#content div.mermaid svg .node rect, #content div.mermaid svg rect');
      return rect ? getComputedStyle(rect).fill : '';
    });
    expect(afterFill).not.toBe('');      // sanity: a node rect was found
    expect(afterFill).not.toBe(beforeFill); // dark palette differs from default
  } finally {
    stopServer(server, dir);
  }
});

test('typography sliders change content metrics and persist; defaults match today', async ({ page }) => {
  const port = nextPort();
  const dir = makeFixture();
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    const defaults = await page.evaluate(() => {
      const cs = getComputedStyle(document.getElementById('content'));
      return { fs: cs.fontSize, lh: cs.lineHeight };
    });
    expect(defaults.fs).toBe('16px');
    expect(parseFloat(defaults.lh)).toBeCloseTo(16 * 1.7, 0);

    await openSettings(page);
    await page.locator('#setting-font-scale').fill('1.2');
    // Dispatch input event so the store listener fires
    await page.locator('#setting-font-scale').dispatchEvent('input');
    const fs = await page.evaluate(() => getComputedStyle(document.getElementById('content')).fontSize);
    expect(parseFloat(fs)).toBeCloseTo(19.2, 1);
    await page.reload();
    // Gate on content render before reading computed style: applyTypography runs
    // inside loadSettings() which is called after await fetchFileList() in init().
    // Without this gate, page.evaluate races against the async /api/files round-trip
    // and may read the var(--font-scale, 1) fallback (16px) instead of the
    // persisted 1.2× value.  Same pattern used in settings-groups.spec.js G6.
    await expect(page.locator('#content h1')).toHaveText('Theme Doc');
    const fs2 = await page.evaluate(() => getComputedStyle(document.getElementById('content')).fontSize);
    expect(parseFloat(fs2)).toBeCloseTo(19.2, 1);
  } finally {
    stopServer(server, dir);
  }
});
