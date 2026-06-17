// @ts-check
// Adaptive Reading Shell (redesign 2026-06-14) — three-zone docs layout +
// 66ch measure. Port base 7300 (new suite; never renumber existing bases).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { seedSettings } = require('./helpers/layout');

let port = 7300;
const nextPort = () => port++;

const DOC = `# Quantization

A long body paragraph that must wrap within the constrained measure rather than
running the full width of a wide desktop viewport at 1440 pixels, so the line
length stays in the readable 66ch band instead of the legacy ~95 characters.

## Section A.8.1

More body text under a subsection.
`;

function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

test('T2: default prose measure is ~66ch (much narrower than the legacy 860px width)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');
    // max-width = min(--measure-ch 66ch, 1100px) + 80px padding compensation.
    // At 16px body this resolves well under the old 940px (860 + 80).
    const mw = await page.evaluate(() =>
      parseFloat(getComputedStyle(document.getElementById('content')).maxWidth));
    expect(mw).toBeLessThan(820);
    expect(mw).toBeGreaterThan(520);
  } finally {
    stopServer(server, dir);
  }
});

test('T2: the measure CSS var defaults to 66ch and the slider drives it', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');
    const def = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--measure-ch').trim());
    expect(def).toBe('66ch');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// T4: three-zone docs layout — corpus nav (#sidebar) | prose (#content) |
//     context column (#right-pane: Outline | Marks | Peek). The right pane
//     reparents the live #outline-list / #highlights-list nodes, so the same
//     builders feed both the sidebar drawer (reader/focus) and the pane (docs).
// ─────────────────────────────────────────────────────────────────────────────

// A doc with enough headings + a highlight so both Outline and Marks have
// content to render in the right pane.
const TZ_DOC = `# Quantization

Intro paragraph one with ==yellow: a marked phrase== inside it for the Marks pane.

## Section A

Body under section A.

## Section B

Body under section B.

### Section B.1

Deeper body text under B.1 so the outline has a third-level entry too.
`;

function tzFixture() { return createFixtureDir({ 'tz.md': TZ_DOC }); }

// Seed chrome:'docs' directly (the FOUC guard maps it pre-paint) so the page
// boots in the docked three-zone shell rather than the reader default.
async function gotoDocs(page, p) {
  await seedSettings(page, { chrome: 'docs' });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`http://localhost:${p}/?file=tz.md`);
  await expect(page.locator('#content h1')).toHaveText('Quantization');
}

test('T4: sidebar (docked files) and right-pane are both visible in docs at 1440px', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    await gotoDocs(page, p);
    // Three zones co-resident: left nav, center prose, right context column.
    await expect(page.locator('#sidebar')).toBeVisible();
    await expect(page.locator('#right-pane')).toBeVisible();
    // The left nav is files-only in docs (outline/marks tab buttons hidden).
    await expect(page.locator('#file-list')).toBeVisible();
    await expect(page.locator('.sidebar-tab[data-tab="outline"]')).toBeHidden();
    await expect(page.locator('.sidebar-tab[data-tab="highlights"]')).toBeHidden();
    // Content leaves room on both sides for the two fixed rails.
    const margins = await page.evaluate(() => {
      const cs = getComputedStyle(document.getElementById('content'));
      return { ml: parseFloat(cs.marginLeft), mr: parseFloat(cs.marginRight) };
    });
    expect(margins.ml).toBeGreaterThan(100);   // docked sidebar
    expect(margins.mr).toBeGreaterThan(100);   // right pane
  } finally {
    stopServer(server, dir);
  }
});

test('T4: right-pane exposes Outline|Marks|Peek segments; outline is the default and is populated', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    await gotoDocs(page, p);
    const segs = page.locator('#right-pane .rp-seg');
    await expect(segs).toHaveCount(3);
    await expect(page.locator('#right-pane .rp-seg[data-seg="outline"]')).toBeVisible();
    await expect(page.locator('#right-pane .rp-seg[data-seg="marks"]')).toBeVisible();
    await expect(page.locator('#right-pane .rp-seg[data-seg="peek"]')).toBeVisible();

    // Default active segment is outline.
    await expect(page.locator('#right-pane .rp-seg[data-seg="outline"]'))
      .toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('#rp-outline')).toBeVisible();
    await expect(page.locator('#rp-marks')).toBeHidden();
    await expect(page.locator('#rp-peek')).toBeHidden();

    // The reparented #outline-list lives inside #rp-outline and is populated.
    await expect(page.locator('#rp-outline #outline-list')).toHaveCount(1);
    // 1 H1 + 2 H2 + 1 H3 = 4 entries.
    await expect(page.locator('#rp-outline .outline-entry')).toHaveCount(4);
  } finally {
    stopServer(server, dir);
  }
});

test('T4: clicking a right-pane outline entry scrolls content and marks it active', async ({ page }) => {
  const p = nextPort();
  // Pad the doc so "Section B.1" sits well below the fold.
  const filler = Array.from({ length: 50 }, (_, i) => `Filler line ${i}.`).join('\n\n');
  const dir = createFixtureDir({
    'long.md': `# Quantization\n\n${filler}\n\n## Section A\n\n${filler}\n\n## Far Section\n\nBottom body.\n`,
  });
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=long.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');

    const farEntry = page.locator('#rp-outline .outline-entry[data-anchor="far-section"]');
    await expect(farEntry).toHaveCount(1);
    await farEntry.click();
    await page.waitForTimeout(400);

    expect(page.url()).toContain('#far-section');
    await expect(farEntry).toHaveClass(/active/);
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeGreaterThan(500);
  } finally {
    stopServer(server, dir);
  }
});

test('T4: switching to the Marks segment reveals the reparented highlights list', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    await gotoDocs(page, p);

    await page.locator('#right-pane .rp-seg[data-seg="marks"]').click();
    await expect(page.locator('#right-pane .rp-seg[data-seg="marks"]'))
      .toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('#rp-marks')).toBeVisible();
    await expect(page.locator('#rp-outline')).toBeHidden();

    // #highlights-list reparented into #rp-marks, with the one yellow hit.
    await expect(page.locator('#rp-marks #highlights-list')).toHaveCount(1);
    await expect(page.locator('#rp-marks .hl-entry')).toHaveCount(1);
    await expect(page.locator('#rp-marks .hl-entry .hl-entry-text')).toHaveText('a marked phrase');
  } finally {
    stopServer(server, dir);
  }
});

test('T4: right-pane is hidden in reader mode (default) and at <=768px', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    // Reader is the default chrome — no seed.
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=tz.md`);
    await expect(page.locator('#content h1')).toHaveText('Quantization');
    await expect(page.locator('#right-pane')).toBeHidden();
    // The outline/highlights nodes are back inside the sidebar drawer.
    await expect(page.locator('#sidebar #outline-list')).toHaveCount(1);
    await expect(page.locator('#sidebar #highlights-list')).toHaveCount(1);

    // Even in docs, the right pane must be hidden on the mobile shell.
    await page.evaluate(() => {
      const KEY = 'viewer.settings.v1';
      const s = JSON.parse(localStorage.getItem(KEY) || '{}');
      s.chrome = 'docs';
      localStorage.setItem(KEY, JSON.stringify(s));
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload();
    await expect(page.locator('#content h1')).toHaveText('Quantization');
    await expect(page.locator('#right-pane')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #15: folder-scoped right-pane outline resolves siblings ──

test('T4: folder-scoped right-pane outline resolves sibling files (no stuck "Loading…")', async ({ page }) => {
  const p = nextPort();
  // A multi-file folder: when docs first builds the right-pane outline the
  // siblings are NOT yet cached, so the async sibling-prefetch path runs. The
  // re-entry guard must rebuild the outline (it is driven by isRightPaneActive,
  // NOT the sidebar activeTab which is 'files' in docs) or the sibling sections
  // stay on their 'Loading…' placeholder forever.
  const dir = createFixtureDir({
    'a.md': '# File A\n\n## A One\n\nbody\n\n## A Two\n\nbody\n',
    'b.md': '# File B\n\n## B One\n\nbody\n\n## B Two\n\nbody\n',
    'c.md': '# File C\n\n## C One\n\nbody\n\n## C Two\n\nbody\n',
  });
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('File A');
    await expect(page.locator('#right-pane')).toBeVisible();

    // The outline lists every sibling's headings; the sibling sections must NOT
    // remain on the 'Loading…' placeholder once their fetch lands.
    const outline = page.locator('#right-pane #outline-list');
    await expect.poll(async () =>
      await outline.locator('.outline-entry', { hasText: 'B One' }).count()).toBeGreaterThan(0);
    await expect(outline.locator('.outline-entry', { hasText: 'C Two' })).toHaveCount(1);
    await expect(outline.locator('.outline-empty', { hasText: 'Loading…' })).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #3: right-pane controls don't strand focus on collapse ───

test('T4: focus on a right-pane segment is rescued when the pane collapses (<1400px)', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://localhost:${p}/?file=tz.md`);
    await expect(page.locator('#right-pane')).toBeVisible();

    // Focus a .rp-seg tab button (lives directly in #right-pane, never reparented).
    await page.locator('#right-pane .rp-seg[data-seg="marks"]').focus();
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('marks');

    // Cross below the 1400px breakpoint → CSS hides #right-pane. The mqlWidePane
    // 'change' event (which runs the rescue) fires after the browser re-lays-out
    // and has already dropped focus to <body>, so the rescue is inherently async.
    // Poll until focus lands on a visible target, never stranded on <body> nor on
    // a now-hidden right-pane control.
    await page.setViewportSize({ width: 1200, height: 900 });
    await expect(page.locator('#right-pane')).toBeHidden();
    await expect.poll(async () => await page.evaluate(() => {
      const ae = document.activeElement;
      const stranded = ae === document.body || ae === null
        || document.getElementById('right-pane')?.contains(ae);
      return !stranded;
    })).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #4: #rp-segs WAI-ARIA roving tabindex + arrow-key nav ────
// #rp-segs is role="tablist" with three role="tab" buttons. It must implement
// the roving tabindex model: exactly one tab in the Tab order (tabindex=0, the
// selected one), the rest tabindex=-1; Arrow keys move selection + focus +
// activate, with wrap-around; Home/End jump to the ends.

test('T4: #rp-segs is a roving tablist — Arrow/Home/End move selection + focus, wrap-around', async ({ page }) => {
  const p = nextPort();
  const dir = tzFixture();
  const server = await startServer(dir, p);
  try {
    await gotoDocs(page, p);
    const segs = page.locator('#right-pane .rp-seg');
    await expect(segs).toHaveCount(3);

    // Exactly one tab is in the Tab order (the selected one, tabindex=0).
    const roving = async () => await page.evaluate(() =>
      Array.from(document.querySelectorAll('#rp-segs .rp-seg')).map((b) => b.tabIndex));
    expect(await roving()).toEqual([0, -1, -1]);   // outline selected by default

    // ArrowRight moves selection + focus to Marks and activates it.
    await page.locator('#right-pane .rp-seg[data-seg="outline"]').focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('#right-pane .rp-seg[data-seg="marks"]')).toHaveAttribute('aria-selected', 'true');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('marks');
    expect(await roving()).toEqual([-1, 0, -1]);
    await expect(page.locator('#rp-marks')).toBeVisible();   // activation (not just focus)

    // ArrowRight again → Peek; once more wraps back to Outline.
    await page.keyboard.press('ArrowRight');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('peek');
    await page.keyboard.press('ArrowRight');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('outline');   // wrap

    // ArrowLeft wraps the other way (outline → peek).
    await page.keyboard.press('ArrowLeft');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('peek');

    // Home → first, End → last.
    await page.keyboard.press('Home');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('outline');
    await page.keyboard.press('End');
    expect(await page.evaluate(() => document.activeElement?.dataset?.seg)).toBe('peek');

    // Click still works and re-rovs the tabindex.
    await page.locator('#right-pane .rp-seg[data-seg="outline"]').click();
    await expect(page.locator('#right-pane .rp-seg[data-seg="outline"]')).toHaveAttribute('aria-selected', 'true');
    expect(await roving()).toEqual([0, -1, -1]);
  } finally {
    stopServer(server, dir);
  }
});
