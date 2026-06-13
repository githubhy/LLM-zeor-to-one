# Proposed-mode addendum — Phase 4 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P1-2`, `P2-3`).

**P1-2 — memory-guided synthesis (replaces the blind UNION merge). PROMOTED TO BASELINE 2026-06-03 — now the default method for the large/high-stakes multi-agent synthesis path in `phases/phase-4-synthesis.md`; this flag is a retained no-op alias. Promoted on survey-scale A/B evidence (RESULTS Updates 8/11/14); see `decisions/2026-06-03-01`. The block below is kept for provenance.** Write sections
SEQUENTIALLY, not as independent parallel drafts. Maintain a running global-state
memory of every symbol/term defined, every equation/result stated, and what each
prior section covered. Before writing section k, reuse the established notation and
definitions EXACTLY — never redefine a symbol, never restate an equation
differently, never contradict a prior section. After each section, update the
memory. Order sections by conceptual dependency. Do NOT generate independent drafts
and merge them.

**[P2-3] Mid-generation steering checkpoint.** For long surveys, after the outline
and again after a first-draft pass, surface a lightweight review the user can
redirect — not only at the two endpoints.
