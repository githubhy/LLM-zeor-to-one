---
slug: sae-frontier-followups
date_filed: 2026-07-02
status: open
---

# SAE-frontier study — follow-on work

## Context
The `sae-frontier` reference-implementation study (docs/sae-frontier-implementation-study.md, gates
G1–G4 PASS) confirmed H1–H4 and recommends TopK, at commodity scale (synthetic + GPT-2-small). These
are the deferred items named in its roadmap (Sec. 11) and red-team (Sec. 10).

## What is left
- **Gemma-scale port.** Reproduce the frontier on Gemma-2-2B via **pretrained Gemma Scope** SAEs on a
  GPU host (the survey's original target; infeasible on the 17 GB Mac — decision 2026-07-02-01). Test
  H1/H4 at production scale + the survey's headline loss-recovered.
- **JumpReLU STE robustness.** Make the STE bandwidth data-adaptive (its ranking is bandwidth-conditional,
  bug 2026-07-02-01); add a regression test asserting θ moves under a sparsity sweep.
- **Adaptive-count variants.** Add BatchTopK + Matryoshka (catalog-only here); the red-team predicts
  they beat exact-k TopK on heavy-tailed / dense activations (the regime where JumpReLU already flipped ahead).
- **Widen S2.** Multiple GPT-2 sites + a full loss-recovered frontier (not just the mid operating point).
- **Shrinkage on orthonormal substrate.** The empirical shrinkage-ratio is noisy on superposition; a
  dedicated orthonormal-atom run would give a clean H2 empirical curve to overlay on the closed form.

## Acceptance
A Phase-6-style report for the Gemma-scale port (per `sim-report-completeness`); the other items land
as tests / new candidates / extended artifacts under `artifacts/sae-frontier/`.

## Refs
- Study: `docs/sae-frontier-implementation-study.md`; code `implementation/sae_frontier/`.
- Parent handoff: `todos/2026-07-01-mechinterp-ris-handoff.md` (candidates 2 & 3 still open).
- Bug `2026-07-02-01`; decision `2026-07-02-01`.
