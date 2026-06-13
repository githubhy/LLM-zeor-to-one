// viewer/lib/settings-store.js
// Namespaced, schema-validated settings store (spec 2026-06-10 section 3).
// Pure module: storage is injected; no DOM, no globals touched.
(function (root) {
  'use strict';

  const SETTINGS_KEY = 'viewer.settings.v1';

  const SCHEMA = {
    layout:              { def: 'reader', ok: (v) => v === 'reader' || v === 'classic' },
    theme:               { def: 'light',  ok: (v) => v === 'light' || v === 'sepia' || v === 'dark' },
    fontScale:           { def: 1.0,      ok: (v) => typeof v === 'number' && v >= 0.8 && v <= 1.4 },
    lineHeight:          { def: 1.7,      ok: (v) => typeof v === 'number' && v >= 1.3 && v <= 2.1 },
    contentMax:          { def: 860,      ok: (v) => typeof v === 'number' && v >= 600 && v <= 1200 },
    fontFamily:          { def: 'sans',   ok: (v) => v === 'sans' || v === 'serif' },
    scrollFx:            { def: true,     ok: (v) => typeof v === 'boolean' },
    updateFx:            { def: true,     ok: (v) => typeof v === 'boolean' },
    noteMarker:          { def: 'icon',   ok: (v) => v === 'icon' || v === 'ring' },
    readingProgress:     { def: true,     ok: (v) => typeof v === 'boolean' },
    readingProgressMode: { def: 'doc',    ok: (v) => v === 'doc' || v === 'section' },
    citationMode:        { def: 'github', ok: (v) => v === 'github' || v === 'local' || v === 'relative' },
  };

  // [legacyKey, schemaKey, parse]
  const LEGACY = [
    ['viewer-scroll-fx',             'scrollFx',            (v) => v !== 'off'],
    ['viewer-update-fx',             'updateFx',            (v) => v !== 'off'],
    ['viewer-note-marker',           'noteMarker',          (v) => (v === 'ring' ? 'ring' : 'icon')],
    ['viewer-reading-progress',      'readingProgress',     (v) => v !== 'off'],
    ['viewer-reading-progress-mode', 'readingProgressMode', (v) => (v === 'section' ? 'section' : 'doc')],
    ['viewer-citation-mode',         'citationMode',        (v) => v],
  ];

  function createSettingsStore(opts) {
    const storage = opts.storage;
    const subs = new Set();

    function defaults() {
      const o = {};
      for (const k of Object.keys(SCHEMA)) o[k] = SCHEMA[k].def;
      return o;
    }

    function load() {
      const raw = storage.getItem(SETTINGS_KEY);
      if (raw == null) return null;
      try {
        const parsed = JSON.parse(raw);
        if (typeof parsed !== 'object' || parsed === null) return null;
        const o = defaults();
        for (const k of Object.keys(SCHEMA)) {
          if (k in parsed && SCHEMA[k].ok(parsed[k])) o[k] = parsed[k];
        }
        return o;
      } catch (e) { return null; }
    }

    let state = load();
    if (state == null) {
      state = defaults();
      // One-time legacy migration (when the namespaced key is absent or unreadable).
      for (const [legacyKey, key, parse] of LEGACY) {
        const raw = storage.getItem(legacyKey);
        if (raw == null) continue;
        const v = parse(raw);
        if (SCHEMA[key].ok(v)) state[key] = v;
      }
      // Only drop the legacy keys once the namespaced write actually landed
      // (quota-full / private-mode storage must not eat the user's prefs).
      if (persist()) {
        for (const [legacyKey] of LEGACY) storage.removeItem(legacyKey);
      }
    }

    function persist() {
      try { storage.setItem(SETTINGS_KEY, JSON.stringify(state)); return true; }
      catch (e) { return false; }
    }

    function get(key) { return state[key]; }
    function getAll() { return Object.assign({}, state); }
    function set(key, value) {
      if (!(key in SCHEMA) || !SCHEMA[key].ok(value) || state[key] === value) return;
      state[key] = value;
      persist();
      subs.forEach((fn) => { try { fn(key, value); } catch (e) { /* subscriber fault isolated */ } });
    }
    function subscribe(fn) { subs.add(fn); return () => subs.delete(fn); }

    return { get, getAll, set, subscribe };
  }

  const api = { createSettingsStore, SETTINGS_KEY };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) { root.createSettingsStore = createSettingsStore; root.SETTINGS_KEY = SETTINGS_KEY; }
})(typeof window !== 'undefined' ? window : null);
