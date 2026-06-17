// @ts-check
// Coverage for the 2026-05-25 CommonMark column-0 inline-HTML bugs.
//
//   Bug 2026-05-25-01 — secref / secxref markers at column 0 (paragraph or
//     list-item content) trigger CommonMark Type-2 HTML-block parsing,
//     swallowing the subsequent markdown link as raw text. Lint regex
//     extended; 32 source occurrences fixed.
//   Bug 2026-05-25-02 — `<a id="sec-X.Y.Z"></a>` at column 0 of a heading
//     line blocks ATX heading parsing (`#` must be at col 0-3). 1306
//     corpus lines migrated to `### <a id="..."></a>Title`. A regression
//     in `stripInlineMarkersForSlug()` (outline panel displaying literal
//     `<a id>` HTML) was caught the same session and fixed.
//
// Each test below is a structural assertion against the rendered DOM via
// markdown-it (the viewer's exact stack). Failures indicate either a
// reintroduction of the bug source pattern or a regression in the
// renderer / outline pipeline.

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 5400;
function nextPort() { return portCounter++; }

// Outline-panel assertions need the docked sidebar — pin classic layout
// (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

// ─────────────────────────────────────────────────────────────────────────────
// Bug 2026-05-25-02 — heading anchor placement (h3 / h4 / h5 / h6)
// ─────────────────────────────────────────────────────────────────────────────

test('Bug A: post-ATX heading anchor — heading renders as <h3>, sec-anchor lives inside', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Channel densities',
      '',
      'Body paragraph.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Top');
    // The §D.5 line must render as an <h3>, NOT a <p> with literal `### ` visible.
    const h3 = page.locator('#content h3');
    await expect(h3).toHaveCount(1);
    await expect(h3).toHaveText('D.5 Channel densities');
    // The inline sec-anchor lives inside the h3.
    const anchor = page.locator('h3 a[id="sec-D.5"]');
    await expect(anchor).toHaveCount(1);
    // And getElementById finds it.
    const found = await page.evaluate(() => !!document.getElementById('sec-D.5'));
    expect(found).toBe(true);
    // No literal `### ` appears anywhere in the rendered body.
    const literalHash = await page.evaluate(() => /\#{3}\s+D\./.test(document.body.innerText));
    expect(literalHash).toBe(false);
  } finally {
    stopServer(server, dir);
  }
});

test('Bug A: post-ATX heading anchor at h4 / h5 / h6', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Parent',
      '',
      '<!-- sec:D.5.1 -->',
      '#### <a id="sec-D.5.1"></a>D.5.1 H4 sub',
      '',
      '<!-- sec:D.5.1.1 -->',
      '##### <a id="sec-D.5.1.1"></a>D.5.1.1 H5 leaf',
      '',
      '<!-- sec:D.5.1.1.1 -->',
      '###### <a id="sec-D.5.1.1.1"></a>D.5.1.1.1 H6 leaf',
      '',
      'Body.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h3')).toHaveText('D.5 Parent');
    await expect(page.locator('#content h4')).toHaveText('D.5.1 H4 sub');
    await expect(page.locator('#content h5')).toHaveText('D.5.1.1 H5 leaf');
    await expect(page.locator('#content h6')).toHaveText('D.5.1.1.1 H6 leaf');
    // All four inline sec-anchors live in the DOM and parent-match.
    for (const [sec, tag] of [
      ['sec-D.5', 'H3'], ['sec-D.5.1', 'H4'],
      ['sec-D.5.1.1', 'H5'], ['sec-D.5.1.1.1', 'H6'],
    ]) {
      const parent = await page.evaluate((id) => {
        const el = document.getElementById(id);
        return el && el.parentElement ? el.parentElement.tagName : null;
      }, sec);
      expect(parent).toBe(tag);
    }
    // No literal `###`/`####`/`#####`/`######` text in the body.
    const literalHashes = await page.evaluate(
      () => (document.body.innerText.match(/#{3,6}\s+D\./g) || []).length
    );
    expect(literalHashes).toBe(0);
  } finally {
    stopServer(server, dir);
  }
});

test('Bug A regression: legacy column-0 heading anchor would render as <p> (parser-spec witness)', async ({ page }) => {
  // This test documents WHY the pre-2026-05-25 convention was wrong.
  // We render the legacy form and assert the symptom — heading demoted
  // to a paragraph with literal `### ` visible. If a future change ever
  // makes markdown-it permissive enough to parse this as an <h3>, the
  // bug premise no longer holds and the lint guard could be relaxed —
  // until then, this test pins the failure mode.
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '<a id="sec-D.5"></a>### D.5 Legacy form',
      '',
      'Body.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    // The h1 at top renders fine.
    await expect(page.locator('#content h1')).toHaveText('Top');
    // The legacy form must NOT render as h3 — it falls through to <p>.
    const h3count = await page.locator('#content h3').count();
    expect(h3count).toBe(0);
    // The literal `### ` text is visible in the body.
    const hasLiteralHash = await page.evaluate(
      () => /###\s+D\.5/.test(document.body.innerText)
    );
    expect(hasLiteralHash).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Bug 2026-05-25-01 — secref / secxref column-0 / list-item-content
// ─────────────────────────────────────────────────────────────────────────────

test('Bug B: secref marker mid-paragraph renders link as clickable <a>', async ({ page }) => {
  // Sanity baseline — the working form. The marker has preceding prose,
  // so it does not start a CommonMark Type-2 HTML block.
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Heading',
      '',
      'See <!-- secref:D.5 -->[§D.5](#sec-D.5) for details.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    const link = page.locator('p a[href="#sec-D.5"]');
    await expect(link).toHaveCount(1);
    await expect(link).toHaveText('§D.5');
    // No literal `[§D.5](#sec-D.5)` text anywhere in body.
    const hasLiteralLink = await page.evaluate(
      () => /\[§D\.5\]\(#sec-D\.5\)/.test(document.body.innerText)
    );
    expect(hasLiteralLink).toBe(false);
  } finally {
    stopServer(server, dir);
  }
});

test('Bug B regression: secref at column 0 of a paragraph swallows the link as raw text', async ({ page }) => {
  // Pins the parser-spec witness for the paragraph-level failure.
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Heading',
      '',
      '<!-- secref:D.5 -->[§D.5](#sec-D.5) opens the paragraph.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    // Wait for the page to render (otherwise the link-count assertion
    // below passes vacuously because the DOM is still empty).
    await expect(page.locator('#content h1')).toHaveText('Top');
    await expect(page.locator('#content h3')).toHaveText('D.5 Heading');
    // The `[§D.5](#sec-D.5)` does NOT become a clickable link because
    // the column-0 `<!--` opens a Type-2 HTML block consuming the line.
    const link = page.locator('p a[href="#sec-D.5"]');
    await expect(link).toHaveCount(0);
    // Literal markdown source IS visible in the body.
    const hasLiteralLink = await page.evaluate(
      () => /\[§D\.5\]\(#sec-D\.5\)/.test(document.body.innerText)
    );
    expect(hasLiteralLink).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

test('Bug B regression: secref as first child of a list item also swallows the link', async ({ page }) => {
  // Same Type-2 trigger inside <li> sub-document. This is the list-item
  // variant covered by lint check #3's regex `(?:[-*+]\s+|\d+\.\s+)?`.
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Heading',
      '',
      '- <!-- secref:D.5 -->[§D.5](#sec-D.5) — TOC entry.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Top');
    await expect(page.locator('#content h3')).toHaveText('D.5 Heading');
    const link = page.locator('li a[href="#sec-D.5"]');
    await expect(link).toHaveCount(0);
    const hasLiteralLink = await page.evaluate(
      () => /\[§D\.5\]\(#sec-D\.5\)/.test(document.body.innerText)
    );
    expect(hasLiteralLink).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

test('Bug B fix pattern: glyph-before-marker in TOC list renders byte-identically', async ({ page }) => {
  // The post-2026-05-25 fix pattern for TOC bullets uses a literal `§`
  // glyph before the marker, with link text `D.X` (no §). Visual output
  // is "§D.X" — same as before the fix, but the source now parses cleanly.
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': [
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Heading',
      '',
      '- §<!-- secref:D.5 -->[D.5](#sec-D.5) — TOC entry.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    const link = page.locator('li a[href="#sec-D.5"]');
    await expect(link).toHaveCount(1);
    await expect(link).toHaveText('D.5');
    // The full visible text on the list item is "§D.5 — TOC entry."
    const liText = await page.locator('li').first().innerText();
    expect(liText.replace(/\s+/g, ' ')).toContain('§D.5 — TOC entry.');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Outline panel — must show clean heading text, not literal `<a id>` HTML
// ─────────────────────────────────────────────────────────────────────────────
//
// This was a regression from the Bug A fix: after migrating heading
// anchors to the post-ATX position, the heading line's source text is
// `### <a id="sec-D.5"></a>D.5 Title`. The outline panel's
// `extractHeadings()` captures the `(.+?)` group after `###`, which
// includes the inline `<a id>` HTML. `stripInlineMarkersForSlug()`
// did not strip raw HTML tags (only markdown link / code / bold /
// italic), so the displayed outline entry was literally
// `<a id="sec-D.5"></a>D.5 Title`. Fixed by adding inline-HTML strip
// to `stripInlineMarkersForSlug()` to match `slugify()`'s behavior.

async function openOutline(page) {
  await page.locator('.sidebar-tab[data-tab="outline"]').click();
  await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);
}

test('outline panel — entries display clean text (no inline <a id> HTML)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['doc.md']),
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:D.5 -->',
      '### <a id="sec-D.5"></a>D.5 Channel densities',
      '',
      '<!-- sec:D.5.1 -->',
      '#### <a id="sec-D.5.1"></a>D.5.1 Step 1',
      '',
      '<!-- sec:D.5.2 -->',
      '#### <a id="sec-D.5.2"></a>D.5.2 Step 2',
      '',
      'Body.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Top');
    await openOutline(page);
    // Wait for entries to render
    await expect(page.locator('.outline-entry')).toHaveCount(4);
    // No outline entry's text may contain literal `<a id="` substring.
    const buggyCount = await page.evaluate(() => {
      const entries = Array.from(document.querySelectorAll('.outline-entry'));
      return entries.filter(e => (e.textContent || '').includes('<a id="')).length;
    });
    expect(buggyCount).toBe(0);
    // And the specific entries display only the heading text.
    const texts = await page.locator('.outline-entry').allTextContents();
    expect(texts).toEqual([
      'Top',
      'D.5 Channel densities',
      'D.5.1 Step 1',
      'D.5.2 Step 2',
    ]);
  } finally {
    stopServer(server, dir);
  }
});

test('outline panel — strips inline <!-- secref --> markers from heading text', async ({ page }) => {
  // A heading that carries an inline `<!-- xref:... -->` marker after its
  // section anchor should also display clean — the comment is stripped
  // by the same HTML-tag rule. This is the appendix-a.md pattern
  // (e.g., `#### <a id="sec-A.8.1"></a>A.8.1 ... (Recovering Equation
  // [(2)](decoding-algorithms.md#eq-2) <!-- xref:5.2.1-1 -->)`).
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['doc.md']),
    'doc.md': [
      '# Top',
      '',
      '<!-- sec:A.8.1 -->',
      '#### <a id="sec-A.8.1"></a>A.8.1 Channel LLR (Recovering Equation [(2)](decoding-algorithms.md#eq-2) <!-- xref:5.2.1-1 -->)',
      '',
      'Body.',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Top');
    await openOutline(page);
    await expect(page.locator('.outline-entry')).toHaveCount(2);
    const texts = await page.locator('.outline-entry').allTextContents();
    // Heading-text outline entry: <a id> stripped, <!-- xref --> stripped,
    // markdown link `[(2)](...)` collapsed to `(2)`.
    expect(texts[1]).toBe('A.8.1 Channel LLR (Recovering Equation (2) )');
    // (The trailing ` )` is a side-effect of the comment being stripped
    // mid-parens; harmless and matches the slugify behavior.)
  } finally {
    stopServer(server, dir);
  }
});
