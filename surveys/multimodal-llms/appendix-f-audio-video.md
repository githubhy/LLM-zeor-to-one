<!-- sec:F -->
## <a id="sec-F"></a>F Audio and video front-ends

<a id="p-f-audio-and-video-front-ends-1"></a><!-- para:f-audio-and-video-front-ends-1 --> **Depth tier:** headline

<a id="p-f-audio-and-video-front-ends-2"></a><!-- para:f-audio-and-video-front-ends-2 --> Section <!-- secxref:7 -->[§7](modality-breadth.md#sec-7) established that nothing in the partition → summarize → align template is specific to images, and derived the log-mel front-end far enough to make that point. This appendix pays the rest of the bill: the exact arithmetic that turns a waveform into a fixed number of encoder positions, why a text-pretrained decoder transfers its competence to audio tokens at all, how two encoders trained on different things are made to share one sequence, and the token-budget algebra that makes long video the hardest open problem in this survey. Every numeric constant below is read from the cited paper; where a paper does **not** state a number the survey needs, that is recorded as a gap in <!-- secref:F.7 -->[§F.7](#sec-F.7) rather than filled in from memory.

<!-- sec:F.1 -->
### <a id="sec-F.1"></a>F.1 From waveform to frames: where the numbers come from

<a id="p-f1-from-waveform-to-frames-where-the-numbers-come-from-1"></a><!-- para:f1-from-waveform-to-frames-where-the-numbers-come-from-1 --> Whisper <!-- cite:19 -->[[19]](#ref-19) resamples all audio to $16$ kHz and computes an $80$-channel log-magnitude mel spectrogram on $25$ ms windows with a $10$ ms stride. Those three numbers — rate, window, hop — fix everything downstream, so it is worth seeing exactly how.

<a id="p-f1-from-waveform-to-frames-where-the-numbers-come-from-2"></a><!-- para:f1-from-waveform-to-frames-where-the-numbers-come-from-2 --> The hop, not the window, sets the frame rate. A window of $W$ seconds advanced by a hop of $H$ seconds produces frames at $1/H$ per second regardless of $W$: the window controls how much each frame *sees*, the hop controls how often we *look*. With $H = 10$ ms,

<a id="eq-1"></a><!-- eq:F-1 -->
$$
r_{\text{mel}} = \frac{1}{H} = \frac{1}{0.010\ \text{s}} = 100\ \text{frames/s} \tag{1}
$$

<a id="p-f1-from-waveform-to-frames-where-the-numbers-come-from-3"></a><!-- para:f1-from-waveform-to-frames-where-the-numbers-come-from-3 --> The window and the hop overlap deliberately: $W = 25$ ms against $H = 10$ ms means each sample is covered by $W/H = 2.5$ windows on average. That redundancy is not waste — it is what keeps the short-time Fourier transform's output smooth in time, and it is the audio counterpart of the overlapping receptive fields of a strided convolution.

<a id="p-f1-from-waveform-to-frames-where-the-numbers-come-from-4"></a><!-- para:f1-from-waveform-to-frames-where-the-numbers-come-from-4 --> **Why $80$ channels and not $257$.** A $25$ ms window at $16$ kHz is $400$ samples, so a real-input FFT yields on the order of $200$ linear frequency bins (or $257$ if zero-padded to $512$). The mel filterbank collapses those into $80$ perceptually-spaced bands, and two things justify the reduction. First, human frequency resolution is roughly logarithmic above $\sim1$ kHz, so linear bins over-resolve the top octaves and under-resolve the bottom; the mel scale spends its channels where discrimination actually happens. Second — the systems reason — $80$ channels is a substantial cut in the encoder's input width at essentially no loss for speech. The log is the third piece: loudness is perceived multiplicatively, and a log turns a multiplicative dynamic range of many orders of magnitude into an additive one that a network can normalize. Whisper does exactly this, then "globally scale[s] the input to be between $-1$ and $1$ with approximately zero mean across the pre-training dataset" <!-- cite:19 -->[[19]](#ref-19).

> <a id="p-f1-from-waveform-to-frames-where-the-numbers-come-from-5"></a><!-- para:f1-from-waveform-to-frames-where-the-numbers-come-from-5 --> **Note — the mel filterbank is the one hand-designed stage left in a modern multimodal stack.** Everything else in this survey is learned end to end; this filterbank is fixed, and it is fixed because a century of psychoacoustics already found a good answer. Vision has no equivalent inherited basis, which is why <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2) learns its patch projection instead. The asymmetry is historical rather than principled — learned audio front-ends exist and work; they simply have not displaced a basis that costs nothing and transfers across every corpus.

<!-- sec:F.2 -->
### <a id="sec-F.2"></a>F.2 The Whisper encoder, and a 30-second chunk end to end

<a id="p-f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-1"></a><!-- para:f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-1 --> Whisper's encoder applies "a small stem consisting of two convolution layers with a filter width of 3 and the GELU activation function ... where the second convolution layer has a stride of two", then adds sinusoidal position embeddings and runs pre-activation transformer blocks <!-- cite:19 -->[[19]](#ref-19). The stem is the audio analogue of ViT's patch projection: a learned filterbank running over the *already* mel-filtered spectrogram, mixing the $80$ channels up to the model width while halving the time axis.

<a id="p-f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-2"></a><!-- para:f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-2 --> A stride-$s$ convolution decimates the frame rate by exactly $s$, so with one stride-1 layer and one stride-2 layer the rate entering the transformer is

<a id="eq-2"></a><!-- eq:F-2 -->
$$
r_{\text{enc}} = \frac{r_{\text{mel}}}{s_1 s_2} = \frac{100}{1 \cdot 2} = 50\ \text{frames/s} \tag{2}
$$

<a id="p-f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-3"></a><!-- para:f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-3 --> **Worked example — the token cost of thirty seconds of audio.** Whisper processes audio in fixed $30$ s segments <!-- cite:19 -->[[19]](#ref-19). Composing Equations <!-- ref:F-1 -->[(1)](#eq-1) and <!-- ref:F-2 -->[(2)](#eq-2),

<a id="eq-3"></a><!-- eq:F-3 -->
$$
N_{\text{audio}} = T_{\text{chunk}} \cdot r_{\text{enc}} = 30\ \text{s} \times 50\ \text{frames/s} = 1500\ \text{encoder positions} \tag{3}
$$

<a id="p-f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-4"></a><!-- para:f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-4 --> Two observations make this number worth carrying. First, $1500$ tokens is *comparable to an image*: a $336$-px frame at patch size $14$ costs $(336/14)^2 = 576$ tokens, so half a minute of speech costs about what three images cost. Audio is cheap per second and expensive per minute, which is the opposite of the intuition that sound is the "lighter" modality. Second, the $30$ s figure is a hard architectural boundary rather than a default: Whisper models "are trained on 30-second audio chunks and cannot consume longer audio inputs at once" <!-- cite:19 -->[[19]](#ref-19), because the encoder's positional embedding table is exactly this long. Long-form transcription is therefore a *chunking* problem layered on top of the model, which is where its long-form failure modes come from.

<a id="p-f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-5"></a><!-- para:f2-the-whisper-encoder-and-a-30-second-chunk-end-to-end-5 --> **A caution about where Equation <!-- ref:F-3 -->[(3)](#eq-3) comes from.** The paper states every ingredient ($16$ kHz, $25$ ms, $10$ ms, stride $2$, $30$ s) and never prints $1500$ or $3000$ anywhere in its main text or its hyperparameter appendices. The composition above is therefore *derived from the paper's own constants*, not quoted from it. It is stated here rather than hedged because every input is verbatim and the arithmetic is forced — but a reader should know which side of that line it sits on, and <!-- secref:F.7 -->[§F.7](#sec-F.7) records it as derived.

<!-- sec:F.3 -->
### <a id="sec-F.3"></a>F.3 Discrete audio tokens, and why text competence transfers

<a id="p-f3-discrete-audio-tokens-and-why-text-competence-transfers-1"></a><!-- para:f3-discrete-audio-tokens-and-why-text-competence-transfers-1 --> The front-end above yields *continuous* features, which a connector projects into the LLM's space. To let a model **generate** speech, the features must instead be discretized, exactly as <!-- secxref:6.1 -->[§6.1](multimodal-generation.md#sec-6.1) discretizes images. AudioPaLM <!-- cite:22 -->[[22]](#ref-22) extracts embeddings from a speech encoder and quantizes them by $k$-means, producing "tokens at a rate of 25Hz" with a "token vocabulary ... of size 1024".

<a id="p-f3-discrete-audio-tokens-and-why-text-competence-transfers-2"></a><!-- para:f3-discrete-audio-tokens-and-why-text-competence-transfers-2 --> The vocabulary-extension mechanism is where the interesting claim lives, and the paper is precise about it. Writing $\mathbf{E}$ for the $t \times m$ token-embedding matrix of a text decoder over $t$ tokens at width $m$, AudioPaLM observes that "the rest of the decoder architecture is completely agnostic to the number of tokens modelled", so admitting audio requires exactly one change: expand $\mathbf{E}$ to $(t + a) \times m$, where $a$ is the audio-token count <!-- cite:22 -->[[22]](#ref-22). Indices $0$ through $t-1$ remain the text tokens; indices $t$ through $t+a-1$ are the new audio rows.

<a id="eq-4"></a><!-- eq:F-4 -->
$$
\mathbf{E}' = \begin{bmatrix} \mathbf{E}_{\text{text}} \\ \mathbf{E}_{\text{audio}} \end{bmatrix} \in \mathbb{R}^{(t+a) \times m}, \qquad \mathbf{E}_{\text{text}}\ \text{inherited}, \quad \mathbf{E}_{\text{audio}}\ \text{newly initialized} \tag{4}
$$

<a id="p-f3-discrete-audio-tokens-and-why-text-competence-transfers-3"></a><!-- para:f3-discrete-audio-tokens-and-why-text-competence-transfers-3 --> **Why this predicts transfer.** Everything above the embedding lookup — every attention block, every MLP, the output projection — is shared between the two token families and inherited from text pretraining. An audio token is not routed down a separate pathway; it is *looked up* into the same residual stream the text tokens occupy, and from the second layer onward the model cannot tell which rows of $\mathbf{E}'$ its inputs came from. So whatever competence the text model has as a function *on that residual stream* — including translating between two languages — is available to any input that lands there, however it entered. The falsifiable prediction: a model trained to translate X→En in text, and separately trained only to *transcribe* X in speech, should translate X speech into English text without ever seeing that pair as a speech-translation example.

<a id="p-f3-discrete-audio-tokens-and-why-text-competence-transfers-4"></a><!-- para:f3-discrete-audio-tokens-and-why-text-competence-transfers-4 --> That is measured. On FLEURS, restricted to languages for which only transcription data was seen — genuinely zero-shot for speech translation — AudioPaLM-2 8B reaches $20.7$ BLEU against $10.0$ for AudioPaLM 8B, with *zero* hours of speech-translation data for those languages in either case <!-- cite:22 -->[[22]](#ref-22). On languages whose speech-translation data *was* seen, the same two models score $28.6$ and $22.4$. The gap between those columns is the price of the transfer; that the ASR-only column is non-trivial at all *is* the transfer. Note what the comparison does not license: the paper's own footnote records that its Whisper reference "has seen AST data for all languages considered", so Whisper's $19.6$ in that column is **not** a zero-shot number, and putting it beside AudioPaLM's $20.7$ as though it were would compare two different quantities. *[established]*

<a id="p-f3-discrete-audio-tokens-and-why-text-competence-transfers-5"></a><!-- para:f3-discrete-audio-tokens-and-why-text-competence-transfers-5 --> **One thing the paper says twice, differently.** Its architecture section describes the new audio rows as "freshly initialized"; its experimental-setup section [§5.1], specifying the actual run, states they "are initialized to 0" <!-- cite:22 -->[[22]](#ref-22). Zero-init is *a* fresh initialization, so the two are compatible — but they are not equally informative, and the architectural description does not disclose the choice the headline results used. It matters because a zero-initialized embedding row is a genuinely different training dynamic from a Gaussian one: it contributes nothing to the residual stream on the first forward pass, so its gradient arrives only through the output-side projection, and the row is revived rather than refined.

<!-- sec:F.4 -->
### <a id="sec-F.4"></a>F.4 Two encoders, one sequence: concatenation and window-level resampling

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-1"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-1 --> Speech recognition and general audio understanding want different features — a speech encoder is trained toward invariances that discard exactly the timbral detail an audio-event classifier needs. SALMONN <!-- cite:21 -->[[21]](#ref-21) resolves this by refusing to choose: it runs a Whisper speech encoder and a BEATs non-speech audio encoder in parallel and concatenates them **along the feature dimension**,

<a id="eq-5"></a><!-- eq:F-5 -->
$$
\mathbf{Z} = \mathrm{Concat}\big(\mathrm{Encoder}_{\text{whisper}}(\mathbf{X}),\ \mathrm{Encoder}_{\text{beats}}(\mathbf{X})\big) \in \mathbb{R}^{T \times (d_w + d_b)} \tag{5}
$$

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-2"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-2 --> Equation <!-- ref:F-5 -->[(5)](#eq-5) is frame-by-frame, which is well-posed only if both encoders emit the *same number of frames*. They do, and not by luck: the paper notes that "both encoders have the same output frame rate of 50Hz" <!-- cite:21 -->[[21]](#ref-21) — the same $50$ Hz that Equation <!-- ref:F-2 -->[(2)](#eq-2) derived for Whisper. No resampling or alignment stage is needed and none is performed. This is worth stating explicitly because the natural expectation is the opposite: two independently trained encoders agreeing on a frame rate looks like a coincidence, and is in fact a shared convention inherited from the $10$ ms hop that Equation <!-- ref:F-1 -->[(1)](#eq-1) started from. Had the rates differed, Equation <!-- ref:F-5 -->[(5)](#eq-5) would need an interpolation stage and the design would be materially more complex.

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-3"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-3 --> **The window-level Q-Former.** Concatenation fixes the feature problem and leaves the length problem: $\mathbf{Z}$ still has $T$ frames, which for $30$ s is the $1500$ of Equation <!-- ref:F-3 -->[(3)](#eq-3). BLIP-2's Q-Former (<!-- secxref:C.1 -->[§C.1](appendix-c-connector-derivations.md#sec-C.1)) compresses a whole image to a fixed token count; applying it to a whole *waveform* would destroy time resolution, since one fixed set of queries cannot represent a signal of unbounded length. SALMONN's fix is to apply it **per window**, segmenting $\mathbf{Z}$ into $L$-frame windows and treating each window "as if the encoder output frames stacked in each window were an image" <!-- cite:21 -->[[21]](#ref-21):

<a id="eq-6"></a><!-- eq:F-6 -->
$$
\mathbf{H} = \big[\,\mathrm{Q\text{-}Former}(\mathbf{Q}, \mathbf{Z}_l)\,\big]_{l=1}^{\lceil T/L \rceil}, \qquad \lvert \mathbf{H} \rvert = \lceil T/L \rceil \times N \tag{6}
$$

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-4"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-4 --> This makes the output length *linear in duration* rather than constant, which is the right call: audio content grows with time, and a constant budget would degrade without bound. With $N = 1$ query and $L = 17$ frames, about $0.33$ s per window <!-- cite:21 -->[[21]](#ref-21), the compression from Equation <!-- ref:F-3 -->[(3)](#eq-3) is roughly $1500 \to 88$, a factor of $17$, and the token rate falls to about $2.9$ tokens per second of audio — cheaper per second than transcribed text at a normal speaking rate.

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-5"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-5 --> **A one-token inconsistency in the source.** The paper reports "88 textual tokens output by Q-Former for a 30-second audio" <!-- cite:21 -->[[21]](#ref-21). Equation <!-- ref:F-6 -->[(6)](#eq-6) as printed does not give that. With the paper's own $T = 30 \times 50 = 1500$, $L = 17$ and $N = 1$,

<a id="eq-7"></a><!-- eq:F-7 -->
$$
\left\lceil \frac{1500}{17} \right\rceil = \lceil 88.24 \rceil = 89 \neq 88 = \left\lfloor \frac{1500}{17} \right\rfloor \tag{7}
$$

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-6"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-6 --> The reported figure is the floor; the printed formula is the ceiling. The ceiling is also what the surrounding prose describes, because the paper explicitly pads "the last window with zeros" — and padding exists precisely to promote a final partial window into a full one, which is the ceiling's job. So the notation and the padding language agree with each other and disagree with the reported number, by exactly one token. The likely cause is a floor in the implementation against a ceiling in the write-up, i.e. the final partial window is dropped rather than padded; a shorter effective $T$ would also explain it, but only for $T \le 1496$, which contradicts the paper's own $50$ Hz. Nothing in this survey turns on one token. The reason to record it is methodological: this is the *only* token count in Appendix F that can be checked against a second independent statement by the same paper, and it fails that check. Single-source token arithmetic should be treated as unverified whenever no second statement constrains it.

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-7"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-7 --> **Task over-fitting, and the sharpest piece of evidence in this appendix.** SALMONN reports that after instruction tuning the model "exhibits limited or almost no ability to perform untrained cross-modal tasks" <!-- cite:21 -->[[21]](#ref-21) — it responds as though asked to transcribe, whatever it was actually asked. The paper's account decomposes the instructed distribution by Bayes' rule,

<a id="eq-8"></a><!-- eq:F-8 -->
$$
P_\Lambda(\mathbf{Y} \mid \mathbf{X}, \mathbf{I}) = \frac{P_\Lambda(\mathbf{Y} \mid \mathbf{X})\, P_\Lambda(\mathbf{I} \mid \mathbf{Y}, \mathbf{X})}{P_\Lambda(\mathbf{I} \mid \mathbf{X})} \tag{8}
$$

<a id="p-f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-8"></a><!-- para:f4-two-encoders-one-sequence-concatenation-and-window-level-resampling-8 --> isolating an *intrinsic conditional LM* $P_\Lambda(\mathbf{Y} \mid \mathbf{X})$ that instruction tuning has biased toward short, deterministic, transcription-shaped responses, which then suppresses any novel instruction needing a different response shape. The compelling part is the test. Because that bias is carried by the LoRA adapter, merely **discounting the LoRA scaling factor at inference** should release it with no retraining at all — and halving the factor from $4.0$ to about $2.0$ does exactly that, at which point the model "suddenly emerges with cross-modal reasoning abilities" <!-- cite:21 -->[[21]](#ref-21). A mechanistic account that predicts the effect of a single knob, and is then confirmed by turning that knob, is stronger evidence than the benchmark tables around it, and is rarer in this literature than it should be. The shipped remedy applies the same insight at training time — *activation tuning*, twelve stories over twelve steps, one sample each — moving speech-audio-QA accuracy from $0.19$ to $0.41$ and story-task diversity from $7.77$ to $82.57$ while transcription word-error rate holds at $2.1$ <!-- cite:21 -->[[21]](#ref-21). *[established]*

<!-- sec:F.5 -->
### <a id="sec-F.5"></a>F.5 Video: the token-budget equation and its three levers

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-1"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-1 --> Video's cost is <!-- secxref:8.1 -->[§8.1](inference-and-serving.md#sec-8.1)'s problem multiplied by the frame count. Sampling a clip to $F$ frames and encoding each into $N_v^{\text{frame}}$ patch tokens gives

<a id="eq-9"></a><!-- eq:F-9 -->
$$
N_{\text{video}} = F \cdot N_v^{\text{frame}} = F \cdot \frac{HW}{P^2} \tag{9}
$$

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-2"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-2 --> before any reduction, the second form substituting the patch-count identity of <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2). Written this way, Equation <!-- ref:F-9 -->[(9)](#eq-9) exposes the three independent levers the field actually pulls — and shows they are not interchangeable.

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-3"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-3 --> **Lever 1, lower $F$ (sparse sampling).** Video-LLaVA "uniformly sample[s] 8 frames from each video" at $224 \times 224$ <!-- cite:23 -->[[23]](#ref-23), a *fixed* budget independent of duration, and its own authors state the consequence: this "results in the loss of detailed information from long videos" <!-- cite:23 -->[[23]](#ref-23). Note that a fixed frame count is not a sampling *rate* at all — eight frames is $0.8$ fps on a ten-second clip and $0.001$ fps on a two-hour film, so the same model is a dense sampler and a nearly blind one depending only on input length.

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-4"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-4 --> **Lever 2, lower $N_v^{\text{frame}}$ (spatial merging).** Qwen2-VL compresses "adjacent $2 \times 2$ tokens into a single token" with an MLP after the ViT <!-- cite:7 -->[[7]](#ref-7), a $4\times$ reduction. Its worked case closes exactly: a $224 \times 224$ image at patch size $14$ gives $(224/14)^2 = 256$ patch tokens, merged to $64$, plus two boundary tokens, for the $66$ the paper states <!-- cite:7 -->[[7]](#ref-7). That the arithmetic closes is why this number is quoted and the Video-LLaVA per-frame count below is not.

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-5"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-5 --> **Lever 3, cap the product (dynamic resolution).** Qwen2-VL samples video "at two frames per second" — a genuine rate, unlike lever 1 — then "dynamically adjust[s] the resolution of each video frame, limiting the total number of tokens per video to 16384" <!-- cite:7 -->[[7]](#ref-7). This inverts the design: instead of letting Equation <!-- ref:F-9 -->[(9)](#eq-9) determine the cost, the cost is fixed and Equation <!-- ref:F-9 -->[(9)](#eq-9) is solved for the resolution. The price is that per-frame fidelity degrades silently as clips lengthen — at two frames per second a $16384$-token budget allows about $273$ tokens per frame for a $30$ s clip and about $27$ for a $300$ s one.

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-6"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-6 --> **Worked example — where the wall actually is.** Take the $336$-px, patch-$14$ frame of <!-- secref:F.2 -->[§F.2](#sec-F.2), so $N_v^{\text{frame}} = 576$, and sample at two frames per second:

| Clip | $F$ | $N_{\text{video}}$ by Eq. <!-- ref:F-9 -->[(9)](#eq-9) | Verdict |
|---|---|---|---|
| $8$ frames (Video-LLaVA) | $8$ | $4{,}608$ | fits any modern context |
| $30$ s | $60$ | $34{,}560$ | fits, but dominates the context |
| $5$ min | $600$ | $345{,}600$ | exceeds most deployed contexts |
| $2$ h | $14{,}400$ | $8{,}294{,}400$ | infeasible by three orders of magnitude |

<a id="p-f5-video-the-token-budget-equation-and-its-three-levers-7"></a><!-- para:f5-video-the-token-budget-equation-and-its-three-levers-7 --> The last row is the long-video problem stated numerically, and no single lever closes a $10^3$ gap: lever 2 buys $4\times$, lever 1 buys whatever temporal coverage you are willing to surrender, and lever 3 buys a fixed ceiling by spending per-frame detail. That is why long video is an *architecture* question in <!-- secxref:13 -->[§13](open-problems-and-roadmap.md#sec-13) rather than a serving-configuration question. *[established]*

<!-- sec:F.6 -->
### <a id="sec-F.6"></a>F.6 M-RoPE: giving a token a time coordinate

<a id="p-f6-m-rope-giving-a-token-a-time-coordinate-1"></a><!-- para:f6-m-rope-giving-a-token-a-time-coordinate-1 --> Sparse or merged, the surviving tokens must still carry *when* they occurred. Qwen2-VL's M-RoPE deconstructs the rotary position embedding "into three components: temporal, height, and width" <!-- cite:7 -->[[7]](#ref-7), so a token's position is a triple rather than a scalar index. The assignment rules are modality-dependent and, read carefully, are what make the scheme backward-compatible: "For text inputs, these components utilize identical position IDs, making M-RoPE functionally equivalent to 1D-RoPE" <!-- cite:7 -->[[7]](#ref-7); for an image the temporal component is constant across the image's tokens while height and width vary; for video the temporal component increments per frame.

<a id="p-f6-m-rope-giving-a-token-a-time-coordinate-2"></a><!-- para:f6-m-rope-giving-a-token-a-time-coordinate-2 --> The claimed payoff is not primarily expressiveness but *range*: M-RoPE "reduces the value of position IDs for images and videos, enabling the model to extrapolate to longer sequences during inference" <!-- cite:7 -->[[7]](#ref-7). The mechanism is arithmetic. Under 1-D RoPE the $60$-frame, $576$-token-per-frame clip of <!-- secref:F.5 -->[§F.5](#sec-F.5) consumes $34{,}560$ consecutive position indices, pushing the model far outside the index range it was trained on. Under M-RoPE that same clip consumes $60$ temporal indices and $24$ each of height and width, so every component stays small and none of them extrapolates. Position-index exhaustion — one of the two things that breaks long video, the other being Equation <!-- ref:F-9 -->[(9)](#eq-9) itself — is dissolved by re-coordinatizing rather than by extending anything.

<a id="p-f6-m-rope-giving-a-token-a-time-coordinate-3"></a><!-- para:f6-m-rope-giving-a-token-a-time-coordinate-3 --> **What the source does not tell us.** The paper never states how the head dimension's frequency channels are *divided* among the three components — equal thirds, weighted toward the temporal axis, or otherwise. That allocation is not a detail: it fixes the relative resolution of time against space, and a reader trying to reimplement M-RoPE cannot proceed without it. It is absent from the M-RoPE subsection and from its figure, so it is left open here rather than filled with a plausible guess.

<!-- sec:F.7 -->
### <a id="sec-F.7"></a>F.7 What the primary sources do not state

<a id="p-f7-what-the-primary-sources-do-not-state-1"></a><!-- para:f7-what-the-primary-sources-do-not-state-1 --> Four quantities this appendix would use are simply not in the papers that would have to supply them. Recording them explicitly is the point: an unstated number filled in from a plausible memory is exactly the failure this survey's citation discipline exists to prevent, and each of these is individually plausible enough to have been guessed without anyone noticing.

| Quantity | Where it would live | Status |
|---|---|---|
| Whisper's encoder sequence length ($1500$) | <!-- cite:19 -->[[19]](#ref-19), main text or hyperparameter appendix | never printed; **derived** in Eq. <!-- ref:F-3 -->[(3)](#eq-3) from stated constants, and flagged there as derived |
| M-RoPE frequency-channel allocation | <!-- cite:7 -->[[7]](#ref-7), M-RoPE subsection and figure | absent; **not supplied here** |
| Video-LLaVA tokens per frame | <!-- cite:23 -->[[23]](#ref-23), model settings / training details | absent. The encoder name (OpenCLIP-L/14) and the $224$ resize target imply $256$, but the paper never performs or confirms that arithmetic, so the per-video total is an estimate and is **not** cited as a source number |
| AudioPaLM USM-v2 token rate and vocabulary size | <!-- cite:22 -->[[22]](#ref-22), tokenization subsection | stated for the w2v-BERT and USM-v1 variants ($25$ Hz, $1024$); **not restated** for USM-v2 |

<a id="p-f7-what-the-primary-sources-do-not-state-2"></a><!-- para:f7-what-the-primary-sources-do-not-state-2 --> Two of these would stall a reimplementation and none is load-bearing for any claim this survey makes. The pattern is consistent enough to name: papers reliably state the constants they *tuned* and reliably omit the constants that *fell out* — which is precisely backwards for a reader reconstructing the system, because the derived quantities are the ones that decide whether it fits in memory.
