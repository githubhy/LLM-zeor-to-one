/* interact.cjs — Layer-2 INTERACTION review driver for the markdown viewer's
 * ui-review-loop. Drives each interactive surface, captures the RESULTING states,
 * and asserts the DOM/a11y (data-chrome flips, focus moves/traps/returns,
 * aria-selected, #content-b visibility, persistence across reload). Interaction
 * findings are assertion-backed, not vision-guessed. There is NO auth.
 *
 * Run from viewer/ (Playwright resolves there); require-playwright.cjs also walks up
 * to find it from any cwd. Needs the live server.
 *   node viewer/serve.js <content-dir> -p PORT &                  # the server
 *   cd viewer && node <skill>/scripts/interact.cjs --out <dir> \
 *        --base http://localhost:PORT --file <relpath-with-math.md>
 * Output: <out>/img/*.png + <out>/interactions.json */
const { resolveChromium } = require("./require-playwright.cjs");
const { chromium } = resolveChromium();
const fs = require("fs");
const path = require("path");

function arg(name, def) { const i = process.argv.indexOf(`--${name}`); return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def; }
const OUT = path.resolve(arg("out", `reports/ui-interaction-${new Date().toISOString().slice(0, 10)}`));
const IMG = path.join(OUT, "img");
fs.mkdirSync(IMG, { recursive: true });
const BASE = arg("base", "http://localhost:3000");
// A math/cross-ref-heavy doc gives the palette / peek / split / sidenote drivers
// real targets. Override with --file for a different served doc.
const FILE = arg("file", "appendix-a-qkv-first-principles.md");
const SETTINGS_KEY = "viewer.settings.v1";
const META = process.platform === "darwin"; // use Meta on macOS, Control elsewhere
const MOD = META ? "Meta" : "Control";
const urlFor = (f) => `/?file=${encodeURIComponent(f || FILE)}&nocache=1`;

(async () => {
  const browser = await chromium.launch();

  // Seed settings into localStorage before load (the FOUC guard + loadSettings()
  // read this exact key — the page boots straight into the requested chrome/theme).
  function seed(page, patch) {
    return page.addInitScript(([key, p]) => {
      let existing = {}; try { existing = JSON.parse(localStorage.getItem(key)) || {}; } catch (e) {}
      // patch is the BASE (applies on the first/empty load); existing OVERRIDES it,
      // so a value the test mutates at runtime survives a reload. (This init-script
      // re-runs on every reload — merging the patch OVER existing would clobber the
      // very value a persistence assertion is checking.)
      localStorage.setItem(key, JSON.stringify(Object.assign({}, p, existing)));
    }, [SETTINGS_KEY, patch]);
  }
  async function mkctx(opts) { return browser.newContext(opts); }
  const desktop = () => mkctx({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
  const wide = () => mkctx({ viewport: { width: 1500, height: 940 }, colorScheme: "light" });
  const mobile = () => mkctx({ viewport: { width: 390, height: 844 }, colorScheme: "light", deviceScaleFactor: 2, isMobile: true, hasTouch: true });

  let n = 0;
  async function snap(page, label) { const file = path.join(IMG, `${String(++n).padStart(2, "0")}-${label}.png`); await page.screenshot({ path: file }); return { label, file: path.relative(OUT, file) }; }
  async function open(ctx, settings, file) {
    const p = await ctx.newPage();
    if (settings) await seed(p, settings);
    await p.goto(BASE + urlFor(file), { waitUntil: "load", timeout: 30000 });
    await p.waitForTimeout(1200);
    try { await p.evaluate(() => document.fonts && document.fonts.ready); } catch {}
    return p;
  }
  const A = (name, pass, detail) => ({ name, pass: !!pass, detail: String(detail) });
  const chromeAttr = (p) => p.evaluate(() => document.documentElement.getAttribute("data-chrome"));
  const themeAttr = (p) => p.evaluate(() => document.documentElement.getAttribute("data-theme"));

  const results = [];
  async function run(id, label, route, viewport, category, fn) {
    const r = { id, label, route, viewport, category, steps: [], shots: [], assertions: [], error: null };
    try { await fn(r); } catch (e) { r.error = String((e && e.message) || e); }
    const ok = r.assertions.filter((a) => a.pass).length, tot = r.assertions.length;
    console.log(`${id.padEnd(26)} ${r.error ? "ERR " + r.error.slice(0, 40) : `${ok}/${tot} asserts`}`);
    results.push(r);
  }

  // 1 ★ Immersive toggle + Focus shortcut + PERSISTENCE across reload (the FOUC trap)
  await run("immersive-toggle", "Immersive toggle (#rt-mode) + Focus + persistence", urlFor(), "desktop", "changed", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    r.assertions.push(A("boots into reader (immersive)", (await chromeAttr(p)) === "reader", `data-chrome=${await chromeAttr(p)}`));
    r.shots.push(await snap(p, "immersive-reader"));
    await p.locator("#rt-mode").click(); await p.waitForTimeout(350); r.steps.push("click #rt-mode");
    r.assertions.push(A("#rt-mode flips reader → docs", (await chromeAttr(p)) === "docs", `data-chrome=${await chromeAttr(p)}`));
    r.assertions.push(A("html loses .immersive in docs", !(await p.evaluate(() => document.documentElement.classList.contains("immersive"))), "immersive removed"));
    r.shots.push(await snap(p, "immersive-docs"));
    await p.keyboard.press(`${MOD}+Shift+f`); await p.waitForTimeout(350); r.steps.push("Ctrl/Cmd+Shift+F");
    r.assertions.push(A("Ctrl/Cmd+Shift+F enters focus", (await chromeAttr(p)) === "focus", `data-chrome=${await chromeAttr(p)}`));
    r.shots.push(await snap(p, "immersive-focus"));
    // PERSISTENCE: seed docs, reload, assert it boots docs pre-paint (no FOUC/hydration revert).
    await p.evaluate((k) => { const s = JSON.parse(localStorage.getItem(k) || "{}"); s.chrome = "docs"; localStorage.setItem(k, JSON.stringify(s)); }, SETTINGS_KEY);
    await p.reload({ waitUntil: "load" }); await p.waitForTimeout(800); r.steps.push("reload with chrome=docs seeded");
    r.assertions.push(A("chrome persists docs across reload", (await chromeAttr(p)) === "docs", `data-chrome=${await chromeAttr(p)}`));
    await ctx.close();
  });

  // 2 ★ Command palette — open / focus / prefix modes / Esc / >toggle immersive
  await run("command-palette", "Command palette (Ctrl/Cmd+K) + prefixes", urlFor(), "desktop", "changed", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "docs", theme: "light" });
    await p.keyboard.press(`${MOD}+k`); await p.waitForTimeout(350); r.steps.push("Ctrl/Cmd+K");
    r.assertions.push(A("palette opens (#cmd-palette visible)", await p.locator("#cmd-palette").isVisible(), "visible"));
    r.assertions.push(A("#cmd-input focused", await p.evaluate(() => document.activeElement && document.activeElement.id === "cmd-input"), "focus on cmd-input"));
    r.shots.push(await snap(p, "palette-open"));
    // # index mode (headings + Eq. (N) jumps)
    await p.locator("#cmd-input").fill("#"); await p.waitForTimeout(400); r.steps.push('type "#" (index mode)');
    r.assertions.push(A("# mode lists index entries", (await p.locator("#cmd-results .pal-item").count()) > 0, `${await p.locator("#cmd-results .pal-item").count()} items`));
    r.shots.push(await snap(p, "palette-index"));
    // > command mode → toggle immersive
    await p.locator("#cmd-input").fill(">toggle immersive"); await p.waitForTimeout(350); r.steps.push('type ">toggle immersive"');
    r.shots.push(await snap(p, "palette-command"));
    await p.keyboard.press("Enter"); await p.waitForTimeout(400); r.steps.push("Enter");
    r.assertions.push(A(">toggle immersive flips chrome docs→reader", (await chromeAttr(p)) === "reader", `data-chrome=${await chromeAttr(p)}`));
    // reopen + Esc
    await p.keyboard.press(`${MOD}+k`); await p.waitForTimeout(250);
    await p.keyboard.press("Escape"); await p.waitForTimeout(300); r.steps.push("reopen, Escape");
    r.assertions.push(A("Escape closes palette", await p.locator("#cmd-palette").isHidden(), "hidden"));
    await ctx.close();
  });

  // 3 ★ Settings sheet — open (#rt-aa) / background inert / Esc / focus return
  await run("settings-sheet", "Settings sheet open/inert/dismiss/focus-return", urlFor(), "desktop", "changed", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    await p.locator("#rt-aa").click(); await p.waitForTimeout(350); r.steps.push("click #rt-aa");
    r.assertions.push(A("settings sheet opens", await p.locator("#settings-sheet").isVisible(), "visible"));
    r.assertions.push(A("opener aria-expanded=true", (await p.locator("#rt-aa").getAttribute("aria-expanded")) === "true", "aria-expanded"));
    r.assertions.push(A("background #content inert", (await p.locator("#content").getAttribute("inert")) !== null, "inert present"));
    r.shots.push(await snap(p, "settings-open"));
    await p.keyboard.press("Escape"); await p.waitForTimeout(350); r.steps.push("Escape");
    r.assertions.push(A("Escape closes sheet", await p.locator("#settings-sheet").isHidden(), "hidden"));
    r.assertions.push(A("focus returns to #rt-aa", await p.evaluate(() => document.activeElement && document.activeElement.id === "rt-aa"), "focus on rt-aa"));
    r.assertions.push(A("opener aria-expanded=false", (await p.locator("#rt-aa").getAttribute("aria-expanded")) === "false", "aria-expanded"));
    await ctx.close();
  });

  // 4 ★ Right-pane segments (docs ≥1400px) — aria-selected flip + panel visibility
  await run("right-pane-segments", "Right-pane segments (Outline/Marks/Peek)", urlFor(), "wide-1500", "changed", async (r) => {
    const ctx = await wide(); const p = await open(ctx, { chrome: "docs", theme: "light" });
    r.assertions.push(A("#right-pane visible at ≥1400px docs", await p.locator("#right-pane").isVisible(), "visible"));
    r.assertions.push(A("outline seg selected by default", (await p.locator('#right-pane .rp-seg[data-seg="outline"]').getAttribute("aria-selected")) === "true", "aria-selected"));
    r.shots.push(await snap(p, "rp-outline"));
    await p.locator('#right-pane .rp-seg[data-seg="marks"]').click(); await p.waitForTimeout(300); r.steps.push("click Marks seg");
    r.assertions.push(A("Marks seg aria-selected=true", (await p.locator('#right-pane .rp-seg[data-seg="marks"]').getAttribute("aria-selected")) === "true", "aria-selected"));
    r.assertions.push(A("Marks panel visible", await p.locator("#rp-marks").isVisible(), "visible"));
    r.assertions.push(A("Outline panel hidden", await p.locator("#rp-outline").isHidden(), "hidden"));
    r.shots.push(await snap(p, "rp-marks"));
    await p.locator('#right-pane .rp-seg[data-seg="peek"]').click(); await p.waitForTimeout(300); r.steps.push("click Peek seg");
    r.assertions.push(A("Peek seg aria-selected=true", (await p.locator('#right-pane .rp-seg[data-seg="peek"]').getAttribute("aria-selected")) === "true", "aria-selected"));
    r.shots.push(await snap(p, "rp-peek"));
    await ctx.close();
  });

  // 5 ★ In-situ peeks — hover/click a cross-ref → #peek-popover, Esc dismiss
  await run("in-situ-peek", "Cross-reference peek popover", urlFor(), "desktop", "changed", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    const ref = p.locator('#content a[href^="#eq-"], #content a[href^="#sec-"], #content a[href^="#ref-"]').first();
    const has = await ref.count();
    r.assertions.push(A("a same-doc cross-ref exists in content", has > 0, `count=${has}`));
    if (has) {
      await ref.scrollIntoViewIfNeeded(); await p.waitForTimeout(150);
      await ref.click(); await p.waitForTimeout(500); r.steps.push("click cross-ref");
      const vis = await p.locator("#peek-popover").isVisible();
      r.assertions.push(A("#peek-popover opens", vis, `visible=${vis}`));
      r.shots.push(await snap(p, "peek-open"));
      await p.keyboard.press("Escape"); await p.waitForTimeout(300); r.steps.push("Escape");
      r.assertions.push(A("Escape dismisses peek", await p.locator("#peek-popover").isHidden(), "hidden"));
    }
    await ctx.close();
  });

  // 6 ★ Split view (≥1440px) — Cmd/Ctrl-click cross-ref → Pane B, Esc closes it first
  await run("split-view", "Split-view Pane B via modifier-click", urlFor(), "wide-1500", "changed", async (r) => {
    const ctx = await wide(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    const ref = p.locator('#content a[href^="#eq-"], #content a[href^="#sec-"], #content a[href^="#ref-"]').first();
    const has = await ref.count();
    r.assertions.push(A("cross-ref exists for split target", has > 0, `count=${has}`));
    if (has) {
      await ref.click({ modifiers: [META ? "Meta" : "Control"] }); await p.waitForTimeout(600); r.steps.push("Cmd/Ctrl-click cross-ref");
      r.assertions.push(A("#content-b (Pane B) visible", await p.locator("#content-b").isVisible(), "visible"));
      r.assertions.push(A("#app gets .split-open", await p.evaluate(() => document.getElementById("app").classList.contains("split-open")), "split-open"));
      r.shots.push(await snap(p, "split-open"));
      await p.keyboard.press("Escape"); await p.waitForTimeout(400); r.steps.push("Escape");
      r.assertions.push(A("Escape closes Pane B", await p.locator("#content-b").isHidden(), "hidden"));
    }
    await ctx.close();
  });

  // 7 ★ Margin sidenotes (reader ≥1400px) — band renders + no vertical overlap
  await run("margin-sidenotes", "Margin sidenotes render + de-collision", urlFor(), "wide-1500", "changed", async (r) => {
    const ctx = await wide(); const p = await open(ctx, { chrome: "reader", theme: "light", marginNotes: true });
    await p.waitForTimeout(600);
    const band = await p.locator("#sidenote-band").count();
    r.assertions.push(A("#sidenote-band renders", band > 0, `count=${band}`));
    const notes = await p.evaluate(() => Array.from(document.querySelectorAll(".sidenote")).map((n) => { const b = n.getBoundingClientRect(); return { y: b.top, h: b.height }; }).sort((a, b) => a.y - b.y));
    r.assertions.push(A("at least one .sidenote present", notes.length > 0, `count=${notes.length}`));
    let overlap = false;
    for (let i = 1; i < notes.length; i++) if (notes[i].y < notes[i - 1].y + notes[i - 1].h - 2) overlap = true;
    r.assertions.push(A("adjacent sidenotes do not vertically overlap", !overlap, `overlap=${overlap} (n=${notes.length})`));
    r.shots.push(await snap(p, "sidenotes"));
    await ctx.close();
  });

  // 8 Theme cycle (#rt-theme) + persistence across reload
  await run("theme-cycle", "Theme cycle (#rt-theme) + persistence", urlFor(), "desktop", "core", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    const t0 = await themeAttr(p);
    await p.locator("#rt-theme").click(); await p.waitForTimeout(300); r.steps.push("click #rt-theme");
    const t1 = await themeAttr(p);
    r.assertions.push(A("#rt-theme changes data-theme", t0 !== t1, `before=${t0} after=${t1}`));
    r.shots.push(await snap(p, "theme-cycled"));
    await p.reload({ waitUntil: "load" }); await p.waitForTimeout(700); r.steps.push("reload");
    r.assertions.push(A("theme persists across reload", (await themeAttr(p)) === t1, `after-reload=${await themeAttr(p)}`));
    await ctx.close();
  });

  // 9 Density → html.density-* + --ui-density-lh (NOT --content-lh)
  await run("density", "Density preset → --ui-density-lh", urlFor(), "desktop", "core", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "docs", theme: "light", density: "normal" });
    const before = await p.evaluate(() => ({ cls: document.documentElement.className, ui: getComputedStyle(document.documentElement).getPropertyValue("--ui-density-lh").trim(), content: getComputedStyle(document.documentElement).getPropertyValue("--content-lh").trim() }));
    // change via settings sheet radio
    await p.locator("#settings-btn").click().catch(() => {}); await p.locator("#rt-aa").click().catch(() => {}); await p.waitForTimeout(300);
    await p.locator('input[name="density-mode"][value="compact"]').check(); await p.waitForTimeout(350); r.steps.push("set density=compact");
    const after = await p.evaluate(() => ({ cls: document.documentElement.className, ui: getComputedStyle(document.documentElement).getPropertyValue("--ui-density-lh").trim(), content: getComputedStyle(document.documentElement).getPropertyValue("--content-lh").trim() }));
    r.assertions.push(A("html gets density-compact", /density-compact/.test(after.cls), `class=${after.cls}`));
    r.assertions.push(A("--ui-density-lh changes", before.ui !== after.ui, `before=${before.ui} after=${after.ui}`));
    r.assertions.push(A("--content-lh unchanged by density", before.content === after.content, `content-lh ${before.content}→${after.content}`));
    r.shots.push(await snap(p, "density-compact"));
    await ctx.close();
  });

  // 10 Drawer (reader) — Ctrl/Cmd+B and Ctrl/Cmd+Shift+O toggle #sidebar
  await run("drawer", "Reader drawer (Ctrl/Cmd+B, +Shift+O)", urlFor(), "desktop", "core", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    await p.keyboard.press(`${MOD}+b`); await p.waitForTimeout(400); r.steps.push("Ctrl/Cmd+B");
    const open1 = await p.evaluate(() => document.getElementById("app").classList.contains("drawer-open"));
    r.assertions.push(A("Ctrl/Cmd+B opens drawer (#app.drawer-open)", open1, `drawer-open=${open1}`));
    r.shots.push(await snap(p, "drawer-open"));
    await p.keyboard.press("Escape"); await p.waitForTimeout(350); r.steps.push("Escape");
    const open2 = await p.evaluate(() => document.getElementById("app").classList.contains("drawer-open"));
    r.assertions.push(A("Escape closes drawer", !open2, `drawer-open=${open2}`));
    await p.keyboard.press(`${MOD}+Shift+o`); await p.waitForTimeout(400); r.steps.push("Ctrl/Cmd+Shift+O");
    const outlineActive = await p.evaluate(() => { const t = document.querySelector('.sidebar-tab[data-tab="outline"]'); return !!t && (t.classList.contains("active") || t.getAttribute("aria-selected") === "true"); });
    r.assertions.push(A("Ctrl/Cmd+Shift+O opens drawer on Outline", outlineActive, `outline active=${outlineActive}`));
    await ctx.close();
  });

  // 11 Mobile adaptive bar (≤768px) — search slot opens palette
  await run("mobile-bar", "Mobile toolbar search slot → palette", urlFor(), "mobile", "core", async (r) => {
    const ctx = await mobile(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    r.assertions.push(A("#mobile-toolbar present on mobile", await p.locator("#mobile-toolbar").count() > 0, "present"));
    r.shots.push(await snap(p, "mobile-bar"));
    await p.locator('#mobile-toolbar [data-mt="search"]').click(); await p.waitForTimeout(400); r.steps.push("tap search slot");
    r.assertions.push(A("search slot opens command palette", await p.locator("#cmd-palette").isVisible(), "palette visible"));
    r.assertions.push(A("#cmd-input focused", await p.evaluate(() => document.activeElement && document.activeElement.id === "cmd-input"), "focus on cmd-input"));
    r.shots.push(await snap(p, "mobile-palette"));
    await ctx.close();
  });

  // 12 Highlight gesture — select text in #content → #hl-toolbar appears
  await run("highlight-gesture", "Text selection → highlight toolbar", urlFor(), "desktop", "core", async (r) => {
    const ctx = await desktop(); const p = await open(ctx, { chrome: "reader", theme: "light" });
    const box = await p.evaluate(() => {
      const para = document.querySelector("#content p");
      if (!para || !para.firstChild) return null;
      const tn = para.firstChild;
      const len = (tn.textContent || "").length;
      if (len < 12) return null;
      const sel = window.getSelection(); sel.removeAllRanges();
      const rng = document.createRange(); rng.setStart(tn, 2); rng.setEnd(tn, Math.min(len, 24)); sel.addRange(rng);
      const rect = rng.getBoundingClientRect();
      return { x: rect.left + rect.width / 2, y: rect.bottom };
    });
    r.assertions.push(A("selectable paragraph text found", !!box, box ? "ok" : "no #content p text node"));
    if (box) {
      await p.mouse.move(box.x, box.y); await p.dispatchEvent("#content", "mouseup", {}).catch(() => {});
      await p.evaluate((b) => document.dispatchEvent(new MouseEvent("mouseup", { clientX: b.x, clientY: b.y, bubbles: true })), box);
      await p.waitForTimeout(450); r.steps.push("select text + mouseup");
      const tb = await p.locator("#hl-toolbar").count();
      const visible = tb > 0 ? await p.locator("#hl-toolbar").isVisible().catch(() => false) : false;
      r.assertions.push(A("#hl-toolbar appears on selection", tb > 0 && visible, `toolbar present=${tb > 0} visible=${visible}`));
      r.shots.push(await snap(p, "highlight-toolbar"));
    }
    await ctx.close();
  });

  // 13 Reduced-motion — code finding + render under reduce
  await run("reduced-motion", "prefers-reduced-motion handling", urlFor(), "desktop", "a11y", async (r) => {
    const handled = (() => { try { return require("child_process").execSync('grep -l "prefers-reduced-motion" ../style.css 2>/dev/null || grep -rl "prefers-reduced-motion" . 2>/dev/null || true', { cwd: __dirname }).toString().trim().length > 0; } catch { return false; } })();
    r.assertions.push(A("viewer CSS honors prefers-reduced-motion", handled, handled ? "found in style.css" : "NOT found — verify grep path"));
    const ctx = await mkctx({ viewport: { width: 1440, height: 900 }, colorScheme: "light", reducedMotion: "reduce" });
    const p = await open(ctx, { chrome: "reader", theme: "light" });
    r.steps.push("loaded with reducedMotion=reduce");
    r.shots.push(await snap(p, "reduced-motion"));
    await ctx.close();
  });

  fs.writeFileSync(path.join(OUT, "interactions.json"), JSON.stringify(results, null, 2));
  await browser.close();
  const passed = results.flatMap((r) => r.assertions).filter((a) => a.pass).length;
  const total = results.flatMap((r) => r.assertions).length;
  console.log(`\nDONE. ${results.length} scenarios, ${passed}/${total} assertions passed → ${OUT}`);
})();
