## Synthesis: One Architecture, Nine Orders of Magnitude

<a id="p-synthesis-one-architecture-nine-orders-of-magnitude-1"></a><!-- para:synthesis-one-architecture-nine-orders-of-magnitude-1 --> Appendices C through G walked the LLM ladder from a $203$-parameter toy to a $671$B-parameter frontier model. This closing chapter draws the rungs together: a single master table of every dimension across the five models, the accretion of design choices that separates them, and the scaling account — where the parameters, the compute, and the memory actually go. The through-line is the one worth keeping: across nine orders of magnitude in size, the core computation never changed. Every model is the toy of <!-- secxref:C.1 -->[§C.1](appendix-c-toy-transformer.md#sec-C.1), widened and deepened, refined on exactly five axes.

<!-- sec:H.1 -->
### <a id="sec-H.1"></a>H.1 The Master Table

<a id="p-h1-the-master-table-1"></a><!-- para:h1-the-master-table-1 --> The five models, dimension by dimension. Numbers are sourced — Toy (defined in Appendix C), GPT-2 XL <!-- cite:61 --> [[61]](references.md#ref-61), Llama 7B/70B <!-- cite:65 --> [[65]](references.md#ref-65) <!-- cite:63 --> [[63]](references.md#ref-63), DeepSeek-V3 <!-- cite:64 --> [[64]](references.md#ref-64):

| | Toy (C) | GPT-2 XL (D) | Llama 7B (E) | Llama 70B (F) | DeepSeek-V3 (G) |
|---|---|---|---|---|---|
| total params | 203 | 1.5B | 6.7B | 70B | 671B |
| active / token | 203 | 1.5B | 6.7B | 70B | 37B |
| width $d$ | 4 | 1600 | 4096 | 8192 | 7168 |
| layers $L$ | 1 | 48 | 32 | 80 | 61 |
| heads $H$ | 1 | 25 | 32 | 64 | 128 |
| per-head $d_{\text{head}}$ | 4 | 64 | 128 | 128 | 128 |
| vocab $V$ | 3 | 50257 | 32k | 32k | 128k |
| context | 3 | 1024 | 4096 | 4096 | 128k |
| normalization | LayerNorm | LayerNorm | RMSNorm | RMSNorm | RMSNorm |
| position | learned | learned | RoPE | RoPE | RoPE |
| activation | ReLU | GELU | SwiGLU | SwiGLU | SwiGLU |
| attention | MHA | MHA | MHA | GQA | MLA |
| feed-forward | dense | dense | dense | dense | MoE |

<a id="p-h1-the-master-table-2"></a><!-- para:h1-the-master-table-2 --> ![Two log-scale line charts over the five models. Left: total parameters rising from 203 to 671 billion (nine orders of magnitude), with an active-parameters line that tracks the total until DeepSeek-V3, where the MoE splits the active count down to 37 billion. Right: the trained context length rising from 3 tokens to 128K.](figures/appendix-h-scale-sweep.svg)

<!-- sec:H.1-figure-h -->
<a id="p-h1-the-master-table-3"></a><!-- para:h1-the-master-table-3 --> <a id="sec-H.1-figure-h"></a>**Figure H.2.** The scale sweep. *Left:* capacity grows from $203$ to $671$B parameters — nine orders of magnitude — with active compute diverging from total only at the MoE frontier. *Right:* context grows from $3$ to $128$k tokens. Every axis of scale moved by orders of magnitude; the architecture did not. Regenerate via `surveys/llms-for-coding/figures/appendix-h-scale-sweep.py`.

<a id="p-h1-the-master-table-4"></a><!-- para:h1-the-master-table-4 --> Two patterns stand out. The per-head width $d_{\text{head}}$ locks at $128$ from the 7B onward — scaling adds heads, not wider heads — and the active parameter count tracks the total exactly until DeepSeek-V3, where the mixture-of-experts of <!-- secxref:G.4 -->[§G.4](appendix-g-moe.md#sec-G.4) finally pulls them apart.

<!-- sec:H.2 -->
### <a id="sec-H.2"></a>H.2 The Five Axes of Refinement

<a id="p-h2-the-five-axes-of-refinement-1"></a><!-- para:h2-the-five-axes-of-refinement-1 --> The bottom five rows of the master table are the entire architectural story, and Figure H.1 colours them by era. Read left to right, each axis is refined once and then frozen: nothing is ever redesigned, only improved and inherited.

<a id="p-h2-the-five-axes-of-refinement-2"></a><!-- para:h2-the-five-axes-of-refinement-2 --> ![A five-by-five matrix. Rows are the five design axes — normalization, position, activation, attention, feed-forward — and columns are the five models from the toy to DeepSeek-V3. Cells are colour-coded by era: classic choices (LayerNorm, learned positions, ReLU, MHA, dense) fill the upper-left, the GELU intermediate sits at GPT-2's activation, the modern dense choices (RMSNorm, RoPE, SwiGLU, GQA) spread across the middle columns, and the frontier choices (MoE, MLA) appear only at DeepSeek-V3 in the lower-right.](figures/appendix-h-choices.svg)

<!-- sec:H.2-figure-h -->
<a id="p-h2-the-five-axes-of-refinement-3"></a><!-- para:h2-the-five-axes-of-refinement-3 --> <a id="sec-H.2-figure-h"></a>**Figure H.1.** Accretion, not redesign. The same five axes, refined left-to-right: classic → GELU → modern dense (E) → frontier (G). Regenerate via `surveys/llms-for-coding/figures/appendix-h-choices.py`.

<a id="p-h2-the-five-axes-of-refinement-4"></a><!-- para:h2-the-five-axes-of-refinement-4 --> The five refinements, each with its one-line reason: **normalization** went LayerNorm → RMSNorm (<!-- secxref:E.2 -->[§E.2](appendix-e-modern-dense.md#sec-E.2)) to drop a re-centering the residual stream makes redundant; **position** went learned → RoPE (<!-- secxref:E.3 -->[§E.3](appendix-e-modern-dense.md#sec-E.3)) to encode *relative* position and extrapolate past the trained length; **activation** went ReLU → GELU → SwiGLU (<!-- secxref:D.2 -->[§D.2](appendix-d-gpt2.md#sec-D.2), <!-- secxref:E.4 -->[§E.4](appendix-e-modern-dense.md#sec-E.4)) to add a learned multiplicative gate; **attention** went MHA → GQA → MLA (<!-- secxref:E.5 -->[§E.5](appendix-e-modern-dense.md#sec-E.5), <!-- secxref:G.5 -->[§G.5](appendix-g-moe.md#sec-G.5)) to shrink the KV cache for long-context serving; and the **feed-forward** layer went dense → MoE (<!-- secxref:G.1 -->[§G.1](appendix-g-moe.md#sec-G.1)) to decouple capacity from compute. That is the whole difference between a 2019 model and a 2025 one.

<!-- sec:H.3 -->
### <a id="sec-H.3"></a>H.3 The Scaling Account

<a id="p-h3-the-scaling-account-1"></a><!-- para:h3-the-scaling-account-1 --> Four relations, derived once across the series, govern every model's cost. Collected as a reference card:

| quantity | relation |
|---|---|
| total parameters | $N \approx (V+T_{ctx})\,d + L\,(4d^2 + 3\,d\,d_{ff})$, with the FFN term over routed experts for MoE |
| training compute | $C \approx 6\,N\,D$ FLOPs over $D$ tokens |
| inference compute | $\approx 2\,N_{\text{active}}$ FLOPs per token |
| training memory | $\approx 16\,N$ bytes (weights, gradients, fp32 master, Adam $m$, $v$) |
| KV cache | $2\,L\,G\,d_{\text{head}}\,T\,b$ (GQA), or $L\,(d_c+d_h^R)\,T\,b$ (MLA) |

<a id="p-h3-the-scaling-account-2"></a><!-- para:h3-the-scaling-account-2 --> These were established in the parameter and compute accounting of <!-- secxref:D.3 -->[§D.3](appendix-d-gpt2.md#sec-D.3), the SwiGLU width rule of <!-- secxref:E.1 -->[§E.1](appendix-e-modern-dense.md#sec-E.1), the memory wall of <!-- secxref:F.2 -->[§F.2](appendix-f-scaling.md#sec-F.2), the KV-cache analyses of <!-- secxref:E.5 -->[§E.5](appendix-e-modern-dense.md#sec-E.5) and <!-- secxref:G.5 -->[§G.5](appendix-g-moe.md#sec-G.5), and the active-vs-total split of <!-- secxref:G.4 -->[§G.4](appendix-g-moe.md#sec-G.4). The one structural change across the whole ladder is the appearance of $N_{\text{active}} \neq N$ in the last row of the master table: until MoE, the same $N$ sets parameters, compute, *and* memory; after it, capacity and per-token cost are separately tunable. Everything else is the same arithmetic at larger dimensions.

<!-- sec:H.4 -->
### <a id="sec-H.4"></a>H.4 The Invariant Core

<a id="p-h4-the-invariant-core-1"></a><!-- para:h4-the-invariant-core-1 --> Strip away the five refinements and what remains is identical in all five models, and was gradient-checked end-to-end in <!-- secxref:C.5 -->[§C.5](appendix-c-toy-transformer.md#sec-C.5): tokens enter a residual stream by embedding lookup; each block reads the stream through a normalization, mixes positions with the scaled-dot-product attention of <!-- secxref:A.6 -->[§A.6](appendix-a-qkv-first-principles.md#sec-A.6) (the QK/OV circuits of <!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2)), and transforms features through a feed-forward layer, each sublayer added back to the stream; a final norm and an unembedding produce logits; cross-entropy scores them; and the gradient of that loss, computed by the exact backward pass of <!-- secxref:C.3 -->[§C.3](appendix-c-toy-transformer.md#sec-C.3), drives the Adam update of <!-- secxref:C.4 -->[§C.4](appendix-c-toy-transformer.md#sec-C.4). The toy and DeepSeek-V3 run the same five lines of computation. A reader who can derive the $203$-parameter model — forward, backward, and one optimizer step — has, up to five well-motivated substitutions and a great deal of width, derived the frontier.

<!-- sec:H.5 -->
### <a id="sec-H.5"></a>H.5 Reading the Ladder for a Coding Model

<a id="p-h5-reading-the-ladder-for-a-coding-model-1"></a><!-- para:h5-reading-the-ladder-for-a-coding-model-1 --> For a coding system specifically, the ladder is a menu of operating points. The dense 7B–70B band (Appendices E–F) is the latency-and-cost tier: small enough to serve cheaply, with GQA and long context (<!-- secxref:F.3 -->[§F.3](appendix-f-scaling.md#sec-F.3)) sized for repository-scale inputs, which is why open code models concentrate there — Code Llama at 7B–70B <!-- cite:6 --> [[6]](references.md#ref-6) and DeepSeek-Coder at 1.3B–33B <!-- cite:10 --> [[10]](references.md#ref-10). The MoE frontier (Appendix G) is the capacity tier: DeepSeek-Coder-V2 buys $236$B of knowledge at $21$B-active cost <!-- cite:43 --> [[43]](references.md#ref-43), the right trade when quality dominates and the serving fleet can hold the experts in memory. Both tiers share the code-specific choices the main survey treats in depth — fill-in-the-middle training for infilling, long context for whole-file reasoning, and the compute-optimal-versus-over-trained tension of <!-- secxref:3.6 -->[§3.6](language-models-from-first-principles.md#sec-3.6). The architecture is settled; for code, the engineering is in the data, the context, and the choice of rung.
