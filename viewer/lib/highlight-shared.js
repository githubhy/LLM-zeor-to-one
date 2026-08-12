(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ViewerHighlightShared = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';

  const DEFAULT_HIGHLIGHT_COLOR = 'yellow';
  const HIGHLIGHT_COLORS = [
    'yellow',
    'green',
    'red',
    'blue',
    'orange',
    'purple',
    'teal',
    'pink',
  ];
  const HIGHLIGHT_COLOR_SET = new Set(HIGHLIGHT_COLORS);
  const HL_COLOR_ALT = HIGHLIGHT_COLORS.join('|');

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function normalizeWhitespace(value) {
    return String(value || '').replace(/[ \t\r\n]+/g, ' ').trim();
  }

  function makeInlineHighlightId(file, sourceStart, sourceEnd) {
    return `inline:${encodeURIComponent(file || '')}:${sourceStart}:${sourceEnd}`;
  }

  function makeSidecarHighlightId(file, suffix) {
    return `sidecar:${encodeURIComponent(file || '')}:${suffix}`;
  }

  function lineStartsOf(source) {
    const starts = [0];
    for (let i = 0; i < source.length; i++) {
      if (source[i] === '\n') starts.push(i + 1);
    }
    return starts;
  }

  function lineOfOffset(lineStarts, offset) {
    let lo = 0;
    let hi = lineStarts.length - 1;
    let best = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (lineStarts[mid] <= offset) {
        best = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    return best;
  }

  function fencedBlockAtLineStart(source, index) {
    let cursor = index;
    while (cursor < source.length && source[cursor] === ' ') cursor++;
    const marker = source[cursor];
    if (marker !== '`' && marker !== '~') return null;
    let end = cursor;
    while (end < source.length && source[end] === marker) end++;
    if (end - cursor < 3) return null;
    return { marker, size: end - cursor };
  }

  function advanceOne(source, state) {
    if (source[state.index] === '\n') {
      state.line++;
      state.atLineStart = true;
    } else if (state.atLineStart && source[state.index] === ' ') {
      state.atLineStart = true;
    } else {
      state.atLineStart = false;
    }
    state.index++;
  }

  function startsWithFenceClose(source, index, marker, size) {
    let cursor = index;
    while (cursor < source.length && source[cursor] === ' ') cursor++;
    let matched = 0;
    while (cursor + matched < source.length && source[cursor + matched] === marker) {
      matched++;
    }
    return matched >= size;
  }

  function readBacktickRun(source, index) {
    let end = index;
    while (end < source.length && source[end] === '`') end++;
    return end - index;
  }

  function parseHighlightPrefix(source, start) {
    const colorMatch = source.slice(start).match(new RegExp(`^(${HL_COLOR_ALT}):\\s*`, 'i'));
    if (!colorMatch) {
      return {
        color: DEFAULT_HIGHLIGHT_COLOR,
        innerStart: start,
      };
    }
    return {
      color: colorMatch[1].toLowerCase(),
      innerStart: start + colorMatch[0].length,
    };
  }

  function extractInlineHighlights(source, file) {
    const hits = [];
    const lines = lineStartsOf(source);
    const state = {
      index: 0,
      line: 0,
      atLineStart: true,
    };
    let fence = null;
    let inlineCodeRun = 0;

    while (state.index < source.length) {
      if (!inlineCodeRun && state.atLineStart) {
        const nextFence = fencedBlockAtLineStart(source, state.index);
        if (nextFence) {
          if (!fence) {
            fence = nextFence;
          } else if (nextFence.marker === fence.marker && nextFence.size >= fence.size) {
            fence = null;
          }
          // Treat the fence marker line as structural, not inline-code content.
          while (state.index < source.length && source[state.index] !== '\n') {
            state.index++;
            state.atLineStart = false;
          }
          continue;
        }
      }

      if (!fence && source[state.index] === '`') {
        const run = readBacktickRun(source, state.index);
        if (!inlineCodeRun) {
          inlineCodeRun = run;
        } else if (run === inlineCodeRun) {
          inlineCodeRun = 0;
        }
        state.index += run;
        state.atLineStart = false;
        continue;
      }

      if (fence) {
        advanceOne(source, state);
        continue;
      }

      if (!inlineCodeRun && source[state.index] === '=' && source[state.index + 1] === '=') {
        const sourceStart = state.index;
        const startLine = state.line;
        const prefix = parseHighlightPrefix(source, sourceStart + 2);
        let cursor = prefix.innerStart;
        while (cursor < source.length - 1) {
          if (source[cursor] === '=' && source[cursor + 1] === '=') break;
          cursor++;
        }
        if (cursor < source.length - 1) {
          const sourceEnd = cursor + 2;

          // Look for an adjacent [^...] note ref (must be flush, no whitespace).
          let noteRefStart = null;
          let noteRefEnd = null;
          let noteId = null;
          if (source[sourceEnd] === '[' && source[sourceEnd + 1] === '^') {
            let refClose = sourceEnd + 2;
            while (
              refClose < source.length
              && source[refClose] !== ']'
              && source[refClose] !== '\n'
              && source[refClose] !== ' '
              && source[refClose] !== '\t'
            ) {
              refClose++;
            }
            if (source[refClose] === ']' && refClose > sourceEnd + 2) {
              const candidateId = source.slice(sourceEnd + 2, refClose);
              // Reserved-id convention: only `note-*` ids are absorbed as
              // note refs. Other footnote ids (citations etc.) are left as
              // ordinary footnotes and not associated with the highlight.
              if (candidateId.startsWith('note-')) {
                noteId = candidateId;
                noteRefStart = sourceEnd;
                noteRefEnd = refClose + 1;
              }
            }
          }

          const innerText = source.slice(prefix.innerStart, cursor);
          const excerpt = normalizeWhitespace(innerText);
          if (excerpt) {
            const endLine = lineOfOffset(lines, cursor);
            hits.push({
              id: makeInlineHighlightId(file, sourceStart, sourceEnd),
              file,
              backend: 'inline',
              color: prefix.color,
              sourceStart,
              sourceEnd,
              innerStart: prefix.innerStart,
              innerEnd: cursor,
              lineStart: startLine,
              lineEnd: endLine,
              excerpt,
              text: innerText,
              noteRefStart,
              noteRefEnd,
              noteId,
              noteDefStart: null,
              noteDefEnd: null,
              noteBody: null,
              noteHasMath: false,
            });
          }
          if (noteRefEnd !== null) {
            state.index = noteRefEnd;
          } else {
            state.index = sourceEnd;
          }
          state.line = lineOfOffset(lines, state.index);
          state.atLineStart = source[state.index - 1] === '\n';
          continue;
        }
      }

      advanceOne(source, state);
    }

    const defs = resolveFootnoteDefs(source);
    for (const hit of hits) {
      if (!hit.noteId) continue;
      const def = defs.get(hit.noteId);
      if (!def) continue;
      hit.noteDefStart = def.defStart;
      hit.noteDefEnd = def.defEnd;
      hit.noteBody = def.body;
      hit.noteHasMath = /\$[^$]+\$|\$\$/.test(def.body);
    }
    return hits;
  }

  function resolveFootnoteDefs(source) {
    const src = String(source || '');
    const defs = new Map();
    // Pre-compute line starts for offset arithmetic.
    const lineStarts = lineStartsOf(src);
    // CRLF files (Windows surveys) keep a trailing '\r' after split('\n').
    // The def regex's `(.*)$` then never matches ('.' won't cross '\r' and
    // JS `$` without /m/ anchors only at true end-of-string), so every
    // footnote def — and therefore every note body — was dropped. Parse
    // against a '\r'-stripped line view; keep `rawLines` for offset/length
    // math so defStart/defEnd still index the original source (editNote /
    // deleteNote slice `src` by these, and rely on defEnd landing on '\n').
    const rawLines = src.split('\n');
    const lines = rawLines.map(l => (l.endsWith('\r') ? l.slice(0, -1) : l));
    let i = 0;
    while (i < lines.length) {
      const m = lines[i].match(/^\[\^([^\]\s]+)\]:[ \t]?(.*)$/);
      if (!m) { i++; continue; }
      const id = m[1];
      const bodyLines = [m[2]];
      const startLine = i;
      let endLine = i;
      let j = i + 1;
      while (j < lines.length) {
        const next = lines[j];
        if (next === '') {
          // Peek: is there an indented line later that continues this def?
          let k = j + 1;
          while (k < lines.length && lines[k] === '') k++;
          if (k < lines.length && /^    /.test(lines[k]) && !/^\[\^/.test(lines[k].slice(4))) {
            // Blank line is part of multi-paragraph def body.
            bodyLines.push('');
            endLine = j;
            j++;
            continue;
          }
          break;
        }
        if (/^    /.test(next)) {
          bodyLines.push(next.slice(4));
          endLine = j;
          j++;
          continue;
        }
        break;
      }
      const defStart = lineStarts[startLine];
      // Use the RAW last line (incl. any '\r') so defEnd lands on the
      // terminating '\n' for both LF and CRLF — preserves the exact
      // pre-existing LF semantics deleteNote/editNote depend on.
      const lastLine = rawLines[endLine];
      const defEnd = lineStarts[endLine] + lastLine.length;
      defs.set(id, {
        id,
        body: bodyLines.join('\n').replace(/\s+$/g, ''),
        defStart,
        defEnd,
      });
      i = endLine + 1;
    }
    return defs;
  }

  function materializeManifestEntry(entry, override) {
    return Object.assign({
      id: entry.id,
      file: entry.file,
      backend: entry.backend,
      color: entry.color,
      excerpt: entry.excerpt,
    }, override || {});
  }

  function slugify(text) {
    // Match GitHub's slugger exactly: replace EACH whitespace character with a
    // hyphen individually (/ /g per-char, no run-collapse), and do NOT collapse
    // consecutive hyphens.  This means "3 — Folding…" (em-dash stripped, two
    // adjacent spaces remain) → "3--folding-…" — the double-hyphen form that
    // GitHub emits and that markdown authors write in their anchor hrefs.
    // The old code used /\s+/g (run→single hyphen) + /-+/g (hyphen collapse),
    // which produced "3-folding-…" — a mismatch with every double-hyphen link.
    // trim() runs BEFORE the per-char space→hyphen (mirroring github-slugger's
    // leading .trim()) so leading/trailing whitespace does NOT become stray edge
    // hyphens; the final ^-+|-+$ strips any hyphen run left by a kept literal '-'.
    return String(text)
      .toLowerCase()
      .replace(/<[^>]+>/g, '')
      .replace(/[^\w\s-]/g, '')
      .trim()
      .replace(/\s/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  // GitHub-compatible per-document anchor de-duplication. slugify() alone
  // maps two identically-titled headings to the same id, producing duplicate
  // DOM ids; getElementById then resolves every such link to the first node.
  // A slugger instance tracks ids emitted within one render: the first
  // occurrence keeps the bare slug (existing anchors stay stable), repeats
  // get `-1`, `-2`, … exactly as GitHub renders them. The `used` set also
  // guards the pathological cross-collision ("Foo","Foo","Foo 1") that
  // GitHub itself renders non-uniquely — we bump further so a DOM id is
  // never duplicated. Construct one per render / per extractHeadings call.
  function makeUniqueSlugger() {
    const used = new Set();
    const counts = new Map();
    return function uniqueSlug(text) {
      const base = slugify(text);
      let n = counts.get(base) || 0;
      let candidate = base;
      while (used.has(candidate)) {
        n += 1;
        candidate = `${base}-${n}`;
      }
      counts.set(base, n);
      used.add(candidate);
      return candidate;
    };
  }

  function stripInlineMarkersForSlug(text) {
    return String(text)
      // Inline HTML tags + comments — must run BEFORE the link/code/etc
      // rules so an `<a id="sec-X.Y.Z"></a>` (post-2026-05-25 heading
      // anchor convention) or `<!-- secref:... -->` marker doesn't
      // leak through to the displayed outline entry as literal HTML.
      // The matching `slugify()` already does this for the slug ID;
      // this keeps the displayed text in sync with the slug.
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/<\/?[a-zA-Z][^>]*>/g, '')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\$([^$]+)\$/g, '$1')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/__([^_]+)__/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/(?<!\w)_([^_]+)_(?!\w)/g, '$1');
  }

  function sectionSlugAt(source, position) {
    const src = String(source || '');
    let cursor = Math.min(Math.max(0, position | 0), src.length);
    while (cursor > 0) {
      let lineStart = cursor;
      while (lineStart > 0 && src[lineStart - 1] !== '\n') lineStart--;
      let lineEnd = lineStart;
      while (lineEnd < src.length && src[lineEnd] !== '\n') lineEnd++;
      const line = src.slice(lineStart, lineEnd);
      const m = line.match(/^(#{1,6})\s+(.*?)\s*$/);
      if (m) {
        const stripped = stripInlineMarkersForSlug(m[2]);
        const slug = slugify(stripped);
        return slug || 'top';
      }
      if (lineStart === 0) break;
      cursor = lineStart - 1;
    }
    return 'top';
  }

  function nextNoteIdForSection(source, sectionSlug) {
    const slug = String(sectionSlug || 'top');
    const re = new RegExp('note-' + escapeRegExp(slug) + '-(\\d+)\\b', 'g');
    let max = 0;
    let m;
    const src = String(source || '');
    while ((m = re.exec(src)) !== null) {
      const n = parseInt(m[1], 10);
      if (Number.isFinite(n) && n > max) max = n;
    }
    return 'note-' + slug + '-' + (max + 1);
  }


  // ── The render pipeline's two pure string transforms ──────────────────────
  //
  // Extracted verbatim from viewer.js so that OFFLINE CHECKERS DRIVE THE SAME
  // CODE THE BROWSER DOES.  viewer/tools/verify-katex-render.cjs previously
  // reimplemented a subset of this pipeline: it omitted markdown-it-mark and
  // knew nothing of the `==color: $$` display-math wrapper, so it counted the
  // viewer's own highlight markup as a `$$` "leak" (false positives) while
  // being blind to genuinely corrupted `==` markup (false negatives -- it
  // passed on all three documents corrupted by bugs/2026-07-09-02).
  //
  // A checker that re-implements the thing it checks tests its own copy.
  // Both consumers now import these.

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

  // ── Inline-span boundary snapping ────────────────────────────────────────
  //
  // A wrapping action (==color: ... ==, **bold**, *italic*, `code`) splices a
  // delimiter pair into the source at offsets derived from the RENDERED text.
  // Markdown emphasis delimiters are absent from the rendered text, so a
  // selection that visually begins at "motion" maps to an offset *inside*
  // `*motion*` — between the `*` and the `m`. Splicing there yields
  //
  //     *==blue: motion*  names ... $n$==
  //
  // whose delimiters INTERLEAVE rather than nest: markdown parses `*==blue:
  // motion*` as an emphasis span holding the literal text `==blue: motion`, and
  // the closing `==` is orphaned. The marker renders as source. See bugs/
  // 2026-07-09-02 (observed three times in one reading session, on `*motion*`,
  // `*First*` and `**normalized Doppler**`).
  //
  // The invariant: an inserted delimiter pair must NEST with every existing
  // inline span, never interleave with one. A selection strictly inside a span
  // is fine (`*mo==x==n*` is legal); only a boundary that cuts a span is not.
  //
  // Math is masked before scanning, because `*` and `` ` `` occur inside KaTeX
  // (`a^*`, `\ast`) and must never be read as emphasis delimiters.

  const _WRAP_SPAN_RE = [
    /`[^`\n]+`/g,          // code spans
    /\*\*[^\n]*?\*\*/g,    // strong
    /\*[^*\n]+?\*/g,       // emphasis
  ];

  function _maskMath(src) {
    // Replace math spans (and their delimiters) with same-length filler so that
    // offsets are preserved but no `*`/backtick inside them can match.
    let out = src;
    const blank = (m) => ' '.repeat(m.length);
    out = out.replace(/\$\$[\s\S]*?\$\$/g, blank);
    out = out.replace(/\$[^$\n]+?\$/g, blank);
    return out;
  }

  function _spansOf(masked) {
    const spans = [];
    let work = masked;
    for (const re of _WRAP_SPAN_RE) {
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(work)) !== null) {
        spans.push([m.index, m.index + m[0].length]);
      }
      // blank out what we matched so the next (weaker) pattern cannot re-match
      // inside it — notably `**a**` must not also be seen as `*` + `*a*` + `*`.
      for (const [s, e] of spans) {
        work = work.slice(0, s) + ' '.repeat(e - s) + work.slice(e);
      }
    }
    return spans;
  }

  /**
   * Move selStart/selEnd outward so neither boundary sits strictly inside an
   * inline-markup span that the selection does not fully contain.
   *
   * Returns {selStart, selEnd, changed}. Pure; never throws.
   */
  function snapOutOfInlineSpans(source, selStart, selEnd) {
    const src = String(source || '');
    let s = Math.max(0, Math.min(selStart, src.length));
    let e = Math.max(s, Math.min(selEnd, src.length));
    const spans = _spansOf(_maskMath(src));
    let changed = false;

    // Iterate to a fixpoint: snapping outward can expose an enclosing span.
    for (let guard = 0; guard < 8; guard++) {
      let moved = false;
      for (const [a, b] of spans) {
        // start cuts the span, and the span closes within the selection
        if (a < s && s < b && b <= e) { s = a; moved = true; }
        // end cuts the span, and the span opens within the selection
        else if (s <= a && a < e && e < b) { e = b; moved = true; }
        // span fully contains the selection -> legal nesting, leave alone
      }
      if (!moved) break;
      changed = true;
    }
    return { selStart: s, selEnd: e, changed };
  }

  return {
    DEFAULT_HIGHLIGHT_COLOR,
    HIGHLIGHT_COLORS,
    HIGHLIGHT_COLOR_SET,
    snapOutOfInlineSpans,
    processHighlights,
    shieldDisplayMath,
    HL_COLOR_ALT,
    escapeRegExp,
    normalizeWhitespace,
    lineStartsOf,
    lineOfOffset,
    makeInlineHighlightId,
    makeSidecarHighlightId,
    extractInlineHighlights,
    resolveFootnoteDefs,
    materializeManifestEntry,
    slugify,
    makeUniqueSlugger,
    stripInlineMarkersForSlug,
    sectionSlugAt,
    nextNoteIdForSection,
  };
});
