# Experiment / Implementation Report Completeness Rule

Loaded on demand by `CLAUDE.md`. Read this file before writing or signing
off any reproduction / evaluation-study report under `docs/` or
`reports/` (e.g. a `reference-implementation-study` Phase-6 deliverable).

The exhaustive, section-by-section specification — with the rationale and
what each artifact concretely contains — belongs in a companion
experiment-report-spec proposal under `proposals/` (authored on demand).
This rule is the load-bearing summary plus the mechanically-checked subset.

## The rule

A complete report carries the 14-section spine below; a missing **[M]**
artifact blocks sign-off like a `lint-math` violation. The three governing
tests: a decision-maker gets the verdict in 60 seconds (Section 0); a
skeptic walks every claim down to the figure/table that proves it; a
stranger regenerates every number from one command.

| Sec | Title | Load-bearing [M] artifact |
|---|---|---|
| 0 | Executive Summary | headline number + signed margin + CI on line 1; claims→evidence spine |
| 1 | Problem, Scope & Descent | pre-registered hypotheses with numeric thresholds; link to the parent survey |
| 2 | Task, Dataset & Protocol Anchors | fixture tables with benchmark-version / split traceability; external reference value (model card / paper) cited at point of use |
| 3 | Task Model, Candidates & Conventions | numbered task + candidate + metric equations; decoding-config-convention block (temperature / top-p / n-shot / max-tokens); notation glossary |
| 4 | Implementation & Math-to-Code | module map; equation↔function table; numerical-safety floors |
| 5 | Verification & Sanity Anchors | verification-vs-validation split; published-baseline / closed-form anchor table; test-to-claim inventory |
| 6 | Baseline Results & Verdict | margin-accounting table; **CI on every cell**; one reconciled citable margin |
| 7 | Sensitivity & Ablation | per-hypothesis PASS/FAIL/INCONCLUSIVE verdicts |
| 8 | Quantization | float-vs-low-bit knee table (fp16/bf16 → int8/int4, if quantization in scope) |
| 9 | Recommendation | one imperative verdict + conditions table + do-not-cite clause |
| 10 | Limitations, Red-Team & Flip | skeptic-authored threats; flip-table; ≥2 lose-to-baseline scenarios |
| 11 | Roadmap | prioritised gaps → `todos/` |
| 12 | Reproducibility Appendix | one-command reproduce recipe + env + seed map + raw-data invariant |
| 13 | Audit Trail | `bugs/`/`decisions/`/`field-notes/` IDs; citation-integrity statement |

A small single-metric study (e.g. a perplexity-only or accuracy-only run)
need not have all 14 sections, but must not *silently* drop an [M] artifact —
drop it explicitly with a one-line reason ("explicit n/a beats silent
absence").

## Five emphases this rule front-stops

**Theory is a predictor, not only a bound.** Every result with a closed
form (a scaling-law loss prediction, a `pass@k`-vs-`k` curve, an
emergent-capability threshold) carries the analytic prediction *overlaid*
on the experiment points with the residual; residuals beyond tolerance are
root-caused into {harness bug / asymptotic-only / unmodeled effect}. Sanity
anchors (Section 5) check fixed known values; this checks the predicted
*curve*. Hypotheses are tagged Quantitative (magnitude predicted) vs
Directional; prefer Quantitative wherever a closed form exists.

**"Protocol-faithful" is graded, not binary.** Section 2 carries a
**Protocol-vs-Eval conformance matrix** — one row per benchmark-mandated or
agreed parameter with a status in `{EXACT / APPROXIMATED / IDEALIZED /
DEVIATED / PROTOCOL-SILENT-CHOICE}` and a metric-impact column. Three
buckets: **mandated** (the eval must match the official protocol — prompt
template, scoring, n-shot), **idealizable** (the eval approximates; disclose
the metric impact in the discrepancy budget), and **protocol-silent** (the
decoding params, system prompt, and other choices the benchmark does *not*
fix — design choices, not compliance). For a benchmark that presumes a
decoding setup without mandating it, the honest claim is "an eval of *this
configuration* clears the bar," not "the benchmark mandates this
configuration."

**A published benchmark score is not a target — decompose it.**
`[opt:SIM-REQBASIS · default ON · toggle .claude/skill-options.json]` When the
report benchmarks against an **externally published number** (a model card's
reported MMLU, a leaderboard entry, a paper's headline `pass@1`), that number is
**reference performance + a configuration stack** (prompt template, few-shot $k$
and exemplar pool, decoding params, harness version, answer-extraction rule),
*not* a bare capability measurement. Section 2 states the decomposition
`published = reference + configuration delta`, with the reference **sourced** to
the artifact that reports it (per `.claude/rules/citation-integrity.md`), and the
verdict names **which basis it is measured against**: a margin measured against a
number produced under *your* harness and prompt is a real delta; a margin against
a vendor-published number is mostly harness and prompt difference and must **not**
be cited as a capability gain. The failure mode is a "+N point" headline that is
largely answer-extraction and few-shot formatting — reproducible on every re-run,
because the number was never wrong; the *story about it* was. If the reference
cannot be reproduced under your harness, disclose that and benchmark against the
published value with the caveat (explicit n/a beats silent absence). This is
`.claude/rules/calibration-residuals.md` check 4 (metric-basis reconciliation)
applied to the published number itself.

**The baseline is under test too — validate the control at its own best operating
point before publishing a margin against it.**
`[opt:SIM-BASELINE · default ON · toggle .claude/skill-options.json]` A comparative
result is a *difference*, so it is exactly as sensitive to the control arm as to the
treatment — but the scrutiny is never symmetric. The treatment is the thing being
proposed and gets derivations, sweeps and adversarial review; the control inherits an
obvious-looking default configuration and is never itself questioned. **A handicapped
control inflates the treatment effect, and it reproduces perfectly on every re-run**,
so no amount of repetition, seeding discipline or CI-tightening will surface it.

Before publishing a margin, state for the **baseline** what you would state for the
candidate: its configuration, why that configuration, and — the load-bearing one —
evidence that it is not being run below its own best setting. The cheapest sufficient
check is usually to vary the baseline's one most-arbitrary knob and confirm the chosen
setting is not dominated. In LLM work that knob is nearly always the decoding
temperature / top-$p$, the few-shot $k$, or the retriever's top-$k$ — a decoding
method compared against greedy, or a reranker compared against a retriever run at a
$k$ that starves it, is measuring its own baseline's handicap. The shape to watch for:
the baseline's *simpler* variant beating its *elaborated* one is proof the elaborated
arm is miscalibrated, not proof the treatment is good. Upstream measured a case where
roughly **half** a published gain was the baseline's miscalibration; forty-plus runs
never surfaced it. This is `.claude/rules/calibration-residuals.md` check 6 ("check
the rig's preconditions, **especially on the control**") applied one level up, at the
moment a comparative margin is published rather than when a residual is attributed.

**A single reference value has no dispersion — carry the contributing
population.** `[opt:SIM-REFPOP · default ON · toggle .claude/skill-options.json]`
Extends `[opt:SIM-REQBASIS]`. A published benchmark number is one lab's run under
one harness: the **spread across independent reproductions is the matched noise
floor** for any margin measured against it
(`.claude/rules/calibration-residuals.md` check 6 corollary — significance is not
materiality). A `+0.5` point margin means one thing when independent harnesses
reproduce the reference within 0.3 points and something else when they span 3
points, and a single published value cannot tell you which. This is not
hypothetical for LLM benchmarks: the same model on the same test split routinely
differs by several points across evaluation harnesses, purely from prompt-template
and answer-extraction differences.

**Obligation, graded by the claim — not by the result.** Wherever the report
publishes a **margin** against a reference, it carries the contributing
population as *structured data*, not prose:

```
reference_performance: { value, basis_condition, selection_rule,
                         source, n, contributors: [ {source, value,
                         condition, harness} ] }
```

Elsewhere it is best-effort, and an unavailable population is recorded
`(not-published)` — explicit n/a beats silent absence. Acquisition is via
`source-fetch` and the model card / paper; never from memory
(`.claude/rules/citation-integrity.md`).

**Two constraints that make it honest rather than decorative:**

- **Only same-basis values may be pooled**, and every contributor carries its
  `condition`. A 0-shot number, a 5-shot number, and a 5-shot-CoT number for one
  model on one benchmark are **three different quantities, not a spread**; pooling
  them manufactures dispersion that does not exist. Check 4 again, one level down.
- **N is small and self-selected.** A benchmark's published reproductions are few,
  and a lab with an awkward result need not publish. **State N and the raw values;
  never percentile or quantile language** — "our result sits at the 60th
  percentile" over five self-selected samples is not a statistic. The population
  bounds a claim; it does not confer significance.

The `selection_rule` field is load-bearing, not bookkeeping: whether a reported
number is a single run, a best-of-$n$, or a mean over seeds is part of the value's
meaning, and a margin against a best-of-$n$ reference is not the same claim as a
margin against a mean.

## Anti-patterns (mechanically checked)

`viewer/tools/check-report-completeness.py <report.md>` flags these (it runs
as a `reference-implementation-study` `REPORT`-gate step and can be run
standalone, parallel to `check-citation-sources.py`):

- a results headline with no CI / uncertainty column
- a rate metric (accuracy / `pass@k` / exact-match) reported with a
  Wald/Gaussian interval — require Wilson / Clopper–Pearson
- "protocol-faithful" asserted as a binary, with no per-parameter
  EXACT/IDEALIZED/DEVIATED status
- a result with a known closed-form prediction shown *without* the analytic
  overlay (theory used only as a threshold, never as a predictor)
- a protocol-silent design choice (decoding config, system prompt, few-shot
  selection) presented as a compliance item
- "further study is warranted" without a named `todos/` action; "production
  default" without the numeric value
- a figure value that lives only in source code, not the caption
- a missing Reproduce block / external value with no source tag

## Cross-references

- a companion experiment-report-spec proposal under `proposals/` — the full
  14-section spine, per-section ingredients, definition-of-done checklist
  (authored on demand).
- `.claude/skills/sim-audit/SKILL.md` — produces the Verification-suite,
  conformance-matrix, and uncertainty artifacts this rule mandates.
- `.claude/rules/figure-operating-conditions.md` — the figure caption +
  numeric operating-conditions disclosure conventions (model, decoding
  params, few-shot $k$, seeds/CIs) this rule builds on.
- `.claude/rules/citation-integrity.md` — external-value provenance the
  Section-2 anchors and Section-13 statement must satisfy.
- `.claude/skills/reference-implementation-study/phases/phase-1b-derivation-gate.md` —
  the Phase-1.5 **G0 derivation-soundness gate** (`[opt:RIS-DERIV]`, default on).
  Its per-candidate derivation ledger (independent re-derivation, limit checks,
  assumptions) pre-populates the Section-4 **equation↔function table left column**:
  G0 attests the *equation* is sound before Phase 2; the Section-4 table then attests
  the *code* matches it. The two gates are complementary, not redundant.
- Worked instance: a reproduction/eval study's Phase-6 report.
