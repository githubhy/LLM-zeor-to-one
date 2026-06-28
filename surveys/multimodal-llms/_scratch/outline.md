# Phase-2 Outline — Multimodal LLMs survey

Mode: proposed · scale: wide · audience: learner · response mode: Survey.
Depth tiers (R-GOV): **H** = headline (full derivation + worked example + figure), **L** = load-bearing
(derivation + intuition + complexity), **C** = catalog-only (stated result + applicability + explicit n/a).
Learner register pins all fundamentals at **H**. Coverage is scored as a fraction over H+L items (R-RUBRIC),
never prose volume.

Per-section research questions are tagged **[MH]** must-have (blocks the section) or **[NH]** nice-to-have.

## File architecture (order.json manifest, mirrors llms-for-coding)

1. `index.md` — front matter: title, abstract, reading guide, depth-tier legend, **NOTATION CONTRACT** (R-SURVEY).
2. `executive-summary.md` — 60-second verdict + claims→evidence spine.
3. `introduction-and-scope.md` — §1.
4. `fundamentals.md` — §2 (may split if > 200 KB wide threshold).
5. `architecture-building-blocks.md` — §3 (connectors) + §4 (fusion).
6. `method-inventory.md` — §5 R-CARD model-family cards (may split by modality).
7. `training-and-alignment.md` — §6.
8. `multimodal-generation.md` — §7 any-to-any generation.
9. `modality-breadth.md` — §8 video / audio / omni.
10. `inference-and-serving.md` — §9.
11. `evaluation-and-benchmarks.md` — §10.
12. `comparison-and-tradeoffs.md` — §11 master comparison matrix (R-SURVEY).
13. `state-of-the-art-and-practice.md` — §12 quantitative SOTA + deployment-gap thesis (R-SURVEY).
14. `design-guidance.md` — §13.
15. `open-problems-and-roadmap.md` — §14 + reference-implementation handoff (R-SURVEY).
16. `appendix-a-vit-and-encoders.md` — ViT patch-embed + attention; CLIP/SigLIP encoder internals.
17. `appendix-b-contrastive-infonce.md` — CLIP InfoNCE derivation from first principles.
18. `appendix-c-connector-derivations.md` — Q-Former objectives; Flamingo gated cross-attention; perceiver resampler.
19. `appendix-d-visual-tokenization.md` — VQ-VAE / VQGAN, straight-through estimator, codebook losses.
20. `appendix-e-unified-generation.md` — Chameleon AR mixed-modal; Transfusion AR+diffusion joint loss; Janus decoupling.
21. `appendix-f-audio-video.md` — audio front-ends (mel, Whisper encoder); video temporal sampling/pooling.
22. `appendix-q-reader-questions.md` — Q&A appendix (R-SURVEY; wires survey-explainer-fold).
23. `references.md` — single reference list, source-tag invariant.

## Section detail

### index.md — Front matter
- Title, abstract (≤200 words), reading guide, depth-tier legend.
- **Notation contract** (R-SURVEY): symbol → meaning → units/convention → defining-section link. Symbols:
  image $x_v$, text tokens $x_t$, patch grid $P$, patch dim, ViT embedding $z$, vision encoder $f_v$,
  LLM $p_\theta$, connector $g_\phi$, contrastive temperature $\tau$, codebook $\mathcal{C}$, etc.

### §1 Introduction & scope  (introduction-and-scope.md)
- RQ1.1 [MH] What precisely makes an LLM "multimodal" — perception vs generation vs both?
- RQ1.2 [MH] The three taxonomy axes: (a) where modalities enter (input/output), (b) how they fuse
  (deep cross-attention / early token-concat / native unified token), (c) what is generated (text-only /
  any-to-any). Tier: H (this taxonomy frames the whole survey).
- RQ1.3 [NH] Brief history: CLIP (2021) → Flamingo/BLIP-2 (2022) → LLaVA (2023) → native-token & omni (2024–25).

### §2 Fundamentals  (fundamentals.md) — all **H** (learner floor)
- RQ2.1 [MH] The tokenization problem: text is discrete, images/audio/video are continuous — how do we
  feed a continuous signal to a token-based transformer? (SP analogy: sampling + quantization of a
  continuous-time signal; embedding ≈ a learned filterbank.)
- RQ2.2 [MH] Vision encoders from first principles: ViT patch-embedding (conv-as-patchify), the encoder
  attention stack, [CLS] vs patch tokens. Derivation → appendix-a.
- RQ2.3 [MH] Contrastive alignment: the CLIP image-text InfoNCE objective, derived (why a shared embedding
  space; temperature; the symmetric loss). Derivation → appendix-b. SigLIP sigmoid variant.
- RQ2.4 [MH] Projecting non-text into LLM token space: what "a visual token in the LLM's embedding space"
  means; dimensionality match; why a frozen encoder + trained projector works.
- RQ2.5 [NH] Audio & video as signals: mel-spectrogram front-end (SP analogy: STFT), frames as a temporal
  sequence — set up §8.

### §3+§4 Architecture building blocks  (architecture-building-blocks.md)
- RQ3.1 [MH] Connector taxonomy. **MLP/linear projector** (LLaVA) [H], **Q-Former** (BLIP-2) [H],
  **perceiver resampler + gated cross-attention** (Flamingo) [H]. Each: mechanism, params, what it fixes.
- RQ3.2 [MH] Head-to-head: parameter count, training data efficiency, where each shines. → §11 matrix.
- RQ4.1 [MH] Fusion paradigms: **deep fusion** (cross-attention into frozen LLM, Flamingo) vs **early
  fusion** (project + concatenate into the token stream, LLaVA) vs **native/unified token** (image patches
  as first-class tokens, Fuyu; mixed-modal AR, Chameleon). Tier H. SP analogy: side-information injected at
  the mixer (deep) vs prepended to the sample stream (early).
- RQ4.2 [MH] Resolution handling: fixed-grid vs **AnyRes/tiling** (LLaVA-NeXT) vs **native resolution**
  (Qwen2-VL NaViT-style, M-RoPE). Token-budget cost of high-res. Tier L.

### §5 Method inventory  (method-inventory.md) — R-CARD uniform cards
Each card = 10 R-CARD elements (idea / in-context / derivation / intuition / limits / worked example /
complexity / failure modes / falsifiable+epistemic tag / eq-to-code). Tiers:
- **H** (full card): CLIP, ViT, LLaVA(-1.5), BLIP-2 (Q-Former), Flamingo (gated xattn), Chameleon
  (native mixed-modal), Transfusion (AR+diffusion), VQ-VAE/VQGAN.
- **L** (derivation+intuition+complexity): SigLIP, Qwen2-VL / Qwen2.5-VL (M-RoPE, native res), InternVL
  (vision scaling), Fuyu (decoder-only patch tokens), LLaVA-NeXT (AnyRes), Emu3 (next-token any-to-any),
  Whisper (audio encoder), Qwen-Audio, SALMONN.
- **C** (stated result + applicability + n/a): Idefics/Idefics2, Molmo/PixMo, Pixtral, NVLM, PaliGemma,
  MiniGPT-4, mPLUG-Owl, CogVLM, Video-LLaMA, Video-LLaVA, VideoChat, AudioPaLM, Janus/Janus-Pro,
  DeepSeek-VL, GPT-4V/4o, Gemini, Claude-vision (closed; card from technical reports, weak source tags).

### §6 Training & alignment  (training-and-alignment.md)
- RQ6.1 [MH] Pretraining objectives & data: image-text contrastive, captioning/next-token on
  interleaved image-text (MMC4, LAION), data curation & dedup. Tier H.
- RQ6.2 [MH] Visual instruction tuning: the LLaVA recipe (GPT-4-generated instruction data, two-stage
  align-then-finetune). Tier H. Worked example: a training step.
- RQ6.3 [MH] Multimodal alignment: RLHF/DPO for VLMs; **hallucination mitigation** (RLHF-V, POPE-driven).
  Tier L.
- RQ6.4 [NH] Freezing strategy: frozen vs unfrozen encoder/LLM, when each is used.

### §7 Multimodal generation (any-to-any)  (multimodal-generation.md)
- RQ7.1 [MH] Discrete visual tokenization: VQ-VAE / VQGAN, the codebook, straight-through estimator,
  commitment loss. Tier H. Derivation → appendix-d. SP analogy: vector quantization / codebook = a
  learned quantizer (like LBG/k-means in speech coding).
- RQ7.2 [MH] Autoregressive image+text generation: Chameleon (single transformer over mixed tokens),
  Emu3 (next-token prediction for everything). Tier H. → appendix-e.
- RQ7.3 [MH] Diffusion-LLM hybrids: Transfusion (one transformer, LM loss on text + diffusion loss on
  image patches), Janus (decoupled understanding/generation encoders). Tier H/L. → appendix-e.
- RQ7.4 [NH] Why discrete-AR vs continuous-diffusion for images — the central design tension.

### §8 Modality breadth  (modality-breadth.md) — omni-modal parity, **H/L**
- RQ8.1 [MH] Video LLMs: frame sampling, temporal pooling/compression, time encoding. Tier L. → appendix-f.
- RQ8.2 [MH] Audio/speech LLMs from first principles: audio encoder (Whisper), speech tokens, Qwen-Audio /
  SALMONN / AudioPaLM. Tier H/L. → appendix-f.
- RQ8.3 [MH] Omni / real-time: GPT-4o-style interleaved any-to-any, streaming, full-duplex speech. Tier L.

### §9 Inference & serving  (inference-and-serving.md)
- RQ9.1 [MH] The vision-token cost problem: a high-res image = thousands of tokens → prefill & KV-cache
  blow-up. Tier H. Worked example: token count for a 1344×1344 image at common patch settings.
- RQ9.2 [MH] Token compression/pruning: pooling, perceiver resampling, FastV-style pruning, token merging.
  Tier L.
- RQ9.3 [NH] KV-cache & batching implications specific to interleaved image-text.

### §10 Evaluation & benchmarks  (evaluation-and-benchmarks.md)
- RQ10.1 [MH] Benchmark inventory: MMMU, MMBench, MME, VQAv2, TextVQA, DocVQA, ChartQA, MathVista, AI2D;
  video (Video-MME, MVBench); audio. What each measures. Tier L.
- RQ10.2 [MH] Hallucination eval: POPE, CHAIR, object-hallucination. Tier L.
- RQ10.3 [MH] Pitfalls: contamination, prompt sensitivity, judge bias, single-image bias. Tier L.

### §11 Comparison & tradeoffs  (comparison-and-tradeoffs.md) — R-SURVEY §7
- RQ11.1 [MH] **Master comparison matrix**: rows = every H+L inventory method; columns = entry-point /
  fusion / connector / resolution / generation-capable / params / training-data + an **assumptions & cost**
  column (frozen vs trained, instruction-data volume, compute). Plus a **selection/decision table**
  (when to use / when not). Tier H (this is a load-bearing synthesis artifact).

### §12 SOTA & current practice  (state-of-the-art-and-practice.md) — R-SURVEY §8
- RQ12.1 [MH] **Quantitative SOTA table**: one row per published model/result, metric + eval conditions
  (benchmark, split, shots, decoding, scale) + source tag, normalization note when incomparable. Tier H.
- RQ12.2 [MH] Deployment-gap thesis: why early-fusion LLaVA-style dominates open practice; closed frontier
  (GPT-4o, Gemini, Claude) vs open (Qwen2.5-VL, InternVL2.5, Llama-3.2-V, Molmo, Pixtral). Tier H.
- RQ12.3 [MH] Per-stage dominant-practice map (encoder choice / connector / training / serving).

### §13 Design guidance  (design-guidance.md)
- RQ13.1 [MH] Decision framework: given a target (doc-VQA, video QA, any-to-any, edge), which encoder /
  connector / fusion / resolution / training recipe. Tier L.

### §14 Open problems & roadmap  (open-problems-and-roadmap.md) — R-SURVEY §10
- RQ14.1 [MH] Gaps as {question, known, unknown, why-it-matters, state-of-attack, plausible approach,
  candidate next step}: unified omni-modal at parity, long-video, fine-grained grounding, hallucination,
  vision-token efficiency, eval validity. Tier L.
- RQ14.2 [NH] Reference-implementation handoff: nominate 1–2 study-ready methods with baseline-to-beat +
  predicted margin (e.g. a token-compression scheme; a connector ablation) for a downstream
  reference-implementation-study.

### Appendices A–F — full derivations (co-located heavy math, R-CARD element 3)
- A: ViT patch-embedding + encoder attention; CLIP/SigLIP encoder internals.
- B: CLIP InfoNCE from cross-entropy first principles; temperature; symmetric loss; SigLIP sigmoid.
- C: Q-Former (ITC/ITM/ITG objectives); Flamingo perceiver resampler + gated tanh cross-attention.
- D: VQ-VAE/VQGAN, straight-through gradient, codebook + commitment losses, EMA codebook.
- E: Chameleon mixed-modal AR likelihood; Transfusion joint LM+diffusion loss; Janus decoupling.
- F: audio mel/Whisper encoder; video temporal sampling/pooling math.

### appendix-q-reader-questions.md — Q&A (R-SURVEY)
Pre-answer: "why a frozen vision encoder?", "why do high-res images cost so many tokens?", "discrete vs
continuous image generation — what breaks?", "why does early-fusion beat cross-attention in practice?",
"what is M-RoPE and why native resolution?". Wires survey-explainer-fold proactively.

## MAST coverage-gap check (P2-5, [specification])
Taxonomy axes covered: entry-point (§3/§4 ✓), fusion (§4 ✓), generation (§7 ✓). Dominant families all
homed: CLIP-encoder+MLP (LLaVA ✓), Q-Former (BLIP-2 ✓), Flamingo-xattn ✓, native-token (Fuyu/Chameleon ✓),
any-to-any (Emu3/Transfusion ✓), audio (Qwen-Audio/SALMONN ✓), video ✓, omni (GPT-4o ✓). Cross-survey:
fundamentals reuse the transformer/attention machinery — cross-link to surveys/llms-for-coding appendices
(QKV, attention) rather than re-deriving the base transformer. No taxonomy axis omitted.

## Acquisition list (Phase 3 seed — exact-title source-fetch targets)
CLIP (Radford 2021), ViT (Dosovitskiy 2020), SigLIP (Zhai 2023), Flamingo (Alayrac 2022),
BLIP-2 (Li 2023), LLaVA (Liu 2023), LLaVA-1.5 (Liu 2023b), LLaVA-NeXT, Qwen-VL (Bai 2023),
Qwen2-VL (Wang 2024), Qwen2.5-VL, InternVL (Chen 2023/2024), Fuyu-8B (Adept 2023), Chameleon (2024),
Emu3 (2024), Transfusion (Zhou 2024), Janus / Janus-Pro (2024/2025), Whisper (Radford 2022),
Qwen-Audio (2023), SALMONN (2024), AudioPaLM (2023), Video-LLaVA (2023), VQ-VAE (van den Oord 2017),
VQGAN (Esser 2021), MMMU (Yue 2023), POPE (Li 2023), Idefics2 (2024), Molmo/PixMo (2024),
Pixtral (2024), PaliGemma (2024), NVLM (2024), DeepSeek-VL (2024). (~35 targets; wide ≤200/day.)
