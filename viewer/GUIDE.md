# Markdown Viewer — User Guide

A zero-build, real-time markdown viewer for multi-file document sets with full KaTeX math rendering, cross-file navigation, live reload, and inline highlights.

## Install

```bash
cd viewer && npm install
```

This installs the required `chokidar`, `ws`, and `ignore` packages. You need **Node.js 18+**.

## Quick Start

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
| Math not rendering | Check browser console for KaTeX errors. Ensure internet is available for CDN. |
| Live reload not working | Check terminal for "chokidar not installed" warning. Run `cd viewer && npm install`. |
| Images not loading | Verify image paths in markdown are relative to the target directory (e.g., `figures/image.png`). |
| Port in use | Use `-p` flag: `node viewer/serve.js docs -p 8080` |
| Search returns no results | Search needs at least 2 characters. It searches raw markdown text, not rendered HTML. |
