# Proposed-mode addendum — Phase 4 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P1-2`, `P2-3`, `R-DEPTH`). `R-DEPTH` is a Part-2 richness item (apply iff `proposed`
/ `richness` is set or `R-DEPTH` is in `flags`); read `R-GOV` in `addenda/phase-2.md`
first — it tiers which methods/results get the heavy treatment below.

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

**[R-DEPTH] Per-card depth gates (apply to `headline`/`load-bearing` items per R-GOV).**
When authoring each method card (R-CARD), write these elements to depth:

  - DERIVATION [C1]: from definitions -> NUMBERED assumptions -> NUMBERED intermediate
    steps (none skipped, per `math-authoring.md`) -> boxed result, structured as named
    Step / Assumption / Theorem-Lemma blocks. A bare stated+cited governing equation is
    a flagged gap of the same class as an omission.
  - INTUITION [C2]: a paired "why this construction exists / what it buys / geometric
    picture" alongside the math for each non-obvious result.
  - LIMITING CASES + ASYMPTOTICS [C4 + M1]: (a) reduce the closed form to at least one
    named known result in an explicit limit (e.g. greedy / zero-temperature decoding,
    single-token context, the infinite-data or infinite-compute limit, the large-width
    limit), AND (b) give the leading-order scaling law, the crossover/knee point vs the
    baseline, the saturation / irreducible-loss-floor asymptote, and the model breakdown
    boundary — the part a designer derives FROM to predict and decide (distinct from the
    correctness-only reduces-to check).
  - WORKED EXAMPLE [C3]: carry the smallest non-trivial (or a production-realistic,
    model-scale-anchored) parameter set through the derived equation with intermediate
    values shown and the config disclosed; it doubles as a reference-implementation
    unit-test oracle.
  - COMPLEXITY + FINITE-PRECISION [C8]: dominant op-count per token / per forward pass,
    big-O WITH the leading constant where it matters, memory (parameters / activations /
    KV-cache), bit-width (fp16 / bf16 / int8), and a one-line conditioning /
    numerical-stability note — in implementation-relevant units, feeding the §7 matrix.
  - FAILURE MODES + ROBUSTNESS [M2 + M3]: a short "when it breaks, why, and the symptom"
    entry, plus per load-bearing assumption what happens when it is violated (graceful
    degradation vs cliff). Seeds the downstream red-team / limitations work.
  - PREDICTION + EPISTEMIC TAGS [M4 + M9]: tag each performance/complexity claim
    Quantitative (predicts a magnitude + tolerance, falsifiable downstream) vs
    Directional; tag each load-bearing result with its epistemic basis
    {derived-here / reproduced-from-primary / textbook / inference / conjecture}.
  - EQ-TO-CODE / SPEC CORRESPONDENCE + TRACEABILITY [C19 + C13]: anchor every spec- or
    model-card-defined quantity to its exact section / clause / version at point of use
    (bracket-wrapped external-section form, e.g. `[MCP spec §6.2]`), classify it
    MANDATED / PRESUMED / SPEC-SILENT, and name the reference / spec equation the derived
    result reproduces ("these coincide under this specialization") plus the implementing
    function where a reference implementation exists.
  - SECOND-ROUTE CROSS-CHECK [C5] (load-bearing only): confirm via an independent
    derivation OR a numeric/Monte-Carlo check — two routes converging is the strongest
    internal consistency check the survey can carry without an external citation.
  - UNIFYING-FRAMEWORK DERIVATION [M6] (method families): where a family admits one,
    derive a single master result and recover members as parameter settings (e.g. a
    general attention-kernel form recovering softmax / linear / sparse attention) —
    simultaneously more rigorous and SHORTER than N independent derivations.

**[R-DEPTH] Audience-register modulation (read `config/audience-register.json`; default
`practitioner` = current behavior).** The resolved register tunes the EXPOSITION of each gate
above WITHOUT changing the math: `learner` derives prerequisites, expands every routine step,
pairs intuition + analogy around each result, LEADS with the worked example, and defines terms
on first use; `expert` compresses ROUTINE algebra ("standard manipulation gives ..."), gives a
one-line intuition, and relegates definitions to the notation contract. **INVARIANT:** the
DERIVATION [C1] load-bearing-step floor holds in EVERY register — `expert` compresses routine
connective algebra, never a load-bearing logical step (`math-authoring.md` "do not skip steps"
applies to load-bearing steps always); and the boxed result, the WORKED-EXAMPLE [C3] oracle
numbers, and the PREDICTION + EPISTEMIC tags are identical across registers (config
`register_invariants`). The register changes how it reads, never what is true.
