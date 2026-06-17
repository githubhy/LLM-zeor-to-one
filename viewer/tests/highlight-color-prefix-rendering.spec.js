// @ts-check
// Regression: `==color: text==` highlights must render as a coloured <mark>
// with the `color:` prefix stripped — not as literal `==color:` / `==` text.
//
// Bug 2026-05-20-01 (user-spotted at surveys/5g-nr-ldpc/fundamentals.md §3.7.3)
// was NOT a viewer-pipeline defect. The offending source had IMPROPERLY-NESTED
// (crossing) delimiters — `**==purple: lead.** rest==` — i.e. a `**` bold pair
// that OPENS before the `==` mark-open and CLOSES inside the mark. markdown-it-
// mark (correctly, per CommonMark, exactly like GitHub) refuses to form a
// <mark> across a strong-emphasis pair, so the `==` markers survived literally.
//
// The fix nested the highlight OUTSIDE the bold (`==purple: **lead.** rest==`).
// These tests pin: (1) valid `==color:==` shapes render as hl-<color> marks;
// (2) the crossing shape is the invalid pattern that renders literally — so a
// future markdown-it-mark version change (or a re-introduced crossing source
// line) is caught.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4972;
function nextPort() { return portCounter++; }

async function renderFixture(page, name, body) {
  const port = nextPort();
  const dir = createFixtureDir({ [name]: `# Doc\n\n${body}\n` });
  const server = await startServer(dir, port);
  await page.goto(`http://localhost:${port}?file=${name}`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { server, dir };
}

test('plain ==color: text== renders as a coloured mark with prefix stripped', async ({ page }) => {
  const ctx = await renderFixture(page, 'plain.md', '==purple: plain highlighted text==');
  try {
    const mark = page.locator('#content mark.hl-purple');
    await expect(mark).toHaveCount(1);
    await expect(mark).toHaveText('plain highlighted text');
    const text = await page.locator('#content').innerText();
    expect(text).not.toContain('==purple:');
    expect(text).not.toMatch(/==/);
  } finally {
    stopServer(ctx.server, ctx.dir);
  }
});

test('==color: **bold** rest== (mark wraps bold) renders correctly — the L464 fix shape', async ({ page }) => {
  // This is the exact shape fundamentals.md §3.7.3 was corrected to.
  const ctx = await renderFixture(
    page, 'fix.md',
    '- ==purple: **Algorithm comparison.** EXIT charts narrow the tunnel relative to BP. The SCMS curve tracks BP, near-optimal.=='
  );
  try {
    const mark = page.locator('#content li mark.hl-purple');
    await expect(mark).toHaveCount(1);
    // Bold lead-in is nested inside the mark.
    await expect(mark.locator('strong')).toHaveText('Algorithm comparison.');
    const text = await page.locator('#content').innerText();
    expect(text).not.toContain('==purple:');
    expect(text).not.toMatch(/==/);
  } finally {
    stopServer(ctx.server, ctx.dir);
  }
});

test('==color: text with $math$== renders the mark and the math, no literal markers', async ({ page }) => {
  const ctx = await renderFixture(
    page, 'math.md',
    'Prose. ==purple: The curve is shifted by the factor $\\alpha$ here.=='
  );
  try {
    const mark = page.locator('#content mark.hl-purple');
    await expect(mark).toHaveCount(1);
    await expect(mark.locator('.katex')).toHaveCount(1);
    const text = await page.locator('#content').innerText();
    expect(text).not.toContain('==purple:');
    expect(text).not.toContain('$\\alpha$');
  } finally {
    stopServer(ctx.server, ctx.dir);
  }
});

test('crossing **==color: lead.** rest== is the invalid pattern — renders literally (root-cause guard)', async ({ page }) => {
  // Documents WHY the source had to be nested. If markdown-it-mark ever starts
  // forming a <mark> here (a behaviour change), this assertion flips and alerts us.
  const ctx = await renderFixture(
    page, 'crossing.md',
    '- **==purple: Algorithm comparison.** EXIT charts narrow the tunnel.=='
  );
  try {
    // No coloured mark is formed across the bold pair...
    await expect(page.locator('#content mark.hl-purple')).toHaveCount(0);
    // ...and the literal markers survive in the rendered text.
    const text = await page.locator('#content').innerText();
    expect(text).toContain('==purple:');
  } finally {
    stopServer(ctx.server, ctx.dir);
  }
});
