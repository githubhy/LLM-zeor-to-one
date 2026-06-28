# Evidence Ledger — Cluster E4: Inference & Serving — Vision-Token Cost & Compression
<!-- created 2026-06-28 -->

---
## Q1 — Vision-Token Cost: How Many Tokens Does a High-Res Image Become?

### LLaVA-NeXT AnyRes token budget
- **value/result**: Standard CLIP encoder (ViT patch size 14×14, 336×336 input) produces 576 tokens per sub-image. AnyRes splits a high-res image into up to 6 patches (grid configs: {2×2, 1×{2,3,4}, {2,3,4}×1} + 1 thumbnail); a 5-patch configuration yields 5 × 576 = **2,880 visual tokens** per image; formula L = (a×b + 1) × T.
- **condition**: LLaVA-NeXT with CLIP ViT-L/14@336; default 5-patch AnyRes grid
- **source**: LLaVA-NeXT blog + LLaVA-OneVision arXiv:2408.03326 · **tier**: B · **confidence**: high

### Qwen2-VL dynamic resolution token range
- **value/result**: Qwen2-VL maps images at native resolution to a dynamic number of visual tokens. Default supported range is **4–16,384 tokens** per image; users can set min_pixels/max_pixels (e.g., 256–1,280 for speed/memory trade-off). Patches are 14×14 pixels merged in 2×2 groups (effective stride 28 px); approximate count for H×W image ≈ (H/28) × (W/28).
- **condition**: Qwen2-VL (arXiv:2409.12191); no fixed resolution; configurable range
- **source**: Qwen2-VL paper arXiv:2409.12191 + Qwen2-VL blog https://qwenlm.github.io/blog/qwen2-vl/ · **tier**: A · **confidence**: high

### BLIP-2 Q-Former baseline comparison (frozen ViT input size)
- **value/result**: With frozen ViT-L/14 encoder, the raw visual feature sequence is **257 tokens** (256 patch tokens + 1 [CLS]); Q-Former compresses these down to **32 output query tokens** (Z of size 32 × 768), a ~8× reduction before the LLM sees any visual content.
- **condition**: BLIP-2 with ViT-L/14; Q-Former with 32 learned queries; dimension 768
- **source**: Li et al., "BLIP-2," ICML 2023, local: download/li-blip2-2023.pdf, p. 3 · **tier**: A · **confidence**: high

---
## Q2 — Token-Compression / Pruning Methods

### FastV: attention-based visual token pruning (50% pruning → ~45% FLOP reduction)
- **value/result**: FastV prunes visual tokens after LLM layer 2 by ranking them via attention scores from the final query token. At K=2, R=50% (pruning 50% of visual tokens), it achieves **~45% FLOPs reduction** across LLaVA-1.5, QwenVL-Chat, Video-LLaVA while maintaining competitive performance; can compress a 13B model to 7B FLOP budget with higher accuracy than native 7B.
- **condition**: ECCV 2024 Oral; plug-and-play, no retraining; R=50%, K=2 ablation
- **source**: Chen et al., "An Image is Worth 1/2 Tokens After Layer 2," ECCV 2024, arXiv:2403.06764 · **tier**: A · **confidence**: high

### LLaVA-PruMerge: adaptive token reduction (~14.4× compression)
- **value/result**: PruMerge uses attention scores to select important visual tokens and clusters similar tokens via key-vector similarity to merge them. Reduces 576 LLaVA-1.5 visual tokens to ~40 tokens (**14.4× reduction**, 576/40 ≈ 14.4) on MME/TextVQA, matching text-prompt token count. Accelerates LLM prefill FLOPs proportionally to token reduction.
- **condition**: LLaVA-1.5; 576 input tokens; reported on MME and TextVQA benchmarks
- **source**: Shang et al., "LLaVA-PruMerge," arXiv:2403.15388, 2024 · **tier**: B · **confidence**: high

### ToMe: token merging for ViTs (2–3× speedup on vision encoder)
- **value/result**: ToMe merges similar tokens inside ViT blocks during inference using a bipartite soft matching algorithm on key vectors. Achieves **2–3× faster evaluation** on standard ViTs (e.g., DeiT, ViT-B/16) with minimal accuracy loss, without retraining. Training-free and composable with existing ViT checkpoints.
- **condition**: ICLR 2023; evaluated on ImageNet with DeiT/ViT; top-1 accuracy drop < 1% for 2× speedup
- **source**: Bolya et al., "Token Merging: Your ViT but Faster," ICLR 2023, arXiv:2210.09461 · **tier**: A · **confidence**: high

### BLIP-2 Q-Former as compressor (32 tokens from 257 → LLM)
- **value/result**: The Q-Former acts as an information bottleneck: 32 learned query embeddings cross-attend to frozen image features (257 tokens for ViT-L/14; 1,408 tokens for ViT-g/14) via cross-attention layers, outputting **32 visual tokens** that are projected and prepended to LLM input. This removes irrelevant visual information and reduces the LLM's vision-alignment burden; described as an "information bottleneck." Q-Former has 188M parameters (initialized from BERT-base).
- **condition**: BLIP-2 with ViT-L/14 or ViT-g/14; 32 queries, dim=768; ICML 2023
- **source**: Li et al., "BLIP-2," ICML 2023, local: download/li-blip2-2023.pdf, p. 3–4 · **tier**: A · **confidence**: high

### Flamingo Perceiver Resampler (64 fixed visual tokens from variable feature maps)
- **value/result**: The Perceiver Resampler accepts a variable-length sequence of spatial image/video features from the NFNet vision encoder and outputs a **fixed 64 visual tokens** regardless of input resolution or video length. Uses a fixed set of learned latent queries that cross-attend to the variable encoder outputs. Reduces computational complexity of subsequent vision-text cross-attention in the frozen LM.
- **condition**: Flamingo (3B / 9B / 80B); NeurIPS 2022; video frames sampled at 1 FPS, encoded independently then resampled to 64 tokens
- **source**: Alayrac et al., "Flamingo," NeurIPS 2022, arXiv:2204.14198, local: download/alayrac-flamingo-2022.pdf, p. 5 · **tier**: A · **confidence**: high

---
## Q3 — KV-Cache / Prefill Implications for Long Image+Video Token Sequences

### Prefill dominates latency at scale: 83% of total latency at 80K context
- **value/result**: At 80K token cache sequence length in video-LLM inference, **83% of total latency** is taken by the prefill stage; of that prefill latency, **74%** is consumed by KV cache retrieval — identifying prefill as the dominant bottleneck, not decoding.
- **condition**: Streaming video LLM (V-Rex paper); 80K sequence length; GPU inference
- **source**: V-Rex arXiv:2512.12284, 2024 · **tier**: B · **confidence**: high

### Streaming video KV cache growth and mitigation
- **value/result**: Streaming video LLMs face unbounded KV cache growth as new frames arrive continuously. Each new frame (typically encoded as 64–256+ vision tokens) triggers an iterative prefill step. The ViT encoding stage and LLM prefilling stage are cited as the two primary cost centers; temporal redundancy between adjacent frames is a key wasteful computation. Techniques (DyCoke token merging across frames, VidCom², StreamingTOM) apply compression ratios to maintain a bounded cache.
- **condition**: General streaming video-LLM setting (1 FPS or real-time); 2024–2025 literature
- **source**: LiveVLM arXiv:2505.15269; StreamKV arXiv:2511.07278; HybridKV arXiv:2604.05887 · **tier**: B · **confidence**: med

### KV cache is modality-heterogeneous: vision tokens need separate treatment
- **value/result**: Standard LLM KV-cache eviction methods (e.g., H2O, StreamingLLM) are not directly applicable to multimodal models because **vision tokens are spatially continuous and semantically sparse** relative to dense language tokens. Naive eviction degrades visual comprehension; recent work (HybridKV) proposes hybrid per-modality eviction policies.
- **condition**: MLLMs with interleaved image + text KV caches; 2024–2025
- **source**: A Survey on LLM KV Cache Management arXiv:2412.19442; HybridKV arXiv:2604.05887 · **tier**: B · **confidence**: med

### FastV prefill-phase acceleration
- **value/result**: FastV directly reduces prefill cost by dropping 50% of visual tokens after layer 2 of the LLM backbone, reducing FLOPs by ~45%; however, its original design requires access to full attention matrices (incompatible with FlashAttention), resulting in high GPU memory usage — a practical deployment constraint noted in follow-up work.
- **condition**: LLaVA-1.5, QwenVL-Chat, Video-LLaVA; R=50% pruning; ECCV 2024
- **source**: Chen et al., "FastV," arXiv:2403.06764, ECCV 2024 (Oral) · **tier**: A · **confidence**: high
