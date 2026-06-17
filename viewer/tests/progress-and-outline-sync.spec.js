// @ts-check
// REGRESSION GATE for the reading-progress bar + always-on outline sync.
// This suite asserts the feature's BEHAVIORAL CONTRACT, not internals, so
// it survives benign refactors but fails loudly on the three known
// regression vectors:
//   (1) #content.innerHTML re-render wiping the bar  -> test 2 (added in Task 3)
//   (2) relapse to IntersectionObserver-only spy     -> tests 6/7 (added in Task 4)
//   (3) relapse to a post-navigation suppression lock -> test 8 (added in Task 4)
// Determinism: forced auto-scroll, condition-based waits only, fail on any
// page/console error. See docs/superpowers/specs/2026-05-18-viewer-
// progress-and-outline-sync-design.md §8.
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout } = require('./helpers/layout');

let portCounter = 4955;
function nextPort() { return portCounter++; }

const FILLER = Array.from({ length: 30 },
  (_, i) => `Filler paragraph ${i} lorem ipsum dolor sit amet consectetur.`).join('\n\n');

function longDoc() {
  let s = 'Intro prose before any heading.\n\n' + FILLER + '\n\n';
  for (let i = 1; i <= 6; i++) {
    s += `## Section ${i}\n\n${FILLER}\n\n`;
  }
  s += '## Short Final\n\nOne short line. [Jump to Section 2](#section-2)\n';
  return s;
}
function mathDoc() {
  let s = '';
  for (let i = 1; i <= 5; i++) {
    s += `## Math Section ${i}\n\n${FILLER}\n\n$$\\sum_{n=0}^{\\infty} x_n = \\frac{1}{1-x} \\tag{${i}}$$\n\n${FILLER}\n\n`;
  }
  return s;
}
const NO_HEADINGS = 'Just prose.\n\n' + FILLER;
const SHORT = '## Only Heading\n\nOne short paragraph.\n';

function fixture() {
  return createFixtureDir({
    'long.md': longDoc(),
    'math.md': mathDoc(),
    'none.md': NO_HEADINGS,
    'short.md': SHORT,
    'other.md': '# Other\n\nDifferent file.\n\n' + FILLER,
  });
}

// Inject forced-instant scrolling so assertions never race a smooth-scroll.
// addInitScript runs before <html> is parsed, so documentElement/head may be
// null — defer to DOMContentLoaded in that case.
// This suite pins the LEGACY top-progress-bar + docked-sidebar outline
// contract, which after redesign 02 is the CLASSIC layout (reader mode
// replaces the bar with a right-edge rail and docks no sidebar) — see
// helpers/layout.js (merge-write keeps the test-5 persistence flow intact).
async function gotoFile(page, port, file) {
  await pinClassicLayout(page);
  await page.addInitScript(() => {
    const inject = () => {
      const st = document.createElement('style');
      st.textContent = 'html{scroll-behavior:auto !important}';
      (document.head || document.documentElement).appendChild(st);
    };
    if (document.documentElement) inject();
    else document.addEventListener('DOMContentLoaded', inject);
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(`http://localhost:${port}?file=${file}`);
  await page.waitForSelector('#content h2, #content p');
  return errors;
}

test('1. default state: bar present, visible, whole-doc', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    const errors = await gotoFile(page, port, 'long.md');
    await expect(page.locator('#reading-progress')).toBeAttached();
    const state = await page.evaluate(() => ({
      noClass: !document.documentElement.classList.contains('no-reading-progress'),
      checked: document.getElementById('setting-reading-progress')?.checked,
      mode: [...document.querySelectorAll('input[name="reading-progress-mode"]')]
        .find(r => r.checked)?.value,
    }));
    expect(state.noClass).toBe(true);
    expect(state.checked).toBe(true);
    expect(state.mode).toBe('whole-doc');
    expect(errors, errors.join(' | ')).toHaveLength(0);
  } finally { stopServer(server, dir); }
});

test('5. settings off/on + mode persist across reload', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    await page.locator('#settings-btn').click();
    await page.locator('#setting-reading-progress').uncheck();
    await page.waitForFunction(() =>
      document.documentElement.classList.contains('no-reading-progress'));
    await page.reload();
    await page.waitForSelector('#content h2');
    expect(await page.evaluate(() =>
      document.documentElement.classList.contains('no-reading-progress'))).toBe(true);
    await page.locator('#settings-btn').click();
    await page.locator('#setting-reading-progress').check();
    await page.locator('input[name="reading-progress-mode"][value="section"]').check();
    await page.waitForFunction(() => {
      try {
        var s = JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}');
        return s.readingProgressMode === 'section';
      } catch (e) { return false; }
    });
    await page.reload();
    await page.waitForSelector('#content h2');
    const after = await page.evaluate(() => ({
      on: !document.documentElement.classList.contains('no-reading-progress'),
      mode: [...document.querySelectorAll('input[name="reading-progress-mode"]')]
        .find(r => r.checked)?.value,
    }));
    expect(after.on).toBe(true);
    expect(after.mode).toBe('section');
  } finally { stopServer(server, dir); }
});

test('11. bar left edge tracks the sidebar', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    const expanded = await page.evaluate(() =>
      document.getElementById('reading-progress').getBoundingClientRect().left);
    expect(expanded).toBeGreaterThan(50);
    await page.locator('#sidebar-toggle').click();
    await page.waitForFunction(() =>
      document.getElementById('sidebar').classList.contains('collapsed'));
    await page.waitForFunction(() =>
      document.getElementById('reading-progress').getBoundingClientRect().left < 5);
    const collapsed = await page.evaluate(() =>
      document.getElementById('reading-progress').getBoundingClientRect().left);
    expect(collapsed).toBeLessThan(5);
  } finally { stopServer(server, dir); }
});

test('2. survives re-render: bar not under #content, persists across file switch', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    const errors = await gotoFile(page, port, 'long.md');
    expect(await page.evaluate(() =>
      !document.querySelector('#content #reading-progress')
      && !!document.querySelector('#app > #reading-progress'))).toBe(true);
    await page.evaluate(() => window.scrollTo(0, 1500));
    await page.waitForFunction(() => {
      const w = document.getElementById('reading-progress-fill').style.width;
      return w && parseFloat(w) > 0;
    });
    await page.goto(`http://localhost:${port}?file=other.md`);
    await page.waitForSelector('#content h1');
    await page.goto(`http://localhost:${port}?file=long.md`);
    await page.waitForSelector('#content h2');
    expect(await page.locator('#reading-progress').count()).toBe(1);
    await page.evaluate(() => window.scrollTo(0, 1200));
    await page.waitForFunction(() =>
      parseFloat(document.getElementById('reading-progress-fill').style.width) > 0);
    expect(errors, errors.join(' | ')).toHaveLength(0);
  } finally { stopServer(server, dir); }
});

test('3. whole-doc fill is monotonic, ~0 top, >=0.99 bottom', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    const errors = await gotoFile(page, port, 'long.md');
    const widths = [];
    for (const y of [0, 0.2, 0.4, 0.6, 0.8, 1.0]) {
      await page.evaluate((f) => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo(0, Math.round(max * f));
      }, y);
      await page.waitForFunction((expected) => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        return Math.abs(window.scrollY - Math.round(max * expected)) < 4;
      }, y);
      // Wait until the controller's rAF tick for THIS scroll has applied:
      // the rendered fill must converge on the live whole-doc fraction
      // scrollY / (docHeight - viewport). The previous two-equal-polls
      // heuristic kept its dataset.pw marker ACROSS stops, so a poll that
      // ran before the controller's rAF matched the prior stop's stored
      // width and accepted it as "stable" — a machine-timing race that
      // sampled stale fills (bug 2026-06-11-01; reproduced fills stuck at
      // 60%/80% at the bottom stop).
      await page.waitForFunction(() => {
        const el = document.getElementById('reading-progress-fill');
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const want = (window.scrollY / Math.max(1, max)) * 100;
        const w = parseFloat(el.style.width || '-1');
        return Math.abs(w - want) < 1;
      });
      widths.push(await page.evaluate(() =>
        parseFloat(document.getElementById('reading-progress-fill').style.width)));
    }
    for (let i = 1; i < widths.length; i++) {
      expect(widths[i]).toBeGreaterThanOrEqual(widths[i - 1] - 0.5);
    }
    expect(widths[0]).toBeLessThan(2);
    expect(widths[widths.length - 1]).toBeGreaterThan(99);
    expect(errors, errors.join(' | ')).toHaveLength(0);
  } finally { stopServer(server, dir); }
});

test('4. section mode fill resets at a heading boundary', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    await page.evaluate(() => {
      // Write to the namespaced settings key (redesign 01 T5; legacy key no longer read after boot)
      var s = {};
      try { s = JSON.parse(localStorage.getItem('viewer.settings.v1') || '{}'); } catch (e) {}
      s.readingProgressMode = 'section';
      localStorage.setItem('viewer.settings.v1', JSON.stringify(s));
    });
    await page.reload();
    await page.waitForSelector('#content h2');
    const widthAt = async (sel, dy) => {
      await page.evaluate(({ sel, dy }) => {
        const h = [...document.querySelectorAll('#content h2')]
          .find(e => e.textContent.includes(sel));
        window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY + dy);
      }, { sel, dy });
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));
      return page.evaluate(() =>
        parseFloat(document.getElementById('reading-progress-fill').style.width));
    };
    const deepInS2 = await widthAt('Section 2', 1200);
    const startOfS3 = await widthAt('Section 3', 5);
    expect(startOfS3).toBeLessThan(deepInS2);
  } finally { stopServer(server, dir); }
});

test('10. edge fixtures: no-headings + not-scrollable do not error', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    let errors = await gotoFile(page, port, 'none.md');
    await page.evaluate(() => window.scrollTo(0, 400));
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));
    // (Until Task 4 wires registerOutlineSpy, no entry is ever marked active;
    // post-Task-4 this still holds for a no-headings document.)
    expect(await page.evaluate(() =>
      document.querySelectorAll('.outline-entry.active').length)).toBe(0);
    expect(errors, errors.join(' | ')).toHaveLength(0);
    errors = await gotoFile(page, port, 'short.md');
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));
    expect(await page.evaluate(() =>
      parseFloat(document.getElementById('reading-progress-fill').style.width) || 0)).toBe(0);
    expect(errors, errors.join(' | ')).toHaveLength(0);
  } finally { stopServer(server, dir); }
});

async function activeText(page) {
  return page.evaluate(() => {
    const a = document.querySelector('.outline-entry.active');
    return a ? a.textContent.trim() : null;
  });
}
async function openOutline(page) {
  await page.locator('.sidebar-tab[data-tab="outline"]').click();
  await page.waitForSelector('#outline-list:not(.tab-hidden) .outline-entry');
}

test('6. outline syncs within a long section (no heading crossing)', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    await openOutline(page);
    await page.evaluate(() => {
      const h = [...document.querySelectorAll('#content h2')]
        .find(e => e.textContent.includes('Section 3'));
      window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY + 900);
    });
    await page.waitForFunction(() => {
      const a = document.querySelector('.outline-entry.active');
      return a && a.textContent.includes('Section 3');
    });
    expect(await activeText(page)).toContain('Section 3');
  } finally { stopServer(server, dir); }
});

test('7. scroll sweep: exactly one active entry, matches scan line', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    await openOutline(page);
    for (const target of ['Section 1', 'Section 2', 'Section 4', 'Section 6', 'Short Final']) {
      await page.evaluate((t) => {
        const h = [...document.querySelectorAll('#content h2')]
          .find(e => e.textContent.includes(t));
        window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY + 20);
      }, target);
      await page.waitForFunction((t) => {
        const xs = document.querySelectorAll('.outline-entry.active');
        return xs.length === 1 && xs[0].textContent.includes(t);
      }, target);
      expect(await page.evaluate(() =>
        document.querySelectorAll('.outline-entry.active').length)).toBe(1);
    }
  } finally { stopServer(server, dir); }
});

test('8. no stale window after a jump + immediate re-scroll still updates', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'long.md');
    await openOutline(page);
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.locator('#content a[href="#section-2"]').click();
    await page.waitForFunction(() => {
      const a = document.querySelector('.outline-entry.active');
      return a && a.textContent.includes('Section 2');
    }, undefined, { timeout: 2000 });
    await page.evaluate(() => {
      const h = [...document.querySelectorAll('#content h2')]
        .find(e => e.textContent.includes('Section 4'));
      window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY + 30);
    });
    await page.waitForFunction(() => {
      const a = document.querySelector('.outline-entry.active');
      return a && a.textContent.includes('Section 4');
    }, undefined, { timeout: 1500 });
    expect(await activeText(page)).toContain('Section 4');
  } finally { stopServer(server, dir); }
});

test('9. late KaTeX layout: active entry correct after math reflow', async ({ page }) => {
  const port = nextPort(); const dir = fixture(); const server = await startServer(dir, port);
  try {
    await gotoFile(page, port, 'math.md');
    await page.waitForFunction(() =>
      document.querySelectorAll('#content .katex').length >= 3);
    await openOutline(page);
    await page.evaluate(() => {
      const h = [...document.querySelectorAll('#content h2')]
        .find(e => e.textContent.includes('Math Section 4'));
      window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY + 10);
    });
    await page.waitForFunction(() => {
      const a = document.querySelector('.outline-entry.active');
      return a && a.textContent.includes('Math Section 4');
    }, undefined, { timeout: 2000 });
    expect(await activeText(page)).toContain('Math Section 4');
  } finally { stopServer(server, dir); }
});
