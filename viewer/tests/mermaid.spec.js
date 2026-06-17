// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');

let portCounter = 4700;
function nextPort() { return portCounter++; }

// Default timeout for Mermaid render. CDN fetch + parse + render typically
// completes well under 3s in CI; we give 5s headroom before failing.
const MERMAID_TIMEOUT_MS = 5_000;

// ─────────────────────────────────────────────────────────────────────────────
// Basic flowchart renders to SVG
// ─────────────────────────────────────────────────────────────────────────────
test('mermaid flowchart renders to svg', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'diag.md': [
      '# Flowchart demo',
      '',
      '```mermaid',
      'graph LR',
      '  A[Start] --> B{Decision}',
      '  B -->|yes| C[Continue]',
      '  B -->|no| D[Stop]',
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=diag.md`);
    await page.waitForLoadState('networkidle');
    // The fence should survive into the DOM as a .mermaid container.
    await expect(page.locator('div.mermaid')).toHaveCount(1);
    // Mermaid replaces the container's inner text with an <svg> after run().
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
    const bbox = await page.locator('div.mermaid svg').boundingBox();
    expect(bbox).not.toBeNull();
    expect(bbox.width).toBeGreaterThan(50);
    expect(bbox.height).toBeGreaterThan(30);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Sequence diagram renders to SVG
// ─────────────────────────────────────────────────────────────────────────────
test('mermaid sequenceDiagram renders to svg', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'seq.md': [
      '# Sequence demo',
      '',
      '```mermaid',
      'sequenceDiagram',
      '    participant A',
      '    participant B',
      '    A->>B: hello',
      '    B->>A: world',
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=seq.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Quoted labels with parens / special chars render (regression for review-doc
// bug that required wrapping SN node and edge labels in double quotes)
// ─────────────────────────────────────────────────────────────────────────────
test('mermaid flowchart with quoted paren-labels renders (regression)', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'parens.md': [
      '# Paren labels',
      '',
      '```mermaid',
      'graph LR',
      '  S["snr.py<br/>ρ(θ) = elevation-dependent CNR"]',
      '  A --> S',
      '  S -->|"f_D,sat(θ_k), t_axis"| B',
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=parens.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
    // If render failed, mermaid injects an error-text node with `Syntax error`
    // — asserting SVG with no error banner confirms clean parse.
    const errBanner = page.locator('div.mermaid text').getByText('Syntax error in text');
    await expect(errBanner).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Multiple diagrams in one file render independently
// ─────────────────────────────────────────────────────────────────────────────
test('multiple mermaid fences in one document all render', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'multi.md': [
      '# Multi',
      '',
      '## One',
      '',
      '```mermaid',
      'graph LR',
      '  A --> B',
      '```',
      '',
      '## Two',
      '',
      '```mermaid',
      'sequenceDiagram',
      '    A->>B: hi',
      '```',
      '',
      '## Three',
      '',
      '```mermaid',
      'graph TB',
      '  X --> Y',
      '  Y --> Z',
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=multi.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(3, { timeout: MERMAID_TIMEOUT_MS });
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Real review-doc content: first tracker block diagram (Order-1 FLL) from
// reports/reviews/2026-04-21-tracker-block-diagrams.md renders cleanly.
// Uses the actual mermaid source from the committed document so if the
// review's syntax drifts, this test catches it.
// ─────────────────────────────────────────────────────────────────────────────
test('real review doc — Order-1 FLL block diagram renders', async ({ page }) => {
  const docPath = path.resolve(
    __dirname, '..', '..',
    'reports/reviews/2026-04-21-tracker-block-diagrams.md'
  );
  // Skip gracefully if the review doc isn't present in this checkout.
  if (!fs.existsSync(docPath)) {
    test.skip(true, 'review doc not present in this checkout');
    return;
  }
  // Normalize CRLF→LF so regex matches on Windows checkouts.
  const doc = fs.readFileSync(docPath, 'utf8').replace(/\r\n/g, '\n');
  // Extract the first ```mermaid … ``` block (the Order-1 FLL diagram in §1).
  const m = doc.match(/```mermaid\n([\s\S]*?)\n```/);
  expect(m).not.toBeNull();
  const mermaidSrc = m[1];

  const port = nextPort();
  const dir = createFixtureDir({
    'order1.md': [
      '# Order-1 FLL',
      '',
      '```mermaid',
      mermaidSrc,
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=order1.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
    // Sanity: the NCO block label should appear somewhere in the rendered SVG.
    // Mermaid places label text inside <foreignObject> or <text> elements;
    // a textContent search across the container covers both. (innerText on a
    // raw <svg> throws "Node is not an HTMLElement" in Playwright.)
    const mermaidText = await page.locator('div.mermaid').first().evaluate(el => el.textContent || '');
    expect(mermaidText).toContain('NCO');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Real review doc — full-chain architecture Mermaid from
// reports/reviews/2026-04-21-fullchain-arch-and-signalflow.md renders.
// This one carries the quoted SN node label + quoted edge labels that
// previously hit "Parse error on line 12" and "line 30" (fixed at f508453
// and 6aaf8e5). Regression coverage.
// ─────────────────────────────────────────────────────────────────────────────
test('real review doc — full-chain arch diagram renders (paren regression)', async ({ page }) => {
  const docPath = path.resolve(
    __dirname, '..', '..',
    'reports/reviews/2026-04-21-fullchain-arch-and-signalflow.md'
  );
  if (!fs.existsSync(docPath)) {
    test.skip(true, 'arch review doc not present in this checkout');
    return;
  }
  // Normalize CRLF to LF so the regex works on Windows checkouts too.
  const doc = fs.readFileSync(docPath, 'utf8').replace(/\r\n/g, '\n');
  // First mermaid fence is the architecture flowchart (graph LR with SN[snr.py]).
  // Accept any opener (graph LR / graph TB / flowchart) — the regression we care
  // about is quoted-paren-label parsing, not the specific graph type.
  const m = doc.match(/```mermaid\n([\s\S]*?)\n```/);
  expect(m).not.toBeNull();
  const mermaidSrc = m[1];

  const port = nextPort();
  const dir = createFixtureDir({
    'arch.md': [
      '# Full-chain arch',
      '',
      '```mermaid',
      mermaidSrc,
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=arch.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
    // No syntax-error text — Mermaid renders its own banner when parsing fails.
    const errBanner = page.locator('div.mermaid text').getByText('Syntax error in text');
    await expect(errBanner).toHaveCount(0);
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Real review doc — HW/SW partition diagram (subgraph bracket-label + classDef)
// Regression for the "subgraph ID "title"" form failing on mermaid 11.4.1;
// the fix was switching to subgraph ID["title"] bracket form + renaming
// classDef `if` (reserved word) to `iface`.
// ─────────────────────────────────────────────────────────────────────────────
test('real review doc — HW/SW partition diagram renders', async ({ page }) => {
  const docPath = path.resolve(
    __dirname, '..', '..',
    'reports/reviews/2026-04-21-hw-sw-partition.md'
  );
  if (!fs.existsSync(docPath)) {
    test.skip(true, 'HW/SW partition review doc not present');
    return;
  }
  const doc = fs.readFileSync(docPath, 'utf8').replace(/\r\n/g, '\n');
  const m = doc.match(/```mermaid\n([\s\S]*?)\n```/);
  expect(m).not.toBeNull();
  const mermaidSrc = m[1];

  const port = nextPort();
  const dir = createFixtureDir({
    'partition.md': [
      '# HW/SW partition',
      '',
      '```mermaid',
      mermaidSrc,
      '```',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=partition.md`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('div.mermaid svg'))
      .toHaveCount(1, { timeout: MERMAID_TIMEOUT_MS });
    // Regression: mermaid 11.4.1 rejects `subgraph ID "title"` (unquoted id
    // followed by quoted title); only `subgraph ID["title"]` works. A failure
    // here will also trigger the error-banner path.
    const errBanner = page.locator('div.mermaid text').getByText('Syntax error in text');
    await expect(errBanner).toHaveCount(0);
    // Sanity: subgraph labels appear in the rendered SVG.
    const mermaidText = await page.locator('div.mermaid').first().evaluate(el => el.textContent || '');
    expect(mermaidText).toContain('HW');
    expect(mermaidText).toContain('SW');
    expect(mermaidText).toContain('Interface');
  } finally {
    stopServer(server, dir);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Mermaid fence content keeps data-source-line for source-index / outline
// ─────────────────────────────────────────────────────────────────────────────
test('mermaid container preserves data-source-line for source-index', async ({ page }) => {
  const port = nextPort();
  const dir = createFixtureDir({
    'src-line.md': [
      '# Top',
      '',
      '## Section one',
      '',
      '```mermaid',
      'graph LR',
      '  A --> B',
      '```',
      '',
      '## Section two',
    ].join('\n'),
  });
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=src-line.md`);
    await page.waitForLoadState('networkidle');
    // Even after mermaid.run() replaces innerHTML with SVG, the outer .mermaid
    // div survives and its data-source-line attribute must still be set so
    // the citation toolbar / outline can locate it.
    const attr = await page.locator('div.mermaid').first().getAttribute('data-source-line');
    expect(attr).not.toBeNull();
    expect(Number(attr)).toBeGreaterThanOrEqual(1);
  } finally {
    stopServer(server, dir);
  }
});
