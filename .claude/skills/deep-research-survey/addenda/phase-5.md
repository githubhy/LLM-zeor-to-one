# Proposed-mode addendum — Phase 5 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P1-3`, `P0-2`, `P2-2`, `P3-1`, `R-MATHREV`, `R-COVER`, `R-RUBRIC`). The "TARGETED
EDITS" rule below is mandatory whenever P0-2, P1-3, or R-MATHREV is active. The `R-*`
items are Part-2 richness items (apply iff `proposed` / `richness` is set or the id is
in `flags`).

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

**[R-MATHREV] Adversarial math-derivation review (sibling to the citation audit;
mandatory when active).** Before sign-off, a SEPARATE reviewer (never the writer)
re-derives every boxed/derived result from first principles and audits it for sign /
scale errors, algebra slips, wrong constants, fabricated operating-configs, and
overclaims — especially the words "exact" / "optimal" / "minimal", which must be
downgraded to honest bounds unless the derivation supports them. This is the math-side
counterpart of P1-3's citation audit and the most reliable rigor lever in the repo's
logs — it routinely catches sign / scale errors in derived results (e.g. a flipped
scaling-law exponent or a mis-normalized softmax). Apply fixes as TARGETED EDITS only
(same rule as the P0-2/P1-3 block above).

**[R-COVER] Adversarial coverage / completeness audit (replaces the single 'Coverage'
judge number).** Operationalize "omission risk is a quality problem": decompose the
topic into sub-areas; per sub-area run an independent ideal-inventory-finder ->
adversarial-verifier to build the inventory the survey SHOULD contain, plus an
exclusions manifest; diff it against the actual §5 inventory and flag every gap. Add a
cross-cutting completeness critic that no single-sub-area reviewer owns. Run before the
R-RUBRIC coverage-fraction scoring so the denominator (the ideal inventory) is trustworthy.

**[R-RUBRIC] Re-pointed depth rubric (extends the P0-2 gate onto depth axes).** When
P0-2 is active, ADD these depth dimensions, each scored by a COVERAGE FRACTION over
LOAD-BEARING items (per R-GOV) or by presence-of-structured-artifact — NEVER by prose
volume, so padding cannot raise the score (the explicit fix for the P0-2 "added length,
not quality" failure):

  - Derivation completeness: fraction of load-bearing methods with a no-skipped-steps
    derivation (flag any multi-step result given as a single prose block).
  - Intuition coverage: fraction with a why/intuition companion.
  - Worked-example coverage: fraction with a hand-checkable instance.
  - Asymptotics/regime coverage: fraction of load-bearing closed forms with a
    scaling-law + crossover analysis.
  - Complexity coverage: fraction with op-count + finite-precision.
  - Spec-traceability: fraction of spec- / model-card-defined quantities with a clause /
    version anchor + MANDATED/PRESUMED/SPEC-SILENT classification.
  - Decision-usefulness (artifact-presence): comparison matrix has one row per inventory
    method; a selection/decision table is present.

Gate sign-off on per-fraction thresholds; emit the fractions into the
"## Self-evaluation scorecard" alongside the P0-2 dimensions.

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
context load. (d) CONCURRENCY CAP + FAULT SPLIT: cap verify fan-out at the active scale's limit (`config/operational-scale.json`: standard 4-6, wide ≤12) concurrent agents;
an agent that gets empty tool output returns `tool-unavailable` (re-queued serially), never
`unverifiable` (which is a source finding). GUARDRAIL: triage demotes effort, it never skips
verification of load-bearing values — every `numeric-load-bearing` citation still gets a
value-reproduction read. ACCEPTANCE: re-run on a survey carrying a known mislabeled-source
violation; the violation must still surface. Full design + measurement plan:
`proposals/2026-05-31-citation-audit-token-efficiency.md`.
