// Citation builder — pure functions, no DOM mutation.
// Called from the highlight toolbar's cite-rich / cite-md actions.
//
// Exposes `window.buildCitation` (browser) and module.exports (Node/tests).

(function (root) {
  'use strict';

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function encodePathSegment(p) {
    // Preserve forward slashes, URL-encode everything else per segment.
    return String(p)
      .split('/')
      .map((seg) => encodeURIComponent(seg))
      .join('/');
  }

  function collapseSelection(text) {
    // Preserve newlines between blocks (just trim trailing/leading ws).
    return String(text == null ? '' : text).replace(/\s+$/g, '').replace(/^\s+/, '');
  }

  function quoteMarkdown(text) {
    // Produce a markdown blockquote that preserves interior newlines.
    const lines = String(text).split(/\r?\n/);
    return lines.map((l) => '> ' + l).join('\n');
  }

  function buildFragment(linkMode, anchorId, usedHeadingFallback) {
    if (!anchorId) return '';
    // GitHub's sanitizer prefixes `user-content-` onto user-authored HTML id
    // attributes (e.g., <a id="p-foo"> becomes <a id="user-content-p-foo">).
    // Heading slugs come from the markdown renderer itself and are NOT
    // prefixed, so the fallback-to-heading path must emit the bare slug.
    if (linkMode === 'github' && !usedHeadingFallback) return 'user-content-' + anchorId;
    return anchorId;
  }

  function buildUrl(opts, anchorId, warnings, usedHeadingFallback) {
    const {
      linkMode, gitInfo, relPath, viewerOrigin,
    } = opts;
    const frag = buildFragment(linkMode, anchorId, usedHeadingFallback);
    const fragSuffix = frag ? '#' + frag : '';
    const encPath = encodePathSegment(relPath || '');

    if (linkMode === 'github') {
      if (!gitInfo || !gitInfo.available) {
        warnings.push('GitHub info unavailable — using relative path');
        return { url: (relPath || '') + fragSuffix, effectiveMode: 'relative' };
      }
      if (gitInfo.headPushed === false) {
        warnings.push('HEAD not pushed — GitHub link may 404 until you push');
      } else if (gitInfo.headPushed == null) {
        warnings.push('Cannot verify push status — GitHub link may 404');
      }
      const { owner, repo, sha } = gitInfo;
      return {
        url: `https://github.com/${owner}/${repo}/blob/${sha}/${encPath}${fragSuffix}`,
        effectiveMode: 'github',
      };
    }

    if (linkMode === 'local') {
      const origin = (viewerOrigin || '').replace(/\/+$/, '');
      return {
        url: `${origin}/?file=${encodeURIComponent(relPath || '')}${fragSuffix}`,
        effectiveMode: 'local',
      };
    }

    // relative
    return { url: (relPath || '') + fragSuffix, effectiveMode: 'relative' };
  }

  function buildCitation(input) {
    const opts = input || {};
    const warnings = [];
    const selectedText = collapseSelection(opts.selectedText || '');

    let anchorId = opts.paragraphAnchorId || null;
    let usedHeadingFallback = false;
    if (!anchorId) {
      anchorId = opts.headingAnchorId || null;
      usedHeadingFallback = !!anchorId;
    }

    const { url, effectiveMode } = buildUrl(opts, anchorId, warnings, usedHeadingFallback);

    const documentTitle = opts.documentTitle || opts.relPath || '';
    const headingText = opts.headingText || '';
    const relPath = opts.relPath || '';
    const sourceLine = opts.sourceLine != null ? Number(opts.sourceLine) : null;

    // Attribution bits
    const locSuffix = (usedHeadingFallback && sourceLine != null)
      ? ` (L${sourceLine})`
      : '';
    const sectionBit = headingText ? ` § ${headingText}` : '';

    // plainText
    const plainAttribution = `${documentTitle}${sectionBit} (${relPath}${sourceLine != null ? ':L' + sourceLine : ''})`;
    const plainText = `"${selectedText}" — ${plainAttribution}`;

    // markdown
    let mdLink;
    if (effectiveMode === 'relative') {
      const pathPart = url;
      mdLink = `\`${pathPart}\``;
    } else {
      mdLink = `[${documentTitle}${sectionBit}](${url})`;
    }
    const markdown = `${quoteMarkdown(selectedText)}\n>\n> — ${mdLink}${locSuffix}`;

    // html
    const htmlQuote = `<blockquote>${escapeHtml(selectedText).replace(/\r?\n/g, '<br>')}</blockquote>`;
    const htmlAttrLabel = escapeHtml(`${documentTitle}${sectionBit}${locSuffix}`);
    let htmlAttr;
    if (effectiveMode === 'relative') {
      htmlAttr = `<p><em>—</em> <code>${escapeHtml(url)}</code>${locSuffix ? ' ' + escapeHtml(locSuffix.trim()) : ''}</p>`;
    } else {
      htmlAttr = `<p><em>—</em> <a href="${escapeHtml(url)}">${htmlAttrLabel}</a></p>`;
    }
    const html = htmlQuote + htmlAttr;

    return {
      url,
      anchorId,
      html,
      markdown,
      plainText,
      warnings,
      effectiveMode,
      usedHeadingFallback,
    };
  }

  // Resolve the repo-root-relative path for a viewer-relative file.
  // The /api/git-info endpoint returns `repoRelDir` (the viewer target dir,
  // relative to the git repo root). GitHub blob URLs must embed the full
  // path, not just the basename — otherwise citation URLs 404 whenever the
  // viewer is launched against a subtree like `surveys/xxx/`.
  function resolveRepoPath(currentFile, gitInfo) {
    const f = String(currentFile || '');
    if (!gitInfo || !gitInfo.available) return f;
    const prefix = String(gitInfo.repoRelDir || '').replace(/^[\\/]+|[\\/]+$/g, '');
    if (!prefix) return f;
    return prefix + '/' + f;
  }

  // Extract citation-ready text from a DOM Range while (a) replacing each
  // KaTeX span with its LaTeX source so MathML + rendered glyphs are not
  // concatenated, and (b) collapsing the inline-span layout whitespace KaTeX
  // introduces. Exported for unit testing; the browser wraps it around
  // `savedRange.cloneContents()` at call time.
  //
  // The caller supplies the cloned fragment so this function stays DOM-only
  // and works in both the browser and a JSDOM test harness.
  function katexAwareText(fragment) {
    if (!fragment) return '';
    const katexNodes = fragment.querySelectorAll('span.katex');
    katexNodes.forEach((k) => {
      // KaTeX output:'html' (bug 2026-06-10-01) carries the TeX source on a
      // data-tex attribute; the MathML <annotation> fallback covers DOM
      // produced by the legacy htmlAndMathml output.
      const attrTex = (typeof k.getAttribute === 'function' && k.getAttribute('data-tex')) || '';
      const ann = k.querySelector('annotation[encoding="application/x-tex"]');
      const tex = (attrTex && attrTex.trim())
        || ((ann && ann.textContent) ? ann.textContent.trim() : '');
      const isDisplay = (k.classList && k.classList.contains('katex-display'))
        || !!(k.closest && k.closest('.katex-display'));
      const delim = isDisplay ? '$$' : '$';
      const replacement = tex ? (delim + tex + delim) : '';
      const doc = fragment.ownerDocument || (typeof document !== 'undefined' ? document : null);
      if (!doc) return;
      k.replaceWith(doc.createTextNode(replacement));
    });
    fragment.querySelectorAll('.katex-mathml').forEach((n) => n.remove());
    const raw = fragment.textContent || '';
    return raw
      .split(/\n/)
      .map((line) => line.replace(/[ \t\u00A0\u200B]+/g, ' ').replace(/\s+$/g, ''))
      .join('\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  const api = { buildCitation, resolveRepoPath, katexAwareText };
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.buildCitation = buildCitation;
    root.resolveRepoPath = resolveRepoPath;
    root.katexAwareText = katexAwareText;
  }
})(typeof window !== 'undefined' ? window : null);
