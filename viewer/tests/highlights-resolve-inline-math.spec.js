// @ts-check
// Regression: PLAIN_SPANNING_MATH on a paragraph dense with inline math +
// HTML comment / markdown-link refs (e.g. surveys/5g-nr-ldpc/appendix-a.md
// §A.8.3 WLOG-normalization paragraph). The pre-fix `resolveInlineMath`
// fallback for the FIRST selected katex element used a position-ratio
// heuristic that drifted because:
//   (a) `blockSrc.length` includes `<!-- ref:... -->` HTML comments and
//       `[(N)](#eq-N)` markdown-link characters that don't appear in DOM,
//   (b) `blockEl.textContent.length` is inflated non-uniformly per math
//       span by KaTeX MathML annotations + rendered-glyph spans.
// Both axes drift independently, so the ratio comparison silently picked
// the wrong source-side `$...$` (e.g. math#3 instead of math#4) and the
// downstream `prefixNorm.lastIndexOf(plainHead)` lookup returned -1. The
// fix in `resolveInlineMath` adds a fast path: when DOM katex count
// matches source `$...$` count, the mapping is strictly index-based.
// See: bugs/2026-04-29-01-resolve-inline-math-ratio-drift.md
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4900;
function nextPort() { return portCounter++; }

const DENSE_PARA =
  '**WLOG normalization of incoming messages.** Strictly speaking, the messages produced by the BP rules ' +
  '(Equations <!-- ref:a.4-4 -->[(19)](#eq-19) and <!-- ref:a.5-4 -->[(23)](#eq-23)) are non-negative ' +
  '*functions*, not necessarily PMFs — they are defined only up to positive scale. Both updates are ' +
  'positively homogeneous: multiplying any single input message by $c > 0$ rescales every downstream ' +
  'message by the same factor, which the proportionality "$\\propto$" in Equation ' +
  '<!-- ref:a.6-1 -->[(24)](#eq-24) absorbs when the belief is normalized. The LLR derivation in §A.8.2 ' +
  'makes the invariance even sharper — every place a message enters, it appears as a ratio ' +
  '$\\mu(0)/\\mu(1)$ in which a common scale cancels exactly. We are therefore free to renormalize ' +
  'each CN-input message to sum to one without altering any LLR or any hard decision, and we adopt ' +
  '$\\mu_{x_{j\'} \\to f_i}(0) + \\mu_{x_{j\'} \\to f_i}(1) = 1$ for every ' +
  '$j\' \\in \\mathcal{N}(i) \\setminus j$ throughout the remainder of §A.8.3. This is purely an ' +
  'interpretive convenience: it lets the product $\\prod_{j\'} \\mu_{x_{j\'} \\to f_i}$ be read as a ' +
  'literal joint PMF, so that the upcoming indicator-weighted sum is a probability of an event rather ' +
  'than the same expression scaled by an unnormalized partition function ' +
  '$Z = \\prod_{j\'} [\\mu_{x_{j\'} \\to f_i}(0) + \\mu_{x_{j\'} \\to f_i}(1)]$ (which would cancel ' +
  'anyway when the LLR is taken in Equation <!-- ref:a.8.3-6 -->[(40)](#eq-40)).\n';

test('PLAIN_SPANNING_MATH on a 7-math-span paragraph with ref-links resolves to the correct source position', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'dense.md': '# Dense\n\n' + DENSE_PARA });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=dense.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await page.waitForFunction(() => {
      return document.querySelectorAll('#content p .katex:not(.katex .katex)').length >= 7;
    });

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('show') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Build a Range that mirrors the reported user gesture: start at "we
    // adopt" (the second occurrence of "we" in the paragraph, immediately
    // before math#4) and end after "interpretive convenience" (after
    // math#5, before math#6).
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      let startText = null, startOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const t = /** @type {Text} */ (child);
        const idx = (t.nodeValue || '').lastIndexOf('and we adopt ');
        if (idx !== -1) { startText = t; startOffset = idx + 'and '.length; }
      }
      if (!startText) return { err: 'start text not found' };

      let endText = null, endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const t = /** @type {Text} */ (child);
        const idx = (t.nodeValue || '').indexOf('interpretive convenience');
        if (idx !== -1) { endText = t; endOffset = idx + 'interpretive convenience'.length; break; }
      }
      if (!endText) return { err: 'end text not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { ok: true };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="blue"]').click();
    await page.waitForTimeout(300);

    expect(toasts.find(t => /Could not locate/i.test(t)),
      `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/dense.md`);
    const txt = await res.text();
    // The wrap must start at "we adopt" and end at "interpretive convenience".
    expect(txt).toMatch(/==blue:\s*we adopt \$\\mu_\{x_\{j'\} \\to f_i\}\(0\)[\s\S]*?interpretive convenience==/);
  } finally {
    stopServer(server, dir);
  }
});

// Regression for bugs/2026-06-02-04: a selection that STARTS INSIDE one inline
// math span and ends in plain text after a SECOND span (the MIXED_MATH_TEXT
// multi-span case, e.g. the §5 positivity bullet `$\lvert d_a\rvert \le f_a$,
// $\lvert D_k\rvert \le S_k$ term-by-term`). The inline reconstruction only
// processed the single startKatex and missed the intermediate span → "Could not
// locate highlight in source" toast. Fix: route multi-span MIXED_MATH_TEXT to
// the robust sidecar backend (block line-range, no source text-matching).
test('MIXED_MATH_TEXT spanning two inline-math spans falls back to sidecar (bug 2026-06-02-04)', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'multimath.md': '# Multi\n\nEdge-wise $\\lvert d_a\\rvert \\le f_a$, $\\lvert D_k\\rvert \\le S_k$ term-by-term gives the bound.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=multimath.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await page.waitForFunction(() =>
      document.querySelectorAll('#content p .katex:not(.katex .katex)').length >= 2);

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) new MutationObserver(() => {
        if (tEl.classList.contains('show') && tEl.textContent) {
          // @ts-ignore
          window.__recordToast(tEl.textContent);
        }
      }).observe(tEl, { attributes: true, childList: true, subtree: true });
    });

    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };
      const firstKatex = p.querySelector('.katex:not(.katex .katex)');
      if (!firstKatex) return { err: 'no katex' };
      let endText = null, endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const idx = (child.nodeValue || '').indexOf('term-by-term');
        if (idx !== -1) { endText = child; endOffset = idx + 'term-by-term'.length; break; }
      }
      if (!endText) return { err: 'no end text' };
      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(firstKatex, 0);          // start INSIDE the first inline-math span
      r.setEnd(endText, endOffset);        // ...end in plain text after the second span
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: 100, clientY: 100, bubbles: true }));
      return { ok: true };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(80);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="blue"]').click();
    await page.waitForTimeout(200);

    // Bug symptom gone.
    expect(toasts.find(t => /Could not locate/i.test(t)),
      `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    // Routed to the robust sidecar backend — one sidecar highlight, no inline source edit.
    const annRes = await request.get(`http://localhost:${port}/api/highlights/multimath.md`);
    expect(annRes.ok()).toBe(true);
    const ann = await annRes.json();
    expect(ann.highlights.length).toBe(1);
    expect(ann.highlights[0].backend).toBe('sidecar');

    const src = await (await request.get(`http://localhost:${port}/api/md/multimath.md`)).text();
    expect(src).not.toContain('==blue:');
  } finally {
    stopServer(server, dir);
  }
});
