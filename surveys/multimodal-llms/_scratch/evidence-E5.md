# Evidence Ledger E5 — Audio / Video / Omni Breadth
<!-- generated 2026-06-28 -->

---
## Q1 — Audio encoder front-end: Whisper mel-spectrogram + encoder; Qwen-Audio and SALMONN connection to LLM

### Whisper mel-spectrogram preprocessing and encoder architecture
- **value/result**: Audio resampled to 16 kHz; 80-channel log-magnitude mel spectrogram computed on 25 ms windows with 10 ms stride; encoder front-end consists of two conv layers (filter width 3, GELU, second conv stride-2) followed by sinusoidal position embeddings and pre-activation Transformer blocks with LayerNorm; encoder and decoder share the same width and number of Transformer blocks.
- **condition**: Applies to all Whisper model sizes; trained on 680,000 hours of multilingual + multitask supervision
- **source**: Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision," arXiv:2212.04356 (2022) · **tier**: A · **confidence**: high

### Qwen-Audio audio encoder connection to LLM
- **value/result**: Reuses the Whisper audio encoder (32-layer Transformer with two conv downsampling layers; 640M parameters). Audio preprocessed to 16 kHz, 80-channel mel spectrogram with 25 ms window and 10 ms hop; a stride-2 pooling layer further reduces length so each encoder output frame spans ~40 ms. SpecAugment applied at training time. The encoder output is fed directly into Qwen-7B LLM via next-token prediction with hierarchical multi-task decoder tags (language tag, task tag, timestamps tag, transcription tag) to handle 30+ tasks without task-specific fine-tuning.
- **condition**: Qwen-7B backbone; 30+ tasks, 8 languages, multiple audio types (speech, natural sounds, music)
- **source**: Chu et al., "Qwen-Audio: Advancing Universal Audio Understanding via Unified Large-Scale Audio-Language Models," arXiv:2311.07919 (2023) · **tier**: A · **confidence**: high

### SALMONN: dual encoder + window-level Q-Former + LoRA
- **value/result**: Dual encoder: Whisper-Large-v2 (speech) + BEATs (non-speech audio), both at 50 Hz output frame rate; concatenated frame-by-frame along feature dimension. Window-level Q-Former segments encoder output into L=17 frame windows (~0.33 s each), applies N=1 trainable query per window to produce 88 text tokens for a 30 s audio. LoRA (rank=8, scaling=4.0) adapts query and value weight matrices of the frozen Vicuna-13B backbone. Only Q-Former + LoRA are trainable (~33 M parameters, ~0.24% of total model).
- **condition**: Vicuna-13B backbone; three-stage training (pre-training, instruction tuning, activation tuning)
- **source**: Tang et al., "SALMONN: Towards Generic Hearing Abilities for Large Language Models," arXiv:2310.13289v2, ICLR 2024 · **tier**: A · **confidence**: high


---
## Q2 — AudioPaLM's discrete-audio-token approach

### AudioPaLM unified multimodal vocabulary with discrete audio tokens
- **value/result**: Converts raw audio into discrete tokens via k-means quantization of embeddings from w2v-BERT (multilingual) or USM (2B-parameter Universal Speech Model) encoders. Token rate: 25 Hz; vocabulary size: 1024 audio tokens. Text-only PaLM-2 8B checkpoint is extended by expanding the embedding matrix from t × m to (t + a) × m (a = 1024); text embeddings reused, audio embeddings freshly initialized and trained. A single decoder-only Transformer then processes freely interleaved text and audio tokens with task-prefix markup (e.g., [ASR French], [S2ST English French]). Audio output is materialized via AudioLM stages 2+3 or the non-autoregressive SoundStorm (~2 orders of magnitude faster than AR decoding).
- **condition**: AudioPaLM-2 8B; evaluated on CoVoST2 AST (37.8 BLEU), CVSS S2ST (ASR-BLEU 32.5 for 8B S2ST model), VoxPopuli ASR (WER 9.8% for AudioPaLM-2 8B AST)
- **source**: Rubenstein et al., "AudioPaLM: A Large Language Model That Can Speak and Listen," arXiv:2306.12925 (2023) · **tier**: A · **confidence**: high

### AudioPaLM initialization from text LLM improves speech tasks
- **value/result**: Initializing AudioPaLM with a text-only pretrained checkpoint (PaLM or PaLM-2) and fine-tuning all parameters on mixed speech+text tasks significantly outperforms training from scratch. AudioPaLM-2 8B AST achieves 37.8 BLEU on CoVoST2, versus 30.7 for USM-M and 29.1 for Whisper Large-v2 (1.5B). Zero-shot AST on languages unseen in speech-translation training (only ASR data seen) yields 28.6 BLEU (AudioPaLM-2 8B AST), showing that translation capability is inherited from the text LLM backbone.
- **condition**: Zero-shot = source language appeared in ASR training only, not in S2T translation pairs; FLEURS dataset
- **source**: Rubenstein et al., "AudioPaLM: A Large Language Model That Can Speak and Listen," arXiv:2306.12925 (2023) · **tier**: A · **confidence**: high


---
## Q3 — Video LLMs: frame-sampling + temporal modeling strategies

### Video-LLaVA: uniform frame sampling + LanguageBind pre-alignment before projection
- **value/result**: Uniformly samples 8 frames per video; each frame resized and cropped to 224×224. Visual encoders (image and video) are both initialized from LanguageBind, which pre-aligns images and videos into a shared language feature space before any projection. A single shared linear projection layer maps the unified representation into the LLM (Vicuna-7B). Two-stage training: Stage 1 on 558k image-text pairs + 702k video-text pairs (concise captions, 1 epoch, batch=256); Stage 2 instruction tuning on 665k LLaVA-mixed + 100k Video-ChatGPT data. Joint image+video training takes 3–4 days on 8 GPUs.
- **condition**: Vicuna-7B backbone; uniform 8-frame sampling is the only temporal modeling; long-video information loss acknowledged
- **source**: Lin et al., "Video-LLaVA: Learning United Visual Representation by Alignment Before Projection," arXiv:2311.10122 (2023/2024) · **tier**: A · **confidence**: high

### Video-LLaVA benchmark results vs Video-ChatGPT
- **value/result**: Video-LLaVA-7B surpasses Video-ChatGPT-7B by +5.8% on MSRVTT-QA (59.2 vs 49.3), +9.9% on MSVD-QA (70.7 vs 64.9), +18.6% on TGIF-QA (70.0 vs 51.4), and +10.1% on ActivityNet-QA (45.3 vs 35.2). On image benchmarks, outperforms InstructBLIP-7B on multiple evaluations. Chat-UniVi outperforms on ActivityNet because Video-LLaVA's 8-frame limit loses detail in long videos.
- **condition**: ChatGPT-3.5-turbo used as evaluator following Video-ChatGPT protocol; zero-shot
- **source**: Lin et al., "Video-LLaVA: Learning United Visual Representation by Alignment Before Projection," arXiv:2311.10122 (2023/2024) · **tier**: A · **confidence**: high

### General pattern: video LLMs use sparse uniform sampling + pooled temporal aggregation
- **value/result**: The dominant approach in early video-LLMs (VideoChat, Video-LLaMA, Video-ChatGPT, Video-LLaVA) is uniform sparse frame sampling (typically 8–16 frames) followed by per-frame visual encoding (ViT-based). Temporal modeling is implicit through position embeddings or frame-level token pooling; no explicit temporal attention across frames in the base Video-LLaVA design. More recent models (e.g., Chat-UniVi, LongVA, Video-LLaMA2) use adaptive or hierarchical token merging to handle longer contexts and denser temporal structure.
- **condition**: General landscape circa 2023–2024; uniform 8-frame design acknowledged as a bottleneck for long videos
- **source**: Lin et al., "Video-LLaVA: Learning United Visual Representation by Alignment Before Projection," arXiv:2311.10122 (2023/2024), related work section · **tier**: B · **confidence**: med


---
## Q4 — Omni / real-time: GPT-4o interleaved any-to-any + full-duplex / streaming speech

### GPT-4o: end-to-end omni model with native audio tokens
- **value/result**: GPT-4o is an autoregressive omni model trained end-to-end across text, audio, image, and video modalities using a single neural network (not a cascade of separate models). It accepts any combination of text, audio, image, and video as input and generates any combination of text, audio, and image as output. Audio response latency: minimum 232 ms, average 320 ms — comparable to human conversational response time. Architecture and tokenization details are not publicly disclosed; the system card describes capabilities, safety evaluations, and alignment procedures but not the model internals (weights, codec design, or exact token vocabulary).
- **condition**: GPT-4o (released May 2024); system card published August 2024; numbers from system card
- **source**: OpenAI, "GPT-4o System Card," arXiv:2410.21276 (2024) · URL: https://cdn.openai.com/gpt-4o-system-card.pdf · **tier**: B · **confidence**: high (latency numbers from system card; architecture UNVERIFIED / not disclosed)

### Moshi: full-duplex real-time speech-text foundation model
- **value/result**: Moshi (Kyutai) is a 7B-parameter Temporal Transformer designed for full-duplex spoken dialogue. It simultaneously processes three token streams at each timestep: user audio, system audio, and system text. The "Inner Monologue" mechanism predicts time-aligned text tokens alongside speech tokens, grounding generation. Audio codec: Mimi (streaming neural codec). Theoretical latency: 160 ms (practical ~200 ms on modern hardware). Training is 4-phase: (1) Temporal Transformer pre-training initialized from Helium; (2) post-training on diarized multi-stream data; (3) fine-tuning on Fisher dataset for full-duplex capability; (4) instruction fine-tuning on synthetic scripts. Model does not use explicit turn-taking; silence tokens model conversational gaps.
- **condition**: Full-duplex (simultaneous listen + speak); publicly released model; 7B params
- **source**: Défossez et al. (Kyutai), "Moshi: a speech-text foundation model for real-time dialogue," https://kyutai.org/Moshi.pdf (2024) · **tier**: B · **confidence**: high

