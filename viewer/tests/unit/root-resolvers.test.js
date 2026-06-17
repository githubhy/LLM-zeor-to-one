'use strict';

const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const { rootForFile, rootForAbsPath } = require('../../lib/content-source');

const ROOTS = [
  { id: 'surveys', absPath: '/repo/surveys', label: 'Surveys' },
  { id: 'docs', absPath: '/repo/docs', label: 'Documentation' },
];

// ---------------------------------------------------------------------------
// rootForFile
// ---------------------------------------------------------------------------

test('rootForFile: namespaced id resolves to its root + relative path', () => {
  assert.deepEqual(rootForFile(ROOTS, 'surveys/5g-nr-ldpc/00-intro.md'), {
    root: ROOTS[0], rel: '5g-nr-ldpc/00-intro.md',
  });
  assert.deepEqual(rootForFile(ROOTS, 'docs/foo.md'), { root: ROOTS[1], rel: 'foo.md' });
});

test('rootForFile: a file equal to a root id has empty rel', () => {
  assert.deepEqual(rootForFile(ROOTS, 'surveys'), { root: ROOTS[0], rel: '' });
});

test('rootForFile: no claiming root in multi-root mode returns null', () => {
  assert.equal(rootForFile(ROOTS, 'reports/x.md'), null);
});

test('rootForFile: empty-id root is the sole fallback (single-root compat)', () => {
  const single = [{ id: '', absPath: '/repo/surveys', label: '' }];
  assert.deepEqual(rootForFile(single, 'anything/x.md'), { root: single[0], rel: 'anything/x.md' });
});

test('rootForFile: longest matching id prefix wins when ids nest', () => {
  const nested = [
    { id: 'a', absPath: '/r/a', label: 'A' },
    { id: 'a/b', absPath: '/r/a/b', label: 'A-B' },
  ];
  assert.deepEqual(rootForFile(nested, 'a/b/x.md'), { root: nested[1], rel: 'x.md' });
  assert.deepEqual(rootForFile(nested, 'a/c.md'), { root: nested[0], rel: 'c.md' });
});

// ---------------------------------------------------------------------------
// rootForAbsPath
// ---------------------------------------------------------------------------

test('rootForAbsPath: abs path under a root resolves to {root, rel}', () => {
  const abs = path.join('/repo/surveys', '5g-nr-ldpc', 'a.md');
  assert.deepEqual(rootForAbsPath(ROOTS, abs), { root: ROOTS[0], rel: '5g-nr-ldpc/a.md' });
});

test('rootForAbsPath: a path outside every root returns null', () => {
  assert.equal(rootForAbsPath(ROOTS, '/repo/sim/x.py'), null);
});

test('rootForAbsPath: longest absPath ancestor wins for nested roots', () => {
  const nested = [
    { id: 'a', absPath: '/r/a', label: 'A' },
    { id: 'ab', absPath: '/r/a/b', label: 'AB' },
  ];
  assert.deepEqual(rootForAbsPath(nested, '/r/a/b/x.md'), { root: nested[1], rel: 'x.md' });
});

test('rootForAbsPath: the root dir itself resolves with empty rel', () => {
  assert.deepEqual(rootForAbsPath(ROOTS, '/repo/surveys'), { root: ROOTS[0], rel: '' });
});
