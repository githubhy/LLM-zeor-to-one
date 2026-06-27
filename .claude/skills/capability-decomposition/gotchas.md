# Gotchas

Each of these cost real debugging time in practice. Read before starting.

## Workflow `args` arrive as a STRING
The Workflow tool sometimes delivers `args` to the script as a JSON string, not an object, so `args.units` is `undefined` and `pipeline()` throws `expects an array`. The shipped `cap_decompose.workflow.js` already guards this: `const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})`. Keep that guard if you edit the workflow.

## zsh does not word-split unquoted variables
`python3 viewer/tools/$chk` where `chk="lint-math.py f --errors-only"` passes the WHOLE string as one argv to python (so it tries to open a file literally named `lint-math.py f --errors-only`). bash splits; zsh (the default shell here) does not. Always run checks through a function that forwards args positionally:
```sh
run(){ shift; out=$("$@" 2>&1); [ $? -eq 0 ] && pass=$((pass+1)) || { echo "FAIL $*"; echo "$out"|grep -iE "error|bare|untagged"; }; }
run lint python3 viewer/tools/lint-math.py "$F" --errors-only
```
(Filename globbing like `*.md` DOES work in zsh — only variable word-splitting is off.)

## The renderer must neutralize survey-linter false-positives
`render_module.py`'s `esc()`/`esc_md()` already do these; if you add a linter, add the neutralization there and re-render ALL modules:
- **`§` on external clause numbers** → `cl. ` (else `validate-refs --bare-refs-only` reads "§5.3" as an internal section ref).
- **`Eq. (N)` / `Eq (N)`** → `eq N` (else the same bare-ref check reads it as an internal equation ref).
- **ordered lists `^N. `** → bullets. `check-citation-sources` matches `^\d+\.` / `^[\d]` ANYWHERE in the file as a bibliography entry (it has no `## References` section-scoping), so numbered list items get flagged "untagged". Use bullets in survey bodies; keep `[N]` only in the References section.
- **cross-reference markers (`<!-- cite -->`, `<!-- secref -->`) must never be the first content of a block or list item** — CommonMark eats the line as raw HTML. Keep them mid-sentence after prose.

## The renderer must escape markdown emphasis/mark in DATA strings (not a linter — a *render-fidelity* bug)
This one is invisible to `/check-survey` and only shows when you read the rendered survey in the viewer. The data is full of literal code tokens — Python dunders (`__init__`, `__all__`, `__getstate__`), `*args`/`**kwargs`, operators (`e==0`, `retries==1`), `n*m`. Dropped into markdown as plain text they are eaten by the **strong/em** (`__x__`, `*x*`) and **`==mark==`** rules: `__init__`→"init", `__all__`→"all", `e==0`→"e0", and a `*` inside the renderer's own `*role*` italic wrap mangles the whole cell. `esc_md()` fixes this by escaping `_`/`*`/`==` **outside** backtick code spans (so the data's own `` `inline code` `` is left intact, and `code()`-wrapped evidence stays raw — backticks already shield it). Use `esc_md()` for every plain-text cell (summary/role/proc/step/detail/why/what + the index's gap table); keep `code()` raw.

## References run together without a blank line between entries
`render_module.py` must emit a blank line between consecutive bib entries (`if i>1: P('')`). Without it the `[1]…`/`[2]…` lines are one CommonMark paragraph and render as a single run-together line in the viewer (passes the gate, looks broken to a reader). overview.md's hand-authored references already have the blank lines — match that.

## Leaked machine-absolute paths in evidence
The decomposition agents sometimes record evidence/file as `/Users/<you>/.../src/<pkg>/...` (machine-absolute) instead of repo-relative `src/<pkg>/...`. These render verbatim into the published survey. Strip the repo-root prefix in the data before rendering (a textual `replace('<repo-root>/', '')` over the `*.units.json` is safe and format-preserving). `build-index.py` had the same leak in its `.index.md` regen-comment (now emits `os.path.relpath`).

## `check-citation-sources` resolves paths from `viewer/tools/parents[2]`
It (correctly) treats `<repo>/viewer/tools/<tool>.py → parents[2]` as repo root, so `(spec: docs/specs/mcp/...)` files resolve. Any tool you relocate that uses a fixed `parents[N]` for repo root will break — resolve via `CLAUDE_PROJECT_DIR` or a `.git` walk instead (any cross-directory move triggers this).

## 100 KB = multi-file, always
One module's step-level tree is often 100–200 KB. Never concatenate modules into a single file (the `deep-research-survey` rule, and the post-edit lint hook chokes on huge files). One file per module + a top-level `index.md`.

## Commit per module; survive session limits
A full run can be ~100+ agents and can outlast a usage window. Commit each module the moment it's `/check-survey`-green. If a workflow dies on a limit, re-launch it (cached agents return instantly via `resumeFromRunId`) once the window resets — completed modules are already safe on disk.

## Don't string-equal the verdict
Verifiers phrase the verdict freely ("TRUSTWORTHY", "HIGH TRUSTWORTHINESS", "Largely trustworthy…"). Match loosely (`test("trustworth";"i")`) or you'll false-alarm on a perfectly good module. The thing that actually matters is whether any `checked[].status == "refuted"` or a correction flips a status.

## The `.md` is generated — persist the data or you can't update
Chapters are rendered from `_data/<module>.units.json`; the data, not the `.md`, is the source of truth. Hand-edits to a chapter are clobbered on the next render. And if you don't persist `_data/` at the end of a build, the only way to ever *update* the decomposition is to re-decompose everything from scratch — Phase 5's cheap diff-based update needs the saved leaf data + a recorded source baseline. Persist `_data/` every build.

## Pilot before fanning out
The grain stop-rule is the biggest quality lever. Run ONE module end-to-end, eyeball the leaf tables, adjust the grain, THEN fan out the rest against the fixed template. Re-grading 10 modules is expensive; re-grading 1 is cheap.
