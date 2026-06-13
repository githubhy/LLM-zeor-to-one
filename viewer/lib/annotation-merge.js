// Annotation merge — LWW-by-updatedAt with retained tombstones. Pure; Node + browser + Worker.
(function (root) {
  'use strict';
  function ts(h) { return Number(h && h.updatedAt) || 0; }
  // Union two highlight arrays by id; for each id keep the entry with the larger
  // updatedAt (ties keep `b`). Tombstones (deleted:true) participate as normal
  // entries and are RETAINED in the result so deletions converge across devices.
  function mergeHighlights(a, b) {
    const byId = new Map();
    for (const h of Array.isArray(a) ? a : []) if (h && h.id) byId.set(h.id, h);
    for (const h of Array.isArray(b) ? b : []) {
      if (!h || !h.id) continue;
      const cur = byId.get(h.id);
      if (!cur || ts(h) >= ts(cur)) byId.set(h.id, h);
    }
    return [...byId.values()];
  }
  // Merge two full sidecar docs ({version,file,highlights}) → merged doc.
  function mergeDocs(localDoc, remoteDoc, file) {
    const a = (localDoc && localDoc.highlights) || [];
    const b = (remoteDoc && remoteDoc.highlights) || [];
    return {
      version: 1,
      file: file || (remoteDoc && remoteDoc.file) || (localDoc && localDoc.file) || null,
      highlights: mergeHighlights(a, b),
    };
  }
  // Drop tombstones for rendering.
  function liveHighlights(doc) {
    return ((doc && doc.highlights) || []).filter((h) => !h.deleted);
  }
  const api = { mergeHighlights, mergeDocs, liveHighlights };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) { root.mergeHighlights = mergeHighlights; root.mergeDocs = mergeDocs; root.liveHighlights = liveHighlights; }
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : null));
