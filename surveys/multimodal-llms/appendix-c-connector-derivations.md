<!-- sec:C -->
## <a id="sec-C"></a>C Connector derivations

<a id="p-c-connector-derivations-1"></a><!-- para:c-connector-derivations-1 --> This appendix completes the two connectors § <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3)–<!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4) introduced but did not fully derive: BLIP-2's Q-Former, whose three pretraining objectives share one set of queries by switching attention masks, and Flamingo's gated cross-attention, whose stability rests on a single zero-initialized scalar.

<!-- sec:C.1 -->
### <a id="sec-C.1"></a>C.1 The Q-Former's three objectives

<a id="p-c1-the-q-formers-three-objectives-1"></a><!-- para:c1-the-q-formers-three-objectives-1 --> BLIP-2 <!-- cite:4 -->[[4]](#ref-4) pretrains its $32$ learned queries with three objectives that share input format and weights and differ *only* in the self-attention mask between queries and text — the mask is how one module learns three behaviors.

<a id="p-c1-the-q-formers-three-objectives-2"></a><!-- para:c1-the-q-formers-three-objectives-2 --> **Image-Text Contrastive (ITC).** Align the query outputs $\mathbf{Z}\in\mathbb{R}^{32\times d_q}$ with the text's `[CLS]` representation $t$. Because there are $32$ query vectors but one text vector, the image-text similarity is the *best-matching* query:

<a id="eq-1"></a><!-- eq:C-1 -->
$$
s(I,T) = \max_{m\in\{1,\dots,32\}} \mathrm{sim}(\mathbf{z}_m,\, t) \tag{1}
$$

<a id="p-c1-the-q-formers-three-objectives-3"></a><!-- para:c1-the-q-formers-three-objectives-3 --> trained with an InfoNCE objective (§ <!-- secxref:B -->[§B](appendix-b-contrastive-infonce.md#sec-B)) over in-batch negatives — affordable because the frozen encoder lets many samples fit per device, so no momentum queue is needed. A *unimodal* mask forbids queries and text from attending to each other, preventing information leakage that would trivialize the matching.

<a id="p-c1-the-q-formers-three-objectives-4"></a><!-- para:c1-the-q-formers-three-objectives-4 --> **Image-grounded Text Generation (ITG).** Train the queries to extract the visual information *needed to generate* the caption. Since the queries are the only bridge to the frozen image features, forcing them to support generation makes them capture caption-relevant content. A *multimodal-causal* mask lets queries attend to each other (but not to text), and each text token attend to all queries and the preceding text — the causal structure of generation, with the image available throughout.

<a id="p-c1-the-q-formers-three-objectives-5"></a><!-- para:c1-the-q-formers-three-objectives-5 --> **Image-Text Matching (ITM).** A binary "is this pair matched?" classifier. A *bidirectional* mask lets all queries and text tokens see each other, so each output query embedding is multimodal; a two-class head scores each, and the logits are averaged. Hard-negative mining (pairs the ITC stage found confusable) sharpens the decision. The three masks turn one $32$-query module into a contrastive aligner, a conditional generator, and a matcher — the bottleneck $\mathbf{Z}$ of § <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3) (Eq 2 there) is what all three squeeze the image through.

<!-- sec:C.2 -->
### <a id="sec-C.2"></a>C.2 The Perceiver Resampler as cross-attention

<a id="p-c2-the-perceiver-resampler-as-cross-attention-1"></a><!-- para:c2-the-perceiver-resampler-as-cross-attention-1 --> Flamingo's resampler (§ 3.3) is a cross-attention block with a twist: the *queries* are a fixed bank of $M$ learned latent vectors $\mathbf{L}$, and the *keys and values* are the variable-length visual features $\mathbf{X}$ concatenated with the latents themselves. The output inherits the query bank's shape $M\times d_v$, so however many features arrive, exactly $M$ come out — the learned down-sampler of § 3.3. For video, the spatio-temporal feature grid (frames at $1$ FPS, with learned temporal embeddings) is flattened into $\mathbf{X}$ before resampling, which is why one mechanism handles images and video identically: both are just a variable-length set of vectors to be summarized into $M$.

<!-- sec:C.3 -->
### <a id="sec-C.3"></a>C.3 Gated cross-attention dense, in full

<a id="p-c3-gated-cross-attention-dense-in-full-1"></a><!-- para:c3-gated-cross-attention-dense-in-full-1 --> The GATED XATTN-DENSE block of § <!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4) (Eq 3 there) is inserted *between* each pair of frozen language-model layers, and runs four steps on the running representation $\mathbf{y}$: a gated cross-attention to the visual tokens, a gated dense feed-forward, then the original frozen self-attention and feed-forward. The two new sublayers are scaled by $\tanh(\alpha)$ with per-layer learnable scalars $\alpha$ initialized to zero, so at initialization $\tanh(0)=0$ makes both new sublayers vanish and the block is the identity — the conditioned model reproduces the frozen LM exactly (§ 3.4 worked example). As training proceeds each layer opens its gate independently, and because the gate is *per-layer*, the model learns *where* in its depth to admit visual information rather than being forced to use it uniformly. The cost, as § 3.4 noted, is that these blocks are many new parameters and the frozen LM cannot adapt its own weights to vision — it can only react through the gated ports. This is the deep-fusion counterpart to the Q-Former's bottleneck: where BLIP-2 compresses the image into a soft prompt the LM reads at its input, Flamingo leaves the image uncompressed and lets the LM *reach out* to it at every layer.
