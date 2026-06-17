// @ts-check
// Responsive web design: wide content (long URLs, many-column tables, wide
// display-math, long code lines) must wrap/scroll INSIDE the content column,
// never force the whole page to scroll horizontally — at any viewport width,
// in both reader and classic layouts. Guards the flex min-width:auto trap
// (bug 2026-06-13-01): #content min-width:0 + overflow-wrap + child containment.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 6900;
function nextPort() { return portCounter++; }

// Pathological content that stresses every wide-element path at once.
const STRESS = `# A Heading Long Enough To Exercise Wrapping On Small Screens

Prose with a very long unbreakable token https://example.com/a/very/long/path/that/should/not/blow/out/the/layout/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa and words after.

| Col A | Col B | Col C | Col D | Col E | Col F | Col G | Col H |
|---|---|---|---|---|---|---|---|
| alpha | bravo | charlie | delta | echo | foxtrot | golf | hotel |

$$
\\int_{-\\infty}^{\\infty} e^{-x^2}\\, dx = \\sqrt{\\pi} \\quad\\text{and}\\quad \\sum_{n=0}^{N} a_n x^n + b_n y^n + c_n z^n + d_n w^n = \\Phi(x,y,z,w) \\tag{1}
$$

\`\`\`
a_very_long_unbreakable_line_of_code_that_must_scroll_not_overflow_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = 1
\`\`\`

Trailing prose.
`;

async function overflowAt(page, port, layout, width) {
  await page.addInitScript((l) => localStorage.setItem('viewer.settings.v1', JSON.stringify({ layout: l })), layout);
  await page.setViewportSize({ width, height: 800 });
  await page.goto(`http://localhost:${port}?file=doc.md`);
  await expect(page.locator('#content h1')).toBeVisible();
  await page.waitForTimeout(120);
  return page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
}

for (const layout of ['reader', 'classic']) {
  for (const width of [320, 360, 768]) {
    test(`no horizontal overflow with wide content — ${layout} @ ${width}px`, async ({ page }) => {
      const port = nextPort();
      const dir = createFixtureDir({ 'doc.md': STRESS });
      const server = await startServer(dir, port);
      try {
        const over = await overflowAt(page, port, layout, width);
        expect(over, `page overflows the viewport by ${over}px`).toBeLessThanOrEqual(1);
      } finally { await stopServer(server, dir); }
    });
  }
}
