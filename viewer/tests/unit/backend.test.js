const test = require('node:test');
const assert = require('node:assert/strict');
const { createLocalServerBackend } = require('../../lib/backend');

// Minimal fake Response. headers is a Map-like with .get().
function fakeRes({ ok = true, status = 200, text = '', json = null, headers = {} }) {
  const h = new Map(Object.entries(headers));
  return {
    ok,
    status,
    headers: { get: (k) => (h.has(k) ? h.get(k) : null) },
    text: async () => text,
    json: async () => json,
  };
}

// Records calls and returns queued responses.
function fakeFetch(responder) {
  const calls = [];
  const fn = async (url, opts) => {
    calls.push({ url, opts });
    return responder(url, opts);
  };
  fn.calls = calls;
  return fn;
}

test('listFiles returns files + defaultFile', async () => {
  const fetch = fakeFetch(() => fakeRes({ json: { files: ['a.md', 'b.md'], defaultFile: 'a.md' } }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.listFiles();
  assert.deepEqual(out, { files: ['a.md', 'b.md'], roots: null, defaultFile: 'a.md' });
  assert.equal(fetch.calls[0].url, '/api/files');
});

test('getMarkdown returns text + revision from ETag', async () => {
  const fetch = fakeFetch(() => fakeRes({ text: '# Hi', headers: { ETag: '"abc"' } }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.getMarkdown('dir/x.md');
  assert.equal(out.text, '# Hi');
  assert.equal(out.revision, '"abc"');
  assert.equal(fetch.calls[0].url, '/api/md/dir%2Fx.md');
});

test('getMarkdown throws on non-ok', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: false, status: 404 }));
  const backend = createLocalServerBackend({ fetch });
  await assert.rejects(() => backend.getMarkdown('missing.md'), /404/);
});

test('putMarkdown sends If-Match and reports conflict on 409', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: false, status: 409, headers: { ETag: '"new"' } }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.putMarkdown('x.md', 'body', '"old"');
  assert.equal(out.ok, false);
  assert.equal(out.status, 409);
  assert.equal(out.conflict, true);
  assert.equal(out.revision, '"new"');
  assert.equal(fetch.calls[0].opts.method, 'PUT');
  assert.equal(fetch.calls[0].opts.headers['If-Match'], '"old"');
});

test('putMarkdown never throws — network error becomes ok:false', async () => {
  const fetch = fakeFetch(() => { throw new Error('offline'); });
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.putMarkdown('x.md', 'body', null);
  assert.equal(out.ok, false);
  assert.equal(out.conflict, false);
});

test('putMarkdown omits If-Match when no revision given (204 success)', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: true, status: 204 }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.putMarkdown('x.md', 'body');
  assert.equal(out.ok, true);
  assert.equal(out.status, 204);
  assert.equal(fetch.calls[0].opts.headers['If-Match'], undefined);
});

test('getAnnotations returns doc + revision from X-Annotations-Revision', async () => {
  const doc = { version: 1, file: 'x.md', highlights: [] };
  const fetch = fakeFetch(() => fakeRes({ json: doc, headers: { 'X-Annotations-Revision': '"r1"' } }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.getAnnotations('x.md');
  assert.deepEqual(out.doc, doc);
  assert.equal(out.revision, '"r1"');
  assert.equal(fetch.calls[0].url, '/api/highlights/x.md');
});

test('getAnnotations returns null on non-ok', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: false, status: 404 }));
  const backend = createLocalServerBackend({ fetch });
  assert.equal(await backend.getAnnotations('x.md'), null);
});

test('putAnnotations sends If-Match + X-Document-Revision, 204 ok', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: true, status: 204, headers: { 'X-Annotations-Revision': '"r2"' } }));
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.putAnnotations('x.md', { highlights: [] }, '"r1"', '"doc1"');
  assert.equal(out.ok, true);
  assert.equal(out.status, 204);
  assert.equal(out.revision, '"r2"');
  assert.equal(out.conflict, false);
  assert.equal(fetch.calls[0].opts.headers['If-Match'], '"r1"');
  assert.equal(fetch.calls[0].opts.headers['X-Document-Revision'], '"doc1"');
});

test('getManifest with file uses query param; without file fetches all', async () => {
  const fetch = fakeFetch(() => fakeRes({ json: { entries: [{ id: 'h1' }] } }));
  const backend = createLocalServerBackend({ fetch });
  const one = await backend.getManifest('dir/x.md');
  assert.deepEqual(one.entries, [{ id: 'h1' }]);
  assert.equal(fetch.calls[0].url, '/api/highlights-manifest?file=dir%2Fx.md');
  await backend.getManifest();
  assert.equal(fetch.calls[1].url, '/api/highlights-manifest');
});

test('getManifest returns null on non-ok', async () => {
  const fetch = fakeFetch(() => fakeRes({ ok: false, status: 500 }));
  const backend = createLocalServerBackend({ fetch });
  assert.equal(await backend.getManifest('x.md'), null);
});

test('getGitInfo returns parsed info on ok', async () => {
  const info = { available: true, owner: 'a', repo: 'r', sha: 'deadbeef' };
  const fetch = fakeFetch(() => fakeRes({ json: info }));
  const backend = createLocalServerBackend({ fetch });
  assert.deepEqual(await backend.getGitInfo(), info);
  assert.equal(fetch.calls[0].url, '/api/git-info');
  assert.equal(fetch.calls[0].opts.cache, 'no-store');
});

test('getGitInfo never throws — returns available:false on error', async () => {
  const fetch = fakeFetch(() => { throw new Error('boom'); });
  const backend = createLocalServerBackend({ fetch });
  const out = await backend.getGitInfo();
  assert.equal(out.available, false);
  assert.match(out.reason, /boom/);
});

test('connectLiveReload parses frames to onMessage and fires onClose', async () => {
  const listeners = {};
  class FakeWS {
    constructor(url) { this.url = url; FakeWS.last = this; }
    addEventListener(type, cb) { listeners[type] = cb; }
    close() { if (listeners.close) listeners.close(); }
  }
  const backend = createLocalServerBackend({
    WebSocketImpl: FakeWS,
    getLocation: () => ({ protocol: 'http:', host: 'localhost:3000' }),
  });
  const seen = [];
  let closed = false;
  const handle = backend.connectLiveReload({
    onMessage: (m) => seen.push(m),
    onClose: () => { closed = true; },
  });
  assert.equal(FakeWS.last.url, 'ws://localhost:3000');
  listeners.message({ data: JSON.stringify({ type: 'change', target: 'markdown', file: 'x.md' }) });
  listeners.message({ data: 'not json' }); // ignored, no throw
  assert.deepEqual(seen, [{ type: 'change', target: 'markdown', file: 'x.md' }]);
  handle.close();
  assert.equal(closed, true);
});

test('connectLiveReload uses wss for https', async () => {
  class FakeWS { constructor(url) { FakeWS.last = this; this.url = url; } addEventListener() {} close() {} }
  const backend = createLocalServerBackend({
    WebSocketImpl: FakeWS,
    getLocation: () => ({ protocol: 'https:', host: 'example.com' }),
  });
  backend.connectLiveReload({});
  assert.equal(FakeWS.last.url, 'wss://example.com');
});
