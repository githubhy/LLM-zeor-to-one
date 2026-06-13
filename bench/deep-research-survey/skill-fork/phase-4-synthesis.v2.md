# Phase 4: Synthesis (v2 — memory-guided, implements proposal P1-2)

## Goal
Write section drafts from the evidence ledger, preserving supported findings and
resolving conflicts explicitly, with a running global-state memory so sections
stay mutually consistent.

## Constraints
- Distinguish standard practice from state of the art from engineering judgment.
- Preserve supported outlier findings that add real signal.
- **MEMORY-GUIDED SYNTHESIS (replaces the blind UNION merge).** Write sections
  sequentially, not as independent parallel drafts:
  - Maintain a running memory of every symbol/term defined, every equation/result
    stated, and what each prior section already covered.
  - Before writing section k, read the memory; reuse the established notation and
    definitions EXACTLY; never redefine a symbol, never restate an equation
    differently, never contradict a prior section.
  - After writing section k, update the memory.
  - Order sections by conceptual dependency (prerequisites first).
- Do NOT generate independent drafts and merge them.
- Optionally spawn a verification pass to check factual accuracy against the ledger.

## Attribution Discipline
- Sourced facts: cited inline
- Engineering judgment: labeled as such
- Inferences: labeled as such
- When no source found: say "no source found" rather than omitting or fabricating

## Deliverable
Complete section drafts, internally consistent in notation and claims, with inline
citations and clearly separated facts/inferences/recommendations.
