'use strict';
/* ══════════════════════════════════════════════════════════════════
   Lightweight Markdown Viewer — client-side renderer
   ══════════════════════════════════════════════════════════════════ */

// Prevent browser from auto-restoring scroll on back/forward — we manage it
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let currentFile  = null;          // filename currently displayed
let fileContents = {};            // cache: filename → raw markdown
let fileList     = [];            // ordered list of filenames (namespaced in multi-root)
let viewerRoots  = [{ id: '', label: '' }]; // content roots from /api/files (schema 2)
let fileRevisions = {};           // cache: filename -> ETag revision
let annotationDocs = {};          // cache: filename -> annotation sidecar doc
let annotationRevisions = {};     // cache: filename -> sidecar revision
let manifestByFile = new Map();   // cache: filename -> highlight manifest entries
let manifestDirtyFiles = new Set();  // files whose cached entries are known-stale
let manifestNeedsFullRefresh = true; // force next loadManifest() to full-refetch

// Request versioning — guards async file loads against out-of-order completion
let loadRequestSeq    = 0;        // monotonic request counter
let activeLoadRequest = 0;        // ID of the latest accepted load

const contentEl     = document.getElementById('content');
const fileListEl    = document.getElementById('file-list');
const searchInput   = document.getElementById('search-input');
const searchRes     = document.getElementById('search-results');
const sidebar       = document.getElementById('sidebar');
const sidebarBtn    = document.getElementById('sidebar-toggle');
const outlineEl     = document.getElementById('outline-list');
const highlightsEl  = document.getElementById('highlights-list');
const settingsBtn   = document.getElementById('settings-btn');
const settingsSheet = document.getElementById('settings-sheet');
let   settingsOpen  = false;   // the #settings-sheet modal is open (declared early — TDZ-safe for syncMobileActiveSlot)
const searchBoxEl   = document.getElementById('search-box');
// Right context column (redesign T4) — Docs-only third zone. The Outline and
// Marks panels host the SAME outlineEl / highlightsEl nodes the sidebar drawer
// uses; applyChrome() reparents them between the two homes. Capture each node's
// ORIGINAL sidebar parent once here so reader/focus can restore them.
const rightPane     = document.getElementById('right-pane');
const rpOutline     = document.getElementById('rp-outline');
const rpMarks       = document.getElementById('rp-marks');
const rpPeek        = document.getElementById('rp-peek');
// Tracks whether the most recent focus landed inside #right-pane. A media-query
// hide moves focus to <body> BEFORE the JS 'change' event fires, so the right-
// pane focus-rescue (applyRightPane hide branch) needs this signal to know the
// orphaned <body> focus came from a now-hidden pane control.
let rpFocusWasInPane = false;
if (rightPane) {
  document.addEventListener('focusin', (e) => {
    rpFocusWasInPane = rightPane.contains(e.target);
  });
}
// Pane B — split-view secondary reference pane (redesign T7). A LIGHT read-only
// surface (no outline scroll-spy, no sidenotes, no progress): viewer.js renders
// a referenced section/file through render() into .cb-body and owns its open/
// close via the #app.split-open state class. See openSplitPane() below.
const contentBEl    = document.getElementById('content-b');
const cbBodyEl      = contentBEl ? contentBEl.querySelector('.cb-body') : null;
const cbCrumbEl     = contentBEl ? contentBEl.querySelector('#cb-crumb') : null;
const outlineHome   = outlineEl ? outlineEl.parentNode : null;     // #sidebar
const highlightsHome = highlightsEl ? highlightsEl.parentNode : null;
let rightPaneSeg    = 'outline';  // active segment: 'outline' | 'marks' | 'peek'
let activeTab = 'files';          // 'files' | 'outline' | 'highlights'
let buildOutlineSeq = 0;          // re-entry guard for async outline rebuilds
let buildHighlightsSeq = 0;       // re-entry guard for async highlights rebuilds
let pendingHighlightsScroll = null; // preserves sidebar scrollTop across bursty rebuilds
let pendingOutlineScroll = null;    // preserves outline sidebar scrollTop across rebuilds
let progressMode = 'whole-doc';   // 'whole-doc' | 'section'; set by loadSettings
const HighlightShared = window.ViewerHighlightShared || {};

// ---------------------------------------------------------------------------
// markdown-it setup
// ---------------------------------------------------------------------------
const md = window.markdownit({
  html: true,
  linkify: false,
  typographer: false,
});

// ── texmath plugin (KaTeX) ────────────────────────────────────────
// KaTeX runs with output:'html' — the default 'htmlAndMathml' emits a hidden
// MathML twin per equation, doubling math DOM (bug 2026-06-10-01: iOS WebKit
// jetsam-kills the content process on math-heavy files). The TeX source the
// MathML annotation used to carry (consumed by citation.js katexAwareText)
// is preserved as a data-tex attribute on the KaTeX root span instead.
if (window.texmath) {
  // Prototype-chained wrapper: texmath sees the full katex API; only
  // renderToString is overridden to stamp data-tex on the output.
  const texmathEngine = Object.create(window.katex);
  texmathEngine.renderToString = (tex, opts) => katexHtmlWithSource(tex, opts);
  md.use(window.texmath, {
    engine: texmathEngine,
    delimiters: 'dollars',
    katexOptions: {
      throwOnError: false,
      trust: true,
      macros: {},
      output: 'html',
    },
  });
}

// ── markdown-it-mark plugin (==highlight==) ───────────────────────
if (window.markdownitMark) {
  md.use(window.markdownitMark);
}

// ── markdown-it-footnote plugin ([^id] refs + defs) ───────────────────────
if (window.markdownitFootnote) {
  md.use(window.markdownitFootnote);
  // Override footnote_ref renderer to embed data-note-id on the <a> when the
  // footnote label starts with "note-". This lets Task 20's click handler
  // look up the matching sidebar entry without relying on numeric fn IDs.
  const _origFnRef = md.renderer.rules.footnote_ref;
  md.renderer.rules.footnote_ref = function(tokens, idx, options, env, slf) {
    const token = tokens[idx];
    const label = token.meta && token.meta.label;
    const base = _origFnRef(tokens, idx, options, env, slf);
    if (label && /^note-/.test(label)) {
      // Inject data-note-id onto the <a> element inside the <sup>.
      return base.replace('<a ', `<a data-note-id="${label}" `);
    }
    return base;
  };
}

// ── GFM-style heading anchors + inline-marker stripping — from highlight-shared ──
const stripInlineMarkersForSlug = HighlightShared.stripInlineMarkersForSlug;
// Per-render heading-anchor de-duplicator. Reset at the top of each md.render
// (see render()/note-body render) so identically-titled headings get stable
// GitHub-style `-1`/`-2` ids instead of colliding on one DOM id.
let _slugger = HighlightShared.makeUniqueSlugger();

// ── Folder grouping helper (matches buildSidebar's first-slash rule) ──
function folderOf(f) { const i = f.indexOf('/'); return i >= 0 ? f.slice(0, i) : ''; }
// Survey-level scope key for sibling grouping (outline / highlights / search).
// Single-root: the first segment (the survey) — identical to folderOf, so no
// behavior change. Multi-root: the first TWO segments (root/survey), so siblings
// scope to the survey, not the whole root. The first segment alone is the ROOT.
function isMultiRootMode() { return !(viewerRoots.length === 1 && viewerRoots[0].id === ''); }
function folderOf2(f) {
  if (!isMultiRootMode()) return folderOf(f);
  const parts = String(f).split('/');
  // 3+ segments (root/survey/…) → scope is the survey sub-folder (root/survey).
  // A root-level flat file (root/file.md, 2 segments) scopes to the ROOT, NOT
  // root/file — else every flat file (reports/, wikis/, proposals/, …) would be
  // its own singleton folder-scope, breaking the Folder outline/search/highlights
  // for those roots. This matches how renderFolderGroups buckets the files.
  if (parts.length >= 3) return `${parts[0]}/${parts[1]}`;
  return parts[0] || '';
}

// ── Parse ATX headings from raw markdown, skipping fenced code and $$ math.
function extractHeadings(markdown) {
  const headings = [];
  // Fresh per call so a sibling file's outline ids match what the renderer
  // would emit for that same file (GitHub-compatible duplicate suffixing).
  const slug = HighlightShared.makeUniqueSlugger();
  const lines = (markdown || '').split('\n');
  // Skip a leading YAML frontmatter block — its closing `---` would otherwise be
  // read as a setext underline turning the last frontmatter line (e.g. `title:`)
  // into a phantom h2 (the live DOM doesn't list frontmatter; sibling outlines
  // must match). Frontmatter is `---` on line 1 through the next `---` / `...`.
  let start = 0;
  if (lines[0] !== undefined && lines[0].trim() === '---') {
    for (let i = 1; i < lines.length; i++) {
      const t = lines[i].trim();
      if (t === '---' || t === '...') { start = i + 1; break; }
    }
  }
  let inFence = false, inMath = false;
  // The previous line eligible to be a setext-heading text line (a paragraph
  // line, not blank / list / blockquote / table / ATX / indented-code). When the
  // next line is a setext underline (=== → h1, --- → h2) this becomes a heading —
  // matching what markdown-it renders, so sibling outlines don't miss setext
  // headings the live-DOM outline (current file) already shows.
  let prevText = null;
  for (let li = start; li < lines.length; li++) {
    const line = lines[li];
    const stripped = line.trim();
    if (!inMath && /^(`{3,}|~{3,})/.test(stripped)) { inFence = !inFence; prevText = null; continue; }
    if (inFence) { prevText = null; continue; }
    if (!inMath && (stripped === '$$' || /^==\w+:\s*\$\$$/.test(stripped))) { inMath = true; prevText = null; continue; }
    if (inMath && (stripped === '$$' || stripped === '$$==')) { inMath = false; prevText = null; continue; }
    if (inMath) { prevText = null; continue; }
    const m = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (m) {
      const cleanTxt = stripInlineMarkersForSlug(m[2]);
      headings.push({ level: m[1].length, text: cleanTxt, id: slug(cleanTxt) });
      prevText = null;
      continue;
    }
    // Setext underline directly under a paragraph line — but a 4-space/tab
    // indented run is an indented code block, not a setext underline.
    if (prevText != null && /^(=+|-+)\s*$/.test(stripped) && !/^(?: {4,}|\t)/.test(line)) {
      const cleanTxt = stripInlineMarkersForSlug(prevText.trim());
      headings.push({ level: stripped[0] === '=' ? 1 : 2, text: cleanTxt, id: slug(cleanTxt) });
      prevText = null;
      continue;
    }
    // Track the current line's eligibility as a setext heading text line
    // (not blank / list / blockquote / table / ATX / indented-code).
    prevText = (stripped === '' || /^(?: {4,}|\t)/.test(line) || /^([-*+]\s|>\s?|\d+\.\s|\||#)/.test(stripped))
      ? null : line;
  }
  return headings;
}

// ── Block-level data-source-line annotation ──────────────────────
// Emit data-source-line on every block element so the highlight
// source mapper can locate the original markdown for a DOM range.
function srcLineAttr(token) {
  if (token.map && token.map[0] != null) {
    const origLine = _lineMap[token.map[0]] != null ? _lineMap[token.map[0]] : token.map[0];
    return ` data-source-line="${origLine}"`;
  }
  return '';
}

md.renderer.rules.heading_open = function(tokens, idx) {
  const token = tokens[idx];
  const tag = token.tag;
  const inline = tokens[idx + 1];
  const text = inline && inline.children
    ? inline.children.map(t => t.content).join('')
    : '';
  const id = _slugger(text);
  return `<${tag} id="${id}"${srcLineAttr(token)}>`;
};

// Generic block-open renderers that just need the tag + data-source-line
['paragraph_open', 'bullet_list_open', 'ordered_list_open',
 'list_item_open', 'table_open', 'blockquote_open'].forEach(rule => {
  md.renderer.rules[rule] = function(tokens, idx) {
    const token = tokens[idx];
    return `<${token.tag}${srcLineAttr(token)}>`;
  };
});

// Fence needs special handling to preserve language class.
// Mermaid fences are emitted as a raw-content .mermaid container for mermaid.js
// to post-process (turns them into SVG on renderToContent's mermaid.run() call).
md.renderer.rules.fence = function(tokens, idx) {
  const token = tokens[idx];
  const info = token.info ? token.info.trim() : '';
  if (info === 'mermaid') {
    // Mermaid needs the literal source (including `<br/>` in labels). Do NOT
    // escapeHtml; mermaid's parser reads innerHTML which browsers already
    // HTML-decode. Keep data-source-line so source-index lookup still works.
    return `<div class="mermaid"${srcLineAttr(token)}>${token.content}</div>\n`;
  }
  const langClass = info ? ` class="language-${escapeHtml(info)}"` : '';
  return `<pre${srcLineAttr(token)}><code${langClass}>${escapeHtml(token.content)}</code></pre>\n`;
};

// ---------------------------------------------------------------------------
// Highlight color post-processing
// ---------------------------------------------------------------------------
// Converts <mark>color: text</mark> → <mark class="hl-color">text</mark>
const HIGHLIGHT_COLORS = HighlightShared.HIGHLIGHT_COLORS || ['yellow', 'green', 'red', 'blue', 'orange', 'purple', 'teal', 'pink'];
const HL_COLOR_ALT = HighlightShared.HL_COLOR_ALT || HIGHLIGHT_COLORS.join('|');
const HL_REGEX = new RegExp(
  `<mark>(${HL_COLOR_ALT}):\\s*`,
  'gi'
);

function processHighlights(html) {
  return html.replace(HL_REGEX, (_, color) => `<mark class="hl-${color.toLowerCase()}">`);
}

// ---------------------------------------------------------------------------
// Display-math shielding
// ---------------------------------------------------------------------------
// Extract multi-line $$...$$ blocks BEFORE markdown-it's block parser runs,
// so that lines starting with +, -, *, etc. inside math are never mistaken
// for lists, emphasis, or other markdown constructs.

function shieldDisplayMath(markdown) {
  const blocks = [];
  const lineMap = [];   // lineMap[shieldedLine] = originalLine
  const lines  = markdown.split('\n');
  const output = [];
  let inMath   = false;
  let inFence  = false;
  let mathLines = [];
  let hlColor  = null;  // color prefix on the opening $$ line, if any
  let origIdx  = 0;

  for (const line of lines) {
    const stripped = line.trim();

    // Track fenced code blocks so we don't touch $$ inside them
    if (!inMath && /^(`{3,}|~{3,})/.test(stripped)) {
      inFence = !inFence;
      lineMap.push(origIdx);
      output.push(line);
      origIdx++; continue;
    }
    if (inFence) { lineMap.push(origIdx); output.push(line); origIdx++; continue; }

    // Single-line $$...$$ on its own line (with optional ==color: prefix and
    // ==suffix). Must be detected BEFORE the multi-line opening rule below,
    // otherwise a line like `$$x$$` would open math (matching `$$`) and then
    // never find a matching close on its own line.
    if (!inMath) {
      const singleLine = stripped.match(
        new RegExp(`^(?:==(${HL_COLOR_ALT}):\\s*)?\\$\\$([^\\$\\n][\\s\\S]*?)\\$\\$(==)?$`)
      );
      if (singleLine) {
        const color = singleLine[1] || null;
        const content = singleLine[2];
        blocks.push(content);
        const colorAttr = color ? ` data-hl-color="${color}"` : '';
        lineMap.push(origIdx);
        output.push(`<div data-math-block="${blocks.length - 1}"${colorAttr}></div>`);
        origIdx++; continue;
      }
    }

    // Opening delimiter: bare $$ or ==color: $$
    if (!inMath) {
      const colorM = stripped.match(new RegExp(`^==(${HL_COLOR_ALT}):\\s*\\$\\$$`));
      if (stripped === '$$' || colorM) {
        inMath    = true;
        hlColor   = colorM ? colorM[1] : null;
        mathLines = [];
        origIdx++; continue;      // consume opening $$
      }
    }

    // Closing delimiter: bare $$ or $$==
    if (inMath && (stripped === '$$' || stripped === '$$==')) {
      inMath = false;
      blocks.push(mathLines.join('\n'));
      const colorAttr = hlColor ? ` data-hl-color="${hlColor}"` : '';
      lineMap.push(origIdx - mathLines.length - 1);   // map placeholder to opening $$
      output.push(`<div data-math-block="${blocks.length - 1}"${colorAttr}></div>`);
      hlColor = null;
      origIdx++; continue;        // consume closing $$
    }

    if (inMath) {
      mathLines.push(line);
      origIdx++; continue;
    }

    lineMap.push(origIdx);
    output.push(line);
    origIdx++;
  }

  // Unclosed block — restore original lines so nothing is silently lost
  if (inMath) {
    const openLine = hlColor ? `==${hlColor}: $$` : '$$';
    output.push(openLine);
    output.push(...mathLines);
  }

  return { text: output.join('\n'), blocks, lineMap };
}

// Escape a string for use inside a double-quoted HTML attribute value.
function escapeAttr(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;');
}

// Render TeX through KaTeX with output:'html' and stamp the source on a
// data-tex attribute of the root .katex span (citation.js reads it back;
// the MathML <annotation> that used to carry it is no longer emitted).
function katexHtmlWithSource(tex, opts) {
  const rendered = window.katex.renderToString(tex, Object.assign({}, opts, { output: 'html' }));
  // displayMode output nests <span class="katex"> inside .katex-display;
  // a first-occurrence string replace lands on the root in both modes.
  return rendered.replace('<span class="katex">', `<span class="katex" data-tex="${escapeAttr(tex)}">`);
}

// Above this many display blocks in one document, equation bodies render
// lazily (IntersectionObserver) instead of eagerly — bug 2026-06-10-01.
const LAZY_DISPLAY_MATH_THRESHOLD = 80;

function renderedDisplayMathHtml(math, idx, colorClass) {
  try {
    const rendered = katexHtmlWithSource(math, {
      displayMode: true,
      throwOnError: false,
      trust: true,
      macros: {},
    });
    return `<div data-math-block="${idx}" class="display-math-wrap${colorClass}">${rendered}</div>`;
  } catch (e) {
    return `<div data-math-block="${idx}" class="katex-error${colorClass}"><pre>${escapeHtml(math)}</pre></div>`;
  }
}

function restoreDisplayMath(html, blocks) {
  const lazy = blocks.length > LAZY_DISPLAY_MATH_THRESHOLD;
  return html.replace(
    /<div data-math-block="(\d+)"(?: data-hl-color="(\w+)")?><\/div>/g,
    (_, idx, color) => {
      const math = blocks[parseInt(idx)];
      const colorClass = color ? ` hl-${color}` : '';
      if (lazy) {
        // Placeholder sized to roughly one rendered row per source line so
        // the scrollbar and anchor offsets are stable before lazy render.
        const lines = String(math).split('\n').filter((l) => l.trim()).length || 1;
        const minH = (lines * 2.2 + 1).toFixed(1);
        return `<div data-math-block="${idx}" data-math-pending="1" class="display-math-wrap math-pending${colorClass}" style="min-height:${minH}em"></div>`;
      }
      return renderedDisplayMathHtml(math, idx, colorClass);
    }
  );
}

// ── Lazy display-math rendering (large documents) ────────────────────
let lazyMathBlocks = null;     // blocks array backing the current render
let lazyMathObserver = null;
let lazyMathRefreshTimer = 0;

function renderPendingMathBlock(el) {
  const idx = parseInt(el.dataset.mathBlock);
  const math = lazyMathBlocks ? lazyMathBlocks[idx] : undefined;
  // In-place render: the wrapper element (and any attributes stamped on it
  // after the initial render, e.g. data-source-line) stays in the DOM.
  el.removeAttribute('data-math-pending');
  el.classList.remove('math-pending');
  el.style.minHeight = '';
  if (math === undefined) return;
  try {
    el.innerHTML = katexHtmlWithSource(math, {
      displayMode: true,
      throwOnError: false,
      trust: true,
      macros: {},
    });
  } catch (e) {
    el.classList.remove('display-math-wrap');
    el.classList.add('katex-error');
    el.innerHTML = `<pre>${escapeHtml(math)}</pre>`;
  }
}

function setupLazyDisplayMath() {
  if (lazyMathObserver) { lazyMathObserver.disconnect(); lazyMathObserver = null; }
  const pending = contentEl.querySelectorAll('[data-math-pending]');
  // Containment CSS (content-visibility) is scoped to lazy documents; the
  // class persists for the document's lifetime even after all blocks render.
  contentEl.classList.toggle('lazy-math-doc', pending.length > 0);
  if (!pending.length) return;
  lazyMathObserver = new IntersectionObserver((entries) => {
    let renderedAny = false;
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      lazyMathObserver.unobserve(entry.target);
      renderPendingMathBlock(entry.target);
      renderedAny = true;
    }
    if (renderedAny) {
      // Heading tops shift as equations materialize; keep outline-sync and
      // reading-progress honest (debounced — batches arrive in bursts). The
      // SAME shift desynchronizes the Tufte margin sidenotes (each is frozen at
      // its anchor's top, but a placeholder growing ABOVE an anchor pushes that
      // anchor — and the line it cites — down while the sidenote stays put), so
      // re-run the O(n) de-collision pass in the same debounce. layoutSidenotes()
      // alone (not a full rebuild) suffices and is cheap.
      clearTimeout(lazyMathRefreshTimer);
      lazyMathRefreshTimer = setTimeout(() => {
        scrollSyncRefreshLayout();
        if (sidenoteBand) layoutSidenotes();
      }, 150);
    }
  }, { root: null, rootMargin: '2000px 0px' });
  pending.forEach((el) => lazyMathObserver.observe(el));
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
let _lineMap = [];   // shielded→original line mapping, set during render()

function render(markdown) {
  const { text, blocks, lineMap } = shieldDisplayMath(markdown);
  _lineMap = lineMap;
  _slugger = HighlightShared.makeUniqueSlugger();
  lazyMathBlocks = blocks;   // backs lazy display-math rendering, if engaged
  let html = md.render(text);
  if (blocks.length) html = restoreDisplayMath(html, blocks);
  html = processHighlights(html);
  return html;
}

// Render markdown for the secondary split pane (Pane B). Mirrors render() but
// (a) forces EAGER display-math — Pane B has no IntersectionObserver, so every
// equation must render up front — and (b) never touches the global
// `lazyMathBlocks` that Pane A's lazy renderer depends on. `_slugger` /
// `_lineMap` are reset for the synchronous md.render() pass exactly as render()
// does; Pane A's next render() resets them again, so there is no cross-pane leak.
function renderForPane(markdown) {
  const { text, blocks, lineMap } = shieldDisplayMath(markdown);
  _lineMap = lineMap;
  _slugger = HighlightShared.makeUniqueSlugger();
  let html = md.render(text);
  if (blocks.length) {
    // Eager restore for every block (no lazy threshold): the placeholder divs
    // emitted by shieldDisplayMath are replaced with rendered KaTeX directly.
    html = html.replace(
      /<div data-math-block="(\d+)"(?: data-hl-color="(\w+)")?><\/div>/g,
      (_, idx, color) => renderedDisplayMathHtml(blocks[parseInt(idx)], idx, color ? ` hl-${color}` : '')
    );
  }
  html = processHighlights(html);
  return html;
}

// Process any .mermaid containers left by the fence renderer.
// Each container already has data-source-line from markdown-it; mermaid.run()
// replaces the container's innerHTML with the rendered SVG.
async function renderMermaidDiagrams() {
  if (!window.mermaid || typeof window.mermaid.run !== 'function') return;
  const nodes = Array.from(contentEl.querySelectorAll('div.mermaid:not([data-processed="true"])'));
  if (!nodes.length) return;
  // Capture the raw diagram source before mermaid.run() replaces innerHTML
  // with SVG, so rethemeMermaid() can restore it for a re-render.
  // Use innerHTML (not textContent): mermaid reads innerHTML at render time
  // (confirmed in vendored mermaid.min.js run(): `s=u.innerHTML`), and the
  // fence renderer passes raw source through unescaped so `<br/>` in labels
  // survives as a real BR element by the time we get here. textContent would
  // silently drop the BR, merging multi-line labels on re-render.
  for (const n of nodes) {
    if (!n.dataset.mermaidSrc) n.dataset.mermaidSrc = n.innerHTML;
  }
  try {
    await window.mermaid.run({ nodes });
  } catch (e) {
    // Render-level failures (parse errors, syntax issues) are reported per
    // node by mermaid; keep the viewer alive and surface the error in-place.
    console.warn('mermaid.run() reported errors:', e);
  }
}

// ---------------------------------------------------------------------------
// Footnote-ref hover tooltip (Task 21)
// ---------------------------------------------------------------------------
const noteRefTooltip = (() => {
  const el = document.createElement('div');
  el.className = 'note-ref-tooltip';
  document.body.appendChild(el);
  return el;
})();
let noteRefTooltipTimer = null;

function getNoteBodyById(noteId) {
  if (!currentFile) return null;
  const entries = manifestByFile.get(currentFile) || [];
  const e = entries.find(x => x.noteId === noteId);
  return e?.noteBody || null;
}

function showNoteRefTooltip(anchor, noteId) {
  const body = getNoteBodyById(noteId);
  if (!body) return;
  noteRefTooltip.textContent = body.length > 120 ? body.slice(0, 120) + '…' : body;
  const rect = anchor.getBoundingClientRect();
  // Position below-center of the ref so it doesn't cover it.
  const tooltipW = 360;
  let left = rect.left + rect.width / 2 - tooltipW / 2;
  left = Math.max(8, Math.min(left, document.documentElement.clientWidth - tooltipW - 8));
  noteRefTooltip.style.left = left + 'px';
  noteRefTooltip.style.top = (rect.bottom + 6) + 'px';
  noteRefTooltip.classList.add('visible');
}

function hideNoteRefTooltip() {
  noteRefTooltip.classList.remove('visible');
  if (noteRefTooltipTimer) {
    clearTimeout(noteRefTooltipTimer);
    noteRefTooltipTimer = null;
  }
}

// ---------------------------------------------------------------------------
// Footnote-ref click → sidebar scroll/expand/flash (Task 20)
// ---------------------------------------------------------------------------
function installFootnoteRefHandlers() {
  const refs = contentEl.querySelectorAll('sup.footnote-ref a, .footnote-ref a');
  refs.forEach((a) => {
    if (a.dataset.notesHandlerWired === '1') return;
    a.dataset.notesHandlerWired = '1';
    a.addEventListener('click', (e) => {
      const noteId = a.dataset.noteId || '';
      // Only intercept our note-* ids; other footnotes keep default behavior.
      if (!/^note-/.test(noteId)) return;
      e.preventDefault();
      scrollSidebarToNoteEntry(noteId);
    });
    a.addEventListener('mouseenter', () => {
      const noteId = a.dataset.noteId;
      if (!noteId || !/^note-/.test(noteId)) return;
      if (noteRefTooltipTimer) clearTimeout(noteRefTooltipTimer);
      noteRefTooltipTimer = setTimeout(() => showNoteRefTooltip(a, noteId), 250);
    });
    a.addEventListener('mouseleave', () => {
      hideNoteRefTooltip();
    });
  });
}

async function scrollSidebarToNoteEntry(noteId) {
  // The note entry lives in the sidebar — in any overlay layout (reader
  // desktop sheet, mobile bottom sheet) the sidebar is off-canvas, so
  // without opening it the tab switch below is invisible and the click
  // reads as a no-op. Mobile included since redesign 03 (Plan 02 had
  // scoped this to desktop; decision 2026-06-12-03 item 3).
  if (isOverlayChrome() && !isDrawerOpen()) openDrawer();
  // Ensure the Highlights tab is active and its entries are rendered.
  // buildHighlights() is async (fetches manifest); we must await it so the
  // row lookup below is guaranteed to run after the DOM is populated.
  if (activeTab !== 'highlights') {
    // Update tab button/pane visibility synchronously first so the tab
    // appears active immediately (switchTab would also call buildHighlights,
    // but we call it directly here to be able to await it).
    activeTab = 'highlights';
    document.querySelectorAll('.sidebar-tab').forEach(t => {
      const on = t.dataset.tab === 'highlights';
      t.classList.toggle('active', on);
      if (t.hasAttribute('role')) t.setAttribute('aria-selected', String(on));
    });
    syncRovingTabindex(document.getElementById('sidebar-tabs'));
    fileListEl.classList.add('tab-hidden');
    outlineEl.classList.add('tab-hidden');
    highlightsEl.classList.remove('tab-hidden');
  }
  await buildHighlights();
  // Find row by data-note-id (set in Task 18's renderHlEntries).
  const row = highlightsEl.querySelector(`[data-note-id="${noteId}"]`);
  if (!row) return;
  row.classList.add('hl-note-expanded');
  // Lazy-render markdown body if not yet rendered (mirrors Task 18).
  const body = row.querySelector('.hl-note-body');
  if (body && body.dataset.rendered === '0') {
    const wrapper = document.createElement('div');
    wrapper.className = 'hl-note-body-rendered';
    _slugger = HighlightShared.makeUniqueSlugger();
    wrapper.innerHTML = md.render(body.dataset.noteBody || '');
    const editBtn = body.querySelector('.hl-note-edit');
    if (editBtn) body.insertBefore(wrapper, editBtn);
    else body.appendChild(wrapper);
    body.dataset.rendered = '1';
  }
  row.scrollIntoView({ block: 'center', behavior: 'smooth' });
  row.classList.add('hl-flash');
  setTimeout(() => row.classList.remove('hl-flash'), 800);
}

// ---------------------------------------------------------------------------
// In-situ peeks (redesign 06) — anchored popover for same-file eq/ref/sec refs
// ---------------------------------------------------------------------------
const peekPopover = document.getElementById('peek-popover');
const peekBody    = document.getElementById('peek-body');
const peekGoto    = document.getElementById('peek-goto');
let peekShowTimer = null;
let peekHideTimer = null;
let peekGotoId    = null;
let peekReturnFocus = null;

function peekClearTimers() {
  if (peekShowTimer) { clearTimeout(peekShowTimer); peekShowTimer = null; }
  if (peekHideTimer) { clearTimeout(peekHideTimer); peekHideTimer = null; }
}
function hidePeek() {
  peekClearTimers();
  if (!peekPopover || peekPopover.hidden) return;
  peekPopover.hidden = true;
  peekBody.innerHTML = '';
  peekGotoId = null;
  // Restore focus to the trigger when the peek was opened via click/keyboard
  // (review wrnjhusbu — keyboard reachability).
  if (peekReturnFocus && document.body.contains(peekReturnFocus)) {
    try { peekReturnFocus.focus(); } catch (e) { /* element gone */ }
  }
  peekReturnFocus = null;
}

// Nearest [data-math-block] that follows the anchor in document order — robust
// to the anchor being wrapped in a <p> (nextElementSibling would miss it).
function mathBlockAfter(anchor) {
  const blocks = contentEl.querySelectorAll('[data-math-block]');
  for (const b of blocks) {
    if (anchor.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) return b;
  }
  return null;
}
function buildEqPeek(anchorId) {
  const anchor = document.getElementById(anchorId);
  if (!anchor) return null;
  const block = mathBlockAfter(anchor);
  if (!block) return null;
  const wrap = document.createElement('div');
  wrap.className = 'peek-math';
  if (block.dataset.mathPending && lazyMathBlocks) {
    // Render a STANDALONE copy from the lazy store — never force the page copy
    // (spec section 9). idx indexes lazyMathBlocks identically to the page.
    const idx = parseInt(block.dataset.mathBlock, 10);
    const tex = lazyMathBlocks[idx];
    if (tex === undefined) return null;
    try {
      wrap.innerHTML = katexHtmlWithSource(tex, { displayMode: true, throwOnError: false, trust: true, macros: {} });
    } catch (e) { wrap.textContent = tex; }
  } else {
    const rendered = block.querySelector('.katex-display') || block.querySelector('.katex');
    if (!rendered) return null;
    wrap.appendChild(rendered.cloneNode(true));
  }
  return wrap;
}
function buildRefPeek(anchorId) {
  const anchor = document.getElementById(anchorId);
  if (!anchor) return null;
  const block = anchor.closest('p, li, blockquote, div');
  if (!block) return null;
  const clone = block.cloneNode(true);
  clone.querySelectorAll('a[id^="ref-"]').forEach((a) => a.remove());   // drop the anchor itself
  clone.querySelectorAll('a[href^="http"]').forEach((a) => { a.target = '_blank'; a.rel = 'noopener'; });
  const wrap = document.createElement('div');
  wrap.className = 'peek-ref';
  wrap.innerHTML = clone.innerHTML;
  if (!wrap.innerHTML.trim()) return null;     // anchor-only entry → fall back to jump
  return wrap;
}
function buildSecPeek(anchorId) {
  const anchor = document.getElementById(anchorId);
  if (!anchor) return null;
  const heading = anchor.closest('h1, h2, h3, h4, h5, h6');
  if (!heading) return null;
  const wrap = document.createElement('div');
  wrap.className = 'peek-sec';
  const hc = heading.cloneNode(true);
  hc.querySelectorAll('a[id^="sec-"]').forEach((a) => a.remove());
  const head = document.createElement('div');
  head.className = 'peek-sec-heading';
  head.innerHTML = hc.innerHTML;
  wrap.appendChild(head);
  // First following paragraph (stop at the next heading).
  let sib = heading.nextElementSibling;
  while (sib && !/^H[1-6]$/.test(sib.tagName) && sib.tagName !== 'P') sib = sib.nextElementSibling;
  if (sib && sib.tagName === 'P') {
    const body = document.createElement('div');
    body.className = 'peek-sec-body';
    body.innerHTML = sib.cloneNode(true).innerHTML;
    wrap.appendChild(body);
  }
  return wrap;
}
function buildPeekContent(kind, anchorId) {
  if (kind === 'eq')  return buildEqPeek(anchorId);
  if (kind === 'ref') return buildRefPeek(anchorId);
  if (kind === 'sec') return buildSecPeek(anchorId);
  return null;
}
// Returns true if a peek was shown, false if the target was unresolvable.
// focusOnOpen moves focus into the popover (click/keyboard activation); hover
// passes it falsy so a mouse preview never steals focus mid-read.
function showPeek(anchorEl, parsed, focusOnOpen) {
  const anchorId = `${parsed.kind}-${parsed.id}`;
  const content = buildPeekContent(parsed.kind, anchorId);
  if (!content) return false;
  // In Docs the right pane owns the preview surface: mirror the same content
  // into #rp-peek and auto-switch to the Peek segment. The floating popover
  // below still drives reader/focus (where the pane is hidden).
  if (rpPeek && document.documentElement.dataset.chrome === 'docs') {
    renderPanePeek(content.cloneNode(true), anchorId);
  }
  hidePeek();                                  // one peek at a time
  peekBody.appendChild(content);
  peekGotoId = anchorId;
  // Measure off-screen, then clamp into the viewport near the trigger.
  peekPopover.hidden = false;
  peekPopover.style.left = '-9999px';
  peekPopover.style.top = '-9999px';
  const rect = anchorEl.getBoundingClientRect();
  const w = peekPopover.offsetWidth || 420;
  const h = peekPopover.offsetHeight || 460;   // match CSS max-height fallback
  const { left, top } = clampToolbarBox(rect, w, h);
  peekPopover.style.left = left + 'px';
  peekPopover.style.top = top + 'px';
  if (focusOnOpen) { peekReturnFocus = anchorEl; peekGoto.focus(); }
  return true;
}

// Mirror a peek into the Docs right-pane Peek segment and switch to it. The
// content is a clone of what the floating popover shows; a "Go to" footer
// reuses the same jump as the popover so the pane is fully interactive.
function renderPanePeek(content, anchorId) {
  if (!rpPeek) return;
  rpPeek.innerHTML = '';
  rpPeek.appendChild(content);
  const goto = document.createElement('button');
  goto.type = 'button';
  goto.className = 'rp-peek-goto';
  goto.textContent = 'Go to ↗';
  goto.addEventListener('click', () => { updateURL(currentFile, anchorId); scrollToAnchor(anchorId); });
  rpPeek.appendChild(goto);
  // Nested ref-links inside the pane navigate (jump), matching the popover.
  rpPeek.addEventListener('click', panePeekLinkNav);
  setRightPaneSeg('peek', { silent: true });
}
function panePeekLinkNav(e) {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  e.preventDefault();
  const id = a.getAttribute('href').slice(1);
  updateURL(currentFile, id);
  scrollToAnchor(id);
}

if (peekPopover) {
  peekGoto.addEventListener('click', () => {
    const id = peekGotoId;
    hidePeek();
    if (id) { updateURL(currentFile, id); scrollToAnchor(id); }
  });
  const peekClose = document.getElementById('peek-close');
  if (peekClose) peekClose.addEventListener('click', hidePeek);
  // Nested ref-links inside the peek navigate (jump + dismiss), never nest.
  peekBody.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;                            // external links keep default (new tab)
    e.preventDefault();
    const id = a.getAttribute('href').slice(1);
    hidePeek();
    updateURL(currentFile, id);
    scrollToAnchor(id);
  });
  // Dismiss: Esc, outside pointerdown (but not on a trigger or the popover), scroll.
  document.addEventListener('keydown', (e) => {
    if (peekPopover.hidden) return;
    if (e.key === 'Escape') { hidePeek(); e.stopPropagation(); }
  });
  document.addEventListener('pointerdown', (e) => {
    if (peekPopover.hidden) return;
    if (peekPopover.contains(e.target)) return;
    if (e.target.closest('a[href^="#eq-"], a[href^="#ref-"], a[href^="#sec-"]')) return;
    hidePeek();
  });
  window.addEventListener('scroll', () => { if (!peekPopover.hidden) hidePeek(); }, true);
  // Hover-bridge: keep the peek alive while the pointer is over it.
  peekPopover.addEventListener('mouseenter', peekClearTimers);
  peekPopover.addEventListener('mouseleave', () => { peekHideTimer = setTimeout(hidePeek, 350); });
}

// Wire hover (300ms intent) + click on same-file eq/ref/sec ref links. Mirrors
// installFootnoteRefHandlers; re-run per render (idempotent via data-peekWired).
function installPeekHandlers() {
  if (!peekPopover) return;
  const refs = contentEl.querySelectorAll('a[href^="#eq-"], a[href^="#ref-"], a[href^="#sec-"]');
  refs.forEach((a) => {
    if (a.dataset.peekWired === '1') return;
    a.dataset.peekWired = '1';
    const parsed = window.PeekTarget.parsePeekHref(a.getAttribute('href'));
    if (!parsed.kind || !parsed.sameFile) return;     // cross-file / non-peekable
    const anchorId = `${parsed.kind}-${parsed.id}`;
    a.addEventListener('mouseenter', () => {
      peekClearTimers();
      peekShowTimer = setTimeout(() => showPeek(a, parsed), 300);   // intent delay
    });
    a.addEventListener('mouseleave', () => {
      if (peekShowTimer) { clearTimeout(peekShowTimer); peekShowTimer = null; }
      peekHideTimer = setTimeout(hidePeek, 350);                     // hover-bridge
    });
    a.addEventListener('click', (e) => {
      e.preventDefault();                                            // stops handleLinkClick scroll
      peekClearTimers();
      // Modifier-click (Ctrl/Cmd) opens the target in the split reference pane
      // instead of the floating peek — at the ≥1440px gate. Below the gate (or
      // if the open fails) it falls back to the peek / navigation path.
      if ((e.ctrlKey || e.metaKey) && openSplitPane(currentFile, anchorId)) return;
      if (!showPeek(a, parsed, true)) { updateURL(currentFile, anchorId); scrollToAnchor(anchorId); }
    });
  });
}

// ---------------------------------------------------------------------------
// Split-view secondary reference pane (Pane B, redesign T7)
// ---------------------------------------------------------------------------
// Pane B (#content-b) is a LIGHT read-only companion to the full-featured Pane A
// (#content). It renders a referenced section/file through renderForPane() into
// .cb-body — its own scroll, its own breadcrumb, its own close control — and
// SCOPES every post-render step (KaTeX is eager via renderForPane; mermaid runs
// scoped to #content-b) to itself. It deliberately has NO outline scroll-spy, NO
// sidenote band, and NO progress: those stay Pane A's, untouched, so none of
// T1–T7 regress. Opening requires the ≥1440px gate (mqlSplit) and a non-mobile
// shell; the floating peek remains the resolution path everywhere else.
//
// The pane file it currently shows (so a re-open targeting the same file just
// re-scrolls instead of re-rendering).
let splitPaneFile = null;
// The element focus should return to when Pane B closes. Pane B has Tab-
// focusable controls (.cb-close + rendered <a> links) and never inerts the
// background, so closing it (button / Esc) hides the focused element out from
// under a keyboard user; without a saved target focus falls to <body>
// (bug-2026-06-13-02 failure class). Captured on open, restored on close via
// the same getClientRects visibility probe closeSettings() uses.
let splitReturnFocus = null;

function isSplitOpen() { return !!(appEl && appEl.classList.contains('split-open')); }

// Gate: wide-desktop (≥1440px) and NOT the mobile shell. Mirrors the CSS
// @media (min-width: 1440px) floor; below it the pane is unavailable and the
// caller falls back to normal navigation / the floating peek.
function splitGateActive() {
  return !!contentBEl && mqlSplit.matches && !mqlNarrow.matches;
}

// Render a file's markdown into Pane B and scroll to an anchor (if any).
// `markdown` is the raw source; KaTeX renders eagerly (no IntersectionObserver),
// mermaid runs scoped to #content-b. Relative image paths resolve against the
// pane's file dir, mirroring fixRelativePaths() for Pane A.
function renderSplitContent(markdown, file, anchor) {
  if (!cbBodyEl) return;
  cbBodyEl.innerHTML = renderForPane(markdown);
  // Resolve relative image src against the pane file's directory.
  const slash = file ? file.lastIndexOf('/') : -1;
  const dir = slash >= 0 ? file.slice(0, slash) : '';
  if (dir) {
    cbBodyEl.querySelectorAll('img[src]').forEach((img) => {
      const src = img.getAttribute('src');
      if (src && !src.startsWith('/') && !src.startsWith('http')) img.setAttribute('src', `/${dir}/${src}`);
    });
    cbBodyEl.querySelectorAll('a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      if (!href || href.startsWith('/') || href.startsWith('#')) return;
      if (/^[a-z][a-z0-9+.-]*:/i.test(href) || /\.md(#.*)?$/i.test(href)) return;
      a.setAttribute('href', `/${dir}/${href}`);
    });
  }
  if (cbCrumbEl) cbCrumbEl.textContent = file || '';
  renderMermaidIn(cbBodyEl);
  if (anchor) {
    // The anchor lives inside cbBodyEl; scroll the pane's own scroller to it
    // (NOT the window). A double-rAF lets KaTeX settle so the offset is final.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const target = cbBodyEl.querySelector(`#${CSS.escape(anchor)}`)
        || document.getElementById(anchor);
      if (target && cbBodyEl.contains(target)) {
        const top = target.getBoundingClientRect().top - cbBodyEl.getBoundingClientRect().top + cbBodyEl.scrollTop;
        cbBodyEl.scrollTo({ top: Math.max(0, top - 24), behavior: 'auto' });
        flashAnchor(target);
      }
    }));
  } else {
    cbBodyEl.scrollTop = 0;
  }
}

// Scoped mermaid render (sibling of renderMermaidDiagrams, which is bound to
// #content). Pane B gets full mermaid fidelity by reusing the same vendored
// mermaid.run() against its own un-processed diagram nodes.
async function renderMermaidIn(rootEl) {
  if (!rootEl || !window.mermaid || typeof window.mermaid.run !== 'function') return;
  const nodes = Array.from(rootEl.querySelectorAll('div.mermaid:not([data-processed="true"])'));
  if (!nodes.length) return;
  for (const n of nodes) { if (!n.dataset.mermaidSrc) n.dataset.mermaidSrc = n.innerHTML; }
  try { await window.mermaid.run({ nodes }); }
  catch (e) { console.warn('mermaid.run() (pane B) reported errors:', e); }
}

// Open Pane B on `file` (defaults to the current file) at `anchor`. No-op below
// the gate — the caller is responsible for the fallback (navigate / peek). In
// docs the #right-pane is hidden by the split-open CSS class while open.
function openSplitPane(file, anchor) {
  if (!splitGateActive()) return false;
  const target = file || currentFile;
  if (!target) return false;
  const source = fileContents[target];
  if (source == null) {
    // Pane B only shows already-loaded files (same-file cross-refs and the
    // current section always satisfy this); a not-yet-fetched file is a no-op.
    return false;
  }
  // Capture the return-focus target ONCE per open (the ctrl-clicked ref link
  // or the palette opener). A re-open with the pane already up keeps the
  // original target rather than overwriting it with .cb-body content.
  if (!isSplitOpen()) splitReturnFocus = document.activeElement;
  contentBEl.hidden = false;
  appEl.classList.add('split-open');
  // The Tufte sidenote band lives in #content's right whitespace, which Pane B
  // now occupies (the band has no z-index, Pane B is z-index:50 → buried). Tear
  // it down while split is open; closeSplitPane() rebuilds it. marginNotesGate-
  // Active() also reports false while split is open so a render mid-split skips it.
  teardownSidenoteBand();
  if (splitPaneFile !== target) {
    renderSplitContent(source, target, anchor || null);
    splitPaneFile = target;
  } else if (anchor) {
    // Same file already shown — just re-scroll to the new anchor and re-arm the
    // landing flash (without flashAnchor the repeat re-scroll was silent — review
    // w9d47hl9a #18).
    const t = cbBodyEl.querySelector(`#${CSS.escape(anchor)}`);
    if (t) {
      const top = t.getBoundingClientRect().top - cbBodyEl.getBoundingClientRect().top + cbBodyEl.scrollTop;
      cbBodyEl.scrollTo({ top: Math.max(0, top - 24), behavior: 'smooth' });
      flashAnchor(t);
    }
  }
  return true;
}

// Open Pane B on the section currently at the top of Pane A's viewport. Finds
// the last heading whose top sits at/above the scan line, mirrors the
// scroll-spy threshold, and shows that anchor in the pane.
function openSplitForCurrentSection() {
  if (!splitGateActive() || !currentFile) return false;
  let anchor = null;
  const headings = contentEl.querySelectorAll('h1[id],h2[id],h3[id],h4[id],h5[id],h6[id]');
  const scan = (typeof SCROLL_SYNC_THRESHOLD === 'number' ? SCROLL_SYNC_THRESHOLD : 80) + 4;
  headings.forEach((h) => { if (h.getBoundingClientRect().top <= scan) anchor = h.id; });
  return openSplitPane(currentFile, anchor);
}

function closeSplitPane() {
  if (!isSplitOpen()) return;
  // Restore focus BEFORE hiding the pane: if the active element is inside
  // Pane B (the .cb-close button or a rendered link), hiding contentBEl first
  // would make focus() a no-op and strand the keyboard user at <body>. Mirror
  // closeSettings()'s visibility probe: restore the saved opener only if it's
  // still visible, else fall back to #content (always present in any chrome).
  const visible = (el) => !!el && document.body.contains(el) && el.getClientRects().length > 0;
  const activeInPane = contentBEl && contentBEl.contains(document.activeElement);
  const refocus = visible(splitReturnFocus) ? splitReturnFocus : contentEl;
  if (activeInPane && refocus) { try { refocus.focus(); } catch (e) { /* gone */ } }
  appEl.classList.remove('split-open');
  if (contentBEl) contentBEl.hidden = true;
  if (cbBodyEl) cbBodyEl.innerHTML = '';
  splitPaneFile = null;
  splitReturnFocus = null;
  // The right whitespace is Pane A's again — rebuild the sidenote band (a no-op
  // unless the margin-notes gate is satisfied: immersive + marginNotes + ≥1400px).
  applyMarginNotes();
}

// Pane B nested links: same-file anchors re-scroll the pane; everything else
// (cross-file, external) closes the pane and navigates Pane A so the reference
// pane never becomes a second navigation surface.
if (contentBEl) {
  const cbClose = contentBEl.querySelector('.cb-close');
  if (cbClose) cbClose.addEventListener('click', closeSplitPane);
  cbBodyEl.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href') || '';
    if (href.startsWith('#')) {
      e.preventDefault();
      const id = href.slice(1);
      const t = cbBodyEl.querySelector(`#${CSS.escape(id)}`);
      if (t) {
        const top = t.getBoundingClientRect().top - cbBodyEl.getBoundingClientRect().top + cbBodyEl.scrollTop;
        cbBodyEl.scrollTo({ top: Math.max(0, top - 24), behavior: 'smooth' });
        flashAnchor(t);
      }
      return;
    }
    // Cross-file .md link: route through the SPA loader instead of letting the
    // browser hard-navigate the top frame (which would tear down the whole app —
    // scroll positions, highlight cache, the split pane, in-memory content).
    // Resolve relative to the PANE's file dir (splitPaneFile), not currentFile.
    const mdMatch = href.match(/^([^#]*\.md)(?:#(.*))?$/);
    if (mdMatch) {
      e.preventDefault();
      const [, rawFile, anchor] = mdMatch;
      const file = resolveRelPathFrom(splitPaneFile, rawFile);
      closeSplitPane();          // hand the reference back to Pane A's full surface
      loadFile(file, anchor || undefined);
      return;
    }
    // External link: open in a new tab so it never replaces the app frame.
    if (/^https?:/.test(href)) {
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener');
    }
  });
}

// Esc ordering: cheat-sheet > peek > split > drawer (the topmost surface owns
// the first Escape). This capture-phase listener closes Pane B and uses
// stopImmediatePropagation so it preempts the bubble-phase drawer handler.
// It MUST bail when a higher-priority surface owns the keyboard: the palette and
// settings sheet (already guarded), the keyboard cheat-sheet (its own Esc
// handler is bubble-phase, so without this bail an Esc with both open would
// close the BACKGROUND split and stopImmediatePropagation would block the
// foreground cheat-sheet's Esc, dismissing the wrong surface), AND an open peek
// popover. The peek is a transient popover stacked above the split (z 1050 vs
// 50), so it takes Esc first — matching the drawer Esc handler, which already
// defers to an open peek `(!peekPopover || peekPopover.hidden)`. With this guard
// the capture handler bails while a peek is up, letting the peek's bubble-phase
// Esc close the peek first; a second Esc (peek now gone) then closes the split.
function shortcutCheatsheetOpen() {
  return !!(shortcutSheetEl && !shortcutSheetEl.hidden);
}
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && isSplitOpen()
      && !paletteOpen && !settingsOpen && !shortcutCheatsheetOpen()
      && (!peekPopover || peekPopover.hidden)) {
    closeSplitPane();
    e.preventDefault();
    e.stopImmediatePropagation();
  }
}, true);   // capture phase — runs before the bubble-phase drawer handler

// ---------------------------------------------------------------------------
// Tufte margin sidenotes (T7) — in-content references rendered in the right
// whitespace beside the centered prose, vertically aligned to their anchor and
// de-collided so KaTeX-tall sidenotes never overlap.
//
// Activation gate (all three required): marginNotes ON, html.immersive
// (reader/focus — docs owns the right whitespace via #right-pane), and the
// viewport ≥1400px (the right whitespace is only wide enough below the cap
// there). Off any condition → no band, and the floating peek popover stays the
// resolution path (unchanged). The band is an absolutely-positioned child of
// #content so it scrolls WITH the prose; the layout pass runs O(n) on
// render-settle / resize / typography change only — never per scroll frame.
// ---------------------------------------------------------------------------
// The ≥1400px breakpoint is the same matchMedia the Docs right pane uses
// (mqlWidePane, defined later at module scope). It is referenced inside the
// gate function — which only runs at event time, after init — so the forward
// reference is safe (a top-level alias here would hit the TDZ).
let sidenoteBand = null;

function marginNotesGateActive() {
  return !!settingsStore.get('marginNotes')
    && document.documentElement.classList.contains('immersive')
    && mqlWidePane.matches
    && !mqlNarrow.matches
    // Split view (Pane B) occupies the right whitespace the band needs — gate
    // it off so the band is never built buried under Pane B (T7 collision).
    && !isSplitOpen();
}

// ResizeObserver that re-runs the de-collision pass when any sidenote's own box
// grows or shrinks. KaTeX (and web-font swaps) settle AFTER the band is first
// laid out, so a display-math sidenote that measured short at build time can
// grow taller a frame later and overlap its successor. Observing each .sidenote
// (and the band) catches that late growth and re-de-collides. Debounced via rAF
// so a burst of simultaneous size changes collapses to one layout pass.
let sidenoteResizeObserver = null;
let sidenoteResizeRaf = 0;
function ensureSidenoteResizeObserver() {
  if (sidenoteResizeObserver || typeof ResizeObserver === 'undefined') return;
  sidenoteResizeObserver = new ResizeObserver(() => {
    if (sidenoteResizeRaf) return;
    sidenoteResizeRaf = requestAnimationFrame(() => {
      sidenoteResizeRaf = 0;
      if (sidenoteBand) layoutSidenotes();
    });
  });
}

// Remove the band entirely (gate off, re-render about to wipe #content, etc.).
function teardownSidenoteBand() {
  if (sidenoteResizeObserver) sidenoteResizeObserver.disconnect();
  if (sidenoteResizeRaf) { cancelAnimationFrame(sidenoteResizeRaf); sidenoteResizeRaf = 0; }
  if (sidenoteBand && sidenoteBand.parentNode) sidenoteBand.parentNode.removeChild(sidenoteBand);
  sidenoteBand = null;
}

// In-content references in document order, each described by the in-text marker
// to mirror and the peek-content recipe to fill its body. Footnote refs map to
// their definition text; numbered cites / eq / sec refs reuse the peek builders.
function collectSidenoteRefs() {
  const out = [];
  // Footnote refs: <sup class="footnote-ref"><a href="#fnN" id="fnrefN">[k]</a>.
  // Skip the back-references inside the footnote list itself (.footnote-backref).
  contentEl.querySelectorAll('sup.footnote-ref a[href^="#fn"], .footnote-ref a[href^="#fn"]').forEach((a) => {
    out.push({ anchor: a, kind: 'fn', mark: a.textContent.trim(), targetId: a.getAttribute('href').slice(1) });
  });
  // Numbered citations + eq/sec cross-refs: same-file #ref-/#eq-/#sec- links,
  // excluding the reference-list entry anchors themselves (which carry no href).
  contentEl.querySelectorAll('a[href^="#eq-"], a[href^="#ref-"], a[href^="#sec-"]').forEach((a) => {
    const parsed = window.PeekTarget.parsePeekHref(a.getAttribute('href'));
    if (!parsed.kind || !parsed.sameFile) return;
    // A reference-list back-link (inside .footnotes / a ref entry) is not an
    // in-text invocation — only count anchors that sit in the prose body.
    if (a.closest('.footnotes')) return;
    out.push({ anchor: a, kind: parsed.kind, mark: a.textContent.trim(), peekId: `${parsed.kind}-${parsed.id}` });
  });
  // Document order: footnote refs and cross-refs were collected in two passes;
  // sort by DOM position so the de-collision pass walks top-to-bottom.
  out.sort((p, q) => {
    if (p.anchor === q.anchor) return 0;
    return (p.anchor.compareDocumentPosition(q.anchor) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
  });
  return out;
}

// Body content for one sidenote. Reuses the peek builders for eq/ref/sec; for a
// footnote, clones the matching definition <li> text (minus its back-ref arrow).
function buildSidenoteBody(ref) {
  if (ref.kind === 'fn') {
    const def = document.getElementById(ref.targetId);
    if (!def) return null;
    const clone = def.cloneNode(true);
    clone.querySelectorAll('.footnote-backref').forEach((b) => b.remove());
    const wrap = document.createElement('div');
    wrap.className = 'peek-ref';
    wrap.innerHTML = clone.innerHTML;
    return wrap.innerHTML.trim() ? wrap : null;
  }
  return buildPeekContent(ref.kind, ref.peekId);
}

// Build (or rebuild) the band + its sidenotes, then run the de-collision pass.
// Idempotent: tears the old band down first so a re-render never doubles it.
function buildSidenoteBand() {
  teardownSidenoteBand();
  if (!marginNotesGateActive()) return;
  const refs = collectSidenoteRefs();
  if (!refs.length) return;
  const band = document.createElement('div');
  band.id = 'sidenote-band';
  band.setAttribute('aria-hidden', 'true');   // a parallel affordance; the in-text ref + peek stay the a11y path
  for (const ref of refs) {
    const body = buildSidenoteBody(ref);
    if (!body) continue;                       // unresolvable target → no sidenote (peek still works)
    const note = document.createElement('div');
    note.className = 'sidenote';
    note.dataset.refMark = ref.mark || '';
    const mark = document.createElement('span');
    mark.className = 'sidenote-mark';
    mark.textContent = ref.mark || '';
    const bodyWrap = document.createElement('span');
    bodyWrap.className = 'sidenote-body';
    bodyWrap.appendChild(body);
    note.appendChild(mark);
    note.appendChild(bodyWrap);
    note._sidenoteAnchor = ref.anchor;         // stashed for the layout pass
    band.appendChild(note);
  }
  if (!band.children.length) return;           // every target was unresolvable
  contentEl.appendChild(band);                 // child of #content → scrolls with the prose
  sidenoteBand = band;
  layoutSidenotes();
  // Re-de-collide once KaTeX/web fonts settle (each sidenote's measured height
  // can grow after the synchronous build): observe every note for late growth,
  // and re-run once when document.fonts.ready resolves.
  ensureSidenoteResizeObserver();
  if (sidenoteResizeObserver) {
    sidenoteResizeObserver.observe(band);
    for (const note of band.children) sidenoteResizeObserver.observe(note);
  }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => { if (sidenoteBand === band) layoutSidenotes(); });
  }
}

// O(n) top-to-bottom de-collision pass. Desired top = the invoking anchor's
// offset from #content's top (so the sidenote aligns with the line that cites
// it); a single sweep enforces top = max(desiredTop, prevBottom + gap) so a
// tall KaTeX sidenote pushes its successors down instead of overlapping them.
// Positions are #content-relative (the band's offset parent), so they hold as
// the page scrolls without any per-scroll work.
const SIDENOTE_GAP = 10;
function layoutSidenotes() {
  if (!sidenoteBand) return;
  const contentTop = contentEl.getBoundingClientRect().top;
  let prevBottom = -Infinity;
  for (const note of sidenoteBand.children) {
    const anchor = note._sidenoteAnchor;
    if (!anchor || !anchor.isConnected) { note.style.display = 'none'; continue; }
    note.style.display = '';
    // Anchor top relative to #content (viewport delta is scroll-invariant since
    // both rects share the same scroll position at measurement time).
    const desiredTop = anchor.getBoundingClientRect().top - contentTop;
    const top = Math.max(desiredTop, prevBottom + SIDENOTE_GAP);
    note.style.top = top + 'px';
    prevBottom = top + note.offsetHeight;
  }
}

// Subscriber + gate-change entry point: rebuild from scratch (cheap — one DOM
// build + one O(n) pass). Called on the marginNotes toggle, chrome change, and
// the ≥1400px breakpoint cross.
function applyMarginNotes() {
  buildSidenoteBand();
}

// Bumped on every renderToContent call so stale scroll-to-anchor callbacks
// from a prior render cannot fire after a newer render has replaced the DOM.
// Without this guard, clicking a cross-file link whose anchor id also exists
// in the *previous* file (e.g. both files have #eq-14) lets the old render's
// delayed scrollToAnchor kick in during a subsequent back-navigation and
// yank the restored scroll position onto the wrong element.
let renderSeq = 0;

function renderToContent(markdown, anchor) {
  hideToolbar();
  hideNotePopover();
  hidePeek();
  contentEl.innerHTML = render(markdown);
  setupLazyDisplayMath();
  fixRelativePaths();
  enhanceFigures();
  installFootnoteRefHandlers();
  installPeekHandlers();
  renderMermaidDiagrams();
  updateDocumentTitle();
  // When the Docs right pane is on screen both panels are always-on, so both
  // rebuild every render; otherwise (reader/focus, or Docs below the wide
  // breakpoint where the panes live in the sidebar) only the active tab
  // rebuilds (lazy).
  if (isRightPaneActive()) {
    buildOutline();
    buildHighlights();
  } else {
    if (activeTab === 'outline') buildOutline();
    if (activeTab === 'highlights') buildHighlights();
  }
  const mySeq = ++renderSeq;
  // Recompute heading tops after first paint and after late KaTeX/Mermaid
  // reflow so progress + outline-sync stay correct (runs every render,
  // independent of `anchor` and of which sidebar tab is active).
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (mySeq !== renderSeq) return;
      scrollSyncRefreshLayout();
      // Margin sidenotes (T7): the band is a child of #content, wiped by the
      // innerHTML assignment above, so it is rebuilt from scratch here. Built at
      // the first settle (so anchor tops are post-paint) and again after the
      // 300ms KaTeX-reflow window (so tall display-math sidenotes de-collide
      // against their final rendered height).
      applyMarginNotes();
      setTimeout(() => {
        if (mySeq === renderSeq) { scrollSyncRefreshLayout(); applyMarginNotes(); }
      }, 300);
    });
  });
  if (anchor) {
    // Double-RAF waits for one full paint cycle; the follow-up setTimeout
    // catches late reflow (e.g. KaTeX block layout in narrow viewports).
    requestAnimationFrame(() => {
      if (mySeq !== renderSeq) return;
      requestAnimationFrame(() => {
        if (mySeq !== renderSeq) return;
        // Instant jump on file load: a smooth scroll would sweep the
        // IntersectionObserver past every lazy math placeholder en route,
        // rendering the whole document and defeating the lazy path
        // (bug 2026-06-10-01). In-page navigation keeps smooth behavior.
        scrollToAnchor(anchor, { instant: true });
        setTimeout(() => {
          if (mySeq !== renderSeq) return;
          scrollToAnchor(anchor, { instant: true });
        }, 300);
      });
    });
  }
}

// ---------------------------------------------------------------------------
// Live-reload diff highlights
// ---------------------------------------------------------------------------
function snapshotBlocks() {
  return Array.from(contentEl.children).map(el => el.innerHTML);
}

function highlightChangedBlocks(oldSnapshot) {
  if (document.documentElement.classList.contains('no-update-fx')) return 0;
  const oldSet = new Set(oldSnapshot);
  const children = contentEl.children;
  let count = 0;
  for (let i = 0; i < children.length; i++) {
    if (!oldSet.has(children[i].innerHTML)) {
      children[i].classList.add('block-changed');
      count++;
    }
  }
  contentEl.querySelectorAll('.block-changed').forEach(el => {
    el.addEventListener('animationend', () => el.classList.remove('block-changed'), { once: true });
  });
  return count;
}

// Toast notification
const toastEl = (() => {
  const el = document.createElement('div');
  el.id = 'reload-toast';
  document.body.appendChild(el);
  return el;
})();
let toastTimer = null;

function showToast(msg, onClick) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  // Remove any prior click handler, then attach new one if provided.
  if (toastEl._clickHandler) { toastEl.removeEventListener('click', toastEl._clickHandler); toastEl._clickHandler = null; }
  if (onClick) {
    const handler = () => { toastEl.removeEventListener('click', handler); toastEl._clickHandler = null; onClick(); };
    toastEl._clickHandler = handler;
    toastEl.addEventListener('click', handler);
  }
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.remove('show');
    if (toastEl._clickHandler) {
      toastEl.removeEventListener('click', toastEl._clickHandler);
      toastEl._clickHandler = null;
    }
  }, 2500);
}

// ---------------------------------------------------------------------------
// Version-check (cloud mode only) — nudge once per new publish version.
// ---------------------------------------------------------------------------
function checkVersion(liveVersion) {
  if (!liveVersion) return;
  try {
    const lastSeen = localStorage.getItem('viewer:lastVersion');
    if (window.shouldNudgeReload && window.shouldNudgeReload(liveVersion, lastSeen)) {
      showToast('New version available — tap to reload', function () { location.reload(); });
    }
    const next = (window.nextLastSeen ? window.nextLastSeen(liveVersion, lastSeen) : liveVersion) || '';
    if (next) localStorage.setItem('viewer:lastVersion', next);
  } catch {}
}

let _versionCheckInFlight = false;
function scheduleVersionCheck() {
  if (backend.kind !== 'cloud') return;
  if (_versionCheckInFlight) return;
  _versionCheckInFlight = true;
  backend.listFiles().then(function (data) {
    _versionCheckInFlight = false;
    checkVersion(data.version || (window.VIEWER_CONFIG && window.VIEWER_CONFIG.version) || null);
  }).catch(function () { _versionCheckInFlight = false; });
}

function revisionFromResponse(res, fallback = 'X-Document-Revision') {
  return res.headers.get('ETag') || res.headers.get(fallback) || null;
}

function markManifestDirty(file) {
  if (file) {
    // If we already have local source for this file, rebuild the manifest
    // immediately from that source rather than deleting it. This prevents a
    // brief window where the manifest is absent (causing findInlineEntryForMark
    // to return null) when a WS change message arrives for a self-originated
    // write whose applyLocalSourceUpdate already set an authoritative manifest.
    if (!refreshManifestFromLocalState(file)) {
      manifestByFile.delete(file);
      manifestDirtyFiles.add(file);
    }
  } else {
    // Global invalidation — force the next loadManifest() to full-refetch.
    manifestNeedsFullRefresh = true;
    manifestDirtyFiles.clear();
  }
}

function minSidecarLine(segment) {
  const candidates = [segment?.lineStart, segment?.blockLine, segment?.tableLine];
  for (const value of candidates) {
    const n = Number(value);
    if (Number.isFinite(n)) return Math.max(0, n);
  }
  return 0;
}

function maxSidecarLine(segment, fallback) {
  const n = Number(segment?.lineEnd);
  if (Number.isFinite(n)) return Math.max(fallback, n);
  return fallback;
}

function sidecarManifestEntriesFromDoc(file, doc) {
  const normalizeWhitespace = HighlightShared.normalizeWhitespace
    ? HighlightShared.normalizeWhitespace
    : (value) => String(value || '').replace(/[ \t\r\n]+/g, ' ').trim();
  const highlights = Array.isArray(doc?.highlights) ? doc.highlights : [];
  return highlights.filter((h) => !h.deleted).map((hit) => {
    let lineStart = Number.POSITIVE_INFINITY;
    let lineEnd = 0;
    const segments = Array.isArray(hit.segments) ? hit.segments : [];
    for (const segment of segments) {
      const segStart = minSidecarLine(segment);
      const segEnd = maxSidecarLine(segment, segStart);
      lineStart = Math.min(lineStart, segStart);
      lineEnd = Math.max(lineEnd, segEnd);
    }
    if (!Number.isFinite(lineStart)) lineStart = 0;
    return {
      id: hit.id,
      file,
      backend: 'sidecar',
      color: hit.color || 'yellow',
      excerpt: normalizeWhitespace(hit.excerpt || ''),
      lineStart,
      lineEnd,
      revision: hit.revision || doc.documentRevision || fileRevisions[file] || null,
    };
  });
}

function refreshManifestFromLocalState(file) {
  if (!file) return false;
  const source = fileContents[file];
  const inline = (typeof source === 'string' && HighlightShared.extractInlineHighlights)
    ? HighlightShared.extractInlineHighlights(source, file).map((entry) => ({
      id: entry.id,
      file,
      backend: 'inline',
      color: entry.color,
      excerpt: entry.excerpt,
      lineStart: entry.lineStart,
      lineEnd: entry.lineEnd,
      sourceStart: entry.sourceStart,
      sourceEnd: entry.sourceEnd,
      innerStart: entry.innerStart,
      innerEnd: entry.innerEnd,
      noteId: entry.noteId,
      noteRefStart: entry.noteRefStart,
      noteRefEnd: entry.noteRefEnd,
      noteDefStart: entry.noteDefStart,
      noteDefEnd: entry.noteDefEnd,
      noteBody: entry.noteBody,
      noteHasMath: entry.noteHasMath,
      revision: fileRevisions[file] || null,
    }))
    : [];
  const sidecar = sidecarManifestEntriesFromDoc(file, annotationDocs[file]);
  if (!inline.length && !sidecar.length && typeof source !== 'string') return false;
  manifestByFile.set(file, [...inline, ...sidecar]);
  manifestDirtyFiles.delete(file);
  return true;
}

// ── DOM-position-ratio manifest lookup ───────────────────────────────────────
// Locates the manifest entry for a rendered <mark> using source-position
// arithmetic rather than textContent comparison.  Robust against KaTeX
// inflation, markdown formatting wrappers, and multi-line whitespace.
//
// Algorithm:
//   1. Walk up to the nearest [data-source-line] block element.
//   2. Compute the block's source byte range [bso, beo) from the line table.
//   3. Filter the manifest to inline entries whose sourceStart falls inside
//      that range.
//   4. If only one entry qualifies, return it immediately.
//   5. For multiple entries, compute the mark's DOM-position-ratio within the
//      block and pick the entry whose source-position-ratio is closest.
//
// All helpers (nextBlockSibling, lineStartOffset, textBeforeNode) are already
// defined in this file and used by clearMarkEl.
function findInlineEntryAtMark(markEl) {
  if (!markEl || !currentFile) return null;
  const blockEl = markEl.closest('[data-source-line]');
  if (!blockEl) return null;
  const blockSrcLine = parseInt(blockEl.dataset.sourceLine, 10);
  if (!Number.isFinite(blockSrcLine)) return null;
  const source = fileContents[currentFile];
  if (typeof source !== 'string') return null;

  // Block source range [bso, beo).
  const nextEl  = nextBlockSibling(blockEl);
  const lines   = source.split('\n');
  const nextLine = nextEl ? parseInt(nextEl.dataset.sourceLine, 10) : lines.length;
  const bso = lineStartOffset(source, blockSrcLine);
  const beo = nextEl ? lineStartOffset(source, nextLine) : source.length;

  // Manifest entries that fall inside this block.
  const entries = (manifestByFile.get(currentFile) || [])
    .filter(e => e.backend === 'inline'
      && typeof e.sourceStart === 'number'
      && e.sourceStart >= bso && e.sourceStart < beo);
  if (entries.length === 0) return null;
  if (entries.length === 1) return entries[0];

  // Disambiguate by DOM-position-ratio ↔ source-position-ratio.
  const blockText = blockEl.textContent || '';
  if (!blockText.length) return entries[0];
  const domPre   = textBeforeNode(markEl, blockEl);
  const domRatio = domPre.length / blockText.length;
  const blockSrcLen = beo - bso;
  return entries.reduce((best, e) => {
    const eRatio    = (e.sourceStart - bso) / blockSrcLen;
    const bestRatio = (best.sourceStart - bso) / blockSrcLen;
    return Math.abs(eRatio - domRatio) < Math.abs(bestRatio - domRatio) ? e : best;
  });
}

// Locate the manifest entry for a rendered <mark> by delegating to the
// DOM-position-ratio helper above.  Replaces the old naive textContent
// comparison which failed for marks whose source contains KaTeX or formatting.
function findInlineEntryForMark(markEl) {
  return findInlineEntryAtMark(markEl);
}

// Undo state — bounded revision-aware stack
const UNDO_LIMIT = 20;
const undoStack = []; // [{ file, source, revision }]

function pushUndo(action) {
  undoStack.push(action);
  if (undoStack.length > UNDO_LIMIT) undoStack.shift();
}

const undoToastEl = (() => {
  const el  = document.createElement('div');
  el.id     = 'undo-toast';
  const msg = document.createElement('span');
  el.appendChild(msg);
  const btn = document.createElement('button');
  btn.textContent = 'Undo';
  btn.addEventListener('click', () => undoLastAction());
  el.appendChild(btn);
  document.body.appendChild(el);
  return el;
})();
let undoTimer = null;

function showUndoToast(message) {
  undoToastEl.firstChild.textContent = message;
  undoToastEl.classList.add('show');
  clearTimeout(undoTimer);
  undoTimer = setTimeout(() => undoToastEl.classList.remove('show'), 5000);
}

function hideUndoToast() {
  undoToastEl.classList.remove('show');
  clearTimeout(undoTimer);
  undoTimer = null;
}

async function undoLastAction() {
  const action = undoStack.pop();
  if (!action) return;
  const { file, source, revision, backend } = action;
  hideUndoToast();
  if (backend === 'sidecar') {
    const loaded = await ensureAnnotationsLoaded(file, true);
    if (!loaded) {
      showToast('Undo failed: could not read annotations');
      return;
    }
    const nextDoc = {
      ...loaded.doc,
      file,
      highlights: (action.previousHighlights || []).map(h => ({
        ...h,
        segments: Array.isArray(h.segments) ? [...h.segments] : [],
      })),
    };
    const wrote = await putAnnotations(file, nextDoc, revision || loaded.revision, fileRevisions[file] || null);
    if (!wrote.ok) {
      if (wrote.conflict) {
        showToast('Undo conflict: annotations changed, reload and retry');
        await ensureAnnotationsLoaded(file, true);
        if (file === currentFile) applySidecarHighlights();
      } else {
        showToast(`Undo failed: ${wrote.status}`);
      }
      return;
    }
    annotationDocs[file] = nextDoc;
    if (wrote.revision != null) annotationRevisions[file] = wrote.revision;
    if (!refreshManifestFromLocalState(file)) markManifestDirty(file);
    if (file === currentFile) applySidecarHighlights();
    if (activeTab === 'highlights') buildHighlights();
    return;
  }
  const res = await putMarkdownSource(file, source, revision);
  if (!res.ok) {
    if (res.conflict) {
      showToast('Undo conflict: document changed, reload and retry');
      await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
    } else {
      showToast(`Undo failed: ${res.status}`);
    }
    return;
  }
  applyLocalSourceUpdate(file, source, res.revision);
}

// Resolve relative image/link paths based on current file's directory
// Set the browser tab/title from the current document's H1 (if any),
// falling back to the filename. Called after every renderToContent() so
// in-place edits and live-reload also refresh the title.
function updateDocumentTitle() {
  const h1 = contentEl.querySelector('h1');
  const base = (h1 && h1.textContent.trim()) || (currentFile || '');
  document.title = base ? `${base} — Markdown Viewer` : 'Markdown Viewer';
  const crumb = document.getElementById('reader-crumb');
  if (crumb) crumb.textContent = currentFile || '';
}

function fixRelativePaths() {
  const dir = currentFileDir();
  if (!dir) return;
  // Fix image src
  contentEl.querySelectorAll('img[src]').forEach(img => {
    const src = img.getAttribute('src');
    if (src && !src.startsWith('/') && !src.startsWith('http')) {
      img.setAttribute('src', `/${dir}/${src}`);
    }
  });
  // Fix relative asset links (e.g. a link to figures/*.svg or *.pdf) so they
  // resolve against the doc's directory like images do — not the SPA root, where
  // they 404. `.md` links are left for the click handler's in-app navigation;
  // #anchors, already-absolute, and scheme (http:/mailto:/…) links are untouched.
  contentEl.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (!href || href.startsWith('/') || href.startsWith('#')) return;
    if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return;   // has a scheme
    if (/\.md(#.*)?$/i.test(href)) return;           // .md → in-app navigation
    a.setAttribute('href', `/${dir}/${href}`);
  });
}

function currentFileDir() {
  if (!currentFile) return '';
  const idx = currentFile.lastIndexOf('/');
  return idx >= 0 ? currentFile.slice(0, idx) : '';
}

// ── Spec-driven figures (progressive enhancement) ────────────────────────────
// A figure embedded as `![alt](fig.png "ID")` where ID is a known figure is
// upgraded in the viewer to a live, reflowing, style-switchable render
// (viewer/lib/figure-pipeline.js). GitHub / no-JS keep the static PNG. The
// figure DATA is a sibling `spec.json` (same dir as the PNG), fetched once.
// To add a figure: register its id below + ship `<dir>/spec.json` + a renderer
// in figure-pipeline.js — no other viewer change.
const FIGURE_REGISTRY = { 'pipeline-figure': true };
const figureSpecCache = {}; // id -> Promise<spec|null>

function currentFigureStyle() {
  return settingsStore.get('figureStyle') || 'colour-academic';
}

function figureSpec(id, specUrl) {
  if (!figureSpecCache[id]) {
    figureSpecCache[id] = fetch(specUrl)
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
  }
  return figureSpecCache[id];
}

// Post-render: wrap each not-yet-wrapped marked image, then render the current
// style. Idempotent — re-running skips already-wrapped figures.
function enhanceFigures() {
  if (!window.FigurePipeline) return;
  window.FigurePipeline.ensureStyles();
  contentEl.querySelectorAll('img[title]').forEach((img) => {
    const id = img.getAttribute('title');
    if (!FIGURE_REGISTRY[id]) return;
    if (img.closest('.fp-wrap')) return; // already enhanced
    const src = img.getAttribute('src') || '';
    const wrap = document.createElement('div');
    wrap.className = 'fp-wrap';
    wrap.dataset.figureId = id;
    wrap.dataset.specUrl = src.replace(/[^/]+$/, 'spec.json');
    img.replaceWith(wrap);
    img.classList.add('fp-fallback');
    wrap.appendChild(img);
    const renderDiv = document.createElement('div');
    renderDiv.className = 'fp-render';
    wrap.appendChild(renderDiv);
    wrap.appendChild(buildFigureChip());
    renderFigure(wrap);
  });
}

// Re-render every enhanced figure in place — called by the store subscriber on a
// figureStyle change (no full document re-render; mirrors applyMarginNotes()).
function applyFigureStyle() {
  contentEl.querySelectorAll('.fp-wrap').forEach(renderFigure);
}

function renderFigure(wrap) {
  const id = wrap.dataset.figureId;
  const style = currentFigureStyle();
  const renderDiv = wrap.querySelector('.fp-render');
  const img = wrap.querySelector('img.fp-fallback');
  updateFigureChip(wrap, style);
  // Toggle via inline display (beats the higher-specificity `#content img` rule
  // in style.css, which would otherwise keep the static PNG visible).
  if (style === 'image') {
    if (renderDiv) { renderDiv.innerHTML = ''; renderDiv.style.display = 'none'; }
    if (img) img.style.display = '';
    return;
  }
  if (img) img.style.display = 'none';
  if (renderDiv) renderDiv.style.display = '';
  figureSpec(id, wrap.dataset.specUrl).then((spec) => {
    if (!renderDiv) return;
    if (currentFigureStyle() !== style) return; // a newer change superseded this
    if (!spec) { renderDiv.style.display = 'none'; if (img) img.style.display = ''; return; }
    renderDiv.innerHTML = window.FigurePipeline.render(spec, style);
  });
}

function buildFigureChip() {
  const chip = document.createElement('div');
  chip.className = 'fp-chip';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'fp-chip-btn';
  btn.setAttribute('aria-haspopup', 'true');
  btn.title = 'Figure style';
  btn.textContent = '▦ style ▾';
  const menu = document.createElement('div');
  menu.className = 'fp-chip-menu';
  menu.hidden = true;
  (window.FigurePipeline ? window.FigurePipeline.STYLES : []).forEach((s) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.dataset.styleId = s.id;
    item.textContent = s.label;
    item.addEventListener('click', () => {
      settingsStore.set('figureStyle', s.id);
      menu.hidden = true;
      chip.classList.remove('open');
    });
    menu.appendChild(item);
  });
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = menu.hidden;
    menu.hidden = !open;
    chip.classList.toggle('open', open);
    if (open) {
      const close = (ev) => {
        if (!chip.contains(ev.target)) {
          menu.hidden = true; chip.classList.remove('open');
          document.removeEventListener('click', close);
        }
      };
      setTimeout(() => document.addEventListener('click', close), 0);
    }
  });
  chip.appendChild(btn);
  chip.appendChild(menu);
  return chip;
}

function updateFigureChip(wrap, style) {
  wrap.querySelectorAll('.fp-chip-menu button[data-style-id]').forEach((b) => {
    b.setAttribute('aria-current', b.dataset.styleId === style ? 'true' : 'false');
  });
}

// Resolve a relative .md path against the current file's directory
function resolveRelPath(relPath) {
  return resolveRelPathFrom(currentFile, relPath);
}

// Resolve `relPath` against the directory of `baseFile` (not necessarily the
// active file). Pane B uses this so a .md link inside the reference pane
// resolves relative to the PANE's file, which may differ from currentFile.
function resolveRelPathFrom(baseFile, relPath) {
  const slash = baseFile ? baseFile.lastIndexOf('/') : -1;
  const dir = slash >= 0 ? baseFile.slice(0, slash) : '';
  const combined = dir ? `${dir}/${relPath}` : relPath;
  // Normalize: resolve ".." and "."
  const parts = combined.split('/');
  const resolved = [];
  for (const p of parts) {
    if (p === '..') resolved.pop();
    else if (p !== '.') resolved.push(p);
  }
  return resolved.join('/');
}

// ---------------------------------------------------------------------------
// File loading
// ---------------------------------------------------------------------------
let defaultFile = null;           // set by server in single-file mode

// Single transport seam — selects local-server (dev) or cloud/native (published bundle)
// based on window.VIEWER_CONFIG.backend injected by the build/host environment.
const backend = selectBackend(typeof window !== 'undefined' ? window : {});

// Register the service worker and hand it the bearer token (cloud mode only).
// The SW persists the token to IndexedDB and injects it as Authorization: Bearer
// on forwarded fetches (forward-compat for native shell + offline auth).
// The HttpOnly vt= cookie still rides along automatically on same-origin requests.
if (window.VIEWER_CONFIG && window.VIEWER_CONFIG.backend === 'cloud' && 'serviceWorker' in navigator) {
  navigator.serviceWorker.register(window.__PWA_SW_URL || 'sw.js').then(function () {
    var token = localStorage.getItem('viewer:token');
    var post = function () { if (navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage({ type: 'token', token: token }); };
    post();
    navigator.serviceWorker.addEventListener('controllerchange', post);
  }).catch(function () {});
}

// Flush the offline write-queue when the browser regains connectivity.
window.addEventListener('online', function () {
  if (backend.flushQueue) backend.flushQueue();
});

async function fetchFileList() {
  const data = await backend.listFiles();
  fileList = data.files;
  // Schema-2 payloads carry the content roots; a v1 payload (old SW-cached
  // files.json) lacks them → degrade to a single ungrouped root.
  viewerRoots = Array.isArray(data.roots) && data.roots.length ? data.roots : [{ id: '', label: '' }];
  defaultFile = data.defaultFile || null;
  for (const file of [...manifestByFile.keys()]) {
    if (!fileList.includes(file)) manifestByFile.delete(file);
  }
  markManifestDirty();
  return { files: fileList, version: data.version || null };
}

// Resolve a possibly-stale file id against the current fileList. An exact match
// wins. Otherwise (multi-root: an old flat ?file= bookmark/deep-link whose id is
// now namespaced) try a unique namespace-suffix match, then a unique basename
// match. Returns the resolved id, or null when zero/ambiguous (caller falls
// through to default/first). In single-root mode the exact match always hits,
// so the fallback is inert.
function resolveFileId(id) {
  if (!id) return null;
  if (fileList.includes(id)) return id;
  const suffix = fileList.filter((f) => f.endsWith('/' + id));
  if (suffix.length === 1) return suffix[0];
  if (suffix.length === 0) {
    const base = id.split('/').pop();
    const byBase = fileList.filter((f) => f.split('/').pop() === base);
    if (byBase.length === 1) return byBase[0];
  }
  return null;
}

async function fetchFile(filename) {
  const { text, revision } = await backend.getMarkdown(filename);
  fileContents[filename] = text;
  fileRevisions[filename] = revision;
  return { text, revision };
}

async function putMarkdownSource(filename, source, expectedRevision) {
  return backend.putMarkdown(filename, source, expectedRevision);
}

async function ensureAnnotationsLoaded(file, force = false) {
  if (!force && annotationDocs[file] && annotationRevisions[file]) {
    return { doc: annotationDocs[file], revision: annotationRevisions[file] };
  }
  const result = await backend.getAnnotations(file);
  if (!result) return null;
  annotationDocs[file] = result.doc;
  annotationRevisions[file] = result.revision;
  return result;
}

async function putAnnotations(file, doc, expectedRevision, documentRevision) {
  return backend.putAnnotations(file, doc, expectedRevision, documentRevision);
}

async function loadFile(filename, anchor, pushHistory = true) {
  if (!filename) return;
  undoStack.length = 0;
  hideUndoToast();
  const requestId = ++loadRequestSeq;
  activeLoadRequest = requestId;
  try {
    const fetched = await fetchFile(filename);
    if (requestId !== activeLoadRequest) return;   // stale — drop

    // Snapshot outgoing scroll position into the current history entry
    // BEFORE innerHTML replacement. Replacing contentEl.innerHTML clamps
    // window.scrollY to the new document's height, so reading scrollY
    // after the render would corrupt the outgoing entry's saved position.
    // Only snapshot on push navigations (not popstate or 'replace').
    if (pushHistory === true && currentFile && currentFile !== filename) {
      const prev = history.state || {};
      history.replaceState(
        { ...prev, file: prev.file || currentFile, scrollY: window.scrollY },
        ''
      );
    }

    currentFile = filename;
    renderToContent(fetched.text, anchor);
    // Populate manifest from local source so toolbar note-button decisions
    // don't depend on the highlights tab having been opened first.
    refreshManifestFromLocalState(filename);
    await ensureAnnotationsLoaded(filename);
    applySidecarHighlights();
    updateSidebarActive();
    if (pushHistory === 'replace') {
      // Initial load — seed the current entry without creating an extra one
      const params = new URLSearchParams();
      if (filename) params.set('file', filename);
      const hash = anchor ? `#${anchor}` : '';
      history.replaceState({ file: filename, anchor, scrollY: window.scrollY }, '', `?${params}${hash}`);
    } else if (pushHistory) {
      // skipSnapshot=true: loadFile already stamped the outgoing scrollY
      // above; letting updateURL re-stamp would overwrite it with the
      // post-render (clamped) window.scrollY.
      updateURL(filename, anchor, true);
    }
  } catch (err) {
    if (requestId !== activeLoadRequest) return;
    contentEl.innerHTML = `<p style="color:red">Error loading ${filename}: ${err.message}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------
function buildSidebar() {
  fileListEl.innerHTML = '';
  if (!isMultiRootMode()) {
    // Single-root: per-folder groups keyed on the first path segment (unchanged).
    renderFolderGroups(fileList, fileListEl, '');
    return;
  }
  // Multi-root: an outer collapsible group per root (its label), each holding
  // that root's per-folder groups (rendered relative to the root prefix).
  for (const root of viewerRoots) {
    const pfx = `${root.id}/`;
    const rootFiles = fileList.filter((f) => f.startsWith(pfx));
    if (!rootFiles.length) continue;
    const group = document.createElement('div');
    group.className = 'dir-group root-group';
    group.dataset.root = root.id;
    const header = document.createElement('div');
    header.className = 'dir-header root-header';
    const arrow = document.createElement('span');
    arrow.className = 'dir-arrow';
    arrow.innerHTML = '&#9654;';
    header.appendChild(arrow);
    header.appendChild(document.createTextNode(` ${root.label || root.id}`));
    header.addEventListener('click', () => group.classList.toggle('open'));
    group.appendChild(header);
    const children = document.createElement('div');
    children.className = 'dir-children';
    renderFolderGroups(rootFiles.map((f) => f.slice(pfx.length)), children, pfx);
    group.appendChild(children);
    fileListEl.appendChild(group);
  }
}

// Render per-folder groups for `files` (paths RELATIVE to `prefix`) into
// `container`; each entry's data-file is the full namespaced id (`prefix + rel`).
function renderFolderGroups(files, container, prefix) {
  const dirs = {};       // first-segment dir → [rel paths]
  const topLevel = [];   // rel files with no further dir
  for (const f of files) {
    const slash = f.indexOf('/');
    if (slash >= 0) { const dir = f.slice(0, slash); (dirs[dir] = dirs[dir] || []).push(f); }
    else topLevel.push(f);
  }
  for (const dir of Object.keys(dirs).sort()) {
    const group = document.createElement('div');
    group.className = 'dir-group';
    group.dataset.dir = prefix + dir;
    const header = document.createElement('div');
    header.className = 'dir-header';
    header.innerHTML = `<span class="dir-arrow">&#9654;</span> ${dir}/`;
    header.addEventListener('click', () => group.classList.toggle('open'));
    group.appendChild(header);
    const ch = document.createElement('div');
    ch.className = 'dir-children';
    for (const f of dirs[dir]) ch.appendChild(makeFileEntry(prefix + f));
    group.appendChild(ch);
    container.appendChild(group);
  }
  for (const f of topLevel) container.appendChild(makeFileEntry(prefix + f));
}

function makeFileEntry(f) {
  const div = document.createElement('div');
  div.className = 'file-entry';
  // Show only the filename part (without directory and .md)
  const name = f.includes('/') ? f.slice(f.lastIndexOf('/') + 1) : f;
  div.textContent = name.replace(/\.md$/, '');
  div.dataset.file = f;
  div.addEventListener('click', () => {
    loadFile(f);
    // Opening a file from the drawer dismisses it so the reader sees content.
    maybeCloseDrawer();
  });
  return div;
}

function updateSidebarActive() {
  // Highlight active file
  fileListEl.querySelectorAll('.file-entry').forEach(el => {
    el.classList.toggle('active', el.dataset.file === currentFile);
  });
  // Auto-expand the parent group(s) of the active file.
  if (currentFile && currentFile.includes('/')) {
    if (isMultiRootMode()) {
      const parts = currentFile.split('/');
      const rootGroup = fileListEl.querySelector(`.root-group[data-root="${parts[0]}"]`);
      if (rootGroup) rootGroup.classList.add('open');
      // The folder subgroup's data-dir is root/<first-rel-segment>.
      if (parts.length >= 3) {
        const folderGroup = fileListEl.querySelector(`.dir-group[data-dir="${parts[0]}/${parts[1]}"]`);
        if (folderGroup) folderGroup.classList.add('open');
      }
    } else {
      const dir = currentFile.slice(0, currentFile.indexOf('/'));
      const group = fileListEl.querySelector(`.dir-group[data-dir="${dir}"]`);
      if (group) group.classList.add('open');
    }
  }
}

function flashSidebarEntry(filename) {
  fileListEl.querySelectorAll('.file-entry').forEach(el => {
    if (el.dataset.file === filename) {
      el.classList.remove('changed');
      void el.offsetWidth;
      el.classList.add('changed');
    }
  });
}

// ── Off-canvas drawer (narrow viewport) ─────────────────────────────────────
// At ≤768px the sidebar is a slide-over drawer driven by `#app.drawer-open`
// (CSS owns the transform/backdrop). At ≥769px the sidebar is docked and the
// toggle keeps its desktop `.collapsed` behavior — the drawer is OFF.
const appEl          = document.getElementById('app');
const drawerBackdrop = document.getElementById('drawer-backdrop');
const mqlNarrow      = window.matchMedia('(max-width: 768px)');
// The Docs right pane is only WORTH its width on a genuinely wide desktop — the
// CSS reveals it at ≥1400px. The JS reparent must track the SAME breakpoint:
// below it the outline/marks panes stay in the sidebar drawer (the right pane
// is display:none, so reparenting INTO it would hide them). Re-evaluated on a
// breakpoint cross so a window resize re-homes the panes correctly.
const mqlWidePane    = window.matchMedia('(min-width: 1400px)');
mqlWidePane.addEventListener('change', () => {
  applyRightPane(document.documentElement.dataset.chrome);
  // The ≥1400px floor is also the margin-sidenote gate — crossing it builds or
  // tears down the band (applyMarginNotes re-checks the full gate).
  applyMarginNotes();
});
// Split-view (Pane B) gate — TIGHTER than the right pane: two readable columns
// need ≥1440px. Crossing the floor downward while split is open collapses it
// (the CSS would otherwise leave a phantom half-panel below the breakpoint).
const mqlSplit       = window.matchMedia('(min-width: 1440px)');
mqlSplit.addEventListener('change', () => {
  if (!mqlSplit.matches && isSplitOpen()) closeSplitPane();
});

function isDrawerOpen()  { return appEl.classList.contains('drawer-open'); }

// Overlay layout = the sidebar behaves as an over-content sheet rather than
// a docked rail: always at narrow width (mobile drawer), and at desktop
// width whenever the reader layout is active (redesign 02).
function isOverlayChrome() {
  return mqlNarrow.matches || document.documentElement.dataset.chrome !== 'docs';
}

// Every control that opens the sheet reports its expanded state — in reader
// mode #sidebar-toggle is display:none, so without the pill/Aa updates no
// visible control would expose the sheet state to assistive tech.
// (#sidebar-toggle is NOT in this list: it is a classic-only collapse
// control — redesign 04 — and its aria tracks the docked sidebar instead.)
function setSheetExpanded(expanded) {
  // The mobile search slot opens the command palette and the Aa controls
  // (#rt-aa, the 'aa' slot) open the settings sheet — both are modals, not the
  // drawer — so they are excluded here; their aria is managed by openPalette /
  // openSettings via aria-haspopup="dialog".
  document.querySelectorAll('#reader-pill [data-pill], #mobile-toolbar [data-mt]:not([data-mt="search"]):not([data-mt="aa"])').forEach((b) =>
    b.setAttribute('aria-expanded', String(expanded)));
}

// Classic docked-sidebar collapse (redesign 04): one mutation point so the
// toggle's aria-expanded always tracks docked-sidebar visibility. Overlay
// layouts never call this — their state lives in #app.drawer-open and is
// reported by setSheetExpanded on the sheet-opener controls.
function setClassicCollapsed(on) {
  sidebar.classList.toggle('collapsed', on);
  syncClassicToggleAria();
}
function syncClassicToggleAria() {
  if (!sidebarBtn) return;
  if (document.documentElement.dataset.chrome === 'docs') {
    sidebarBtn.setAttribute('aria-expanded', String(!sidebar.classList.contains('collapsed')));
  }
}
// Mobile bar pill (mobile-bar T5): mark the slot whose sheet is open, regardless
// of how it opened (toolbar tap, keyboard shortcut, note-entry click, reader
// pill, palette). Driven off the open sheet's active pane (or the settings panel
// for the Aa slot) so it is consistent across every opener (review w9brruifz).
function syncMobileActiveSlot() {
  // The settings sheet is its own surface (settings-isolation): the 'aa' slot
  // lights when it is open, independently of which content tab the drawer holds.
  let active = '';
  if (mqlNarrow.matches) {
    if (settingsOpen) active = 'aa';
    else if (isDrawerOpen()) active = activeTab;
  }
  document.querySelectorAll('#mobile-toolbar [data-mt]').forEach((x) => {
    const on = x.dataset.mt === active;
    x.classList.toggle('mt-active', on);
    if (on) x.setAttribute('aria-current', 'true'); else x.removeAttribute('aria-current');
  });
}
function openDrawer() {
  appEl.classList.add('drawer-open');
  setSheetExpanded(true);
  syncMobileActiveSlot();
}
function closeDrawer() {
  appEl.classList.remove('drawer-open');
  // The mobile sheet's transient state must not leak into the next open: a
  // drag-dismiss leaves an inline transform and an expanded sheet stays
  // .sheet-full — both reset to the 75% resting detent (redesign 03).
  // No-ops on desktop, where neither is ever set.
  sidebar.classList.remove('sheet-full');
  sidebar.style.transform = '';
  setSheetExpanded(false);
  syncMobileActiveSlot();                              // clears the pill (drawer now closed)
}
function toggleDrawer() { isDrawerOpen() ? closeDrawer() : openDrawer(); }
function maybeCloseDrawer() { if (isOverlayChrome()) closeDrawer(); }

// When the viewport crosses the breakpoint, reset to that mode's resting state:
// leaving narrow width must clear any open drawer so the desktop dock is clean;
// entering narrow width must start closed (no auto-open). Chrome auto-hide
// state resets too — readerChromeTick is dormant while narrow, so a stale
// reader-chrome-hidden would otherwise survive a desktop→mobile→desktop
// crossing and resume with the top bar/pill hidden (QR finding).
mqlNarrow.addEventListener('change', () => {
  // Clear ALL mobile-only chrome state on a breakpoint crossing, or it strands
  // on desktop: a selection's docked annotation toolbar would stay pinned to the
  // viewport bottom (.docked / body.annotating), and a pending rail label timer
  // would fire against the now-hidden rail (review w9brruifz blocker).
  hideToolbar();
  closeDrawer();
  document.documentElement.classList.remove('reader-chrome-hidden');
  rcLastY = null;
  if (railLabelTimer) { clearTimeout(railLabelTimer); railLabelTimer = null; }
  if (mobileRailLabel) mobileRailLabel.classList.remove('show');
});

// Sidebar toggle — classic-only (display:none in reader desktop and at
// ≤768px, where the Plan-03 toolbar owns the sheet): plain collapse, no
// overlay branch (redesign 04 deleted the dead toggleDrawer() arm).
sidebarBtn.addEventListener('click', () => {
  setClassicCollapsed(!sidebar.classList.contains('collapsed'));
});

// Backdrop tap dismisses the drawer.
if (drawerBackdrop) {
  drawerBackdrop.addEventListener('click', () => closeDrawer());
}

// ── Mobile sheet drag (redesign 03 T3) ──────────────────────────────────────
// Pointer-events drag on the grab handle only (a content drag would fight
// the pane lists' internal scrolling). Detents step one at a time:
// down >90px dismisses from rest / collapses from full; up >60px expands.
// The sheet follows the finger downward; upward release snaps via the CSS
// height transition. Inline transform cleanup lives in closeDrawer.
{
  const sheetHandle = document.getElementById('sheet-handle');
  let sheetDragY0 = null;
  let sheetDragDy = 0;
  if (sheetHandle) {
    sheetHandle.addEventListener('pointerdown', (e) => {
      if (!mqlNarrow.matches || !isDrawerOpen()) return;
      sheetDragY0 = e.clientY;
      sheetDragDy = 0;
      sidebar.classList.add('sheet-dragging');
      sheetHandle.setPointerCapture(e.pointerId);
    });
    sheetHandle.addEventListener('pointermove', (e) => {
      if (sheetDragY0 === null) return;
      sheetDragDy = e.clientY - sheetDragY0;
      // Follow the finger downward only; upward stays detented until release.
      sidebar.style.transform = sheetDragDy > 0 ? `translateY(${sheetDragDy}px)` : '';
    });
    const sheetDragEnd = () => {
      if (sheetDragY0 === null) return;
      sidebar.classList.remove('sheet-dragging');
      sidebar.style.transform = '';
      const dy = sheetDragDy;
      sheetDragY0 = null;
      if (dy > 90) {
        if (sidebar.classList.contains('sheet-full')) sidebar.classList.remove('sheet-full');
        else closeDrawer();
      } else if (dy < -60) {
        sidebar.classList.add('sheet-full');
      }
    };
    sheetHandle.addEventListener('pointerup', sheetDragEnd);
    sheetHandle.addEventListener('pointercancel', sheetDragEnd);
  }
}

// Sidebar resize drag
{
  const resizeHandle = document.getElementById('sidebar-resize');
  const MIN_W = 160, MAX_W = 600;
  let dragging = false;

  // Restore persisted width
  const savedW = localStorage.getItem('viewer-sidebar-w');
  if (savedW) {
    const w = Math.min(MAX_W, Math.max(MIN_W, parseInt(savedW, 10)));
    document.documentElement.style.setProperty('--sidebar-w', w + 'px');
  }

  resizeHandle.addEventListener('mousedown', (e) => {
    e.preventDefault();
    dragging = true;
    document.documentElement.classList.add('sidebar-resizing');
  });

  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const w = Math.min(MAX_W, Math.max(MIN_W, e.clientX));
    document.documentElement.style.setProperty('--sidebar-w', w + 'px');
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.documentElement.classList.remove('sidebar-resizing');
    const w = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w').trim();
    localStorage.setItem('viewer-sidebar-w', w);
  });
}

// Note: outside-tap dismissal at narrow width is handled by the drawer backdrop
// (see closeDrawer / #drawer-backdrop click handler above). No document-level
// outside-click handler is needed — the backdrop intercepts the tap, and any
// in-content navigation closes the drawer explicitly.

// Keep every history entry's scrollY up to date so back/forward can restore it
{
  let scrollSaveTimer = null;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollSaveTimer);
    scrollSaveTimer = setTimeout(() => {
      const s = history.state || {};
      history.replaceState(
        { ...s, file: s.file || currentFile, scrollY: window.scrollY },
        ''
      );
    }, 150);
  }, { passive: true });
}

// ---------------------------------------------------------------------------
// Reading progress + always-on outline scroll sync
// ---------------------------------------------------------------------------
// Heading positions are derived from the DOM here (not from the outline
// sidebar), so "section" progress works regardless of which sidebar tab is
// active. buildOutline() (Task 4) supplies only the heading->entry map used
// for the outline .active class.
const scrollSync = window.ViewerScrollSync;
const SCROLL_SYNC_THRESHOLD = 80;
let ssHeadingEls = [];          // current-file <hN> elements, document order
let ssHeadingTops = [];         // their document-Y tops, parallel to ssHeadingEls
let ssEntryByHeading = null;    // Map<hN element, outline-entry element> | null
let ssActiveEntry = null;       // current .active outline entry; reset whenever
                                // the heading set changes (ssCollectHeadings) and
                                // by registerOutlineSpy — so a stale entry from a
                                // previous file/render can never dedupe-suppress.
let ssRafPending = false;
const progressFillEl = document.getElementById('reading-progress-fill');
const pillPctEl = document.getElementById('pill-pct');
const railFillEl = document.getElementById('reader-rail-fill');
// Mobile bottom reading rail (mobile-bar T1): always-visible position +
// tap-to-summon + label cycle. Fed by the same whole-doc fraction below.
const mobileRailFill = document.getElementById('mobile-rail-fill');
const mobileRail = document.getElementById('mobile-rail');
const mobileRailLabel = document.getElementById('mobile-rail-label');
let railLabelMode = 'percent';
let railLabelTimer = null;
let railActiveSection = '';
let railActivePct = 0;

function ssCollectHeadings() {
  ssHeadingEls = Array.from(
    contentEl.querySelectorAll('h1, h2, h3, h4, h5, h6'));
  // Heading set just changed (new file/render or resize): the previously
  // active entry is stale, so clear it to avoid dedupe-suppressing the
  // first match against an entry from the old document.
  ssActiveEntry = null;
  ssRecomputeHeadingTops();
}

// Separated from ssCollectHeadings so a future resize-only path can refresh
// positions without re-walking the DOM for the (unchanged) heading set.
function ssRecomputeHeadingTops() {
  ssHeadingTops = ssHeadingEls.map(
    (el) => el.getBoundingClientRect().top + window.scrollY);
}

// Called by buildOutline() (Task 4) with a Map from the current file's
// heading elements to their outline-entry elements. Pass null to clear.
function registerOutlineSpy(entryByHeading) {
  ssEntryByHeading = entryByHeading instanceof Map ? entryByHeading : null;
  ssActiveEntry = null;
  scheduleScrollSync();
}

// Called post-render and on resize: heading positions shifted.
function scrollSyncRefreshLayout() {
  ssCollectHeadings();
  scheduleScrollSync();
}

function scheduleScrollSync() {
  if (ssRafPending) return;
  ssRafPending = true;
  requestAnimationFrame(() => {
    ssRafPending = false;
    // Chrome auto-hide shares this rAF (one coalesced callback per frame)
    // and runs FIRST: it reads scrollHeight, and running it after the
    // progress writes below would force a synchronous reflow every scroll
    // frame in reader mode (QR finding).
    readerChromeTick();
    scrollSyncTick();
  });
}

function scrollSyncTick() {
  if (!scrollSync) return;
  const scrollTop = window.scrollY;
  const viewport = window.innerHeight;
  const docHeight = document.documentElement.scrollHeight;
  const scanLine = scrollTop + SCROLL_SYNC_THRESHOLD;

  let activeIdx = -1;
  if (ssHeadingTops.length) {
    activeIdx = scrollSync.computeActiveHeadingIndex(ssHeadingTops, scanLine);
    if (scrollTop + viewport >= docHeight - 2) {
      activeIdx = ssHeadingTops.length - 1;
    }
  }

  // Outline active entry (only when an entry map is registered — Task 4).
  if (activeIdx >= 0 && ssEntryByHeading) {
    const headingEl = ssHeadingEls[activeIdx];
    const entry = headingEl ? ssEntryByHeading.get(headingEl) : null;
    if (entry && entry !== ssActiveEntry && entry.isConnected) {
      outlineEl.querySelectorAll('.outline-entry.active')
        .forEach((x) => x.classList.remove('active'));
      entry.classList.add('active');
      entry.scrollIntoView({ block: 'nearest', behavior: 'auto' });
      ssActiveEntry = entry;
    }
  }

  // Progress fill.
  if (progressFillEl) {
    let sectionTop = NaN;
    let sectionBottom = NaN;
    if (progressMode === 'section' && activeIdx >= 0) {
      sectionTop = ssHeadingTops[activeIdx];
      sectionBottom = (activeIdx + 1 < ssHeadingTops.length)
        ? ssHeadingTops[activeIdx + 1] : docHeight;
    }
    const frac = scrollSync.computeProgress({
      mode: progressMode, scrollTop, viewport, docHeight,
      scanThreshold: SCROLL_SYNC_THRESHOLD, sectionTop, sectionBottom,
    });
    progressFillEl.style.width = (frac * 100) + '%';
    // The pill % and the rail are always WHOLE-DOC, even in section mode:
    // the rail's geometry and click-to-jump map linearly over the document,
    // so a section-relative fill would put the visible fill edge and the
    // click target on different scales (QR finding). Section mode remains a
    // classic-bar feature.
    const fracDoc = (progressMode === 'section')
      ? scrollSync.computeProgress({
          mode: 'whole-doc', scrollTop, viewport, docHeight,
          scanThreshold: SCROLL_SYNC_THRESHOLD, sectionTop: NaN, sectionBottom: NaN,
        })
      : frac;
    // Guarded write: an unconditional textContent assignment replaces the
    // text node even when identical, keeping layout dirty every frame.
    const pct = Math.round(fracDoc * 100) + '%';
    if (pillPctEl && pillPctEl.textContent !== pct) pillPctEl.textContent = pct;
    if (railFillEl) railFillEl.style.height = (fracDoc * 100) + '%';
    if (mobileRailFill) mobileRailFill.style.width = (fracDoc * 100) + '%';
    railActivePct = fracDoc * 100;
    railActiveSection = (activeIdx >= 0 && ssHeadingEls[activeIdx]) ? ssHeadingEls[activeIdx].textContent.trim() : '';
  }
}

window.addEventListener('scroll', scheduleScrollSync, { passive: true });
window.addEventListener('resize', scrollSyncRefreshLayout, { passive: true });
// Margin sidenotes re-evaluate the gate (width may cross ≥1400px) and re-run the
// O(n) de-collision pass on resize — wrapping width changes every anchor's top.
// applyMarginNotes() does a full teardown + KaTeX-clone rebuild + layout-
// thrashing de-collision; firing it raw on every resize event janks a continuous
// resize-drag of a sidenote-heavy immersive doc. Coalesce to one pass per frame.
let marginNotesResizeRaf = 0;
window.addEventListener('resize', () => {
  if (marginNotesResizeRaf) return;
  marginNotesResizeRaf = requestAnimationFrame(() => {
    marginNotesResizeRaf = 0;
    applyMarginNotes();
  });
}, { passive: true });

// ---------------------------------------------------------------------------
// Cross-file link interception (registered once during init)
// ---------------------------------------------------------------------------
function handleLinkClick(e) {
  // A more specific click handler (e.g. installFootnoteRefHandlers on a noted
  // footnote ref) may have already preventDefault()ed and routed the click to
  // the sidebar. Don't double-handle by also scrolling the document.
  if (e.defaultPrevented) return;
  const a = e.target.closest('a');
  if (!a) return;
  const href = a.getAttribute('href');
  if (!href) return;

  // Internal anchor link within current file
  if (href.startsWith('#')) {
    e.preventDefault();
    updateURL(currentFile, href.slice(1));
    scrollToAnchor(href.slice(1));
    return;
  }

  // Cross-file .md link
  const mdMatch = href.match(/^([^#]*\.md)(?:#(.*))?$/);
  if (mdMatch) {
    e.preventDefault();
    const [, rawFile, anchor] = mdMatch;
    // Resolve relative to current file's directory
    const file = resolveRelPath(rawFile);
    loadFile(file, anchor);
    return;
  }

  // External links open in new tab
  if (href.startsWith('http')) {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener');
  }
}

// ---------------------------------------------------------------------------
// Anchor scrolling
// ---------------------------------------------------------------------------
// Re-arm the landing flash on `el`: remove the class, force a synchronous
// reflow (`void el.offsetWidth`) so the browser registers the removal, then
// re-add it — without the reflow a remove+add in the same tick is a no-op and
// re-navigating to an already-flashed anchor would be silent. When
// html.no-scroll-fx is set the CSS suppresses the .anchor-highlight animation
// (style.css), so the reflow has nothing to re-arm; skip it but still toggle
// the class so the DOM state is consistent. Shared by Pane A's scrollToAnchor
// and both Pane B scroll paths (review w9d47hl9a #18).
function flashAnchor(el) {
  if (!el) return;
  el.classList.remove('anchor-highlight');
  if (!document.documentElement.classList.contains('no-scroll-fx')) {
    void el.offsetWidth;   // force reflow so the re-add restarts the animation
  }
  el.classList.add('anchor-highlight');
}

function scrollToAnchor(anchor, opts) {
  if (!anchor) return;
  const el = document.getElementById(anchor);
  if (!el) return;
  // In a lazy-math document (bug 2026-06-10-01) a smooth scroll sweeps the
  // IntersectionObserver past every placeholder en route (rendering them
  // all), and blocks rendering above the target shift its position while
  // the animation runs (overflow-anchor is disabled globally). So: jump
  // instantly and re-snap once the near-target placeholders have rendered.
  const hasPendingMath = !!contentEl.querySelector('[data-math-pending]');
  const instant = !!(opts && opts.instant) || hasPendingMath;
  const smooth = !instant && !document.documentElement.classList.contains('no-scroll-fx');
  // 'instant' (not 'auto') — behavior:'auto' defers to the html
  // scroll-behavior:smooth CSS and would still animate.
  el.scrollIntoView({ behavior: instant ? 'instant' : (smooth ? 'smooth' : 'auto'), block: 'start' });
  if (hasPendingMath) {
    setTimeout(() => {
      const target = document.getElementById(anchor);
      if (target) target.scrollIntoView({ behavior: 'instant', block: 'start' });
    }, 350);
  }
  // Flash highlight
  flashAnchor(el);

  // Also highlight the parent display equation or paragraph
  const parent = el.closest('.katex-display, p, tr, li') || el.parentElement;
  if (parent && parent !== el) flashAnchor(parent);
}

// ---------------------------------------------------------------------------
// URL management (bookmarkable)
// ---------------------------------------------------------------------------
function updateURL(file, anchor, skipSnapshot = false) {
  // Snapshot current scrollY into the *outgoing* history entry so popstate
  // can restore the exact position the user was at before navigating away.
  // Cross-file callers (loadFile) snapshot earlier — before renderToContent
  // clamps window.scrollY — and pass skipSnapshot=true to avoid the
  // post-render read clobbering the correct value.
  if (!skipSnapshot) {
    const prev = history.state || {};
    history.replaceState({ ...prev, scrollY: window.scrollY }, '');
  }

  const params = new URLSearchParams();
  if (file) params.set('file', file);
  const hash = anchor ? `#${anchor}` : '';
  const url = `?${params}${hash}`;
  history.pushState({ file, anchor }, '', url);
}

function parseURL() {
  const params = new URLSearchParams(location.search);
  const file   = params.get('file');
  const anchor = location.hash ? location.hash.slice(1) : null;
  return { file, anchor };
}

// Instant scroll that bypasses CSS `scroll-behavior: smooth` so back/forward
// navigation snaps to the saved position instead of animating through a long
// smooth-scroll trajectory.
function scrollToInstant(y) {
  window.scrollTo({ top: y, left: 0, behavior: 'instant' });
}

// Re-assert scrollY on every frame for up to `durationMs` so late KaTeX
// layout, font loads, or browser scroll-anchoring cannot drift the
// restored position off-target. The loop ends early once the position has
// been stable for three consecutive frames.
function scrollToStable(y, durationMs = 600) {
  const start = performance.now();
  let stableFrames = 0;
  const tick = () => {
    const delta = window.scrollY - y;
    if (delta !== 0) {
      scrollToInstant(y);
      stableFrames = 0;
    } else {
      stableFrames++;
    }
    if (stableFrames >= 3) return;
    if (performance.now() - start < durationMs) {
      requestAnimationFrame(tick);
    }
  };
  requestAnimationFrame(tick);
}

window.addEventListener('popstate', (e) => {
  const state = e.state || parseURL();
  const file   = state.file;
  const anchor = state.anchor || null;
  const targetScrollY = typeof state.scrollY === 'number' ? state.scrollY : null;
  if (!file) return;

  // Same file — skip the expensive re-render; just scroll.
  if (file === currentFile) {
    if (targetScrollY != null) {
      scrollToInstant(targetScrollY);
    } else if (anchor) {
      scrollToAnchor(anchor);
    }
    return;
  }

  // Cross-file pop. If we have an explicit scrollY to restore, pass
  // anchor=null so loadFile doesn't scroll to the anchor (which would
  // override our restore) — then scroll to targetScrollY once the new
  // content has been laid out.
  if (targetScrollY != null) {
    loadFile(file, null, false).then(() => scrollToStable(targetScrollY));
  } else {
    loadFile(file, anchor, false);
  }
});

// ---------------------------------------------------------------------------
// Search scope: follows the active sidebar tab's pane scope.
// Outline tab    → getScope(folder, 'outline')
// Highlights tab → getScope(folder, 'highlights')
// Files / other  → 'workspace' (search across every file in fileList)
// ---------------------------------------------------------------------------
function getSearchScope() {
  if (!currentFile) return 'workspace';
  if (activeTab === 'outline')    return getScope(folderOf2(currentFile), 'outline');
  if (activeTab === 'highlights') return getScope(folderOf2(currentFile), 'highlights');
  return 'workspace';
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------
let searchTimeout = null;

const searchClear = document.getElementById('search-clear');

function syncSearchClearVisibility() {
  searchClear.hidden = searchInput.value.length === 0;
}

searchInput.addEventListener('input', () => {
  syncSearchClearVisibility();
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(doSearch, 200);
});

searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    searchInput.value = '';
    searchRes.innerHTML = '';
    syncSearchClearVisibility();
    searchInput.blur();
  }
});

searchClear.addEventListener('click', () => {
  searchInput.value = '';
  searchRes.innerHTML = '';
  syncSearchClearVisibility();
  searchInput.focus();
});

async function doSearch() {
  const query = searchInput.value.trim().toLowerCase();
  if (query.length < 2) {
    searchRes.innerHTML = '';
    return;
  }

  // Resolve target file set per scope. In-folder files come first so the
  // 50-result cap fills with current-folder hits before out-of-folder hits.
  const scope = getSearchScope();
  const activeFolder = currentFile ? folderOf2(currentFile) : null;
  const here       = activeFolder != null ? fileList.filter(f => folderOf2(f) === activeFolder) : [];
  const elsewhere  = activeFolder != null ? fileList.filter(f => folderOf2(f) !== activeFolder) : fileList;
  const targetFiles = scope === 'file'   ? (currentFile ? [currentFile] : [])
                    : scope === 'folder' ? here
                    : [...here, ...elsewhere]; // workspace

  // Prefetch only the files we'll search.
  await Promise.all(targetFiles.map(f => {
    if (!fileContents[f]) return fetchFile(f);
    return Promise.resolve();
  }));

  const results = [];
  for (const f of targetFiles) {
    const lines = (fileContents[f] || '').split('\n');
    for (let i = 0; i < lines.length; i++) {
      const idx = lines[i].toLowerCase().indexOf(query);
      if (idx !== -1) {
        // Extract snippet around match
        const start = Math.max(0, idx - 30);
        const end   = Math.min(lines[i].length, idx + query.length + 30);
        let snippet = lines[i].slice(start, end);
        // Highlight match in snippet
        const matchStart = idx - start;
        snippet = escapeHtml(snippet.slice(0, matchStart))
                + '<em>' + escapeHtml(snippet.slice(matchStart, matchStart + query.length)) + '</em>'
                + escapeHtml(snippet.slice(matchStart + query.length));
        results.push({ file: f, line: i + 1, snippet });
        if (results.length >= 50) break;
      }
    }
    if (results.length >= 50) break;
  }

  // Group results: in-folder first, then a divider, then out-of-folder.
  // Divider only renders when both groups have hits (i.e. workspace mode
  // with at least one of each); folder/file scope produces an empty
  // elsewhereResults so the divider never appears.
  const hereResults      = activeFolder == null ? []      : results.filter(r => folderOf2(r.file) === activeFolder);
  const elsewhereResults = activeFolder == null ? results : results.filter(r => folderOf2(r.file) !== activeFolder);

  const renderHit = (r) =>
    `<div class="search-hit" data-file="${r.file}" data-line="${r.line}">
       <div class="search-hit-file">${r.file}:${r.line}</div>
       <div class="search-hit-text">${r.snippet}</div>
     </div>`;

  let html = hereResults.map(renderHit).join('');
  if (hereResults.length && elsewhereResults.length) {
    html += '<div class="search-sep">Other folders</div>';
  }
  html += elsewhereResults.map(renderHit).join('');
  searchRes.innerHTML = html;

  // Click handler for search results — async so we can scroll to the matched
  // line after the file finishes loading + rendering.
  searchRes.querySelectorAll('.search-hit').forEach(el => {
    el.addEventListener('click', async () => {
      const file = el.dataset.file;
      const line = parseInt(el.dataset.line, 10);
      searchInput.value = '';
      searchRes.innerHTML = '';
      // A search-hit tap navigates to content — dismiss the drawer at narrow width.
      maybeCloseDrawer();
      await loadFile(file);
      if (Number.isFinite(line)) {
        const block = findEnclosingBlockByLine(line);
        if (block) block.scrollIntoView({ behavior: 'auto', block: 'center' });
      }
    });
  });
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Settings sheet is a modal and owns the keyboard while open: Esc closes it,
  // every other shortcut is inert behind it (mirrors the palette block below).
  if (settingsOpen) {
    if (e.key === 'Escape') { e.preventDefault(); closeSettings(); }
    return;
  }
  // Esc closes the slide-over drawer at narrow width or in reader layout (when
  // open) — but only once the peek is gone, so Esc dismisses the topmost overlay
  // (the peek) first rather than both at once (review wrnjhusbu).
  if (e.key === 'Escape' && isOverlayChrome() && isDrawerOpen() && (!peekPopover || peekPopover.hidden)) {
    e.preventDefault();
    closeDrawer();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    // Cmd/Ctrl+K now opens the command palette (redesign 05). The sidebar
    // search box stays reachable via the mobile-toolbar 'search' slot and the
    // classic docked box; the palette's full-text mode routes back into it.
    paletteOpen ? closePalette() : openPalette();
    return;
  }
  // While the palette is open it owns the keyboard: background shortcuts must
  // not mutate state behind the modal (the Ctrl+K branch above already toggled
  // it closed; Esc is handled by the palette input itself). Review weqs70hun.
  if (paletteOpen) return;
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault();
    if (isOverlayChrome()) {
      toggleDrawer();
    } else {
      setClassicCollapsed(!sidebar.classList.contains('collapsed'));
    }
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
    if (undoStack.length) { e.preventDefault(); undoLastAction(); }
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'o') {
    e.preventDefault();
    if (isOverlayChrome()) {
      // Opening a closed sheet always shows the REQUESTED pane: activeTab
      // persists after maybeCloseDrawer(), so the docked toggle semantics
      // would reopen on the files pane whenever outline was already active
      // (QR finding). Toggling only applies to a visible pane.
      if (!isDrawerOpen()) { openDrawer(); switchTab('outline'); return; }
    } else if (sidebar.classList.contains('collapsed')) {
      setClassicCollapsed(false);
    }
    switchTab(activeTab === 'outline' ? 'files' : 'outline');
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'h') {
    e.preventDefault();
    if (isOverlayChrome()) {
      if (!isDrawerOpen()) { openDrawer(); switchTab('highlights'); return; }
    } else if (sidebar.classList.contains('collapsed')) {
      setClassicCollapsed(false);
    }
    switchTab(activeTab === 'highlights' ? 'files' : 'highlights');
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'f') {
    e.preventDefault();
    // Focus = the deepest immersive notch; toggle in (from reader/docs/focus)
    // and back out to reader. Mirrors the prototype's ⌘⇧F Focus affordance.
    settingsStore.set('chrome', settingsStore.get('chrome') === 'focus' ? 'reader' : 'focus');
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'l') {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);
    if (!contentEl.contains(range.commonAncestorContainer)) return;
    e.preventDefault();
    savedRange = range.cloneRange();
    hlToolbar.classList.remove('clear-only');
    hlToolbar.classList.remove('recolor-only');
    showToolbar(range);
  }
});

// ---------------------------------------------------------------------------
// Named refresh helper — single code path for current-file revalidation
// ---------------------------------------------------------------------------
async function refreshCurrentFile({ preserveScroll = true, showDiffToast = true } = {}) {
  if (!currentFile) return;
  try {
    const { text, revision } = await backend.getMarkdown(currentFile);
    fileRevisions[currentFile] = revision;
    // Content-equality check: skip rerender if nothing changed (dedupes self-originated edits).
    // Still rebuild the manifest in case markManifestDirty() deleted it when the WS change
    // message arrived (the WS handler always calls markManifestDirty before refreshCurrentFile,
    // so the manifest entry may be absent even though our local state is authoritative).
    if (text === fileContents[currentFile]) {
      refreshManifestFromLocalState(currentFile);
      return;
    }
    fileContents[currentFile] = text;
    const oldBlocks = snapshotBlocks();
    const scrollY = window.scrollY;
    renderToContent(text);
    await ensureAnnotationsLoaded(currentFile, true);
    applySidecarHighlights();
    markManifestDirty(currentFile);
    const n = highlightChangedBlocks(oldBlocks);
    if (preserveScroll) requestAnimationFrame(() => window.scrollTo(0, scrollY));
    if (showDiffToast && n > 0) showToast(`${n} block${n > 1 ? 's' : ''} updated`);
    if (activeTab === 'highlights') buildHighlights();
  } catch {}
}

// ---------------------------------------------------------------------------
// WebSocket — live reload
// ---------------------------------------------------------------------------
function connectWS() {
  backend.connectLiveReload({
    onMessage: (msg) => {
      try {
        if (msg.type === 'change') {
          markManifestDirty(msg.file);
          if (msg.target === 'annotations') {
            delete annotationDocs[msg.file];
            delete annotationRevisions[msg.file];
            if (msg.file === currentFile) {
              ensureAnnotationsLoaded(msg.file, true).then(() => {
                applySidecarHighlights();
                if (activeTab === 'highlights') buildHighlights();
              });
            }
          } else if (msg.file === currentFile) {
            refreshCurrentFile();
          } else {
            delete fileContents[msg.file];
            delete fileRevisions[msg.file];
            flashSidebarEntry(msg.file);
            if (activeTab === 'outline' && folderOf2(msg.file) === folderOf2(currentFile)) {
              fetchFile(msg.file).catch(() => {}).then(() => buildOutline());
            }
          }
        } else if (msg.type === 'add' || msg.type === 'remove') {
          markManifestDirty();
          fetchFileList().then(() => buildSidebar());
        }
      } catch {}
    },
    onClose: () => { setTimeout(connectWS, 2000); },
  });
}

// Catch missed file-system events when tab regains focus — registered once
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    refreshCurrentFile();
    scheduleVersionCheck();
  }
});

function clearSidecarPaint() {
  contentEl.querySelectorAll('[data-sidecar-hit-id]').forEach((el) => {
    el.classList.remove('sidecar-hl');
    el.classList.remove('hl-yellow', 'hl-green', 'hl-red', 'hl-blue', 'hl-orange', 'hl-purple', 'hl-teal', 'hl-pink');
    delete el.dataset.sidecarHitId;
  });
}

function applySidecarHighlights() {
  clearSidecarPaint();
  if (!currentFile) return;
  const doc = annotationDocs[currentFile];
  if (!doc || !Array.isArray(doc.highlights)) return;
  for (const hit of doc.highlights) {
    if (hit.deleted) continue;
    const color = HIGHLIGHT_COLORS.includes(hit.color) ? hit.color : 'yellow';
    const segments = Array.isArray(hit.segments) ? hit.segments : [];
    for (const seg of segments) {
      const lineStart = Math.max(0, Number(seg.lineStart ?? seg.blockLine ?? 0) || 0);
      const lineEnd = Math.max(lineStart, Number(seg.lineEnd ?? lineStart) || lineStart);
      // Collect candidate elements first, then retain only the topmost — any
      // element whose ancestor is also in the candidate set is a nested
      // descendant that would cause double-painting.
      const candidates = [];
      contentEl.querySelectorAll('[data-source-line]').forEach((el) => {
        const line = parseInt(el.dataset.sourceLine, 10);
        if (!Number.isFinite(line)) return;
        if (line < lineStart || line > lineEnd) return;
        candidates.push(el);
      });
      const candidateSet = new Set(candidates);
      for (const el of candidates) {
        let ancestor = el.parentElement;
        let nested = false;
        while (ancestor && ancestor !== contentEl) {
          if (candidateSet.has(ancestor)) { nested = true; break; }
          ancestor = ancestor.parentElement;
        }
        if (nested) continue;
        el.classList.add('sidecar-hl', `hl-${color}`);
        el.dataset.sidecarHitId = hit.id;
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Immediate local source update after successful writes
// ---------------------------------------------------------------------------
function applyLocalSourceUpdate(filename, newSource, revision = fileRevisions[filename] || null) {
  fileContents[filename] = newSource;
  if (revision) fileRevisions[filename] = revision;
  if (!refreshManifestFromLocalState(filename)) markManifestDirty(filename);
  if (filename !== currentFile) return;
  const oldBlocks = snapshotBlocks();
  const scrollY = window.scrollY;
  renderToContent(newSource);
  ensureAnnotationsLoaded(filename).then(() => applySidecarHighlights());
  requestAnimationFrame(() => window.scrollTo(0, scrollY));
  highlightChangedBlocks(oldBlocks);
  if (activeTab === 'highlights') buildHighlights();
}

// ---------------------------------------------------------------------------
// Highlight toolbar & source mapper
// ---------------------------------------------------------------------------

// ── Toolbar DOM ──────────────────────────────────────────────────
const hlToolbar = (() => {
  const bar = document.createElement('div');
  bar.id = 'hl-toolbar';
  bar.setAttribute('role', 'toolbar');             // announced when it appears / docks (review w9brruifz)
  bar.setAttribute('aria-label', 'Annotation toolbar');
  // Color swatches
  for (const color of HIGHLIGHT_COLORS) {
    const sw = document.createElement('button');
    sw.className = 'hl-swatch';
    sw.dataset.action = color;
    sw.type = 'button';
    sw.setAttribute('aria-label', `Highlight color ${color}`);
    sw.title = color[0].toUpperCase() + color.slice(1);
    bar.appendChild(sw);
  }
  // Separator
  const sep = document.createElement('div');
  sep.className = 'hl-sep hl-sep-styles';
  bar.appendChild(sep);
  // Style buttons
  for (const [action, label] of [['bold','B'],['italic','I'],['code','<>']]) {
    const btn = document.createElement('button');
    btn.className = 'hl-btn';
    btn.dataset.action = action;
    btn.type = 'button';
    btn.textContent = label;
    btn.title = action[0].toUpperCase() + action.slice(1);
    bar.appendChild(btn);
  }
  // Separator + clear button
  const sep2 = document.createElement('div');
  sep2.className = 'hl-sep hl-sep-clear';
  bar.appendChild(sep2);
  const clearBtn = document.createElement('button');
  clearBtn.className = 'hl-btn hl-btn-clear';
  clearBtn.dataset.action = 'clear';
  clearBtn.type = 'button';
  clearBtn.textContent = '×';
  clearBtn.title = 'Remove highlight';
  bar.appendChild(clearBtn);
  // Citation buttons
  for (const [action, label, title] of [
    ['cite-rich', '\u275D', 'Copy citation (rich HTML)'],
    ['cite-md',   '\u27E6M\u27E7', 'Copy citation (markdown)'],
  ]) {
    const btn = document.createElement('button');
    btn.className = 'toolbar-cite-btn';
    btn.dataset.action = action;
    btn.type = 'button';
    btn.textContent = label;
    btn.title = title;
    bar.appendChild(btn);
  }
  // Note button
  const noteBtn = document.createElement('button');
  noteBtn.type = 'button';
  noteBtn.className = 'hl-note-btn';
  noteBtn.dataset.action = 'note';
  noteBtn.title = 'Add or edit note';
  noteBtn.innerHTML = '📝';
  bar.appendChild(noteBtn);
  document.body.appendChild(bar);
  return bar;
})();

const noteBtn = hlToolbar.querySelector('[data-action="note"]');

// ── Note popover ─────────────────────────────────────────────────
const notePopover = (() => {
  const el = document.createElement('div');
  el.id = 'note-popover';
  el.innerHTML = `
    <div class="np-header"></div>
    <textarea class="np-body" placeholder="Write a note (markdown allowed)…"></textarea>
    <div class="np-footer">
      <button class="np-delete" type="button" title="Delete note">Delete</button>
      <span class="np-spacer"></span>
      <button class="np-cancel" type="button">Cancel</button>
      <button class="np-save" type="button">Save</button>
    </div>
  `;
  document.body.appendChild(el);
  return el;
})();
const notePopHeader = notePopover.querySelector('.np-header');
const notePopBody = notePopover.querySelector('.np-body');
const notePopSave = notePopover.querySelector('.np-save');
const notePopCancel = notePopover.querySelector('.np-cancel');
const notePopDelete = notePopover.querySelector('.np-delete');

let notePopActiveEntry = null;       // manifest entry being edited
let notePopMode = null;              // 'create' | 'edit'
let notePopOriginalBody = '';        // for unsaved-changes confirm

function showNotePopover(entry, mode, anchorRect) {
  notePopActiveEntry = entry;
  notePopMode = mode;
  notePopHeader.textContent = (entry.excerpt || '').slice(0, 80);
  const initialBody = mode === 'edit' ? (entry.noteBody || '') : '';
  notePopBody.value = initialBody;
  notePopOriginalBody = initialBody;
  notePopDelete.style.display = (mode === 'edit') ? '' : 'none';
  // Position viewport-clamped near the anchor. Make it visible off-screen first
  // so we can read its real height for the vertical flip clamp (safe-area aware).
  notePopover.style.left = '-9999px';
  notePopover.style.top = '-9999px';
  notePopover.classList.add('visible');
  const rect = anchorRect
    ? { left: anchorRect.left, top: anchorRect.top, right: anchorRect.right,
        bottom: anchorRect.bottom, width: anchorRect.width ?? 0, height: anchorRect.height ?? 0 }
    : { left: 100, top: 100, right: 100, bottom: 100, width: 0, height: 0 };
  const popW = notePopover.offsetWidth || 380;
  const popH = notePopover.offsetHeight || 200;
  // Left-bias by 20px to mirror the prior placement, then clamp.
  const biased = { ...rect, left: rect.left - 20, right: (rect.left - 20) + rect.width };
  const { left, top } = clampToolbarBox(biased, popW, popH);
  notePopover.style.left = left + 'px';
  notePopover.style.top = top + 'px';
  setTimeout(() => notePopBody.focus(), 0);
}

function hideNotePopover() {
  notePopover.classList.remove('visible');
  notePopActiveEntry = null;
  notePopMode = null;
  notePopOriginalBody = '';
  notePopBody.value = '';
}

function notePopoverIsDirty() {
  return notePopBody.value !== notePopOriginalBody;
}

notePopCancel.addEventListener('click', () => {
  if (notePopoverIsDirty() && !confirm('Discard unsaved note?')) return;
  hideNotePopover();
});

document.addEventListener('keydown', (e) => {
  if (!notePopover.classList.contains('visible')) return;
  if (e.key === 'Escape') {
    if (notePopoverIsDirty() && !confirm('Discard unsaved note?')) {
      e.stopPropagation();
      return;
    }
    hideNotePopover();
    e.stopPropagation();
  } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    notePopSave.click();
  }
});

// Hide on outside click
document.addEventListener('pointerdown', (e) => {
  if (!notePopover.classList.contains('visible')) return;
  if (notePopover.contains(e.target)) return;
  if (notePopoverIsDirty()) return;  // require explicit Save/Cancel when dirty
  hideNotePopover();
});

// ── Note popover save ────────────────────────────────────────────
async function saveNoteFromPopover() {
  if (!notePopActiveEntry) return;
  const body = notePopBody.value.trim();
  if (!body) {
    showToast('Note body cannot be empty');
    return;
  }
  const file = notePopActiveEntry.file || currentFile;
  if (!file) return;
  const source = fileContents[file];
  if (typeof source !== 'string') {
    showToast('File source not loaded');
    return;
  }
  let newSource;
  let appliedNoteId;
  try {
    if (notePopMode === 'edit') {
      newSource = window.ViewerNoteMutation.editNote(source, notePopActiveEntry, body);
      appliedNoteId = notePopActiveEntry.noteId;
    } else {
      const sectionSlug = window.ViewerHighlightShared.sectionSlugAt(source, notePopActiveEntry.sourceEnd);
      const result = window.ViewerNoteMutation.addNote(source, notePopActiveEntry, body, sectionSlug);
      newSource = result.newSource;
      appliedNoteId = result.noteId;
    }
  } catch (err) {
    showToast('Save failed: ' + (err.message || 'unknown'));
    return;
  }
  // Push undo before mutating.
  pushUndo({
    file,
    source,
    revision: fileRevisions[file] || null,
    backend: 'inline',
  });
  const wrote = await putMarkdownSource(file, newSource, fileRevisions[file] || null);
  if (!wrote.ok) {
    // Discard the wasted undo entry.
    undoStack.pop();
    showToast('Save failed: ' + (wrote.error || wrote.status || 'conflict'));
    return;
  }
  applyLocalSourceUpdate(file, newSource, wrote.revision);
  const completedMode = notePopMode;   // capture before hideNotePopover() clears it
  hideNotePopover();
  showUndoToast(completedMode === 'edit' ? 'Note updated' : 'Note added');
}

notePopSave.addEventListener('click', saveNoteFromPopover);

// ── Note popover delete ───────────────────────────────────────────
async function deleteNoteFromPopover() {
  if (!notePopActiveEntry || !notePopActiveEntry.noteId) return;
  if (!confirm('Delete this note?')) return;
  const file = notePopActiveEntry.file || currentFile;
  const source = fileContents[file];
  if (typeof source !== 'string') return;
  let newSource;
  try {
    newSource = window.ViewerNoteMutation.deleteNote(source, notePopActiveEntry);
  } catch (err) {
    showToast('Delete failed: ' + (err.message || 'unknown'));
    return;
  }
  pushUndo({ file, source, revision: fileRevisions[file] || null, backend: 'inline' });
  const wrote = await putMarkdownSource(file, newSource, fileRevisions[file] || null);
  if (!wrote.ok) {
    undoStack.pop();
    showToast('Delete failed: ' + (wrote.error || wrote.status || 'conflict'));
    return;
  }
  applyLocalSourceUpdate(file, newSource, wrote.revision);
  hideNotePopover();
  showUndoToast('Note deleted');
}

notePopDelete.addEventListener('click', deleteNoteFromPopover);

let savedRange  = null;   // snapshot of the selection range before toolbar click
let savedMarkEl = null;   // set when toolbar was triggered by a click on a <mark>
let savedSidecarId = null; // set when toolbar triggered inside sidecar-painted blocks

// Declared here (above hideToolbar) so hideToolbar can cancel a pending show.
// Assigned by onSelectionChangeDebounced below.
let selectionChangeTimer = null;

function hideToolbar() {
  // Cancel any pending debounced show so a dismissal during the 120ms window
  // cannot re-pop the toolbar after it is hidden (the selection is still
  // non-collapsed at that point and would otherwise re-trigger showToolbar).
  if (selectionChangeTimer) { clearTimeout(selectionChangeTimer); selectionChangeTimer = null; }
  hlToolbar.classList.remove('visible');
  hlToolbar.classList.remove('clear-only');
  hlToolbar.classList.remove('recolor-only');
  hlToolbar.classList.remove('docked');             // mobile dock state (mobile-bar T3)
  document.body.classList.remove('annotating');
  hlToolbar.querySelectorAll('.hl-swatch.active')
    .forEach(sw => sw.classList.remove('active'));
  savedRange  = null;
  savedMarkEl = null;
  savedSidecarId = null;
}

// Read an env(safe-area-inset-*) value (px) from a computed style, or 0 if the
// browser does not expose it (desktop, non-iOS). We probe a CSS var the
// stylesheet sets to `env(...)` so JS can see the resolved inset.
function safeAreaInset(cs, side) {
  try {
    const v = cs.getPropertyValue(`--safe-${side}`);
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : 0;
  } catch {
    return 0;
  }
}

// Clamp a fixed-position box (width x height) so it lies fully inside the
// viewport, respecting safe-area insets, and flip it below `rect` when placing
// it above would push it under the top safe-area. `rect` is the selection /
// anchor rectangle (viewport coords). Returns {left, top}.
function clampToolbarBox(rect, width, height) {
  const margin = 8;
  const vw = document.documentElement.clientWidth;
  const vh = document.documentElement.clientHeight;
  // Call getComputedStyle once and read all four safe-area insets from it.
  const cs = getComputedStyle(document.documentElement);
  const insetL = safeAreaInset(cs, 'left');
  const insetR = safeAreaInset(cs, 'right');
  const insetT = safeAreaInset(cs, 'top');
  const insetB = safeAreaInset(cs, 'bottom');

  // Horizontal: center on the rect, then clamp into [margin+insetL, vw-w-margin-insetR].
  let left = rect.left + rect.width / 2 - width / 2;
  const minLeft = margin + insetL;
  const maxLeft = Math.max(minLeft, vw - width - margin - insetR);
  left = Math.max(minLeft, Math.min(left, maxLeft));

  // Vertical: prefer below the selection. If that overflows the bottom, try
  // above. If above would clear the top safe-area, use it; otherwise clamp to
  // the bottom edge. Never emit a negative top (degenerate / zero rect).
  const minTop = margin + insetT;
  const maxTop = Math.max(minTop, vh - height - margin - insetB);
  let top = rect.bottom + 6;
  if (top > maxTop) {
    const above = rect.top - height - 6;
    top = (above >= minTop) ? above : maxTop;
  }
  top = Math.max(minTop, Math.min(top, maxTop));
  return { left, top };
}

function showToolbar(range, mouse) {
  // Anchor rect: prefer the selection rect (correct on iOS where clientX/Y are
  // 0 during the native callout). Fall back to a tiny rect at the mouse point
  // on desktop so the existing mouse-driven UX is preserved. Intentional side
  // effect on desktop: the toolbar now anchors centered under the selection rect
  // rather than at the mouse click point — this is a deliberate improvement, not
  // a regression.
  let rect = null;
  if (range && typeof range.getBoundingClientRect === 'function') {
    const r = range.getBoundingClientRect();
    // A collapsed/zero rect (width===0 && height===0) is useless for anchoring;
    // fall through to the mouse point if we have one.
    if (r && (r.width > 0 || r.height > 0)) rect = r;
  }
  if (!rect && mouse) {
    rect = { left: mouse.x, top: mouse.y, right: mouse.x, bottom: mouse.y, width: 0, height: 0 };
  }
  if (!rect) {
    rect = { left: 8, top: 8, right: 8, bottom: 8, width: 0, height: 0 };
  }

  // Mobile (≤768px): the bar morphs into the annotation surface — dock the
  // toolbar to the bottom edge full-width (CSS positions .docked) rather than
  // floating it near the selection, which is unreliable by the notch / home
  // indicator (mobile Adaptive Reader Bar T3). Clear any prior inline coords.
  if (mqlNarrow.matches) {
    hlToolbar.classList.add('docked');
    document.body.classList.add('annotating');     // nav bar + rail yield (CSS)
    hlToolbar.style.left = '';
    hlToolbar.style.top = '';
    hlToolbar.classList.add('visible');
    return;
  }
  hlToolbar.classList.remove('docked');
  // Measure the toolbar: make it visible (off-screen) to read its real size,
  // then position it. This keeps the clamp accurate across clear-only /
  // recolor-only width variants instead of a hardcoded 220px guess.
  hlToolbar.style.left = '-9999px';
  hlToolbar.style.top = '-9999px';
  hlToolbar.classList.add('visible');
  const w = hlToolbar.offsetWidth || 220;
  const h = hlToolbar.offsetHeight || 40;
  const { left, top } = clampToolbarBox(rect, w, h);
  hlToolbar.style.left = `${left}px`;
  hlToolbar.style.top = `${top}px`;
}

// Show toolbar from current selection gesture
function handleSelectionGesture(e) {
  // Ignore if the pointerup is on the toolbar itself
  if (hlToolbar.contains(e.target)) return;
  const mouseX = e.clientX, mouseY = e.clientY;
  setTimeout(() => {
    const sel = window.getSelection();
    if (!sel) { hideToolbar(); return; }

    if (sel.isCollapsed) {
      // Single click — show clear-only toolbar if cursor is inside a styled element
      const node = sel.anchorNode;
      const el   = node ? (node.nodeType === Node.TEXT_NODE ? node.parentElement : node) : null;
      let markEl = el ? el.closest('mark, strong, em, code') : null;
      const sidecarHitEl = el ? el.closest('[data-sidecar-hit-id]') : null;
      // Exclude <code> inside <pre> (fenced code blocks are not removable this way)
      if (markEl && markEl.tagName === 'CODE' && markEl.closest('pre')) markEl = null;
      if (markEl && contentEl.contains(markEl)) {
        const markRange = document.createRange();
        markRange.selectNodeContents(markEl);
        savedRange  = markRange;
        savedMarkEl = markEl;

        if (markEl.tagName === 'MARK') {
          hlToolbar.classList.remove('clear-only');
          hlToolbar.classList.add('recolor-only');
          const curColor = [...markEl.classList]
            .find(c => c.startsWith('hl-'))
            ?.slice(3) ?? 'yellow';
          hlToolbar.querySelectorAll('.hl-swatch').forEach(sw => {
            sw.classList.toggle('active', sw.dataset.action === curColor);
          });
          // Show note button for inline highlights only.
          const inlineEntry = findInlineEntryForMark(markEl);
          noteBtn.style.display = inlineEntry ? '' : 'none';
          if (inlineEntry?.noteId) {
            noteBtn.classList.add('has-note');
            noteBtn.title = 'Edit note';
          } else {
            noteBtn.classList.remove('has-note');
            noteBtn.title = 'Add note';
          }
        } else {
          hlToolbar.classList.add('clear-only');
          hlToolbar.classList.remove('recolor-only');
          noteBtn.style.display = 'none';   // strong/em/code can't carry notes
        }

        showToolbar(markRange, { x: mouseX, y: mouseY });
      } else if (sidecarHitEl && contentEl.contains(sidecarHitEl)) {
        const blockRange = document.createRange();
        blockRange.selectNodeContents(sidecarHitEl);
        savedRange = blockRange;
        savedSidecarId = sidecarHitEl.dataset.sidecarHitId || null;
        const ann = (annotationDocs[currentFile]?.highlights || [])
          .find((h) => h.id === savedSidecarId);
        const curColor = ann?.color || 'yellow';
        hlToolbar.classList.remove('clear-only');
        hlToolbar.classList.add('recolor-only');
        hlToolbar.querySelectorAll('.hl-swatch').forEach(sw => {
          sw.classList.toggle('active', sw.dataset.action === curColor);
        });
        noteBtn.style.display = 'none';   // Sidecar highlights cannot have notes in v1
        showToolbar(blockRange, { x: mouseX, y: mouseY });
      } else {
        hideToolbar();
      }
      return;
    }

    if (!sel.toString().trim()) { hideToolbar(); return; }
    const range = sel.getRangeAt(0);
    if (!contentEl.contains(range.commonAncestorContainer)) { hideToolbar(); return; }
    savedRange = range.cloneRange();
    hlToolbar.classList.remove('clear-only');
    noteBtn.style.display = 'none';   // Must highlight first
    showToolbar(range);
  }, 10);
}

// Show the new-highlight toolbar for the current NON-COLLAPSED selection,
// anchored on the selection rect. Shared by the desktop mouse path (above) and
// the iOS selectionchange path (below). Returns true if it showed the toolbar.
// On iOS the native selection-callout zeroes clientX/clientY, so we must never
// rely on pointer coords here — `showToolbar(range)` uses range.getBoundingClientRect().
function showToolbarForRangeSelection(sel) {
  if (!sel || sel.isCollapsed) return false;
  if (!sel.toString().trim()) return false;
  const range = sel.getRangeAt(0);
  if (!contentEl.contains(range.commonAncestorContainer)) return false;
  savedRange = range.cloneRange();
  savedMarkEl = null;
  savedSidecarId = null;
  hlToolbar.classList.remove('clear-only');
  hlToolbar.classList.remove('recolor-only');
  hlToolbar.querySelectorAll('.hl-swatch.active').forEach(sw => sw.classList.remove('active'));
  noteBtn.style.display = 'none';   // Must highlight first
  showToolbar(range);
  return true;
}

document.addEventListener('pointerup', handleSelectionGesture);
document.addEventListener('mouseup', handleSelectionGesture);

// ── iOS touch path: selectionchange-driven show ──────────────────────────────
// iOS Safari does not deliver a reliable `pointerup`/`mouseup` at the end of a
// touch text-selection gesture (the drag may become a system gesture and fire
// `pointercancel`, or the selection is finalized by the native callout with no
// JS pointer event at all). `selectionchange` is the only event guaranteed to
// fire when the selection settles. We debounce it (~120ms) so the rapidly
// repeating events during a drag collapse into a single show after the user
// lifts. The desktop mouse path keeps working unchanged; when both fire for the
// same selection, showToolbar is idempotent (re-positions the same toolbar) so
// there is no flicker beyond a single reflow.
function onSelectionChangeDebounced() {
  if (selectionChangeTimer) clearTimeout(selectionChangeTimer);
  selectionChangeTimer = setTimeout(() => {
    selectionChangeTimer = null;
    const sel = window.getSelection();
    // Only the non-collapsed, in-content case is handled here. A collapsed
    // selection (single tap / caret) is left to the pointerup path's
    // mark/sidecar recolor logic; selectionchange must not steal that or it
    // would pop a clear-only toolbar on every caret move.
    if (sel && !sel.isCollapsed) {
      showToolbarForRangeSelection(sel);
    }
  }, 120);
}
document.addEventListener('selectionchange', onSelectionChangeDebounced);

// ── pointercancel: treat as gesture end ──────────────────────────────────────
// On iOS a text-selection drag can become a system gesture, firing
// `pointercancel` instead of `pointerup`. Don't assume pointerup ran — schedule
// a re-evaluation through the same debounced selectionchange path so the
// toolbar still shows once the selection settles.
document.addEventListener('pointercancel', () => { onSelectionChangeDebounced(); });

// ── Guarded outside-tap hide (the iOS catch-22 fix) ──────────────────────────
// The original unconditional `pointerdown → hideToolbar` nuked the toolbar the
// instant the user tapped to dismiss iOS's native selection-callout (the tap
// lands outside #hl-toolbar, so the old code hid). Predicate now:
//
//   - Never hide a tap inside #hl-toolbar (it's a toolbar action).
//   - While a NON-COLLAPSED selection still exists AND the tap target is inside
//     the selected content area (i.e. the user is still interacting with their
//     selection / dismissing the callout), keep the toolbar alive.
//   - Otherwise (tap in chrome / empty space, OR the selection has collapsed),
//     it is a genuine dismissal → hideToolbar().
//
// This keeps the toolbar through the callout-dismiss tap but still closes it on
// a deliberate tap away or once the selection is gone.
document.addEventListener('pointerdown', (e) => {
  if (hlToolbar.contains(e.target)) return;       // toolbar action — never hide
  if (!hlToolbar.classList.contains('visible')) return;
  const sel = window.getSelection();
  const hasSelection = sel && !sel.isCollapsed && sel.toString().trim();
  if (hasSelection) {
    // Keep if the tap landed anywhere inside #content while the selection
    // persists — on iOS the callout-dismiss tap can land on an adjacent block.
    // (The narrower commonAncestorContainer check is strictly subsumed by this.)
    const target = e.target instanceof Node ? e.target : null;
    if (target && contentEl.contains(target)) return;
  }
  hideToolbar();
});

// Hide on scroll and Escape
window.addEventListener('scroll', hideToolbar, true);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') hideToolbar();
});

// ── Toolbar click handler ────────────────────────────────────────
hlToolbar.addEventListener('click', (e) => {
  const el = e.target.closest('[data-action]');
  if (!el) return;
  e.preventDefault();
  e.stopPropagation();
  const action = el.dataset.action;

  if (action === 'note') {
    if (!savedMarkEl || savedMarkEl.tagName !== 'MARK') {
      hideToolbar();
      return;
    }
    const entry = findInlineEntryForMark(savedMarkEl);
    if (!entry) { hideToolbar(); return; }
    const mode = entry.noteId ? 'edit' : 'create';
    const rect = savedMarkEl.getBoundingClientRect();
    hideToolbar();
    showNotePopover(entry, mode, rect);
    return;
  }

  if (action === 'cite-rich' || action === 'cite-md') {
    copyCitation(action === 'cite-rich' ? 'rich' : 'md');
    return;
  }
  applyHighlight(action);
});

// ── Source mapper helpers ────────────────────────────────────────

function blockOf(node) {
  let el = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
  while (el && el !== contentEl) {
    if (el.dataset && el.dataset.sourceLine != null) return el;
    el = el.parentElement;
  }
  return null;
}

// Find the nearest preceding heading (walks previous siblings at each
// ancestor level, searching sibling subtrees for a deepest-last heading).
// Deliberately NOT closest() — a selection is almost never inside a heading.
function nearestHeading(block) {
  if (!block) return null;
  const HEADING_SEL = 'h1, h2, h3, h4, h5, h6';
  const toHeading = (h) => ({
    id: h.id || null,
    text: (h.textContent || '').trim(),
    level: Number(h.tagName[1]),
  });
  // If the block IS a heading (user selected text inside it), return it directly.
  // Without this check, the loop below walks to the PREVIOUS heading instead.
  if (block.matches && block.matches(HEADING_SEL)) return toHeading(block);
  let cur = block;
  while (cur && cur !== contentEl) {
    let sib = cur.previousElementSibling;
    while (sib) {
      if (sib.matches && sib.matches(HEADING_SEL)) return toHeading(sib);
      const inner = sib.querySelectorAll ? sib.querySelectorAll(HEADING_SEL) : [];
      if (inner.length) return toHeading(inner[inner.length - 1]);
      sib = sib.previousElementSibling;
    }
    cur = cur.parentElement;
  }
  return null;
}

// Fetch /api/git-info with session-level cache.
let _gitInfoPromise = null;
function fetchGitInfo() {
  if (_gitInfoPromise) return _gitInfoPromise;
  try {
    const cached = sessionStorage.getItem('viewer-git-info');
    if (cached) {
      _gitInfoPromise = Promise.resolve(JSON.parse(cached));
      return _gitInfoPromise;
    }
  } catch (_) { /* ignore */ }
  _gitInfoPromise = backend.getGitInfo()
    .then((info) => {
      try { sessionStorage.setItem('viewer-git-info', JSON.stringify(info)); } catch (_) {}
      return info;
    });
  return _gitInfoPromise;
}

// Copy a citation to the clipboard. variant ∈ {'rich','md'}.
async function copyCitation(variant) {
  if (!savedRange) return;
  // Snapshot everything synchronously — the clipboard call loses focus.
  const selectedText = window.katexAwareText(savedRange.cloneContents());
  if (!selectedText.trim()) return;
  const startNode = savedRange.startContainer;
  const block = blockOf(startNode);
  const paragraphAnchorEl = block ? block.querySelector('a[id^="p-"]') : null;
  const paragraphAnchorId = paragraphAnchorEl ? paragraphAnchorEl.id : null;
  const heading = nearestHeading(block);
  const titleEl = document.querySelector('#content h1')
    || document.querySelector('#content h2');
  const documentTitle = (titleEl && titleEl.textContent.trim()) || currentFile || '';
  const sourceLine = block && block.dataset && block.dataset.sourceLine != null
    ? Number(block.dataset.sourceLine)
    : null;
  const linkMode = settingsStore.get('citationMode');

  let gitInfo = null;
  if (linkMode === 'github') {
    try { gitInfo = await fetchGitInfo(); } catch (_) { gitInfo = null; }
  }
  const relPath = linkMode === 'github'
    ? window.resolveRepoPath(currentFile, gitInfo)
    : (currentFile || '');

  const result = window.buildCitation({
    selectedText,
    paragraphAnchorId,
    headingAnchorId: heading ? heading.id : null,
    headingText: heading ? heading.text : null,
    documentTitle,
    relPath,
    sourceLine,
    linkMode,
    gitInfo,
    viewerOrigin: window.location.origin,
  });

  try {
    if (variant === 'rich' && window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': new Blob([result.html], { type: 'text/html' }),
          'text/plain': new Blob([result.plainText], { type: 'text/plain' }),
        }),
      ]);
    } else {
      // Fallback when ClipboardItem is unavailable: always write the markdown
      // blockquote format.  result.plainText is a bare attribution line —
      // less useful to paste into a document than the full blockquote.
      await navigator.clipboard.writeText(result.markdown);
    }
    const suffix = result.warnings.length ? (' — ' + result.warnings[0]) : '';
    showToast('Citation copied' + suffix);
  } catch (err) {
    if (err && err.name === 'NotAllowedError') {
      showToast('Copy failed — click the page and retry');
    } else {
      console.error('copyCitation failed', err);
      showToast('Copy failed — see console');
    }
  }
}

function nextBlockSibling(el) {
  let cur = el;
  while (cur) {
    // Check next sibling and its descendants
    cur = cur.nextElementSibling;
    if (!cur) {
      // Walk up and try parent's next sibling
      let parent = el.parentElement;
      while (parent && parent !== contentEl) {
        if (parent.nextElementSibling) { cur = parent.nextElementSibling; break; }
        parent = parent.parentElement;
      }
      if (!cur) return null;
    }
    if (cur.dataset && cur.dataset.sourceLine != null) return cur;
    // Check descendants
    const inner = cur.querySelector('[data-source-line]');
    if (inner) return inner;
  }
  return null;
}

function charOffsetWithinElement(node, offset, root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let total = 0;
  while (walker.nextNode()) {
    if (walker.currentNode === node) return total + offset;
    total += walker.currentNode.textContent.length;
  }
  return total + offset;
}

function textBeforeNode(targetNode, root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let text = '';
  while (walker.nextNode()) {
    if (targetNode.contains(walker.currentNode)) break;
    text += walker.currentNode.textContent;
  }
  return text;
}

function lineStartOffset(source, lineNum) {
  const lines = source.split('\n');
  let offset = 0;
  for (let i = 0; i < lineNum && i < lines.length; i++) {
    offset += lines[i].length + 1;  // +1 for \n
  }
  return offset;
}

// Normalize `src` for DOM-text-to-source matching in the PLAIN_TEXT and
// PLAIN_SPANNING_MATH / MIXED_*_MATH highlight paths. Four transformations
// are applied:
//
//   1. Strip inline markdown formatting markers (`*`, `` ` ``, `~`, and
//      non-intraword `_`). DOM text has no markers, so a literal search
//      in raw `src` misses when the selection crosses a `*em*`, `**bold**`,
//      `` `code` `` or `~~strike~~` span.
//
//   2. Collapse any run of whitespace (` `, `\t`, `\n`) to a single space.
//      Soft line breaks in markdown are rendered as a single space in the
//      DOM, but the raw source contains `\n` plus continuation-line indent
//      (e.g. 2 spaces inside a list item). Without collapsing, the needle
//      `is a certificate` does not match the haystack `is a   certificate`.
//
//   3. Strip HTML comments (`<!--...-->`). These are invisible in the DOM
//      but may appear in the source as `<!-- ref:SECTION-N -->` markers
//      immediately before citation / cross-reference links.
//
//   4. Unwrap inline markdown links `[text](url)` and collapsed reference
//      links `[text][ref]` to just their visible `text`. The DOM renders
//      the link text but not the brackets or the destination, so a raw
//      search for the rendered text would miss. The map for each text
//      char points back to its original source position *inside* the
//      brackets, so recovered offsets still land on real chars.
//
// Returns `{ stripped, map }` where `src[map[i]] === stripped[i]` for
// non-whitespace chars. For collapsed whitespace runs, `map[i]` points at
// the *first* whitespace char of the run so that selStart/selEnd recovered
// via `bso + map[hit]` always lands on a real character in `src`.
//
// Intraword rule (CommonMark/GFM): `_` flanked by alphanumeric chars on
// BOTH sides is literal (e.g. `fn_name`, `x_1`) and must be preserved,
// otherwise the stripped haystack diverges from DOM text.
function stripInlineMarkersWithMap(src) {
  const MARKERS = '*`~';
  const isWord = (c) => /[A-Za-z0-9]/.test(c);
  const isWS   = (c) => c === ' ' || c === '\t' || c === '\n' || c === '\r';
  let stripped = '';
  const map = [];
  let prevWS = false;

  // Emit the char at raw position k through the inline-marker / whitespace
  // filter. Shared by the main walker and the link-text walker.
  const emit = (k) => {
    const c = src[k];
    if (MARKERS.indexOf(c) !== -1) return;
    if (c === '_') {
      const prev = k > 0 ? src[k - 1] : '';
      const next = k + 1 < src.length ? src[k + 1] : '';
      if (isWord(prev) && isWord(next)) {
        stripped += c; map.push(k); prevWS = false;
      }
      return;
    }
    if (isWS(c)) {
      if (prevWS) return;
      stripped += ' '; map.push(k); prevWS = true;
      return;
    }
    stripped += c; map.push(k); prevWS = false;
  };

  let i = 0;
  while (i < src.length) {
    // HTML comment: <!-- ... -->
    if (src[i] === '<' && src.startsWith('<!--', i)) {
      const end = src.indexOf('-->', i + 4);
      if (end !== -1) { i = end + 3; continue; }
    }
    // Inline markdown link [text](url) or collapsed ref link [text][ref].
    // Find the matching ']' for the first '['; bail on newline or unmatched.
    if (src[i] === '[') {
      let j = i + 1;
      let depth = 1;
      while (j < src.length) {
        const c = src[j];
        if (c === '\n') break;
        if (c === '\\' && j + 1 < src.length) { j += 2; continue; }
        if (c === '[') depth++;
        else if (c === ']') { depth--; if (depth === 0) break; }
        j++;
      }
      if (depth === 0 && j < src.length && src[j] === ']') {
        const afterBracket = j + 1;
        // Inline link: [text](url)
        if (src[afterBracket] === '(') {
          let k = afterBracket + 1;
          let urlDepth = 1;
          while (k < src.length) {
            const c = src[k];
            if (c === '\n') break;
            if (c === '\\' && k + 1 < src.length) { k += 2; continue; }
            if (c === '(') urlDepth++;
            else if (c === ')') { urlDepth--; if (urlDepth === 0) break; }
            k++;
          }
          if (urlDepth === 0 && k < src.length) {
            for (let m = i + 1; m < j; m++) emit(m);
            i = k + 1;
            continue;
          }
        }
        // Collapsed / full reference link: [text][ref]
        if (src[afterBracket] === '[') {
          let k = afterBracket + 1;
          while (k < src.length && src[k] !== ']' && src[k] !== '\n') k++;
          if (k < src.length && src[k] === ']') {
            for (let m = i + 1; m < j; m++) emit(m);
            i = k + 1;
            continue;
          }
        }
        // Otherwise: treat the `[` as a literal character (fall through).
      }
    }
    emit(i);
    i++;
  }
  return { stripped, map };
}

// Resolve each element in katexEls (in DOM order) to its corresponding
// source inline-math formula from allMath. For elements after the first,
// inter-math text anchoring is tried before falling back to the global
// position ratio, making the lookup robust against ==color:...== annotations
// that add source characters not present in DOM text.
function resolveInlineMath(katexEls, allMath, blockSrc, blockEl) {
  // Fast path: if every inline `$...$` in the block source rendered as a
  // KaTeX element, the mapping is strictly index-based by document order.
  // This avoids the ratio-based heuristic below, which is unreliable when
  // (a) the source contains HTML comments / markdown links not present in
  // DOM text, or (b) KaTeX inflates DOM `textContent` non-uniformly per
  // span via MathML annotations + rendered-glyph spans. Both effects are
  // common and they compound when a paragraph has many inline math spans.
  const allBlockKatex = [...blockEl.querySelectorAll('.katex:not(.katex .katex)')];
  if (allBlockKatex.length === allMath.length) {
    return katexEls.map(el => allMath[allBlockKatex.indexOf(el)]);
  }

  const mathPos = [];
  const domLen = blockEl.textContent.length;
  for (let mi = 0; mi < katexEls.length; mi++) {
    const katexEl = katexEls[mi];
    const domPreText = textBeforeNode(katexEl, blockEl);
    const domRatio = domLen ? domPreText.length / domLen : 0;

    if (mi > 0) {
      const prevKatex = katexEls[mi - 1];
      const prevMatch = mathPos[mi - 1];
      const interR = document.createRange();
      try { interR.setStartAfter(prevKatex); } catch (_e) {}
      try { interR.setEndBefore(katexEl); } catch (_e) {}
      if (!interR.collapsed) {
        const interText = interR.toString().replace(/[ \t\n\r]+/g, ' ');
        if (interText.trim()) {
          const searchFrom = prevMatch.index + prevMatch[0].length;
          const sfx = blockSrc.slice(searchFrom);
          const { stripped: sfxNorm, map: sfxMap } = stripInlineMarkersWithMap(sfx);
          const textIdx = sfxNorm.indexOf(interText);
          if (textIdx !== -1) {
            const afterOff = textIdx + interText.length;
            const absAfter = searchFrom + (afterOff < sfxMap.length ? sfxMap[afterOff] : sfx.length);
            const nextCands = allMath.filter(m => m.index >= absAfter);
            if (nextCands.length > 0) {
              mathPos.push(nextCands[0]);
              continue;
            }
          }
        }
      }
    }

    // First element or anchoring failed: position ratio, constrained to be
    // monotone (only consider formulas after the previous match).
    const searchPool = mi > 0
      ? allMath.filter(m => m.index >= mathPos[mi - 1].index + mathPos[mi - 1][0].length)
      : allMath;
    mathPos.push(
      (searchPool.length > 0 ? searchPool : allMath).reduce((b, c) =>
        Math.abs(c.index / blockSrc.length - domRatio) < Math.abs(b.index / blockSrc.length - domRatio) ? c : b
      )
    );
  }
  return mathPos;
}

// Walk up from `range.startContainer` toward `blockEl` and find the
// outermost inline-formatting ancestor (`<strong>`, `<em>`, `<code>`,
// `<del>`, `<s>`) whose start the range crosses into. If found, expand
// the range to begin BEFORE that ancestor, so a subsequent `==color: ...==`
// wrap does not split a `**...**` / `*...*` / `` `...` `` open from its
// close. Mutates `range`. Same logic for the end side.
function expandRangeToFormatBoundaries(range, blockEl) {
  const FMT = new Set(['STRONG', 'EM', 'CODE', 'DEL', 'S']);
  const findOutermostFmtAncestor = (node) => {
    let el = node && node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    let outermost = null;
    while (el && el !== blockEl) {
      if (FMT.has(el.tagName)) outermost = el;
      el = el.parentElement;
    }
    return outermost;
  };
  const startFmt = findOutermostFmtAncestor(range.startContainer);
  if (startFmt) { try { range.setStartBefore(startFmt); } catch (_e) {} }
  const endFmt = findOutermostFmtAncestor(range.endContainer);
  if (endFmt) { try { range.setEndAfter(endFmt); } catch (_e) {} }
}

function makeSidecarId() {
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  if (HighlightShared.makeSidecarHighlightId) {
    return HighlightShared.makeSidecarHighlightId(currentFile, suffix);
  }
  return `sidecar:${encodeURIComponent(currentFile)}:${suffix}`;
}

function sidecarSegmentsFromRange(range, startBlock, endBlock) {
  const startLine = Math.max(0, parseInt(startBlock?.dataset?.sourceLine || '0', 10) || 0);
  const endLine = Math.max(startLine, parseInt(endBlock?.dataset?.sourceLine || String(startLine), 10) || startLine);
  return [{
    kind: 'block-range',
    lineStart: startLine,
    lineEnd: endLine,
  }];
}

async function updateSidecarDoc(mutator, successToast) {
  const loaded = await ensureAnnotationsLoaded(currentFile, true);
  if (!loaded) {
    showToast('Failed to read annotations');
    return { ok: false };
  }
  const prevHighlights = Array.isArray(loaded.doc.highlights) ? loaded.doc.highlights : [];
  const workingDoc = {
    ...loaded.doc,
    file: currentFile,
    highlights: prevHighlights.map(h => ({ ...h, segments: Array.isArray(h.segments) ? [...h.segments] : [] })),
  };
  mutator(workingDoc.highlights);
  const wrote = await putAnnotations(currentFile, workingDoc, loaded.revision, fileRevisions[currentFile] || null);
  if (!wrote.ok) {
    if (wrote.conflict) {
      showToast('Highlight conflict: reload and retry');
      await ensureAnnotationsLoaded(currentFile, true);
      applySidecarHighlights();
    } else {
      showToast(`Annotation write failed: ${wrote.status}`);
    }
    return { ok: false };
  }
  annotationDocs[currentFile] = workingDoc;
  if (wrote.revision != null) annotationRevisions[currentFile] = wrote.revision;
  if (!refreshManifestFromLocalState(currentFile)) markManifestDirty(currentFile);
  applySidecarHighlights();
  if (activeTab === 'highlights') buildHighlights();
  if (successToast) showToast(successToast);
  return { ok: true, prevHighlights };
}

async function addSidecarHighlightForSelection(action, range, startBlock, endBlock) {
  const excerpt = (HighlightShared.normalizeWhitespace
    ? HighlightShared.normalizeWhitespace(range.toString())
    : range.toString().replace(/[ \t\r\n]+/g, ' ').trim()) || 'Selection';
  const entry = {
    id: makeSidecarId(),
    file: currentFile,
    color: action,
    backend: 'sidecar',
    revision: fileRevisions[currentFile] || null,
    excerpt,
    segments: sidecarSegmentsFromRange(range, startBlock, endBlock),
    updatedAt: Date.now(),
  };
  const result = await updateSidecarDoc((highlights) => {
    highlights.push(entry);
  }, 'Sidecar highlight saved');
  if (!result.ok) return false;
  pushUndo({
    file: currentFile,
    source: null,
    revision: annotationRevisions[currentFile] || null,
    backend: 'sidecar',
    previousHighlights: result.prevHighlights,
  });
  return true;
}

async function recolorSidecarHighlight(id, newColor) {
  const result = await updateSidecarDoc((highlights) => {
    const hit = highlights.find((h) => h.id === id);
    if (hit) { hit.color = newColor; hit.updatedAt = Date.now(); }
  }, `Color changed to ${newColor}`);
  if (!result.ok) return false;
  pushUndo({
    file: currentFile,
    source: null,
    revision: annotationRevisions[currentFile] || null,
    backend: 'sidecar',
    previousHighlights: result.prevHighlights,
  });
  return true;
}

async function clearSidecarHighlight(id) {
  const result = await updateSidecarDoc((highlights) => {
    const hit = highlights.find((h) => h.id === id);
    if (hit) { hit.deleted = true; hit.updatedAt = Date.now(); }
  }, 'Highlight removed');
  if (!result.ok) return false;
  pushUndo({
    file: currentFile,
    source: null,
    revision: annotationRevisions[currentFile] || null,
    backend: 'sidecar',
    previousHighlights: result.prevHighlights,
  });
  return true;
}

// ── Direct mark-clear (fast path for click-on-mark + ✕) ─────────
// Primary path: uses findInlineEntryAtMark (DOM-position-ratio manifest lookup)
// to locate the manifest entry by source position, then calls
// cascadeDeleteHighlight to strip the ==color:text== markers (and the note ref
// + def if a note is attached), preserving inner text.
//
// Fallback path (regex pipeline): only reached when the manifest lookup
// returns null (stale manifest on rare race conditions).  Handles STRONG, EM,
// CODE in addition to MARK — those element types do not go through the
// manifest path because the manifest only tracks inline highlights.

async function clearMarkEl(markEl) {
  if (markEl.tagName === 'MARK') {
    // ── Fast path: source-position-direct strip via manifest lookup ──────────
    // findInlineEntryAtMark uses DOM-position-ratio ↔ source-position-ratio
    // mapping, so it succeeds even for marks whose source contains KaTeX,
    // **bold**, *italic*, `code`, or links — where the old textContent comparison
    // and the regex pipeline both fail.
    //
    // cascadeDeleteHighlight is used for ALL inline marks (not just noted ones)
    // because it correctly handles both cases:
    //   • noted highlight (noteId != null): strips ==color:text==, ref, and def.
    //   • plain highlight (noteId == null): strips ==color:text==, preserves inner text.
    // This is a unified path with defense-in-depth: the regex fallback below
    // is only reached when the manifest lookup returns null (stale manifest on
    // rare race conditions).
    const directEntry = findInlineEntryAtMark(markEl);
    if (directEntry && typeof directEntry.sourceStart === 'number'
        && typeof directEntry.sourceEnd === 'number') {
      const file   = currentFile;
      const source = fileContents[file];
      if (typeof source !== 'string') { hideToolbar(); return; }
      let newSource;
      try {
        newSource = window.ViewerNoteMutation.cascadeDeleteHighlight(source, directEntry);
      } catch (err) {
        showToast('Clear failed: ' + (err.message || 'unknown'));
        hideToolbar(); return;
      }
      const wrote = await putMarkdownSource(file, newSource, fileRevisions[file] || null);
      if (!wrote.ok) {
        if (wrote.conflict) {
          showToast('Write conflict: document changed, reload and retry');
          await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
        } else {
          showToast('Clear failed: ' + (wrote.error || wrote.status || 'write error'));
        }
        hideToolbar(); return;
      }
      pushUndo({ file, source, revision: wrote.revision, backend: 'inline' });
      applyLocalSourceUpdate(file, newSource, wrote.revision);
      showUndoToast(directEntry.noteId != null ? 'Highlight + note cleared' : 'Style removed');
      hideToolbar();
      const sel = window.getSelection();
      if (sel) sel.removeAllRanges();
      return;
    }
    // directEntry is null — manifest may be momentarily stale.
    // Fall through to the regex pipeline as a defense-in-depth fallback.
  }

  let markText = markEl.textContent.trim();
  if (!markText) { hideToolbar(); return; }

  const blockEl = blockOf(markEl);
  if (!blockEl) { showToast('Cannot identify source block'); hideToolbar(); return; }

  let source;
  let sourceRevision = fileRevisions[currentFile] || null;
  try {
    const got = await backend.getMarkdown(currentFile);
    source = got.text;
    sourceRevision = got.revision;
    if (sourceRevision) fileRevisions[currentFile] = sourceRevision;
  } catch (err) {
    showToast(`Failed to read file: ${err.message}`);
    hideToolbar(); return;
  }

  const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
  const srcLines     = source.split('\n');
  const nextEl       = nextBlockSibling(blockEl);
  const nextSrcLine  = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
  const bso          = lineStartOffset(source, blockSrcLine);
  const blockSrc     = srcLines.slice(blockSrcLine, nextSrcLine).join('\n');

  // Disambiguate multiple occurrences via DOM position ratio
  const domPreText = textBeforeNode(markEl, blockEl);
  const domRatio   = blockEl.textContent.length ? domPreText.length / blockEl.textContent.length : 0;

  // If the mark contains inline math, reconstruct the source-level text.
  // markEl.textContent strips $...$, so walk child nodes and substitute each
  // top-level .katex element with its matching $...$ formula from blockSrc.
  //
  // Sequential-walk fix: the Nth .katex in DOM order maps to the Nth $math$
  // in source order (after the mark's approximate start position).  The old
  // per-element arg-min approach collapsed to the same $math$ for two adjacent
  // KaTeX spans because their domRatios were nearly equal.
  if (markEl.querySelector('.katex')) {
    const allMath = [...blockSrc.matchAll(/\$[^$\n]+?\$/g)];
    // Approximate the mark's start in the block source via DOM-position-ratio,
    // with 0.05 of slack to absorb ratio rounding.
    const blockText = blockEl.textContent || '';
    const markStartDomRatio = textBeforeNode(markEl, blockEl).length / Math.max(blockText.length, 1);
    let mathIdx = 0;
    while (mathIdx < allMath.length
      && allMath[mathIdx].index / blockSrc.length < markStartDomRatio - 0.05) {
      mathIdx++;
    }
    let srcText = '';
    for (const child of markEl.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        srcText += child.textContent;
      } else {
        const topKatex = child.classList && child.classList.contains('katex') ? child
          : (child.querySelector ? child.querySelector('.katex:not(.katex .katex)') : null);
        if (topKatex && mathIdx < allMath.length) {
          srcText += allMath[mathIdx][0];
          mathIdx++;
        } else {
          srcText += child.textContent;
        }
      }
    }
    markText = srcText.trim();
  }

  // Normalize whitespace to \s+ so that soft line breaks survive the
  // roundtrip: CRLF source files store \r\n but DOM textContent delivers
  // only \n (markdown-it renders softbreak as \n), so a literal space or
  // newline in escaped would not match \r\n in blockSrc.
  const escaped = markText
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\s+/g, '\\s+');
  const tag     = markEl.tagName;

  // Build ordered list of patterns to try, most specific first
  let patterns;
  if (tag === 'MARK') {
    patterns = [
      new RegExp(`==(${HL_COLOR_ALT}):\\s*${escaped}==`, 'g'),
      new RegExp(`==${escaped}==`, 'g'),
    ];
  } else if (tag === 'STRONG') {
    patterns = [
      new RegExp(`\\*\\*${escaped}\\*\\*`, 'g'),
      new RegExp(`__${escaped}__`, 'g'),
    ];
  } else if (tag === 'EM') {
    // Match *text* or _text_ but NOT **text** / __text__
    patterns = [
      new RegExp(`(?<!\\*)\\*(?!\\*)${escaped}(?<!\\*)\\*(?!\\*)`, 'g'),
      new RegExp(`(?<!_)_(?!_)${escaped}(?<!_)_(?!_)`, 'g'),
    ];
  } else if (tag === 'CODE') {
    patterns = [new RegExp(`\`${escaped}\``, 'g')];
  } else {
    showToast('Cannot remove style for this element type');
    hideToolbar(); return;
  }

  let best = null;
  for (const re of patterns) {
    const hits = [...blockSrc.matchAll(re)];
    if (hits.length > 0) {
      best = hits.reduce((b, m) =>
        Math.abs(m.index / blockSrc.length - domRatio) < Math.abs(b.index / blockSrc.length - domRatio) ? m : b
      );
      break;
    }
  }
  if (!best) {
    showToast('Could not locate style in source');
    hideToolbar(); return;
  }

  // Extract the original source content from the match so that CRLF line
  // endings inside a multi-line annotation are preserved verbatim.
  // markText is built from DOM textContent which only has \n (markdown-it
  // renders softbreak as \n), not the \r\n that may exist in the source.
  // Only MARK annotations can realistically span line breaks; for
  // STRONG/EM/CODE continue using markText as before.
  const srcContent = tag === 'MARK'
    ? best[0].replace(/^==(?:[a-z]+:\s*)?/, '').replace(/==$/, '')
    : markText;
  const newSource = source.slice(0, bso + best.index) + srcContent + source.slice(bso + best.index + best[0].length);

  const wrote = await putMarkdownSource(currentFile, newSource, sourceRevision);
  if (!wrote.ok) {
    if (wrote.conflict) {
      showToast('Write conflict: document changed, reload and retry');
      await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
    } else {
      showToast(`Write failed: ${wrote.status}`);
    }
    hideToolbar();
    return;
  }

  pushUndo({ file: currentFile, source, revision: wrote.revision, backend: 'inline' });
  showUndoToast('Style removed');
  hideToolbar();
  const sel = window.getSelection();
  if (sel) sel.removeAllRanges();
  applyLocalSourceUpdate(currentFile, newSource, wrote.revision);
}

// ── Recolor existing mark (fast path for click-on-mark + swatch) ─
async function recolorMarkEl(markEl, newColor) {
  // ── Fast path: source-offset-direct recolor via manifest lookup ──────────
  // findInlineEntryAtMark resolves via authoritative sourceStart/innerStart,
  // so it succeeds even for marks whose source contains a [link](url),
  // `code`, **bold**, *italic*, $math$, or an absorbed note ref — where the
  // textContent→regex pipeline below cannot relocate the ==color:…== span
  // (it builds the pattern from rendered text, which differs from the raw
  // markdown). Mirrors the fast path clearMarkEl already uses; the regex
  // pipeline remains as a defense-in-depth fallback when the manifest lookup
  // returns null (rare stale-manifest race).
  const directEntry = findInlineEntryAtMark(markEl);
  if (directEntry && typeof directEntry.sourceStart === 'number'
      && typeof directEntry.sourceEnd === 'number') {
    const file   = currentFile;
    const source = fileContents[file];
    if (typeof source === 'string') {
      let newSource;
      try {
        newSource = window.ViewerNoteMutation.recolorHighlight(source, directEntry, newColor);
      } catch (err) {
        showToast('Recolor failed: ' + (err.message || 'unknown'));
        hideToolbar(); return;
      }
      const wrote = await putMarkdownSource(file, newSource, fileRevisions[file] || null);
      if (!wrote.ok) {
        if (wrote.conflict) {
          showToast('Write conflict: document changed, reload and retry');
          await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
        } else {
          showToast(`Write failed: ${wrote.status}`);
        }
        hideToolbar(); return;
      }
      pushUndo({ file, source, revision: wrote.revision, backend: 'inline' });
      showUndoToast(`Color changed to ${newColor}`);
      hideToolbar();
      const sel = window.getSelection();
      if (sel) sel.removeAllRanges();
      applyLocalSourceUpdate(file, newSource, wrote.revision);
      return;
    }
    // source not cached — fall through to the fetch-based regex pipeline.
  }

  // directEntry null — manifest may be momentarily stale. Defense-in-depth:
  let markText = markEl.textContent.trim();
  if (!markText) { hideToolbar(); return; }

  const blockEl = blockOf(markEl);
  if (!blockEl) { showToast('Cannot identify source block'); hideToolbar(); return; }

  let source;
  let sourceRevision = fileRevisions[currentFile] || null;
  try {
    const got = await backend.getMarkdown(currentFile);
    source = got.text;
    sourceRevision = got.revision;
    if (sourceRevision) fileRevisions[currentFile] = sourceRevision;
  } catch (err) {
    showToast(`Failed to read file: ${err.message}`);
    hideToolbar(); return;
  }

  const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
  const srcLines     = source.split('\n');
  const nextEl       = nextBlockSibling(blockEl);
  const nextSrcLine  = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
  const bso          = lineStartOffset(source, blockSrcLine);
  const blockSrc     = srcLines.slice(blockSrcLine, nextSrcLine).join('\n');

  const domPreText = textBeforeNode(markEl, blockEl);
  const domRatio   = blockEl.textContent.length
    ? domPreText.length / blockEl.textContent.length : 0;

  // Inline-math reconstruction — verbatim copy from clearMarkEl
  if (markEl.querySelector('.katex')) {
    const allMath = [...blockSrc.matchAll(/\$[^$\n]+?\$/g)];
    let srcText = '';
    for (const child of markEl.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        srcText += child.textContent;
      } else {
        const topKatex = child.classList && child.classList.contains('katex') ? child
          : (child.querySelector ? child.querySelector('.katex:not(.katex .katex)') : null);
        if (topKatex && allMath.length > 0) {
          const pre = textBeforeNode(topKatex, blockEl);
          const r   = blockEl.textContent.length ? pre.length / blockEl.textContent.length : 0;
          const fm  = allMath.reduce((b, c) =>
            Math.abs(c.index / blockSrc.length - r) <
            Math.abs(b.index / blockSrc.length - r) ? c : b
          );
          srcText += fm[0];
        } else {
          srcText += child.textContent;
        }
      }
    }
    markText = srcText.trim();
  }

  // Normalize whitespace to \s+ so that soft line breaks in the annotation
  // can be matched even when the source has CRLF (\r\n) endings but DOM
  // textContent delivers only \n (markdown-it renders softbreak as \n).
  const escaped = markText
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\s+/g, '\\s+');
  const patterns = [
    new RegExp(`==(${HL_COLOR_ALT}):\\s*${escaped}==`, 'g'),
    new RegExp(`==${escaped}==`, 'g'),
  ];

  let best = null;
  for (const re of patterns) {
    const hits = [...blockSrc.matchAll(re)];
    if (hits.length > 0) {
      best = hits.reduce((b, m) =>
        Math.abs(m.index / blockSrc.length - domRatio) <
        Math.abs(b.index / blockSrc.length - domRatio) ? m : b
      );
      break;
    }
  }
  if (!best) {
    showToast('Could not locate highlight in source');
    hideToolbar(); return;
  }

  // Preserve original source content (including \r\n line endings) by
  // changing only the color label in the matched text rather than rebuilding
  // from markText (which has \n only, not \r\n).
  const replacement = /^==[a-z]+:/.test(best[0])
    ? best[0].replace(/^==[a-z]+:/, `==${newColor}:`)  // replace color label
    : `==${newColor}: ${best[0].slice(2, -2)}`;          // add label to uncolored ==text==
  const newSource = source.slice(0, bso + best.index) +
                    replacement +
                    source.slice(bso + best.index + best[0].length);

  const wrote = await putMarkdownSource(currentFile, newSource, sourceRevision);
  if (!wrote.ok) {
    if (wrote.conflict) {
      showToast('Write conflict: document changed, reload and retry');
      await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
    } else {
      showToast(`Write failed: ${wrote.status}`);
    }
    hideToolbar();
    return;
  }

  pushUndo({ file: currentFile, source, revision: wrote.revision, backend: 'inline' });
  showUndoToast(`Color changed to ${newColor}`);
  hideToolbar();
  const sel = window.getSelection();
  if (sel) sel.removeAllRanges();
  applyLocalSourceUpdate(currentFile, newSource, wrote.revision);
}

// ── Main highlight pipeline ──────────────────────────────────────

async function applyHighlight(action) {
  // Fast path: recolor via sidecar block click
  if (HIGHLIGHT_COLORS.includes(action) && savedSidecarId) {
    const ok = await recolorSidecarHighlight(savedSidecarId, action);
    if (ok) showUndoToast(`Color changed to ${action}`);
    hideToolbar();
    const sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    return;
  }
  // Fast path: clear via sidecar block click
  if (action === 'clear' && savedSidecarId) {
    const ok = await clearSidecarHighlight(savedSidecarId);
    if (ok) showUndoToast('Highlight removed');
    hideToolbar();
    const sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    return;
  }
  // Fast path: recolor via direct mark click
  if (HIGHLIGHT_COLORS.includes(action) && savedMarkEl?.tagName === 'MARK') {
    const curColor = [...savedMarkEl.classList]
      .find(c => c.startsWith('hl-'))
      ?.slice(3) ?? 'yellow';
    if (action === curColor) { hideToolbar(); return; }
    return recolorMarkEl(savedMarkEl, action);
  }
  // Fast path: clear via direct mark click
  if (action === 'clear' && savedMarkEl) return clearMarkEl(savedMarkEl);
  // Step 1 — Use saved range (mousedown on toolbar clears native selection)
  const range = savedRange;
  if (!range) return;
  const selectedText = range.toString();
  if (!selectedText.trim()) { hideToolbar(); return; }

  // Step 2 — Guard
  if (!contentEl.contains(range.commonAncestorContainer)) { hideToolbar(); return; }

  // Step 3 — Classify
  let ancestor = range.commonAncestorContainer;
  if (ancestor.nodeType === Node.TEXT_NODE) ancestor = ancestor.parentElement;

  let type, mathEl, blockEl, startBlock, endBlock;

  if (ancestor.closest('[data-math-block]')) {
    type = 'DISPLAY_MATH';
    mathEl = ancestor.closest('[data-math-block]');
  } else if (ancestor.closest('.katex')) {
    type = 'INLINE_MATH';
    mathEl = ancestor.closest('.katex');
  } else if (ancestor.closest('table')) {
    type = 'SIDECAR';
    startBlock = blockOf(range.startContainer);
    endBlock = blockOf(range.endContainer) || startBlock;
  } else if (ancestor.closest('pre')) {
    type = 'SIDECAR';
    startBlock = blockOf(range.startContainer);
    endBlock = blockOf(range.endContainer) || startBlock;
  } else {
    startBlock = blockOf(range.startContainer);
    endBlock   = blockOf(range.endContainer);
    // Detect whether selection boundary is inside inline math
    const _sc = range.startContainer.nodeType === Node.TEXT_NODE
      ? range.startContainer.parentElement : range.startContainer;
    const _ec = range.endContainer.nodeType === Node.TEXT_NODE
      ? range.endContainer.parentElement : range.endContainer;
    const startKatex = _sc.closest('.katex');
    const endKatex   = _ec.closest('.katex');
    if (!startBlock) { type = 'UNSUPPORTED'; showToast('Cannot identify source block'); }
    else if (startBlock !== endBlock) {
      type = 'SIDECAR';
    } else if (startKatex && !endKatex) {
      // If the selection spans multiple inline-math spans (start inside first
      // katex, but one or more additional katex lie before the plain-text tail),
      // the inline reconstruction in Step 5M only processes the single startKatex
      // and misses intermediate math spans → source text mismatch → toast.
      // Fall back to the robust sidecar backend for the multi-span case.
      const _fragM = range.cloneContents();
      const _nKatexM = _fragM.querySelectorAll('.katex:not(.katex .katex)').length;
      if (_nKatexM > 1) {
        // Start is inside the first inline-math span and the selection covers
        // additional inline-math span(s) before its plain-text end. Step 5M
        // (MIXED_MATH_TEXT) handles only the single start span, but Step 5P
        // (PLAIN_SPANNING_MATH) reconstructs across every spanned math; when
        // the range starts inside the first katex its `plainHead` collapses to
        // '' so `selStart` anchors at that math's source offset. Route there
        // for a precise source-marker highlight instead of the whole-block
        // sidecar fallback (which highlighted the entire paragraph).
        type = 'PLAIN_SPANNING_MATH';
        blockEl = startBlock;
      } else {
        type = 'MIXED_MATH_TEXT';   // math-then-text (one math at start)
        mathEl  = startKatex;
        blockEl = startBlock;
      }
    } else if (!startKatex && endKatex) {
      // If there are additional katex elements before the end, use the spanning handler
      const _frag = range.cloneContents();
      const _nKatex = _frag.querySelectorAll('.katex:not(.katex .katex)').length;
      if (_nKatex > 1) {
        type = 'PLAIN_SPANNING_MATH';
        blockEl = startBlock;
      } else {
        type = 'MIXED_TEXT_MATH';   // text-then-math (simple: one math at end)
        mathEl  = endKatex;
        blockEl = startBlock;
      }
    } else {
      // Both start and end are outside katex — check if any katex is spanned
      const _frag = range.cloneContents();
      if (_frag.querySelector('.katex')) {
        type = 'PLAIN_SPANNING_MATH';
        blockEl = startBlock;
      } else {
        type = 'PLAIN_TEXT';
        blockEl = startBlock;
      }
    }
  }

  if (type === 'UNSUPPORTED') { hideToolbar(); return; }
  if (type === 'SIDECAR') {
    if (!HIGHLIGHT_COLORS.includes(action)) {
      showToast('Only highlight colors are supported for sidecar selections');
      hideToolbar();
      return;
    }
    const ok = await addSidecarHighlightForSelection(action, range, startBlock, endBlock);
    if (!ok) {
      hideToolbar();
      return;
    }
    showUndoToast('Style applied');
    hideToolbar();
    const sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    return;
  }

  // Fetch fresh source to avoid stale cache
  let source;
  let sourceRevision = fileRevisions[currentFile] || null;
  try {
    const got = await backend.getMarkdown(currentFile);
    source = got.text;
    sourceRevision = got.revision;
    if (sourceRevision) fileRevisions[currentFile] = sourceRevision;
  } catch (err) {
    showToast(`Failed to read file: ${err.message}`);
    hideToolbar(); return;
  }

  let selStart, selEnd, selText = selectedText;

  // Step 5A — Display math
  if (type === 'DISPLAY_MATH') {
    const mathBlockIdx = parseInt(mathEl.dataset.mathBlock);
    if (isNaN(mathBlockIdx)) {
      showToast('Could not identify equation \u2014 try reloading');
      hideToolbar(); return;
    }
    // Walk source line-by-line with the SAME rules as `shieldDisplayMath`
    // so the index assigned at render time matches the index recovered
    // here. The shielder recognizes BOTH multi-line `$$\n...\n$$` and
    // single-line `$$...$$` (top-level after trim) — Step 5A must too,
    // or the index drifts and the wrong equation gets wrapped.
    const colorOpen = new RegExp(`^==(${HL_COLOR_ALT}):\\s*\\$\\$$`);
    const singleLineRe = new RegExp(
      `^(?:==(${HL_COLOR_ALT}):\\s*)?\\$\\$([^\\$\\n][\\s\\S]*?)\\$\\$(==)?$`
    );
    const lines = source.split('\n');
    let count = -1, inMath = false, inFence = false;
    let openDollarPos = -1;     // source position of the opening `$$`
    let lineStart = 0;
    let blockStart = -1, blockEnd = -1;
    for (let li = 0; li < lines.length; li++) {
      const line = lines[li];
      const stripped = line.trim();
      if (!inMath && /^(`{3,}|~{3,})/.test(stripped)) {
        inFence = !inFence;
        lineStart += line.length + 1;
        continue;
      }
      if (inFence) {
        lineStart += line.length + 1;
        continue;
      }
      if (!inMath) {
        // Single-line $$...$$ takes precedence (mirrors shielder)
        if (singleLineRe.test(stripped)) {
          count++;
          if (count === mathBlockIdx) {
            blockStart = lineStart + line.indexOf('$$');
            blockEnd   = lineStart + line.lastIndexOf('$$') + 2;
            // Extend over a trailing `==` if present (i.e. `$$...$$==`)
            if (line.endsWith('==')) blockEnd = lineStart + line.length;
            // Pull a leading `==color: ` into the wrap so re-color preserves it
            const colorPrefix = stripped.match(new RegExp(`^==(${HL_COLOR_ALT}):\\s*`));
            if (colorPrefix) {
              blockStart = lineStart + line.indexOf('==');
            }
            break;
          }
          lineStart += line.length + 1;
          continue;
        }
        if (stripped === '$$' || colorOpen.test(stripped)) {
          inMath = true;
          count++;
          openDollarPos = lineStart + line.indexOf('$$');
        }
      } else {
        if (stripped === '$$' || stripped === '$$==') {
          inMath = false;
          if (count === mathBlockIdx) {
            blockStart = openDollarPos;
            blockEnd   = lineStart + line.indexOf('$$') + 2;
            break;
          }
        }
      }
      lineStart += line.length + 1;
    }
    if (blockStart === -1) {
      showToast('Could not locate equation in source');
      hideToolbar(); return;
    }
    selStart = blockStart;
    selEnd   = blockEnd;
    selText  = source.slice(selStart, selEnd);
    showToast('Math equation highlighted as a whole.');
  }

  // Step 5B — Inline math
  if (type === 'INLINE_MATH') {
    blockEl = mathEl.closest('[data-source-line]');
    if (!blockEl) {
      showToast('Cannot identify source block for math');
      hideToolbar(); return;
    }
    const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
    const srcLines = source.split('\n');
    const nextEl = nextBlockSibling(blockEl);
    const nextSrcLine = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
    const blockSrc = srcLines.slice(blockSrcLine, nextSrcLine).join('\n').trimEnd();

    const inlineMathPattern = /\$[^$\n]+?\$/g;
    const candidates = [...blockSrc.matchAll(inlineMathPattern)];
    if (candidates.length === 0) {
      showToast('Could not locate inline math in source');
      hideToolbar(); return;
    }

    const allKatexInBlock = [...blockEl.querySelectorAll('.katex:not(.katex .katex)')];
    const mathOrdinal = allKatexInBlock.indexOf(mathEl);
    const katexSlice = mathOrdinal > 0 ? allKatexInBlock.slice(0, mathOrdinal + 1) : [mathEl];
    const best = resolveInlineMath(katexSlice, candidates, blockSrc, blockEl)[katexSlice.length - 1];

    const bso = lineStartOffset(source, blockSrcLine);
    selStart = bso + best.index;
    selEnd   = selStart + best[0].length;
    selText  = source.slice(selStart, selEnd);
    showToast('Math equation highlighted as a whole.');
  }

  // Step 5M — Mixed inline math + plain text (selection spans both)
  if (type === 'MIXED_MATH_TEXT' || type === 'MIXED_TEXT_MATH') {
    const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
    const srcLines = source.split('\n');
    const nextEl = nextBlockSibling(blockEl);
    const nextSrcLine = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
    const blockSrc = srcLines.slice(blockSrcLine, nextSrcLine).join('\n').trimEnd();
    const bso = lineStartOffset(source, blockSrcLine);

    // Locate the inline math formula using inter-math text anchoring
    const candidates = [...blockSrc.matchAll(/\$[^$\n]+?\$/g)];
    if (candidates.length === 0) {
      showToast('Could not locate inline math in source');
      hideToolbar(); return;
    }
    const allKatexInBlockM = [...blockEl.querySelectorAll('.katex:not(.katex .katex)')];
    const mathOrdinalM = allKatexInBlockM.indexOf(mathEl);
    const katexSliceM = mathOrdinalM > 0 ? allKatexInBlockM.slice(0, mathOrdinalM + 1) : [mathEl];
    const bestMath = resolveInlineMath(katexSliceM, candidates, blockSrc, blockEl)[katexSliceM.length - 1];
    const mathStart = bestMath.index;
    const mathEnd   = bestMath.index + bestMath[0].length;

    if (type === 'MIXED_MATH_TEXT') {
      // Selection starts inside math, ends in plain text after it
      const afterR = document.createRange();
      afterR.setStartAfter(mathEl);
      afterR.setEnd(range.endContainer, range.endOffset);
      const plainTail = afterR.toString().replace(/[ \t\n]+/g, ' ');
      if (!plainTail.trim()) {
        selStart = bso + mathStart;
        selEnd   = bso + mathEnd;
      } else {
        const suffix = blockSrc.slice(mathEnd);
        const { stripped: suffixNorm, map: suffixMap } = stripInlineMarkersWithMap(suffix);
        const hit = suffixNorm.indexOf(plainTail);
        if (hit === -1) {
          showToast('Could not locate selection end in source');
          hideToolbar(); return;
        }
        const endInNorm = hit + plainTail.length;
        const rawTailEnd = endInNorm < suffixMap.length ? suffixMap[endInNorm] : suffix.length;
        selStart = bso + mathStart;
        selEnd   = bso + mathEnd + rawTailEnd;
      }
    } else {
      // MIXED_TEXT_MATH: selection starts in plain text, ends inside math
      const beforeR = document.createRange();
      beforeR.setStart(range.startContainer, range.startOffset);
      beforeR.setEndBefore(mathEl);
      const plainHead = beforeR.toString().replace(/[ \t\n]+/g, ' ');
      if (!plainHead.trim()) {
        selStart = bso + mathStart;
        selEnd   = bso + mathEnd;
      } else {
        const prefix = blockSrc.slice(0, mathStart);
        const { stripped: prefixNorm, map: prefixMap } = stripInlineMarkersWithMap(prefix);
        const hit = prefixNorm.lastIndexOf(plainHead);
        if (hit === -1) {
          showToast('Could not locate selection start in source');
          hideToolbar(); return;
        }
        selStart = bso + prefixMap[hit];
        selEnd   = bso + mathEnd;
      }
    }
    selText = source.slice(selStart, selEnd);
  }

  // Step 5P — Plain text selection spanning one or more inline math elements
  if (type === 'PLAIN_SPANNING_MATH') {
    const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
    const srcLines = source.split('\n');
    const nextEl = nextBlockSibling(blockEl);
    const nextSrcLine = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
    const blockSrc = srcLines.slice(blockSrcLine, nextSrcLine).join('\n').trimEnd();
    const bso = lineStartOffset(source, blockSrcLine);

    // Find all top-level katex elements inside the block that intersect the range
    const katexEls = [...blockEl.querySelectorAll('.katex:not(.katex .katex)')]
      .filter(el => range.intersectsNode(el));
    if (katexEls.length === 0) {
      showToast('Selection contains formatted text \u2014 highlight is not supported here');
      hideToolbar(); return;
    }

    const allMath = [...blockSrc.matchAll(/\$[^$\n]+?\$/g)];
    if (allMath.length === 0) {
      showToast('Could not locate inline math in source');
      hideToolbar(); return;
    }

    // Map each katex element to its source formula using inter-math text
    // anchoring (more robust than raw position ratio when ==color:...==
    // annotations add source chars not present in DOM text).
    const mathPos = resolveInlineMath(katexEls, allMath, blockSrc, blockEl);
    const firstMath  = mathPos[0];
    const lastMath   = mathPos[mathPos.length - 1];
    const lastMathEnd = lastMath.index + lastMath[0].length;

    // Plain text head: from range start to just before first katex
    const firstKatex = katexEls[0];
    const headR = document.createRange();
    headR.setStart(range.startContainer, range.startOffset);
    try { headR.setEndBefore(firstKatex); } catch(_e) {}
    const plainHead = headR.collapsed ? '' : headR.toString().replace(/[ \t\n]+/g, ' ');

    // Plain text tail: from after last katex to range end (skip if end is inside last katex)
    const lastKatex = katexEls[katexEls.length - 1];
    const endInsideLastKatex = lastKatex.contains(range.endContainer);
    let plainTail = '';
    if (!endInsideLastKatex) {
      const tailR = document.createRange();
      try { tailR.setStartAfter(lastKatex); } catch(_e) {}
      tailR.setEnd(range.endContainer, range.endOffset);
      plainTail = tailR.collapsed ? '' : tailR.toString().replace(/[ \t\n]+/g, ' ');
    }

    // Locate selStart. The prefix slice (everything before the first inline
    // math in source) is normalized via stripInlineMarkersWithMap so that
    // HTML comments like `<!-- ref:... -->` and markdown links like
    // `[(9)](#eq-9)` — present in source but not in DOM text — are folded
    // down to the same visible form as `plainHead`.
    if (!plainHead.trim()) {
      selStart = bso + firstMath.index;
    } else {
      const prefix = blockSrc.slice(0, firstMath.index);
      const { stripped: prefixNorm, map: prefixMap } = stripInlineMarkersWithMap(prefix);
      const hit = prefixNorm.lastIndexOf(plainHead);
      if (hit === -1) {
        showToast('Could not locate selection start in source');
        hideToolbar(); return;
      }
      selStart = bso + prefixMap[hit];
    }

    // Locate selEnd. Same normalization on the suffix slice (everything
    // after the last inline math in source).
    if (!plainTail.trim()) {
      selEnd = bso + lastMathEnd;
    } else {
      const suffix = blockSrc.slice(lastMathEnd);
      const { stripped: suffixNorm, map: suffixMap } = stripInlineMarkersWithMap(suffix);
      const hit = suffixNorm.indexOf(plainTail);
      if (hit === -1) {
        showToast('Could not locate selection end in source');
        hideToolbar(); return;
      }
      const endInNorm = hit + plainTail.length;
      const rawTailEnd = endInNorm < suffixMap.length ? suffixMap[endInNorm] : suffix.length;
      selEnd = bso + lastMathEnd + rawTailEnd;
    }

    selText = source.slice(selStart, selEnd);
  }

  // Step 5C — Plain text
  if (type === 'PLAIN_TEXT') {
    const blockSrcLine = parseInt(blockEl.dataset.sourceLine);
    const srcLines = source.split('\n');
    const nextEl = nextBlockSibling(blockEl);
    const nextSrcLine = nextEl ? parseInt(nextEl.dataset.sourceLine) : srcLines.length;
    const blockSrc = srcLines.slice(blockSrcLine, nextSrcLine).join('\n').trimEnd();

    // 5C-i: expand the range to formatting boundaries. If the selection
    // starts inside a `<strong>` / `<em>` / `<code>` / `<del>` / `<s>`
    // span (or ends inside one), wrapping `==color: ...==` around the raw
    // source span would split the open marker from its close (e.g.
    // `**A ==color: B**` leaves `==` unmatched). Extend the range to
    // include the entire formatting span so the wrap is well-formed.
    const pRange = range.cloneRange();
    expandRangeToFormatBoundaries(pRange, blockEl);
    const pSelText = pRange.toString();

    const blockTextContent = blockEl.textContent;
    const domCharOffset = charOffsetWithinElement(
      pRange.startContainer, pRange.startOffset, blockEl
    );
    const domRatio = blockTextContent.length ? domCharOffset / blockTextContent.length : 0;

    // 5C-iii: build a single normalized form of blockSrc that strips
    // inline markers AND collapses whitespace runs to a single space,
    // with a position map back to source offsets. The needle is
    // normalized the same way (collapse whitespace runs).
    const { stripped: blockNorm, map: blockMap } =
      stripInlineMarkersWithMap(blockSrc);
    const selTextN = pSelText.replace(/[ \t\n]+/g, ' ');

    const hits = [];
    {
      let searchFrom = 0;
      while (true) {
        const idx = blockNorm.indexOf(selTextN, searchFrom);
        if (idx === -1) break;
        hits.push(idx);
        searchFrom = idx + 1;
      }
    }

    if (hits.length === 0) {
      showToast('Selection contains formatted text \u2014 highlight is not supported here');
      hideToolbar(); return;
    }

    // 5C-v: disambiguate via DOM ratio.
    const bso = lineStartOffset(source, blockSrcLine);
    const pickClosest = (arr, denom) => arr.reduce((best, h) =>
      Math.abs(h / denom - domRatio) < Math.abs(best / denom - domRatio) ? h : best
    );
    const hitIdx = hits.length === 1 ? hits[0] : pickClosest(hits, blockNorm.length);
    const endInNorm = hitIdx + selTextN.length;   // exclusive
    const rawStart  = blockMap[hitIdx];
    // `rawEnd` is the source position just past the last matched char.
    // If the next normalized char exists, use its source position; otherwise
    // use blockSrc.length.
    const rawEnd = endInNorm < blockMap.length
      ? blockMap[endInNorm]
      : blockSrc.length;
    selStart = bso + rawStart;
    selEnd   = bso + rawEnd;
    // Sweep any leading inline-marker run at selStart into the highlight
    // so the opening emphasis marker stays paired with its closing one.
    const MARKER_SET = '*_`~';
    while (selStart > bso &&
           MARKER_SET.indexOf(source[selStart - 1]) !== -1) {
      selStart--;
    }
    selText = source.slice(selStart, selEnd);
  }

  // Step 6 — Detect and strip existing highlight markers
  const prefix = source.slice(Math.max(0, selStart - 60), selStart);
  const openMatch = prefix.match(new RegExp(`==(${HL_COLOR_ALT}):\\s*$`));
  if (openMatch) {
    const closeIdx = source.indexOf('==', selEnd);
    // Accept any closing == on the same line (no newline between selEnd and ==)
    if (closeIdx !== -1 && !source.slice(selEnd, closeIdx).includes('\n')) {
      selStart = selStart - openMatch[0].length;
      selEnd   = closeIdx + 2;
      let innerText = source.slice(selStart, selEnd);
      innerText = innerText.replace(new RegExp(`^==(${HL_COLOR_ALT}):\\s*`), '').replace(/==$/, '');
      selText = innerText;
    }
  } else {
    // Check plain ==text== markers
    const pfx2 = source.slice(Math.max(0, selStart - 4), selStart);
    if (pfx2.endsWith('==')) {
      const closeIdx = source.indexOf('==', selEnd);
      if (closeIdx !== -1 && !source.slice(selEnd, closeIdx).includes('\n')) {
        selStart = selStart - 2;
        selEnd   = closeIdx + 2;
        let innerText = source.slice(selStart, selEnd);
        innerText = innerText.replace(/^==/, '').replace(/==$/, '');
        selText = innerText;
      }
    }
  }

  // Step 7 — Trim surrounding whitespace so delimiters never abut spaces
  // (markdown-it-mark rejects "== text ==" just like "** text **")
  {
    const lead  = selText.length - selText.trimStart().length;
    const trail = selText.length - selText.trimEnd().length;
    selStart += lead;
    selEnd   -= trail;
    selText   = selText.slice(lead, trail ? -trail : undefined);
  }
  if (!selText) { hideToolbar(); return; }

  // Step 8 — Build markup
  // Guard: applying bold/italic/code to a DISPLAY_MATH selection wraps the
  // multi-line $$...$$  block in markers (e.g. **$$\n...\n$$**), which breaks
  // shieldDisplayMath — it no longer sees a bare `$$` on its own line.
  // Reject these actions early; color highlights and `clear` are still valid.
  if ((action === 'bold' || action === 'italic' || action === 'code') && type === 'DISPLAY_MATH') {
    showToast('Bold/italic/code not supported for equation blocks');
    hideToolbar();
    return;
  }
  const ACTION_MAP = {
    yellow: `==yellow: ${selText}==`,
    green:  `==green: ${selText}==`,
    red:    `==red: ${selText}==`,
    blue:   `==blue: ${selText}==`,
    orange: `==orange: ${selText}==`,
    purple: `==purple: ${selText}==`,
    teal:   `==teal: ${selText}==`,
    pink:   `==pink: ${selText}==`,
    bold:   `**${selText}**`,
    italic: `*${selText}*`,
    code:   `\`${selText}\``,
    clear:  selText,
  };
  const markup = ACTION_MAP[action];
  if (!markup) { hideToolbar(); return; }

  // Step 9 — Assemble new source
  const newSource = source.slice(0, selStart) + markup + source.slice(selEnd);

  // Step 10 — Write to server
  const wrote = await putMarkdownSource(currentFile, newSource, sourceRevision);
  if (!wrote.ok) {
    if (wrote.conflict) {
      showToast('Write conflict: document changed, reload and retry');
      await refreshCurrentFile({ preserveScroll: false, showDiffToast: false });
    } else {
      showToast(`Write failed: ${wrote.status}`);
    }
    hideToolbar();
    return;
  }

  // Step 10 — Dismiss and update cache
  pushUndo({ file: currentFile, source, revision: wrote.revision, backend: 'inline' });
  const label = action === 'clear' ? 'Highlight removed' : 'Style applied';
  showUndoToast(label);
  hideToolbar();
  const sel = window.getSelection();
  if (sel) sel.removeAllRanges();
  applyLocalSourceUpdate(currentFile, newSource, wrote.revision);
}

// ---------------------------------------------------------------------------
// Roving-tabindex tablist keyboard model (WAI-ARIA Tabs)
// ---------------------------------------------------------------------------
// Both tablists — the left sidebar's Files/Outline/Highlights (#sidebar-tabs)
// and the right context column's Outline/Marks/Peek (#rp-segs) — are
// role="tablist" with role="tab" children, so they MUST implement the roving
// tabindex + arrow-key model: exactly one tab is in the Tab order (tabindex=0,
// the selected one), the rest are tabindex=-1; Arrow keys (and Home/End) move
// selection + focus + activate, with wrap-around (review w9d47hl9a #4). Click
// behaviour is unchanged — both wirings still go through their activate fn.
//
// The two tablists differ in their selected-tab marker and activate path:
//   #sidebar-tabs → .active class, dataset.tab, activated via switchTab()
//   #rp-segs      → .active + aria-selected, dataset.seg, via setRightPaneSeg()
// so wireRovingTablist takes a per-tablist `activate(tabEl)` callback (the
// existing switch fn) and reads the selected tab off the shared `.active`
// class. syncRovingTabindex() is called by switchTab/setRightPaneSeg after they
// flip .active so the roving tabindex tracks the selected tab regardless of who
// triggered the change (click, keyboard, or a programmatic switch).
function syncRovingTabindex(tablistEl) {
  if (!tablistEl) return;
  tablistEl.querySelectorAll('[role="tab"]').forEach((t) => {
    t.tabIndex = t.classList.contains('active') ? 0 : -1;
  });
}

function wireRovingTablist(tablistEl, activate) {
  if (!tablistEl) return;
  const tabs = () => Array.from(tablistEl.querySelectorAll('[role="tab"]'));
  syncRovingTabindex(tablistEl);
  tablistEl.addEventListener('keydown', (e) => {
    const list = tabs();
    if (!list.length) return;
    let idx = list.indexOf(document.activeElement);
    if (idx < 0) idx = list.findIndex((t) => t.classList.contains('active'));
    if (idx < 0) idx = 0;
    let next = null;
    switch (e.key) {
      case 'ArrowRight': case 'ArrowDown': next = (idx + 1) % list.length; break;
      case 'ArrowLeft':  case 'ArrowUp':   next = (idx - 1 + list.length) % list.length; break;
      case 'Home': next = 0; break;
      case 'End':  next = list.length - 1; break;
      default: return;   // leave Tab / Enter / Space / typing alone
    }
    e.preventDefault();
    const target = list[next];
    activate(target);        // flips .active (+ syncRovingTabindex via the caller)
    target.focus();          // roving focus follows selection (WAI-ARIA Tabs)
  });
}

// ---------------------------------------------------------------------------
// Sidebar tabs
// ---------------------------------------------------------------------------
document.querySelectorAll('.sidebar-tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});
wireRovingTablist(document.getElementById('sidebar-tabs'), (tab) => switchTab(tab.dataset.tab));

function switchTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.sidebar-tab').forEach(t => {
    const on = t.dataset.tab === tabName;
    t.classList.toggle('active', on);
    if (t.hasAttribute('role')) t.setAttribute('aria-selected', String(on));
  });
  syncRovingTabindex(document.getElementById('sidebar-tabs'));
  fileListEl.classList.toggle('tab-hidden', tabName !== 'files');
  outlineEl.classList.toggle('tab-hidden', tabName !== 'outline');
  highlightsEl.classList.toggle('tab-hidden', tabName !== 'highlights');
  if (tabName === 'outline') buildOutline();
  if (tabName === 'highlights') buildHighlights();
  // Search scope follows the active tab (see getSearchScope). When the user
  // switches tabs with a query already typed, re-run so the results match
  // the new scope.
  if (searchInput.value.trim().length >= 2) doSearch();
  syncMobileActiveSlot();                              // pill follows the active pane (mobile-bar T5)
}

// ---------------------------------------------------------------------------
// Highlights tab
// ---------------------------------------------------------------------------
const hlFilters = new Set(HIGHLIGHT_COLORS);
let cachedHits = [];

async function refreshManifestFile(file) {
  const data = await backend.getManifest(file);
  if (!data) return false;
  manifestByFile.set(file, data.entries);
  manifestDirtyFiles.delete(file);
  return true;
}

async function loadManifestFull() {
  const data = await backend.getManifest();
  if (!data) return false;
  const next = new Map();
  for (const entry of data.entries) {
    const list = next.get(entry.file) || [];
    list.push(entry);
    next.set(entry.file, list);
  }
  manifestByFile = next;
  manifestDirtyFiles.clear();
  manifestNeedsFullRefresh = false;
  return true;
}

async function loadManifest(force = false) {
  if (force || manifestNeedsFullRefresh || manifestByFile.size === 0) {
    return loadManifestFull();
  }
  // Drop cache entries for files that have disappeared from fileList.
  for (const known of [...manifestByFile.keys()]) {
    if (!fileList.includes(known)) {
      manifestByFile.delete(known);
      manifestDirtyFiles.delete(known);
    }
  }
  // Files needing refresh = explicitly dirty + any new files missing from cache.
  const toRefresh = new Set(manifestDirtyFiles);
  for (const f of fileList) {
    if (!manifestByFile.has(f)) toRefresh.add(f);
  }
  if (toRefresh.size === 0) return true;
  // If many files are stale, a single corpus fetch is cheaper than N per-file
  // fetches. The half-of-corpus threshold preserves the previous heuristic.
  const threshold = Math.max(1, Math.floor(fileList.length / 2));
  if (toRefresh.size > threshold) {
    return loadManifestFull();
  }
  const results = await Promise.all([...toRefresh].map((f) => refreshManifestFile(f)));
  if (results.every((ok) => ok)) {
    for (const f of toRefresh) manifestDirtyFiles.delete(f);
    return true;
  }
  // A per-file fetch failed; fall back to a full refresh to recover.
  return loadManifestFull();
}

async function buildHighlights() {
  // Preserve pane scroll across bursty rebuilds. Multiple callers
  // (renderToContent, applySidecarHighlights, WS change) can invoke this
  // back-to-back. The first caller stashes the live scrollTop; subsequent
  // callers reuse the stashed value so the wipe-and-rebuild sequence
  // doesn't lose the user's position.
  const mySeq = ++buildHighlightsSeq;
  if (pendingHighlightsScroll === null) pendingHighlightsScroll = highlightsEl.scrollTop;
  highlightsEl.innerHTML = '';
  await loadManifest();
  if (mySeq !== buildHighlightsSeq) return; // superseded by a later call

  // Scope to the active folder (same rule as the outline).
  const activeFolder = currentFile ? folderOf2(currentFile) : null;
  const scope = currentFile ? getScope(activeFolder, 'highlights') : 'folder';

  // Toggle is appended first so it stays above the filter bar and entries.
  if (currentFile) highlightsEl.appendChild(renderScopeToggle('highlights'));

  // Precompute fileList position for a stable chapter-order sort.
  const fileOrder = new Map();
  fileList.forEach((f, i) => fileOrder.set(f, i));

  cachedHits = [...manifestByFile.values()].flat();
  if (scope === 'file') {
    cachedHits = cachedHits.filter(h => h.file === currentFile);
  } else if (activeFolder != null) {
    cachedHits = cachedHits.filter(h => folderOf2(h.file) === activeFolder);
  }
  cachedHits.sort((a, b) => {
    if (a.file !== b.file) {
      const ia = fileOrder.has(a.file) ? fileOrder.get(a.file) : Number.MAX_SAFE_INTEGER;
      const ib = fileOrder.has(b.file) ? fileOrder.get(b.file) : Number.MAX_SAFE_INTEGER;
      if (ia !== ib) return ia - ib;
      return a.file.localeCompare(b.file);
    }
    const la = Number(a.lineStart || 0);
    const lb = Number(b.lineStart || 0);
    if (la !== lb) return la - lb;
    const sa = Number(a.sourceStart);
    const sb = Number(b.sourceStart);
    if (Number.isFinite(sa) && Number.isFinite(sb) && sa !== sb) return sa - sb;
    return String(a.id || '').localeCompare(String(b.id || ''));
  });

  highlightsEl.appendChild(renderHlFilterBar());
  renderHlEntries(highlightsEl, cachedHits);
  // Restore the stashed pane scroll; clear the stash so the next user
  // scroll is captured fresh on the next rebuild burst.
  highlightsEl.scrollTop = pendingHighlightsScroll || 0;
  pendingHighlightsScroll = null;
}

function renderHlFilterBar() {
  const bar = document.createElement('div');
  bar.id = 'hl-filter-bar';
  for (const color of HIGHLIGHT_COLORS) {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'hl-chip' + (hlFilters.has(color) ? ' on' : '');
    chip.textContent = color;
    chip.style.backgroundColor = `var(--hl-${color})`;
    chip.dataset.color = color;
    chip.setAttribute('aria-pressed', hlFilters.has(color) ? 'true' : 'false');
    chip.addEventListener('click', () => {
      if (hlFilters.has(color)) hlFilters.delete(color);
      else hlFilters.add(color);
      chip.classList.toggle('on');
      chip.setAttribute('aria-pressed', hlFilters.has(color) ? 'true' : 'false');
      renderHlEntries(highlightsEl, cachedHits);
    });
    bar.appendChild(chip);
  }
  return bar;
}

function escapeCss(value) {
  if (window.CSS && typeof window.CSS.escape === 'function') return window.CSS.escape(value);
  return String(value).replace(/["\\]/g, '\\$&');
}

// Find the block element whose data-source-line is the greatest value
// <= lineStart. data-source-line is set only on block-opening elements,
// so a mid-paragraph highlight never matches lineStart exactly; we need
// to walk up to the enclosing block.
function findEnclosingBlockByLine(lineStart) {
  let best = null;
  let bestLine = -1;
  for (const el of contentEl.querySelectorAll('[data-source-line]')) {
    const l = parseInt(el.dataset.sourceLine, 10);
    if (!Number.isFinite(l)) continue;
    if (l <= lineStart && l > bestLine) { bestLine = l; best = el; }
  }
  return best;
}

function resolveHighlightTarget(hit) {
  if (hit.backend === 'sidecar' && hit.id) {
    const el = contentEl.querySelector(`[data-sidecar-hit-id="${escapeCss(hit.id)}"]`);
    if (el) return el;
  }
  let block = null;
  if (hit.lineStart != null) block = findEnclosingBlockByLine(hit.lineStart);
  if (!block && hit.lineEnd != null) block = findEnclosingBlockByLine(hit.lineEnd);
  if (!block) return null;

  // For inline highlights, prefer the actual <mark> inside the block so
  // the scroll centers on the highlighted phrase rather than the whole
  // paragraph — important for long blocks of math-heavy text.
  if (hit.backend === 'inline' && hit.color) {
    const excerpt = String(hit.excerpt || hit.text || '')
      .replace(/\s+/g, ' ').trim();
    if (excerpt) {
      const needle = excerpt.slice(0, 24);
      for (const m of block.querySelectorAll(`mark.hl-${hit.color}`)) {
        const txt = m.textContent.replace(/\s+/g, ' ').trim();
        if (txt.includes(needle) || needle.includes(txt.slice(0, 16))) {
          return m;
        }
      }
      // Fallback: any mark whose text contains a meaningful head substring.
      for (const m of block.querySelectorAll('mark')) {
        const txt = m.textContent.replace(/\s+/g, ' ').trim();
        if (txt && (txt.includes(needle) || needle.includes(txt.slice(0, 16)))) {
          return m;
        }
      }
    }
  }
  return block;
}

function navigateToHighlight(hit) {
  loadFile(hit.file, null).then(() => {
    // Two-phase scroll: first RAF centers on whatever the DOM looks like
    // right after the innerHTML swap; the 300 ms follow-up re-centers after
    // KaTeX block layout has stabilized (same pattern as renderToContent).
    const tryScroll = () => {
      const target = resolveHighlightTarget(hit);
      if (target) target.scrollIntoView({ block: 'center', behavior: 'auto' });
      return !!target;
    };
    requestAnimationFrame(() => {
      tryScroll();
      setTimeout(tryScroll, 300);
    });
  });
}

function renderHlEntries(container, hits) {
  container.querySelectorAll('.hl-entry, .hl-empty').forEach(el => el.remove());

  const visible = hits.filter(h => hlFilters.has(h.color));
  if (!visible.length) {
    const msg = document.createElement('div');
    msg.className = 'hl-empty';
    msg.textContent = 'No highlights match the active filters.';
    container.appendChild(msg);
    return;
  }

  for (const hit of visible) {
    const entry = document.createElement('button');
    entry.type = 'button';
    entry.className = 'hl-entry';
    entry.setAttribute('aria-label', `Jump to highlight in ${hit.file}`);

    const dot = document.createElement('div');
    dot.className = 'hl-entry-dot';
    dot.style.backgroundColor = `var(--hl-${hit.color})`;

    const body = document.createElement('div');
    body.className = 'hl-entry-body';

    const fileLabel = document.createElement('div');
    fileLabel.className = 'hl-entry-file';
    const lineLabel = Number.isFinite(Number(hit.lineStart)) ? Number(hit.lineStart) + 1 : 1;
    fileLabel.textContent = `${hit.file}:${lineLabel}`;

    const text = document.createElement('div');
    text.className = 'hl-entry-text';
    text.textContent = hit.excerpt || hit.text || '';

    body.appendChild(fileLabel);
    body.appendChild(text);
    entry.appendChild(dot);
    entry.appendChild(body);

    // ── Note icon + collapsible body (inline highlights with a note only) ──
    let noteBodyEl = null;
    let noteIconEl = null;
    if (hit.backend === 'inline' && hit.noteId) {
      entry.classList.add('highlights-entry'); // dual-class: Task 12 CSS rules fire
      entry.classList.add('has-note');
      entry.dataset.noteId = hit.noteId;       // forward-compat for Task 20

      noteIconEl = document.createElement('span');
      noteIconEl.className = 'hl-note-icon';
      noteIconEl.textContent = '✎';
      noteIconEl.title = 'Toggle note body';
      // Place icon between dot (first child) and body.
      entry.insertBefore(noteIconEl, body);

      noteBodyEl = document.createElement('div');
      noteBodyEl.className = 'hl-note-body';
      noteBodyEl.dataset.rendered = '0';
      noteBodyEl.dataset.noteBody = hit.noteBody || '';
      noteBodyEl.dataset.noteHasMath = hit.noteHasMath ? '1' : '0';
      entry.appendChild(noteBodyEl);

      const editBtn = document.createElement('span');
      editBtn.className = 'hl-note-edit';
      editBtn.textContent = '✎ edit';
      editBtn.title = 'Edit note';
      noteBodyEl.appendChild(editBtn);

      const toggle = (e) => {
        if (e.target === editBtn || editBtn.contains(e.target)) return;
        entry.classList.toggle('hl-note-expanded');
        if (entry.classList.contains('hl-note-expanded') && noteBodyEl.dataset.rendered === '0') {
          // Lazy markdown render — md instance already includes texmath for KaTeX.
          const wrapper = document.createElement('div');
          wrapper.className = 'hl-note-body-rendered';
          _slugger = HighlightShared.makeUniqueSlugger();
          wrapper.innerHTML = md.render(noteBodyEl.dataset.noteBody || '');
          noteBodyEl.insertBefore(wrapper, editBtn);
          noteBodyEl.dataset.rendered = '1';
        }
      };

      noteIconEl.addEventListener('click', (e) => {
        e.stopPropagation(); // prevent triggering entry click (navigateToHighlight)
        toggle(e);
      });

      // In ring mode the inline ✎ is hidden; the ringed color dot is the
      // visible marker. Wire it as a click target too so the user can
      // expand/collapse without the icon. Non-ring modes still navigate
      // (the entry's click handler runs as usual).
      dot.addEventListener('click', (e) => {
        if (!document.documentElement.classList.contains('note-marker-ring')) return;
        e.stopPropagation();
        toggle(e);
      });

      noteBodyEl.addEventListener('click', (e) => {
        e.stopPropagation(); // prevent navigateToHighlight when interacting with note body
      });

      editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const rect = entry.getBoundingClientRect();
        showNotePopover(hit, 'edit', rect);
      });
    }

    entry.addEventListener('click', (e) => {
      // Don't navigate when the user clicks the note icon or note body area.
      if (noteIconEl && (e.target === noteIconEl || noteIconEl.contains(e.target))) return;
      if (noteBodyEl && (e.target === noteBodyEl || noteBodyEl.contains(e.target))) return;
      navigateToHighlight(hit);
    });

    container.appendChild(entry);
  }
}

// ---------------------------------------------------------------------------
// Per-pane scope toggle (Folder/File)
// Storage key:  viewer.scope.<folder>.<pane>  →  'folder' | 'file'
// Per-folder, per-pane. Default 'folder' preserves prior behavior.
// ---------------------------------------------------------------------------
function getScope(folder, pane) {
  try {
    const v = localStorage.getItem(`viewer.scope.${folder}.${pane}`);
    return (v === 'file' || v === 'workspace') ? v : 'folder';
  } catch { return 'folder'; }
}

function setScope(folder, pane, value) {
  try { localStorage.setItem(`viewer.scope.${folder}.${pane}`, value); }
  catch { /* private mode / quota — fall through, in-memory only */ }
}

// Builds the segmented control for a pane. Caller appends to the pane element.
// Click handler reads currentFile at click time so the right folder is targeted
// even if the user navigated between renders.
function renderScopeToggle(paneName) {
  const folder = currentFile ? folderOf2(currentFile) : '';
  const current = getScope(folder, paneName);
  const wrap = document.createElement('div');
  wrap.className = 'pane-scope';
  wrap.setAttribute('role', 'group');
  wrap.setAttribute('aria-label', 'Show entries from');

  // 'workspace' (cross-folder, all roots) is offered only for the outline pane
  // in multi-root mode — single-root keeps the Folder/File toggle unchanged.
  const values = (paneName === 'outline' && isMultiRootMode())
    ? ['folder', 'file', 'workspace'] : ['folder', 'file'];
  for (const value of values) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pane-scope-btn';
    btn.dataset.scope = value;
    btn.textContent = value === 'folder' ? 'Folder' : value === 'file' ? 'File' : 'All';
    btn.setAttribute('aria-pressed', current === value ? 'true' : 'false');
    btn.addEventListener('click', () => {
      if (!currentFile) return;
      const f = folderOf2(currentFile);
      if (getScope(f, paneName) === value) return;        // no-op click on pressed
      setScope(f, paneName, value);
      if (paneName === 'outline') buildOutline();
      else if (paneName === 'highlights') buildHighlights();
      // If a search query is active and this pane is the one driving the
      // search scope (i.e. it's the active tab), re-run search so results
      // reflect the new scope without making the user retype.
      if (activeTab === paneName && searchInput.value.trim().length >= 2) doSearch();
    });
    wrap.appendChild(btn);
  }
  return wrap;
}

// ---------------------------------------------------------------------------
// Outline (TOC) — active entry driven by the rAF scroll-sync controller
// ---------------------------------------------------------------------------
// Collapsed sibling-file groups persist per session (the current file is never
// collapsed, so the scroll-spy never targets hidden entries). Keyed by the
// namespaced file id.
// Chapter-number sort (#5, off by default): an optional sibling ordering keyed
// on the filename's leading numeric token so e.g. `2.9-x.md` sorts before
// `2.10-x.md`. Single module-singleton numeric collator. order.json file order
// stays authoritative unless this is toggled on (session-persisted, per pane).
const NUMERIC_COLLATOR = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
function outlineChapterSort() {
  try { return sessionStorage.getItem('viewer.outline.chapterSort') === '1'; } catch { return false; }
}
function setOutlineChapterSort(on) {
  try { sessionStorage.setItem('viewer.outline.chapterSort', on ? '1' : '0'); } catch { /* ignore */ }
}
function renderOutlineSortToggle() {
  const on = outlineChapterSort();
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'outline-sort-toggle';
  btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  btn.title = on ? 'Sorting siblings by chapter number — click for file order' : 'Sort siblings by chapter number';
  btn.setAttribute('aria-label', btn.title);
  btn.textContent = '1·2';
  btn.addEventListener('click', () => { setOutlineChapterSort(!outlineChapterSort()); buildOutline(); });
  return btn;
}

function outlineCollapsedSet() {
  try { return new Set(JSON.parse(sessionStorage.getItem('viewer.outline.collapsed') || '[]')); }
  catch { return new Set(); }
}
function saveOutlineCollapsed(set) {
  try { sessionStorage.setItem('viewer.outline.collapsed', JSON.stringify([...set])); } catch { /* ignore */ }
}
function toggleOutlineFileGroup(group) {
  const file = group.dataset.file;
  const set = outlineCollapsedSet();
  const nowCollapsed = !group.classList.contains('collapsed');
  // Expanding a workspace-scope lazy group builds its headings on demand (#6).
  if (!nowCollapsed) {
    const wrap = group.querySelector('.outline-file-children');
    if (wrap && wrap.dataset.lazy) { buildLazyOutlineGroup(group); }
  }
  group.classList.toggle('collapsed', nowCollapsed);
  const sep = group.querySelector('.outline-file-sep');
  if (sep) sep.setAttribute('aria-expanded', String(!nowCollapsed));
  if (nowCollapsed) set.add(file); else set.delete(file);
  saveOutlineCollapsed(set);
  syncOutlineRovingTabindex();
}

// Build one outline heading entry (click navigates within the current file or
// loads the sibling). Factored so the eager loop and the lazy workspace expand
// share identical entry behavior.
function makeOutlineEntry(file, h, isCurrent) {
  const entry = document.createElement('div');
  entry.className = 'outline-entry';
  entry.dataset.level  = h.level;
  entry.dataset.file   = file;
  entry.dataset.anchor = h.id;
  if (isCurrent) entry.dataset.current = '';
  entry.textContent = h.text;
  entry.setAttribute('role', 'treeitem');
  entry.setAttribute('aria-level', String(h.level));
  entry.addEventListener('click', () => {
    if (entry.dataset.file === currentFile) {
      outlineEl.querySelectorAll('.outline-entry.active').forEach(x => x.classList.remove('active'));
      entry.classList.add('active');
      ssActiveEntry = entry;
      entry.scrollIntoView({ block: 'nearest', behavior: 'auto' });
      updateURL(currentFile, h.id);
      scrollToAnchor(h.id);
      scheduleScrollSync();
    } else {
      loadFile(entry.dataset.file, entry.dataset.anchor);
    }
    maybeCloseDrawer();
  });
  return entry;
}

// Lazily populate a collapsed workspace-scope sibling group on first expand:
// fetch its markdown (bounded — one file, not the whole workspace) and render
// its headings into the (previously empty) children wrapper.
async function buildLazyOutlineGroup(group) {
  const wrap = group.querySelector('.outline-file-children');
  if (!wrap || !wrap.dataset.lazy) return;
  delete wrap.dataset.lazy;                          // claim it (no double-build)
  const file = group.dataset.file;
  if (!fileContents[file]) { try { await fetchFile(file); } catch { /* offline */ } }
  const entries = extractHeadings(fileContents[file] || '');
  if (!entries.length) {
    const empty = document.createElement('div');
    empty.className = 'outline-empty';
    empty.textContent = fileContents[file] ? '(no headings)' : 'Loading…';
    wrap.appendChild(empty);
  } else {
    for (const h of entries) wrap.appendChild(makeOutlineEntry(file, h, false));
  }
  setOutlineTreeAria();        // the freshly-built entries need tree level/posinset
  syncOutlineRovingTabindex();
}

// Roving-tabindex + arrow-key navigation over the outline's tree items (file
// separators + heading entries). One item is tabindex=0, the rest -1; Down/Up
// move through VISIBLE items, Right/Left expand/collapse a file group (or move),
// Home/End jump, Enter/Space activate (click). A tree-like accessible list — not
// full APG TreeView (no aria-setsize/posinset or type-ahead).
function outlineVisibleItems() {
  return Array.from(outlineEl.querySelectorAll('.outline-file-sep, .outline-entry'))
    .filter((el) => el.classList.contains('outline-file-sep') || el.offsetParent !== null);
}
function syncOutlineRovingTabindex() {
  const items = outlineVisibleItems();
  const hasZero = items.some((el) => el.tabIndex === 0);
  items.forEach((el, i) => { el.tabIndex = (!hasZero && i === 0) || el.tabIndex === 0 ? 0 : -1; });
  // Guarantee exactly one tabindex=0.
  if (!items.some((el) => el.tabIndex === 0) && items.length) items[0].tabIndex = 0;
}
// Set the ARIA tree structure: top-level treeitems (group headers, or single-
// file entries) are level 1; entries inside a group are level 2. setsize/posinset
// are computed within each level so a screen reader announces "N of M".
function setOutlineTreeAria() {
  const treeEl = outlineEl.querySelector('.outline-tree');
  if (!treeEl) return;
  const topItems = Array.from(treeEl.children).map((c) =>
    c.classList.contains('outline-file-group') ? c.querySelector(':scope > .outline-file-sep')
      : (c.classList.contains('outline-entry') ? c : null)).filter(Boolean);
  topItems.forEach((el, i) => {
    // aria-level MUST reflect the document's heading depth, not flat tree depth,
    // or a screen reader hears no structure. A file-group header is tree-level 1;
    // a single-file heading keeps its own h1..h6 depth (data-level).
    el.setAttribute('aria-level', el.classList.contains('outline-file-sep') ? '1' : (el.dataset.level || '1'));
    el.setAttribute('aria-posinset', String(i + 1));
    el.setAttribute('aria-setsize', String(topItems.length));
  });
  treeEl.querySelectorAll('.outline-file-group').forEach((grp) => {
    const entries = Array.from(grp.querySelectorAll(':scope > .outline-file-children > .outline-entry'));
    entries.forEach((el, i) => {
      // Headings nest UNDER the level-1 file header → heading depth + 1.
      el.setAttribute('aria-level', String((Number(el.dataset.level) || 1) + 1));
      el.setAttribute('aria-posinset', String(i + 1));
      el.setAttribute('aria-setsize', String(entries.length));
    });
  });
}

function wireOutlineRovingTree() {
  const all = Array.from(outlineEl.querySelectorAll('.outline-file-sep, .outline-entry'));
  all.forEach((el, i) => { el.setAttribute('role', 'treeitem'); el.tabIndex = i === 0 ? 0 : -1; });
  setOutlineTreeAria();
  if (outlineEl.dataset.rovingWired) return;
  outlineEl.dataset.rovingWired = '1';
  outlineEl.addEventListener('keydown', (e) => {
    const items = outlineVisibleItems();
    if (!items.length) return;
    let idx = items.indexOf(document.activeElement);
    if (idx < 0) return;
    const cur = items[idx];
    const isSep = cur.classList.contains('outline-file-sep');
    const group = isSep ? cur.closest('.outline-file-group') : null;
    let next = null;
    switch (e.key) {
      case 'ArrowDown': next = Math.min(idx + 1, items.length - 1); break;
      case 'ArrowUp':   next = Math.max(idx - 1, 0); break;
      case 'Home':      next = 0; break;
      case 'End':       next = items.length - 1; break;
      case 'ArrowRight':
        if (group && group.classList.contains('collapsed')) { e.preventDefault(); toggleOutlineFileGroup(group); return; }
        next = Math.min(idx + 1, items.length - 1); break;
      case 'ArrowLeft':
        // The current file's group is never collapsible (its entries feed the
        // scroll-spy) — mirror the mouse path, which adds no toggle handler to a
        // [data-current] sep. Without this guard ArrowLeft would collapse it.
        if (group && !group.classList.contains('collapsed') && !group.querySelector('.outline-file-sep[data-current]')) {
          e.preventDefault(); toggleOutlineFileGroup(group); return;
        }
        next = Math.max(idx - 1, 0); break;
      case 'Enter': case ' ':
        e.preventDefault(); cur.click(); return;
      default:
        // Type-ahead: a single printable char jumps to the next visible item
        // whose label starts with it (wrapping), the APG first-letter convention.
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
          const ch = e.key.toLowerCase();
          for (let k = 1; k <= items.length; k++) {
            const cand = items[(idx + k) % items.length];
            if ((cand.textContent || '').trim().toLowerCase().startsWith(ch)) {
              e.preventDefault();
              items.forEach((el) => { el.tabIndex = -1; });
              cand.tabIndex = 0;
              cand.focus();
              return;
            }
          }
        }
        return;
    }
    if (next != null) {
      e.preventDefault();
      items.forEach((el) => { el.tabIndex = -1; });
      items[next].tabIndex = 0;
      items[next].focus();
    }
  });
}

function buildOutline() {
  // Preserve pane scroll across bursty rebuilds (same pattern as
  // buildHighlights). First caller stashes the live scrollTop; reuse it
  // until the rebuild completes so the pane doesn't jump.
  if (pendingOutlineScroll === null) pendingOutlineScroll = outlineEl.scrollTop;
  outlineEl.innerHTML = '';
  if (!currentFile) { registerOutlineSpy(null); return; }

  const activeFolder = folderOf2(currentFile);
  const scope = getScope(activeFolder, 'outline');
  let siblings = scope === 'file'
    ? [currentFile]
    : scope === 'workspace'
      ? fileList                                              // cross-folder, all roots (#3)
      : fileList.filter(f => folderOf2(f) === activeFolder);

  // Optional chapter-number sort (#5): reorder siblings by the filename's
  // leading numeric token (file order.json order is otherwise authoritative).
  if (scope !== 'file' && outlineChapterSort()) {
    siblings = [...siblings].sort((a, b) =>
      NUMERIC_COLLATOR.compare(a.slice(a.lastIndexOf('/') + 1), b.slice(b.lastIndexOf('/') + 1)));
  }

  // Toggle is appended first so it stays above any empty-state placeholder.
  outlineEl.appendChild(renderScopeToggle('outline'));
  // The chapter-sort toggle only matters when there is more than one sibling.
  if (siblings.length > 1) outlineEl.appendChild(renderOutlineSortToggle());

  // The tree items live in a dedicated role="tree" container so the (non-tree)
  // scope/sort toggles are not mis-parsed as tree members (APG conformance).
  const tree = document.createElement('div');
  tree.className = 'outline-tree';
  tree.setAttribute('role', 'tree');
  tree.setAttribute('aria-label', 'Document outline');
  outlineEl.appendChild(tree);

  if (!siblings.length) {
    const empty = document.createElement('div');
    empty.className = 'outline-empty';
    empty.textContent = 'No headings';
    outlineEl.appendChild(empty);
    registerOutlineSpy(null);
    return;
  }

  // Kick off lazy prefetch for any sibling whose raw markdown isn't cached
  // yet. Re-enter buildOutline once fetches complete, guarded by a sequence
  // counter so rapid file switches don't stack rebuilds.
  // Workspace scope (#6): do NOT bulk-prefetch all ~hundreds of files — siblings
  // render collapsed + lazy, and a group fetches its own headings on first
  // expand. Folder scope keeps eager prefetch (a survey is tens of files).
  const seq = ++buildOutlineSeq;
  const pending = scope === 'workspace' ? [] : siblings.filter(f => !fileContents[f]);
  if (pending.length) {
    Promise.all(pending.map(f => fetchFile(f).catch(() => {})))
      // Re-enter once the sibling fetches land — but only if the outline is
      // still a live render target. In DOCS the outline lives in #right-pane and
      // is driven by isRightPaneActive(), NOT the sidebar activeTab (which is
      // typically 'files' in docs, the sidebar outline/marks tabs being hidden).
      // Without the isRightPaneActive() arm the folder-scoped sibling outline
      // sticks on 'Loading…' forever (the fetch completes but the rebuild is
      // suppressed). The seq guard still prevents stacking on rapid file switches.
      .then(() => {
        if (seq === buildOutlineSeq && (activeTab === 'outline' || isRightPaneActive())) buildOutline();
      });
  }

  const spyEntries = [];
  const showFileSeps = siblings.length > 1;

  for (const file of siblings) {
    const isCurrent = file === currentFile;

    // Container for this file's entries: a collapsible group when multiple
    // siblings are shown (#2), else the tree directly (single-file = flat).
    let container = tree;
    if (showFileSeps) {
      const group = document.createElement('div');
      group.className = 'outline-file-group';
      group.dataset.file = file;
      const sep = document.createElement('div');
      sep.className = 'outline-file-sep';
      if (isCurrent) sep.dataset.current = '';
      sep.dataset.file = file;
      sep.textContent = file.slice(file.lastIndexOf('/') + 1);
      sep.setAttribute('role', 'treeitem');
      // The current file is never collapsed — its entries feed the scroll-spy,
      // and a display:none entry can't be scrolled-into-view or highlighted.
      // Workspace-scope siblings default collapsed + lazy (#3/#6): only the
      // current file's entries are rendered up front; siblings build on expand.
      const lazy = scope === 'workspace' && !isCurrent;
      const collapsed = !isCurrent && (lazy || outlineCollapsedSet().has(file));
      sep.setAttribute('aria-expanded', String(!collapsed));
      if (collapsed) group.classList.add('collapsed');
      if (!isCurrent) sep.addEventListener('click', () => toggleOutlineFileGroup(group));
      group.appendChild(sep);
      const childWrap = document.createElement('div');
      childWrap.className = 'outline-file-children';
      childWrap.setAttribute('role', 'group');
      if (lazy) childWrap.dataset.lazy = '1';
      group.appendChild(childWrap);
      tree.appendChild(group);
      container = childWrap;
      // Lazy siblings render as a bare collapsed sep; entries build on expand.
      if (lazy) continue;
    }

    // Current file uses the live DOM (authoritative IDs + spy-map targets).
    // Siblings synthesize entries from parsed raw markdown.
    let entries;
    if (isCurrent) {
      entries = Array.from(contentEl.querySelectorAll('h1, h2, h3, h4, h5, h6'))
        .map(h => ({ level: +h.tagName[1], text: h.textContent, id: h.id, el: h }));
    } else {
      const src = fileContents[file] || '';
      entries = extractHeadings(src);
    }

    if (!entries.length) {
      if (showFileSeps && !isCurrent) {
        const empty = document.createElement('div');
        empty.className = 'outline-empty';
        empty.textContent = fileContents[file] ? '(no headings)' : 'Loading…';
        container.appendChild(empty);
      }
      continue;
    }

    for (const h of entries) {
      const entry = makeOutlineEntry(file, h, isCurrent);
      container.appendChild(entry);
      if (isCurrent && h.el) spyEntries.push({ el: entry, heading: h.el });
    }
  }

  // Roving-tabindex + arrow-key tree nav over the rendered seps/entries (#4).
  wireOutlineRovingTree();

  // Deterministic scroll sync: register the current file's heading->entry
  // Map with the rAF controller (replaces the old IntersectionObserver —
  // see plan 2026-05-18 Task 4 / spec §6). Headings are DOM-derived in the
  // controller; this Map only supplies which entry to mark .active.
  registerOutlineSpy(new Map(spyEntries.map((x) => [x.heading, x.el])));

  // Restore the stashed pane scroll; clear the stash so the next rebuild
  // burst captures a fresh live value.
  outlineEl.scrollTop = pendingOutlineScroll || 0;
  pendingOutlineScroll = null;
}

// ---------------------------------------------------------------------------
// Theme + typography helpers (redesign 01)
// ---------------------------------------------------------------------------
// Browser-chrome tint per theme (meta theme-color). Light/sepia use the
// theme accent; dark deliberately uses the panel surface (#1a1d23) — a
// bright accent chrome on a dark page would be garish. The FOUC guard in
// index.html inlines the sepia/dark values (it runs pre-modules); the
// fouc-guard unit test pins them together.
const THEME_COLORS = { light: '#2563EB', sepia: '#8a5a2b', dark: '#1a1d23' };

function applyChrome(state) {
  const ch = (state === 'docs' || state === 'focus') ? state : 'reader';
  document.documentElement.dataset.chrome = ch;
  // Immersive (reader + focus) shares the off-canvas sidebar + rail; docs docks.
  document.documentElement.classList.toggle('immersive', ch !== 'docs');
  // Mode switches must not strand an open overlay or stale chrome state.
  // The close is guarded: unconditional closeDrawer() slammed the mobile
  // drawer shut when the mode radio was tapped inside it (QR finding).
  if (!mqlNarrow.matches && isDrawerOpen()) closeDrawer();
  // A chrome switch from inside the settings sheet must not strand the modal —
  // its opener (#rt-mode) vanishes when the topbar hides in docs/focus (spec R7).
  if (settingsOpen) closeSettings();
  // A chrome switch must not orphan Pane B: the split-open CSS is not chrome-
  // gated, so flipping mode with split open would leave a stale half-screen
  // reference pane pinned over the new chrome. Guarded no-op when not open.
  if (isSplitOpen()) closeSplitPane();
  document.documentElement.classList.remove('reader-chrome-hidden');
  rcLastY = null;
  // Docs docks the sidebar: the toggle's aria must reflect the docked sidebar
  // (redesign 04 — its aria is collapse state, not sheet state).
  syncClassicToggleAria();
  syncChromeControls(ch);
  applyRightPane(ch);
  // Chrome toggles html.immersive — the margin-sidenote gate flips with it
  // (docs has no band; reader/focus may build one if the other gate bits hold).
  applyMarginNotes();
}

// Reparent the live outline + highlights nodes between the sidebar drawer
// (reader/focus) and the Docs right pane (docs). The build functions target
// these nodes by reference, so a move via appendChild keeps them working —
// including the rAF scroll-spy, which clears/sets `.outline-entry.active`
// inside outlineEl regardless of parent. Docs additionally force-builds both
// panels (the right pane is always-on, unlike the sidebar tabs which build
// lazily on switchTab); reader/focus restores the nodes and re-runs switchTab's
// tab-visibility so the drawer tabs render whatever the active tab is.
// The right pane is the panes' home only when it is actually on screen: Docs
// chrome, the ≥1400px wide-desktop breakpoint, and not the mobile shell. In
// every other case the panes belong in the sidebar drawer (reachable via the
// tabs) — reparenting them into a display:none pane would strand them.
function isRightPaneActive() {
  return document.documentElement.dataset.chrome === 'docs'
    && mqlWidePane.matches && !mqlNarrow.matches;
}

function applyRightPane(ch) {
  if (!rightPane || !outlineEl || !highlightsEl) return;
  const paneActive = ch === 'docs' && mqlWidePane.matches && !mqlNarrow.matches;
  if (paneActive) {
    // Move the panes into the right column (idempotent — appendChild is a
    // no-op when the node is already the child).
    if (outlineEl.parentNode !== rpOutline) rpOutline.appendChild(outlineEl);
    if (highlightsEl.parentNode !== rpMarks) rpMarks.appendChild(highlightsEl);
    // In the pane both panels are always live (the .tab-hidden class is owned
    // by the sidebar-tab machinery); clear it so the segment control — not the
    // sidebar tab state — governs visibility.
    outlineEl.classList.remove('tab-hidden');
    highlightsEl.classList.remove('tab-hidden');
    setRightPaneSeg(rightPaneSeg, { silent: true });
    // The right pane is always-on, so populate both regardless of activeTab.
    buildOutline();
    buildHighlights();
  } else {
    // Focus rescue: the .rp-seg tab buttons and #rp-peek controls live directly
    // in #right-pane and are NEVER reparented (only the outline/marks nodes move).
    // When this branch fires (breakpoint cross below 1400px, or a docs→reader/
    // focus chrome switch) the CSS hides #right-pane, so focus sitting on one of
    // those controls would fall to <body>. Move it to a stable visible target
    // first (the matching sidebar tab / toggle / #content), guarded by the same
    // getClientRects visibility probe closeSettings() uses.
    // A media-query-driven display:none fires AFTER the browser has already
    // moved focus off the hidden element to <body> (the mqlWidePane 'change'
    // event runs post-hide). So rescue when focus is STILL in the pane OR when
    // it just fell to <body>/null while the last focus was a right-pane control
    // (tracked by the focusin listener below).
    const activeNowInPane = rightPane && rightPane.contains(document.activeElement);
    const fellToBodyFromPane = rpFocusWasInPane
      && (document.activeElement === document.body || document.activeElement === null);
    if (rightPane && (activeNowInPane || fellToBodyFromPane)) {
      const vis = (el) => !!el && document.body.contains(el) && el.getClientRects().length > 0;
      let target = [
        document.querySelector('.sidebar-tab[data-tab="outline"]'),
        sidebarBtn,
      ].find(vis);
      // Last resort: #content (always visible). A bare <main> is not focusable,
      // so make it programmatically focusable (-1: not in the Tab order).
      if (!target && vis(contentEl)) { contentEl.tabIndex = -1; target = contentEl; }
      if (target) { try { target.focus(); } catch (e) { /* gone */ } }
    }
    rpFocusWasInPane = false;
    // Restore to the sidebar; re-assert the tab-hidden state for the active tab
    // so the drawer shows the right pane (switchTab toggles by reference too).
    if (outlineHome && outlineEl.parentNode !== outlineHome) outlineHome.appendChild(outlineEl);
    if (highlightsHome && highlightsEl.parentNode !== highlightsHome) highlightsHome.appendChild(highlightsEl);
    outlineEl.classList.toggle('tab-hidden', activeTab !== 'outline');
    highlightsEl.classList.toggle('tab-hidden', activeTab !== 'highlights');
  }
}

// Segment control for the Docs right pane: shows exactly one of
// #rp-outline / #rp-marks / #rp-peek and marks the active button. `silent`
// skips a redundant rebuild (applyRightPane already builds on entry).
function setRightPaneSeg(seg, opts) {
  const o = opts || {};
  if (seg !== 'outline' && seg !== 'marks' && seg !== 'peek') seg = 'outline';
  rightPaneSeg = seg;
  rpOutline.classList.toggle('tab-hidden', seg !== 'outline');
  rpMarks.classList.toggle('tab-hidden', seg !== 'marks');
  rpPeek.classList.toggle('tab-hidden', seg !== 'peek');
  document.querySelectorAll('#right-pane .rp-seg').forEach((b) => {
    const on = b.dataset.seg === seg;
    b.classList.toggle('active', on);
    b.setAttribute('aria-selected', String(on));
  });
  syncRovingTabindex(document.getElementById('rp-segs'));
  // Building lazily keeps the inactive panel cheap; the active panel must be
  // current when revealed (a highlight added while Outline was showing, etc.).
  if (!o.silent && isRightPaneActive()) {
    if (seg === 'outline') buildOutline();
    if (seg === 'marks') buildHighlights();
  }
}

document.querySelectorAll('#right-pane .rp-seg').forEach((b) => {
  b.addEventListener('click', () => setRightPaneSeg(b.dataset.seg));
});
wireRovingTablist(document.getElementById('rp-segs'), (tab) => setRightPaneSeg(tab.dataset.seg));

// Keep the immersive-toggle controls in sync with the active chrome state
// (the settings Mode radios). #rt-mode is a one-way "exit immersive → Docs"
// COMMAND button, not a toggle: it is only ever visible in reader/focus chrome
// (the topbar is hidden in docs) and always sends chrome→docs, so a toggle's
// aria-pressed would be permanently 'true' and announce a misleading "pressed"
// state. It carries a command aria-label ("Switch to Docs view") instead and
// has no aria-pressed — nothing to sync here for it (review w9d47hl9a #5).
function syncChromeControls(ch) {
  document.querySelectorAll('input[name="chrome-mode"]').forEach((r) => {
    const want = r.value === ch;
    if (r.checked !== want) r.checked = want;
  });
}

// Resolve a stored theme to the EFFECTIVE theme that paints the page.
// 'auto' tracks the OS via prefers-color-scheme (dark → dark, else light);
// light/sepia/dark resolve to themselves. The inline FOUC guard resolves
// 'auto' the SAME way (matchMedia is synchronously readable in the head
// script), so an auto-on-dark-OS user is stamped data-theme=dark pre-paint
// and never flashes the light baseline; this function keeps the running app
// in sync as the OS preference flips live.
function effectiveTheme(theme) {
  if (theme !== 'auto') return theme;
  return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
    ? 'dark' : 'light';
}

function applyTheme(theme) {
  // data-theme always reflects the EFFECTIVE theme (light/sepia/dark), never
  // the literal 'auto' — CSS keys off the resolved value, the store keeps the
  // user's choice. light removes the attribute (it is the :root baseline).
  const eff = effectiveTheme(theme);
  if (eff === 'light') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = eff;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', THEME_COLORS[eff] || THEME_COLORS.light);
}

// Live system-theme tracking: when the stored theme is 'auto', re-resolve and
// re-paint on every OS light/dark flip. Registered ONCE at module scope (not
// per-change) with the non-deprecated addEventListener; it no-ops unless the
// stored theme is 'auto', so light/sepia/dark users are unaffected.
if (window.matchMedia) {
  const darkMql = window.matchMedia('(prefers-color-scheme: dark)');
  darkMql.addEventListener('change', () => {
    if (settingsStore.get('theme') !== 'auto') return;
    applyTheme('auto');
    rethemeMermaid(effectiveTheme('auto'));
  });
}

// Density preset (spec §8) — ORTHOGONAL to body typography. Toggles exactly
// one html.density-* class; the CSS keys --ui-density-lh / --section-gap off
// it for chrome/nav/outline/marks/code only. The prose --content-lh /
// --font-scale / --measure-ch stay slider-controlled and are never touched.
function applyDensity(d) {
  const dn = (d === 'compact' || d === 'spacious') ? d : 'normal';
  const cl = document.documentElement.classList;
  cl.toggle('density-compact', dn === 'compact');
  cl.toggle('density-normal', dn === 'normal');
  cl.toggle('density-spacious', dn === 'spacious');
}

const SERIF_STACK = "Georgia, 'Iowan Old Style', 'Times New Roman', serif";

function applyTypography(s) {
  const r = document.documentElement.style;
  r.setProperty('--font-scale', String(s.fontScale));
  r.setProperty('--content-lh', String(s.lineHeight));
  r.setProperty('--measure-ch', s.measureCh + 'ch');
  if (s.fontFamily === 'serif') r.setProperty('--content-font', SERIF_STACK);
  else r.removeProperty('--content-font');
}

// Full mermaid init options, mirroring the inline init in index.html so that
// rethemeMermaid() does not silently revert securityLevel / flowchart /
// sequence settings on the first theme toggle.  mermaid 11's initialize()
// resets siteConfig to defaults then merges the caller's object, so passing
// only {startOnLoad, theme} would drop the 'loose' securityLevel and the
// htmlLabels / useMaxWidth flags that the boot init set.
function mermaidInitOptions(theme) {
  return {
    startOnLoad: false,
    securityLevel: 'loose',
    theme: theme === 'dark' ? 'dark' : 'default',
    flowchart: { useMaxWidth: true, htmlLabels: true },
    sequence: { useMaxWidth: true },
  };
}

async function rethemeMermaid(theme) {
  if (!window.mermaid || typeof window.mermaid.initialize !== 'function') return;
  window.mermaid.initialize(mermaidInitOptions(theme));
  const done = Array.from(contentEl.querySelectorAll('div.mermaid[data-processed="true"]'));
  for (const n of done) {
    if (!n.dataset.mermaidSrc) continue;
    // Restore via innerHTML (not textContent) to preserve <br/> elements in
    // labels — mermaid reads innerHTML at render time, so innerHTML round-trip
    // is the correct inverse of the innerHTML capture in renderMermaidDiagrams.
    n.innerHTML = n.dataset.mermaidSrc;
    n.removeAttribute('data-processed');
  }
  if (done.length) await renderMermaidDiagrams();
}

// ---------------------------------------------------------------------------
// Settings panel
// ---------------------------------------------------------------------------
const settingsStore = window.createSettingsStore({ storage: localStorage });

// React to changes from any writer (panel controls, top-bar theme cycle,
// future palette). Registered at module scope, NOT inside loadSettings():
// loadSettings runs after init()'s awaited fetchFileList(), and the top-bar
// controls are interactive before that — a subscriber registered late would
// let an early rt-theme click persist a theme without applying it (QR
// finding). The appliers are pure DOM functions with no init dependency.
settingsStore.subscribe((key, value) => {
  if (key === 'chrome') applyChrome(value);
  if (key === 'theme') {
    applyTheme(value);
    // Mermaid keys off the EFFECTIVE theme (auto → dark/light), not the
    // stored literal — 'auto' must not silently fall through to the light
    // diagram palette when the system is dark.
    rethemeMermaid(effectiveTheme(value));
    // rt-theme (top bar) also writes 'theme' — keep the panel radios in
    // sync (by the STORED value, so the 'auto' radio checks even though
    // data-theme resolved to light/dark), or the stale-checked radio
    // becomes a dead control (no change event fires on an already-checked
    // radio).
    document.querySelectorAll('input[name="theme"]').forEach((r) => {
      r.checked = r.value === value;
    });
  }
  if (key === 'density') applyDensity(value);
  if (key === 'fontScale' || key === 'lineHeight' || key === 'measureCh' || key === 'fontFamily') {
    applyTypography(settingsStore.getAll());
    // Typography changes the prose measure → every anchor's top moves; rebuild
    // the margin-sidenote band so it re-aligns and re-de-collides.
    applyMarginNotes();
  }
  if (key === 'marginNotes') applyMarginNotes();
  if (key === 'figureStyle') applyFigureStyle();
});

function loadSettings() {
  const scrollFx = settingsStore.get('scrollFx');
  const updateFx = settingsStore.get('updateFx');
  document.getElementById('setting-scroll-fx').checked = scrollFx;
  document.getElementById('setting-update-fx').checked = updateFx;
  document.documentElement.classList.toggle('no-scroll-fx', !scrollFx);
  document.documentElement.classList.toggle('no-update-fx', !updateFx);

  // Note marker style: 'icon' (✎ glyph in entry) | 'ring' (outline on color dot)
  const noteMarker = settingsStore.get('noteMarker');
  document.documentElement.classList.toggle('note-marker-icon', noteMarker === 'icon');
  document.documentElement.classList.toggle('note-marker-ring', noteMarker === 'ring');
  document.querySelectorAll('input[name="note-marker"]').forEach((r) => {
    r.checked = r.value === noteMarker;
    r.addEventListener('change', (e) => {
      if (!e.target.checked) return;
      const value = e.target.value === 'ring' ? 'ring' : 'icon';
      settingsStore.set('noteMarker', value);
      document.documentElement.classList.toggle('note-marker-icon', value === 'icon');
      document.documentElement.classList.toggle('note-marker-ring', value === 'ring');
    });
  });

  // Reading progress bar: on/off + mode (mirrors note-marker pattern).
  const rpOn = settingsStore.get('readingProgress');
  document.documentElement.classList.toggle('no-reading-progress', !rpOn);
  const rpCheckbox = document.getElementById('setting-reading-progress');
  if (rpCheckbox) {
    rpCheckbox.checked = rpOn;
    rpCheckbox.addEventListener('change', (e) => {
      const on = !!e.target.checked;
      settingsStore.set('readingProgress', on);
      document.documentElement.classList.toggle('no-reading-progress', !on);
      document.querySelectorAll('input[name="reading-progress-mode"]')
        .forEach((r) => { r.disabled = !on; });
    });
  }
  // Mode persists independently of on/off (last explicit choice wins on re-enable).
  progressMode = settingsStore.get('readingProgressMode') === 'section' ? 'section' : 'whole-doc';
  document.querySelectorAll('input[name="reading-progress-mode"]').forEach((r) => {
    r.checked = r.value === progressMode;
    r.disabled = !rpOn;
    r.addEventListener('change', (e) => {
      if (!e.target.checked) return;
      progressMode = e.target.value === 'section' ? 'section' : 'whole-doc';
      settingsStore.set('readingProgressMode', progressMode === 'section' ? 'section' : 'doc');
      scheduleScrollSync();
    });
  });

  // Citation link mode
  const citationMode = settingsStore.get('citationMode');
  const radios = document.querySelectorAll('input[name="citation-mode"]');
  radios.forEach((r) => { r.checked = r.value === citationMode; });
  radios.forEach((r) => {
    r.addEventListener('change', (e) => {
      if (e.target.checked) {
        settingsStore.set('citationMode', e.target.value);
        if (e.target.value === 'github') {
          fetchGitInfo().then((info) => {
            if (!info || !info.available) {
              showToast('GitHub info unavailable — citations will fall back to relative');
            } else if (info.headPushed === false) {
              showToast('HEAD not pushed — GitHub citations may 404 until you push');
            } else if (info.headPushed == null) {
              showToast('Cannot verify push status — citation URLs may 404');
            }
          });
        }
      }
    });
  });
  if (citationMode === 'github') {
    // Opportunistic probe so the first citation click is instant.
    fetchGitInfo();
  }

  // Mode (chrome)
  applyChrome(settingsStore.get('chrome'));
  document.querySelectorAll('input[name="chrome-mode"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('chrome');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('chrome', e.target.value); });
  });

  // Margin notes (T7) — opt-in Tufte sidenotes; the store subscriber's
  // applyMarginNotes() builds/tears down the band on change (and the gate
  // re-check covers immersive-state / width). The checkbox just writes the pref.
  const mnCheckbox = document.getElementById('setting-margin-notes');
  if (mnCheckbox) {
    mnCheckbox.checked = !!settingsStore.get('marginNotes');
    mnCheckbox.addEventListener('change', (e) => settingsStore.set('marginNotes', !!e.target.checked));
  }

  // Theme (light|sepia|dark|auto — auto tracks prefers-color-scheme).
  applyTheme(settingsStore.get('theme'));
  document.querySelectorAll('input[name="theme"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('theme');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('theme', e.target.value); });
  });

  // Density preset (chrome/nav only — orthogonal to the typography sliders).
  applyDensity(settingsStore.get('density'));
  document.querySelectorAll('input[name="density-mode"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('density');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('density', e.target.value); });
  });

  // Typography
  applyTypography(settingsStore.getAll());
  const bindRange = (id, key, parse) => {
    const el = document.getElementById(id);
    el.value = String(settingsStore.get(key));
    el.addEventListener('input', () => settingsStore.set(key, parse(el.value)));
  };
  bindRange('setting-font-scale', 'fontScale', parseFloat);
  bindRange('setting-line-height', 'lineHeight', parseFloat);
  bindRange('setting-measure-ch', 'measureCh', (v) => parseInt(v, 10));
  document.querySelectorAll('input[name="content-font"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('fontFamily');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('fontFamily', e.target.value); });
  });

  // Figure style (spec-driven figures) — radios mirror the inline figure chip
  // and the palette commands; the store subscriber's applyFigureStyle()
  // re-renders any enhanced figure in place on change.
  document.querySelectorAll('input[name="figure-style"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('figureStyle');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('figureStyle', e.target.value); });
  });
  // (Store subscriber lives at module scope, right after settingsStore — see
  // the comment there.)
}

// ── Settings sheet (settings-isolation) ──────────────────────────────────────
// A self-contained top-level modal — sibling of #cmd-palette / #peek-popover —
// fully decoupled from the #sidebar tab container. All four entries (the docked
// gear, #rt-aa, the mobile 'aa' slot, the palette command) call openSettings();
// the sheet inerts the background and owns the keyboard (Esc / outside-tap /
// close-button dismiss). Mirrors the command palette (openPalette below); mobile
// renders it as a bottom sheet, desktop as a centred modal (CSS). The settings
// CONTROLS are unchanged — they keep their ids, so loadSettings + the store
// subscriber wire them exactly as before, wherever the markup now lives.
let settingsReturnFocus = null;
function settingsSetBackgroundInert(on) {
  if (!appEl) return;
  Array.from(appEl.children).forEach((c) => {
    if (c === settingsSheet) return;
    if (on) c.setAttribute('inert', ''); else c.removeAttribute('inert');
  });
}
function setSettingsExpanded(expanded) {
  document.querySelectorAll('#settings-btn, #rt-aa, #mobile-toolbar [data-mt="aa"]').forEach((b) =>
    b.setAttribute('aria-expanded', String(expanded)));
}
function openSettings() {
  if (settingsOpen || !settingsSheet) return;
  hidePeek();                                   // settings supersedes any peek…
  closePalette();                               // …and any open palette (one modal at a time)
  settingsOpen = true;
  settingsReturnFocus = document.activeElement;
  settingsSetBackgroundInert(true);
  settingsSheet.hidden = false;
  setSettingsExpanded(true);
  syncMobileActiveSlot();                        // light the mobile 'aa' slot
  const first = settingsSheet.querySelector('input, button, [tabindex]');
  if (first) { try { first.focus(); } catch (e) { /* none focusable */ } }
}
function closeSettings() {
  if (!settingsOpen) return;
  settingsOpen = false;
  settingsSheet.hidden = true;
  settingsSetBackgroundInert(false);
  setSettingsExpanded(false);
  syncMobileActiveSlot();                        // clear the 'aa' slot
  // Restore focus to the opener — but only if it is still visible. An in-sheet
  // layout switch (reader→classic) hides #reader-topbar, so a saved #rt-aa would
  // be display:none; document.body.contains() stays true and focus() then
  // silently no-ops to <body>, stranding the keyboard user at the top of the
  // document. getClientRects() is empty for display:none yet non-empty for a
  // visible position:fixed element (where offsetParent is null), so it is the
  // robust visibility probe. Fall back to a still-visible settings entry (the
  // docked gear, which survives the layout switch) when the opener was hidden.
  const visible = (el) => !!el && document.body.contains(el) && el.getClientRects().length > 0;
  const refocus = visible(settingsReturnFocus)
    ? settingsReturnFocus
    : [settingsBtn, document.getElementById('rt-aa')].find(visible) || null;
  if (refocus) { try { refocus.focus(); } catch (e) { /* element gone */ } }
  settingsReturnFocus = null;
}
if (settingsSheet) {
  // Dim-area click (outside the box) dismisses; clicks on the box do not.
  settingsSheet.addEventListener('click', (e) => { if (e.target === settingsSheet) closeSettings(); });
  document.getElementById('settings-close')?.addEventListener('click', () => closeSettings());
}

settingsBtn.addEventListener('click', () => {
  settingsOpen ? closeSettings() : openSettings();
});

// ── Reader top bar (redesign 02 T3) ──────────────────────────────────
const THEME_CYCLE = ['light', 'sepia', 'dark'];
// Advance the theme cycle deterministically. 'auto' is NOT in the ring, so a
// raw indexOf('auto') would be -1 and (-1+1)%3 = 0 → silently resets to light,
// the opposite of what an auto-on-dark user sees and losing the auto choice
// without warning. Instead, cycle from the EFFECTIVE theme (what the user
// actually sees), so cycling from auto advances to the next visible theme.
function nextThemeInCycle(cur) {
  const start = THEME_CYCLE.includes(cur) ? cur : effectiveTheme(cur);
  const idx = THEME_CYCLE.indexOf(start);
  return THEME_CYCLE[((idx < 0 ? 0 : idx) + 1) % THEME_CYCLE.length];
}
document.getElementById('rt-theme')?.addEventListener('click', () => {
  settingsStore.set('theme', nextThemeInCycle(settingsStore.get('theme')));
});
document.getElementById('rt-aa')?.addEventListener('click', () => openSettings());
document.getElementById('rt-mode')?.addEventListener('click', () => {
  // Exit immersion to the non-immersive Docs three-zone view.
  settingsStore.set('chrome', 'docs');
});

// ── Reader bottom pill (redesign 02 T4) ──────────────────────────────
document.querySelectorAll('#reader-pill [data-pill]').forEach((b) => {
  b.addEventListener('click', () => { switchTab(b.dataset.pill); openDrawer(); });
});

// ── Mobile bottom toolbar (redesign 03 T1) ───────────────────────────
// The five slots reuse the existing sheet machinery: files/outline/
// highlights switch the pane then open; search opens then focuses the
// (always-visible) search box; Aa mirrors rt-aa. The hamburger is retired
// at ≤768px (display:none) — this toolbar is the only opener there.
document.querySelectorAll('#mobile-toolbar [data-mt]').forEach((b) => {
  b.addEventListener('click', () => {
    const slot = b.dataset.mt;
    if (slot === 'search') {
      openPalette();                                 // command palette = the mobile search entry (mobile-bar T2)
      return;                                         // transient modal — no bar pill
    }
    if (slot === 'aa') {
      openSettings();                                  // settings is its own sheet now
    } else {
      switchTab(slot);                                 // (also syncs the pill)
      openDrawer();
    }
  });
});

// ---------------------------------------------------------------------------
// Command palette (redesign 05) — top-level modal, Cmd/Ctrl+K
// ---------------------------------------------------------------------------
// A self-contained modal at z 1200 (CSS), independent of the sidebar drawer so
// it sidesteps the sidebar's visibility:hidden / backdrop focus traps. Actions
// reuse existing module-scope seams (loadFile, scrollToAnchor, settingsStore,
// copyCitation, doSearch, backend). Ctrl/Cmd+K opens it (rebound below).
const palRoot    = document.getElementById('cmd-palette');
const palInput   = document.getElementById('cmd-input');
const palResults = document.getElementById('cmd-results');
let paletteOpen  = false;
let palItems     = [];
let palSel       = 0;
let palReturnFocus = null;

// Make everything behind the modal inert (no focus, no pointer, hidden from
// assistive tech) while the palette is open. The palette lives inside #app, so
// inert its siblings only — not #app itself. Review weqs70hun (a11y).
function palSetBackgroundInert(on) {
  if (!appEl) return;
  Array.from(appEl.children).forEach((c) => {
    if (c === palRoot) return;
    if (on) c.setAttribute('inert', '');
    else c.removeAttribute('inert');
  });
}
function openPalette() {
  // Hard-fail safe: if the ranker module did not load, the palette would throw
  // on first keystroke — leave Ctrl+K a no-op rather than a broken modal.
  if (paletteOpen || !palRoot || !window.PaletteRank) return;
  hidePeek();                                  // palette supersedes any open peek
  if (settingsOpen) closeSettings();           // …and the settings sheet (one modal at a time)
  paletteOpen = true;
  palReturnFocus = document.activeElement;
  palSetBackgroundInert(true);
  palRoot.hidden = false;
  palInput.value = '';
  palRebuild();
  palInput.focus();
}
function closePalette() {
  if (!paletteOpen) return;
  paletteOpen = false;
  palRoot.hidden = true;
  palSetBackgroundInert(false);
  palInput.value = '';
  palResults.innerHTML = '';
  palItems = [];
  if (palReturnFocus && document.body.contains(palReturnFocus)) {
    try { palReturnFocus.focus(); } catch (e) { /* element gone */ }
  }
  palReturnFocus = null;
}

// Mode is selected by input prefix: '>' commands, '#' cross-ref index
// (headings + equations + references), '?' keyboard cheat-sheet, else files.
function palParseMode(raw) {
  const s = raw || '';
  if (s.startsWith('>')) return { mode: 'command', q: s.slice(1).trim() };
  if (s.startsWith('#')) return { mode: 'index', q: s.slice(1).trim() };
  if (s.startsWith('?')) return { mode: 'shortcuts', q: s.slice(1).trim() };
  return { mode: 'file', q: s.trim() };
}
function palBuildFiles(q) {
  const ranked = window.PaletteRank.rankItems(q, fileList.map((f) => ({ text: f })), { key: 'text', limit: 50 });
  const items = ranked.map((r) => ({
    kind: 'file', label: r.text, positions: r.positions,
    run: () => { closePalette(); loadFile(r.text); },
  }));
  if (q.length >= 2) {                                          // trailing full-text runner (T6)
    items.push({ kind: 'search', label: `Search “${q}” across all files`, hint: 'Enter', positions: [],
      run: () => palRunSearch(q) });
  }
  return items;
}
// The '#' cross-reference index over the CURRENT file: headings, numbered
// equations, and reference-list entries — all extracted from live DOM (real
// rendered ids), so scrollToAnchor jumps without the extractHeadings
// sibling-slugger mismatch. One ranked pool lets a query like '#eq 2' or
// '#shannon' reach an equation or a reference as readily as a heading.
function palIndexEntries() {
  const entries = [];
  // Headings — searchable by their text; carry an H<level> hint.
  contentEl.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach((h) => {
    if (!h.id) return;
    const level = Number(h.tagName[1]);
    entries.push({ text: h.textContent.trim(), id: h.id, kind: 'heading', hint: 'H' + level, level });
  });
  // Numbered equations — the anchor is an empty <a id="eq-N">; the visible
  // label "Eq. (N)" is derived from the id, and "eq N" is appended to the
  // searchable text so a bare number or the word "eq" both match.
  contentEl.querySelectorAll('[id^="eq-"]').forEach((a) => {
    const n = a.id.slice(3);
    entries.push({ text: `Eq. (${n}) eq ${n}`, label: `Eq. (${n})`, id: a.id, kind: 'eq', hint: '⏎' });
  });
  // Reference-list entries — the anchor sits just before the "[N] Author…"
  // text; the parent block's text is the searchable + visible label.
  contentEl.querySelectorAll('[id^="ref-"]').forEach((a) => {
    const n = a.id.slice(4);
    const block = a.closest('p, li, tr') || a.parentElement;
    let txt = (block ? block.textContent : '').trim();
    if (!txt) txt = `[${n}]`;
    else if (!/^\[/.test(txt)) txt = `[${n}] ${txt}`;
    if (txt.length > 90) txt = txt.slice(0, 88) + '…';
    entries.push({ text: txt, id: a.id, kind: 'ref', hint: 'ref' });
  });
  return entries;
}
function palBuildIndex(q) {
  const ranked = window.PaletteRank.rankItems(q, palIndexEntries(), { key: 'text', limit: 60 });
  return ranked.map((r) => ({
    kind: r.kind, label: r.label || r.text, hint: r.hint || '', level: r.level,
    positions: r.label ? [] : r.positions,   // positions index the searchable text; suppress when label differs
    run: () => { closePalette(); scrollToAnchor(r.id); updateURL(currentFile, r.id); },
  }));
}
function palAct(fn) { return () => { closePalette(); fn(); }; }

// Command registry. Each action reuses an existing module-scope seam. Push/pull
// are gated on the cloud backend (absent under local-server, which fixtures use).
//
// Single source of truth for the keyboard map: feeds both the '?' cheat-sheet
// (palBuildShortcuts → openShortcutCheatsheet) and the '>shortcut' reference
// rows in the command list, so the two never drift. [label, keys].
const PALETTE_SHORTCUTS = [
  ['Command palette', 'Ctrl+K'],
  ['Toggle sidebar', 'Ctrl+B'],
  ['Outline', 'Ctrl+Shift+O'],
  ['Highlights', 'Ctrl+Shift+H'],
  ['Highlight selection', 'Ctrl+Shift+L'],
  ['Focus mode (immersive)', 'Ctrl+Shift+F'],
  ['Undo', 'Ctrl+Z'],
];
function paletteCommands() {
  const cloud = !!(typeof backend !== 'undefined' && backend && backend.kind === 'cloud');
  const cmds = [
    { text: 'Toggle theme', run: palAct(() => {
        settingsStore.set('theme', nextThemeInCycle(settingsStore.get('theme')));
      }) },
    { text: 'Theme: Light',  run: palAct(() => settingsStore.set('theme', 'light')) },
    { text: 'Theme: Sepia',  run: palAct(() => settingsStore.set('theme', 'sepia')) },
    { text: 'Theme: Dark',   run: palAct(() => settingsStore.set('theme', 'dark')) },
    // Mode is desktop-only (spec section 6); below the breakpoint chrome is
    // always reader, so omit the toggle on mobile to match the settings panel,
    // which hides the mode radios there. Review weqs70hun.
    // Focus toggle carries the real ⌘⇧F binding hint; the Docs/Reader toggle
    // has no keyboard binding, so it carries none (no fabricated shortcut).
    ...(!mqlNarrow.matches ? [
      { text: 'Toggle immersive (Docs / Reader)', run: palAct(() =>
        settingsStore.set('chrome', settingsStore.get('chrome') === 'docs' ? 'reader' : 'docs')) },
      { text: 'Toggle focus mode (immersive)', hint: '⌘⇧F', run: palAct(() =>
        settingsStore.set('chrome', settingsStore.get('chrome') === 'focus' ? 'reader' : 'focus')) },
      { text: 'Toggle margin notes', run: palAct(() =>
        settingsStore.set('marginNotes', !settingsStore.get('marginNotes'))) },
    ] : []),
    // Split-view (Pane B) — only offered at the ≥1440px gate. Opening shows the
    // section currently at the top of Pane A's viewport in the reference pane;
    // when split is already open the command toggles it closed.
    ...(splitGateActive() ? [
      { text: isSplitOpen() ? 'Close split (reference pane)' : 'Open current section in split',
        run: palAct(() => { isSplitOpen() ? closeSplitPane() : openSplitForCurrentSection(); }) },
    ] : []),
    { text: 'Open settings', run: palAct(() => openSettings()) },
    { text: 'Keyboard shortcuts', hint: '?', run: palAct(() => openShortcutCheatsheet()) },
    { text: 'Copy citation', run: palAct(() => {
        if (savedRange) copyCitation('rich'); else showToast('Select text first');
      }) },
    // Figure render style (mirrors the settings-sheet group + the inline chip).
    ...(window.FigurePipeline ? window.FigurePipeline.STYLES.map((s) => (
      { text: 'Figure style: ' + s.label, run: palAct(() => settingsStore.set('figureStyle', s.id)) }
    )) : []),
  ];
  if (cloud) {
    cmds.push({ text: 'Push annotations to cloud', run: palAct(() => {
      if (backend.flushQueue) backend.flushQueue(); showToast('Pushing annotations…'); }) });
    cmds.push({ text: 'Pull annotations from cloud', run: palAct(() => {
      if (currentFile) { loadFile(currentFile, null, false); showToast('Pulling annotations…'); } }) });
  }
  // Read-only shortcut reference (spec section 4 — palette lists existing
  // shortcuts). run:null rows just close on Enter (palExec handles non-fn run).
  PALETTE_SHORTCUTS.forEach(([text, key]) =>
    cmds.push({ text: 'Shortcut: ' + text, hint: key, run: null }));
  return cmds;
}

// '?' prefix — the keyboard cheat-sheet as palette rows: a leading
// "Keyboard shortcuts" opener (reveals the overlay) plus every binding inline.
function palBuildShortcuts(q) {
  const items = [{ text: 'Keyboard shortcuts', hint: '⏎', run: palAct(() => openShortcutCheatsheet()) }];
  PALETTE_SHORTCUTS.forEach(([text, key]) => items.push({ text, hint: key, run: null }));
  const ranked = window.PaletteRank.rankItems(q, items, { key: 'text', limit: 40 });
  return ranked.map((r) => ({
    kind: 'command', label: r.text, hint: r.hint || '', positions: r.positions, run: r.run,
  }));
}

// Keyboard cheat-sheet — a lightweight top-level modal (sibling of the palette)
// listing every binding from the single PALETTE_SHORTCUTS source. Built lazily
// on first open, owns Esc / backdrop-tap dismiss, and restores focus.
let shortcutSheetEl = null;
let shortcutReturnFocus = null;
function buildShortcutSheet() {
  if (shortcutSheetEl) return shortcutSheetEl;
  const el = document.createElement('div');
  el.id = 'shortcut-cheatsheet';
  el.hidden = true;
  el.setAttribute('role', 'dialog');
  el.setAttribute('aria-modal', 'true');
  el.setAttribute('aria-label', 'Keyboard shortcuts');
  const rows = PALETTE_SHORTCUTS.map(([label, key]) =>
    `<div class="sc-row"><span class="sc-label">${escapeHtml(label)}</span>`
    + `<kbd class="sc-key">${escapeHtml(key)}</kbd></div>`).join('');
  el.innerHTML = `<div id="shortcut-cheatsheet-box">`
    + `<div class="sc-head"><h2 class="sc-title">Keyboard shortcuts</h2>`
    + `<button type="button" class="sc-close" aria-label="Close">&times;</button></div>`
    + `<div class="sc-rows">${rows}</div></div>`;
  (appEl || document.body).appendChild(el);
  el.addEventListener('click', (e) => { if (e.target === el) closeShortcutCheatsheet(); });
  el.querySelector('.sc-close').addEventListener('click', () => closeShortcutCheatsheet());
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeShortcutCheatsheet(); }
  });
  shortcutSheetEl = el;
  return el;
}
// Make everything behind the cheat-sheet inert while it is open. The sheet is
// appended to #app (buildShortcutSheet), so inert its siblings only — mirroring
// settingsSetBackgroundInert / palSetBackgroundInert. Without this the sheet
// declares aria-modal=true yet a single Tab escapes it into the live document
// behind the dim backdrop (the sheet's only focusable control is .sc-close).
function shortcutSetBackgroundInert(on) {
  if (!appEl || !shortcutSheetEl) return;
  Array.from(appEl.children).forEach((c) => {
    if (c === shortcutSheetEl) return;
    if (on) c.setAttribute('inert', '');
    else c.removeAttribute('inert');
  });
}
function openShortcutCheatsheet() {
  const el = buildShortcutSheet();
  if (!el.hidden) return;
  shortcutReturnFocus = document.activeElement;
  el.hidden = false;
  shortcutSetBackgroundInert(true);
  const close = el.querySelector('.sc-close');
  if (close) { try { close.focus(); } catch (e) { /* none */ } }
}
function closeShortcutCheatsheet() {
  if (!shortcutSheetEl || shortcutSheetEl.hidden) return;
  shortcutSheetEl.hidden = true;
  shortcutSetBackgroundInert(false);
  if (shortcutReturnFocus && document.body.contains(shortcutReturnFocus)) {
    try { shortcutReturnFocus.focus(); } catch (e) { /* gone */ }
  }
  shortcutReturnFocus = null;
}

function palBuildCommands(q) {
  const ranked = window.PaletteRank.rankItems(q, paletteCommands(), { key: 'text', limit: 60 });
  return ranked.map((r) => ({
    kind: 'command', label: r.text, hint: r.hint || '', positions: r.positions, run: r.run,
  }));
}
// Full-text search routes to the EXISTING sidebar index (spec section 4 —
// "existing search index"): seed the box, reveal it if overlay, run doSearch.
function palRunSearch(q) {
  closePalette();
  if (isOverlayChrome() && !isDrawerOpen()) openDrawer();
  searchInput.value = q;
  syncSearchClearVisibility();
  doSearch();
  searchInput.focus();
}

function palRebuild() {
  const { mode, q } = palParseMode(palInput.value);
  if (mode === 'command') palItems = palBuildCommands(q);
  else if (mode === 'index') palItems = palBuildIndex(q);
  else if (mode === 'shortcuts') palItems = palBuildShortcuts(q);
  else palItems = palBuildFiles(q);
  palSel = 0;
  palRender();
}
function palRender() {
  if (!palItems.length) {
    palResults.innerHTML = '<li class="pal-empty" role="status">No matches</li>';
    palInput.removeAttribute('aria-activedescendant');
    palInput.setAttribute('aria-expanded', 'false');
    return;
  }
  palInput.setAttribute('aria-expanded', 'true');
  palResults.innerHTML = palItems.map((it, i) => {
    const sel = i === palSel;
    const indent = it.kind === 'heading' && it.level
      ? ` style="padding-left:${10 + (it.level - 1) * 12}px"` : '';
    const hint = it.hint ? `<span class="pal-hint">${escapeHtml(it.hint)}</span>` : '';
    return `<li class="pal-item${sel ? ' sel' : ''} pal-${it.kind}" role="option" id="pal-opt-${i}"`
      + ` aria-selected="${sel}" data-idx="${i}"${indent}>`
      + `<span class="pal-item-label">${palHighlight(it.label, it.positions)}</span>${hint}</li>`;
  }).join('');
  palInput.setAttribute('aria-activedescendant', `pal-opt-${palSel}`);
}
function palHighlight(text, positions) {
  if (!positions || !positions.length) return escapeHtml(text);
  let out = '', last = 0;
  for (const p of positions) {
    out += escapeHtml(text.slice(last, p)) + '<mark>' + escapeHtml(text[p]) + '</mark>';
    last = p + 1;
  }
  return out + escapeHtml(text.slice(last));
}
function palMove(d) {
  if (!palItems.length) return;
  palSel = (palSel + d + palItems.length) % palItems.length;
  palRender();
  const el = palResults.querySelector('.pal-item.sel');
  if (el) el.scrollIntoView({ block: 'nearest' });
}
function palExec() {
  const it = palItems[palSel];
  if (!it) return;
  if (typeof it.run === 'function') it.run();
  else closePalette();                       // read-only rows (shortcut reference)
}

if (palRoot) {
  palInput.addEventListener('input', palRebuild);
  palInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); palMove(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); palMove(-1); }
    else if (e.key === 'Tab') { e.preventDefault(); palMove(e.shiftKey ? -1 : 1); }
    else if (e.key === 'Enter') { e.preventDefault(); palExec(); }
    else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closePalette(); }
  });
  palResults.addEventListener('click', (e) => {
    const li = e.target.closest('.pal-item');
    if (!li || li.dataset.idx == null) return;
    palSel = Number(li.dataset.idx);
    palExec();
  });
  // Dim-area click (outside the box) dismisses; clicks on the box do not.
  palRoot.addEventListener('click', (e) => { if (e.target === palRoot) closePalette(); });
  document.getElementById('rt-palette')?.addEventListener('click', openPalette);
}

// ── Reader chrome auto-hide (redesign 02 T5) ─────────────────────────
// Hide on meaningful scroll-down, reveal on scroll-up / near-top /
// mouse-to-top / focus / short documents. Reader-desktop only. Runs inside
// scheduleScrollSync's rAF (no listener of its own — see that function).
// rcLastY is null whenever the tick has been dormant (boot, mode switch,
// breakpoint crossing): the first tick after (re)activation only baselines,
// so a programmatic jump — session restore, deep link — never reads as a
// user scroll-down that hides the chrome on arrival (QR finding).
let rcLastY = null;
function readerChromeTick() {
  // Mobile (≤768px) is always reader (redesign 03); desktop participates
  // only in reader layout. While a sheet is open the chrome state is
  // frozen — the toolbar sits dimmed under the backdrop and must not
  // slide away mid-interaction (also stops the desktop chrome hiding
  // behind its backdrop).
  if (!mqlNarrow.matches && document.documentElement.dataset.chrome === 'docs') return;
  if (isDrawerOpen()) return;
  const y = window.scrollY;
  if (rcLastY === null) { rcLastY = y; return; }
  const fits = document.documentElement.scrollHeight <= window.innerHeight + 4;
  if (fits || y < 60 || y < rcLastY - 4) {
    document.documentElement.classList.remove('reader-chrome-hidden');
  } else if (y > rcLastY + 4) {
    document.documentElement.classList.add('reader-chrome-hidden');
  }
  if (Math.abs(y - rcLastY) > 4) rcLastY = y;
}
document.addEventListener('mousemove', (e) => {
  if (e.clientY < 8) document.documentElement.classList.remove('reader-chrome-hidden');
}, { passive: true });
// Touch mirror of the mouse-to-top reveal: the chrome lives at the BOTTOM
// on mobile, so the reveal gesture is a tap near the bottom edge (spec
// section 5 — "returns on scroll-up or tap at screen bottom"). The 48px
// band roughly matches the hidden toolbar's footprint; taps while a sheet
// is open belong to the backdrop instead.
document.addEventListener('click', (e) => {
  if (!mqlNarrow.matches || isDrawerOpen()) return;
  if (window.innerHeight - e.clientY <= 48) {
    document.documentElement.classList.remove('reader-chrome-hidden');
  }
});
// Keyboard mirror of the mousemove reveal: tabbing into auto-hidden chrome
// must bring it back on-screen, or focus lands on invisible controls.
['reader-topbar', 'reader-pill'].forEach((id) => {
  document.getElementById(id)?.addEventListener('focusin', () => {
    document.documentElement.classList.remove('reader-chrome-hidden');
  });
});

// ── Reader right-edge progress rail: click-to-jump (redesign 02 T6) ──
// Pointer-only + aria-hidden is deliberate parity, not an oversight: the
// legacy #reading-progress bar it replaces was aria-hidden and
// pointer-events:none, the percentage stays AT-visible via #pill-pct in the
// nav, and keyboard users keep equivalent navigation (outline sheet,
// PageUp/Down, Home/End) — no function is exclusively mouse-locked.
document.getElementById('reader-rail')?.addEventListener('click', (e) => {
  const railEl = e.currentTarget;
  const f = (e.clientY - railEl.getBoundingClientRect().top) / railEl.clientHeight;
  const max = document.documentElement.scrollHeight - window.innerHeight;
  window.scrollTo({ top: Math.max(0, Math.min(1, f)) * max, behavior: 'instant' });
});

// Mobile reading rail (mobile-bar T1): tap reveals the auto-hidden bar and
// briefly shows a position label that cycles percent ↔ section on each tap.
function summonMobileChrome() {
  document.documentElement.classList.remove('reader-chrome-hidden');
  rcLastY = null;                                  // re-baseline so it does not instantly re-hide
}
function showRailLabel() {
  mobileRailLabel.textContent = window.ReadingPosition.formatPosition(
    railLabelMode, { pct: railActivePct, section: railActiveSection });
  mobileRailLabel.classList.add('show');
  if (railLabelTimer) clearTimeout(railLabelTimer);
  railLabelTimer = setTimeout(() => mobileRailLabel.classList.remove('show'), 1800);
}
if (mobileRail) {
  const railActivate = () => {
    summonMobileChrome();
    // Cycle from the persisted mode and persist the new one (per-device — spec
    // section 3.2). showRailLabel reads the module var set here.
    railLabelMode = window.ReadingPosition.nextPositionMode(settingsStore.get('railLabelMode'), ['percent', 'section']);
    settingsStore.set('railLabelMode', railLabelMode);
    showRailLabel();
  };
  mobileRail.addEventListener('click', railActivate);
  mobileRail.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); railActivate(); }
  });
}

document.getElementById('setting-scroll-fx').addEventListener('change', (e) => {
  settingsStore.set('scrollFx', e.target.checked);
  document.documentElement.classList.toggle('no-scroll-fx', !e.target.checked);
});

document.getElementById('setting-update-fx').addEventListener('change', (e) => {
  settingsStore.set('updateFx', e.target.checked);
  document.documentElement.classList.toggle('no-update-fx', !e.target.checked);
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
// Keep wheel scroll inside a chrome region even when its content fits and shows no
// scrollbar. CSS overscroll-behavior:contain only engages when the element is
// actually scrollable, so the fits case (a #sidebar with few items, a modal whose
// content fits, or the modal backdrop) still chains to the page. This walks the
// wheel target's ancestor chain within the region; if nothing there can scroll in
// the wheel's direction, the chain to the document is prevented.
function trapRegionScroll(region) {
  if (!region || region._scrollTrapped) return;
  region._scrollTrapped = true;
  region.addEventListener('wheel', (e) => {
    for (let n = e.target; n && n !== region.parentElement; n = n.parentElement) {
      if (n.scrollHeight > n.clientHeight + 1) {
        const atTop = n.scrollTop <= 0;
        const atBottom = n.scrollTop + n.clientHeight >= n.scrollHeight - 1;
        if (!((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom))) return;
      }
    }
    e.preventDefault();
  }, { passive: false });
}

function setupScrollTraps() {
  ['sidebar', 'right-pane', 'content-b', 'settings-sheet', 'cmd-palette', 'shortcut-cheatsheet']
    .map((id) => document.getElementById(id))
    .forEach(trapRegionScroll);
}

async function init() {
  // One-time event registrations
  contentEl.addEventListener('click', handleLinkClick);
  setupScrollTraps();

  const { version: initVersion } = await fetchFileList();
  buildSidebar();
  // Check for new publish version on initial load (cloud only; no-op on dev).
  if (backend.kind === 'cloud') checkVersion(initVersion || (window.VIEWER_CONFIG && window.VIEWER_CONFIG.version) || null);

  // Flush any annotation writes queued while offline (cloud mode only).
  if (backend.flushQueue) backend.flushQueue();

  // At narrow width the sidebar is an off-canvas drawer that starts CLOSED by
  // default (CSS translateX(-100%); no `#app.drawer-open` class). No JS action
  // is needed on load — and we must NOT leave a stale `.collapsed` on #sidebar,
  // or it would carry over and start the desktop sidebar collapsed if the
  // viewport later widens.

  loadSettings();

  // Load from URL, server default (single-file mode), or first file. resolveFileId
  // rescues an old flat ?file= bookmark whose id is now namespaced (multi-root);
  // loadFile(..., 'replace') then rewrites the URL to the resolved namespaced id.
  const { file, anchor } = parseURL();
  const resolved = resolveFileId(file);
  const target = resolved
               || (defaultFile && fileList.includes(defaultFile) ? defaultFile : fileList[0]);
  if (target) {
    await loadFile(target, anchor, 'replace');
  }

  // Restore scroll position from previous session (browser refresh).
  // A single rAF + scrollTo is unreliable for math-heavy pages: the
  // KaTeX HTML is in place but the custom KaTeX fonts load asynchronously,
  // and the document height keeps growing for several hundred ms after
  // the initial paint. A one-shot scrollTo lands at a clamped Y and
  // never re-asserts. Use scrollToStable to keep re-asserting frame
  // by frame until the document is tall enough, plus a one-shot pass
  // after `document.fonts.ready` for very late layout shifts.
  try {
    const saved = sessionStorage.getItem('viewer-scroll');
    if (saved) {
      const state = JSON.parse(saved);
      // state.scrollY > 0: skip the 3-second scrollToStable loop when the
      // saved position is 0 — the browser already starts at 0, and asserting
      // it frame-by-frame for 3 s gains nothing while fighting any subsequent
      // programmatic scroll. Non-zero positions restore exactly as before.
      if (state.file === currentFile && !anchor && typeof state.scrollY === 'number'
          && state.scrollY > 0) {
        scrollToStable(state.scrollY, 3000);
        if (document.fonts && document.fonts.ready) {
          document.fonts.ready.then(() => {
            if (Math.abs(window.scrollY - state.scrollY) > 1) {
              scrollToInstant(state.scrollY);
            }
          });
        }
      }
      sessionStorage.removeItem('viewer-scroll');
    }
  } catch {}

  connectWS();

  // Prefetch all files for search
  Promise.all(fileList.map(f => {
    if (!fileContents[f]) return fetchFile(f);
    return Promise.resolve();
  }));
}

// Save scroll position before browser refresh/close
window.addEventListener('beforeunload', () => {
  try {
    sessionStorage.setItem('viewer-scroll', JSON.stringify({
      file: currentFile,
      scrollY: window.scrollY,
    }));
  } catch {}
});

init();
