<!-- sec:4 -->
## <a id="sec-4"></a>4 Method inventory

<a id="p-4-method-inventory-1"></a><!-- para:4-method-inventory-1 --> Sections 2 and 3 built the machinery and the design space; this section is the *catalog* — one uniform card per named system, so that methods can be compared at a glance rather than reconstructed from scattered prose. Every card answers the same fixed questions, in the same order: **What & where** (the idea and its placement on the entry-point / connector / fusion axes of § <!-- secxref:3.1 -->[§3.1](architecture-building-blocks.md#sec-3.1)); **Mechanism** (the load-bearing equation, with the full derivation cross-referenced to § 2–3 or an appendix rather than repeated); **Intuition** (one line, with a signal-processing analogy where one sharpens it); **Numbers** (a worked figure plus complexity/cost); **Limits** (limitations and characteristic failure modes); and **Status** (where it is preferred today, with an epistemic tag — *[established]*, *[reported]*, or *[contested]*). Headline cards (**H**) carry all six fields with a worked figure; load-bearing cards (**L**) compress to mechanism, intuition, numbers, and status; the long tail of catalog systems (**C**) is gathered into one table at the end. The derivation each card points to is the same one element of the R-CARD skeleton — the inventory does not re-derive, it indexes.

<!-- sec:4.1 -->
### <a id="sec-4.1"></a>4.1 CLIP — contrastive language–image pretraining [H]

<a id="p-41-clip-contrastive-languageimage-pretraining-h-1"></a><!-- para:41-clip-contrastive-languageimage-pretraining-h-1 --> **What & where.** The component almost every later system reuses: a vision encoder pretrained to share an embedding geometry with text, by contrastive matching of images to their captions <!-- cite:1 -->[[1]](#ref-1). Entry-point: it *is* the encoder. **Mechanism.** Symmetric InfoNCE over an $N\times N$ batch similarity matrix, derived in full at § <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) (Eq 3–4 there); the learned inverse-temperature $\exp(t')=1/\tau$ is clipped at $100$ for numerical stability. **Intuition.** Matched filtering at scale — each caption is a template the image must correlate with and no other. **Numbers.** Trained at batch $N=32{,}768$ on $\sim 400$M web pairs; the worked temperature example of § 2.4 shows a cosine margin of $0.30$ becoming a $0.96$ match probability. Cost is the $O(N^2 d_e)$ similarity matrix with a batch-global softmax. **Limits.** Aligns *one* image vector to *one* caption vector — coarse, image-level, weak on spatial/compositional detail, a seed of downstream hallucination. **Status.** The default frozen visual front-end for open VLMs; ImageNet zero-shot $76.2\%$ <!-- cite:1 -->[[1]](#ref-1). *[established]*

<!-- sec:4.2 -->
### <a id="sec-4.2"></a>4.2 ViT — the Vision Transformer [H]

<a id="p-42-vit-the-vision-transformer-h-1"></a><!-- para:42-vit-the-vision-transformer-h-1 --> **What & where.** The patch-token backbone every image encoder is built on: cut the image into a grid, linearly embed each patch, run a standard transformer <!-- cite:2 -->[[2]](#ref-2). Entry-point: the encoder's internals. **Mechanism.** Patch embedding (Eq 1) and the pre-norm encoder stack (Eq 2), derived at § <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2)–<!-- secxref:2.3 -->[§2.3](fundamentals.md#sec-2.3); the patch projection is literally a strided `Conv2d`. **Intuition.** A learned analysis filterbank (patch embedding) feeding a global, content-adaptive mixer (self-attention). **Numbers.** A $224$-px image at patch $14$ gives $N_v=256$ tokens; cost scales as resolution-squared in tokens and resolution-to-the-fourth in attention (§ 2.2 worked figure). **Limits.** Little 2-D inductive bias → data-hungry; position embeddings are tied to the training grid and must be interpolated at new resolutions. **Status.** Universal — every encoder-based VLM in this inventory has a ViT (or a SigLIP/CLIP variant of one) inside it. *[established]*

<!-- sec:4.3 -->
### <a id="sec-4.3"></a>4.3 SigLIP — sigmoid language–image pretraining [L]

<a id="p-43-siglip-sigmoid-languageimage-pretraining-l-1"></a><!-- para:43-siglip-sigmoid-languageimage-pretraining-l-1 --> **What & where.** A cheaper drop-in replacement for CLIP's contrastive objective; same role (the encoder), different loss <!-- cite:15 -->[[15]](#ref-15). **Mechanism.** Replace the batch-global softmax with a per-pair sigmoid (binary "match?" on every cell), derived at § <!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5) (Eq 5); the learned bias $b=-10$ encodes the prior that almost all pairs mismatch. **Numbers.** No all-gather and no $N\times N$ matrix in memory → trains a strong encoder on a handful of accelerators; sigmoid beats softmax below $\sim 16$k batch, the two converging above it. **Status.** An increasingly common encoder default precisely because it is cheap to produce; SigLIP-pretrained ViTs back PaliGemma, Idefics2, and others in the catalog. *[established]*

<!-- sec:4.4 -->
### <a id="sec-4.4"></a>4.4 LLaVA / LLaVA-1.5 — visual instruction tuning [H]

<a id="p-44-llava-llava-15-visual-instruction-tuning-h-1"></a><!-- para:44-llava-llava-15-visual-instruction-tuning-h-1 --> **What & where.** The recipe that democratized VLMs: frozen CLIP encoder + a tiny projector + an instruction-tuned LLM, early-fusion <!-- cite:5 -->[[5]](#ref-5). Connector: token-preserving projector. **Mechanism.** A single linear map (LLaVA) or two-layer MLP (LLaVA-1.5 <!-- cite:6 -->[[6]](#ref-6)) projects every patch feature into the LLM token space and prepends it to the text — § <!-- secxref:2.6 -->[§2.6](fundamentals.md#sec-2.6) (Eq 6); trained in two stages (projector-only align, then LLM fine-tune). **Intuition.** Because CLIP features already live in a language-shaped geometry, the connector is mostly a change of basis, not a re-encoding. **Numbers.** $\sim 256$ visual tokens at $224$ px ($576$ at $336$ px); the instruction data is a modest GPT-generated set, not web-scale. **Limits.** Token count grows with resolution; the LLM is fine-tuned, so forgetting must be managed by data mixing. **Status.** *The* dominant open recipe — the structural template the entire catalog tail varies. *[established]*

<!-- sec:4.5 -->
### <a id="sec-4.5"></a>4.5 BLIP-2 — the Q-Former bottleneck [H]

<a id="p-45-blip-2-the-q-former-bottleneck-h-1"></a><!-- para:45-blip-2-the-q-former-bottleneck-h-1 --> **What & where.** Bridge a *frozen* encoder and a *frozen* LLM with a small trained query transformer <!-- cite:4 -->[[4]](#ref-4). Connector: token-reducing query resampler. **Mechanism.** $32$ learned queries cross-attend the patch features to a fixed $32\times 768$ output, lifted by an FC layer into a soft visual prompt — § <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3) (Eq 2); pretrained in two stages over three objectives (ITC / ITM / ITG, derived in Appendix C). **Intuition.** An information bottleneck: a $32$-token ceiling forces the queries to keep only the most text-relevant visual content. **Numbers.** Compresses $257\times 1024$ to $32\times 768$ ($8\times$ smaller), constant in resolution; both heavy models frozen → trainable on a single $16\times$A100 node. **Limits.** Aggressive compression loses fine detail (OCR, small text); the Q-Former is itself a nontrivial module needing its own pretraining. **Status.** The canonical query-resampler; its soft-prompt idea persists even where the Q-Former itself has been displaced by MLP projectors. *[established]*

<!-- sec:4.6 -->
### <a id="sec-4.6"></a>4.6 Flamingo — gated cross-attention into a frozen LM [H]

<a id="p-46-flamingo-gated-cross-attention-into-a-frozen-lm-h-1"></a><!-- para:46-flamingo-gated-cross-attention-into-a-frozen-lm-h-1 --> **What & where.** Deep fusion: keep the LM frozen and splice visual cross-attention between its layers <!-- cite:3 -->[[3]](#ref-3). Connector: Perceiver Resampler (64 tokens); fusion: deep. **Mechanism.** Zero-initialized $\tanh$-gated cross-attention (GATED XATTN-DENSE) and the interleaved-likelihood factorization — § <!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4) (Eq 3–4); the resampler is Eq 1 there. **Intuition.** Begin as the exact pretrained LM (gate $=0$) and open the gate continuously — an architectural warmup. **Numbers.** Visual tokens are cross-attended, never in the text sequence, so token cost is independent of image count → many-image, interleaved, few-shot prompts (up to $32$ shots). **Limits.** Many new cross-attention parameters; the frozen LM cannot reshape its own representations around vision. **Status.** The reference deep-fusion design; the pattern of choice when the LM must stay frozen or inputs are many-image/interleaved. *[established]*

<!-- sec:4.7 -->
### <a id="sec-4.7"></a>4.7 Qwen2-VL / Qwen2.5-VL — native dynamic resolution [L]

<a id="p-47-qwen2-vl-qwen25-vl-native-dynamic-resolution-l-1"></a><!-- para:47-qwen2-vl-qwen25-vl-native-dynamic-resolution-l-1 --> **What & where.** A leading open VLM family that drops the fixed-grid assumption: a ViT encoder processes images at *native* resolution and variable token count, with multimodal rotary position encoding (M-RoPE) over time/height/width <!-- cite:7 -->[[7]](#ref-7). Connector: MLP projector with windowed attention; fusion: early. **Mechanism.** Native-resolution patching (an image becomes as many tokens as its size warrants) plus M-RoPE, extending § 3's early-fusion stack; full M-RoPE treatment is forward-referenced to the modality-breadth section. **Numbers.** Qwen2.5-VL-72B reports MMMU(val) $70.2$, DocVQA(test) $96.4$, MathVista $74.8$ — the first open model to match GPT-4o's $69.1$ MMMU <!-- cite:26 -->[[26]](#ref-26); Qwen2-VL-72B MMMU $64.5$ <!-- cite:7 -->[[7]](#ref-7). **Status.** Among the strongest open VLMs; native resolution is now a widely-copied design. *[reported]* (benchmark numbers read from the technical reports; see § on SOTA for eval conditions).

<!-- sec:4.8 -->
### <a id="sec-4.8"></a>4.8 InternVL — scaling the vision encoder [L]

<a id="p-48-internvl-scaling-the-vision-encoder-l-1"></a><!-- para:48-internvl-scaling-the-vision-encoder-l-1 --> **What & where.** Pushes the usually-small vision tower to LLM scale (a $\sim 6$B "InternViT") and aligns it to the LLM with a learned bridge <!-- cite:24 -->[[24]](#ref-24). Connector: MLP projector (later versions); fusion: early. **Mechanism.** A large vision encoder + progressive alignment, scaling § 3's encoder box rather than changing the fusion pattern. **Numbers.** InternVL2.5-78B reports MMMU(val) $70.1$, DocVQA(test) $95.1$, MathVista $72.3$ (cross-tabulated in the Qwen2.5-VL report <!-- cite:26 -->[[26]](#ref-26)). **Status.** A consistent open-SOTA contender; evidence that a *bigger* encoder, not only a bigger LLM, moves multimodal scores. *[reported]*

<!-- sec:4.9 -->
### <a id="sec-4.9"></a>4.9 Fuyu — the encoder-free decoder [L]

<a id="p-49-fuyu-the-encoder-free-decoder-l-1"></a><!-- para:49-fuyu-the-encoder-free-decoder-l-1 --> **What & where.** The clean instance of the encoder-free entry point: no vision tower, raw patches linearly projected straight into the decoder's first layer <!-- cite:14 -->[[14]](#ref-14). Connector: a single linear patch projection; fusion: native-as-input. **Mechanism.** Image patches are projected and laid in the sequence with an image-newline marker; with no encoder fixing a grid, any resolution is just a longer patch sequence (§ <!-- secxref:3.2 -->[§3.2](architecture-building-blocks.md#sec-3.2)). **Numbers.** One model, no separate ViT; arbitrary resolution at inference. **Limits.** Forgoes the CLIP visual prior, so it leans harder on multimodal training data to reach the same perception quality. **Status.** A minority but instructive design (GUI/agent use); proof that the encoder is a choice, not a necessity. *[reported]* (architecture from the vendor blog; weak source).

<!-- sec:4.10 -->
### <a id="sec-4.10"></a>4.10 LLaVA-NeXT — AnyRes tiling [L]

<a id="p-410-llava-next-anyres-tiling-l-1"></a><!-- para:410-llava-next-anyres-tiling-l-1 --> **What & where.** The standard fix for the LLaVA projector's resolution ceiling: tile a high-resolution image into sub-images, encode each, concatenate <!-- cite:33 -->[[33]](#ref-33). Connector: MLP projector over tiles; fusion: early. **Mechanism.** A dynamic grid (e.g. $2\times2$ plus a downsampled global view) raises the effective pixel budget $\sim 4\times$ over LLaVA-1.5 while reusing the same projector. **Numbers.** Supports up to $\sim 672\times672$ (or $336\times1344$); token count scales with the tile count. **Limits.** More tiles = more tokens = the § 3.3 budget tension, now multiplied. **Status.** The dominant high-resolution strategy in open early-fusion VLMs. *[reported]* (blog source).

<!-- sec:4.11 -->
### <a id="sec-4.11"></a>4.11 VQ-VAE / VQGAN — discrete visual tokenization [H]

<a id="p-411-vq-vae-vqgan-discrete-visual-tokenization-h-1"></a><!-- para:411-vq-vae-vqgan-discrete-visual-tokenization-h-1 --> **What & where.** The component that makes images *speak the LM's native language*: a learned codec that maps an image to a grid of integer tokens from a finite codebook <!-- cite:16 -->[[16]](#ref-16), the prerequisite for native-token fusion (§ <!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4)) and discrete any-to-any generation. **Mechanism.** An encoder output $z_e(x)$ is snapped to its nearest codebook vector,

<a id="eq-1"></a><!-- eq:4-1 -->
$$
z_q(x) = e_k, \qquad k = \arg\min_{j\in\{1,\dots,K\}} \lVert z_e(x) - e_j\rVert_2 \tag{1}
$$

<a id="p-411-vq-vae-vqgan-discrete-visual-tokenization-h-2"></a><!-- para:411-vq-vae-vqgan-discrete-visual-tokenization-h-2 --> and trained through the non-differentiable $\arg\min$ by a straight-through estimator (copy the decoder-input gradient to the encoder output), under a three-term loss:

<a id="eq-2"></a><!-- eq:4-2 -->
$$
\mathcal{L}_{\text{VQ-VAE}} = \lVert x - \hat{x}\rVert_2^2 + \lVert \mathrm{sg}[z_e(x)] - e\rVert_2^2 + \beta\,\lVert z_e(x) - \mathrm{sg}[e]\rVert_2^2 \tag{2}
$$

<a id="p-411-vq-vae-vqgan-discrete-visual-tokenization-h-3"></a><!-- para:411-vq-vae-vqgan-discrete-visual-tokenization-h-3 --> where $\mathrm{sg}[\cdot]$ is stop-gradient: reconstruction, a codebook term pulling codes toward encoder outputs, and a commitment term ($\beta=0.25$) pulling encoder outputs toward codes. The full derivation (straight-through gradient, EMA codebook, the VQGAN perceptual+adversarial upgrade <!-- cite:17 -->[[17]](#ref-17)) is Appendix D. **Intuition.** A learned vector quantizer — exactly the LBG/$k$-means codebook of classical speech coding, trained end-to-end so the decoder can invert it. **Numbers.** A codebook of $K$ entries turns an image into a short integer grid (orders of magnitude fewer symbols than pixels); VQGAN's adversarial loss is what makes those few tokens decode to sharp images. **Limits.** Quantization is lossy (codebook collapse, blur on fine texture) — the fidelity ceiling every discrete-token generator inherits. **Status.** The tokenizer under Chameleon and Emu3; the discrete half of the generation design space. *[established]*

<!-- sec:4.12 -->
### <a id="sec-4.12"></a>4.12 Chameleon — mixed-modal autoregression [H]

<a id="p-412-chameleon-mixed-modal-autoregression-h-1"></a><!-- para:412-chameleon-mixed-modal-autoregression-h-1 --> **What & where.** The canonical native-token model: quantize images to discrete tokens, interleave with text in one vocabulary, train one transformer with one next-token loss <!-- cite:8 -->[[8]](#ref-8). Entry/fusion: native-token early fusion; no encoder, no connector. **Mechanism.** Images are VQ-tokenized (Eq 1–2), concatenated with text token ids, and modeled by a single autoregressive cross-entropy $-\sum_\ell \log p_\theta(s_\ell\mid s_{<\ell})$ over the joint symbol stream $s$; stability tricks (query-key norm, reordered norms) tame the mixed-modal training. Full likelihood in Appendix E. **Intuition.** Erase the modality boundary — image and text are the *same kind of object*, so one machine both reads and writes either. **Numbers.** Trained from scratch (a text-only LLM has no visual tokens to inherit); one model emits interleaved text and images. **Limits.** Full pretraining cost; image quality is capped by the VQ tokenizer (§ 4.11). **Status.** The reference discrete-AR any-to-any model; the substrate the unified-generation section builds on. *[established]*

<!-- sec:4.13 -->
### <a id="sec-4.13"></a>4.13 Transfusion — one transformer, two losses [H]

<a id="p-413-transfusion-one-transformer-two-losses-h-1"></a><!-- para:413-transfusion-one-transformer-two-losses-h-1 --> **What & where.** The continuous-generation rival to Chameleon: keep images as *continuous* latent patches and generate them by diffusion, while text stays discrete and autoregressive — in a single transformer over shared parameters <!-- cite:10 -->[[10]](#ref-10). **Mechanism.** Text contributes a next-token LM loss; image patches (VAE latents) contribute a DDPM denoising loss; the two are summed:

<a id="eq-3"></a><!-- eq:4-3 -->
$$
\mathcal{L}_{\text{Transfusion}} = \mathcal{L}_{\text{LM}} + \lambda\,\mathcal{L}_{\text{DDPM}}, \qquad \mathcal{L}_{\text{DDPM}} = \mathbb{E}_{t,\boldsymbol{\epsilon}}\big[\lVert \boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t, c)\rVert_2^2\big] \tag{3}
$$

<a id="p-413-transfusion-one-transformer-two-losses-h-2"></a><!-- para:413-transfusion-one-transformer-two-losses-h-2 --> with causal attention over the sequence but *bidirectional* attention within each image's patches; full joint-loss derivation in Appendix E. **Intuition.** Use each modality's native objective rather than forcing images through a lossy quantizer — autoregression for the discrete stream, denoising for the continuous one. **Numbers.** A $7$B Transfusion trains on $\sim 2$T mixed-modal tokens; images live as VAE latents, never quantized. **Limits.** Two objectives and a diffusion sampler to balance; heavier generation-time compute than a single AR pass. **Status.** The leading evidence that continuous-diffusion image generation can share one backbone with text AR — the other pole of the § 7 design tension. *[established]*

<!-- sec:4.14 -->
### <a id="sec-4.14"></a>4.14 Emu3 — next-token prediction for everything [L]

<a id="p-414-emu3-next-token-prediction-for-everything-l-1"></a><!-- para:414-emu3-next-token-prediction-for-everything-l-1 --> **What & where.** Pushes the discrete-AR thesis to its limit: tokenize images *and video* and predict the next token for all of it, no diffusion, no CLIP <!-- cite:9 -->[[9]](#ref-9). Fusion: native-token. **Mechanism.** A single transformer over a unified discrete vocabulary spanning text, image, and video tokens, trained purely by next-token prediction — the Chameleon recipe extended to video. **Numbers.** One objective across all modalities; competitive generation and perception from pure AR. **Status.** The strongest "next-token-is-all-you-need" datapoint for any-to-any; full treatment in § 7. *[reported]*

<!-- sec:4.15 -->
### <a id="sec-4.15"></a>4.15 Whisper — the audio front-end [L]

<a id="p-415-whisper-the-audio-front-end-l-1"></a><!-- para:415-whisper-the-audio-front-end-l-1 --> **What & where.** The audio analogue of CLIP's encoder: a robust speech encoder almost every audio-LLM reuses <!-- cite:19 -->[[19]](#ref-19). **Mechanism.** Resample to $16$ kHz, compute an $80$-channel log-mel spectrogram ($25$ ms window, $10$ ms hop), two conv layers (stride-2) then a transformer encoder; the mel front-end is the STFT-based analogue of ViT's patch embedding (Appendix F). **Numbers.** Trained on $680$k hours of weakly-supervised multilingual audio; output frames at $\sim 50$ Hz, often pooled to $\sim 40$ ms/frame. **Status.** The default audio encoder — Qwen-Audio and SALMONN both build on it. *[established]*

<!-- sec:4.16 -->
### <a id="sec-4.16"></a>4.16 Qwen-Audio / SALMONN — audio LLMs [L]

<a id="p-416-qwen-audio-salmonn-audio-llms-l-1"></a><!-- para:416-qwen-audio-salmonn-audio-llms-l-1 --> **What & where.** Two ways to attach a frozen Whisper-style encoder to an LLM. Qwen-Audio feeds encoder frames into Qwen-7B with hierarchical task tags for $30$+ audio tasks <!-- cite:20 -->[[20]](#ref-20); SALMONN adds a *second* encoder (BEATs for non-speech) and a window-level Q-Former, adapting a frozen Vicuna with LoRA <!-- cite:21 -->[[21]](#ref-21). Connector: early-fusion projection (Qwen-Audio) vs window-level Q-Former (SALMONN). **Mechanism.** SALMONN's window-level Q-Former compresses each $\sim 0.33$ s window to a fixed token count ($88$ tokens for $30$ s), the temporal analogue of BLIP-2's spatial resampler (§ 4.5); only Q-Former + LoRA train ($\sim 0.24\%$ of parameters). **Numbers.** SALMONN trains $\sim 33$M of $\sim 14$B parameters; dual-encoder covers speech *and* music/sound. **Status.** Representative perceive-audio LLMs; the discrete-audio-token alternative (AudioPaLM) and full-duplex speech (Moshi) are in the catalog and § 8. *[reported]*

<!-- sec:4.17 -->
### <a id="sec-4.17"></a>4.17 Catalog — the long tail [C]

<a id="p-417-catalog-the-long-tail-c-1"></a><!-- para:417-catalog-the-long-tail-c-1 --> The systems below extend or recombine the patterns above without introducing a new axis; each is stated with its distinctive choice and its strongest source tag. Closed frontier models (GPT-4o, Gemini, Claude) are listed for completeness with the explicit caveat that their internals are undisclosed, so every architectural claim is *[contested]* and rests on a weak source — they appear here as capability landmarks, not as design references, and carry no load-bearing claim.

| Model | Distinctive choice | Connector / fusion | Source |
|---|---|---|---|
| Qwen-VL <!-- cite:25 -->[[25]](#ref-25) | early open native-res VLM; position-aware adapter | cross-attn adapter → early | local *[established]* |
| Idefics2 <!-- cite:27 -->[[27]](#ref-27) | ablation: autoregressive + pooling beats cross-attention | learned pooling to 64 tokens → early | local *[established]* |
| PaliGemma <!-- cite:28 -->[[28]](#ref-28) | SigLIP + Gemma; prefix-LM mask; zero-init linear (MLP gave no gain) | linear → early (prefix-LM) | local *[established]* |
| Molmo / PixMo <!-- cite:29 -->[[29]](#ref-29) | open *data* (no distillation from closed models) | MLP → early | local *[established]* |
| Pixtral 12B <!-- cite:30 -->[[30]](#ref-30) | native-res ViT from scratch; strong Apache-2.0 model | MLP → early | local *[established]* |
| DeepSeek-VL <!-- cite:31 -->[[31]](#ref-31) | hybrid vision encoder for doc + general | MLP adaptor → early | local *[established]* |
| NVLM <!-- cite:32 -->[[32]](#ref-32) | compares decoder-only vs cross-attention vs hybrid | both → studied | local *[established]* |
| Janus <!-- cite:18 -->[[18]](#ref-18) | *decouples* the encoder for understanding vs generation | dual encoders → unified AR | local *[reported]* |
| CogVLM <!-- cite:34 -->[[34]](#ref-34) | per-layer "visual expert" (separate QKV+MLP) in a frozen LM | per-layer expert → deep | abstract *[reported]* |
| MiniGPT-4 <!-- cite:35 -->[[35]](#ref-35) | single linear projection between two frozen models | linear → early | abstract *[reported]* |
| mPLUG-Owl <!-- cite:36 -->[[36]](#ref-36) | "visual abstractor" cross-attention pooling | abstractor → early | abstract *[reported]* |
| Video-LLaVA <!-- cite:23 -->[[23]](#ref-23) | align image+video before projection; 8-frame uniform sampling | shared linear → early | local *[established]* |
| Video-LLaMA <!-- cite:37 -->[[37]](#ref-37) | dual video + audio Q-Formers | Q-Formers → early | abstract *[reported]* |
| AudioPaLM <!-- cite:22 -->[[22]](#ref-22) | discrete audio tokens in a shared text+audio vocabulary | vocabulary merge → native | local *[established]* |
| Moshi <!-- cite:38 -->[[38]](#ref-38) | full-duplex real-time speech; inner-monologue text grounding | streaming codec → native | web *[contested]* |
| GPT-4o <!-- cite:13 -->[[13]](#ref-13) | end-to-end omni (text/audio/image/video), $\sim 320$ ms speech latency | undisclosed | web *[contested]* |

<a id="p-417-catalog-the-long-tail-c-2"></a><!-- para:417-catalog-the-long-tail-c-2 --> The full quantitative comparison (benchmark scores with eval conditions and source tags) is the SOTA section's job; the master architectural comparison matrix over every **H/L** card above is the comparison-and-tradeoffs section. This inventory is the index those two synthesis artifacts draw on.
