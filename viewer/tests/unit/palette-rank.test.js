const test = require('node:test');
const assert = require('node:assert/strict');
const { fuzzyScore, rankItems } = require('../../lib/palette-rank');

test('fuzzyScore: exact subsequence matches, non-subsequence is null', () => {
  assert.ok(fuzzyScore('abc', 'abc'));
  assert.deepEqual(fuzzyScore('abc', 'abc').positions, [0, 1, 2]);
  assert.ok(fuzzyScore('ac', 'abc'));
  assert.deepEqual(fuzzyScore('ac', 'abc').positions, [0, 2]);
  assert.equal(fuzzyScore('xyz', 'abc'), null);
  assert.equal(fuzzyScore('abcd', 'abc'), null); // query longer than any subsequence
});

test('fuzzyScore: empty query matches everything at score 0', () => {
  const r = fuzzyScore('', 'anything');
  assert.equal(r.score, 0);
  assert.deepEqual(r.positions, []);
});

test('fuzzyScore: case-insensitive', () => {
  assert.ok(fuzzyScore('LDPC', 'ldpc-intro.md'));
  assert.ok(fuzzyScore('ldpc', 'LDPC-Intro.md'));
});

test('fuzzyScore: consecutive run beats scattered match', () => {
  const consec = fuzzyScore('abc', 'abcxx').score;
  const scattered = fuzzyScore('abc', 'axbxc').score;
  assert.ok(consec > scattered, `consecutive ${consec} should beat scattered ${scattered}`);
});

test('fuzzyScore: word-boundary start beats mid-word start', () => {
  const boundary = fuzzyScore('fo', 'foo-bar').score;   // f at index 0
  const midword  = fuzzyScore('fo', 'xfoo').score;       // f at index 1 (after 'x')
  assert.ok(boundary > midword, `boundary ${boundary} should beat midword ${midword}`);
});

test('rankItems: filters non-matches, orders by score, respects limit', () => {
  const items = [
    { text: 'other.md' },
    { text: '5g-nr-ldpc/intro.md' },
    { text: 'ldpc-notes.md' },
  ];
  const ranked = rankItems('ldpc', items, { key: 'text', limit: 10 });
  assert.equal(ranked.length, 2);                        // 'other.md' filtered out
  assert.ok(ranked.every(r => Array.isArray(r.positions)));
  // 'ldpc-notes.md' (boundary, consecutive run at start) ranks above the nested path.
  assert.equal(ranked[0].text, 'ldpc-notes.md');
  const capped = rankItems('', items, { key: 'text', limit: 2 });
  assert.equal(capped.length, 2);                        // empty query → all, capped
});

test('rankItems: empty query preserves original order (stable)', () => {
  const items = [{ text: 'a' }, { text: 'b' }, { text: 'c' }];
  const ranked = rankItems('', items, { key: 'text' });
  assert.deepEqual(ranked.map(r => r.text), ['a', 'b', 'c']);
});

test('rankItems: preserves item fields and adds score/positions', () => {
  const ranked = rankItems('a', [{ text: 'abc', id: 7, run: 'X' }], { key: 'text' });
  assert.equal(ranked[0].id, 7);
  assert.equal(ranked[0].run, 'X');
  assert.equal(typeof ranked[0].score, 'number');
});
