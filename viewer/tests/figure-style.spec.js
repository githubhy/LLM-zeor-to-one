// @ts-check
// Spec-driven figure: progressive enhancement + style switcher.
// ─────────────────────────────────────────────────────────────────────────────
//   F1  default style enhances the marked image to a live colour-academic render
//   F2  'image' style keeps the embedded PNG (no live render)
//   F3  settings radio switches the style live (no reload) → swimlane
//   F4  inline chip switches the style and persists to the store
//   F5  narrow column reflows the linear figure to a vertical stack
//
// spec.json is fixtured under an /artifacts/ path so serve.js's figure-asset
// route serves it (.json under /artifacts/ — see serve.js asset gate).
const { test, expect } = require('@playwright/test');
const { createFixtureDir, startServer, stopServer } = require('./helpers/server');
const { pinClassicLayout, seedSettings } = require('./helpers/layout');

let portCounter = 5980;
const nextPort = () => portCounter++;

// Demo spec: the scaled dot-product attention pipeline (a canonical LLM figure).
const SPEC = {
  id: 'pipeline-figure', title: 'scaled dot-product attention',
  input: { label: 'x', sub: 'tokens' }, output: { label: 'context' },
  stages: [
    { id: 'qkv', title: 'QKV projection', detail: 'W_Q,W_K,W_V', ref: '§3.3', group: 'A' },
    { id: 'sc',  title: 'Scores', detail: 'QK^T', ref: '§3.4', group: 'A' },
    { id: 'sm',  title: 'Scaled softmax', detail: 'over keys', ref: '§3.2', group: 'B', highlight: true },
    { id: 'wv',  title: 'Weighted sum', detail: 'over V', ref: '§5c', group: 'C' },
    { id: 'op',  title: 'Output projection', detail: 'W_O', ref: '§5d', group: 'C' },
  ],
  edges: ['Q,K,V', 'scores', 'weights', 'heads'],
  groups: {
    A: { label: 'project', color: '#1f77b4' },
    B: { label: 'attend', color: '#ff7f0e' },
    C: { label: 'combine', color: '#2ca02c' },
  },
  defaultStyle: 'colour-academic',
  styles: [
    { id: 'colour-academic', label: 'Colour academic' },
    { id: 'monochrome', label: 'Monochrome' },
    { id: 'minimal', label: 'Minimal line' },
    { id: 'swimlane', label: 'Swimlane tiers' },
    { id: 'image', label: 'Static image' },
  ],
};

const FIXTURE = {
  'order.json': JSON.stringify(['index.md']),
  'index.md': '# Figure Test\n\n![pipeline diagram](artifacts/fig/pipeline.png "pipeline-figure")\n\nAfter the figure.\n',
  'artifacts/fig/spec.json': JSON.stringify(SPEC),
};

test.beforeEach(async ({ page }) => { await pinClassicLayout(page); });

test('F1: default style enhances the marked image to a live colour-academic render', async ({ page }) => {
  const port = nextPort(); const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Figure Test');
    const wrap = page.locator('.fp-wrap');
    await expect(wrap).toHaveCount(1);
    await expect(wrap.locator('.fp-render .fp-linear.fp-colour-academic')).toBeVisible();
    await expect(wrap.locator('.fp-box.fp-hot')).toContainText('Scaled softmax');
    await expect(wrap.locator('.fp-render')).toContainText('Q,K,V');
    // fallback img must be visually hidden when a live style is active — guards
    // the `#content img` specificity regression (the static PNG showing on top).
    await expect(wrap.locator('img.fp-fallback')).toBeHidden();
  } finally { stopServer(server, dir); }
});

test('F2: static-image style keeps the embedded PNG (no live render)', async ({ page }) => {
  await seedSettings(page, { figureStyle: 'image' });
  const port = nextPort(); const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('#content h1')).toHaveText('Figure Test');
    const wrap = page.locator('.fp-wrap');
    await expect(wrap).toHaveCount(1);
    const disp = await wrap.locator('img.fp-fallback').evaluate((el) => getComputedStyle(el).display);
    expect(disp).not.toBe('none');
    await expect(wrap.locator('.fp-render .fp-linear')).toHaveCount(0);
  } finally { stopServer(server, dir); }
});

test('F3: settings radio switches the style live, no reload (→ swimlane)', async ({ page }) => {
  const port = nextPort(); const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    await expect(page.locator('.fp-wrap .fp-render .fp-colour-academic')).toBeVisible();
    await page.locator('#settings-btn').click();
    await page.locator('input[name="figure-style"][value="swimlane"]').check();
    await expect(page.locator('.fp-wrap .fp-render .fp-swimlane')).toBeVisible();
    await expect(page.locator('.fp-wrap .fp-band')).toHaveCount(3);
  } finally { stopServer(server, dir); }
});

test('F4: inline chip switches the style and persists to the store', async ({ page }) => {
  const port = nextPort(); const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.goto(`http://localhost:${port}/?file=index.md`);
    const wrap = page.locator('.fp-wrap');
    await expect(wrap.locator('.fp-render .fp-colour-academic')).toBeVisible();
    await wrap.hover();
    await wrap.locator('.fp-chip-btn').click();
    await wrap.locator('.fp-chip-menu button[data-style-id="monochrome"]').click();
    await expect(wrap.locator('.fp-render .fp-monochrome')).toBeVisible();
    const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('viewer.settings.v1')).figureStyle);
    expect(stored).toBe('monochrome');
  } finally { stopServer(server, dir); }
});

test('F5: narrow column reflows the linear figure to a vertical stack', async ({ page }) => {
  const port = nextPort(); const dir = createFixtureDir(FIXTURE);
  const server = await startServer(dir, port);
  try {
    await page.setViewportSize({ width: 420, height: 900 });
    await page.goto(`http://localhost:${port}/?file=index.md`);
    const fig = page.locator('.fp-wrap .fp-linear');
    await expect(fig).toBeVisible();
    const flexDir = await fig.evaluate((el) => getComputedStyle(el).flexDirection);
    expect(flexDir).toBe('column');
    const vDisplay = await page.locator('.fp-wrap .fp-arr .fp-gl-v').first().evaluate((el) => getComputedStyle(el).display);
    expect(vDisplay).not.toBe('none');
  } finally { stopServer(server, dir); }
});
