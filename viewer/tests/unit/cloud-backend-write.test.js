const test = require('node:test');
const assert = require('node:assert/strict');
const { createCloudBackend } = require('../../lib/backend');

function fakeRes({ ok = true, status = 200, headers = {} }) {
  return { ok, status, headers: { get: (k) => headers[k] ?? null }, async text() { return ''; }, async json() { return {}; } };
}
function recordingFetch(res) { const calls = []; const fn = async (url, opts) => { calls.push({ url, opts }); return res; }; fn.calls = calls; return fn; }

test('every cloud request carries Authorization: Bearer <token>', async () => {
  const fetch = recordingFetch(fakeRes({ headers: {} }));
  const b = createCloudBackend({ base: '/b', token: 'TOK', fetch });
  await b.getMarkdown('a.md').catch(() => {});
  assert.equal(fetch.calls[0].opts.headers.Authorization, 'Bearer TOK');
});

test('putAnnotations PUTs JSON to /api/annotations/<file> and reports revision', async () => {
  const fetch = recordingFetch(fakeRes({ ok: true, status: 204, headers: { 'X-Annotations-Revision': '"abc"' } }));
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch });
  const out = await b.putAnnotations('a.md', { highlights: [] }, null, null);
  assert.deepEqual(out, { ok: true, status: 204, revision: '"abc"', conflict: false });
  const call = fetch.calls.find((c) => c.url.includes('/api/annotations/'));
  assert.equal(call.opts.method, 'PUT');
  assert.equal(call.opts.headers.Authorization, 'Bearer TOK');
  assert.equal(call.url, './api/annotations/a.md');
});

test('getAnnotations reads the LIVE API and returns {doc, revision}', async () => {
  const fetch = recordingFetch({ ok: true, status: 200, headers: { get: (k) => (k === 'X-Annotations-Revision' ? '"r9"' : null) }, async json() { return { version: 1, file: 'a.md', highlights: [{ id: 'x' }] }; } });
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch });
  const out = await b.getAnnotations('a.md');
  assert.equal(out.revision, '"r9"');
  assert.deepEqual(out.doc.highlights.map((h) => h.id), ['x']);
  assert.equal(fetch.calls[0].url, './api/annotations/a.md');
  assert.equal(fetch.calls[0].opts.headers.Authorization, 'Bearer TOK');
});

test('getManifest reads the LIVE API and filters by file', async () => {
  const fetch = recordingFetch({ ok: true, status: 200, headers: { get: () => null }, async json() { return { entries: [{ id: '1', file: 'a.md' }, { id: '2', file: 'b.md' }] }; } });
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch });
  assert.deepEqual((await b.getManifest('a.md')).entries, [{ id: '1', file: 'a.md' }]);
  assert.equal(fetch.calls[0].url, './api/annotations-manifest');
});

test('putMarkdown stays read-only', async () => {
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch: recordingFetch(fakeRes({})) });
  assert.deepEqual(await b.putMarkdown('a.md', 'x', null), { ok: false, status: 'read-only', conflict: false });
});

// ---------------------------------------------------------------------------
// Queue injection tests
// ---------------------------------------------------------------------------

function fakeWriteQueue() {
  const items = [];
  return {
    items,
    enqueue: async (item) => { items.push(item); },
    drain: async () => {},
    size: async () => items.length,
  };
}

test('(a) fetch throws + queue present → queued:true and item enqueued', async () => {
  const throwingFetch = async () => { throw new Error('net'); };
  const q = fakeWriteQueue();
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch: throwingFetch, writeQueue: q });
  const doc = { version: 1, file: 'a.md', highlights: [] };
  const out = await b.putAnnotations('a.md', doc, null, null);
  assert.deepEqual(out, { ok: true, queued: true, status: 0, conflict: false, revision: null });
  assert.equal(q.items.length, 1);
  assert.equal(q.items[0].file, 'a.md');
  assert.deepEqual(q.items[0].doc, doc);
});

test('(b) fetch throws + queue enqueue rejects → dropped:true, ok:false', async () => {
  const throwingFetch = async () => { throw new Error('net'); };
  const rejectingQueue = {
    enqueue: async () => { throw new Error('quota'); },
    drain: async () => {},
    size: async () => 0,
  };
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch: throwingFetch, writeQueue: rejectingQueue });
  const out = await b.putAnnotations('a.md', {}, null, null);
  assert.equal(out.ok, false);
  assert.equal(out.dropped, true);
  assert.equal(out.status, 'offline+storage-unavailable');
  assert.equal(out.conflict, false);
});

test('(c) fetch resolves 409 → conflict shape, queue not called', async () => {
  const fetch = recordingFetch(fakeRes({ ok: false, status: 409, headers: {} }));
  const q = fakeWriteQueue();
  const b = createCloudBackend({ base: '.', token: 'TOK', fetch, writeQueue: q });
  const out = await b.putAnnotations('a.md', {}, null, null);
  assert.equal(out.ok, false);
  assert.equal(out.conflict, true);
  assert.equal(out.status, 409);
  assert.equal(q.items.length, 0);
});
