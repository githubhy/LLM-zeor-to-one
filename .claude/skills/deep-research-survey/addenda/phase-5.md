# Proposed-mode addendum — Phase 5 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P1-3`, `P0-2`, `P2-2`). The "TARGETED EDITS" rule below is mandatory whenever
either P0-2 or P1-3 is active.

**P1-3 — adversarial, separate-model verification + contradiction detection.** Run
the citation/factual audit with a SEPARATE model from the one that wrote the
synthesis (never let the writer verify its own citations). For high-stakes claims,
spawn a small adversarial refute-panel and keep a claim only if it survives. Add an
active contradiction-detection sub-step: decompose to atomic claims, cross-check for
source disagreement, and surface contradictions explicitly in the gaps section.

**P0-2 — self-evaluation rubric gate (mandatory before sign-off).** Have a separate
judge score the draft on Coverage, Structure, Relevance, Synthesis, Critical-Analysis
(each 1-5) plus a cross-section consistency check. If any dimension is below 4/5, fix
the weakest area and re-score; repeat until every dimension is at least 4/5. Emit the
final scorecard into the report under a "## Self-evaluation scorecard" heading.

**Applying P0-2 / P1-3 fixes — TARGETED EDITS ONLY (never regenerate the document).**
At survey scale, re-outputting the whole survey to apply a fix silently drops sections
and breaks citations: bug `2026-05-30-04` saw a single-turn whole-document rewrite cut a
7-section survey to 5 and dangle all 144 citations (no reference list), scoring 16/25.
Instead, the fix step must emit a LIST of localized edits — each
`{op: replace | append_end, old_string (verbatim + unique), new_string}` — that the
orchestrator applies deterministically (exact-match replace, or append at end). After
applying, assert three guardrails: (1) section count is preserved vs the pre-fix draft,
(2) every citation marker resolves to a reference anchor (no dangling links), (3) no agent
reasoning preamble leaked into the body. Validated on the HST A/B (RESULTS Update 12): the
same P0-2/P1-3 gates applied as targeted diffs scored 24.67/25 (all 7 sections kept,
citations intact, the wrong conformance value corrected) vs 16/25 for the whole-document
rewrite — a +8.7-point swing from the mechanism alone.

**[P2-2] Cost / latency telemetry.** Emit a one-line telemetry footer in the report:
tokens, wall-clock, and estimated USD per survey and per agent (the Workflow runtime
exposes `budget.spent()` and per-agent counts). Use it to make the agent-sizing
limits data-driven instead of a frozen 2026-03 heuristic.

**[P3-1] Token-efficient citation audit (locus-targeted + materiality triage). PROMOTED TO BASELINE 2026-05-31 — now the default behaviour of `.claude/skills/citation-audit/SKILL.md` (Phases 1 & 3); this flag is a retained no-op alias. Promoted on directional N=1 A/B evidence by user directive, ahead of the proposal's multi-topic gate; see `decisions/2026-05-31-03` and `proposals/2026-05-31-citation-audit-token-efficiency.md` [§5.1]. The block below is kept for provenance.** Cut the
Phase-5 citation-audit cost without losing detection. (a) MATERIALITY TRIAGE: after the
Phase-1 ledger, classify each citation `numeric-load-bearing` / `claim-load-bearing` /
`decorative`. Only the two load-bearing classes get a source-opening verify agent;
`decorative` citations get the mechanical check (`check-citation-sources.py` presence + tag)
plus a one-line bibliographic spot-check — no agent. (b) LOCUS-TARGETED READS: a verify agent
reads ONLY the cited locus — `grep` the spec clause / cited value and read a tight window, or
`Read` a narrow PDF `pages` range — never the whole source; widen only on a miss. (c)
SOURCE-GROUPING: one agent per distinct source file, verifying all its citations in one
context load. (d) CONCURRENCY CAP + FAULT SPLIT: cap verify fan-out at 4-6 concurrent agents;
an agent that gets empty tool output returns `tool-unavailable` (re-queued serially), never
`unverifiable` (which is a source finding). GUARDRAIL: triage demotes effort, it never skips
verification of load-bearing values — every `numeric-load-bearing` citation still gets a
value-reproduction read. ACCEPTANCE: re-run on a survey carrying a known mislabeled-source
violation; the violation must still surface. Full design + measurement plan:
`proposals/2026-05-31-citation-audit-token-efficiency.md`.
