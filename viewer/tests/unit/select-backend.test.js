const test = require('node:test');
const assert = require('node:assert/strict');
const { selectBackend } = require('../../lib/backend');

test('defaults to local-server when no VIEWER_CONFIG', () => {
  assert.equal(selectBackend({}).kind, 'local-server');
});
test('selects cloud when VIEWER_CONFIG.backend === "cloud"', () => {
  assert.equal(selectBackend({ VIEWER_CONFIG: { backend: 'cloud', base: '.' } }).kind, 'cloud');
});
test('ignores unknown backend values (falls back to local)', () => {
  assert.equal(selectBackend({ VIEWER_CONFIG: { backend: 'martian' } }).kind, 'local-server');
});
test('handles null/undefined global gracefully', () => {
  assert.equal(selectBackend(null).kind, 'local-server');
  assert.equal(selectBackend(undefined).kind, 'local-server');
});
