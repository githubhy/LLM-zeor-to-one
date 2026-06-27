/* capture.cjs — replay the STATE MATRIX per doc and screenshot each state for the
 * markdown viewer's ui-review-loop. The viewer is a vanilla-JS SPA: theme / chrome
 * / density / marginNotes are APP STATE in localStorage['viewer.settings.v1'],
 * seeded BEFORE load via Playwright addInitScript — NOT browser colorScheme
 * (exception: theme:'auto' follows colorScheme). There is NO auth / cookie / admin.
 *
 * Run from viewer/ so Playwright resolves (it's a viewer dev dep — see
 * viewer/package.json); require-playwright.cjs also walks up to find it from any
 * cwd. Pass an absolute --routes path:
 *   cd viewer && node <skill>/scripts/capture.cjs --out <dir> --routes <routes.json> \
 *        [--base http://localhost:PORT] [--only docs-light,reader-dark]
 *
 * Writes <out>/img/*.png and <out>/manifest.json. Each shot records the DOM facts
 * verified after the seed (data-chrome / data-theme / immersive / density-*), so a
 * mis-seeded capture is caught here, not by a vision agent downstream. */
const { resolveChromium } = require("./require-playwright.cjs");
const { chromium } = resolveChromium();
const fs = require("fs");
const path = require("path");

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
}
const OUT = path.resolve(arg("out", `reports/ui-review-${new Date().toISOString().slice(0, 10)}`));
const ROUTES_FILE = arg("routes", null);
const ONLY = (arg("only", "") || "").split(",").map((s) => s.trim()).filter(Boolean);

if (!ROUTES_FILE) { console.error("ERROR: --routes <routes.json> required (produce it with discover-routes.cjs)"); process.exit(1); }
const SPEC = JSON.parse(fs.readFileSync(path.resolve(ROUTES_FILE), "utf8"));
const BASE = arg("base", SPEC.base || "http://localhost:3000");
const ROUTES = SPEC.routes || [];
let MATRIX = SPEC.stateMatrix || [];
if (ONLY.length) MATRIX = MATRIX.filter((m) => ONLY.includes(m.id));

const IMG = path.join(OUT, "img");
fs.mkdirSync(IMG, { recursive: true });

const SETTINGS_KEY = "viewer.settings.v1";

// Seed settings into localStorage BEFORE any viewer code runs. This is the heart
// of the adaptation: the FOUC guard + loadSettings() read this exact key, so the
// page boots straight into the target chrome/theme/density with no flash.
function seedInit(page, settings) {
  return page.addInitScript(([key, patch]) => {
    let s = {};
    try { s = JSON.parse(localStorage.getItem(key)) || {}; } catch (e) { s = {}; }
    Object.assign(s, patch);
    localStorage.setItem(key, JSON.stringify(s));
  }, [SETTINGS_KEY, settings]);
}

// Auto-scroll to trigger lazy-rendered KaTeX / mermaid below the fold, then return
// to the top. Tall full-page captures render math blank without this (known artifact).
const autoScroll = (page) =>
  page.evaluate(() => new Promise((res) => {
    let y = 0;
    const step = () => {
      window.scrollBy(0, 900); y += 900;
      if (y >= document.body.scrollHeight) { window.scrollTo(0, 0); setTimeout(res, 500); }
      else setTimeout(step, 70);
    };
    step();
  }));

function ctxOpts(state) {
  const vp = state.viewport || { w: 1440, h: 900 };
  const base = { viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: state.mobile ? 2 : 1 };
  if (state.mobile) { base.isMobile = true; base.hasTouch = true; }
  // For theme:'auto' the viewer follows the OS colorScheme; otherwise pin light so
  // the seeded data-theme is the only thing driving the palette.
  base.colorScheme = state.settings && state.settings.theme === "dark" ? "dark" : "light";
  return base;
}

// Read back the DOM facts the seed should have produced — the audit-resolvable
// artifact (each shot's verified DOM state is recorded ground truth, mirroring
// the repo's audit-trail discipline).
async function readDomState(page) {
  return page.evaluate(() => {
    const h = document.documentElement;
    return {
      chrome: h.getAttribute("data-chrome"),
      theme: h.getAttribute("data-theme"),
      immersive: h.classList.contains("immersive"),
      density: ["compact", "normal", "spacious"].find((d) => h.classList.contains("density-" + d)) || null,
      splitOpen: !!document.getElementById("app") && document.getElementById("app").classList.contains("split-open"),
      sidenoteBand: !!document.getElementById("sidenote-band"),
      rightPaneVisible: (() => { const rp = document.getElementById("right-pane"); if (!rp) return false; const r = rp.getBoundingClientRect(); return r.width > 0 && r.height > 0; })(),
    };
  });
}

function checkExpect(expect, dom) {
  const fails = [];
  if (!expect) return fails;
  if ("chrome" in expect && dom.chrome !== expect.chrome) fails.push(`chrome=${dom.chrome}≠${expect.chrome}`);
  if ("theme" in expect && dom.theme !== expect.theme) fails.push(`theme=${dom.theme}≠${expect.theme}`);
  if ("immersive" in expect && dom.immersive !== expect.immersive) fails.push(`immersive=${dom.immersive}≠${expect.immersive}`);
  if ("density" in expect && dom.density !== expect.density) fails.push(`density=${dom.density}≠${expect.density}`);
  return fails;
}

// Open Pane B (split view) by invoking the palette "Open current section in split"
// command — the same path a user takes. Only works at the ≥1440px gate.
async function openSplit(page) {
  await page.keyboard.press(process.platform === "darwin" ? "Meta+k" : "Control+k");
  await page.waitForTimeout(250);
  await page.locator("#cmd-input").fill(">split");
  await page.waitForTimeout(250);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(500);
}

async function shoot(browser, route, state) {
  const ctx = await browser.newContext(ctxOpts(state));
  const page = await ctx.newPage();
  await seedInit(page, state.settings || {});
  const name = `${route.key}__${state.id}`;
  const file = path.join(IMG, name + ".png");
  const out = { name, stateId: state.id, group: state.group, file: path.relative(OUT, file), status: null, error: null, dom: null, seedFails: [] };
  try {
    const resp = await page.goto(BASE + route.url + "&nocache=1", { waitUntil: "load", timeout: 30000 });
    out.status = resp ? resp.status() : null;
    await page.waitForTimeout(1400);
    try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch {}
    if (state.openSplit) { try { await openSplit(page); } catch (e) { out.error = "openSplit: " + String((e && e.message) || e); } }
    if (state.fullpage) await autoScroll(page); // trigger lazy KaTeX/mermaid before a tall shot
    out.dom = await readDomState(page);
    out.seedFails = checkExpect(state.expect, out.dom);
    await page.screenshot({ path: file, fullPage: !!state.fullpage });
  } catch (e) { out.error = String((e && e.message) || e); }
  finally { await ctx.close(); }
  return out;
}

(async () => {
  const browser = await chromium.launch();
  const manifest = [];
  for (const route of ROUTES) {
    const entry = { ...route, shots: {} };
    for (const state of MATRIX) {
      const s = await shoot(browser, route, state);
      entry.shots[state.id] = s;
      const flag = s.error ? "ERR " + s.error.slice(0, 44) : (s.seedFails.length ? "SEED✗ " + s.seedFails.join(",") : "ok");
      console.log(`${route.key.slice(0, 22).padEnd(22)} ${state.id.padEnd(22)} ${String(s.status).padEnd(4)} ${flag}`);
    }
    manifest.push(entry);
  }
  fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2));
  await browser.close();
  const seedBad = manifest.flatMap((m) => Object.values(m.shots)).filter((s) => s.seedFails && s.seedFails.length).length;
  console.log(`\nDONE. ${manifest.length} docs × ${MATRIX.length} states → ${OUT}` + (seedBad ? `  (⚠️ ${seedBad} captures failed the settings-seed assertion — investigate before review)` : ""));
})();
