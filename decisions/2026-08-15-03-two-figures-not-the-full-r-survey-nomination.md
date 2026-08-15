---
id: 2026-08-15-03
title: Close the R-SURVEY figure gap with two figures chosen for what they can prove, not the full per-family nomination
status: accepted
date: 2026-08-15
plan: todos/2026-08-15-multimodal-residual-gaps.md item 3
---

## Context

The `deep-research-survey` richness layer (R-SURVEY) nominates, for a max-mode survey, **at
least one conceptual block diagram per architecture family** plus **a reproducible figure with
persisted data and generator for each load-bearing quantitative claim**. The 2026-08-15
expansion pass produced neither; `surveys/multimodal-llms/` had no `figures/` directory at all,
and the gap was filed as `todos/2026-08-15-multimodal-residual-gaps.md` item 3 with three
candidates named.

Read literally, the nomination is large. The survey has five architecture families (§ 3.6's
table) and considerably more than five load-bearing quantitative claims — the attention cost of
$N_v$, the connector token bill, the KV-cache arithmetic, the audio frame-rate chain, the video
token budget, the InfoNCE bound, the VQ compression ratio, the EMA convergence. A figure per
claim would be a dozen-plus figures, most of them restating in a plot what the equation already
states in one line.

## Decision

Produce **two** figures, chosen by what a figure can do that prose cannot, rather than by
covering the nomination's enumeration:

1. `figures/appendix-f-video-token-wall.py` / `.svg` / `.json` — a two-panel quantitative
   figure (§ F.8) for the video token budget.
2. A zero-dependency **ASCII block diagram** (§ 3.6) of the encoder → connector → LLM template,
   with a five-row table instantiating all five families against it.

The selection rule applied: a figure earns its place when it shows a **relationship between
curves** that a table of points cannot — a crossing, a slope difference, a divergence — or when
it shows **shared structure across variants** that prose must repeat once per variant. Both
deliverables meet that; a plot of a single monotone formula does not.

## Alternatives considered

- **One block diagram per family (five diagrams), per the nomination's wording.** Rejected: the
  five families differ by *three knob settings on one template*, which is the survey's own
  thesis (§ 3.1). Five separate diagrams would draw the template five times and bury the
  variation; one diagram plus a table puts the variation in the reader's eye at once. This is a
  case where following the nomination literally would produce a worse artifact than its intent.
- **A figure per load-bearing quantitative claim.** Rejected as restatement. Most of the
  survey's load-bearing quantities are single closed forms already displayed as numbered
  equations with worked examples; plotting $N_v = (H/P)^2$ adds nothing a reader of Eq. (9)
  lacks. The video budget is the exception precisely because its content *is* a crossing —
  a linear-in-duration cost against a constant context — and the crossing is the argument.
- **Separate figures for the token wall and the three-lever decomposition** (candidates 1 and 3
  in the todo). Rejected in favour of merging them: lever 3's cost is *the per-frame budget
  under a cap*, which is the same arithmetic as the wall solved for a different unknown. Two
  panels of one figure keep them on shared axes; two figures would invite reading them as
  independent results.
- **Deferring all figures again.** Rejected: the arithmetic to back them now exists (Appendix F
  § F.5 was written this cycle), so the cheapest moment to produce them is now, and a second
  deferral would be the third pass in which the same nomination goes unmet.

## Consequences

**Enables.** The video-wall figure makes one claim visible that the § F.5 table could only
assert: the curves are straight lines of slope 1 in log–log while every context is horizontal,
so the wall is *structural* and no context size removes it. It also surfaced a basis question
the prose had left implicit — "128k context" is decimal (128,000) in the survey, and the binary
reading (131,072) moves the two-hour overshoot from $64.8\times$ to $63.3\times$. Both are now
declared in the caption and carried in the persisted JSON, per `[opt:MATH-BASIS]`.

**Forecloses.** Nothing structurally — the `figures/` directory, the byte-reproducible
generator pattern (`svg.hashsalt` + `metadata={'Date': None}`, per `bugs/2026-08-15-03`), and
the four-section caption schema are now established in this survey, so a later figure is an
increment rather than a bootstrap.

**Follow-up.** The R-SURVEY nomination is *not* fully met and this decision does not claim it
is. What remains unfigured is recorded in the todo's resolution rather than left implicit; the
strongest remaining candidate is the connector token-bill comparison (§ 3.3's 576 / 64 / 32 on
identical input), which was left out only because § 3.6's table already carries those three
numbers side by side.

**Also declined, deliberately.** The § 3.6 diagram ships with **no generator and no persisted
data**, and says so in its own caveats section. The diagram rule's persistence requirement
exists so a figure can be regenerated without re-running an experiment; there is no experiment
and no computation here, and manufacturing a script that emits a fixed string would satisfy the
letter of the rule while adding a file to keep in sync with the prose it duplicates.

## Refs

- `todos/2026-08-15-multimodal-residual-gaps.md` — the todo this closes (item 3).
- `bugs/2026-08-15-03` — the byte-reproducibility fix both new generators adopt at birth.
- `.claude/rules/figure-operating-conditions.md` — the § 1 numeric-disclosure contract, met by
  both captions including the explicit `n/a` rows for model / decoding / benchmark / seed.
- `.claude/rules/workflow.md` § Diagram Rules — persistence and determinism.
- `surveys/multimodal-llms/appendix-f-audio-video.md` § F.8;
  `surveys/multimodal-llms/architecture-building-blocks.md` § 3.6.
