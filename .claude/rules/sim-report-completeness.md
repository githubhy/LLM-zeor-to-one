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

## Two emphases this rule front-stops

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
- Worked instance: a reproduction/eval study's Phase-6 report.
