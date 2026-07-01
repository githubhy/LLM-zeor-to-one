# Implementation Report — Mechanistic Interpretability Survey

**Date:** 2026-07-01 · **Branch:** `survey/mechanistic-interpretability` · **Skill:** `deep-research-survey`
**Config:** mode `proposed` (all P-items + all R-* richness) · scale `wide` · audience `practitioner` · depth `balanced` · breadth `toy→frontier+vision-roots`

## 0. Executive summary

Produced a complete, mechanically-validated multi-file survey of mechanistic interpretability
under `surveys/mechanistic-interpretability/` — **24 files, ~25.4k words, 36 numbered equations,
81 references** (63 strong `local:` + 18 `web`). `/check-survey` is green on all 8 checks; a
targeted citation-audit verified load-bearing numerics against the acquired PDFs and corrected two
secondary-source value drifts. The survey covers the full method inventory across the requested
"various models" spine (toy → GPT-2 → Pythia → Gemma 2 → Claude 3, with vision roots) and lands the
field's current inflection — the 2024–25 SAE reckoning and the pivot to transcoders / attribution
graphs — as its headline SOTA finding.

## 1. Deliverable

| Block | Files | Depth (R-GOV) |
|---|---|---|
| Front matter | index (notation contract, depth legend), executive-summary (claims→evidence spine), introduction-and-scope | — |
| Fundamentals | fundamentals | headline (residual stream, QK/OV, LRH, superposition) |
| Method inventory | methodology-and-taxonomy + 5 R-CARD files (observational / causal / dictionary / steering-editing / automation) | headline: activation patching, SAEs, attribution graphs; load-bearing: lenses, ACDC/EAP, DAS, ROME, steering, transcoders; catalog: probing/SAE micro-variants |
| Analysis | circuits-across-models, evaluation-and-metrics, comparison-and-tradeoffs, state-of-the-art-and-practice, applications, design-guidance, open-problems-and-roadmap | mixed |
| Appendices | A transformer-circuits math · B superposition + grokking · C causal interventions · D SAE derivations · E steering/editing math · Q reader Q&A | headline derivations |
| References | references (81 entries, source-tag invariant) | — |

**R-SURVEY artifacts delivered:** notation contract (front matter); §11.1 master comparison matrix
(20 methods × 7 axes) + §11.2 selection/decision table; §12.3 quantitative SOTA suite table (Gemma
Scope / OpenAI GPT-4 SAE / Claude 3) with disclosed conditions + normalization caveat; §15 open
problems in {known/unknown/why/state-of-attack} form + RIS handoff; Appendix Q reader Q&A (8 items,
proactive `survey-explainer-fold` seeds). Full first-principles derivations for every headline /
load-bearing method (ROME Lagrangian rank-one, superposition phase diagram + feature-dimensionality,
grokking Fourier readout, SAE L1-shrinkage soft-threshold + JumpReLU STE, attribution-graph local
replacement model).

## 2. Phase telemetry

- **Phase 3 — evidence** (`wf_8d9c6b10-882`): 14 hardened Sonnet clusters, ~47 research questions,
  file-first `_scratch/ev-*.md`. **14/14 alive, 0 dead**; `evaluation` cluster died once
  (API-Overloaded) and **recovered at retry attempt-1** — the bounded-escalating-retry safety net
  fired as designed. 15 agents, 1.30M tokens, 320 tool-uses, ~10.4 min. Restart-intensity ceiling
  not hit; no main-thread fallback; no coverage-gap markers required.
- **Acquisition** (`source-fetch` / `oa_fetch.py`): **63/63 arXiv PDFs into `download/`, 0 failures**
  (58 corpus + 4 supplementary + Marks); 18 web-native sources (transformer-circuits.pub / distill /
  lab blogs / alignment forum) tagged `(web)`. The `references.md ↔ download/` invariant holds
  (check-citation-sources: 63 `local:` files all present on disk).
- **Phase 4 — synthesis:** main-thread only (no agent delegation of writing, per skill rule). All
  24 files authored with math-authoring marker discipline inline.
- **Phase 5 — gates + citation-audit** (`wf_f9750bd8-8f4`): below.

## 3. Mechanical gate — `/check-survey` GREEN

lint-math (0 errors) · renumber-equations (36 tags sequential) · link-references (0 orphaned / 0
uncited) · renumber-paragraphs (clean) · renumber-sections (0 orphaned secref/secxref, 218 valid
cross-file links) · validate-refs (0 errors / 0 warnings) · bare-refs `--severity=error` (PASS) ·
check-citation-sources (81 entries, 63 strong / 18 weak, 0 errors).

Fixes landed to reach green: 6 `secref→secxref` (cross-file), 3 cite-at-line-start joins
(wrapped-framing-paragraph hazard), 1 stray paragraph anchor, a `>99%`→"over 99%"
spurious-blockquote, and 3 uncited-reference wirings (incl. the DAS primary [43], a genuine
content miss).

## 4. Citation-audit (Phase-5 gate)

10 Sonnet verifiers over the highest-risk load-bearing numerics vs. acquired local PDFs; **25
checks — 21 verified (MATCH/CLOSE), 2 corrected, 1 false alarm, 1 workflow lesson.**

| Source | Result |
|---|---|
| Gao TopK scaling-law constants (Eq.3), 16M/7%-dead/40B, n^0.6/0.65 | MATCH ×3 |
| Hase R²=0.585, +0.03 localization critique | MATCH ×2 |
| Gemma Scope >400 SAEs / >30M feats / JumpReLU / token budgets | MATCH ×5 |
| Wang IOI 26 heads / 7 classes / F(M)=3.56 | MATCH ×2 |
| Meng MEMIT ~10,000 edits / layers {3–8} | MATCH ×2 |
| Gupta ~1,400-edit forgetting onset / ~3× fewer than ROME | MATCH ×2 |
| Miller faithfulness >50-pt swing / ~150% edge-ablation | CLOSE ×2 |
| **Meng ROME AIE attribution** | **MISMATCH → corrected** (8.7% is individual-state peak; MLP is 6.6%, attention 1.6%) |
| **Zou RepE LoRRA deltas** | **MISMATCH → corrected** (+11.3/+11.6 pp, not +6.6/+13.1) |
| Arditi refusal (13 models / 72B) | NOT_FOUND → **false alarm** (shared-`/tmp` verifier race; file re-confirmed correct in-process) |

Both corrections were values the Phase-3 evidence ledger had **already flagged** as secondary-sourced
— the flag-then-audit discipline worked end-to-end. Details: `bugs/2026-07-01-01`. Weak-form (`web`)
load-bearing claims that cannot be locally verified (MacDiarmid >99% AUROC; Chughtai RMU-shallow
71%/45%; Templeton 34M/~12M-alive; Amodei 5–10 yr) are attributed to their `(web)` primaries and
noted as such at point of use.

## 5. Records filed

- **bugs/** `2026-07-01-01` — the two citation-value drifts (med, fixed).
- **field-notes/** `2026-07-01-mechinterp-survey` — wrapped-paragraph hazard, `>`-blockquote
  hazard, citation-audit shared-temp-file race (per-agent scratch isolation lesson).
- **todos/** `2026-07-01-mechinterp-ris-handoff` (3 study-ready reproduction candidates → RIS);
  `2026-07-01-mechinterp-crosslink-polish` (19 advisory link candidates above 218 existing).
- No `decisions/` entry: scope choices (register/depth/breadth) were user-made via the P0-3 gate,
  not autonomous judgment calls; file layout followed the `multimodal-llms` precedent.

## 6. Coverage & residuals

Coverage-gap (MAST specification) check: every must-have research question in `_scratch/outline.md`
is represented; all MI taxonomy axes have a home; out-of-scope LLM axes (pretraining, serving,
agents) are cross-linked, not silently dropped. **Residual not closed:** at `scale: wide`
(searches=40, above the ~28 measured death boundary) the residual risk is an "alive-but-shallow"
return — mitigated here by 0 dead clusters and the citation-audit, not eliminated. The cross-link
polish and the RIS reproduction studies are the two tracked follow-ons.

## Footer

**Active config:** `deep-research-survey` · mode `proposed` · scale `wide` · audience `practitioner`
· depth `balanced` · breadth `toy→frontier+vision-roots`. **Safety-net invariants (all ON):**
checkpoint-writes, event-driven death detection + retry (`max_retries=2`, 1 recovery used),
structured-output schemas, main-thread synthesis, citation-integrity gate, restart-intensity ceiling.
**Retry telemetry:** evidence — 14 clusters, 1 death (evaluation), 1 recovery @ attempt-1, 0
trimmed, 0 main-thread fallbacks. Not committed — pending sign-off.
