## The Modern Dense Block: a 7B Llama-Family Model

<a id="p-the-modern-dense-block-a-7b-llama-family-model-1"></a><!-- para:the-modern-dense-block-a-7b-llama-family-model-1 --> GPT-2 (Appendix D) is the canonical decoder; the models that power today's coding assistants — Llama, Mistral, Qwen, DeepSeek's dense variants — are GPT-2 with four targeted substitutions, each fixing a specific inefficiency. The skeleton is untouched: a pre-norm residual stream, $L$ stacked blocks of an attention sublayer and a feed-forward sublayer, a final norm, an unembedding, trained by the same cross-entropy, backpropagation, and Adam of Appendices <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3)–<!-- secxref:C.4 -->[§C.4](appendix-c-toy-transformer.md#sec-C.4). What changes is *inside* the boxes: LayerNorm becomes RMSNorm, learned positional embeddings become rotary embeddings (RoPE) applied inside attention, the GELU MLP becomes a gated SwiGLU MLP, and — at the larger sizes — full multi-head attention becomes grouped-query attention. This chapter derives all four from first principles, each forward *and* backward, and validates every gradient against a finite-difference check before stating it (the engine is `figures/appendix-e-validate.py`; quoted residuals are its output).

<a id="p-the-modern-dense-block-a-7b-llama-family-model-2"></a><!-- para:the-modern-dense-block-a-7b-llama-family-model-2 --> ![Two pre-norm decoder blocks side by side. Left: the GPT-2 block — LayerNorm then multi-head attention then a residual add, then LayerNorm then a GELU MLP then a residual add. Right: the modern Llama block with the same shape but RMSNorm in place of LayerNorm, GQA plus RoPE in place of plain attention, and a SwiGLU MLP in place of the GELU MLP. A central ledger lists the four substitutions with one-line reasons, and notes the skeleton — pre-norm, residual stream, same forward/backward/Adam — is unchanged.](figures/appendix-e-block.svg)

<a id="p-the-modern-dense-block-a-7b-llama-family-model-3"></a><!-- para:the-modern-dense-block-a-7b-llama-family-model-3 --> **Figure E.1.** The modern dense block is the GPT-2 block with four substitutions, the skeleton unchanged. Each is derived in this chapter: RMSNorm (E.2), RoPE (E.3), SwiGLU (E.4), GQA (E.5). Regenerate via `surveys/llms-for-coding/figures/appendix-e-block.py`.

<!-- sec:E.1 -->
### <a id="sec-E.1"></a>E.1 The Sourced Sizes

<a id="p-e1-the-sourced-sizes-1"></a><!-- para:e1-the-sourced-sizes-1 --> Llama is released at four sizes, whose only varying dimensions are again the width $d$, the head count $H$, and the depth $L$ (Table 2 of <!-- cite:65 --> [[65]](references.md#ref-65)):

| size | params | $d$ | heads $H$ | $d_{\text{head}}$ | layers $L$ |
|---|---|---|---|---|---|
| 7B | 6.7B | 4096 | 32 | 128 | 32 |
| 13B | 13.0B | 5120 | 40 | 128 | 40 |
| 33B | 32.5B | 6656 | 52 | 128 | 60 |
| 65B | 65.2B | 8192 | 64 | 128 | 80 |

<a id="p-e1-the-sourced-sizes-2"></a><!-- para:e1-the-sourced-sizes-2 --> Two structural facts read off the table. First, the per-head width is pinned at $d_{\text{head}}=d/H=128$ across every size — twice GPT-2's $64$ — so scaling adds heads and layers, not wider heads. Second, the feed-forward hidden width is set to $\tfrac{8}{3}d$ rather than GPT-2's $4d$ (<!-- cite:65 --> [[65]](references.md#ref-65), Sec 2.2); for the 7B that is $\tfrac{8}{3}\cdot 4096 \approx 10923$, rounded to $11008$ (a multiple of $256$) in the released configuration. The $\tfrac{8}{3}$ factor is derived in <!-- secref:E.4 -->[§E.4](#sec-E.4): it is exactly what keeps the *three-matrix* SwiGLU MLP at the same parameter count as the *two-matrix* GELU MLP it replaces. The token vocabulary is a $32$k-class SentencePiece byte-pair encoding <!-- cite:65 --> [[65]](references.md#ref-65); at $d=4096$ the embedding is $\approx 0.13$B parameters, under $2\%$ of the 7B total, which is — as in <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3) — dominated by its blocks.

<!-- sec:E.2 -->
### <a id="sec-E.2"></a>E.2 RMSNorm: Normalization Without Re-Centering

<a id="p-e2-rmsnorm-normalization-without-re-centering-1"></a><!-- para:e2-rmsnorm-normalization-without-re-centering-1 --> LayerNorm (used by the toy of <!-- secxref:C.2 -->[§C.2](appendix-c-toy-transformer.md#sec-C.2)) subtracts the mean and divides by the standard deviation. RMSNorm keeps only the second operation: it rescales a vector by its root-mean-square and drops the mean subtraction entirely. For an input $\mathbf{x}\in\mathbb{R}^{d}$ with a learned per-channel gain $\mathbf{g}$, writing the normalizer as $r = \sqrt{\tfrac{1}{d}\sum_{j}x_j^2 + \epsilon}$,

<a id="eq-1"></a><!-- eq:E-1 -->
$$
y_i = g_i\,\frac{x_i}{r},\qquad r = \sqrt{\frac{1}{d}\sum_{j=1}^{d} x_j^2 + \epsilon}. \tag{1}
$$

<a id="p-e2-rmsnorm-normalization-without-re-centering-2"></a><!-- para:e2-rmsnorm-normalization-without-re-centering-2 --> The backward pass differentiates Equation <!-- ref:E-1 -->[(1)](#eq-1) through the shared scalar $r$. Writing the gain-weighted upstream gradient $a_i = g_i\,\partial\mathcal{L}/\partial y_i$, and using $\partial r/\partial x_k = x_k/(d\,r)$, every output couples to every input only through $r$, giving the validated gradients

<a id="eq-2"></a><!-- eq:E-2 -->
$$
\begin{aligned}
\frac{\partial\mathcal{L}}{\partial x_k}
&= \frac{1}{r}\left( a_k - \frac{x_k}{d\,r^2}\sum_{i=1}^{d} a_i\,x_i \right), &&\text{(chain rule through $y_i=g_i x_i/r$ and $r(\mathbf{x})$)}\\[2pt]
\frac{\partial\mathcal{L}}{\partial g_i}
&= \frac{\partial\mathcal{L}}{\partial y_i}\,\frac{x_i}{r}. &&\text{(gain enters $y_i$ linearly)}
\end{aligned} \tag{2}
$$

<a id="p-e2-rmsnorm-normalization-without-re-centering-3"></a><!-- para:e2-rmsnorm-normalization-without-re-centering-3 --> The check in `appendix-e-validate.py` matches Equation <!-- ref:E-2 -->[(2)](#eq-2) to central finite differences at relative error $4\times10^{-10}$ ($\partial\mathcal{L}/\partial\mathbf{x}$) and $4\times10^{-10}$ ($\partial\mathcal{L}/\partial\mathbf{g}$). The structure is the LayerNorm Jacobian of <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3) with the mean-removal term deleted.

> <a id="p-e2-rmsnorm-normalization-without-re-centering-4"></a><!-- para:e2-rmsnorm-normalization-without-re-centering-4 --> **Note — why dropping the mean is safe.** *Geometrically,* Equation <!-- ref:E-1 -->[(1)](#eq-1) projects $\mathbf{x}$ onto the sphere of radius $\sqrt{d}$ (times the gain), fixing the scale that otherwise makes gradients explode or vanish with depth; *re-centering* — removing $\bar{x}$ — turns out to contribute little once a residual stream already keeps activations roughly centered, so RMSNorm buys one fewer reduction, one fewer subtraction per element, and no mean-gradient term, at no measured quality cost. It is the normalization of choice in every model in <!-- secref:E.1 -->[§E.1](#sec-E.1).

<!-- sec:E.3 -->
### <a id="sec-E.3"></a>E.3 RoPE: Position as Rotation

<a id="p-e3-rope-position-as-rotation-1"></a><!-- para:e3-rope-position-as-rotation-1 --> GPT-2 adds a learned vector $\mathbf{p}_t$ to the token embedding (<!-- secxref:D.1 -->[§D.1](appendix-d-gpt2.md#sec-D.1)), an *absolute* code that does not extrapolate past the trained length. Rotary Position Embedding (RoPE) instead encodes position by *rotating* the query and key vectors, in fixed two-dimensional planes, by an angle proportional to the token's position <!-- cite:66 --> [[66]](references.md#ref-66). Pairing up coordinates $(2j,2j{+}1)$ and assigning each pair a frequency $\theta_j = b^{-2j/d}$ (base $b=10^4$), the vector at position $p$ is rotated pair-by-pair:

<a id="eq-3"></a><!-- eq:E-3 -->
$$
\begin{pmatrix} \tilde{x}_{2j} \\ \tilde{x}_{2j+1} \end{pmatrix}
= \underbrace{\begin{pmatrix} \cos p\theta_j & -\sin p\theta_j \\ \sin p\theta_j & \cos p\theta_j \end{pmatrix}}_{R(p\theta_j)}
\begin{pmatrix} x_{2j} \\ x_{2j+1} \end{pmatrix}. \tag{3}
$$

<a id="p-e3-rope-position-as-rotation-2"></a><!-- para:e3-rope-position-as-rotation-2 --> The point of rotating rather than adding is what happens in the attention score. Because rotation matrices satisfy $R(\alpha)^{\top}R(\beta) = R(\beta-\alpha)$, the dot product of a query at position $m$ with a key at position $n$ — the quantity the softmax of <!-- secxref:A.6 -->[§A.6](appendix-a-qkv-first-principles.md#sec-A.6) consumes — depends on their positions *only through the offset* $m-n$:

<a id="eq-4"></a><!-- eq:E-4 -->
$$
\langle R_m\,\mathbf{q},\; R_n\,\mathbf{k}\rangle
= \mathbf{q}^{\top} R(m\Theta)^{\top} R(n\Theta)\,\mathbf{k}
= \mathbf{q}^{\top} R\!\left((n-m)\Theta\right)\mathbf{k}
= g(\mathbf{q},\mathbf{k},\,m-n), \tag{4}
$$

<a id="p-e3-rope-position-as-rotation-3"></a><!-- para:e3-rope-position-as-rotation-3 --> where $R_p$ stacks the per-pair rotations of Equation <!-- ref:E-3 -->[(3)](#eq-3). Equation <!-- ref:E-4 -->[(4)](#eq-4) is the whole idea: absolute positions enter, but only their *difference* survives into the score, so the model sees *relative* position for free, with no learned position table and graceful behavior beyond the training length. The backward pass is trivial — $R_p$ is orthogonal, so the gradient is the same rotation transposed, $R_p^{\top} = R_{-p}$ — which is why RoPE adds no parameters and negligible compute. Figure E.2 is the numerical proof: evaluating Equation <!-- ref:E-4 -->[(4)](#eq-4) at three anchor positions $n$ with the same offset gives identical scores to relative error $9\times10^{-16}$.

<a id="p-e3-rope-position-as-rotation-4"></a><!-- para:e3-rope-position-as-rotation-4 --> ![Two panels. Left: a query vector drawn at positions 0, 1, 2, each a rotation of the previous by a fixed angle, alongside a key vector at position 0, illustrating that position acts by rotation in a 2-D plane. Right: the attention score as a function of the offset m minus n, plotted for three different key-anchor positions n equals 0, 4, 9; all three sets of markers fall exactly on a single reference curve, with maximum spread 9e-16, showing the score depends only on the offset.](figures/appendix-e-rope.svg)

<!-- sec:E.3-figure-e -->
<a id="p-e3-rope-position-as-rotation-5"></a><!-- para:e3-rope-position-as-rotation-5 --> <a id="sec-E.3-figure-e"></a>**Figure E.2.** RoPE encodes position as rotation. *Left:* a query rotates by $p\theta$ at position $p$. *Right:* the score $\langle R_m\mathbf{q},R_n\mathbf{k}\rangle$ collapses onto a single curve in the offset $m-n$ regardless of the absolute anchor — the relative-position property of Equation <!-- ref:E-4 -->[(4)](#eq-4), verified to $9\times10^{-16}$. Regenerate via `surveys/llms-for-coding/figures/appendix-e-rope.py`.

<!-- sec:E.4 -->
### <a id="sec-E.4"></a>E.4 SwiGLU: a Gated Feed-Forward Network

<a id="p-e4-swiglu-a-gated-feed-forward-network-1"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-1 --> The GELU MLP of <!-- secxref:D.2 -->[§D.2](appendix-d-gpt2.md#sec-D.2) applies one nonlinearity to one projection. SwiGLU splits the up-projection into two parallel maps — a *gate* and a *value* — passes the gate through the SiLU activation $\mathrm{SiLU}(z)=z\,\sigma(z)$, and multiplies them elementwise before projecting down. With weights $W_g, W_u \in \mathbb{R}^{d\times d_{ff}}$ and $W_d \in \mathbb{R}^{d_{ff}\times d}$, the forward pass on a row $\mathbf{x}$ is

<a id="eq-5"></a><!-- eq:E-5 -->
$$
\mathbf{y} = \Big(\, \mathrm{SiLU}(\mathbf{x}W_g)\;\odot\;(\mathbf{x}W_u) \,\Big)\,W_d, \tag{5}
$$

<a id="p-e4-swiglu-a-gated-feed-forward-network-2"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-2 --> with $\odot$ the elementwise product. Writing $\mathbf{a}=\mathbf{x}W_g$, $\mathbf{u}=\mathbf{x}W_u$, and $\mathbf{h}=\mathrm{SiLU}(\mathbf{a})\odot\mathbf{u}$, the backward pass threads the upstream gradient $\mathrm{d}\mathbf{y}$ back through the down-projection, the elementwise gate, and the two parallel projections:

<a id="eq-6"></a><!-- eq:E-6 -->
$$
\begin{aligned}
\mathrm{d}\mathbf{h} &= \mathrm{d}\mathbf{y}\,W_d^{\top}, \qquad \mathrm{d}W_d = \mathbf{h}^{\top}\mathrm{d}\mathbf{y}, &&\text{(linear down-projection)}\\[2pt]
\mathrm{d}\mathbf{u} &= \mathrm{d}\mathbf{h}\odot\mathrm{SiLU}(\mathbf{a}), \qquad
\mathrm{d}\mathbf{a} = \big(\mathrm{d}\mathbf{h}\odot\mathbf{u}\big)\odot \mathrm{SiLU}'(\mathbf{a}), &&\text{(product rule on the gate $\odot$)}\\[2pt]
\mathrm{d}W_g &= \mathbf{x}^{\top}\mathrm{d}\mathbf{a}, \quad \mathrm{d}W_u = \mathbf{x}^{\top}\mathrm{d}\mathbf{u}, \quad
\mathrm{d}\mathbf{x} = \mathrm{d}\mathbf{a}\,W_g^{\top} + \mathrm{d}\mathbf{u}\,W_u^{\top}, &&\text{(two linear branches sum at $\mathbf{x}$)}
\end{aligned} \tag{6}
$$

<a id="p-e4-swiglu-a-gated-feed-forward-network-3"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-3 --> with $\mathrm{SiLU}'(z)=\sigma(z) + z\,\sigma(z)\big(1-\sigma(z)\big)$. All four gradients in Equation <!-- ref:E-6 -->[(6)](#eq-6) match finite differences at relative error below $3\times10^{-9}$ in `appendix-e-validate.py`. The gate $\mathrm{SiLU}(\mathbf{a})$ lets the network modulate each value channel multiplicatively — a learned, input-dependent mask — which is the expressive gain over a single static nonlinearity.

<a id="p-e4-swiglu-a-gated-feed-forward-network-4"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-4 --> ![Two panels. Left: SiLU, GELU, and ReLU activation curves with SiLU's derivative; SiLU is a smooth self-gate that dips to a minimum of about minus 0.28 near x equals minus 1.28 and tracks GELU closely. Right: a schematic of the SwiGLU MLP — the input fans into a gate projection and an up projection, the gate passes through SiLU, the two are multiplied elementwise, and the result passes through a down projection; a note explains the 8/3 d hidden width keeps the three-matrix SwiGLU at the same parameter count as the two-matrix GELU MLP.](figures/appendix-e-swiglu.svg)

<!-- sec:E.4-figure-e -->
<a id="p-e4-swiglu-a-gated-feed-forward-network-5"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-5 --> <a id="sec-E.4-figure-e"></a>**Figure E.3.** SwiGLU. *Left:* the SiLU gate $z\,\sigma(z)$ and its derivative. *Right:* the gated three-matrix structure of Equation <!-- ref:E-5 -->[(5)](#eq-5). Regenerate via `surveys/llms-for-coding/figures/appendix-e-swiglu.py`.

<a id="p-e4-swiglu-a-gated-feed-forward-network-6"></a><!-- para:e4-swiglu-a-gated-feed-forward-network-6 --> The width $\tfrac{8}{3}d$ now follows by accounting. The GELU MLP holds $2\cdot d\cdot(4d) = 8d^2$ weights in its two matrices. SwiGLU has *three* matrices of shape $d\times d_{ff}$, i.e. $3\,d\,d_{ff}$ weights; setting $3\,d\,d_{ff} = 8d^2$ gives $d_{ff} = \tfrac{8}{3}d$ — exactly the rule of <!-- secref:E.1 -->[§E.1](#sec-E.1). The gate is bought at no net parameter cost by making each of the three matrices narrower than the two it replaces.

<!-- sec:E.5 -->
### <a id="sec-E.5"></a>E.5 Grouped-Query Attention and the KV Cache

<a id="p-e5-grouped-query-attention-and-the-kv-cache-1"></a><!-- para:e5-grouped-query-attention-and-the-kv-cache-1 --> The fourth change is an inference-time one. Recall from <!-- secxref:3.5.1 -->[§3.5.1](language-models-from-first-principles.md#sec-3.5.1) that autoregressive generation caches the key and value vectors of every past token so each new token is $O(T)$ rather than $O(T^2)$ work; the price is memory, and that memory scales with the number of *key/value* heads. Standard multi-head attention (<!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2)) gives each of the $H$ query heads its own key/value head, so the cache stores $H$ of them per layer. Grouped-query attention (GQA) keeps the $H$ query heads but lets every group of $H/G$ of them *share* one key/value head, for $G$ shared heads total; multi-query attention (MQA) is the extreme $G=1$. The per-token KV-cache size across $L$ layers is

<a id="eq-7"></a><!-- eq:E-7 -->
$$
\text{KV-cache} = 2\,L\,G\,d_{\text{head}}\,\cdot(\text{bytes/elt}),\qquad
\frac{\text{cache}_{\text{GQA}}}{\text{cache}_{\text{MHA}}} = \frac{G}{H}, \tag{7}
$$

<a id="p-e5-grouped-query-attention-and-the-kv-cache-2"></a><!-- para:e5-grouped-query-attention-and-the-kv-cache-2 --> the factor $2$ for keys and values. Because the cache scales with $G$ and not $H$, GQA at $G=8$ on an $H=32$ model cuts the cache fourfold and MQA cuts it $32$-fold (Figure E.4), with the query heads — and thus most of the model's expressivity — untouched. The reduction is exact and free of approximation in the limit $G=H$: the validation engine confirms GQA with $G=H$ reproduces full MHA to $0$. Llama-2 adopts GQA at its 34B and 70B sizes (with $H=64$, $G=8$), keeping full MHA at 7B and 13B <!-- cite:63 --> [[63]](references.md#ref-63); it is the standard attention of frontier dense and mixture-of-experts models alike.

<a id="p-e5-grouped-query-attention-and-the-kv-cache-3"></a><!-- para:e5-grouped-query-attention-and-the-kv-cache-3 --> ![Two panels. Left: a head-sharing schematic with eight query heads on top and, below, the key/value heads they map to — eight for MHA, two for GQA, one for MQA — with lines showing each query head connecting to its shared key/value head, and a note that the cache is proportional to the number of key/value heads. Right: a bar chart of per-token KV-cache memory as a fraction of MHA for an H equals 32 model: MHA 100 percent, GQA with G equals 8 is 25 percent (a 4x reduction), MQA is 3 percent (a 32x reduction).](figures/appendix-e-gqa.svg)

<!-- sec:E.5-figure-e -->
<a id="p-e5-grouped-query-attention-and-the-kv-cache-4"></a><!-- para:e5-grouped-query-attention-and-the-kv-cache-4 --> <a id="sec-E.5-figure-e"></a>**Figure E.4.** The MHA → GQA → MQA spectrum. *Left:* $H=8$ query heads sharing $G=8,2,1$ key/value heads. *Right:* per-token KV-cache memory falls with $G$, not $H$ — the serving lever of Equation <!-- ref:E-7 -->[(7)](#eq-7). Regenerate via `surveys/llms-for-coding/figures/appendix-e-gqa.py`.

<!-- sec:E.6 -->
### <a id="sec-E.6"></a>E.6 What Changes Next

<a id="p-e6-what-changes-next-1"></a><!-- para:e6-what-changes-next-1 --> A modern 7B is GPT-2 with cheaper normalization, relative positions, a gated MLP, and a slimmer KV cache — four local substitutions, every one derived and gradient-checked above, inside an unchanged pre-norm residual skeleton. From here the size ladder splits in two. Scaling this *same* dense block to 33B–70B (Appendix F) changes only $d$, $H$, and $L$ — no new parts, exactly the accounting of <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3) and <!-- secref:E.1 -->[§E.1](#sec-E.1) run larger. The frontier instead changes the *block*: it replaces the single SwiGLU MLP with a sparse mixture of many expert MLPs, of which each token uses a few — the mixture-of-experts model of Appendix G, where parameter count and compute-per-token finally decouple.
