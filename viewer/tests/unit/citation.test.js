const test = require('node:test');
const assert = require('node:assert/strict');
const { buildCitation, resolveRepoPath, katexAwareText } = require('../../lib/citation');

const base = {
  selectedText: 'The FLL error is small.',
  paragraphAnchorId: 'p-tracking-loops-4',
  headingAnchorId: 'tracking-loops',
  headingText: 'Tracking Loops',
  documentTitle: 'Tracking Loops',
  relPath: 'surveys/ntn-initial-sync-tracking/tracking-loops.md',
  sourceLine: 142,
  viewerOrigin: 'http://localhost:3000',
};

test('github mode emits user-content- fragment prefix', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: {
      available: true,
      owner: 'acme',
      repo: 'receiver',
      sha: 'abc1234',
      branch: 'main',
      headPushed: true,
    },
  });
  assert.match(r.url, /^https:\/\/github\.com\/acme\/receiver\/blob\/abc1234\//);
  assert.match(r.url, /#user-content-p-tracking-loops-4$/);
  assert.equal(r.warnings.length, 0);
});

test('local mode uses raw anchor id, no user-content prefix', () => {
  const r = buildCitation({ ...base, linkMode: 'local', gitInfo: null });
  assert.match(r.url, /^http:\/\/localhost:3000\/\?file=/);
  assert.match(r.url, /#p-tracking-loops-4$/);
  assert.doesNotMatch(r.url, /user-content/);
});

test('relative mode emits plain path, markdown uses code span', () => {
  const r = buildCitation({ ...base, linkMode: 'relative', gitInfo: null });
  assert.equal(r.effectiveMode, 'relative');
  assert.match(r.url, /\.md#p-tracking-loops-4$/);
  assert.match(r.markdown, /`surveys\/.*?\.md#p-tracking-loops-4`/);
});

test('headPushed false surfaces a warning', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: {
      available: true,
      owner: 'a', repo: 'b', sha: 'cafef00d',
      branch: 'feat', headPushed: false,
    },
  });
  assert.ok(r.warnings.some((w) => /not pushed/i.test(w)));
  assert.match(r.url, /#user-content-/);
});

// Bug #3 regression: headPushed=null (no upstream tracking) was silently ignored.
// A branch without --set-upstream causes `git merge-base --is-ancestor HEAD @{upstream}`
// to exit with status 128 (not 1), setting headPushed=null rather than false.
// The fix: treat null as equally unverifiable and surface a warning.
test('regression Bug#3: headPushed null (no upstream) surfaces a verify warning', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: {
      available: true,
      owner: 'a', repo: 'b', sha: 'cafef00d',
      branch: 'feat', headPushed: null,
    },
  });
  // Before fix: r.warnings was empty. After fix: must contain a verify warning.
  assert.ok(
    r.warnings.some((w) => /verify/i.test(w)),
    `Expected a "verify" warning, got: ${JSON.stringify(r.warnings)}`,
  );
  // URL is still emitted (we don't downgrade to relative for null)
  assert.match(r.url, /github\.com/);
});

// Bug #10 regression: heading-fallback anchors must NOT be prefixed with
// `user-content-` in github mode. GitHub only prefixes user-authored HTML
// ids; heading slugs come from the markdown renderer and stay bare. Before
// the fix, clicking a heading-fallback citation URL landed at the top of
// the file because `#user-content-<slug>` matched nothing.
test('regression Bug#10: heading fallback in github mode uses bare slug, not user-content- prefix', () => {
  const r = buildCitation({
    ...base,
    paragraphAnchorId: null,
    linkMode: 'github',
    gitInfo: {
      available: true,
      owner: 'acme', repo: 'recv', sha: 'deadbeef',
      branch: 'main', headPushed: true,
    },
  });
  assert.ok(r.usedHeadingFallback);
  assert.match(r.url, /#tracking-loops$/);
  assert.doesNotMatch(r.url, /user-content/);
});

test('regression Bug#10: paragraph anchor in github mode still uses user-content- prefix', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: {
      available: true,
      owner: 'acme', repo: 'recv', sha: 'deadbeef',
      branch: 'main', headPushed: true,
    },
  });
  assert.equal(r.usedHeadingFallback, false);
  assert.match(r.url, /#user-content-p-tracking-loops-4$/);
});

test('missing paragraph anchor falls back to heading + (L<line>)', () => {
  const r = buildCitation({
    ...base,
    paragraphAnchorId: null,
    linkMode: 'local',
    gitInfo: null,
  });
  assert.equal(r.anchorId, 'tracking-loops');
  assert.ok(r.usedHeadingFallback);
  assert.match(r.markdown, /\(L142\)/);
});

test('github info unavailable downgrades with warning', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: { available: false, reason: 'no .git' },
  });
  assert.ok(r.warnings.some((w) => /GitHub info unavailable/.test(w)));
  assert.equal(r.effectiveMode, 'relative');
  assert.doesNotMatch(r.url, /github\.com/);
});

// Bug #4 regression: warning previously said "URL omitted" which implied no
// URL was present, but the citation does include a relative-path code span.
// The corrected text is "using relative path".
test('regression Bug#4: unavailable github info warning says "using relative path", not "omitted"', () => {
  const r = buildCitation({
    ...base,
    linkMode: 'github',
    gitInfo: { available: false, reason: 'no .git' },
  });
  assert.ok(
    r.warnings.some((w) => /using relative path/i.test(w)),
    `Expected "using relative path" in warning, got: ${JSON.stringify(r.warnings)}`,
  );
  assert.ok(
    !r.warnings.some((w) => /URL omitted/i.test(w)),
    'Old "URL omitted" text must not appear',
  );
});

test('regression: github URL includes the repo-root-relative path verbatim', () => {
  // Bug #2 — earlier versions passed only `currentFile` (basename within the
  // viewer's target dir). The client must now pass the full repo path.
  const r = buildCitation({
    ...base,
    relPath: 'surveys/ntn-initial-sync-tracking/tracking-loops.md',
    linkMode: 'github',
    gitInfo: {
      available: true, owner: 'acme', repo: 'recv',
      sha: 'deadbeef', branch: 'main', headPushed: true,
      repoRelDir: 'surveys/ntn-initial-sync-tracking',
    },
  });
  assert.match(
    r.url,
    /^https:\/\/github\.com\/acme\/recv\/blob\/deadbeef\/surveys\/ntn-initial-sync-tracking\/tracking-loops\.md#user-content-p-tracking-loops-4$/,
  );
});

test('multi-line selection preserves interior newlines in markdown', () => {
  const r = buildCitation({
    ...base,
    selectedText: 'Line one.\nLine two.\nLine three.',
    linkMode: 'local',
    gitInfo: null,
  });
  const quoteLines = r.markdown.split('\n').filter((l) => l.startsWith('> ') && !l.startsWith('> —'));
  // three quoted content lines
  assert.ok(quoteLines.length >= 3);
});

// ──────────────────────────────────────────────────────────────────────
// resolveRepoPath — regression for Bug #2 (GitHub URL missing repo subdir)
// ──────────────────────────────────────────────────────────────────────
test('resolveRepoPath prepends repoRelDir when gitInfo supplies it', () => {
  const out = resolveRepoPath('tracking-loops.md', {
    available: true,
    repoRelDir: 'surveys/ntn-initial-sync-tracking',
  });
  assert.equal(out, 'surveys/ntn-initial-sync-tracking/tracking-loops.md');
});

test('resolveRepoPath returns the bare file when gitInfo is unavailable', () => {
  assert.equal(resolveRepoPath('x.md', null), 'x.md');
  assert.equal(resolveRepoPath('x.md', { available: false }), 'x.md');
});

test('resolveRepoPath does not double-slash when repoRelDir has trailing/leading slashes', () => {
  const out = resolveRepoPath('x.md', { available: true, repoRelDir: '/a/b/' });
  assert.equal(out, 'a/b/x.md');
});

test('resolveRepoPath returns the bare file when viewer target is the repo root', () => {
  const out = resolveRepoPath('x.md', { available: true, repoRelDir: '' });
  assert.equal(out, 'x.md');
});

// ── multi-root (schema 2): per-root repoRelDir keyed by namespace id ──
const MR_GIT = {
  schema: 2,
  roots: {
    surveys: { available: true, repoRelDir: 'surveys' },
    docs: { available: true, repoRelDir: 'docs' },
  },
};

test('resolveRepoPath (multi-root) uses the OWNING root repoRelDir, not the first', () => {
  // A file in root B must not inherit root A's prefix (the 404 bug).
  assert.equal(resolveRepoPath('docs/foo.md', MR_GIT), 'docs/foo.md');
  assert.equal(resolveRepoPath('surveys/5g/intro.md', MR_GIT), 'surveys/5g/intro.md');
});

test('resolveRepoPath (multi-root) returns bare file for an unknown namespace', () => {
  assert.equal(resolveRepoPath('reports/x.md', MR_GIT), 'reports/x.md');
});

test('resolveRepoPath (schema 2 single-root) falls back to the empty-id root', () => {
  const single = { schema: 2, roots: { '': { available: true, repoRelDir: 'surveys/5g-nr-ldpc' } } };
  assert.equal(resolveRepoPath('intro.md', single), 'surveys/5g-nr-ldpc/intro.md');
});

test('resolveRepoPath (multi-root) unavailable owning root → bare file', () => {
  const g = { schema: 2, roots: { surveys: { available: false } } };
  assert.equal(resolveRepoPath('surveys/x.md', g), 'surveys/x.md');
});

// ──────────────────────────────────────────────────────────────────────
// katexAwareText — regression for Bug #1 (KaTeX triple-text duplication)
// ──────────────────────────────────────────────────────────────────────
// Minimal DOM shim: node's built-in runtime does not ship a DOM, so the
// helper is driven through a fake fragment that supports the three methods
// it uses (querySelectorAll, textContent, ownerDocument). This keeps the
// test lightweight while still exercising the KaTeX substitution path.
function fakeKatex({ tex, display = false }) {
  const ann = {
    textContent: tex,
    parentNode: null,
  };
  const mathml = {
    tagName: 'SPAN',
    className: 'katex-mathml',
    textContent: 'MATHML-GLYPHS-' + tex,
  };
  const katexHtml = { tagName: 'SPAN', className: 'katex-html', textContent: 'VIS-' + tex };
  const classList = {
    _list: display ? ['katex', 'katex-display'] : ['katex'],
    contains(c) { return this._list.includes(c); },
  };
  const node = {
    tagName: 'SPAN',
    classList,
    querySelector(sel) {
      if (sel.includes('annotation')) return ann;
      return null;
    },
    closest(sel) { return display && sel.includes('katex-display') ? node : null; },
    replaceWith(newNode) {
      node._replacement = newNode;
    },
  };
  return { node, mathml, katexHtml, get replacement() { return node._replacement; } };
}

function fakeFragment(children) {
  return {
    textContent: '',
    ownerDocument: {
      createTextNode(t) { return { _text: t, textContent: t }; },
    },
    querySelectorAll(sel) {
      if (sel === 'span.katex') return children.filter((c) => c.tagName === 'SPAN' && c.classList && c.classList.contains('katex'));
      if (sel === '.katex-mathml') {
        const out = [];
        for (const c of children) {
          if (c.className === 'katex-mathml') out.push({ remove() { c._removed = true; } });
        }
        return out;
      }
      return [];
    },
  };
}

test('katexAwareText: inline KaTeX becomes $tex$ (no mathml duplication)', () => {
  // Build a fragment where a katex span's textContent includes both the
  // mathml placeholder and visible glyphs, and the helper must replace it
  // with the LaTeX source.
  const k = fakeKatex({ tex: 'e^{j\\phi}', display: false });
  const fragment = fakeFragment([k.node]);
  // Simulate Range textContent after replacement: we drive katexAwareText
  // with a fragment whose children array drives querySelectorAll. After the
  // helper runs, it reads fragment.textContent — we simulate by patching it
  // to reflect the replacement node's text.
  const origGetText = Object.getOwnPropertyDescriptor;
  fragment.textContent = 'prefix $e^{j\\phi}$ suffix';
  const out = katexAwareText(fragment);
  assert.equal(out, 'prefix $e^{j\\phi}$ suffix');
  assert.ok(k.replacement, 'katex node was replaced');
  assert.equal(k.replacement._text, '$e^{j\\phi}$');
});

test('katexAwareText: display KaTeX becomes $$tex$$', () => {
  const k = fakeKatex({ tex: '\\sum_i x_i', display: true });
  const fragment = fakeFragment([k.node]);
  fragment.textContent = '$$\\sum_i x_i$$';
  katexAwareText(fragment);
  assert.equal(k.replacement._text, '$$\\sum_i x_i$$');
});

test('katexAwareText: resolves tex from data-tex attribute when MathML annotation is absent (output: html)', () => {
  // With KaTeX output:'html' (bug 2026-06-10-01 Tier-1 fix) there is no
  // <annotation> element; the renderer stamps the source on a data-tex
  // attribute of the root span instead.
  const k = fakeKatex({ tex: '', display: false }); // annotation path empty
  k.node.querySelector = () => null;                 // no MathML at all
  k.node.getAttribute = (name) => (name === 'data-tex' ? 'e^{j\\phi}' : null);
  const fragment = fakeFragment([k.node]);
  fragment.textContent = 'prefix $e^{j\\phi}$ suffix';
  const out = katexAwareText(fragment);
  assert.equal(out, 'prefix $e^{j\\phi}$ suffix');
  assert.ok(k.replacement, 'katex node was replaced');
  assert.equal(k.replacement._text, '$e^{j\\phi}$');
});

test('katexAwareText: display KaTeX with data-tex only becomes $$tex$$', () => {
  const k = fakeKatex({ tex: '', display: true });
  k.node.querySelector = () => null;
  k.node.getAttribute = (name) => (name === 'data-tex' ? '\\sum_i x_i' : null);
  const fragment = fakeFragment([k.node]);
  fragment.textContent = '$$\\sum_i x_i$$';
  katexAwareText(fragment);
  assert.equal(k.replacement._text, '$$\\sum_i x_i$$');
});

test('katexAwareText: collapses KaTeX inline-span whitespace runs', () => {
  const fragment = fakeFragment([]);
  fragment.textContent = 'foo   \u00A0 bar\n\n\nbaz';
  const out = katexAwareText(fragment);
  // Multiple spaces + NBSP collapse to single space; 3+ newlines → 2.
  assert.equal(out, 'foo bar\n\nbaz');
});
