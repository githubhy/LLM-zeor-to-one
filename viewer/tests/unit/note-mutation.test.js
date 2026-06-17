const test = require('node:test');
const assert = require('node:assert/strict');
const mut = require('../../lib/note-mutation');
const shared = require('../../lib/highlight-shared');

test('addNote inserts ref flush against highlight close, def at paragraph end', () => {
  const src = 'Prose ==yellow:hi== more.\n\nNext para.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const result = mut.addNote(src, hits[0], 'body text', 'top');
  assert.equal(result.noteId, 'note-top-1');
  assert.match(result.newSource, /==yellow:hi==\[\^note-top-1\] more\./);
  assert.match(result.newSource, /\[\^note-top-1\]: body text/);
});

test('addNote indents continuation lines 4 spaces (multi-line body)', () => {
  const src = '==yellow:hi== prose.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const body = 'line one.\nline two.';
  const result = mut.addNote(src, hits[0], body, 'top');
  assert.match(result.newSource, /\[\^note-top-1\]: line one\.\n {4}line two\./);
});

test('addNote allocates next-id when other notes exist in same section', () => {
  const src = [
    '==yellow:a==[^note-top-1] then ==yellow:b== more.',
    '',
    '[^note-top-1]: existing.',
  ].join('\n');
  const hits = shared.extractInlineHighlights(src, 'a.md');
  // Hit at index 1 is the one without a note.
  const target = hits.find(h => h.noteId === null);
  const result = mut.addNote(src, target, 'new body', 'top');
  assert.equal(result.noteId, 'note-top-2');
});

test('editNote replaces def body in place, keeping the same id', () => {
  const src = '==yellow:hi==[^note-test-1] prose.\n\n[^note-test-1]: old body.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.editNote(src, hits[0], 'new body');
  assert.match(newSource, /\[\^note-test-1\]: new body/);
  assert.doesNotMatch(newSource, /\[\^note-test-1\]: old body/);
  // Ref position unchanged.
  const newHits = shared.extractInlineHighlights(newSource, 'a.md');
  assert.equal(newHits[0].noteId, 'note-test-1');
  assert.equal(newHits[0].noteBody, 'new body');
});

test('editNote handles multi-line bodies (re-indent)', () => {
  const src = '==yellow:hi==[^note-test-1] prose.\n\n[^note-test-1]: old.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.editNote(src, hits[0], 'line one\nline two');
  assert.match(newSource, /\[\^note-test-1\]: line one\n {4}line two/);
});

test('editNote throws when entry has no note', () => {
  const src = '==yellow:bare==';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.throws(() => mut.editNote(src, hits[0], 'body'), /no note/);
});

test('deleteNote strips both ref and def, leaving highlight intact', () => {
  const src = 'Prose ==yellow:noted==[^note-test-1] more.\n\n[^note-test-1]: body.\n\nNext para.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.deleteNote(src, hits[0]);
  assert.match(newSource, /==yellow:noted== more\./);
  assert.doesNotMatch(newSource, /\[\^note-test-1\]/);
  // Highlight still parseable.
  const newHits = shared.extractInlineHighlights(newSource, 'a.md');
  assert.equal(newHits.length, 1);
  assert.equal(newHits[0].noteId, null);
});

test('deleteNote collapses double blank lines created by removing the def block', () => {
  const src = 'Prose ==yellow:n==[^note-test-2] more.\n\n[^note-test-2]: body.\n\nNext para.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.deleteNote(src, hits[0]);
  assert.doesNotMatch(newSource, /\n\n\n+/);
});

test('deleteNote throws when entry has no note', () => {
  const src = '==yellow:bare==';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.throws(() => mut.deleteNote(src, hits[0]), /no note/);
});

test('cascadeDeleteHighlight strips highlight markers + ref + def, preserving inner text', () => {
  const src = 'Prose ==yellow:gone==[^note-test-1] more.\n\n[^note-test-1]: body.\n\nNext.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.cascadeDeleteHighlight(src, hits[0]);
  assert.match(newSource, /Prose gone more\.\n\nNext\./);  // text "gone" PRESERVED
  assert.doesNotMatch(newSource, /==/);
  assert.doesNotMatch(newSource, /\[\^note-test-1\]/);
});

test('cascadeDeleteHighlight handles highlight without note (preserves inner text)', () => {
  const src = 'Prose ==yellow:gone== more.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const newSource = mut.cascadeDeleteHighlight(src, hits[0]);
  assert.match(newSource, /Prose gone more\./);  // text "gone" PRESERVED
  assert.doesNotMatch(newSource, /==/);
});

// ── recolorHighlight ────────────────────────────────────────────────────────
// Regression for bugs/2026-05-19-03: recolor must rewrite only the ==color:
// opener via authoritative source offsets, preserving inner text VERBATIM —
// links, `code`, $math$, refs, CRLF — which the old textContent→regex path
// could not relocate at all.

test('recolorHighlight swaps the color label, inner text unchanged', () => {
  const src = 'Prose ==yellow: hi there== more.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'green');
  assert.equal(out, 'Prose ==green: hi there== more.');
  const re = shared.extractInlineHighlights(out, 'a.md');
  assert.equal(re[0].color, 'green');
  assert.equal(re[0].text, 'hi there');
});

test('recolorHighlight adds a label to an uncolored ==text==', () => {
  const src = '==bare bit==';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'blue');
  assert.equal(out, '==blue: bare bit==');
});

test('recolorHighlight preserves a markdown link inner verbatim (the bug)', () => {
  const src = 'X ==yellow: see [the docs](https://e.com/p?x=1&y=2) now== Y';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'red');
  assert.equal(out, 'X ==red: see [the docs](https://e.com/p?x=1&y=2) now== Y');
});

test('recolorHighlight preserves inline code and math inner verbatim', () => {
  const src = '==green: use `f(x)` when $x^2 \\le 1$ holds==';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'purple');
  assert.equal(out, '==purple: use `f(x)` when $x^2 \\le 1$ holds==');
});

test('recolorHighlight leaves an absorbed note ref and its def untouched', () => {
  const src = 'P ==yellow: noted bit==[^note-test-1] q.\n\n[^note-test-1]: body.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'orange');
  assert.match(out, /==orange: noted bit==\[\^note-test-1\] q\./);
  assert.match(out, /\[\^note-test-1\]: body\./);
  const re = shared.extractInlineHighlights(out, 'a.md');
  assert.equal(re[0].color, 'orange');
  assert.equal(re[0].noteId, 'note-test-1');
});

test('recolorHighlight preserves CRLF inside the inner text (no \\r loss)', () => {
  const src = 'A ==yellow: left\r\nright== B';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  const out = mut.recolorHighlight(src, hits[0], 'teal');
  assert.equal(out, 'A ==teal: left\r\nright== B');
});

test('recolorHighlight rejects an invalid color', () => {
  const src = '==yellow: x==';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.throws(() => mut.recolorHighlight(src, hits[0], 'chartreuse'), /invalid color/);
});

test('recolorHighlight throws when entry is missing source positions', () => {
  assert.throws(() => mut.recolorHighlight('==yellow: x==', {}, 'green'), /missing source positions/);
});
