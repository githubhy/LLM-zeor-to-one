#!/usr/bin/env node
/*
 * verify-katex-render.cjs — render every math fragment of a markdown file
 * through the SAME vendored libraries, plugin set and config the browser
 * viewer uses, and fail on any that KaTeX cannot render or on any markup that
 * leaks into the rendered HTML.
 *
 * Why this exists (complements lint-math.py):
 *   lint-math.py checks the *delimiter* rules statically (digit-adjacency,
 *   blank-line-after-$$, list/math interactions). It does NOT actually run
 *   KaTeX, so a syntactically-delimited but mathematically-broken equation
 *   (bad environment, unsupported command, mismatched braces) passes lint yet
 *   renders as a red `.katex-error` node in the viewer. This tool closes that
 *   gap by driving the viewer's real render path.
 *
 * Faithfulness (2026-07-09 rewrite — see bugs/2026-07-09-02):
 *   Earlier revisions REIMPLEMENTED a subset of the viewer's pipeline: they
 *   loaded markdown-it + texmath but not markdown-it-mark, ran no
 *   `<mark>color:` post-regex, and used a hand-rolled `$$` scanner that did not
 *   know about the project's `==color: $$` / `$$==` display-math wrapper. Two
 *   consequences, both observed in the wild:
 *
 *     - FALSE POSITIVES: a highlighted display block was counted as a `$$`
 *       "leak". Six mechanistic-interpretability files failed for this reason,
 *       which is what blocked the render gate's rollout.
 *     - FALSE NEGATIVES: the tool passed cleanly on all three documents that
 *       bugs/2026-07-09-02 corrupted, because nothing here parsed `==` markup.
 *
 *   A checker that re-implements the thing it checks is testing its own copy.
 *   `shieldDisplayMath` and `processHighlights` are now imported from
 *   viewer/lib/highlight-shared.js — the very functions viewer.js calls.
 *
 * Usage:  node viewer/tools/verify-katex-render.cjs <file.md> [<file.md> ...]
 * Exit:   0 = all fragments render clean; 1 = at least one failure.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const VENDOR = path.resolve(__dirname, '..', 'vendor');
const katex = require(path.join(VENDOR, 'katex.min.js'));
const markdownit = require(path.join(VENDOR, 'markdown-it.min.js'));
const texmath = require(path.join(VENDOR, 'texmath.min.js'));
const markdownitMark = require(path.join(VENDOR, 'markdown-it-mark.min.js'));

const { shieldDisplayMath, processHighlights, HL_COLOR_ALT } =
  require(path.resolve(__dirname, '..', 'lib', 'highlight-shared.js'));

// A corrupted highlight leaves its literal OPENER — `==blue:` — in the rendered
// prose (bugs/2026-07-09-02). A bare `==` does not imply corruption: prose may
// legitimately contain it (`the puncture-free self-test (buggy == correct)`), and
// an uncoloured `==text==` is a valid <mark>. Detect the opener, not the digraph.
const HL_LEAK_RE = new RegExp(`==(?:${HL_COLOR_ALT}):`, 'gi');

const KOPTS_DISPLAY = { throwOnError: true, trust: true, macros: {}, output: 'html', displayMode: true };
const KOPTS_INLINE = { throwOnError: true, trust: true, macros: {}, output: 'html', displayMode: false };

// Mirrors viewer.js: markdownit({html,linkify:false,typographer:false}) + texmath + mark.
function makeMd() {
  return markdownit({ html: true, linkify: false, typographer: false })
    .use(markdownitMark)
    .use(texmath, {
      engine: katex,
      delimiters: 'dollars',
      katexOptions: { throwOnError: false, trust: true, macros: {}, output: 'html' },
    });
}

const PLACEHOLDER = /<div data-math-block="(\d+)"(?: data-hl-color="(\w+)")?><\/div>/g;

/**
 * Display blocks come from shieldDisplayMath — the viewer's own scanner, which
 * is fence-aware and understands `==color: $$` / `$$==` and single-line `$$..$$`.
 * Inline spans are scanned from the SHIELDED text, so a `$` inside a display
 * block can never be mistaken for an inline delimiter.
 */
function extract(src) {
  const { text, blocks, lineMap } = shieldDisplayMath(src);
  const shielded = text.split('\n');

  const display = blocks.map((tex, i) => {
    const li = shielded.findIndex((l) => l.includes(`data-math-block="${i}"`));
    const orig = li >= 0 ? (lineMap[li] !== undefined ? lineMap[li] : li) : 0;
    return { line: orig + 1, tex };
  });

  const inline = [];
  let inFence = false;
  for (let i = 0; i < shielded.length; i++) {
    const ln = shielded[i];
    if (/^(`{3,}|~{3,})/.test(ln.trim())) { inFence = !inFence; continue; }
    if (inFence) continue;
    const re = /(?<!\$)\$([^$\n]+?)\$(?!\$)/g;
    let m;
    while ((m = re.exec(ln)) !== null) {
      const orig = lineMap[i] !== undefined ? lineMap[i] : i;
      inline.push({ line: orig + 1, tex: m[1] });
    }
  }
  return { display, inline };
}

function renderList(list, opts) {
  const fails = [];
  for (const it of list) {
    try { katex.renderToString(it.tex, opts); }
    catch (e) { fails.push({ line: it.line, tex: it.tex.slice(0, 90), err: String(e.message || e).split('\n')[0] }); }
  }
  return fails;
}

/** Reproduce viewer.js::renderMarkdown end-to-end, then scan the resulting HTML. */
function pipelineScan(src) {
  const md = makeMd();
  const { text, blocks } = shieldDisplayMath(src);
  let html = md.render(text);
  html = html.replace(PLACEHOLDER, (_, idx, color) => {
    const cls = color ? ` hl-${color}` : '';
    let inner;
    try {
      inner = katex.renderToString(blocks[parseInt(idx, 10)],
        { throwOnError: false, trust: true, macros: {}, output: 'html', displayMode: true });
    } catch (_e) {
      inner = '<span class="katex-error"></span>';
    }
    return `<div class="display-math-wrap${cls}">${inner}</div>`;
  });
  html = processHighlights(html);

  // A "leak" means markup rendered as literal prose. Code spans and fenced
  // blocks are SUPPOSED to show literal text — `a == b`, `$$`, `\begin{...}`
  // inside <code>/<pre> are content, not leaks. Strip them before counting, or
  // the checker repeats the very context-blindness it exists to catch.
  const prose = html
    .replace(/<pre[\s\S]*?<\/pre>/g, '')
    .replace(/<code[\s\S]*?<\/code>/g, '');

  return {
    katexSpans: (html.match(/class="katex"/g) || []).length,
    katexErr: (html.match(/katex-error/g) || []).length,
    dollarLeak: (prose.match(/\$\$/g) || []).length,
    beginLeak: (prose.match(/\\begin\{/g) || []).length,
    // A literal `==color:` opener surviving into rendered prose means the
    // highlight markup did not parse — the interleaved-delimiter corruption of
    // bugs/2026-07-09-02.
    markLeak: (prose.match(HL_LEAK_RE) || []).length,
    // `<mark>word:` that survived processHighlights is a mis-spelled colour name.
    badMark: (prose.match(/<mark>\w+:/g) || []).length,
  };
}

function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error('usage: node verify-katex-render.cjs <file.md> [<file.md> ...]');
    process.exit(2);
  }
  let allOK = true;
  for (const file of files) {
    const src = fs.readFileSync(file, 'utf8');
    const { display, inline } = extract(src);
    const dFail = renderList(display, KOPTS_DISPLAY);
    const iFail = renderList(inline, KOPTS_INLINE);
    const p = pipelineScan(src);
    const ok = dFail.length === 0 && iFail.length === 0 && p.katexErr === 0
      && p.dollarLeak === 0 && p.beginLeak === 0 && p.markLeak === 0 && p.badMark === 0;
    allOK = allOK && ok;
    console.log(`${file}`);
    console.log(`  display $$…$$ : ${display.length - dFail.length}/${display.length} OK`);
    console.log(`  inline  $…$   : ${inline.length - iFail.length}/${inline.length} OK`);
    console.log(`  pipeline: ${p.katexSpans} katex spans, ${p.katexErr} errors, `
      + `${p.dollarLeak} '$$' leaks, ${p.beginLeak} '\\begin{' leaks, `
      + `${p.markLeak} '==color:' leaks, ${p.badMark} bad <mark>`);
    for (const f of [...dFail, ...iFail]) console.log(`  FAIL @L${f.line}: ${f.err}\n       tex: ${f.tex}`);
    console.log(`  => ${ok ? 'PASS' : 'FAIL'}`);
  }
  process.exit(allOK ? 0 : 1);
}

main();
