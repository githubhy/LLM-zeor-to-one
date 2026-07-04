---
id: 2026-07-04-02
title: H9 structured as a two-part mechanism-vs-behavior contrast, at commodity scale
status: accepted
date: 2026-07-04
plan: plans/2026-07-04-h9-algorithmic-icl.md
---

## Context

H9 ("algorithmic ICL — does the forward pass implement an online learner?") was pre-registered
in the tiny-transformer study and hard-gated on a source-fetch
(`todos/2026-06-28-icl-as-online-learning-intuition.md`, decision `2026-07-01-03`). With the gate
cleared, the understand phase read the four acquired sources page-by-page and surfaced a
structural fact the plan had not pre-decided: the literature does **not** support one uniform
claim. The exact "attention = gradient descent" identity is for **linear** attention with
**constructed** weights (von Oswald Prop 1); single-head **softmax fails** it (von Oswald §A.9).
A **trained softmax** model only **behaviorally matches** least-squares (Garg; Akyürek). Dai's
"LLMs implicitly perform gradient descent" title is downgraded in its own body to a relaxed-
*linear*-attention dual form plus finetuning-similarity on classification. Two judgment calls
followed: (1) how to structure the study so it does not collapse these into a single over-claim;
(2) what scale to run on 16 GB / MPS, given Garg's 9.5M-param / 500k-step reference.

## Decision

Structure H9 as an explicit **two-part contrast**, and make the contrast itself the deliverable:
- **Part A (mechanistic, exact):** implement the von Oswald Prop-1 *linear*-attention construction
  and verify, to machine precision, that one layer = one GD step (and $K$ threaded layers =
  $K$-step GD). No training.
- **Part B (behavioral, trained):** train a small *softmax* regression transformer and show its
  in-context predictions *track* OLS/ridge (tightening with depth and context), **without**
  claiming it mechanistically runs GD.
Run Part B at **commodity scale** ($d=8$, ~140K params, 12k steps, depth sweep {1,2,4}) rather
than Garg-scale, and disclose the scale-down numerically (figure-operating-conditions rule),
framing H9-B as "an eval of *this* configuration tracks OLS," not a benchmark-mandated claim.
The report's §2 source table and §10 do-NOT list enforce the mechanism-vs-behavior boundary.

## Alternatives considered

- **Part B only (train + compare to learners).** Rejected: without the exact Part-A anchor the
  study cannot *separate* "the mechanism exists (for linear attention)" from "a trained softmax
  model behaves like OLS," which is exactly the conflation the sources warn against — it would
  invite the "trained transformers do gradient descent" over-read.
- **Part A only (construction identity).** Rejected: the H9 pre-registration and the parent todo
  require the trained loss-vs-examples curve and the model-vs-learner overlay — a behavioral
  result Part A cannot provide.
- **Garg-scale reproduction ($d=20$, ~9.5M params, 500k steps).** Rejected: infeasible on the
  16 GB / MPS laptop; and unnecessary — the behavioral claim is curve-shape + operating-point,
  robust to scale-down (the commodity model still reaches $\Delta_{\text{norm}}=0.009$, an order
  of magnitude inside the bar). Garg-scale is filed as a follow-on.
- **Interleaved vs concatenated token layout, shared across both parts.** Rejected a single shared
  layout: Part A uses von Oswald's concatenated $e_i=(x_i,y_i)$ tokens (the construction's own
  regime) and Part B uses Garg's interleaved $[x_i, y_i]$ stream — each faithful to the source it
  reproduces; forcing one layout would misrepresent one of them.

## Consequences

- Enables an honest split verdict: H9-A PASS (exact, linear+constructed), H9-B/C/D PASS
  (behavioral, softmax+trained) — with the boundary between them cited to the exact source that
  supports each side. This is the study's main scientific contribution.
- Forecloses nothing; the deferred pieces (mechanistic probing of the trained model, two-head-
  softmax approximate GD, GD++, Garg-scale, kernel extension) are filed in
  `todos/2026-07-04-h9-followups.md`.
- The `_quiet_blas` FPE-suppression and the shared GD-convention decisions are implementation
  details recorded in the field note, not here.

## Refs

- Plan `plans/2026-07-04-h9-algorithmic-icl.md`; report `docs/h9-algorithmic-icl-study.md`.
- Prior decision `decisions/2026-07-01-03` (H9 fold-in + hard source-gate).
- Code `implementation/icl_regression/` (construction.py = Part A, model.py/run.py = Part B).
- Survey note `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.23.
- Follow-ons `todos/2026-07-04-h9-followups.md`; field notes `field-notes/2026-07-04-h9-algorithmic-icl.md`.
