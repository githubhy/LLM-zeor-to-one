// @ts-check
// Tombstone lifecycle e2e (Plan 03, Task 5).
//   - A `deleted: true` sidecar highlight is NOT painted at render and is
//     absent from the Highlights tab, while a live sibling paints + lists.
//   - A PUT containing a `deleted: true` highlight round-trips: serve.js's
//     normalizeAnnotationDoc retains the tombstone (so a desktop save cannot
//     silently strip it), and `updatedAt` survives too.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, seedAnnotations, startServer, stopServer } = require('./helpers/server');

let portCounter = 4810;
function nextPort() { return portCounter++; }

// ─────────────────────────────────────────────────────────────────────────────
// 1) Seed a sidecar with one live highlight and one tombstone. The live one
//    paints + lists; the tombstone neither paints nor lists.
// ─────────────────────────────────────────────────────────────────────────────
test('tombstoned sidecar highlight is filtered at render and in the Highlights tab', async ({ page }) => {
  const port = nextPort();
  // Two paragraphs on distinct source lines so each highlight maps to its own
  // data-source-line block. blockLine is 0-based on the source.
  //   line 0: # Tomb
  //   line 1: (blank)
  //   line 2: live paragraph
  //   line 3: (blank)
  //   line 4: dead paragraph
  const dir = createFixtureDir({
    'tomb.md': '# Tomb\n\nLive paragraph here.\n\nDead paragraph here.\n',
  });
  seedAnnotations(dir, 'tomb.md', {
    file: 'tomb.md',
    documentRevision: null,
    highlights: [
      {
        id: 'live1',
        color: 'yellow',
        excerpt: 'Live paragraph here.',
        segments: [{ blockLine: 2, lineStart: 2, lineEnd: 2, text: 'Live paragraph here.' }],
      },
      {
        id: 'dead1',
        color: 'green',
        deleted: true,
        updatedAt: 1700000000000,
        excerpt: 'Dead paragraph here.',
        segments: [{ blockLine: 4, lineStart: 4, lineEnd: 4, text: 'Dead paragraph here.' }],
      },
    ],
  });
  const server = await startServer(dir, port);

  try {
    await page.goto(`http://localhost:${port}/?file=tomb.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('#content h1')).toHaveText('Tomb');

    // The live highlight paints; the tombstone does not.
    await expect(page.locator('.sidecar-hl[data-sidecar-hit-id="live1"]')).toHaveCount(1);
    await expect(page.locator('[data-sidecar-hit-id="dead1"]')).toHaveCount(0);

    // Highlights tab lists only the live one. The tab populates async after
    // the switch — assert with the auto-waiting form, not an immediate
    // allInnerTexts() snapshot (flake: bug 2026-06-12-03).
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator('#highlights-list')).toBeVisible();
    await expect(page.locator('.hl-entry .hl-entry-text')).toHaveText(['Live paragraph here.']);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// 2) Round-trip the normalize: PUT a doc carrying a tombstone, GET it back,
//    assert the tombstone (and its updatedAt) survived serve.js normalize.
// ─────────────────────────────────────────────────────────────────────────────
test('PUT of a tombstoned highlight round-trips through serve.js normalize', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'rt.md': '# RT\n\nRound-trip body text.\n',
  });
  const server = await startServer(dir, port);

  try {
    // Initial GET to grab the current annotations ETag + document revision.
    const getRes = await request.get(`http://localhost:${port}/api/highlights/rt.md`);
    expect(getRes.ok()).toBe(true);
    const ifMatch = getRes.headers()['etag'];
    const docRevision = getRes.headers()['x-document-revision'];
    expect(ifMatch).toBeTruthy();

    const putBody = {
      version: 1,
      file: 'rt.md',
      documentRevision: docRevision || null,
      highlights: [
        {
          id: 'keep1',
          color: 'yellow',
          excerpt: 'kept',
          updatedAt: 111,
          segments: [{ blockLine: 2, lineStart: 2, lineEnd: 2 }],
        },
        {
          id: 'gone1',
          color: 'green',
          excerpt: 'gone',
          deleted: true,
          updatedAt: 222,
          segments: [{ blockLine: 2, lineStart: 2, lineEnd: 2 }],
        },
      ],
    };
    const putRes = await request.put(`http://localhost:${port}/api/highlights/rt.md`, {
      headers: {
        'Content-Type': 'application/json',
        'If-Match': ifMatch,
        'X-Document-Revision': docRevision || '',
      },
      data: JSON.stringify(putBody),
    });
    expect(putRes.status()).toBe(204);

    // GET it back: the tombstone must have survived normalize, with updatedAt.
    const back = await request.get(`http://localhost:${port}/api/highlights/rt.md`);
    expect(back.ok()).toBe(true);
    const doc = await back.json();
    const byId = Object.fromEntries(doc.highlights.map((h) => [h.id, h]));

    expect(byId.keep1).toBeTruthy();
    expect('deleted' in byId.keep1).toBe(false);
    expect(byId.keep1.updatedAt).toBe(111);

    expect(byId.gone1).toBeTruthy();
    expect(byId.gone1.deleted).toBe(true);
    expect(byId.gone1.updatedAt).toBe(222);
  } finally {
    stopServer(server, dir);
  }
});
