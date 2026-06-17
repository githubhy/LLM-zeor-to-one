const test = require('node:test');
const assert = require('node:assert/strict');
const sourceIndex = require('../../lib/source-index');

test('stripInlineMarkersWithMap removes markdown wrappers but keeps text', () => {
  const src = 'A *bold* [link](https://example.com) and <!-- note -->text';
  const out = sourceIndex.stripInlineMarkersWithMap(src);
  assert.equal(out.stripped, 'A bold link and text');
  assert.equal(src[out.map[0]], 'A');
});

test('sourceOffsetFromVisibleOffset maps visible offsets into source', () => {
  const idx = sourceIndex.buildBlockSourceIndex('A **bold** token');
  const offset = sourceIndex.sourceOffsetFromVisibleOffset(idx, idx.visibleText.indexOf('token'));
  assert.equal(idx.blockSource.slice(offset, offset + 5), 'token');
});

test('findInlineMathRanges returns non-display inline formulas only', () => {
  const src = 'x $a+b$ y $$display$$ z $c$';
  const ranges = sourceIndex.findInlineMathRanges(src);
  assert.equal(ranges.length, 2);
  assert.deepEqual(ranges.map((r) => r.text), ['$a+b$', '$c$']);
});
