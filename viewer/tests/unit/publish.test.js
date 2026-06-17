'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs'); const os = require('os'); const path = require('path');
const { buildBundle, buildHtmlAndAssets, referencedAssets } = require('../../publish');

function fixture(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pub-'));
  for (const [n, c] of Object.entries(files)) {
    const p = path.join(dir, n); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, c);
  }
  return dir;
}

test('referencedAssets extracts local image paths, skips remote/data', () => {
  const md = '![a](figures/x.png)\n<img src="figures/y.svg">\n![w](https://h/z.png)\n![d](data:image/png;base64,AA)';
  const got = referencedAssets(md).sort();
  assert.deepEqual(got, ['figures/x.png', 'figures/y.svg']);
});

test('buildBundle emits content, files.json, git-info.json, annotations + manifest', () => {
  const target = fixture({
    'order.json': JSON.stringify(['a.md']),
    'a.md': '# A\n\n![fig](figures/x.png)\n\ntext ==yellow:hi==',
    'figures/x.png': 'PNG',
    '.viewer-highlights/a.md.json': JSON.stringify({ version: 1, file: 'a.md', highlights: [] }),
  });
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'dist-'));
  const r = buildBundle({ roots: [{ id: '', absPath: target, label: '' }], outDir: out, version: 'v1', gitInfo: { available: true, sha: 'abc' } });

  assert.equal(r.fileCount, 1);
  assert.equal(fs.readFileSync(path.join(out, 'content/a.md'), 'utf8').startsWith('# A'), true);
  assert.ok(fs.existsSync(path.join(out, 'figures/x.png')));
  const files = JSON.parse(fs.readFileSync(path.join(out, 'files.json'), 'utf8'));
  assert.deepEqual(files.files, ['a.md']);
  assert.equal(files.version, 'v1');
  assert.equal(files.defaultFile, null);
  assert.equal(JSON.parse(fs.readFileSync(path.join(out, 'git-info.json'), 'utf8')).sha, 'abc');
  assert.ok(fs.existsSync(path.join(out, 'annotations/a.md.json')));
  const man = JSON.parse(fs.readFileSync(path.join(out, 'annotations-manifest.json'), 'utf8'));
  assert.ok(Array.isArray(man.entries));
  assert.ok(man.entries.some((e) => e.color === 'yellow'));
});

test('buildHtmlAndAssets copies Cloudflare functions + lib so dist/ is deployable', () => {
  const target = fixture({ 'a.md': '# A' });
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'dist-'));
  buildBundle({ roots: [{ id: '', absPath: target, label: '' }], outDir: out, version: 'v1', gitInfo: { available: false } });
  buildHtmlAndAssets({ outDir: out, version: 'v1' });

  assert.ok(fs.existsSync(path.join(out, 'functions/_middleware.js')), 'middleware copied');
  assert.ok(fs.existsSync(path.join(out, 'functions/api/annotations/[[path]].js')), 'annotations route copied');
  assert.ok(fs.existsSync(path.join(out, 'lib/cloud-api.js')), 'cloud-api lib copied');
});

test('buildBundle wipes a stale outDir before writing', () => {
  const target = fixture({ 'a.md': '# A' });
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'dist-'));
  fs.writeFileSync(path.join(out, 'STALE.txt'), 'old');
  buildBundle({ roots: [{ id: '', absPath: target, label: '' }], outDir: out, version: 'v1', gitInfo: { available: false } });
  assert.equal(fs.existsSync(path.join(out, 'STALE.txt')), false);
});
