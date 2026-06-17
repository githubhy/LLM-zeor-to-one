const test = require('node:test');
const assert = require('node:assert/strict');
const shared = require('../../lib/highlight-shared');

test('extractInlineHighlights preserves source order within a line', () => {
  const src = 'One ==yellow: first== and ==orange: second== entry.\n';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits.length, 2);
  assert.equal(hits[0].excerpt, 'first');
  assert.equal(hits[1].excerpt, 'second');
  assert.ok(hits[0].sourceStart < hits[1].sourceStart);
});

test('extractInlineHighlights ignores fenced code blocks', () => {
  const src = [
    '```js',
    'const fake = "==red: not-a-highlight==";',
    '```',
    '',
    '==green: real highlight==',
  ].join('\n');
  const hits = shared.extractInlineHighlights(src, 'code.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].color, 'green');
  assert.equal(hits[0].excerpt, 'real highlight');
});

test('extractInlineHighlights ignores inline code spans', () => {
  const src = '`==teal: ignore==` and ==teal: keep==';
  const hits = shared.extractInlineHighlights(src, 'inline.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].excerpt, 'keep');
});

test('slugify lowercases, strips, and hyphenates like GitHub', () => {
  assert.equal(shared.slugify('Hello World'), 'hello-world');
  // GitHub replaces each space individually and never collapses, so a stripped
  // em-dash between two spaces leaves a DOUBLE hyphen — e.g. the wiki heading
  // "## 3 — Folding…" is linked as "#3--folding-…". The previous expectation
  // ('section-523-title', single hyphen) encoded the non-GitHub collapse that
  // broke every such cross-link (bug 2026-06-02-02).
  assert.equal(shared.slugify('Section 5.2.3 — Title!'), 'section-523--title');
  assert.equal(shared.slugify('3 — Folding (and why)'), '3--folding-and-why');
  // trim() keeps leading/trailing whitespace from becoming edge hyphens.
  assert.equal(shared.slugify('  Leading and trailing  '), 'leading-and-trailing');
});

test('stripInlineMarkersForSlug removes link/code/math/em markers', () => {
  assert.equal(shared.stripInlineMarkersForSlug('A `code` and *em*'), 'A code and em');
  assert.equal(shared.stripInlineMarkersForSlug('A [link](url) and $math$'), 'A link and math');
  assert.equal(shared.stripInlineMarkersForSlug('A **bold** and __also__'), 'A bold and also');
});

test('stripInlineMarkersForSlug strips inline <a id> heading anchors (bug 2026-05-25-02)', () => {
  // Post-2026-05-25 heading anchor convention places the anchor inline
  // after the ATX prefix; outline + sectionSlugAt must strip it so the
  // displayed text and slug don't carry literal `<a id="...">` HTML.
  assert.equal(
    shared.stripInlineMarkersForSlug('<a id="sec-D.5"></a>D.5 Channel densities'),
    'D.5 Channel densities'
  );
  assert.equal(
    shared.stripInlineMarkersForSlug('<a id="sec-3.7.6"></a>3.7.6 Quantization'),
    '3.7.6 Quantization'
  );
});

test('stripInlineMarkersForSlug strips inline <!-- ... --> HTML comments', () => {
  // Some appendix headings carry inline `<!-- xref:... -->` / `<!-- secref:... -->`
  // markers within the heading text (e.g., appendix-a.md A.8.1). These
  // are invisible in rendered output and must be invisible in outline /
  // slug computation too.
  assert.equal(
    shared.stripInlineMarkersForSlug('A.8.1 Channel LLR <!-- xref:5.2.1-1 -->'),
    'A.8.1 Channel LLR '
  );
  assert.equal(
    shared.stripInlineMarkersForSlug('<a id="sec-A.8.1"></a>A.8.1 Foo <!-- xref:5.2.1-1 -->'),
    'A.8.1 Foo '
  );
});

test('sectionSlugAt finds nearest preceding heading slug', () => {
  const src = [
    '# Top',
    '',
    'Para before any subhead.',
    '',
    '## Section One',
    '',
    'Para in section one.',
    '',
    '### Sub 1.1',
    '',
    'Deep para.',
  ].join('\n');
  // position pointing at "Para before any subhead." → "top"
  const posTop = src.indexOf('Para before any subhead.');
  assert.equal(shared.sectionSlugAt(src, posTop), 'top');
  // position in "Para in section one." → "section-one"
  const posSec = src.indexOf('Para in section one.');
  assert.equal(shared.sectionSlugAt(src, posSec), 'section-one');
  // position in "Deep para." → "sub-11"
  const posSub = src.indexOf('Deep para.');
  assert.equal(shared.sectionSlugAt(src, posSub), 'sub-11');
});

test('sectionSlugAt returns "top" when no heading precedes', () => {
  const src = 'Just prose, no headings at all.';
  assert.equal(shared.sectionSlugAt(src, 5), 'top');
});

test('sectionSlugAt strips inline markers from heading text', () => {
  const src = '## Section with `code` and $math$\n\nprose here.';
  const pos = src.indexOf('prose here.');
  assert.equal(shared.sectionSlugAt(src, pos), 'section-with-code-and-math');
});

test('extractInlineHighlights captures adjacent footnote ref as note', () => {
  const src = 'Prose ==yellow:noted==[^note-top-1] more.\n\n[^note-top-1]: body.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].noteId, 'note-top-1');
  assert.equal(typeof hits[0].noteRefStart, 'number');
  assert.equal(typeof hits[0].noteRefEnd, 'number');
  assert.equal(src.slice(hits[0].noteRefStart, hits[0].noteRefEnd), '[^note-top-1]');
});

test('extractInlineHighlights leaves note fields null when no ref follows', () => {
  const src = 'Prose ==yellow:bare== more.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].noteId, null);
  assert.equal(hits[0].noteRefStart, null);
  assert.equal(hits[0].noteRefEnd, null);
});

test('extractInlineHighlights does not absorb a footnote ref separated by whitespace', () => {
  const src = 'Prose ==yellow:noted== [^note-top-1] more.\n\n[^note-top-1]: body.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].noteId, null);
});

test('resolveFootnoteDefs collects single-line def with body', () => {
  const src = 'Prose.\n\n[^note-top-1]: a single-line body.';
  const defs = shared.resolveFootnoteDefs(src);
  assert.ok(defs.has('note-top-1'));
  const d = defs.get('note-top-1');
  assert.equal(d.body, 'a single-line body.');
  assert.equal(src.slice(d.defStart, d.defEnd), '[^note-top-1]: a single-line body.');
});

test('resolveFootnoteDefs collects multi-line continuation body', () => {
  const src = [
    'Prose.',
    '',
    '[^n]: line one.',
    '    line two continuation.',
    '    line three.',
    '',
    'Other prose.',
  ].join('\n');
  const defs = shared.resolveFootnoteDefs(src);
  const d = defs.get('n');
  assert.equal(d.body, 'line one.\nline two continuation.\nline three.');
});

test('extractInlineHighlights populates noteBody when ref + def both present', () => {
  const src = 'P ==yellow:hi==[^note-test-1].\n\n[^note-test-1]: body with $\\sigma$ math.';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits[0].noteId, 'note-test-1');
  assert.equal(hits[0].noteBody, 'body with $\\sigma$ math.');
  assert.equal(hits[0].noteHasMath, true);
});

test('extractInlineHighlights leaves noteBody null when ref has no def', () => {
  const src = 'P ==yellow:hi==[^note-orphan].';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits[0].noteId, 'note-orphan');
  assert.equal(hits[0].noteBody, null);
  assert.equal(hits[0].noteDefStart, null);
});

test('extractInlineHighlights does NOT absorb non-`note-*` footnote refs (citation reservation)', () => {
  // Citation footnotes like [^smith2024] flush against highlights must remain
  // as ordinary footnote refs, not be misidentified as notes.
  const src = 'P ==yellow:hi==[^smith2024].\n\n[^smith2024]: Smith, J. (2024).';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits[0].noteId, null);
  assert.equal(hits[0].noteRefStart, null);
});

test('nextNoteIdForSection returns -1 when no notes exist in section', () => {
  const src = '## Section A\n\nPlain prose.';
  assert.equal(shared.nextNoteIdForSection(src, 'section-a'), 'note-section-a-1');
});

test('nextNoteIdForSection finds max existing N and increments', () => {
  const src = [
    '## Sec',
    '',
    'P ==yellow:a==[^note-sec-1] then ==yellow:b==[^note-sec-2] then ==yellow:c==[^note-sec-5].',
    '',
    '[^note-sec-1]: x.',
    '[^note-sec-2]: y.',
    '[^note-sec-5]: z.',
  ].join('\n');
  assert.equal(shared.nextNoteIdForSection(src, 'sec'), 'note-sec-6');
});

test('nextNoteIdForSection ignores other sections', () => {
  const src = [
    '## Sec A',
    '',
    'P ==yellow:a==[^note-sec-a-1].',
    '',
    '[^note-sec-a-1]: x.',
    '',
    '## Sec B',
    '',
    'P ==yellow:b==[^note-sec-b-9].',
    '',
    '[^note-sec-b-9]: y.',
  ].join('\n');
  assert.equal(shared.nextNoteIdForSection(src, 'sec-a'), 'note-sec-a-2');
  assert.equal(shared.nextNoteIdForSection(src, 'sec-b'), 'note-sec-b-10');
});

// ── CRLF regressions (bug 2026-05-18-01) ──────────────────────────────────────
// On Windows, survey files are CRLF. `resolveFootnoteDefs` split on '\n' leaves
// a trailing '\r' on every line; the def regex `(.*)$` then fails to match
// (`.` won't cross '\r', and JS `$` without /m/ anchors only at true EOS), so
// EVERY footnote definition in a CRLF file was dropped and every note became an
// orphan (noteBody/noteDefStart null → edit/delete throw "entry has no note").

test('resolveFootnoteDefs collects single-line def with body (CRLF)', () => {
  const src = 'Prose.\r\n\r\n[^note-top-1]: a single-line body.\r\n';
  const defs = shared.resolveFootnoteDefs(src);
  assert.ok(defs.has('note-top-1'));
  const d = defs.get('note-top-1');
  assert.equal(d.body, 'a single-line body.');
  // defStart/defEnd index the ORIGINAL (CRLF) source; the span runs through
  // the '\r' so defEnd lands on the terminating '\n' (deleteNote relies on
  // `source[defEnd] === '\n'`).
  assert.equal(src.slice(d.defStart, d.defEnd), '[^note-top-1]: a single-line body.\r');
  assert.equal(src[d.defEnd], '\n');
});

test('resolveFootnoteDefs collects multi-line continuation body (CRLF)', () => {
  const src = [
    'Prose.',
    '',
    '[^n]: line one.',
    '    line two continuation.',
    '    line three.',
    '',
    'Other prose.',
  ].join('\r\n');
  const defs = shared.resolveFootnoteDefs(src);
  const d = defs.get('n');
  assert.equal(d.body, 'line one.\nline two continuation.\nline three.');
});

test('extractInlineHighlights resolves noteBody on a CRLF document', () => {
  const src =
    'P ==orange: $E_s/N_0$==[^note-test-1] tail.\r\n\r\n' +
    '[^note-test-1]: This $\\frac{E_s}{N_0}$ is the matched-filter output SNR.\r\n';
  const hits = shared.extractInlineHighlights(src, 'a.md');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].noteId, 'note-test-1');
  assert.equal(hits[0].noteBody,
    'This $\\frac{E_s}{N_0}$ is the matched-filter output SNR.');
  assert.equal(hits[0].noteHasMath, true);
  assert.equal(typeof hits[0].noteDefStart, 'number');
  assert.equal(typeof hits[0].noteDefEnd, 'number');
});
