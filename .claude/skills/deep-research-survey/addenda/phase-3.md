# Proposed-mode addendum — Phase 3 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P0-1`, `P1-1`, `P2-1`).

**P0-1 — deterministic Workflow orchestration.** Collect evidence with a `Workflow`
`pipeline()` (one `evidence-collector` agent per section/subtopic, a structured-output
schema for each ledger row) instead of manual background `Agent` launches. The
runtime supplies completion handling and durable journaling, so the manual
scratch-file checkpoint and 15-minute dead-agent poll become a non-Workflow fallback
only. Keep the per-agent scope rule (5 or fewer questions per agent).

**P1-1 — structured (AttributeTree) evidence.** Distill each source into a structured
record — `{claim, method, result, condition, source_url, quote, quality_tier,
confidence}` — at collection time (a natural fit for the Workflow output schema),
instead of free-text ledger cells. Synthesis then cites structured fields, not prose
recollection.

**[P2-1] Optional citation-graph evidence model.** For high-stakes surveys, organize
evidence as a citation/semantic graph stratified into Foundation / Development /
Frontier layers (or a taxonomy) instead of the flat ledger, so multi-aspect coverage
and cross-section synthesis are structural rather than manual. Keep optional.
