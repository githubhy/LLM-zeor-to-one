## Scaling the Dense Block: 33B–70B

<a id="p-scaling-the-dense-block-33b70b-1"></a><!-- para:scaling-the-dense-block-33b70b-1 --> The modern block of Appendix E does not change again on the way to 70B — and that is the chapter. Scaling a dense model from 7B to 70B alters only three numbers, the width $d$, the head count $H$, and the depth $L$; every module, every equation, every gradient derived in Appendices C–E is reused byte-for-byte. What *does* appear at this scale is not new mathematics but a new constraint: the model's state no longer fits on a single device, and the arithmetic of *why* — derived directly from the Adam optimizer of <!-- secxref:C.4 -->[§C.4](appendix-c-toy-transformer.md#sec-C.4) — is the substance here. This 33B–70B band is also the dense sweet spot for code: Code Llama ships at 34B and 70B <!-- cite:6 --> [[6]](references.md#ref-6) and DeepSeek-Coder tops out at 33B <!-- cite:10 --> [[10]](references.md#ref-10).

<!-- sec:F.1 -->
### <a id="sec-F.1"></a>F.1 Scale Is Only $(d, H, L)$

<a id="p-f1-scale-is-only-d-h-l-1"></a><!-- para:f1-scale-is-only-d-h-l-1 --> The four Llama sizes differ in exactly three dimensions (Table 2 of <!-- cite:65 --> [[65]](references.md#ref-65)), shown in Figure F.1: width $d$ from $4096$ to $8192$, heads $H$ from $32$ to $64$, depth $L$ from $32$ to $80$. The per-head width stays at $d_{\text{head}}=128$ (<!-- secxref:E.1 -->[§E.1](appendix-e-modern-dense.md#sec-E.1)), the feed-forward rule stays at $\tfrac{8}{3}d$, RMSNorm/RoPE/SwiGLU are untouched, and Llama-2's 70B simply takes the 65B's width and depth and adds the grouped-query attention of <!-- secxref:E.5 -->[§E.5](appendix-e-modern-dense.md#sec-E.5) <!-- cite:63 --> [[63]](references.md#ref-63). The parameter count is the same $N \approx (V+T_{ctx})d + L\cdot(4d^2 + 3\,d\,d_{ff})$ accounting of <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3) (now with the three SwiGLU matrices) evaluated at larger dimensions — no new terms.

<a id="p-f1-scale-is-only-d-h-l-2"></a><!-- para:f1-scale-is-only-d-h-l-2 --> ![Two panels. Left: a log-scale bar chart of the four Llama sizes — 6.7B, 13.0B, 32.5B, 65.2B parameters — each bar annotated with its width d, head count H, and depth L. Right: the width-to-depth aspect ratio d over L for the four sizes, plotted as 128, 128, 111, 102, sitting in a shaded band between 100 and 128.](figures/appendix-f-scale-ladder.svg)

<!-- sec:F.1-figure-f -->
<a id="p-f1-scale-is-only-d-h-l-3"></a><!-- para:f1-scale-is-only-d-h-l-3 --> <a id="sec-F.1-figure-f"></a>**Figure F.1.** The Llama dense ladder. *Left:* only $d$, $H$, $L$ change across sizes <!-- cite:65 --> [[65]](references.md#ref-65). *Right:* the width/depth ratio $d/L$ stays in a narrow band ($\approx 100$–$128$) — depth is scaled roughly in step with width rather than either alone. Regenerate via `surveys/llms-for-coding/figures/appendix-f-scale-ladder.py`.

<a id="p-f1-scale-is-only-d-h-l-4"></a><!-- para:f1-scale-is-only-d-h-l-4 --> One regularity is worth naming. The aspect ratio $d/L$ drifts only from $128$ at 7B to $102$ at 65B (Figure F.1, right): models are scaled by adding width and depth *together*, not by making one dominate. A network that is too shallow for its width wastes parameters on representations it cannot compose; one too deep for its width is hard to optimize. The narrow band is the empirical compromise, and it holds across the family.

<!-- sec:F.2 -->
### <a id="sec-F.2"></a>F.2 The Memory Wall

<a id="p-f2-the-memory-wall-1"></a><!-- para:f2-the-memory-wall-1 --> At 70B the architecture is unremarkable but the bookkeeping is decisive. Mixed-precision training keeps, *per parameter*, five quantities, and their byte counts follow directly from the optimizer of <!-- secxref:C.4 -->[§C.4](appendix-c-toy-transformer.md#sec-C.4): the bf16 weight ($2$ bytes) used in the forward and backward passes, its bf16 gradient ($2$ bytes), and — because Adam maintains a first moment $m$ and second moment $v$, and mixed precision keeps an fp32 master copy of the weight for a numerically safe update — three fp32 quantities ($4$ bytes each). Inference keeps only the weight:

<a id="eq-1"></a><!-- eq:F-1 -->
$$
M_{\text{train}} \approx \underbrace{(2 + 2 + 4 + 4 + 4)}_{\text{weight, grad, master, }m,\,v}\,N = 16\,N \text{ bytes},
\qquad M_{\text{infer}} \approx 2\,N + \text{KV-cache}. \tag{1}
$$

<a id="p-f2-the-memory-wall-2"></a><!-- para:f2-the-memory-wall-2 --> The factor of $8$ between training and inference is the whole story of Figure F.2. A 7B needs $\approx 107$ GB of training state — already past a single $80$ GB accelerator — while a 70B needs $\approx 1.12$ TB, roughly fourteen such devices for the optimizer state *alone*, before activations. Even inference, at $2N$, puts the 70B's $\approx 140$ GB of weights across at least two devices. This is why frontier training is inseparable from *sharding*: the parameters, gradients, and optimizer moments of Equation <!-- ref:F-1 -->[(1)](#eq-1) are partitioned across many accelerators, and the forward/backward of Appendices C–E run as the same computation distributed over them. The math of the model is unchanged; only its physical realization is now plural.

<a id="p-f2-the-memory-wall-3"></a><!-- para:f2-the-memory-wall-3 --> ![A bar chart of memory in gigabytes for four cases: 7B training, 7B inference, 70B training, 70B inference. The training bars are stacked into five components — bf16 weights, bf16 grads, fp32 master, Adam m, Adam v. The 7B training bar reaches about 107 GB, 7B inference about 13 GB, 70B training towers to about 1120 GB labelled 16N and annotated as roughly 14 devices, and 70B inference about 140 GB. A dashed red line marks one 80 GB device near the bottom.](figures/appendix-f-memory-wall.svg)

<!-- sec:F.2-figure-f -->
<a id="p-f2-the-memory-wall-4"></a><!-- para:f2-the-memory-wall-4 --> <a id="sec-F.2-figure-f"></a>**Figure F.2.** The memory wall. Training state is the $16N$ bytes of Equation <!-- ref:F-1 -->[(1)](#eq-1) — the five stacked components — against a single $80$ GB device (dashed). A 70B's $\approx 1.12$ TB sits far above the line, forcing the state across many accelerators. Regenerate via `surveys/llms-for-coding/figures/appendix-f-memory-wall.py`.

<!-- sec:F.3 -->
### <a id="sec-F.3"></a>F.3 Why Grouped-Query Attention Earns Its Place Here

<a id="p-f3-why-grouped-query-attention-earns-its-place-here-1"></a><!-- para:f3-why-grouped-query-attention-earns-its-place-here-1 --> The KV-cache term left implicit in Equation <!-- ref:F-1 -->[(1)](#eq-1) is what makes grouped-query attention load-bearing at this scale. From <!-- secxref:E.5 -->[§E.5](appendix-e-modern-dense.md#sec-E.5), the cache holds, per token, two vectors per key/value head across every layer, so in bytes

<a id="eq-2"></a><!-- eq:F-2 -->
$$
\text{KV}(T) = 2\,L\,G\,d_{\text{head}}\,T\,b, \tag{2}
$$

<a id="p-f3-why-grouped-query-attention-earns-its-place-here-2"></a><!-- para:f3-why-grouped-query-attention-earns-its-place-here-2 --> with $G$ key/value heads, $b$ bytes per element. Code models make $T$ large on purpose — Code Llama trains on $16$k-token sequences and serves up to $100$k <!-- cite:6 --> [[6]](references.md#ref-6), DeepSeek-Coder uses a $16$k window <!-- cite:10 --> [[10]](references.md#ref-10) — because a coding assistant must hold whole files and repositories in context (the motivation of <!-- secxref:3.5.1 -->[§3.5.1](language-models-from-first-principles.md#sec-3.5.1)). Evaluating Equation <!-- ref:F-2 -->[(2)](#eq-2) for the 70B ($L=80$, $d_{\text{head}}=128$, bf16) at a $100$k context: full multi-head attention ($G=H=64$) would need $\approx 2.6$ MB per token, or $\approx 262$ GB of cache — *larger than the model's own weights*. Grouped-query attention with $G=8$ cuts that to $\approx 0.33$ MB per token and $\approx 33$ GB, an eightfold reduction that is the difference between a servable long-context model and an impossible one. The query heads — and the model's expressivity — are untouched; only the cached state shrinks.

<!-- sec:F.4 -->
### <a id="sec-F.4"></a>F.4 The Code Tier, and the Limit of Dense

<a id="p-f4-the-code-tier-and-the-limit-of-dense-1"></a><!-- para:f4-the-code-tier-and-the-limit-of-dense-1 --> The 33B–70B band is where open dense code models concentrate, and they share two code-specific choices on top of the architecture of Appendix E: long context for repository-scale inputs and a fill-in-the-middle training objective for infilling (Code Llama 34B/70B <!-- cite:6 --> [[6]](references.md#ref-6); DeepSeek-Coder 33B <!-- cite:10 --> [[10]](references.md#ref-10)). They are also deliberately *over-trained*: the compute-optimal prescription of <!-- secxref:3.6 -->[§3.6](language-models-from-first-principles.md#sec-3.6) <!-- cite:56 --> [[56]](references.md#ref-56) minimizes loss for a fixed *training* budget, but a model served billions of times is optimized for *inference* cost, which rewards a smaller $N$ trained on far more tokens than Chinchilla-optimal — exactly DeepSeek-Coder's $2$T-token regime at 33B <!-- cite:10 --> [[10]](references.md#ref-10).

<a id="p-f4-the-code-tier-and-the-limit-of-dense-2"></a><!-- para:f4-the-code-tier-and-the-limit-of-dense-2 --> But Equation <!-- ref:F-1 -->[(1)](#eq-1) also marks the ceiling of the dense approach: every token pays for every one of the $N$ parameters, in both the $16N$-byte training state and the $2N$-FLOP-per-token forward pass of <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3). To grow capacity past 70B without growing the per-token cost in lockstep, the block itself must finally change — replacing the single SwiGLU MLP with many expert MLPs of which each token uses only a few, so that parameter count and compute-per-token *decouple*. That is the mixture-of-experts model of Appendix G.
