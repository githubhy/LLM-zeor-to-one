// End-to-end proof for bugs/2026-07-09-02: a highlight whose selection begins
// inside an inline-markup span must render as ONE <mark>, not as literal source.
//
// Drives the viewer's real vendored stack (markdown-it + markdown-it-mark +
// texmath + KaTeX) plus the `<mark>color:` post-regex of viewer.js, so a pass
// here is what the browser DOM actually contains.
//
// Note: verify-katex-render.cjs does NOT load markdown-it-mark and is therefore
// blind to this whole bug class -- see todos/2026-07-09-wire-katex-render-gate.md.

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { snapOutOfInlineSpans } = require('../../lib/highlight-shared');

const VENDOR = path.resolve(__dirname, '..', '..', 'vendor');
const katex = require(path.join(VENDOR, 'katex.min.js'));
const markdownit = require(path.join(VENDOR, 'markdown-it.min.js'));
const texmath = require(path.join(VENDOR, 'texmath.min.js'));
const mark = require(path.join(VENDOR, 'markdown-it-mark.min.js'));

const md = markdownit({ html: true, linkify: false, typographer: false })
  .use(mark)
  .use(texmath, {
    engine: katex,
    delimiters: 'dollars',
    katexOptions: { throwOnError: false, trust: true, macros: {}, output: 'html' },
  });

// viewer.js: <mark>color: text</mark> -> <mark class="hl-color">text</mark>
const HL = /<mark>(blue|yellow|green|red|orange|purple|teal|pink):\s*/gi;
const render = (src) => md.render(src).replace(HL, (_, c) => `<mark class="hl-${c.toLowerCase()}">`);

/** Emulate applyHighlight Steps 7B->9 for a colour action. */
function applyColor(source, visibleStart, visibleEnd, color) {
  const snapped = snapOutOfInlineSpans(source, visibleStart, visibleEnd);
  const text = source.slice(snapped.selStart, snapped.selEnd);
  return source.slice(0, snapped.selStart) + `==${color}: ${text}==` + source.slice(snapped.selEnd);
}

const CASES = [
  {
    name: '*motion* — opener would land inside the emphasis',
    src: "Throughout this section, then, *motion* names the trajectory's variation in $n$ — a path.",
    visible: "motion* names the trajectory's variation in $n$",
    color: 'blue',
  },
  {
    name: '*First*, ... **column** ... **same** — emphasis at the boundary, strong inside',
    src: 'Three things follow. *First*, every **column** of $H$ is the **same** kernel, shifted by $e$ and scaled.',
    visible: 'First*, every **column** of $H$ is the **same** kernel, shifted by $e$',
    color: 'yellow',
  },
  {
    name: '**normalized Doppler** — opener would land inside the strong span',
    src: 'The one dimensionless knob is the **normalized Doppler** $f = a/b$. As a rule of thumb',
    visible: 'normalized Doppler** $f = a/b$',
    color: 'blue',
  },
];

for (const c of CASES) {
  test(`renders as one <mark>: ${c.name}`, () => {
    const s = c.src.indexOf(c.visible);
    assert.ok(s > 0, 'fixture must contain the visible run');
    const fixed = applyColor(c.src, s, s + c.visible.length, c.color);
    const html = render(fixed);

    assert.equal((html.match(new RegExp(`<mark class="hl-${c.color}">`, 'g')) || []).length, 1,
      `expected exactly one <mark class="hl-${c.color}">, got:\n${html}`);
    assert.equal((html.match(/==/g) || []).length, 0, `literal '==' leaked into HTML:\n${html}`);
    assert.ok(!/<mark>/.test(html), 'the colour prefix must be consumed by the post-regex');
  });

  test(`WITHOUT the snap the same case is broken: ${c.name}`, () => {
    const s = c.src.indexOf(c.visible);
    const e = s + c.visible.length;
    // pre-fix behaviour: splice at the raw rendered-text offsets
    const broken = c.src.slice(0, s) + `==${c.color}: ${c.src.slice(s, e)}==` + c.src.slice(e);
    const html = render(broken);
    assert.equal((html.match(new RegExp(`<mark class="hl-${c.color}">`, 'g')) || []).length, 0,
      'the un-snapped form must NOT produce a mark (this is the bug)');
    assert.ok(html.includes('=='), 'the un-snapped form leaks literal == (this is the bug)');
  });
}

test('emphasis survives inside the mark', () => {
  const src = "then, *motion* names it.";
  const v = 'motion* names it.';
  const s = src.indexOf(v);
  const html = render(applyColor(src, s, s + v.length, 'blue'));
  assert.match(html, /<mark class="hl-blue"><em>motion<\/em> names it\.<\/mark>/);
});
