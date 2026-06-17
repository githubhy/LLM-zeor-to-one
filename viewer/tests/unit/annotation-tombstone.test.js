const test = require('node:test');
const assert = require('node:assert/strict');
const os = require('os'); const fs = require('fs'); const path = require('path');
const cs = require('../../lib/content-source');

test('content-source normalizeAnnotationDoc carries updatedAt + deleted', () => {
  const doc = cs.normalizeAnnotationDoc('a.md', null, { highlights: [{ id: 'x', updatedAt: 9, deleted: true, segments: [] }] });
  assert.equal(doc.highlights[0].updatedAt, 9);
  assert.equal(doc.highlights[0].deleted, true);
});
test('content-source normalize defaults updatedAt to 0 and omits deleted when absent', () => {
  const doc = cs.normalizeAnnotationDoc('a.md', null, { highlights: [{ id: 'x', segments: [] }] });
  assert.equal(doc.highlights[0].updatedAt, 0);
  assert.equal('deleted' in doc.highlights[0], false);
});
test('loadSidecarManifest skips tombstones', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'vh-'));
  fs.mkdirSync(path.join(dir, '.viewer-highlights'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'a.md'), '# a\n');
  fs.writeFileSync(path.join(dir, '.viewer-highlights', 'a.md.json'), JSON.stringify({
    version: 1, file: 'a.md',
    highlights: [{ id: 'x', segments: [{ blockLine: 1 }] }, { id: 'y', deleted: true, segments: [{ blockLine: 2 }] }],
  }));
  const m = cs.loadSidecarManifest(dir, 'a.md', null);
  assert.deepEqual(m.entries.map((e) => e.id), ['x']);
});
