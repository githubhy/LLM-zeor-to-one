'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

// Require from the module under test — will fail (red) until implemented.
const { buildIgnoreMatcher, listMarkdownFiles } = require('../../lib/content-source');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fixture(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'vi-'));
  for (const [name, content] of Object.entries(files)) {
    const p = path.join(dir, name);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, content, 'utf8');
  }
  return dir;
}

// ---------------------------------------------------------------------------
// Tests: buildIgnoreMatcher built-in defaults
// ---------------------------------------------------------------------------

test('built-in defaults: node_modules/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('node_modules/'), true);
  assert.equal(m.ignores('node_modules/foo.md'), true);
});

test('built-in defaults: dist/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('dist/'), true);
  assert.equal(m.ignores('dist/bundle.js'), true);
});

test('built-in defaults: temp/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('temp/'), true);
  assert.equal(m.ignores('temp/scratch.md'), true);
});

test('built-in defaults: archive/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('archive/'), true);
});

test('built-in defaults: .viewer-highlights/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('.viewer-highlights/'), true);
});

test('built-in defaults: download/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('download/'), true);
});

test('built-in defaults: .git/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('.git/'), true);
});

test('built-in defaults: viewer/ is ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('viewer/'), true);
});

test('built-in defaults: ordinary docs are NOT ignored', () => {
  const m = buildIgnoreMatcher({});
  assert.equal(m.ignores('surveys/my-doc.md'), false);
  assert.equal(m.ignores('docs/guide.md'), false);
});

// ---------------------------------------------------------------------------
// Tests: project .viewerignore — glob patterns
// ---------------------------------------------------------------------------

test('project .viewerignore: glob **/*.scratch.md excludes a scratch file', () => {
  const dir = fixture({ '.viewerignore': '**/*.scratch.md\n' });
  const m = buildIgnoreMatcher({ projectIgnorePath: path.join(dir, '.viewerignore') });
  assert.equal(m.ignores('notes/work.scratch.md'), true);
  assert.equal(m.ignores('notes/work.md'), false);
});

// ---------------------------------------------------------------------------
// Tests: negation patterns
// ---------------------------------------------------------------------------

test('negation: !keep.md after *.md re-includes keep.md', () => {
  const dir = fixture({ '.viewerignore': '*.md\n!keep.md\n' });
  const m = buildIgnoreMatcher({ projectIgnorePath: path.join(dir, '.viewerignore') });
  assert.equal(m.ignores('other.md'), true);
  assert.equal(m.ignores('keep.md'), false);
});

// ---------------------------------------------------------------------------
// Tests: parent-dir hard limit
// ---------------------------------------------------------------------------

test('parent-dir hard limit: temp/ then !temp/keep.md still excludes keep.md', () => {
  // gitignore semantics: once a directory is excluded, negation patterns for
  // files inside it are not applied. This is the hard limit test from the spec.
  const dir = fixture({ '.viewerignore': 'temp/\n!temp/keep.md\n' });
  const m = buildIgnoreMatcher({ projectIgnorePath: path.join(dir, '.viewerignore') });
  assert.equal(m.ignores('temp/keep.md'), true, 'should still be ignored (parent-dir hard limit)');
});

// ---------------------------------------------------------------------------
// Tests: re-including .md under ignored directory with globstar
// ---------------------------------------------------------------------------

test('sim/** then !sim/**/*.md re-includes .md DIRECTLY under sim, not nested', () => {
  const dir = fixture({ '.viewerignore': 'sim/**\n!sim/**/*.md\n' });
  const m = buildIgnoreMatcher({ projectIgnorePath: path.join(dir, '.viewerignore') });
  // Honest gitignore semantics (empirically verified against the `ignore`
  // package): `sim/**` excludes sim/'s contents at every depth, INCLUDING the
  // subdirectory `sim/results/`. The negation `!sim/**/*.md` can only re-include
  // a file whose parent dir is not itself excluded — so a .md DIRECTLY under
  // sim/ is re-included, but a .md under an excluded subdir is NOT (the
  // parent-directory hard limit applies to negations too).
  assert.equal(m.ignores('sim/model.py'), true, 'non-md content under sim is excluded');
  assert.equal(m.ignores('sim/output.md'), false, 'md directly under sim is re-included');
  assert.equal(m.ignores('sim/results/output.md'), true, 'md under an excluded subdir stays excluded (hard limit)');
});

// ---------------------------------------------------------------------------
// Tests: absent .viewerignore (no crash, just built-ins)
// ---------------------------------------------------------------------------

test('absent projectIgnorePath: no crash; only built-ins apply', () => {
  const m = buildIgnoreMatcher({ projectIgnorePath: '/nonexistent/.viewerignore' });
  assert.equal(m.ignores('node_modules/'), true);
  assert.equal(m.ignores('my-survey.md'), false);
});

test('no opts arg: only built-ins apply', () => {
  const m = buildIgnoreMatcher();
  assert.equal(m.ignores('dist/'), true);
  assert.equal(m.ignores('surveys/foo.md'), false);
});

// ---------------------------------------------------------------------------
// Tests: perRootIgnorePath
// ---------------------------------------------------------------------------

test('per-root .viewerignore: patterns apply on top of defaults + project', () => {
  const projDir = fixture({ '.viewerignore': '' });
  const rootDir = fixture({ '.viewerignore': 'drafts/\n' });
  const m = buildIgnoreMatcher({
    projectIgnorePath: path.join(projDir, '.viewerignore'),
    perRootIgnorePath: path.join(rootDir, '.viewerignore'),
  });
  assert.equal(m.ignores('drafts/doc.md'), true);
  assert.equal(m.ignores('published/doc.md'), false);
});

// ---------------------------------------------------------------------------
// Tests: listMarkdownFiles with a matcher
// ---------------------------------------------------------------------------

test('listMarkdownFiles with matcher: drops order.json entry pointing at ignored file', () => {
  const dir = fixture({
    'order.json': JSON.stringify(['keep.md', 'ignored-dir/hidden.md']),
    'keep.md': '# Keep',
    'ignored-dir/hidden.md': '# Hidden',
    '.viewerignore': 'ignored-dir/\n',
  });
  const m = buildIgnoreMatcher({ projectIgnorePath: path.join(dir, '.viewerignore') });
  // honorRootOrderJson=true exercises the root short-circuit + ignore filter.
  const files = listMarkdownFiles(dir, { ignore: m, honorRootOrderJson: true });
  assert.ok(files.includes('keep.md'), 'keep.md should be present');
  assert.ok(!files.includes('ignored-dir/hidden.md'), 'ignored-dir/hidden.md should be dropped');
});

test('listMarkdownFiles with matcher: walker skips ignored dirs', () => {
  const dir = fixture({
    'surveys/a.md': '# A',
    'dist/bundle.md': '# Bundle',
    'temp/scratch.md': '# Scratch',
  });
  // Use built-in defaults (no project .viewerignore)
  const m = buildIgnoreMatcher({});
  const files = listMarkdownFiles(dir, { ignore: m });
  assert.ok(files.includes('surveys/a.md'), 'surveys/a.md should be included');
  assert.ok(!files.includes('dist/bundle.md'), 'dist/bundle.md should be excluded');
  assert.ok(!files.includes('temp/scratch.md'), 'temp/scratch.md should be excluded');
});

// Fix (review w7ny49x0k #1): the single-root compat path passes NO matcher, so
// it is byte-identical to the legacy walk — dist/temp/etc. markdown the user
// explicitly pointed at is SERVED, not pruned. Only the (matcher-bearing)
// multi-root path prunes the expanded noise set.
test('single-root (no matcher) is legacy byte-identical; only the matcher prunes the noise set', () => {
  const dir = fixture({
    'main.md': '# Main',
    'sub/s.md': '# Sub',
    'dist/bundle.md': '# Baked',
    'temp/scratch.md': '# Scratch',
    'node_modules/pkg/r.md': '# Dep',
  });
  // Single-root serve/publish call: { honorRootOrderJson:true }, NO ignore.
  const compat = listMarkdownFiles(dir, { honorRootOrderJson: true }).sort();
  assert.deepEqual(compat, ['dist/bundle.md', 'main.md', 'sub/s.md', 'temp/scratch.md'],
    'legacy skip set only (node_modules) — dist/temp/.md served, byte-identical to main');
  // Multi-root call: with the matcher, the expanded noise set is pruned.
  const pruned = listMarkdownFiles(dir, { ignore: buildIgnoreMatcher({}) }).sort();
  assert.deepEqual(pruned, ['main.md', 'sub/s.md'], 'matcher prunes dist/ and temp/');
});
