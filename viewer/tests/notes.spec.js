// @ts-check
// Smoke test: verify the markdown-it-footnote plugin loaded from CDN and
// parses [^id] syntax correctly. A CDN failure or wrong URL would leave
// window.markdownitFootnote undefined, the guard in viewer.js would skip
// silently, and every downstream note feature would silently break.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, seedAnnotations, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 5200;
function nextPort() { return portCounter++; }

// Sidebar pencil / note-card flows need the docked sidebar — pin classic
// layout (see helpers/layout.js).
test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

// ─────────────────────────────────────────────────────────────────────────────
// markdown-it-footnote plugin loads and parses [^id] syntax
// ─────────────────────────────────────────────────────────────────────────────
test('markdown-it-footnote plugin loads and renders footnote syntax', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'fn.md': 'Hello world[^fn1].\n\n[^fn1]: The footnote body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=fn.md`);
    await page.waitForLoadState('networkidle');

    // The inline reference must render as a superscript with class footnote-ref.
    // If the plugin failed to load, [^fn1] is left as literal text and no
    // sup.footnote-ref exists.
    await expect(page.locator('sup.footnote-ref')).toHaveCount(1);

    // The footnote definitions must collect into a section.footnotes block.
    await expect(page.locator('section.footnotes')).toHaveCount(1);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Happy-path: user creates a note on an inline highlight via toolbar popover
// ─────────────────────────────────────────────────────────────────────────────
test('user can create a note on an inline highlight', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'note-fixture.md': '# Test fixture\n\nLead ==yellow:noted== tail.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=note-fixture.md`);
    await page.waitForLoadState('networkidle');

    // Simulate a single click inside the mark by setting a collapsed selection
    // and dispatching mouseup — the same pattern used by highlights.spec.js.
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-yellow');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 2); r.setEnd(tn, 2);   // collapsed inside the mark
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    // Toolbar should be visible in recolor-only mode with the note button.
    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    // Note button is visible for inline highlights.
    await expect(page.locator('.hl-note-btn')).toBeVisible();

    // Click the note button in the toolbar to open the popover.
    await page.locator('.hl-note-btn').click();

    // Fill in the note body and save.
    await page.locator('#note-popover textarea.np-body').fill('this is the body');
    await page.locator('#note-popover .np-save').click();

    // After save, the note is written inline as a footnote reference.
    // The markdown-it-footnote plugin renders [^id] as sup.footnote-ref.
    await expect(page.locator('sup.footnote-ref')).toBeVisible();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Cascade clear: clearing a highlight that has a note strips both the mark
// and the attached [^id] ref + def in one atomic write.
// ─────────────────────────────────────────────────────────────────────────────
test('clearing a highlight also removes its note', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'cascade-fixture.md': '# Test fixture\n\nLead ==yellow:gone==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=cascade-fixture.md`);
    await page.waitForLoadState('networkidle');

    // Simulate a click inside the mark using the same collapsed-selection +
    // mouseup pattern used by the other note tests.
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-yellow');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 2); r.setEnd(tn, 2);   // collapsed inside the mark
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    // Toolbar should be visible (recolor-only for a mark click).
    await expect(page.locator('#hl-toolbar')).toBeVisible();

    // Click the clear button on the toolbar.
    await page.locator('#hl-toolbar .hl-btn-clear').click();
    await page.waitForTimeout(200);

    // The mark must be gone.
    await expect(page.locator('mark.hl-yellow')).toHaveCount(0);
    // The footnote ref must also be gone (cascade delete stripped it).
    await expect(page.locator('sup.footnote-ref')).toHaveCount(0);

    // Undo-restore: the undo toast must be visible; clicking Undo must restore
    // both the highlight mark and the footnote ref.
    await expect(page.locator('#undo-toast.show')).toBeVisible();
    await page.locator('#undo-toast button').click();
    // Wait for the undo PUT to complete and the page to re-render.
    await expect(page.locator('mark.hl-yellow')).toHaveCount(1, { timeout: 5000 });
    await expect(page.locator('sup.footnote-ref')).toHaveCount(1, { timeout: 5000 });
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Delete: user can delete an existing note via popover delete button
// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────
// Sidebar note icon + collapsible body
// ─────────────────────────────────────────────────────────────────────────────
test('sidebar entry shows note marker (✎) and renders markdown body on expand', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'sidebar-fixture.md': '# Test fixture\n\nLead ==yellow:already-noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=sidebar-fixture.md`);
    await page.waitForLoadState('networkidle');

    // Open the Highlights tab via keyboard shortcut.
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();

    // The noted entry must carry the dual class.
    const noted = page.locator('.hl-entry.highlights-entry');
    await expect(noted).toHaveCount(1);

    // Note marker glyph must be visible (the slim ✎ in default 'icon' mode).
    const icon = noted.locator('.hl-note-icon');
    await expect(icon).toBeVisible();
    await expect(icon).toHaveText('✎');

    // Note body must be collapsed initially (CSS hides it).
    const noteBody = noted.locator('.hl-note-body');
    await expect(noteBody).toBeHidden();

    // Click the icon to expand.
    await icon.click();
    await expect(noteBody).toBeVisible();

    // Rendered content must contain the note body text.
    await expect(noteBody).toContainText('existing note body');

    // Edit button must be visible in expanded state.
    await expect(noted.locator('.hl-note-edit')).toBeVisible();

    // Clicking icon again collapses the body.
    await icon.click();
    await expect(noteBody).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});

test('clicking sidebar pencil opens popover pre-filled with body', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'pencil-fixture.md': '# Test fixture\n\nLead ==yellow:already-noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=pencil-fixture.md`);
    await page.waitForLoadState('networkidle');
    // Open the highlights tab
    await page.locator('button.sidebar-tab[data-tab="highlights"]').click();
    // Expand the noted entry by clicking the icon
    await page.locator('.highlights-entry .hl-note-icon').click();
    // Click the edit pencil
    await page.locator('.highlights-entry .hl-note-edit').click();
    // Popover opens, textarea pre-filled
    const textarea = page.locator('#note-popover textarea.np-body');
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveValue('existing note body.');
  } finally {
    stopServer(server, dir);
  }
});

test('user can delete a note via popover', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'note-with-existing.md': '# Test fixture\n\nLead ==yellow:already-noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=note-with-existing.md`);
    await page.waitForLoadState('networkidle');

    // Simulate a click inside the mark using the same collapsed-selection +
    // mouseup pattern as the create-note test above.
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-yellow');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 2); r.setEnd(tn, 2);   // collapsed inside the mark
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await page.waitForTimeout(50);

    // Toolbar should be visible in recolor-only mode with the note button.
    await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
    await expect(page.locator('.hl-note-btn')).toBeVisible();

    // Open the note popover (existing note → edit mode).
    await page.locator('.hl-note-btn').click();

    // Accept the confirm() dialog that deleteNoteFromPopover shows.
    page.once('dialog', d => d.accept());

    // Click the delete button.
    await page.locator('#note-popover .np-delete').click();

    // After deletion the footnote reference must be gone.
    await expect(page.locator('sup.footnote-ref')).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Task 20: clicking a [^note-*] footnote ref in the rendered prose switches
// the sidebar to Highlights, scrolls to the matching entry, expands it, and
// flashes it.
// ─────────────────────────────────────────────────────────────────────────────
test('clicking footnote ref scrolls sidebar to note entry', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'ref-click-fixture.md': '# Test fixture\n\nLead ==yellow:noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=ref-click-fixture.md`);
    await page.waitForLoadState('networkidle');
    // Click the footnote ref superscript in the main content area.
    await page.locator('sup.footnote-ref a').first().click();
    // Sidebar Highlights tab must now be active.
    await expect(page.locator('button.sidebar-tab[data-tab="highlights"].active')).toBeVisible();
    // The noted row must be expanded.
    const row = page.locator('.highlights-entry.hl-note-expanded');
    await expect(row).toBeVisible();
    // The note body must contain the note text (lazy-rendered).
    await expect(row.locator('.hl-note-body')).toContainText('existing note body');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Task 21: hovering a [^note-*] footnote ref for ~250 ms shows a tooltip
// preview with the first ~120 chars of the note body.
// ─────────────────────────────────────────────────────────────────────────────
test('hovering footnote ref shows tooltip preview', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'tooltip-fixture.md': '# Test fixture\n\nLead ==yellow:noted==[^note-test-fixture-1] tail.\n\n[^note-test-fixture-1]: existing note body for tooltip.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=tooltip-fixture.md`);
    await page.waitForLoadState('networkidle');
    await page.locator('sup.footnote-ref a').first().hover();
    await page.waitForTimeout(350);
    await expect(page.locator('.note-ref-tooltip.visible')).toBeVisible();
    await expect(page.locator('.note-ref-tooltip')).toContainText('existing note body for tooltip');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Task 23: multi-note same-section id allocation
// Adding notes to multiple highlights in the same section yields unique
// sequential ids: note-<section-slug>-1, -2, -3, ...
// ─────────────────────────────────────────────────────────────────────────────
test('adding notes to multiple highlights in same section gets unique sequential ids', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'multi-note.md': '# Multi-note section\n\nFirst ==yellow:hl-1==[^note-multi-note-section-1] and second ==yellow:hl-2== and third ==yellow:hl-3==.\n\n[^note-multi-note-section-1]: existing first note.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=multi-note.md`);
    await page.waitForLoadState('networkidle');
    const marks = page.locator('mark.hl-yellow');
    // Helper: click inside the Nth mark (0-based) and wait for the toolbar
    // to appear in recolor-only mode. Uses the same collapsed-selection +
    // document.mouseup pattern as the other note tests so that
    // handleSelectionGesture sees sel.anchorNode inside the correct mark.
    async function clickMark(n) {
      await page.evaluate((idx) => {
        const allMarks = document.querySelectorAll('mark.hl-yellow');
        const mk = allMarks[idx];
        const tn = mk.firstChild;
        const sel = window.getSelection();
        sel.removeAllRanges();
        const r = document.createRange();
        r.setStart(tn, 2); r.setEnd(tn, 2);   // collapsed inside the mark
        sel.addRange(r);
        const rect = mk.getBoundingClientRect();
        document.dispatchEvent(new MouseEvent('mouseup', {
          clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
        }));
      }, n);
      // Wait for the 10 ms setTimeout inside handleSelectionGesture to fire
      // and for the toolbar to become visible before returning.
      await expect(page.locator('#hl-toolbar.visible')).toBeVisible({ timeout: 3000 });
    }

    // Add note to second highlight (currently no note).
    {
      await clickMark(1);
      await expect(page.locator('.hl-note-btn')).toBeVisible({ timeout: 3000 });
      await page.locator('.hl-note-btn').click();
      await expect(page.locator('#note-popover textarea.np-body')).toBeVisible({ timeout: 3000 });
      await page.locator('#note-popover textarea.np-body').fill('second note');
      await page.locator('#note-popover .np-save').click();
      // Wait for save round-trip and re-render: the undo toast signals completion.
      await expect(page.locator('#undo-toast.show')).toBeVisible({ timeout: 5000 });
      // Wait past any pending requestAnimationFrame scroll-restore that renderToContent
      // queues after applyLocalSourceUpdate. If that RAF fires while savedMarkEl is set
      // from the next clickMark's 10 ms timeout, the resulting scroll event calls
      // hideToolbar() and clears savedMarkEl before the note button is clicked.
      // 50 ms comfortably outlasts one animation frame (~16 ms) plus the 10 ms timeout.
      await page.waitForTimeout(50);
    }
    // Add note to third highlight (currently no note)
    {
      await clickMark(2);
      await expect(page.locator('.hl-note-btn')).toBeVisible({ timeout: 3000 });
      await page.locator('.hl-note-btn').click();
      await expect(page.locator('#note-popover textarea.np-body')).toBeVisible({ timeout: 3000 });
      await page.locator('#note-popover textarea.np-body').fill('third note');
      await page.locator('#note-popover .np-save').click();
      await expect(page.locator('#undo-toast.show')).toBeVisible({ timeout: 5000 });
    }
    // Verify three distinct refs render
    await expect(page.locator('sup.footnote-ref')).toHaveCount(3);
    // Verify sidebar shows 3 noted entries
    await page.locator('button.sidebar-tab[data-tab="highlights"]').click();
    await expect(page.locator('.highlights-entry .hl-note-icon')).toHaveCount(3);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Task 24: math in note body — raw in popover textarea, KaTeX in sidebar body
// ─────────────────────────────────────────────────────────────────────────────
test('note body with math renders KaTeX in sidebar, raw in popover', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'note-with-math.md': '# Math test\n\nLead ==yellow:noted== tail.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=note-with-math.md`);
    await page.waitForLoadState('networkidle');

    // Click inside the mark using the same collapsed-selection + mouseup pattern
    // as the other notes tests so handleSelectionGesture sees the click correctly.
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    await page.evaluate(() => {
      const mk = document.querySelector('mark.hl-yellow');
      const tn = mk.firstChild;
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(tn, 2); r.setEnd(tn, 2);   // collapsed inside the mark
      sel.addRange(r);
      const rect = mk.getBoundingClientRect();
      document.dispatchEvent(new MouseEvent('mouseup', {
        clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
      }));
    });
    await expect(page.locator('#hl-toolbar.visible')).toBeVisible({ timeout: 3000 });

    // Open note popover via note button.
    await page.locator('.hl-note-btn').click();

    // Fill the body with inline math and save.
    await page.locator('#note-popover textarea.np-body').fill('See $\\sigma_n$ value.');

    // Popover textarea shows raw markdown (textarea is plain text only).
    await expect(page.locator('#note-popover textarea.np-body')).toHaveValue('See $\\sigma_n$ value.');
    // No KaTeX rendered inside the popover — textarea cannot render math.
    await expect(page.locator('#note-popover .katex')).toHaveCount(0);

    // Save the note.
    await page.locator('#note-popover .np-save').click();
    await expect(page.locator('#undo-toast.show')).toBeVisible({ timeout: 5000 });

    // Open sidebar Highlights tab.
    await page.locator('button.sidebar-tab[data-tab="highlights"]').click();

    // Expand the noted entry by clicking the note icon.
    await page.locator('.highlights-entry .hl-note-icon').click();

    // KaTeX must render inside the expanded note body (sidebar uses md.render).
    await expect(page.locator('.highlights-entry .hl-note-body .katex')).toBeVisible();
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Task 22: clicking a sidecar-painted block shows toolbar but hides note button
// (Q1=(a): sidecar highlights cannot have notes in v1)
// ─────────────────────────────────────────────────────────────────────────────
test('toolbar hides note button on sidecar highlights', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'sidecar-fixture.md': '# Test fixture\n\nsidecar painted text only.\n',
  });
  // Seed the sidecar annotation JSON before booting the server.
  // blockLine: 2 targets the paragraph on source line 2 (0-based).
  seedAnnotations(dir, 'sidecar-fixture.md', {
    file: 'sidecar-fixture.md',
    documentRevision: null,
    highlights: [{
      id: 'sidecar:test-1',
      color: 'yellow',
      excerpt: 'sidecar painted text only.',
      segments: [{ blockLine: 2, text: 'sidecar painted text only.' }],
    }],
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=sidecar-fixture.md`);
    await page.waitForLoadState('networkidle');

    // The sidecar painting must have produced at least one [data-sidecar-hit-id]
    // element. If not, the fixture or segment schema is mismatched.
    const sidecarHit = page.locator('[data-sidecar-hit-id]').first();
    const box = await sidecarHit.boundingBox();
    if (!box) {
      throw new Error('Sidecar hit element not painted — check fixture/server schema');
    }

    // Simulate a collapsed selection inside the painted block and dispatch
    // mouseup — the same gesture pattern used by the other notes tests.
    await page.evaluate(({ x, y }) => {
      const el = document.elementFromPoint(x, y);
      const sel = window.getSelection();
      sel.removeAllRanges();
      const r = document.createRange();
      r.setStart(el, 0);
      r.collapse(true);
      sel.addRange(r);
      document.dispatchEvent(new MouseEvent('mouseup', {
        bubbles: true, clientX: x, clientY: y,
      }));
    }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
    await page.waitForTimeout(50);

    // Toolbar must appear (sidecar click enters the recolor-only branch).
    await expect(page.locator('#hl-toolbar.visible')).toBeVisible();

    // Note button must be hidden — Task 14 sets display:none in the sidecar branch.
    const noteBtn = page.locator('.hl-note-btn');
    await expect(noteBtn).toBeHidden();
  } finally {
    stopServer(server, dir);
  }
});
