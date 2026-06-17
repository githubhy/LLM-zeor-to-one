#!/usr/bin/env node
// Click every entry on the Highlights tab of a running viewer and verify
// each click navigates to the expected file and scrolls to the expected
// source line.
//
// Usage: node tools/check-highlights.js [--url http://localhost:PORT]

'use strict';

const { chromium } = require('playwright');

async function main() {
  const urlArg = process.argv.find((a, i, all) => all[i - 1] === '--url');
  const baseUrl = urlArg || 'http://localhost:3600';

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  console.log(`Opening ${baseUrl} …`);
  await page.goto(baseUrl);
  await page.waitForLoadState('networkidle');

  await page.locator('.sidebar-tab[data-tab="highlights"]').click();
  await page.waitForSelector('#highlights-list:not(.tab-hidden)', { timeout: 5000 });
  await page.waitForTimeout(800); // manifest load

  const total = await page.locator('.hl-entry').count();
  console.log(`Found ${total} highlight entries.\n`);
  if (!total) { await browser.close(); return; }

  // Snapshot the entry metadata so clicks do not invalidate live refs.
  const meta = await page.locator('.hl-entry').evaluateAll((els) =>
    els.map((el) => ({
      file:    el.querySelector('.hl-entry-file')?.textContent || '',
      excerpt: el.querySelector('.hl-entry-text')?.textContent || '',
    })),
  );

  const results = [];
  for (let i = 0; i < total; i++) {
    const { file: label, excerpt } = meta[i];
    const m = label.match(/^(.+):(\d+)$/);
    const expectedFile = m ? m[1] : label;
    const expectedLine = m ? parseInt(m[2], 10) : null;

    // Click the i-th entry. Re-query to get the current DOM node.
    await page.locator('.hl-entry').nth(i).click();

    // Wait for the URL to reflect the expected file (up to 5s).
    try {
      await page.waitForURL((u) => u.searchParams.get('file') === expectedFile, { timeout: 5000 });
    } catch {
      // fall through; the check below will record file mismatch
    }

    // Wait until the file's H1 is visible (fresh render completed).
    try {
      await page.waitForSelector('#content h1', { timeout: 5000 });
    } catch {}

    // Give scrollIntoView + any late reflow a moment.
    await page.waitForTimeout(500);

    const actualUrl = new URL(page.url());
    const actualFile = actualUrl.searchParams.get('file') || '';

    // Diagnose on-screen state. We accept either the literal <mark> being
    // visible OR the enclosing block (via data-source-line <= expectedLine)
    // being visible. Inline math excerpts contain raw "$...$" in the
    // manifest, but the rendered DOM has KaTeX-rendered spans, so textContent
    // comparison alone yields false negatives.
    const diag = await page.evaluate(({ excerpt, expectedLine }) => {
      const normalize = (s) => (s || '').replace(/\s+/g, ' ').trim();
      const want = normalize(excerpt).slice(0, 40);
      const vh = window.innerHeight;
      const inView = (rect) => rect && rect.top > -200 && rect.top < vh + 200;

      // Try exact-text mark first.
      let matched = null;
      for (const el of document.querySelectorAll('mark')) {
        if (normalize(el.textContent).includes(want)) { matched = el; break; }
      }
      const matchedRect = matched ? matched.getBoundingClientRect() : null;

      // Enclosing block by source line (the viewer's own fallback target).
      let enclosing = null;
      let enclosingLine = -1;
      if (expectedLine != null) {
        const target0 = expectedLine - 1;
        for (const el of document.querySelectorAll('[data-source-line]')) {
          const l = parseInt(el.dataset.sourceLine, 10);
          if (!Number.isFinite(l)) continue;
          if (l <= target0 && l > enclosingLine) { enclosingLine = l; enclosing = el; }
        }
      }
      const enclosingRect = enclosing ? enclosing.getBoundingClientRect() : null;

      // Nearest source-line to viewport midpoint (sanity).
      const mid = window.scrollY + vh * 0.5;
      let nearestLine = null, nearestDist = Infinity;
      for (const el of document.querySelectorAll('[data-source-line]')) {
        const line = parseInt(el.dataset.sourceLine, 10);
        if (!Number.isFinite(line)) continue;
        const top = el.getBoundingClientRect().top + window.scrollY;
        const dist = Math.abs(top - mid);
        if (dist < nearestDist) { nearestDist = dist; nearestLine = line; }
      }

      return {
        matchedFound: !!matched,
        matchedOnScreen: inView(matchedRect),
        matchedTop: matchedRect ? Math.round(matchedRect.top) : null,
        enclosingLine,
        enclosingOnScreen: inView(enclosingRect),
        enclosingTop: enclosingRect ? Math.round(enclosingRect.top) : null,
        nearestLine, scrollY: window.scrollY, vh,
      };
    }, { excerpt, expectedLine });

    const fileOK = actualFile === expectedFile;
    const landedOnTarget = diag.matchedOnScreen || diag.enclosingOnScreen;
    const pass = fileOK && landedOnTarget;
    results.push({
      i, expectedFile, actualFile, expectedLine,
      nearestLine: diag.nearestLine, enclosingLine: diag.enclosingLine,
      excerpt: excerpt.slice(0, 55), fileOK, landedOnTarget, pass,
      matchedOnScreen: diag.matchedOnScreen, matchedFound: diag.matchedFound,
      enclosingOnScreen: diag.enclosingOnScreen,
    });

    const tag = pass ? 'OK ' : 'BAD';
    const why = [];
    if (!fileOK) why.push(`file=${actualFile}≠${expectedFile}`);
    if (!landedOnTarget) {
      why.push(`mark=${diag.matchedFound ? (diag.matchedOnScreen ? 'OK' : `y=${diag.matchedTop}`) : 'not-found'}`);
      why.push(`block=${diag.enclosingOnScreen ? 'OK' : (diag.enclosingLine >= 0 ? `y=${diag.enclosingTop}` : 'none')}`);
    }
    console.log(
      `${tag} [${String(i + 1).padStart(2, '0')}/${total}] ` +
      `${expectedFile}:${expectedLine} "${excerpt.slice(0, 45)}"` +
      (why.length ? `  → ${why.join('; ')}` : ''),
    );

    // Ensure Highlights tab remains visible for the next click.
    const listHidden = await page.evaluate(() =>
      document.getElementById('highlights-list').classList.contains('tab-hidden'),
    );
    if (listHidden) {
      await page.locator('.sidebar-tab[data-tab="highlights"]').click();
      await page.waitForSelector('#highlights-list:not(.tab-hidden)', { timeout: 2000 });
    }
  }

  const passed = results.filter((r) => r.pass).length;
  console.log(`\n${passed}/${total} highlights land correctly.`);

  if (passed < total) {
    console.log('\nFailing entries:');
    for (const r of results) if (!r.pass) {
      console.log(
        `  ${String(r.i + 1).padStart(2, '0')}  ${r.expectedFile}:${r.expectedLine}  "${r.excerpt}"  ` +
        `file=${r.fileOK ? 'OK' : r.actualFile}  mark=${r.matchedOnScreen ? 'OK' : (r.matchedFound ? 'off' : 'no')}  block=${r.enclosingOnScreen ? 'OK' : 'no'}`,
      );
    }
  }

  await browser.close();
  process.exit(passed === total ? 0 : 1);
}

main().catch((err) => { console.error(err); process.exit(2); });
