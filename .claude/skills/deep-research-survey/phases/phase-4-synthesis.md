# Phase 4: Synthesis

## Goal
Write section drafts from the evidence ledger, preserving supported findings and resolving conflicts explicitly.

## Constraints
- Distinguish standard practice from state of the art from engineering judgment.
- Preserve supported outlier findings that add real signal.
- For large or high-stakes surveys, write sections with **memory-guided synthesis**: draft them sequentially in conceptual-dependency order, keep a running memory of every symbol/term defined and every equation/result stated, reuse that notation and those definitions exactly in each later section (never redefine a symbol, restate an equation differently, or contradict an earlier section), update the memory after each section, and keep every unique supported finding. This is now the default for the multi-agent path, superseding the older blind UNION merge (independent parallel drafts merged with no shared state), which drifts cross-section (the same quantity defined two ways, one result given two equation numbers). Survey-scale validated — about 40% fewer cross-section inconsistencies across topics; see decision 2026-06-03-01. Single-pass quick surveys are unaffected.
- Optionally spawn a verification pass to check factual accuracy against the evidence ledger.

## Attribution Discipline
- **Sourced facts**: cited inline
- **Engineering judgment**: labeled as such
- **Inferences**: labeled as such
- When no source found: say "no source found" rather than omitting or fabricating

## Deliverable
Complete section drafts with inline citations, clearly separated facts/inferences/recommendations.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` / `richness` or `flags: P2-3, R-DEPTH` is active, read `addenda/phase-4.md` (P2-3 mid-generation steering checkpoint; **R-DEPTH per-card depth gates** — derivation / intuition / limiting-cases+asymptotics / worked-example / complexity+finite-precision / failure-modes+robustness / prediction+epistemic tags / eq-to-code+spec / second-route cross-check / unifying-framework, tiered by R-GOV) and apply the active blocks. **P1-2 (memory-guided synthesis) was promoted to baseline — see Constraints above and decision 2026-06-03-01; its flag is now a retained no-op alias.** In `original` mode, skip — do not read it.
