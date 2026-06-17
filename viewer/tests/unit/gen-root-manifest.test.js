'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { generateManifest, serialize } = require('../../tools/gen-root-manifest');

function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grm-'));
  const write = (rel, c) => {
    const p = path.join(dir, rel);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, c);
  };
  write('roota/order.json', JSON.stringify(['a.md']));
  write('roota/a.md', '# A');
  write('roota/sub/x.md', '# X');
  write('roota/dist/noise.md', '# noise (pruned)');
  write('rootb/b.md', '# B');
  write('viewer.content.json', JSON.stringify({
    roots: [
      { id: 'roota', path: 'roota', label: 'Root A' },
      { id: 'rootb', path: 'rootb', label: 'Root B' },
    ],
  }));
  return path.join(dir, 'viewer.content.json');
}

test('generateManifest: schema, labelled roots, namespaced files, noise pruned', () => {
  const { manifest } = generateManifest(fixture());
  assert.equal(manifest.schema, 1);
  assert.deepEqual(manifest.roots, [
    { id: 'roota', label: 'Root A' },
    { id: 'rootb', label: 'Root B' },
  ]);
  assert.ok(manifest.files.includes('roota/a.md'));
  assert.ok(manifest.files.includes('roota/sub/x.md'));
  assert.ok(manifest.files.includes('rootb/b.md'));
  assert.ok(!manifest.files.some((f) => f.includes('dist/')), 'dist/ noise pruned by the matcher');
});

test('serialize is deterministic (the --check drift gate relies on it)', () => {
  const cfg = fixture();
  assert.equal(serialize(generateManifest(cfg).manifest), serialize(generateManifest(cfg).manifest));
});

const { spawnSync } = require('node:child_process');

test('--config with a missing root path exits 2 with a clean message (no ENOENT crash)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'grm-miss-'));
  fs.writeFileSync(path.join(dir, 'viewer.content.json'),
    JSON.stringify({ roots: [{ id: 'gone', path: 'does-not-exist' }] }));
  const r = spawnSync('node',
    [path.resolve(__dirname, '../../tools/gen-root-manifest.js'), '--config', path.join(dir, 'viewer.content.json')],
    { encoding: 'utf8' });
  assert.equal(r.status, 2, 'clean config-error exit code (not 1/ENOENT)');
  assert.match(r.stderr, /config root not found/);
});
