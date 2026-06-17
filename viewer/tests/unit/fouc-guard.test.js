// Pins the cross-file contract between the inline FOUC guard in index.html
// (which cannot import modules — it runs before first paint) and the
// settings store / theme palette it deliberately duplicates.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { createSettingsStore, SETTINGS_KEY } = require('../../lib/settings-store');

const html = fs.readFileSync(path.join(__dirname, '../../index.html'), 'utf8');
const guard = (html.match(/<script>[^]*?FOUC guard[^]*?<\/script>/) || [''])[0];

test('FOUC guard exists and reads the store SETTINGS_KEY', () => {
  assert.ok(guard.length > 0, 'guard script block found');
  assert.ok(guard.includes(`'${SETTINGS_KEY}'`), `guard reads ${SETTINGS_KEY}`);
});

test('FOUC guard whitelist matches exactly the non-light themes the schema accepts', () => {
  const store = (seed) => {
    const m = new Map(Object.entries(seed || {}));
    return createSettingsStore({ storage: {
      getItem: (k) => (m.has(k) ? m.get(k) : null),
      setItem: (k, v) => m.set(k, String(v)),
      removeItem: (k) => m.delete(k),
    } });
  };
  for (const t of ['sepia', 'dark']) {
    assert.ok(guard.includes(`'${t}'`), `guard whitelists ${t}`);
    const s = store();
    s.set('theme', t);
    assert.equal(s.get('theme'), t, `schema accepts ${t}`);
  }
  const s = store();
  s.set('theme', 'neon');
  assert.equal(s.get('theme'), 'light', 'schema rejects unknown themes the guard would also ignore');
});

test('FOUC guard tint literals match the viewer.js THEME_COLORS palette', () => {
  const viewerJs = fs.readFileSync(path.join(__dirname, '../../viewer.js'), 'utf8');
  for (const hex of ['#1a1d23', '#8a5a2b']) {
    assert.ok(guard.includes(`'${hex}'`), `guard carries ${hex}`);
    assert.ok(viewerJs.includes(`'${hex}'`), `THEME_COLORS carries ${hex}`);
  }
});

test('FOUC guard resolves theme:auto via prefers-color-scheme pre-paint', () => {
  // An auto-on-dark-OS user must be stamped data-theme=dark before first paint
  // (the CSS dark palette is keyed solely off html[data-theme="dark"]; there is
  // NO prefers-color-scheme @media fallback in style.css, so without this the
  // page paints the light :root baseline and snaps to dark when JS runs).
  assert.ok(guard.includes("'auto'"), 'guard handles the auto theme literal');
  assert.ok(
    guard.includes('prefers-color-scheme: dark'),
    'guard reads the OS dark-mode media query synchronously',
  );
  // The store accepts 'auto' as a persistable theme (the guard must handle it).
  const s = chromeStore();
  s.set('theme', 'auto');
  assert.equal(s.get('theme'), 'auto', 'schema accepts auto');
});

test('FOUC guard stamps the density preset class pre-paint', () => {
  // density compact/spacious are part of the first-paint chrome state; without
  // a pre-paint stamp non-default-density users flash normal-density chrome
  // until applyDensity() lands after the awaited fetchFileList() round-trip.
  assert.ok(guard.includes('density-'), 'guard stamps a density-* class');
  for (const d of ['compact', 'spacious']) {
    assert.ok(guard.includes(`'${d}'`), `guard recognises density:${d}`);
    const s = chromeStore();
    s.set('density', d);
    assert.equal(s.get('density'), d, `schema accepts density:${d}`);
  }
});

test('FOUC guard stamps --measure-ch pre-paint from a non-default measureCh', () => {
  // --measure-ch caps the prose column width and is slider-controlled
  // (applyTypography sets it post-load). Without a pre-paint stamp a non-default
  // measure reflows the content column on first paint (review w9d47hl9a #11).
  assert.ok(guard.includes('measure-ch'), 'guard sets the --measure-ch property');
  assert.ok(guard.includes('measureCh'), 'guard reads s.measureCh from the store');
  // The guard must range-gate against the schema (48..80ch) so a corrupt store
  // cannot poison the layout — the same bounds settings-store.js enforces.
  for (const v of [48, 80]) {
    const s = chromeStore();
    s.set('measureCh', v);
    assert.equal(s.get('measureCh'), v, `schema accepts measureCh:${v}`);
  }
  const s = chromeStore();
  s.set('measureCh', 999);
  assert.equal(s.get('measureCh'), 66, 'schema rejects out-of-range measureCh → default 66');
});

// ── Chrome FOUC guard — pins the duplicate of settings-store SCHEMA.chrome ──

function chromeStore(seed) {
  const m = new Map(Object.entries(seed || {}));
  return createSettingsStore({ storage: {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  } });
}

test('FOUC guard sets data-chrome attribute', () => {
  // Removing this stamp would boot the page painted docs while JS treats it
  // as reader until loadSettings() lands (the layout-flash QR finding).
  assert.ok(
    guard.includes('dataset.chrome') || guard.includes('data-chrome'),
    'guard assigns data-chrome (via dataset.chrome or setAttribute)',
  );
});

test('FOUC guard whitelists the docked "docs" chrome value', () => {
  assert.ok(guard.includes("'docs'"), "guard contains the literal 'docs'");
  const s = chromeStore();
  s.set('chrome', 'docs');
  assert.equal(s.get('chrome'), 'docs', 'schema accepts docs');
});

test('FOUC guard defaults unrecognised chrome to "reader"', () => {
  assert.ok(guard.includes("'reader'"), "guard contains the literal 'reader'");
  const s = chromeStore();
  s.set('chrome', 'neon');
  assert.equal(s.get('chrome'), 'reader', 'schema rejects unknown chrome → default reader');
});

test('FOUC guard maps legacy layout:classic to chrome:docs', () => {
  // The guard reads parsed.chrome, falling back to legacy parsed.layout.
  assert.ok(guard.includes("'classic'"), 'guard recognises legacy classic for migration');
  const s = chromeStore({ 'viewer.settings.v1': JSON.stringify({ layout: 'classic' }) });
  assert.equal(s.get('chrome'), 'docs', 'store migrates legacy classic to docs');
});
