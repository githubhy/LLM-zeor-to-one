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
let fileList     = [];            // ordered list of filenames
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
const settingsPanel = document.getElementById('settings-panel');
const searchBoxEl   = document.getElementById('search-box');
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

// ── Parse ATX headings from raw markdown, skipping fenced code and $$ math.
function extractHeadings(markdown) {
  const headings = [];
  // Fresh per call so a sibling file's outline ids match what the renderer
  // would emit for that same file (GitHub-compatible duplicate suffixing).
  const slug = HighlightShared.makeUniqueSlugger();
  const lines = (markdown || '').split('\n');
  let inFence = false, inMath = false;
  for (const line of lines) {
    const stripped = line.trim();
    if (!inMath && /^(`{3,}|~{3,})/.test(stripped)) { inFence = !inFence; continue; }
    if (inFence) continue;
    if (!inMath && (stripped === '$$' || /^==\w+:\s*\$\$$/.test(stripped))) { inMath = true; continue; }
    if (inMath && (stripped === '$$' || stripped === '$$==')) { inMath = false; continue; }
    if (inMath) continue;
    const m = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (m) {
      const cleanTxt = stripInlineMarkersForSlug(m[2]);
      headings.push({ level: m[1].length, text: cleanTxt, id: slug(cleanTxt) });
    }
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
      // reading-progress honest (debounced — batches arrive in bursts).
      clearTimeout(lazyMathRefreshTimer);
      lazyMathRefreshTimer = setTimeout(() => scrollSyncRefreshLayout(), 150);
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
  if (isOverlayLayout() && !isDrawerOpen()) openDrawer();
  // Ensure the Highlights tab is active and its entries are rendered.
  // buildHighlights() is async (fetches manifest); we must await it so the
  // row lookup below is guaranteed to run after the DOM is populated.
  if (activeTab !== 'highlights') {
    // Update tab button/pane visibility synchronously first so the tab
    // appears active immediately (switchTab would also call buildHighlights,
    // but we call it directly here to be able to await it).
    activeTab = 'highlights';
    document.querySelectorAll('.sidebar-tab').forEach(t =>
      t.classList.toggle('active', t.dataset.tab === 'highlights')
    );
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
      if (!showPeek(a, parsed, true)) { updateURL(currentFile, anchorId); scrollToAnchor(anchorId); }
    });
  });
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
  installFootnoteRefHandlers();
  installPeekHandlers();
  renderMermaidDiagrams();
  updateDocumentTitle();
  if (activeTab === 'outline') buildOutline();
  if (activeTab === 'highlights') buildHighlights();
  const mySeq = ++renderSeq;
  // Recompute heading tops after first paint and after late KaTeX/Mermaid
  // reflow so progress + outline-sync stay correct (runs every render,
  // independent of `anchor` and of which sidebar tab is active).
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (mySeq !== renderSeq) return;
      scrollSyncRefreshLayout();
      setTimeout(() => {
        if (mySeq === renderSeq) scrollSyncRefreshLayout();
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
}

function currentFileDir() {
  if (!currentFile) return '';
  const idx = currentFile.lastIndexOf('/');
  return idx >= 0 ? currentFile.slice(0, idx) : '';
}

// Resolve a relative .md path against the current file's directory
function resolveRelPath(relPath) {
  const dir = currentFileDir();
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
  defaultFile = data.defaultFile || null;
  for (const file of [...manifestByFile.keys()]) {
    if (!fileList.includes(file)) manifestByFile.delete(file);
  }
  markManifestDirty();
  return { files: fileList, version: data.version || null };
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

  // Group files by directory
  const dirs = {};    // dirName → [filePaths]
  const topLevel = []; // files without a directory
  for (const f of fileList) {
    const slash = f.indexOf('/');
    if (slash >= 0) {
      const dir = f.slice(0, slash);
      (dirs[dir] = dirs[dir] || []).push(f);
    } else {
      topLevel.push(f);
    }
  }

  // Render directory groups first, then top-level files
  const dirNames = Object.keys(dirs).sort();
  for (const dir of dirNames) {
    const group = document.createElement('div');
    group.className = 'dir-group';
    group.dataset.dir = dir;

    const header = document.createElement('div');
    header.className = 'dir-header';
    header.innerHTML = `<span class="dir-arrow">&#9654;</span> ${dir}/`;
    header.addEventListener('click', () => {
      group.classList.toggle('open');
    });
    group.appendChild(header);

    const children = document.createElement('div');
    children.className = 'dir-children';
    for (const f of dirs[dir]) {
      children.appendChild(makeFileEntry(f));
    }
    group.appendChild(children);
    fileListEl.appendChild(group);
  }

  for (const f of topLevel) {
    fileListEl.appendChild(makeFileEntry(f));
  }
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
  // Auto-expand parent directory group
  if (currentFile && currentFile.includes('/')) {
    const dir = currentFile.slice(0, currentFile.indexOf('/'));
    const group = fileListEl.querySelector(`.dir-group[data-dir="${dir}"]`);
    if (group) group.classList.add('open');
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

function isDrawerOpen()  { return appEl.classList.contains('drawer-open'); }

// Overlay layout = the sidebar behaves as an over-content sheet rather than
// a docked rail: always at narrow width (mobile drawer), and at desktop
// width whenever the reader layout is active (redesign 02).
function isOverlayLayout() {
  return mqlNarrow.matches || document.documentElement.dataset.layout !== 'classic';
}

// Every control that opens the sheet reports its expanded state — in reader
// mode #sidebar-toggle is display:none, so without the pill/Aa updates no
// visible control would expose the sheet state to assistive tech.
// (#sidebar-toggle is NOT in this list: it is a classic-only collapse
// control — redesign 04 — and its aria tracks the docked sidebar instead.)
function setSheetExpanded(expanded) {
  document.querySelectorAll('#reader-pill [data-pill], #rt-aa, #mobile-toolbar [data-mt]').forEach((b) =>
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
  if (document.documentElement.dataset.layout === 'classic') {
    sidebarBtn.setAttribute('aria-expanded', String(!sidebar.classList.contains('collapsed')));
  }
}
function openDrawer() {
  appEl.classList.add('drawer-open');
  setSheetExpanded(true);
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
}
function toggleDrawer() { isDrawerOpen() ? closeDrawer() : openDrawer(); }
function maybeCloseDrawer() { if (isOverlayLayout()) closeDrawer(); }

// When the viewport crosses the breakpoint, reset to that mode's resting state:
// leaving narrow width must clear any open drawer so the desktop dock is clean;
// entering narrow width must start closed (no auto-open). Chrome auto-hide
// state resets too — readerChromeTick is dormant while narrow, so a stale
// reader-chrome-hidden would otherwise survive a desktop→mobile→desktop
// crossing and resume with the top bar/pill hidden (QR finding).
mqlNarrow.addEventListener('change', () => {
  closeDrawer();
  document.documentElement.classList.remove('reader-chrome-hidden');
  rcLastY = null;
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
  }
}

window.addEventListener('scroll', scheduleScrollSync, { passive: true });
window.addEventListener('resize', scrollSyncRefreshLayout, { passive: true });

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
  el.scrollIntoView({ behavior: instant ? 'instant' : (smooth ? 'smooth' : 'auto'), block: 'center' });
  if (hasPendingMath) {
    setTimeout(() => {
      const target = document.getElementById(anchor);
      if (target) target.scrollIntoView({ behavior: 'instant', block: 'center' });
    }, 350);
  }
  // Flash highlight
  el.classList.remove('anchor-highlight');
  void el.offsetWidth;
  el.classList.add('anchor-highlight');

  // Also highlight the parent display equation or paragraph
  const parent = el.closest('.katex-display, p, tr, li') || el.parentElement;
  if (parent && parent !== el) {
    parent.classList.remove('anchor-highlight');
    void parent.offsetWidth;
    parent.classList.add('anchor-highlight');
  }
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
  if (activeTab === 'outline')    return getScope(folderOf(currentFile), 'outline');
  if (activeTab === 'highlights') return getScope(folderOf(currentFile), 'highlights');
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
  const activeFolder = currentFile ? folderOf(currentFile) : null;
  const here       = activeFolder != null ? fileList.filter(f => folderOf(f) === activeFolder) : [];
  const elsewhere  = activeFolder != null ? fileList.filter(f => folderOf(f) !== activeFolder) : fileList;
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
  const hereResults      = activeFolder == null ? []      : results.filter(r => folderOf(r.file) === activeFolder);
  const elsewhereResults = activeFolder == null ? results : results.filter(r => folderOf(r.file) !== activeFolder);

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
  // Esc closes the slide-over drawer at narrow width or in reader layout (when
  // open) — but only once the peek is gone, so Esc dismisses the topmost overlay
  // (the peek) first rather than both at once (review wrnjhusbu).
  if (e.key === 'Escape' && isOverlayLayout() && isDrawerOpen() && (!peekPopover || peekPopover.hidden)) {
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
    if (isOverlayLayout()) {
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
    if (isOverlayLayout()) {
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
    if (isOverlayLayout()) {
      if (!isDrawerOpen()) { openDrawer(); switchTab('highlights'); return; }
    } else if (sidebar.classList.contains('collapsed')) {
      setClassicCollapsed(false);
    }
    switchTab(activeTab === 'highlights' ? 'files' : 'highlights');
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
            if (activeTab === 'outline' && folderOf(msg.file) === folderOf(currentFile)) {
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
        type = 'SIDECAR';
        endBlock = startBlock;   // single-block selection; sidecar needs both ends
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
// Sidebar tabs
// ---------------------------------------------------------------------------
document.querySelectorAll('.sidebar-tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

function switchTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.sidebar-tab').forEach(t =>
    t.classList.toggle('active', t.dataset.tab === tabName)
  );
  fileListEl.classList.toggle('tab-hidden', tabName !== 'files');
  outlineEl.classList.toggle('tab-hidden', tabName !== 'outline');
  highlightsEl.classList.toggle('tab-hidden', tabName !== 'highlights');
  if (tabName === 'outline') buildOutline();
  if (tabName === 'highlights') buildHighlights();
  // Search scope follows the active tab (see getSearchScope). When the user
  // switches tabs with a query already typed, re-run so the results match
  // the new scope.
  if (searchInput.value.trim().length >= 2) doSearch();
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
  const activeFolder = currentFile ? folderOf(currentFile) : null;
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
    cachedHits = cachedHits.filter(h => folderOf(h.file) === activeFolder);
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
    return localStorage.getItem(`viewer.scope.${folder}.${pane}`) === 'file'
      ? 'file' : 'folder';
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
  const folder = currentFile ? folderOf(currentFile) : '';
  const current = getScope(folder, paneName);
  const wrap = document.createElement('div');
  wrap.className = 'pane-scope';
  wrap.setAttribute('role', 'group');
  wrap.setAttribute('aria-label', 'Show entries from');

  for (const value of ['folder', 'file']) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pane-scope-btn';
    btn.dataset.scope = value;
    btn.textContent = value === 'folder' ? 'Folder' : 'File';
    btn.setAttribute('aria-pressed', current === value ? 'true' : 'false');
    btn.addEventListener('click', () => {
      if (!currentFile) return;
      const f = folderOf(currentFile);
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
function buildOutline() {
  // Preserve pane scroll across bursty rebuilds (same pattern as
  // buildHighlights). First caller stashes the live scrollTop; reuse it
  // until the rebuild completes so the pane doesn't jump.
  if (pendingOutlineScroll === null) pendingOutlineScroll = outlineEl.scrollTop;
  outlineEl.innerHTML = '';
  if (!currentFile) { registerOutlineSpy(null); return; }

  const activeFolder = folderOf(currentFile);
  const scope = getScope(activeFolder, 'outline');
  const siblings = scope === 'file'
    ? [currentFile]
    : fileList.filter(f => folderOf(f) === activeFolder);

  // Toggle is appended first so it stays above any empty-state placeholder.
  outlineEl.appendChild(renderScopeToggle('outline'));

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
  const seq = ++buildOutlineSeq;
  const pending = siblings.filter(f => !fileContents[f]);
  if (pending.length) {
    Promise.all(pending.map(f => fetchFile(f).catch(() => {})))
      .then(() => { if (seq === buildOutlineSeq && activeTab === 'outline') buildOutline(); });
  }

  const spyEntries = [];
  const showFileSeps = siblings.length > 1;

  for (const file of siblings) {
    const isCurrent = file === currentFile;

    if (showFileSeps) {
      const sep = document.createElement('div');
      sep.className = 'outline-file-sep';
      if (isCurrent) sep.dataset.current = '';
      sep.dataset.file = file;
      sep.textContent = file.slice(file.lastIndexOf('/') + 1);
      outlineEl.appendChild(sep);
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
        outlineEl.appendChild(empty);
      }
      continue;
    }

    for (const h of entries) {
      const entry = document.createElement('div');
      entry.className = 'outline-entry';
      entry.dataset.level  = h.level;
      entry.dataset.file   = file;
      entry.dataset.anchor = h.id;
      if (isCurrent) entry.dataset.current = '';
      entry.textContent = h.text;

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
        // Navigating from the outline drawer dismisses it so content is visible.
        maybeCloseDrawer();
      });

      outlineEl.appendChild(entry);
      if (isCurrent && h.el) spyEntries.push({ el: entry, heading: h.el });
    }
  }

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

function applyLayout(layout) {
  document.documentElement.dataset.layout = (layout === 'classic') ? 'classic' : 'reader';
  // Mode switches must not strand an open overlay or stale chrome state.
  // The close is guarded: unconditional closeDrawer() slammed the mobile
  // drawer shut when the layout radio was tapped inside it, where the
  // switch is visually inert (QR finding).
  if (!mqlNarrow.matches && isDrawerOpen()) closeDrawer();
  document.documentElement.classList.remove('reader-chrome-hidden');
  rcLastY = null;
  // Entering classic: the toggle's aria must reflect the docked sidebar
  // (redesign 04 — its aria is collapse state, not sheet state).
  syncClassicToggleAria();
}

function applyTheme(theme) {
  if (theme === 'light') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', THEME_COLORS[theme] || THEME_COLORS.light);
}

const SERIF_STACK = "Georgia, 'Iowan Old Style', 'Times New Roman', serif";

function applyTypography(s) {
  const r = document.documentElement.style;
  r.setProperty('--font-scale', String(s.fontScale));
  r.setProperty('--content-lh', String(s.lineHeight));
  r.setProperty('--content-max', s.contentMax + 'px');
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
  if (key === 'layout') applyLayout(value);
  if (key === 'theme') {
    applyTheme(value);
    rethemeMermaid(value);
    // rt-theme (top bar) also writes 'theme' — keep the panel radios in
    // sync, or the stale-checked radio becomes a dead control (no change
    // event fires on an already-checked radio).
    document.querySelectorAll('input[name="theme"]').forEach((r) => {
      r.checked = r.value === value;
    });
  }
  if (key === 'fontScale' || key === 'lineHeight' || key === 'contentMax' || key === 'fontFamily') {
    applyTypography(settingsStore.getAll());
  }
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

  // Layout
  applyLayout(settingsStore.get('layout'));
  document.querySelectorAll('input[name="layout-mode"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('layout');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('layout', e.target.value); });
  });

  // Theme
  applyTheme(settingsStore.get('theme'));
  document.querySelectorAll('input[name="theme"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('theme');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('theme', e.target.value); });
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
  bindRange('setting-content-max', 'contentMax', (v) => parseInt(v, 10));
  document.querySelectorAll('input[name="content-font"]').forEach((r) => {
    r.checked = r.value === settingsStore.get('fontFamily');
    r.addEventListener('change', (e) => { if (e.target.checked) settingsStore.set('fontFamily', e.target.value); });
  });
  // (Store subscriber lives at module scope, right after settingsStore — see
  // the comment there.)
}

settingsBtn.addEventListener('click', () => {
  // In overlay layout (reader desktop), open the drawer so the settings
  // panel (which lives in the sidebar) is visible and interactive.
  if (isOverlayLayout()) openDrawer();
  settingsPanel.classList.toggle('settings-hidden');
});

// ── Reader top bar (redesign 02 T3) ──────────────────────────────────
const THEME_CYCLE = ['light', 'sepia', 'dark'];
document.getElementById('rt-theme')?.addEventListener('click', () => {
  const cur = settingsStore.get('theme');
  settingsStore.set('theme', THEME_CYCLE[(THEME_CYCLE.indexOf(cur) + 1) % THEME_CYCLE.length]);
});
document.getElementById('rt-aa')?.addEventListener('click', () => {
  // The settings panel lives in the sidebar header — open the sheet with
  // the panel expanded (fixed popovers inside the transformed sidebar are
  // a CSS containing-block trap; the sheet is the sanctioned surface).
  openDrawer();
  document.getElementById('settings-panel').classList.remove('settings-hidden');
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
    if (slot === 'aa') {
      openDrawer();
      settingsPanel.classList.remove('settings-hidden');
    } else if (slot === 'search') {
      openDrawer();
      searchInput.focus();
      searchInput.select();
    } else {
      switchTab(slot);
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

// Mode is selected by input prefix: '>' commands, '#' headings, else files.
function palParseMode(raw) {
  const s = raw || '';
  if (s.startsWith('>')) return { mode: 'command', q: s.slice(1).trim() };
  if (s.startsWith('#')) return { mode: 'heading', q: s.slice(1).trim() };
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
// Headings of the CURRENT file from live DOM (real rendered ids), so
// scrollToAnchor jumps without the extractHeadings sibling-slugger mismatch.
function palBuildHeadings(q) {
  const heads = Array.from(contentEl.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .filter((h) => h.id)
    .map((h) => ({ text: h.textContent.trim(), id: h.id, level: Number(h.tagName[1]) }));
  const ranked = window.PaletteRank.rankItems(q, heads, { key: 'text', limit: 50 });
  return ranked.map((r) => ({
    kind: 'heading', label: r.text, hint: 'H' + r.level, level: r.level, positions: r.positions,
    run: () => { closePalette(); scrollToAnchor(r.id); },
  }));
}
function palAct(fn) { return () => { closePalette(); fn(); }; }

// Command registry. Each action reuses an existing module-scope seam. Push/pull
// are gated on the cloud backend (absent under local-server, which fixtures use).
function paletteCommands() {
  const cloud = !!(typeof backend !== 'undefined' && backend && backend.kind === 'cloud');
  const cmds = [
    { text: 'Toggle theme', run: palAct(() => {
        const c = settingsStore.get('theme');
        settingsStore.set('theme', THEME_CYCLE[(THEME_CYCLE.indexOf(c) + 1) % THEME_CYCLE.length]);
      }) },
    { text: 'Theme: Light',  run: palAct(() => settingsStore.set('theme', 'light')) },
    { text: 'Theme: Sepia',  run: palAct(() => settingsStore.set('theme', 'sepia')) },
    { text: 'Theme: Dark',   run: palAct(() => settingsStore.set('theme', 'dark')) },
    // Classic is desktop-only (spec section 6); below the breakpoint the layout
    // is always reader, so omit the toggle on mobile to match the settings
    // panel, which hides the layout radio there. Review weqs70hun.
    ...(!mqlNarrow.matches ? [{ text: 'Toggle layout (Reader / Classic)', run: palAct(() =>
        settingsStore.set('layout', settingsStore.get('layout') === 'classic' ? 'reader' : 'classic')) }] : []),
    { text: 'Open settings', run: palAct(() => {
        if (isOverlayLayout()) openDrawer();
        settingsPanel.classList.remove('settings-hidden');
      }) },
    { text: 'Copy citation', run: palAct(() => {
        if (savedRange) copyCitation('rich'); else showToast('Select text first');
      }) },
  ];
  if (cloud) {
    cmds.push({ text: 'Push annotations to cloud', run: palAct(() => {
      if (backend.flushQueue) backend.flushQueue(); showToast('Pushing annotations…'); }) });
    cmds.push({ text: 'Pull annotations from cloud', run: palAct(() => {
      if (currentFile) { loadFile(currentFile, null, false); showToast('Pulling annotations…'); } }) });
  }
  // Read-only shortcut reference (spec section 4 — palette lists existing
  // shortcuts). run:null rows just close on Enter (palExec handles non-fn run).
  [
    ['Shortcut: Command palette', 'Ctrl+K'],
    ['Shortcut: Toggle sidebar', 'Ctrl+B'],
    ['Shortcut: Outline', 'Ctrl+Shift+O'],
    ['Shortcut: Highlights', 'Ctrl+Shift+H'],
    ['Shortcut: Highlight selection', 'Ctrl+Shift+L'],
    ['Shortcut: Undo', 'Ctrl+Z'],
  ].forEach(([text, key]) => cmds.push({ text, hint: key, run: null }));
  return cmds;
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
  if (isOverlayLayout() && !isDrawerOpen()) openDrawer();
  searchInput.value = q;
  syncSearchClearVisibility();
  doSearch();
  searchInput.focus();
}

function palRebuild() {
  const { mode, q } = palParseMode(palInput.value);
  if (mode === 'command') palItems = palBuildCommands(q);
  else if (mode === 'heading') palItems = palBuildHeadings(q);
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
  if (!mqlNarrow.matches && document.documentElement.dataset.layout === 'classic') return;
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
async function init() {
  // One-time event registrations
  contentEl.addEventListener('click', handleLinkClick);

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

  // Load from URL, server default (single-file mode), or first file
  const { file, anchor } = parseURL();
  const target = file && fileList.includes(file) ? file
               : defaultFile && fileList.includes(defaultFile) ? defaultFile
               : fileList[0];
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
