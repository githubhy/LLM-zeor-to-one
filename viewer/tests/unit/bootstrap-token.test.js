const test = require('node:test');
const assert = require('node:assert/strict');
const { bootstrapToken } = require('../../lib/backend');

function fakeStore() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), _m: m }; }

test('bootstrapToken stashes ?k=, strips it, returns the token', () => {
  const ls = fakeStore();
  let replaced = null;
  const token = bootstrapToken({
    location: { search: '?k=SECRET', href: 'https://x/page?k=SECRET', pathname: '/page' },
    localStorage: ls,
    history: { replaceState: (_s, _t, url) => { replaced = url; } },
  });
  assert.equal(token, 'SECRET');
  assert.equal(ls.getItem('viewer:token'), 'SECRET');
  assert.ok(replaced && !/[?&]k=/.test(replaced));
});

test('bootstrapToken returns the stored token when no ?k=', () => {
  const ls = fakeStore(); ls.setItem('viewer:token', 'OLD');
  const token = bootstrapToken({ location: { search: '', pathname: '/' }, localStorage: ls, history: { replaceState() {} } });
  assert.equal(token, 'OLD');
});

test('bootstrapToken returns null and never throws when nothing is available', () => {
  assert.equal(bootstrapToken({}), null);
  assert.equal(bootstrapToken({ location: { search: '' } }), null);
});
