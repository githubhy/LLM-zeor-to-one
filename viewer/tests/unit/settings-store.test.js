const test = require('node:test');
const assert = require('node:assert/strict');
const { createSettingsStore, SETTINGS_KEY } = require('../../lib/settings-store');

function fakeStorage(seed = {}) {
  const m = new Map(Object.entries(seed));
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
    _dump: () => Object.fromEntries(m),
  };
}

test('defaults: fresh storage yields documented defaults', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('theme'), 'light');
  assert.equal(s.get('chrome'), 'reader');
  assert.equal(s.get('fontScale'), 1.0);
  assert.equal(s.get('lineHeight'), 1.7);
  assert.equal(s.get('measureCh'), 66);
  assert.equal(s.get('fontFamily'), 'sans');
  assert.equal(s.get('citationMode'), 'github');
});

test('marginNotes: defaults off, accepts booleans only, persists', () => {
  const st = fakeStorage();
  const s = createSettingsStore({ storage: st });
  // Default off (T7 — Tufte margin sidenotes, opt-in feature).
  assert.equal(s.get('marginNotes'), false);
  // Non-boolean rejected; old value kept.
  s.set('marginNotes', 'yes');
  assert.equal(s.get('marginNotes'), false);
  // Boolean accepted + persisted across a fresh store.
  s.set('marginNotes', true);
  assert.equal(s.get('marginNotes'), true);
  assert.equal(createSettingsStore({ storage: st }).get('marginNotes'), true);
});

test('set persists under the namespaced key and survives a second store', () => {
  const st = fakeStorage();
  createSettingsStore({ storage: st }).set('theme', 'dark');
  const again = createSettingsStore({ storage: st });
  assert.equal(again.get('theme'), 'dark');
  assert.ok(st.getItem(SETTINGS_KEY).includes('"theme":"dark"'));
});

test('invalid values are rejected and the old value kept', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  s.set('theme', 'neon');
  s.set('fontScale', 99);
  assert.equal(s.get('theme'), 'light');
  assert.equal(s.get('fontScale'), 1.0);
});

test('subscribe notifies on change with (key, value) and unsubscribe stops it', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  const seen = [];
  const un = s.subscribe((k, v) => seen.push([k, v]));
  s.set('theme', 'sepia');
  un();
  s.set('theme', 'dark');
  assert.deepEqual(seen, [['theme', 'sepia']]);
});

test('legacy keys migrate once and are removed', () => {
  const st = fakeStorage({
    'viewer-scroll-fx': 'off',
    'viewer-update-fx': 'on',
    'viewer-note-marker': 'ring',
    'viewer-reading-progress': 'off',
    'viewer-reading-progress-mode': 'section',
    'viewer-citation-mode': 'local',
  });
  const s = createSettingsStore({ storage: st });
  assert.equal(s.get('scrollFx'), false);
  assert.equal(s.get('updateFx'), true);
  assert.equal(s.get('noteMarker'), 'ring');
  assert.equal(s.get('readingProgress'), false);
  assert.equal(s.get('readingProgressMode'), 'section');
  assert.equal(s.get('citationMode'), 'local');
  assert.equal(st.getItem('viewer-scroll-fx'), null);
  assert.equal(st.getItem('viewer-citation-mode'), null);
});

test('migration does not run when the namespaced key already exists', () => {
  const st = fakeStorage({ 'viewer-citation-mode': 'local' });
  createSettingsStore({ storage: st }).set('citationMode', 'relative');
  st.setItem('viewer-citation-mode', 'github'); // stray legacy write
  const again = createSettingsStore({ storage: st });
  assert.equal(again.get('citationMode'), 'relative');
});

test('corrupt JSON falls back to defaults without throwing', () => {
  const st = fakeStorage();
  st.setItem(SETTINGS_KEY, '{not json');
  const s = createSettingsStore({ storage: st });
  assert.equal(s.get('theme'), 'light');
});

test('stored JSON with an invalid field falls back to that field default only', () => {
  const st = fakeStorage();
  st.setItem(SETTINGS_KEY, JSON.stringify({ theme: 'neon', fontScale: 1.2 }));
  const s = createSettingsStore({ storage: st });
  assert.equal(s.get('theme'), 'light');
  assert.equal(s.get('fontScale'), 1.2);
});

test('throwing setItem: store stays usable and legacy keys are preserved', () => {
  const st = fakeStorage({ 'viewer-citation-mode': 'local' });
  const broken = {
    getItem: st.getItem,
    setItem: () => { throw new Error('quota'); },
    removeItem: st.removeItem,
  };
  const s = createSettingsStore({ storage: broken });
  assert.equal(s.get('citationMode'), 'local');           // migrated in memory
  assert.equal(st.getItem('viewer-citation-mode'), 'local'); // NOT deleted
  s.set('theme', 'dark');                                  // does not throw
  assert.equal(s.get('theme'), 'dark');
});

test('chrome: defaults to reader; predicate accepts docs|reader|focus', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('chrome'), 'reader');
  s.set('chrome', 'focus'); assert.equal(s.get('chrome'), 'focus');
  s.set('chrome', 'docs'); assert.equal(s.get('chrome'), 'docs');
  s.set('chrome', 'bogus'); assert.equal(s.get('chrome'), 'docs'); // unchanged
});

test('chrome: legacy layout:classic migrates to docs; reader/unknown -> reader', () => {
  const mk = (seed) => createSettingsStore({ storage: fakeStorage({ 'viewer.settings.v1': JSON.stringify(seed) }) });
  assert.equal(mk({ layout: 'classic' }).get('chrome'), 'docs');
  assert.equal(mk({ layout: 'reader' }).get('chrome'), 'reader');
  assert.equal(mk({ layout: 'bogus' }).get('chrome'), 'reader');
  assert.equal(mk({ layout: 'classic' }).get('layout'), undefined);
});

test('theme: predicate accepts auto in addition to light|sepia|dark', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('theme'), 'light');
  s.set('theme', 'auto'); assert.equal(s.get('theme'), 'auto');
  s.set('theme', 'sepia'); assert.equal(s.get('theme'), 'sepia');
  s.set('theme', 'neon'); assert.equal(s.get('theme'), 'sepia'); // rejected -> unchanged
});

test('density: defaults to normal; predicate accepts compact|normal|spacious', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('density'), 'normal');
  s.set('density', 'compact'); assert.equal(s.get('density'), 'compact');
  s.set('density', 'spacious'); assert.equal(s.get('density'), 'spacious');
  s.set('density', 'bogus'); assert.equal(s.get('density'), 'spacious'); // rejected -> unchanged
});

test('measureCh: default 66, clamps to 48-80', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('measureCh'), 66);
  s.set('measureCh', 50); assert.equal(s.get('measureCh'), 50);
  s.set('measureCh', 90); assert.equal(s.get('measureCh'), 50); // rejected -> unchanged
  s.set('measureCh', 40); assert.equal(s.get('measureCh'), 50); // rejected -> unchanged
});

test('measureCh: legacy px contentMax migrates to the 66ch default (no px conversion)', () => {
  const s = createSettingsStore({ storage: fakeStorage({ 'viewer.settings.v1': JSON.stringify({ contentMax: 1040 }) }) });
  assert.equal(s.get('measureCh'), 66);
  assert.equal(s.get('contentMax'), undefined);
});

test('combined legacy payload {layout:classic, contentMax:N} migrates BOTH keys at once', () => {
  // The most representative real pre-redesign "classic" power-user payload
  // carried a custom layout AND a custom width. The two migration `if`s are
  // independent (settings-store.js:67,70); this pins that a single object with
  // both legacy keys migrates chrome AND measureCh together, drops both legacy
  // keys, and preserves a valid non-legacy key (theme). A future early-return
  // short-circuiting one migration on the other would otherwise pass silently.
  const s = createSettingsStore({ storage: fakeStorage({
    'viewer.settings.v1': JSON.stringify({ layout: 'classic', contentMax: 1040, theme: 'dark' }),
  }) });
  assert.equal(s.get('chrome'), 'docs');        // layout:classic -> docs
  assert.equal(s.get('measureCh'), 66);         // contentMax -> 66ch default
  assert.equal(s.get('theme'), 'dark');         // valid non-legacy key survives
  assert.equal(s.get('layout'), undefined);     // legacy key dropped
  assert.equal(s.get('contentMax'), undefined); // legacy key dropped
});
