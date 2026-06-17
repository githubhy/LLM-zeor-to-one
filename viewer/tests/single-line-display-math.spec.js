// @ts-check
// Regression: single-line $$...$$ display math is shielded into a
// data-math-block element so the highlight pipeline can identify and wrap
// it. Pre-fix (bug 2026-04-30-01), only multi-line `$$\n...\n$$` was
// shielded; single-line equations like
//   $$K_\ell = \sum ... = O(...)$$
// (used in surveys/5g-nr-ldpc/fundamentals.md §3.6.1) had no
// data-math-block attribute and the user couldn't click-and-highlight them.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4950;
function nextPort() { return portCounter++; }

test('single-line $$...$$ display math is shielded with data-math-block', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'oneline.md':
      '# OneLine\n\n' +
      'Some prose before.\n\n' +
      '$$K_\\ell = \\sum_{k=0}^{2\\ell} (\\text{nodes at depth } k) \\;=\\; O\\!\\left(((d_v-1)(d_c-1))^{\\ell}\\right)$$\n\n' +
      'Some prose after.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=oneline.md`);
    await expect(page.locator('#content h1')).toBeVisible();
    await page.waitForFunction(() =>
      document.querySelectorAll('#content [data-math-block]').length >= 1
    );

    await expect(page.locator('#content [data-math-block]')).toHaveCount(1);
    await expect(page.locator('#content .katex-display')).toHaveCount(1);
  } finally {
    stopServer(server, dir);
  }
});

test('single-line $$...$$ can be highlighted via the swatch toolbar', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'oneline.md':
      '# OneLine\n\n' +
      'Some prose before.\n\n' +
      '$$K_\\ell = O\\left(((d_v-1)(d_c-1))^{\\ell}\\right)$$\n\n' +
      'Some prose after.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=oneline.md`);
    await expect(page.locator('#content [data-math-block="0"]')).toBeVisible();

    const sel = await page.evaluate(() => {
      const el = document.querySelector('#content [data-math-block="0"]');
      if (!el) return { err: 'block not found' };
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const t = tw.nextNode();
      if (!t) return { err: 'no text in block' };
      const s = window.getSelection(); s.removeAllRanges();
      const r = document.createRange();
      r.setStart(t, 0);
      r.setEnd(t, Math.min(2, (t.nodeValue || '').length));
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: 100, clientY: 100, bubbles: true }));
      return { ok: true };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();
    await page.waitForTimeout(200);

    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/oneline.md`);
    const txt = await res.text();
    expect(txt).toContain('==green: $$K_\\ell = O\\left(((d_v-1)(d_c-1))^{\\ell}\\right)$$==');
  } finally {
    stopServer(server, dir);
  }
});
