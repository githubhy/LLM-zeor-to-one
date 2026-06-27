# Phase 3 — Render + conform

## Goal
Turn each module's verified leaf-trees into a `/check-survey`-green survey file, and commit it.

## Steps (per module)

1. **Write the meta.** Author `<module>_meta.json` (shape: `schema/meta.example.json`): `title`, `slug`, `coverage`, `cite_sentence` (with `<!-- cite:N -->[[N]](#ref-N)` markers), `order` (unit keys), `titles` (key→label), `references` (full tagged bib lines — `(local: ...)` for an acquired paper, `(spec: ...)` for an acquired formal spec, `(web)` otherwise; see `.claude/rules/citation-integrity.md`). Acquire any cited paper or spec first (`source-fetch`) so the tag is strong.

2. **Render.** `python3 assets/render_module.py <module>_units.json <module>_meta.json > surveys/<slug>/<module>.md`. The renderer emits the preamble, legend, subtree matrix, per-class procedure→step tables, "not in the box" callouts, the roll-up, and references — and **bakes in the survey-linter conventions** (bullets not ordered lists; `§`→`cl.`; `Eq.(N)`→`eq N`) so it passes first try. Don't hand-edit the body; fix the data or the renderer. It also **warns to stderr** on any partial/absent leaf missing a `why` (fix the data), and — when `meta.explorer` is set — emits per-class "Open in explorer" cross-links (see SKILL.md → *Optional deliverable*; the `{slug}:{ci}` must match `build_explorer_data.py`).

3. **Run the marker tools + gate** (the `/check-survey` sequence):
   ```
   viewer/tools/renumber-sections.py surveys/<slug>/      # inject sec anchors
   viewer/tools/link-references.py   surveys/<slug>/<module>.md
   viewer/tools/build-index.py       surveys/<slug>/<module>.md --min-lines 200
   # then check-survey: lint-math, renumber-{equations,paragraphs,sections} --check,
   # link-references --check, validate-refs, validate-refs --bare-refs-only --severity=error,
   # check-citation-sources, check-footnote-refs  → all must pass
   ```
   Run the checks through a shell function that passes args positionally (`run(){ ...; out=$("$@"); ...}`), NOT `python3 viewer/tools/$var` — zsh does not word-split unquoted variables (see gotchas).

4. **Commit the module** (`docs(survey): add <module> step-level capability tree`). Per-module commits make the run resilient to interruptions and keep the diff legible.

## If a check fails
The renderer fixes the known false-positives; a new failure means either new data shape (e.g. a fresh linter pattern — neutralize it in `render_module.py`'s `esc()` and re-render all modules) or a real content issue. The common ones are in `gotchas.md`.

## Deliverable
`surveys/<slug>/<module>.md` (+ `.index.md`), `/check-survey`-green, committed.
