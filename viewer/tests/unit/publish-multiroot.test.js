'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { buildBundle } = require('../../publish');
const { buildIgnoreMatcher } = require('../../lib/content-source');

function tmp() { return fs.mkdtempSync(path.join(os.tmpdir(), 'pub-mr-')); }
function write(dir, rel, content) {
  const p = path.join(dir, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content);
}
const IGNORE = buildIgnoreMatcher({});
const GIT = { schema: 2, roots: {} };

test('multi-root publish: namespaced dist/content, schema-2 files.json, per-folder order preserved', () => {
  const base = tmp();
  // root A with its own order.json controlling file order; root B simple.
  write(base, 'roota/order.json', JSON.stringify(['second.md', 'first.md']));
  write(base, 'roota/first.md', '# First');
  write(base, 'roota/second.md', '# Second');
  write(base, 'rootb/b.md', '# B');
  write(base, 'rootb/dist/noise.md', '# noise');

  const roots = [
    { id: 'roota', absPath: path.join(base, 'roota'), label: 'Root A' },
    { id: 'rootb', absPath: path.join(base, 'rootb'), label: 'Root B' },
  ];
  const out = tmp();
  buildBundle({ roots, outDir: out, version: 't', gitInfo: GIT, ignore: IGNORE });

  // namespaced content
  assert.ok(fs.existsSync(path.join(out, 'content/roota/first.md')));
  assert.ok(fs.existsSync(path.join(out, 'content/rootb/b.md')));
  // .viewerignore pruned the noise dir
  assert.ok(!fs.existsSync(path.join(out, 'content/rootb/dist/noise.md')));

  const fj = JSON.parse(fs.readFileSync(path.join(out, 'files.json'), 'utf8'));
  assert.equal(fj.schema, 2);
  assert.deepEqual(fj.roots, [{ id: 'roota', label: 'Root A' }, { id: 'rootb', label: 'Root B' }]);
  // per-folder order.json honoured under the namespace (second before first), and
  // the root short-circuit was NOT taken (it would have ignored order.json).
  assert.deepEqual(fj.files, ['roota/second.md', 'roota/first.md', 'rootb/b.md']);
});

test('multi-root publish: a doc-relative asset bakes at the browser-requested namespaced path', () => {
  const base = tmp();
  write(base, 'roota/sub/doc.md', '# Doc\n\n![x](figures/x.png)\n');
  write(base, 'roota/sub/figures/x.png', 'PNGDATA');
  const roots = [{ id: 'roota', absPath: path.join(base, 'roota'), label: 'A' }];
  const out = tmp();
  buildBundle({ roots, outDir: out, version: 't', gitInfo: GIT, ignore: IGNORE });
  // fixRelativePaths() turns src into /<docDir>/figures/x.png = /roota/sub/figures/x.png
  assert.ok(fs.existsSync(path.join(out, 'roota/sub/figures/x.png')), 'asset baked at namespaced doc-dir path');
});

test('single-root publish (id=\'\') keeps the flat, un-namespaced dist/content layout', () => {
  const base = tmp();
  write(base, '5g/intro.md', '# Intro\n\n![y](img/y.png)\n');
  write(base, '5g/img/y.png', 'Y');
  const roots = [{ id: '', absPath: base, label: '' }];
  const out = tmp();
  buildBundle({ roots, outDir: out, version: 't', gitInfo: GIT, ignore: IGNORE });
  // No namespace prefix — byte-identical layout to the legacy single-root bake.
  assert.ok(fs.existsSync(path.join(out, 'content/5g/intro.md')));
  assert.ok(fs.existsSync(path.join(out, '5g/img/y.png')));
  const fj = JSON.parse(fs.readFileSync(path.join(out, 'files.json'), 'utf8'));
  assert.deepEqual(fj.files, ['5g/intro.md']);
  assert.deepEqual(fj.roots, [{ id: '', label: '' }]);
});
