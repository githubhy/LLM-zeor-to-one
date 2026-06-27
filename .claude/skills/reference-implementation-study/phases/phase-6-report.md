# Phase 6: Report & Decision

## Goal
Consolidate all findings into a written study with a clear recommendation.

## Study Document Must Cover
1. Problem statement and task & data distribution (model under study, benchmark, decoding params)
2. Candidate method descriptions with key equations
3. Baseline comparison results with figures (including CI error bars; e.g. a quality-vs-budget curve)
4. Sensitivity analysis highlights
5. Realisation / reduced-precision results (if Phase 5 ran)
6. **Recommendation table**: winner, runner-up, conditions where each alternative wins
7. **Red-team critique**: challenge the top recommendation with at least two realistic scenarios where the runner-up would outperform, assumptions that if violated change the ranking, and metrics within CI of another candidate
8. Limitations and suggested follow-on work

The full section-by-section structure (executive summary, protocol/harness-conformance matrix,
theory-as-predictor overlays — e.g. a scaling-law prediction laid over the measured loss/accuracy
curve, reproduce block, audit trail) is the load-bearing subset enforced by
`viewer/tools/check-report-completeness.py` — author to it; it is mechanically gated (below). Use
the conformance grades **EXACT / IDEALIZED / SPEC-SILENT** where "spec" is the published eval
protocol / model card / paper the reproduction is graded against.

## Completeness & verification (before sign-off)

Run **`/study-signoff <study> <topic>`** (or `python .claude/skills/reference-implementation-study/signoff.py <study> <topic>`) for the one-shot **mechanical** board — G1–G4 + REPORT (report-completeness, `viewer/tools/check-report-completeness.py`) + CITE (citation source-tags). Then the two **agent-driven** audits the runner can only remind about:

- Run the **`sim-audit`** skill — the untrusting multi-lens numerical-correctness audit
  (independent re-derivation, property/invariant tests, statistical validity, published-baseline
  anchors, edge-case robustness, determinism) — and fold its per-lens verdict + defect register
  into the report's Audit-Trail section. Do this before believing the headline.
- Run the **`citation-audit`** skill on external citations (the existing citation gate).

## Final Checklist
- [ ] Number all display equations
- [ ] Record milestone completion in the study manifest (`artifacts/<study>/study-manifest.json`)
- [ ] Log delivery in the session's `prompts/YYYY-MM-DD-<session-slug>.md`
- [ ] All quality gates passed (G1-G4, or G1-G2 if Phases 4-5 skipped)
- [ ] REPORT gate passes (report-completeness) + `sim-audit` run, defects filed to `bugs/`

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P1-2, P2-2, P2-4` is active, read `addenda/phase-6.md` and apply the active blocks (P1-2 multi-metric aggregation, P2-2 reproduce-from-artifacts, P2-4 Pareto-front/dominance analysis). In `original` mode, skip — do not read it.
