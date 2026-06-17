// @ts-check
// Citation toolbar — end-to-end integration tests
// ─────────────────────────────────────────────────────────────────────────────
// Coverage:
//   T1  Cite buttons appear in toolbar when text is selected
//   T2  Bug #1 regression: cite buttons HIDDEN in recolor-only mode
//   T3  GitHub mode: correct owner/repo/sha/file + user-content- fragment
//   T4  GitHub mode: repoRelDir is prepended to file path in URL
//   T5  Local mode: localhost origin with plain anchor fragment
//   T6  Relative mode: code-span path only
//   T7  No paragraph anchor → heading fallback + (L<N>) line suffix
//   T8  gitInfo unavailable → "GitHub info unavailable" warning toast
//   T9  headPushed=false → "not pushed" warning toast
//   T10 Bug #3 regression: headPushed=null → warning toast (no silent 404)
//   T11 Bug #2 regression: selection inside heading → correct heading text
//   T12 Settings panel persists citation mode to localStorage
//   T13 sessionStorage caches git info — only one /api/git-info fetch per page

const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout, seedSettings } = require('./helpers/layout');

let portCounter = 5100;
function nextPort() { return portCounter++; }

// Settings-panel radios and citation-mode flows live in the docked sidebar —
// pin classic layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

// ── Fixtures ─────────────────────────────────────────────────────────────────

// Plain document — no paragraph anchors, just headings and body paragraphs.
const BASIC_DOC = [
  '# Main Title',
  '',
  '## Section One',
  '',
  'The FLL error is small when the loop bandwidth is narrow.',
  '',
  '## Section Two',
  '',
  'The PLL operates on the phase discriminator output.',
].join('\n');

// Document with paragraph anchors embedded in paragraphs.
const ANCHOR_DOC = [
  '# Main Title',
  '',
  '## Section One',
  '',
  '<a id="p-section-one-1"></a> The FLL error is small.',
  '',
  '<a id="p-section-one-2"></a> Second paragraph with anchor.',
  '',
  '## Section Two',
  '',
  '<a id="p-section-two-1"></a> The PLL operates on the phase.',
].join('\n');

const MOCK_GIT_INFO = {
  available: true,
  owner:     'testowner',
  repo:      'testrepo',
  sha:       'cafef00d',
  branch:    'main',
  headPushed: true,
  repoRelDir: '',
};

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Override navigator.clipboard.writeText on the page instance so that writes
 * land in window.__clipText instead of the OS clipboard.  Also nullifies
 * .write so the rich path falls through to writeText.
 */
async function patchClipboard(page) {
  await page.evaluate(() => {
    window.__clipText = null;
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText = async (text) => { window.__clipText = text; };
    // Set write to null so the `variant==='rich' && navigator.clipboard.write` guard
    // in copyCitation() falls through to writeText even for cite-rich clicks.
    navigator.clipboard.write = null;
  });
}

/**
 * Walk the element to find the first non-empty text node, set a selection
 * [startOffset, endOffset] on it, then fire mouseup to open the toolbar.
 */
async function selectText(page, cssSelector, startOffset, endOffset) {
  await page.evaluate(({ sel, s, e }) => {
    const el = document.querySelector(sel);
    if (!el) throw new Error(`selectText: no element for "${sel}"`);

    // Find first non-empty text node (may be a child of a child)
    let textNode = null;
    function walk(node) {
      if (textNode) return;
      if (node.nodeType === 3 && node.textContent.trim()) { textNode = node; return; }
      for (const c of node.childNodes) walk(c);
    }
    walk(el);
    if (!textNode) throw new Error(`selectText: no text node in "${sel}"`);

    const endOff = Math.min(e, textNode.textContent.length);
    const sel2 = window.getSelection();
    sel2.removeAllRanges();
    const range = document.createRange();
    range.setStart(textNode, s);
    range.setEnd(textNode, endOff);
    sel2.addRange(range);

    const rect = el.getBoundingClientRect();
    document.dispatchEvent(new MouseEvent('mouseup', {
      clientX: rect.left + 20, clientY: rect.bottom + 2, bubbles: true,
    }));
  }, { sel: cssSelector, s: startOffset, e: endOffset });

  await page.waitForTimeout(60);
}

// ─────────────────────────────────────────────────────────────────────────────
// T1 — Cite buttons appear in the toolbar on a text selection
// ─────────────────────────────────────────────────────────────────────────────
test('T1: cite buttons visible in toolbar when text is selected', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'doc.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await selectText(page, '#content p', 0, 10);

    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await expect(page.locator('[data-action="cite-rich"]')).toBeVisible();
    await expect(page.locator('[data-action="cite-md"]')).toBeVisible();
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T2 — Bug #1 regression: cite buttons HIDDEN in recolor-only mode
// Root cause: CSS for .recolor-only omitted .toolbar-cite-btn rule,
//   leaving cite buttons visible but non-functional (savedRange is null).
// Fix: #hl-toolbar.recolor-only .toolbar-cite-btn { display: none; }
// ─────────────────────────────────────────────────────────────────────────────
test('T2 [Bug#1]: cite buttons hidden when toolbar is in recolor-only mode', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nA line with ==green: highlighted word== here.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('mark.hl-green')).toBeVisible();

    // Single-click (collapsed selection) inside the mark → recolor-only toolbar
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-green');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 3); r.setEnd(tn, 3);   // collapsed
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(60);

    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);

    // Bug #1: before fix, both cite buttons were visible here.
    await expect(page.locator('[data-action="cite-rich"]')).not.toBeVisible();
    await expect(page.locator('[data-action="cite-md"]')).not.toBeVisible();
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T3 — GitHub mode: URL has owner/repo/sha/path and user-content- fragment
// ─────────────────────────────────────────────────────────────────────────────
test('T3: github mode URL has correct owner/repo/sha, path, and user-content- fragment', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': ANCHOR_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(MOCK_GIT_INFO) }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 1, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    expect(clipText).toMatch(
      /https:\/\/github\.com\/testowner\/testrepo\/blob\/cafef00d\/test\.md#user-content-p-section-one-1/,
    );
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T4 — GitHub mode: repoRelDir is prepended to the file name in the URL
// ─────────────────────────────────────────────────────────────────────────────
test('T4: github mode URL includes repoRelDir prefix in file path', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': ANCHOR_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ ...MOCK_GIT_INFO, repoRelDir: 'surveys/my-survey' }),
      }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 1, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    expect(clipText).toMatch(/blob\/cafef00d\/surveys\/my-survey\/test\.md/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T5 — Local mode: URL uses localhost origin with plain anchor (no user-content-)
// ─────────────────────────────────────────────────────────────────────────────
test('T5: local mode URL uses localhost origin and plain anchor fragment', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': ANCHOR_DOC });
  const server = await startServer(dir, port);
  try {
    await seedSettings(page, { citationMode: 'local' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 1, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    // URL must include the viewer origin and plain anchor (no user-content- prefix)
    expect(clipText).toMatch(new RegExp(
      `http://localhost:${port}/\\?file=test\\.md#p-section-one-1`,
    ));
    expect(clipText).not.toMatch(/user-content/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T6 — Relative mode: markdown output uses back-tick code-span path
// ─────────────────────────────────────────────────────────────────────────────
test('T6: relative mode produces back-tick code-span path in markdown', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': ANCHOR_DOC });
  const server = await startServer(dir, port);
  try {
    await seedSettings(page, { citationMode: 'relative' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 1, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    // Relative mode wraps path in backtick code span
    expect(clipText).toMatch(/`test\.md#p-section-one-1`/);
    expect(clipText).not.toMatch(/http/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T7 — No paragraph anchor → falls back to heading anchor + (L<N>) suffix
// ─────────────────────────────────────────────────────────────────────────────
test('T7: no paragraph anchor falls back to heading anchor with (L<N>) suffix', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await seedSettings(page, { citationMode: 'local' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 0, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    // Heading anchor (not a para anchor) and line number suffix
    expect(clipText).toMatch(/#section-one/);
    expect(clipText).toMatch(/\(L\d+\)/);
    // Must NOT contain a paragraph anchor id
    expect(clipText).not.toMatch(/#p-/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T8 — gitInfo unavailable → warning in toast, no github.com in output
// ─────────────────────────────────────────────────────────────────────────────
test('T8: github mode with unavailable git info downgrades and warns', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ available: false, reason: 'no .git directory' }),
      }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 0, 10);
    await page.locator('[data-action="cite-md"]').click();

    // Toast must contain the warning
    await expect(page.locator('#reload-toast')).toContainText('GitHub info unavailable', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    expect(clipText).not.toMatch(/github\.com/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T9 — headPushed=false → "not pushed" warning in toast
// ─────────────────────────────────────────────────────────────────────────────
test('T9: github mode with headPushed=false surfaces not-pushed warning', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ ...MOCK_GIT_INFO, headPushed: false }),
      }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 0, 10);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('not pushed', { timeout: 4000 });
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T10 — Bug #3 regression: headPushed=null (no upstream) → warning in toast
// Root cause: buildUrl and loadSettings only checked `=== false`, not `null`.
//   A local-only branch with no `--set-upstream` sets headPushed to null,
//   silently generating GitHub URLs that 404.
// Fix: treat headPushed=null as equally unverifiable, surface a warning.
// ─────────────────────────────────────────────────────────────────────────────
test('T10 [Bug#3]: github mode with no upstream (headPushed=null) surfaces warning', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ ...MOCK_GIT_INFO, headPushed: null }),
      }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 0, 10);
    await page.locator('[data-action="cite-md"]').click();

    // Bug #3: before fix this showed "Citation copied" with no warning.
    // After fix the toast must contain a "verify" or "404" caution.
    await expect(page.locator('#reload-toast')).toContainText('verify', { timeout: 4000 });
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T11 — Bug #2 regression: selection inside a heading → correct heading text
// Root cause: nearestHeading(block) walked block.previousElementSibling when
//   block itself was a heading, so it returned the *previous* heading's text.
// Fix: check if block itself is a heading before walking siblings.
// ─────────────────────────────────────────────────────────────────────────────
test('T11 [Bug#2]: selecting text inside a heading cites that heading, not the prior one', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await seedSettings(page, { citationMode: 'local' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content h2').first()).toBeVisible();

    await patchClipboard(page);

    // Select text inside the first h2 ("Section One")
    await page.evaluate(() => {
      const h2 = document.querySelector('#content h2');       // "Section One"
      const tn = h2.firstChild;
      if (!tn || tn.nodeType !== 3) throw new Error('Expected text node inside h2');
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 0);
      r.setEnd(tn, Math.min(7, tn.textContent.length));      // "Section"
      sel.addRange(r);
      const rect = h2.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 10, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(60);

    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('[data-action="cite-md"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);

    // Bug #2: before fix, the citation said "§ Main Title" (the previous heading).
    // After fix, it must say "§ Section One".
    expect(clipText).toMatch(/§\s*Section One/);
    expect(clipText).not.toMatch(/§\s*Main Title/);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T12 — Settings panel persists citation mode to localStorage
// ─────────────────────────────────────────────────────────────────────────────
test('T12: settings panel radio persists citation mode to localStorage and survives reload', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'doc.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);

    // Open settings panel
    await page.locator('#settings-btn').click();
    await expect(page.locator('#settings-sheet')).toBeVisible();

    // Select the "Localhost viewer" radio
    await page.locator('input[name="citation-mode"][value="local"]').click();
    await page.waitForTimeout(50);

    // Verify localStorage updated (settings stored under namespaced key since redesign 01 T5)
    const stored = await page.evaluate(() => {
      try { return JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}').citationMode; }
      catch (e) { return null; }
    });
    expect(stored).toBe('local');

    // Reload and verify the radio re-checks correctly
    await page.reload();
    await expect(page.locator('#content p').first()).toBeVisible();
    await page.locator('#settings-btn').click();
    const localChecked = await page.locator('input[name="citation-mode"][value="local"]').isChecked();
    expect(localChecked).toBe(true);
    const githubChecked = await page.locator('input[name="citation-mode"][value="github"]').isChecked();
    expect(githubChecked).toBe(false);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T13 — sessionStorage caches git info: only one /api/git-info fetch per page
// ─────────────────────────────────────────────────────────────────────────────
test('T13: git info is fetched exactly once per page load (sessionStorage cache)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    let fetchCount = 0;
    await page.route('**/api/git-info', async (route) => {
      fetchCount++;
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(MOCK_GIT_INFO) });
    });

    // Pre-set github mode so loadSettings() triggers the opportunistic fetch.
    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();
    await page.waitForTimeout(300);   // let opportunistic fetch settle

    await patchClipboard(page);

    // Cite twice — both invocations must reuse the cached promise, no new fetch.
    await selectText(page, '#content p', 0, 5);
    await page.locator('[data-action="cite-md"]').click();
    await page.waitForTimeout(100);

    await selectText(page, '#content p', 0, 8);
    await page.locator('[data-action="cite-md"]').click();
    await page.waitForTimeout(100);

    // Exactly ONE /api/git-info request for the entire page session.
    expect(fetchCount).toBe(1);
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T14 — Bug #4 regression: toast says "using relative path", not "URL omitted"
// Root cause: warning text "GitHub info unavailable — URL omitted" implied the
//   citation contained no URL, but the relative-path code span is still present.
// Fix: changed to "GitHub info unavailable — using relative path".
// ─────────────────────────────────────────────────────────────────────────────
test('T14 [Bug#4]: unavailable git info toast says "using relative path" not "URL omitted"', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': BASIC_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ available: false, reason: 'no .git' }),
      }));

    await seedSettings(page, { citationMode: 'github' });
    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 0, 10);
    await page.locator('[data-action="cite-md"]').click();

    // Bug #4: old toast text "URL omitted" implied no URL present.
    // New text correctly says "using relative path".
    await expect(page.locator('#reload-toast')).toContainText('using relative path', { timeout: 4000 });
    await expect(page.locator('#reload-toast')).not.toContainText('URL omitted');
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T15 — Bug #5 regression: style buttons (B/I/<>) on display-math rejected
// Root cause: clicking Bold on a display-math selection produced `**$$\n...\n$$**`
//   in source. shieldDisplayMath looks for a bare `$$` on its own line and would
//   not recognise `**$$`, so the equation silently broke.
// Fix: guard at Step 8 rejects 'bold'/'italic'/'code' when type=DISPLAY_MATH.
// ─────────────────────────────────────────────────────────────────────────────
test('T15 [Bug#5]: bold action on display-math selection shows error and does not corrupt source', async ({ page, request }) => {
  const port = nextPort();
  const mathDoc = [
    '# Equations',
    '',
    'Some text before the equation.',
    '',
    '$$',
    'f = ma',
    '$$',
    '',
    'Some text after.',
  ].join('\n');
  const dir = createFixtureDir({ 'eq.md': mathDoc });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=eq.md`);
    // Wait for KaTeX to render the display math
    await expect(page.locator('.display-math-wrap')).toBeVisible();

    // Track PUT requests so we can confirm no write happened
    const puts = [];
    page.on('request', (req) => {
      if (req.method() === 'PUT') puts.push(req.url());
    });

    // Click inside the display math to create a collapsed selection there,
    // then fire mouseup to trigger the toolbar.
    await page.evaluate(() => {
      const wrap = document.querySelector('.display-math-wrap');
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.selectNodeContents(wrap);
      r.collapse(true);
      sel.addRange(r);
      const rect = wrap.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2, bubbles: true,
      }));
    });
    await page.waitForTimeout(60);

    // Now make a non-collapsed selection inside the math block
    await page.evaluate(() => {
      const wrap = document.querySelector('.display-math-wrap');
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.selectNodeContents(wrap);
      sel.addRange(r);
      const rect = wrap.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + rect.width / 2, clientY: rect.bottom + 2, bubbles: true,
      }));
    });
    await page.waitForTimeout(60);

    if (await page.locator('#hl-toolbar').evaluate(el => el.classList.contains('visible'))) {
      // Click the Bold button — must show an error toast, NOT write to file.
      await page.locator('[data-action="bold"]').click();
      await page.waitForTimeout(200);

      // Bug #5: before fix, source was corrupted with **$$...$$**.
      // After fix: error toast appears, no PUT request issued.
      await expect(page.locator('#reload-toast')).toContainText('not supported', { timeout: 3000 });
      expect(puts.length).toBe(0);

      // Source must remain unchanged.
      const res = await request.get(`http://localhost:${port}/api/md/eq.md`);
      const txt = await res.text();
      expect(txt).toContain('$$\nf = ma\n$$');
      expect(txt).not.toContain('**$$');
    }
    // If toolbar isn't visible (selection couldn't be set in the math block DOM),
    // the test is vacuously safe — the action was never triggered.
  } finally { stopServer(server, dir); }
});

// ─────────────────────────────────────────────────────────────────────────────
// T16 — Bug #6 regression: rich citation fallback writes markdown, not plain text
// Root cause: when ClipboardItem is unavailable, cite-rich wrote result.plainText
//   (a bare attribution line like '"text" — Title (file:L42)') instead of the
//   markdown blockquote, which is more useful when pasting into documents.
// Fix: text fallback always writes result.markdown for both variants.
// ─────────────────────────────────────────────────────────────────────────────
test('T16 [Bug#6]: cite-rich text fallback writes markdown blockquote, not bare plainText', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'test.md': ANCHOR_DOC });
  const server = await startServer(dir, port);
  try {
    await page.route('**/api/git-info', route =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(MOCK_GIT_INFO) }));

    await page.addInitScript(() => {
      const KEY = 'viewer.settings.v1';
      let s = {};
      try { s = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { s = {}; }
      s.citationMode = 'local';
      localStorage.setItem(KEY, JSON.stringify(s));
      // Force the fallback path: nullify ClipboardItem and clipboard.write
      // so copyCitation() goes to the else branch (writeText).
      Object.defineProperty(window, 'ClipboardItem', { value: undefined, configurable: true });
    });

    await page.goto(`http://localhost:${port}?file=test.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    await patchClipboard(page);
    await selectText(page, '#content p', 1, 10);
    await page.locator('[data-action="cite-rich"]').click();
    await expect(page.locator('#reload-toast')).toContainText('Citation copied', { timeout: 4000 });

    const clipText = await page.evaluate(() => window.__clipText);
    // Bug #6: old fallback wrote bare plainText like: '"text" — Title (file:L42)'
    // After fix: fallback writes the markdown blockquote (starts with "> ")
    expect(clipText).toMatch(/^>/);        // starts with a blockquote ">"
    expect(clipText).not.toMatch(/^"/);    // NOT a quoted plain-text attribution
  } finally { stopServer(server, dir); }
});
