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

> <a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-4"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-4 --> **Note — the conclusion is a theorem, but the chain in Equation <!-- ref:B-4 -->[(4)](#eq-4) does not establish it, and the broken link is the $\approx$, not the $\ge$.** Two things are worth separating here, because the obvious complaint is the wrong one. *The $\ge$ is fine.* Read pointwise it would require $r \le 1$, which fails for individual pairs — but it is never applied pointwise. Under the expectation it actually sits in, put $u = -\log r$ and it becomes $\phi(u) = \log(e^{u} + N - 1) - \log N$, a log-sum-exp and hence **convex**, increasing, with $\phi(0) = 0$; since $\mathbb{E}[u] = I(x_v;x_t) \ge 0$, Jensen runs the helpful way and $\mathbb{E}\phi(u) \ge \phi(I) \ge 0$ unconditionally. *The $\approx$ is not fine.* Replacing the sum over negatives by its mean is also a Jensen step, but on $\log(1 + rS)$, which is **concave** in $S$ — so it yields $\mathcal{L}^{\star} \le \mathbb{E}\log[1 + r(N-1)]$, an **upper** bound at exactly the point the argument needs a lower one. A chain of the form $A \lesssim B \ge C$ establishes nothing about $A$ versus $C$, so Equation <!-- ref:B-4 -->[(4)](#eq-4) as written does not prove Equation <!-- ref:B-5 -->[(5)](#eq-5), however large $N$ becomes — the looseness the source flags ("the approximation sharpens as $N$ grows") is about magnitude, and the defect is about **direction**, which no amount of $N$ repairs. Equation <!-- ref:B-5 -->[(5)](#eq-5) is nonetheless true; it is a standard result reachable by routes that avoid the substitution entirely. So the honest reading is that the *bound* is safe to use and the *printed derivation of it* is not a proof. *[established]*

> <a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-5"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-5 --> **Why this is worth the space.** A first pass over this derivation — mine included — flags the bare $\ge$, because an inequality asserted without its condition looks like the defect. Patching it (bounding the pointwise loss by $\log\frac{N}{N-1}$ and retreating to $I \ge \log(N-1) - \mathcal{L}$) produces a weaker claim that is *also* unnecessary, while the step that actually breaks the chain sits one line above and reads as routine. **The lesson is directional: in a chain proving a lower bound, every step must be a lower bound, and an $\approx$ is not exempt from carrying a direction.** Checking the conspicuous step and stopping is how a sound-looking audit misses the real one.

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-6"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-6 --> Two consequences follow directly, and both were visible empirically in <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4). First, the bound is **tighter as $N$ grows**: more in-batch negatives means $\log N$ is larger and the gap the loss must close is a better estimate of the true MI — the precise, information-theoretic reason CLIP trains at a batch of $32{,}768$ and SigLIP studies batch size as a first-class variable (<!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)). The matched-filter intuition of <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) and this bound are the same statement in two languages: more interferers to reject sharpens the learned discrimination *and* tightens the MI estimate. Second, the bound **caps what one batch can certify** — $\log N$ nats is the ceiling of an $N$-way classification, no matter how good the encoder — so returns to batch size must diminish once $\log N$ exceeds the true $I$.

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-7"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-7 --> **Worked example — reading the ceiling, and the arm it applies to.** At $N = 32{,}768$ the ceiling is $\log N = 10.4$ nats ($15.0$ bits exactly); at $N = 16{,}384$ it is $9.7$ nats. Equation <!-- ref:B-5 -->[(5)](#eq-5) predicts that returns to batch size diminish once $\log N$ comfortably exceeds the true $I$, since past that point extra negatives certify information the pair does not contain — and the measured curves do plateau. The temptation is to close the loop by quoting a saturation point, and it must be resisted for a reason internal to this appendix: **the batch-size curve most often cited is SigLIP's, and SigLIP's sigmoid objective is exactly the one <!-- secref:B.4 -->[§B.4](#sec-B.4) says abandons this bound.** Using it here would argue about a $\log N$ ceiling from the arm that has no $\log N$ ceiling. On the arm the bound does govern, the same source reports that "the softmax loss required 98k for optimal performance" <!-- cite:15 -->[[15]](#ref-15) — i.e. softmax kept paying for batch well past where sigmoid stopped, which is the *opposite* of a story in which the ceiling stops mattering early.

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-8"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-8 --> Two further cautions keep this honest. Comparing a bound in **nats** against a plateau in **accuracy points** is a basis mismatch: Equation <!-- ref:B-5 -->[(5)](#eq-5) constrains $\log N - \mathcal{L}_{\mathrm{NCE}}$, and none of these reports states $\mathcal{L}_{\mathrm{NCE}}$, so whether the bound is tight or slack at any batch size is simply **not measured** by an accuracy curve. And the ceiling argument is a claim about what a batch can *certify*, not about what a model can *achieve* — a plateau is consistent with the ceiling binding and with it being slack, and distinguishing them needs the loss. The defensible statement is therefore the conditional one: the bound predicts diminishing returns, the softmax arm is the arm it applies to, and confirming it would require reporting $\mathcal{L}_{\mathrm{NCE}}$ alongside accuracy — which the literature generally does not. *[reported]*

<a id="p-b3-the-mutual-information-lower-bound-and-why-batch-size-matters-9"></a><!-- para:b3-the-mutual-information-lower-bound-and-why-batch-size-matters-9 --> The same source contains a sharper caution, and this one survives the arm objection above because it needs no bound at all to be interesting. On multilingual retrieval the batch-size curve does not merely flatten, it **turns over**: cross-modal average scores of $34.8$, $34.9$, $34.4$, $33.6$, $32.7$ at batches of $16$k, $32$k, $64$k, $128$k and $240$k <!-- cite:15 -->[[15]](#ref-15) — a $2.2$-point *decline* from a peak at $32$k. Whatever else is true, a monotonically increasing lower bound cannot predict a non-monotone outcome, so the mechanism behind that decline lies outside this appendix's theory entirely. It is the cleanest available reminder that Equation <!-- ref:B-5 -->[(5)](#eq-5) is a statement about what a batch can certify, and not a model of what more batch does to a trained system. *[established]*

<!-- sec:B.4 -->
### <a id="sec-B.4"></a>B.4 From the bound back to CLIP and SigLIP

<a id="p-b4-from-the-bound-back-to-clip-and-siglip-1"></a><!-- para:b4-from-the-bound-back-to-clip-and-siglip-1 --> CLIP instantiates Equation <!-- ref:B-1 -->[(1)](#eq-1) symmetrically — once classifying captions given an image, once images given a caption — because the density ratio $p(x_t\mid x_v)/p(x_t)$ and its transpose $p(x_v\mid x_t)/p(x_v)$ are different quantities, and aligning both directions is what makes the geometry usable for retrieval either way (<!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)). The temperature $\tau$ is the softmax's inverse gain: it scales the cosine similarities into logits, and because CLIP learns it (clipped for stability), the model tunes how sharply the $N$-way classification is peaked. SigLIP's sigmoid loss (<!-- secxref:2.5 -->[§2.5](fundamentals.md#sec-2.5)) abandons the softmax of Equation <!-- ref:B-1 -->[(1)](#eq-1) — and with it the explicit $\log N$ MI bound — in exchange for a per-pair objective that factorizes across the batch; it trades the clean information-theoretic interpretation for the memory and communication savings that matter at engineering scale. Both, in the end, are learning the same density ratio; they differ only in how they normalize it.
