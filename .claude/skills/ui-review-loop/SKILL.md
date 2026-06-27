---
name: ui-review-loop
description: 'Full-coverage screenshot review of the running markdown VIEWER: capture each representative doc across the viewer STATE MATRIX (chrome × theme × density × width — docs/reader/focus, light/sepia/dark, compact/spacious, desktop/wide/mobile) with Playwright, fan out a multi-agent vision review, VERIFY each finding against code/DOM (high false-alarm rate — do not trust raw agent output), then loop fix→recapture→re-review until it converges. Plus a Layer-2 assertion-backed interaction driver for the viewer surfaces (immersive toggle, command palette, settings sheet, right-pane segments, in-situ peeks, split view, margin sidenotes, drawer, mobile bar, highlight gesture). Use during a viewer UI redesign / large front-end change. Token-heavy — invoke explicitly.'
---

# ui-review-loop (markdown viewer)

Capture → review → **verify** → report → loop, until the viewer UI converges to
"ship-with-minor-fixes / no blockers." Built for moments of large front-end change
to the viewer (a chrome redesign, a theme migration, a responsive overhaul) where
a test suite can't see "the right context pane ate the prose column at 1500px."

The target is THIS repo's viewer (`viewer/`): a **vanilla-JS single-page markdown
viewer**, not a Next.js site. It is served by `node viewer/serve.js <content-dir>
[-p <port>]` (default 3000) and a doc is loaded via `?file=<relpath-within-served-dir>`.
There are no app routes, no locales, no auth/admin. The review dimension that
*replaces* "every route" is the **state matrix** below.

## Core principle: VERIFY before you report

The vision agents have a **high false-alarm rate.** Every agent finding is a
**hypothesis, not a fact.** Before a finding enters the report as real, cross-check
it against ground truth — the triage layer **is the product.** Viewer-specific false
alarms to rule out:

- "Math is broken / blank" → lazy-KaTeX/mermaid below the fold on a tall full-page
  capture. The viewer lazy-renders math under the fold; `capture.cjs` auto-scrolls
  first, but residual blanks at the very bottom are still artifacts, not breaks.
- "Body text fails AA in dark mode" → vision sampling anti-aliased glyph edges. Read
  the `--text` / `--bg` tokens from `viewer/style.css` and compute WCAG — trust the math.
- "Code block stays light in dark mode" → by design. Code may keep its own palette.
- "Horizontal scrollbar / overflow" → re-measure `scrollWidth` vs viewport; the flex
  `min-width:auto` overflow trap is real, a vision guess is not.
- "Stale / wrong content" → the service worker (`sw.js`) caches aggressively; captures
  use `?nocache` and a fresh context. If you see old chrome, confirm the cache.
- There is **no Next.js dev overlay** here — no floating "N"/"1 Issue" badge to ignore.

| Claim type | How to verify (don't eyeball the screenshot) |
|---|---|
| Layout / overflow | Re-measure headless: `getBoundingClientRect()`, `scrollWidth` vs viewport; watch the flex `min-width:auto` overflow trap |
| Contrast / "fails AA" | Read `--text`/`--bg`/`--accent`/`--border`/`--text-muted` from `viewer/style.css` (`:root` + `html[data-theme="sepia"]` / `html[data-theme="dark"]` blocks) and compute the WCAG ratio — trust the math |
| Broken / blank math or figure | Auto-scroll first (lazy KaTeX below fold), then judge; `existsSync` the figure asset; a blank at the bottom of a full-page shot is almost always lazy-render |
| State gating | Assert the capture's verified DOM: `html[data-chrome]`, `html[data-theme]`, `html.immersive`, `html.density-*` (already recorded per shot in the manifest) |
| Wide-layout overlap | Measure pane rects: `#right-pane` (≥1400px docs), `#content-b` (≥1440px split), `.sidenote` (≥1400px reader) vs `#content` — do they overlap? |
| Stale chrome | Confirm `sw.js` cache isn't serving an old build; recapture with `?nocache` / a fresh context |

Findings that survive verification are worth fixing; the rest go in a "triaged /
non-bug" section with the reason. A report that just relays agent output is
confidently wrong.

## The STATE MATRIX (the core adaptation)

The viewer's theme/chrome/density are **app state in
`localStorage['viewer.settings.v1']`**, seeded BEFORE load via Playwright
`addInitScript` — NOT browser `colorScheme` (exception: `theme:'auto'` follows
`colorScheme`). The settings keys live in `viewer/lib/settings-store.js`: `chrome`
(docs|reader|focus), `theme` (light|sepia|dark|auto), `density`
(compact|normal|spacious), `marginNotes`, `measureCh`, etc.

`discover-routes.cjs` emits the matrix; `capture.cjs` replays it per doc and
**verifies the seed took effect** (`html[data-chrome]`/`[data-theme]`/`.immersive`/
`.density-*` read off the live page — a mis-seed is a finding, caught at capture, not
by a vision agent). The default matrix (12 states):

| State id | Width | Seed | What it exercises |
|---|---|---|---|
| `docs-light` | 1440 | `{chrome:docs, theme:light}` | docked shell + left sidebar |
| `docs-dark` | 1440 | `{chrome:docs, theme:dark}` | dark docked shell |
| `reader-light` | 1440 | `{chrome:reader, theme:light}` | immersive reader (full-page) |
| `reader-dark` | 1440 | `{chrome:reader, theme:dark}` | dark immersive |
| `focus-dark` | 1440 | `{chrome:focus, theme:dark}` | focus chrome, minimal |
| `sepia-reader` | 1440 | `{chrome:reader, theme:sepia}` | sepia palette |
| `density-compact-docs` | 1440 | `{chrome:docs, density:compact}` | tighter `--ui-density-lh` |
| `density-spacious-docs` | 1440 | `{chrome:docs, density:spacious}` | looser chrome line-height |
| `three-zone-docs` | 1500 | `{chrome:docs}` | `#right-pane` visible (≥1400px) |
| `split-view` | 1500 | `{chrome:reader}` + open split | Pane B `#content-b` (≥1440px) |
| `margin-notes` | 1500 | `{chrome:reader, marginNotes:true}` | `#sidenote-band` (≥1400px reader, full-page) |
| `mobile-reader` | 390 | `{chrome:reader}` (isMobile) | mobile bottom toolbar |

Widths: **1440** desktop; **1500** for the three-zone/split/margin states (split
needs ≥1440, right-pane & sidenotes need ≥1400 — 1500 clears both); **390** mobile
(`isMobile`). Full-page shots auto-scroll to trigger lazy KaTeX/mermaid first.

## When to use / not

- **Use** during an active viewer redesign or large UI change, before merge.
- **Don't** for a stable viewer — a one-shot `playwright screenshot` + eyeball is
  enough. This loop is token-heavy (~0.7M tokens + ~10 min per review pass). Invoke
  explicitly; never auto-run.

## Inputs / parameters

- `OUT` — report dir, `reports/ui-review-<YYYY-MM-DD>/` (don't overwrite a prior one).
- `CONTENT` — the served content dir. A good rich target is `surveys/llms-for-coding/`
  (math, tables, code, citations, deep section nesting).
- `BASE` — defaults to `http://localhost:3000`.
- `ROUTES` — a `routes.json` from `discover-routes.cjs` (doc list + state matrix).
- `MAX_ITERS` — convergence cap (default 3).
- **No auth.** All cookie/`ADMIN_SECRET` logic from the Next.js source is dropped.

**Run the `.cjs` scripts from `viewer/`** so `require("playwright")` resolves
(playwright is a `viewer/` dev dep — see `viewer/package.json`). The skill paths
below are absolute from the repo root.

## Process

### Phase 0 — Discover docs + emit the state matrix
```bash
node .claude/skills/ui-review-loop/scripts/discover-routes.cjs surveys/llms-for-coding/ > /tmp/routes.json
```
Enumerates the served dir's `.md`/`.markdown` files, honours `order.json` ordering,
and curates a small representative set (largest math/table/code-heavy doc, a median,
the smallest / `index.md`) — pass `--all` to capture every doc. It also emits the
state matrix. **Review the output**; swap in a different long doc if the auto-pick
missed your most complex page.

### Phase 1 — Capture the matrix
Boot the server and wait for it, then capture:
```bash
node viewer/serve.js surveys/llms-for-coding/ -p 3000 &     # background
curl --retry 40 --retry-connrefused -s http://localhost:3000/ > /dev/null
cd viewer && node .claude/skills/ui-review-loop/scripts/capture.cjs \
  --out <OUT> --routes /tmp/routes.json --base http://localhost:3000
```
Replays every state per doc, seeds settings via `addInitScript`, **asserts the seed
took effect**, auto-scrolls full-page shots, opens split where the matrix requests it.
Writes `<OUT>/img/*.png` and `<OUT>/manifest.json` (each shot carries its verified DOM
state + any `seedFails`). A `--only docs-light,reader-dark` filter captures a subset.

### Phase 2 — Multi-agent vision review
```bash
node .claude/skills/ui-review-loop/scripts/build-review-input.cjs <OUT> > <OUT>/review-input.json
```
Inject `review-input.json` into `scripts/review-workflow.template.js` (replace the
`/*__ROUTES__*/` marker) and run it with the **Workflow** tool — one vision agent per
(doc × state-group), then a synthesis agent. The agents get the verified DOM state per
shot, so they judge *appearance* against a known *mode*. Save the returned `reviews`
and `synthesis` to `<OUT>/reviews.json` + `<OUT>/synthesis.json`.

### Phase 3 — VERIFY (the critical phase)
For **every** finding marked `blocker`/`major`, run the verification in the table
above before accepting it. Open the contested screenshots yourself. Demote false
alarms (lazy-math blanks, contrast guesses, by-design code blocks, stale cache) to a
"triaged / non-bug" list with the reason. This is where the skill earns its keep.

### Phase 4 — Report
```bash
node .claude/skills/ui-review-loop/scripts/assemble.cjs <OUT>
```
Generates `<OUT>/README.md`: verdict, a capture-integrity table (any seed
mismatches), the panel issue table, per-doc state-matrix gallery with DOM
annotations. Lead with your own "Verified corrections" where they override the panel.

### Phase 5 — Loop to convergence
Fix the **verified** issues (smallest-blast-radius first; shared tokens / a single
`@media (min-width:1400px)` rule clear many states at once). Re-run the viewer tests +
recapture and re-review (Phases 1–4) on the fixed build. Stop when the verdict is
`ship-with-minor-fixes` / no blockers, or `MAX_ITERS` reached. Keep each round's report
in its own `OUT` dir so the progression is auditable.

## Layer 2 — Interaction review (separate phase, shared harness, one report)

Phases 1–5 cover **resting states** (visual). Layer 2 covers **behavior under input**
— and it's a *different reliability profile*: interaction findings are
**assertion-backed**, not vision-guessed. Run it as a distinct phase in the same loop
iteration, then merge into the same report.

```bash
# needs the live server (it DRIVES the browser)
cd viewer && node .claude/skills/ui-review-loop/scripts/interact.cjs \
  --out <OUT_INTERACTION> --base http://localhost:3000 --file appendix-a-qkv-first-principles.md
```
`interact.cjs` drives each surface, captures the **resulting** states, and asserts the
DOM/a11y (`data-chrome` flips, focus moves/traps/returns, `aria-selected`,
`#content-b` visibility, **persistence across reload**). It writes `interactions.json`.
Then:
```bash
node .claude/skills/ui-review-loop/scripts/build-interaction-input.cjs <OUT_INTERACTION> > <OUT_INTERACTION>/interaction-review-input.json
# inject into interaction-review-workflow.template.js (replace the SCENARIOS marker) → run with Workflow →
# save reviews.json/synthesis.json → then:
node .claude/skills/ui-review-loop/scripts/interaction-assemble.cjs <OUT_INTERACTION>
```
The vision pass judges only the **visual** quality of the open states; the
**assertions** are ground truth for behavior — so VERIFY = root-cause every failed
assertion (e.g. a `MutationObserver` to see *when* `data-chrome` changes), don't trust
a screenshot.

### Viewer interaction catalog (★ = recently redesigned; scrutinize)

- ★ **immersive toggle** — `#rt-mode` click flips `data-chrome` reader→docs;
  `Ctrl/Cmd+Shift+F` toggles Focus; **persistence across reload** (seed `chrome=docs`,
  reload, assert `data-chrome` — the FOUC/hydration trap, analogous to the source's
  theme-toggle persistence test).
- ★ **command palette** — `Ctrl/Cmd+K` opens `#cmd-palette`, focuses `#cmd-input`;
  prefix modes (`>` command, `#` index incl `Eq. (N)` jump); `Esc` closes;
  `>toggle immersive` flips `data-chrome`.
- ★ **settings sheet** — `#rt-aa` (reader) / `#settings-btn` (docs) opens
  `#settings-sheet`; background `#content` gets `inert`; `Esc`/outside/close-button
  dismiss; focus **returns** to opener; `aria-expanded` flips.
- ★ **right-pane segments** (docs ≥1400px) — `#right-pane .rp-seg[data-seg=outline|marks|peek]`
  click → `aria-selected` flips + panel (`#rp-outline`/`#rp-marks`/`#rp-peek`) visibility.
- ★ **in-situ peeks** — click an `#eq-`/`#ref-`/`#sec-` cross-ref → `#peek-popover`;
  `Esc`/outside/scroll dismiss.
- ★ **split view** (≥1440px) — palette "Open current section in split" or
  Cmd/Ctrl-click a cross-ref → `#content-b` visible + `#app.split-open`; `Esc` closes
  Pane B first.
- ★ **margin sidenotes** (reader ≥1400px) — `marginNotes:true` → `#sidenote-band` renders;
  adjacent `.sidenote` boxes do not vertically overlap (de-collision).
- **theme cycle** — `#rt-theme` click cycles `data-theme` (light→sepia→dark→auto);
  persistence across reload.
- **density** — radio `name="density-mode"` → `html.density-*` + `--ui-density-lh`
  changes (NOT `--content-lh`, which stays at the prose default).
- **drawer** (reader) — `Ctrl/Cmd+B` / `Ctrl/Cmd+Shift+O` toggle the off-canvas
  `#sidebar` (`#app.drawer-open`).
- **mobile adaptive bar** (≤768px) — `#mobile-toolbar [data-mt="search"]` opens the
  palette; selection morphs the bar into `#hl-toolbar`.
- **highlight gesture** — select text in `#content` → the highlight toolbar
  (`#hl-toolbar`) appears.
- **reduced-motion** — grep `viewer/style.css` for `prefers-reduced-motion`; render
  under `reducedMotion:'reduce'`.

**Why it's worth its own phase:** a static screenshot review *cannot* catch
persistence/behavior/a11y bugs ("reader mode reverts on reload because the pre-paint
FOUC guard read stale storage" — invisible to a resting snapshot). Static is cheap and
re-run on every visual change; interaction is per-surface and re-run when behavior
changes. Keep them separate phases, merge findings into one "UI health at this commit"
report.

## Known artifacts (auto-dismiss these)
- Lazy-loaded KaTeX/mermaid below the fold on tall full-page captures render blank —
  `capture.cjs` auto-scrolls first, but a blank at the very bottom is still an artifact.
- The service worker (`sw.js`) caches aggressively — capture with a fresh context /
  `?nocache` (both are wired into the scripts).
- No Next.js dev overlay exists in this viewer — there is no harness badge to ignore.
- Intentional "by-design" surfaces (e.g. a code block that keeps its own color in dark
  mode) — confirm against design intent before flagging.

## Convergence criteria
- No `blocker` survives verification.
- No `major` survives verification (or each is a documented, accepted trade-off).
- Verdict ≥ `ship-with-minor-fixes`. Remaining items are cosmetic → file to `todos/`
  rather than blocking.
- Layer 2: every redesigned-surface assertion passes (chrome persists across reload,
  focus returns/traps, segments flip, Pane B opens/closes, sidenotes de-collide).

## Cost
Each visual review pass ≈ 0.7M output tokens + ~10 min (one agent per doc × state-group
+ synthesis; the default matrix is ~12 states × a few docs grouped into ~5 groups/doc).
Capture ≈ 2–4 min. The interaction pass adds ~13 scenarios. A 3-round loop is ~2–3M
tokens. Worth it before a big viewer merge; overkill otherwise.
