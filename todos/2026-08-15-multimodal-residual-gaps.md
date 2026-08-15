---
slug: multimodal-residual-gaps
date_filed: 2026-08-15
status: closed
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

## Resolution

**Closed 2026-08-15.** All four items worked; three resolved by verification against primary
sources, one by production. Three PDFs were acquired to `download/` in the process
(`yuan-mmgist-2026.pdf`, `akhtar-benchmark-saturation-2026.pdf`, `wu-reverse-2025.pdf`); every
arXiv ID was confirmed against its abs page before the PDF was trusted.

**Item 1 — the unverified numbers.** All three fetched and checked. Two survived; one survived
as a number but not as an attribution.

- *Text-only solvability.* **Verified**: AI2D $66.7\%$, MMMU $51.2\%$ (MMGist, arXiv:2606.22437).
  The sweep had not captured the basis, which turned out to matter: five inspector models from
  different providers, image-free question text only, eight responses sampled per item. That is a
  more permissive test than MMStar's single-model no-image score ($42.9\%$), so the $8.3$-point
  spread between them is mostly basis, not progress. Now cited in § 9.3 with the basis stated and
  the non-comparability spelled out.
- *The 18-benchmark distortion fraction.* **Real number, wrong paper.** arXiv:2602.16763 ("When AI
  Benchmarks Plateau") studies 60 **language-model** benchmarks and contains no such figure. The
  $68.8\%$ is MMGist's own, and is not "≥68.8%" but the exact complement of its retention rate
  ($7{,}262$ of $23{,}250 = 31.2\%$). Filed as `bugs/2026-08-15-05`; the ledger carries a
  correction block; § 9.3 now states it correctly attributed, derived, and tagged *[reported]*
  because it is one pipeline's removal rate self-reported by the paper proposing the survivor.
- *The hallucination-mitigation disagreement.* **Resolved in favour of 34%** — "28%" appears
  nowhere in arXiv:2504.13169. Reading the paper's tables produced four basis facts the search
  summaries could not: both headline figures are **relative** and both are **maxima over three
  backbones** (the $12\%$ is $6.4\%$ on the most-reported one); the $34\%$ is measured against the
  **untreated base model**; baselines mix the authors' re-runs with numbers carried from other
  papers; and HaloQuest is judged by a substituted judge model. The population split is the real
  finding — the gain is concentrated in false-premise and insufficient-context items while the
  **visually-challenging subset regresses on all three backbones**, and at the aggressive
  threshold caption coverage falls $51.0 \to 26.9$. All now in § 5.3.

**Item 2 — uncorroborated model names. Closed: confirmed artifact.** Checked against the
HuggingFace model API. `sensenova` is a real org with real released models
(`SenseNova-U1.5-8B-MoT-Preview`, `SenseNova-Vision-7B-MoT`, …), but "UNSenseNova" and "CongRong"
each return **zero** results, and no `SenseNova-V6` exists. The shared `UN` prefix across two
otherwise-unrelated names is the tell — a real naming coincidence does not repeat. Neither row's
subject is a released model; nothing was cited and nothing should be.

**Item 3 — R-SURVEY figures. Produced.** Two, with the selection rule and the rejected
alternatives recorded in `decisions/2026-08-15-03`:

- `figures/appendix-f-video-token-wall.py` / `.svg` / `.json`, embedded as § F.8 — two panels:
  the token budget against clip length with four context lines, and the per-frame budget a hard
  cap leaves. Reproduces § F.5's three worked rows exactly ($34{,}560$ / $345{,}600$ /
  $8{,}294{,}400$) and its capped per-frame figures ($273$ / $27.3$), and adds the $1.14$
  tokens/frame the two-hour case implies. Byte-identical across runs (`svg.hashsalt` +
  `metadata={"Date": None}`, per `bugs/2026-08-15-03`, adopted at birth rather than retrofitted).
- § 3.6, an ASCII block diagram of the encoder → connector → LLM template plus a five-row table
  instantiating every architecture family against it — one diagram covering what the nomination
  asked five to cover, because the families differ by three knob settings on one template.

Both captions carry § 1 numeric operating conditions **including explicit `n/a` rows** for model,
precision, decoding params, benchmark, harness, metric, CI, sampling $n$, `pass@k` and seed —
neither figure runs a model, and silent absence would be indistinguishable from an omission.

Not figured, and closed rather than deferred: the connector token-bill comparison
($576$ / $64$ / $32$ on identical input). § 3.6's table already puts those three numbers side by
side, so a plot would restate a three-cell row.

**Item 4 — the EMA attribution. Confirmed, and the section was deepened as a result.** EMA
codebook updates **are** in the VQ-VAE paper — Appendix A.1, with the main text pointing at it —
so the attribution stands. Reading it surfaced two things the survey had wrong or missing. The
paper explicitly notes EMA was "**not used for the experiments in this work**", so the mechanism
is the source's while the empirical case for preferring it is not; the survey had implied
otherwise. And § D.2 had carried the update as a sentence with no mathematics. It now derives the
$k$-means centroid the update targets, the two-accumulator online form with $\gamma = 0.99$, and
the two properties that justify the ratio: it weights minibatches by evidence (with the fixed
point recovering the centroid exactly), and an unused code is held **exactly** invariant because
both accumulators decay by the same factor — the case where a one-accumulator form evaluates
$0/0$, and precisely the state a collapsing codebook is in. Four new equations.

## Verification

`normalize-survey` clean on the delivered set (`validate-refs` OK, bare-refs $0$, citation
sources $55$ entries $0$ errors); `check-depth-tiers` $22$ labels $0$ violations;
`check-link-fragments` $342$ links $0$ dangling; `check-section-ownership` OK; `check-record-ids`
OK; `crosslink check` no gaps. The three residual `lint-math` errors are in `_scratch/` evidence
ledgers, predate this pass, and are in no manifest — left as preserved artifacts rather than
edited.

## Refs

- `bugs/2026-08-15-05` — the fused-attribution bug item 1 uncovered.
- `decisions/2026-08-15-03` — the figure-scope decision closing item 3.
