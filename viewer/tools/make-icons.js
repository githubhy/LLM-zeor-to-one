'use strict';
const zlib = require('node:zlib');
const fs = require('node:fs');
const path = require('node:path');

function canvas(size) { return { size, data: new Uint8ClampedArray(size * size * 4) }; }
function px(c, x, y, [r, g, b, a]) {
  if (x < 0 || y < 0 || x >= c.size || y >= c.size) return;
  const i = (y * c.size + x) * 4, ia = a / 255, na = 1 - ia;
  c.data[i] = r * ia + c.data[i] * na;
  c.data[i + 1] = g * ia + c.data[i + 1] * na;
  c.data[i + 2] = b * ia + c.data[i + 2] * na;
  c.data[i + 3] = Math.max(c.data[i + 3], a);
}
function roundRect(c, x0, y0, w, h, rad, color) {
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const dx = Math.min(x, w - 1 - x), dy = Math.min(y, h - 1 - y);
    if (dx < rad && dy < rad) { const ddx = rad - dx, ddy = rad - dy; if (ddx * ddx + ddy * ddy > rad * rad) continue; }
    px(c, x0 + x, y0 + y, color);
  }
}
const CRC_TABLE = (() => { const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c; } return t; })();
function crc32(buf) { let c = 0xFFFFFFFF; for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function encodePng(c) {
  const size = c.size, stride = size * 4 + 1, raw = Buffer.alloc(stride * size);
  for (let y = 0; y < size; y++) { raw[y * stride] = 0;
    for (let x = 0; x < size * 4; x++) raw[y * stride + 1 + x] = c.data[y * size * 4 + x]; }
  const idat = zlib.deflateSync(raw, { level: 9 });
  const chunk = (type, body) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(body.length, 0);
    const t = Buffer.from(type, 'latin1'); const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(Buffer.concat([t, body])), 0);
    return Buffer.concat([len, t, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0); ihdr.writeUInt32BE(size, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);
}
const BG = [37, 99, 235, 255];   // #2563EB
const FG = [255, 255, 255, 235];
const DESIGN = {
  cornerRadiusFrac: 0.22, barLeftFrac: 0.26, barWidthFrac: 0.48,
  barHeightFrac: 0.07, barGapFrac: 0.14, firstBarTopFrac: 0.30,
  shortBarFrac: 0.60, maskablePadFrac: 0.18,
};
function renderIconPng(size, { maskable }) {
  const c = canvas(size);
  const pad = maskable ? Math.round(size * DESIGN.maskablePadFrac) : 0;
  roundRect(c, pad, pad, size - 2 * pad, size - 2 * pad, Math.round((size - 2 * pad) * DESIGN.cornerRadiusFrac), BG);
  const inner = size - 2 * pad, ox = pad + Math.round(inner * DESIGN.barLeftFrac), bw = Math.round(inner * DESIGN.barWidthFrac);
  const bh = Math.max(2, Math.round(inner * DESIGN.barHeightFrac)), gap = Math.round(inner * DESIGN.barGapFrac);
  let oy = pad + Math.round(inner * DESIGN.firstBarTopFrac);
  for (let k = 0; k < 3; k++) { roundRect(c, ox, oy, k === 2 ? Math.round(bw * DESIGN.shortBarFrac) : bw, bh, Math.round(bh / 2), FG); oy += gap; }
  return encodePng(c);
}
const ICON_SPECS = [
  { name: 'apple-touch-icon.png', size: 180, maskable: false },
  { name: 'icon-192.png', size: 192, maskable: false },
  { name: 'icon-512.png', size: 512, maskable: false },
  { name: 'icon-512-maskable.png', size: 512, maskable: true },
];
function writeAll(outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  for (const s of ICON_SPECS) fs.writeFileSync(path.join(outDir, s.name), renderIconPng(s.size, { maskable: s.maskable }));
  return ICON_SPECS.map((s) => s.name);
}
module.exports = { renderIconPng, ICON_SPECS, writeAll };
if (require.main === module) { const out = path.join(__dirname, '..', 'icons'); console.log('wrote', writeAll(out).join(', '), 'to', out); }
