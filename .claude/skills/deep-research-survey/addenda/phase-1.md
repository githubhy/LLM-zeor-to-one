# Proposed-mode addendum — Phase 1 (load on demand)

Apply iff `proposed` or `flags: P0-3` is active.

**P0-3 — research-brief + plan-preview gate.** Before leaving Phase 1, emit a
one-screen research brief (subject, audience, depth, output contract, exclusions,
source preferences) plus the section outline with must-have / nice-to-have flags
**and the R-GOV depth-tier table**
(`[opt:DT-L2-OUTLINE · default ON · toggle .claude/skill-options.json]` — a
`section · tier · one-line justification` row per section, so the outline the user
approves is already tiered; **surface every `supporting` row explicitly** so the user
confirms it is genuine non-method context, not a depth-dodge), and surface it for a
SINGLE user confirmation. Do not spend evidence-collection budget before the brief is
acknowledged. Persist the brief as the "north star" the later phases refer back to —
the tier table as a `<!-- depth-tier-allocation -->` block in
`survey/_scratch/00-*-outline.md` (R-GOV), which the Phase-5 drift-diff reads back.
*Off (`DT-L2-OUTLINE` off):* the brief carries the outline without a tier table (the
pre-2026-07-08 behaviour); Layers 1 and 3′ remain the edit-path backstop.
