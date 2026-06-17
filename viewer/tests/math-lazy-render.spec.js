// @ts-check
// Regression: bugs/2026-06-10-01 — iOS WebKit content-process crash on
// math-heavy survey files. Three-tier fix under test:
//   Tier 1: KaTeX output:'html' (no hidden MathML twin per equation) with the
//           TeX source preserved on a data-tex attribute for citation.js.
//   Tier 2: display-math blocks beyond LAZY_DISPLAY_MATH_THRESHOLD render
//           lazily via IntersectionObserver on the existing data-math-block
//           placeholder seam; small documents keep the eager behavior.
//   Tier 3: content-visibility:auto containment on .display-math-wrap.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 5300;
function nextPort() { return portCounter++; }

function mathDoc(n, { anchorAt = -1 } = {}) {
  let s = '# Big Math Doc\n\n';
  for (let i = 0; i < n; i++) {
    if (i === anchorAt) s += '<a id="deep-target"></a>\n\n';
    s += `Paragraph ${i} with inline $x_{${i}}$ math.\n\n`;
    s += `$$\ny_{${i}} = \\sum_{k=0}^{${i}} x_k + \\frac{1}{${i + 1}}\n$$\n\n`;
  }
  return s;
}

const BIG_BLOCKS = 120;   // above LAZY_DISPLAY_MATH_THRESHOLD (80)
const SMALL_BLOCKS = 5;   // below threshold — eager path preserved

test('Tier 1: no MathML twin — zero .katex-mathml nodes and data-tex on every top-level katex span', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'small.md': mathDoc(SMALL_BLOCKS) });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=small.md`);
    await page.waitForFunction(
      (n) => document.querySelectorAll('#content .display-math-wrap .katex').length >= n,
      SMALL_BLOCKS
    );
    const mathmlCount = await page.evaluate(
      () => document.querySelectorAll('#content .katex-mathml').length
    );
    expect(mathmlCount).toBe(0);
    const { total, withTex } = await page.evaluate(() => {
      const ks = [...document.querySelectorAll('#content .katex:not(.katex .katex)')];
      return {
        total: ks.length,
        withTex: ks.filter((k) => (k.getAttribute('data-tex') || '').length > 0).length,
      };
    });
    expect(total).toBeGreaterThanOrEqual(SMALL_BLOCKS * 2); // display + inline
    expect(withTex).toBe(total);
  } finally {
    await stopServer(server);
  }
});

test('Tier 2: large doc renders display math lazily — pending placeholders at load, render on scroll', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'big.md': mathDoc(BIG_BLOCKS) });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=big.md`);
    // Near-viewport math must render promptly...
    await page.waitForFunction(
      () => document.querySelectorAll('#content .display-math-wrap .katex').length > 0
    );
    // ...but far-below-fold blocks stay as unrendered pending placeholders.
    const counts = await page.evaluate(() => ({
      pending: document.querySelectorAll('#content [data-math-pending]').length,
      blocks: document.querySelectorAll('#content [data-math-block]').length,
    }));
    expect(counts.blocks).toBe(BIG_BLOCKS);
    expect(counts.pending).toBeGreaterThan(0);

    // Scrolling the last block into view renders it. Instant jump: a CSS
    // smooth scroll animates toward a position computed up front, while
    // above-viewport placeholders rendering en route shift the target
    // (overflow-anchor is disabled) — real user scrolling is incremental.
    await page.evaluate(() => {
      const all = document.querySelectorAll('#content [data-math-block]');
      all[all.length - 1].scrollIntoView({ behavior: 'instant' });
    });
    await page.waitForFunction(() => {
      const all = document.querySelectorAll('#content [data-math-block]');
      const last = all[all.length - 1];
      return !last.hasAttribute('data-math-pending') && !!last.querySelector('.katex');
    });
  } finally {
    await stopServer(server);
  }
});

test('Tier 2 threshold: small doc keeps the eager path — all display math rendered, no pending placeholders', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'small.md': mathDoc(SMALL_BLOCKS) });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=small.md`);
    await page.waitForFunction(
      (n) => document.querySelectorAll('#content .display-math-wrap .katex').length >= n,
      SMALL_BLOCKS
    );
    const pending = await page.evaluate(
      () => document.querySelectorAll('#content [data-math-pending]').length
    );
    expect(pending).toBe(0);
  } finally {
    await stopServer(server);
  }
});

test('Tier 3: containment is scoped to lazy docs — content-visibility:auto in big docs, default in small docs', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'content-visibility computed-style assertion is chromium-scoped');
  const port = nextPort();
  const dir = createFixtureDir({
    'big.md': mathDoc(BIG_BLOCKS),
    'small.md': mathDoc(SMALL_BLOCKS),
  });
  const server = await startServer(dir, port);
  try {
    // Lazy doc: wrappers get containment.
    await page.goto(`http://localhost:${port}?file=big.md`);
    await page.waitForFunction(
      () => document.querySelectorAll('#content .display-math-wrap .katex').length > 0
    );
    const cvBig = await page.evaluate(() => {
      const el = document.querySelector('#content .display-math-wrap');
      return el ? getComputedStyle(el).contentVisibility : 'missing';
    });
    expect(cvBig).toBe('auto');

    // Eager doc: no containment — remembered sizes don't survive reload, so
    // containment would break pixel-exact refresh scroll-restore there.
    await page.goto(`http://localhost:${port}?file=small.md`);
    await page.waitForFunction(
      (n) => document.querySelectorAll('#content .display-math-wrap .katex').length >= n,
      SMALL_BLOCKS
    );
    const cvSmall = await page.evaluate(() => {
      const el = document.querySelector('#content .display-math-wrap');
      return el ? getComputedStyle(el).contentVisibility : 'missing';
    });
    expect(cvSmall).toBe('visible');
  } finally {
    await stopServer(server);
  }
});

test('deep-anchor load into a large doc lands on a rendered equation', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'big.md': mathDoc(BIG_BLOCKS, { anchorAt: BIG_BLOCKS - 5 }) });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=big.md#deep-target`);
    // The block right after the anchor must end up rendered and on-screen.
    await page.waitForFunction(() => {
      const a = document.getElementById('deep-target');
      if (!a) return false;
      // The standalone <a> line is wrapped in a <p> by markdown-it; walk
      // block-level siblings from the wrapping paragraph.
      let el = (a.closest('#content > *') || a).nextElementSibling;
      while (el && !el.hasAttribute('data-math-block')) el = el.nextElementSibling;
      if (!el || !el.querySelector('.katex')) return false;
      const r = el.getBoundingClientRect();
      return r.top >= -r.height && r.top <= window.innerHeight;
    });
  } finally {
    await stopServer(server);
  }
});
