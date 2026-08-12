# Phase 0: Survey-Side Derivation Authoring (conditional)

`[opt:RIS-PHASE0 · default ON · toggle .claude/skill-options.json]`

**Conditional phase.** Runs at the very start of the study — **before Phase 1** — but **only when
the study needs load-bearing math the survey does not yet contain** (a finite-precision variant, a
new operator, a discretized recursion, a new channel/estimator model). When the survey already
derives every operator the study will implement, **skip this phase** and go straight to Phase 1;
the Prerequisites line + the G0 gate (Phase 1.5) then cover the existing derivations. When
`RIS-PHASE0` is `off`, skip the phase regardless and author any needed derivation ad-hoc (the
pre-2026-07-24 flow).

## Why this phase exists

The RIS Prerequisites assume "a completed survey with method inventory and first-principles
derivations," and G0 (Phase 1.5) *verifies* that by independently re-deriving each load-bearing
operator. But a study frequently introduces **new math the survey does not yet contain** and must
**author that derivation into the survey first**, to survey standard, to have a foundation to
implement (and later G0-attest) against. Absent this phase, studies invent a study-local "Phase 0"
with no guidance for what it must deliver — which recurred upstream twice (a
decoder-parameter study authoring a new operator into an appendix; a finite-precision study
authoring a bounded-accumulator recursion).

**P0 is not P1.5.** They are complementary, not redundant:

| | Phase 0 (this phase) | Phase 1.5 (G0) |
|---|---|---|
| Action | **authors** the derivation INTO the survey (the foundation) | **independently re-derives** it to attest soundness |
| Output | a survey/wiki section to survey standard + the procedure↔equation inventory | a `derivation_ledger` (re-derived from axioms, not re-read) |
| Guards | the equation *exists and is authored correctly* | the equation *is sound* before any code |

So P0 writes the foundation; G0 (a **different** pass, ideally different agent) checks it from
scratch. Running the same reasoning twice — once to write, once to attest — is the point;
`.claude/rules/sim-report-completeness.md` already notes "G0 attests the equation is sound before
Phase 2; the §4 table then attests the code matches it."

## Goal

Author the load-bearing derivation(s) the study needs **into the survey corpus** (`surveys/**` or a
`wikis/` derivation ledger), to survey standard, and produce a **procedure↔equation inventory** so
that every code procedure the later phases will write maps to a numbered survey equation.

## Deliverables

1. **The authored survey section(s)**, first-principles, per `.claude/rules/workflow.md` math rules
   and `.claude/rules/math-authoring.md` (numbered equations with stable-ID markers, cross-links,
   paragraph anchors). Build **on** existing survey sections (cite and reduce to them), do not
   duplicate.
2. **Each new equation states the form it reduces to** in the appropriate limit (the `b → ∞` /
   `Δ → 0` / continuous limit that recovers the operator it generalizes, citing that operator's
   existing equation number). A new operator whose limit does **not** recover the known form is a
   derivation bug caught here — and this limit statement *is* the study's H-characterization
   prediction that the finite version reduces correctly.
3. **The procedure↔equation inventory** — one row per code procedure the study will implement →
   the numbered survey equation it computes, **0-uncovered**, each row semantically checked with
   the CA-INTERNAL discriminator (does the equation's arity/pushforward match what the procedure
   computes — a single-argument deterministic map vs. a density-level order-statistic/convolution
   — not merely that an anchor RESOLVES). Authoring this map up front (rather than retrofitting it
   at the Report §4 stage) pre-populates both the G0 ledger's `survey_ref` column and the Report §4
   eq↔function table.

## Gate (P0)

P0 defers to the **survey gates** rather than adding a new validator target:

- `/check-survey <dir>` (lint-math errors-only, renumber eq/sec/para `--check`, validate-refs,
  bare-refs at `error`, citation-source tags) — all clean.
- `citation-audit` on any external citations the new derivation introduces (prefer citing
  derivations already in the survey over new external sources — `.claude/rules/citation-integrity.md`).
- **Cross-link sign-off** (`.claude/rules/cross-linking.md`): a freshly authored section fires the
  gap detector by design — clear the high-value gaps or file a `todos/`.
- **0-uncovered** procedure↔equation inventory (every planned procedure maps to ≥1 authored
  equation; each row arity/pushforward-checked, not resolve-only).

A P0 that leaves an uncovered procedure, an un-reduced new operator, or a red survey gate is not
signed off — the study has no sound foundation to implement against.

## Worked instances

- **a finite-precision study (2026-07)** — §D.11 "Finite-precision datapath: the bounded accumulator
  and its image" in a survey appendix (a numbered equation block): the bounded reduced-precision
  accumulator, the saturation-fold density image, the lift-consistency identity, the `b → ∞`
  reduction back to §D.7, and the extrinsic caveat — built on §D.7, all survey gates clean.
- **a method-parameter study** — an upstream Phase-0 plan for the same shape
  + `.../2026-05-21-appendix-d-oms-cn-operator.md`: authored Appendix D's OMS-CN operator derivation
  + the §D.6 layered P-DE recursion.

## Cross-references

- `phases/phase-1b-derivation-gate.md` — the G0 gate P0 feeds (P0 authors → G0 attests).
- `.claude/rules/math-authoring.md`, `.claude/rules/workflow.md` (math derivation rules),
  `.claude/rules/cross-linking.md`, `.claude/rules/citation-integrity.md` — the survey standard P0
  authors to.
- `.claude/skill-options.json` (`RIS-PHASE0`) — this phase's toggle.
