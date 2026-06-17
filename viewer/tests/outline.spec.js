// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 7400;
function nextPort() { return portCounter++; }

// Docked-sidebar outline contract — pin classic layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

async function openOutline(page) {
  await page.locator('.sidebar-tab[data-tab="outline"]').click();
  // Wait for outline pane to become visible
  await expect(page.locator('#outline-list')).not.toHaveClass(/tab-hidden/);
}

// ─────────────────────────────────────────────────────────────────────────────
// Folder-wide outline — flat list across all files in fileList order
// ─────────────────────────────────────────────────────────────────────────────
test('outline lists headings from every file in the folder in sidebar order', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['index.md', 'chap-a.md', 'chap-b.md']),
    'index.md':   '# Index\n\n## Welcome\n\nHello.',
    'chap-a.md':  '# Chapter A\n\n## A.1 First\n\n## A.2 Second',
    'chap-b.md':  '# Chapter B\n\n## B.1 Only',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await openOutline(page);

    // Three separators, one per file, in order.json order.
    const seps = page.locator('.outline-file-sep');
    await expect(seps).toHaveCount(3);
    await expect(seps.nth(0)).toHaveText('index.md');
    await expect(seps.nth(1)).toHaveText('chap-a.md');
    await expect(seps.nth(2)).toHaveText('chap-b.md');

    // Current file separator is marked.
    await expect(seps.nth(0)).toHaveAttribute('data-current', '');
    await expect(seps.nth(1)).not.toHaveAttribute('data-current', '');

    // Sibling prefetch is async — wait for synthetic entries to appear.
    await expect(page.locator('.outline-entry[data-file="chap-a.md"]')).toHaveCount(3);
    await expect(page.locator('.outline-entry[data-file="chap-b.md"]')).toHaveCount(2);
    await expect(page.locator('.outline-entry[data-file="index.md"]')).toHaveCount(2);

    // Ordering: all index entries appear before any chap-a, which appears before chap-b.
    const files = await page.locator('.outline-entry').evaluateAll(els => els.map(e => e.dataset.file));
    const firstA = files.indexOf('chap-a.md');
    const lastIdx = files.lastIndexOf('index.md');
    const firstB = files.indexOf('chap-b.md');
    expect(lastIdx).toBeLessThan(firstA);
    expect(firstA).toBeLessThan(firstB);

    // Current-file entries are tinted.
    const currentEntries = page.locator('.outline-entry[data-current]');
    await expect(currentEntries).toHaveCount(2);
    await expect(currentEntries.first()).toHaveAttribute('data-file', 'index.md');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Single-file folder degrades to the old behavior (no separators)
// ─────────────────────────────────────────────────────────────────────────────
test('single-file folder hides file separators', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'solo.md': '# Solo\n\n## Section 1\n\n## Section 2',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=solo.md`);
    await expect(page.locator('#content h1')).toHaveText('Solo');
    await openOutline(page);

    await expect(page.locator('.outline-file-sep')).toHaveCount(0);
    await expect(page.locator('.outline-entry')).toHaveCount(3);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Clicking a sibling heading loads that file and scrolls to the anchor
// ─────────────────────────────────────────────────────────────────────────────
test('clicking a sibling heading navigates to that file and anchor', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['a.md', 'b.md']),
    'a.md': '# A\n\n## A Section',
    'b.md': '# B\n\n## B Section\n\n## Deep Topic',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');
    await openOutline(page);

    // Wait for sibling entries
    await expect(page.locator('.outline-entry[data-file="b.md"]')).toHaveCount(3);

    // Click "Deep Topic" — anchor id slug "deep-topic".
    const deepTopic = page.locator('.outline-entry[data-file="b.md"][data-anchor="deep-topic"]');
    await deepTopic.click();

    await page.waitForTimeout(400);
    expect(page.url()).toContain('file=b.md');
    expect(page.url()).toContain('#deep-topic');
    await expect(page.locator('#content h1')).toHaveText('B');

    // After navigation, outline rebuilds — b.md is now the current-file group.
    await expect(page.locator('.outline-file-sep[data-current]')).toHaveText('b.md');

    // Target heading should be present in the new content.
    const target = page.locator('#content h2#deep-topic');
    await expect(target).toBeVisible();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Clicking a current-file heading scrolls in place and updates URL
// ─────────────────────────────────────────────────────────────────────────────
test('clicking a current-file heading scrolls without re-fetch', async ({ page }) => {
  const port = nextPort();
  const filler = Array.from({ length: 60 }, (_, i) => `Line ${i}`).join('\n\n');
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['main.md', 'other.md']),
    'main.md': `# Main\n\n## Top\n\n${filler}\n\n## Far Below`,
    'other.md': '# Other\n\n## O.1',
  });
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`http://localhost:${port}/?file=main.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('#content h1')).toHaveText('Main', { timeout: 10_000 });
    await openOutline(page);

    // Record the fetch count for main.md, then click its "Far Below" outline entry.
    let fetchCount = 0;
    page.on('request', (req) => {
      if (req.url().includes('/api/md/main.md')) fetchCount++;
    });

    const farBelow = page.locator('.outline-entry[data-file="main.md"][data-anchor="far-below"]');
    await farBelow.click();
    await page.waitForTimeout(500);

    expect(page.url()).toContain('file=main.md');
    expect(page.url()).toContain('#far-below');
    expect(fetchCount).toBe(0); // same file, no refetch

    // The active class should be on far-below entry.
    await expect(farBelow).toHaveClass(/active/);

    // Page scrolled down to the heading.
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeGreaterThan(500);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Slug parity: extractHeadings must produce the same id as the renderer
// ─────────────────────────────────────────────────────────────────────────────
test('slugs for inline-math and inline-code headings match the rendered DOM', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['render.md', 'sib.md']),
    'render.md':
      '# Render\n\n' +
      '## Required SNR for $P_d = 99\\%$\n\n' +
      '## Use the `helper()` function\n\n' +
      '## Bold **word** here',
    'sib.md': '# Sibling\n\n## Just a section',
  });
  const server = await startServer(dir, port);
  try {
    // Load sib.md so that render.md headings come from the *sibling* code path
    // (parsed from raw markdown, not from the DOM).
    await page.goto(`http://localhost:${port}/?file=sib.md`);
    await expect(page.locator('#content h1')).toHaveText('Sibling');
    await openOutline(page);

    // Wait for sibling entries from render.md to appear (lazy prefetch).
    await expect(page.locator('.outline-entry[data-file="render.md"]')).toHaveCount(4);

    // Grab the data-anchor values computed from raw markdown.
    const anchors = await page.locator('.outline-entry[data-file="render.md"]')
      .evaluateAll(els => els.map(e => e.dataset.anchor));

    // Now load render.md and compare with the live DOM ids.
    await page.locator('.outline-entry[data-file="render.md"]').first().click();
    await expect(page.locator('#content h1')).toHaveText('Render');

    const domIds = await page.locator('#content h2').evaluateAll(els => els.map(e => e.id));

    // The parsed anchors for h2 entries (indices 1..3) must match the DOM ids.
    expect(anchors.slice(1)).toEqual(domIds);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Live-reload: sibling file change refreshes the outline while tab is visible
// ─────────────────────────────────────────────────────────────────────────────
test('outline refreshes when a sibling file changes on disk', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['current.md', 'watched.md']),
    'current.md': '# Current\n\n## Here',
    'watched.md': '# Watched\n\n## Before',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=current.md`);
    await expect(page.locator('#content h1')).toHaveText('Current');
    await openOutline(page);

    await expect(page.locator('.outline-entry[data-file="watched.md"]')).toHaveCount(2);
    await expect(page.locator('.outline-entry[data-file="watched.md"]').nth(1))
      .toHaveText('Before');

    // Modify watched.md on disk.
    fs.writeFileSync(
      path.join(dir, 'watched.md'),
      '# Watched\n\n## Before\n\n## After',
      'utf8',
    );

    // Give the WS change event + re-fetch + rebuild a moment.
    await expect(page.locator('.outline-entry[data-file="watched.md"]')).toHaveCount(3, { timeout: 5000 });
    await expect(page.locator('.outline-entry[data-file="watched.md"]').nth(2))
      .toHaveText('After');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Heading extractor skips fenced code blocks and $$ math
// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────
// Highlights tab: scoped to the active folder and ordered by fileList
// ─────────────────────────────────────────────────────────────────────────────
test('highlights list is scoped to the active folder and ordered by chapter', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    // The server reads order.json only at the target-dir root; list files in
    // an order that defies alphabetical sort so we can prove chapter order wins.
    'order.json': JSON.stringify([
      'work/z-first.md',
      'work/a-second.md',
      'work/m-third.md',
      'other/extra.md',
    ]),
    'work/z-first.md':  '# Z\n\n==yellow: Z-hit==\n',
    'work/a-second.md': '# A\n\n==green: A-hit==\n',
    'work/m-third.md':  '# M\n\n==red: M-hit==\n',
    // Different top-level folder — must NOT appear when viewing `work/`.
    'other/extra.md':   '# Extra\n\n==blue: Extra-hit==\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=work/z-first.md`);
    await expect(page.locator('#content h1')).toHaveText('Z');

    // Open Highlights tab
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();

    // Only the three hits from work/* — not "Extra-hit" from other/*.
    await expect(page.locator('.hl-entry')).toHaveCount(3);
    const texts = await page.locator('.hl-entry .hl-entry-text').allInnerTexts();
    expect(texts).toEqual(['Z-hit', 'A-hit', 'M-hit']);

    const labels = await page.locator('.hl-entry .hl-entry-file').allInnerTexts();
    expect(labels[0]).toContain('z-first.md');
    expect(labels[1]).toContain('a-second.md');
    expect(labels[2]).toContain('m-third.md');

    // No stray entries from the other folder.
    const joined = labels.join('|');
    expect(joined).not.toContain('extra.md');
  } finally {
    stopServer(server, dir);
  }
});

test('highlights sidebar scroll is preserved across click navigation', async ({ page }) => {
  const port = nextPort();
  // Make enough highlights that the list overflows vertically.
  const files = {};
  const fileNames = [];
  const hits = [];
  for (let f = 0; f < 3; f++) {
    const fname = `f${f}.md`;
    fileNames.push(fname);
    let md = `# F${f}\n\n`;
    for (let k = 0; k < 10; k++) {
      md += `==yellow: hit-${f}-${k}== in paragraph ${k}.\n\n`;
      hits.push({ file: fname, k });
    }
    files[fname] = md;
  }
  files['order.json'] = JSON.stringify(fileNames);
  const dir = createFixtureDir(files);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 1200, height: 420 }); // keep sidebar short
    await page.goto(`http://localhost:${port}/?file=f0.md`);
    await expect(page.locator('#content h1')).toHaveText('F0');
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();
    await expect(page.locator('.hl-entry')).toHaveCount(30, { timeout: 5000 });

    // Scroll the sidebar list down to the middle.
    const preScrollTop = await page.evaluate(() => {
      const el = document.getElementById('highlights-list');
      el.scrollTop = 400;
      return el.scrollTop;
    });
    expect(preScrollTop).toBeGreaterThan(100);

    // Click an entry far down in the list that's currently visible. Blur
    // the button afterwards so the browser's native "scroll focused
    // element into view" doesn't masquerade as a scroll-preservation bug.
    const clickIndex = 20;
    await page.locator('.hl-entry').nth(clickIndex).evaluate((el) => {
      el.click();
      el.blur();
    });
    await page.waitForTimeout(800);

    // After nav, sidebar scroll should still be near the pre-click value.
    const postScrollTop = await page.evaluate(() =>
      document.getElementById('highlights-list').scrollTop,
    );
    expect(Math.abs(postScrollTop - preScrollTop)).toBeLessThanOrEqual(40);
  } finally {
    stopServer(server, dir);
  }
});

test('highlights list rescopes when navigating to a different folder', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/one.md', 'beta/two.md']),
    'alpha/one.md':  '# One\n\n==yellow: alpha-hit==\n',
    'beta/two.md':   '# Two\n\n==green: beta-hit==\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha/one.md`);
    await expect(page.locator('#content h1')).toHaveText('One');
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();

    // Only alpha-hit visible.
    await expect(page.locator('.hl-entry')).toHaveCount(1);
    await expect(page.locator('.hl-entry .hl-entry-text').first()).toHaveText('alpha-hit');

    // Navigate to beta folder — switch back to files tab first, since
    // Highlights tab hides the sidebar file list.
    await page.locator('.sidebar-tab[data-tab="files"]').click();
    await page.locator('.dir-group[data-dir="beta"] .dir-header').click();
    await page.locator('.file-entry[data-file="beta/two.md"]').click();
    await expect(page.locator('#content h1')).toHaveText('Two');

    // Flip back to Highlights to check the list rescoped.
    await page.locator('.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('#highlights-list')).toBeVisible();

    // Highlights should now show only beta-hit.
    await expect(page.locator('.hl-entry')).toHaveCount(1);
    await expect(page.locator('.hl-entry .hl-entry-text').first()).toHaveText('beta-hit');
  } finally {
    stopServer(server, dir);
  }
});

test('extractHeadings skips fenced code and display math containing # lines', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'tricky.md']),
    'home.md': '# Home\n\n## Hi',
    'tricky.md':
      '# Tricky\n\n' +
      '## Real Heading\n\n' +
      '```\n' +
      '# not a heading (fenced)\n' +
      '## also not\n' +
      '```\n\n' +
      '$$\n' +
      '# inside display math\n' +
      '$$\n\n' +
      '## Another Real One',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);

    // tricky.md should have exactly 3 headings: H1 "Tricky", H2 "Real Heading", H2 "Another Real One".
    await expect(page.locator('.outline-entry[data-file="tricky.md"]')).toHaveCount(3);
    const texts = await page.locator('.outline-entry[data-file="tricky.md"]')
      .evaluateAll(els => els.map(e => e.textContent));
    expect(texts).toEqual(['Tricky', 'Real Heading', 'Another Real One']);
  } finally {
    stopServer(server, dir);
  }
});

test('extractHeadings recognizes setext headings (=== h1, --- h2) in siblings', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'setext.md']),
    'home.md': '# Home\n\n## Hi',
    'setext.md':
      'Setext Title\n' +
      '===\n\n' +
      'A Subsection\n' +
      '---\n\n' +
      '## ATX Also\n\n' +
      'Para then a blank line then a rule\n\n' +
      '---\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);
    // The trailing `---` has a blank line before it (thematic break, not setext),
    // so only 3 headings are listed.
    const texts = await page.locator('.outline-entry[data-file="setext.md"]')
      .evaluateAll(els => els.map(e => e.textContent));
    expect(texts).toEqual(['Setext Title', 'A Subsection', 'ATX Also']);
  } finally {
    stopServer(server, dir);
  }
});

test('sibling outline groups collapse on sep click and persist across reload (#2)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'other.md']),
    'home.md': '# Home\n\n## H2',
    'other.md': '# Other\n\n## Other H2\n\n## Other H3',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);
    const otherFirst = page.locator('.outline-file-group[data-file="other.md"] .outline-entry').first();
    await expect(otherFirst).toBeVisible();
    await page.locator('.outline-file-group[data-file="other.md"] .outline-file-sep').click();
    await expect(page.locator('.outline-file-group[data-file="other.md"]')).toHaveClass(/collapsed/);
    await expect(otherFirst).toBeHidden();
    // persists across reload (sessionStorage)
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);
    await expect(page.locator('.outline-file-group[data-file="other.md"]')).toHaveClass(/collapsed/);
  } finally {
    stopServer(server, dir);
  }
});

test('outline tree: ArrowDown moves roving focus between entries (#4)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({ 'a.md': '# A\n\n## A2\n\n## A3' });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('A');
    await openOutline(page);
    const entries = page.locator('.outline-entry');
    await expect(entries).toHaveCount(3);
    await entries.nth(0).focus();
    await page.keyboard.press('ArrowDown');
    await expect(entries.nth(1)).toBeFocused();
    await page.keyboard.press('ArrowDown');
    await expect(entries.nth(2)).toBeFocused();
  } finally {
    stopServer(server, dir);
  }
});

test('extractHeadings skips YAML frontmatter — no phantom setext heading (review #3)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'fm.md']),
    'home.md': '# Home',
    'fm.md': '---\ntitle: Front Matter\ndate: 2026\n---\n\n# Real Heading\n\n## Sub',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);
    // The closing `---` must NOT make a phantom h2 of "date: 2026".
    const texts = await page.locator('.outline-entry[data-file="fm.md"]')
      .evaluateAll(els => els.map(e => e.textContent));
    expect(texts).toEqual(['Real Heading', 'Sub']);
  } finally {
    stopServer(server, dir);
  }
});

test('ArrowLeft does not collapse the CURRENT file group (scroll-spy guard, review #4)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['home.md', 'other.md']),
    'home.md': '# Home\n\n## H2',
    'other.md': '# Other',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=home.md`);
    await expect(page.locator('#content h1')).toHaveText('Home');
    await openOutline(page);
    const curGroup = page.locator('.outline-file-group[data-file="home.md"]');
    await expect(curGroup).not.toHaveClass(/collapsed/);
    await curGroup.locator('.outline-file-sep').focus();
    await page.keyboard.press('ArrowLeft');
    await expect(curGroup).not.toHaveClass(/collapsed/);
  } finally {
    stopServer(server, dir);
  }
});

test('chapter-number sort toggle reorders siblings by filename numeric token (#5)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    // order.json puts 10 before 2 (authoritative file order by default)
    'order.json': JSON.stringify(['c-10.md', 'c-2.md']),
    'c-10.md': '# Ten',
    'c-2.md': '# Two',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=c-10.md`);
    await expect(page.locator('#content h1')).toHaveText('Ten');
    await openOutline(page);
    // default: order.json order (10 before 2)
    let order = await page.locator('.outline-file-group').evaluateAll(els => els.map(e => e.dataset.file));
    expect(order).toEqual(['c-10.md', 'c-2.md']);
    // toggle chapter sort → numeric (2 before 10)
    await page.locator('.outline-sort-toggle').click();
    order = await page.locator('.outline-file-group').evaluateAll(els => els.map(e => e.dataset.file));
    expect(order).toEqual(['c-2.md', 'c-10.md']);
  } finally {
    stopServer(server, dir);
  }
});

test('outline is an ARIA tree: role=tree container, aria-level/setsize/posinset, type-ahead', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha.md', 'bravo.md']),
    'alpha.md': '# Alpha\n\n## A1\n\n## A2',
    'bravo.md': '# Bravo',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=alpha.md`);
    await expect(page.locator('#content h1')).toHaveText('Alpha');
    await openOutline(page);
    await expect(page.locator('.outline-tree[role="tree"]')).toHaveCount(1);
    const alphaSep = page.locator('.outline-file-sep[data-file="alpha.md"]');
    await expect(alphaSep).toHaveAttribute('role', 'treeitem');
    await expect(alphaSep).toHaveAttribute('aria-level', '1');
    await expect(alphaSep).toHaveAttribute('aria-setsize', '2'); // 2 sibling files
    // aria-level reflects HEADING depth (not flat tree depth): in a group the h1
    // title nests at level 2, an h2 at level 3 — DISTINCT, so flattening can't
    // silently re-land (review w4t4jnj9r). posinset/setsize within the group.
    const entries = page.locator('.outline-file-group[data-file="alpha.md"] .outline-entry');
    await expect(entries.nth(0)).toHaveAttribute('aria-level', '2'); // Alpha (h1)
    await expect(entries.nth(0)).toHaveAttribute('aria-posinset', '1');
    await expect(entries.nth(0)).toHaveAttribute('aria-setsize', '3'); // Alpha, A1, A2
    await expect(entries.nth(1)).toHaveAttribute('aria-level', '3'); // A1 (h2) — deeper
    // type-ahead: 'b' jumps to the bravo group header
    await alphaSep.focus();
    await page.keyboard.press('b');
    await expect(page.locator('.outline-file-sep[data-file="bravo.md"]')).toBeFocused();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Scope toggle — per-pane Folder/File switch with per-folder persistence
// ─────────────────────────────────────────────────────────────────────────────
test('outline scope toggle renders and defaults to folder', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['index.md', 'chap-a.md']),
    'index.md':   '# Index\n\n## Welcome',
    'chap-a.md':  '# Chap A\n\n## A.1',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await openOutline(page);

    const toggle = page.locator('#outline-list .pane-scope');
    await expect(toggle).toBeVisible();
    await expect(toggle.locator('.pane-scope-btn[data-scope="folder"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(toggle.locator('.pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'false');

    // Folder mode: separators visible because there are 2 sibling files
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(2);
  } finally {
    stopServer(server, dir);
  }
});

test('outline file mode shows only current file headings, no separators', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['index.md', 'chap-a.md', 'chap-b.md']),
    'index.md':   '# Index\n\n## Welcome',
    'chap-a.md':  '# Chap A\n\n## A.1\n\n## A.2',
    'chap-b.md':  '# Chap B\n\n## B.1',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Index');
    await openOutline(page);

    // Wait for sibling prefetch so folder mode is fully populated before toggling.
    await expect(page.locator('.outline-entry[data-file="chap-a.md"]')).toHaveCount(3);

    await page.locator('#outline-list .pane-scope-btn[data-scope="file"]').click();

    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(0);
    await expect(page.locator('.outline-entry[data-file="chap-a.md"]')).toHaveCount(0);
    await expect(page.locator('.outline-entry[data-file="chap-b.md"]')).toHaveCount(0);
    await expect(page.locator('.outline-entry[data-file="index.md"]')).toHaveCount(2);
  } finally {
    stopServer(server, dir);
  }
});

test('outline scope persists per folder across navigation', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'order.json': JSON.stringify(['alpha/a1.md', 'alpha/a2.md', 'beta/b1.md', 'beta/b2.md']),
    'alpha/a1.md': '# A1\n\n## A1.1',
    'alpha/a2.md': '# A2\n\n## A2.1',
    'beta/b1.md':  '# B1\n\n## B1.1',
    'beta/b2.md':  '# B2\n\n## B2.1',
  });
  const server = await startServer(dir, port);
  try {
    // Folder alpha: opt into file mode
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');
    await openOutline(page);
    await page.locator('#outline-list .pane-scope-btn[data-scope="file"]').click();
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(0);

    // Navigate to folder beta — should default back to folder mode
    await page.goto(`http://localhost:${port}/?file=beta/b1.md`);
    await expect(page.locator('#content h1')).toHaveText('B1');
    await openOutline(page);
    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="folder"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(2);

    // Return to alpha — the file-mode preference must be restored
    await page.goto(`http://localhost:${port}/?file=alpha/a1.md`);
    await expect(page.locator('#content h1')).toHaveText('A1');
    await openOutline(page);
    await expect(page.locator('#outline-list .pane-scope-btn[data-scope="file"]'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#outline-list .outline-file-sep')).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});
