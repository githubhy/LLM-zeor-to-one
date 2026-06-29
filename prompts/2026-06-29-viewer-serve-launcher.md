# Conversation Log — 2026-06-29 — session: viewer-serve-launcher

## Conversation 1
- **Request**: Add a cross-platform script to fix `node viewer/serve.js -p 3500` crashing with `Error: Cannot find module 'ws'`.
- **Actions**: Diagnosed root cause — `viewer/node_modules` never installed (serve.js hard-requires `ws`). Added paired launchers `scripts/serve-viewer.sh` + `scripts/serve-viewer.ps1` (matching `install-git-hooks.{sh,ps1}` convention) that auto-install viewer deps on first run (canary = `node_modules/ws`; `npm ci` if lockfile else `npm install`), and default the content root to `surveys/` when none is given so a bare `-p <port>` works. Updated `viewer/GUIDE.md` (Install tip, Quick Start launcher block, troubleshooting row). Filed decision `2026-06-29-01`.
- **Result**: Verified end-to-end on both platforms — PowerShell launcher → HTTP 200 on :3598; bash launcher → HTTP 200 on :3597; `ws` installed; `node_modules` gitignored. Working tree adds only the two scripts (+ docs/decision/log).
- **Findings**: `serve.js` needs a content root and the repo ships no `viewer.content.json`, so even after the `ws` fix the user's bare `-p 3500` would hit "no content roots" — the launcher's default-to-`surveys/` closes that gap. `content-source.js` walks subdirs recursively, so `surveys/` surfaces all three surveys.

## Conversation 2
- **Request**: In appendix-a §A.17 ("The Learned Metric M versus the Whitening Σ⁻¹"), make "The four relaxations" more specific and concrete.
- **Actions**: Added a "What each relaxation buys, concretely" block after the summary table — four bold-led paragraphs expanding each relaxation with mechanism + concrete example: (1) asymmetry → directed read, grounded in the worked induction head of §A.9 ([60]) and a code def/use example; (2) indefiniteness → learned repulsion via negative eigenvalues of M_sym; (3) low rank → per-head subspace specialist with first-principles param counts (d=4096,d_k=128,h=32 → ~1.05M vs ~16.8M, ~16×), citing the low-rank "QK circuit" of [59]; (4) learned origin → task structure no noise model produces, framed as the mechanism that fills the other three. Cross-linked sibling §B.8. Verified [59]/[60] against their actual pages via WebFetch before citing (both pre-existing bib entries). Ran renumber-sections + renumber-paragraphs --init + full validation sweep.
- **Result**: All gates green (lint-math 0, validate-refs 0/0, check-citation-sources 0, crosslink no gaps, all --check clean). No new bib entries; no deferred items.
- **Findings**: §A.9 already builds the induction head and §B.8 already frames a parallel "four departures" — so the enrichment reuses/cross-links existing material rather than re-deriving. [59] explicitly names W_Q^T W_K the low-rank "QK circuit"; the rank-≤d_k bound and param counts are first-principles (no citation needed).

<!-- LOG-END -->
