/* discover-routes.cjs — route + STATE-MATRIX manifest for the markdown viewer's
 * ui-review-loop. Unlike a Next.js site there are no app routes: a "route" here
 * is ONE markdown doc loaded via `?file=<relpath>`, and the REAL review dimension
 * is the per-doc STATE MATRIX (chrome × theme × density × width × marginNotes),
 * seeded into localStorage['viewer.settings.v1'] before load.
 *
 * Usage (no server needed — it just reads the served dir):
 *   node .../discover-routes.cjs <content-dir> [--all] [--base http://localhost:PORT] > routes.json
 *
 * It enumerates the served dir's .md/.markdown files, picks a CURATED few
 * (a long math-heavy doc, a mid doc, a short doc) unless --all is given, honours
 * surveys/<name>/order.json ordering when present, and emits both the doc list
 * and the STATE_MATRIX the capture step replays. REVIEW the output: swap in a
 * different long doc if the auto-pick missed your math/table/code-heavy page. */
const fs = require("fs");
const path = require("path");

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
}
const CONTENT_DIR = path.resolve(process.argv[2] && !process.argv[2].startsWith("--") ? process.argv[2] : ".");
const ALL = process.argv.includes("--all");
const BASE = arg("base", "http://localhost:3000");

if (!fs.existsSync(CONTENT_DIR) || !fs.statSync(CONTENT_DIR).isDirectory()) {
  console.error(`ERROR: content dir not found or not a directory: ${CONTENT_DIR}`);
  process.exit(1);
}

// Recursively collect markdown files (relative POSIX paths within the served dir).
function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith(".")) continue; // skip .viewer-highlights, .git, etc.
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, acc);
    else if (/\.(md|markdown)$/i.test(e.name)) acc.push(full);
  }
  return acc;
}

let files = walk(CONTENT_DIR).map((f) => path.relative(CONTENT_DIR, f).split(path.sep).join("/"));

// Honour a survey order.json (top-level) when present, so docs sort meaningfully.
try {
  const order = JSON.parse(fs.readFileSync(path.join(CONTENT_DIR, "order.json"), "utf8"));
  if (Array.isArray(order)) {
    const rank = new Map(order.map((n, i) => [n, i]));
    files.sort((a, b) => (rank.has(a) ? rank.get(a) : 1e6) - (rank.has(b) ? rank.get(b) : 1e6) || a.localeCompare(b));
  }
} catch { files.sort(); }

const sizeOf = (rel) => { try { return fs.statSync(path.join(CONTENT_DIR, rel)).size; } catch { return 0; } };

// Curate a small representative set: the largest (math/table/code-heavy), a
// mid-size, and the smallest non-trivial doc. The doc COUNT is deliberately
// small — coverage comes from the state matrix, not from route count.
function curate(list) {
  if (ALL || list.length <= 3) return list;
  const sorted = [...list].sort((a, b) => sizeOf(b) - sizeOf(a));
  const pick = new Set();
  pick.add(sorted[0]);                                   // largest (math/tables/code)
  pick.add(sorted[Math.floor(sorted.length / 2)]);       // median
  pick.add(sorted[sorted.length - 1]);                   // smallest
  // Prefer an index.md as the short doc if one exists (entry point readers see first).
  const idx = list.find((f) => /(^|\/)index\.md$/i.test(f));
  if (idx) pick.add(idx);
  return list.filter((f) => pick.has(f));
}

const chosen = curate(files);

const routes = chosen.map((rel) => {
  const key = rel.replace(/\.(md|markdown)$/i, "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase();
  const bytes = sizeOf(rel);
  return {
    key,
    label: rel,
    file: rel,
    url: `/?file=${encodeURIComponent(rel)}`,
    bytes,
    // The largest chosen doc gets the heaviest matrix + full-page shots; small
    // docs render fast so their full-page shot is cheap too.
    heavy: bytes >= 60000,
  };
});

// ── STATE MATRIX ──────────────────────────────────────────────────────────
// Each entry is one CAPTURE: a viewport + a settings patch seeded into
// localStorage['viewer.settings.v1'] BEFORE load (Playwright addInitScript), plus
// the DOM facts the capture verifies took effect. `fullpage` shots auto-scroll
// first to trigger lazy KaTeX/mermaid below the fold.
//
// Width rules: desktop = 1440; the three-zone / split / margin states that need
// the wide-desktop CSS gate use 1500 (≥1440 for split, ≥1400 for right-pane &
// sidenotes — 1500 clears both). Mobile = 390 (isMobile).
//
// `expect` keys map to DOM assertions in capture.cjs:
//   chrome  -> html[data-chrome]
//   theme   -> html[data-theme]  (omitted/absent when light)
//   immersive -> html.immersive present (chrome reader|focus)
//   density -> html.density-<v>
const STATE_MATRIX = [
  { id: "docs-light",          group: "core",     viewport: { w: 1440, h: 900 }, settings: { chrome: "docs",   theme: "light" },                       fullpage: false, expect: { chrome: "docs",   immersive: false } },
  { id: "docs-dark",           group: "core",     viewport: { w: 1440, h: 900 }, settings: { chrome: "docs",   theme: "dark"  },                       fullpage: false, expect: { chrome: "docs",   theme: "dark", immersive: false } },
  { id: "reader-light",        group: "core",     viewport: { w: 1440, h: 900 }, settings: { chrome: "reader", theme: "light" },                       fullpage: true,  expect: { chrome: "reader", immersive: true } },
  { id: "reader-dark",         group: "core",     viewport: { w: 1440, h: 900 }, settings: { chrome: "reader", theme: "dark"  },                       fullpage: false, expect: { chrome: "reader", theme: "dark", immersive: true } },
  { id: "focus-dark",          group: "core",     viewport: { w: 1440, h: 900 }, settings: { chrome: "focus",  theme: "dark"  },                       fullpage: false, expect: { chrome: "focus",  theme: "dark", immersive: true } },
  { id: "sepia-reader",        group: "theme",    viewport: { w: 1440, h: 900 }, settings: { chrome: "reader", theme: "sepia" },                       fullpage: false, expect: { chrome: "reader", theme: "sepia", immersive: true } },
  { id: "density-compact-docs",  group: "density", viewport: { w: 1440, h: 900 }, settings: { chrome: "docs", theme: "light", density: "compact"  },   fullpage: false, expect: { chrome: "docs", density: "compact" } },
  { id: "density-spacious-docs", group: "density", viewport: { w: 1440, h: 900 }, settings: { chrome: "docs", theme: "light", density: "spacious" },   fullpage: false, expect: { chrome: "docs", density: "spacious" } },
  { id: "three-zone-docs",     group: "wide",     viewport: { w: 1500, h: 940 }, settings: { chrome: "docs",   theme: "light" },                       fullpage: false, expect: { chrome: "docs",   immersive: false }, note: "≥1400px → #right-pane visible" },
  { id: "split-view",          group: "wide",     viewport: { w: 1500, h: 940 }, settings: { chrome: "reader", theme: "light" },                       fullpage: false, expect: { chrome: "reader", immersive: true }, openSplit: true, note: "≥1440px → Pane B (#content-b) opened" },
  { id: "margin-notes",        group: "wide",     viewport: { w: 1500, h: 940 }, settings: { chrome: "reader", theme: "light", marginNotes: true },    fullpage: true,  expect: { chrome: "reader", immersive: true }, note: "≥1400px reader → #sidenote-band" },
  { id: "mobile-reader",       group: "mobile",   viewport: { w: 390,  h: 844 }, settings: { chrome: "reader", theme: "light" }, mobile: true,         fullpage: false, expect: { chrome: "reader", immersive: true } },
];

const out = { base: BASE, contentDir: CONTENT_DIR, routes, stateMatrix: STATE_MATRIX };
process.stdout.write(JSON.stringify(out, null, 2) + "\n");
process.stderr.write(
  `discovered ${files.length} md docs in ${CONTENT_DIR}; chose ${routes.length}` +
  `${ALL ? " (--all)" : ""}; ${STATE_MATRIX.length} states → ${routes.length * STATE_MATRIX.length} captures\n`
);
