const test = require('node:test');
const assert = require('node:assert/strict');
const { nextPositionMode, formatPosition } = require('../../lib/reading-position');

test('nextPositionMode cycles through the mode list and wraps', () => {
  const modes = ['percent', 'section'];
  assert.equal(nextPositionMode('percent', modes), 'section');
  assert.equal(nextPositionMode('section', modes), 'percent');
  assert.equal(nextPositionMode('bogus', modes), 'percent');   // unknown → first
});

test('formatPosition renders each mode', () => {
  assert.equal(formatPosition('percent', { pct: 38, section: '3.7 Decoding' }), '38%');
  assert.equal(formatPosition('section', { pct: 38, section: '3.7 Decoding' }), '3.7 Decoding');
  assert.equal(formatPosition('section', { pct: 38, section: '' }), '38%'); // no heading → fall back to %
});
