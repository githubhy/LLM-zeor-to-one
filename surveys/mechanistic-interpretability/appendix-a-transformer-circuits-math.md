<!-- sec:A -->
## <a id="sec-A"></a>A Transformer-circuits mathematics

<a id="p-a-transformer-circuits-mathematics-1"></a><!-- para:a-transformer-circuits-mathematics-1 --> **Depth tier:** headline

<a id="p-a-transformer-circuits-mathematics-2"></a><!-- para:a-transformer-circuits-mathematics-2 --> This appendix derives, from first principles, the residual-stream decomposition, the QK/OV factoring, virtual weights, and the composition types stated in § <!-- secxref:2 -->[§2](fundamentals.md#sec-2).

<a id="p-a-transformer-circuits-mathematics-3"></a><!-- para:a-transformer-circuits-mathematics-3 --> **How to read it.** <!-- secref:A.1 -->[§A.1](#sec-A.1)–<!-- secref:A.4 -->[§A.4](#sec-A.4) develop the circuits picture on top of the transformer as given. <!-- secref:A.5 -->[§A.5](#sec-A.5)–<!-- secref:A.8 -->[§A.8](#sec-A.8) then go *under* that floor and derive the things the primary sources state without deriving — where the softmax-weighted sum comes from at all (<!-- secref:A.5 -->[§A.5](#sec-A.5)), why the scale factor is $\sqrt{d_k}$ and why an unscaled score is harmful (<!-- secref:A.6 -->[§A.6](#sec-A.6)), why a concatenation of heads is really a sum (<!-- secref:A.7 -->[§A.7](#sec-A.7)), and what LayerNorm does to logit attribution (<!-- secref:A.8 -->[§A.8](#sec-A.8)). A reader who wants the ground floor should start at <!-- secref:A.5 -->[§A.5](#sec-A.5). <!-- secref:A.9 -->[§A.9](#sec-A.9) records where these sources argue less than their reputation suggests.

<a id="p-a-transformer-circuits-mathematics-4"></a><!-- para:a-transformer-circuits-mathematics-4 --> **Provenance.** The QK/OV factorization, virtual weights, the path-expansion trick and the three-way composition taxonomy are all due to Elhage et al. <!-- cite:1 --> [[1]](references.md#ref-1); the widely-cited later circuit papers re-state that framework rather than establish it, and this appendix cites the record. The underlying architecture is Vaswani et al. <!-- cite:101 --> [[101]](references.md#ref-101), and the specific model most of this survey's case studies use is GPT-2 <!-- cite:102 --> [[102]](references.md#ref-102).

<a id="p-a-transformer-circuits-mathematics-5"></a><!-- para:a-transformer-circuits-mathematics-5 --> **Two conventions, declared once** (per the two-bases rule, because the sources mix them and the mixture is not harmless). **(i) Token layout.** This appendix uses the **row-token** convention: a residual-stream state for a whole context is $X \in \mathbb{R}^{n_{\text{ctx}} \times d}$, one token per *row*, and a single token's state is a column vector $\mathbf{x} \in \mathbb{R}^{d}$. Elhage et al. use the **column-token** convention and write the attention pattern as $A = \mathrm{softmax}(x^{\top} W_Q^{\top} W_K x)$; under the row-token layout the same object is $\mathrm{softmax}(X W_{QK} X^{\top})$. The two differ by a transpose, and transcribing one form under the other's declared shapes produces an expression that is not even conformable — a mistake that has reached print in at least one re-statement of this material. **(ii) Head-dimension ratio.** $d_{\text{head}}/d$ is small, "around 1/10 to 1/100" in Elhage et al.'s survey of typical values <!-- cite:1 --> [[1]](references.md#ref-1); <!-- secref:A.7 -->[§A.7](#sec-A.7) shows this is exactly the statement that each head reads and writes a low-rank slice of the stream.

<!-- sec:A.1 -->
### <a id="sec-A.1"></a>A.1 The residual stream as a sum over paths

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-1"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-1 --> Unrolling the additive update of Equation [(1)](fundamentals.md#eq-1) <!-- xref:2-1 --> from $\mathbf{x}_0 = W_E\,\mathrm{onehot}(t)$ gives the final state as a plain sum of every component's write:

<a id="eq-1"></a><!-- eq:A-1 -->
$$
\mathbf{x}_L = W_E\,\mathrm{onehot}(t) + \sum_{\ell=1}^{L}\sum_{h=1}^{H}\mathrm{head}^{h}_\ell(\mathbf{x}_{\ell-1}) + \sum_{\ell=1}^{L}\mathrm{MLP}_\ell(\mathbf{x}_{\ell-1}). \tag{1}
$$

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-2"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-2 --> Because the unembedding is linear, the logits decompose the same way — a **direct-path** term plus one term per head and per MLP:

<a id="eq-2"></a><!-- eq:A-2 -->
$$
\boldsymbol{\ell} = W_U\,\mathbf{x}_L = \underbrace{W_U W_E\,\mathrm{onehot}(t)}_{\text{direct path (bigram)}} + \sum_{\ell,h} W_U\,\mathrm{head}^{h}_\ell + \sum_{\ell} W_U\,\mathrm{MLP}_\ell. \tag{2}
$$

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-3"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-3 --> This is the logit-attribution identity that underlies the "logit lens" (§ <!-- secxref:4.2 -->[§4.2](method-inventory-observational.md#sec-4.2)) and direct-logit-attribution analysis: each component's contribution to any output logit can be read independently because they *add*. **Equation <!-- ref:A-2 -->[(2)](#eq-2) is written as though the unembedding sees $\mathbf{x}_L$ directly, and in a real pre-LN model it does not** — a final LayerNorm sits on that path. The decomposition survives because that normalization is affine on any fixed-norm level set, but its residual error is exactly the term derived in <!-- secref:A.8 -->[§A.8](#sec-A.8), and every DLA magnitude in this survey inherits it. The matrices $W_U W_E$, and per head $W_U W_{OV}^h W_E$, are **virtual weights** — products never stored in the parameters but governing the interaction along a path.

<!-- sec:A.2 -->
### <a id="sec-A.2"></a>A.2 QK and OV circuits

<a id="p-a2-qk-and-ov-circuits-1"></a><!-- para:a2-qk-and-ov-circuits-1 --> With $W_Q^h, W_K^h, W_V^h \in \mathbb{R}^{d_{\text{head}}\times d}$ and $W_O^h \in \mathbb{R}^{d\times d_{\text{head}}}$, the attention score between destination $i$ and source $j$ is

<a id="eq-3"></a><!-- eq:A-3 -->
$$
s^h_{ij} = (W_Q^h \mathbf{x}_i)^{\!\top}(W_K^h \mathbf{x}_j) = \mathbf{x}_i^{\!\top}\,\underbrace{(W_Q^h)^{\!\top} W_K^h}_{W_{QK}^h}\,\mathbf{x}_j, \tag{3}
$$

<a id="p-a2-qk-and-ov-circuits-2"></a><!-- para:a2-qk-and-ov-circuits-2 --> a bilinear form on the *pair* of stream states, with $W_{QK}^h \in \mathbb{R}^{d\times d}$ of rank $\le d_{\text{head}}$. The head's write-back applies the OV circuit $W_{OV}^h = W_O^h W_V^h$ to the attended values:

<a id="eq-4"></a><!-- eq:A-4 -->
$$
\mathrm{head}^h(X)_i = \sum_j A^h_{ij}\,W_O^h W_V^h\,\mathbf{x}_j = \sum_j A^h_{ij}\,W_{OV}^h\,\mathbf{x}_j, \qquad A^h_{ij}=\operatorname*{softmax}_j\!\big(s^h_{ij}/\sqrt{d_{\text{head}}}\big). \tag{4}
$$

<a id="p-a2-qk-and-ov-circuits-3"></a><!-- para:a2-qk-and-ov-circuits-3 --> Sandwiching between embedding and unembedding gives the two token-by-token tables that make a head legible: the **QK bigram table** $W_E^{\top} W_{QK}^h W_E$ (which source token each destination token attends to) and the **OV copying table** $W_U W_{OV}^h W_E$ (which output logits an attended token promotes). A head whose OV copying table is approximately a positive multiple of the identity on the token-embedding subspace is a **copying head** — the OV signature of name-mover and induction heads (§ <!-- secxref:9 -->[§9](circuits-across-models.md#sec-9)).

<!-- sec:A.3 -->
### <a id="sec-A.3"></a>A.3 Composition and the induction head

<a id="p-a3-composition-and-the-induction-head-1"></a><!-- para:a3-composition-and-the-induction-head-1 --> A later head reads the residual stream, which by layer $\ell'$ already contains earlier heads' OV writes. Substituting the residual state $\mathbf{x} + W_{OV}^{A}\mathbf{x}$ (raw token plus head $A$'s write) into head $B$'s key map exposes a cross term — the **K-composition** virtual weight:

<a id="eq-5"></a><!-- eq:A-5 -->
$$
W_K^{B}\big(\mathbf{x} + W_{OV}^{A}\mathbf{x}\big) = \underbrace{W_K^{B}\mathbf{x}}_{\text{from raw token}} + \underbrace{W_K^{B} W_{OV}^{A}\,\mathbf{x}}_{\text{K-composition}}. \tag{5}
$$

<a id="p-a3-composition-and-the-induction-head-2"></a><!-- para:a3-composition-and-the-induction-head-2 --> Analogously $W_Q^{B} W_{OV}^{A}$ (Q-composition) and $W_V^{B} W_{OV}^{A}$ (V-composition). Q- and K-composition change *where* head $B$ attends (its pattern now depends on computed features, not raw tokens); V-composition changes only *what* it moves. The **induction head** is the canonical K-composition circuit: a previous-token head $A$ writes token $t{-}1$'s identity at position $t$, so head $B$'s key at each position encodes "the token that preceded me," and its query (the current token) matches the position *after* the last occurrence of the current token — implementing $[A][B]\dots[A]\!\to\![B]$ <!-- cite:1 --> [[1]](references.md#ref-1), <!-- cite:80 --> [[80]](references.md#ref-80).

<!-- sec:A.4 -->
### <a id="sec-A.4"></a>A.4 Why the residual stream has no privileged basis

<a id="p-a4-why-the-residual-stream-has-no-privileged-basis-1"></a><!-- para:a4-why-the-residual-stream-has-no-privileged-basis-1 --> Let $R\in\mathbb{R}^{d\times d}$ be orthogonal ($R^{\top}R = I$). Replace $\mathbf{x}\mapsto R\mathbf{x}$ everywhere, and simultaneously $W_E\mapsto R W_E$, $W_U\mapsto W_U R^{\top}$, and every reading matrix $W_{\{Q,K,V\},\text{in}}\mapsto W R^{\top}$ and writing matrix $W_{O,\text{out}}\mapsto R W$. Every inner product and every write is preserved:

<a id="eq-6"></a><!-- eq:A-6 -->
$$
(W R^{\top})(R\mathbf{x}) = W\mathbf{x}, \qquad R\,(W\,\cdot) \ \text{writes into the rotated frame identically}, \tag{6}
$$

<a id="p-a4-why-the-residual-stream-has-no-privileged-basis-2"></a><!-- para:a4-why-the-residual-stream-has-no-privileged-basis-2 --> so the function computed is unchanged. Hence no coordinate axis of the raw residual stream is special — meaning lives in *directions*, not coordinates. An elementwise nonlinearity breaks this symmetry (it does not commute with a general rotation), which is why the **post-nonlinearity** MLP-neuron basis, or an SAE's learned basis, is where axis-aligned features can exist at all — when a privileged basis *does* appear in the residual stream it is a phenomenon worth explaining in its own right <!-- cite:6 --> [[6]](references.md#ref-6), and the neuron/SAE basis is the formal justification for dictionary learning in § <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6).

<!-- sec:A.5 -->
### <a id="sec-A.5"></a>A.5 Where the softmax-weighted sum comes from

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-1"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-1 --> Everything above takes the attention operation as given. It is worth asking where it comes from, because the primary source does not say: Vaswani et al. introduce scaled dot-product attention as a *definition* and derive only its scale factor <!-- cite:101 --> [[101]](references.md#ref-101). The form is not arbitrary, and the derivation below is short enough that presenting it as a definition costs the reader more than it saves.

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-2"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-2 --> **Start from retrieval, which is what attention is for.** We hold $n$ key–value pairs $(\mathbf{k}_j, \mathbf{v}_j)$ and issue a query $\mathbf{q}$. The operation we actually want is a lookup: return the value whose key best matches the query,

<a id="eq-7"></a><!-- eq:A-5-1 -->
$$
\mathrm{lookup}(\mathbf{q}) \;=\; \mathbf{v}_{j^{\star}}, \qquad j^{\star} \;=\; \arg\max_{j}\; s_j, \qquad s_j \;=\; \mathrm{sim}(\mathbf{q}, \mathbf{k}_j). \tag{7}
$$

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-3"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-3 --> **Why that cannot be the operation.** Equation <!-- ref:A-5-1 -->[(7)](#eq-7) is piecewise constant in $\mathbf{q}$: perturb the query slightly and either nothing changes or the output jumps to a different value vector. Its gradient is therefore zero almost everywhere and undefined on the tie set, so it transmits no learning signal. A network that must be trained by gradient descent cannot use it.

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-4"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-4 --> **Relax the point mass, not the similarity.** The natural relaxation keeps the *shape* of the answer — a selection among positions — and softens the selection: replace the point mass $\delta_{j^{\star}}$ with a distribution $\mathbf{p}$ on the simplex $\Delta^{n-1}$ and return the expected value $\sum_j p_j \mathbf{v}_j$. This immediately gives the property that makes attention interpretable at all: **the output is a convex combination of value vectors**, so it lies in their convex hull and "the head moved information from position $j$ to position $i$" is a literal statement about $p_{ij}$, not a metaphor.

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-5"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-5 --> **Which distribution?** We want $\mathbf{p}$ to concentrate on high-similarity keys — that is the retrieval requirement — while staying spread out enough to keep a usable gradient. Those two demands are exactly an entropy-regularized linear program on the simplex:

<a id="eq-8"></a><!-- eq:A-5-2 -->
$$
\mathbf{p}^{\star} \;=\; \arg\max_{\mathbf{p}\,\in\,\Delta^{n-1}}\ \sum_j p_j s_j \;+\; \tau H(\mathbf{p}), \qquad H(\mathbf{p}) = -\sum_j p_j \log p_j, \quad \tau > 0. \tag{8}
$$

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-6"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-6 --> **Solve it.** Attach a multiplier $\mu$ to the constraint $\sum_j p_j = 1$ (the non-negativity constraints are inactive, since $H$ has infinite slope at $0$ and so pushes every $p_j$ strictly positive) and differentiate the Lagrangian $\mathcal{L} = \sum_j p_j s_j - \tau\sum_j p_j\log p_j - \mu\big(\sum_j p_j - 1\big)$:

<a id="eq-9"></a><!-- eq:A-5-3 -->
$$
\frac{\partial \mathcal{L}}{\partial p_j} \;=\; s_j - \tau\big(\log p_j + 1\big) - \mu \;=\; 0 \quad\Longrightarrow\quad p_j \;\propto\; e^{s_j/\tau}. \tag{9}
$$

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-7"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-7 --> Normalizing to the simplex fixes the constant and gives the boxed result. The objective is strictly concave ($H$ is strictly concave, the linear term is affine) on a convex set, so the stationary point is the unique global maximizer — this is a solution, not merely a critical point:

<a id="eq-10"></a><!-- eq:A-5-4 -->
$$
\boxed{\;\mathbf{p}^{\star} \;=\; \operatorname{softmax}(\mathbf{s}/\tau), \qquad \text{output} \;=\; \sum_j p^{\star}_j \mathbf{v}_j\;} \tag{10}
$$

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-8"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-8 --> **Read off three things.** First, **softmax is not a squashing function someone picked**: it is the unique maximizer of similarity-plus-entropy over the simplex, and any other normalization would be solving a different problem. Second, $\tau$ is a **temperature** and it interpolates the whole family — $\tau \to 0$ recovers the hard lookup of Equation <!-- ref:A-5-1 -->[(7)](#eq-7) *when the maximizing score is unique* (and spreads mass evenly across tied maximizers otherwise), while $\tau \to \infty$ gives uniform averaging over all positions. Third, the choice of $\mathrm{sim}$ is still open, and *bilinearity* narrows it: requiring the score to be bilinear in the two stream states — so that each side is read by its own learned linear map — forces the form $s_{ij} = \mathbf{x}_i^{\top} M\, \mathbf{x}_j$ for some $M \in \mathbb{R}^{d\times d}$, and nothing further. **Bilinearity alone permits $M$ to be full rank.** Writing $M = (W_Q)^{\top}W_K$ with both factors passing through a $d_{\text{head}}$-dimensional bottleneck is a *strictly stronger and independent* architectural choice — the one that makes the QK circuit of <!-- secref:A.2 -->[§A.2](#sec-A.2) low-rank — and <!-- secref:A.7 -->[§A.7](#sec-A.7) derives that consequence separately rather than smuggling it in here. The factorization is also not unique: $W_Q \mapsto G^{-\top}W_Q$, $W_K \mapsto G W_K$ leaves $M$ unchanged for any invertible $G$, a gauge freedom internal to the head.

<a id="p-a5-where-the-softmax-weighted-sum-comes-from-9"></a><!-- para:a5-where-the-softmax-weighted-sum-comes-from-9 --> Assembling the three, with $\tau = \sqrt{d_{\text{head}}}$, reproduces the scaled dot-product attention of Vaswani et al. 2017, Eq. (1), exactly. The next section derives why that particular temperature.

<!-- sec:A.6 -->
### <a id="sec-A.6"></a>A.6 Why the temperature is $\sqrt{d_k}$, in both halves

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-1"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-1 --> Vaswani et al. give this argument in two pieces, and **only the first is derived**. The second — the part that actually says why a large score spread is *harmful* — is an explicit conjecture: "We **suspect** that for large values of $d_k$, the dot products grow large in magnitude, pushing the softmax function into regions where it has extremely small gradients", supported by a citation to someone else's empirical finding that additive attention outperforms unscaled dot-product attention at large $d_k$ <!-- cite:101 --> [[101]](references.md#ref-101). This section derives the first half in full and then supplies the second, which no source in this survey's corpus does.

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-2"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-2 --> **Half one — the score spread grows like $\sqrt{d_k}$.** Assume, as the source's footnote 4 does, that the components of $\mathbf{q}$ and $\mathbf{k}$ are independent random variables with mean $0$ and variance $1$ (the footnote says *independent*, not *identically distributed*; the argument also needs $\mathbf{q}$ independent of $\mathbf{k}$, which the footnote does not state — see <!-- secref:A.9 -->[§A.9](#sec-A.9)). Then term by term, $\mathbb{E}[q_i k_i] = \mathbb{E}[q_i]\mathbb{E}[k_i] = 0$, so the dot product is mean-zero; and $\operatorname{Var}(q_i k_i) = \mathbb{E}[q_i^2 k_i^2] = \mathbb{E}[q_i^2]\mathbb{E}[k_i^2] = 1$. Independence across coordinates makes the variances add:

<a id="eq-11"></a><!-- eq:A-6-1 -->
$$
\operatorname{Var}(\mathbf{q}\cdot\mathbf{k}) \;=\; \sum_{i=1}^{d_k} \operatorname{Var}(q_i k_i) \;=\; d_k, \qquad \text{so } \operatorname{sd}(\mathbf{q}\cdot\mathbf{k}) = \sqrt{d_k}. \tag{11}
$$

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-3"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-3 --> Dividing by $\sqrt{d_k}$ therefore standardizes the score distribution to unit scale independently of head width — in the language of <!-- secref:A.5 -->[§A.5](#sec-A.5), it is the temperature that holds the score spread at $O(1)$ as $d_k$ grows.

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-4"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-4 --> **Half two — why a large spread is harmful.** Differentiate the softmax. With $\mathbf{p} = \operatorname{softmax}(\mathbf{z})$, the $(i,j)$ entry of the Jacobian is $\partial p_i/\partial z_j = p_i(\delta_{ij} - p_j)$, i.e.

<a id="eq-12"></a><!-- eq:A-6-2 -->
$$
\boxed{\;J \;=\; \operatorname{diag}(\mathbf{p}) - \mathbf{p}\mathbf{p}^{\top}\;} \tag{12}
$$

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-5"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-5 --> **This matrix has an identity worth naming**: it is exactly the covariance matrix of the one-hot indicator $Y = \mathbf{e}_I$ of a categorical draw $I \sim \mathbf{p}$. That single observation delivers every property we need for free — $J \succeq 0$ (a covariance matrix is positive semi-definite), $J\mathbf{1} = 0$ (the total probability cannot change), and the total sensitivity is the total variance:

<a id="eq-13"></a><!-- eq:A-6-3 -->
$$
\operatorname{tr}(J) \;=\; \sum_i p_i(1 - p_i) \;=\; 1 - \lVert \mathbf{p} \rVert_2^2 . \tag{13}
$$

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-6"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-6 --> Equation <!-- ref:A-6-3 -->[(13)](#eq-13) is the derivation Vaswani et al. leave as a suspicion, and it is *sharper* than the conjecture: the attention pattern's total sensitivity to its scores is exactly one minus the collision probability of $\mathbf{p}$. It is maximal at the uniform distribution ($1 - 1/n$) and it is **exactly zero** when $\mathbf{p}$ is a point mass. Since $J \succeq 0$, its spectral norm is bounded by its trace, so $\lVert J\rVert_2 \le 1 - \lVert\mathbf{p}\rVert_2^2$ and *no* direction of score perturbation escapes the collapse. Saturation does not merely attenuate the gradient; it annihilates it, and the point mass is precisely the hard lookup we relaxed away from in <!-- secref:A.5 -->[§A.5](#sec-A.5). Scaling is what keeps the relaxation from silently un-relaxing itself.

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-7"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-7 --> **What it costs numerically.** Take $d_k = 64$, the value used throughout Vaswani et al.'s base model ($h = 8$ heads, $d_k = d_v = d_{\text{model}}/h = 64$, $d_{\text{model}} = 512$). The gap between two competing *unscaled* scores is a difference of two such dot products, with standard deviation $\sqrt{2 d_k} \approx 11.3$ — a step that needs the two scores to be **uncorrelated**, which holds, and *not* independent, which fails, since two scores issued from one query share that query. After scaling the gap is $\sqrt{2} \approx 1.41$. Evaluating Equation <!-- ref:A-6-3 -->[(13)](#eq-13) on a two-way competition at each gap gives $\operatorname{tr}(J) = 2.44\times10^{-5}$ unscaled against $0.315$ scaled.

<a id="p-a6-why-the-temperature-is-sqrtd_k-in-both-halves-8"></a><!-- para:a6-why-the-temperature-is-sqrtd_k-in-both-halves-8 --> **That ratio is $1.29\times10^{4}$, and it is a statement about the softmax's own input — not about the gradient reaching the query and key matrices.** Those parameters are reached through one further factor, $\partial z/\partial u = 1/\sqrt{d_k}$, so measured in the raw dot-product basis the ratio is $1.61\times10^{3}$, smaller by exactly $\sqrt{d_k} = 8$. Both are large and the conclusion is identical either way, but they are two different quantities and quoting one for the other is precisely the basis error <!-- secxref:C.5 -->[§C.5](appendix-c-causal-interventions.md#sec-C.5) is written about. Note also that in this two-outcome case $\lVert J\rVert_2 = \operatorname{tr}(J)$ **exactly**, so the bound stated above is tight here rather than merely an upper limit. This is the quantitative content of "extremely small gradients", and it is why the fix is a division rather than a different nonlinearity.

<!-- sec:A.7 -->
### <a id="sec-A.7"></a>A.7 Multi-head attention is a sum, not a concatenation

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-1"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-1 --> Section <!-- secref:A.1 -->[§A.1](#sec-A.1) wrote the residual stream as a sum with one term per head. Vaswani et al. do not write multi-head attention that way — they write $\mathrm{MultiHead} = \mathrm{Concat}(\mathrm{head}_1,\dots,\mathrm{head}_h)W^O$ <!-- cite:101 --> [[101]](references.md#ref-101) — and the step between the two formulations is assumed by every circuits paper without being shown. It is one line of block algebra, and it is load-bearing, so here it is.

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-2"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-2 --> Partition $W^O \in \mathbb{R}^{h d_v \times d}$ by rows into $h$ blocks $W^O_{[i]} \in \mathbb{R}^{d_v \times d}$, matching the concatenation. Block multiplication then gives

<a id="eq-14"></a><!-- eq:A-7-1 -->
$$
\mathrm{Concat}(\mathrm{head}_1,\dots,\mathrm{head}_h)\,W^O \;=\; \begin{bmatrix}\mathrm{head}_1 & \cdots & \mathrm{head}_h\end{bmatrix}\begin{bmatrix}W^O_{[1]} \\ \vdots \\ W^O_{[h]}\end{bmatrix} \;=\; \sum_{i=1}^{h} \mathrm{head}_i\, W^O_{[i]} . \tag{14}
$$

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-3"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-3 --> **The concatenation is presentational; the arithmetic is additive.** Each head owns a disjoint row-block of $W^O$, so each contributes an independent additive term to the stream, and the block $W^O_{[i]}$ is what <!-- secref:A.2 -->[§A.2](#sec-A.2) calls that head's $W_O^h$. This identity — and nothing else — is what licenses treating heads as separable units, which is the premise of per-head ablation, per-head logit attribution, and the entire circuits programme <!-- cite:1 --> [[1]](references.md#ref-1).

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-4"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-4 --> **The low-rank consequence.** Both per-head matrices are products through a $d_{\text{head}}$-dimensional bottleneck: $W_{QK}^h = (W_Q^h)^{\top}W_K^h$ with both factors in $\mathbb{R}^{d_{\text{head}}\times d}$, and $W_{OV}^h = W_O^h W_V^h$ with $W_O^h \in \mathbb{R}^{d \times d_{\text{head}}}$. Since $\operatorname{rank}(AB) \le \min(\operatorname{rank}A, \operatorname{rank}B)$, both are $d\times d$ matrices of rank at most $d_{\text{head}}$. With $d_{\text{head}}/d$ between about 1/10 and 1/100 <!-- cite:1 --> [[1]](references.md#ref-1), each head reads from and writes to a **small subspace of a large stream** — which is the formal version of the informal claim that heads can operate without interfering, and simultaneously the reason they *can* interfere when their subspaces happen to overlap. Composition (<!-- secref:A.3 -->[§A.3](#sec-A.3)) is exactly the case where the overlap is used deliberately.

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-5"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-5 --> **Unpacking the tensor notation.** Elhage et al. write a head as $(A \otimes W_{OV})\cdot x$ <!-- cite:1 --> [[1]](references.md#ref-1), which is compact but opaque on first reading. Under the row-token convention declared at the top of this appendix, with $X \in \mathbb{R}^{n_{\text{ctx}}\times d}$, it means

<a id="eq-15"></a><!-- eq:A-7-2 -->
$$
(A \otimes W_{OV})\cdot X \;=\; A\,X\,W_{OV}^{\top}, \qquad \text{row } i:\ \ \sum_j A_{ij}\,W_{OV}\mathbf{x}_j . \tag{15}
$$

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-6"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-6 --> **What the notation buys, stated carefully.** It is tempting to say that because $A$ multiplies on the *left* (mixing across positions) and $W_{OV}^{\top}$ on the *right* (acting within each position), the two "commute" and are therefore independent. That argument is empty: $(AX)W_{OV}^{\top} = A(XW_{OV}^{\top})$ is plain associativity, true of any conformable triple, and it establishes nothing about this operation in particular. Two real claims survive in its place. **(i) Structural:** the head is a *pure* tensor $A \otimes W_{OV}$ rather than a sum of such terms, so the across-position and within-position actions are genuinely separate factors of one map — that is what the $\otimes$ notation records, and what a sum would destroy. **(ii) Parameter-level:** the pattern is produced by $\{W_Q, W_K\}$ and the movement by $\{W_V, W_O\}$, disjoint parameter sets, so the two can be studied independently *as functions of the weights*.

<a id="p-a7-multi-head-attention-is-a-sum-not-a-concatenation-7"></a><!-- para:a7-multi-head-attention-is-a-sum-not-a-concatenation-7 --> **What does not survive is independence as a property of the forward pass**, because $A$ is itself a function of $X$. Freezing $A$ at its observed values therefore *is* an approximation — the same kind <!-- secref:A.8 -->[§A.8](#sec-A.8) quantifies for the frozen LayerNorm scale, and one this appendix does not quantify. It is what makes attribution graphs tractable (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)) and it leaves the map exactly linear in the *values*, but the pattern's own dependence on the input has been set aside, not shown to be absent.

<!-- sec:A.8 -->
### <a id="sec-A.8"></a>A.8 LayerNorm, and the error term it puts into logit attribution

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-1"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-1 --> Direct logit attribution (<!-- secref:A.1 -->[§A.1](#sec-A.1)) treats the path from a component to the logits as linear. A LayerNorm sits on that path, and it is not linear. The usual treatment is to note the problem and proceed; the source that introduced the survey's most-cited circuit concedes its attribution dot products "are not appropriately scaled" and justifies continuing on the grounds that the correction was complicated and produced similar plots <!-- cite:35 --> [[35]](references.md#ref-35). That is an empirical shrug with no error bound. The structure of LayerNorm supports a better statement.

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-2"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-2 --> **Decompose it.** Write $\mathrm{LN}(\mathbf{x}) = \boldsymbol{\gamma}\odot\frac{\mathbf{x} - \bar{x}\mathbf{1}}{\sigma(\mathbf{x})} + \boldsymbol{\beta}$, and let $P = I - \tfrac{1}{d}\mathbf{1}\mathbf{1}^{\top}$ be the orthogonal projection onto the mean-zero hyperplane. Then $\mathbf{x} - \bar{x}\mathbf{1} = P\mathbf{x}$ exactly, and $\sigma(\mathbf{x}) = \lVert P\mathbf{x}\rVert_2/\sqrt{d}$ under the **biased** ($1/d$, not $1/(d-1)$) variance convention that every transformer implementation uses, so

<a id="eq-16"></a><!-- eq:A-8-1 -->
$$
\mathrm{LN}(\mathbf{x}) \;=\; \boldsymbol{\gamma}\odot\left(\sqrt{d}\;\frac{P\mathbf{x}}{\lVert P\mathbf{x}\rVert_2}\right) + \boldsymbol{\beta}. \tag{16}
$$

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-3"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-3 --> **Everything in Equation <!-- ref:A-8-1 -->[(16)](#eq-16) is linear except one scalar.** The projection $P$ is linear, the diagonal scaling by $\boldsymbol{\gamma}$ is linear, the shift by $\boldsymbol{\beta}$ is affine; the *only* nonlinearity is the reciprocal norm $1/\lVert P\mathbf{x}\rVert_2$, which is a single number per token. So LayerNorm is exactly affine on every level set of $\lVert P\mathbf{x}\rVert_2$ — attribution is exact there, with no approximation whatsoever — and off those sets, the entire error is a scale factor.

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-4"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-4 --> **The error term, to first order.** Freeze the scale at the value observed on the full stream, $s_0 = \lVert P\mathbf{x}_0\rVert_2$, which is what every practical implementation does. Adding a component's contribution $\boldsymbol{\delta}$ to the stream changes the norm to $\lVert P(\mathbf{x}_0 + \boldsymbol{\delta})\rVert_2 = s_0\big(1 + \langle P\mathbf{x}_0, P\boldsymbol{\delta}\rangle/s_0^2 + O(\lVert P\boldsymbol{\delta}\rVert^2/s_0^2)\big)$, so the relative error the frozen-scale attribution makes on that component is

<a id="eq-17"></a><!-- eq:A-8-2 -->
$$
\varepsilon(\boldsymbol{\delta}) \;\simeq\; \frac{\langle P\mathbf{x}_0,\, P\boldsymbol{\delta}\rangle}{\lVert P\mathbf{x}_0\rVert_2^{2}} \;=\; \frac{\lVert P\boldsymbol{\delta}\rVert_2}{\lVert P\mathbf{x}_0\rVert_2}\,\cos\theta, \tag{17}
$$

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-5"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-5 --> with $\theta$ the angle between $P\mathbf{x}_0$ and $P\boldsymbol{\delta}$ — **the two vectors after projection, not the raw write and the raw stream state.** The distinction is not pedantic: a component written entirely along $\mathbf{1}$ has $P\boldsymbol{\delta} = 0$ and therefore zero attribution error at every order, whatever angle it makes with the unprojected stream, because LayerNorm discards that direction before anything downstream sees it. So the exactness test a practitioner should apply is $P\boldsymbol{\delta} \perp P\mathbf{x}_0$, and checking $\boldsymbol{\delta} \perp \mathbf{x}_0$ instead answers a different question.

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-6"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-6 --> **This is a usable statement where the shrug was not.** Direct logit attribution is exact to first order for a component whose *projected* write is orthogonal to the present projected stream direction, and its error grows with both the component's relative projected magnitude and its alignment. A large component pointed along the stream is precisely the case to distrust — and it is also, unhelpfully, the case that most often looks like an important finding.

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-7"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-7 --> **Which normalizer this is about, and where it stops applying.** Everything above is a statement about **LayerNorm** specifically. Many current models (the Llama, Mistral and Gemma families among them) use **RMSNorm**, which omits the mean subtraction entirely — there is no $P$, so the projection step of Equation <!-- ref:A-8-1 -->[(16)](#eq-16) disappears and the error term of Equation <!-- ref:A-8-2 -->[(17)](#eq-17) is taken against $\mathbf{x}_0$ and $\boldsymbol{\delta}$ unprojected. The *shape* of the result is unchanged (an exactly-affine map off one scalar), and that is what makes it worth stating once; the projected-versus-raw distinction this section insists on is a LayerNorm-only complication. A cross-model survey should therefore not apply Equation <!-- ref:A-8-2 -->[(17)](#eq-17) verbatim to an RMSNorm model.

<a id="p-a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-8"></a><!-- para:a8-layernorm-and-the-error-term-it-puts-into-logit-attribution-8 --> **Which architecture the case studies are about.** GPT-2 — the model behind most of the case studies in § <!-- secxref:9 -->[§9](circuits-across-models.md#sec-9) — is **pre-LN**: layer normalization "was moved to the input of each sub-block, similar to a pre-activation residual network[,] and an additional layer normalization was added after the final self-attention block" <!-- cite:102 --> [[102]](references.md#ref-102). Vaswani et al.'s original is post-LN, $\mathrm{LayerNorm}(\mathbf{x} + \mathrm{Sublayer}(\mathbf{x}))$ <!-- cite:101 --> [[101]](references.md#ref-101), and at least one widely-read re-statement of the circuits formalism simplifies to a single terminal LayerNorm. The distinction matters for this appendix specifically: under pre-LN the residual stream itself is never normalized in place, which is what makes the clean additive decomposition of Equation <!-- ref:A-1 -->[(1)](#eq-1) true as written. Under post-LN it is not, and the decomposition holds only between normalizations.

<!-- sec:A.9 -->
### <a id="sec-A.9"></a>A.9 Where these sources argue less than their reputation suggests

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-1"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-1 --> This appendix's sources are foundational and heavily cited, which is exactly why the places they assert rather than argue are worth marking. None of the following is an error; each is a claim carrying less support than its downstream use implies.

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-2"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-2 --> **Vaswani et al. on scaling.** The variance half is derived, in a footnote. The consequential half — that a large score spread hurts learning — is prefaced "We suspect" and backed by a citation to a *different* paper's empirical comparison. <!-- secref:A.6 -->[§A.6](#sec-A.6) supplies the missing argument; until it is supplied, the field's most-repeated architectural justification is a conjecture.

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-3"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-3 --> **Vaswani et al. on multiple heads.** The stated justification is "Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions. With a single attention head, averaging inhibits this." That is an intuition, and this survey does not dress it up as a derivation. In particular the paper says only that the projections are "different, learned linear projections" — it makes **no** claim that heads occupy non-overlapping subspaces, and generically they do not. The honest statement is the rank bound of <!-- secref:A.7 -->[§A.7](#sec-A.7): heads occupy *low-dimensional* subspaces, which makes non-interference easy but not automatic.

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-4"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-4 --> **The independence assumption.** Footnote 4 assumes the components are "independent random variables with mean 0 and variance 1". It does not say *identically distributed*, and the variance computation additionally requires $\mathbf{q}$ to be independent of $\mathbf{k}$ — which is false in a trained model, where queries and keys are computed from a shared residual stream. Equation <!-- ref:A-6-1 -->[(11)](#eq-11) is therefore a statement about an initialization-time null model, not about a trained network. It is still the right null model for choosing a fixed scale factor, but it does not describe the scores a trained head actually produces.

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-5"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-5 --> **The layout convention.** As flagged at the top, the sources split between row-token and column-token conventions. This is not pedantry: transcribing Elhage et al.'s $\mathrm{softmax}(x^{\top}W_{QK}x)$ under a declared row-token shape yields an expression whose factors do not multiply, and that non-conformable form has reached print. Where a formula in the literature seems to disagree with this appendix by a transpose, check the layout before checking the mathematics.

<a id="p-a9-where-these-sources-argue-less-than-their-reputation-suggests-6"></a><!-- para:a9-where-these-sources-argue-less-than-their-reputation-suggests-6 --> **Direct logit attribution.** Every DLA-based claim in this survey inherits the error term of Equation <!-- ref:A-8-2 -->[(17)](#eq-17) — with the alignment measured between the **projected** vectors, and with the caveat that the term is derived for LayerNorm and not for RMSNorm. It is small in the common case and is *not* small for large components aligned with the residual direction, so DLA magnitudes should be read as ranked evidence rather than as calibrated effect sizes — the same distinction <!-- secxref:C.2 -->[§C.2](appendix-c-causal-interventions.md#sec-C.2) draws for attribution patching against exact patching.
