const test = require('node:test');
const assert = require('node:assert/strict');
const shared = require('../../lib/highlight-shared');

// Regression for the duplicate-heading-anchor bug: two headings with identical
// text (`##### Noise Bandwidth` under § 8.1.1 and again under § 8.1.3) both
// slugified to `noise-bandwidth`, producing two DOM nodes with the same id.
// getElementById then resolved every "Noise Bandwidth" link to the first one
// (§ 8.1.1), so clicking the § 8.1.3 outline entry jumped to § 8.1.1.
// makeUniqueSlugger() de-duplicates GitHub-compatibly within one document.

test('duplicate heading text gets GitHub-style numeric suffixes', () => {
  const slug = shared.makeUniqueSlugger();
  assert.equal(slug('Noise Bandwidth'), 'noise-bandwidth');
  assert.equal(slug('Noise Bandwidth'), 'noise-bandwidth-1');
});

test('a single occurrence keeps the bare slug (existing anchors stay stable)', () => {
  const slug = shared.makeUniqueSlugger();
  assert.equal(slug('Steady-State Errors'), 'steady-state-errors');
});

test('three or more duplicates increment -1, -2 like GitHub', () => {
  const slug = shared.makeUniqueSlugger();
  assert.equal(slug('Summary'), 'summary');
  assert.equal(slug('Summary'), 'summary-1');
  assert.equal(slug('Summary'), 'summary-2');
});

test('each slugger instance is independent (per-render reset)', () => {
  const a = shared.makeUniqueSlugger();
  const b = shared.makeUniqueSlugger();
  assert.equal(a('Overview'), 'overview');
  assert.equal(b('Overview'), 'overview');
});

test('never emits a duplicate id even on manufactured cross-collision', () => {
  // "Foo 1" slugifies to `foo-1`, which the 2nd "Foo" already claimed.
  // GitHub is itself non-unique here; we bump further so the DOM id is
  // always unique (navigation correctness > byte-parity in this corner).
  const slug = shared.makeUniqueSlugger();
  assert.equal(slug('Foo'), 'foo');
  assert.equal(slug('Foo'), 'foo-1');
  const third = slug('Foo 1');
  assert.equal(third, 'foo-1-1');
});
