# Max-Mode Expansion of `surveys/llms-for-coding` — Phase-5 Report

**Date:** 2026-08-14 · **Commit:** `1b87bb3` (baseline `1d8f017`) · **Skill:** `deep-research-survey`

---

## 0. Executive summary

The invocation named a survey that already existed. The decision that shaped everything else
was made by measuring it rather than by reading its table of contents: **the body carried
~11,900 words across sixteen sections and zero equations**, while appendices A–I ran to 379 KB
of derivation about the *general* transformer. A survey whose own rules require
"a rigorous first-principles mathematical derivation for every method included" had none in
its body, and the section its title advertises — agentic software engineering — was its
thinnest at 795 words with 2024-era frontier evidence, in a run dated 2026-08-14.

This pass added the missing mathematics as a dedicated appendix, rebuilt the two headline
sections most damaged by staleness, corrected a high-severity citation error in pre-existing
content, and — the part worth arguing about — **declined to report two categories of number
that the evidence did not support**.

| Deliverable | Before | After |
|---|---|---|
| Appendix J — code-specific derivations | — | **4,297 words, 19 equations** |
| §12 Agentic coding systems | 795 words | **3,131 words** |
| §13 Evaluation and benchmarks | 1,018 words | **2,503 words** |
| `references.md` | 97 entries | **110** (97 strong-`local:`) |
| Sources in `download/` | 181 | **191** (10 acquired + identity-verified) |
| Top-level `sec-N` anchors | **0** | **27** |

All gates green, corpus-wide, at push: lint-math 0 · validate-refs 0/0 · 1,021 fragment links
0 dangling · 242 reference entries 0 errors in **index mode** · depth-tiers 19 labels 0
violations · tier drift-diff **0 TIER-DRIFT** · crosslink 0 gaps / 0 uncovered / 0 unreachable
· record-ids consistent.

---

## 1. Configuration

`max` resolved to **`proposed` + `scale: wide` + `audience: learner`**, recorded here per the
footer rule.

**The binding constraint was not the one the flag names.** `scale: wide` sets
`searches_per_agent = 40`, but `searches_per_session` is a harness-enforced pool of ~200
**shared across the main thread and every subagent**. Eight agents sized by the per-agent knob
would have *requested* 320 against that pool. Sizing followed the config's own rule —
`min(40, (200 − 25) / 8) = 21` searches per agent, with a 25-call holdback reserved for
main-thread verification. The holdback was what later made it possible to acquire and read ten
papers rather than cite them from search snippets.

**Audience register.** `learner` shows up concretely in Appendix J: each derivation opens with
a worked instance before the general statement, every algebra step carries a one-line reason,
and interpretation is labelled where it departs from what a source states. The register changed
exposition only — no boxed result, worked number, or epistemic tag differs from what a
`practitioner` register would have carried.

---

## 2. Evidence round — and its failures

Eight `evidence-collector` agents on **Sonnet** (bulk search and extraction against a fixed
ledger schema — the documented Sonnet case), hardened per DRS-HARDEN: exact paths, no `Glob`,
WebFetch ≤ 2, ~4 questions each, and the incrementally-written `_scratch/max-c*.md` file as the
graded deliverable.

### Retry telemetry

| Cluster | Deaths | Retries | Trimmed | Recovered | Outcome |
|---|---|---|---|---|---|
| C1 agent loop | 0 | 0 | — | — | complete (31 tool calls) |
| C2 frontier systems | 0 | 0 | — | — | complete (31) |
| C3 evaluation | 0 | 0 | — | — | complete (27) |
| C4 pretraining | 1 | 1 | yes | partial | Q1–Q3 complete; **Q4 coverage-gap marker** |
| C5 alignment | 0 | 0 | — | — | complete (25) |
| C6 test-time compute | 1 | 1 | yes | at attempt 2 | complete |
| C7 retrieval | 0 | 0 | — | — | complete (28) |
| C8 serving/safety | 1 | 1 | yes | at attempt 2 | complete |

**Every death was the step cap, and none was context.** The three dead agents stopped at 28–31
tool calls with an intermediate progress narration as their final message — the documented
`stop_reason=tool_use` shape — while their `_scratch` files held complete, high-quality answers
for the questions they had reached. The file-first rule is the entire reason a ~40% cluster
death rate cost one sub-question rather than three clusters.

**The restart-intensity ceiling fired once.** C4's Q4 died on both the original and the trimmed
retry. Rather than spawn a third, the subtopic carries a visible coverage-gap marker in
`_scratch/max-c4.md`, which is what the safety-net invariant requires.

### What the agents caught that the brief got wrong

The citation-integrity rule requires marking one's own recollections as unverified priors and
instructing agents to override them. That paid twice:

- **SemDeDup was never demonstrated on code.** The brief implied it was; the paper evaluates
  LAION and C4 text only. The agent corrected the brief rather than inheriting the error.
- **MCP's origin date** was corrected from a vague "~late 2024" to 25 November 2024, verified
  against the specification itself.

And once in the other direction: C5, reading the RLEF paper for a different question, noticed
the *survey* disagreed with it — which became `bugs/2026-08-14-01`.

---

## 3. What was deliberately not reported

Two categories of number were available and were left out. Both are recorded as decisions, not
omissions.

**Current SWE-bench leaderboard figures.** Two independent search passes returned top-of-leaderboard
values that disagreed with each other for the *same* leaderboard, and the authoritative pages
render their tables in JavaScript that a text fetch does not capture. Worse, at least three
denominators circulate for "SWE-bench Verified" — the original 500 plus smaller counts used by
particular evaluators who drop instances they judge unusable. A cross-vendor percentage
comparison on unstated denominators is a metric-basis difference presented as a capability
difference, which is exactly what `calibration-residuals.md` check 4 exists to stop. §13.4
states the denominator problem instead of a number.

**Multi-agent coding results.** Several systems report head-to-head gains over a single-agent
baseline with the base model held fixed. Every such ablation located was produced by the team
proposing the method — the `[opt:SIM-BASELINE]` deficit, where the treatment gets the design
effort and the control inherits a default nobody interrogated. One system reports two mutually
inconsistent resolve rates for itself across public descriptions. §12.7 states the question is
open and says why, which is a stronger claim than any of the numbers would have been.

---

## 4. Bugs and structural defects

**`bugs/2026-08-14-01` (high, fixed).** §8.3 read RLEF's two-column `Valid | Test` results table
as a *before/after* pair. The published sentence claimed a rise "from 37.5 to 40.4 on validation…
reaches 41.2 on test (versus 38.0 with feedback limited to public tests)". Against Table 1: 37.5
and 40.1 are the post-RLEF *validation* and *test* scores of one row; 40.4 and 41.2 appear
nowhere; and no public-tests-only ablation exists. The true effect is **25.9 → 37.5 validation
and 27.5 → 40.1 test at a 1@3 budget** — roughly 11.6 points, not the ~2.9 implied.

The reason this matters beyond one sentence: **a substring check would have passed it.** Every
digit string except two appears somewhere in the paper. What was wrong was the row-and-column
assignment — the citation's semantics, not its tokens. And it was found *by accident*. That
makes the pre-existing body's ~180 citation markers an unaudited population, which is now the
top item in the follow-ups todo.

**`bugs/2026-08-14-02` (med, open).** The `/study` pulse check reported "1 fold added" for a
session that added none: fold lines carry their paragraph anchor inline, so a routine
`renumber-paragraphs` pass rewrites every fold line and the added-line scan re-counts them.
This converts a zero-folds honesty guardrail into a rubber stamp, precisely after routine
maintenance.

**Top-level anchors (fixed, `todos/…-top-level-section-anchors` closed).** No section in the
survey had a `sec-N` anchor, so no document could link to a whole section — silently, because
subsections *were* indexed, so no gate fired. I initially deferred this on the assumption the
fix required re-marking headings and cascading every paragraph anchor. That assumption was
wrong: the corpus's two healthy surveys use an anchor-only marking that leaves visible text
untouched, and `renumber-paragraphs --check` confirmed `Updates: 0`. Checking how the working
examples actually did it beat reasoning about the fix from the grammar.

**The drift-diff was not binding.** The Phase-1 outline wrote its Section cells as `sec-4` where
`depth-tier-coverage.py` expects the bare token `4`. Its first "0 TIER-DRIFT" was therefore
vacuous — a green gate that had not looked. Corrected; it now binds and reports 0 TIER-DRIFT and
0 advisory against 19 allocated sections.

---

## 5. Self-evaluation scorecard

Scored against the **delivered** scope. Depth fractions are coverage over load-bearing items per
R-GOV, never prose volume.

| P0-2 dimension | Score | Basis |
|---|---|---|
| Coverage | 4/5 | Eight clusters covering the full pipeline; one explicit coverage gap (C4 Q4); four `load-bearing` sections labelled but not expanded. |
| Structure | 5/5 | Tier allocation approved before authoring, delivered with 0 drift; all gates green. |
| Relevance | 5/5 | Depth went to the code-specific spine, as approved; general-transformer material deliberately untouched. |
| Synthesis | 5/5 | The scaffold-thinning thesis is carried by three independent lines (ACI reversal, o1-ioi vs o3, the J.4 coverage-vs-selection derivation) rather than asserted. |
| Critical analysis | 5/5 | Two number categories declined on evidence-quality grounds; a negative result (METR) given its own subsection; self-reported figures tiered as such. |

| R-RUBRIC depth axis | Fraction | Note |
|---|---|---|
| Derivation completeness | **4/4** of the appendix's load-bearing results | No-skipped-steps, learner register. |
| Intuition coverage | **4/4** | Each derivation opens with motivation and closes with what it licenses. |
| Worked-example coverage | **4/4** | Every derivation carries a hand-checkable instance, all recomputed numerically. |
| Asymptotics / regime | **2/4** | J.4 (small-`p` limit, `k ∝ 1/p`) and J.2 (FIM-rate limit at 100%). J.1 and J.3 have no natural regime map. |
| Complexity / finite-precision | **1/4** | J.1 only (the float64 precision argument for the product form). Genuinely absent elsewhere. |
| Decision-usefulness | **partial** | §13.6 is a portfolio selection table; the survey-wide master comparison matrix was **not** built (see §7). |

**Honest weak axis:** complexity and finite-precision coverage is 1 of 4. It is not padded to
look better; the three remaining derivations have no meaningful op-count or precision story, and
inventing one would be exactly the "added length, not judged quality" failure R-GOV exists to
prevent.

---

## 6. Depth-tier coverage (Layer 3′)

```
depth-tier-coverage: 0 TIER-DRIFT, 0 advisory (0 missing, 0 over, 0 n/a-form).
Tier tally (delivered): headline 8, load-bearing 6, supporting 5.
Outline allocation:    19 section(s) tiered in 00-max-mode-outline.md.
```

Delivered tiers match the allocation approved at the P0-3 gate exactly.

---

## 7. Coverage gaps and what is left

Tracked in `todos/2026-08-14-llms-for-coding-followups.md`; the load-bearing ones:

1. **A `citation-audit` pass over sections 1–11 and 14–18.** The population is unaudited, and
   one error found by chance is evidence about a rate.
2. **Four `load-bearing` sections labelled but not expanded** — 11 retrieval, 14 cost, 15 SOTA,
   16 safety. Their evidence is collected and preserved in `_scratch/max-c7.md`, `max-c2.md`,
   `max-c8.md`, unconsumed rather than lost. The unbuilt R-SURVEY artifacts (master comparison
   matrix, quantitative SOTA table, notation contract) belong with §15.
3. **"Code training improves general reasoning" is unverified in the acquired corpus.** No
   source opened measures it. The survey must not repeat it, and must not resolve it in favour
   of the popular answer.
4. **Multi-agent coding has no independent replication.** A genuine research gap, not a search
   failure.

---

## 8. Citation-integrity statement

Every citation added in this pass traces to a source opened during it. Ten papers were acquired
to `download/` and **identity-verified from page 1** before use; the numbers quoted from them
were read from the source text or table, not from search summaries. Where a claim rests on a
live web resource whose page *is* the citation (a protocol specification, a vendor engineering
post), it carries a `(web)` tag and is described as vendor-stated rather than measured. Where a
figure could not be traced to a read source, it was omitted or explicitly marked
reported-not-verified — §12.2's mini-SWE-agent figure and §13.5's benchmark-retirement
announcement are both labelled in the prose as self-reported or unacquired.

`check-citation-sources.py --index` — the strong form, resolving against git's index rather than
the working tree — reports **110 entries, 0 errors** for this survey and 242 entries, 0 errors
corpus-wide.

---

## 9. Audit trail

- `decisions/2026-08-14-03` — expand-in-place, depth on the code-specific spine, and the two
  declined number categories.
- `bugs/2026-08-14-01` (high, fixed) · `bugs/2026-08-14-02` (med, open).
- `todos/2026-08-14-llms-for-coding-followups` (open) ·
  `todos/2026-08-14-recall-prompt-is-a-label-not-a-question` (open) ·
  `todos/2026-08-14-top-level-section-anchors` (closed).
- `surveys/llms-for-coding/_scratch/00-max-mode-outline.md` — the approved brief and allocation.
- `surveys/llms-for-coding/_scratch/max-c1.md` … `max-c8.md` — the evidence ledgers.
- `surveys/llms-for-coding/_scratch/review-appendix-j.md` — the R-MATHREV adversarial
  re-derivation (§10).
- `prompts/2026-08-12-upstream-sync.md` Conversation 13.

**Footer.** mode `proposed` · flags — · scale `wide` (searches 21/agent effective, 40 nominal;
verify fan-out unused; file-split 200 KB) · audience `learner` · `agent_hardening: on` ·
`retry_policy: on` (3 retries fired, 2 recovered, 1 hit the ceiling).

---

## 10. R-MATHREV — adversarial re-derivation (complete)

`max` activates `[R-MATHREV]`, and `[opt:MATH-REDERIVE]` triggers independently on the new
`\tag{}` lines. An Opus reviewer derived all four results from first principles and wrote them
to disk **before** opening the appendix — the deliverable carries a `<!-- PHASE-A-END -->`
sentinel marking that boundary — then diffed, then recomputed every number.

**Verdict: sound in its four core results; two findings had to be fixed before sign-off.**

What the review confirmed rather than merely accepted: the concavity expression and its
Jensen direction are correct *including the sign* (it looked for an inversion and found none);
the estimator is genuinely unbiased, verified to `3.8e-15`, so the appendix's "no
approximation, no large-$n$ limit" is an **earned** claim it explicitly recommended *not*
downgrading; the product identity is exact over 4,000 random triples including the degenerate
branch, and the printed twelve-digit check value is right to the last digit; the KL
convexity block is entirely correct; the FIM causal-mask argument and the $L/3$ spacing result
both hold.

### Findings and dispositions — 2 high, 11 med, 6 low; all applied

| # | Sev | Finding | Applied |
|---|---|---|---|
| 1 | **high** | J.1's punchline claimed a one-in-a-hundred model scores `pass@100 ≈ 1`. It is **0.6340**. The point was right; the instance refuted it. | Rewritten at $p = 0.05$ (0.9941), with the $p = 0.01$ value kept as the counter-example and the governing product $pk$ named. |
| 2 | **high** | The GRPO caveat said the lemma "licenses subtracting the mean" and only the division is a heuristic. **Backwards** — the group mean contains $r_i$, violating the lemma's one hypothesis. | Rewritten with the derivation: in-group centring yields exactly $\frac{G-1}{G}\nabla J$. Added as a new numbered equation, verified by Monte Carlo (0.4998 / 0.7499 / 0.8748 vs 0.5 / 0.75 / 0.875), and noted that leave-one-out would be exactly licensed. |
| 3 | med | The FIM "contains an AR sub-task" claim named the **suffix** factors; those are gap-conditioned continuation. The **prefix** factors are the ones that satisfy it. | Corrected, with the suffix case called out explicitly as the genuinely different task. |
| 4 | med | The precision argument cited $\binom{200}{100}$, which the estimator never forms; at the worked point the naive ratio is **bit-exact**. | Requalified as a general-case overflow hazard near $k \approx n/2$, with the worked-point measurement stated against it. |
| 5 | med | "solve rate vs $\log k$ looks like a straight line" — a single-$p$ curve is a saturating sigmoid. | Corrected, with the decade increments printed and log-linearity attributed to its actual mechanism (a mixture over problems of differing $p$). |
| 6 | med | $k \approx 202$ for 95% coverage: 202 gives 0.94978, and the bound is a $\ge$. | Corrected to **203**, with the shortfall shown. |
| 7 | med | The worked GRPO `std = 0.5` is the population form; the sample form gives 0.577 and $\pm 0.866$. `[opt:MATH-BASIS]` requires the declaration. | Basis declared inline with both values. |
| 8–9 | med | Two argument gaps: the unbiasedness proof jumped from the subset fact to the expectation without the tower step (and never stated $n \ge k$); the KL block never established that $f(u)$ *estimates* a KL. | Both closed — the tower step made explicit, and $\mathbb{E}[f(u)] = \mathbb{D}_{\mathrm{KL}}$ derived in two lines. |

**The finding worth dwelling on is 9-adjacent: J.4 substituted an *averaged* pass rate into a
concave function — the exact Jensen fallacy J.1 spends fifteen paragraphs warning against.**
Committed in the same document that teaches against it, roughly two thousand words later. It is
now flagged in place, along with the wrong-event mismatch beside it (the rate is
pass-the-example-tests, not solve), and the number is framed as an order-of-magnitude anchor
rather than a budget. This is precisely the class an oracle cannot catch: every number involved
was arithmetically correct.

**Scope honesty.** The review reports seven external-sourcing claims as **UNCHECKED** rather
than correct — the Codex appendix, the FIM-rate sweep, InCoder, Reflexion, AlphaCode and the IOI
figures. Those belong to `citation-audit`, not to a re-derivation, and are folded into the
follow-ups todo rather than silently counted as verified.

Post-fix state: **20 numbered equations, sequential**; survey re-normalized; all gates clean.

*Why this gate earns its cost:* the numerical oracle I ran while authoring confirmed every value
in J.1 and J.3 and would have confirmed them forever. Findings 1 and 2 are both cases where the
arithmetic was right and the *sentence built on it* was wrong. Oracles test values; re-derivation
tests reasoning.
