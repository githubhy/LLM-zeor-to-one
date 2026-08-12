# Calibration-Residual Attribution Rule

Loaded on demand by `CLAUDE.md`. Read this file before attributing **any
residual between two numbers that ought to agree** to a cause, and before any
report, survey, or sign-off gate states such an attribution as fact.

The canonical case is a **reproduction versus an external published reference** —
any number you did not generate: a paper's headline benchmark score, a model
card's reported accuracy, a leaderboard entry, a digitized curve from a published
figure, or an independent implementation of the same method.

**But the reference does not have to be external, and the rule does not weaken
when it isn't.** The discipline applies verbatim to any residual between two
things that should agree, including both sides being yours:

- a **port versus its source** (`.claude/rules/cross-language-port.md` §3 already
  invokes this rule for exactly that, triaging into `{port bug | cross-language
  convention/boundary | reference gap}`);
- one **method versus another** on the same input — e.g. a fused kernel against a
  reference implementation, or a fast approximate retriever against exact search;
- an **experiment against its own earlier self**, or against a closed-form
  prediction it is supposed to reproduce (a scaling-law fit, a `pass@k`-vs-`k`
  curve, an attention FLOP count).

The reason is that checks 4 and 5 — *reconcile the metric basis* and *triage into
four buckets* — are about **two computations disagreeing**, not about where the
numbers came from. An internal residual is if anything *more* seductive, because
"both sides are mine, so a convention mismatch is impossible" is a comfortable and
false thought.

**Domain-agnostic.** These failure modes were measured upstream across five
unrelated domains before this rule was written. Nothing here is specific to any
one of them; the LLM instances below are the shapes they take here.

## The rule

**A residual is root-caused only when you can state, numerically, how much of
the gap the proposed cause closes *at the representative operating point* — and
name what is left.** Anything less is a *lead*, not a root cause, and must be
written as one.

This is the one reusable check behind every instance below. A mechanism that is
*directionally* right is not a weaker version of correct — it is **more**
dangerous, because it reads as confirmation on a casual pass.

## The six checks

**1 — Quantify the closure, at the representative operating point.**
"X explains the residual" requires: the gap before X, the gap after X, and the
operating point at which both were evaluated. The operating point must be the
one the reference actually uses, not the one that flatters X. *(A sweep whose
maximal setting still falls short of the reference does not "bracket" it.)*

**2 — A cause measured in one configuration is not established for the others.**
Re-running a candidate cause at one model size, one benchmark, or one few-shot
$k$ and asserting it for the rest is the single highest-severity error in this
class. If the attribution is claimed for N configurations, it is measured in N
configurations or it is scoped, in the prose, to the ones it was measured in.

**3 — An independent implementation is not an oracle.**
A cross-check **excludes** hypotheses and **localizes** leads. It does not
**prove** an attribution. Two implementations can straddle the reference in
opposite order across benchmarks — so "ours agrees with theirs" is evidence about
*them*, not about the reference.

**4 — Reconcile the metric BASIS on both sides before believing agreement *or*
disagreement.**
A lower score can be an answer-extraction difference, not a capability gap.
Before comparing, state on both sides: what quantity is averaged, over what
population, with what normalization, in what units/convention. In LLM work the
recurring axes are few-shot $k$ and exemplar pool, prompt template, `pass@1` vs
`pass@k`, bits vs nats, non-embedding vs total parameters, unique vs seen tokens,
and the harness's answer-extraction rule. A disagreement that dissolves under
basis reconciliation was never a model finding. When the bases differ, say which
one the *reference* is on — that is what arbitrates.

**5 — Triage every residual into one of four buckets, explicitly.**
`{ harness/code bug | convention or metric-basis mismatch | model-scope gap (a
population or effect the experiment omits) | genuine model error }`. The default
assumption must not be the last one.

**6 — A number that reproduces is not an attribution that holds. Split the
population, and check the rig's preconditions, before believing a rate or a
trend.** `[opt:CR-SPLIT · default ON · toggle .claude/skill-options.json]`

Reproducibility feels like verification and is not: a wrong *story* about a
number reproduces exactly as reliably as a right one. Before stating what a
measured quantity *means*, run these three:

- **Split the population.** An aggregate rate mixes sub-populations. Decompose it
  and check the effect survives in the part you are attributing it to. A benchmark
  accuracy delta that is really concentrated in one subject split, or a `pass@k`
  gain that lives entirely in the problems the baseline already solved at $k=1$,
  is a different finding from the one the aggregate suggests.
- **Check the rig's preconditions — especially on the "easy" case.** Choosing a
  degenerate-free control is right; skipping *its* preconditions because it is
  the simple one is how a null rig gets read as a finding. An eval that silently
  scored an empty completion, a prompt template that truncated the question, or a
  retriever returning zero documents will produce a clean, reproducible,
  meaningless number. The tell is usually in the first output and read past — a
  degenerate distribution (all-zero scores, a 50% exact-match on a binary task)
  is an **absent signal**, not a weak effect.
- **Establish the noise floor before believing a trend or a sweep.** One seed at
  three settings *looks* like a controlled sweep and is three anecdotes.
  Decoding-temperature and few-shot-order effects are large enough to invert a
  single-seed trend.

**Corollary — significance is not materiality.** With a large enough eval set
almost any statistic reaches significance, so an absolute threshold on a
statistic is the wrong instrument. Compare the **decision-relevant effect against
a matched noise floor** — the same statistic under resampling that changes nothing
real (a different seed, a shuffled few-shot order, a re-run of the same
configuration).

## Forbidden phrasings, and their honest forms

| Do not write | Write instead |
|---|---|
| "brackets the reference" | "closes X of the Y gap at the representative point; Z remains" |
| "agrees with" / "matches" / "close to" | the signed delta, the percentage, and the CI |
| "qualitative match" | a numeric gate, or "not yet gated — lead only" |
| "confirmed" (for a positive attribution) | "partial root-cause — dominant driver is X; residual UNCLOSED" |
| "X under-performs Y" | "the X-vs-Y gap is partly a metric-basis difference; the reference is on the ... basis" |
| a flattering rounded delta | the committed artifact's number, to its committed precision |
| "the number reproduces, so the finding holds" | the number reproduced; state which sub-population it survives in, and what the rig's preconditions were |
| "statistically significant (p<...)" as a verdict | the effect size against a matched noise floor — significance without materiality is not a finding |

The right-hand column is not pedantry: every left-hand phrasing above was actually
drafted upstream, and each was caught only by an adversarial pass — never by a
careful re-read.

## Two operational traps

- **Seed the library, not the framework.** For any third-party stack
  (torch/transformers/vLLM or an eval harness), find its *own* RNG and sampling
  seed. A framework-level seed may not control the dataloader, the sampler, or
  the harness's few-shot shuffling, and same-seed runs that silently differ will
  be read as model variance. Prove repeats are identical *before* trusting any
  number — and note that attention and reduction kernels are not bit-reproducible
  by default, so "identical" may legitimately mean "within kernel tolerance",
  which you then state.
- **Cite the config value to the source, not by inheritance.** A parameter you
  "know" the reference used — its few-shot $k$, its temperature, its harness
  version — is an unverified memory citation
  (`.claude/rules/citation-integrity.md`). Find the line in the paper, model card,
  or harness config.

## Failure shapes this rule is earned from

These were measured upstream in other domains; the mechanism is what transfers,
and the middle column is the shape it takes in LLM work.

| Check | Upstream failure | The LLM shape of the same error |
|---|---|---|
| 1, 2 | A gap attributed to a release delta, generalized from a **single** re-run and provably false for the sibling configuration. | A regression attributed to a quantization scheme after testing one model size, then asserted for the family. |
| 4 | A "+5.33 dB" margin computed against the **requirement** rather than the **reference performance** — ~3.8 dB of the claimed headroom was a margin stack, not headroom. | A "+N point" gain computed against a **vendor-published** score rather than the same harness — most of it prompt template and answer extraction, not capability. |
| 5 | A calibration residual that turned out to be a **code bug** (a tail mass-loss in a convolution), not a model gap. | A benchmark gap that is a truncated prompt, a wrong stop sequence, or a scorer that marks a correct-but-differently-formatted answer wrong. |
| 6 | "92.75% of messages are erased" survived a population split as **96.54% / 0.00%** — the erasure was structural, and the real effect was ~20%, at a different stage, from a different mechanism. | "The method fixes 90% of failures" that, split by subject or by baseline-difficulty, turns out to fix the ones already passing and none of the hard ones. |
| 6 | A **control** rig running on an identically null input for 28% of seeds; its noise-only output was written up as a property of the system and retracted. | A control arm whose retriever returned zero documents, or whose few-shot block was silently dropped by a truncating template. |
| 6 | A single-seed "the trend goes backwards" that was cleanly monotone across five seeds. | A temperature or few-shot-$k$ sweep run at one seed, inverted by ordering noise. |

## What this rule is not

It is **not** a calibration workflow, and it does not tell you how to *build* a
reproduction. It governs only the moment of attribution. The surrounding
machinery already exists:

- `.claude/rules/sim-report-completeness.md` — the **reporting** side:
  protocol-vs-eval conformance matrix, theory-as-predictor overlays, CI on every
  result, "protocol-faithful is graded, not binary". This rule supplies the
  honesty standard for the *discrepancy budget* those artifacts carry, and its
  `[opt:SIM-BASELINE]` / `[opt:SIM-REQBASIS]` clauses are check 4 and check 6
  applied at publication time.
- `.claude/skills/sim-audit/SKILL.md` — the **numerical-correctness** side
  (check 5's "harness/code bug" bucket is what a sim-audit closes).
- `.claude/rules/citation-integrity.md` — the reference value itself must be
  traceable to an acquired source, never written from memory.
- `.claude/skills/results-reconciliation/SKILL.md` — catches the *stale* residual
  framing ("X remains open") after a later pass closes it.
- `viewer/tools/check-basis-declarations.py` — the mechanical gate for check 4 at
  *authoring* time (`[opt:MATH-BASIS]`); this rule owns the moment of
  *attribution*.
