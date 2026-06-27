---
name: reference-implementation-study
description: >
  Drive a topic from survey findings through reference implementation,
  comparative evaluation, sensitivity analysis, reduced-precision /
  quantized realization, and a final engineering recommendation. Use after a
  deep-research-survey has produced a completed survey with method inventory,
  math derivations, and SOTA assessment. Applicable to any LLM / AI method,
  ML-systems, or algorithm-engineering domain.
---

# Reference Implementation Study

Take the output of a completed deep-research-survey and turn it into working reference code, reproducible comparative experiments, and an actionable engineering recommendation.

## Modes and flags

Selected from the skill arguments (`$ARGUMENTS`):

- **`original`** (default) — baseline 6-phase workflow only. Do NOT read any `addenda/` file. Current behavior, unchanged.
- **`proposed`** — apply ALL improvements (P0-1 … P2-4).
- **`flags: <ids>`** — apply ONLY the named items, e.g. `flags: P0-1,P0-2` (per-item lattice for item-by-item A/B ablation).

**Lazy loading (token discipline).** The improvement addenda are NOT inlined — they live in `addenda/` and cost zero tokens unless a non-`original` mode is active. When `proposed` or `flags:` is set: read `addenda/global.md` once (P1-3), then read `addenda/phase-N.md` just-in-time when you begin phase N — and only if `proposed` is set or one of that phase's item ids (named in each phase file's one-line pointer) is in the active `flags` set. Apply a block iff `proposed` is set OR its id is in `flags`. Pass the active flags to the gate validator as `--flags <ids>` so its optional checks fire. Record the active mode/flags in the study doc. Default stays `original` — no `addenda/` file is ever read. Item registry: `bench/reference-implementation-study/items.json` — **not yet present in this repo** (the registry and bench scenarios are not mirrored here; the default `original` mode needs none of them, and the `proposed`/`flags` modes are fully driven by the `addenda/` files below — graceful degradation).

## Prerequisites

- A completed survey under `./surveys/` with method inventory and first-principles derivations.
- A clear problem domain (task type, input/data distribution, evaluation setting, target model or serving platform).

If either is missing, run `deep-research-survey` first or ask the user to supply the gap.

## Phases

Run in order with quality gates. Read each phase file just-in-time.

| Phase | File | Goal | Gate |
|-------|------|------|------|
| 1. Scenario | `phases/phase-1-scenario.md` | Define task & data distribution, metrics, constraints, candidates | — |
| 2. Implementation | `phases/phase-2-implementation.md` | Code each candidate with uniform interface | G1 |
| 3. Baseline | `phases/phase-3-baseline.md` | Multi-seed comparative eval study with CI | G2 |
| 4. Sensitivity | `phases/phase-4-sensitivity.md` | Sweep hyperparameters and environment | G3 |
| 5. Precision | `phases/phase-5-precision.md` | Reduced-precision / quantized realisation (skip if N/A) | G4 |
| 6. Report | `phases/phase-6-report.md` | Consolidate findings + recommendation + red-team | — |

Gate validation: `python .claude/skills/reference-implementation-study/validate_gate.py <study-name> <gate>`

**Citation gate.** Before Phase 6 sign-off, run the `citation-audit` skill on the report's citations: every external citation must trace to an acquired source per `.claude/rules/citation-integrity.md`.

## Artefact Rules

- **Persistent data**: save results so figures regenerate without rerunning compute (eval traces, scores).
- **Interactive**: support zoom, pan, hover unless embedded in a static document.
- **Reproducibility**: every config stored in JSON summary; all random seeds and decoding params explicit.
- **Naming**: `artifacts/<study-name>/` with one subdirectory per phase.
- **Manifest**: maintain `artifacts/<study-name>/study-manifest.json` — versioned iteration log.

## Implementation Rules

- All configs as **frozen dataclasses** with typed fields and sensible defaults.
- All random seeds and decoding parameters **explicit and stored** in config.
- Shared helpers in `implementation/<topic>/utils.py`.
- Named constants for numerical-safety floors (softmax / log-sum-exp / normalisation epsilons).
- Tests under `tests/<topic>/`.

## Skill Chaining

```
deep-research-survey  →  reference-implementation-study
       surveys/                implementation/<topic>/ + artifacts/ + docs/
```

## Gotchas

- Gate G1 failures from import errors are usually missing `__init__.py` files or circular imports. Fix before proceeding.
- Phase 3 CI error bars require at least 3 seeds. With exactly 3, the CI is wide — prefer 5.
- Phase 5 quantization with saturation can silently clip activations / weights. Always check for saturation (clipping/overflow) warnings.
- The study manifest must be updated after every phase — forgetting breaks regression tracking.
- Red-team critique in Phase 6 must be substantive. "The winner is clearly best" is not a valid critique.

## Cross-link sign-off

Before sign-off, cross-link the new/expanded study + survey content into the corpus (per `.claude/rules/cross-linking.md`): run the `cross-link` skill (or `crosslink.py check $SCOPE --changed`) and clear the reported high-value gaps, or file a `todos/` entry for any left out of scope. A freshly authored document has no links and the gap detector will fire — clearing it is part of done.
