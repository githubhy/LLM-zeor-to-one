const test = require('node:test');
const assert = require('node:assert/strict');
const os = require('os'); const fs = require('fs'); const path = require('path');
const { pullAnnotations, pushAnnotations } = require('../../pull-annotations');

function mockFetch(routes) {
  return async (url) => {
    const key = Object.keys(routes).find((r) => url.endsWith(r));
    const body = key ? routes[key] : null;
    return { ok: body != null, status: body != null ? 200 : 404, async json() { return body; } };
  };
}

test('pull writes a new cloud highlight into the local sidecar', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pull-'));
  const fetch = mockFetch({
    '/api/annotations-manifest': { entries: [{ id: 'x', file: 'a.md' }] },
    '/api/annotations/a.md': { version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 5, segments: [] }] },
  });
  const summary = await pullAnnotations({ base: 'https://c', token: 'T', sidecarDir: dir, fetch });
  const onDisk = JSON.parse(fs.readFileSync(path.join(dir, 'a.md.json'), 'utf8'));
  assert.equal(onDisk.highlights.find((h) => h.id === 'x').updatedAt, 5);
  assert.equal(summary.filesChanged, 1);
});

test('pull tombstone removes a local live highlight (retained as tombstone)', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pull-'));
  fs.writeFileSync(path.join(dir, 'a.md.json'), JSON.stringify({ version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 1, segments: [] }] }));
  const fetch = mockFetch({
    '/api/annotations-manifest': { entries: [{ id: 'x', file: 'a.md' }] },
    '/api/annotations/a.md': { version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 9, deleted: true, segments: [] }] },
  });
  await pullAnnotations({ base: 'https://c', token: 'T', sidecarDir: dir, fetch });
  const onDisk = JSON.parse(fs.readFileSync(path.join(dir, 'a.md.json'), 'utf8'));
  assert.equal(onDisk.highlights.find((h) => h.id === 'x').deleted, true);
});

test('push PUTs each local sidecar to the live API with the bearer header', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'push-'));
  fs.writeFileSync(path.join(dir, 'a.md.json'), JSON.stringify({ version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 1, segments: [] }] }));
  const calls = [];
  const fetch = async (url, opts) => { calls.push({ url, opts }); return { ok: true, status: 204 }; };
  const summary = await pushAnnotations({ base: 'https://c', token: 'T', sidecarDir: dir, fetch });
  assert.equal(summary.filesPushed, 1);
  const call = calls.find((c) => c.url.endsWith('/api/annotations/a.md'));
  assert.equal(call.opts.method, 'PUT');
  assert.equal(call.opts.headers.Authorization, 'Bearer T');
});

test('pull syncs a tombstone-only cloud file (enumerated via manifest.files)', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pull-'));
  fs.writeFileSync(path.join(dir, 'a.md.json'), JSON.stringify({ version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 1, segments: [] }] }));
  const fetch = mockFetch({
    '/api/annotations-manifest': { entries: [], files: ['a.md'] },   // no live entries; file listed
    '/api/annotations/a.md': { version: 1, file: 'a.md', highlights: [{ id: 'x', updatedAt: 9, deleted: true, segments: [] }] },
  });
  await pullAnnotations({ base: 'https://c', token: 'T', sidecarDir: dir, fetch });
  const onDisk = JSON.parse(fs.readFileSync(path.join(dir, 'a.md.json'), 'utf8'));
  assert.equal(onDisk.highlights.find((h) => h.id === 'x').deleted, true);
});

test('pull counts a live->tombstone transition once, not pre-existing tombstones', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pull-'));
  // local already has a tombstone (x) and a live highlight (y)
  fs.writeFileSync(path.join(dir, 'a.md.json'), JSON.stringify({ version: 1, file: 'a.md', highlights: [
    { id: 'x', updatedAt: 9, deleted: true, segments: [] },
    { id: 'y', updatedAt: 1, segments: [] },
  ] }));
  // remote tombstones y (newer) and keeps x's tombstone
  const fetch = mockFetch({
    '/api/annotations-manifest': { entries: [{ id: 'y', file: 'a.md' }] },
    '/api/annotations/a.md': { version: 1, file: 'a.md', highlights: [
      { id: 'x', updatedAt: 9, deleted: true, segments: [] },
      { id: 'y', updatedAt: 5, deleted: true, segments: [] },
    ] },
  });
  const summary = await pullAnnotations({ base: 'https://c', token: 'T', sidecarDir: dir, fetch });
  assert.equal(summary.tombstonesApplied, 1); // only y is newly tombstoned; x was already a tombstone
});
