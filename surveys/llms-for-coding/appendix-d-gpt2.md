## GPT-2 Scale: the Toy, Grown Up

<a id="p-gpt-2-scale-the-toy-grown-up-1"></a><!-- para:gpt-2-scale-the-toy-grown-up-1 --> The toy of Appendix C is, structurally, a small GPT-2. This chapter is the first rung up the size ladder: it takes that exact anatomy — embedding, a pre-norm decoder block with a self-attention sublayer and a feed-forward sublayer, a final norm, an unembedding — and instantiates it at the four real sizes of GPT-2, the model that established the decoder-only LLM as a general-purpose engine. Almost nothing about the math changes: the forward pass, the complete backward pass, and the Adam step of Appendix C carry over verbatim. Only two ingredients differ from the toy — a smoother nonlinearity (GELU rather than ReLU) and a *tied* unembedding — and a third quantity becomes worth deriving once the model is large: where the parameters and the compute actually go. We take those in turn, citing GPT-2's own report for every dimension <!-- cite:61 --> [[61]](references.md#ref-61).

<!-- sec:D.1 -->
### <a id="sec-D.1"></a>D.1 The Same Anatomy, Four Sizes

<a id="p-d1-the-same-anatomy-four-sizes-1"></a><!-- para:d1-the-same-anatomy-four-sizes-1 --> GPT-2 is "a Transformer based architecture ... largely follow[ing] the details of the OpenAI GPT model," scaled to four sizes <!-- cite:61 --> [[61]](references.md#ref-61). Its Table 2 reports the only dimensions that change between them — the depth $L$ and the width $d$ — while the vocabulary $V=50257$ (a byte-pair encoding) and the context length $T_{ctx}=1024$ are shared. The released names *small / medium / large / XL* correspond to $L = 12, 24, 36, 48$ and $d = 768, 1024, 1280, 1600$, for $117$M, $345$M, $762$M, and $1542$M parameters.

<a id="p-d1-the-same-anatomy-four-sizes-2"></a><!-- para:d1-the-same-anatomy-four-sizes-2 --> ![Two panels. Left: a log-scale bar chart of GPT-2's four sizes (117M, 345M, 762M, 1542M parameters), each annotated with its layer count L and width d. Right: a stacked bar chart splitting each size's parameters into a small embedding part and a large blocks part, with the embedding fraction falling from 32 percent for the smallest model to 5 percent for the largest.](figures/appendix-d-gpt2-sizes.svg)

<!-- sec:D.1-figure-d -->
<a id="p-d1-the-same-anatomy-four-sizes-3"></a><!-- para:d1-the-same-anatomy-four-sizes-3 --> <a id="sec-D.1-figure-d"></a>**Figure D.1.** GPT-2 at four scales. *Left:* the sizes as reported in Table 2 <!-- cite:61 --> [[61]](references.md#ref-61) — depth $L$ and width $d$ are the only dimensions that change. *Right:* where those parameters live, split into the embeddings $(V+T_{ctx})\,d$ and the $L$ transformer blocks ($\approx 12 d^2$ each; see D.3). The token-embedding share falls from $32\%$ of the smallest model to $5\%$ of the largest — blocks grow as $L d^2$ while the embedding grows only as $V d$, so a big model is almost entirely its stacked blocks. Regenerate via `surveys/llms-for-coding/figures/appendix-d-gpt2-sizes.py`.

<a id="p-d1-the-same-anatomy-four-sizes-4"></a><!-- para:d1-the-same-anatomy-four-sizes-4 --> Everything mechanical is inherited. Each of the $L$ blocks is the pre-norm pair of sublayers of <!-- secxref:C.2 -->[§C.2](appendix-c-toy-transformer.md#sec-C.2); the attention sublayer now runs $h = d/64$ heads of the standard width $d_k=64$ (so $12$ heads at $d=768$ up to $25$ at $d=1600$), each head exactly the QK/OV circuit pair dissected in <!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2) and summed as in <!-- secxref:A.10 -->[§A.10](appendix-a-qkv-first-principles.md#sec-A.10). Training is still the cross-entropy of Section <!-- secxref:3.1 -->[§3.1](language-models-from-first-principles.md#sec-3.1), backpropagated module by module exactly as in <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3) and stepped by the Adam of <!-- secxref:C.4 -->[§C.4](appendix-c-toy-transformer.md#sec-C.4). What follows is only the delta.

<!-- sec:D.2 -->
### <a id="sec-D.2"></a>D.2 The Two Changes: GELU and a Tied Unembedding

<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-1"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-1 --> **GELU.** The toy's ReLU is replaced by the Gaussian Error Linear Unit, which gates an input by the probability a standard normal lands below it:

<a id="eq-1"></a><!-- eq:D-1 -->
$$
\mathrm{GELU}(x) = x\,\Phi(x),\qquad \Phi(x) = \tfrac{1}{2}\big(1+\mathrm{erf}(x/\sqrt{2})\big),\qquad
\mathrm{GELU}'(x) = \Phi(x) + x\,\phi(x), \tag{1}
$$

<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-2"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-2 --> with $\phi$ the standard-normal density. The forward and backward of the feed-forward sublayer are then identical to the feed-forward pass of <!-- secxref:C.2 -->[§C.2](appendix-c-toy-transformer.md#sec-C.2) and its backward in <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3), with only the ReLU mask $\mathbb{1}[Z>0]$ replaced by $\mathrm{GELU}'(Z)$. The difference is qualitative: where ReLU's gate is hard ($0$ or $1$), GELU's is a smooth ramp that dips slightly *below zero* for moderately negative inputs and *overshoots* $1$ for moderately positive ones, so a unit that ReLU would have switched fully off still receives a small, input-dependent gradient.

<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-3"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-3 --> ![Two panels. Left: GELU and ReLU activations versus x; GELU is a smooth curve that dips slightly negative near x equals minus 0.75 before rising, while ReLU is a hard hinge at zero. Right: their derivatives; ReLU's is a hard step from 0 to 1, while GELU's is a smooth S-curve that goes slightly negative for negative x and overshoots above 1 for positive x near 1.4.](figures/appendix-d-gelu.svg)

<!-- sec:D.2-figure-d -->
<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-4"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-4 --> <a id="sec-D.2-figure-d"></a>**Figure D.2.** GELU versus ReLU. *Left:* the activation of Equation <!-- ref:D-1 -->[(1)](#eq-1) is a smooth gate — it dips to $-0.17$ near $x \approx -0.75$ rather than clamping flat at zero. *Right:* the derivatives that enter backprop — ReLU's is the hard set $\{0,1\}$, GELU's the smooth $\Phi(x)+x\phi(x)$, which is slightly negative for negative $x$ and overshoots to $\approx 1.13$ near $x\approx 1.4$. Smoothness is why GELU passes a usable gradient through units a hard ReLU would have killed. Regenerate via `surveys/llms-for-coding/figures/appendix-d-gelu.py`.

<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-5"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-5 --> **Tied unembedding.** The toy kept a separate unembedding $W_U$. GPT-2 *ties* it to the token embedding, $W_U = E^{\top}$, so the same $V\times d$ table both reads tokens in and scores them out. This removes $Vd$ parameters (a third of the small model, by Figure D.1) and couples the two roles in the backward pass: with $\mathrm{logits} = H^F E^{\top}$, the table's gradient is the *sum* of its read-side and write-side duties,

<a id="eq-2"></a><!-- eq:D-2 -->
$$
\frac{\partial\mathcal{L}}{\partial E} = \underbrace{\sum_{t:\,x_t=v}\mathrm{d}\mathbf{h}^0_t}_{\text{embedding lookup (read)}} \;+\; \underbrace{(\mathrm{d}\,\mathrm{logits})^{\top} H^F}_{\text{unembedding (write)}}, \tag{2}
$$

<a id="p-d2-the-two-changes-gelu-and-a-tied-unembedding-6"></a><!-- para:d2-the-two-changes-gelu-and-a-tied-unembedding-6 --> the first term the scatter-add of the embedding lookup, the second the unembedding gradient of <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3) now landing back on $E$. Tying makes a token's "input meaning" and its "output score direction" share one vector — a constraint, but an efficient and well-performing one.

<!-- sec:D.3 -->
### <a id="sec-D.3"></a>D.3 Counting the Model: Parameters and Compute

<a id="p-d3-counting-the-model-parameters-and-compute-1"></a><!-- para:d3-counting-the-model-parameters-and-compute-1 --> At scale it is worth counting the anatomy exactly. With biases and norms neglected (they are $O(Ld)$, sub-leading), each block holds $4d^2$ in the attention projections $W_Q,W_K,W_V,W_O$ and $8d^2$ in the two feed-forward matrices ($d\times 4d$ and $4d\times d$), so

<a id="eq-3"></a><!-- eq:D-3 -->
$$
N \;\approx\; \underbrace{(V + T_{ctx})\,d}_{\text{embeddings (tied)}} \;+\; \underbrace{L\cdot 12 d^2}_{L\text{ blocks}}. \tag{3}
$$

<a id="p-d3-counting-the-model-parameters-and-compute-2"></a><!-- para:d3-counting-the-model-parameters-and-compute-2 --> Evaluated at the four sizes this gives $124$M, $355$M, $773$M, and $1.56$B — within a few percent of the paper's stated $117$M$/345$M$/762$M$/1542$M <!-- cite:61 --> [[61]](references.md#ref-61), the residual being the bias and LayerNorm terms and the report's embedding-counting convention. Equation <!-- ref:D-3 -->[(3)](#eq-3) explains Figure D.1's right panel: the embedding term grows only linearly in $d$, the block term quadratically and with depth, so the embedding's share collapses from $32\%$ (small) to $5\%$ (XL). A frontier model is, to a first approximation, $12 L d^2$.

<a id="p-d3-counting-the-model-parameters-and-compute-3"></a><!-- para:d3-counting-the-model-parameters-and-compute-3 --> The compute follows the same accounting. A forward pass costs $\approx 2N$ floating-point operations per token (one multiply-add per parameter), and the backward pass about twice that, so training on $D$ tokens costs

<a id="eq-4"></a><!-- eq:D-4 -->
$$
C_{\text{train}} \;\approx\; 6\,N\,D \quad\text{FLOPs}, \tag{4}
$$

<a id="p-d3-counting-the-model-parameters-and-compute-4"></a><!-- para:d3-counting-the-model-parameters-and-compute-4 --> the relation behind the scaling laws of Section <!-- secxref:3.6 -->[§3.6](language-models-from-first-principles.md#sec-3.6) and the training-budget economics of Section <!-- secxref:3.5 -->[§3.5](language-models-from-first-principles.md#sec-3.5). GPT-3, two years later, is *this same architecture* with $N$ pushed to $175$B and $D$ to hundreds of billions of tokens <!-- cite:62 --> [[62]](references.md#ref-62) — no new parts, only Equations <!-- ref:D-3 -->[(3)](#eq-3) and <!-- ref:D-4 -->[(4)](#eq-4) run at a larger scale.

<!-- sec:D.4 -->
### <a id="sec-D.4"></a>D.4 What Changes Next

<a id="p-d4-what-changes-next-1"></a><!-- para:d4-what-changes-next-1 --> GPT-2 is the toy widened and deepened with two small substitutions. The next rung is not a bigger GPT-2 but a *re-engineered* dense block: the modern 7B models keep this exact skeleton yet replace LayerNorm with RMSNorm, learned positions with rotary embeddings, the GELU MLP with a gated SwiGLU one, and full multi-head attention with grouped-query attention — four changes, each with a clean first-principles reason, derived in Appendix E.
