'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { listMarkdownFiles, buildManifest } = require('../../lib/content-source');

function fixture(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cs-'));
  for (const [name, content] of Object.entries(files)) {
    const p = path.join(dir, name);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, content, 'utf8');
  }
  return dir;
}

test('listMarkdownFiles honors top-level order.json', () => {
  const dir = fixture({ 'order.json': JSON.stringify(['b.md', 'a.md']), 'a.md': '# A', 'b.md': '# B' });
  assert.deepEqual(listMarkdownFiles(dir), ['b.md', 'a.md']);
});

test('listMarkdownFiles falls back to alphabetical and skips node_modules', () => {
  const dir = fixture({ 'a.md': '# A', 'z.md': '# Z', 'node_modules/x.md': '# X' });
  assert.deepEqual(listMarkdownFiles(dir), ['a.md', 'z.md']);
});

test('buildManifest returns inline highlight entries', () => {
  const dir = fixture({ 'a.md': 'text ==yellow:hi== more' });
  const m = buildManifest(dir, null);
  assert.ok(Array.isArray(m.entries));
  assert.ok(m.entries.some((e) => e.color === 'yellow' && e.backend === 'inline'));
});
