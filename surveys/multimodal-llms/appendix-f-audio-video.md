<!-- sec:F -->
## <a id="sec-F"></a>F Audio and video front-ends

<a id="p-f-audio-and-video-front-ends-1"></a><!-- para:f-audio-and-video-front-ends-1 --> Section <!-- secxref:7 -->[§7](modality-breadth.md#sec-7) derived the log-mel audio front-end and sketched video sampling; this appendix fills in the Whisper encoder, the discrete-audio-token path, and the token-budget arithmetic that governs video.

<!-- sec:F.1 -->
### <a id="sec-F.1"></a>F.1 The Whisper encoder, end to end

<a id="p-f1-the-whisper-encoder-end-to-end-1"></a><!-- para:f1-the-whisper-encoder-end-to-end-1 --> Whisper's encoder <!-- cite:19 -->[[19]](#ref-19) takes the log-mel spectrogram of § <!-- secxref:7.1 -->[§7.1](modality-breadth.md#sec-7.1) — an $80$-channel representation at a $10$ ms hop, so $100$ frames per second — and processes it in three stages. First, a **convolutional stem** of two layers (filter width $3$, GELU activations, the second with stride $2$) halves the time resolution to $\sim50$ frames per second and projects the $80$ mel channels to the model width; this is the audio counterpart of ViT's patch projection, a learned filterbank over the spectrogram. Second, **sinusoidal position embeddings** mark each frame's place in time (audio, like text, has a temporal order, so a fixed positional code suffices). Third, a **transformer encoder** of pre-norm blocks (§ <!-- secxref:A.2 -->[§A.2](appendix-a-vit-and-encoders.md#sec-A.2)) processes the frame sequence bidirectionally. The output is a sequence of feature vectors — "audio tokens" in the § 7.1 sense — that a connector hands to the LLM. Downstream models often add a further stride-$2$ pooling so each output frame spans $\sim40$ ms, trading time resolution for a shorter sequence, the audio version of the § <!-- secxref:8.2 -->[§8.2](inference-and-serving.md#sec-8.2) token-budget tradeoff.

<!-- sec:F.2 -->
### <a id="sec-F.2"></a>F.2 Discrete audio tokens

<a id="p-f2-discrete-audio-tokens-1"></a><!-- para:f2-discrete-audio-tokens-1 --> The discrete path of § 7.1 quantizes the encoder's continuous frames into a small vocabulary so that audio can be *generated* by next-token prediction. AudioPaLM <!-- cite:22 -->[[22]](#ref-22) clusters speech-encoder embeddings (via $k$-means, the same vector-quantization idea as § <!-- secxref:D -->[§D](appendix-d-visual-tokenization.md#sec-D)) into roughly a thousand audio tokens at a $\sim25$ Hz rate, then *extends the text LLM's embedding matrix* by those new rows — text embeddings reused, audio embeddings freshly initialized — so one decoder-only transformer predicts interleaved text and audio tokens under a single next-token loss. Materializing a waveform from generated audio tokens is a separate decoder stage (a vocoder-like model). The striking transfer result of § 7.1 — translation ability inherited from the text backbone for language pairs never seen in speech — follows directly from this shared-vocabulary design: the model's text competence is *in the same parameters* the audio tokens now flow through.

<!-- sec:F.3 -->
### <a id="sec-F.3"></a>F.3 Video: the token-budget arithmetic

<a id="p-f3-video-the-token-budget-arithmetic-1"></a><!-- para:f3-video-the-token-budget-arithmetic-1 --> Video's cost is the § <!-- secxref:8.1 -->[§8.1](inference-and-serving.md#sec-8.1) problem multiplied by the frame count. Sampling a clip to $F$ frames and encoding each with a ViT that yields $N_v^{\text{frame}}$ patch tokens gives a total visual-token count

<a id="eq-1"></a><!-- eq:F-1 -->
$$
N_{\text{video}} = F \cdot N_v^{\text{frame}} \tag{1}
$$

<a id="p-f3-video-the-token-budget-arithmetic-2"></a><!-- para:f3-video-the-token-budget-arithmetic-2 --> before any reduction. The arithmetic is why video is hard: at $F=8$ frames and $N_v^{\text{frame}}=576$ (a $336$-px frame), Equation <!-- ref:F-1 -->[(1)](#eq-1) is already $4608$ tokens — and eight frames is far too few for a long video, while the hundreds of frames a long clip needs would be tens of thousands of tokens. The three levers of § <!-- secxref:7.2 -->[§7.2](modality-breadth.md#sec-7.2) all attack a factor in Equation <!-- ref:F-1 -->[(1)](#eq-1): sparse sampling lowers $F$ (at the cost of temporal coverage), temporal pooling and token-merging lower the effective $N_v^{\text{frame}}$ by exploiting frame-to-frame redundancy, and time encoding (Qwen2-VL's M-RoPE, which assigns each token a separate temporal, height, and width coordinate) lets a model use fewer tokens without losing track of *when* each was seen. The unsolved long-video regime is exactly the regime where no setting of Equation <!-- ref:F-1 -->[(1)](#eq-1) is simultaneously cheap enough to serve and dense enough to answer — the open problem of § <!-- secxref:13.1 -->[§13.1](open-problems-and-roadmap.md#sec-13.1).
