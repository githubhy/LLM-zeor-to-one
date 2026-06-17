const test = require('node:test');
const assert = require('node:assert/strict');
const ss = require('../../lib/scroll-sync');

test('clamp01 clamps and rejects non-finite', () => {
  assert.equal(ss.clamp01(-0.5), 0);
  assert.equal(ss.clamp01(0), 0);
  assert.equal(ss.clamp01(0.42), 0.42);
  assert.equal(ss.clamp01(1), 1);
  assert.equal(ss.clamp01(1.7), 1);
  assert.equal(ss.clamp01(NaN), 0);
  assert.equal(ss.clamp01('x'), 0);
});

test('computeActiveHeadingIndex: empty/non-array -> -1', () => {
  assert.equal(ss.computeActiveHeadingIndex([], 100), -1);
  assert.equal(ss.computeActiveHeadingIndex(null, 100), -1);
  assert.equal(ss.computeActiveHeadingIndex(undefined, 100), -1);
});

test('computeActiveHeadingIndex: above first heading -> 0 (clamp to first)', () => {
  assert.equal(ss.computeActiveHeadingIndex([200, 600, 1200], 50), 0);
});

test('computeActiveHeadingIndex: exactly on a heading top -> that index', () => {
  assert.equal(ss.computeActiveHeadingIndex([200, 600, 1200], 600), 1);
});

test('computeActiveHeadingIndex: between two headings -> lower index', () => {
  assert.equal(ss.computeActiveHeadingIndex([200, 600, 1200], 900), 1);
});

test('computeActiveHeadingIndex: past last -> last index', () => {
  assert.equal(ss.computeActiveHeadingIndex([200, 600, 1200], 99999), 2);
});

test('computeProgress whole-doc: top 0, mid ~0.5, bottom 1', () => {
  assert.equal(ss.computeProgress({ mode: 'whole-doc', scrollTop: 0, viewport: 800, docHeight: 2800 }), 0);
  assert.equal(ss.computeProgress({ mode: 'whole-doc', scrollTop: 1000, viewport: 800, docHeight: 2800 }), 0.5);
  assert.equal(ss.computeProgress({ mode: 'whole-doc', scrollTop: 2000, viewport: 800, docHeight: 2800 }), 1);
});

test('computeProgress whole-doc: not scrollable -> 0', () => {
  assert.equal(ss.computeProgress({ mode: 'whole-doc', scrollTop: 0, viewport: 900, docHeight: 600 }), 0);
});

test('computeProgress section: start ~0, within, clamped at end', () => {
  const base = { mode: 'section', viewport: 800, docHeight: 5000, scanThreshold: 0 };
  assert.equal(ss.computeProgress({ ...base, scrollTop: 1000, sectionTop: 1000, sectionBottom: 2000 }), 0);
  assert.equal(ss.computeProgress({ ...base, scrollTop: 1500, sectionTop: 1000, sectionBottom: 2000 }), 0.5);
  assert.equal(ss.computeProgress({ ...base, scrollTop: 2600, sectionTop: 1000, sectionBottom: 2000 }), 1);
});

test('computeProgress section: scanThreshold offsets the read line', () => {
  assert.equal(
    ss.computeProgress({ mode: 'section', scrollTop: 1000, viewport: 800, docHeight: 5000,
      scanThreshold: 80, sectionTop: 1000, sectionBottom: 1800 }),
    0.1,
  );
});

test('computeProgress section: missing section data -> whole-doc fallback', () => {
  assert.equal(
    ss.computeProgress({ mode: 'section', scrollTop: 1000, viewport: 800, docHeight: 2800 }),
    0.5,
  );
});
