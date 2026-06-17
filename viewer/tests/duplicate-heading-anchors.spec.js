// @ts-check
// Regression suite for the duplicate-heading-slug navigation bug
// (bugs/2026-05-19-02). Two identically-titled headings used to collide on
// one DOM id; getElementById then resolved every such link to the FIRST
// occurrence, so clicking the 2nd+ duplicate outline entry jumped to the 1st.
// These tests pin the GitHub-compatible de-dup invariant end-to-end across
// the renderer path, the current-file outline path, and the sibling-file
// (extractHeadings) path.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 4700;
function nextPort() { return portCounter++; }

// Outline-entry clicks need the docked sidebar — pin classic layout
// (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

async function openOutline(page) {
  await page.locator('.sidebar-tab[data-tab="outline"]').click();
  await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);
}

const FILLER = Array.from({ length: 80 }, (_, i) => `Filler paragraph ${i}.`).join('\n\n');

// ─────────────────────────────────────────────────────────────────────────────
// Renderer: identically-titled headings must get unique DOM ids, GitHub-style.
// First occurrence keeps the bare slug so existing anchors stay stable.
// ─────────────────────────────────────────────────────────────────────────────
test('duplicate headings render unique GitHub-style ids; first stays bare', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Survey\n\n' +
      '## 8.1.1 FLL\n\n### Steady-State Errors\n\n### Noise Bandwidth\n\n' +
      '## 8.1.3 PLL\n\n### Noise Bandwidth\n\n## Summary\n\n## Summary\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Survey');

    // The two "Noise Bandwidth" h3s get distinct, GitHub-compatible ids.
    const nb = page.locator('#content h3', { hasText: 'Noise Bandwidth' });
    await expect(nb).toHaveCount(2);
    await expect(nb.nth(0)).toHaveAttribute('id', 'noise-bandwidth');
    await expect(nb.nth(1)).toHaveAttribute('id', 'noise-bandwidth-1');

    // Three-way duplicate increments -1, -2.
    const sm = page.locator('#content h2', { hasText: 'Summary' });
    await expect(sm).toHaveCount(2);
    await expect(sm.nth(0)).toHaveAttribute('id', 'summary');
    await expect(sm.nth(1)).toHaveAttribute('id', 'summary-1');

    // Unique heading keeps its bare slug (existing cross-links don't break).
    await expect(page.locator('#content h3#steady-state-errors')).toBeVisible();

    // Core invariant: no two heading elements in the document share an id.
    const ids = await page.locator('#content :is(h1,h2,h3,h4,h5,h6)')
      .evaluateAll(els => els.map(e => e.id).filter(Boolean));
    expect(new Set(ids).size).toBe(ids.length);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// The exact reported bug: clicking the 2nd duplicate outline entry must scroll
// to the 2nd heading — not the 1st. Pre-fix both entries pointed at the same
// id and getElementById returned the first occurrence.
// ─────────────────────────────────────────────────────────────────────────────
test('clicking each duplicate outline entry scrolls to its own heading', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Doc\n\n' +
      '## Section A\n\n### Noise Bandwidth\n\n' + FILLER + '\n\n' +
      '## Section B\n\n### Noise Bandwidth\n\n' + FILLER + '\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');
    await openOutline(page);

    const entries = page.locator('.outline-entry[data-file="doc.md"]', { hasText: 'Noise Bandwidth' });
    await expect(entries).toHaveCount(2);

    // Entries carry distinct anchors mirroring the deduped DOM ids.
    await expect(entries.nth(0)).toHaveAttribute('data-anchor', 'noise-bandwidth');
    await expect(entries.nth(1)).toHaveAttribute('data-anchor', 'noise-bandwidth-1');

    const h = page.locator('#content h3', { hasText: 'Noise Bandwidth' });

    // Scroll-independent invariant: the anchor an entry points at must resolve
    // (via getElementById, exactly the viewer's scrollToAnchor lookup) to the
    // SAME heading occurrence as the entry. Pre-fix both anchors were
    // `noise-bandwidth` and this returned index 0 for the 2nd entry too.
    const resolvedIndex = (anchor) => page.evaluate((a) => {
      const el = document.getElementById(a);
      const all = [...document.querySelectorAll('#content h3')]
        .filter(x => x.textContent.includes('Noise Bandwidth'));
      return all.indexOf(el);
    }, anchor);

    // Click the SECOND entry → second heading scrolls into view, first does not.
    // toBeInViewport auto-retries, so it rides out the smooth-scroll animation
    // and the can't-centre-at-doc-edge clamp (any intersection counts).
    await entries.nth(1).click();
    await expect(h.nth(1)).toBeInViewport();
    await expect(h.nth(0)).not.toBeInViewport();
    expect(page.url()).toContain('#noise-bandwidth-1');
    expect(await resolvedIndex('noise-bandwidth-1')).toBe(1);

    // Click the FIRST entry → back to the first heading, second leaves view.
    await entries.nth(0).click();
    await expect(h.nth(0)).toBeInViewport();
    await expect(h.nth(1)).not.toBeInViewport();
    expect(page.url()).toContain('#noise-bandwidth');
    expect(page.url()).not.toContain('#noise-bandwidth-1');
    expect(await resolvedIndex('noise-bandwidth')).toBe(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Sibling-file path: extractHeadings must de-dup identically to the renderer
// so a cross-file click lands on the right occurrence after the file loads.
// ─────────────────────────────────────────────────────────────────────────────
test('sibling-file outline de-dups duplicate headings same as the renderer', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'survey.md']),
    'home.md': '# Home\n\n## Start',
    'survey.md':
      '# Survey\n\n## 8.1.1 FLL\n\n### Noise Bandwidth\n\n' +
      '## 8.1.3 PLL\n\n### Noise Bandwidth\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);

    // survey.md entries come from the sibling (raw-markdown) code path.
    const sib = page.locator('.outline-entry[data-file="survey.md"]', { hasText: 'Noise Bandwidth' });
    await expect(sib).toHaveCount(2);
    const sibAnchors = await sib.evaluateAll(els => els.map(e => e.dataset.anchor));
    expect(sibAnchors).toEqual(['noise-bandwidth', 'noise-bandwidth-1']);

    // Load survey.md and confirm the live DOM ids match the sibling anchors.
    await page.locator('.outline-entry[data-file="survey.md"]').first().click();
    await expect(page.locator('#content h1')).toHaveText('Survey');
    const domIds = await page.locator('#content h3', { hasText: 'Noise Bandwidth' })
      .evaluateAll(els => els.map(e => e.id));
    expect(domIds).toEqual(['noise-bandwidth', 'noise-bandwidth-1']);

    // And the deep cross-file link resolves to the SECOND occurrence.
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await openOutline(page);
    await page.locator('.outline-entry[data-file="survey.md"][data-anchor="noise-bandwidth-1"]').click();
    await page.waitForTimeout(500);
    expect(page.url()).toContain('file=survey.md');
    expect(page.url()).toContain('#noise-bandwidth-1');
    const target = page.locator('#content h3#noise-bandwidth-1');
    await expect(target).toBeVisible();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Three-or-more duplicates: each outline entry must navigate to its own
// occurrence (anchors results / results-1 / results-2, each resolving to a
// distinct heading node), not all collapse onto the first.
// ─────────────────────────────────────────────────────────────────────────────
test('a heading repeated three times navigates to three distinct targets', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Doc\n\n' +
      '## Results\n\n' + FILLER + '\n\n' +
      '## Results\n\n' + FILLER + '\n\n' +
      '## Results\n\n' + FILLER + '\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`http://localhost:${port}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');
    await openOutline(page);

    const entries = page.locator('.outline-entry[data-file="doc.md"]', { hasText: 'Results' });
    await expect(entries).toHaveCount(3);
    const anchors = await entries.evaluateAll(els => els.map(e => e.dataset.anchor));
    expect(anchors).toEqual(['results', 'results-1', 'results-2']);

    const h = page.locator('#content h2', { hasText: 'Results' });
    const resolvedIndex = (anchor) => page.evaluate((a) => {
      const el = document.getElementById(a);
      const all = [...document.querySelectorAll('#content h2')]
        .filter(x => x.textContent.includes('Results'));
      return all.indexOf(el);
    }, anchor);

    for (let i = 0; i < 3; i++) {
      await entries.nth(i).click();
      // Auto-retrying viewport assertion rides out the smooth scroll and the
      // doc-edge centring clamp; node-identity is fully scroll-independent.
      await expect(h.nth(i)).toBeInViewport();
      expect(await resolvedIndex(anchors[i])).toBe(i);
    }
  } finally {
    stopServer(server, dir);
  }
});
