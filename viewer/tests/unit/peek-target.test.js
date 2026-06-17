const test = require('node:test');
const assert = require('node:assert/strict');
const { parsePeekHref } = require('../../lib/peek-target');

test('parsePeekHref: equation/citation/section same-file refs', () => {
  assert.deepEqual(parsePeekHref('#eq-1'), { kind: 'eq', id: '1', sameFile: true });
  assert.deepEqual(parsePeekHref('#ref-12'), { kind: 'ref', id: '12', sameFile: true });
  assert.deepEqual(parsePeekHref('#sec-D.5'), { kind: 'sec', id: 'D.5', sameFile: true });
  assert.deepEqual(parsePeekHref('#sec-3.7.6-step-3'), { kind: 'sec', id: '3.7.6-step-3', sameFile: true });
});

test('parsePeekHref: cross-file refs are not peekable', () => {
  assert.deepEqual(parsePeekHref('other.md#eq-5'), { kind: null, id: null, sameFile: false });
  assert.deepEqual(parsePeekHref('appendix-d.md#sec-D.5'), { kind: null, id: null, sameFile: false });
});

test('parsePeekHref: non-peekable same-file anchors and junk → kind null', () => {
  assert.deepEqual(parsePeekHref('#p-intro-1'), { kind: null, id: null, sameFile: true });
  assert.deepEqual(parsePeekHref('#some-heading'), { kind: null, id: null, sameFile: true });
  assert.deepEqual(parsePeekHref(''), { kind: null, id: null, sameFile: false });
  assert.deepEqual(parsePeekHref(null), { kind: null, id: null, sameFile: false });
});
