# Evidence Ledger E7 — Catalog-tier multimodal models & connector breadth
<!-- generated 2026-06-28 -->

## Q1 — Fuyu-8B and LLaVA-NeXT (AnyRes)

### Fuyu-8B: decoder-only, raw patch token projection
- **value/result**: Decoder-only transformer (no separate image encoder); image patches are linearly projected directly into the first layer of the transformer alongside text tokens, with a special image-newline character to mark row boundaries. No positional embeddings on images → arbitrary resolution at inference.
- **condition**: Adept AI release (Oct 2023), 8B parameters; designed for GUI/agent tasks
- **source**: Bavishi et al. (Adept AI), "Fuyu-8B: A Multimodal Architecture for AI Agents," 2023, https://www.adept.ai/blog/fuyu-8b/ · **tier**: B · **confidence**: high
- **connector type**: linear projection (image patch → LLM embedding space), no separate encoder, no Q-Former

### LLaVA-NeXT: AnyRes dynamic tiling for high-resolution
- **value/result**: Extends LLaVA-1.5 by tiling high-resolution images into a dynamic grid (up to 2×2 or rectangular variants: 1×{2,3,4}, {2,3,4}×1), encoding each tile plus a downsampled global view through CLIP/SigLIP ViT; all tile tokens are concatenated and fed to the LLM, increasing effective pixel budget 4× over LLaVA-1.5 (up to 672×672, 336×1344, or 1344×336).
- **condition**: January 2024 blog release; architecture uses vision encoder + 2-layer MLP connector + LLaMA/Mistral LLM backbone
- **source**: Liu et al., "LLaVA-NeXT: Improved reasoning, OCR, and world knowledge," blog post 2024-01-30, https://llava-vl.github.io/blog/2024-01-30-llava-next/ · **tier**: B · **confidence**: high
- **connector type**: MLP projector (2-layer); fully autoregressive; tile tokens concatenated into single sequence

## Q2 — CogVLM, MiniGPT-4, mPLUG-Owl

### CogVLM: visual expert modules per transformer layer
- **value/result**: Adds a parallel "visual expert" to every attention and FFN layer of the frozen LLM (Vicuna-7B backbone + EVA2-CLIP-E encoder); the expert carries its own QKV matrices and MLP weights (6.5B extra params) so visual and language tokens attend through separate weight paths inside the same layer — deep fusion without degrading NLP performance.
- **condition**: arxiv 2311.03079, 2023; 17B total parameters (6.5B expert + 10.5B base)
- **source**: Wang et al., "CogVLM: Visual Expert for Pretrained Language Models," arXiv:2311.03079, 2023, https://arxiv.org/abs/2311.03079 · **tier**: A · **confidence**: high
- **connector type**: per-layer visual expert (new QKV+MLP); 2-layer MLP adapter for initial vision→LLM projection; fully autoregressive

### MiniGPT-4: single linear projection aligning frozen encoders
- **value/result**: Aligns a frozen BLIP-2 ViT+Q-Former visual encoder with a frozen Vicuna LLM through a single linear projection layer; minimal trainable parameters; two-stage training (large-scale pretraining then curated instruction tuning).
- **condition**: arxiv 2304.10592, April 2023
- **source**: Zhu et al., "MiniGPT-4: Enhancing Vision-Language Understanding with Advanced Large Language Models," arXiv:2304.10592, 2023, https://arxiv.org/pdf/2304.10592 · **tier**: A · **confidence**: high
- **connector type**: single linear projection; frozen encoder + frozen LLM; Q-Former inherited from BLIP-2

### mPLUG-Owl: modular visual abstractor with two-stage training
- **value/result**: Introduces a "visual abstractor" module (a learned cross-attention pooling layer) between the frozen CLIP-like vision encoder and the LLM; stage-1 trains image-text alignment with the LLM frozen; stage-2 joint instruction tuning unfreezes the visual abstractor and low-rank LLM adapters, enabling both visual knowledge and instruction-following.
- **condition**: arxiv 2304.14178, April 2023
- **source**: Ye et al., "mPLUG-Owl: Modularization Empowers Large Language Models with Multimodality," arXiv:2304.14178, 2023, https://arxiv.org/pdf/2304.14178 · **tier**: A · **confidence**: high
- **connector type**: visual abstractor (cross-attention pooling); two-stage training separating alignment from instruction tuning

## Q3 — Idefics2, PaliGemma, DeepSeek-VL2

### Idefics2: fully autoregressive with pooled visual tokens, ablated architecture choice
- **value/result**: 8B-parameter VLM (SigLIP-SO400M encoder + Mistral-7B LLM) using a fully autoregressive architecture — vision features from the encoder are projected and pooled to 64 visual tokens via a Perceiver-style learned pooling, then concatenated with text tokens and fed to the LLM; supports images up to 980×980. Paper conducts the first proper ablation showing fully autoregressive + LoRA (69.5 avg) outperforms cross-attention frozen (66.7) despite the cross-attention design being used in earlier IDEFICS/Flamingo.
- **condition**: Laurençon et al. 2024, "What matters when building vision-language models?" (local: download/laurencon-idefics2-2024.pdf), pages 0–3; avg score on 4 benchmarks
- **source**: Laurençon et al., "What matters when building vision-language models?" (Idefics2), arXiv:2405.02246, 2024 · **tier**: A · **confidence**: high (read from local PDF)
- **connector type**: modality projection MLP + learned pooling (64 tokens); fully autoregressive concatenation

### PaliGemma: SigLIP encoder → linear projection → Gemma-2B decoder with prefix-LM masking
- **value/result**: 3B total (SigLIP-So400m 400M + Gemma-2B); images resized to fixed square (224/448/896 px → 256/1024/4096 tokens); a zero-initialized linear layer maps vision tokens into Gemma's embedding dimension — MLPs gave no advantage (Section 5.5 ablation); tokens ordered as [image tokens, BOS, prefix, SEP, suffix, EOS]; full bidirectional attention over image+prefix (prefix-LM), autoregressive on suffix only; positioned as a transfer base model (not instruction-tuned).
- **condition**: Beyer et al. 2024, local PDF download/beyer-paligemma-2024.pdf, pages 0–3; "versatile 3B VLM for transfer"
- **source**: Beyer et al., "PaliGemma: A versatile 3B VLM for transfer," arXiv:2407.07726, July 2024 · **tier**: A · **confidence**: high (read from local PDF)
- **connector type**: linear projection (zero-initialized); fully autoregressive decoder with prefix-LM masking on image+prefix

### DeepSeek-VL2: MoE LLM + dynamic tiling + MLA attention
- **value/result**: Three-module architecture: SigLIP-SO400M-384 vision encoder + vision-language adaptor + DeepSeekMoE LLM backbone (with Multi-head Latent Attention that compresses KV cache into latent vectors); dynamic tiling strategy splits high-resolution images into 384×384 tiles of varying aspect ratio; three model sizes (1.0B / 2.8B / 4.5B activated parameters in Tiny/Small/base).
- **condition**: arXiv 2412.10302, December 2024
- **source**: DeepSeek-AI, "DeepSeek-VL2: Mixture-of-Experts Vision-Language Models for Advanced Multimodal Understanding," arXiv:2412.10302, 2024, https://arxiv.org/abs/2412.10302 · **tier**: A · **confidence**: high
- **connector type**: vision-language adaptor (LLaVA-style MLP); MoE LLM with MLA; dynamic tiling for multi-resolution

## Q4 — Video-LLaMA and VideoLLaMA 2

### Video-LLaMA: dual VL+AL branch with Q-Former for temporal and audio fusion
- **value/result**: Built on BLIP-2/MiniGPT-4; adds (1) a Video Q-Former that aggregates frame features with learnable positional embeddings across T frames into a fixed-length visual sequence, and (2) an Audio-Language branch using ImageBind as the audio encoder plus an Audio Q-Former that similarly compresses M×2-second audio clips into fixed-length audio tokens; both branches project into the frozen LLM's input space — first multimodal model to jointly handle visual+audio from video.
- **condition**: EMNLP 2023 Demo; arXiv:2306.02858; instruction-tuned on video-text pairs
- **source**: Zhang et al., "Video-LLaMA: An Instruction-tuned Audio-Visual Language Model for Video Understanding," EMNLP 2023 Demo, arXiv:2306.02858, https://arxiv.org/abs/2306.02858 · **tier**: A · **confidence**: high
- **connector type**: Video Q-Former (temporal aggregation over frames) + Audio Q-Former (ImageBind encoder); dual-branch projection into frozen LLM

### VideoLLaMA 2: spatial-temporal convolution connector for video
- **value/result**: Successor to Video-LLaMA; replaces the Q-Former temporal aggregator with a Spatial-Temporal Convolution (STC) connector that applies 3D convolutions over the frame token grid to capture local spatial-temporal correlations while compressing sequence length; also improves audio understanding; shows that convolution-based pooling outperforms Q-Former-style attention pooling for dense video tasks.
- **condition**: arXiv:2406.07476, June 2024
- **source**: Cheng et al., "VideoLLaMA 2: Advancing Spatial-Temporal Modeling and Audio Understanding in Video-LLMs," arXiv:2406.07476, 2024, https://arxiv.org/pdf/2406.07476 · **tier**: A · **confidence**: high
- **connector type**: Spatial-Temporal Convolution (STC) connector; 3D-conv pooling over frame-token grid; replaces Q-Former

