# Phase 4 — Index + roll-up + cross-link

## Goal
Tie the module files into one navigable survey package and land it.

## Steps

1. **Build the manifest.** A list `[{slug, title, units:"<module>_units.json"}]` in the reading order you want (e.g. core → io → client → models → transport → utils).

2. **Render the index.** `python3 assets/render_index.py manifest.json > surveys/<slug>/index.md`. It computes the cross-module matrix (per module: in / partial / out / classes, with a TOTAL row), a headline out-of-the-box gaps table (top `moduleLevelAbsent` per module), and a "how to read a module file" note.

3. **Conform the index.** Run `renumber-sections.py` on the dir and the per-file checks on `index.md` (lint-math, validate-refs, bare-refs, check-citation-sources, check-footnote-refs). The index has no `## References`, so the citation check sees 0 entries and passes.

4. **Pair with an overview (optional but recommended).** If a `deep-research-survey` narrative exists, put it in the same package as `overview.md` and make `index.md` the shared entry: a "start here → overview.md" pointer above the matrix, and a "deeper companion → index.md" pointer in the overview. One package, two layers.

5. **Commit the index** (`docs(survey): add capability-tree index + cross-module matrix`), then **merge** the branch to the integration branch (fast-forward keeps history linear) and push.

## Honesty in the final artifact
- State the scale (modules · classes · leaves · in/partial/out) in the index preamble.
- Note the verification discipline and that corrections were minor (or list material ones).
- If you bounded coverage (skipped a module, coarsened the grain), say so — silent truncation reads as "covered everything" when it didn't.

## Deliverable
`surveys/<slug>/index.md` + the merged, pushed package. One entry point: open `index.md`.
