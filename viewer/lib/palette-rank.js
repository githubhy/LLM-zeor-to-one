// viewer/lib/palette-rank.js
// Pure fuzzy ranking/filter for the command palette (spec 2026-06-10 section 4).
// No DOM, no globals touched: callers inject the item arrays. Dual export so
// node:test can require() it and the browser gets window.PaletteRank.
(function (root) {
  'use strict';

  const BOUNDARY = /[\s\-_/.]/;

  // Greedy first-occurrence subsequence match with positional bonuses.
  // Returns { score, positions } or null when `query` is not a subsequence
  // of `text` (case-insensitive). Empty query -> { score: 0, positions: [] }.
  function fuzzyScore(query, text) {
    const t = String(text == null ? '' : text);
    const q = String(query == null ? '' : query);
    if (!q) return { score: 0, positions: [] };
    const tl = t.toLowerCase();
    const ql = q.toLowerCase();
    let qi = 0, score = 0, prev = -2;
    const positions = [];
    for (let ti = 0; ti < tl.length && qi < ql.length; ti++) {
      if (tl[ti] !== ql[qi]) continue;
      let bonus = 1;
      if (ti === prev + 1) bonus += 3;                              // consecutive
      if (ti === 0 || BOUNDARY.test(tl[ti - 1])) bonus += 2;        // word boundary
      score += bonus;
      positions.push(ti);
      prev = ti;
      qi++;
    }
    if (qi < ql.length) return null;                               // unmatched query chars
    // Tie-breakers: prefer shorter text and an earlier first match.
    score -= tl.length * 0.01;
    score -= positions[0] * 0.1;
    return { score, positions };
  }

  // Score every item on item[opts.key] (default 'text'), drop non-matches,
  // sort by score desc with a STABLE tie-break (original index), slice to
  // opts.limit. Returns new objects = item plus { score, positions }.
  function rankItems(query, items, opts) {
    const key = (opts && opts.key) || 'text';
    const limit = opts && typeof opts.limit === 'number' ? opts.limit : Infinity;
    const scored = [];
    for (let i = 0; i < items.length; i++) {
      const r = fuzzyScore(query, items[i][key]);
      if (r) scored.push({ item: items[i], i, score: r.score, positions: r.positions });
    }
    scored.sort((a, b) => (b.score - a.score) || (a.i - b.i));
    const out = [];
    for (let k = 0; k < scored.length && k < limit; k++) {
      out.push(Object.assign({}, scored[k].item, { score: scored[k].score, positions: scored[k].positions }));
    }
    return out;
  }

  const api = { fuzzyScore, rankItems };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.PaletteRank = api;
})(typeof window !== 'undefined' ? window : null);
