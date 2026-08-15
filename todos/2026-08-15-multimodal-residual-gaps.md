---
slug: multimodal-residual-gaps
date_filed: 2026-08-15
status: open
---

# Residual gaps after the multimodal-llms max-mode expansion

## Context

Filed at sign-off of the 2026-08-15 expansion pass. Nothing here blocks the survey — every
item below is something that was **deliberately not used** rather than something that was used
badly. They are recorded so the next pass does not have to rediscover why they are absent.

## What is left

**1. Numbers the sweep flagged as unverified, and this survey therefore did not cite.**
The evidence agents were instructed to mark provenance, and did. Several figures were read via
search-engine paraphrase rather than from a primary PDF, and the agent explicitly recommended
re-verification before they were stated as hard numbers:

- text-only ("blind") solvability rates for two standard multimodal benchmarks;
- a fraction-of-items-distorted figure across an 18-benchmark audit;
- a hallucination-mitigation improvement where two search summaries disagreed with each other
  on the same comparison (the disagreement is itself the reason it is not cited).

The qualitative claims these support *are* in the survey (§13.1 item 7); the numbers are not.
Fetch the primary PDFs, verify, and then either state the numbers or record that they did not
survive verification.

**2. Model and system names the sweep could not corroborate.** Several names appearing in
leaderboard-aggregator summaries could not be confirmed as real released models, and at least
one looked like a scraping or parsing artifact of a secondary site. None was used. If a future
pass wants to cite any leaderboard row, corroborate the row's *subject* exists before citing
its score.

**3. R-SURVEY figures were not produced this pass.** The richness layer nominates at least one
conceptual block diagram per architecture family, plus a reproducible figure with persisted
data and generator for each load-bearing quantitative claim. `surveys/multimodal-llms/` has no
`figures/` directory. The strongest candidates, now that the arithmetic exists to back them:

- the video token-budget wall (Appendix F §F.5's four-row table is already the data — an
  ASCII or rendered plot of tokens vs clip length against typical context limits);
- the encoder → connector → LLM stack as an ASCII block diagram (zero-dependency default);
- the three-lever decomposition of the token-budget equation.

Any rendered figure must follow `.claude/rules/figure-operating-conditions.md` (numeric
operating conditions in §1 of the caption) and the diagram rule's determinism requirements —
including the byte-reproducibility fix from `bugs/2026-08-15-03` (`svg.hashsalt` +
`metadata={'Date': None}`), which is not optional and is cheap to get right up front.

**4. An unverified attribution in Appendix D.** §D.2 attributes EMA codebook updates to the
VQ-VAE reference. The evidence pass for this appendix read only that paper's main text
(pp. 1–6) and did not confirm the EMA material there; the claim predates this session and was
left untouched. Confirm it against the paper's appendix, or re-attribute.

## Acceptance

- Every item above is either resolved (number verified and cited, figure produced, attribution
  confirmed) or explicitly closed with a reason.
- No number enters the survey from this list without a primary-source read.

## Refs

- `surveys/multimodal-llms/_scratch/ev-frontier-eval.md`, `ev-frontier-models.md` — the
  ledgers, each with its own `Coverage gaps` / `Basis conflicts` section.
- `decisions/2026-08-15-02` — the decision that kept these out of the survey.
- `.claude/rules/citation-integrity.md`; `.claude/rules/figure-operating-conditions.md`;
  `bugs/2026-08-15-03` (figure byte-reproducibility).
