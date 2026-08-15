<!-- sec:B -->
## <a id="sec-B"></a>B Contrastive alignment: InfoNCE from first principles

<a id="p-b-contrastive-alignment-infonce-from-first-principles-1"></a><!-- para:b-contrastive-alignment-infonce-from-first-principles-1 --> **Depth tier:** headline

<a id="p-b-contrastive-alignment-infonce-from-first-principles-2"></a><!-- para:b-contrastive-alignment-infonce-from-first-principles-2 --> Section <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) stated CLIP's symmetric loss and used it; this appendix derives *why* that loss does what it does — why a batch-classification objective produces a meaningful shared embedding geometry — by way of its information-theoretic origin in Contrastive Predictive Coding <!-- cite:49 -->[[49]](#ref-49). The payoff is a precise answer to a question <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) left implicit: why does the batch size matter so much?

<!-- sec:B.1 -->
### <a id="sec-B.1"></a>B.1 The loss is a classification

<a id="p-b1-the-loss-is-a-classification-1"></a><!-- para:b1-the-loss-is-a-classification-1 --> Fix an image $x_v$ and its matching caption, and place that caption in a set $X = \{x_t^{(1)},\dots,x_t^{(N)}\}$ of $N$ candidates, exactly one of which is the true match (the other $N-1$ are other captions from the batch). Define a *score* $f(x_v, x_t)$ measuring compatibility. The InfoNCE loss is the categorical cross-entropy of picking the true caption out of the set:

<a id="eq-1"></a><!-- eq:B-1 -->
$$
\mathcal{L}_{\mathrm{NCE}} = -\,\mathbb{E}_{X}\!\left[\log \frac{f(x_v, x_t^{+})}{\sum_{j=1}^{N} f(x_v, x_t^{(j)})}\right] \tag{1}
$$

<a id="p-b1-the-loss-is-a-classification-2"></a><!-- para:b1-the-loss-is-a-classification-2 --> where $x_t^{+}$ is the true caption. This is precisely a softmax classifier over $N$ classes whose logits are the scores — the same object as a row of CLIP's loss in <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4), once we identify $f$ with the exponentiated scaled similarity $f(x_v,x_t) = \exp(\mathrm{sim}(x_v,x_t)/\tau)$. CLIP's "predict which caption goes with which image" is literally Equation <!-- ref:B-1 -->[(1)](#eq-1).

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

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-1"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-1 --> Because the optimal score is the density ratio, the loss is tied to the **mutual information** $I(x_v; x_t)$ between image and caption. The source states the resulting bound in its main text and defers the derivation to an appendix <!-- cite:49 -->[[49]](#ref-49); since that derivation is the only place the batch-size argument is actually earned, it is worked here in full rather than asserted. Substitute the optimal score $f^\star = p(x_t \mid x_v)/p(x_t)$ into Equation <!-- ref:B-1 -->[(1)](#eq-1) and split the denominator into the positive and the $N-1$ negatives. Writing $r \equiv p(x_t^{+})/p(x_t^{+}\mid x_v)$ for the *reciprocal* density ratio at the positive sample, the summand becomes

<a id="eq-3"></a><!-- eq:B-3 -->
$$
\mathcal{L}^{\star} = \mathbb{E}_X \log\left[1 + r \sum_{x_j \in X_{\text{neg}}} \frac{p(x_j \mid x_v)}{p(x_j)}\right] \tag{3}
$$

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-2"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-2 --> Each negative is drawn from the marginal, and $\mathbb{E}_{x_j \sim p}\big[p(x_j\mid x_v)/p(x_j)\big] = 1$ exactly, so replacing the sum over $N-1$ negatives by its mean gives $r(N-1)$ — an approximation that sharpens as $N$ grows, and the one place the source flags its own looseness. Then

<a id="eq-4"></a><!-- eq:B-4 -->
$$
\mathcal{L}^{\star} \approx \mathbb{E}_X \log\big[1 + r(N-1)\big] \;\geq\; \mathbb{E}_X \log\big[rN\big] = \log N - I(x_v; x_t) \tag{4}
$$

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-3"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-3 --> where the last equality is just $\mathbb{E}[\log r] = -I$ by definition of mutual information. Rearranging gives the bound the field quotes:

<a id="eq-5"></a><!-- eq:B-5 -->
$$
I(x_v; x_t) \;\geq\; \log N - \mathcal{L}_{\mathrm{NCE}} \tag{5}
$$

> <a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-4"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-4 --> **Note — the middle inequality of Equation <!-- ref:B-4 -->[(4)](#eq-4) does not hold pointwise, and the repair costs one symbol.** The step $\log[1 + r(N-1)] \ge \log[rN]$ is equivalent, since $\log$ is monotone and $r > 0$, to $1 + r(N-1) \ge rN$, i.e. to $r \le 1$ — which says the caption is *more* likely given the image than unconditionally. That is true on average (it is what positive mutual information means) but **not** guaranteed for every drawn pair, and the source asserts the step with a bare inequality and no condition. The gap is nevertheless bounded, uniformly and tightly. The ratio of the two arguments, $h(r) = \dfrac{1 + r(N-1)}{rN} = \dfrac{1}{rN} + \dfrac{N-1}{N}$, is strictly decreasing in $r$ with infimum $\frac{N-1}{N}$, so for **every** $r > 0$ the step loses at most $\log\frac{N}{N-1}$ nats. The unconditional statement is therefore $I \ge \log(N-1) - \mathcal{L}_{\mathrm{NCE}}$: the published bound with $N$ replaced by $N-1$. At CLIP's $N = 32{,}768$ the difference is $3.1 \times 10^{-5}$ nats, so nothing downstream changes — but the honest form of Equation <!-- ref:B-5 -->[(5)](#eq-5) is the $N-1$ one, and the $N$ version needs a pointwise assumption nobody states.

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-5"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-5 --> Two consequences follow directly, and both were visible empirically in <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4). First, the bound is **tighter as $N$ grows**: more in-batch negatives means $\log N$ is larger and the gap the loss must close is a better estimate of the true MI — the precise, information-theoretic reason CLIP trains at a batch of $32{,}768$ and SigLIP studies batch size as a first-class variable (<!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)). The matched-filter intuition of <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) and this bound are the same statement in two languages: more interferers to reject sharpens the learned discrimination *and* tightens the MI estimate. Second, the bound **caps what one batch can certify** — $\log N$ nats is the ceiling of an $N$-way classification, no matter how good the encoder — so returns to batch size must diminish once $\log N$ exceeds the true $I$.

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-6"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-6 --> **Worked example — the ceiling is not the binding constraint.** At $N = 32{,}768$ the ceiling is $\log N = 10.4$ nats ($15.0$ bits); at $N = 16{,}384$ it is $9.7$ nats. If image-caption mutual information were anywhere near $10$ nats, doubling the batch would keep paying. It does not: SigLIP measures ImageNet zero-shot accuracy of $71.6$, $73.2$, $73.2$, $73.2$, $73.1$ at batches of $16$k, $32$k, $64$k, $128$k and $240$k <!-- cite:15 -->[[15]](#ref-15) — flat to within $0.1$ points across a $7.5\times$ range, having saturated by $32$k. So the $\log N$ ceiling is *not* what stops batch scaling in practice: at $32$k the bound still permits $10.4$ nats and the model has stopped improving anyway. The binding constraint is elsewhere — the encoders, the data, and the fact that a caption simply does not carry ten nats about its image. **This is the load-bearing correction to the naive reading of Equation <!-- ref:B-5 -->[(5)](#eq-5)**: the bound explains why large batches help *at first*, and explicitly does not explain the plateau. *[established]*

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-7"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-7 --> The same source contains a sharper caution. On multilingual retrieval the batch-size curve does not merely flatten, it **turns over**: cross-modal average scores of $34.8$, $34.9$, $34.4$, $33.6$, $32.7$ at those same five batch sizes <!-- cite:15 -->[[15]](#ref-15) — a $2.2$-point *decline* from the peak at $32$k, on the identical runs whose ImageNet column was flat. A monotone lower bound on mutual information cannot predict a non-monotone outcome, so whatever drives the multilingual decline lies outside this appendix's theory entirely. Reporting only the ImageNet column would make the bound look predictive; reporting both shows the honest scope of what Equation <!-- ref:B-5 -->[(5)](#eq-5) buys.

<!-- sec:B.4 -->
### <a id="sec-B.4"></a>B.4 From the bound back to CLIP and SigLIP

<a id="p-b4-from-the-bound-back-to-clip-and-siglip-1"></a><!-- para:b4-from-the-bound-back-to-clip-and-siglip-1 --> CLIP instantiates Equation <!-- ref:B-1 -->[(1)](#eq-1) symmetrically — once classifying captions given an image, once images given a caption — because the density ratio $p(x_t\mid x_v)/p(x_t)$ and its transpose $p(x_v\mid x_t)/p(x_v)$ are different quantities, and aligning both directions is what makes the geometry usable for retrieval either way (<!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)). The temperature $\tau$ is the softmax's inverse gain: it scales the cosine similarities into logits, and because CLIP learns it (clipped for stability), the model tunes how sharply the $N$-way classification is peaked. SigLIP's sigmoid loss (<!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)) abandons the softmax of Equation <!-- ref:B-1 -->[(1)](#eq-1) — and with it the explicit $\log N$ MI bound — in exchange for a per-pair objective that factorizes across the batch; it trades the clean information-theoretic interpretation for the memory and communication savings that matter at engineering scale. Both, in the end, are learning the same density ratio; they differ only in how they normalize it.
