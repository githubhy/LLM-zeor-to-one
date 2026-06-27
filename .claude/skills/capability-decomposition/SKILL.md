---
name: capability-decomposition
description: >
  Exhaustively map what a codebase implements vs does NOT — drilled
  module → class → procedure → STEP, every leaf tagged ✅ in / ⚠️ partial /
  ❌ out with path:line evidence and adversarially verified against source,
  rendered as a conformant multi-file survey under surveys/. Use when you need
  a source-grounded, step-granular "what's in / out of the box, and why" map of
  a library or subsystem. NOT for a high-level narrative (use
  deep-research-survey), a literature/SOTA landscape (deep-research-survey),
  evaluating a single candidate method, or auditing an experiment/eval.
  Token-heavy (~2 agents × every subtree); invoke explicitly.
---

# capability-decomposition — exhaustive step-level in/out-of-box map

## When to use

The question is **"what does this codebase actually implement, and what is missing — down to the level of a single algorithm step?"** and you want a TRUSTWORTHY, re-verifiable answer, not a plausible summary. The discipline below is what makes the verdict reliable: it builds full-codebase capability trees (tens of modules, hundreds of classes, thousands of step-leaves, all `/check-survey`-green), and the adversarial-verify gate catches real status/line errors before they ship.

Do NOT use for: a readable capability/architecture **narrative** (that is `deep-research-survey`, response-mode "Survey" — this skill is its exhaustive companion, not its replacement); a **literature/SOTA** landscape; deciding whether ONE proposed method is viable (a single-method evaluation); auditing the numerical correctness of an **experiment / eval harness** (an experiment audit); a quick "does X exist?" lookup (just grep).

## The output

A multi-file survey package under `surveys/<slug>/`: one `<module>.md` per top module + a top-level `index.md` (cross-module matrix + headline gaps). Each module file is module → class → procedure → step tables, per-class/subtree "not in the box" callouts, a roll-up of everything not fully in the box, and tagged references. Pairs naturally with a `deep-research-survey` overview as the front chapter (see Composition).

## The grain stop-rule (the crux — get this right or results drift)

A **step is the finest named operation that could independently be present, absent, or carry variants** — NOT an arithmetic primitive. For an HTTP client's `request` method the steps are: build the URL · merge default + per-call headers · apply auth · open/reuse the connection · encode and stream the body · read the status line + headers · decode the response body · follow redirects — each a leaf with `path:line` and a status. They are NOT "concatenate two strings", "call `len()`", "index a dict". If a leaf can't be independently present/absent/variant, it's too fine; if it hides a present-vs-absent distinction, it's too coarse. This sentence is the most important thing in the skill — put it in every decomposer prompt.

## Status tags

- **✅ present (In)** — implemented; the detail field gives variants/extent.
- **⚠️ partial (Partial)** — implemented with a material restriction or approximation; detail + `why`.
- **❌ absent (Out)** — not implemented; `why` (cite the assert / docstring / NotImplementedError / missing standard feature). The ❌ column IS the "what's not in the box, and why" deliverable.

## Phases

Run in order; read each phase file just-in-time when you start it.

| Phase | File | Goal |
|---|---|---|
| 1. Scope & scout | `phases/phase-1-scope.md` | Enumerate the module tree; choose module boundaries, subtree units, and the grain |
| 2. Decompose + verify | `phases/phase-2-decompose.md` | One agent per subtree fills the leaf tree; an adversarial verifier re-checks every absent/partial against `path:line` |
| 3. Render + conform | `phases/phase-3-render.md` | Render each module's verified leaves to a `/check-survey`-green survey file; commit per module |
| 4. Index + roll-up | `phases/phase-4-index.md` | Build the top-level index (cross-module matrix + gaps); cross-link; merge |
| 5. Update (re-run) | `phases/phase-5-update.md` | Refresh only what changed: diff source vs baseline → re-decompose touched units → splice + changelog → re-render |

**Persist the data.** At the end of a build, save the verified per-module leaf data, render metas, and the manifest into `surveys/<slug>/_data/` (with a source-baseline note). The `.md` chapters are *generated* from this data — persisting it is what makes Phase 5 (cheap incremental update + a leaf-level changelog) possible at all. Without `_data/`, the only way to update is a full re-decomposition.

**Before you start, read `gotchas.md`** — it is short and every entry cost real debugging time (workflow `args` arrive as a string; zsh doesn't word-split; the renderer must neutralize survey-linter false-positives; `check-citation-sources` has no section scoping; the 100 KB multi-file rule; commit-per-module to survive session limits).

## Assets (shipped — do not re-derive)

- `assets/cap_decompose.workflow.js` — the reusable decompose+verify Workflow, parameterized via `args = {module, root, units:[{key, prompt}]}`. Invoke with `Workflow({scriptPath, args})`.
- `assets/render_module.py <units.json> <meta.json>` — renders one module's verified leaf-trees to a conformant survey `.md` (bakes in the survey-linter conventions so it passes `/check-survey` first try). `units.json` is the workflow's `result.units`; `meta.json` shape is in `schema/meta.example.json`. It **warns** (stderr) on any partial/absent leaf missing a `why`, and emits per-class "Open in explorer" cross-links **only when `meta.explorer` is truthy** (see below).
- `assets/render_index.py <manifest.json>` — renders the top-level `index.md` cross-module matrix + headline gaps from all module unit files.
- `assets/update_diff.py --old <m>.units.json --new <rerun>.units.json [--out --changelog]` — splices re-decomposed subtree units into saved data and emits a leaf-level ✅/⚠️/❌ changelog (Phase 5).
- `assets/recall_check.py <source-dir>... --units <module>_units.json` — the **recall / completeness** check (Phase 2): enumerates the module's public classes and reports those not represented in the decomposed units (the candidate-miss list). Complements the precision verify stage.
- `schema/leaf.schema.json` — the per-subtree decomposition schema (LEAF_SCHEMA); now **requires `why` for `status ∈ {partial, absent}`**. `schema/meta.example.json` — the per-module render meta.

## Optional deliverable — interactive explorer

The persisted `_data/` can drive an **interactive explorer** (a zoomable icicle/treemap over modules→classes→procedures→steps with in-place code reveal) alongside the `.md` chapters. To enable it for a survey:

1. Build the explorer data with a `build_explorer_data.py` that merges `_data/*.units.json` → `tree.json` + `code-spans.json` (keyed by raw `path:line` evidence). The class id convention is `{slug}:{ci}` where `ci` is the **module-global class index in units-file order**.
2. Set `"explorer": true` in each module's `meta.json`. `render_module.py` then emits an `[Open <Class> in the explorer ↗](/explorer.html?node={slug}:{ci})` link per class heading — the `{slug}:{ci}` MUST match `build_explorer_data.py`'s counter (file order, not meta order). With the flag absent, no links are emitted (so other decompositions are not given dead links).

> A `build_explorer_data.py` is typically survey-/viewer-coupled (hardcoded out-dir, repo source roots) — generalise it per codebase, or treat the explorer as an optional, reference-implementation-coupled add-on.

## Dependencies

Reuses the survey infrastructure (do NOT re-implement it): `viewer/tools/` validators (lint-math, renumber-*, link-references, validate-refs, check-citation-sources, build-index), `.claude/rules/math-authoring.md` + `citation-integrity.md`, and the `/check-survey` gate. If those are absent, install them (they ship with `deep-research-survey` / the survey toolchain) before running this skill.

## Composition

- **`deep-research-survey`** — write the readable overview as the front chapter; this skill produces the exhaustive step-level chapters under the same `surveys/<slug>/` package. (e.g. `overview.md` + one step-level chapter per module + `index.md` in one package.)
- **A follow-on method-evaluation / experiment-audit / reference-implementation study** — a ❌/⚠️ leaf is a concrete starting point: "is this missing variant worth adding / how does the present one compare?" The `path:line` evidence feeds straight in.

## Cost

Roughly `N_modules × N_subtrees × 2` agents (decompose + verify). A full-codebase run can reach ~100+ agents. Scale by **grain** (coarser stop-rule = fewer leaves) and by **module selection** (pilot one module first to calibrate the grain before fanning out). Commit per module so a session limit never loses completed work.

## Cross-link sign-off

Before sign-off, cross-link the new/expanded survey into the corpus (per `.claude/rules/cross-linking.md`): run the `cross-link` skill (or `crosslink.py check $SCOPE --changed`) and clear the reported high-value gaps, or file a `todos/` entry for any left out of scope. A freshly authored document has no links and the gap detector will fire — clearing it is part of done.
