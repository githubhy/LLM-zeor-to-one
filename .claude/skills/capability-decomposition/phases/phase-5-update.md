# Phase 5 — Update an existing decomposition

## When
The codebase changed (new release, added feature, refactor) and a capability-tree package already exists with persisted data in `surveys/<slug>/_data/` (`<module>.units.json` + `<module>.meta.json` + `manifest.json` + a baseline in `_data/README.md`). Goal: refresh **only what changed**, and produce a changelog of how the capability surface moved.

> **Precondition.** This phase needs the persisted `_data/` (the verified leaf data). A full build (Phases 1–4) that didn't persist `_data/` can only be updated by re-decomposing from scratch — so always persist `_data/` at the end of a build.

## Steps

1. **Scope the change against the baseline.** Read the source baseline from `_data/README.md`, then diff the source roots:
   ```
   git diff --name-only <baseline-commit> HEAD -- src/<pkg>        # in-repo source package
   git diff <old-submodule-sha> <new-submodule-sha> --name-only    # for a vendored submodule
   ```
   Map each changed file to its **subtree unit** using the unit→files mapping in the module's `*.meta.json` order + the original unit prompts. The set of touched units is your work-list. If nothing in a module changed, skip it entirely.

2. **Re-decompose only the touched units.** Run `assets/cap_decompose.workflow.js` with `args.units` = just the changed units for that module (same prompts as the original, refreshed for any new files). This is the whole point: a one-file change re-runs ~2 agents, not the whole tree.

3. **Splice + changelog.** Merge the re-run units into the saved data and see what moved:
   ```
   python3 assets/update_diff.py --old surveys/<slug>/_data/<m>.units.json \
                                 --new /tmp/<m>_rerun.units.json \
                                 --out surveys/<slug>/_data/<m>.units.json \
                                 --changelog /tmp/<m>_changelog.md
   ```
   The changelog lists every leaf transition (e.g. `❌→✅  Session · request · follow redirects`), added/removed steps, and class/module-level absence changes. Review it — it is the human-readable "what the source change did to the capability surface."

4. **Re-render the affected chapters + index** (Phase 3 render step, but only for touched modules), run `/check-survey surveys/<slug>/` to green.

5. **Update the baseline** in `_data/README.md` to the new source commit(s)/date, and **commit** — include the changelog in the commit body (or as `surveys/<slug>/_data/CHANGELOG-<date>.md`) so the capability delta is part of the record.

## Notes
- The `.md` chapters are generated; **never hand-patch them** — edit `_data/*.units.json` (or re-decompose) and re-render.
- Granularity is whole-subtree: a tiny change still re-runs the unit it lives in. To surgically flip a single known leaf without an agent, you may edit the leaf in `_data/<m>.units.json` directly and re-render — but prefer re-decomposition so the verify gate still runs.
- If the change adds a whole new module/subtree, that's a Phase-1 scope addition (new unit + meta entry + manifest row), not just an update.
