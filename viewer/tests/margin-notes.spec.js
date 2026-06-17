// @ts-check
// T7: Tufte margin sidenotes. When `marginNotes` is on AND the chrome is
// immersive (reader/focus) AND the viewport is ≥1400px, in-content references
// (footnote refs, numbered citations → #ref-N, eq/sec cross-refs) render as
// sidenotes in the right whitespace beside the centered prose column, vertically
// aligned to their anchor and de-collided top-to-bottom so KaTeX-tall sidenotes
// never overlap. Below 1400px / in docs / non-immersive the band is absent and
// the floating peek popover remains the resolution path.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// Port base 7330 — clear of in-situ-peeks (6500) and reader-shell (5900).
let portCounter = 7330;
function nextPort() { return portCounter++; }

// Two cross-refs close together near the top (eq-1 then ref-1 in adjacent
// paragraphs) plus a footnote — exercises de-collision (two anchors a few lines
// apart whose sidenotes, once the eq sidenote renders tall KaTeX, would overlap).
const DOC = `# Margin Doc

The slope equation <a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

is referenced here: see equation [(1)](#eq-1) for the slope-intercept form, and
also reference [[1]](#ref-1) which sits just below it[^a].

[^a]: A footnote definition giving extra context for the claim above.

${'Filler paragraph to make the page scrollable and keep the prose tall.\n\n'.repeat(40)}

## References

<a id="ref-1"></a>
[1] Smith, J. Example Paper. Journal of Examples, 2020. [paper](https://example.com/p).
`;

async function boot(page, port, seed, viewport, files = { 'doc.md': DOC }) {
  const dir = createFixtureDir(files);
  const server = await startServer(dir, port);
  if (viewport) await page.setViewportSize(viewport);
  if (seed) {
    await page.addInitScript((s) => {
      localStorage.setItem('viewer.settings.v1', JSON.stringify(s));
    }, seed);
  }
  await page.goto(`http://localhost:${port}?file=doc.md`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { dir, server };
}

test('reader + marginNotes:on at 1440px renders aligned, de-collided sidenotes', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(
    page, port, { chrome: 'reader', marginNotes: true }, { width: 1440, height: 900 });
  try {
    const band = page.locator('#sidenote-band');
    await expect(band).toHaveCount(1);
    const notes = page.locator('.sidenote');
    await expect.poll(async () => await notes.count()).toBeGreaterThan(0);

    // Each sidenote sits to the RIGHT of the content column's right edge.
    const contentRight = (await page.locator('#content').boundingBox()).x
      + (await page.locator('#content').boundingBox()).width;
    const count = await notes.count();
    const boxes = [];
    for (let i = 0; i < count; i++) {
      const b = await notes.nth(i).boundingBox();
      boxes.push(b);
      expect(b.x).toBeGreaterThanOrEqual(contentRight - 2);
    }
    // De-collision: sorted by top, no two adjacent sidenotes overlap vertically.
    boxes.sort((p, q) => p.y - q.y);
    for (let i = 1; i < boxes.length; i++) {
      // b.top >= a.bottom within a small tolerance.
      expect(boxes[i].y).toBeGreaterThanOrEqual(boxes[i - 1].y + boxes[i - 1].height - 2);
    }
  } finally { await stopServer(server); }
});

test('below 1400px (1200px) renders no sidenotes; the cross-ref still peeks', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(
    page, port, { chrome: 'reader', marginNotes: true }, { width: 1200, height: 900 });
  try {
    await expect(page.locator('.sidenote')).toHaveCount(0);
    // Fallback resolution path is unaffected: a cross-ref still opens the peek.
    await page.locator('#content a[href="#eq-1"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
  } finally { await stopServer(server); }
});

test('docs mode at 1440px renders no sidenotes (docs owns the right whitespace)', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(
    page, port, { chrome: 'docs', marginNotes: true }, { width: 1440, height: 900 });
  try {
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('.sidenote')).toHaveCount(0);
  } finally { await stopServer(server); }
});

test('toggling marginNotes off removes the band', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(
    page, port, { chrome: 'reader', marginNotes: true }, { width: 1440, height: 900 });
  try {
    await expect.poll(async () => await page.locator('.sidenote').count()).toBeGreaterThan(0);
    // Toggle the setting off via the settings sheet checkbox.
    await page.locator('#rt-aa').click();
    await page.locator('#setting-margin-notes').uncheck();
    await page.locator('#settings-close').click();
    await expect(page.locator('.sidenote')).toHaveCount(0);
  } finally { await stopServer(server); }
});

// ── Review w9d47hl9a #7/#19: split-view tears down the band; close rebuilds ───

test('opening split with margin-notes on removes the band; closing rebuilds it', async ({ page }) => {
  const port = nextPort();
  // 1500px clears BOTH gates (margin notes ≥1400, split ≥1440).
  const { server } = await boot(
    page, port, { chrome: 'reader', marginNotes: true }, { width: 1500, height: 900 });
  try {
    await expect.poll(async () => await page.locator('.sidenote').count()).toBeGreaterThan(0);
    // Open split via the palette command. The band lives in the right whitespace
    // Pane B now occupies, so it must be torn down (not buried under Pane B).
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();
    await expect(page.locator('#sidenote-band')).toHaveCount(0);

    // Closing split rebuilds the band (the right whitespace is Pane A's again).
    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
    await expect.poll(async () => await page.locator('.sidenote').count()).toBeGreaterThan(0);
  } finally { await stopServer(server); }
});

// ── Review w9d47hl9a #12: band never forces horizontal page scroll ────────────

for (const vw of [1400, 1500, 1600]) {
  test(`band does not force horizontal page scroll at ${vw}px (wide measure + font-scale)`, async ({ page }) => {
    const port = nextPort();
    // Worst case: widest measure (80ch) and highest font-scale (1.4) push the
    // band's right edge toward the viewport edge — the overflow window the
    // finding identified (~1400-1610px). The width cap + #app overflow-x:clip
    // must keep document scrollWidth ≤ clientWidth.
    const { server } = await boot(
      page, port,
      { chrome: 'reader', marginNotes: true, measureCh: 80, fontScale: 1.4 },
      { width: vw, height: 900 });
    try {
      await expect.poll(async () => await page.locator('.sidenote').count()).toBeGreaterThan(0);
      const overflow = await page.evaluate(() => ({
        scrollW: document.documentElement.scrollWidth,
        clientW: document.documentElement.clientWidth,
      }));
      expect(overflow.scrollW).toBeLessThanOrEqual(overflow.clientW + 1);
    } finally { await stopServer(server); }
  });
}

// ── Review w9d47hl9a #14: sidenotes re-de-collide as lazy math renders ────────

// A document with >80 display-math blocks engages the lazy IntersectionObserver
// renderer; the early blocks carry cross-refs whose sidenotes must stay
// de-collided after the (initially under-estimated) placeholders render tall.
const MATH_DOC = (() => {
  let s = '# Math Doc\n\n';
  s += 'Top references: equation [(1)](#eq-1) and reference [[1]](#ref-1) sit close together[^a].\n\n';
  s += '[^a]: A footnote near the top whose sidenote must not overlap its neighbours.\n\n';
  s += '<a id="eq-1"></a>\n\n$$\ny = m x + b \\tag{1}\n$$\n\n';
  // 90 display blocks → over the LAZY_DISPLAY_MATH_THRESHOLD of 80.
  for (let i = 2; i <= 91; i++) {
    s += `Paragraph ${i} with prose to keep the column tall and scrollable.\n\n`;
    s += `$$\n\\sum_{k=0}^{${i}} \\frac{x^k}{k!} = e^x_{${i}} \\tag{${i}}\n$$\n\n`;
  }
  s += '## References\n\n<a id="ref-1"></a>\n[1] Smith, J. Example. 2020. [p](https://example.com/p).\n';
  return s;
})();

test('sidenotes stay de-collided after lazy-math placeholders render', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(
    page, port, { chrome: 'reader', marginNotes: true }, { width: 1500, height: 900 },
    { 'doc.md': MATH_DOC });
  try {
    // Lazy renderer must be engaged (the document is over-threshold).
    await expect(page.locator('#content')).toHaveClass(/lazy-math-doc/);
    const notes = page.locator('.sidenote');
    await expect.poll(async () => await notes.count()).toBeGreaterThan(0);
    // Let the eq-1 sidenote settle to its true (tall KaTeX) height + the band's
    // ResizeObserver / fonts.ready de-collision passes run.
    await page.waitForTimeout(700);

    const boxes = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('.sidenote').forEach((n) => {
        if (n.style.display === 'none') return;
        const r = n.getBoundingClientRect();
        out.push({ top: r.top, bottom: r.bottom });
      });
      return out.sort((a, b) => a.top - b.top);
    });
    // No two adjacent sidenotes overlap vertically (≤2px tolerance).
    for (let i = 1; i < boxes.length; i++) {
      expect(boxes[i].top).toBeGreaterThanOrEqual(boxes[i - 1].bottom - 2);
    }
  } finally { await stopServer(server); }
});
