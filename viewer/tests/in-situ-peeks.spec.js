// @ts-check
// Redesign 06: in-situ peeks. Hover (300ms) / click / tap a same-file eq/ref/sec
// reference link opens an anchored popover (#peek-popover, z 1050) with the
// target content, a Go-to affordance, one-at-a-time, dismiss on Esc/outside/scroll.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

// Port base 6500 — clear of every existing spec (6000 = X11 unsafe; 6300 = palette).
let portCounter = 6500;
function nextPort() { return portCounter++; }

const DOC = `# Peek Doc

The line equation <a id="eq-1"></a>

$$
y = m x + b \\tag{1}
$$

is referenced here: see equation [(1)](#eq-1) for the slope-intercept form.
${'Filler paragraph to make the page scrollable.\n\n'.repeat(40)}
`;

async function boot(page, port, files = { 'doc.md': DOC }) {
  const dir = createFixtureDir(files);
  const server = await startServer(dir, port);
  await page.goto(`http://localhost:${port}?file=doc.md`);
  await expect(page.locator('#content h1')).toBeVisible();
  return { dir, server };
}

// ── Task 2: shell + equation peek (rendered) + dismiss + go-to ──────────────

test('clicking an equation ref opens a peek with the rendered equation', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await expect(page.locator('#peek-popover')).toBeHidden();
    await page.locator('#content a[href="#eq-1"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await expect(page.locator('#peek-popover .katex')).toBeVisible();   // equation rendered
  } finally { await stopServer(server); }
});

test('the peek Go-to button jumps to the target and dismisses', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#content a[href="#eq-1"]').click();
    await page.locator('#peek-goto').click();
    await expect(page.locator('#peek-popover')).toBeHidden();
    await expect(page).toHaveURL(/#eq-1$/);
  } finally { await stopServer(server); }
});

test('peek dismisses on Esc, outside-click, and scroll; one at a time', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    const ref = page.locator('#content a[href="#eq-1"]');
    await ref.click(); await expect(page.locator('#peek-popover')).toBeVisible();
    await page.keyboard.press('Escape'); await expect(page.locator('#peek-popover')).toBeHidden();
    await ref.click(); await expect(page.locator('#peek-popover')).toBeVisible();
    await page.locator('#content h1').click(); await expect(page.locator('#peek-popover')).toBeHidden();
    await ref.click(); await expect(page.locator('#peek-popover')).toBeVisible();
    await page.mouse.wheel(0, 400); await expect(page.locator('#peek-popover')).toBeHidden();
  } finally { await stopServer(server); }
});

// ── Task 3: lazy-pending equation peek (non-disturbance) ────────────────────

test('lazy-pending equation peeks from the store without rendering the page copy', async ({ page }) => {
  const port = nextPort();
  // 90 display-math blocks → lazy threshold (80) engaged. eq-90 lives far below
  // the fold; its ref sits at the top and is never scrolled into view.
  let md = '# Lazy Peek\n\nSee the last equation [(90)](#eq-90).\n\n';
  for (let i = 1; i <= 90; i++) {
    md += `Para ${i}.\n\n<a id="eq-${i}"></a>\n\n$$\nz_{${i}} = ${i} \\tag{${i}}\n$$\n\n`;
  }
  const { server } = await boot(page, port, { 'doc.md': md });
  try {
    // The deep target must still be a pending placeholder (never scrolled to).
    await expect(page.locator('#content [data-math-block][data-math-pending]')).not.toHaveCount(0);
    const targetBlock = page.locator('#content [data-math-block]').last();
    await expect(targetBlock).toHaveAttribute('data-math-pending', '1');
    await page.locator('#content a[href="#eq-90"]').click();
    await expect(page.locator('#peek-popover .katex')).toBeVisible();         // popover rendered
    await expect(targetBlock).toHaveAttribute('data-math-pending', '1');       // page copy UNDISTURBED
  } finally { await stopServer(server); }
});

// ── Task 4: citation (#ref) and section (#sec) peeks ────────────────────────

const DOC_RS = `# RS Doc

Body cites reference [[1]](#ref-1) and points to [§2](#sec-2).

## <a id="sec-2"></a>2 Methods

This is the first paragraph of the Methods section, the peek preview text.

More Methods detail in a second paragraph.

## References

<a id="ref-1"></a>
[1] Smith, J. Example Paper. Journal of Examples, 2020. [paper](https://example.com/p).
`;

test('citation ref peek shows the reference entry with a clickable link', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': DOC_RS });
  try {
    await page.locator('#content a[href="#ref-1"]').click();
    const peek = page.locator('#peek-popover');
    await expect(peek).toBeVisible();
    await expect(peek).toContainText('Smith, J. Example Paper');
    await expect(peek.locator('a[href="https://example.com/p"]')).toHaveAttribute('target', '_blank');
  } finally { await stopServer(server); }
});

test('section ref peek shows the heading and its first paragraph only', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port, { 'doc.md': DOC_RS });
  try {
    await page.locator('#content a[href="#sec-2"]').click();
    const peek = page.locator('#peek-popover');
    await expect(peek).toBeVisible();
    await expect(peek).toContainText('Methods');
    await expect(peek).toContainText('first paragraph of the Methods');
    await expect(peek).not.toContainText('second paragraph');               // first para only
  } finally { await stopServer(server); }
});

// ── Task 5: hover-intent, cross-file skip, nested-ref navigate ──────────────

test('hover opens the peek after the intent delay', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);                  // DOC with eq-1
  try {
    await page.locator('#content a[href="#eq-1"]').hover();
    await expect(page.locator('#peek-popover')).toBeVisible({ timeout: 2000 });  // ~300ms intent
  } finally { await stopServer(server); }
});

test('cross-file refs navigate (no peek)', async ({ page }) => {
  const port = nextPort();
  const docs = {
    'a.md': '# Doc A\n\nGo to [(5)](b.md#eq-5) in B.\n',
    'b.md': '# Doc B\n\n<a id="eq-5"></a>\n\n$$\nq = 5 \\tag{5}\n$$\n',
  };
  const dir = createFixtureDir(docs);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}?file=a.md`);
    await expect(page.locator('#content h1')).toHaveText('Doc A');
    await page.locator('#content a[href="b.md#eq-5"]').click();
    await expect(page.locator('#peek-popover')).toBeHidden();
    await expect(page.locator('#content h1')).toHaveText('Doc B');            // navigated
  } finally { await stopServer(server); }
});

test('a ref-link inside a peek navigates instead of nesting', async ({ page }) => {
  const port = nextPort();
  const md = `# Nest Doc

Jump via [§2](#sec-2).

## <a id="sec-2"></a>2 Methods

First paragraph references [(1)](#eq-1) inline.

<a id="eq-1"></a>

$$
y = 1 \\tag{1}
$$
`;
  const { server } = await boot(page, port, { 'doc.md': md });
  try {
    await page.locator('#content a[href="#sec-2"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await page.locator('#peek-popover a[href="#eq-1"]').click();              // nested ref
    await expect(page.locator('#peek-popover')).toBeHidden();                 // navigated, not nested
    await expect(page).toHaveURL(/#eq-1$/);
  } finally { await stopServer(server); }
});

// ── Task 6: review-hardening (adversarial review wrnjhusbu) ─────────────────

test('the peek close button dismisses it', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#content a[href="#eq-1"]').click();
    await expect(page.locator('#peek-popover')).toBeVisible();
    await page.locator('#peek-close').click();
    await expect(page.locator('#peek-popover')).toBeHidden();
  } finally { await stopServer(server); }
});

test('keyboard: focusing a ref link and pressing Enter opens the peek, focusing Go-to', async ({ page }) => {
  const port = nextPort();
  const { server } = await boot(page, port);
  try {
    await page.locator('#content a[href="#eq-1"]').focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('#peek-popover')).toBeVisible();
    await expect(page.locator('#peek-goto')).toBeFocused();
  } finally { await stopServer(server); }
});
