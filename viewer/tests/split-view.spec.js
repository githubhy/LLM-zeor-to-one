// @ts-check
// Redesign 07: split-view secondary reference pane. At wide desktop width
// (≥1440px) Pane B (#content-b) opens beside the full-featured Pane A
// (#content) to show a referenced section/file. Pane B is a LIGHT read-only
// pane (no outline scroll-spy, no sidenotes, no progress); Pane A keeps all of
// T1–T7 unchanged. Port base 7340 — clear of three-zone (7300) and palette.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { seedSettings } = require('./helpers/layout');

let port = 7340;
const nextPort = () => port++;

// The product accepts BOTH Ctrl-click and Cmd-click to open split (handler
// tests `e.ctrlKey || e.metaKey`). On macOS, Ctrl-click is the OS context-menu
// gesture and Playwright does not deliver it as a left-click-with-ctrlKey, so
// the cross-platform-reliable modifier in tests is Meta (Cmd) — the native
// macOS chord. Real users on Windows/Linux get Ctrl-click for free.
const SPLIT_MOD = ['Meta'];

// A doc with a cross-ref equation link plus several headings so both the
// "open current section" command and a ctrl-click cross-ref have a target.
const DOC = `# Split Doc

Intro paragraph. The slope-intercept form is equation [(1)](#eq-1) below.

<a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

## Section Alpha

Body under Alpha referencing equation [(1)](#eq-1) again.

${'Filler paragraph for Alpha.\n\n'.repeat(20)}

## Section Beta

Body under Beta with inline math $z = a t^2$ for fidelity checking.

${'Filler paragraph for Beta.\n\n'.repeat(20)}
`;

function fixture() { return createFixtureDir({ 'doc.md': DOC }); }

// ── Open via palette command ────────────────────────────────────────────────

test('palette "Open … split" opens #content-b beside #content at ≥1440px', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    await expect(page.locator('#content-b')).toBeHidden();

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    const row = page.locator('#cmd-results .pal-item', { hasText: 'split' });
    await expect(row.first()).toBeVisible();
    await row.first().click();

    // Pane B is visible beside Pane A; both are on screen and side-by-side.
    await expect(page.locator('#content-b')).toBeVisible();
    await expect(page.locator('#content')).toBeVisible();
    const boxes = await page.evaluate(() => {
      const a = document.getElementById('content').getBoundingClientRect();
      const b = document.getElementById('content-b').getBoundingClientRect();
      return { aRight: a.right, bLeft: b.left, bHasContent: !!document.querySelector('#content-b .cb-body h1, #content-b .cb-body h2') };
    });
    // Pane B sits to the right of Pane A (side-by-side, not overlapping).
    expect(boxes.bLeft).toBeGreaterThanOrEqual(boxes.aRight - 2);
    // Pane B rendered the file's markdown (headings present).
    expect(boxes.bHasContent).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

// ── Open via Ctrl/Cmd-click on a cross-ref ──────────────────────────────────

test('Ctrl-click on a same-file cross-ref opens the target in split', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    await expect(page.locator('#content-b')).toBeHidden();

    // Modifier-click must NOT open the floating peek; it opens Pane B instead.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await expect(page.locator('#peek-popover')).toBeHidden();
    // The rendered equation is present in Pane B (KaTeX rendered).
    await expect(page.locator('#content-b .cb-body .katex').first()).toBeVisible();
  } finally {
    stopServer(server, dir);
  }
});

// ── Esc closes Pane B first; close restores Pane A to full width ────────────

test('Esc closes #content-b first; after close it is hidden and #content is full width', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    const before = await page.evaluate(() => {
      const r = document.getElementById('content').getBoundingClientRect();
      return { width: r.width, right: r.right };
    });

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();
    // Split open: Pane A is confined to the left half (its right edge no longer
    // reaches past the viewport midpoint) and Pane B sits in the right half.
    const split = await page.evaluate(() => {
      const a = document.getElementById('content').getBoundingClientRect();
      const b = document.getElementById('content-b').getBoundingClientRect();
      return { aRight: a.right, bLeft: b.left, vw: window.innerWidth };
    });
    expect(split.aRight).toBeLessThanOrEqual(split.vw / 2 + 2);   // Pane A in left half
    expect(split.bLeft).toBeGreaterThanOrEqual(split.vw / 2 - 2); // Pane B in right half

    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
    // After close Pane A returns to its pre-split geometry (full width again).
    const restored = await page.evaluate(() => {
      const r = document.getElementById('content').getBoundingClientRect();
      return { width: r.width, right: r.right };
    });
    expect(Math.abs(restored.width - before.width)).toBeLessThan(3);
  } finally {
    stopServer(server, dir);
  }
});

test('the per-pane close button dismisses Pane B', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await page.locator('#content-b .cb-close').click();
    await expect(page.locator('#content-b')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

// ── Gate: below 1440px the split command does nothing ───────────────────────

test('at 1200×900 the split command is a no-op (#content-b stays hidden)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1200, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    const row = page.locator('#cmd-results .pal-item', { hasText: 'split' });
    // Either the command is absent, or running it is a no-op — assert the pane
    // never appears. (Run it if present.)
    if (await row.count()) { await row.first().click(); }
    else { await page.keyboard.press('Escape'); }
    await expect(page.locator('#content-b')).toBeHidden();

    // A modifier-click below the gate must fall back to normal navigation/peek,
    // never the split pane.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

// ── Docs mode: split collapses #right-pane, restores it on close ────────────

test('in docs mode opening split hides #right-pane; closing restores it', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    await expect(page.locator('#right-pane')).toBeVisible();

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();
    await expect(page.locator('#right-pane')).toBeHidden();   // collapsed for room

    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
    await expect(page.locator('#right-pane')).toBeVisible();  // restored
  } finally {
    stopServer(server, dir);
  }
});

// ── Modals stay on top of the panes ─────────────────────────────────────────

test('the palette overlays an open split pane', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();

    await page.keyboard.press('Control+k');
    await expect(page.locator('#cmd-palette')).toBeVisible();
    const z = await page.evaluate(() => {
      const pal = parseInt(getComputedStyle(document.getElementById('cmd-palette')).zIndex) || 0;
      const cb = parseInt(getComputedStyle(document.getElementById('content-b')).zIndex) || 0;
      return { pal, cb };
    });
    expect(z.pal).toBeGreaterThan(z.cb);
    expect(z.pal).toBeGreaterThanOrEqual(1200);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #1: closing Pane B restores focus (no strand on <body>) ──

test('closing Pane B (Esc / close button) restores focus away from <body>', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    // Esc path: open via the ref link, focus the close button (inside Pane B),
    // press Esc. Focus must NOT fall to <body>.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await page.locator('#content-b .cb-close').focus();
    expect(await page.evaluate(() => document.activeElement?.id || document.activeElement?.className)).toContain('cb-close');
    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
    const afterEsc = await page.evaluate(() => document.activeElement === document.body || document.activeElement === null);
    expect(afterEsc).toBe(false);

    // Close-button path: same expectation when dismissing via the X.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await page.locator('#content-b .cb-close').click();
    await expect(page.locator('#content-b')).toBeHidden();
    const afterBtn = await page.evaluate(() => document.activeElement === document.body || document.activeElement === null);
    expect(afterBtn).toBe(false);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #6: switching chrome with split open closes Pane B ───────

test('switching chrome (reader↔docs) while split is open closes Pane B', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');
    // Default is reader. Open split, then flip to docs via the palette command.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>toggle immersive');
    await page.locator('#cmd-results .pal-item', { hasText: 'Toggle immersive' }).first().click();

    // The chrome flipped (immersive class cleared → docs) AND Pane B is closed,
    // not left orphaned over the new chrome.
    await expect(page.locator('html')).toHaveAttribute('data-chrome', 'docs');
    await expect(page.locator('#content-b')).toBeHidden();
    await expect(page.locator('#app')).not.toHaveClass(/split-open/);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #16: Pane B .md / external links don't hard-navigate ─────

test('a cross-file .md link in Pane B loads via the SPA (no full navigation)', async ({ page }) => {
  const p = nextPort();
  // Two files: doc.md links to other.md; opening other.md in Pane B and clicking
  // a relative .md link inside it must route through the SPA, not the top frame.
  const dir = createFixtureDir({
    'doc.md': '# Doc A\n\nSee [the other doc](other.md) for details.\n',
    'other.md': '# Doc B\n\nBack to [doc A](doc.md) here.\n',
  });
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=other.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc B');

    // Open Pane B on the current file (other.md) via the palette split command.
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();

    // Sentinel on the live JS context: a full top-frame navigation (the bug)
    // would reload the page and wipe this global. An SPA loadFile() leaves it
    // intact. This is the definitive "the app survived" probe.
    await page.evaluate(() => { window.__navSentinel = true; });

    // Click the relative .md link inside Pane B → should load doc.md into Pane A.
    await page.locator('#content-b .cb-body a[href="doc.md"]').first().click();
    await expect(page.locator('#content h1')).toHaveText('Doc A');
    // Pane B handed the reference back to Pane A and closed.
    await expect(page.locator('#content-b')).toBeHidden();
    // The SPA survived — no hard reload (the sentinel persists).
    expect(await page.evaluate(() => window.__navSentinel === true)).toBe(true);
  } finally {
    stopServer(server, dir);
  }
});

test('an external link in Pane B gets target=_blank/rel=noopener (no in-frame nav)', async ({ page }) => {
  const p = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nExternal [example](https://example.com/x) link.\n',
  });
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc');

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();

    const link = page.locator('#content-b .cb-body a[href="https://example.com/x"]').first();
    // A real click would otherwise navigate the top frame; the handler stamps
    // target=_blank so the browser opens a new tab instead. Assert the stamping
    // happens (dispatch the click handler, then read the attrs).
    await link.dispatchEvent('click');
    await expect(link).toHaveAttribute('target', '_blank');
    await expect(link).toHaveAttribute('rel', 'noopener');
    // The app did not navigate away.
    await expect(page.locator('#content h1')).toHaveText('Doc');
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #3/#9: cheat-sheet takes Esc before the split handler ────

test('Esc closes the cheat-sheet (topmost) before the open split pane', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    // Open split, then open the cheat-sheet on top via the palette '?' path.
    await page.locator('#content a[href="#eq-1"]').first().click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('?');
    await page.locator('#cmd-results .pal-item', { hasText: 'Keyboard shortcuts' }).first().click();
    await expect(page.locator('#shortcut-cheatsheet')).toBeVisible();

    // First Esc closes the cheat-sheet (topmost), NOT the background split.
    await page.keyboard.press('Escape');
    await expect(page.locator('#shortcut-cheatsheet')).toBeHidden();
    await expect(page.locator('#content-b')).toBeVisible();   // split survived
    // Second Esc now closes the split.
    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #20: peek-over-split Esc ordering (decision flip) ────────
// The dismissal order follows z-stacking: an open peek (transient popover, z
// 1050) sits above the split pane (z 50), so Esc dismisses the peek FIRST, then
// a second Esc closes the split — matching the drawer Esc handler, which already
// defers to an open peek. Net order: cheat-sheet > peek > split > drawer.

test('Esc closes an open peek (over the split) before the split pane', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    // Open split via a modifier-click on the cross-ref, then open a (floating)
    // peek over it by plain-clicking the same ref.
    const ref = page.locator('#content a[href="#eq-1"]').first();
    await ref.click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    await ref.click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await expect(page.locator('#content-b')).toBeVisible();   // split still up under the peek

    // First Esc dismisses the PEEK (topmost), not the background split.
    await page.keyboard.press('Escape');
    await expect(page.locator('#peek-popover')).toBeHidden();
    await expect(page.locator('#content-b')).toBeVisible();   // split survived
    // Second Esc (peek gone) now closes the split.
    await page.keyboard.press('Escape');
    await expect(page.locator('#content-b')).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #13: a wide-dragged sidebar must not crush Pane A ────────
// In DOCS chrome at the split gate, Pane A is squeezed between the docked
// sidebar (--sidebar-w, draggable to 600px) and Pane B. A flat 50vw Pane B
// leaves Pane A = 100vw − sidebar − 50vw ≈ 150px at 1500px/600px — unusable.
// Pane B is now capped so Pane A keeps a readable floor and the page never
// overflows horizontally.

test('split + wide-dragged sidebar in docs keeps Pane A readable (no overflow)', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await seedSettings(page, { chrome: 'docs' });
    await page.setViewportSize({ width: 1500, height: 900 });
    // Drag the sidebar to ~its 600px max before load (the resize clamp persists
    // viewer-sidebar-w and the restore path clamps it to MAX_W=600 on boot).
    await page.addInitScript(() => localStorage.setItem('viewer-sidebar-w', '600px'));
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    await page.keyboard.press('Control+k');
    await page.locator('#cmd-input').fill('>split');
    await page.locator('#cmd-results .pal-item', { hasText: 'split' }).first().click();
    await expect(page.locator('#content-b')).toBeVisible();

    const geo = await page.evaluate(() => {
      const a = document.getElementById('content').getBoundingClientRect();
      const sw = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w').trim();
      return {
        aWidth: a.width,
        sidebarW: parseFloat(sw),
        docW: document.documentElement.scrollWidth,
        vw: window.innerWidth,
      };
    });
    // Sidebar really is wide (the clamp restored ~600px), so this is the crush
    // scenario, not a trivially-wide viewport.
    expect(geo.sidebarW).toBeGreaterThanOrEqual(560);
    // Pane A keeps a readable floor (≥360px) instead of collapsing to ~150px.
    expect(geo.aWidth).toBeGreaterThanOrEqual(360);
    // And the page does not overflow horizontally.
    expect(geo.docW).toBeLessThanOrEqual(geo.vw + 1);
  } finally {
    stopServer(server, dir);
  }
});

// ── Review w9d47hl9a #18: Pane B anchor flash re-fires on repeat re-scroll ────
// Re-navigating to an anchor already shown in an open Pane B must re-arm the
// .anchor-highlight landing flash (the same-file re-scroll branch was silent
// before the shared flashAnchor() helper).

test('re-navigating to an anchor in an open Pane B re-adds .anchor-highlight', async ({ page }) => {
  const p = nextPort();
  const dir = fixture();
  const server = await startServer(dir, p);
  try {
    await page.setViewportSize({ width: 1500, height: 900 });
    await page.goto(`http://localhost:${p}/?file=doc.md`);
    await expect(page.locator('#content h1')).toHaveText('Split Doc');

    // Open Pane B on eq-1 via modifier-click (fresh render → flashes once).
    const ref = page.locator('#content a[href="#eq-1"]').first();
    await ref.click({ modifiers: SPLIT_MOD });
    await expect(page.locator('#content-b')).toBeVisible();
    const target = page.locator('#content-b .cb-body #eq-1');
    await expect(target).toHaveCount(1);

    // Let the first flash's 2s animation lapse and strip the class so the
    // re-trigger is unambiguous (the animation auto-removes nothing; we clear
    // it explicitly, then assert the re-scroll re-adds it).
    await page.evaluate(() => {
      const t = document.querySelector('#content-b .cb-body #eq-1');
      if (t) t.classList.remove('anchor-highlight');
    });
    await expect(target).not.toHaveClass(/anchor-highlight/);

    // Re-navigate to the SAME anchor in the already-open pane (the else-if branch
    // in openSplitPane). With flashAnchor() it must re-add the class.
    await ref.click({ modifiers: SPLIT_MOD });
    await expect(target).toHaveClass(/anchor-highlight/);
  } finally {
    stopServer(server, dir);
  }
});
