// viewer/lib/figure-pipeline.js
// Spec-driven, framework-free renderer for a canonical block-diagram pipeline
// figure (e.g. a method/architecture pipeline in a survey section).
//
// render(spec, styleId) -> HTML string (no DOM nodes), so it is unit-testable in
// Node with no DOM AND usable in the browser via `el.innerHTML = render(...)`.
// The viewer (progressive enhancement) and any offline bake script (a sibling
// figures/bake.js) both call the same function, so the embedded fallback PNG and
// the live figure are the same drawing.
//
// Styles (curated set, all pure HTML/CSS, all reflow on a narrow column via a
// container query): colour-academic (default), monochrome, minimal, swimlane.
// 'image' is handled by the caller (keep the static <img>); render() is not
// called for it.
(function (root) {
  'use strict';

  const STYLES = [
    { id: 'colour-academic', label: 'Colour academic' },
    { id: 'monochrome',      label: 'Monochrome' },
    { id: 'minimal',         label: 'Minimal line' },
    { id: 'swimlane',        label: 'Swimlane tiers' },
    { id: 'image',           label: 'Static image' },
  ];
  const STYLE_IDS = STYLES.map((s) => s.id);
  const RENDERED_IDS = ['colour-academic', 'monochrome', 'minimal', 'swimlane'];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function io(o, kind) {
    o = o || {};
    return '<div class="fp-io fp-' + kind + '"><span class="fp-iocap">' + esc(o.label || '') + '</span>' +
      (o.sub ? '<span class="fp-iosub">' + esc(o.sub) + '</span>' : '') + '</div>';
  }
  function arr(lab) {
    return '<div class="fp-arr">' + (lab ? '<span class="fp-lab">' + esc(lab) + '</span>' : '') +
      '<span class="fp-gl-h" aria-hidden="true">→</span><span class="fp-gl-v" aria-hidden="true">↓</span></div>';
  }
  function box(s, groups) {
    const col = (groups[s.group] && groups[s.group].color) || '#888888';
    return '<div class="fp-box fp-g-' + esc(s.group) + (s.highlight ? ' fp-hot' : '') +
      '" style="--gc:' + esc(col) + '">' +
      '<div class="fp-t">' + esc(s.title) + '</div>' +
      (s.detail ? '<div class="fp-d">' + esc(s.detail) + '</div>' : '') +
      (s.ref ? '<div class="fp-r">' + esc(s.ref) + '</div>' : '') +
      '</div>';
  }

  function renderLinear(spec, styleId) {
    const groups = spec.groups || {};
    const stages = spec.stages || [];
    const edges = spec.edges || [];
    let h = '<div class="fp fp-linear fp-' + esc(styleId) + '" role="img" aria-label="' +
      esc(spec.title || 'pipeline') + '">';
    h += io(spec.input, 'in');
    h += arr('');
    stages.forEach((s, i) => {
      if (i > 0) h += arr(edges[i - 1] || '');
      h += box(s, groups);
    });
    h += arr('');
    h += io(spec.output, 'out');
    h += '</div>';
    return h;
  }

  function renderSwimlane(spec) {
    const groups = spec.groups || {};
    const stages = spec.stages || [];
    const order = [];
    const byG = {};
    stages.forEach((s) => {
      if (!byG[s.group]) { byG[s.group] = []; order.push(s.group); }
      byG[s.group].push(s);
    });
    const inp = spec.input || {};
    const out = spec.output || {};
    let h = '<div class="fp fp-swimlane" role="img" aria-label="' + esc(spec.title || 'pipeline') + '">';
    h += '<div class="fp-io fp-in"><span class="fp-iocap">' + esc(inp.label || '') + '</span> ' +
      esc(inp.sub || '') + ' <span class="fp-gl-v" aria-hidden="true">↓</span></div>';
    order.forEach((gid, idx) => {
      const g = groups[gid] || {};
      const col = g.color || '#888888';
      h += '<div class="fp-band fp-g-' + esc(gid) + '" style="--gc:' + esc(col) + '">';
      h += '<div class="fp-btag">' + esc(gid) + ' · ' + esc(g.label || '') + '</div>';
      h += '<div class="fp-bstages">';
      byG[gid].forEach((s) => {
        h += '<div class="fp-scard' + (s.highlight ? ' fp-hot' : '') + '">' +
          '<div class="fp-t">' + esc(s.title) + '</div>' +
          '<div class="fp-d">' + esc(s.detail || '') + (s.ref ? ' · ' + esc(s.ref) : '') + '</div></div>';
      });
      h += '</div></div>';
      if (idx < order.length - 1) h += '<div class="fp-down" aria-hidden="true">↓</div>';
    });
    h += '<div class="fp-io fp-out"><span class="fp-gl-v" aria-hidden="true">↓</span> <span class="fp-iocap">' +
      esc(out.label || '') + '</span></div>';
    h += '</div>';
    return h;
  }

  function render(spec, styleId) {
    if (!spec || typeof spec !== 'object') return '';
    if (!RENDERED_IDS.includes(styleId)) styleId = spec.defaultStyle || 'colour-academic';
    if (!RENDERED_IDS.includes(styleId)) styleId = 'colour-academic';
    return styleId === 'swimlane' ? renderSwimlane(spec) : renderLinear(spec, styleId);
  }

  const CSS = [
    /* wrapper — container so the figure reflows on its column width, not the window */
    '.fp-wrap{container-type:inline-size;display:block;position:relative;margin:0}',
    '.fp-wrap img.fp-fallback{width:100%;display:block;border-radius:6px}',
    /* must beat the UA [hidden]{display:none} that the display:block above would
       otherwise override — without this the static PNG shows above the live render */
    '.fp-wrap img.fp-fallback[hidden]{display:none}',
    '.fp-render{font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}',
    /* inline style chip (top-right) */
    '.fp-chip{position:absolute;top:8px;right:8px;z-index:3;font:12px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}',
    '.fp-chip-btn{border:1px solid #d7dde4;background:rgba(255,255,255,.92);border-radius:7px;padding:3px 9px;cursor:pointer;color:#475569;opacity:0;transition:opacity .12s}',
    '.fp-wrap:hover .fp-chip-btn,.fp-chip.open .fp-chip-btn{opacity:1}',
    '.fp-chip-btn:hover{color:#1f2937;border-color:#9aa3b2}',
    '.fp-chip-menu{position:absolute;right:0;top:27px;background:#fff;border:1px solid #e5e7eb;border-radius:9px;box-shadow:0 8px 28px rgba(0,0,0,.14);padding:5px;min-width:158px}',
    '.fp-chip-menu[hidden]{display:none}',
    '.fp-chip-menu button{display:block;width:100%;text-align:left;border:none;background:none;padding:6px 9px;border-radius:6px;cursor:pointer;font-size:12.5px;color:#1f2937}',
    '.fp-chip-menu button:hover{background:#f1f5f9}',
    '.fp-chip-menu button[aria-current="true"]{background:#eef4fb;font-weight:600}',
    /* shared linear scaffold */
    '.fp{--fp-arrow:#94a3b8;--fp-elab:#64748b}',
    '.fp-linear{display:flex;align-items:stretch;justify-content:center;gap:0;flex-wrap:nowrap;padding:8px 2px}',
    '.fp-io{align-self:center;text-align:center;flex:none;padding:0 8px}',
    '.fp-iocap{display:block;font-weight:700;font-size:14px;color:#1f2937}',
    '.fp-iosub{display:block;color:var(--fp-elab);font-size:11px}',
    '.fp-box{flex:1 1 0;min-width:0;padding:11px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;gap:2px}',
    '.fp-t{font-weight:700;font-size:13.5px;line-height:1.22;color:#1f2937}',
    '.fp-d{color:var(--fp-elab);font-size:11.5px}',
    '.fp-r{font-size:10px;font-weight:700;margin-top:3px;letter-spacing:.02em}',
    '.fp-arr{align-self:center;flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--fp-arrow);min-width:30px}',
    '.fp-lab{font-size:10.5px;color:var(--fp-elab);font-style:italic;margin-bottom:1px;white-space:nowrap}',
    '.fp-gl-h{font-size:18px;line-height:1}',
    '.fp-gl-v{display:none;font-size:18px;line-height:1}',
    /* colour-academic */
    '.fp-colour-academic .fp-box{border:1.8px solid var(--gc);background:color-mix(in srgb,var(--gc) 8%,#fff);border-radius:13px;margin:0 3px}',
    /* "Times New Roman" first so a label like "L0" renders with a full-height
       (lining) zero, not Georgia\'s oldstyle zero that reads like an "o" (Lo). */
    '.fp-colour-academic .fp-t{font-family:"Times New Roman",Georgia,serif;font-variant-numeric:lining-nums;font-size:14.5px}',
    '.fp-colour-academic .fp-iocap{font-family:"Times New Roman",Georgia,serif;font-variant-numeric:lining-nums}',
    '.fp-colour-academic .fp-r{color:var(--gc)}',
    '.fp-colour-academic .fp-box.fp-hot{border-color:#ef7d10;background:#ffe9cf;box-shadow:0 0 0 3px color-mix(in srgb,#ef7d10 14%,transparent)}',
    '.fp-colour-academic .fp-box.fp-hot .fp-r{color:#ef7d10}',
    /* monochrome */
    '.fp-monochrome{font-family:"Times New Roman",Georgia,serif;font-variant-numeric:lining-nums}',
    '.fp-monochrome .fp-box{border:1.5px solid #111;background:#fff;border-radius:10px;margin:0 3px}',
    '.fp-monochrome .fp-box.fp-hot{border-width:2.4px;background:#fafafa}',
    '.fp-monochrome .fp-d,.fp-monochrome .fp-r{color:#333}',
    '.fp-monochrome .fp-arr{color:#111}',
    '.fp-monochrome .fp-lab{color:#333}',
    /* minimal */
    '.fp-minimal .fp-box{border:none;background:none;border-radius:0;padding:6px 8px;gap:1px}',
    '.fp-minimal .fp-t{font-size:12.5px}',
    '.fp-minimal .fp-box::before{content:"";display:block;width:12px;height:12px;border-radius:50%;border:2.5px solid var(--gc);margin:0 auto 8px;background:#fff}',
    '.fp-minimal .fp-box.fp-hot::before{width:16px;height:16px;box-shadow:0 0 0 4px color-mix(in srgb,var(--gc) 20%,#fff)}',
    '.fp-minimal .fp-r{color:var(--gc)}',
    '.fp-minimal .fp-arr{min-width:22px}',
    '.fp-minimal .fp-gl-h{font-size:14px;opacity:.5}',
    /* swimlane */
    '.fp-swimlane{display:flex;flex-direction:column;align-items:stretch;gap:0;padding:6px 4px}',
    '.fp-swimlane .fp-io{align-self:center;color:var(--fp-elab);font-size:12px;padding:3px 0}',
    '.fp-swimlane .fp-iocap{display:inline;font-weight:700;color:#1f2937}',
    '.fp-swimlane .fp-gl-v{display:inline;font-size:15px;color:var(--fp-arrow)}',
    '.fp-swimlane .fp-band{display:flex;align-items:center;gap:12px;border:1.6px solid var(--gc);border-radius:12px;padding:10px 12px;background:color-mix(in srgb,var(--gc) 6%,#fff)}',
    '.fp-swimlane .fp-btag{flex:none;font-size:11px;font-weight:700;color:#fff;background:var(--gc);border-radius:7px;padding:7px 10px;max-width:165px;line-height:1.2}',
    '.fp-swimlane .fp-bstages{flex:1;display:flex;gap:10px}',
    '.fp-swimlane .fp-scard{flex:1;background:#fff;border:1px solid #d7dde4;border-radius:8px;padding:9px 10px;text-align:center}',
    '.fp-swimlane .fp-scard .fp-t{font-size:12.5px}',
    '.fp-swimlane .fp-scard .fp-d{color:var(--fp-elab);font-size:10.5px}',
    '.fp-swimlane .fp-scard.fp-hot{border-color:#ef7d10;background:#fff7ed}',
    '.fp-swimlane .fp-down{align-self:center;color:var(--fp-arrow);font-size:18px;padding:2px 0}',
    /* Reflow to a vertical stack whenever the figure\'s column is narrower than a
       comfortable 5-box row needs (~900px). This covers the reader measure
       (~665px) and phones — horizontal only shows in a wide Docs column and in
       the baked PNG. (Container query → keys on the column, not the window.) */
    '@container (max-width:900px){',
    '  .fp-linear{flex-direction:column;align-items:stretch}',
    '  .fp-linear .fp-box{margin:4px 0;width:100%}',
    '  .fp-linear .fp-io{padding:2px 0}',
    '  .fp-linear .fp-arr{min-width:0;flex-direction:row;gap:6px;padding:3px 0}',
    '  .fp-linear .fp-gl-h{display:none}',
    '  .fp-linear .fp-gl-v{display:block}',
    '  .fp-linear .fp-lab{margin-bottom:0}',
    '  .fp-swimlane .fp-bstages{flex-direction:column}',
    '}',
  ].join('\n');

  function ensureStyles() {
    if (typeof document === 'undefined') return;
    if (document.getElementById('fp-css')) return;
    const st = document.createElement('style');
    st.id = 'fp-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  const api = { render, ensureStyles, CSS, STYLES, STYLE_IDS, RENDERED_IDS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.FigurePipeline = api;
})(typeof window !== 'undefined' ? window : null);
