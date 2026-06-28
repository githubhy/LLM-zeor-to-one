---
slug: multimodal-llms-reference-impl-handoff
date_filed: 2026-06-28
status: open
---

# Multimodal-LLMs survey → reference-implementation study handoff

## Context
The `surveys/multimodal-llms/` deep-research survey (mode: proposed, scale: wide,
audience: learner) names two study-ready methods in its §13.2 roadmap
(`open-problems-and-roadmap.md`). Per the Todo Capture convention, a survey roadmap /
reference-implementation-study target must be tracked in `todos/` even though no one
asked to defer it. These are the nominated downstream `reference-implementation-study`
candidates, each with a baseline-to-beat and a falsifiable predicted margin.

## What is left
Two candidate reference-implementation studies (run via the `reference-implementation-study`
skill), in priority order:

1. **Vision-token pruning, reproduced and stress-tested.**
   - Baseline: an instruction-tuned early-fusion VLM (LLaVA-1.5-class) at full visual-token count.
   - Intervention: attention-ranked LLM-side pruning (FastV-style, survey §8.2; ref [45]).
   - Predicted margin: ~45% prefill-FLOP reduction at <1-point drop on a document/VQA suite,
     with a sharp accuracy knee past a task-dependent prune fraction.
   - Why first: plug-and-play (no retraining), quantitative/falsifiable prediction, and the
     FlashAttention-incompatibility caveat makes the systems-vs-accuracy tradeoff a real experiment.

2. **Connector ablation at matched budget.**
   - Baseline: a Q-Former bridge (BLIP-2-class, 32 tokens; ref [4]).
   - Intervention: an MLP projector at matched/larger token budget.
   - Predicted margin: projector wins on detail-sensitive tasks (DocVQA, TextVQA) at higher token
     cost — quantifying the §3.3 fidelity-vs-budget tradeoff the survey argued qualitatively.

## Acceptance
A `reference-implementation-study` is run on at least candidate (1): reference implementation +
comparative evaluation + sensitivity analysis + reduced-precision realization + engineering
recommendation, with a Phase-6 report under `reports/` passing the REPORT/CITE gates, and the
predicted margin confirmed or refuted with CIs.

## Refs
- `surveys/multimodal-llms/open-problems-and-roadmap.md` §13.2 (the handoff)
- `surveys/multimodal-llms/inference-and-serving.md` §8.2 (FastV mechanism), references [45] FastV, [4] BLIP-2
- survey commit series (§1–§13), session log `prompts/2026-06-28-multimodal-llms-survey.md`
