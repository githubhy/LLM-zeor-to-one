(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    const shared = require('./highlight-shared');
    module.exports = factory(shared);
  } else {
    root.ViewerNoteMutation = factory(root.ViewerHighlightShared || {});
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function(shared) {
  'use strict';

  function formatBody(body) {
    const text = String(body == null ? '' : body);
    if (!text.includes('\n')) return text;
    const lines = text.split('\n');
    return lines[0] + '\n' + lines.slice(1).map(function(l) { return '    ' + l; }).join('\n');
  }

  function findParagraphEnd(source, fromPos) {
    let i = fromPos;
    while (i < source.length) {
      if (source[i] === '\n' && (i + 1 === source.length || source[i + 1] === '\n')) {
        return i;
      }
      i++;
    }
    return source.length;
  }

  function addNote(source, entry, body, sectionSlug) {
    if (!entry || typeof entry.sourceEnd !== 'number') {
      throw new Error('addNote: entry missing sourceEnd');
    }
    const noteId = shared.nextNoteIdForSection(source, sectionSlug || 'top');
    const refSnippet = '[^' + noteId + ']';
    const paraEnd = findParagraphEnd(source, entry.sourceEnd);
    const defSnippet = '\n\n[^' + noteId + ']: ' + formatBody(body);
    // Apply edits in reverse source order: def at paraEnd first, then ref at sourceEnd.
    const withDef = source.slice(0, paraEnd) + defSnippet + source.slice(paraEnd);
    const final = withDef.slice(0, entry.sourceEnd) + refSnippet + withDef.slice(entry.sourceEnd);
    return { newSource: final, noteId };
  }

  function editNote(source, entry, newBody) {
    if (!entry || !entry.noteId || entry.noteDefStart == null || entry.noteDefEnd == null) {
      throw new Error('editNote: entry has no note');
    }
    const newDef = '[^' + entry.noteId + ']: ' + formatBody(newBody);
    return source.slice(0, entry.noteDefStart) + newDef + source.slice(entry.noteDefEnd);
  }

  function deleteNote(source, entry) {
    if (!entry || !entry.noteId || entry.noteDefStart == null || entry.noteDefEnd == null) {
      throw new Error('deleteNote: entry has no note');
    }
    // Reverse-order edits: def first (later position), then ref (earlier).
    // Strip the def AND the blank-line block separator that addNote inserted before it.
    let defStart = entry.noteDefStart;
    let defEnd = entry.noteDefEnd;
    // Eat one trailing newline if present (def ended at end-of-line, not end-of-file).
    if (defEnd < source.length && source[defEnd] === '\n') defEnd++;
    // Eat the leading blank-line block separator that precedes the def.
    while (defStart > 0 && source[defStart - 1] === '\n') {
      if (defStart >= 2 && source[defStart - 1] === '\n' && source[defStart - 2] === '\n') {
        defStart--;
        break;
      }
      defStart--;
    }
    const withoutDef = source.slice(0, defStart) + source.slice(defEnd);
    // Now strip ref. Positions in withoutDef are unchanged for offsets < defStart.
    const refStart = entry.noteRefStart;
    const refEnd = entry.noteRefEnd;
    return withoutDef.slice(0, refStart) + withoutDef.slice(refEnd);
  }

  function cascadeDeleteHighlight(source, entry) {
    if (!entry || typeof entry.sourceStart !== 'number' || typeof entry.sourceEnd !== 'number') {
      throw new Error('cascadeDeleteHighlight: entry missing source positions');
    }
    if (typeof entry.innerStart !== 'number' || typeof entry.innerEnd !== 'number') {
      throw new Error('cascadeDeleteHighlight: entry missing inner positions');
    }
    // If a note is attached, strip def + ref first via deleteNote (operates on later positions).
    let working = source;
    if (entry.noteId && entry.noteDefStart != null && entry.noteDefEnd != null) {
      working = deleteNote(working, entry);
    }
    // Now strip the ==color: prefix and trailing == markers, PRESERVING inner text.
    // Apply edits in reverse source order: closing == first (later position), then ==color: prefix (earlier).
    // entry.sourceStart/innerStart/innerEnd/sourceEnd are still valid in `working` because deleteNote only
    // touched positions >= noteRefStart > sourceEnd.
    const afterCloseStrip = working.slice(0, entry.innerEnd) + working.slice(entry.sourceEnd);
    return afterCloseStrip.slice(0, entry.sourceStart) + afterCloseStrip.slice(entry.innerStart);
  }

  // Recolor an inline highlight by rewriting ONLY the `==color:` opener via
  // authoritative source offsets. Inner text + closing `==` + any absorbed
  // note ref are kept byte-for-byte (they may hold links, `code`, $math$, or
  // CRLF that the rendered DOM does not reproduce — the reason the old
  // textContent→regex relocation failed for "rich" highlights).
  function recolorHighlight(source, entry, newColor) {
    if (!entry || typeof entry.sourceStart !== 'number' || typeof entry.sourceEnd !== 'number') {
      throw new Error('recolorHighlight: entry missing source positions');
    }
    if (typeof entry.innerStart !== 'number') {
      throw new Error('recolorHighlight: entry missing inner positions');
    }
    const colorSet = shared.HIGHLIGHT_COLOR_SET;
    if (!colorSet || !colorSet.has(newColor)) {
      throw new Error('recolorHighlight: invalid color ' + newColor);
    }
    // [sourceStart, innerStart) is exactly `==` (+ optional `oldcolor:\s*`).
    // Everything from innerStart onward (inner text, closing `==`, note ref,
    // and the rest of the file) is preserved unchanged.
    return source.slice(0, entry.sourceStart)
      + '==' + newColor + ': '
      + source.slice(entry.innerStart);
  }

  return {
    addNote,
    editNote,
    deleteNote,
    cascadeDeleteHighlight,
    recolorHighlight,
    formatBody,        // exposed for testability
    findParagraphEnd,  // exposed for testability
  };
});
