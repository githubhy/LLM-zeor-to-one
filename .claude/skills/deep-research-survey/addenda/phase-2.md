# Proposed-mode addendum — Phase 2 (load on demand)

Apply each block iff `proposed` / `richness` is set OR its id is in the active `flags`
set (`R-GOV`, `R-CARD`, `R-SURVEY`). These are the **Part-2 richness / depth** items
(the survey-improvement proposal, Part 2). They raise depth PER LOAD-BEARING CONCEPT,
not words per method. **Read `R-GOV` first — it governs the cost of every other depth
gate (R-CARD, R-DEPTH, R-MATHREV, R-COVER, R-RUBRIC); without it the per-method gates
become a length tax on a long inventory.**

**[R-GOV] Depth-tier governor (read first; precondition for all depth gates).** In the
outline — **assigned in Phase 1, before the `P0-3` confirmation gate**, so the outline
the user approves is already tiered (`[opt:DT-L2-OUTLINE · default ON · toggle .claude/skill-options.json]`) —
tag every method/variant and every load-bearing result as one of
`headline` / `load-bearing` / `catalog`. The heavy artifacts (full derivation,
worked example, second-route cross-check, dedicated figure) apply to `headline` and
`load-bearing` items only. A `catalog` item carries a compact stated-result + a
one-line applicability note + an EXPLICIT `n/a (<reason>)` for each skipped artifact
("explicit n/a beats silent absence"). Depth is
measured as a COVERAGE FRACTION over load-bearing items, never as prose volume (see
R-RUBRIC). A tight survey that fully treats its few headline methods and catalogs the
rest must score HIGHER than a bloated one that half-treats everything. This is the
direct fix for the known "added length, not judged quality" failure of the P0-2 loop.
The three tier names are a **fixed vocabulary, mechanically gated** by
`viewer/tools/check-depth-tiers.py` (a `/check-survey` step): an invented or
mistyped tier is a build error, since R-GOV is the precondition for every
downstream depth gate and nothing else re-reads the authored `Depth tier:`
label. One off-ladder label, `supporting`, is allowed-but-distinct — reserved
for non-method **context** sections (standardization-provenance traces, not
method cards, so not on the depth-budget ladder); adding or retiring a
vocabulary value is a taxonomy change recorded in `decisions/` (2026-07-08-02).
**Persisted allocation (the Layer-3′ north-star).**
`[opt:DT-L2-OUTLINE · default ON · toggle .claude/skill-options.json]` Record the
per-section tiers as a machine-readable table in the Phase-1 outline artifact
(`survey/_scratch/00-*-outline.md`) under a `<!-- depth-tier-allocation -->`
marker: a markdown table `| Section | Tier | Justification |`, one row per numbered
section, the `Section` cell being the delivered heading-anchor id (`<a id="sec-N">`).
This table is the authoritative depth-budget allocation every later phase reads back,
and is the left-hand side of the Phase-5 drift-diff
(`viewer/tools/depth-tier-coverage.py`, wired by R-COVER/R-RUBRIC): a delivered
`Depth tier:` label that diverges from its approved row is a `TIER-DRIFT` finding.
*Off (`DT-L2-OUTLINE` off):* tiers stay prose-only in the outline and no drift
baseline exists — Layer 3′ still runs its category-safe checks but skips
`TIER-DRIFT` / `MISSING-TIER`.
*Audience-register interaction:* the resolved `audience` register
(`config/audience-register.json`, set in Phase 1) sets the FUNDAMENTALS FLOOR — `learner`
pins the fundamentals / prerequisite concepts at `headline` (full pedagogical depth);
`expert` demotes them to `catalog`/recap (assume known) so the depth budget concentrates on
advanced material; `practitioner` (default) tiers them on merit as usual. The register tunes
WHICH tier the basics get; it never changes the coverage-fraction SCORING (R-RUBRIC stays
register-blind) or any boxed result.

**[R-CARD] Uniform per-method "method card" outline template.** Every entry in the §5
method/variant inventory instantiates the SAME card skeleton, so the inventory is
equal-depth and decision-comparable, and true variants nest under their parent:

  1. One-line idea.
  2. Method-in-context — taxonomy placement (umbrella class, sibling techniques, the
     one distinguishing mechanism) + lineage (which predecessor limitation it was
     created to fix) + equivalences/reductions to siblings.
  3. First-principles derivation (depth set by R-DEPTH in Phase 4).
  4. Intuition / motivation companion (R-DEPTH).
  5. Limiting cases + asymptotics / regime-map (R-DEPTH).
  6. Worked numerical example (R-DEPTH).
  7. Complexity + finite-precision (R-DEPTH).
  8. Failure modes + robustness to assumption violation (R-DEPTH).
  9. Falsifiable prediction tag + epistemic-status tag (R-DEPTH).
 10. Equation-to-code / spec correspondence + traceability (R-DEPTH).

A card element a `catalog` method omits must show `n/a (<reason>)`, not vanish.
Co-locate the full derivations with the card, or in a dedicated derivations appendix
(split to its own file once > 100 KB), mirroring the dedicated-derivations-appendix
precedent the repo's deepest surveys converged on.

**[R-SURVEY] Survey-level richness artifacts (reserve slots in the outline).** Beyond
per-card content, nominate these default deliverables:

  - §7 MASTER COMPARISON MATRIX: rows = every inventory method (gate the row count
    against §5), fixed columns = the declared evaluation axes PLUS an "assumptions &
    cost" column (the extra supervision / preference data / reward model / compute /
    context the method needs — so a higher-scoring method that did NOT ship has a
    visible reason), and a SELECTION / decision table ("when to use / when not").
  - §8 QUANTITATIVE SOTA: a results table (one row per published model/result — metrics
    + eval conditions (benchmark, few-shot $k$, decoding params, model scale) + source
    tag, with a normalization note when conditions are incomparable) + a causal
    deployment-gap thesis (published-vs-deployed, and WHY) + a per-stage
    (pretraining / alignment / inference) dominant-practice map.
  - FIGURES (per the `.claude/rules/figure-operating-conditions.md` rule + the `workflow.md` diagram rule):
    each architecture/method-family carries at least one conceptual block diagram (ASCII
    fenced-code as the zero-dependency default) and each load-bearing quantitative claim
    carries a reproducible figure with persisted data + generator + a numeric-disclosure
    caption.
  - NOTATION CONTRACT (front matter): one table of symbol -> meaning -> UNITS &
    CONVENTION (nats vs bits, log base, per-token vs per-sequence, pre- vs post-softmax
    logits) -> defining-section cross-link. The externalized form of the P1-2 symbol
    memory.
  - §10 OPEN PROBLEMS + REFERENCE-IMPLEMENTATION HANDOFF: each gap = {question, known,
    unknown, why it matters (which section's limit it hits), state-of-attack, plausible
    approach + one-line reason, candidate next step}; nominate study-ready methods with a
    baseline-to-beat + a closed-form PREDICTED MARGIN + the hypothesis a downstream
    `reference-implementation-study` will test.
  - READER'S-QUESTIONS / Q&A APPENDIX: an anchored section that pre-answers the "why is
    X built this way / what breaks if not / why this and not the obvious alternative"
    questions (wires `survey-explainer-fold` in proactively, not as a later patch).
  - METHOD-SEARCH REGISTER (optional): route any load-bearing-but-unsettled viability
    question ("is a faster/cheaper realization possible?") through the `method-eval`
    skill and archive scored dossiers under `surveys/<survey>/method-search/`.
