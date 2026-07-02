---
slug: mi-appendix-followups
date_filed: 2026-07-01
status: closed
---

# Appendix I (MI) — post-buildout follow-ups

## Context

Appendix I (Mechanistic Interpretability, I.1–I.9) was authored and validated in one session (report `reports/2026-07-01-mi-appendix-buildout.md`). All mechanical gates are green and every citation was verified in-source at authoring time (catching + fixing two attribution errors, see `field-notes/2026-07-01-mi-appendix-authoring.md`). Two small items remain.

## What is left

- **Run the formal `citation-audit` skill** over Appendix I as the independent final gate. Authoring-time in-source verification was done, but the standalone audit (the mandated delivery gate for newly-cited content per `.claude/rules/citation-integrity.md`) was not separately run. Scope: references [70]–[93] and their in-text uses in `appendix-i-mechanistic-interpretability.md`.
- **Optional backlinks** §A.9 and §A.22 → §I.4/§I.6 (induction material → intervention toolkit + head zoo). The crosslink gate is already green without them (appendix-i links *to* those sections), so this is polish, not a gap.
- **Optional origin-credit web refs**: Elhage "Toy Models of Superposition" and Bricken/Templeton monosemanticity (transformer-circuits.pub, `web` tags) if a future pass wants to credit the superposition/monosemanticity origins. Not load-bearing; the derivations are self-contained and the local SAE papers carry the cited claims.

## Acceptance

- `citation-audit` run on Appendix I with any findings resolved.
- Backlinks added or explicitly deemed unnecessary.

## Refs

- Report: `reports/2026-07-01-mi-appendix-buildout.md`; plan: `plans/2026-07-01-mi-clusters-survey-buildout.md`.
- Rule: `.claude/rules/citation-integrity.md`; skill: `.claude/skills/citation-audit/SKILL.md`.

**Resolution.** (2026-07-01) Formal `citation-audit` run on Appendix I — **24/24 citations `correct`** at bibliographic/locational/claim/value layers; report `reports/citation-audit-appendix-i-2026-07-01.md`. Optional §A.9/§A.22→§I backlinks and origin-credit `web` refs **scoped out** as unnecessary: the `crosslink --changed` gate is already green (appendix-i links *to* those sections), and the derivations are self-contained so the web-only origins carry no load. No `bugs/` entry (no wrong citation shipped).
