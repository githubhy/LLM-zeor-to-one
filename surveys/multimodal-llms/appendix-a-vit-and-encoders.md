<!-- sec:A -->
## <a id="sec-A"></a>A ViT and encoder internals

<a id="p-a-vit-and-encoder-internals-1"></a><!-- para:a-vit-and-encoder-internals-1 --> This appendix supplies the encoder-specific machinery that § <!-- secxref:2.3 -->[§2.3](fundamentals.md#sec-2.3) deferred: the multi-head bookkeeping, the pre-norm block's rationale, the GELU MLP, the class-token readout, and the projection head that turns a ViT into a CLIP/SigLIP encoder. The base scaled-dot-product attention is assumed; its first-principles derivation is in the companion [attention appendix](../llms-for-coding/appendix-a-qkv-first-principles.md).

<!-- sec:A.1 -->
### <a id="sec-A.1"></a>A.1 Multi-head self-attention, the encoder version

<a id="p-a1-multi-head-self-attention-the-encoder-version-1"></a><!-- para:a1-multi-head-self-attention-the-encoder-version-1 --> Inside the MSA sublayer of the § 2.3 encoder block, the patch sequence $\mathbf{z}\in\mathbb{R}^{N\times d_v}$ is processed by $h$ attention heads in parallel. Each head $i$ projects the sequence to its own queries, keys, and values, runs scaled-dot-product attention, and the heads are concatenated and mixed by an output projection:

<a id="eq-1"></a><!-- eq:A-1 -->
$$
\mathrm{head}_i = \mathrm{softmax}\!\left(\frac{(\mathbf{z}W_Q^i)(\mathbf{z}W_K^i)^\top}{\sqrt{d_h}}\right)\mathbf{z}W_V^i, \qquad \mathrm{MSA}(\mathbf{z}) = \big[\mathrm{head}_1;\cdots;\mathrm{head}_h\big]W_O \tag{1}
$$

<a id="p-a1-multi-head-self-attention-the-encoder-version-2"></a><!-- para:a1-multi-head-self-attention-the-encoder-version-2 --> with $W_Q^i, W_K^i, W_V^i\in\mathbb{R}^{d_v\times d_h}$, per-head width $d_h = d_v/h$, and $W_O\in\mathbb{R}^{d_v\times d_v}$. Two encoder-specific points distinguish this from a language model's attention. First, there is **no causal mask**: row $j$ of the softmax attends over *all* $N$ patches, left and right, because an image has no temporal arrow — the encoder is bidirectional (§ 2.3). Second, multiple heads let the encoder run several distinct "matched filters" at once — one head may track texture continuity, another long-range object structure — and the output projection $W_O$ recombines them; the per-head dimension $d_h$ is small precisely so that $h$ heads fit in the same $d_v$ budget.

<!-- sec:A.2 -->
### <a id="sec-A.2"></a>A.2 Pre-norm and the residual stream

<a id="p-a2-pre-norm-and-the-residual-stream-1"></a><!-- para:a2-pre-norm-and-the-residual-stream-1 --> The § 2.3 encoder block places layer normalization *before* each sublayer and adds the residual *after* — the pre-norm arrangement. The reason is gradient stability in deep stacks: with pre-norm, the residual path from input to output is an unobstructed identity (each block adds $\mathrm{MSA}(\mathrm{LN}(\cdot))$ to the running stream rather than normalizing the sum), so the gradient reaches early layers undiminished and very deep encoders train without the warmup gymnastics post-norm needs. The running sum down the stack is the *residual stream*: each block reads the current representation, computes a correction, and writes it back, so a patch token's vector accumulates evidence layer by layer. The class token (§ A.4) is one more lane of this stream, distinguished only by carrying no patch content at the input.

<!-- sec:A.3 -->
### <a id="sec-A.3"></a>A.3 The MLP sublayer

<a id="p-a3-the-mlp-sublayer-1"></a><!-- para:a3-the-mlp-sublayer-1 --> The second sublayer is a position-wise two-layer MLP with a GELU nonlinearity, applied identically to every token: $\mathrm{MLP}(\mathbf{x}) = \mathrm{GELU}(\mathbf{x}W_1 + b_1)W_2 + b_2$, with $W_1\in\mathbb{R}^{d_v\times d_{\mathrm{ff}}}$ expanding to a wider hidden width ($d_{\mathrm{ff}}$ is typically $4d_v$) and $W_2$ projecting back. Where attention *mixes* information across tokens, the MLP *transforms* each token's features in place; the alternation of the two — mix, then transform, repeated $L$ times — is the transformer's basic rhythm, unchanged from text to vision. GELU, a smooth gated approximation to ReLU, is the activation ViT inherits from the language-model lineage it deliberately copies.

<!-- sec:A.4 -->
### <a id="sec-A.4"></a>A.4 Class token, patch tokens, and resolution change

<a id="p-a4-class-token-patch-tokens-and-resolution-change-1"></a><!-- para:a4-class-token-patch-tokens-and-resolution-change-1 --> The prepended class token's final-layer state $\mathbf{z}_L^0$, after a last layer norm, is the single-vector image representation $\mathbf{y}$ (§ 2.2). It works as a readout register: carrying no patch content itself, its only way to become informative is to attend to the patches, so after $L$ layers it holds a learned pooling of the whole image. This is the vector CLIP aligns to text (§ <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)) — and, as § 2.4 noted, its single-vector nature is a bottleneck, which is why instruction-tuned VLMs feed the LLM the *grid* of patch tokens $\mathbf{z}_L^{1:N}$ instead. Changing input resolution changes $N$, and because the learned 1-D position embeddings $\mathbf{E}_{\text{pos}}$ were trained for one specific grid, they must be **2-D interpolated** to the new grid before fine-tuning at a higher resolution — the one place a 2-D spatial prior is manually reinjected into an otherwise shape-agnostic model, and a routine source of fine-tuning bugs.

<!-- sec:A.5 -->
### <a id="sec-A.5"></a>A.5 From ViT to a CLIP/SigLIP encoder

<a id="p-a5-from-vit-to-a-clipsiglip-encoder-1"></a><!-- para:a5-from-vit-to-a-clipsiglip-encoder-1 --> A bare ViT outputs $d_v$-dimensional features; turning it into a *language-aligned* encoder adds a projection into the joint embedding space and a pooling choice. CLIP <!-- cite:1 -->[[1]](#ref-1) takes the class-token representation, applies a single **linear projection** $W_I$ into the shared $d_e$-dimensional space, and $L2$-normalizes (§ 2.4); it deliberately avoids a nonlinear projection head, which the authors found co-adapts to the image-only self-supervised setting and does not help here. SigLIP <!-- cite:15 -->[[15]](#ref-15) keeps the same ViT backbone and projection structure and changes only the *loss* (the sigmoid objective of § <!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)), which is why a "SigLIP encoder" is a drop-in replacement for a "CLIP encoder" everywhere in this survey — same architecture, cheaper training, language-aligned $d_v$-dimensional patch features that a connector (§ <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3)) maps into the LLM. The audio encoder of § <!-- secxref:7.1 -->[§7.1](modality-breadth.md#sec-7.1) is the same template over a spectrogram rather than a patch grid.
