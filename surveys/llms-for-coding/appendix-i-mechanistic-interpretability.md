## Mechanistic Interpretability: Reading the Trained Model

<a id="p-mechanistic-interpretability-reading-the-trained-model-1"></a><!-- para:mechanistic-interpretability-reading-the-trained-model-1 --> The anatomy appendices built the machine from first principles — the attention circuits of Appendix A, the fully worked toy of Appendix C, the scale ladder of Appendices D–H. This appendix turns the same rigor the other way: given a *trained* model, how do we read what it computes? Mechanistic interpretability (MI) is the reverse-engineering discipline, and its results are the empirical counterpart to the derivations elsewhere in this series — the hand-built induction head of <!-- secxref:A.9 -->[§A.9](appendix-a-qkv-first-principles.md#sec-A.9) and the solved grokking circuit of <!-- secxref:C.8 -->[§C.8](appendix-c-toy-transformer.md#sec-C.8) are MI in miniature.

<a id="p-mechanistic-interpretability-reading-the-trained-model-2"></a><!-- para:mechanistic-interpretability-reading-the-trained-model-2 --> Two things make this appendix worth its own chapter. First, the appendices so far read the model at the **circuit level** — what a head's weights compute — but a trained network also has a **feature level**: what the *activations* mean, and how thousands of concepts share a few hundred dimensions. Second, MI is where interpretability meets the survey's own subject: what does a model of *code* represent — syntax, scope, types, the running state of the program? The sections below build the feature-level tools (superposition, sparse autoencoders), the causal methodology for finding circuits, the empirical catalog of what has been found (including in code models), the control that understanding buys (steering, editing), and the honest limits of the whole enterprise.

<!-- sec:I.1 -->
### <a id="sec-I.1"></a>I.1 Two Levels: Circuits and Features

<a id="p-i1-two-levels-circuits-and-features-1"></a><!-- para:i1-two-levels-circuits-and-features-1 --> The MI literature reads a transformer at two complementary levels, and separating them dissolves most early confusion.

<a id="p-i1-two-levels-circuits-and-features-2"></a><!-- para:i1-two-levels-circuits-and-features-2 --> The **circuit level** asks what a fixed set of weights computes. This is the level of Appendix A: the query–key map $M=W_Q^{\top}W_K$ of <!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2), the output–value map $W_{OV}=W_O W_V$ of <!-- secxref:A.3 -->[§A.3](appendix-a-qkv-first-principles.md#sec-A.3), and the observation that only these gauge-invariant products are observable (<!-- secxref:A.4 -->[§A.4](appendix-a-qkv-first-principles.md#sec-A.4)). A *circuit* is a subgraph of such components that together implement a behavior — the two-layer induction circuit of <!-- secxref:A.18 -->[§A.18](appendix-a-qkv-first-principles.md#sec-A.18) is the canonical example.

<a id="p-i1-two-levels-circuits-and-features-3"></a><!-- para:i1-two-levels-circuits-and-features-3 --> The **feature level** asks what the *activations* represent. Its organizing conjecture is the **linear representation hypothesis**: a network represents a concept as a *direction* in activation space, and a hidden vector is a sparse sum of the concept-directions active at that position. Writing $\mathbf{d}_i\in\mathbb{R}^d$ for the unit direction of feature $i$ and $f_i(\mathbf{x})\ge 0$ for its activation,

<a id="eq-1"></a><!-- eq:I-1-1 -->
$$
\mathbf{x} \;\approx\; \sum_{i} f_i(\mathbf{x})\,\mathbf{d}_i, \tag{1}
$$

<a id="p-i1-two-levels-circuits-and-features-4"></a><!-- para:i1-two-levels-circuits-and-features-4 --> with only a handful of the $f_i$ nonzero at any one position. Under this hypothesis, interpreting the stream means recovering the dictionary $\{\mathbf{d}_i\}$ and the sparse code $\{f_i\}$ — the problem <!-- secref:I.3 -->[§I.3](#sec-I.3) solves.

<a id="p-i1-two-levels-circuits-and-features-5"></a><!-- para:i1-two-levels-circuits-and-features-5 --> A basis is **privileged** when the architecture gives its coordinate axes a special status — the axes a nonlinearity acts on element-wise, i.e. the neuron directions after a ReLU/GELU. It is **non-privileged** when any rotation is as good as any other — the residual stream itself, which no element-wise nonlinearity reads directly (every sublayer first multiplies by a weight matrix, so a rotation of the stream is absorbed into those matrices, exactly the gauge freedom of <!-- secxref:A.4 -->[§A.4](appendix-a-qkv-first-principles.md#sec-A.4)). The distinction matters because features need not align with neurons: a single neuron can participate in many features and a feature can spread across many neurons — **polysemanticity**, the roadblock the next two sections attack <!-- cite:70 --> [[70]](references.md#ref-70).

<!-- sec:I.2 -->
### <a id="sec-I.2"></a>I.2 Superposition: More Features Than Dimensions

<a id="p-i2-superposition-more-features-than-dimensions-1"></a><!-- para:i2-superposition-more-features-than-dimensions-1 --> The toy of <!-- secxref:C.10 -->[§C.10](appendix-c-toy-transformer.md#sec-C.10) was roomy — width $d=4$ held only $V=3$ tokens, so every token could get its own orthogonal direction. Real models are the opposite: GPT-2 small routes on the order of tens of thousands of distinguishable concepts through a $768$-dimensional stream. When the number of features $m$ exceeds the dimension $d$, they *cannot* all be orthogonal, and the model stores them in **superposition** — an overcomplete set of nearly-orthogonal directions, tolerating a little interference in exchange for representing far more than $d$ things <!-- cite:70 --> [[70]](references.md#ref-70).

<a id="p-i2-superposition-more-features-than-dimensions-2"></a><!-- para:i2-superposition-more-features-than-dimensions-2 --> **The interference cost.** Take the linear-representation picture of Equation <!-- ref:I-1-1 -->[(1)](#eq-1) and read feature $i$ back off the stream with its own direction as the probe, $\hat f_i = \mathbf{d}_i^{\top}\mathbf{x}$. Substituting Equation <!-- ref:I-1-1 -->[(1)](#eq-1),

<a id="eq-2"></a><!-- eq:I-2-1 -->
$$
\hat f_i = \mathbf{d}_i^{\top}\!\sum_j f_j\,\mathbf{d}_j = f_i + \sum_{j\neq i} (\mathbf{d}_i^{\top}\mathbf{d}_j)\,f_j, \tag{2}
$$

<a id="p-i2-superposition-more-features-than-dimensions-3"></a><!-- para:i2-superposition-more-features-than-dimensions-3 --> using $\mathbf{d}_i^{\top}\mathbf{d}_i=1$. The first term is the wanted signal; the sum is **interference** from every other feature that happens to be active, weighted by how non-orthogonal its direction is to $\mathbf{d}_i$. If the $\mathbf{d}_i$ were orthonormal the interference would vanish — but that caps $m$ at $d$. Superposition is the choice to let $m>d$ and pay the sum.

<a id="p-i2-superposition-more-features-than-dimensions-4"></a><!-- para:i2-superposition-more-features-than-dimensions-4 --> **Why sparsity makes the trade worth it.** Model each feature as active independently with probability $p$ and typical squared magnitude $s$, and give the extra features random directions. For random unit vectors in $\mathbb{R}^d$, $\mathbb{E}[\mathbf{d}_i^{\top}\mathbf{d}_j]=0$ and $\mathbb{E}[(\mathbf{d}_i^{\top}\mathbf{d}_j)^2]=1/d$, so the mean-square interference in Equation <!-- ref:I-2-1 -->[(2)](#eq-2) is

<a id="eq-3"></a><!-- eq:I-2-2 -->
$$
\mathbb{E}\big[(\hat f_i - f_i)^2\big] = \sum_{j\neq i}\mathbb{E}[(\mathbf{d}_i^{\top}\mathbf{d}_j)^2]\,\mathbb{E}[f_j^2] \approx \frac{(m-1)}{d}\,p\,s. \tag{3}
$$

<a id="p-i2-superposition-more-features-than-dimensions-5"></a><!-- para:i2-superposition-more-features-than-dimensions-5 --> The interference scales with the **activation density** $p$: when features are sparse ($p\ll 1$) — as natural-language and code features are, most being absent from any given token — the noise is small even for $m\gg d$. Sparsity is what buys superposition: rare features can share the space because they are rarely active *together*.

<a id="p-i2-superposition-more-features-than-dimensions-6"></a><!-- para:i2-superposition-more-features-than-dimensions-6 --> **How many fit.** The capacity is set by how many nearly-orthogonal directions $\mathbb{R}^d$ holds. For a tolerance $\varepsilon$ on pairwise overlap, a random construction places

<a id="eq-4"></a><!-- eq:I-2-3 -->
$$
m \;\sim\; \exp\!\big(c\,\varepsilon^{2} d\big) \quad\text{directions with}\quad \lvert \mathbf{d}_i^{\top}\mathbf{d}_j\rvert \le \varepsilon \ \ (i\neq j), \tag{4}
$$

<a id="p-i2-superposition-more-features-than-dimensions-7"></a><!-- para:i2-superposition-more-features-than-dimensions-7 --> a Johnson–Lindenstrauss–style bound (provable from Gaussian concentration, no appeal to a source needed): the number of "good enough" directions grows *exponentially* in $d$, so a $768$-wide stream can carry vastly more than $768$ sparse features. Whether a feature earns a direction at all is itself governed by sparsity — features must activate sufficiently sparsely for superposition to arise, since otherwise the interference of Equation <!-- ref:I-2-1 -->[(2)](#eq-2) overwhelms the signal <!-- cite:70 --> [[70]](references.md#ref-70).

<a id="p-i2-superposition-more-features-than-dimensions-8"></a><!-- para:i2-superposition-more-features-than-dimensions-8 --> **What it buys.**

- <a id="p-i2-superposition-more-features-than-dimensions-9"></a><!-- para:i2-superposition-more-features-than-dimensions-9 --> A quantitative reason the residual stream is a non-privileged basis (<!-- secref:I.1 -->[§I.1](#sec-I.1)): features live along arbitrary directions, not neuron axes, so a neuron reads a *mixture* of features — polysemanticity is the direct consequence of Equation <!-- ref:I-2-1 -->[(2)](#eq-2).
- The precise sense in which the toy of <!-- secxref:C.10 -->[§C.10](appendix-c-toy-transformer.md#sec-C.10) is unrepresentative: at $d>V$ it never enters superposition, so it never shows the interference that defines real models.
- The problem statement for <!-- secref:I.3 -->[§I.3](#sec-I.3): if features are sparse directions in superposition, recovering them is a sparse dictionary-learning problem.

<a id="p-i2-superposition-more-features-than-dimensions-10"></a><!-- para:i2-superposition-more-features-than-dimensions-10 --> **Intuition.** A lecture hall with $768$ seats can host far more than $768$ occasional visitors, as long as few show up on any given day — assign each a favorite seat, tolerate the rare double-booking, and you host thousands. Superposition is that scheduling trick; sparsity is what keeps the collisions rare; the interference of Equation <!-- ref:I-2-1 -->[(2)](#eq-2) is the occasional double-booking the model has learned to live with.

<!-- sec:I.3 -->
### <a id="sec-I.3"></a>I.3 Sparse Autoencoders: Recovering Monosemantic Features

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-1"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-1 --> If concepts are sparse directions superimposed in the stream (<!-- secref:I.2 -->[§I.2](#sec-I.2)), then reading the model means *un-mixing* them — inverting Equation <!-- ref:I-1-1 -->[(1)](#eq-1) to recover a large dictionary of directions and a sparse code. A **sparse autoencoder (SAE)** does exactly this, and is the workhorse of current feature-level MI <!-- cite:70 --> [[70]](references.md#ref-70).

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-2"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-2 --> **The architecture.** An SAE learns an over-complete dictionary of $m\gg d$ features. It encodes an activation $\mathbf{x}\in\mathbb{R}^d$ into a sparse, non-negative code $\mathbf{f}\in\mathbb{R}^m$ and decodes back:

<a id="eq-5"></a><!-- eq:I-3-1 -->
$$
\mathbf{f} = \mathrm{ReLU}\!\big(W_{\mathrm{enc}}(\mathbf{x}-\mathbf{b}_{\mathrm{dec}}) + \mathbf{b}_{\mathrm{enc}}\big), \qquad \hat{\mathbf{x}} = W_{\mathrm{dec}}\,\mathbf{f} + \mathbf{b}_{\mathrm{dec}}. \tag{5}
$$

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-3"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-3 --> The columns of $W_{\mathrm{dec}}\in\mathbb{R}^{d\times m}$ are the recovered feature directions $\mathbf{d}_i$ of Equation <!-- ref:I-1-1 -->[(1)](#eq-1); the code entry $f_i$ is feature $i$'s activation. Reconstruction alone is trivial when $m\ge d$ (the identity would do), so the whole content is in forcing $\mathbf{f}$ to be sparse.

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-4"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-4 --> **The objective.** Train on the model's own activations to reconstruct while paying for every active feature:

<a id="eq-6"></a><!-- eq:I-3-2 -->
$$
\mathcal{L}(\mathbf{x}) = \lVert \mathbf{x} - \hat{\mathbf{x}} \rVert_2^2 + \lambda \sum_{i} \lvert f_i \rvert, \tag{6}
$$

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-5"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-5 --> where the $L_1$ term $\lambda\lVert\mathbf{f}\rVert_1$ is a convex surrogate for the thing actually wanted — a small $L_0$, the *count* of active features — which is non-differentiable. Minimizing Equation <!-- ref:I-3-2 -->[(6)](#eq-6) pushes most $f_i$ to exactly zero, so each input is explained by a few interpretable, near-monosemantic features.

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-6"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-6 --> **The shrinkage bias, derived.** The $L_1$ surrogate has a cost. Freeze the dictionary and ask what magnitude a single feature should take: minimize $\tfrac12(f-a)^2 + \lambda f$ over $f\ge 0$, where $a$ is the "true" projection. Setting the derivative to zero gives $f = a-\lambda$, clipped at zero — the **soft-threshold**

<a id="eq-7"></a><!-- eq:I-3-3 -->
$$
f^\star = \mathrm{ReLU}(a-\lambda) = \max(0,\,a-\lambda). \tag{7}
$$

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-7"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-7 --> Every recovered activation is biased *downward* by $\lambda$: the same penalty that zeroes out noise also systematically **shrinks** the features that survive. This is the central defect of the vanilla SAE, and the next-generation variants each target it.

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-8"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-8 --> **Removing the bias.** Three fixes, all recovering the same lesson — decouple *which* features fire from *how much*:

- <a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-9"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-9 --> **Gated SAE** <!-- cite:72 --> [[72]](references.md#ref-72): split the encoder into a *gate* that decides which features are active (and carries the $L_1$ penalty) and a *magnitude* path that is not penalized, so the $L_1$ shrinkage no longer touches the estimated sizes. It resolves shrinkage and reaches a given reconstruction with about half as many active features.
- **Top-$k$ SAE** <!-- cite:71 --> [[71]](references.md#ref-71): drop $L_1$ entirely and keep only the $k$ largest pre-activations, $\mathbf{f}=\mathrm{TopK}(W_{\mathrm{enc}}(\mathbf{x}-\mathbf{b}_{\mathrm{dec}}))$, which fixes $L_0=k$ exactly and removes the magnitude penalty (hence the shrinkage) by construction.
- **JumpReLU SAE** <!-- cite:73 --> [[73]](references.md#ref-73): replace the ReLU with a thresholded jump $\mathrm{JumpReLU}_\theta(z)=z\,\mathbb{1}[z>\theta]$, which passes a feature at full magnitude once it clears the learned threshold $\theta$ (no shrinkage above threshold). Because the jump is discontinuous, the sparsity $L_0$ is trained directly through a straight-through estimator rather than through the $L_1$ proxy.

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-10"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-10 --> **Evaluating an SAE.** Two axes trade off — fidelity and sparsity. Fidelity is measured by **loss recovered**: splice the reconstruction $\hat{\mathbf{x}}$ back into the model in place of $\mathbf{x}$ and see how much of the model's performance survives,

<a id="eq-8"></a><!-- eq:I-3-4 -->
$$
\text{loss recovered} = 1 - \frac{\mathcal{L}_{\mathrm{CE}}(\hat{\mathbf{x}}) - \mathcal{L}_{\mathrm{CE}}(\mathbf{x})}{\mathcal{L}_{\mathrm{CE}}(\text{ablate } \mathbf{x}) - \mathcal{L}_{\mathrm{CE}}(\mathbf{x})}, \tag{8}
$$

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-11"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-11 --> so $1$ means the SAE lost nothing and $0$ means it was no better than deleting the activation; sparsity is the average $L_0$. A newer SAE dominates when it reaches the same loss-recovered at lower $L_0$ — the Pareto frontier the gated, top-$k$, and JumpReLU variants push out <!-- cite:71 --> [[71]](references.md#ref-71), <!-- cite:73 --> [[73]](references.md#ref-73).

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-12"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-12 --> **What it buys.**

- <a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-13"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-13 --> A *scalable, unsupervised* decomposition of the stream into monosemantic features — the direct answer to the polysemanticity of <!-- secref:I.1 -->[§I.1](#sec-I.1) and the superposition of <!-- secref:I.2 -->[§I.2](#sec-I.2), and the substrate the steering of <!-- secref:I.8 -->[§I.8](#sec-I.8) acts on.
- Features precise enough to pin the components *causally* responsible for a behavior more finely than a neuron- or head-level decomposition <!-- cite:70 --> [[70]](references.md#ref-70).

<a id="p-i3-sparse-autoencoders-recovering-monosemantic-features-14"></a><!-- para:i3-sparse-autoencoders-recovering-monosemantic-features-14 --> **Intuition.** The residual stream is a chord — many notes struck at once and summed into one waveform. An SAE is the ear that hears the individual notes: the dictionary $W_{\mathrm{dec}}$ is the set of pitches it knows, the sparse code $\mathbf{f}$ is which few are sounding now, and the sparsity penalty is the prior that music is made of a few notes at a time, not all of them.

<!-- sec:I.4 -->
### <a id="sec-I.4"></a>I.4 The Intervention Toolkit: Finding Circuits Causally

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-1"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-1 --> Reading a feature (<!-- secref:I.3 -->[§I.3](#sec-I.3)) says what is represented; it does not say what is *used*. Establishing that a component **causes** a behavior needs intervention, not correlation — the discipline that separates a circuit claim from a just-so story. The induction ablation of <!-- secxref:A.22 -->[§A.22](appendix-a-qkv-first-principles.md#sec-A.22) is the simplest instance; this section is the full toolkit.

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-2"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-2 --> **Ablation (necessity).** Delete a component — replace its output with zero, the dataset mean, or a resampled value — and measure the damage to a metric $m$. A large drop shows the component was *necessary*. Resample (or mean) ablation is preferred over zero: zeroing pushes the network off its activation manifold and over-states importance.

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-3"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-3 --> **Activation patching (sufficiency).** The sharper test runs the model twice — a **clean** input and a minimally different **corrupted** one — and transplants one activation from the clean run into the corrupted run, measuring how much of the metric is restored:

<a id="eq-9"></a><!-- eq:I-4-1 -->
$$
\Delta_{\mathrm{patch}}(\ell) = m\big(\mathbf{x}_{\mathrm{corr}} \,\big|\, \mathbf{h}_\ell \leftarrow \mathbf{h}_\ell^{\mathrm{clean}}\big) - m(\mathbf{x}_{\mathrm{corr}}). \tag{9}
$$

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-4"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-4 --> A site $\ell$ whose patch restores the clean behavior is *sufficient* to carry the information the corruption removed. This is **causal tracing**, which localized factual recall in GPT to a band of mid-layer feed-forward sublayers <!-- cite:74 --> [[74]](references.md#ref-74). **Path patching** refines Equation <!-- ref:I-4-1 -->[(9)](#eq-9) to a single edge — patch the contribution that flows from sender component $A$ *directly* into receiver $B$, holding all other paths at their corrupted values — which is what distinguishes a head's direct effect on the logits from its effect mediated by later heads <!-- cite:75 --> [[75]](references.md#ref-75).

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-5"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-5 --> **Attribution patching (a cheap linear approximation).** Patching every site is $O(\text{components})$ forward passes. A first-order Taylor expansion of the metric around the corrupted activation replaces them with a *single* backward pass:

<a id="eq-10"></a><!-- eq:I-4-2 -->
$$
\Delta_{\mathrm{patch}}(\ell) \approx \big(\mathbf{h}_\ell^{\mathrm{clean}} - \mathbf{h}_\ell^{\mathrm{corr}}\big)^{\top} \left.\frac{\partial m}{\partial \mathbf{h}_\ell}\right|_{\mathbf{h}_\ell^{\mathrm{corr}}}, \tag{10}
$$

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-6"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-6 --> the gradient-times-difference score that makes whole-model circuit attribution tractable, exact to first order and to be checked against true patching where it matters.

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-7"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-7 --> **The lens family (reading intermediate states).** Because every layer writes to the same residual stream (<!-- secxref:A.15 -->[§A.15](appendix-a-qkv-first-principles.md#sec-A.15)), an intermediate state $\mathbf{h}_\ell$ can be pushed through the *final* unembedding to read the model's provisional guess — the **logit lens**:

<a id="eq-11"></a><!-- eq:I-4-3 -->
$$
\hat{\mathbf{p}}_\ell = \mathrm{softmax}\big(W_U\,\mathrm{LN}(\mathbf{h}_\ell)\big). \tag{11}
$$

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-8"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-8 --> The logit lens is biased because $\mathbf{h}_\ell$ is not in the same basis the final layer expects; the **tuned lens** fixes this with a per-layer learned affine map $(A_\ell,\mathbf{b}_\ell)$ trained so the read-out matches the model's true final distribution <!-- cite:76 --> [[76]](references.md#ref-76):

<a id="eq-12"></a><!-- eq:I-4-4 -->
$$
\hat{\mathbf{p}}_\ell = \mathrm{softmax}\big(W_U\,\mathrm{LN}(A_\ell \mathbf{h}_\ell + \mathbf{b}_\ell)\big). \tag{12}
$$

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-9"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-9 --> Equation <!-- ref:I-4-3 -->[(11)](#eq-11) is the empirical face of <!-- secxref:A.21 -->[§A.21](appendix-a-qkv-first-principles.md#sec-A.21): a component's write is read by projecting the stream through $W_U$ — direct logit attribution and the logit lens are the same operation, applied to a head's output and to a layer's state respectively.

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-10"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-10 --> **Automation, and distributed variables.** Iterating path patching and pruning every edge below an effect threshold **automates** circuit discovery, recovering known circuits without hand-guidance <!-- cite:77 --> [[77]](references.md#ref-77). And when a causal variable is not axis-aligned — spread across neurons in superposition — **distributed alignment search** finds the variable by learning the rotation that aligns a subspace of the activations with a high-level causal variable via gradient descent, then intervening in that learned basis <!-- cite:78 --> [[78]](references.md#ref-78).

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-11"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-11 --> **What it buys.**

- <a id="p-i4-the-intervention-toolkit-finding-circuits-causally-12"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-12 --> A causal, not correlational, definition of a circuit: Equation <!-- ref:I-4-1 -->[(9)](#eq-9) turns "this looks important" into a measured counterfactual, the standard the induction result of <!-- secxref:A.22 -->[§A.22](appendix-a-qkv-first-principles.md#sec-A.22) already meets.
- A cost ladder — exact patching, cheap attribution (Equation <!-- ref:I-4-2 -->[(10)](#eq-10)), then automation — that scales interpretability from single heads to whole-model circuit graphs.

<a id="p-i4-the-intervention-toolkit-finding-circuits-causally-13"></a><!-- para:i4-the-intervention-toolkit-finding-circuits-causally-13 --> **Intuition.** To prove a wire matters in a circuit board you do not stare at it; you cut it and see what breaks (ablation), or you splice in a known-good signal and see what heals (patching). The lens is a multimeter you touch to an intermediate node to read the voltage the final output *would* see; attribution patching is the linearized estimate of every cut at once, from a single measurement.

<!-- sec:I.5 -->
### <a id="sec-I.5"></a>I.5 A Discovered Circuit: Reverse-Engineering a Real Model

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-1"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-1 --> Appendix A *built* an induction head and Appendix C *derived* grokking; neither reverse-engineered a behavior a model learned on its own. The **indirect object identification (IOI)** circuit in GPT-2 small is the canonical worked example of the latter — the largest end-to-end reverse-engineering of a natural behavior "in the wild" <!-- cite:75 --> [[75]](references.md#ref-75).

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-2"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-2 --> **The task and metric.** In *"When Mary and John went to the store, John gave a drink to ___"* the model must complete the **indirect object** (IO $=$ Mary) rather than repeat the **subject** (S $=$ John). The natural metric is the logit difference,

<a id="eq-13"></a><!-- eq:I-5-1 -->
$$
m_{\mathrm{IOI}} = \mathrm{logit}(\text{IO}) - \mathrm{logit}(\text{S}), \tag{13}
$$

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-3"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-3 --> which cleanly isolates the one decision the task turns on and gives patching (Equation <!-- ref:I-4-1 -->[(9)](#eq-9)) a scalar to move.

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-4"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-4 --> **The discovered mechanism.** Causal interventions revealed a circuit of **26 attention heads in 7 classes** that compute Equation <!-- ref:I-5-1 -->[(13)](#eq-13) as a three-step algorithm <!-- cite:75 --> [[75]](references.md#ref-75): (i) **duplicate-token** and **induction** heads detect that "John" has occurred twice; (ii) **S-inhibition** heads write a signal that says *do not attend to the duplicated subject*; (iii) **name-mover** heads, reading that signal, attend to the remaining name "Mary" and copy it to the output — a copying operation of exactly the positive-OV-eigenvalue kind read off a head in <!-- secxref:A.8 -->[§A.8](appendix-a-qkv-first-principles.md#sec-A.8). (There are also **backup** name-movers that take over if the primary ones are ablated, and **negative** name-movers that subtract — the copy-suppression of <!-- secref:I.6 -->[§I.6](#sec-I.6).)

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-5"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-5 --> **Was the circuit really found?** The explanation is held to three quantitative tests <!-- cite:75 --> [[75]](references.md#ref-75). **Faithfulness** asks how much of the full behavior the circuit alone reproduces,

<a id="eq-14"></a><!-- eq:I-5-2 -->
$$
\text{faithfulness} = \frac{m_{\mathrm{IOI}}(\text{circuit only})}{m_{\mathrm{IOI}}(\text{full model})}, \tag{14}
$$

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-6"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-6 --> **completeness** asks that no important node was missed, and **minimality** that no included node is redundant. The three together are what upgrade a suggestive diagram to a claim — and, honestly reported, they also flag where the account is still incomplete.

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-7"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-7 --> **Other solved circuits.** The same method reverse-engineered how GPT-2 computes *greater-than* — predicting a year-ending larger than the one given, implemented by mid-layer feed-forward sublayers feeding attention that carries the comparison <!-- cite:80 --> [[80]](references.md#ref-80) — and, run automatically, edge-pruning recovers such circuits without hand-guidance <!-- cite:77 --> [[77]](references.md#ref-77).

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-8"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-8 --> **What it buys.**

- <a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-9"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-9 --> Existence proof that a *natural* behavior in a real model decomposes into nameable, testable components — the empirical payoff of the circuit language built abstractly in Appendix A.
- A template — task, clean/corrupt pair, scalar metric, path patching, faithfulness/completeness/minimality — reusable for any behavior, including the code-specific circuits of <!-- secref:I.7 -->[§I.7](#sec-I.7).

<a id="p-i5-a-discovered-circuit-reverse-engineering-a-real-model-10"></a><!-- para:i5-a-discovered-circuit-reverse-engineering-a-real-model-10 --> **Intuition.** IOI is the "grammar of not repeating yourself" wired into silicon: one group of heads notices the repeated name, another posts a *don't-look-here* sticky note over it, and a third reads the note and copies whatever name is left. Every step was found by cutting and splicing, not by inspection.

<!-- sec:I.6 -->
### <a id="sec-I.6"></a>I.6 The Attention-Head Zoo

<a id="p-i6-the-attention-head-zoo-1"></a><!-- para:i6-the-attention-head-zoo-1 --> The induction head of <!-- secxref:A.9 -->[§A.9](appendix-a-qkv-first-principles.md#sec-A.9) is one species in a catalog of **recurring, interpretable** head types that appear across models. Each is read with the same $M=W_Q^{\top}W_K$ (where it attends) and $W_{OV}=W_O W_V$ (what it writes) language of <!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2)–<!-- secxref:A.3 -->[§A.3](appendix-a-qkv-first-principles.md#sec-A.3).

- <a id="p-i6-the-attention-head-zoo-2"></a><!-- para:i6-the-attention-head-zoo-2 --> **Previous-token heads** — QK attends from position $t$ to $t-1$; they write the previous token's identity into the stream and are the first half of the two-layer induction circuit of <!-- secxref:A.18 -->[§A.18](appendix-a-qkv-first-principles.md#sec-A.18).
- **Duplicate-token heads** — QK attends from a token to an earlier copy of *itself*; they flag repetition (the trigger the IOI circuit of <!-- secref:I.5 -->[§I.5](#sec-I.5) reads).
- **Induction heads** — attend to the token *after* a previous copy and copy it forward; the in-context-learning workhorse of <!-- secxref:A.22 -->[§A.22](appendix-a-qkv-first-principles.md#sec-A.22) <!-- cite:79 --> [[79]](references.md#ref-79).
- **Name-mover heads** — a copying OV (positive eigenvalues, <!-- secxref:A.8 -->[§A.8](appendix-a-qkv-first-principles.md#sec-A.8)) that moves an attended token to the output; the final stage of IOI <!-- cite:75 --> [[75]](references.md#ref-75).
- **Successor heads** — map an ordinal token to its successor ("one"$\to$"two", "Monday"$\to$"Tuesday"), a single interpretable direction on which the OV acts as an increment <!-- cite:81 --> [[81]](references.md#ref-81):

<a id="eq-15"></a><!-- eq:I-6-1 -->
$$
W_{OV}\,\mathbf{v}_{\mathrm{ord}}(n) \approx \mathbf{v}_{\mathrm{ord}}(n+1), \tag{15}
$$

<a id="p-i6-the-attention-head-zoo-3"></a><!-- para:i6-the-attention-head-zoo-3 --> where $\mathbf{v}_{\mathrm{ord}}(n)$ is the shared "ordinal-$n$" feature direction.

- <a id="p-i6-the-attention-head-zoo-4"></a><!-- para:i6-the-attention-head-zoo-4 --> **Copy-suppression (negative name-mover) heads** — the mirror of copying: they attend to a token the model is about to over-predict and write *against* it, subtracting its unembedding from the logits <!-- cite:82 --> [[82]](references.md#ref-82):

<a id="eq-16"></a><!-- eq:I-6-2 -->
$$
\Delta\boldsymbol{\ell} \;\propto\; -\,\mathbf{u}_{t^\star}, \qquad t^\star = \text{the attended (soon-to-be-copied) token}, \tag{16}
$$

<a id="p-i6-the-attention-head-zoo-5"></a><!-- para:i6-the-attention-head-zoo-5 --> with $\mathbf{u}_{t^\star}$ that token's unembedding row — a calibration mechanism that damps the model's own over-confident copying.

<a id="p-i6-the-attention-head-zoo-6"></a><!-- para:i6-the-attention-head-zoo-6 --> **What it buys.**

- <a id="p-i6-the-attention-head-zoo-7"></a><!-- para:i6-the-attention-head-zoo-7 --> A vocabulary of parts: complex behaviors (IOI, greater-than) are compositions of a small zoo of reusable heads, so reverse-engineering becomes recognition rather than derivation from scratch.
- Evidence for **universality** — the same head types recur across architectures and scales, so the toy circuits of Appendix A are not idiosyncratic but instances of what real models reliably grow.

<a id="p-i6-the-attention-head-zoo-8"></a><!-- para:i6-the-attention-head-zoo-8 --> **Intuition.** Heads specialize like enzymes: each recognizes one structural motif (a repeat, a previous token, an ordinal, an over-copied name) and catalyzes one edit to the stream. The zoo is the parts list; a circuit (<!-- secref:I.5 -->[§I.5](#sec-I.5)) is the assembly.

<!-- sec:I.7 -->
### <a id="sec-I.7"></a>I.7 What Code Models Represent

<a id="p-i7-what-code-models-represent-1"></a><!-- para:i7-what-code-models-represent-1 --> The tools so far are domain-general; the survey's subject is not. A model of *code* is a natural probe target because code has ground-truth structure — a syntax tree, a scope, a type, and a precise **execution semantics** — so we can ask, sharply, whether the activations track it.

<a id="p-i7-what-code-models-represent-2"></a><!-- para:i7-what-code-models-represent-2 --> **The probing method.** Train a small classifier $g_\phi$ (usually linear, to test *linear* decodability) on a frozen hidden state $\mathbf{h}_\ell$ to predict a code property $y$ — an AST node type, an identifier's scope, a variable's value:

<a id="eq-17"></a><!-- eq:I-7-1 -->
$$
\hat y = g_\phi(\mathbf{h}_\ell), \qquad \mathrm{acc} = \Pr_{(\mathbf{h},y)}\!\big[\,g_\phi(\mathbf{h}) = y\,\big]. \tag{17}
$$

<a id="p-i7-what-code-models-represent-3"></a><!-- para:i7-what-code-models-represent-3 --> High accuracy means the property is *present and decodable* in the stream. But a probe can succeed simply because it is powerful, so the honest measure is **selectivity** against a control task with random labels — decodability the model actually organized, not the probe memorized:

<a id="eq-18"></a><!-- eq:I-7-2 -->
$$
\mathrm{selectivity} = \mathrm{acc}_{\mathrm{task}} - \mathrm{acc}_{\mathrm{control}}. \tag{18}
$$

<a id="p-i7-what-code-models-represent-4"></a><!-- para:i7-what-code-models-represent-4 --> **Syntax and identifiers are there.** Under this method, pretrained code models demonstrably encode syntactic structure, the notion of identifiers, and namespaces — though they can fail on deeper properties such as semantic equivalence <!-- cite:86 --> [[86]](references.md#ref-86); structural analyses find the attention patterns and hidden states carry syntax-tree (AST) motifs <!-- cite:87 --> [[87]](references.md#ref-87).

<a id="p-i7-what-code-models-represent-5"></a><!-- para:i7-what-code-models-represent-5 --> **Execution state — a world model.** The stronger claim is that a sequence model builds a *world model* of the process it predicts, not just its surface form. A transformer trained only to predict legal Othello moves develops an emergent internal representation of the **board state** — decodable by a probe, and one whose *intervention* steers the model's move predictions as the rules dictate, a causal world model rather than a correlational one <!-- cite:83 --> [[83]](references.md#ref-83):

<a id="eq-19"></a><!-- eq:I-7-3 -->
$$
\mathrm{do}\big(\text{decoded state} = s'\big) \ \Rightarrow\ \text{model's next-move distribution follows } s', \tag{19}
$$

<a id="p-i7-what-code-models-represent-6"></a><!-- para:i7-what-code-models-represent-6 --> and the world state turns out to be represented **linearly** once read in the right (relative "mine vs. theirs") coordinates <!-- cite:84 --> [[84]](references.md#ref-84). The result transfers to code: a language model trained on programs in a grid-world DSL develops an increasingly accurate representation of the **intermediate program state** — the semantics the program will produce when executed — over the course of training, established with an *interventional* baseline that disentangles what the model represents from what the probe learns <!-- cite:85 --> [[85]](references.md#ref-85). This is the code-modality analog of Equation <!-- ref:I-7-3 -->[(19)](#eq-19): the model of code carries a trace of execution, not merely token statistics.

<a id="p-i7-what-code-models-represent-7"></a><!-- para:i7-what-code-models-represent-7 --> **Code-specific circuits.** At the circuit level, the induction head of <!-- secxref:A.22 -->[§A.22](appendix-a-qkv-first-principles.md#sec-A.22) is the mechanism behind copying an identifier from earlier in a file or from retrieved repository context — the survey's own repetition-heavy setting — and duplicate-token and previous-token heads (<!-- secref:I.6 -->[§I.6](#sec-I.6)) are the natural substrate for bracket matching and variable tracking. The IOI template of <!-- secref:I.5 -->[§I.5](#sec-I.5) — task, clean/corrupt pair, scalar metric, path patching — is directly reusable to reverse-engineer them.

<a id="p-i7-what-code-models-represent-8"></a><!-- para:i7-what-code-models-represent-8 --> **What it buys.**

- <a id="p-i7-what-code-models-represent-9"></a><!-- para:i7-what-code-models-represent-9 --> Evidence that a code model's competence rests on structured internal representations — syntax, scope, and even execution state — rather than surface $n$-gram statistics, which bears on generalization, hallucinated APIs, and where the model will break.
- A concrete research program for the survey's domain: probe for program state, then reverse-engineer the circuits that compute it, with the general tools of <!-- secref:I.4 -->[§I.4](#sec-I.4)–<!-- secref:I.6 -->[§I.6](#sec-I.6).

<a id="p-i7-what-code-models-represent-10"></a><!-- para:i7-what-code-models-represent-10 --> **Intuition.** A model that only memorized token co-occurrences would be a phrasebook; a model that represents the running program state is closer to an interpreter that has read ahead. The probing-plus-intervention method is how we tell the phrasebook from the interpreter — and code, with its exact semantics, is where the test is cleanest.

<!-- sec:I.8 -->
### <a id="sec-I.8"></a>I.8 The Payoff: Steering, Editing, and Auditing

<a id="p-i8-the-payoff-steering-editing-and-auditing-1"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-1 --> Interpretability earns its keep when reading the model becomes *controlling* it. Three levers follow directly from the feature and circuit pictures above.

<a id="p-i8-the-payoff-steering-editing-and-auditing-2"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-2 --> **Steering (edit the activations).** If a concept is a direction $\mathbf{v}$ (a feature from an SAE of <!-- secref:I.3 -->[§I.3](#sec-I.3), or a difference-of-means "reading vector" between contrasting prompts), then adding it to the residual stream at inference pushes the model along that concept:

<a id="eq-20"></a><!-- eq:I-8-1 -->
$$
\mathbf{h}_\ell \leftarrow \mathbf{h}_\ell + \alpha\,\mathbf{v}, \tag{20}
$$

<a id="p-i8-the-payoff-steering-editing-and-auditing-3"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-3 --> with strength $\alpha$. Activation steering / activation engineering demonstrates behavioral control from such additions at essentially no training cost <!-- cite:88 --> [[88]](references.md#ref-88), and **representation engineering** turns the reading and controlling of these directions into a systematic top-down method for transparency and control <!-- cite:89 --> [[89]](references.md#ref-89). Equation <!-- ref:I-8-1 -->[(20)](#eq-20) is the linear-representation hypothesis (Equation <!-- ref:I-1-1 -->[(1)](#eq-1)) used *generatively*.

<a id="p-i8-the-payoff-steering-editing-and-auditing-4"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-4 --> **Editing (edit the weights).** To change a stored fact rather than a runtime activation, edit the weights. Viewing a feed-forward layer as the key–value memory of <!-- secxref:A.6 -->[§A.6](appendix-a-qkv-first-principles.md#sec-A.6)/<!-- secxref:C.2 -->[§C.2](appendix-c-toy-transformer.md#sec-C.2), inserting the association $\mathbf{k}_*\!\to\!\mathbf{v}_*$ with minimal disturbance (under the key covariance $C=KK^{\top}$) has the rank-one closed form

<a id="eq-21"></a><!-- eq:I-8-2 -->
$$
W' = W + \frac{(\mathbf{v}_* - W\mathbf{k}_*)\,(C^{-1}\mathbf{k}_*)^{\top}}{\mathbf{k}_*^{\top} C^{-1}\mathbf{k}_*}, \tag{21}
$$

<a id="p-i8-the-payoff-steering-editing-and-auditing-5"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-5 --> which is exactly the ROME edit, localized to the mid-layer sublayer that causal tracing (<!-- secref:I.4 -->[§I.4](#sec-I.4)) identified as storing the fact <!-- cite:74 --> [[74]](references.md#ref-74). Editing *many* facts at once generalizes Equation <!-- ref:I-8-2 -->[(21)](#eq-21) to a regularized least-squares update spread over several layers,

<a id="eq-22"></a><!-- eq:I-8-3 -->
$$
\Delta = R\,K^{\top}\big(C + K K^{\top}\big)^{-1}, \qquad K = [\mathbf{k}_1\cdots\mathbf{k}_n],\ \ R = [\mathbf{r}_1\cdots\mathbf{r}_n], \tag{22}
$$

<a id="p-i8-the-payoff-steering-editing-and-auditing-6"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-6 --> with residuals $\mathbf{r}_i=\mathbf{v}_i-W\mathbf{k}_i$ — the MEMIT update, which scales to thousands of edits at once <!-- cite:90 --> [[90]](references.md#ref-90).

<a id="p-i8-the-payoff-steering-editing-and-auditing-7"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-7 --> **Auditing (use it for safety).** The same causal tooling that finds a circuit can *audit* a model: localize and read the features a model uses, to detect deception, backdoors, or unwanted capabilities that behavioral testing alone would miss. This is the bridge from these appendices to the survey's safety discussion — interpretability as an assurance method, not only an explanatory one.

<a id="p-i8-the-payoff-steering-editing-and-auditing-8"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-8 --> **What it buys.**

- <a id="p-i8-the-payoff-steering-editing-and-auditing-9"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-9 --> A control surface: the features of <!-- secref:I.3 -->[§I.3](#sec-I.3) and circuits of <!-- secref:I.5 -->[§I.5](#sec-I.5) are not just explanatory — they are *actuators* (Equations <!-- ref:I-8-1 -->[(20)](#eq-20)–<!-- ref:I-8-3 -->[(22)](#eq-22)) for steering behavior and editing knowledge.
- A safety rationale for MI: reading the mechanism is a route to catching failures that input–output evaluation cannot.

<a id="p-i8-the-payoff-steering-editing-and-auditing-10"></a><!-- para:i8-the-payoff-steering-editing-and-auditing-10 --> **Intuition.** Once you know which wire carries which signal, you can not only explain the circuit but also splice it — nudge a runtime signal (steering), re-solder a stored value (editing), or tap a line to check for a hidden one (auditing). Understanding and control are the same knowledge used in two directions.

<!-- sec:I.9 -->
### <a id="sec-I.9"></a>I.9 Limits and Epistemics

<a id="p-i9-limits-and-epistemics-1"></a><!-- para:i9-limits-and-epistemics-1 --> MI is powerful and young, and its claims fail in characteristic ways. An honest appendix names them.

<a id="p-i9-limits-and-epistemics-2"></a><!-- para:i9-limits-and-epistemics-2 --> **Probes read; they do not prove use.** A direction can be decodable (Equation <!-- ref:I-7-1 -->[(17)](#eq-17)) without the model *using* it — high probe accuracy is necessary, not sufficient, for a causal claim. This is why selectivity (Equation <!-- ref:I-7-2 -->[(18)](#eq-18)) and, better, *intervention* (Equation <!-- ref:I-7-3 -->[(19)](#eq-19)) are required; the interventional baseline of the code-semantics result of <!-- secref:I.7 -->[§I.7](#sec-I.7) exists precisely to close this gap.

<a id="p-i9-limits-and-epistemics-3"></a><!-- para:i9-limits-and-epistemics-3 --> **Interpretability illusions.** A direction that appears to mean one thing on one dataset can mean something else on another; the same neuron or direction admits inconsistent "explanations" depending on the data it is examined over <!-- cite:91 --> [[91]](references.md#ref-91). Analogous illusions afflict activation patching when the corrupted distribution is chosen carelessly. The lesson is that an interpretation is a hypothesis about the model's *global* computation, not a caption for one example set.

<a id="p-i9-limits-and-epistemics-4"></a><!-- para:i9-limits-and-epistemics-4 --> **Ablation is not clean necessity.** Real models exhibit *self-repair*: ablating a component that genuinely participates can show a small effect because a backup component (the backup name-movers of <!-- secref:I.5 -->[§I.5](#sec-I.5)) compensates. Necessity as measured by a single ablation therefore *understates* importance, and completeness/minimality (<!-- secref:I.5 -->[§I.5](#sec-I.5)) exist to catch it.

<a id="p-i9-limits-and-epistemics-5"></a><!-- para:i9-limits-and-epistemics-5 --> **Attention weights are not explanations.** Reading a head's attention pattern as its "explanation" is unreliable: attention distributions can be perturbed adversarially without changing the prediction, so they do not by themselves constitute a faithful account <!-- cite:92 --> [[92]](references.md#ref-92) — though under stricter, task-aware tests attention can still carry genuine explanatory content <!-- cite:93 --> [[93]](references.md#ref-93). The debate itself is the lesson: *faithfulness must be tested causally* (<!-- secref:I.4 -->[§I.4](#sec-I.4)), never read off a heat-map. This is why the anatomy series reads heads through the gauge-invariant $W_{OV}$/$M$ circuits of <!-- secxref:A.4 -->[§A.4](appendix-a-qkv-first-principles.md#sec-A.4), not through attention weights alone.

<a id="p-i9-limits-and-epistemics-6"></a><!-- para:i9-limits-and-epistemics-6 --> **The streetlight caveat.** Solved circuits (IOI, greater-than, grokking) are narrow, algorithmic, and small-model — chosen partly because they are tractable. Whether the same methods scale to a frontier code model's messy, superposed, cross-layer computation is the open frontier the SAE and automation lines of <!-- secref:I.3 -->[§I.3](#sec-I.3) and <!-- secref:I.4 -->[§I.4](#sec-I.4) are pushing on.

<a id="p-i9-limits-and-epistemics-7"></a><!-- para:i9-limits-and-epistemics-7 --> **What it buys.**

- <a id="p-i9-limits-and-epistemics-8"></a><!-- para:i9-limits-and-epistemics-8 --> A calibration on confidence: every claim in this appendix is a causal hypothesis held to faithfulness/completeness/minimality, not a proof — the same epistemic standard the reproduction rules of this repo apply to experiments.
- A research compass: the gaps above (reading vs. using, illusions, self-repair, scaling) are exactly where the next methods must go.

<a id="p-i9-limits-and-epistemics-9"></a><!-- para:i9-limits-and-epistemics-9 --> **Intuition.** Interpretability is empirical natural science on an artifact we built but do not understand: a probe is an observation, a patch is an experiment, and a circuit is a theory that survives its controls. The illusions are what happen when we mistake a suggestive observation for a confirmed theory — so the discipline is to keep cutting and splicing until the story survives.
