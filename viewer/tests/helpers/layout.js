// Pin the pre-redesign CLASSIC layout for legacy suites that exercise the
// docked sidebar / settings gear / top progress bar at desktop width.
// Redesign 02 made READER the desktop default (data-layout attribute, plan
// 2026-06-11-viewer-redesign-02), which sends the sidebar off-canvas and
// hides those affordances — the legacy suites pin the classic contract,
// while reader-mode coverage lives in reader-shell.spec.js.
//
// The init script MERGES into the stored settings instead of replacing
// them, so persistence-across-reload flows (settings-groups G2/G6/G8,
// progress-and-outline-sync test 5) keep their own keys intact.
async function pinClassicLayout(page) {
  await seedSettings(page, { layout: 'classic' });
}

// Merge-write arbitrary settings into the namespaced store before page load.
// Tests must seed via this (NOT the legacy viewer-* localStorage keys): the
// store only migrates legacy keys when viewer.settings.v1 is absent, and
// pinClassicLayout creates it — a legacy seed after the pin is silently
// ignored (citation T5/T6/T11 regression, 2026-06-12). Legacy migration
// itself is covered by tests/unit/settings-store.test.js.
async function seedSettings(page, patch) {
  await page.addInitScript((p) => {
    const KEY = 'viewer.settings.v1';
    let s = {};
    try { s = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { s = {}; }
    Object.assign(s, p);
    localStorage.setItem(KEY, JSON.stringify(s));
  }, patch);
}

module.exports = { pinClassicLayout, seedSettings };
