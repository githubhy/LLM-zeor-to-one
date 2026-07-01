<!-- sec:A -->
## <a id="sec-A"></a>A Transformer-circuits mathematics

<a id="p-a-transformer-circuits-mathematics-1"></a><!-- para:a-transformer-circuits-mathematics-1 --> This appendix derives, from first principles, the residual-stream decomposition, the QK/OV factoring, virtual weights, and the composition types stated in § <!-- secxref:2 -->[§2](fundamentals.md#sec-2).

<!-- sec:A.1 -->
### <a id="sec-A.1"></a>A.1 The residual stream as a sum over paths

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-1"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-1 --> Unrolling the additive update of Equation <!-- ref:2-1 -->[(1)](fundamentals.md#eq-1) from $\mathbf{x}_0 = W_E\,\mathrm{onehot}(t)$ gives the final state as a plain sum of every component's write:

<a id="eq-1"></a><!-- eq:A-1 -->
$$
\mathbf{x}_L = W_E\,\mathrm{onehot}(t) + \sum_{\ell=1}^{L}\sum_{h=1}^{H}\mathrm{head}^{h}_\ell(\mathbf{x}_{\ell-1}) + \sum_{\ell=1}^{L}\mathrm{MLP}_\ell(\mathbf{x}_{\ell-1}). \tag{1}
$$

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-2"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-2 --> Because the unembedding is linear, the logits decompose the same way — a **direct-path** term plus one term per head and per MLP:

<a id="eq-2"></a><!-- eq:A-2 -->
$$
\boldsymbol{\ell} = W_U\,\mathbf{x}_L = \underbrace{W_U W_E\,\mathrm{onehot}(t)}_{\text{direct path (bigram)}} + \sum_{\ell,h} W_U\,\mathrm{head}^{h}_\ell + \sum_{\ell} W_U\,\mathrm{MLP}_\ell. \tag{2}
$$

<a id="p-a1-the-residual-stream-as-a-sum-over-paths-3"></a><!-- para:a1-the-residual-stream-as-a-sum-over-paths-3 --> This is the logit-attribution identity that underlies the "logit lens" (§ <!-- secxref:4.2 -->[§4.2](method-inventory-observational.md#sec-4.2)) and direct-logit-attribution analysis: each component's contribution to any output logit can be read independently because they *add*. The matrices $W_U W_E$, and per head $W_U W_{OV}^h W_E$, are **virtual weights** — products never stored in the parameters but governing the interaction along a path.

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
