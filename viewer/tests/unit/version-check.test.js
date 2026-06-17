const test = require('node:test');
const assert = require('node:assert/strict');
const { shouldNudgeReload, nextLastSeen } = require('../../lib/version-check');

// shouldNudgeReload(current, lastSeen) → true iff both truthy AND different
test('shouldNudgeReload: different versions → true', () => {
  assert.equal(shouldNudgeReload('b', 'a'), true);
});
test('shouldNudgeReload: same version → false', () => {
  assert.equal(shouldNudgeReload('a', 'a'), false);
});
test('shouldNudgeReload: lastSeen null (first run) → false', () => {
  assert.equal(shouldNudgeReload('a', null), false);
});
test('shouldNudgeReload: lastSeen undefined → false', () => {
  assert.equal(shouldNudgeReload('a', undefined), false);
});
test('shouldNudgeReload: current null → false', () => {
  assert.equal(shouldNudgeReload(null, 'a'), false);
});
test('shouldNudgeReload: current empty string → false', () => {
  assert.equal(shouldNudgeReload('', 'a'), false);
});
test('shouldNudgeReload: current undefined → false', () => {
  assert.equal(shouldNudgeReload(undefined, 'a'), false);
});

// nextLastSeen(current, lastSeen) → current if truthy, else lastSeen
test('nextLastSeen: current truthy → returns current', () => {
  assert.equal(nextLastSeen('b', 'a'), 'b');
});
test('nextLastSeen: current null → returns lastSeen', () => {
  assert.equal(nextLastSeen(null, 'a'), 'a');
});
test('nextLastSeen: current undefined → returns lastSeen', () => {
  assert.equal(nextLastSeen(undefined, 'a'), 'a');
});
test('nextLastSeen: current empty string → returns lastSeen', () => {
  assert.equal(nextLastSeen('', 'a'), 'a');
});
