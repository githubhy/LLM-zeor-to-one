## Frontier Mixture-of-Experts: DeepSeek-V3

<a id="p-frontier-mixture-of-experts-deepseek-v3-1"></a><!-- para:frontier-mixture-of-experts-deepseek-v3-1 --> Appendix F ended at the ceiling of the dense design: every token pays, in compute and in the $16N$-byte training state, for every one of the $N$ parameters. The frontier breaks that tie by finally changing the block. In a mixture-of-experts (MoE) model the single SwiGLU MLP of <!-- secxref:E.4 -->[§E.4](appendix-e-modern-dense.md#sec-E.4) is replaced by *many* expert MLPs and a lightweight router; each token is sent to only a few of them, so the model's total parameter count — its *capacity* — grows far beyond the *active* count that sets per-token compute. DeepSeek-V3 carries $671$B total parameters but activates only $37$B per token <!-- cite:64 --> [[64]](references.md#ref-64); its code-specialized sibling DeepSeek-Coder-V2 is $236$B total / $21$B active <!-- cite:43 --> [[43]](references.md#ref-43). Everything else — the residual stream, RMSNorm, RoPE, the cross-entropy, backprop, Adam — is exactly Appendices C–F. This chapter derives the two pieces that are new: the router (forward and the gradient through it, gradient-checked in `figures/appendix-g-validate.py`) and the accounting that makes $671$B affordable.

<a id="p-frontier-mixture-of-experts-deepseek-v3-2"></a><!-- para:frontier-mixture-of-experts-deepseek-v3-2 --> ![Two FFN blocks. Left: the dense block of Appendix E — one SwiGLU MLP, always on, every token pays for all of it. Right: the DeepSeekMoE FFN — the token goes to a router computing a sigmoid affinity against 256 routed experts; the top 8 (highlighted) run, plus one always-on shared expert; their outputs are combined by normalized gating values into the block output.](figures/appendix-g-moe-block.svg)

<a id="p-frontier-mixture-of-experts-deepseek-v3-3"></a><!-- para:frontier-mixture-of-experts-deepseek-v3-3 --> **Figure G.1.** Dense FFN vs DeepSeekMoE FFN. The dense MLP is always on; the MoE FFN routes each token to its top $8$ of $256$ routed experts plus $1$ shared expert (counts from DeepSeek-V3 <!-- cite:64 --> [[64]](references.md#ref-64)), so it touches $9$ of $257$ experts. Regenerate via `surveys/llms-for-coding/figures/appendix-g-moe-block.py`.

<!-- sec:G.1 -->
### <a id="sec-G.1"></a>G.1 The MoE Feed-Forward Layer

<a id="p-g1-the-moe-feed-forward-layer-1"></a><!-- para:g1-the-moe-feed-forward-layer-1 --> Each MoE layer holds $N_s$ shared experts (always applied) and $N_r$ routed experts (DeepSeek-V3: $N_s=1$, $N_r=256$, with experts of intermediate width $2048$, in all but the first three layers <!-- cite:64 --> [[64]](references.md#ref-64)). A router scores the token $\mathbf{u}$ against a learned centroid $\mathbf{e}_i$ per routed expert, keeps the top $K_r$ ($=8$), and combines their SwiGLU outputs by gating values normalized over the selected set:

<a id="eq-1"></a><!-- eq:G-1 -->
$$
\mathbf{o} = \sum_{i=1}^{N_s}\mathrm{FFN}^{(s)}_i(\mathbf{u}) \;+\; \sum_{i\in\mathcal{S}} g_i\,\mathrm{FFN}^{(r)}_i(\mathbf{u}),
\qquad
g_i = \frac{s_i}{\sum_{j\in\mathcal{S}} s_j},\quad
s_i = \sigma(\mathbf{e}_i^{\top}\mathbf{u}),\quad
\mathcal{S} = \mathrm{TopK}\big(\{s_j\}_{j=1}^{N_r},\,K_r\big), \tag{1}
$$

<a id="p-g1-the-moe-feed-forward-layer-2"></a><!-- para:g1-the-moe-feed-forward-layer-2 --> with $\sigma$ the sigmoid and each $\mathrm{FFN}$ a SwiGLU of <!-- secxref:E.4 -->[§E.4](appendix-e-modern-dense.md#sec-E.4). Equation <!-- ref:G-1 -->[(1)](#eq-1) is the DeepSeek-V3 gating of its Eqs (12)–(15) <!-- cite:64 --> [[64]](references.md#ref-64): a *sigmoid* affinity (independent per expert, unlike a softmax over all experts), hard top-$K_r$ selection, and a renormalization so the active gates sum to one. The cost is set by $K_r + N_s = 9$ experts, not by $N_r + N_s = 257$.

<!-- sec:G.2 -->
### <a id="sec-G.2"></a>G.2 The Gradient Through the Router

<a id="p-g2-the-gradient-through-the-router-1"></a><!-- para:g2-the-gradient-through-the-router-1 --> The one subtlety in the backward pass is that $\mathrm{TopK}$ is a non-differentiable mask: it selects which experts contribute, but carries no gradient itself. Gradient instead flows through the *gating values* $g_i$ — which depend on the affinities $s_i$, hence on the centroids $\mathbf{e}_i$ and the input $\mathbf{u}$ — for the selected experts only. Writing the upstream gradient $\mathrm{d}\mathbf{o}$, the per-expert gate gradient $\mathrm{d}g_i = \langle \mathrm{d}\mathbf{o},\,\mathrm{FFN}^{(r)}_i(\mathbf{u})\rangle$, the normalizer $Z=\sum_{j\in\mathcal{S}} s_j$, and $a_k = \mathbf{e}_k^{\top}\mathbf{u}$:

<a id="eq-2"></a><!-- eq:G-2 -->
$$
\begin{aligned}
\mathrm{d}s_k &= \frac{1}{Z}\Big(\mathrm{d}g_k - \sum_{i\in\mathcal{S}} g_i\,\mathrm{d}g_i\Big), &&\text{(differentiate $g_i=s_i/Z$ over the selected set)}\\[2pt]
\mathrm{d}\mathbf{e}_k &= \mathrm{d}s_k\,\sigma'(a_k)\,\mathbf{u}, &&\text{(through $s_k=\sigma(a_k)$, $a_k=\mathbf{e}_k^{\top}\mathbf{u}$)}\\[2pt]
\mathrm{d}\mathbf{u} &= \sum_{i\in\mathcal{S}} g_i\,\big[\partial\mathrm{FFN}^{(r)}_i\big] + \sum_{i=1}^{N_s}\big[\partial\mathrm{FFN}^{(s)}_i\big] + \sum_{k\in\mathcal{S}} \mathrm{d}s_k\,\sigma'(a_k)\,\mathbf{e}_k. &&\text{(expert paths $+$ router path)}
\end{aligned} \tag{2}
$$

<a id="p-g2-the-gradient-through-the-router-2"></a><!-- para:g2-the-gradient-through-the-router-2 --> The middle term of the $\mathrm{d}s_k$ expression — the gate-weighted average $\sum_i g_i\,\mathrm{d}g_i$ subtracted from each $\mathrm{d}g_k$ — is exactly the softmax-style coupling: raising one gate must lower the others, because they are renormalized to sum to one. The first two terms of $\mathrm{d}\mathbf{u}$ are the ordinary SwiGLU backward of <!-- secxref:E.4 -->[§E.4](appendix-e-modern-dense.md#sec-E.4) run through the active experts; the third is the router's own contribution. Every gradient in Equation <!-- ref:G-2 -->[(2)](#eq-2) matches central finite differences in `appendix-g-validate.py` — $\mathrm{d}\mathbf{u}$ to $1.6\times10^{-9}$, the centroids $\mathrm{d}\mathbf{e}$ to $2\times10^{-8}$.

<!-- sec:G.3 -->
### <a id="sec-G.3"></a>G.3 Load Balancing, Without an Auxiliary Loss

<a id="p-g3-load-balancing-without-an-auxiliary-loss-1"></a><!-- para:g3-load-balancing-without-an-auxiliary-loss-1 --> A router left to itself collapses: a few experts win nearly every token, the rest are never selected and so never train, and the model's capacity is wasted (Figure G.3, left). The classic fix adds an auxiliary load-balancing loss that penalizes uneven utilization, but too strong a penalty degrades quality. DeepSeek-V3 instead uses an *auxiliary-loss-free* scheme <!-- cite:64 --> [[64]](references.md#ref-64): a per-expert bias $b_i$, adjusted online toward even load, is added to the affinity *for selection only*, while the gate value keeps the unbiased affinity:

<a id="eq-3"></a><!-- eq:G-3 -->
$$
\mathcal{S} = \mathrm{TopK}\big(\{\,s_j + b_j\,\}_{j=1}^{N_r},\,K_r\big),
\qquad g_i = \frac{s_i}{\sum_{j\in\mathcal{S}} s_j}\quad (i\in\mathcal{S}), \tag{3}
$$

<a id="p-g3-load-balancing-without-an-auxiliary-loss-2"></a><!-- para:g3-load-balancing-without-an-auxiliary-loss-2 --> so the bias steers *which* experts fire — nudging underused ones into the top-$K_r$ — without distorting the *weights* they receive once selected, and adds no gradient term to the loss. The result is even utilization (Figure G.3, right), so all $N_r$ experts are trained and the capacity is real.

<a id="p-g3-load-balancing-without-an-auxiliary-loss-3"></a><!-- para:g3-load-balancing-without-an-auxiliary-loss-3 --> ![Two bar charts of per-expert token share across experts. Left: routing collapse — a few experts spike far above the fair-share target line while most sit near zero, labelled 30 of 64 experts nearly dead. Right: balanced utilization under the auxiliary-loss-free bias — every expert sits near the fair-share target line, labelled all experts trained.](figures/appendix-g-load-balance.svg)

<!-- sec:G.3-figure-g -->
<a id="p-g3-load-balancing-without-an-auxiliary-loss-4"></a><!-- para:g3-load-balancing-without-an-auxiliary-loss-4 --> <a id="sec-G.3-figure-g"></a>**Figure G.3.** Why the router needs balancing. Without it (left) a few experts dominate and most die; the bias $b_i$ of Equation <!-- ref:G-3 -->[(3)](#eq-3) restores even load (right). Target share $=K_r/N_r$. Regenerate via `surveys/llms-for-coding/figures/appendix-g-load-balance.py`.

<!-- sec:G.4 -->
### <a id="sec-G.4"></a>G.4 The Decoupling: Capacity vs Compute

<a id="p-g4-the-decoupling-capacity-vs-compute-1"></a><!-- para:g4-the-decoupling-capacity-vs-compute-1 --> The accounting is the whole payoff. Per token, the active parameters are the attention and embeddings plus only the $N_s + K_r$ experts that fired; the total includes all $N_r$ routed experts that merely *exist*:

<a id="eq-4"></a><!-- eq:G-4 -->
$$
N_{\text{active}} = N_{\text{attn+emb}} + (N_s + K_r)\,N_{\text{expert}}
\;\;\ll\;\;
N_{\text{total}} = N_{\text{attn+emb}} + (N_s + N_r)\,N_{\text{expert}},
\qquad C \approx 2\,N_{\text{active}}\ \text{FLOPs/token}. \tag{4}
$$

<a id="p-g4-the-decoupling-capacity-vs-compute-2"></a><!-- para:g4-the-decoupling-capacity-vs-compute-2 --> The forward cost is the $2N$-per-token rule of <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3) — but now with $N_{\text{active}}$, not $N_{\text{total}}$, in the exponent that matters. DeepSeek-V3 makes this concrete (Figure G.2): $671$B parameters of capacity at the per-token compute of a $37$B dense model, a $5.5\%$ active fraction. This is why a frontier model can hold far more knowledge than any dense model that must run all of itself on every token — capacity is bought with memory (all experts are stored and, in training, sharded as in <!-- secxref:F.2 -->[§F.2](appendix-f-scaling.md#sec-F.2)), while inference compute tracks only the active slice.

<a id="p-g4-the-decoupling-capacity-vs-compute-3"></a><!-- para:g4-the-decoupling-capacity-vs-compute-3 --> ![A grouped bar chart, log scale, of total versus active parameters for four models: dense 7B (7B/7B), dense 70B (70B/70B), DeepSeek-Coder-V2 236B (236B total, 21B active, only 9 percent), and DeepSeek-V3 671B (671B total, 37B active, only 6 percent). For the dense models the two bars are equal; for the MoE models the total bar towers over the active bar.](figures/appendix-g-decoupling.svg)

<!-- sec:G.4-figure-g -->
<a id="p-g4-the-decoupling-capacity-vs-compute-4"></a><!-- para:g4-the-decoupling-capacity-vs-compute-4 --> <a id="sec-G.4-figure-g"></a>**Figure G.2.** MoE decouples capacity from compute. Dense models have total $=$ active; DeepSeek-Coder-V2 and DeepSeek-V3 carry $236$B/$671$B of capacity at $21$B/$37$B active per token (Equation <!-- ref:G-4 -->[(4)](#eq-4)). Regenerate via `surveys/llms-for-coding/figures/appendix-g-decoupling.py`.

<!-- sec:G.5 -->
### <a id="sec-G.5"></a>G.5 Multi-Head Latent Attention: Compressing the Cache

<a id="p-g5-multi-head-latent-attention-compressing-the-cache-1"></a><!-- para:g5-multi-head-latent-attention-compressing-the-cache-1 --> DeepSeek-V3 pairs MoE with a second efficiency, on the attention side. Grouped-query attention (<!-- secxref:E.5 -->[§E.5](appendix-e-modern-dense.md#sec-E.5)) shrinks the KV cache by sharing key/value *heads*; Multi-head Latent Attention (MLA) shrinks it differently, by *compressing* what is cached. Instead of storing the full keys and values, MLA caches a single low-rank latent vector $\mathbf{c}^{KV}_t$ of dimension $d_c$ per token per layer, from which the per-head keys and values are reconstructed on the fly by up-projection, plus a small decoupled RoPE key of width $d_h^{R}$ <!-- cite:64 --> [[64]](references.md#ref-64). The cached state per token across $L$ layers is then

<a id="eq-5"></a><!-- eq:G-5 -->
$$
\text{KV}_{\text{MLA}}(T) = L\,(d_c + d_h^{R})\,T\,b
\quad\text{vs}\quad
\text{KV}_{\text{MHA}} = 2\,L\,n_h\,d_{\text{head}}\,T\,b, \tag{5}
$$

<a id="p-g5-multi-head-latent-attention-compressing-the-cache-2"></a><!-- para:g5-multi-head-latent-attention-compressing-the-cache-2 --> with $b$ bytes per element. DeepSeek-V3 sets $d_c=512$ and $d_h^{R}=64$ against $n_h=128$ heads of width $d_{\text{head}}=128$ <!-- cite:64 --> [[64]](references.md#ref-64), so MLA caches $d_c + d_h^{R} = 576$ elements per token per layer where full multi-head attention would cache $2\,n_h\,d_{\text{head}} = 32768$ — a $\approx 57\times$ reduction, on the same long-context serving problem that motivated GQA in <!-- secxref:F.3 -->[§F.3](appendix-f-scaling.md#sec-F.3). The full MLA forward and backward are a derivation in their own right; the cache arithmetic of Equation <!-- ref:G-5 -->[(5)](#eq-5) is what it buys.

<!-- sec:G.6 -->
### <a id="sec-G.6"></a>G.6 The Anatomy, Complete

<a id="p-g6-the-anatomy-complete-1"></a><!-- para:g6-the-anatomy-complete-1 --> With MoE the survey has walked the whole ladder: a $203$-parameter toy (Appendix C), GPT-2 (D), the modern 7B dense block (E), its scaling to 70B (F), and now a $671$B frontier model — and every rung is the *same* residual stream, the *same* attention and feed-forward primitives, the *same* cross-entropy, backprop, and Adam, gradient-checked at each step. What changed across three orders of magnitude was never the core computation, only four kinds of refinement: the normalization and position encoding (E), the activation (D, E), the attention's cache footprint (E, G), and — only at the frontier — the feed-forward layer's split into routed experts (G). Appendix H draws these threads together into a single scaling account, mapping every dimension from the toy to DeepSeek-V3 and tallying where the parameters, the compute, and the memory go at each scale.
