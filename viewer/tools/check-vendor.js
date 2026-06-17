'use strict';
const fs = require('fs');
const path = require('path');
const V = path.join(__dirname, '..', 'vendor');
const REQUIRED = [
  ['katex.min.js', 'KaTeX'], ['katex.min.css', 'katex'],
  ['markdown-it.min.js', 'markdown-it'], ['texmath.min.js', 'texmath'],
  ['texmath.min.css', null], ['markdown-it-mark.min.js', null],
  ['markdown-it-footnote.min.js', null], ['mermaid.min.js', 'mermaid'],
];
let bad = 0;
for (const [file, marker] of REQUIRED) {
  const p = path.join(V, file);
  if (!fs.existsSync(p)) { console.error(`MISSING vendor/${file}`); bad++; continue; }
  if (fs.statSync(p).size === 0) { console.error(`EMPTY vendor/${file}`); bad++; continue; }
  if (marker && !fs.readFileSync(p, 'utf8').includes(marker)) { console.error(`vendor/${file} missing marker "${marker}"`); bad++; }
}
const fontsDir = path.join(V, 'fonts');
if (!fs.existsSync(fontsDir) || fs.readdirSync(fontsDir).filter((f) => f.endsWith('.woff2')).length < 10) {
  console.error('vendor/fonts/: expected >=10 KaTeX .woff2 files'); bad++;
}
if (bad) { console.error(`check-vendor: ${bad} problem(s)`); process.exit(1); }
console.log('check-vendor: OK');
