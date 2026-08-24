# Markdown Viewer — User Guide

A zero-build, real-time markdown viewer for multi-file document sets with full KaTeX math rendering, cross-file navigation, live reload, and inline highlights.

## Install

```bash
cd viewer && npm install
```

This installs the required `chokidar`, `ws`, and `ignore` packages. You need **Node.js 18+**.

> **Tip — skip the manual install.** The launcher scripts below auto-install
> `viewer/node_modules` on first run, so you can go straight to Quick Start
> without this step. Running `node viewer/serve.js` directly *before* installing
> fails with `Error: Cannot find module 'ws'` — the launchers exist to prevent
> exactly that.

## Quick Start

The cross-platform launcher scripts auto-install dependencies on first run and
default to serving `surveys/` when no directory is given, so a bare port flag
just works:

```bash
# macOS / Linux / Git Bash
scripts/serve-viewer.sh                       # serves surveys/ on :3000
scripts/serve-viewer.sh -p 3500               # serves surveys/ on :3500
scripts/serve-viewer.sh surveys/llms-for-coding -p 3500
```

```powershell
# Windows PowerShell
scripts\serve-viewer.ps1                       # serves surveys/ on :3000
scripts\serve-viewer.ps1 -p 3500              # serves surveys/ on :3500
scripts\serve-viewer.ps1 surveys/llms-for-coding -p 3500
```

Once dependencies are installed you can also call `serve.js` directly:

```bash
# From the repository root
node viewer/serve.js surveys/llms-for-coding

# Custom port
node viewer/serve.js surveys/llms-for-coding -p 8080

# Extended asset sandbox: markdown in reports/ references images under sim/
node viewer/serve.js reports/ --allow .
```

Open `http://localhost:3000` in your browser.

### `--allow <path>` extended asset roots

The asset sandbox is normally the same directory as the served markdown. For cross-cutting review docs that embed images from another directory (e.g. a figure-review report in `reports/` referencing PNGs under `sim/.../figures/`), pass `--allow <path>` one or more times to extend the read-only asset sandbox. Markdown file access remains strictly limited to the primary target directory. Each `--allow` root is independently sandboxed — `..` escapes inside one root cannot cross into another.

## Launching Without a Terminal (macOS)

`tools/make-mac-app.sh` builds **Survey Viewer.app** — a double-clickable launcher
that starts `serve.js` and opens the viewer in a standalone, chrome-less window.

```bash
./viewer/tools/make-mac-app.sh                 # -> ~/Applications/Survey Viewer.app
./viewer/tools/make-mac-app.sh --port 4000     # bake in a non-default port
./viewer/tools/make-mac-app.sh --out /Applications --name "Surveys"
```

Double-click it, or drag it to the Dock.

**The app is not bound to any repository.** At launch it resolves which repo to
serve, then runs *that* repo's own `viewer-launcher.sh`:

1. `VIEWER_REPO`, if set — a one-off override, never added to the recents.
2. The **last repo you opened**, with no dialog. This is the common path.
3. Otherwise, a chooser: your recents, plus *Other (browse)…* for a new one.

**Hold Option while launching to get the chooser** even when a repo is remembered —
the standard macOS "let me pick" gesture. `--pick` does the same from a terminal.

If the last-used repo has moved or been deleted, the app says so and opens the
chooser. It deliberately does **not** fall through to the next entry in the
recents: silently serving a different corpus gives you no way to notice you are
reading the wrong repo.

So one app serves any number of clones, and **moving a repo costs a re-pick, not a
rebuild.** The bundle carries exactly one copied file — `Resources/pick-repo.sh`,
the bootstrap that necessarily runs before any repo is known. Everything else
executes from the selected repo, so viewer and launcher edits still take effect
immediately. Re-run `make-mac-app.sh` only to refresh that bootstrap or change the
baked-in port.

### Managing the repo list

```bash
./viewer/tools/pick-repo.sh list             # recents, most recent first
./viewer/tools/pick-repo.sh remember <path>  # add / move to the top
./viewer/tools/pick-repo.sh forget <path>    # drop one
./viewer/tools/pick-repo.sh forget           # drop all (next launch asks)
./viewer/tools/pick-repo.sh resolve          # what would launch right now
```

A directory qualifies as a viewer repo when it has **both** `viewer/serve.js` and an
executable `viewer/tools/viewer-launcher.sh`. Pick the folder that *contains*
`viewer/`, not `viewer/` itself — if you get it wrong the chooser corrects for it
rather than failing. A clone that predates the launcher is rejected until it has
one; copy `viewer/tools/viewer-launcher.sh` and `viewer/tools/pick-repo.sh` into it.

**One server, one repo.** `serve.js` on a given port serves a single repo, so
launching from a different one hands the port over — announced, not silently — and
`status` reports which repo is live.

### Controlling the server

The app is a *launcher*: it starts the server, opens the window, and exits, leaving
the server running (reparented to `launchd`). Manage it with the same script:

```bash
./viewer/tools/viewer-launcher.sh status    # running (pid N, port 3000) | stopped
./viewer/tools/viewer-launcher.sh stop
./viewer/tools/viewer-launcher.sh restart   # after editing serve.js
./viewer/tools/viewer-launcher.sh open      # reopen the window, server untouched
./viewer/tools/viewer-launcher.sh start -p 4000 -- surveys/llms-for-coding
```

Anything after `--` is passed through to `serve.js`, so the launcher supports the
same `--root` / `--allow` / single-file forms as the direct invocation.

| Env var | Effect |
|---|---|
| `VIEWER_PORT` | Default port when `-p` is not given (default `3000`). |
| `VIEWER_NODE` | Full path to the `node` binary, if auto-discovery misses it. |
| `VIEWER_REPO` | Serve this repo, bypassing the recents. |
| `VIEWER_STATE_DIR` | PID/port/log location (default `~/Library/Application Support/SurveyViewer`). |
| `VIEWER_NO_BROWSER` | Set to any value to start the server without opening a window. |

### Behaviour worth knowing

- **`node` is found explicitly, not via `PATH`.** A Finder-launched app inherits
  `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, so Homebrew / nvm / fnm / volta / asdf
  installs are invisible to it — a bare `node` works in Terminal and fails on
  double-click. The launcher searches those locations directly.
- **Starting twice is safe.** If the viewer already answers on the port, the
  launcher just reopens the window instead of spawning a second server.
- **A foreign server on the port is refused, not adopted.** Identity is confirmed
  by probing `/api/files` for the viewer's own payload shape, so the launcher will
  not silently attach to an unrelated dev server holding port 3000.
- **Failures surface as a Finder alert**, since an accessory app has no console.
  Full output goes to `~/Library/Application Support/SurveyViewer/viewer.log`.
- **A missing or wrong repo is reported, not silent.** The shim validates before
  exec'ing. Without that check a bad path would make a double-click do nothing
  whatsoever — `exec` on a missing path writes to a stderr that an `LSUIElement`
  app has no console for.
- **Cancelling the chooser is not an error.** Declining a dialog exits quietly
  rather than raising an alert about a choice you just made.

Covered by `tests/unit/viewer-launcher.test.js` (16 tests, `npm run test:unit`) —
including the moved-repo, wrong-repo and repo-handover cases, so none of the silent
failures can regress.

Why a launcher rather than an Electron or Tauri app: the viewer is already an
installable PWA, and a native shell would fork the rendering target — Tauri's
WKWebView is WebKit, while the 47 Playwright specs (selection, highlight-span
boundaries, KaTeX) all target Chromium. The launcher closes the actual gap, which
is terminal ceremony, without creating an untested second render path.

## Features

### Sidebar Navigation

The left sidebar lists all `.md` files in your target directory. Click any file to load it.

- **Document order:** If the target directory contains an `order.json` file, files appear in that order. Otherwise they sort alphabetically.
- **Active indicator:** The current file is bold with a blue left border.
- **Change flash:** When a file changes on disk, its sidebar entry flashes yellow (if it's not the one you're currently viewing).
- **Collapse:** Click the hamburger button (&#9776;) to hide the sidebar. Click again to restore.

### Math Rendering

All LaTeX math renders automatically via KaTeX:

| Syntax | Renders as |
|--------|-----------|
| `$x^2$` | Inline math |
| `$$\sum_{i=1}^{N} x_i \tag{1}$$` | Display math with equation number |
| `\boxed{...}` | Boxed equation |
| `\begin{cases}...\end{cases}` | Piecewise functions |
| `\begin{bmatrix}...\end{bmatrix}` | Matrices |
| `\boxplus`, `\bigoplus`, `\triangleq` | Standard math symbols |

Unrecognized commands display in red rather than crashing — the rest of the page renders normally.

### Cross-File Links

Links between markdown files work seamlessly:

```markdown
See Equation [(2)](language-models-from-first-principles.md#eq-2) for the derivation.
```

Clicking this link loads `language-models-from-first-principles.md` and scrolls to `#eq-2`. Browser back/forward buttons work as expected.

Internal anchor links (`[link](#eq-3)`) scroll within the current file.

External links (`https://...`) open in a new tab.

### Anchor Scrolling

When you navigate to an anchor (e.g., `#eq-12`), the viewer:
1. Scrolls smoothly to center the target element
2. Flashes a yellow highlight for 2 seconds
3. Also highlights the parent equation block or paragraph

HTML `<a id="eq-N">` anchors in the markdown source are preserved in the rendered output.

### Live Reload

The viewer watches for file changes on disk. When you save a `.md` file in your editor:

- **Current file:** Re-renders automatically, preserving your scroll position.
- **Other file:** Flashes the sidebar entry so you know it changed.

Typical latency from save to re-render: < 300ms.

If the WebSocket connection drops (e.g., you restart the server), the client auto-reconnects after 2 seconds.

### Search

The sidebar includes a search box that searches across all files.

- Type at least 2 characters to start searching
- Results show the filename, line number, and a text snippet with the match highlighted
- Click a result to navigate to that file
- Maximum 50 results shown

**Keyboard shortcuts:**
| Shortcut | Action |
|----------|--------|
| `Ctrl+K` (or `Cmd+K`) | Focus the search box |
| `Ctrl+B` (or `Cmd+B`) | Toggle sidebar |
| `Escape` | Clear search and unfocus |

### Inline Highlights

Mark important text in your markdown source using `==highlight==` syntax. Eight highlight colors are available, each suited to a distinct annotation role:

```markdown
==This text has a yellow highlight==

==green: This derivation is verified==

==red: This bound may not be tight==

==blue: Needs further review==

==orange: Warning or TODO==

==purple: Key equation or theory==

==teal: Definition or terminology==

==pink: Side note==
```

Available colors:

| Syntax | Color | Suggested use |
|--------|-------|---------------|
| `==text==` | Yellow (default) | General highlight |
| `==yellow: text==` | Yellow | General highlight |
| `==green: text==` | Green | Verified / passed |
| `==red: text==` | Red | Errors, broken claims |
| `==blue: text==` | Blue | Information, link |
| `==orange: text==` | Orange | Warnings, TODOs, flags |
| `==purple: text==` | Purple | Key equations, theory |
| `==teal: text==` | Teal | Definitions, terminology |
| `==pink: text==` | Pink | Notes, side remarks |

**Recoloring:** Click anywhere inside an existing highlight (without dragging) to open the toolbar in recolor mode. Click any color swatch to change the color, or ✕ to remove the highlight. The currently-active color is marked with a dark ring.

Highlights are part of the markdown source, so they:
- Survive file edits, renumbers, and splits
- Are visible in any markdown renderer that supports `<mark>` tags
- Print with colored underlines instead of background colors

### Highlights Tab

The Highlights tab in the sidebar (keyboard shortcut `Ctrl+Shift+H` / `Cmd+Shift+H`) aggregates every `==color: text==` span across every file in the document set. Use it as a per-color index of annotated passages.

- A color-chip filter bar at the top toggles which colors are visible. Click a chip to mute it; click again to re-enable.
- Each entry shows the file and 1-based line number, plus the highlighted text. Click an entry to load the file and scroll the matching block into view; the sidebar stays on Highlights so you can navigate further.
- The list refreshes automatically after any highlight is added, recolored, or removed in the current file.

### Bookmarkable URLs

The URL updates as you navigate. You can bookmark or share URLs like:

```
http://localhost:3000?file=appendix-a.md#eq-12
```

This loads `appendix-a.md` and scrolls to equation 12.

### Print

Use your browser's print function (`Ctrl+P`). The print stylesheet:
- Hides the sidebar and search
- Expands content to full width
- Converts highlight backgrounds to colored underlines for readability

## Document Ordering

Create an `order.json` in your target directory to control sidebar order:

```json
[
  "index.md",
  "executive-summary.md",
  "scope-and-the-code-modality.md",
  "language-models-from-first-principles.md",
  "the-code-model-pipeline.md",
  "evaluation-and-benchmarks.md",
  "design-guidance.md",
  "open-problems-and-roadmap.md",
  "references.md"
]
```

Files not listed in `order.json` are omitted from the sidebar. If `order.json` doesn't exist, all `.md` files appear in alphabetical order.

## Serving Different Document Sets

The viewer works with any directory of markdown files, or a single file:

```bash
# Multi-file directory
node viewer/serve.js surveys/llms-for-coding

# Single markdown file (serves parent directory, auto-opens this file)
node viewer/serve.js surveys/attention-demo/attention.md

# Any other directory
node viewer/serve.js path/to/your/docs
```

In single-file mode, the sidebar lists all `.md` files in the same directory, with the specified file opened by default.

Images referenced as `![alt](figures/image.png)` resolve relative to the target directory.

## Document Toolkit

The `viewer/tools/` directory contains scripts for managing structured multi-file documents.

### validate-refs.py — Validate References

Check all cross-file references, equation anchors, image paths, and tag sequences:

```bash
# Validate a single survey
python viewer/tools/validate-refs.py surveys/llms-for-coding/

# Validate multiple surveys (enables cross-survey ref checks)
python viewer/tools/validate-refs.py surveys/llms-for-coding/ surveys/attention-demo/

# Auto-fix stale xref link numbers
python viewer/tools/validate-refs.py surveys/llms-for-coding/ --fix

# JSON output for CI integration
python viewer/tools/validate-refs.py surveys/llms-for-coding/ --json
```

Checks performed:

| Check | Detail |
|-------|--------|
| Xref targets | `<!-- xref:ID -->` has matching `<a id="eq-2"></a><!-- eq:ID -->` in target file |
| Cross-survey xrefs | `<!-- xref:SURVEY:ID -->` resolved across survey directories |
| Anchor existence | `#eq-N` links have corresponding `<a id="eq-N">` anchors |
| Image paths | `![](path)` resolves to an existing file |
| order.json | Every `.md` file is listed (warning) |
| Duplicate eq IDs | No two `<a id="eq-2"></a><!-- eq:ID -->` share the same ID |
| Orphaned refs | `<!-- ref:ID -->` with no matching equation marker |
| Tag sequence | `\tag{N}` numbers are sequential per file |
| Broken links | `[text](file.md)` targets exist |

### split-markdown.py — Split Monolithic Files

Split a large markdown file into structured multi-file format:

```bash
# Interactive split with proposed plan
python viewer/tools/split-markdown.py surveys/big-survey.md

# Custom output directory
python viewer/tools/split-markdown.py surveys/big-survey.md --output surveys/big-survey/

# Preview without writing
python viewer/tools/split-markdown.py surveys/big-survey.md --dry-run

# Split at H3 headings instead of H2
python viewer/tools/split-markdown.py surveys/big-survey.md --split-at H3

# Archive the original file
python viewer/tools/split-markdown.py surveys/big-survey.md --keep-original

# Merge sections shorter than 100 lines with neighbors
python viewer/tools/split-markdown.py surveys/big-survey.md --min-lines 100
```

The script:
1. Scans for headings and proposes a split plan
2. Asks for confirmation before writing
3. Builds an equation map and converts cross-file references
4. Preserves existing cross-survey xrefs
5. Generates `index.md` and `order.json`
6. Runs `renumber-equations.py` and `validate-refs.py` on the result

### init-doc.py — Scaffold New Documents

Create a new multi-file document from a topic outline:

```bash
# From an outline file
python viewer/tools/init-doc.py surveys/new-survey/ --from outline.txt

# Interactive outline entry
python viewer/tools/init-doc.py surveys/new-topic/ --title "My New Survey"

# Include figures directory
python viewer/tools/init-doc.py surveys/new-topic/ --title "My Survey" --with-figures
```

Outline file format (headings become files):

```
# Document Title
## Introduction
## Language Model Fundamentals
### Autoregressive Prediction
### The Cross-Entropy Objective
## Training and Alignment
## References
```

Each `##` heading becomes a separate `.md` file. `###` headings become sections within that file. The script generates skeleton files with `<!-- TODO: content -->` placeholders, plus `index.md`, `order.json`, and a `renumber-all.sh` batch script.

### renumber-equations.py — Renumber Equations

Canonical version of the equation renumbering script:

```bash
# Single file
python viewer/tools/renumber-equations.py surveys/llms-for-coding/language-models-from-first-principles.md

# All files in a directory (respects order.json)
python viewer/tools/renumber-equations.py surveys/llms-for-coding/

# Dry-run
python viewer/tools/renumber-equations.py surveys/llms-for-coding/ --check
```

### Equation Reference Conventions

The toolkit enforces these conventions for equation cross-references:

| Type | Format |
|------|--------|
| Equation marker | `<a id="eq-3"></a><!-- eq:SECTION-N -->` before `$$` |
| Anchor | `<a id="eq-N"></a>` on marker line |
| Tag | `\tag{N}` — sequential per file |
| Within-file ref | `<!-- ref:SECTION-N -->[(N)](#eq-N)` |
| Cross-file ref (same survey) | `[(N)](target.md#eq-N) <!-- xref:SECTION-N -->` |
| Cross-survey ref | `[(N)](../other-survey/file.md#eq-N) <!-- xref:SURVEY:SECTION-N -->` |

## Requirements

- **Node.js** 18+
- **npm packages:** `chokidar`, `ws`, `ignore` (installed in `viewer/node_modules/`)
- **Browser:** Any modern browser (Chrome, Firefox, Edge, Safari)
- **Internet connection** for CDN-loaded libraries (KaTeX, markdown-it) on first load — browsers cache them afterward

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Error: Cannot find module 'ws'` on startup | `viewer/node_modules` isn't installed. Use a launcher (`scripts/serve-viewer.sh` / `scripts\serve-viewer.ps1`), which installs deps automatically, or run `cd viewer && npm install` once. |
| Math not rendering | Check browser console for KaTeX errors. Ensure internet is available for CDN. |
| Live reload not working | Check terminal for "chokidar not installed" warning. Run `cd viewer && npm install`. |
| Images not loading | Verify image paths in markdown are relative to the target directory (e.g., `figures/image.png`). |
| Port in use | Use `-p` flag: `node viewer/serve.js docs -p 8080` |
| Search returns no results | Search needs at least 2 characters. It searches raw markdown text, not rendered HTML. |
