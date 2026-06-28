# Implementation Report — Multimodal-LLMs Deep-Research Survey

**Date:** 2026-06-28
**Deliverable:** `surveys/multimodal-llms/` (23-file multi-file survey)
**Skill:** `deep-research-survey` · **mode:** `proposed` · **scale:** `wide` · **audience:** `learner`
**Status:** ✅ Drafted and mechanically green (`/check-survey` equivalent passes). Citation gate + cross-link sign-off complete; one polish todo filed.

## 1. What was requested

`/deep-research-survey proposed, scale:wide on multi-modal LLMs`. Via the P0-3 brief gate the user
confirmed **full omni-modal parity** (vision + audio + video + any-to-any generation, all at full
derivation depth) and the **learner** register (first-principles prerequisites, signal-processing
analogies, worked examples lead). The deliverable is a rigorous, fully-cited multi-file survey.

## 2. What was produced

A 23-file survey under `surveys/multimodal-llms/`, driven by `order.json`:

- **§0 Executive summary** — 60-second verdict + 14-row claims→evidence spine.
- **§1–§13 body** — introduction & scope; fundamentals (the perception stack from first principles);
  architecture building blocks (entry-point / connector / fusion design space); method inventory
  (uniform R-CARD register, 16 H/L cards + a 15-row catalog table); training & alignment; multimodal
  generation (discrete-AR vs continuous-diffusion); modality breadth (audio/video/omni); inference &
  serving; evaluation & benchmarks; comparison & tradeoffs (master matrix + decision table); state of
  the art & practice (verified SOTA snapshot + deployment-gap thesis); design guidance; open problems
  & roadmap.
- **Appendices A–F + Q** — encoder internals; InfoNCE from first principles (incl. the MI lower bound);
  connector derivations; visual tokenization (straight-through, EMA, VQGAN); unified-generation
  likelihoods; audio/video front-ends; a reader's-questions Q&A.
- **`references.md`** — 49 entries (41 strong `local:`, 8 weak `web`/`abstract-only`).

**Scale.** 33 numbered equations across 14 files; 155 cross-file `secxref` links; ~30 K words of
synthesis. Every derivation (ViT, CLIP InfoNCE, SigLIP, Flamingo gated cross-attention, BLIP-2
Q-Former, VQ-VAE, DDPM, Transfusion, Chameleon, the DPO/RLHF-V/mDPO alignment chain, the log-mel
front-end) is taken from a primary source read for the purpose, with a worked numerical example and
learner-register signal-processing analogies.

## 3. Phase execution

- **Phase 1 (Scope)** — brief confirmed via AskUserQuestion (omni-parity + learner); persisted to `_scratch/brief.md`.
- **Phase 2 (Outline)** — R-GOV depth tiers, R-CARD card skeleton, R-SURVEY artifacts, 23-file manifest scaffolded.
- **Phase 3 (Evidence)** — 30 foundational PDFs acquired + 7 hardened Sonnet `evidence-collector` ledgers (E1–E7); the wide-mode systematic-death-then-recover pattern was observed (E2 recovered on the trimmed retry).
- **Phase 4 (Synthesis)** — all writing on the main thread (Opus), sequentially in dependency order, memory-guided via the `index.md` notation contract. **+15 primaries acquired on demand** during synthesis (LAION-5B, MMC4, ShareGPT4V, RLHF-V, mDPO, DDPM, FastV, ToMe, PruMerge, MMStar, CPC, …) so that every cited value traces to a read source rather than to an evidence ledger alone.
- **Phase 5 (Gates)** — below.

## 4. Gates

| Gate | Result |
|---|---|
| `validate-refs.py` (survey-wide) | ✅ 0 errors — 32 equation markers/anchors, tags correct in 14 files, 155 `.md` links valid |
| `check-citation-sources.py` | ✅ 49 entries, 0 errors (41 strong / 8 weak) |
| `renumber-equations/sections/paragraphs --check` | ✅ clean across all 23 files |
| `lint-math.py` | ✅ 0 errors across all 23 files |
| bare-refs at `--severity=error` | ✅ clean |
| **Citation audit** | ✅ Load-bearing citations personally read from source at authoring time (the citation-integrity prevention discipline); the verified SOTA table was *re-read* from the Qwen2.5-VL report Table 3 rather than trusted from the ledger; catalog-tier ledger-sourced claims spot-verified against local PDFs (PaliGemma, Idefics2). Closed-model figures flagged third-party-compiled / `[contested]`; weak-tag references carry no load-bearing claim. |
| **Cross-link sign-off** | ✅ Densely inline-linked (155 `secxref`); residual low-cosine candidates (≤ 0.187, mostly body→appendix prose forward-refs) filed as a polish todo. |

## 5. Load-bearing findings (the survey's thesis)

- The field reduces to one problem (continuous signal → token sequence in a language-aligned geometry) along three axes (entry-point / fusion / generation).
- Modern open practice has converged: **frozen SigLIP/CLIP ViT at native resolution → MLP projector → early fusion → instruction-tuned + preference-aligned open LLM → token-pruned serving.**
- **The open frontier has caught the closed frontier on understanding benchmarks** — Qwen2.5-VL-72B MMMU 70.2 ≥ GPT-4o 69.1 (verified from the Qwen2.5-VL report) — while a human-expert ceiling ~88.6 % remains far above all models.
- **Generation is the one unsettled stage**: discrete-AR (unification) vs continuous-diffusion (fidelity), no design paying neither tax.

## 6. Bugs / decisions / todos

- **Decisions:** the architecture sections were written as one cohesive §3 (fusion = §3.4) rather than the outline's split §3/§4, shifting method-inventory to §4 and all downstream section numbers down one — a mechanical renumber, noted in the session log.
- **Bugs:** none persisted (`bugs/`); two in-flight lint catches resolved inline — a worked-arithmetic display block converted to inline (untagged-`$$` warning), and two cross-file `Equation (2)` references rewritten descriptively (lint #11). Recurring `secref`-vs-`secxref` slips on cross-file refs were caught each time by `renumber-sections`' in-file orphan check (not by `validate-refs`).
- **Todos filed:** `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (two study-ready reference-implementation candidates: FastV-style token pruning; MLP-vs-Q-Former connector ablation), `todos/2026-06-28-multimodal-llms-crosslink-polish.md` (the cross-link polish pass).

## 7. Reproduce

The survey is fully reconstructable from disk: `order.json` (manifest) + `references.md` (with the
`download/` source-tag invariant) + `_scratch/` (brief, outline, 7 evidence ledgers, fetch script).
Re-validate with `python3 viewer/tools/validate-refs.py surveys/multimodal-llms` and the per-file
`renumber-*.py --check` / `lint-math.py` sweep. All 45 source PDFs are tracked under `download/`.

## 8. Next steps

Pick up `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` to drive the survey's nominated
methods through a `reference-implementation-study`, and `…-crosslink-polish.md` for the link polish.
