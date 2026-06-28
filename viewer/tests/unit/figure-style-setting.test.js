'use strict';
// Unit tests for the `figureStyle` settings-store key (default, validation,
// persistence). Mirrors tests/unit/settings-store.test.js fakeStorage pattern.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createSettingsStore } = require('../../lib/settings-store.js');

function fakeStorage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}

test('figureStyle defaults to colour-academic', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  assert.equal(s.get('figureStyle'), 'colour-academic');
});

test('figureStyle accepts every curated id', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  for (const id of ['colour-academic', 'monochrome', 'minimal', 'swimlane', 'image']) {
    s.set('figureStyle', id);
    assert.equal(s.get('figureStyle'), id);
  }
});

test('figureStyle rejects an unknown id (value unchanged)', () => {
  const s = createSettingsStore({ storage: fakeStorage() });
  s.set('figureStyle', 'swimlane');
  s.set('figureStyle', 'rainbow');
  assert.equal(s.get('figureStyle'), 'swimlane');
});

test('figureStyle persists across a reload', () => {
  const storage = fakeStorage();
  createSettingsStore({ storage }).set('figureStyle', 'minimal');
  assert.equal(createSettingsStore({ storage }).get('figureStyle'), 'minimal');
});
