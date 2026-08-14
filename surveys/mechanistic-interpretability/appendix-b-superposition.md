<!-- sec:B -->
## <a id="sec-B"></a>B Superposition and the grokking circuit

<a id="p-b-superposition-and-the-grokking-circuit-1"></a><!-- para:b-superposition-and-the-grokking-circuit-1 --> **Depth tier:** headline

<a id="p-b-superposition-and-the-grokking-circuit-2"></a><!-- para:b-superposition-and-the-grokking-circuit-2 --> Derivations for § <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) (superposition) and § <!-- secxref:9.3 -->[§9.3](circuits-across-models.md#sec-9.3) (the reverse-engineered modular-addition algorithm).

<!-- sec:B.1 -->
### <a id="sec-B.1"></a>B.1 The ReLU-output toy model

<a id="p-b1-the-relu-output-toy-model-1"></a><!-- para:b1-the-relu-output-toy-model-1 --> The minimal model of superposition <!-- cite:3 --> [[3]](references.md#ref-3) takes $n$ synthetic features $\mathbf{x}\in\mathbb{R}^{n}$, each active independently with probability $1-S_i$ ($S_i$ the sparsity) and carrying importance $I_i$, projects them through $W\in\mathbb{R}^{m\times n}$ with $m<n$, and reconstructs with the tied transpose plus a ReLU:

<a id="eq-1"></a><!-- eq:B-1 -->
$$
\mathbf{x}' = \mathrm{ReLU}\big(W^{\top} W\mathbf{x} + \mathbf{b}\big), \qquad \mathcal{L} = \mathbb{E}_{\mathbf{x}}\sum_{i} I_i\,(x_i - x'_i)^2. \tag{1}
$$

<a id="p-b1-the-relu-output-toy-model-2"></a><!-- para:b1-the-relu-output-toy-model-2 --> The hidden activation $W\mathbf{x}\in\mathbb{R}^{m}$ is the bottleneck; $W^{\top}$ reconstructs; the ReLU filters interference. When features are **dense** (low $S_i$) the optimum represents the $m$ most important features orthogonally and drops the rest (PCA-like); when features are **sparse** (high $S_i$) it packs $>m$ features as non-orthogonal directions, tolerating rare collisions — **superposition**.

<!-- sec:B.2 -->
### <a id="sec-B.2"></a>B.2 Feature dimensionality, capacity, and the phase diagram

<a id="p-b2-feature-dimensionality-capacity-and-the-phase-diagram-1"></a><!-- para:b2-feature-dimensionality-capacity-and-the-phase-diagram-1 --> For learned columns $W_i$ with unit versions $\hat W_i = W_i/\lVert W_i\rVert$, define the **feature dimensionality**

<a id="eq-2"></a><!-- eq:B-2 -->
$$
D_i = \frac{\lVert W_i\rVert_2^{2}}{\sum_{j}\big(\hat W_j\cdot W_i\big)^{2}}, \qquad \sum_i D_i \approx m. \tag{2}
$$

<a id="p-b2-feature-dimensionality-capacity-and-the-phase-diagram-2"></a><!-- para:b2-feature-dimensionality-capacity-and-the-phase-diagram-2 --> $D_i = 1$ means feature $i$ owns a whole dimension (orthogonal to all others); $D_i = 0$ means it is not represented; $D_i = \tfrac12$ is an antipodal pair sharing a dimension. The capacity identity $\sum_i D_i \approx m$ says the model uses ~all of its bottleneck. Sweeping (importance, sparsity) reveals a sharp **phase transition** from no-superposition (orthogonal or dropped) to superposition, where the optimal geometry moves through antipodal pairs to vertices of regular polytopes (line, triangle, pentagon, octahedron, …) that spread directions as uniformly as possible to minimize pairwise interference $\sum_{i\ne j}(\hat W_i\cdot\hat W_j)^2$ — the same objective as the physics **Thomson problem** of charges repelling on a sphere. This is why polysemantic neurons are the *expected* outcome, not a defect, and why the interpretable unit is a learned direction (§ <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6)).

> <a id="p-b2-feature-dimensionality-capacity-and-the-phase-diagram-3"></a><!-- para:b2-feature-dimensionality-capacity-and-the-phase-diagram-3 --> **SP note.** Equation <!-- ref:B-1 -->[(1)](#eq-1) is compressed sensing run by training: a sparse high-dimensional signal is projected to a low-dimensional measurement $W\mathbf{x}$, and recovery is possible under incoherence + sparsity — with the ReLU standing in for the nonlinear recovery step. Dictionary learning (the SAE) is the decoder that inverts it.

<!-- sec:B.3 -->
### <a id="sec-B.3"></a>B.3 The grokking modular-addition algorithm

<a id="p-b3-the-grokking-modular-addition-algorithm-1"></a><!-- para:b3-the-grokking-modular-addition-algorithm-1 --> The one-layer transformer trained on $a+b \bmod p$ ($p=113$) embeds each input, projected onto a sparse set of key frequencies $w_k = 2\pi k/p$, as a point on a circle $(\cos w_k x, \sin w_k x)$ — a discrete Fourier feature <!-- cite:55 --> [[55]](references.md#ref-55). The attention+MLP block combines the embeddings of $a$ and $b$ via the angle-addition identities

<a id="eq-3"></a><!-- eq:B-3 -->
$$
\cos(w_k a)\cos(w_k b) - \sin(w_k a)\sin(w_k b) = \cos\!\big(w_k(a+b)\big), \tag{3}
$$

<a id="p-b3-the-grokking-modular-addition-algorithm-2"></a><!-- para:b3-the-grokking-modular-addition-algorithm-2 --> producing a representation at angle $w_k(a+b)$ for each key frequency. The unembedding forms, for each candidate answer $c$, a logit that (via a further identity) is proportional to a sum over key frequencies:

<a id="eq-4"></a><!-- eq:B-4 -->
$$
\text{logit}(c) \;\propto\; \sum_{k\in\text{key}}\cos\!\big(w_k(a + b - c)\big), \tag{4}
$$

<a id="p-b3-the-grokking-modular-addition-algorithm-3"></a><!-- para:b3-the-grokking-modular-addition-algorithm-3 --> which is a **matched filter**: it is maximized by constructive interference across the frequencies exactly when $c \equiv a+b\ (\mathrm{mod}\ p)$, and near-uniformly small otherwise. The **progress measures** that expose the gradual formation of this circuit under a flat test-loss curve are the *restricted loss* (keep only key frequencies) and *excluded loss* (ablate key frequencies); tracking them reveals the memorization → circuit-formation → cleanup phases <!-- cite:55 --> [[55]](references.md#ref-55). This is the field's cleanest existence proof that gradient descent finds a crisp, human-legible algorithm — and it is entirely a statement in the frequency domain.

<!-- sec:B.4 -->
### <a id="sec-B.4"></a>B.4 Figure — the capacity argument, plotted

<a id="p-b4-figure-the-capacity-argument-plotted-1"></a><!-- para:b4-figure-the-capacity-argument-plotted-1 --> ![Superposition interference and capacity](figures/appendix-b-superposition-capacity.svg)

<a id="p-b4-figure-the-capacity-argument-plotted-2"></a><!-- para:b4-figure-the-capacity-argument-plotted-2 --> **F-B1 · Interference is linear in feature count and sparsity; capacity is inversely proportional to sparsity.**

<a id="p-b4-figure-the-capacity-argument-plotted-3"></a><!-- para:b4-figure-the-capacity-argument-plotted-3 --> **1 · Purpose and operating conditions.** Both panels are **closed forms**, not measurements: no model was trained or run. Parameters: residual width $d = 768$ (GPT-2-small's, used only to keep the numbers recognizable); typical squared magnitude of an active feature $s = 1$; required signal-to-interference ratio $\tau = 10$ in panel (b); sparsities $p \in \{0.5, 0.1, 0.01, 0.001\}$. The Monte-Carlo markers in (a) use `numpy.random.default_rng(0)`, 4,000 trials per point, at $(d,m,p) \in \{(64,200,0.05), (128,500,0.02), (256,2000,0.01)\}$.

<a id="p-b4-figure-the-capacity-argument-plotted-4"></a><!-- para:b4-figure-the-capacity-argument-plotted-4 --> **2 · What it shows.** (a) The mean-square interference from reading one feature off a superposed stream, against the closed form $(m-1)ps/d$; markers are the seeded simulation. (b) The number of features tolerable at a given signal-to-interference ratio, $m_{\max} = 1 + d/(p\tau)$.

<a id="p-b4-figure-the-capacity-argument-plotted-5"></a><!-- para:b4-figure-the-capacity-argument-plotted-5 --> **3 · How to read it.** The interference curve crosses the signal level at the point where a probe recovers noise rather than a feature — that crossing, not any capacity bound, is what limits superposition. In (b), note that $s$ cancels: **tolerable feature count does not depend on how large activations are**, only on how often they fire.

<a id="p-b4-figure-the-capacity-argument-plotted-6"></a><!-- para:b4-figure-the-capacity-argument-plotted-6 --> **4 · Caveats.** The closed form assumes *random* directions; a trained model's directions are not random, and organized geometry can do better. Empirical ratios of simulation to closed form are 0.992, 1.007, 1.017 — agreement is the claim, the third digit is not. Generator and persisted data: `figures/appendix-b-superposition-capacity.py` / `.json`.
