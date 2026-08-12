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

## Evaluation-independence sub-pass `[opt:RIS-EVAL-INDEPENDENCE · default ON · toggle .claude/skill-options.json]`

Standing (default-ON) discipline; skip only if the registry sets it `off`. The same independence extension as Phase 3, applied to the finite-precision numbers. Each load-bearing precision result (a wordlength knee, a float-vs-fixed gap, a quantizer/reconstruction ranking) gets, before G4 sign-off:

1. **An independent oracle** (`[opt:ME-INDEPENDENCE-AUDIT]`) sharing neither code nor assumption with the fixed-point implementation — e.g. a from-first-principles bound, a brute-force enumeration, or a separately-coded reference — not the same kernel re-run. Symmetry, tie-breaking, and saturation conventions are load-bearing *assumptions* to list, not incidentals: a quantizer that silently breaks odd symmetry inflated a hand-rolled MI estimator by 0.0045 bit and made a *proven-optimal* DP look wrong (bug 2026-07-10-25; the DP was innocent — settled only by a brute-force route sharing no code).
2. **The degenerate-case test** (`[opt:ME-ADVERSARIAL-METRIC]`) on the precision metric (a trivial fixed-point config that clears the metric without decoding).

A precision number confirmed only by an oracle built from the same math, or a metric a triviality satisfies, **fails** the sub-pass; record it in Report Section 5. *Off-behavior:* pre-2026-07-11, precision numbers are trusted via the wordlength sweep and a same-code oracle.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P2-3` is active, read `addenda/phase-5.md` and apply the active blocks (P2-3 reduced-precision DoE). In `original` mode, skip — do not read it.
