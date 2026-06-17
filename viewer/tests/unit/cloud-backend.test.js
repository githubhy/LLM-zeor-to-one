const test = require('node:test');
const assert = require('node:assert/strict');
const { createCloudBackend } = require('../../lib/backend');

function fakeRes({ ok = true, status = 200, text = '', json = null }) {
  return { ok, status, headers: { get: () => null }, text: async () => text, json: async () => json };
}
function fakeFetch(map) {
  const calls = [];
  const fn = async (url) => { calls.push(url); return map(url); };
  fn.calls = calls; return fn;
}

test('listFiles fetches files.json under base', async () => {
  const fetch = fakeFetch(() => fakeRes({ json: { files: ['a.md'], defaultFile: null } }));
  const b = createCloudBackend({ base: '/b', fetch });
  assert.deepEqual(await b.listFiles(), { files: ['a.md'], roots: null, defaultFile: null, version: null });
  assert.equal(fetch.calls[0], '/b/files.json');
});

test('getMarkdown fetches content/<file> and throws on non-ok', async () => {
  const fetch = fakeFetch((u) => u.endsWith('a.md') ? fakeRes({ text: '# A' }) : fakeRes({ ok: false, status: 404 }));
  const b = createCloudBackend({ base: '.', fetch, version: 'v1' });
  const got = await b.getMarkdown('a.md');
  assert.equal(got.text, '# A');
  assert.equal(got.revision, 'v1');
  assert.equal(fetch.calls[0], './content/a.md');
  await assert.rejects(() => b.getMarkdown('missing.md'), /404/);
});

test('getAnnotations returns null on 404, doc on hit', async () => {
  const doc = { version: 1, file: 'a.md', highlights: [] };
  const hit = createCloudBackend({ base: '.', fetch: fakeFetch(() => fakeRes({ json: doc })) });
  assert.deepEqual((await hit.getAnnotations('a.md')).doc, doc);
  const miss = createCloudBackend({ base: '.', fetch: fakeFetch(() => fakeRes({ ok: false, status: 404 })) });
  assert.equal(await miss.getAnnotations('a.md'), null);
});

test('getManifest filters by file client-side', async () => {
  const all = { entries: [{ id: '1', file: 'a.md' }, { id: '2', file: 'b.md' }] };
  const b = createCloudBackend({ base: '.', fetch: fakeFetch(() => fakeRes({ json: all })) });
  assert.deepEqual((await b.getManifest('a.md')).entries, [{ id: '1', file: 'a.md' }]);
  assert.equal((await b.getManifest()).entries.length, 2);
});

test('getGitInfo returns the baked info; never rejects', async () => {
  const info = { available: true, sha: 'abc' };
  const ok = createCloudBackend({ base: '.', fetch: fakeFetch(() => fakeRes({ json: info })) });
  assert.deepEqual(await ok.getGitInfo(), info);
  const boom = createCloudBackend({ base: '.', fetch: fakeFetch(() => { throw new Error('x'); }) });
  assert.equal((await boom.getGitInfo()).available, false);
});

test('writes return read-only; connectLiveReload is a no-op', async () => {
  const b = createCloudBackend({ base: '.', fetch: fakeFetch(() => fakeRes({})) });
  assert.deepEqual(await b.putMarkdown('a.md', 'x', null), { ok: false, status: 'read-only', conflict: false });
  const h = b.connectLiveReload({ onMessage() {}, onClose() {} });
  assert.equal(typeof h.close, 'function'); h.close();
  assert.equal(b.kind, 'cloud');
});
