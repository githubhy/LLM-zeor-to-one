// viewer/lib/peek-target.js
// Pure classifier for in-situ peek triggers (spec 2026-06-10 section 8).
// No DOM: turns an href into {kind, id, sameFile}. Dual export so node:test can
// require() it and the browser gets window.PeekTarget.
(function (root) {
  'use strict';
  function parsePeekHref(href) {
    if (typeof href !== 'string' || href.length === 0) return { kind: null, id: null, sameFile: false };
    const sameFile = href.charAt(0) === '#';
    if (!sameFile) return { kind: null, id: null, sameFile: false };
    const m = href.match(/^#(eq|ref|sec)-(.+)$/);
    if (!m) return { kind: null, id: null, sameFile: true };
    return { kind: m[1], id: m[2], sameFile: true };
  }
  const api = { parsePeekHref };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.PeekTarget = api;
})(typeof window !== 'undefined' ? window : null);
