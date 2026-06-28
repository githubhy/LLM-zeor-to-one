# Research Brief (north star) — Multimodal LLMs

**Status:** ✅ CONFIRMED 2026-06-28 (P0-3 gate cleared). Scope = **full omni-modal parity**; register = **learner**.
**Mode:** proposed (all P-items + R-items) · **scale:** wide · **audience:** learner · **response mode:** Survey.

## Subject

A rigorous, first-principles deep-research survey of **multimodal large language models** — models that
extend a transformer language model to *perceive* and/or *generate* non-text modalities (image, video,
audio), spanning the encoder→connector→LLM stack, training recipes, any-to-any generation, evaluation,
SOTA practice, and open gaps.

## Audience / depth / register

- **Register:** `learner` (CONFIRMED) — derive DL/LLM prerequisites from first principles, lead with
  intuition + signal-processing analogies, worked examples first, define terms on first use, fundamentals
  at full depth. R-GOV pins the fundamentals floor at `headline` for this register.
- **Depth:** fundamentals and every load-bearing method derived from first principles; method inventory
  broad; tradeoffs quantified where sources permit (R-GOV depth-tier governs depth-per-concept).
- **Scope:** `full omni-modal parity` (CONFIRMED) — vision, audio, video, AND any-to-any generation each
  get full first-principles derivation depth; §6 (generation) and §7 (audio/video/omni) are promoted to
  **[M]** at full depth (not nice-to-have).

## Output contract

Multi-file survey under `surveys/multimodal-llms/` (driven by `order.json` + a single `references.md`),
mirroring the `llms-for-coding` layout: `index.md`, `executive-summary.md`, numbered body sections,
appendices for the heavy derivations, `figures/`. Fully cited (every external value traces to a
`download/` source per citation-integrity), authored to the math-authoring marker discipline inline,
green through `/check-survey` at sign-off.

## Source preferences

Primary papers (arXiv) + official model cards, acquired full-text via `source-fetch` into `download/`
(wide: ≤200/day, holdback 10–15). Core transformer/scaling papers already in `download/` are reused for
fundamentals. Frontier closed models (GPT-4o, Gemini, Claude) cited from system/technical cards (weak-tag
`web`/`abstract-only` where no full text exists; never load-bearing).

## Proposed section outline  (M = must-have, N = nice-to-have)

1. **Introduction & scope** — what "multimodal LLM" means; the three taxonomy axes (where modalities
   enter, how they fuse, what is generated). **[M]**
2. **Fundamentals** **[M]** — 2.1 the tokenization problem for continuous signals; 2.2 modality encoders
   (ViT, CLIP/SigLIP vision; Whisper-style audio) from first principles; 2.3 contrastive alignment (the
   CLIP InfoNCE objective, derived); 2.4 projecting non-text into LLM token space.
3. **Connector / adapter architectures** **[M]** — 3.1 linear/MLP projection (LLaVA); 3.2 Q-Former
   (BLIP-2); 3.3 perceiver resampler + gated cross-attention (Flamingo); 3.4 head-to-head: params, data
   efficiency, performance.
4. **Fusion paradigms** **[M]** — 4.1 deep fusion (cross-attention) vs early fusion (token concat);
   4.2 native/unified-token models (Fuyu, Chameleon); 4.3 resolution handling (AnyRes/tiling, native res).
5. **Training** **[M]** — 5.1 pretraining objectives & data (interleaved, captioning, contrastive);
   5.2 visual instruction tuning (the LLaVA recipe); 5.3 alignment: multimodal RLHF/DPO, hallucination
   mitigation.
6. **Any-to-any / multimodal generation** **[M]** — 6.1 discrete visual tokenization (VQ-VAE/VQGAN);
   6.2 autoregressive image generation (Chameleon, Emu3); 6.3 diffusion-LLM hybrids (Transfusion, Janus).
7. **Modality breadth beyond images** **[M]** (omni-modal parity) — 7.1 video LLMs (frame sampling,
   temporal modeling); 7.2 audio/speech LLMs (Qwen-Audio, SALMONN, AudioPaLM) from first principles;
   7.3 omni / real-time (GPT-4o-style streaming, interleaved any-to-any).
8. **Inference & serving** **[M]** — vision-token cost, token compression/pruning, KV-cache & prefill
   implications of image/video tokens.
9. **Evaluation & benchmarks** **[M]** — MMMU, MMBench, MME, VQAv2, TextVQA, DocVQA, ChartQA, MathVista,
   Video-MME; hallucination (POPE); contamination/eval pitfalls.
10. **State of the art & current practice** **[M]** — what is actually preferred (early-fusion LLaVA-style
    dominance, native resolution); open frontier (Qwen2.5-VL, InternVL, Llama-3.2-V, Molmo, Pixtral) vs
    closed (GPT-4o, Gemini, Claude).
11. **Roadmap & open gaps** **[M]** — unified omni-modal, long-video, fine-grained grounding, efficiency,
    hallucination, evaluation validity.
12. **Appendices** **[M for the ones backing §2–6]** — full derivations: ViT patch-embedding & attention;
    CLIP/InfoNCE; Q-Former/Flamingo cross-attention; VQ-VAE/straight-through; Transfusion's AR+diffusion loss.

## Exclusions (scope boundaries)

- Pure text-only LLMs (covered by sibling surveys); pure diffusion image generators (SD/DALL·E) except
  where fused into an LLM; contrastive embedders beyond their encoder role.
- Vision-Language-Action / embodied robotics (VLA) — noted as adjacent, not covered in depth.
- Pre-transformer classical multimodal ML; domain-specific MLLMs (medical, doc-AI verticals) beyond a
  mention.

## MAST coverage checkpoint (P2-5)

Outline coverage-gap check: every taxonomy axis (entry point / fusion / generation) and every dominant
production family (CLIP-encoder + MLP, Q-Former, Flamingo-xattn, native-token, any-to-any) has a home
section above. Gaps to confirm with the user: depth of generation (§6) and modality breadth (§7).
