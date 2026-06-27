---
name: sim-audit
description: Verify an experiment's correctness through an untrusting, multi-lens audit — independent re-derivation, property/invariant tests, statistical validity (seeds / CIs / contamination), published-baseline anchors, edge-case robustness, and determinism/software-quality. Use after a reference-implementation-study reproduction/eval experiment is drafted or substantially changed (especially after a shared-API rewrite or subagent-authored kernels), and before any Phase-6 / sign-off gate. Runs standalone on any experiment, not only pipeline output.
---

# Experiment / Eval Audit

## Overview

Establish that a reproduction/evaluation experiment is *correct* — that its
harness and metric kernels compute the quantities they claim, that the
chosen metric is the right one for the task, and that no headline number is
a confidently-wrong artifact. This is the experiment-correctness analogue of
`citation-audit` (which audits external citations) and a companion to
single-method evaluation (which scores one candidate method): `sim-audit`
audits the whole running evaluation harness.

The discipline is **untrusting**. The highest-leverage lenses do *not*
read the experiment's source — they re-derive the answer by an independent
route and diff. A bug that lives in both the derivation and the code
survives self-review; only an independent path catches it.

This skill is the after-the-fact verification; the prevention disciplines
are `.claude/rules/math-authoring.md` (correct derivations),
`.claude/rules/citation-integrity.md` (sourced constants and hyper-parameters),
and the property tests authored alongside the code.

## When to use

- After a reference-implementation-study Phase 2/3 experiment is drafted,
  before the G2 baseline is believed.
- After any **shared-API rewrite** (e.g. a `utils` rewrite) — dependent eval
  drivers drift silently; importability gates miss runtime breakage.
- Whenever a numeric kernel (a metric, scorer, decoder, or log-prob
  aggregator) was subagent-authored or copied from memory.
- Before any delivery, sign-off, or plan-acceptance gate on an experiment study.
- Standalone, when the user asks to audit / verify a named eval harness.

## Output

Two artifacts:

1. **Per-lens verdict table** — one row per lens: `lens | ran? | verdict
   (CLEAN / DEFECT) | evidence`. A DEFECT blocks sign-off.
2. **Defect register** — every defect filed as a `bugs/YYYY-MM-DD-NN-*.md`
   record (per `CLAUDE.md` Bug Capture), with severity, root cause (not
   surface symptom), the metric / correctness impact on prior results, and the
   regression test added. Reporting reports cross-link these IDs.

A CLEAN audit is a positive result, not a non-event: state which numbers
each lens *protects* and which rest on a single unverified path.

## Workflow

Run the seven lenses below. They are independent — **parallelise with the
Workflow tool** (one agent per lens; verify each finding adversarially
before filing it). Scale depth to stakes: a quick check runs lenses 2/4/6;
a sign-off audit runs all seven with adversarial verification.

### Lens 1 — Independent re-derivation (untrusting; highest leverage)

Re-implement each load-bearing numeric kernel **from the benchmark's
published scoring rule / first principles, without reading the harness**,
into throwaway scratch (`/tmp/audit-ref/`), and diff against the harness's
output on fixed examples. Target machine precision for deterministic kernels.

- Dispatch the re-derivation to an agent that is given the *metric
  definition / scoring protocol*, not the harness source, so the two paths
  are genuinely independent.
- Kernels worth re-deriving: metric/scorer formulas (the `pass@k` unbiased
  estimator, exact-match / F1 normalisation, perplexity from token
  log-probs), prompt-template and few-shot assembly, dataset-split
  selection, log-prob aggregation, answer extraction / parsing.
- A diff that matches to ~1e-12 is strong evidence; a mismatch is a defect
  *or* a benign equivalence (e.g. a whitespace / tokenization-normalisation
  difference) — decide which with a decisive check before filing.

### Lens 2 — Property / invariant suite

Author durable tests under `tests/<topic>/` asserting the invariants the
math guarantees, independent of any reference value:

- structural: a softmax row sums to 1 and is non-negative; a per-example
  score lies in `[0, 1]`; `pass@k` is non-decreasing in `k`.
- identity: the metric's batch aggregation equals its per-example mean;
  greedy decoding equals argmax sampling at temperature 0; `pass@1` equals
  mean per-example correctness.
- combinatorial: the prompt / few-shot shuffler is a bijection over the
  example pool; the `n` sampled completions are distinct draws covering the
  requested count.
- monotonic: accuracy monotone in few-shot `k` on a learnable task (a
  sanity check, not a law); `pass@k` monotone non-decreasing in `k`;
  perplexity bounded below by 1.

These lock the audit's findings as regressions (G1 grows with the suite).

### Lens 3 — Statistical validity

Quantify every headline number's uncertainty and confirm seeds are
independent:

- bootstrap the headline operating point (re-pool the metric over a
  seed / example resample, B ≥ 2000) → a CI, persisted via a committed
  driver so it regenerates from code (not a one-off run).
- **rate metrics (accuracy, `pass@k`, exact-match) use a binomial CI
  (Wilson / Clopper–Pearson), not Wald** — Wald under-covers near `p=0` or
  `p=1`. Continuous metrics (perplexity, win-rate, BLEU) use a bootstrap or
  a t-CI across ≥5 seeds.
- state the sampling budget (number of completions `n`, number of examples,
  number of seeds, temperature / top-p) and the stopping rule; flag any
  point whose CI straddles a pass/fail threshold as INCONCLUSIVE, not PASS.
- **contamination check**: confirm the eval set is not present in the
  model's training data, or disclose the overlap — a headline score on a
  contaminated split is a confidently-wrong artifact. Check for verbatim
  n-gram overlap, canary strings, or known-leaked benchmarks before
  believing the number.
- watch the cost: a full bootstrap over many tasks × decoding configs can
  be ~1 h — bootstrap the configs that *moved*, reuse audited CIs for the
  rest, and commit the *driver* as the reproducibility unit.

### Lens 4 — Closed-form / external anchor

Pin the experiment to independently-known values:

- degenerate limits (e.g. temperature → 0 collapses sampling to greedy /
  argmax decoding; few-shot `k = 0` recovers the zero-shot number; a known
  metric identity).
- a **published-baseline** reference for the no-change point: the model
  card's or paper's own reported MMLU / GSM8K / HumanEval / MT-Bench score
  for the *same* model and protocol.
- an oracle upper bound the realizable system must sit below
  (`pass@∞ ≥ pass@k`; a human-ceiling accuracy; an oracle-retrieval RAG
  bound).
- **theory-as-predictor**: where a closed form predicts the *result curve*
  (e.g. a scaling law predicting loss vs compute / tokens, or a
  `pass@k`-vs-`k` curve derived from the per-example success rate), overlay
  it on the experiment and root-cause the residual (harness bug /
  asymptotic-only / unmodeled effect). A shortfall *against* a correct
  prediction localizes the unmodeled effect.

### Lens 5 — Protocol / published-benchmark cross-validation

Confirm no experiment parameter violates the governing benchmark protocol
or its reference implementation. Acquire the benchmark paper / model card /
official harness (`source-fetch`); check the agreed eval assumptions clause
by clause (prompt template, n-shot count, scoring / normalisation, answer
extraction, stop sequences, max new tokens). Where the literature records a
cross-paper spread or leaves a detail unspecified, a single clean run
landing inside that spread is the expected behaviour, not a defect. Build
the **Protocol-vs-Eval conformance matrix** (per `.claude/rules/sim-report-completeness.md`).

### Lens 6 — Edge-case / robustness

Drive every degenerate config and assert finiteness + the numerical-safety
floors: temperature → 0 and very large; top-p `= 0` and `= 1`;
`max_new_tokens = 0`; empty prompt / empty completion; `n = 1`; a
single-example eval set; an all-correct and an all-wrong split (the
binomial-CI boundary pathology at `p=0` / `p=1`). A log-prob sum over an
empty sequence must stay finite; a perplexity on a zero-length completion
must be guarded; a softmax over a fully-masked row must not produce NaN.
Each floor gets a test.

### Lens 7 — Golden-master / determinism / software quality

- **determinism**: same seed + same env (greedy decode, or a fixed sampling
  seed) → bit-identical outputs (`test_*_determinism`); document any
  tolerance if a non-deterministic kernel (GPU non-associativity, a remote
  API) is in the loop.
- **golden-master**: freeze a known-good output (a small fixed eval slice's
  scores); a regression test diffs against it.
- **driver-drift smoke**: every dependent eval script gets a *run*-smoke, not
  just an import — importability gates pass while a driver crashes at
  runtime on a removed helper (the canonical post-rewrite defect). A
  surviving-but-unread parameter (a decoding flag that silently no-ops) is
  worse than a removed one.
- **reproducibility hygiene**: seeds, decoding config, and model
  revision / commit stored in every output JSON / JSONL; figures regenerate
  from persisted data; empty-input guards.

## Lessons (encode these)

- **Importability ≠ runs.** `G1` dotted-imports modules; a driver whose
  removed-function references live *inside* functions imports cleanly and
  crashes on first call. Add a run-smoke per dependent driver.
- **The untrusting lenses catch what code-reading misses.** Re-derivation
  and anchors find off-by-one / normalisation / convention bugs (a tokenizer
  mismatch, a 0-vs-1-indexed few-shot slice, a label permutation) that a
  careful read of the (wrong) code rationalises away.
- **A clean re-derivation is informative**: it means the earlier
  code-reading + absolute-signature checks already flushed the real bugs.

## Cross-references

- `.claude/skills/reference-implementation-study/` — Phase 6 invokes this
  audit before sign-off; the defect register feeds the report's Audit-Trail
  section.
- `.claude/rules/sim-report-completeness.md` — the report must carry the
  Verification-suite, conformance-matrix, and uncertainty artifacts this
  audit produces.
- `.claude/skills/citation-audit/SKILL.md` — sibling audit for citations.
- Single-method evaluation (scoring one candidate method) is the
  complementary lens; this audits the whole eval harness.
- Worked instance: a reproduction/eval study's audit — its field-notes and
  bug records are cross-linked from that study's report.
