(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ViewerScrollSync = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function clamp01(x) {
    const n = Number(x);
    if (!Number.isFinite(n)) return 0;
    if (n < 0) return 0;
    if (n > 1) return 1;
    return n;
  }

  // headingTops: ascending array of heading top positions in document
  // coordinates. scanLine: absolute document Y of the now-reading line.
  // Returns the index of the last heading at/above scanLine; 0 if scanLine
  // is above the first heading (always one active entry); -1 if no headings.
  function computeActiveHeadingIndex(headingTops, scanLine) {
    if (!Array.isArray(headingTops) || headingTops.length === 0) return -1;
    let idx = 0;
    for (let i = 0; i < headingTops.length; i++) {
      if (headingTops[i] <= scanLine) idx = i;
      else break;
    }
    return idx;
  }

  // opts: { mode, scrollTop, viewport, docHeight, scanThreshold,
  //         sectionTop, sectionBottom }
  function computeProgress(opts) {
    opts = opts || {};
    const mode = opts.mode;
    const scrollTop = Number(opts.scrollTop) || 0;
    const viewport = Number(opts.viewport) || 0;
    const docHeight = Number(opts.docHeight) || 0;
    const scanThreshold = Number(opts.scanThreshold) || 0;
    const sectionTop = opts.sectionTop;
    const sectionBottom = opts.sectionBottom;
    if (mode === 'section'
        && Number.isFinite(sectionTop) && Number.isFinite(sectionBottom)
        && sectionBottom > sectionTop) {
      return clamp01((scrollTop + scanThreshold - sectionTop)
                     / Math.max(1, sectionBottom - sectionTop));
    }
    return clamp01(scrollTop / Math.max(1, docHeight - viewport));
  }

  return { clamp01, computeActiveHeadingIndex, computeProgress };
});
