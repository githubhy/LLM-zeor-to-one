# Figure Operating-Conditions Disclosure Rule

Loaded on demand by `CLAUDE.md`. Read this file before generating,
captioning, or auditing any figure that reports LLM/method behavior
under specified operating conditions (model, decoding params, few-shot
$k$, benchmark/split, eval harness, metric/CI, seed, etc.). This is the
concrete home for the "numeric operating-conditions disclosure"
conventions that `.claude/rules/sim-report-completeness.md` builds on.

## The rule

**Every figure must explicitly disclose its operating conditions in
§ 1 (Purpose) of its 4-section caption.** At minimum, the disclosure
includes:

| Parameter | Required for | Form |
|---|---|---|
| Model + size | every method figure | `Llama-3.1-8B`, `Mistral-7B-v0.3`, `Qwen2.5-72B-Instruct`, `GPT-4o (2024-08-06)` |
| Method / variant | every method figure | `FlashAttention-2`, `GQA (8 KV heads)`, `speculative decoding (draft=1B)`, `int4 GPTQ`, `nucleus top-p=0.9` |
| Precision / dtype | every figure | `bf16`, `fp16`, `int8 (LLM.int8())`, `int4 (GPTQ / AWQ, group=128)` |
| Context length | every context / throughput figure | `seq_len = 4096`, `ctx = 32768 (RoPE θ=1e6)` |
| Decoding params | every generation figure | `temperature = 0.0 (greedy)`, `temp = 0.8, top-p = 0.95, top-k = 50, max_new_tokens = 512` |
| Few-shot $k$ + exemplar source | every prompted-eval figure | `5-shot (MMLU dev)`, `0-shot CoT`, `8-shot (GSM8K)` |
| Sampling $n$ (for pass@k) | every pass@k / best-of-$n$ figure | `n = 200 samples; pass@{1,10,100}` |
| Benchmark + split | every scored figure | `MMLU (test)`, `GSM8K (test, 1319)`, `HumanEval (164)`, `MT-Bench (80 prompts)` |
| Eval harness + version | every scored figure | `lm-eval-harness v0.4.x`, `EvalPlus`, `custom (commit <sha>)`; scoring = exact-match / pass@k / LLM-judge (disclose judge model + version) |
| Metric + uncertainty | every scored figure | `acc ± Wilson 95%`, `pass@k (unbiased estimator)`, `win-rate ± bootstrap 95% (10k resamples)` |
| Seed (or seed range) | dashboards (single seed); envelopes ($N$ seeds) | `seed = 0` or `seeds 0..4 (N=5)` |
| Batch / hardware (throughput figures) | every latency / throughput figure | `batch = 1`, `batch = 32, vLLM 0.6.x, 1×A100-80GB` |
| pass@k convention | every code-gen / best-of-$n$ figure | `pass@1 (single sample)` vs `pass@k (k samples, any-correct)`. pass@k is systematically **higher** than pass@1 because one success among $k$ attempts is forgiven. Disclose which the figure reports. (empirically: a high-variance sampler looks far better at pass@100 than pass@1.) |

## How to disclose

Two patterns, depending on caption length:

**Inline (short captions)**: list parameters in parentheses immediately
after the figure subject:

```markdown
### F-S3-M1 · Head-to-head decoding-method ranking
(4 decoders × 3 models × 2 benchmarks; Llama-3.1-8B / Mistral-7B / Qwen2.5-7B;
bf16; ctx = 4096; 0-shot CoT; HumanEval pass@{1,10}, n = 50;
lm-eval-harness v0.4.x; seeds 0..4)
```

**Tabular (long captions)**: a "Configuration" sub-block in § 1:

```markdown
### F-S3-M1 · Head-to-head decoding-method ranking

**Configuration.**

| Parameter | Value |
|---|---|
| Models | Llama-3.1-8B, Mistral-7B-v0.3, Qwen2.5-7B-Instruct |
| Methods | greedy, top-p=0.95, top-k=50, min-p=0.05 |
| Precision | bf16 |
| Context length | 4096 |
| Few-shot | 0-shot CoT |
| Benchmark | HumanEval (164) |
| Sampling | n = 50; pass@{1,10} (unbiased estimator) |
| Eval harness | EvalPlus (commit <sha>) |
| Metric | pass@k ± bootstrap 95% |
| Seeds | 0..4 (N=5) |
| ...
```

Use inline for ≤ 8 parameters; tabular for > 8 or when parameters
have non-trivial sub-structure (e.g., per-model decoding rows).

## "Production default" is not enough

Saying *"temperature = 0.0 (study default)"* satisfies the rule.
Saying *"temperature at study default"* does **not**. The numeric
value must appear in the disclosure.

**Why.** A future reader auditing across model versions / harness
versions / forks needs to verify that "study default" still meant 0.0
at the time the figure was rendered. The numeric value is the
audit-resolvable artifact; the label is documentation. Both are
required.

This is exactly the failure class a hardcoded-parameter figure invites:
if a sampling count such as `n = 200` is hardcoded inside
`figures/_humaneval.py::score_passk` but captions of a pass@k sweep
(planned but not yet rendered) would have inherited the wrong $n$ with
no caption-level clue that anything was off. Caption-level numeric
disclosure of $n$ would flag the discrepancy before any figure is
rendered.

## What to do when a parameter is *not* applicable

If a figure doesn't exercise a parameter (e.g., a greedy-decoding figure
has no top-p; a perplexity figure has no pass@k $n$; envelopes-only
figures don't have a single seed), say so explicitly:

```markdown
| Decoding params | n/a (greedy, temperature = 0.0) |
| pass@k convention | n/a (exact-match accuracy figure) |
| Seed | n/a (envelope across seeds 0..4) |
```

Don't omit the row. Explicit "n/a" beats silent absence — the next
auditor needs to see that the parameter was *considered* and ruled
inapplicable.

## What to do for parameter sweeps

When a figure is a sweep over a parameter (temperature sweep, few-shot
$k$ sweep, context-length sweep, quantization-bit sweep), disclose the
sweep range *and* the held-fixed parameters:

```markdown
**Configuration.** Temperature-sweep figure.
| Parameter | Value |
|---|---|
| Temperature (swept) | {0.0, 0.2, 0.5, 0.8, 1.0} |
| Model | Llama-3.1-8B (bf16) |
| top-p | 0.95 (fixed) |
| Few-shot | 8-shot (GSM8K) |
| Benchmark | GSM8K (test, 1319) |
| Sampling | n = 40; pass@1 |
| Eval | lm-eval-harness v0.4.x; exact-match ± Wilson 95% |
| ...
```

The reader should be able to identify both the variable and the
controls without leaving the figure.

## Verification

`grep` discipline: searching the caption for any of the disclosed
parameter values should find the caption *before* it finds the
kernel code. Concretely:

```bash
# Should find the caption (not the source) for a temperature=0.0 figure:
grep -rn "temperature = 0.0\|temperature=0.0\|temp=0.0" reports/figure-review-guide-*.md
# Should NOT be the only place the value lives:
grep -rn "temperature.*=.*0\.0" sim/*/figures/
```

A figure whose decoding value is only in the source code (not in the
caption) violates this rule.

## Cross-references

- `.claude/rules/sim-report-completeness.md` — the reproduction/eval
  report completeness rule that builds on these disclosure conventions
  (model, decoding params, few-shot $k$, seeds/CIs); Section 3's
  decoding-config-convention block and Section 6's per-cell CI mandate
  are the report-level counterpart of this figure-level rule.
- `.claude/rules/citation-integrity.md` — external-value provenance any
  benchmark number cited in a caption must satisfy (read from the model
  card / paper, never recalled from memory).
- the 4-section caption schema this rule strengthens (§ 1 Purpose now
  requires parameter disclosure) — authored on demand under `proposals/`.
- `bugs/` / `field-notes/` — the hardcoded-parameter and
  undisclosed-operating-conditions audit patterns land here with dated
  IDs once a figure pipeline exists.
