const test = require('node:test');
const assert = require('node:assert');
const { renderIconPng, ICON_SPECS } = require('../../tools/make-icons.js');

test('renderIconPng emits a valid PNG of the requested size', () => {
  const buf = renderIconPng(64, { maskable: false });
  assert.ok(Buffer.isBuffer(buf));
  assert.deepStrictEqual([...buf.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]); // PNG signature
  assert.strictEqual(buf.readUInt32BE(16), 64); // IHDR width
  assert.strictEqual(buf.readUInt32BE(20), 64); // IHDR height
});

test('ICON_SPECS covers the iOS + PWA sizes', () => {
  const names = ICON_SPECS.map((s) => s.name).sort();
  assert.deepStrictEqual(names, ['apple-touch-icon.png', 'icon-192.png', 'icon-512-maskable.png', 'icon-512.png']);
});
