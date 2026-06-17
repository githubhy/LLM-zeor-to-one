// @ts-check
// Regression suite for bugs/2026-05-19-03: recoloring an inline highlight
// whose source contains a link / `code` / $math$ / refs used to fail
// silently — `recolorMarkEl` built a regex from the mark's *rendered*
// textContent and could not relocate the raw `==color:…==` span, so the
// swatch click no-op'd with an easy-to-miss toast. The fix routes recolor
// through findInlineEntryAtMark → ViewerNoteMutation.recolorHighlight
// (authoritative source offsets), the same path clearMarkEl already uses.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4800;
function nextPort() { return portCounter++; }

// Single collapsed click inside `mark.<cls>` to raise the recolor toolbar,
// mirroring the gesture in highlights.spec.js.
async function clickInsideMark(page, cls) {
  await page.evaluate((sel) => {
    const mk = document.querySelector(sel);
    const tn = mk.firstChild;
    const sel2 = window.getSelection();
    sel2.removeAllRanges();
    const r = document.createRange();
    r.setStart(tn, 2); r.setEnd(tn, 2);
    sel2.addRange(r);
    const rect = mk.getBoundingClientRect();
    document.dispatchEvent(new MouseEvent('mouseup', {
      clientX: rect.left + 5, clientY: rect.top + 5, bubbles: true,
    }));
  }, `mark.${cls}`);
  await expect(page.locator('#hl-toolbar')).toHaveClass(/recolor-only/);
}

test('recolor a highlight wrapping a markdown link (inner preserved)', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Doc\n\nIntro ==yellow: see [the docs](https://example.com/p?x=1&y=2) here== end.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    // Mark renders with the link inside it; rendered text ≠ raw source.
    await expect(page.locator('mark.hl-yellow')).toBeVisible();
    await expect(page.locator('mark.hl-yellow a')).toHaveText('the docs');

    await clickInsideMark(page, 'hl-yellow');
    await page.locator('#hl-toolbar .hl-swatch[data-action="green"]').click();

    // Source rewritten with the color swapped and the link byte-identical.
    await expect.poll(async () => {
      const res = await request.get(`http://localhost:${port}/api/md/doc.md`);
      return res.text();
    }).toContain('==green: see [the docs](https://example.com/p?x=1&y=2) here==');
    const finalTxt = await (await request.get(`http://localhost:${port}/api/md/doc.md`)).text();
    expect(finalTxt).not.toContain('==yellow:');

    // DOM reflects the new color, link still intact.
    await expect(page.locator('mark.hl-green a')).toHaveText('the docs');
  } finally {
    stopServer(server, dir);
  }
});

test('recolor a highlight wrapping inline code and math (inner preserved)', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Doc\n\nRun ==yellow: call `init()` then $E=mc^2$ done== now.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('mark.hl-yellow code')).toHaveText('init()');

    await clickInsideMark(page, 'hl-yellow');
    await page.locator('#hl-toolbar .hl-swatch[data-action="red"]').click();

    await expect.poll(async () => {
      const res = await request.get(`http://localhost:${port}/api/md/doc.md`);
      return res.text();
    }).toContain('==red: call `init()` then $E=mc^2$ done==');
    const finalTxt = await (await request.get(`http://localhost:${port}/api/md/doc.md`)).text();
    expect(finalTxt).not.toContain('==yellow:');
    await expect(page.locator('mark.hl-red code')).toHaveText('init()');
  } finally {
    stopServer(server, dir);
  }
});

test('recolor a highlight with an absorbed note ref keeps the ref + def', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md':
      '# Doc\n\nP ==yellow: noted [link](http://x) bit==[^note-top-1] q.\n\n[^note-top-1]: the body.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('mark.hl-yellow')).toBeVisible();

    await clickInsideMark(page, 'hl-yellow');
    await page.locator('#hl-toolbar .hl-swatch[data-action="blue"]').click();

    await expect.poll(async () => {
      const res = await request.get(`http://localhost:${port}/api/md/doc.md`);
      return res.text();
    }).toContain('==blue: noted [link](http://x) bit==[^note-top-1]');
    const finalTxt = await (await request.get(`http://localhost:${port}/api/md/doc.md`)).text();
    expect(finalTxt).toContain('[^note-top-1]: the body.');
    expect(finalTxt).not.toContain('==yellow:');
  } finally {
    stopServer(server, dir);
  }
});

// Control: the common plain-text case must still work (fast path must not
// regress what the regex pipeline handled).
test('recolor a plain-text highlight still works (no regression)', async ({ page, request }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'doc.md': '# Doc\n\nLook ==green: target word== here.\n',
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=doc.md`);
    await expect(page.locator('mark.hl-green')).toHaveText('target word');

    await clickInsideMark(page, 'hl-green');
    await page.locator('#hl-toolbar .hl-swatch[data-action="purple"]').click();

    await expect.poll(async () => {
      const res = await request.get(`http://localhost:${port}/api/md/doc.md`);
      return res.text();
    }).toContain('==purple: target word==');
  } finally {
    stopServer(server, dir);
  }
});
