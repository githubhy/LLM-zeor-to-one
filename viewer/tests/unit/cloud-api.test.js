const test = require('node:test');
const assert = require('node:assert/strict');
const { isAuthorized, handleGate, serializeSessionCookie, applyGateCookie, revisionOf } = require('../../lib/cloud-api');

// Minimal Request-like stub: .headers.get(name) + .url
const req = (headers = {}, url = 'https://x/') => ({
  headers: { get: (k) => headers[k.toLowerCase()] ?? null },
  url,
});

test('revisionOf is deterministic, quoted, and content-sensitive', () => {
  assert.equal(revisionOf('abc'), revisionOf('abc'));
  assert.notEqual(revisionOf('abc'), revisionOf('abd'));
  assert.match(revisionOf('abc'), /^"[0-9a-f]{8}"$/);
});

test('isAuthorized true only on exact bearer match', () => {
  assert.equal(isAuthorized('Bearer abc', 'abc'), true);
  assert.equal(isAuthorized('Bearer abc', 'abd'), false);
  assert.equal(isAuthorized('', 'abc'), false);
  assert.equal(isAuthorized(null, 'abc'), false);
  assert.equal(isAuthorized('Bearer abc', ''), false);   // empty server token never authorizes
});

test('handleGate returns null (proceed) on Authorization header match', async () => {
  assert.equal(await handleGate(req({ authorization: 'Bearer t' }), { token: 't' }), null);
});

test('handleGate returns null (proceed) on session-cookie match', async () => {
  assert.equal(await handleGate(req({ cookie: 'vt=t; other=1' }), { token: 't' }), null);
});

test('handleGate returns {setCookie} on ?k= bootstrap', async () => {
  const out = await handleGate(req({}, 'https://x/?k=t'), { token: 't' });
  assert.ok(out && !(out instanceof Response));
  assert.equal(out.setCookie, 't');
});

test('handleGate returns a generic 404 when unauthorized (no auth hint)', async () => {
  const res = await handleGate(req({ authorization: 'Bearer nope' }), { token: 't' });
  assert.equal(res.status, 404);
  assert.equal(await res.text(), 'Not found');
});

test('serializeSessionCookie is HttpOnly + Secure + SameSite + Path', () => {
  const c = serializeSessionCookie('t');
  assert.match(c, /^vt=t;/);
  for (const flag of ['HttpOnly', 'Secure', 'SameSite=Lax', 'Path=/']) assert.match(c, new RegExp(flag));
});

// applyGateCookie is the shared helper used by _middleware.js; test it directly
// so the assertion covers the real shared code, not a hand-copied replica.
// (decision 2026-06-09-07: the ?k= bootstrap response MUST carry both
// Set-Cookie and Cache-Control: no-store.)
test('applyGateCookie sets Set-Cookie AND Cache-Control: no-store (positive)', () => {
  const out = applyGateCookie(new Response('body', { status: 200 }), 't');
  assert.match(out.headers.get('Set-Cookie'), /^vt=t;/);
  assert.equal(out.headers.get('Cache-Control'), 'no-store');
});

test('applyGateCookie — untouched Response has no Cache-Control: no-store (negative)', () => {
  const plain = new Response('body', { status: 200 });
  assert.notEqual(plain.headers.get('Cache-Control'), 'no-store');
});

const {
  handleGetAnnotation, handlePutAnnotation, handleManifest, normalizeCloudDoc,
} = require('../../lib/cloud-api');

function fakeKV(initial = {}) {
  const m = new Map(Object.entries(initial));
  return {
    store: m,
    async get(k) { return m.has(k) ? m.get(k) : null; },
    async put(k, v) { m.set(k, v); },
    async list({ prefix } = {}) {
      const keys = [...m.keys()].filter((k) => !prefix || k.startsWith(prefix)).map((name) => ({ name }));
      return { keys, list_complete: true };
    },
  };
}
const putReq = (doc) => ({ headers: { get: () => null }, async json() { return doc; }, async text() { return JSON.stringify(doc); } });
const khl = (id, updatedAt, extra = {}) => ({ id, color: 'yellow', segments: [], updatedAt, ...extra });

test('normalizeCloudDoc preserves updatedAt + deleted, drops junk', () => {
  const d = normalizeCloudDoc('a.md', { highlights: [{ id: 'x', color: 'red', updatedAt: 7, deleted: true, junk: 1, segments: [{ blockLine: 3 }] }] });
  assert.equal(d.version, 1);
  assert.equal(d.highlights[0].updatedAt, 7);
  assert.equal(d.highlights[0].deleted, true);
  assert.equal(d.highlights[0].junk, undefined);
});

test('GET returns the default empty doc + ETag when KV is empty', async () => {
  const res = await handleGetAnnotation({ headers: { get: () => null } }, { kv: fakeKV(), token: 't' }, 'a.md');
  assert.equal(res.status, 200);
  assert.ok(res.headers.get('ETag'));
  const doc = await res.json();
  assert.deepEqual(doc, { version: 1, file: 'a.md', highlights: [] });
});

test('PUT merges the incoming doc into the stored doc (LWW) and 204s', async () => {
  const kv = fakeKV();
  await handlePutAnnotation(putReq({ highlights: [khl('x', 1)] }), { kv, token: 't' }, 'a.md');
  const res = await handlePutAnnotation(putReq({ highlights: [khl('x', 2, { color: 'blue' }), khl('y', 1)] }), { kv, token: 't' }, 'a.md');
  assert.equal(res.status, 204);
  assert.ok(res.headers.get('X-Annotations-Revision'));
  const stored = JSON.parse(await kv.get('ann:a.md'));
  const x = stored.highlights.find((h) => h.id === 'x');
  assert.equal(x.color, 'blue');
  assert.equal(stored.highlights.length, 2);
});

test('PUT tombstone is retained across a subsequent stale live PUT', async () => {
  const kv = fakeKV();
  await handlePutAnnotation(putReq({ highlights: [khl('x', 5, { deleted: true })] }), { kv, token: 't' }, 'a.md');
  await handlePutAnnotation(putReq({ highlights: [khl('x', 2)] }), { kv, token: 't' }, 'a.md');
  const stored = JSON.parse(await kv.get('ann:a.md'));
  assert.equal(stored.highlights.find((h) => h.id === 'x').deleted, true);
});

test('manifest aggregates LIVE highlights across files, skipping tombstones', async () => {
  const kv = fakeKV({
    'ann:a.md': JSON.stringify({ version: 1, file: 'a.md', highlights: [khl('x', 1, { excerpt: 'hi', segments: [{ blockLine: 4 }] })] }),
    'ann:b.md': JSON.stringify({ version: 1, file: 'b.md', highlights: [khl('y', 1, { deleted: true })] }),
  });
  const res = await handleManifest({ headers: { get: () => null }, url: 'https://x/api/annotations-manifest' }, { kv, token: 't' });
  const data = await res.json();
  assert.deepEqual(data.entries.map((e) => e.id), ['x']);
  assert.equal(data.entries[0].lineStart, 4);
  assert.equal(data.entries[0].backend, 'sidecar');
});

test('manifest returns a tombstone-inclusive files[] (entries still omit tombstones)', async () => {
  const kv = fakeKV({
    'ann:a.md': JSON.stringify({ version: 1, file: 'a.md', highlights: [khl('x', 1, { segments: [{ blockLine: 1 }] })] }),
    'ann:b.md': JSON.stringify({ version: 1, file: 'b.md', highlights: [khl('y', 1, { deleted: true, segments: [{ blockLine: 2 }] })] }),
  });
  const res = await handleManifest({ headers: { get: () => null }, url: 'https://x/api/annotations-manifest' }, { kv, token: 't' });
  const data = await res.json();
  assert.deepEqual([...data.files].sort(), ['a.md', 'b.md']);   // BOTH files, incl. tombstone-only b.md
  assert.deepEqual(data.entries.map((e) => e.id), ['x']);        // entries still omit the tombstone
});
