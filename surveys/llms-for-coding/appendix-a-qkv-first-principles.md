## A Query, Key, and Value from First Principles

<a id="p-a-query-key-and-value-from-first-principles-1"></a><!-- para:a-query-key-and-value-from-first-principles-1 --> Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3) introduced self-attention as a content-addressed, data-dependent matched filter and gave its defining equation. This appendix asks a sharper question: once a Transformer is *trained*, what do the learned projection matrices $W_Q$, $W_K$, $W_V$ actually mean? The answer is at first deflating and ultimately clarifying — **the three matrices are not individually meaningful; the network only ever uses two gauge-invariant products.** Everything below is derived from the definition of attention with no skipped steps, and each result is paired with an intuition — several in signal-processing terms, for a reader who thinks in correlators, kernels, and noise floors <!-- cite:54 --> [[54]](references.md#ref-54).

<a id="p-a-query-key-and-value-from-first-principles-2"></a><!-- para:a-query-key-and-value-from-first-principles-2 --> Notation follows three rules throughout: vectors are **bold lowercase columns** ($\mathbf{x}$, $\mathbf{q}$), matrices are non-bold capitals ($W_Q$, $M$), and scalars are non-bold lowercase ($s_{ij}$, $d_k$). The plan: A.1 fixes notation; A.2 and A.3 collapse the six projection matrices into two operators; A.4 proves the gauge freedom that makes the raw matrices unobservable; A.5 and A.6 give two intuitions (kernel regression, matched filter); A.7 derives the $1/\sqrt{d_k}$ scaling; A.8 shows how to *read* a trained head through the singular value decompositions of its two operators; A.9 builds an induction head by hand; A.10 extends to multiple heads; A.11 derives why the QK and OV circuits co-adapt, so neither is meaningful in isolation.

<!-- sec:A.1 -->
### <a id="sec-A.1"></a>A.1 Setup and Notation

<a id="p-a1-setup-and-notation-1"></a><!-- para:a1-setup-and-notation-1 --> A token's residual-stream vector is a column $\mathbf{x}_i \in \mathbb{R}^{d}$, and the $T$ tokens of a context form the columns of $X \in \mathbb{R}^{d\times T}$. A single attention head owns four learned matrices: query, key, and value projections $W_Q, W_K \in \mathbb{R}^{d_k\times d}$ and $W_V \in \mathbb{R}^{d_v\times d}$, and an output projection $W_O \in \mathbb{R}^{d\times d_v}$ (the head's slice of the multi-head output map of A.10). Per position, $\mathbf{q}_i = W_Q\mathbf{x}_i$, $\mathbf{k}_j = W_K\mathbf{x}_j$, and $\mathbf{v}_j = W_V\mathbf{x}_j$. Stacking these column vectors as the rows of $Q, K, V$ recovers the compact matrix form of Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3):

<a id="eq-1"></a><!-- eq:A-1 -->
$$
\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V. \tag{1}
$$

<a id="p-a1-setup-and-notation-2"></a><!-- para:a1-setup-and-notation-2 --> To read Equation <!-- ref:A-1 -->[(1)](#eq-1) one position at a time, unpack each matrix operation entrywise. Stacking the per-token column vectors as rows makes row $i$ of $Q$ equal to $\mathbf{q}_i^{\top}$ and row $j$ of $K$ equal to $\mathbf{k}_j^{\top}$, so the $(i,j)$ entry of $QK^{\top}$ is the dot product $\mathbf{q}_i^{\top}\mathbf{k}_j$; dividing by $\sqrt{d_k}$ gives the score $s_{ij}$. The softmax acts independently on each row, and the causal mask sends every entry with $j > i$ to $-\infty$ (so its weight is $0$), leaving row $i$ to normalize only over $j \le i$, which gives the weight $a_{ij}$. Finally, multiplying by $V$ reads, in row $i$, as the combination $\sum_{j\le i} a_{ij}\mathbf{v}_j$ of value rows. Componentwise, then, for query $i$:

<a id="eq-2"></a><!-- eq:A-2 -->
$$
s_{ij} = \frac{\mathbf{q}_i^{\top} \mathbf{k}_j}{\sqrt{d_k}}, \qquad
a_{ij} = \frac{e^{s_{ij}}}{\sum_{j'\le i} e^{s_{ij'}}}, \qquad
\mathbf{o}_i = \sum_{j\le i} a_{ij}\, \mathbf{v}_j, \tag{2}
$$

<a id="p-a1-setup-and-notation-3"></a><!-- para:a1-setup-and-notation-3 --> where $j \le i$ encodes the causal mask (a decoder position attends only to the past, the masking of Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3)). The head's contribution to the residual stream is the output passed through $W_O$, written additively: $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$. These are the only objects in play; the rest of the appendix rewrites them. Figure A.1 traces these objects — the four learned matrices and the activations they produce — through one head.

<a id="p-a1-setup-and-notation-4"></a><!-- para:a1-setup-and-notation-4 --> ![Block diagram of one attention head: a residual-stream vector fans into the learned projections W_Q and W_K (the QK circuit, shaded purple) and W_V (the OV circuit, shaded green); the scaled dot product of the resulting query and key feeds a causal softmax whose weights average the value vectors into the head output o, which the output projection W_O maps back to the additive residual-stream update Delta-x](figures/qkv-head-parameters.svg)

<!-- sec:A.1-figure-a -->
<a id="p-a1-setup-and-notation-5"></a><!-- para:a1-setup-and-notation-5 --> <a id="sec-A.1-figure-a"></a>**Figure A.1.** The parameters in one attention head, with Equation <!-- ref:A-1 -->[(1)](#eq-1) read as a left-to-right dataflow. A residual-stream vector $\mathbf{x}\in\mathbb{R}^{d}$ is read by the head's **four** learned matrices — the query and key projections $W_Q, W_K\in\mathbb{R}^{d_k\times d}$ and the value and output projections $W_V\in\mathbb{R}^{d_v\times d}$, $W_O\in\mathbb{R}^{d\times d_v}$ — whereas $\mathbf{q}_i, \mathbf{k}_j, \mathbf{v}_j, \mathbf{o}_i$ are *computed* intermediates, not parameters. The scaled dot product $\mathbf{q}_i^{\top}\mathbf{k}_j/\sqrt{d_k}$ feeds a causal softmax over $j\le i$ whose weights $a_{ij}$ average the values into $\mathbf{o}_i=\sum_{j\le i}a_{ij}\mathbf{v}_j$ (Equation <!-- ref:A-2 -->[(2)](#eq-2)), and $W_O$ maps that back to the additive update $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$ summed into the stream. The matrices are colored by the two products the network actually uses: $W_Q, W_K$ form the QK circuit $M=W_Q^{\top}W_K$ (<!-- secref:A.2 -->[§A.2](#sec-A.2)) and $W_V, W_O$ form the OV circuit $W_{OV}=W_OW_V$ (<!-- secref:A.3 -->[§A.3](#sec-A.3)) — the collapse the rest of the appendix builds on. The per-head parameter count follows directly from the shapes shown, $\lvert W_Q\rvert+\lvert W_K\rvert+\lvert W_V\rvert+\lvert W_O\rvert = 2d(d_k+d_v)$, which for the base Transformer ($d=512$, $d_k=d_v=64$ <!-- cite:54 --> [[54]](references.md#ref-54)) is $131{,}072$ per head; concrete magnitudes across real code models are tabled in <!-- secref:A.13 -->[§A.13](#sec-A.13). The same head is also drawn as a [canonical scaled-dot-product-attention block](figures/qkv-head-parameters-alt.svg) — the three input projections feeding one attention block, then the output projection — as an alternative view. Regenerate via `surveys/llms-for-coding/figures/qkv-head-parameters.py` (and `qkv-head-parameters-alt.py` for the alternative view).

> <a id="p-a1-setup-and-notation-6"></a><!-- para:a1-setup-and-notation-6 --> **Note — Why is it called the "residual stream"?** Two ideas, both visible
> in Figure A.1. *Residual:* each block is wired as a skip connection
> $\mathbf{x}\leftarrow\mathbf{x}+F(\mathbf{x})$, so it learns only an additive
> *correction* — for a head, the $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$ of
> Equation <!-- ref:A-2 -->[(2)](#eq-2) — never a replacement. *Stream:* because
> every block only adds, the per-token vector is never overwritten; it
> accumulates from the embedding through every layer as one channel that each
> head and MLP reads from (via $W_Q,W_K,W_V$) and writes back to (via $W_O$).
> The full account is in <!-- secref:A.15 -->[§A.15](#sec-A.15).

> <a id="p-a1-setup-and-notation-7"></a><!-- para:a1-setup-and-notation-7 --> **Note — What is the relationship between $i$ and $j$, and what ranges do
> they take?** They are the **row and column indices of the attention map**,
> not quantities tied by an equation: $i$ is the *query* (the token doing the
> attending, selecting $\mathbf{q}_i$ and producing the output $\mathbf{o}_i$),
> $j$ is the *key/value* (the token attended to, selecting $\mathbf{k}_j$ and
> $\mathbf{v}_j$), so the pair $(i,j)$ picks out one entry $s_{ij}$ of
> $QK^{\top}$. *Unmasked,* both run independently over all positions,
> $i, j \in \{1,\dots,T\}$. *Under the causal mask,* $i$ still sweeps all $T$
> positions but the inner index is restricted to $j \le i$ — for a fixed query
> $i$, $j \in \{1,\dots,i\}$ (the diagonal $j=i$, self-attention, included),
> exactly the $\sum_{j\le i}$ support of Equation <!-- ref:A-2 -->[(2)](#eq-2).
> The full breakdown is in <!-- secref:A.14 -->[§A.14](#sec-A.14).

> <a id="p-a1-setup-and-notation-8"></a><!-- para:a1-setup-and-notation-8 --> **Note — How large are $d$, $T$, $d_k$, and $d_v$ in real models?** Across the
> acquired code-LLM sources the three symbols scale very differently. The
> *residual width* $d$ runs from $512$ in the original Transformer to about
> $7000$ in a 33B code model, growth bought mostly by adding layers and heads
> rather than widening each head. The *per-head dimension* $d_k = d_v$ is nearly
> frozen at $64$ to $128$ across a 500-fold parameter range. The *context length*
> $T$ is the one that exploded — from roughly $2000$ tokens in early models to
> $128{,}000$ in the latest, almost entirely through positional-encoding
> extension. A full sourced table, smallest to largest, is in <!-- secref:A.13 -->[§A.13](#sec-A.13).

<!-- sec:A.2 -->
### <a id="sec-A.2"></a>A.2 The Query–Key Collapse: Only $M = W_Q^{\top} W_K$ Governs the Pattern

<a id="p-a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-1"></a><!-- para:a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-1 --> Substitute the definitions $\mathbf{q}_i = W_Q\mathbf{x}_i$ and $\mathbf{k}_j = W_K\mathbf{x}_j$ into the score of Equation <!-- ref:A-2 -->[(2)](#eq-2) and regroup the matrix product, changing nothing:

<a id="eq-3"></a><!-- eq:A-3 -->
$$
s_{ij}
= \frac{(W_Q\mathbf{x}_i)^{\top}(W_K\mathbf{x}_j)}{\sqrt{d_k}}
= \frac{\mathbf{x}_i^{\top}\, W_Q^{\top} W_K\, \mathbf{x}_j}{\sqrt{d_k}}
= \frac{\mathbf{x}_i^{\top}\, M\, \mathbf{x}_j}{\sqrt{d_k}},
\qquad M \equiv W_Q^{\top} W_K \in \mathbb{R}^{d\times d}. \tag{3}
$$

<a id="p-a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-2"></a><!-- para:a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-2 --> Two consequences follow immediately. First, the entire attention pattern $A = \mathrm{softmax}(X^{\top} M X/\sqrt{d_k})$ depends on $W_Q$ and $W_K$ **only through the single matrix $M$**. Second, because $M$ is a product through the $d_k$-dimensional bottleneck, its rank is at most $d_k$, which is far smaller than $d$ in practice ($d_k = 64$ against $d$ in the thousands, A.10).

<a id="p-a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-3"></a><!-- para:a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-3 --> **Intuition.** $M$ is one learned bilinear form on the residual stream — a *comparison metric* that scores how much position $i$ wants to read from position $j$. It is generally **not symmetric**: the feature a token advertises when it is a *key* need not equal the feature it requests when it is a *query*, so the comparison is directed. Splitting $M$ into $W_Q$ and $W_K$ is a *low-rank factorization* (rank $\le d_k$) plus a compute trick: forming the per-position vectors $\mathbf{q}_i$ and $\mathbf{k}_j$ and dotting them costs far less than materializing the $d\times d$ matrix $M$. The factorization is an implementation detail; $M$ is the object that carries meaning. This is exactly the matrix the circuits literature calls the **QK circuit** — the query and key vectors are "intermediate results in the computation of the low-rank matrix" $W_Q^{\top} W_K$, which in this column-vector convention *is* our $M$ <!-- cite:59 --> [[59]](references.md#ref-59). Figure A.2 shows this single form directly — the score pattern it produces and its built-in asymmetry.

<a id="p-a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-4"></a><!-- para:a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-4 --> ![Two panels: the left is a heatmap of the T-by-T raw score matrix produced by the bilinear form M, visibly not symmetric; the right is a scatter of each off-diagonal entry of M against its mirror entry, spread off the diagonal line](figures/qkv-qk-collapse.svg)

<!-- sec:A.2-figure-a -->
<a id="p-a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-5"></a><!-- para:a2-the-querykey-collapse-only-m-w_qtop-w_k-governs-the-pattern-5 --> <a id="sec-A.2-figure-a"></a>**Figure A.2.** The query–key collapse: one $d\times d$ bilinear form governs the pattern. *Left:* the raw score matrix $s_{ij} = \mathbf{x}_i^{\top} M \mathbf{x}_j/\sqrt{d_k}$ — the entire $T\times T$ pattern is a function of the single matrix $M = W_Q^{\top} W_K$, and the explicit $d_k$-dimensional $\mathbf{q},\mathbf{k}$ path reproduces it to machine precision (here a maximum difference of $2\times 10^{-14}$), the collapse of Equation <!-- ref:A-3 -->[(3)](#eq-3) made literal. *Right:* $M$ is generally **not symmetric** — scattering each off-diagonal entry $M_{ab}$ against its mirror $M_{ba}$ spreads the points off the line $M_{ab} = M_{ba}$ (asymmetry $\lVert M-M^{\top}\rVert/\lVert M+M^{\top}\rVert \approx 1$), so the comparison is directed and the score matrix on the left is itself asymmetric. ($M$ is also rank $\le d_k$ — the bottleneck of Figure A.6.) Regenerate via `surveys/llms-for-coding/figures/qkv-qk-collapse.py`.

<!-- sec:A.3 -->
### <a id="sec-A.3"></a>A.3 The Output–Value Collapse: Only $W_{OV} = W_O W_V$ Governs the Content

<a id="p-a3-the-outputvalue-collapse-only-w_ov-w_o-w_v-governs-the-content-1"></a><!-- para:a3-the-outputvalue-collapse-only-w_ov-w_o-w_v-governs-the-content-1 --> Apply the same regrouping to the written update. Substitute $\mathbf{v}_j = W_V\mathbf{x}_j$ into $\mathbf{o}_i$ from Equation <!-- ref:A-2 -->[(2)](#eq-2) and pull $W_O$ through the sum:

<a id="eq-4"></a><!-- eq:A-4 -->
$$
\Delta\mathbf{x}_i = W_O\,\mathbf{o}_i
= W_O\!\left(\sum_{j\le i} a_{ij}\, W_V\mathbf{x}_j\right)
= \sum_{j\le i} a_{ij}\, W_O W_V\, \mathbf{x}_j
= \sum_{j\le i} a_{ij}\, W_{OV}\, \mathbf{x}_j,
\qquad W_{OV} \equiv W_O W_V \in \mathbb{R}^{d\times d}. \tag{4}
$$

<a id="p-a3-the-outputvalue-collapse-only-w_ov-w_o-w_v-governs-the-content-2"></a><!-- para:a3-the-outputvalue-collapse-only-w_ov-w_o-w_v-governs-the-content-2 --> So the *content* a head moves into position $i$ depends on $W_V$ and $W_O$ **only through the product $W_{OV}$** (again rank $\le d_v$). Equations <!-- ref:A-3 -->[(3)](#eq-3) and <!-- ref:A-4 -->[(4)](#eq-4) expose the architecture of a head as two independent computations: the **query–key operator $M$** decides *where to read*, contributing nothing to content, and the **output–value operator $W_{OV}$** decides *what to write*, contributing nothing to the pattern. The literature names these the **QK circuit** and the **OV circuit** and observes that they are "two largely independent computations: a QK circuit which computes the attention pattern, and an OV circuit which computes how each token affects the output if attended to" — the OV circuit being precisely the product $W_O W_V$ <!-- cite:59 --> [[59]](references.md#ref-59).

<!-- sec:A.4 -->
### <a id="sec-A.4"></a>A.4 Gauge Freedom: Why the Raw Matrices Are Not Observable

<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-1"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-1 --> The collapse of A.2 has a consequence that is easy to miss and impossible to unsee. Take any element $R \in \mathrm{GL}(d_k)$ — the group of invertible $d_k\times d_k$ matrices — and reparametrize the head by $W_Q \mapsto R W_Q$ and $W_K \mapsto R^{-\top} W_K$. The query–key operator is unchanged:

<a id="eq-5"></a><!-- eq:A-5 -->
$$
(R W_Q)^{\top}(R^{-\top} W_K)
= W_Q^{\top}\, R^{\top} R^{-\top}\, W_K
= W_Q^{\top} W_K = M. \tag{5}
$$

<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-2"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-2 --> Because $M$ is unchanged, every score, every attention weight, and the whole output of the head are bit-for-bit identical. The same holds for the value path: $W_V \mapsto S^{-1} W_V$ and $W_O \mapsto W_O S$ for any $S \in \mathrm{GL}(d_v)$ leave $W_{OV} = W_O W_V$ fixed. ==orange: The raw matrices therefore carry $d_k^2 + d_v^2$ unobservable degrees of freedom; the specific $W_Q$, $W_K$, $W_V$ in a checkpoint are one arbitrary representative of an infinite equivalence class, selected by initialization and optimizer path, not by the function the head computes.==

<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-3"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-3 --> **Intuition (signal processing).** Asking "what does the trained $W_Q$ mean?" is like asking for the absolute phase of a complex baseband signal: it is not an observable. Only phase *differences* are physical, and here the physical object is the *product* $M$ (and $W_{OV}$), not the factors. Any interpretation that reads structure off the columns of $W_Q$ in isolation is reading gauge, not signal. The two well-posed objects are $M$ and $W_{OV}$.

<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-4"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-4 --> Figure A.3 makes this concrete: a random $\mathrm{GL}(d_k)$ gauge transform moves the raw matrices by a large amount while leaving the attention matrix identical to machine precision.

<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-5"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-5 --> ![Two attention-weight heatmaps that are visually identical despite a large random gauge change to the query and key matrices, and a third heatmap of their difference at the scale of machine epsilon](figures/qkv-gauge-invariance.svg)

<!-- sec:A.4-figure-a -->
<a id="p-a4-gauge-freedom-why-the-raw-matrices-are-not-observable-6"></a><!-- para:a4-gauge-freedom-why-the-raw-matrices-are-not-observable-6 --> <a id="sec-A.4-figure-a"></a>**Figure A.3.** The query and key matrices are gauge, not signal. A random invertible reparametrization $W_Q \mapsto R W_Q$, $W_K \mapsto R^{-\top} W_K$ moves the raw matrices by about 240% in Frobenius norm, yet the causal attention matrix it produces (middle) is identical to the original (left) down to a maximum absolute difference of $3\times 10^{-15}$ — floating-point round-off (right). Only the product $M = W_Q^{\top} W_K$ of Equation <!-- ref:A-3 -->[(3)](#eq-3) is observable; ==orange: the factorization into $W_Q$ and $W_K$ is unobservable gauge.== Regenerate via `surveys/llms-for-coding/figures/qkv-gauge-invariance.py`.

<!-- sec:A.5 -->
### <a id="sec-A.5"></a>A.5 Intuition I: Attention Is Kernel Regression with a Learned Metric

<a id="p-a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-1"></a><!-- para:a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-1 --> Write the output of Equation <!-- ref:A-2 -->[(2)](#eq-2) in its explicit normalized form, using the bilinear score of Equation <!-- ref:A-3 -->[(3)](#eq-3):

<a id="eq-6"></a><!-- eq:A-6 -->
$$
\mathbf{o}_i = \frac{\sum_{j\le i} \kappa(i,j)\, \mathbf{v}_j}{\sum_{j\le i} \kappa(i,j)},
\qquad \kappa(i,j) = \exp\!\left(\frac{\mathbf{x}_i^{\top} M \mathbf{x}_j}{\sqrt{d_k}}\right). \tag{6}
$$

<a id="p-a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-2"></a><!-- para:a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-2 --> This is exactly **Nadaraya–Watson kernel regression**: the output at the query point is a kernel-weighted average of the "responses" $\mathbf{v}_j$, with kernel $\kappa$. ==blue: Attention is a kernel smoother whose kernel is the exponential of a bilinear form — and whose *metric is the learned matrix $M$==*. Training does not just fit regression targets (the values); it learns the geometry $M$ that decides which points are "near." When $M$ is symmetric positive definite, $\mathbf{x}_i^{\top} M \mathbf{x}_j$ is an inner product in the $M$-metric and $\kappa$ is a similarity kernel — but note it is the exponential of an *inner product*, not of a negative squared distance, so unlike a Gaussian RBF it *grows with alignment* rather than decaying with separation, and the softmax denominator (not a fixed bandwidth) supplies the normalization. The asymmetry transformers actually learn makes the kernel *directed*, with distinct read-side and write-side geometries. A reader who has tuned a kernel smoother has the right picture, except that here the metric $M$ — the kernel's whole geometry — is learned, the normalization is the softmax rather than a fixed bandwidth, and the smoothing runs over the sequence rather than over a fixed feature space. Figure A.4 shows both pictures — the kernel-weighted average it produces and why its kernel grows with alignment instead of peaking at the query like an RBF.

<a id="p-a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-3"></a><!-- para:a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-3 --> ![Two panels: the left is a 2-D scatter of token points colored by their value response with marker size showing the attention weight for a starred query and an arrow along the M-times-query direction; the right shows the attention kernel rising monotonically with alignment along a ray while a Gaussian RBF peaks at the query and decays](figures/qkv-kernel-regression.svg)

<!-- sec:A.5-figure-a -->
<a id="p-a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-4"></a><!-- para:a5-intuition-i-attention-is-kernel-regression-with-a-learned-metric-4 --> <a id="sec-A.5-figure-a"></a>**Figure A.4.** Attention is Nadaraya–Watson kernel regression with a learned metric. *Left:* a toy 2-D feature plane; each token $\mathbf{x}_j$ is a point colored by a scalar value response $v_j$ (standing in for the value $\mathbf{v}_j$), and the attention weights $a_j = \mathrm{softmax}_j(\mathbf{x}_q^{\top} M \mathbf{x}_j/\sqrt{d_k})$ for the starred query are drawn as marker size. The output $o = \sum_j a_j v_j$ is their kernel-weighted average — here $2.23$, pulled far from the plain mean $-0.12$ toward the tokens the kernel favors. Because the score is *linear* in $\mathbf{x}_j$, the weight grows along the $M\mathbf{x}_q$ direction: attention weights by **alignment** in the learned (anisotropic, symmetric-positive-definite) $M$-metric, not by proximity. *Right:* that is why the kernel is not a Gaussian RBF — along a ray through the query, the attention kernel $\exp(\mathbf{x}_q^{\top} M\mathbf{x}/\sqrt{d_k})$ (blue) grows monotonically with alignment, while a Gaussian RBF (green dashed) peaks at the query and decays; the softmax denominator of Equation <!-- ref:A-6 -->[(6)](#eq-6), not a fixed bandwidth, supplies the normalization. Regenerate via `surveys/llms-for-coding/figures/qkv-kernel-regression.py`.

<!-- sec:A.6 -->
### <a id="sec-A.6"></a>A.6 Intuition II: The Score Is a Learned Matched Filter

<a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-1"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-1 --> The same score supports the matched-filter reading of Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3), now made precise. The query $\mathbf{q}_i$ is a *template*, the keys $\{\mathbf{k}_j\}$ are *candidate signals*, the inner product $\mathbf{q}_i^{\top} \mathbf{k}_j$ is a correlator output, and the softmax is a *soft detector* — a temperature-$\tfrac{1}{\sqrt{d_k}}$ relaxation of $\arg\max$ that returns a peaked-but-smooth selection rather than a hard one. Through Equation <!-- ref:A-3 -->[(3)](#eq-3), $M = W_Q^{\top} W_K$ is the learned cross-correlation operator between query-content and key-content.

<a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-2"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-2 --> **First principles — what a matched filter is.** A matched-filter receiver decides which of several known templates $\{\mathbf{s}_j\}$ is present in a noisy observation $\mathbf{r} = \mathbf{s} + \mathbf{n}$, with white noise $\mathbf{n}\sim\mathcal{N}(\mathbf{0},\sigma^2 I)$. Filter $\mathbf{r}$ linearly and sample at the decision instant to get the scalar $\mathbf{h}^{\top}\mathbf{r}$, whose output signal-to-noise ratio is $\mathrm{SNR}(\mathbf{h}) = (\mathbf{h}^{\top}\mathbf{s})^2 / (\sigma^2 \lVert\mathbf{h}\rVert^2)$. By Cauchy–Schwarz, $(\mathbf{h}^{\top}\mathbf{s})^2 \le \lVert\mathbf{h}\rVert^2 \lVert\mathbf{s}\rVert^2$ with equality iff $\mathbf{h} \propto \mathbf{s}$, so the SNR-maximizing filter *is the template itself*, $\mathbf{h}^{\star} \propto \mathbf{s}$, and its output is the correlation $\mathbf{s}^{\top}\mathbf{r}$ — that is the entire content of the word "matched." With coloured noise of covariance $\Sigma$ the optimum whitens first, giving the statistic $\mathbf{s}^{\top}\Sigma^{-1}\mathbf{r}$, a Mahalanobis inner product in the $\Sigma^{-1}$ metric. Under equal priors and equal-energy templates the Bayes decision is $\hat{\jmath} = \arg\max_j \mathbf{s}_j^{\top}\mathbf{r}$, and the full posterior over which template is present is $p(j \mid \mathbf{r}) = \mathrm{softmax}_j(\mathbf{s}_j^{\top}\mathbf{r}/\sigma^2)$ — the softmax of the correlator bank, at a temperature fixed by the noise power $\sigma^2$.

> <a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-3"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-3 --> **Note — Why is that posterior *exactly* a softmax of correlators?** It is
> Bayes' rule, not an analogy. White-Gaussian noise makes the likelihood
> $p(\mathbf{r}\mid j)\propto\exp(-\lVert\mathbf{r}-\mathbf{s}_j\rVert^2/2\sigma^2)$;
> expanding the square, the $\lVert\mathbf{r}\rVert^2$ term is common to every
> hypothesis and — for equal-energy templates — so is $\lVert\mathbf{s}_j\rVert^2$,
> so both cancel in the normalization and only the correlator $\mathbf{s}_j^{\top}\mathbf{r}$
> survives in the exponent; the normalized exponential of those correlators *is*
> the softmax. The temperature $\sigma^2$ is the noise power — $\sigma^2\to 0$
> collapses it to $\arg\max$, large $\sigma^2$ flattens it toward uniform — and in
> attention $\sqrt{d_k}$ plays that role. The full derivation and the
> unequal-energy caveat are in <!-- secref:A.16 -->[§A.16](#sec-A.16).

<a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-4"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-4 --> **The mapping, procedure by procedure.** Read the score of Equation <!-- ref:A-2 -->[(2)](#eq-2) against that receiver and every step lines up:

| Procedure step | Matched-filter receiver | Attention head, query $i$ | Why it is the same operation |
|---|---|---|---|
| reference / template | known waveform $\mathbf{s}$ | query $\mathbf{q}_i = W_Q\mathbf{x}_i$ | the pattern being searched for |
| candidate bank | templates $\{\mathbf{s}_j\}$ | keys $\{\mathbf{k}_j = W_K\mathbf{x}_j\}_{j\le i}$ | the hypotheses scored against the reference |
| correlator | $\mathbf{s}_j^{\top}\mathbf{r}$ | $\mathbf{q}_i^{\top}\mathbf{k}_j = \mathbf{x}_i^{\top} M \mathbf{x}_j$ | an inner product is the matched-filter output at the decision instant |
| whitening metric | inverse noise covariance $\Sigma^{-1}$ | learned $M = W_Q^{\top}W_K$ | a bilinear form warping the comparison to the task geometry |
| noise-floor scaling | divide by $\sigma$ | divide by $\sqrt{d_k}$ | normalize the statistic to the no-signal fluctuation level |
| candidate gating | search / time gate | causal mask $s_{ij}\to-\infty$ for $j>i$ | restrict the hypothesis set |
| decision rule | $\arg\max_j$ (hard) | $\mathrm{softmax}_j$ at temperature $1/\sqrt{d_k}$ | softmax is a relaxed argmax, the posterior $\propto e^{s_{ij}}$ |
| readout | decode the detected template | $\mathbf{o}_i = \sum_{j\le i} a_{ij}\mathbf{v}_j$ | combine payloads by confidence (soft) instead of fetching one (hard) |
| deliver | emit the decoded message | $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$ | write the read-out message back to the stream |

<a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-5"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-5 --> **The load-bearing rows are exact, not loose.** The whitening-metric row is Equation <!-- ref:A-3 -->[(3)](#eq-3) itself: $s_{ij} = \mathbf{x}_i^{\top}M\mathbf{x}_j/\sqrt{d_k}$ is a correlator in the learned $M$-metric, the role the inverse noise covariance $\Sigma^{-1}$ plays for the optimal filter (<!-- secref:A.2 -->[§A.2](#sec-A.2)). The noise-floor row is equally literal: <!-- secref:A.7 -->[§A.7](#sec-A.7) derives that $\sqrt{d_k}$ is exactly the standard deviation of the raw score when query and key are uncorrelated, so dividing by it sets the softmax temperature — the detector's threshold — *at* the noise floor rather than above it. The readout and deliver rows are the OV circuit of <!-- secref:A.3 -->[§A.3](#sec-A.3): $W_V$ packages each candidate's payload and $W_O$ delivers the combined message.

<a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-6"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-6 --> **Where attention departs from the classical filter.** Four departures, now precise. *(i) Adaptive, but only in the loose sense* — the templates are generated from the data, $\mathbf{q}_i = W_Q\mathbf{x}_i$, so ==pink: the head is an **adaptive filter** whose bank is rebuilt per input==. The word needs care, because two senses of "adaptive" pull apart here. In the *loose* sense it means **input-dependent**, which attention is. In the *technical SP* sense an **adaptive filter** (LMS, RLS) drives its coefficients toward an MMSE optimum by a recursive, error-fed update across samples, $\mathbf{w}_{n+1} = \mathbf{w}_n + \mu\, e_n\, \mathbf{x}_n$ — and attention is **not** that: at inference it runs no such loop, the templates being a closed-form feedforward map of the current input with $W_Q, W_K$ frozen, so there is no error signal, no recursion, and no convergence. ==orange: The only learning is the offline training that *designs* the filter bank (analogous to choosing the templates/whitening of a matched filter), not an online adaptation of it==. This is why the procedures of <!-- secref:A.6 -->[§A.6](#sec-A.6) map cleanly onto a *fixed* matched filter — the detection operation — and not onto an LMS/RLS recursion that has no counterpart in the forward pass. *(ii) Learned, not noise-derived, metric* — a classical filter's whitening $\Sigma^{-1}$ is dictated by the noise statistics, whereas $M = W_Q^{\top}W_K$ is learned end-to-end and is generally **asymmetric**, a *directed* comparison rather than a symmetric Mahalanobis metric. *(iii) Soft, not hard* — the receiver commits to one template and decodes it, while attention keeps the whole posterior and returns the confidence-weighted average of payloads $\mathbf{o}_i = \sum_{j\le i} a_{ij}\mathbf{v}_j$, the MMSE-flavoured soft combiner that is exactly the kernel-regression dual of <!-- secref:A.5 -->[§A.5](#sec-A.5) rather than a detect-then-fetch. *(iv) Global and content-addressed* — the comparison runs over the whole causally masked sequence and is addressed by content, not by a fixed time-lag as in a convolution's local, position-addressed taps.

> <a id="p-a6-intuition-ii-the-score-is-a-learned-matched-filter-7"></a><!-- para:a6-intuition-ii-the-score-is-a-learned-matched-filter-7 --> **Note — How far is the learned $M$ from a whitening $\Sigma^{-1}$?** They
> share only one thing: both are the bilinear kernel of a quadratic comparison
> ($\mathbf{s}^{\top}\Sigma^{-1}\mathbf{r}$ versus $\mathbf{x}_i^{\top}M\mathbf{x}_j$).
> Otherwise $M$ is strictly more general — a covariance inverse is **symmetric,
> positive-definite, full-rank, and noise-derived**, whereas $M = W_Q^{\top}W_K$
> is generally **asymmetric, indefinite, rank $\le d_k \ll d$, and task-learned**.
> The sharpest gap is symmetry: split $M = M_{\mathrm{sym}} + M_{\mathrm{skew}}$;
> a $\Sigma^{-1}$ has no skew part, so the directed piece $M_{\mathrm{skew}}$ —
> which makes $i\!\to\!j$ differ from $j\!\to\!i$ — has no matched-filter
> counterpart at all. The full account is in <!-- secref:A.17 -->[§A.17](#sec-A.17).

<!-- sec:A.7 -->
### <a id="sec-A.7"></a>A.7 The $1/\sqrt{d_k}$ Scaling, Derived

<a id="p-a7-the-1sqrtd_k-scaling-derived-1"></a><!-- para:a7-the-1sqrtd_k-scaling-derived-1 --> Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3) stated that the $1/\sqrt{d_k}$ factor is a variance normalization; here is the second-moment argument in full. Model the entries of a query and a key as independent, mean-zero, variance-$\sigma^2$ random variables (the standard heuristic of the original paper, with $\sigma^2 = 1$) <!-- cite:54 --> [[54]](references.md#ref-54). The raw score is $\mathbf{q}^{\top}\mathbf{k} = \sum_{l=1}^{d_k} q_l k_l$, a sum over the scalar components. Each term has mean $\mathbb{E}[q_l k_l] = \mathbb{E}[q_l]\,\mathbb{E}[k_l] = 0$, and its variance is $\operatorname{Var}(q_l k_l) = \mathbb{E}[(q_l k_l)^2] - (\mathbb{E}[q_l k_l])^2 = \mathbb{E}[q_l^2]\,\mathbb{E}[k_l^2] - 0 = \sigma^4$, where the squared-mean term drops because $\mathbb{E}[q_l k_l] = 0$ and the remaining expectation factors by independence. The $d_k$ terms are independent, so variances add:

<a id="eq-7"></a><!-- eq:A-7 -->
$$
\mathbb{E}[\mathbf{q}^{\top}\mathbf{k}] = 0, \qquad
\operatorname{Var}(\mathbf{q}^{\top}\mathbf{k}) = \sum_{l=1}^{d_k} \operatorname{Var}(q_l k_l) = d_k\,\sigma^4,
\qquad \operatorname{std}(\mathbf{q}^{\top}\mathbf{k}) = \sigma^2\sqrt{d_k}. \tag{7}
$$

<a id="p-a7-the-1sqrtd_k-scaling-derived-2"></a><!-- para:a7-the-1sqrtd_k-scaling-derived-2 --> The raw score's spread grows like $\sqrt{d_k}$; dividing by $\sqrt{d_k}$ holds it at $\sigma^2$ regardless of head width. Without the correction, the softmax logits scale up with $d_k$, the largest logit runs away, and the softmax saturates into the regime "where it has extremely small gradients," which is precisely the failure the scaling is introduced to prevent <!-- cite:54 --> [[54]](references.md#ref-54).

<a id="p-a7-the-1sqrtd_k-scaling-derived-3"></a><!-- para:a7-the-1sqrtd_k-scaling-derived-3 --> **Intuition (signal processing).** This is the same move as normalizing a correlator's output by its noise standard deviation so that the detector operates in its sensitive regime rather than railing. The scaling fixes the softmax temperature to the *noise floor* of the scores, which is $\sqrt{d_k}$ wide, so that the temperature does not drift with head width.

<a id="p-a7-the-1sqrtd_k-scaling-derived-4"></a><!-- para:a7-the-1sqrtd_k-scaling-derived-4 --> ![Two panels: the left shows the standard deviation of raw scores growing as the square root of head width while scaled scores stay at one; the right shows the unscaled softmax peak weight climbing toward one as width grows while the scaled softmax stays flat and width-invariant above the uniform floor](figures/qkv-sqrt-dk-scaling.svg)

<!-- sec:A.7-figure-a -->
<a id="p-a7-the-1sqrtd_k-scaling-derived-5"></a><!-- para:a7-the-1sqrtd_k-scaling-derived-5 --> <a id="sec-A.7-figure-a"></a>**Figure A.5.** Why attention divides by $\sqrt{d_k}$, made numerical. *Left:* for queries and keys drawn with independent unit-variance entries, the standard deviation of the raw score $\mathbf{q}^{\top}\mathbf{k}$ tracks $\sqrt{d_k}$ exactly (about 8.0 at $d_k = 64$), confirming Equation <!-- ref:A-7 -->[(7)](#eq-7), while the $\sqrt{d_k}$-scaled score sits at 1 for every width. *Right:* the consequence for a softmax over 16 *independent* (no-signal) keys. The unscaled softmax grows spuriously confident as $d_k$ grows — its mean peak weight climbs from 0.43 toward 0.92 purely from noise, the saturated small-gradient regime — whereas the $\sqrt{d_k}$-scaled softmax is width-invariant, its mean peak weight pinned near 0.25 at every $d_k$, far above the $1/16$ uniform floor (the dotted line) yet, crucially, not growing with width. Scaling sets the temperature to the noise floor instead of letting it grow with width. Regenerate via `surveys/llms-for-coding/figures/qkv-sqrt-dk-scaling.py`.

<!-- sec:A.8 -->
### <a id="sec-A.8"></a>A.8 Reading a Trained Head: the SVD of the Two Circuits

<a id="p-a8-reading-a-trained-head-the-svd-of-the-two-circuits-1"></a><!-- para:a8-reading-a-trained-head-the-svd-of-the-two-circuits-1 --> Because $M$ and $W_{OV}$ are the observables, interpreting a trained head means decomposing *them*. Take the singular value decomposition $M = \sum_{r=1}^{d_k} \sigma_r\, \mathbf{u}_r \mathbf{w}_r^{\top}$ (at most $d_k$ nonzero singular values — the remaining terms vanish — by the rank bound of A.2). Substituting into Equation <!-- ref:A-3 -->[(3)](#eq-3) and using $\mathbf{x}_i^{\top} \mathbf{u}_r \mathbf{w}_r^{\top} \mathbf{x}_j = (\mathbf{u}_r^{\top}\mathbf{x}_i)(\mathbf{w}_r^{\top}\mathbf{x}_j)$ gives a sum of rank-one routing rules:

<a id="eq-8"></a><!-- eq:A-8 -->
$$
s_{ij} \;=\; \frac{1}{\sqrt{d_k}}\sum_{r=1}^{d_k} \sigma_r\, (\mathbf{u}_r^{\top}\mathbf{x}_i)\,(\mathbf{w}_r^{\top}\mathbf{x}_j). \tag{8}
$$

<a id="p-a8-reading-a-trained-head-the-svd-of-the-two-circuits-2"></a><!-- para:a8-reading-a-trained-head-the-svd-of-the-two-circuits-2 --> Each triple $(\sigma_r, \mathbf{u}_r, \mathbf{w}_r)$ says: route attention *from* positions whose residual has a large component along the query-side direction $\mathbf{u}_r$ *to* positions with a large component along the key-side direction $\mathbf{w}_r$, with strength $\sigma_r$. The top singular directions are what the head is "for," and the asymmetry $\mathbf{u}_r \ne \mathbf{w}_r$ is the directedness of A.2. The OV circuit reads the same way through its own SVD $W_{OV} = \sum_r \tau_r\, \mathbf{p}_r \mathbf{e}_r^{\top}$: applied to a fetched token, $W_{OV}\mathbf{x}_j = \sum_r \tau_r (\mathbf{e}_r^{\top}\mathbf{x}_j)\,\mathbf{p}_r$ reads the content along the input direction $\mathbf{e}_r$ and writes it along the output direction $\mathbf{p}_r$ with gain $\tau_r$. A channel with $\mathbf{p}_r = \mathbf{e}_r$ copies a feature back verbatim; a channel with $\mathbf{p}_r \ne \mathbf{e}_r$ *remaps* one feature to another — for example "the token here" to "the token to predict next," as in A.9.

<a id="p-a8-reading-a-trained-head-the-svd-of-the-two-circuits-3"></a><!-- para:a8-reading-a-trained-head-the-svd-of-the-two-circuits-3 --> ![Two panels: the left is a log-scale plot of the singular values of M showing eight significant values then a cliff to machine zero; the right shows attention weight from a u-aligned query rising monotonically with each key's alignment to the direction w](figures/qkv-lowrank-routing.svg)

<!-- sec:A.8-figure-a -->
<a id="p-a8-reading-a-trained-head-the-svd-of-the-two-circuits-4"></a><!-- para:a8-reading-a-trained-head-the-svd-of-the-two-circuits-4 --> <a id="sec-A.8-figure-a"></a>**Figure A.6.** The QK circuit is low-rank, and its SVD is the head's routing rule. *Left:* the singular value spectrum of $M = W_Q^{\top} W_K$ for $d_k = 8$ shows exactly eight significant singular values and then a cliff to machine zero — the head compares tokens inside an eight-dimensional subspace of the full residual space, never the whole thing. *Right:* a constructed rank-one routing circuit $M = c\,\mathbf{u} \mathbf{w}^{\top}$ with orthonormal $\mathbf{u}$, $\mathbf{w}$. A query aligned with $\mathbf{u}$ places attention on each key in monotone proportion to that key's alignment $g_j = \mathbf{w}^{\top}\mathbf{x}_j$ — from 0.19 on the most $\mathbf{w}$-aligned key down to 0.002 on the most anti-aligned (uniform would be $1/24 \approx 0.042$) — literally routing $\mathbf{u}$-queries onto $\mathbf{w}$-keys. Regenerate via `surveys/llms-for-coding/figures/qkv-lowrank-routing.py`.

<!-- sec:A.9 -->
### <a id="sec-A.9"></a>A.9 An Induction Head, Built by Hand

<a id="p-a9-an-induction-head-built-by-hand-1"></a><!-- para:a9-an-induction-head-built-by-hand-1 --> The cleanest demonstration that the pair $(M, W_{OV})$ *is* the head is to construct a useful one with no training and watch it work. An **induction head** completes a repeated pattern — given $\ldots [A][B]\ldots[A]$ it raises the probability of $[B]$ — by two sub-behaviors found empirically in trained transformers: *prefix matching* (attend back to tokens that were preceded by the current token) and *copying* (write the attended token into the next-token logits) <!-- cite:60 --> [[60]](references.md#ref-60).

<a id="p-a9-an-induction-head-built-by-hand-2"></a><!-- para:a9-an-induction-head-built-by-hand-2 --> Build it directly. Suppose each position $j$ carries a residual feature $\mathbf{x}_j$ that stacks two one-hot blocks: its own token $\mathbf{e}^{\text{own}}(\text{tok}_j)$ and its predecessor $\mathbf{e}^{\text{prev}}(\text{tok}_{j-1})$ — the predecessor block being what a previous-token head would have written one layer earlier. Define the two circuits as one-hot matchers:

<a id="eq-9"></a><!-- eq:A-9 -->
$$
M = \beta \sum_{a} \mathbf{e}^{\text{own}}(a)\, \mathbf{e}^{\text{prev}}(a)^{\top},
\qquad
W_{OV} = \gamma \sum_{a} \mathbf{e}^{\text{logit}}(a)\, \mathbf{e}^{\text{own}}(a)^{\top}. \tag{9}
$$

<a id="p-a9-an-induction-head-built-by-hand-3"></a><!-- para:a9-an-induction-head-built-by-hand-3 --> Then $\mathbf{x}_i^{\top} M \mathbf{x}_j \propto \beta\,[\,\text{tok}_i = \text{tok}_{j-1}\,]$: the score is large exactly when position $j$ follows an earlier copy of the current token — prefix matching. And $W_{OV}\mathbf{x}_j = \gamma\,\mathbf{e}^{\text{logit}}(\text{tok}_j)$ reads the attended position's own-token block and writes it to the logit space — copying. The strengths $\beta$ (match confidence) and $\gamma$ (copy confidence) are what a real head learns in its circuit norms. Nothing else is needed; the raw $W_Q, W_K, W_V$ never appear, because by A.2–A.3 only $M$ and $W_{OV}$ ever do.

<a id="p-a9-an-induction-head-built-by-hand-4"></a><!-- para:a9-an-induction-head-built-by-hand-4 --> ![Two panels: the left is a bar chart of the attention from the second occurrence of the trigger token, peaking sharply on the position that follows the first occurrence; the right is a bar chart of next-token probabilities peaking on the answer token](figures/qkv-induction-head.svg)

<!-- sec:A.9-figure-a -->
<a id="p-a9-an-induction-head-built-by-hand-5"></a><!-- para:a9-an-induction-head-built-by-hand-5 --> <a id="sec-A.9-figure-a"></a>**Figure A.7.** A hand-built induction head running on the stream `C A D B E F C ?`. *Left:* the attention from the second `C` (the trigger) concentrates with weight 0.91 on position 1 — the token `A` that followed the *first* `C` — exactly the prefix match of Equation <!-- ref:A-9 -->[(9)](#eq-9). *Right:* the OV circuit copies that attended token into the logits, so the head predicts `A` with probability 0.88 against roughly 0.025 for every other token. The whole head is the pair $(M, W_{OV})$; no optimization was run. Regenerate via `surveys/llms-for-coding/figures/qkv-induction-head.py`.

<!-- sec:A.10 -->
### <a id="sec-A.10"></a>A.10 Multiple Heads: a Sum of Low-Rank Circuits

<a id="p-a10-multiple-heads-a-sum-of-low-rank-circuits-1"></a><!-- para:a10-multiple-heads-a-sum-of-low-rank-circuits-1 --> A layer runs $h$ heads in parallel on different projections and sums their writes. Write the output projection as $h$ horizontally stacked $d\times d_v$ blocks, $W^O = [\,W_O^{(1)}\;\cdots\;W_O^{(h)}\,]$; then $W^O$ applied to the stacked per-head output column $[\,\mathbf{o}_i^{(1)};\cdots;\mathbf{o}_i^{(h)}\,]$ expands as $\sum_{\ell} W_O^{(\ell)}\mathbf{o}_i^{(\ell)}$ — concatenate-then-project is exactly the sum of per-head slices, not an approximation. So the layer's update is

<a id="eq-10"></a><!-- eq:A-10 -->
$$
\Delta\mathbf{x}_i = \sum_{\ell=1}^{h} \sum_{j\le i} a_{ij}^{(\ell)}\, W_{OV}^{(\ell)}\, \mathbf{x}_j,
\qquad
a_{ij}^{(\ell)} = \mathrm{softmax}_j\!\left(\frac{\mathbf{x}_i^{\top}\, M^{(\ell)}\, \mathbf{x}_j}{\sqrt{d_k}}\right), \tag{10}
$$

<a id="p-a10-multiple-heads-a-sum-of-low-rank-circuits-2"></a><!-- para:a10-multiple-heads-a-sum-of-low-rank-circuits-2 --> with one query–key operator $M^{(\ell)} = W_Q^{(\ell)\top} W_K^{(\ell)}$ and one output–value operator $W_{OV}^{(\ell)} = W_O^{(\ell)} W_V^{(\ell)}$ per head, each of rank at most $d_k$ or $d_v$. The original Transformer uses $h = 8$ heads with $d_k = d_v = d_{\text{model}}/h = 64$, so the total compute matches a single full-width head while the layer gets eight independent low-rank comparison subspaces — "different representation subspaces at different positions" <!-- cite:54 --> [[54]](references.md#ref-54). Understanding a layer therefore means understanding the *set* of circuit pairs $\{(M^{(\ell)}, W_{OV}^{(\ell)})\}$, each read by its SVD as in A.8 — not the raw projection matrices, which by A.4 are gauge.

<a id="p-a10-multiple-heads-a-sum-of-low-rank-circuits-3"></a><!-- para:a10-multiple-heads-a-sum-of-low-rank-circuits-3 --> ![Two panels. Left: a schematic dataflow of one layer — a single residual-stream box fans out into eight head pipelines, each a QK-circuit box feeding a causal softmax pattern into an OV-circuit box, and all eight per-head writes converge on one summation node that writes back a single update; an inset states the concatenate-then-project identity is exact to machine precision. Right: an eight-by-eight heatmap of pairwise routing dissimilarity between heads, with a zero (black) diagonal and large off-diagonal entries, above which a strip of eight equal colored segments tiles one total budget.](figures/qkv-multihead-sum.svg)

<!-- sec:A.10-figure-a -->
<a id="p-a10-multiple-heads-a-sum-of-low-rank-circuits-4"></a><!-- para:a10-multiple-heads-a-sum-of-low-rank-circuits-4 --> <a id="sec-A.10-figure-a"></a>**Figure A.8.** A layer is a sum of $h$ low-rank circuit pairs. *Left:* the dataflow of Equation <!-- ref:A-10 -->[(10)](#eq-10). One shared residual-stream vector $\mathbf{x}_i$ fans out to $h = 8$ head-pipelines; each head $\ell$ is the circuit pair $(M^{(\ell)}, W_{OV}^{(\ell)})$ — a QK routing operator of rank $\le d_k$ (the head's learned matched filter of A.6) feeding a causal softmax pattern $a^{(\ell)}$, which weights an OV content map of rank $\le d_v$ — and the $h$ per-head writes sum into one update $\Delta\mathbf{x}_i$. Concatenate-then-project is *exactly* this sum of per-head slices, not an approximation: for a random output projection $W^O$ at $d = 512$, $h = 8$, $d_v = 64$ the two sides differ by at most $1.4\times 10^{-14}$ — a check of the algebraic identity, which holds for any $W^O$, not a property measured on trained weights. In the kernel-regression and matched-filter readings of A.5–A.6, the layer is a bank of $h$ smoothers / matched filters, summed. *Right:* the plurality made numerical, and the conserved budget. Eight independent QK circuits $M^{(\ell)} = W_Q^{(\ell)\top} W_K^{(\ell)}$, each genuinely of rank $\le d_k = 8$, read one shared token stream $X$ ($T = 9$, a reduced demo scale) and produce eight distinct causal attention patterns. The $8\times 8$ matrix reports the pairwise routing dissimilarity (total-variation distance between heads' attention rows, a metric chosen here): exactly $0$ on the diagonal and large off-diagonal (mean $\approx 0.64$, max $\approx 0.76$), so the heads route the same tokens through different comparison subspaces — "different representation subspaces at different positions" <!-- cite:54 --> [[54]](references.md#ref-54) — yet are neither orthogonal by construction nor disjoint (no entry reaches $1$). The top strip shows the conserved budget $h\,d_k = 8\times 64 = 512 = d_{\text{model}}$: the eight heads tile one full-width head's budget. Understanding a layer therefore means understanding the set $\{(M^{(\ell)}, W_{OV}^{(\ell)})\}$, each read by its SVD as in A.8 — not the raw projections, which by A.4 are gauge. Regenerate via `surveys/llms-for-coding/figures/qkv-multihead-sum.py`.

<!-- sec:A.11 -->
### <a id="sec-A.11"></a>A.11 Why the QK and OV Circuits Co-Adapt

<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-1"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-1 --> A last derivation explains why $M$ and $W_{OV}$ co-adapt rather than being meaningful in isolation. Differentiate a weight $a_{ij}$ of Equation <!-- ref:A-2 -->[(2)](#eq-2) with respect to a score $s_{im}$ at an unmasked key ($m \le i$). Abbreviate the row normalizer as $Z_i \equiv \sum_{j'\le i} e^{s_{ij'}}$, so that $a_{ij} = e^{s_{ij}}/Z_i$. Two elementary derivatives feed the quotient rule: $\partial e^{s_{ij}}/\partial s_{im} = \delta_{jm}\,e^{s_{ij}}$, with ==blue: $\delta_{jm}$ the Kronecker delta (1 when $j=m$, else 0)==, because $e^{s_{ij}}$ varies with $s_{im}$ only when $j=m$; and $\partial Z_i/\partial s_{im} = e^{s_{im}}$, because only the $j'=m$ term of the sum carries $s_{im}$. Applying the quotient rule and simplifying term by term gives the softmax Jacobian, with no step skipped:

<a id="eq-11"></a><!-- eq:A-11 -->
$$
\begin{aligned}
\frac{\partial a_{ij}}{\partial s_{im}}
&= \frac{\partial}{\partial s_{im}}\!\left(\frac{e^{s_{ij}}}{Z_i}\right)
&&\text{(softmax definition)}\\
&= \frac{\left(\partial_{s_{im}} e^{s_{ij}}\right) Z_i \;-\; e^{s_{ij}}\left(\partial_{s_{im}} Z_i\right)}{Z_i^{2}}
&&\text{(quotient rule)}\\
&= \frac{\delta_{jm}\,e^{s_{ij}}\,Z_i \;-\; e^{s_{ij}}\,e^{s_{im}}}{Z_i^{2}}
&&\text{(insert the two derivatives)}\\
&= \delta_{jm}\,\frac{e^{s_{ij}}}{Z_i} \;-\; \frac{e^{s_{ij}}}{Z_i}\cdot\frac{e^{s_{im}}}{Z_i}
&&\text{(split; cancel one }Z_i\text{)}\\
&= \delta_{jm}\,a_{ij} \;-\; a_{ij}\,a_{im}
&&\text{(recognize the softmax weights)}\\
&= a_{ij}\,(\delta_{jm} - a_{im}).
&&\text{(factor out }a_{ij}\text{)}
\end{aligned} \tag{11}
$$

<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-2"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-2 --> Let $\boldsymbol{\delta}_i = \partial L/\partial \mathbf{o}_i$ be the loss gradient arriving at the head output. Two ingredients drive the calculation. The first is a single weight's effect on the loss. Because $a_{ij}$ enters the loss only through the head output $\mathbf{o}_i = \sum_{j'} a_{ij'} \mathbf{v}_{j'}$ (Equation <!-- ref:A-2 -->[(2)](#eq-2)), the chain rule through the $d_v$ components $o_{ik}$ of $\mathbf{o}_i$ gives:

<a id="eq-12"></a><!-- eq:A-12 -->
$$
\begin{aligned}
\frac{\partial L}{\partial a_{ij}}
&= \sum_{k} \frac{\partial L}{\partial o_{ik}}\,\frac{\partial o_{ik}}{\partial a_{ij}}
&&\text{(chain rule through }\mathbf{o}_i\text{)}\\
&= \sum_{k} \frac{\partial L}{\partial o_{ik}}\, v_{jk}
&&\text{(}\partial o_{ik}/\partial a_{ij}=v_{jk}\text{, the }k\text{th entry of }\mathbf{v}_j\text{)}\\
&= \left(\frac{\partial L}{\partial \mathbf{o}_i}\right)^{\!\top}\mathbf{v}_j
&&\text{(reassemble the inner product over }k\text{)}\\
&= \boldsymbol{\delta}_i^{\top}\mathbf{v}_j.
&&\text{(}\boldsymbol{\delta}_i\equiv\partial L/\partial\mathbf{o}_i\text{)}
\end{aligned} \tag{12}
$$

<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-3"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-3 --> The second ingredient is the softmax Jacobian $\partial a_{ij}/\partial s_{im} = a_{ij}\,(\delta_{jm}-a_{im})$ of Equation <!-- ref:A-11 -->[(11)](#eq-11). Since $s_{im}$ reaches the loss only through the weights $\{a_{ij}\}_{j}$, composing the two ingredients gives the gradient on a score:

<a id="eq-13"></a><!-- eq:A-13 -->
$$
\begin{aligned}
\frac{\partial L}{\partial s_{im}}
&= \sum_{j} \frac{\partial L}{\partial a_{ij}}\,\frac{\partial a_{ij}}{\partial s_{im}}
&&\text{(chain rule via the weights)}\\
&= \sum_{j} (\boldsymbol{\delta}_i^{\top}\mathbf{v}_j)\,a_{ij}\,(\delta_{jm}-a_{im})
&&\text{(insert both ingredients)}\\
&= \sum_{j} (\boldsymbol{\delta}_i^{\top}\mathbf{v}_j)\,a_{ij}\,\delta_{jm} \;-\; \sum_{j} (\boldsymbol{\delta}_i^{\top}\mathbf{v}_j)\,a_{ij}\,a_{im}
&&\text{(distribute the product)}\\
&= a_{im}\,\boldsymbol{\delta}_i^{\top}\mathbf{v}_m \;-\; a_{im}\sum_{j} a_{ij}\,(\boldsymbol{\delta}_i^{\top}\mathbf{v}_j)
&&\text{(}\delta_{jm}\text{ picks } j=m\text{; pull } a_{im}\text{)}\\
&= a_{im}\,\boldsymbol{\delta}_i^{\top}\!\left(\mathbf{v}_m - \sum_{j} a_{ij}\mathbf{v}_j\right)
&&\text{(factor out } a_{im}\boldsymbol{\delta}_i^{\top}\text{)}\\
&= a_{im}\,\boldsymbol{\delta}_i^{\top}(\mathbf{v}_m - \mathbf{o}_i).
&&\text{(collapse } \textstyle\sum_{j} a_{ij}\mathbf{v}_j=\mathbf{o}_i\text{)}
\end{aligned} \tag{13}
$$

<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-4"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-4 --> Gradient descent therefore *raises* the score $s_{im}$ — attends more to key $m$ — exactly when $\boldsymbol{\delta}_i^{\top}(\mathbf{v}_m - \mathbf{o}_i) < 0$, i.e. when pulling the output toward $\mathbf{v}_m$ reduces the loss. The attention pattern is thus trained, key by key, to read from positions whose fetched value (delivered through the OV circuit) helps; and symmetrically $W_{OV}$ is trained to make the fetched content helpful under the current pattern. The QK circuit learns *where to look* and the OV circuit learns *what to bring*, each conditioned on the other — which is the structural reason they are meaningful only as the paired circuits $M$ and $W_{OV}$, never as the six raw matrices. This descent argument shows the two circuits *co-adapt*; it does not by itself prove training converges to the specific low-rank routing or copy circuits of A.8–A.9 — those are what such a head can *implement*, and, for induction heads, are *observed* empirically in trained models (A.9), not a structure this single gradient identity guarantees.

<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-5"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-5 --> ![Two panels. Left: a schematic training loop — boxes for the QK circuit, the OV circuit, the output, and the loss connected left to right, with a backprop arrow returning to a gradient node that splits into two teaching arrows back to the QK and OV circuits, which are enclosed together as a pair. Right: a two-dimensional value-space scatter in which a hyperplane through the output point, perpendicular to the loss gradient, splits five value points into a green attend-more half and a red attend-less half, each point annotated with its signed dot product.](figures/qkv-coadaptation.svg)

<!-- sec:A.11-figure-a -->
<a id="p-a11-why-the-qk-and-ov-circuits-co-adapt-6"></a><!-- para:a11-why-the-qk-and-ov-circuits-co-adapt-6 --> <a id="sec-A.11-figure-a"></a>**Figure A.9.** Why the QK and OV circuits co-adapt — one descent step, not convergence. *Left:* the training loop the score-gradient of Equation <!-- ref:A-13 -->[(13)](#eq-13) closes. The QK circuit $M$ routes (*where to look*), the OV circuit $W_{OV}$ fetches (*what to bring*), the output $\mathbf{o}_i$ (Equation <!-- ref:A-2 -->[(2)](#eq-2)) incurs a loss $L$, and the backprop gradient $\boldsymbol{\delta}_i = \partial L/\partial\mathbf{o}_i$ (Equation <!-- ref:A-12 -->[(12)](#eq-12)) splits into two symmetric teaching signals — one raises $s_{im}$ toward keys whose fetched value helps, the other shapes $W_{OV}$ to make that content helpful under the current pattern — so the head is meaningful only as the pair $(M, W_{OV})$, never as the six raw matrices. This is the optimizer's training loop across steps, not a per-token recursive filter update (cf. A.6). *Right:* the sign rule read geometrically in the head's output space (here $d_v = 2$ for plottability; the split is dimension-independent). For a representative loss gradient $\boldsymbol{\delta}_i$, the hyperplane through $\mathbf{o}_i$ with normal $\boldsymbol{\delta}_i$ splits the value points into an attend-more half (the $-\boldsymbol{\delta}_i$ side, $\boldsymbol{\delta}_i^{\top}(\mathbf{v}_j - \mathbf{o}_i) < 0$, green — descent raises $s_{ij}$) and an attend-less half (red — lowers $s_{ij}$); because $a_{ij} > 0$, the sign of $\partial L/\partial s_{ij}$ is the sign of that dot product. With weights $a_{ij} = [0.28, 0.14, 0.34, 0.08, 0.17]$ the output $\mathbf{o}_i = (0.75, 0.36)$ is the values' weighted mean (inside their convex hull, dotted); the five signed dots are $d_j = [+0.63, -3.02, +1.85, -1.51, -1.53]$. *Caveat — the paragraph's own:* this is one step's identity, showing co-adaptation, not convergence; it does not build the low-rank routing (A.8) or copy/induction (A.9) circuits, which are what a head can implement and, for induction heads, are observed empirically (A.9). Regenerate via `surveys/llms-for-coding/figures/qkv-coadaptation.py`.

<!-- sec:A.12 -->
### <a id="sec-A.12"></a>A.12 Summary

<a id="p-a12-summary-1"></a><!-- para:a12-summary-1 --> Understanding the trained $W_Q$, $W_K$, $W_V$ does not mean inspecting them. By Equations <!-- ref:A-3 -->[(3)](#eq-3) and <!-- ref:A-4 -->[(4)](#eq-4) a head is two operators: the **QK circuit** $M = W_Q^{\top} W_K$, a learned, asymmetric, low-rank bilinear form that *routes* attention — equivalently the metric of a Nadaraya–Watson kernel smoother (A.5) and the cross-correlation operator of a learned matched filter (A.6) — and the **OV circuit** $W_{OV} = W_O W_V$, the low-rank map of *what content moves*. The raw projection matrices carry $d_k^2 + d_v^2$ degrees of unobservable gauge (A.4), so the well-posed reading of a trained head is the SVD of its two circuits (A.8), which exposes routing rules and copy/transform maps directly — as the hand-built induction head of A.9 shows in miniature. The $1/\sqrt{d_k}$ factor is the noise-floor normalization that keeps the softmax detector sensitive at any head width (A.7), and a layer is just a sum of $h$ such low-rank circuit pairs (A.10), co-adapted by the gradient of Equation <!-- ref:A-13 -->[(13)](#eq-13).

<!-- sec:A.13 -->
### <a id="sec-A.13"></a>A.13 Concrete Dimensions in Real-World Models

<a id="p-a13-concrete-dimensions-in-real-world-models-1"></a><!-- para:a13-concrete-dimensions-in-real-world-models-1 --> Section <!-- secref:A.1 -->[§A.1](#sec-A.1) introduced a head's dimensions — the residual width $d$, the context length $T$, the per-head key and value widths $d_k$ and $d_v$, and (in <!-- secref:A.10 -->[§A.10](#sec-A.10)) the head count $h$ — as abstract symbols. Here are their concrete magnitudes, read directly from the architecture tables of the code-LLM papers this survey already cites, ordered from smallest to largest $d$. Every entry is a value its source prints; a dagger (†) marks a value the paper does *not* print, derived from the ones it does via the standard multi-head relation $d = h\,d_k$. Three widely used models report only parameter counts and context lengths and inherit their remaining dimensions from a base model without restating them — Codex <!-- cite:1 --> [[1]](references.md#ref-1), Code Llama <!-- cite:6 --> [[6]](references.md#ref-6), and DeepSeek-Coder-V2 <!-- cite:43 --> [[43]](references.md#ref-43) — so those dimensions are left out here rather than imported from another paper.

| Model (size) | params | $d$ | $L$ | $h$ (heads) | $d_k\!=\!d_v$ | $T$ trained |
|---|---|---|---|---|---|---|
| Transformer (base) | 65M | 512 | 6 | 8 | 64 | — |
| Transformer (big) | 213M | 1024 | 6 | 16 | 64 | — |
| phi-1 | 1.3B | 2048 | 24 | 32 | 64 | 2,048 |
| InCoder | 1.3B | 2048 | 24 | 32 | 64† | 2,048 |
| DeepSeek-Coder | 1.3B | 2048 | 24 | 16 | 128† | 16,384 |
| CodeGen | 2.7B | 2,560† | 32 | 32 | 80 | 2,048 |
| StarCoder2 | 3B | 3072 | 30 | 24 (2 KV) | 128† | 4,096 → 16,384 |
| Qwen2.5-Coder | 7B | 3,584 | 28 | 28 (4 KV) | 128 | 8,192 → 131,072 |
| DeepSeek-Coder | 6.7B | 4096 | 32 | 32 | 128† | 16,384 |
| Qwen2.5-Coder | 14B / 32B | 5120 | 48 / 64 | 40 (8 KV) | 128 | 8,192 → 131,072 |
| StarCoder | 15.5B | 6144 | 40 | 48 (1 KV, MQA) | 128† | 8,192 |
| DeepSeek-Coder | 33B | 7168 | 62 | 56 (7 KV, GQA) | 128† | 16,384 |

<a id="p-a13-concrete-dimensions-in-real-world-models-2"></a><!-- para:a13-concrete-dimensions-in-real-world-models-2 --> Here $L$ is the layer count and $h$ the number of query heads, with the shared key/value head count noted for the multi-query (MQA) and grouped-query (GQA) models; "$a \rightarrow b$" in the $T$ column means trained at length $a$ and extended to $b$ by rescaling the rotary positional encoding (RoPE / YaRN); "—" means the paper reports no fixed context window. Sources, in table order: Transformer <!-- cite:54 --> [[54]](references.md#ref-54); phi-1 <!-- cite:12 --> [[12]](references.md#ref-12); InCoder <!-- cite:4 --> [[4]](references.md#ref-4); DeepSeek-Coder, all sizes <!-- cite:10 --> [[10]](references.md#ref-10); CodeGen <!-- cite:3 --> [[3]](references.md#ref-3); StarCoder2 <!-- cite:9 --> [[9]](references.md#ref-9); Qwen2.5-Coder <!-- cite:11 --> [[11]](references.md#ref-11); StarCoder <!-- cite:8 --> [[8]](references.md#ref-8).

<a id="p-a13-concrete-dimensions-in-real-world-models-3"></a><!-- para:a13-concrete-dimensions-in-real-world-models-3 --> **Reading the table.**

<a id="p-a13-concrete-dimensions-in-real-world-models-4"></a><!-- para:a13-concrete-dimensions-in-real-world-models-4 --> **The residual width $d$** spans about an order of magnitude here — from $512$ in the original Transformer <!-- cite:54 --> [[54]](references.md#ref-54) to $7168$ in the 33B DeepSeek-Coder <!-- cite:10 --> [[10]](references.md#ref-10) — while the parameter count grows roughly 500-fold over the same span. Width is not where most of the scaling goes.

<a id="p-a13-concrete-dimensions-in-real-world-models-5"></a><!-- para:a13-concrete-dimensions-in-real-world-models-5 --> **The per-head width $d_k = d_v$** is the symbol that barely moves. It is $64$ in the 2017 Transformer <!-- cite:54 --> [[54]](references.md#ref-54) and still $64$ or $128$ in nearly every model since. Qwen2.5-Coder states the principle outright, printing a *head size* of $128$ for every size from 0.5B to 32B <!-- cite:11 --> [[11]](references.md#ref-11); at its smallest size that $128$ even exceeds $d/h = 896/14 \approx 64$, so the head width is held fixed by design rather than tracking $d/h$. The lone outlier is CodeGen, whose larger variants widen the head to $256$ <!-- cite:3 --> [[3]](references.md#ref-3).

<a id="p-a13-concrete-dimensions-in-real-world-models-6"></a><!-- para:a13-concrete-dimensions-in-real-world-models-6 --> **The head count $h$** carries the width that $d_k$ does not. It rises from $8$ in the base Transformer <!-- cite:54 --> [[54]](references.md#ref-54) to $48$–$56$ in the 15–33B code models <!-- cite:8 --> [[8]](references.md#ref-8), <!-- cite:10 --> [[10]](references.md#ref-10), and modern models decouple the *key/value* heads from the query heads: StarCoder's multi-query attention shares a single key/value head across all $48$ query heads <!-- cite:8 --> [[8]](references.md#ref-8), while the grouped-query attention of StarCoder2, the 33B DeepSeek-Coder, and Qwen2.5-Coder gives a handful of key/value groups to dozens of query heads <!-- cite:9 --> [[9]](references.md#ref-9), <!-- cite:10 --> [[10]](references.md#ref-10), <!-- cite:11 --> [[11]](references.md#ref-11). The $h$-fold sum of <!-- secref:A.10 -->[§A.10](#sec-A.10) counts query heads; the keys and values they read may be shared.

<a id="p-a13-concrete-dimensions-in-real-world-models-7"></a><!-- para:a13-concrete-dimensions-in-real-world-models-7 --> **The context length $T$** is where the real growth lives. The original Transformer fixes no context window at all — it batches by sentence length <!-- cite:54 --> [[54]](references.md#ref-54); the GPT-era code models train at $2{,}048$ <!-- cite:12 --> [[12]](references.md#ref-12), <!-- cite:4 --> [[4]](references.md#ref-4), <!-- cite:3 --> [[3]](references.md#ref-3); StarCoder reaches $8{,}192$ <!-- cite:8 --> [[8]](references.md#ref-8); the DeepSeek-Coder models and long-context StarCoder2 train to $16{,}384$ <!-- cite:10 --> [[10]](references.md#ref-10), <!-- cite:9 --> [[9]](references.md#ref-9); and the newest models reach $131{,}072$ tokens (128K) — Qwen2.5-Coder by YaRN extension from an $8{,}192$ file-level window <!-- cite:11 --> [[11]](references.md#ref-11), and DeepSeek-Coder-V2 to the same 128K on a 236B-total / 21B-active Mixture-of-Experts backbone <!-- cite:43 --> [[43]](references.md#ref-43). Code Llama sits between, trained at $16{,}384$ and shown stable to about $100{,}000$ tokens at inference <!-- cite:6 --> [[6]](references.md#ref-6). That is a roughly $64$-fold growth in $T$, almost all of it bought by rescaling the positional encoding rather than by enlarging the model.

<a id="p-a13-concrete-dimensions-in-real-world-models-8"></a><!-- para:a13-concrete-dimensions-in-real-world-models-8 --> **What to take away.**

- <a id="p-a13-concrete-dimensions-in-real-world-models-9"></a><!-- para:a13-concrete-dimensions-in-real-world-models-9 --> **Two of the three symbols barely scale.** The per-head width $d_k = d_v$ has stayed within a factor of two — $64$ to $128$ — for the architecture's entire history, and the residual width $d$ grew only about 14-fold (from $512$ to $7{,}168$) while the parameter count grew about 500-fold. Depth $L$ and head count $h$ do most of the scaling work.
- **The $1/\sqrt{d_k}$ normalization of <!-- secref:A.7 -->[§A.7](#sec-A.7) is evaluated at an almost-constant $d_k$.** Because $d_k$ is pinned near $64$–$128$, the noise-floor temperature $1/\sqrt{d_k}$ ranges only from $1/8$ (at $d_k = 64$) to about $1/11$ (at $d_k = 128$) across models that differ in size by orders of magnitude — the width-invariance that derivation promised is realized in practice by *holding $d_k$ fixed*.
- **The $h$-head sum of <!-- secref:A.10 -->[§A.10](#sec-A.10) is now asymmetric in keys and values.** Multi-query and grouped-query attention keep the query-head count $h$ large while sharing a few key/value heads, so the per-head circuits $M^{(\ell)}$ and $W_{OV}^{(\ell)}$ of <!-- secref:A.10 -->[§A.10](#sec-A.10) need not each own a private key/value projection — a serving-cost optimization (a smaller key/value cache) layered on the same circuit algebra.
- **$T$ is the runaway dimension, and it scales outside the head.** Context grows by rescaling the positional encoding, not by changing the linear algebra of <!-- secref:A.2 -->[§A.2](#sec-A.2)–<!-- secref:A.4 -->[§A.4](#sec-A.4) — which is why the gauge, circuit, and kernel-regression readings of this appendix are untouched by the 64-fold growth in context.

<a id="p-a13-concrete-dimensions-in-real-world-models-10"></a><!-- para:a13-concrete-dimensions-in-real-world-models-10 --> **Intuition.** In the kernel-regression picture of <!-- secref:A.5 -->[§A.5](#sec-A.5), a head is a smoother that averages over $T$ stored points using a comparison geometry of width $d_k$. Real models have grown the *number of stored points* $T$ some 64-fold while leaving the *width of each comparison* $d_k$ essentially unchanged — they read over far longer sequences without making any single query–key comparison wider. The residual stream $d$ widens only modestly, mostly to carry more parallel heads; the atom of attention — one $d_k$-dimensional matched filter, <!-- secref:A.6 -->[§A.6](#sec-A.6) — is almost the same size today as it was in 2017.

<!-- sec:A.14 -->
### <a id="sec-A.14"></a>A.14 The Query and Key Indices $i$ and $j$: Relationship and Ranges

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-1"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-1 --> Section <!-- secref:A.1 -->[§A.1](#sec-A.1) wrote the componentwise attention of Equation <!-- ref:A-2 -->[(2)](#eq-2) with two subscripts — $i$ on $\mathbf{q}_i, \mathbf{o}_i$ and $j$ on $\mathbf{k}_j, \mathbf{v}_j$. They are *not* tied to each other by an equation; they are the **row and column indices of the attention map** $QK^{\top}$, and the only thing linking them is the causal inequality $j \le i$. The roles each plays, and the range each takes, are:

| Index | Names | Role in the map | Object it selects | Range (causal) |
|---|---|---|---|---|
| $i$ | the **query** / "current" token | row $i$ — *who is looking* | $\mathbf{q}_i = W_Q\mathbf{x}_i$, output $\mathbf{o}_i$ | $1 \le i \le T$ |
| $j$ | the **key/value** / "source" token | column $j$ — *what is read* | $\mathbf{k}_j = W_K\mathbf{x}_j$, $\mathbf{v}_j = W_V\mathbf{x}_j$ | $1 \le j \le i$ |

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-2"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-2 --> **Term by term.**

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-3"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-3 --> **1. $i$ is the query position — the row.** It indexes the token doing the attending. Row $i$ of $Q$ is $\mathbf{q}_i^{\top}$, and one whole row of the score matrix — the scores $s_{ij}$ of position $i$ against every candidate $j$ — is what a single softmax normalizes into the weights that produce the output $\mathbf{o}_i$. There is one query index per token whose representation is being updated, so $i$ ranges over all $T$ positions of the context: $i \in \{1,\dots,T\}$.

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-4"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-4 --> **2. $j$ is the key/value position — the column.** It indexes a token being attended *to*. Column $j$ of $QK^{\top}$ carries $\mathbf{k}_j$ (what token $j$ advertises) and supplies $\mathbf{v}_j$ (what token $j$ contributes if read). Absent any mask, $j$ also ranges over all $T$ positions, *independently* of $i$, so $QK^{\top}$ is the full $T \times T$ grid of query–key dot products.

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-5"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-5 --> **3. The relationship is row-vs-column, coupled only by causality.** $i$ and $j$ are two independent indices over the *same* set of $T$ positions; the pair $(i,j)$ selects exactly one entry $s_{ij} = \mathbf{q}_i^{\top}\mathbf{k}_j/\sqrt{d_k}$ of $QK^{\top}$, which is why both subscripts appear on $s_{ij}$ and $a_{ij}$, but only $i$ survives on $\mathbf{o}_i$ — the column index is summed away. In a *decoder* the causal mask of Section <!-- secxref:3.3 -->[§3.3](language-models-from-first-principles.md#sec-3.3) sends every above-diagonal entry $j > i$ to $-\infty$, so for a fixed query $i$ the key index is restricted to $j \in \{1,2,\dots,i\}$ (equivalently $j \le i$), with the diagonal $j=i$ — a token attending to itself — included. That is exactly the support of the sums $\sum_{j\le i}$ in Equation <!-- ref:A-2 -->[(2)](#eq-2): $i$ still sweeps all $T$ positions, but the inner index $j$ never runs past $i$.

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-6"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-6 --> **What to take away.**

- <a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-7"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-7 --> **$i$ indexes outputs, $j$ indexes inputs.** Each produced vector $\mathbf{o}_i$ owns one value of $i$; the sum over $j$ collapses all read-from positions into that one output. An attention layer maps $T$ inputs to $T$ outputs — one output per query index $i$.
- **Both range over $\{1,\dots,T\}$; the mask only couples them.** Without the mask the two indices are free and $QK^{\top}$ is a dense $T\times T$ matrix; the causal constraint $j \le i$ is the *only* thing tying them, and it lower-triangularizes the map.

<a id="p-a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-8"></a><!-- para:a14-the-query-and-key-indices-i-and-j-relationship-and-ranges-8 --> **Intuition.** Read $i$ as "now" and $j$ as "now and the past." The output $\mathbf{o}_i = \sum_{j\le i} a_{ij}\,\mathbf{v}_j$ is then a **causal, time-varying combination** of the value sequence — structurally a causal FIR filter whose support grows with the position $i$, except the taps $a_{ij}$ are *data-dependent* (computed from the query–key scores through the softmax) rather than fixed. Masking $j > i$ to zero weight is precisely the no-peeking-at-the-future constraint; this is the same matched-filter reading developed in <!-- secref:A.6 -->[§A.6](#sec-A.6), now indexed explicitly in time.

<!-- sec:A.15 -->
### <a id="sec-A.15"></a>A.15 Why the Shared Vector Is Called the "Residual Stream"

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-1"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-1 --> Section <!-- secref:A.1 -->[§A.1](#sec-A.1) calls the per-token vector $\mathbf{x}_i$ the *residual stream*. The name packs two architectural facts; neither is arbitrary.

| Word | What it names | The math |
|---|---|---|
| **residual** | each block adds a *correction*, it does not replace | $\mathbf{x} \leftarrow \mathbf{x} + F(\mathbf{x})$; a head's correction is $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$ |
| **stream** | the sum is never overwritten, so it flows through the whole depth | $\mathbf{x}^{\text{out}} = \mathbf{x}^{\text{embed}} + \sum_{\ell}\Delta\mathbf{x}^{\text{attn}}_{\ell} + \sum_{\ell}\Delta\mathbf{x}^{\text{mlp}}_{\ell}$ |

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-2"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-2 --> **Term by term.**

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-3"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-3 --> **1. "Residual" — the block learns the correction, not the whole map.** Every attention and MLP sublayer is wired as a *skip (residual) connection*: its output is **added** to its input, $\mathbf{x}\leftarrow\mathbf{x}+F(\mathbf{x})$, rather than overwriting it. The sublayer therefore only has to produce the *residual* $F(\mathbf{x})$ — the part not already present, the leftover correction. For one attention head that residual is exactly the additive update $\Delta\mathbf{x}_i = W_O\mathbf{o}_i$ of Equation <!-- ref:A-2 -->[(2)](#eq-2): $W_O$ maps the head output back into the $d$-dimensional stream space and the result is summed in. Learning a small increment on top of an identity path is easier to optimize — and the identity path lets gradients reach early layers undamped — than learning a full input-to-output transform; this is the residual-connection device the Transformer adopts for every sublayer <!-- cite:54 --> [[54]](references.md#ref-54).

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-4"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-4 --> **2. "Stream" — the running sum is a shared channel, never overwritten.** Because every block only *adds*, the per-token vector is a cumulative sum that persists unmodified from the embedding at the bottom to the unembedding at the top: unrolling the per-block updates gives $\mathbf{x}^{\text{out}} = \mathbf{x}^{\text{embed}} + \sum_{\ell}\Delta\mathbf{x}^{\text{attn}}_{\ell} + \sum_{\ell}\Delta\mathbf{x}^{\text{mlp}}_{\ell}$. Read this way it is a single high-dimensional **communication channel**: each head and MLP *reads* the current value through its input projections ($W_Q, W_K, W_V$ for a head) and *writes* its contribution back additively (through $W_O$). The mechanistic-interpretability framing of attention names this channel the **residual stream** for exactly this reason — the additive, never-overwritten structure lets the final vector be decomposed into the separate contributions that flow down it <!-- cite:59 --> [[59]](references.md#ref-59). The toy transformer of <!-- secxref:C.1 -->[§C.1](appendix-c-toy-transformer.md#sec-C.1) realizes this concretely: a straight climb up one residual stream from the embedding to the logits, each sublayer reading and adding.

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-5"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-5 --> **What it buys.**

- <a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-6"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-6 --> **The stream is linear and additively decomposable.** The only nonlinearities live *inside* the sublayers (each reads through LayerNorm); the stream itself is a plain sum of contributions. This is the property that lets <!-- secref:A.2 -->[§A.2](#sec-A.2)–<!-- secref:A.4 -->[§A.4](#sec-A.4) and the $h$-head sum of <!-- secref:A.10 -->[§A.10](#sec-A.10) read each head's effect on the output in isolation — the whole circuit-reading program of this appendix rests on it.
- **The notation reflects it.** A head's contribution is written $\Delta\mathbf{x}_i$ — an *increment*, not a new state — precisely because the stream is a running sum of such deltas; this is why <!-- secref:A.1 -->[§A.1](#sec-A.1) writes $\Delta\mathbf{x}_i$ rather than a decorated $\mathbf{x}$.

<a id="p-a15-why-the-shared-vector-is-called-the-residual-stream-7"></a><!-- para:a15-why-the-shared-vector-is-called-the-residual-stream-7 --> **Intuition.** In signal-processing terms the residual stream is a **running accumulator refined by increments**: $\mathbf{x}^{(\ell+1)} = \mathbf{x}^{(\ell)} + \Delta^{(\ell)}$ has the shape of ==orange: an iterative-refinement / LMS-style state update — a running estimate (the state) plus a per-step correction (the innovation)==, each layer one refinement step. Equivalently it is a **shared signal bus with additive taps**: many components branch off one line, each reading the current value and summing its result back, so the line carries the *superposition* of all contributions, and ==orange: different heads — writing into different (roughly orthogonal) subspaces — are separated on read by their projections==, the matched filter of <!-- secref:A.6 -->[§A.6](#sec-A.6).

<!-- sec:A.16 -->
### <a id="sec-A.16"></a>A.16 Why the Soft Detector Is the Bayes Posterior

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-1"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-1 --> The *soft detector* of <!-- secref:A.6 -->[§A.6](#sec-A.6) is not a metaphor for a probability: under white-Gaussian noise the softmax of the correlator bank *is* the exact posterior over which template was sent, returned by Bayes' rule. Take $J$ known templates $\{\mathbf{s}_j\}$ of equal energy $\lVert\mathbf{s}_j\rVert^2 = E$, equal priors $p(j) = 1/J$, and an observation $\mathbf{r} = \mathbf{s}_j + \mathbf{n}$ corrupted by white noise $\mathbf{n}\sim\mathcal{N}(\mathbf{0},\sigma^2 I)$. The posterior over which template is present is, by Bayes' rule,

<a id="eq-14"></a><!-- eq:A-16-1 -->
$$
p(j \mid \mathbf{r}) = \frac{p(\mathbf{r}\mid j)\,p(j)}{\sum_{j'} p(\mathbf{r}\mid j')\,p(j')}. \tag{14}
$$

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-2"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-2 --> The Gaussian likelihood of an observation centred on template $j$ is

<a id="eq-15"></a><!-- eq:A-16-2 -->
$$
p(\mathbf{r}\mid j) = (2\pi\sigma^2)^{-d/2}\exp\!\left(-\frac{\lVert\mathbf{r}-\mathbf{s}_j\rVert^2}{2\sigma^2}\right). \tag{15}
$$

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-3"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-3 --> In Equation <!-- ref:A-16-1 -->[(14)](#eq-14) the prefactor $(2\pi\sigma^2)^{-d/2}$ and the equal prior $1/J$ are identical for every hypothesis, so they cancel between numerator and denominator: the posterior is the *normalized exponential of the negative squared distances*, minimum-distance detection in soft form. Expand that distance,

<a id="eq-16"></a><!-- eq:A-16-3 -->
$$
\lVert\mathbf{r}-\mathbf{s}_j\rVert^2 = \lVert\mathbf{r}\rVert^2 \;-\; 2\,\mathbf{s}_j^{\top}\mathbf{r} \;+\; \lVert\mathbf{s}_j\rVert^2, \tag{16}
$$

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-4"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-4 --> and two of its three terms drop out of the normalization: $\lVert\mathbf{r}\rVert^2$ does not depend on $j$, and the energy $\lVert\mathbf{s}_j\rVert^2 = E$ is the same for every template, so each is a common factor shared by numerator and denominator. Only the cross term $-2\,\mathbf{s}_j^{\top}\mathbf{r}$ survives, and putting it through the $-1/2\sigma^2$ in the exponent flips its sign and halves it, leaving $+\mathbf{s}_j^{\top}\mathbf{r}/\sigma^2$:

<a id="eq-17"></a><!-- eq:A-16-4 -->
$$
p(j \mid \mathbf{r}) = \frac{\exp(\mathbf{s}_j^{\top}\mathbf{r}/\sigma^2)}{\sum_{j'} \exp(\mathbf{s}_{j'}^{\top}\mathbf{r}/\sigma^2)} = \mathrm{softmax}_j\!\left(\frac{\mathbf{s}_j^{\top}\mathbf{r}}{\sigma^2}\right). \tag{17}
$$

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-5"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-5 --> **Why each piece is forced.**

- <a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-6"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-6 --> **The correlator is the sufficient statistic.** Once the always-constant $\lVert\mathbf{r}\rVert^2$ and the equal-energy $\lVert\mathbf{s}_j\rVert^2$ leave, $\mathbf{s}_j^{\top}\mathbf{r}$ is the *only* term that distinguishes hypotheses — which is why minimum-distance, maximum-correlation, and matched-filter detection are the same rule, and why the correlator, not the raw $\mathbf{r}$, is all the detector needs.
- **Softmax is the posterior, not a soft proxy for $\arg\max$.** The right-hand side of Equation <!-- ref:A-16-4 -->[(17)](#eq-17) is a normalized exponential of log-likelihoods — which *is* the definition of the softmax. So the head's weights are literally a-posteriori probabilities (the "APP" / soft information a MAP detector hands a decoder), not a heuristic relaxation.
- **The temperature is the noise power.** Write the exponent as $\mathbf{s}_j^{\top}\mathbf{r}/T$ with $T = \sigma^2$. The noise level *forces* the softness: $\sigma^2\to 0$ sends $T\to 0$ and the softmax to $\arg\max$ (no noise, decide hard); large $\sigma^2$ sends the posterior toward uniform (too noisy to prefer anyone). How sharply to commit is dictated by how much the measurement can be trusted, not chosen.

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-7"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-7 --> **The tie-back to attention.** Attention's score $\mathbf{q}_i^{\top}\mathbf{k}_j/\sqrt{d_k}$ has softmax temperature $\sqrt{d_k}$, the role $\sigma^2$ plays in Equation <!-- ref:A-16-4 -->[(17)](#eq-17): <!-- secref:A.7 -->[§A.7](#sec-A.7) shows $\sqrt{d_k}$ is exactly the standard deviation of the raw score when query and key are uncorrelated, so both divide the correlator by its noise scale to set the temperature at the noise floor. The weights $a_{ij}$ are therefore the posterior over *which key matches query $i$*, and $\mathbf{o}_i = \sum_{j\le i} a_{ij}\mathbf{v}_j$ is the posterior-mean readout — the soft-decision combiner, the kernel-regression dual of <!-- secref:A.5 -->[§A.5](#sec-A.5). One honest difference of bookkeeping: the matched filter divides by the noise *power* $\sigma^2$ because it presumes a known signal energy $E$, whereas attention divides by the noise *standard deviation* $\sqrt{d_k}$ because it presumes no signal — it normalizes the no-signal fluctuation to unit variance so that *learned* structure shows up as scores exceeding one.

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-8"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-8 --> **Caveat — unequal energies.** The clean "softmax of pure correlators" needs $\lVert\mathbf{s}_j\rVert^2 = E$. If the templates differ in energy, the $\lVert\mathbf{s}_j\rVert^2$ term in Equation <!-- ref:A-16-3 -->[(16)](#eq-16) does not cancel and reappears as a per-hypothesis bias, $p(j\mid\mathbf{r}) = \mathrm{softmax}_j\big((\mathbf{s}_j^{\top}\mathbf{r} - \tfrac{1}{2}\lVert\mathbf{s}_j\rVert^2)/\sigma^2\big)$ — an energy correction acting like a log-prior. Attention carries no explicit such term; the model folds any key-norm effect into the learned $W_K$ and $M$ of <!-- secref:A.2 -->[§A.2](#sec-A.2).

<a id="p-a16-why-the-soft-detector-is-the-bayes-posterior-9"></a><!-- para:a16-why-the-soft-detector-is-the-bayes-posterior-9 --> **Intuition.** In communications terms Equation <!-- ref:A-16-4 -->[(17)](#eq-17) is the symbol-wise a-posteriori-probability (APP) output of a soft-output detector: rather than slicing to the nearest constellation point, it reports the full posterior over symbols and passes it on as soft information. Attention is that detector with a *learned* constellation (the keys) and a *learned* metric ($M$), reading out a posterior-weighted payload instead of a decoded symbol.

<!-- sec:A.17 -->
### <a id="sec-A.17"></a>A.17 The Learned Metric $M$ versus the Whitening $\Sigma^{-1}$

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-1"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-1 --> The whitening-metric row of <!-- secref:A.6 -->[§A.6](#sec-A.6) lines $M = W_Q^{\top}W_K$ up with the inverse noise covariance $\Sigma^{-1}$ of an optimal matched filter. The two share exactly one property — each is the matrix $K$ in a quadratic comparison $\mathbf{a}^{\top}K\mathbf{b}$ (the statistic $\mathbf{s}^{\top}\Sigma^{-1}\mathbf{r}$ versus the score $\mathbf{x}_i^{\top}M\mathbf{x}_j$ of Equation <!-- ref:A-3 -->[(3)](#eq-3)) — and differ on everything else. $M$ is *strictly more general*: $\Sigma^{-1}$ is the special case of $M$ that is symmetric, positive-definite, full-rank, and noise-derived.

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-2"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-2 --> **The sharpest gap, made exact.** Split any $M$ into its symmetric and skew-symmetric parts:

<a id="eq-18"></a><!-- eq:A-17-1 -->
$$
M = \underbrace{\tfrac{1}{2}(M+M^{\top})}_{M_{\mathrm{sym}}} \;+\; \underbrace{\tfrac{1}{2}(M-M^{\top})}_{M_{\mathrm{skew}}}. \tag{18}
$$

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-3"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-3 --> A covariance inverse is symmetric, so $\Sigma^{-1}$ has *no* skew part — $M_{\mathrm{skew}}$ is exactly the piece of $M$ with no whitening-filter counterpart. It is what makes the comparison **directed**: $\mathbf{x}_i^{\top}M_{\mathrm{skew}}\mathbf{x}_j = -\mathbf{x}_j^{\top}M_{\mathrm{skew}}\mathbf{x}_i$, so the score reverses sign under $i \leftrightarrow j$ and the self-score $\mathbf{x}^{\top}M_{\mathrm{skew}}\mathbf{x} = 0$. Only $M_{\mathrm{sym}}$ could ever be a $\Sigma^{-1}$ — and even it differs, since it need not be positive-definite and is low-rank. So the analogy reaches *at most* the symmetric part of $M$.

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-4"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-4 --> **The four relaxations, in order of significance.**

| Property | $\Sigma^{-1}$ (whitening) | $M = W_Q^{\top}W_K$ | Consequence |
|---|---|---|---|
| symmetry | symmetric (a true metric) | generally **asymmetric** ($W_Q\neq W_K$) | $M$ encodes a *directed* read — what a token offers as a key need not equal what it seeks as a query; a symmetric metric cannot express this |
| definiteness | positive-definite | generally **indefinite** | scores may be negative; $\mathbf{x}^{\top}M\mathbf{x}$ is not a valid norm, while $\Sigma^{-1}$ always returns non-negative energy |
| rank | full-rank ($d\times d$) | rank $\le d_k \ll d$ (the bottleneck) | $M$ compares only inside a $d_k$-dimensional subspace (<!-- secref:A.2 -->[§A.2](#sec-A.2), <!-- secref:A.8 -->[§A.8](#sec-A.8)); whitening uses every direction |
| origin | noise-derived (fixed by the noise statistics, SNR-optimal) | task-learned (gradient descent on the loss) | $M$ can encode syntactic or semantic structure no noise model would produce |

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-5"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-5 --> **What to take away.**

- <a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-6"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-6 --> **$\Sigma^{-1}$ is a corner of the space $M$ lives in.** The matched-filter metric is the symmetric, positive-definite, full-rank, noise-optimal special case; $M$ relaxes all four. The single shared property is being the bilinear kernel of the comparison — the basis of the analogy, and its only load-bearing point.
- **The asymmetry is qualitative, not quantitative.** A whitening metric is symmetric *by definition*, so $M_{\mathrm{skew}}$ is not a "larger" or "smaller" $\Sigma^{-1}$ — it is outside the matched-filter picture entirely. This is also why the kernel-regression reading of <!-- secref:A.5 -->[§A.5](#sec-A.5) carries the explicit caveat "*when $M$ is symmetric positive-definite*" — that is exactly the corner where the metric analogy is clean.

<a id="p-a17-the-learned-metric-m-versus-the-whitening-sigma-1-7"></a><!-- para:a17-the-learned-metric-m-versus-the-whitening-sigma-1-7 --> **Intuition.** $\Sigma^{-1}$ is a reciprocal, energy-based (Mahalanobis / generalized-least-squares) metric: $d(\mathbf{a},\mathbf{b}) = d(\mathbf{b},\mathbf{a})$. The skew part of $M$ is a **non-reciprocal coupling** — the gain from $i$ to $j$ differs from the gain from $j$ to $i$, as in a non-Hermitian operator or a directed, non-reciprocal channel. Whitening cannot represent non-reciprocity at all; that is the part of attention that is genuinely *not* a matched filter.
