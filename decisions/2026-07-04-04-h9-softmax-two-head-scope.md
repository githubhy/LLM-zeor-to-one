---
id: 2026-07-04-04
title: H9 softmax two-head as a constructive (not trained) reproduction; honest-vs-idealized two-object structure
status: accepted
date: 2026-07-04
plan: plans/2026-07-04-h9-softmax-two-head-gd.md
---

## Context

The H9 study (`docs/h9-algorithmic-icl-study.md`) deferred von Oswald §A.9's softmax-side
mechanistic leg (`todos/2026-07-04-h9-followups.md`): a *single* softmax head fails to match the
one-GD-step update; *two* sign-reversed heads approximately recover it via a Taylor-linearisation
offset cancellation (their Eq 14–21, Fig 12). The paper shows this two ways — an *analytical*
argument (Eq 14–21) and a *trained* single-layer 1-head-vs-2-head run (Fig 12). Reproducing "both"
literally would add a stochastic training module (seeds/CIs, MPS risk) for a result H9-B already
partly covers (softmax transformers do learn the ICL behavior).

Reading §A.9 closely surfaced a subtlety the paper glosses with "≈": with an *honest* softmax
(real `exp`, real per-head denominators) the two-head difference is `2β(s_i − s̄)/N`, not `2βs_i/N`
— the head denominators are unequal, leaving a `β`-independent **centering term** `−(η/N)·s̄·Σv`.
The paper's clean Eq-19–21 result assumes "PV subsumes the softmax divisor and is equal per head",
i.e. it *idealizes that term away*. So there is no single "two-head softmax = GD" object: there is
an **idealized** one (exact) and an **honest** one (approximate, with a residual floor).

## Decision

Reproduce §A.9 **constructively** (the paper's constructed weights with a softmax swapped in;
deterministic, no training) as **two objects**: (1) the **idealized** two-head construction
(Eq-16 linearisation + equal divisor), verified `= GD` to machine precision (`3.1e-15`, every `β`)
— the mechanism, provably; and (2) the **honest** full softmax — single head with an irreducible
`O(1)` offset floor (`0.587`), two heads recovering it `4.5×` to `0.130` down to a small `O(1/N)`
**centering floor** that is root-caused (the predicted centering term explains `98.3%` of the
residual) and shown asymptotic-only (floor halves as `N` doubles; single/two ratio `3.1×→15.1×`).
The **trained** Fig-12 run is explicitly **deferred** (a `DEVIATED` conformance row), not built.

## Alternatives considered

- **Train the Fig-12 single-vs-two-head run (literal reproduction).** Rejected as the *primary*
  deliverable: stochastic, needs a torch module + seeds/CIs + MPS mitigation, and answers
  "emerges from training" (partly H9-B) rather than the tracked ask "single fails / two recovers
  via offset-cancellation," which the construction answers *provably*. Kept as a deferred secondary
  leg (todo), so the study stands without it.
- **Only the idealized identity (drop the honest run).** Rejected: it would hide the centering
  floor and overclaim "two-head softmax = GD exactly." The honest run is what reproduces Fig 12's
  "good but not as precise as linear" and is the more honest result.
- **Full-sequence softmax (query attends to itself too).** Rejected for the constructive core: the
  query-self term is orthogonal to §A.9's offset argument and would conflate two effects. Documented
  as an `IDEALIZED` conformance row; belongs to the (deferred) trained leg.

## Consequences

- Enables a rigorous, deterministic §A.9 reproduction with an exact mechanism anchor + an honest,
  root-caused approximation — mirroring H9-A's construction/behavior split.
- Forecloses (for now) a claim about *trained* softmax two-head emergence — deferred, tracked.
- Follow-up: `todos/2026-07-04-h9-followups.md` (trained leg, full-sequence variant, reduced
  precision, Garg-scale) updated — the two-head-softmax *mechanism* item is closed; the *trained*
  sub-item remains.

## Refs

- Report `docs/h9-softmax-two-head-gd-study.md`; code `implementation/icl_regression/softmax_*.py`;
  gate `tests/icl_regression/test_softmax_construction.py`.
- Source §A.9 Eq 14–21 `download/vonoswald-transformers-icl-gradient-descent-2023.pdf`.
- Field notes `field-notes/2026-07-04-h9-softmax-two-head.md`; parent decision `2026-07-04-02`
  (H9 two-part structure); conversation log `prompts/2026-07-03-*.md`.
