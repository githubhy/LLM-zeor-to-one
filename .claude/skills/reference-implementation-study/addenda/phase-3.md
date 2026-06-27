# Proposed-mode addendum — Phase 3 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set (`P0-2`, `P0-4`, `P1-4`).

**[P0-2] Pairwise statistical comparison (paired-seed significance).** Run all candidates on
the SAME seed set (a paired design over the same eval items / sampling seeds), not independent
seeds per candidate. Beyond the existing per-candidate {mean, std, 95% CI}, compute, for each
candidate pair and each metric, a paired significance test (paired t-test, or Wilcoxon signed-rank
for non-normal metrics) plus an effect size, and emit a pairwise comparison matrix in
`summary.json`. Rationale: overlapping per-candidate confidence intervals are **not** a
significance test — a paired test can find a real difference the marginal CIs hide, and vice versa
(the Henderson / Bouthillier variance-accounting lesson). With flag `P0-2`, `validate_gate.py G2
--flags P0-2` checks the pairwise matrix is present, uses a shared seed set, and reports test +
effect size per pair.

**[P0-4] Confidence-driven Monte-Carlo for rate metrics.** The baseline runs a FIXED number of
seeds (default 5) and reports a Gaussian `scipy.stats.t` interval. For any metric that is a
Bernoulli *proportion* — accuracy, pass@k, exact-match rate, win-rate, error rate, refusal rate,
hallucination rate — this is the wrong tool at low rates: a fixed seed budget collects zero or a
handful of the rare events (an unusable point estimate), and the normal / `t` approximation
under-covers near 0 or 1 (its lower bound can even go negative). For rate metrics, augment the
protocol:

1. **Event stopping rule.** Run each `(candidate, operating-point)` until at least a target number
   of the counted *events* is accumulated across the eval ensemble (default ~100 successes/failures,
   e.g. passing or failing items), OR a `max_trials` cap is reached. Record `error_count`,
   `total_trials`, and `stop_reason` ∈ {`target_errors`, `max_trials`}.
2. **Binomial proportion CI.** Report a **Wilson score** or **Clopper–Pearson** interval (set
   `ci_method`), never the Gaussian `t`-interval, for the rate. The point estimate is
   `error_count / total_trials`.

Non-rate metrics (e.g. perplexity, tokens-to-converge, latency, mean reward) keep the existing
mean/std/`t`-CI path unchanged. With flag `P0-4`, `validate_gate.py G2 --flags P0-4` checks each
rate-metric entry carries `error_count`, `total_trials`, `stop_reason`, and a binomial `ci_method`.
(Sequential Monte-Carlo stopping-rule reviews; Wilson / Clopper–Pearson binomial intervals;
bootstrap CIs for benchmark proportions.)

**[P1-4] Measured complexity & runtime profiling protocol.** When any cost / latency / throughput /
complexity metric is in scope (Phase 1), measure it rigorously instead of asserting it:

1. **Distribution, not a single mean.** Warm up (discard cold-start / JIT / autotune runs), then
   take at least `repeats` timed runs and report the distribution — median plus a robust spread
   (IQR) or percentiles. Wall-clock is noisy and right-skewed; a single cold run can mis-rank
   candidates.
2. **Hardware-independent operation count.** Alongside wall-clock, report an op count that survives
   a platform change — FLOPs per token, attention ops × sequence length, multiplies/token, or
   forward passes.
3. **Asymptotic-scaling cross-check.** State the claimed complexity (e.g. O(n) in sequence length)
   and check it against measured runtime on at least 2 problem sizes; flag a mismatch (a
   claimed-linear-attention O(n) routine that measures O(n²)).

Pin the timing environment (CPU/GPU, thread count, batch size, load — ties to P1-3) and persist the
raw per-repeat timings as an artifact. With flag `P1-4`, `validate_gate.py G2 --flags P1-4` checks
the cost summary carries `repeats`, percentiles, an `op_count`, an `asymptotic_claim`, and a
`measured_scaling` record. (Steady-state / warmup microbenchmarking rigor; report-the-distribution
practice.)
