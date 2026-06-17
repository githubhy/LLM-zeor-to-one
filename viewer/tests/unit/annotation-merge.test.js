const test = require('node:test');
const assert = require('node:assert/strict');
const { mergeHighlights, mergeDocs, liveHighlights } = require('../../lib/annotation-merge');

const hl = (id, updatedAt, extra = {}) => ({ id, color: 'yellow', updatedAt, ...extra });

test('disjoint sets union by id', () => {
  const out = mergeHighlights([hl('a', 1)], [hl('b', 1)]);
  assert.deepEqual(out.map((h) => h.id).sort(), ['a', 'b']);
});
test('same id: newer updatedAt wins', () => {
  const out = mergeHighlights([hl('a', 1, { color: 'red' })], [hl('a', 2, { color: 'blue' })]);
  assert.equal(out.length, 1);
  assert.equal(out[0].color, 'blue');
});
test('newer tombstone beats older live and is retained', () => {
  const out = mergeHighlights([hl('a', 1)], [hl('a', 2, { deleted: true })]);
  assert.equal(out.length, 1);
  assert.equal(out[0].deleted, true);
});
test('older tombstone loses to newer live (re-created)', () => {
  const out = mergeHighlights([hl('a', 5)], [hl('a', 2, { deleted: true })]);
  assert.equal(out.length, 1);
  assert.equal(out[0].deleted, undefined);
});
test('missing updatedAt treated as 0 (oldest)', () => {
  const out = mergeHighlights([hl('a', undefined, { color: 'red' })], [hl('a', 1, { color: 'blue' })]);
  assert.equal(out[0].color, 'blue');
});
test('mergeDocs wraps merged highlights with version+file', () => {
  const doc = mergeDocs({ highlights: [hl('a', 1)] }, { highlights: [hl('b', 1)] }, 'x.md');
  assert.equal(doc.version, 1);
  assert.equal(doc.file, 'x.md');
  assert.deepEqual(doc.highlights.map((h) => h.id).sort(), ['a', 'b']);
});
test('liveHighlights drops tombstones', () => {
  assert.deepEqual(liveHighlights({ highlights: [hl('a', 1), hl('b', 2, { deleted: true })] }).map((h) => h.id), ['a']);
});
