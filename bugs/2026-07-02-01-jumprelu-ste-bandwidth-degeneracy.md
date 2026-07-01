---
id: 2026-07-02-01
title: JumpReLU SAE collapses to a dense solution (L0≈48 regardless of λ) — STE bandwidth too small
severity: high
status: fixed
date: 2026-07-02
component: implementation/sae_frontier
---

## Symptom
In the Phase-3 frontier run, JumpReLU produced the SAME L0 (≈48, dense) at every operating point
in its λ sweep, and a spuriously high "EV @ L0=8" (0.953) that was actually an *extrapolation* far
below its real L0 range — making JumpReLU look like the runaway winner. Diagnosis showed the learned
threshold θ never moved from init (0.0010 → 0.0013 across λ ∈ {0.01…0.5}).

## Root cause
The straight-through estimator (STE) for the JumpReLU threshold uses a rectangle kernel of
half-width `STE_BANDWIDTH` around θ. It was set to `1e-3`, but the activations are O(1); almost no
pre-activation lands within ±1e-3 of the (tiny, ~1e-3) threshold, so the STE kernel is ~0 → θ
receives essentially no gradient → stays at init → all features pass → dense SAE. A too-small STE
bandwidth *starves the threshold of gradient* — the SAE cannot learn to sparsify.

## Fix
`utils.STE_BANDWIDTH` 1e-3 → **0.1** (sized for O(1) activations) and
`config.jumprelu_init_threshold` 0.001 → **0.1** (start θ in the active range). JumpReLU then traces
a real frontier (L0 8.5–13.8, θ learns 0.10→0.15 with λ) and the corrected EV@L0=8 is 0.759 (TopK
0.821 now leads, honestly). Commit SHA on landing.

## Regression test
`tests/sae_frontier/test_saes.py::test_gradients_flow[jumprelu]` (θ receives finite gradient) +
`test_jumprelu_passthrough_no_shrink`; the Phase-3 frontier now shows a non-degenerate JumpReLU L0
range. A dedicated "θ moves under a sparsity sweep" assertion is a follow-up (todos).

## Refs
- Report: `docs/sae-frontier-implementation-study.md` Sec. 2 (conformance), Sec. 11.
- Related decision: `decisions/2026-07-02-01`. Field note: session `sae-frontier`.
