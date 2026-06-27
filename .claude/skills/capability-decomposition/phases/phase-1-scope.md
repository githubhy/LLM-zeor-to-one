# Phase 1 — Scope & scout

## Goal
Turn "map this codebase" into a concrete work-list: the module boundaries, the subtree units per module, the grain, and where the survey lands.

## Steps

1. **Enumerate the tree.** For the target package, list: top-level modules, their submodules/files with LOC, and the public classes per submodule. Cheap and mechanical (`find`, `wc -l`, `grep -nE '^class [A-Z]'`, read the `__init__.py` exports). This is the skeleton.

2. **Choose module boundaries.** One survey file (and one workflow run) per **top module** (e.g. `core`, `io`, `client`, `models`, `transport`, plus framework/utils). A big module (e.g. a 13 kLOC subpackage) is still one file; you split it into subtree *units* below, not into multiple files.

3. **Split each module into subtree units.** A **unit = one decomposer agent**, sized to roughly one coherent sub-area (a directory or a few related files, ~one agent's worth of reading). Aim for **5–8 units per module**. Examples: `client` → {session, auth, models, transport, redirects, retries, utils}; a large `io` package → {readers, writers, codecs, streaming, buffering, utils}. Split a procedure-dense file (a 2 kLOC engine) into its own unit; merge thin files into a `utils` unit.

4. **Fix the grain.** Restate the stop-rule from SKILL.md ("a step = finest independently present/absent/variant operation, not arithmetic primitives") and pick a worked example for the module so the decomposers calibrate. If unsure, **pilot one module end-to-end first** and eyeball the leaf tables before fanning out — the grain is the single biggest quality lever and the cheapest thing to get wrong at scale.

5. **Decide placement.** Output is a multi-file package `surveys/<slug>/` (per the 100 KB multi-file rule — never one giant file). If pairing with a `deep-research-survey` overview, that becomes `overview.md` in the same dir and `index.md` is the shared entry.

## Deliverable
A unit list per module: `[{key, files, classes, procedure-hints}]`, ready to drop into the workflow `args`. Plus the chosen slug and grain example.
