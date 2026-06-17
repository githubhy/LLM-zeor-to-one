// @ts-check
// Tests for the expanded highlight palette, recolor flow, and Highlights tab.
// Targets the changes from plans/viewer-highlight-colors.md.
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 7500;
function nextPort() { return portCounter++; }

// Highlights-tab and scope-toggle flows drive the docked sidebar — pin
// classic layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

const ALL_COLORS = ['yellow', 'green', 'red', 'blue', 'orange', 'purple', 'teal', 'pink'];

// ─────────────────────────────────────────────────────────────────────────────
// 1) Eight CSS classes render the eight highlight colors
// ─────────────────────────────────────────────────────────────────────────────
test('all 8 highlight colors render with distinct backgrounds', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'colors.md':
      '# Colors\n\n' +
      ALL_COLORS.map(c => `==${c}: text-${c}==`).join('\n\n') + '\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=colors.md`);
    await expect(page.locator('#content h1')).toHaveText('Colors');

    const seenColors = new Set();
    for (const c of ALL_COLORS) {
      const mark = page.locator(`mark.hl-${c}`);
      await expect(mark).toHaveCount(1);
      await expect(mark).toHaveText(`text-${c}`);
      const bg = await mark.evaluate(el => getComputedStyle(el).backgroundColor);
      expect(bg).not.toBe('rgba(0, 0, 0, 0)');
      seenColors.add(bg);
    }
    // Each color should be visually distinct
    expect(seenColors.size).toBe(ALL_COLORS.length);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 2) Toolbar exposes 8 swatches for new selection
// ─────────────────────────────────────────────────────────────────────────────
test('toolbar shows 8 swatches when text is selected', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nThis is some plain selectable body text for the test.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('#content p')).toBeVisible();

    // Programmatically select text and dispatch mouseup so the toolbar opens
    await page.evaluate(() => {
      const p = document.querySelector('#content p');
      const tn = p.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 5);
      r.setEnd(tn, 12);
      sel.addRange(r);
      const rect = p.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 20, clientY: rect.bottom + 2, bubbles: true,
      }));
    });

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    const swatchCount = await page.locator('#hl-toolbar .hl-swatch').count();
    expect(swatchCount).toBe(8);

    for (const c of ALL_COLORS) {
      await expect(page.locator(`#hl-toolbar .hl-swatch[data-action="${c}"]`)).toHaveCount(1);
    }
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 3) Apply a new color (orange) to a fresh selection — round-trips to source
// ─────────────────────────────────────────────────────────────────────────────
test('applying orange writes ==orange: text== to source', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'apply.md': '# Apply\n\nThe quick brown fox jumps over the lazy dog.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=apply.md`);
    await expect(page.locator('#content p')).toBeVisible();

    // Select "brown" (chars 10..15 in "The quick brown fox jumps over the lazy dog.")
    await page.evaluate(() => {
      const p = document.querySelector('#content p');
      const tn = p.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 10);
      r.setEnd(tn, 15);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(150);

    const res = await request.get(`http://localhost:${port}/api/md/apply.md`);
    const txt = await res.text();
    expect(txt).toContain('==orange: brown==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Ctrl+Z undo reverts the most recent inline highlight.
// Regression guard for the bug where pushUndo stored the pre-write revision
// instead of the post-write revision, causing every undo to hit 409.
// ─────────────────────────────────────────────────────────────────────────────
test('Ctrl+Z undoes the most recent inline highlight write', async ({ page, request }) => {
  const port = nextPort();
  const original = '# Undo\n\nThe quick brown fox jumps over the lazy dog.\n';
  const dir = createFixtureDir({ 'undo.md': original });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=undo.md`);
    await expect(page.locator('#content p')).toBeVisible();

    // Apply an orange highlight to "brown" (chars 10..15).
    await page.evaluate(() => {
      const p = document.querySelector('#content p');
      const tn = p.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 10);
      r.setEnd(tn, 15);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(150);

    // Sanity: the write landed on disk.
    let res = await request.get(`http://localhost:${port}/api/md/undo.md`);
    expect(await res.text()).toContain('==orange: brown==');

    // Now Ctrl+z. Must revert the source file on disk, not just the DOM.
    // Lowercase 'z' matters: Playwright treats 'Control+Z' as Ctrl+Shift+z
    // (Z = shifted z), which fails the handler's `!e.shiftKey` guard.
    await page.keyboard.press('Control+z');
    await page.waitForTimeout(300);

    res = await request.get(`http://localhost:${port}/api/md/undo.md`);
    const reverted = await res.text();
    expect(reverted).toBe(original);
    expect(reverted).not.toContain('==orange:');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 4) Recolor: clicking inside an existing mark opens recolor toolbar
//    with the active swatch ringed; swapping color rewrites source.
// ─────────────────────────────────────────────────────────────────────────────
test('recolor: click existing green mark, switch to purple', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'recolor.md': '# Recolor\n\nLook here ==green: target word== and elsewhere.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=recolor.md`);
    await expect(page.locator('mark.hl-green')).toHaveText('target word');

    // Single click inside the green mark — collapsed selection inside <mark>
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
    await page.waitForTimeout(50);

    // Recolor mode must be active (style buttons hidden, swatches visible)
    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    await expect(page.locator('#hl-toolbar')).not.toHaveClass(/clear-only/);
    // Active ring on green swatch
    await expect(page.locator('#hl-toolbar .hl-swatch[data-action="green"].active'))
      .toHaveCount(1);

    // Click purple
    await page.locator('#hl-toolbar .hl-swatch[data-action="purple"]').click();
    await page.waitForTimeout(150);

    const res = await request.get(`http://localhost:${port}/api/md/recolor.md`);
    const txt = await res.text();
    expect(txt).toContain('==purple: target word==');
    expect(txt).not.toContain('==green: target word==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 5) Same-color swatch click is a no-op (no write)
// ─────────────────────────────────────────────────────────────────────────────
test('clicking the active swatch does not rewrite the file', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'noop.md': '# Noop\n\nA line with ==red: warning text== inside.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=noop.md`);
    await expect(page.locator('mark.hl-red')).toHaveText('warning text');

    // Track PUTs
    const puts = [];
    page.on('request', (req) => {
      if (req.method() === 'PUT' && req.url().includes('/api/md/')) puts.push(req.url());
    });

    // Click inside the red mark
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-red');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 2); r.setEnd(tn, 2);
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 4, clientY: rect.top + 4, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    await page.locator('#hl-toolbar .hl-swatch[data-action="red"]').click();
    await page.waitForTimeout(200);

    expect(puts.length).toBe(0);

    // File still has the original red highlight
    const res = await request.get(`http://localhost:${port}/api/md/noop.md`);
    const txt = await res.text();
    expect(txt).toContain('==red: warning text==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 6) hideToolbar cleanup: stale .recolor-only / .active are cleared
// ─────────────────────────────────────────────────────────────────────────────
test('hideToolbar clears recolor-only and active swatch ring', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'clean.md': '# Clean\n\nA ==blue: blue thing== then more text after it.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=clean.md`);
    await expect(page.locator('mark.hl-blue')).toHaveText('blue thing');

    // Open recolor toolbar on the blue mark
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-blue');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 1); r.setEnd(tn, 1);
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 4, clientY: rect.top + 4, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    await expect(page.locator('#hl-toolbar .hl-swatch.active')).toHaveCount(1);

    // Press Escape to hide
    await page.keyboard.press('Escape');
    await page.waitForTimeout(50);

    const cls = await page.locator('#hl-toolbar').getAttribute('class') || '';
    expect(cls).not.toContain('recolor-only');
    expect(cls).not.toContain('clear-only');
    expect(cls).not.toContain('visible');
    await expect(page.locator('#hl-toolbar .hl-swatch.active')).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 7) Highlights tab: aggregates hits across files, filter chips work,
//    entry click navigates to the file.
// ─────────────────────────────────────────────────────────────────────────────
test('Highlights tab aggregates, filters, and navigates', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'a.md': '# A\n\n==yellow: yhit== and ==orange: ohit==.\n',
    'b.md': '# B\n\n==teal: thit== definition here.\n',
    'c.md': '# C\n\nNothing colored here.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');

    // Switch via shortcut
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();

    // Filter chips: 8 chips, all on by default
    await expect(page.locator('#hl-filter-bar .hl-chip')).toHaveCount(8);
    await expect(page.locator('#hl-filter-bar .hl-chip.on')).toHaveCount(8);

    // Three entries (yhit, ohit, thit) — sorted file-then-line
    const entryTexts = await page.locator('.hl-entry .hl-entry-text').allInnerTexts();
    expect(entryTexts).toEqual(['yhit', 'ohit', 'thit']);
    const fileLabels = await page.locator('.hl-entry .hl-entry-file').allInnerTexts();
    expect(fileLabels[0]).toContain('a.md');
    expect(fileLabels[2]).toContain('b.md');

    // Toggle the "yellow" chip OFF — yhit should disappear
    await page.locator('#hl-filter-bar .hl-chip[data-color="yellow"]').click();
    const remaining = await page.locator('.hl-entry .hl-entry-text').allInnerTexts();
    expect(remaining).toEqual(['ohit', 'thit']);

    // Toggle ALL chips off → empty state
    for (const c of ALL_COLORS) {
      const chip = page.locator(`#hl-filter-bar .hl-chip[data-color="${c}"]`);
      const cls = await chip.getAttribute('class') || '';
      if (cls.includes('on')) await chip.click();
    }
    await expect(page.locator('.hl-empty')).toBeVisible();

    // Re-enable teal, then click the entry to navigate to b.md
    await page.locator('#hl-filter-bar .hl-chip[data-color="teal"]').click();
    await page.locator('.hl-entry').first().click();
    await page.waitForTimeout(150);
    expect(page.url()).toContain('file=b.md');
    // Sidebar still on Highlights tab
    await expect(page.locator('.sidebar-tab.active')).toHaveAttribute('data-tab', 'highlights');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 8) Live refresh: adding a highlight while Highlights tab is open
//    rebuilds the entry list without re-clicking the tab.
// ─────────────────────────────────────────────────────────────────────────────
test('Highlights tab live-refreshes after a local edit', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'live.md': '# Live\n\nNo highlights yet.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=live.md`);
    await expect(page.locator('#content h1')).toHaveText('Live');

    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();
    await expect(page.locator('.hl-empty')).toBeVisible();

    // Simulate a local edit by writing a new source and calling applyLocalSourceUpdate
    await page.evaluate(() => {
      // @ts-ignore
      applyLocalSourceUpdate('live.md', '# Live\n\nNow ==pink: a note== exists.\n');
    });
    await page.waitForTimeout(100);

    await expect(page.locator('.hl-entry')).toHaveCount(1);
    await expect(page.locator('.hl-entry .hl-entry-text')).toHaveText('a note');
  } finally {
    stopServer(server, dir);
  }
});

test('table-cell selection persists as sidecar annotation', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'table.md': '# Table\n\n| c1 | c2 |\n|---|---|\n| alpha | beta |\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=table.md`);
    await expect(page.locator('#content table')).toBeVisible();

    await page.evaluate(() => {
      const td = document.querySelector('#content td');
      const tn = td && td.firstChild;
      const sel = window.getSelection();
      if (!tn || !sel) return;
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 0);
      r.setEnd(tn, String(tn.textContent || '').length);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: 100, clientY: 100, bubbles: true }));
    });
    await page.waitForTimeout(80);
    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(120);

    const annRes = await request.get(`http://localhost:${port}/api/highlights/table.md`);
    expect(annRes.ok()).toBe(true);
    const ann = await annRes.json();
    expect(Array.isArray(ann.highlights)).toBe(true);
    expect(ann.highlights.length).toBe(1);
    expect(ann.highlights[0].backend).toBe('sidecar');
    expect(ann.highlights[0].color).toBe('orange');

    const srcRes = await request.get(`http://localhost:${port}/api/md/table.md`);
    const src = await srcRes.text();
    expect(src).not.toContain('==orange:');
  } finally {
    stopServer(server, dir);
  }
});

test('cross-block selection persists as sidecar annotation', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'cross.md': '# Cross\n\nFirst paragraph target.\n\nSecond paragraph target.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=cross.md`);
    await expect(page.locator('#content p')).toHaveCount(2);

    await page.evaluate(() => {
      const paras = document.querySelectorAll('#content p');
      const firstNode = paras[0] && paras[0].firstChild;
      const secondNode = paras[1] && paras[1].firstChild;
      const sel = window.getSelection();
      if (!firstNode || !secondNode || !sel) return;
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(firstNode, 0);
      r.setEnd(secondNode, String(secondNode.textContent || '').length);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', { clientX: 120, clientY: 120, bubbles: true }));
    });
    await page.waitForTimeout(80);
    await page.locator('#hl-toolbar .hl-swatch[data-action="teal"]').click();
    await page.waitForTimeout(120);

    const annRes = await request.get(`http://localhost:${port}/api/highlights/cross.md`);
    expect(annRes.ok()).toBe(true);
    const ann = await annRes.json();
    expect(ann.highlights.length).toBe(1);
    const seg = ann.highlights[0].segments[0];
    expect(seg.lineEnd).toBeGreaterThanOrEqual(seg.lineStart);
    expect(ann.highlights[0].backend).toBe('sidecar');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 9) Re-highlighting an orange word does not nest into ==orange: ==orange: ====
//    Tests the HL_COLOR_ALT centralization (Step 6 strip with new colors).
// ─────────────────────────────────────────────────────────────────────────────
test('re-applying the same new color does not nest markers', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'nest.md': '# Nest\n\nAlpha ==orange: foo== beta gamma delta.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=nest.md`);
    await expect(page.locator('mark.hl-orange')).toHaveText('foo');

    // Select "foo" inside the existing orange mark (drag-select)
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-orange');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 0); r.setEnd(tn, 3);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(150);

    const res = await request.get(`http://localhost:${port}/api/md/nest.md`);
    const txt = await res.text();
    expect(txt).not.toMatch(/==orange:\s*==orange:/);
    // Should still contain a single orange wrapping foo
    expect((txt.match(/==orange: foo==/g) || []).length).toBe(1);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 10) Regression: selection spanning multiple inline math formulas that also
//     crosses a markdown soft line break must not fail with "Could not locate
//     selection start in source". This is the tracking-loops.md §8.1.1 bug:
//     "given the z-transform\n$F(z)$ of an unknown causal signal $f(n)$".
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_SPANNING_MATH across a soft line break highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'span.md':
      '# Span\n\n' +
      'Suppose we are given the z-transform\n' +
      '$F(z)$ of an unknown causal signal $f(n)$ and more prose here.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=span.md`);
    await expect(page.locator('#content p')).toBeVisible();
    // Ensure KaTeX has rendered two inline formulas
    await expect(page.locator('#content p .katex').first()).toBeVisible();
    const katexCount = await page.locator('#content p .katex:not(.katex .katex)').count();
    expect(katexCount).toBeGreaterThanOrEqual(2);

    // Capture browser toasts to surface highlight failures as test failures
    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const orig = window.showToast;
      // showToast may not be on window — shim it via the element instead
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Build a selection that starts at "given" (inside the first text node,
    // before the soft line break + first katex) and ends after "prose." in
    // the trailing text node. This exercises PLAIN_SPANNING_MATH where both
    // plainHead and plainTail live in DOM text nodes that contain literal \n.
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      // Find the text nodes that contain "given" and "prose." — walk only
      // the direct-child text nodes of <p>, skipping <eq>/<span.katex> subtrees.
      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const idx = data.indexOf('given');
        if (idx !== -1 && !startText) {
          startText = tn; startOffset = idx;
        }
        const eIdx = data.indexOf('here.');
        if (eIdx !== -1) {
          endText = tn; endOffset = eIdx + 'here.'.length;
        }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);

      // Surface the raw plainHead/plainTail for debugging
      const firstKatex = p.querySelector('.katex:not(.katex .katex)');
      const headR = document.createRange();
      headR.setStart(startText, startOffset);
      headR.setEndBefore(firstKatex);
      const plainHead = headR.toString();

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString(), plainHead };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('given the z-transform');
    expect(sel.selText).toContain('here.');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="yellow"]').click();
    await page.waitForTimeout(200);

    // No failure toasts
    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();

    // File should now contain a yellow mark spanning "given ... here."
    const res = await request.get(`http://localhost:${port}/api/md/span.md`);
    const txt = await res.text();
    expect(txt).toMatch(/==yellow: given the z-transform[\s\S]*here\.==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 11) Regression: PLAIN_TEXT selection that crosses an italic `*word*` span.
//     The DOM-rendered needle has no asterisks, so a literal search in the
//     raw source misses; the stripped-map fallback must recover the match.
//     Mirrors the tracking-loops.md §8.1.1 bug where "…first differences
//     *is* the asymptotic value." could not be highlighted.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT selection crossing an italic span highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'italic.md':
      '# Italic\n\n' +
      'This is the time-domain heart of the FVT: the bare infinite sum of first differences *is* the asymptotic value. The remainder follows.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=italic.md`);
    await expect(page.locator('#content em')).toHaveText('is');

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Selection: from "the time-domain" through "asymptotic value."
    // (crosses the <em>is</em> span in the middle)
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };
      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const idx = data.indexOf('the time-domain');
        if (idx !== -1 && !startText) {
          startText = tn; startOffset = idx;
        }
        const eIdx = data.indexOf('asymptotic value.');
        if (eIdx !== -1) {
          endText = tn; endOffset = eIdx + 'asymptotic value.'.length;
        }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('the time-domain');
    expect(sel.selText).toContain('differences is the');
    expect(sel.selText).toContain('asymptotic value.');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="yellow"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();

    const res = await request.get(`http://localhost:${port}/api/md/italic.md`);
    const txt = await res.text();
    // The asterisks around `*is*` must still be present inside the highlight
    // (the stripped-map fallback sweeps them into the highlight span so the
    // emphasis stays balanced).
    expect(txt).toContain('==yellow: the time-domain heart of the FVT: the bare infinite sum of first differences *is* the asymptotic value.==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 12) Regression: PLAIN_TEXT selection crossing a **bold** span.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT selection crossing a bold span highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'bold.md':
      '# Bold\n\n' +
      'Intro prose with **an important phrase** and trailing text afterwards.\n',
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=bold.md`);
    await expect(page.locator('#content strong')).toHaveText('an important phrase');

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };
      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const idx = data.indexOf('prose with');
        if (idx !== -1 && !startText) {
          startText = tn; startOffset = idx;
        }
        const eIdx = data.indexOf('trailing text');
        if (eIdx !== -1) {
          endText = tn; endOffset = eIdx + 'trailing text'.length;
        }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="yellow"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();

    const res = await request.get(`http://localhost:${port}/api/md/bold.md`);
    const txt = await res.text();
    expect(txt).toContain('==yellow: prose with **an important phrase** and trailing text==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 13) Regression: PLAIN_TEXT selection crossing an inline `code` span.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT selection crossing an inline code span highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'code.md':
      '# Code\n\n' +
      'Before the call `fn_name()` continues afterwards in prose.\n',
  });
  const server = await startServer(dir, port);

  // Surface browser page errors as test failures
  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=code.md`);
    await expect(page.locator('#content code')).toHaveText('fn_name()');

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };
      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const idx = data.indexOf('Before the call');
        if (idx !== -1 && !startText) {
          startText = tn; startOffset = idx;
        }
        const eIdx = data.indexOf('continues');
        if (eIdx !== -1) {
          endText = tn; endOffset = eIdx + 'continues'.length;
        }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/code.md`);
    const txt = await res.text();
    expect(txt).toContain('==green: Before the call `fn_name()` continues==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 14) Regression: PLAIN_TEXT selection that starts INSIDE a `**bold**` span
//     (partial overlap) and ends past an `*italic*` span, inside a list-item
//     paragraph that wraps across 3 source lines with 2-space indent. This
//     reproduces the user's report on tracking-loops.md §FVT.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT selection partially overlapping a bold span (list-item, soft-wrap) highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'partial.md':
      '# Partial bold\n\n' +
      '- Item:\n\n' +
      '  **Why the pole condition cannot be dropped.**  The condition is a\n' +
      '  *certificate of validity*, not a technicality.  Two examples illustrate\n' +
      '  what goes wrong if it fails.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=partial.md`);
    await expect(page.locator('#content strong')).toContainText('cannot be dropped');

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    const sel = await page.evaluate(() => {
      // The list-item paragraph; pick the <p> that contains a <strong>.
      const ps = Array.from(document.querySelectorAll('#content p'));
      const p = ps.find(el => el.querySelector('strong'));
      if (!p) return { err: 'paragraph not found' };
      const strong = p.querySelector('strong');
      if (!strong || !strong.firstChild || strong.firstChild.nodeType !== 3) {
        return { err: 'no strong text node' };
      }
      const strongText = /** @type {Text} */ (strong.firstChild);
      const startInStrong = strongText.nodeValue.indexOf('cannot');
      if (startInStrong < 0) return { err: 'cannot not in strong' };

      // Walk forward through the paragraph's descendants to find a text
      // node containing 'technicality'.
      const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      while (walker.nextNode()) {
        const t = /** @type {Text} */ (walker.currentNode);
        const idx = (t.nodeValue || '').indexOf('technicality');
        if (idx !== -1) { endText = t; endOffset = idx + 'technicality'.length; break; }
      }
      if (!endText) return { err: 'technicality not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(strongText, startInStrong);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/partial.md`);
    const txt = await res.text();
    // Selection start is inside `**...**` and end is plain text after the
    // italic span. The fix expands the selection to begin BEFORE the bold
    // open marker so the wrap encloses the whole bold span. The italic
    // span is fully contained, so its source markers stay intact.
    expect(txt).toContain('==green: **Why the pole condition cannot be dropped.**');
    expect(txt).toContain('*certificate of validity*, not a technicality==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 15) Regression: PLAIN_TEXT selection across a soft line break inside a
//     list-item paragraph (continuation line has 2-space indent). The
//     normalize step must collapse the `\n` + indent run to a single space
//     so the DOM-derived needle matches the source haystack.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT selection across a soft break with list-item indent highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'wrap.md':
      '# Wrap\n\n' +
      '- Item:\n\n' +
      '  Some leading prose followed by a phrase that wraps at the\n' +
      '  end of the source line and continues on the next.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=wrap.md`);
    await expect(page.locator('#content p').first()).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    const sel = await page.evaluate(() => {
      const ps = Array.from(document.querySelectorAll('#content p'));
      const p = ps.find(el => (el.textContent || '').includes('Some leading prose'));
      if (!p) return { err: 'paragraph not found' };
      const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      /** @type {Text | null} */ let startText = null; let startOffset = 0;
      /** @type {Text | null} */ let endText   = null; let endOffset   = 0;
      while (walker.nextNode()) {
        const t = /** @type {Text} */ (walker.currentNode);
        const data = t.nodeValue || '';
        const sIdx = data.indexOf('phrase that wraps');
        if (sIdx !== -1 && !startText) { startText = t; startOffset = sIdx; }
        const eIdx = data.indexOf('continues on');
        if (eIdx !== -1) { endText = t; endOffset = eIdx + 'continues on'.length; }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };
      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/wrap.md`);
    const txt = await res.text();
    // The wrap point becomes part of the highlight; the single-space
    // normalization must let the DOM-derived needle match the indented
    // continuation line in the source.
    expect(txt).toMatch(/==green: phrase that wraps at the\n  end of the source line and continues on==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 16) Regression: clicking the N-th display-math equation must highlight the
//     N-th equation in source. After bug 2026-04-30-01 fix, `shieldDisplayMath`
//     recognizes single-line `$$...$$` as a display block too — but only at the
//     top level, not inside blockquotes. Step 5A must use the same line-based
//     scan or its index will drift, highlighting a different equation than the
//     one the user clicked.
// ─────────────────────────────────────────────────────────────────────────────
test('DISPLAY_MATH highlight lands on the clicked equation when single-line $$..$$ precedes it', async ({ page, request }) => {
  const port = nextPort();
  // Layout (post-fix shielding):
  //   Block A — multi-line `$$\n a \n$$`     (data-math-block index 0)
  //   Inline  — `> $$x = 1$$`                 (NOT shielded — blockquote prefix)
  //   Single  — `  $$y = 2$$`                 (data-math-block index 1 — top-level after trim)
  //   Block B — multi-line `$$\n b \n$$`     (data-math-block index 2)
  //   Block C — multi-line `$$\n c \n$$`     (data-math-block index 3)
  // Naive `indexOf('$$')` counting would assign Block C the wrong source
  // index, so clicking Block C would highlight a different block.
  const dir = createFixtureDir({
    'eqns.md':
      '# Eqns\n\n' +
      'Block A:\n\n' +
      '$$\n' +
      'a = 1\n' +
      '$$\n\n' +
      '> $$x = 1$$\n\n' +
      '  $$y = 2$$\n\n' +
      'Block B:\n\n' +
      '$$\n' +
      'b = 2\n' +
      '$$\n\n' +
      'Block C:\n\n' +
      '$$\n' +
      'c = 3\n' +
      '$$\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=eqns.md`);
    // 3 multi-line + 1 top-level single-line ($$y=2$$ after trim) = 4
    // ($$x=1$$ inside `>` blockquote is not shielded.)
    await expect(page.locator('#content [data-math-block]')).toHaveCount(4);

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Click on Block C (data-math-block="3") — its index in the rendered DOM
    // after the single-line $$y=2$$ shielding takes index 1.
    const blockC = page.locator('#content [data-math-block="3"]');
    await expect(blockC).toBeVisible();
    // Make a selection inside Block C so the toolbar opens via mouseup.
    const sel = await page.evaluate(() => {
      const el = document.querySelector('#content [data-math-block="3"]');
      if (!el) return { err: 'block C not found' };
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const t = tw.nextNode();
      if (!t) return { err: 'no text in block C' };
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

    const res = await request.get(`http://localhost:${port}/api/md/eqns.md`);
    const txt = await res.text();
    // Block C must be wrapped, NOT block A or B.
    expect(txt).toContain('==green: $$\nc = 3\n$$==');
    expect(txt).not.toContain('==green: $$\na = 1\n$$==');
    expect(txt).not.toContain('==green: $$\nb = 2\n$$==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 17) Regression: clicking the middle display block when single-line
//     `$$...$$` blocks exist BOTH before and after it. Confirms the index
//     stays correct in either direction of drift.
// ─────────────────────────────────────────────────────────────────────────────
test('DISPLAY_MATH highlight lands on the clicked equation amid mixed inline+block math', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'mixed.md':
      '# Mixed\n\n' +
      '$$\n' +
      'first = 1\n' +
      '$$\n\n' +
      '$$x_1 = 1$$\n\n' +
      '$$\n' +
      'middle = 2\n' +
      '$$\n\n' +
      '$$x_2 = 2$$\n\n' +
      '$$\n' +
      'last = 3\n' +
      '$$\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=mixed.md`);
    // 3 multi-line + 2 single-line top-level = 5 data-math-block elements
    // (after bug 2026-04-30-01 fix).
    await expect(page.locator('#content [data-math-block]')).toHaveCount(5);

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Click the MIDDLE multi-line block (data-math-block="2"; $$x_1$$ takes
    // index 1 between first and middle).
    const sel = await page.evaluate(() => {
      const el = document.querySelector('#content [data-math-block="2"]');
      if (!el) return { err: 'middle block not found' };
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const t = tw.nextNode();
      if (!t) return { err: 'no text' };
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
    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(200);

    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/mixed.md`);
    const txt = await res.text();
    expect(txt).toContain('==orange: $$\nmiddle = 2\n$$==');
    expect(txt).not.toContain('==orange: $$\nfirst = 1\n$$==');
    expect(txt).not.toContain('==orange: $$\nlast = 3\n$$==');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 18) Regression (Bug E): browser refresh restores the exact scroll position
//     on a math-heavy page. The original code used a single rAF + scrollTo,
//     which clamps Y when late-loading KaTeX fonts grow docHeight after the
//     initial paint. The fix (scrollToStable + document.fonts.ready follow-up)
//     re-asserts scroll until the layout settles.
// ─────────────────────────────────────────────────────────────────────────────
test('refresh restores the exact scroll position on a math-heavy page', async ({ page }) => {
  const port = nextPort();
  // Build a tall page with many display-math blocks so docHeight is large
  // and a saved Y that's plausibly past a short pre-font-load docHeight.
  let md = '# Scroll Restore\n\n';
  for (let i = 0; i < 60; i++) {
    md += `Paragraph ${i}: lorem ipsum dolor sit amet consectetur adipiscing elit.\n\n`;
    md += '$$\n';
    md += `E_{${i}} = \\sum_{k=0}^{${i}} \\alpha_k \\cdot \\beta_k^{${i}} + \\int_0^{${i}} f(x)\\,dx\n`;
    md += '$$\n\n';
  }
  const dir = createFixtureDir({ 'tall.md': md });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=tall.md`);
    await expect(page.locator('#content h1')).toHaveText('Scroll Restore');
    // Ensure all display-math blocks are present.
    await expect(page.locator('#content [data-math-block]')).toHaveCount(60);
    // Wait for KaTeX fonts so the initial docHeight is stable.
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(200);

    // Pick a scroll target that's definitely past the initial viewport but
    // still well within docHeight.
    const targetY = 2500;
    await page.evaluate((y) => window.scrollTo({ top: y, left: 0, behavior: 'instant' }), targetY);
    await page.waitForTimeout(50);
    const scrolledY = await page.evaluate(() => Math.round(window.scrollY));
    expect(scrolledY).toBeGreaterThan(2400);

    // Reload. The beforeunload handler saves to sessionStorage; init() must
    // restore the position even as KaTeX fonts shift layout post-paint.
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Scroll Restore');
    await expect(page.locator('#content [data-math-block]')).toHaveCount(60);

    // Wait for fonts.ready + the scrollToStable window (3s) + a small margin
    // so every layout shift settles.
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(3200);

    const restoredY = await page.evaluate(() => Math.round(window.scrollY));
    // Allow small tolerance for sub-pixel rounding on some platforms.
    expect(Math.abs(restoredY - scrolledY)).toBeLessThanOrEqual(2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 19) Regression (Bug E): refresh restore still works when the saved Y is
//     close to the bottom, where font-load-driven docHeight shifts are most
//     likely to cause clamping.
// ─────────────────────────────────────────────────────────────────────────────
test('refresh restores scroll near the bottom of a math-heavy page', async ({ page }) => {
  const port = nextPort();
  let md = '# Bottom Restore\n\n';
  for (let i = 0; i < 40; i++) {
    md += `Para ${i}: text text text text text text text text text text.\n\n`;
    md += '$$\n';
    md += `g_{${i}}(x) = \\frac{1}{\\sqrt{2\\pi}} e^{-x^2/${i + 1}}\n`;
    md += '$$\n\n';
  }
  const dir = createFixtureDir({ 'bottom.md': md });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}?file=bottom.md`);
    await expect(page.locator('#content h1')).toHaveText('Bottom Restore');
    await expect(page.locator('#content [data-math-block]')).toHaveCount(40);
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(200);

    // Scroll to a point in the lower half of the document.
    const [targetY, docH, vpH] = await page.evaluate(() => {
      const dh = document.documentElement.scrollHeight;
      const vh = window.innerHeight;
      const y = Math.max(0, dh - vh - 400);
      window.scrollTo({ top: y, left: 0, behavior: 'instant' });
      return [y, dh, vh];
    });
    await page.waitForTimeout(50);
    expect(targetY).toBeGreaterThan(1000);

    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Bottom Restore');
    await expect(page.locator('#content [data-math-block]')).toHaveCount(40);
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(3200);

    const restoredY = await page.evaluate(() => Math.round(window.scrollY));
    expect(Math.abs(restoredY - targetY)).toBeLessThanOrEqual(2);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 20) Regression (Bug F): PLAIN_SPANNING_MATH selection whose plainHead
//     contains an inline markdown link `[(9)](#eq-9)` and an HTML comment
//     `<!-- ref:... -->` immediately before it. The DOM renders "(9)" as
//     visible link text and drops the comment, so a raw-source `indexOf`
//     of the plainHead string never matched. stripInlineMarkersWithMap
//     must unwrap the link and strip the comment so the head locates
//     correctly. Mirrors the tracking-loops.md §8.1.1 "Effect of feedback
//     delay" paragraph.
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_SPANNING_MATH head containing a ref link and HTML comment highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'refspan.md':
      '# Refspan\n\n' +
      '**Effect of feedback delay $d > 1$.**  The recurrence <!-- ref:8.1.1-S1 -->[(9)](#eq-9) assumes\n' +
      '$d = 1$: the correction at sample $n$ is based on $f_e(n)$ with only the\n' +
      'inherent one-sample integrator delay.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=refspan.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await expect(page.locator('#content p .katex').first()).toBeVisible();
    const katexCount = await page.locator('#content p .katex:not(.katex .katex)').count();
    expect(katexCount).toBeGreaterThanOrEqual(4);

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Build a selection that starts at "The recurrence" and ends after
    // "sample n" (inclusive of the `$n$` math element). The start is in a
    // text node; the end is inside the `$n$` <eq> so the path is
    // PLAIN_SPANNING_MATH with a plainHead containing "The recurrence (9) assumes ".
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      // Find the text node that has "The recurrence "
      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const idx = (tn.nodeValue || '').indexOf('The recurrence');
        if (idx !== -1) { startText = tn; startOffset = idx; break; }
      }
      if (!startText) return { err: 'start text not found' };

      // End inside the `$n$` inline math (the third katex element).
      const katexEls = p.querySelectorAll('.katex:not(.katex .katex)');
      if (katexEls.length < 3) return { err: 'not enough katex' };
      const nMath = katexEls[2]; // $n$
      const tw = document.createTreeWalker(nMath, NodeFilter.SHOW_TEXT);
      const nText = tw.nextNode();
      if (!nText) return { err: 'no text in n' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(nText, (nText.nodeValue || '').length);
      s.addRange(r);

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { ok: true, selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('The recurrence');
    expect(sel.selText).toContain('sample');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="blue"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    // The rewritten source should contain a blue highlight starting at
    // "The recurrence" and ending at the closing `$` of `$n$`. The ref
    // comment and link syntax must be preserved verbatim inside the wrap.
    const res = await request.get(`http://localhost:${port}/api/md/refspan.md`);
    const txt = await res.text();
    expect(txt).toMatch(/==blue: The recurrence <!-- ref:8\.1\.1-S1 -->\[\(9\)\]\(#eq-9\) assumes[\s\S]*?sample \$n\$==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 21) Regression (Bug F): MIXED_TEXT_MATH — selection starts in plain text
//     whose prefix contains a markdown link and ends inside an inline math
//     element. Same normalization fix as test 20 but via the
//     MIXED_TEXT_MATH branch rather than PLAIN_SPANNING_MATH.
// ─────────────────────────────────────────────────────────────────────────────
test('MIXED_TEXT_MATH with a ref link in the plainHead highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'mixlink.md':
      '# MixLink\n\n' +
      'As shown in <!-- ref:sec-2 -->[Section 2](sec2.md) the rate equals $r = 1/2$ in this mode.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=mixlink.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await expect(page.locator('#content p .katex').first()).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Start selection at "As shown" (text node), end inside `$r = 1/2$` math.
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const idx = (tn.nodeValue || '').indexOf('As shown');
        if (idx !== -1) { startText = tn; startOffset = idx; break; }
      }
      if (!startText) return { err: 'start text not found' };

      const katexEls = p.querySelectorAll('.katex:not(.katex .katex)');
      if (katexEls.length < 1) return { err: 'no katex' };
      const rMath = katexEls[0];
      const tw = document.createTreeWalker(rMath, NodeFilter.SHOW_TEXT);
      const rText = tw.nextNode();
      if (!rText) return { err: 'no text in r' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(rText, (rText.nodeValue || '').length);
      s.addRange(r);

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { ok: true, selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('As shown');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/mixlink.md`);
    const txt = await res.text();
    expect(txt).toMatch(/==green: As shown in <!-- ref:sec-2 -->\[Section 2\]\(sec2\.md\) the rate equals \$r = 1\/2\$==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 22) Regression (Bug F): MIXED_MATH_TEXT — selection starts inside inline
//     math and ends in a plain-text tail whose suffix contains a markdown
//     link. The suffix slice must be normalized the same way.
// ─────────────────────────────────────────────────────────────────────────────
test('MIXED_MATH_TEXT with a ref link in the plainTail highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'mixtail.md':
      '# MixTail\n\n' +
      'The rate is $r = 1/2$ as documented in <!-- ref:sec-3 -->[Section 3](sec3.md) today.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=mixtail.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await expect(page.locator('#content p .katex').first()).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Start selection inside `$r = 1/2$`, end after "today" in the tail.
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      const katexEls = p.querySelectorAll('.katex:not(.katex .katex)');
      if (katexEls.length < 1) return { err: 'no katex' };
      const rMath = katexEls[0];
      const tw = document.createTreeWalker(rMath, NodeFilter.SHOW_TEXT);
      const rText = tw.nextNode();
      if (!rText) return { err: 'no text in r' };

      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const idx = data.indexOf('today');
        if (idx !== -1) { endText = tn; endOffset = idx + 'today'.length; break; }
      }
      if (!endText) return { err: 'end text not found' };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(rText, 0);
      r.setEnd(endText, endOffset);
      s.addRange(r);

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { ok: true, selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('today');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="purple"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/mixtail.md`);
    const txt = await res.text();
    expect(txt).toMatch(/==purple: \$r = 1\/2\$ as documented in <!-- ref:sec-3 -->\[Section 3\]\(sec3\.md\) today==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 23) Regression: CRLF-authored source. Files saved on Windows have `\r\n`
//     line endings. `split('\n')` leaves a trailing `\r` on each line, and
//     `stripInlineMarkersWithMap.isWS` must include `\r` or the normalized
//     haystack has literal CR chars wedged between words at the wrap point.
//     markdown-it normalizes CRLF->LF internally, so the DOM-derived needle
//     has no CR — a naive `isWS` set misses cross-line matches against the
//     CRLF haystack and raises "Selection contains formatted text".
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_TEXT cross-line highlight works on CRLF-authored source', async ({ page, request }) => {
  const port = nextPort();
  // Write the fixture with literal CRLF line endings, bypassing the default
  // LF-normalized helper.
  const fs = require('fs');
  const os = require('os');
  const path = require('path');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'viewer-test-crlf-'));
  const crlf =
    '# CRLF\r\n\r\n' +
    '- Some leading prose followed by a phrase that wraps at the\r\n' +
    '  end of the source line and continues on the next line here.\r\n';
  fs.writeFileSync(path.join(dir, 'crlf.md'), crlf, 'utf8');
  const { startServer, stopServer } = require('./helpers/server');
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=crlf.md`);
    await expect(page.locator('#content li').first()).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    const sel = await page.evaluate(() => {
      const li = Array.from(document.querySelectorAll('#content li'))
        .find(el => (el.textContent || '').includes('phrase that wraps'));
      if (!li) return { err: 'li not found' };
      const walker = document.createTreeWalker(li, NodeFilter.SHOW_TEXT);
      /** @type {Text | null} */ let startText = null; let startOffset = 0;
      /** @type {Text | null} */ let endText   = null; let endOffset   = 0;
      while (walker.nextNode()) {
        const t = /** @type {Text} */ (walker.currentNode);
        const data = t.nodeValue || '';
        const sIdx = data.indexOf('phrase that wraps');
        if (sIdx !== -1 && !startText) { startText = t; startOffset = sIdx; }
        const eIdx = data.indexOf('continues on');
        if (eIdx !== -1) { endText = t; endOffset = eIdx + 'continues on'.length; }
      }
      if (!startText || !endText) return { err: 'text nodes not found' };
      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();

    await page.waitForTimeout(50);
    await page.locator('#hl-toolbar .hl-swatch[data-action="yellow"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /not supported|Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/crlf.md`);
    const txt = await res.text();
    // Wrapped highlight must span both source lines, with `\r\n` and the
    // continuation-line indent preserved inside the ==yellow: ... == wrap.
    expect(txt).toMatch(/==yellow: phrase that wraps at the\r\n  end of the source line and continues on==/);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 24) Regression (Bug G): PLAIN_SPANNING_MATH in a block that already has a
//     prior ==color:...== annotation. The annotation adds source characters
//     (the "==green: " prefix and closing "==") that are absent from DOM text,
//     biasing the global position ratio used to match KaTeX elements to source
//     formulas. For elements after the annotation the ratio is systematically
//     too small, and for the second KaTeX element this bias can cause lastMath
//     to resolve to a formula *after* the correct one, making the suffix search
//     for plainTail return -1 and triggering "Could not locate selection end in
//     source". Mirrors the appendix-c-part-2-loop-closure.md paragraph:
//     "The two rates are equal only at the narrow-loop limit $\alpha \to 0$;
//     away from that limit the $d = 2$ envelope is always slower."
// ─────────────────────────────────────────────────────────────────────────────
test('PLAIN_SPANNING_MATH with a prior annotation in the block highlights cleanly', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'annot.md':
      '# Annot\n\n' +
      'First ==green: annotated term== here. The rates are equal only at $\\alpha \\to 0$; away from that limit the $d = 2$ envelope is always slower.\n',
  });
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=annot.md`);
    await expect(page.locator('#content p')).toBeVisible();
    await expect(page.locator('#content p .katex').first()).toBeVisible();
    const katexCount = await page.locator('#content p .katex:not(.katex .katex)').count();
    expect(katexCount).toBeGreaterThanOrEqual(2);

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Select from "The rates" (text node after the <mark>) to end of
    // "envelope is always slower." (text node after the second KaTeX).
    // This is PLAIN_SPANNING_MATH with both KaTeX elements downstream of the
    // annotation; the inter-math text anchoring fix must pick both formulas
    // correctly despite the position-ratio bias from the annotation overhead.
    const sel = await page.evaluate(() => {
      const p = document.querySelector('#content p');
      if (!p) return { err: 'no p' };

      /** @type {Text | null} */ let startText = null;
      let startOffset = 0;
      /** @type {Text | null} */ let endText = null;
      let endOffset = 0;
      for (const child of Array.from(p.childNodes)) {
        if (child.nodeType !== 3) continue;
        const tn = /** @type {Text} */ (child);
        const data = tn.nodeValue || '';
        const sIdx = data.indexOf('The rates');
        if (sIdx !== -1 && !startText) { startText = tn; startOffset = sIdx; }
        const eIdx = data.indexOf('envelope is always slower.');
        if (eIdx !== -1) { endText = tn; endOffset = eIdx + 'envelope is always slower.'.length; }
      }
      if (!startText || !endText) return { err: 'text nodes not found', pText: p.textContent };

      const s = window.getSelection();
      s.removeAllRanges();
      const r = document.createRange();
      r.setStart(startText, startOffset);
      r.setEnd(endText, endOffset);
      s.addRange(r);

      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: 100, clientY: 100, bubbles: true,
      }));
      return { selText: r.toString() };
    });
    expect(sel.err).toBeUndefined();
    expect(sel.selText).toContain('The rates are equal only at');
    expect(sel.selText).toContain('envelope is always slower.');

    await page.waitForTimeout(50);
    await expect(page.locator('#hl-toolbar')).toHaveClass(/visible/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="orange"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    const res = await request.get(`http://localhost:${port}/api/md/annot.md`);
    const txt = await res.text();
    // The rewritten source must contain an orange highlight that wraps both
    // inline math formulas with their surrounding plain text intact.
    expect(txt).toContain(
      '==orange: The rates are equal only at $\\alpha \\to 0$; away from that limit the $d = 2$ envelope is always slower.=='
    );
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 25) Regression (Bug H): recoloring a multi-line annotation in a CRLF-
//     authored source file. The DOM delivers \n (markdown-it renders
//     softbreak as \n) but the source stores \r\n. Building `escaped` from
//     DOM textContent with a literal \n produces a regex that does not match
//     the \r\n in blockSrc, causing "Could not locate highlight in source".
//     Fix: replace whitespace in escaped with \s+ so \r?\n is accepted.
//     Also verifies the rewritten annotation preserves \r\n (color change
//     only, no loss of original line endings).
// ─────────────────────────────────────────────────────────────────────────────
test('recolor of a CRLF multi-line annotation changes color and preserves CRLF', async ({ page, request }) => {
  const port = nextPort();
  const fs = require('fs');
  const os = require('os');
  const path = require('path');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'viewer-test-crlf-recolor-'));
  // Annotation text spans a CRLF line break inside the ==orange:...== markup.
  const crlf =
    '# CRLF Recolor\r\n\r\n' +
    'Look at ==orange: the\r\n' +
    'residual-ramp lag here== done.\r\n';
  fs.writeFileSync(path.join(dir, 'crlfrc.md'), crlf, 'utf8');
  const { startServer, stopServer } = require('./helpers/server');
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=crlfrc.md`);
    await expect(page.locator('mark.hl-orange')).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Single click (collapsed selection) inside the orange mark to enter
    // recolor mode, then switch to blue.
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-orange');
      const tn = mk.firstChild;
      if (!tn) return;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, Math.min(2, (tn.textContent || '').length));
      r.setEnd(tn, Math.min(2, (tn.textContent || '').length));
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    await page.locator('#hl-toolbar .hl-swatch[data-action="blue"]').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    // Color changed; CRLF inside the annotation must be preserved verbatim.
    const res = await request.get(`http://localhost:${port}/api/md/crlfrc.md`);
    const txt = await res.text();
    expect(txt).toContain('==blue: the\r\nresidual-ramp lag here==');
    expect(txt).not.toContain('==orange: the');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 26) Regression (Bug H): clearing a multi-line annotation in a CRLF-
//     authored source file. Same \r\n mismatch as test 25. After clearing,
//     the plain content (including the \r\n soft break) must remain in the
//     source without the ==color:...== delimiters.
// ─────────────────────────────────────────────────────────────────────────────
test('clear of a CRLF multi-line annotation removes markup and preserves CRLF content', async ({ page, request }) => {
  const port = nextPort();
  const fs = require('fs');
  const os = require('os');
  const path = require('path');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'viewer-test-crlf-clear-'));
  const crlf =
    '# CRLF Clear\r\n\r\n' +
    'Look at ==green: the\r\n' +
    'important phrase here== done.\r\n';
  fs.writeFileSync(path.join(dir, 'crlfcl.md'), crlf, 'utf8');
  const { startServer, stopServer } = require('./helpers/server');
  const server = await startServer(dir, port);

  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('console', (m) => { if (m.type() === 'error') pageErrors.push(m.text()); });

  try {
    await page.goto(`http://localhost:${port}?file=crlfcl.md`);
    await expect(page.locator('mark.hl-green')).toBeVisible();

    const toasts = [];
    await page.exposeFunction('__recordToast', (msg) => { toasts.push(msg); });
    await page.evaluate(() => {
      const tEl = document.getElementById('toast');
      if (tEl) {
        const mo = new MutationObserver(() => {
          if (tEl.classList.contains('visible') && tEl.textContent) {
            // @ts-ignore
            window.__recordToast(tEl.textContent);
          }
        });
        mo.observe(tEl, { attributes: true, childList: true, subtree: true });
      }
    });

    // Single click inside the green mark to enter clear mode, then clear it.
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-green');
      const tn = mk.firstChild;
      if (!tn) return;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, Math.min(2, (tn.textContent || '').length));
      r.setEnd(tn, Math.min(2, (tn.textContent || '').length));
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    // In clear-only or recolor-only mode — the ✕ button clears the mark
    await expect(page.locator('#hl-toolbar')).toBeVisible();
    await page.locator('#hl-toolbar .hl-btn-clear').click();
    await page.waitForTimeout(200);

    const errToast = toasts.find(t => /Could not locate/i.test(t));
    expect(errToast, `unexpected toast: ${toasts.join(' | ')}`).toBeUndefined();
    expect(pageErrors, `page errors: ${pageErrors.join(' | ')}`).toHaveLength(0);

    // Markup removed; plain content with the \r\n break must remain intact.
    const res = await request.get(`http://localhost:${port}/api/md/crlfcl.md`);
    const txt = await res.text();
    expect(txt).toContain('the\r\nimportant phrase here');
    expect(txt).not.toContain('==green:');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Scope toggle — Highlights pane (file mode + reload persistence)
// ─────────────────────────────────────────────────────────────────────────────
test('highlights file mode shows only current file entries including notes', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['a.md', 'b.md']),
    'a.md': '# A\n\nThis is ==yellow: marked-in-a==[^note-a-1] text.\n\n[^note-a-1]: a-note-body\n',
    'b.md': '# B\n\nThis is ==teal: marked-in-b== text.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('#highlights-list')).not.toHaveClass(/tab-hidden/);

    // Folder mode: both files contribute entries
    await expect(page.locator('#highlights-list .hl-entry')).toHaveCount(2);

    // Switch to file mode
    await page.locator('#highlights-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('#highlights-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');

    // Only a.md's entry remains, and it carries the 📝 note marker
    await expect(page.locator('#highlights-list .hl-entry')).toHaveCount(1);
    await expect(page.locator('#highlights-list .hl-entry.has-note')).toHaveCount(1);
  } finally {
    stopServer(server, dir);
  }
});

test('highlights scope survives page reload', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['x.md', 'y.md']),
    'x.md': '# X\n\nA ==yellow: hl-x== entry.\n',
    'y.md': '# Y\n\nA ==teal: hl-y== entry.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=x.md`);
    await expect(page.locator('#content h1')).toHaveText('X');
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await page.locator('#highlights-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('#highlights-list .hl-entry')).toHaveCount(1);

    // Reload the page; the Highlights tab is reactivated by clicking it.
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('X');
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('#highlights-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#highlights-list .hl-entry')).toHaveCount(1);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Scope toggle — Outline and Highlights scopes are independent
// ─────────────────────────────────────────────────────────────────────────────
test('outline scope and highlights scope are independent per pane', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['p.md', 'q.md']),
    'p.md': '# P\n\n## P.1\n\nA ==yellow: hl-p== entry.\n',
    'q.md': '# Q\n\n## Q.1\n\nA ==teal: hl-q== entry.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=p.md`);
    await expect(page.locator('#content h1')).toHaveText('P');

    // Outline → file
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);
    await page.locator('#outline-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(0);

    // Highlights → leave at folder default
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('#highlights-list')).not.toHaveClass(/tab-hidden/);
    await expect(page.locator('#highlights-list .pane-scope-btn[data-scope="folder"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#highlights-list .hl-entry')).toHaveCount(2);  // both files

    // Re-open Outline — file mode still in effect for the Outline pane only
    await page.locator('.sidebar-tab[data-tab="outline"]').click();
    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});
