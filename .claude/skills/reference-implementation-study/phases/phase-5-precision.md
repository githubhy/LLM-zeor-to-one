# Phase 5: Reduced-Precision / Resource-Constrained Realisation

**Skip this phase** if the study domain is purely full-precision, train/eval-only, or the user says to skip.

## Goal
Map candidates to realisation structures and evaluate precision robustness.

## Realisation Structures (domain-dependent)
- Quantization scheme: INT8 / INT4 / FP8 / NF4; per-tensor vs per-channel vs per-group/block scales; symmetric vs asymmetric
- Quantization method: round-to-nearest (RTN), GPTQ, AWQ; post-training (PTQ) vs quantization-aware training (QAT)
- Sparsity / pruning: structured (2:4) vs unstructured; magnitude vs Wanda
- KV-cache precision: FP16 vs INT8 / INT4 KV-cache
- Low-rank realisation: LoRA / adapter rank and placement; weight-only vs weight+activation

## Constraints
- Sweep bit-width (or equivalent precision knob) with saturation-aware (clipping-aware) quantization.
- Compare which structure degrades most gracefully.

## Artifacts
Precision-study artifacts under `artifacts/<study>/`. Append realisation findings to study doc.

## Gate G4
Precision artifacts exist; bit-width sweep data loadable; manifest updated.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P2-3` is active, read `addenda/phase-5.md` and apply the active blocks (P2-3 reduced-precision DoE). In `original` mode, skip — do not read it.
