---
slug: h9-followups
date_filed: 2026-07-04
status: open
---

# H9 algorithmic-ICL — follow-on work

## Context

The H9 sub-study (`docs/h9-algorithmic-icl-study.md`, `implementation/icl_regression/`) closed
H9 at commodity scale as a **two-part contrast**: Part A (von Oswald linear-attention
construction = one GD step, exact) and Part B (a small trained *softmax* transformer
*behaviorally* tracks least-squares on in-context linear regression). Plan
`plans/2026-07-04-h9-algorithmic-icl.md` scoped several facets out of this pass; tracked here.

## What is left

- **Training-seed envelope beyond the 3 seeds.** H9-B's uncertainty is a min–max envelope over
  3 training seeds at the main depth; a larger seed set (and per-depth seeds for H9-D) would
  give a proper CI. The single-model eval uses a fixed trained model per seed.
- **Mechanistic probing of the trained softmax model.** Does layer $\ell$ compute a GD/ridge
  step? Akyürek §5 (nonlinear probes for the moment matrix $X^\top Y$ early, $w_{\text{OLS}}$
  late) and the von Oswald weight-space analysis. This would connect Part B (behavioral) toward
  Part A (mechanistic) — currently deliberately kept apart.
- **Two-head-softmax approximate-GD reproduction.** von Oswald §A.9 shows a *single* softmax
  head fails GD but a *two-head* layer approximately matches via Taylor offset-cancellation.
  Reproducing that (single-head fails, two-head recovers) is the softmax-side mechanistic story.
- **GD++ / preconditioned GD.** von Oswald §A.10 / Fig 3: stacked *identical* constructed layers
  implement GD++ (curvature-corrected), not plain $K$-step GD. `construction.k_step_via_construction`
  threads the explicit iterate (plain GD); the un-threaded stacked-layer GD++ behavior is not
  reproduced.
- **Garg-scale.** $d=20$, a ~1–10M-param model, and a longer training budget (Garg: 500k steps,
  curriculum) to reproduce the tight $0.0006$-at-$2d$ figure rather than the commodity-scale
  looser match. GPU host.
- **Kernel (MLP + LSA) extension.** von Oswald Prop 2: an MLP + one linear-attention layer
  implements one GD step on a *kernelized* least-squares loss — nonlinear in-context regression.
- **Reduced-precision.** Only float32 was run; a bf16/fp16 attribution/inference pass (§8 of the
  report, n/a this pass).
- **Non-isotropic / OOD.** Garg Fig 4a (skewed covariance) — the trained model plateaus rather
  than tracking LS; the H9 study is isotropic-Gaussian only.

## Acceptance

A mechanistic-probing pass connects the behavioral OLS-match to an internal computation (or
documents that the small model does not admit a clean GD/ridge readout); a two-head-softmax run
reproduces the single-fails/two-recovers contrast; a Garg-scale run tightens H9-B toward the
published figure — or a documented reason each cannot be closed at commodity scale.

## Refs

- Study `docs/h9-algorithmic-icl-study.md`; code `implementation/icl_regression/`.
- Plan `plans/2026-07-04-h9-algorithmic-icl.md`; decision `decisions/2026-07-01-03` (H9 fold-in).
- Appendix note `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.23.
- Sources [94] von Oswald, [95] Garg, [96] Akyürek, [97] Dai (all `download/`, `local:` tags).
