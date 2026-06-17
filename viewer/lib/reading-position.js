// viewer/lib/reading-position.js
// Pure position-label cycling for the mobile reading rail (spec 2026-06-13).
// No DOM. Dual export so node:test can require() it and the browser gets
// window.ReadingPosition.
(function (root) {
  'use strict';
  function nextPositionMode(mode, modes) {
    const i = modes.indexOf(mode);
    return modes[(i + 1) % modes.length];   // unknown (-1) → first
  }
  function formatPosition(mode, ctx) {
    if (mode === 'section' && ctx.section) return ctx.section;
    return Math.round(ctx.pct) + '%';
  }
  const api = { nextPositionMode, formatPosition };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.ReadingPosition = api;
})(typeof window !== 'undefined' ? window : null);
