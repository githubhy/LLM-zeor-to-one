<!-- sec:2 -->
## <a id="sec-2"></a>2 Fundamentals

<a id="p-2-fundamentals-1"></a><!-- para:2-fundamentals-1 --> Mechanistic interpretability is not a bag of tricks bolted onto transformers; it rests on a small set
of structural facts about how a transformer computes. This section states those facts and the
intuition behind them; the full linear algebra — virtual weights, the three composition types, the
privileged-basis argument — is derived from first principles in
Appendix <!-- secxref:A -->[§A](appendix-a-transformer-circuits-math.md#sec-A), and the superposition
capacity result in Appendix <!-- secxref:B -->[§B](appendix-b-superposition.md#sec-B).

<!-- sec:2.1 -->
### <a id="sec-2.1"></a>2.1 The residual stream as a linear workspace

<a id="p-21-the-residual-stream-as-a-linear-workspace-1"></a><!-- para:21-the-residual-stream-as-a-linear-workspace-1 --> Write $\mathbf{x}_\ell \in \mathbb{R}^{d}$ for the residual-stream activation at one token position
after layer $\ell$. A decoder-only transformer's forward pass is, at each layer, an **additive**
update:

<a id="eq-1"></a><!-- eq:2-1 -->
$$
\mathbf{x}_\ell = \mathbf{x}_{\ell-1} + \sum_{h=1}^{H}\mathrm{head}^{h}_\ell(\mathbf{x}_{\ell-1}) + \mathrm{MLP}_\ell(\mathbf{x}_{\ell-1}), \qquad \mathbf{x}_0 = W_E\,\mathrm{onehot}(t). \tag{1}
$$

<a id="p-21-the-residual-stream-as-a-linear-workspace-2"></a><!-- para:21-the-residual-stream-as-a-linear-workspace-2 --> Because each component's output is *added* rather than substituted, the residual stream is best read
not as "the activations of layer $\ell$" but as a **communication channel** <!-- cite:1 --> [[1]](references.md#ref-1): the embedding writes
the token into it; every head and every MLP reads a linear projection of the current stream and writes
its result back; the unembedding reads the final state to produce logits,

<a id="eq-2"></a><!-- eq:2-2 -->
$$
\boldsymbol{\ell} = W_U\,\mathbf{x}_L. \tag{2}
$$

<a id="p-21-the-residual-stream-as-a-linear-workspace-3"></a><!-- para:21-the-residual-stream-as-a-linear-workspace-3 --> Two consequences drive everything downstream. **First, the graph is "fully linear-until-nonlinearity."**
Between the point where one component writes and another reads, the only operations are linear, so the
composite map along any path that avoids the attention softmax and MLP nonlinearity is a single matrix
product — a **virtual weight** that is never stored in the parameters but governs the interaction. The
"direct path" from embedding to logits, bypassing every layer, is exactly $W_U W_E$; a single head's
direct contribution to the logits is the virtual weight $W_U W_{OV}^{h} W_E$
(§ <!-- secref:2.2 -->[§2.2](#sec-2.2)). **Second, the stream has no privileged basis.** Rotating the
whole stream by an orthogonal $R$ and every reading/writing matrix accordingly leaves the function
unchanged, so an individual residual coordinate carries no intrinsic meaning; meaning lives in
*directions*, and — crucially — a basis becomes privileged only *after* an elementwise nonlinearity
(a ReLU, or an SAE's activation), which is why the neuron basis of an MLP, not the residual basis, is
where axis-aligned features can even be hoped for (§ <!-- secref:2.3 -->[§2.3](#sec-2.3)).

> <a id="p-21-the-residual-stream-as-a-linear-workspace-4"></a><!-- para:21-the-residual-stream-as-a-linear-workspace-4 --> **Intuition — the stream is a shared bus, not a pipeline.** Think of $\mathbf{x}_\ell$ as a wide
> bus that every module can drop a message onto and every later module can read. Nothing is
> overwritten; "layer 6's output" is really "everything written up to and including layer 6." This is
> why interpretability works *by projection* — to ask what a component did, you project the stream
> onto the direction it wrote, not onto a coordinate axis.

<!-- sec:2.2 -->
### <a id="sec-2.2"></a>2.2 QK and OV circuits

<a id="p-22-qk-and-ov-circuits-1"></a><!-- para:22-qk-and-ov-circuits-1 --> An attention head splits cleanly into two independent linear circuits. With per-head maps
$W_Q^h, W_K^h, W_V^h \in \mathbb{R}^{d_{\text{head}}\times d}$ and $W_O^h \in \mathbb{R}^{d\times d_{\text{head}}}$,
define the **query–key circuit** $W_{QK}^h = (W_Q^h)^\top W_K^h$ and the **output–value circuit**
$W_{OV}^h = W_O^h W_V^h$, both $d\times d$ and both of rank at most $d_{\text{head}} \ll d$. The head's
attention pattern and its write-back are

<a id="eq-3"></a><!-- eq:2-3 -->
$$
A^h_{ij} = \operatorname*{softmax}_{j}\!\left(\frac{\mathbf{x}_i^\top W_{QK}^h\, \mathbf{x}_j}{\sqrt{d_{\text{head}}}}\right), \qquad \mathrm{head}^h(X)_i = \sum_{j} A^h_{ij}\, W_{OV}^h\, \mathbf{x}_j. \tag{3}
$$

<a id="p-22-qk-and-ov-circuits-2"></a><!-- para:22-qk-and-ov-circuits-2 --> The QK circuit alone decides *where* a position attends — it is a bilinear form on *pairs* of stream
states and never sees the content that will be moved. The OV circuit alone decides *what* is written
once a source is attended — a fixed linear map applied to whatever token the pattern selected,
independent of why it was selected. This factorization is the single most useful fact in circuit
analysis: it lets one read a head's "wiring" as two token-by-token tables, the QK bigram table
$W_E^\top W_{QK}^h W_E$ ("does token $a$ attend to token $b$?") and the OV copying table
$W_U W_{OV}^h W_E$ ("if I attend to $b$, which logits does it promote?"), derived in full in
Appendix <!-- secxref:A.2 -->[§A.2](appendix-a-transformer-circuits-math.md#sec-A.2).

<a id="p-22-qk-and-ov-circuits-3"></a><!-- para:22-qk-and-ov-circuits-3 --> Multi-layer behavior arises from **composition**: because a later head reads the residual stream, and
the stream already contains an earlier head's OV write, the later head's effective query, key, or value
is a virtual combination of the raw token and the earlier head's output — **Q-composition**,
**K-composition**, and **V-composition** respectively. Q- and K-composition change *where* the later
head attends (its pattern can now depend on computed features, not just literal tokens); V-composition
changes only *what* it moves. The canonical example is the induction head
(§ <!-- secxref:9.1 -->[§9.1](circuits-across-models.md#sec-9.1)): a previous-token head K-composes with
a later head so the later head can attend "to the token that followed the current token last time,"
implementing the copy rule $[A][B]\dots[A]\!\to\![B]$ <!-- cite:80 --> [[80]](references.md#ref-80).

<!-- sec:2.3 -->
### <a id="sec-2.3"></a>2.3 The linear representation hypothesis

<a id="p-23-the-linear-representation-hypothesis-1"></a><!-- para:23-the-linear-representation-hypothesis-1 --> A **feature** is a direction $\mathbf{d}\in\mathbb{R}^{d}$ (a unit vector) whose presence and magnitude
in the stream corresponds to a human-interpretable property of the input <!-- cite:2 --> [[2]](references.md#ref-2). The **linear
representation hypothesis** (LRH) is the working assumption that a stream activation decomposes,
approximately, as a sparse sum of such feature directions,

<a id="eq-4"></a><!-- eq:2-4 -->
$$
\mathbf{x} \;\approx\; \mathbf{b} + \sum_{i} f_i(\mathbf{x})\, \mathbf{d}_i, \qquad f_i(\mathbf{x}) \ge 0,\ \ \lVert \mathbf{f}(\mathbf{x})\rVert_0 \ll d_{\text{sae}}, \tag{4}
$$

<a id="p-23-the-linear-representation-hypothesis-2"></a><!-- para:23-the-linear-representation-hypothesis-2 --> with only a few features active at a time. The LRH is what makes linear probes, difference-in-means
steering vectors, and sparse-dictionary decomposition (§ <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6))
all coherent: if concepts are directions, they can be read out by a dot product and edited by vector
addition. Its empirical support is strong (curve detectors in vision <!-- cite:2 --> [[2]](references.md#ref-2); steering directions that
reliably move behavior, § <!-- secxref:7.1 -->[§7.1](method-inventory-steering-editing.md#sec-7.1);
world-model probes that become linear once the right frame is chosen, Othello-GPT
§ <!-- secxref:4.1 -->[§4.1](method-inventory-observational.md#sec-4.1) <!-- cite:28 --> [[28]](references.md#ref-28)) but not unqualified:
some computationally load-bearing structure is *irreducibly multi-dimensional*, e.g. the circular
day-of-week and month-of-year representations that a model actually uses to do modular date arithmetic <!-- cite:5 --> [[5]](references.md#ref-5). The honest statement is "linear *subspace*, often one-dimensional, sometimes not."

<!-- sec:2.4 -->
### <a id="sec-2.4"></a>2.4 Superposition

<a id="p-24-superposition-1"></a><!-- para:24-superposition-1 --> If features are directions and a layer is $d$-dimensional, at most $d$ features can be mutually
orthogonal — yet models plainly represent far more concepts than they have neurons. The resolution is
**superposition**: a network stores $m \gg d$ features as *non-orthogonal, nearly-orthogonal*
directions, tolerating a little interference in exchange for capacity, and it can do this precisely
because features are **sparse** (rarely co-active) and a downstream nonlinearity filters the small
cross-talk <!-- cite:3 --> [[3]](references.md#ref-3). Superposition is the mechanistic explanation of **polysemanticity** — a single neuron
fires for several unrelated concepts because it is a coordinate that several feature directions happen
to load onto. It is also the reason the interpretable unit is a *direction found by dictionary
learning*, not a neuron.

<a id="p-24-superposition-2"></a><!-- para:24-superposition-2 --> *Toy Models of Superposition* <!-- cite:3 --> [[3]](references.md#ref-3) makes this precise on a synthetic ReLU-output autoencoder: as feature
sparsity rises past a threshold, the optimal geometry undergoes a **phase transition** from
"orthogonal, drop the unimportant features" (a PCA-like regime) to "pack extra features as antipodal
pairs, then as vertices of regular polytopes" (a uniform-superposition regime governed by the same
mathematics as the physics Thomson problem). The derivation, the feature-dimensionality metric, and the
phase diagram are worked in Appendix <!-- secxref:B -->[§B](appendix-b-superposition.md#sec-B).

> <a id="p-24-superposition-3"></a><!-- para:24-superposition-3 --> **Intuition — an overcomplete dictionary in disguise.** Superposition is compressed sensing run in
> reverse by training: a wide, sparse code (the features) is projected into a narrow channel (the
> residual stream), and the network relies on sparsity + a nonlinearity to keep the projections
> separable — exactly the incoherence-plus-sparsity regime under which an overcomplete dictionary is
> recoverable. This is why the fix for superposition (§ <!-- secxref:6.1 -->[§6.1](method-inventory-dictionary.md#sec-6.1))
> is dictionary learning: a sparse autoencoder learns the overcomplete basis that un-mixes the code.

<a id="p-24-superposition-4"></a><!-- para:24-superposition-4 --> **Concrete anchor.** The existence proof of massive superposition is empirical: a sparse autoencoder
trained on the residual stream of Claude 3 Sonnet extracted on the order of tens of millions of
distinct, interpretable features <!-- cite:8 --> [[8]](references.md#ref-8) from a stream only a few thousand dimensions wide — a ratio of
thousands of features per dimension, only possible because at any token almost all of them are silent.

<!-- sec:2.5 -->
### <a id="sec-2.5"></a>2.5 What counts as an explanation

<a id="p-25-what-counts-as-an-explanation-1"></a><!-- para:25-what-counts-as-an-explanation-1 --> Because MI explanations are causal claims, the survey holds them to two standards throughout, both made
operational in § <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1). **Faithfulness**: an
explanation must reproduce the model's actual computation, not merely produce a plausible-sounding
story — a hypothesized circuit is only as good as the fraction of the behavior it recovers when the rest
of the model is ablated. **Completeness and minimality**: the circuit should contain everything the
behavior uses (no load-bearing component left outside) and nothing it does not. These standards are
harder to meet than they look — network **self-repair** systematically hides how important an ablated
component was <!-- cite:59 --> [[59]](references.md#ref-59), and the headline faithfulness number is *not robust* to how the ablation is done <!-- cite:62 --> [[62]](references.md#ref-62) — which is why the evaluation section is not an afterthought but a load-bearing part of the methodology.
