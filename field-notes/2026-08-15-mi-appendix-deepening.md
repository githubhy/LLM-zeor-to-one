# Field notes — 2026-08-15 — deepening the mechanistic-interpretability appendices

## Context

Closing `todos/2026-08-15-mi-survey-remaining-appendices.md`: appendices A/B/C/E deepened from the
audited derivation material, four body updates from the 2026 frontier sweep, and the owed
`[opt:MATH-REDERIVE]` pass on Appendix D. Five independent re-derivations were run (D, then A, B, C,
E), all on Opus, each deriving from first principles **before** opening its target.

## What the re-derivation pass actually bought

This is the first session where `[opt:MATH-REDERIVE]` ran at scale here, so the yield is worth
recording precisely. Across five appendices the reviewers returned **12 ERROR, 15 UNSTATED
HYPOTHESIS, 13 OVERSTATEMENT**. Every displayed equation in A, D and E was correct as printed.

**That distribution is the finding.** The rule's own justification — "oracles test values;
re-derivation tests reasoning" — predicted it, and the data matched: almost nothing was wrong with
the *algebra*, and a great deal was wrong with the **prose claims wrapped around correct algebra**.
A value-checking oracle would have passed all five appendices.

Three were consequential enough to have shipped a wrong conclusion:

- **§C.7 was inverted.** I wrote that the NIE-sum-vs-NIE-all comparison is "uninformative about
  synergy" because the additive and multiplicative nulls "bracket the measurement from opposite
  sides". The bracketing claim is true for **one of five** models. And because $1+e \le e^{e}$
  makes $\exp(\sum e_i) - 1$ a strict *upper bound* on any independent-multiplicative model, four of
  five measurements **exceed** it — which refutes independence and establishes synergy. The section
  now argues the opposite of what I first wrote, and the source's claim comes out **better** supported
  than the comparison it rests on. My lead example, distil, is the one model where synergy is *not*
  demonstrated.
- **§B.8's thesis was false of the sections it named.** I claimed the capacity theorems are
  metric-relative. They are not: for PD $M = R^{\top}R$, the map $u \mapsto Ru$ carries $M$-cosines
  to Euclidean cosines with zero distortion, so packing and recovery counts are metric-**invariant**
  (verified to $10^{-15}$). The critique is real but belongs on the *measured* quantities — feature
  dimensionality, interference on trained directions — not on the existence bounds. Section rewritten
  to split per-result instead of asserting blanket relativity.
- **§B.7's linear-model contrast was $3\times$ too large**, from evaluating at $x = 1$ instead of
  integrating over $[0,1]$, and it silently dropped the bias. Correcting it also killed the argument I
  had built on it: with $b_j < 0$ the *linear* model also prefers positive interference, so
  "charges both signs" is a $b_j = 0$ special case. The durable distinction survived in better shape —
  the ReLU cost is exactly zero on a half-line, the linear cost bottoms out at $b_j^2/4 > 0$. **A free
  region, not an asymmetry.**

Two more were basis errors of exactly the kind `[opt:MATH-BASIS]` exists for: a gradient ratio quoted
in the softmax's input basis but attributed to the query/key parameters (off by $\sqrt{d_k} = 8$), and
a symbol collision where $m$ meant "bottleneck width" and "feature count" one line apart, inside the
paragraph whose conclusion inverts with the ratio's orientation.

## Issues found and resolved inline

- **MEMIT's batched update was non-conformable and live on `main`.** Found while deriving the
  scale-invariance result, not by looking for it. Filed as `bugs/2026-08-15-02` because the root cause
  generalizes: it was the one result in the appendix stated *without* a derivation, so no next line
  could fail to follow from it. No-todo because fixed in the same turn.
- **The figure SVGs were not byte-reproducible** — re-running two untouched generators produced
  363-line diffs. Not nondeterministic computation (coordinates bit-identical); a wall-clock
  `<dc:date>` plus matplotlib's per-process id salt. `bugs/2026-08-15-03`. The gap is between
  *deterministic computation*, which the diagram rule requires and which held, and *reproducible
  artifact*, which it does not mention.
- **A load-bearing reference was weak-form.** Appendix A's entire framing traces to a
  Transformer Circuits Thread article tagged `(web)`, which `citation-integrity` forbids under a
  load-bearing claim. Acquired via a new `download/web-native/` convention
  (`decisions/2026-08-15-01`). Reading the primary then confirmed the audit's separate point: a
  downstream re-statement prints a non-conformable attention formula from a row/column layout mix-up —
  the error I would have inherited by citing the echo.
- **The 77%-vs-9% denominator.** The SAE geometric audit's abstract attributes 77% to features
  "passing a standard recovery bar"; its own §6.3 records that **one** of those seventeen cleared the
  bar. Verified against the PDF before writing. The survey leads with 9%.

## Patterns / lessons

**Agent findings are input, not verdict — in both directions.** Yesterday's `bugs/2026-08-15-01` was a
critic confidently reporting failures that had not occurred. Today four reviewers reported failures
that *had*. The discipline that separated them was the same in both cases: re-verify against the
artifact before acting. I recomputed every numeric finding and re-read the two source PDFs; each time
the finding held, and each time that took under a minute. The cost of checking is far below the cost of
either error.

**"State the basis" is not a style rule.** Three of the twelve errors were one quantity quoted on
another quantity's basis. All three were invisible to inspection and obvious to arithmetic.

**An appendix result with no derivation attached is unprotected.** Both the MEMIT conformability bug
and the §B.7 factor-of-3 sat in sentences that *stated* a result rather than deriving one. Where a
derivation runs, the next line fails to follow and the error surfaces; where it does not, nothing
catches it. That is an argument for deriving even the steps that feel like transcription.

## Refs

- `bugs/2026-08-15-01` (yesterday's inverse case), `bugs/2026-08-15-02`, `bugs/2026-08-15-03`.
- `decisions/2026-08-15-01-web-native-primary-sources.md`.
- `surveys/mechanistic-interpretability/_scratch/review-appendix-{a,b,c,d,e}.md` — the preserved
  re-derivations, per `[opt:MATH-REDERIVE]`.
- `todos/2026-08-15-web-native-source-upgrades.md`.
