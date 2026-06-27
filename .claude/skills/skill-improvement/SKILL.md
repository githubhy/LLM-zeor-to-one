---
name: skill-improvement
description: >
  Run a rigorous, repeatable improvement cycle on an existing skill: landscape
  scan, comparison, tiered proposal, a switchable lazy-loaded flag-lattice
  implementation, A/B verification (per-item + optional end-to-end), report, and
  merge. Use when asked to improve, upgrade, enhance, A/B, or harden an existing
  skill (or its prompts/workflow). Applies the progressive-disclosure + A/B
  discipline it installs into the target skill to itself.
---

# Skill Improvement

Take an existing skill and produce a measured, default-off improvement layer for it —
proposed changes that are independently toggleable, lazily loaded, and verified by A/B
rather than asserted. Born from running this exact process on `deep-research-survey` and
`reference-implementation-study` (see their `proposals/` + `reports/` + `bench/` runs).

## Modes (selectable depth)

Selected from `$ARGUMENTS` (e.g. `deep-research-survey depth: full`):

- **`quick`** (default) — scaled for a fast, low-cost improvement: landscape from parametric
  memory + a few targeted searches; per-item verification only; end-to-end A/B skipped; no
  mandatory branch/merge. Use for a focused upgrade.
- **`full`** — every stage at full rigor: live-web landscape fan-out + adversarial verify +
  completeness critic; per-item AND worktree-isolated end-to-end A/B (trust-but-verify); full
  report; dedicated branch + merge. Use when the improvement must be airtight.

Record the chosen depth + target skill in the proposal and report.

## Read this first

Before Phase 1, read `gotchas.md` (the hard-won failure modes — isolation, trust-but-verify,
don't-over-claim, citation discipline, collision-safe IDs). In `quick` mode skim it; in `full`
mode treat it as binding.

## Phases

Run in order; read each phase file just-in-time. Each names the template(s) it uses.

| Phase | File | Goal | quick | full |
|-------|------|------|-------|------|
| 1. Scope & branch | `phases/phase-1-scope.md` | read the target skill's anatomy; (full) cut a branch | yes | yes |
| 2. Landscape | `phases/phase-2-landscape.md` | competitive scan + adversarial verify + completeness critic | scaled | full |
| 3. Compare & propose | `phases/phase-3-propose.md` | comparison matrix + tiered P0/P1/P2 proposal | yes | yes |
| 4. Implement | `phases/phase-4-implement.md` | lazy flag-lattice (selector + addenda + pointers + items.json) | yes | yes |
| 5. Verify | `phases/phase-5-verify.md` | 5a per-item A/B; 5b end-to-end A/B (worktree, trust-but-verify) | 5a | 5a+5b |
| 6. Report & merge | `phases/phase-6-report.md` | implementation report + ledger; (full) merge + cleanup | report | report+merge |

## Templates (`templates/`, copy-paste-ready)

- `lazy-flag-lattice.md` — the `## Modes and flags` selector + `addenda/` + per-phase pointer convention (Phase 4).
- `items.schema.json` — the per-item flag registry shape (Phase 4).
- `wf-landscape.workflow.js` — parameterized competitive-landscape scan (Phase 2).
- `wf-per-item-verify.py` — per-item verifier: controlled-task output demos + structural-discrimination of any gate (Phase 5a).
- `wf-end-to-end-ab.workflow.js` — worktree-isolated end-to-end A/B driver, trust-but-verify (Phase 5b).

## Core principles (non-negotiable)

- **Additive + default-off.** The improvement layer never changes the target skill's baseline
  behavior unless a mode/flag is set. The original is a strict subset.
- **Lazy from day one.** Improvement text lives in `addenda/` loaded only when a flag is active.
- **Verify, don't assert.** Every claimed benefit is A/B-measured; report nulls and
  inconclusives straight. Trust-but-verify any agent-reported result.
- **Isolate skill execution.** Agents that run the target skill write into a worktree or a
  namespaced sandbox and RETURN text; audit for strays before committing.
