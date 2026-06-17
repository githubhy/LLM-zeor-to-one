'use strict';

/**
 * Phase 0 tests — multi-root discovery skeleton + single-root compat lock.
 * Spec invariant 1: listMarkdownFiles(dir) deep-equals
 *   listMarkdownFilesMultiRoot([{id:'', absPath:dir, label:''}])
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { listMarkdownFiles, listMarkdownFilesMultiRoot } = require('../../lib/content-source');

// ---------------------------------------------------------------------------
// Shared fixture builder
// ---------------------------------------------------------------------------

function mkFixture() {
  // Two subfolders + an order.json in each + a nested file.
  //   <root>/
  //     order.json          — top-level order (NOT a root short-circuit; no top order.json used in multiroot)
  //     folder-a/
  //       order.json        — ["a2.md","a1.md"] (tests per-folder ordering)
  //       a1.md
  //       a2.md
  //     folder-b/
  //       b1.md
  //       nested/
  //         n1.md
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mr-'));
  const write = (rel, content) => {
    const p = path.join(dir, rel);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, content, 'utf8');
  };
  // NO top-level order.json — we want the walker to run (compat lock: a bare
  // listMarkdownFiles(dir) with no top-level order.json goes through the walk
  // path; listMarkdownFilesMultiRoot must produce the same output).
  write('folder-a/order.json', JSON.stringify(['a2.md', 'a1.md']));
  write('folder-a/a1.md', '# A1');
  write('folder-a/a2.md', '# A2');
  write('folder-b/b1.md', '# B1');
  write('folder-b/nested/n1.md', '# N1');
  return dir;
}

// ---------------------------------------------------------------------------
// Step 0.1 — Failing test: single-root identity invariant
// ---------------------------------------------------------------------------

test('listMarkdownFilesMultiRoot([{id:"",absPath,label:""}]) deep-equals listMarkdownFiles(dir)', () => {
  const dir = mkFixture();
  const flat = listMarkdownFiles(dir);
  // listMarkdownFilesMultiRoot is not yet exported — this will fail (red).
  const multi = listMarkdownFilesMultiRoot([{ id: '', absPath: dir, label: '' }]);
  assert.deepEqual(multi, flat);
});

test('listMarkdownFilesMultiRoot with non-empty id prefixes each rel with id/', () => {
  const dir = mkFixture();
  // id='myroot' → every path gets 'myroot/' prefix
  const multi = listMarkdownFilesMultiRoot([{ id: 'myroot', absPath: dir, label: 'My Root' }]);
  const flat = listMarkdownFiles(dir);
  const expected = flat.map((f) => `myroot/${f}`);
  assert.deepEqual(multi, expected);
});

test('listMarkdownFilesMultiRoot concatenates multiple roots in order', () => {
  const dirA = mkFixture();
  const dirB = mkFixture();
  const multi = listMarkdownFilesMultiRoot([
    { id: 'a', absPath: dirA, label: 'A' },
    { id: 'b', absPath: dirB, label: 'B' },
  ]);
  const flatA = listMarkdownFiles(dirA).map((f) => `a/${f}`);
  const flatB = listMarkdownFiles(dirB).map((f) => `b/${f}`);
  assert.deepEqual(multi, [...flatA, ...flatB]);
});
