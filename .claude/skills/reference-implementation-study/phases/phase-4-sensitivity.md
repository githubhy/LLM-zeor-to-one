# Phase 4: Sensitivity & Optimisation

## Goal
Sweep key hyperparameters and environmental variables to understand robustness.

## Constraints
- Per candidate, identify **2-4 key hyperparameters** (learning rate, batch size, model width d_model, depth L, heads h, context length, decoding temperature / top-p, regularisation weight — domain dependent).
- Sweep each on a grid while holding others at baseline.
- Optionally sweep environmental / data-distribution parameters (token/compute budget N·D, few-shot k, prompt format, context length, input difficulty).
- If a composite score is used, document the weight rationale inline.

## Artifacts
Sweep artifacts under `artifacts/<study>/`. Append sensitivity findings to the study doc.

## Gate G3
Sweep artifacts exist; at least one sweep per candidate; manifest updated.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-3, P1-1` is active, read `addenda/phase-4.md` and apply the active blocks (P0-3 global sensitivity, P1-1 Bayesian HPO). In `original` mode, skip — do not read it.
