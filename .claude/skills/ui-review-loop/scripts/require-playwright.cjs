/* require-playwright.cjs — resolve Playwright's `chromium` regardless of cwd.
 * Playwright is installed under viewer/node_modules (a viewer dev dep), and Node
 * resolves a script's bare `require("playwright")` relative to the SCRIPT's dir —
 * not cwd — so these scripts (which live outside viewer/) can't find it by default.
 * This helper tries, in order: a plain require (works if launched with NODE_PATH or
 * from within viewer/), then an explicit require from the repo's viewer/node_modules
 * walking up from cwd, then @playwright/test / playwright-core. Returns { chromium }
 * or exits 2 with guidance. */
const fs = require("fs");
const path = require("path");

function tryReq(id) { try { return require(id); } catch { return null; } }

function fromViewer() {
  // Walk up from cwd looking for a viewer/node_modules/playwright install.
  let dir = process.cwd();
  for (let i = 0; i < 8; i++) {
    for (const base of [path.join(dir, "node_modules"), path.join(dir, "viewer", "node_modules")]) {
      for (const pkg of ["playwright", "playwright-core", "@playwright/test"]) {
        const entry = path.join(base, pkg);
        if (fs.existsSync(entry)) { try { return require(entry); } catch {} }
      }
    }
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return null;
}

function resolveChromium() {
  const mod =
    tryReq("playwright") ||
    tryReq("@playwright/test") ||
    tryReq("playwright-core") ||
    fromViewer();
  if (!mod || !mod.chromium) {
    console.error(
      "ERROR: could not resolve Playwright's chromium.\n" +
      "  Run from the viewer/ dir (where playwright is installed), e.g.:\n" +
      "    cd viewer && node ../.claude/skills/ui-review-loop/scripts/<script>.cjs ...\n" +
      "  or install it: (cd viewer && npm i -D playwright) — browsers via `npx playwright install chromium`."
    );
    process.exit(2);
  }
  return { chromium: mod.chromium };
}

module.exports = { resolveChromium };
