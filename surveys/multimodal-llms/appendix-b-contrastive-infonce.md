<!-- sec:B -->
## <a id="sec-B"></a>B Contrastive alignment: InfoNCE from first principles

<a id="p-b-contrastive-alignment-infonce-from-first-principles-1"></a><!-- para:b-contrastive-alignment-infonce-from-first-principles-1 --> Section <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) stated CLIP's symmetric loss and used it; this appendix derives *why* that loss does what it does — why a batch-classification objective produces a meaningful shared embedding geometry — by way of its information-theoretic origin in Contrastive Predictive Coding <!-- cite:49 -->[[49]](#ref-49). The payoff is a precise answer to a question § 2.4 left implicit: why does the batch size matter so much?

<!-- sec:B.1 -->
### <a id="sec-B.1"></a>B.1 The loss is a classification

<a id="p-b1-the-loss-is-a-classification-1"></a><!-- para:b1-the-loss-is-a-classification-1 --> Fix an image $x_v$ and its matching caption, and place that caption in a set $X = \{x_t^{(1)},\dots,x_t^{(N)}\}$ of $N$ candidates, exactly one of which is the true match (the other $N-1$ are other captions from the batch). Define a *score* $f(x_v, x_t)$ measuring compatibility. The InfoNCE loss is the categorical cross-entropy of picking the true caption out of the set:

<a id="eq-1"></a><!-- eq:B-1 -->
$$
\mathcal{L}_{\mathrm{NCE}} = -\,\mathbb{E}_{X}\!\left[\log \frac{f(x_v, x_t^{+})}{\sum_{j=1}^{N} f(x_v, x_t^{(j)})}\right] \tag{1}
$$

<a id="p-b1-the-loss-is-a-classification-2"></a><!-- para:b1-the-loss-is-a-classification-2 --> where $x_t^{+}$ is the true caption. This is precisely a softmax classifier over $N$ classes whose logits are the scores — the same object as a row of CLIP's loss in § 2.4, once we identify $f$ with the exponentiated scaled similarity $f(x_v,x_t) = \exp(\mathrm{sim}(x_v,x_t)/\tau)$. CLIP's "predict which caption goes with which image" is literally Equation <!-- ref:B-1 -->[(1)](#eq-1).

<!-- sec:B.2 -->
### <a id="sec-B.2"></a>B.2 The optimal score is a density ratio

<a id="p-b2-the-optimal-score-is-a-density-ratio-1"></a><!-- para:b2-the-optimal-score-is-a-density-ratio-1 --> What does minimizing Equation <!-- ref:B-1 -->[(1)](#eq-1) push $f$ toward? Write $p(d=i\mid X, x_v)$ for the probability that candidate $i$ is the true match. The true caption was drawn from the conditional $p(x_t\mid x_v)$ while the distractors were drawn from the marginal $p(x_t)$; Bayes' rule over the set gives

<a id="eq-2"></a><!-- eq:B-2 -->
$$
p(d=i\mid X, x_v) = \frac{\dfrac{p(x_t^{(i)}\mid x_v)}{p(x_t^{(i)})}}{\displaystyle\sum_{j=1}^{N}\dfrac{p(x_t^{(j)}\mid x_v)}{p(x_t^{(j)})}} \tag{2}
$$

<a id="p-b2-the-optimal-score-is-a-density-ratio-2"></a><!-- para:b2-the-optimal-score-is-a-density-ratio-2 --> Matching Equation <!-- ref:B-2 -->[(2)](#eq-2) to the softmax of Equation <!-- ref:B-1 -->[(1)](#eq-1) shows the optimal score is the **density ratio** $f^\star(x_v, x_t) \propto p(x_t\mid x_v)/p(x_t)$, *independent of the number of negatives* <!-- cite:49 -->[[49]](#ref-49). This is the conceptual heart: the network is not asked to model the high-dimensional $p(x_t\mid x_v)$ (a hard generative problem) but only the *ratio* by which seeing the image raises a caption's probability — a far easier discriminative quantity, and exactly the "is this pair more likely than chance?" signal a matched filter computes.

<!-- sec:B.3 -->
### <a id="sec-B.3"></a>B.3 The mutual-information lower bound, and why batch size matters

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-1"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-1 --> Because the optimal score is the density ratio, the loss is tied to the **mutual information** $I(x_v; x_t)$ between image and caption. Substituting $f^\star$ into Equation <!-- ref:B-1 -->[(1)](#eq-1) and bounding yields

<a id="eq-3"></a><!-- eq:B-3 -->
$$
I(x_v; x_t) \;\geq\; \log N - \mathcal{L}_{\mathrm{NCE}} \tag{3}
$$

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-2"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-2 --> so minimizing the InfoNCE loss *maximizes a lower bound on the mutual information* between the two views <!-- cite:49 -->[[49]](#ref-49). Two consequences follow directly, and both were visible empirically in § 2.4. First, the bound is **tighter as $N$ grows**: more in-batch negatives means $\log N$ is larger and the gap the loss must close is a better estimate of the true MI — which is the precise, information-theoretic reason CLIP trains at a batch of $32{,}768$ and SigLIP studies batch size as a first-class variable (§ <!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)). The matched-filter intuition of § 2.4 and this bound are the same statement in two languages: more interferers to reject (more negatives) sharpens the learned discrimination *and* tightens the MI estimate. Second, the bound caps what one batch can teach — $I \leq \log N$ is the most information a single $N$-way classification can certify — so beyond a point, returns to batch size diminish, exactly the saturation SigLIP reports.

<!-- sec:B.4 -->
### <a id="sec-B.4"></a>B.4 From the bound back to CLIP and SigLIP

<a id="p-b4-from-the-bound-back-to-clip-and-siglip-1"></a><!-- para:b4-from-the-bound-back-to-clip-and-siglip-1 --> CLIP instantiates Equation <!-- ref:B-1 -->[(1)](#eq-1) symmetrically — once classifying captions given an image, once images given a caption — because the density ratio $p(x_t\mid x_v)/p(x_t)$ and its transpose $p(x_v\mid x_t)/p(x_v)$ are different quantities, and aligning both directions is what makes the geometry usable for retrieval either way (§ 2.4). The temperature $\tau$ is the softmax's inverse gain: it scales the cosine similarities into logits, and because CLIP learns it (clipped for stability), the model tunes how sharply the $N$-way classification is peaked. SigLIP's sigmoid loss (§ 2.5) abandons the softmax of Equation <!-- ref:B-1 -->[(1)](#eq-1) — and with it the explicit $\log N$ MI bound — in exchange for a per-pair objective that factorizes across the batch; it trades the clean information-theoretic interpretation for the memory and communication savings that matter at engineering scale. Both, in the end, are learning the same density ratio; they differ only in how they normalize it.
