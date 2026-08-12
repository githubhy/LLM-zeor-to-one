// Browser-level regression for bugs/2026-07-09-02.
//
// The pre-existing suite covers a PLAIN_TEXT selection crossing bold/italic/code
// (highlights.spec.js:725/815/897/987) — that branch has been protected since
// `expandRangeToFormatBoundaries()` was wired into Step 5C.
//
// It does NOT cover a selection that starts inside an emphasis span and ENDS
// INSIDE INLINE MATH. That routes to Step 5P (PLAIN_SPANNING_MATH) / 5M, which
// never called the DOM-level expansion. Every one of the three §4.8.1
// corruptions had exactly that shape, ending inside $n$, $\varepsilon$ and
// $f_D T = ...$ respectively.
//
// Guarded now by the source-level `snapOutOfInlineSpans()` (viewer.js Step 7B),
// which runs after 5C/5M/5P converge and therefore covers all three branches.

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4810;
function nextPort() { return portCounter++; }

/**
 * Select from the first occurrence of `startWord` (a direct text-node child of
 * the paragraph) through the end of the last KaTeX span, then apply `color`.
 */
async function selectFromWordThroughMath(page, startWord) {
  return page.evaluate((word) => {
    const p = document.querySelector('#content p');
    if (!p) return { err: 'no p' };
    // start: inside the <em>/<strong> wrapping `word`, at the word's first char
    const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
    let startText = null; let startOffset = 0;
    while (walker.nextNode()) {
      const tn = walker.currentNode;
      if (tn.parentElement.closest('.katex')) continue;
      const i = (tn.nodeValue || '').indexOf(word);
      if (i !== -1) { startText = tn; startOffset = i; break; }
    }
    if (!startText) return { err: 'start word not found' };

    const katexes = p.querySelectorAll('.katex:not(.katex .katex)');
    if (!katexes.length) return { err: 'no katex' };
    const lastKatex = katexes[katexes.length - 1];

    const r = document.createRange();
    r.setStart(startText, startOffset);
    r.setEndAfter(lastKatex);
    const s = window.getSelection();
    s.removeAllRanges();
    s.addRange(r);
    document.dispatchEvent(new Event('selectionchange'));
    return { selText: r.toString() };
  }, startWord);
}

const CASES = [
  {
    name: 'selection starting inside *em* and ending inside inline math',
    file: 'em.md',
    body: '# Em\n\nThroughout this section, then, *motion* names the variation in $n$ and more.\n',
    startWord: 'motion',
    color: 'blue',
    // opener must sit OUTSIDE the emphasis
    expect: /==blue: \*motion\* names the variation in \$n\$==/,
    forbid: /\*==blue: motion\*/,
    innerTag: 'em',
  },
  {
    name: 'selection starting inside **strong** and ending inside inline math',
    file: 'strong.md',
    body: '# Strong\n\nThe one knob is the **normalized Doppler** $f_D T$ and more prose.\n',
    startWord: 'normalized',
    color: 'yellow',
    expect: /==yellow: \*\*normalized Doppler\*\* \$f_D T\$==/,
    forbid: /\*\*==yellow: normalized Doppler\*\*/,
    innerTag: 'strong',
  },
];

for (const c of CASES) {
  test(`bug 2026-07-09-02: ${c.name}`, async ({ page, request }) => {
    const port = nextPort();
    const dir = createFixtureDir({ [c.file]: c.body });
    const server = await startServer(dir, port);
    const toasts = [];
    await page.exposeFunction('__recordToast', (m) => toasts.push(m));
    try {
      await page.goto(`http://localhost:${port}?file=${c.file}`);
      await expect(page.locator(`#content ${c.innerTag}`)).toBeVisible();
      await expect(page.locator('#content p .katex').first()).toBeVisible();

      await page.evaluate(() => {
        const tEl = document.getElementById('toast');
        if (!tEl) return;
        new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) window.__recordToast(tEl.textContent);
        }).observe(tEl, { attributes: true, childList: true, subtree: true });
      });

      const sel = await selectFromWordThroughMath(page, c.startWord);
      expect(sel.err).toBeUndefined();

      await page.waitForTimeout(60);
      await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
      await page.locator(`#hl-toolbar .hl-swatch[data-action="${c.color}"]`).click();
      await page.waitForTimeout(250);

      expect(toasts.find((t) => /Could not locate/i.test(t)),
        `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();

      // 1) SOURCE: delimiters must nest, never interleave
      const txt = await (await request.get(`http://localhost:${port}/api/md/${c.file}`)).text();
      expect(txt, 'opener spliced inside the inline span (the bug)').not.toMatch(c.forbid);
      expect(txt).toMatch(c.expect);

      // 2) DOM: exactly one coloured mark, with the inline span nested inside it
      const marks = page.locator(`#content mark.hl-${c.color}`);
      await expect(marks).toHaveCount(1);
      await expect(marks.locator(c.innerTag)).toHaveCount(1);

      // 3) No literal marker text leaked into the rendered page
      const bodyText = await page.locator('#content').innerText();
      expect(bodyText, 'highlight markup rendered as literal source').not.toContain('==');
    } finally {
      await stopServer(server);
    }
  });
}
