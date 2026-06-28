## The Kernel-Regression Family: Where Attention Sits Among the Similarity-Weighted Averagers

<a id="p-the-kernel-regression-family-where-attention-sits-among-the-similarity-weighted-averagers-1"></a><!-- para:the-kernel-regression-family-where-attention-sits-among-the-similarity-weighted-averagers-1 --> Appendix A dissected one mechanism — attention — down to its two gauge-invariant circuits. This appendix zooms out. It places attention inside a single family of estimators that has been rediscovered under many names — Nadaraya–Watson kernel regression, $k$-nearest-neighbours, Gaussian processes, radial-basis-function networks, and self-attention — and shows that all of them are the *same* one-line idea: predict at a query by taking a **similarity-weighted average of stored responses**. Basic kernel regression is the canonical ancestor; every other member is that skeleton with one ingredient swapped out. We derive each from first principles with no skipped steps, and at each step we ask the organizing question of this appendix: *what, exactly, does this method change relative to basic kernel regression* — and, for attention, why those particular changes are the ones that made transformers work <!-- cite:54 --> [[54]](references.md#ref-54).

<a id="p-the-kernel-regression-family-where-attention-sits-among-the-similarity-weighted-averagers-2"></a><!-- para:the-kernel-regression-family-where-attention-sits-among-the-similarity-weighted-averagers-2 --> Notation follows Appendix A: vectors are **bold lowercase columns** ($\mathbf{x}$, $\mathbf{v}$), matrices are non-bold capitals ($K$, $M$), and scalars are non-bold lowercase ($y_i$, $h$, $d_k$). The plan: B.1 fixes the common skeleton and the axes of comparison; B.2 derives the canonical Nadaraya–Watson form; B.3–B.5 obtain $k$-NN, Gaussian processes, and RBF networks each as a single edit to that form; B.6 places attention as the member with a *learned metric over a dynamic dataset*, linking every departure back to Appendix A; B.7 is the master comparison — one table, two figures, and a reductions lattice; B.8 synthesizes why attention's departures matter.

<!-- sec:B.1 -->
### <a id="sec-B.1"></a>B.1 The Common Skeleton: Prediction as a Similarity-Weighted Average

<a id="p-b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-1"></a><!-- para:b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-1 --> A supervised learner sees pairs $(\mathbf{x}_i, y_i)_{i=1}^{n}$ and must predict the response at a new query $\mathbf{x}$. The most conservative thing it can do — assuming only that *similar inputs have similar outputs* — is to average the responses it has already seen, weighting each by how relevant it is to the query. That is the entire family in one line:

<a id="eq-1"></a><!-- eq:B-1 -->
$$
\hat f(\mathbf{x}) = \sum_{i=1}^{n} w_i(\mathbf{x})\, y_i,
\qquad w_i(\mathbf{x}) \ge 0, \quad \sum_{i=1}^{n} w_i(\mathbf{x}) = 1. \tag{1}
$$

<a id="p-b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-2"></a><!-- para:b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-2 --> Two design questions remain, and *every* method in this appendix is just a pair of answers to them: (i) *which stored points count as relevant to $\mathbf{x}$, and how relevant* — the **kernel** (or similarity) $K(\mathbf{x},\mathbf{x}_i)$; and (ii) *what is being averaged* — the **responses** $y_i$. Fixing the weights to a normalized kernel,

<a id="eq-2"></a><!-- eq:B-2 -->
$$
w_i(\mathbf{x}) = \frac{K(\mathbf{x},\mathbf{x}_i)}{\sum_{j=1}^{n} K(\mathbf{x},\mathbf{x}_j)}, \tag{2}
$$

<a id="p-b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-3"></a><!-- para:b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-3 --> gives the canonical answer. The constraints $w_i \ge 0$ and $\sum_i w_i = 1$ make $\hat f$ a genuine weighted average — an interpolation that never leaves the convex hull of the observed responses. The more powerful members of the family will earn their power precisely by *relaxing* one of these constraints.

<a id="p-b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-4"></a><!-- para:b1-the-common-skeleton-prediction-as-a-similarity-weighted-average-4 --> It is worth naming the axes along which members differ, because the comparison of <!-- secref:B.7 -->[§B.7](#sec-B.7) is organized by them: **(a) the kernel** — fixed and isotropic (Gaussian, box) versus learned and anisotropic; **(b) the weights** — non-negative and normalized, or signed and unnormalized; **(c) the support** — all $n$ data points, the $k$ nearest, $m \ll n$ learned prototypes, or a dynamic per-query set; **(d) what is learned** — nothing (memorize the data), the output weights, the kernel hyperparameters, or the entire metric; and **(e) the output** — a single point estimate or a full predictive distribution. Basic kernel regression is the all-defaults member: a fixed isotropic kernel, non-negative normalized weights, all data, nothing learned, a point estimate. *(Signal-processing reading: Equation <!-- ref:B-1 -->[(1)](#eq-1) is a normalized correlator bank — each stored point is a tap, the kernel sets the tap gains, and the output is a soft, data-dependent average. The whole appendix is a tour of what happens when you let the taps, the gains, and even the tap set be learned.)*

<!-- sec:B.2 -->
### <a id="sec-B.2"></a>B.2 The Canonical Form: Nadaraya–Watson Kernel Regression

<a id="p-b2-the-canonical-form-nadarayawatson-kernel-regression-1"></a><!-- para:b2-the-canonical-form-nadarayawatson-kernel-regression-1 --> Under squared-error loss the optimal predictor is the conditional expectation $f(\mathbf{x}) = \mathbb{E}[y \mid \mathbf{x}]$. If infinitely many samples sat *exactly* at $\mathbf{x}$ we would simply average their responses; because exact matches essentially never occur in a continuous input space, we relax exact matching to *proximity* and weight by a kernel. With the Gaussian kernel of bandwidth $h$ this is the **Nadaraya–Watson estimator**:

<a id="eq-3"></a><!-- eq:B-3 -->
$$
\hat f(\mathbf{x}) = \frac{\sum_{i=1}^{n} K_h(\mathbf{x},\mathbf{x}_i)\, y_i}{\sum_{i=1}^{n} K_h(\mathbf{x},\mathbf{x}_i)},
\qquad K_h(\mathbf{x},\mathbf{x}_i) = \exp\!\left(-\frac{\lVert \mathbf{x}-\mathbf{x}_i\rVert^2}{2h^2}\right). \tag{3}
$$

<a id="p-b2-the-canonical-form-nadarayawatson-kernel-regression-2"></a><!-- para:b2-the-canonical-form-nadarayawatson-kernel-regression-2 --> The formula is not an ansatz; it falls out of the conditional expectation. Write $\mathbb{E}[y\mid\mathbf{x}]$ as a density ratio and estimate the joint and marginal densities with the *same* kernel — an unnormalized kernel-density estimate $p(\mathbf{x},y) \approx \tfrac{1}{n}\sum_i K_h(\mathbf{x},\mathbf{x}_i)\,\delta(y-y_i)$ and $p(\mathbf{x}) \approx \tfrac{1}{n}\sum_i K_h(\mathbf{x},\mathbf{x}_i)$ — and the integral over $y$ collapses the delta onto $y_i$:

<a id="eq-4"></a><!-- eq:B-4 -->
$$
f(\mathbf{x}) = \mathbb{E}[y\mid\mathbf{x}] = \frac{\int y\,p(\mathbf{x},y)\,dy}{p(\mathbf{x})}
\;\approx\; \frac{\sum_i K_h(\mathbf{x},\mathbf{x}_i)\,y_i}{\sum_i K_h(\mathbf{x},\mathbf{x}_i)}. \tag{4}
$$

<a id="p-b2-the-canonical-form-nadarayawatson-kernel-regression-3"></a><!-- para:b2-the-canonical-form-nadarayawatson-kernel-regression-3 --> The two normalizing $\tfrac{1}{n}$ factors — and the Gaussian kernel's omitted $(2\pi h^2)^{-d/2}$ constant — cancel between numerator and denominator, recovering Equation <!-- ref:B-3 -->[(3)](#eq-3) exactly. The bandwidth $h$ is the family's single control knob: small $h$ keeps only the nearest points and gives a wiggly, low-bias, high-variance fit; large $h$ averages widely and gives a smooth, high-bias, low-variance fit. *(Signal-processing reading: $h$ is the bandwidth of a smoothing low-pass over the response — the usual resolution-versus-noise trade, here in input space.)* This is the qualitative break from **linear regression**, which fits a single global line $\hat f(\mathbf{x}) = \mathbf{x}^\top\boldsymbol{\beta}$; kernel regression instead fits a fresh local model at every query. Global structure versus local averaging is the dividing line, and every remaining member of this appendix stays on the local-averaging side of it.

<!-- sec:B.3 -->
### <a id="sec-B.3"></a>B.3 $k$-Nearest-Neighbours: A Hard-Cutoff, Adaptive-Bandwidth Kernel

<a id="p-b3-k-nearest-neighbours-a-hard-cutoff-adaptive-bandwidth-kernel-1"></a><!-- para:b3-k-nearest-neighbours-a-hard-cutoff-adaptive-bandwidth-kernel-1 --> $k$-NN regression is Nadaraya–Watson with two edits and nothing else. Replace the smooth Gaussian by a **hard-cutoff kernel** — the indicator of the $k$ nearest points $N_k(\mathbf{x})$ — and the algebra of Equation <!-- ref:B-3 -->[(3)](#eq-3) collapses the numerator to a plain sum and the denominator to the count $k$:

<a id="eq-5"></a><!-- eq:B-5 -->
$$
K(\mathbf{x},\mathbf{x}_i) = \mathbf{1}\!\left[\mathbf{x}_i \in N_k(\mathbf{x})\right]
\;\Longrightarrow\;
\hat f(\mathbf{x}) = \frac{1}{k}\sum_{i \in N_k(\mathbf{x})} y_i. \tag{5}
$$

<a id="p-b3-k-nearest-neighbours-a-hard-cutoff-adaptive-bandwidth-kernel-2"></a><!-- para:b3-k-nearest-neighbours-a-hard-cutoff-adaptive-bandwidth-kernel-2 --> The first edit changes the *kernel shape* — binary in/out, no smooth decay — so the fit is piecewise-flat (the staircase in <!-- secref:B.7 -->[§B.7](#sec-B.7), Figure B.1). The second is subtler and is what people mean when they call $k$-NN adaptive: fixing the *count* $k$ rather than a *radius* $h$ makes the effective bandwidth shrink in dense regions and grow in sparse ones — $K(\lVert\mathbf{x}-\mathbf{x}_i\rVert / r_k(\mathbf{x}))$ where $r_k(\mathbf{x})$ is the distance to the $k$-th neighbour. Crucially the weights stay non-negative and still sum to one — each is $0$ or $1/k$ — so $k$-NN is the family's *most conservative* relaxation: a genuine average with a brutal kernel and a data-adaptive window. *(Signal-processing reading: a boxcar smoother whose window length is set adaptively to capture a fixed number of samples.)*

<!-- sec:B.4 -->
### <a id="sec-B.4"></a>B.4 Gaussian Processes: Bayesian Kernel Regression

<a id="p-b4-gaussian-processes-bayesian-kernel-regression-1"></a><!-- para:b4-gaussian-processes-bayesian-kernel-regression-1 --> A Gaussian process changes what the kernel *means*. It is no longer a weight but a **prior covariance** between function values, $k(\mathbf{x},\mathbf{x}') = \mathrm{Cov}(f(\mathbf{x}),f(\mathbf{x}'))$ — a statement that nearby inputs should have correlated outputs *before any data are seen*. Place the prior $f \sim \mathcal{N}(0,K)$, add observation noise $\boldsymbol{\varepsilon}\sim\mathcal{N}(0,\sigma_n^2 I)$, and condition on the data. Gaussian conditioning ($\mathbb{E}[b\mid a]=\Sigma_{ba}\Sigma_{aa}^{-1}a$ for a jointly Gaussian pair) gives the posterior at a test point $\mathbf{x}_\ast$ in closed form:

<a id="eq-6"></a><!-- eq:B-6 -->
$$
\hat f(\mathbf{x}_\ast) = \mathbf{k}_\ast^{\top}(K+\sigma_n^2 I)^{-1}\mathbf{y}
= \sum_{i=1}^{n} w_i(\mathbf{x}_\ast)\, y_i,
\qquad
\operatorname{Var}[f_\ast\mid\mathbf{y}] = k_{\ast\ast} - \mathbf{k}_\ast^{\top}(K+\sigma_n^2 I)^{-1}\mathbf{k}_\ast. \tag{6}
$$

<a id="p-b4-gaussian-processes-bayesian-kernel-regression-2"></a><!-- para:b4-gaussian-processes-bayesian-kernel-regression-2 --> Read the mean carefully: it is *still* a similarity-weighted average $\sum_i w_i(\mathbf{x}_\ast)\,y_i$, with the **equivalent-kernel weights** $\mathbf{w}(\mathbf{x}_\ast) = (K+\sigma_n^2 I)^{-1}\mathbf{k}_\ast$. But unlike Nadaraya–Watson these weights are obtained by *solving a global linear system* coupling all points, they are **signed** — carrying small negative side-lobes — and they need not sum to one (empirically $0.996$ in <!-- secref:B.7 -->[§B.7](#sec-B.7), Figure B.2). So a GP relaxes axis (b): non-negativity and normalization both go. In exchange it delivers what no point estimator does — a calibrated predictive variance, the second term of Equation <!-- ref:B-6 -->[(6)](#eq-6), which is axis (e). *(Signal-processing reading: the equivalent kernel is the impulse response of the optimal linear — Wiener — smoother for the assumed covariance and noise; the negative side-lobes are exactly the sharpening such a smoother applies, the deconvolution a matched filter performs to undo the prior's blur.)*

<!-- sec:B.5 -->
### <a id="sec-B.5"></a>B.5 RBF Networks: Kernel Regression with Learned Prototypes

<a id="p-b5-rbf-networks-kernel-regression-with-learned-prototypes-1"></a><!-- para:b5-rbf-networks-kernel-regression-with-learned-prototypes-1 --> Nadaraya–Watson and the GP both *store every training point*: prediction is $O(n)$ per query and GP fitting is $O(n^3)$. A radial-basis-function network removes that cost by replacing the $n$ data centers with $m \ll n$ **learned prototypes** $\mathbf{c}_j$ and making the output coefficients $w_j$ *trainable parameters* fit by least squares:

<a id="eq-7"></a><!-- eq:B-7 -->
$$
\hat f(\mathbf{x}) = \sum_{j=1}^{m} w_j\, \phi_j(\mathbf{x}),
\qquad \phi_j(\mathbf{x}) = \exp\!\left(-\frac{\lVert \mathbf{x}-\mathbf{c}_j\rVert^2}{2\sigma_j^2}\right),
\qquad m \ll n. \tag{7}
$$

<a id="p-b5-rbf-networks-kernel-regression-with-learned-prototypes-2"></a><!-- para:b5-rbf-networks-kernel-regression-with-learned-prototypes-2 --> Two axes move. The support (axis c) shrinks from all $n$ data points to $m$ learned centers; and what is averaged (axis d) is no longer the raw responses $y_i$ but learned weights $w_j$ that *absorb* them — so the responses become parameters rather than data. The result is a parametric, fixed-memory smoother: an RBF network is a one-hidden-layer neural network whose hidden units are **local** bumps rather than global half-spaces. The contrast with an ordinary MLP unit is exact — $\max(0,\mathbf{w}^\top\mathbf{x}+b)$ fires over a global half-space, while $\exp(-\lVert\mathbf{x}-\mathbf{c}\rVert^2/2\sigma^2)$ responds only in a local neighbourhood of its center. RBF networks are the bridge from nonparametric kernel smoothing to trainable architectures, and the first place the pattern "output $=$ similarity $\times$ stored information" became a *learned* layer.

<!-- sec:B.6 -->
### <a id="sec-B.6"></a>B.6 Attention: A Learned Metric over a Dynamic Dataset

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-1"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-1 --> Now attention. Appendix A's normalized form (<!-- secxref:A.5 -->[§A.5](appendix-a-qkv-first-principles.md#sec-A.5)) is, restated for this comparison,

<a id="eq-8"></a><!-- eq:B-8 -->
$$
\mathbf{o}_i = \sum_{j\le i} a_{ij}\,\mathbf{v}_j,
\qquad
a_{ij} = \frac{\kappa(\mathbf{x}_i,\mathbf{x}_j)}{\sum_{j'\le i}\kappa(\mathbf{x}_i,\mathbf{x}_{j'})},
\qquad
\kappa(\mathbf{x}_i,\mathbf{x}_j) = \exp\!\left(\frac{\mathbf{x}_i^{\top} M\, \mathbf{x}_j}{\sqrt{d_k}}\right). \tag{8}
$$

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-2"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-2 --> The mapping to Equation <!-- ref:B-1 -->[(1)](#eq-1) is exact and term-by-term: the **query** $\mathbf{x}_i$ is the regression query $\mathbf{x}$; each **key** position $\mathbf{x}_j$ is a stored data point; each **value** $\mathbf{v}_j = W_V\mathbf{x}_j$ is the response $y_j$ — now a *vector*, not a scalar; and the **softmax of scores** is the normalized kernel of Equation <!-- ref:B-2 -->[(2)](#eq-2). Attention *is* Nadaraya–Watson kernel regression, run over the sequence in a learned feature geometry <!-- cite:54 --> [[54]](references.md#ref-54). But it is the member that changes the most relative to the basic form, and naming the changes is the point of this appendix. There are four, each a thread back into Appendix A.

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-3"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-3 --> **Departure 1 — the kernel is a learned, anisotropic bilinear form, not a fixed isotropic distance.** The score is $\mathbf{x}_i^\top M\,\mathbf{x}_j/\sqrt{d_k}$ with $M = W_Q^{\top} W_K$ *learned* (<!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2)). Every classical kernel above fixes the geometry — a Gaussian weights by Euclidean distance, treating all directions alike; attention learns the metric $M$ that decides which directions count as "near" (<!-- secxref:A.5 -->[§A.5](appendix-a-qkv-first-principles.md#sec-A.5)). The kernel's whole geometry is trained, not assumed.

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-4"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-4 --> **Departure 2 — it grows with alignment, not decays with distance.** Because $\kappa = \exp(\text{inner product})$ rather than $\exp(-\text{squared distance})$, the attention kernel is *not* a radial basis function: along a ray it grows with alignment — monotonically so in the symmetric-positive-definite case Figure A.4 plots — instead of peaking at the query and decaying (<!-- secxref:A.5 -->[§A.5](appendix-a-qkv-first-principles.md#sec-A.5), Figure A.4). The softmax denominator — not a fixed bandwidth $h$ — supplies the normalization, an adaptive temperature set by the $1/\sqrt{d_k}$ scaling derived in <!-- secxref:A.7 -->[§A.7](appendix-a-qkv-first-principles.md#sec-A.7).

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-5"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-5 --> **Departure 3 — the kernel is directed.** In general $M \ne M^{\top}$ (<!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2)), so the similarity of $i$ to $j$ differs from that of $j$ to $i$: the feature a token advertises as a *key* need not be the one it requests as a *query*. Every classical kernel here is symmetric in its two arguments; attention's is not. Read-side and write-side geometries are distinct — the two singular-vector families of the head's SVD (<!-- secxref:A.8 -->[§A.8](appendix-a-qkv-first-principles.md#sec-A.8)).

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-6"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-6 --> **Departure 4 — the dataset is dynamic and content-addressed.** $k$-NN, Nadaraya–Watson, the GP, and the RBF network all regress against a *fixed, stored* training set. Attention's "data points" are the keys and values of the *current sequence*, recomputed from the residual stream at every position and every forward pass (<!-- secxref:A.1 -->[§A.1](appendix-a-qkv-first-principles.md#sec-A.1), <!-- secxref:A.3 -->[§A.3](appendix-a-qkv-first-principles.md#sec-A.3)). There is no stored corpus; the support is built on the fly from the input itself. This is exactly what lets a transformer perform *in-context* regression — fit a fresh predictor to the prompt it is reading — and is the mechanism behind induction heads (<!-- secxref:A.9 -->[§A.9](appendix-a-qkv-first-principles.md#sec-A.9)) <!-- cite:60 --> [[60]](references.md#ref-60).

<a id="p-b6-attention-a-learned-metric-over-a-dynamic-dataset-7"></a><!-- para:b6-attention-a-learned-metric-over-a-dynamic-dataset-7 --> Two further facts from Appendix A complete the picture and have no analogue among the classical members. First, only the gauge-invariant products $M$ and $W_{OV}$ are observable; the raw projections carry unobservable degrees of freedom (<!-- secxref:A.4 -->[§A.4](appendix-a-qkv-first-principles.md#sec-A.4)) — there is no scalar "bandwidth" to read off a column, only the learned operators to decompose. Second, because the responses $\mathbf{v}_j$ are themselves learned projections, routed by a *second* learned operator $W_{OV} = W_O W_V$ (<!-- secxref:A.3 -->[§A.3](appendix-a-qkv-first-principles.md#sec-A.3)) <!-- cite:59 --> [[59]](references.md#ref-59), attention also learns *what to average*, not only *how to weight* — an axis only the RBF network partly shares. In one phrase, attention is **learned kernel regression over learned representations of a dynamic dataset**, and it is simultaneously a *learned adaptive matched filter*, the reading of <!-- secxref:A.6 -->[§A.6](appendix-a-qkv-first-principles.md#sec-A.6).

<!-- sec:B.7 -->
### <a id="sec-B.7"></a>B.7 The Overwhelming Comparison

<a id="p-b7-the-overwhelming-comparison-1"></a><!-- para:b7-the-overwhelming-comparison-1 --> Every method in this appendix is the one estimator $\hat f(\mathbf{x}) = \sum_i w_i(\mathbf{x})\,y_i$ of Equation <!-- ref:B-1 -->[(1)](#eq-1); they differ only in how the weights are built and what is averaged. Table B.1 lays the whole family against the canonical form on every axis at once; the reductions beneath it read the table as a lattice of single edits; and Figures B.1–B.2 confirm, on one shared dataset, that the fits and the weight vectors really are as the table claims.

| Method | "Response" averaged | Kernel / similarity | Weight rule | Weights $\ge 0$ and sum to 1? | Support (data) | What is learned | Uncertainty? |
|---|---|---|---|---|---|---|---|
| **Basic kernel regression** (Nadaraya–Watson) | data $y_i$ | fixed, isotropic (Gaussian, bandwidth $h$) | normalized kernel, Equation <!-- ref:B-2 -->[(2)](#eq-2) | yes / yes | all $n$ points | nothing | no |
| **$k$-NN** | data $y_i$ | hard cutoff (indicator of $k$ nearest) | $1/k$ on the $k$ nearest, else $0$ | yes / yes | the $k$ nearest (of $n$ stored) | nothing (pick $k$) | no |
| **Gaussian process** | data $y_i$ | prior covariance $k(\mathbf{x},\mathbf{x}')$ | $(K+\sigma_n^2 I)^{-1}\mathbf{k}_\ast$, global solve | **no / no** (signed) | all $n$ points | kernel hyperparameters | **yes** (variance) |
| **RBF network** | trained weights $w_j$ | fixed, isotropic about centers | trained by least squares | no / no | $m \ll n$ learned centers | centers and output weights | no |
| **Attention** | learned values $\mathbf{v}_j$ (vectors) | **learned, anisotropic, directed** $\exp(\mathbf{x}_i^\top M\,\mathbf{x}_j/\sqrt{d_k})$ | softmax of scores | yes / yes (per row) | **dynamic** per-input keys | **the metric $M$ and the value map $W_{OV}$** | no (point write) |
| *Linear regression* (contrast) | — | — (global, no locality) | query-independent $\boldsymbol{\beta}$ | — | all $n$, one global fit | the coefficients $\boldsymbol{\beta}$ | no |

<a id="p-b7-the-overwhelming-comparison-2"></a><!-- para:b7-the-overwhelming-comparison-2 --> Read as a lattice of single edits from the canonical form:

- <a id="p-b7-the-overwhelming-comparison-3"></a><!-- para:b7-the-overwhelming-comparison-3 --> **$k$-NN** $=$ basic kernel regression with the Gaussian kernel swapped for a hard indicator and a fixed *radius* swapped for a fixed *count* (adaptive bandwidth).
- **Gaussian process** (mean) $=$ basic kernel regression with the kernel reinterpreted as a prior covariance and the weights solved globally as $(K+\sigma_n^2 I)^{-1}\mathbf{k}_\ast$ — signed, and now paired with a predictive variance.
- **RBF network** $=$ basic kernel regression with the $n$ data centers compressed to $m \ll n$ learned prototypes and the responses replaced by trained output weights.
- **Attention** $=$ basic kernel regression with (i) a learned anisotropic metric in the kernel, (ii) a directed (asymmetric) similarity, (iii) softmax normalization in place of a fixed bandwidth, and (iv) a dynamic, content-addressed dataset of learned key/value projections.
- **Linear regression** is the non-member: a single global fit whose weights do not depend on the query — the one thing every member above refuses to be.

<a id="p-b7-the-overwhelming-comparison-4"></a><!-- para:b7-the-overwhelming-comparison-4 --> ![Four panels on one shared 1-D dataset of forty noisy points: a Nadaraya-Watson Gaussian-kernel fit, a piecewise-flat k-nearest-neighbour fit, a Gaussian-process posterior mean with a shaded 95-percent uncertainty band, and an RBF-network fit with eight center markers; each panel also shows the true function dashed](figures/kernel-family-fits.svg)

<!-- sec:B.7-figure-a -->
<a id="p-b7-the-overwhelming-comparison-5"></a><!-- para:b7-the-overwhelming-comparison-5 --> <a id="sec-B.7-figure-a"></a>**Figure B.1.** One skeleton, four ways to build the weights. The same forty noisy samples of a smooth $f$ are fit by four members of the family, each a linear smoother $\hat f(\mathbf{x}) = \sum_i w_i(\mathbf{x})\,y_i$ in the sense of Equation <!-- ref:B-1 -->[(1)](#eq-1). *Top-left:* Nadaraya–Watson with a Gaussian kernel ($h=0.45$), the baseline (RMSE-to-truth $0.208$). *Top-right:* $k$-NN ($k=5$) gives the piecewise-flat staircase of a hard-cutoff kernel (RMSE $0.192$), the dotted NW curve shown for contrast. *Bottom-left:* the Gaussian process adds what the point estimators cannot — a calibrated $95\%$ band (mean RMSE $0.198$). *Bottom-right:* the RBF network reproduces the fit (RMSE $0.165$) from only $m=8$ centers (triangles) instead of all $n=40$ stored points — the parametric compression of Equation <!-- ref:B-7 -->[(7)](#eq-7). Regenerate via `surveys/llms-for-coding/figures/kernel-family-fits.py`.

<a id="p-b7-the-overwhelming-comparison-6"></a><!-- para:b7-the-overwhelming-comparison-6 --> ![Four stem plots over the same forty data locations, showing the weight each method assigns to every datum to predict at one query point: Nadaraya-Watson gives a positive local bell, k-NN gives five equal spikes, and the Gaussian process and RBF network give signed weights with visible negative side-lobes](figures/kernel-family-weights.svg)

<!-- sec:B.7-figure-b -->
<a id="p-b7-the-overwhelming-comparison-7"></a><!-- para:b7-the-overwhelming-comparison-7 --> <a id="sec-B.7-figure-b"></a>**Figure B.2.** Same $\sum_i w_i\,y_i$, four very different weight vectors. For one query $x^\ast = 0.8$ on the dataset of Figure B.1, each panel stems the weight $w_i(x^\ast)$ that the method places on every datum — the *equivalent kernel* made literal. *Nadaraya–Watson:* a non-negative local bell summing to $1.00$. *$k$-NN:* five equal spikes of height $1/k = 0.20$, the rest exactly zero. *Gaussian process* and *RBF network:* signed weights with visible negative side-lobes (minima $-0.04$ and $-0.05$) that do **not** sum to one ($0.996$ and $1.005$) — the price and the power of relaxing the non-negativity and normalization constraints of Equation <!-- ref:B-1 -->[(1)](#eq-1). Basic kernel regression is the member whose weights stay non-negative, normalized, and local; each relative drops one of those. Regenerate via `surveys/llms-for-coding/figures/kernel-family-weights.py`.

<a id="p-b7-the-overwhelming-comparison-8"></a><!-- para:b7-the-overwhelming-comparison-8 --> One reading of Table B.1 dominates. Basic kernel regression is the member whose weights are simultaneously **non-negative, normalized, local, and built from a fixed isotropic kernel**. Each relative drops exactly one or two of those properties — $k$-NN the kernel's smoothness, the GP the non-negativity and normalization (buying calibrated uncertainty), the RBF network the nonparametric support (buying fixed memory) — and attention drops the most at once: the fixed kernel (a learned metric), the symmetry (a directed similarity), the fixed bandwidth (softmax), and the static dataset (dynamic, content-addressed). The progression from the first member to the last is the progression from *memorizing a dataset* to *learning a geometry and constructing the dataset on the fly* — which is exactly why the last member, alone among them, scales to language.

<!-- sec:B.8 -->
### <a id="sec-B.8"></a>B.8 Synthesis: Why the Departures Matter

<a id="p-b8-synthesis-why-the-departures-matter-1"></a><!-- para:b8-synthesis-why-the-departures-matter-1 --> The comparison is not a curiosity; each of attention's four departures is load-bearing. The **learned metric $M$** lets the network discover its comparison geometry from data instead of being handed Euclidean distance — indispensable, because "similar" in token space is nothing like "close in $\mathbb{R}^{d}$," and the right geometry is different for every head (<!-- secxref:A.8 -->[§A.8](appendix-a-qkv-first-principles.md#sec-A.8)). The **dynamic, content-addressed dataset** is what makes in-context learning possible: the regression set *is* the prompt, so one fixed set of weights solves a new task on every input — the empirical signature of induction heads (<!-- secxref:A.9 -->[§A.9](appendix-a-qkv-first-principles.md#sec-A.9)) <!-- cite:60 --> [[60]](references.md#ref-60). The **directed similarity** lets routing be asymmetric — a pronoun queries for its antecedent without the antecedent symmetrically querying back. And **softmax with the $1/\sqrt{d_k}$ scaling** is a self-normalizing, width-stable temperature (<!-- secxref:A.7 -->[§A.7](appendix-a-qkv-first-principles.md#sec-A.7)), so there is no bandwidth to retune per layer.

<a id="p-b8-synthesis-why-the-departures-matter-2"></a><!-- para:b8-synthesis-why-the-departures-matter-2 --> Basic kernel regression is the Rosetta stone for this entire family: $k$-NN, Gaussian processes, RBF networks, and attention are each one or two edits away from it. Attention is the member that made the kernel, the metric, and the dataset all *learned and dynamic* at once — and that is the whole distance between a 1960s smoother and a transformer. The deeper machinery that makes attention's learned operators *readable* — the gauge freedom, the QK/OV factorization, the singular-value decomposition, and the hand-built induction head — is the subject of Appendix A, whose summary (<!-- secxref:A.12 -->[§A.12](appendix-a-qkv-first-principles.md#sec-A.12)) this appendix has been a wide-angle companion to.
