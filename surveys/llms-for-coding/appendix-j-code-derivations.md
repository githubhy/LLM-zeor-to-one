## <a id="sec-J"></a>Code-Specific Derivations

<a id="p-code-specific-derivations-1"></a><!-- para:code-specific-derivations-1 --> **Depth tier:** headline

<a id="p-code-specific-derivations-2"></a><!-- para:code-specific-derivations-2 --> The appendices before this one derive the *general* transformer: what query, key and value are doing, how a toy model composes into a real one, how the block scales from GPT-2 to a frontier mixture-of-experts, and how to read what the trained network has learned. None of that is specific to code. This appendix collects the four pieces of mathematics that *are* — the ones a reader cannot get from a transformer tutorial, because they exist only because code is executable.

<a id="p-code-specific-derivations-3"></a><!-- para:code-specific-derivations-3 --> Each derivation starts from a concrete instance and builds the general statement from it. Every step is shown; where a step is routine algebra it is still written out, with a one-line reason. Where a claim is an interpretation rather than something the source states, it is labelled as such.

<a id="p-code-specific-derivations-4"></a><!-- para:code-specific-derivations-4 --> The four are chosen because each underwrites a claim the body of the survey makes and would otherwise have to assert:

| Derivation | Underwrites | Source |
|---|---|---|
| J.1 The pass@k estimator | every benchmark number in the survey | Codex |
| J.2 Fill-in-the-middle | why a left-to-right model can fill a hole | FIM |
| J.3 Group-relative policy optimization | how tests become a training signal | DeepSeek-R1 |
| J.4 Sample-and-select scaling | why agents sample, and where that stops paying | AlphaCode |

<!-- sec:J.1 -->
### <a id="sec-J.1"></a>J.1 What pass@k Measures, and Why the Obvious Estimator Is Wrong

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-1"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-1 --> **Start with a concrete case.** A model is given one programming problem. We sample 200 candidate programs from it, run the problem's unit tests on each, and find that 20 of them pass. Now someone asks: *if a user had been allowed only 10 attempts, how often would at least one have worked?*

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-2"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-2 --> The tempting answer is to say the model's success rate is $20/200 = 0.1$, so the chance that all 10 attempts fail is $(1 - 0.1)^{10}$, giving

<a id="eq-1"></a><!-- eq:J-1-1 -->
$$
1 - (1 - 0.1)^{10} = 0.6513. \tag{1}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-3"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-3 --> That number is wrong, and this subsection is about why, because the same reasoning error would corrupt every benchmark figure in this survey.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-4"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-4 --> **The quantity being estimated.** Let $p$ be the true probability that one sample drawn from the model solves this problem — a property of the model and the problem, not of our particular 200 draws. Define

<a id="eq-2"></a><!-- eq:J-1-2 -->
$$
\mathrm{pass@}k \;:=\; \Pr(\text{at least one of } k \text{ independent samples is correct}) \;=\; 1 - (1-p)^k . \tag{2}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-5"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-5 --> We do not know $p$. We know $c$, the number of correct samples among $n$ drawn — and $c$ is random, since a different 200 draws would give a different count.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-6"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-6 --> **Why plugging in the empirical rate is biased.** The natural move is to substitute $\hat p = c/n$ into the definition. The trouble is that $\mathrm{pass@}k$ is a *nonlinear* function of $p$, and the expectation of a nonlinear function is not that function of the expectation. Write $g(p) = 1 - (1-p)^k$. Its second derivative is

<a id="eq-3"></a><!-- eq:J-1-3 -->
$$
g''(p) = -k(k-1)(1-p)^{k-2} \;<\; 0 \quad \text{for } k > 1, \tag{3}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-7"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-7 --> so $g$ is strictly concave. Jensen's inequality then gives $\mathbb{E}[g(\hat p)] < g(\mathbb{E}[\hat p]) = g(p)$: the plug-in estimator **systematically underestimates** the true pass@k for every $k > 1$. The bias is not noise that averages away over problems — it is a fixed downward pull, in the same direction on every problem. The Codex paper states the bias and defers the demonstration to its appendix <!-- cite:1 --> [[1]](references.md#ref-1).

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-8"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-8 --> **The unbiased estimator.** Instead of estimating $p$ and transforming it, estimate the target directly. Among our $n$ samples, $c$ are correct and $n-c$ are not. Draw a subset of size $k$ uniformly at random *from the $n$ we already have*. The number of such subsets is $\binom{n}{k}$; the number containing no correct sample is $\binom{n-c}{k}$, since all $k$ must come from the $n-c$ incorrect ones. So

<a id="eq-4"></a><!-- eq:J-1-4 -->
$$
\Pr(\text{the } k\text{-subset contains no correct sample} \mid c) \;=\; \frac{\binom{n-c}{k}}{\binom{n}{k}}, \tag{4}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-9"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-9 --> and the estimator is one minus that <!-- cite:1 --> [[1]](references.md#ref-1):

<a id="eq-5"></a><!-- eq:J-1-5 -->
$$
\widehat{\mathrm{pass@}k} \;=\; 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}} . \tag{5}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-10"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-10 --> **Why this one is unbiased — the step that makes it work.** Assume $n \ge k$, so the subset exists. Equation <!-- ref:J-1-4 -->[(4)](#eq-4) is a statement *conditional on* $c$; to get the unconditional expectation, average it over the randomness in $c$ by the tower property, $\mathbb{E}\big[\Pr(\,\cdot \mid c)\big] = \Pr(\cdot)$. What that unconditional probability equals is the load-bearing step: a uniformly random $k$-subset of $n$ independent draws from the model is itself distributed exactly as $k$ independent draws from the model — picking which $k$ of the samples to look at, at random, tells you nothing about whether they passed. Therefore

<a id="eq-6"></a><!-- eq:J-1-6 -->
$$
\mathbb{E}\!\left[\frac{\binom{n-c}{k}}{\binom{n}{k}}\right] \;=\; \Pr(k \text{ independent samples are all incorrect}) \;=\; (1-p)^k, \tag{6}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-11"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-11 --> and taking one minus both sides gives $\mathbb{E}\big[\widehat{\mathrm{pass@}k}\big] = 1 - (1-p)^k = \mathrm{pass@}k$ exactly. No approximation, no large-$n$ limit. This is the whole argument, and it is why the combinatorial form is preferred to the intuitive one.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-12"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-12 --> **Back to the worked case.** With $n = 200$, $c = 20$, $k = 10$:

| Estimator | Value |
|---|---|
| Plug-in, $1 - (1 - c/n)^k$ | 0.6513 |
| Unbiased, Equation <!-- ref:J-1-5 -->[(5)](#eq-5) | **0.6602** |
| Difference | $+0.0089$ |

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-13"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-13 --> Just under one point of pass@10, always in the same direction. On a leaderboard where systems are separated by one or two points, a survey that mixed the two conventions would be ranking estimator choices rather than models.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-14"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-14 --> **The numerically stable form.** Computing Equation <!-- ref:J-1-5 -->[(5)](#eq-5) as printed is a bad idea. Expanding the binomial coefficients and cancelling the $k!$ terms,

<a id="eq-7"></a><!-- eq:J-1-7 -->
$$
\frac{\binom{n-c}{k}}{\binom{n}{k}} = \frac{(n-c)!\,(n-k)!}{(n-c-k)!\;n!} = \prod_{i=n-c+1}^{n} \frac{i-k}{i} = \prod_{i=n-c+1}^{n}\left(1 - \frac{k}{i}\right), \tag{7}
$$

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-15"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-15 --> which is the product the Codex paper's reference implementation evaluates term by term <!-- cite:1 --> [[1]](references.md#ref-1). The identity is worth checking rather than trusting: at $n = 200$, $c = 20$, $k = 10$ both sides equal $0.339774376237$ to twelve digits.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-16"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-16 --> Two things this form buys. First, headroom against overflow and precision loss as $k$ approaches $n/2$, where the binomial coefficients are largest: $\binom{200}{100} \approx 9.06 \times 10^{58}$ needs 59 significant digits to represent exactly while a double carries about 16. Two honest qualifications. The estimator never forms *that* coefficient — at the paper's own operating point it forms $\binom{200}{10}$ and $\binom{180}{10}$, of 17 and 16 digits, and the naive floating-point ratio there is in fact bit-exact against the product form. So the instability the paper warns of is a statement about the general case, not about the worked configuration. Second, cost: the product runs over $c$ factors rather than $k$, so when few samples pass — the usual case on a hard benchmark — it is also the cheaper expression.

<a id="p-j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-17"></a><!-- para:j1-what-passk-measures-and-why-the-obvious-estimator-is-wrong-17 --> **What pass@k does and does not measure.** Read Equation <!-- ref:J-1-2 -->[(2)](#eq-2) again: it is a statement about *coverage*. It asks whether the model's output distribution places any mass on a correct program, not whether it reliably produces one. A model that solves a problem one time in twenty and a model that solves it every time both score $\mathrm{pass@}100 \approx 1$ (at $p = 0.05$ the value is $0.9941$). Note how fast that intuition degrades if pushed: at $p = 0.01$, $\mathrm{pass@}100$ is only $0.6340$ — the saturation is governed by the product $pk$, so "many samples" only implies "near certain" once $pk \gg 1$. This is why the survey reports the $k$ alongside every figure, and why pass@1 and pass@100 must never be compared across systems as though they were the same measurement. It is also the reason the whole sample-and-select apparatus of J.4 exists: coverage is cheap to buy with more samples, and converting coverage into a *submitted answer* is the part that is hard.

<!-- sec:J.2 -->
### <a id="sec-J.2"></a>J.2 Fill-in-the-Middle: Infilling as a Permuted Autoregressive Factorization

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-1"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-1 --> **The problem, concretely.** An editor needs a completion in the middle of a file. Above the cursor sits

```python
def sum_positive(xs):
    total = 0
```

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-2"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-2 --> and below it sits

```python
    return total
```

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-3"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-3 --> The model must produce the loop that goes between them. It has to condition on text that comes *after* the hole — and a causal decoder is built so that position $t$ can attend only to positions before it. The suffix is structurally invisible.

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-4"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-4 --> **Why the obvious fixes are unattractive.** One could use a bidirectional encoder, but that gives up the generative left-to-right model everything else in the stack depends on. One could train a second, separate infilling model, and pay for it in parameters and serving complexity. Fill-in-the-middle takes a third route: change nothing about the architecture or the loss, and change the *data* instead <!-- cite:5 --> [[5]](references.md#ref-5).

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-5"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-5 --> **The transformation.** Cut the document at two positions chosen uniformly at random, before tokenization, giving three contiguous pieces: prefix, middle, suffix. Then reorder them and mark the joins with three reserved sentinel tokens. In prefix-suffix-middle (PSM) order the training sequence is

<a id="eq-8"></a><!-- eq:J-2-1 -->
$$
z \;=\; \langle\mathrm{PRE}\rangle \;\Vert\; \mathrm{prefix} \;\Vert\; \langle\mathrm{SUF}\rangle \;\Vert\; \mathrm{suffix} \;\Vert\; \langle\mathrm{MID}\rangle \;\Vert\; \mathrm{middle}, \tag{8}
$$

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-6"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-6 --> where $\Vert$ denotes concatenation <!-- cite:5 --> [[5]](references.md#ref-5). At inference the model is fed everything up to and including $\langle\mathrm{MID}\rangle$ and samples until it emits an end-of-text token, which is its way of saying the prefix and suffix have been joined.

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-7"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-7 --> **The derivation.** The training objective is untouched — ordinary next-token cross-entropy, applied to $z$:

<a id="eq-9"></a><!-- eq:J-2-2 -->
$$
\log p(z) \;=\; \sum_{t} \log p_\theta\!\left(z_t \mid z_{<t}\right). \tag{9}
$$

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-8"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-8 --> Now look at which factors correspond to the middle tokens. Write the middle as $m_1,\dots,m_M$. In the order fixed by Equation <!-- ref:J-2-1 -->[(8)](#eq-8), every token of the prefix *and* every token of the suffix appears earlier in $z$ than $m_1$. So the factor for $m_j$ is

<a id="eq-10"></a><!-- eq:J-2-3 -->
$$
p_\theta\!\left(m_j \mid \mathrm{prefix},\, \mathrm{suffix},\, m_{<j}\right), \tag{10}
$$

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-9"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-9 --> and multiplying these over $j$ gives exactly $p_\theta(\mathrm{middle} \mid \mathrm{prefix}, \mathrm{suffix})$ — the infilling distribution we wanted. The causal mask was never violated: the suffix is in the *left* context of the middle, because the permutation put it there. Nothing was added to the model; the conditional we need is a sub-product of the ordinary chain rule applied to a reordered sequence.

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-10"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-10 --> **Where the "free" comes from.** The loss is kept on all three sections, not masked to the middle alone — the paper is explicit that this is deliberate, and that it is why the autoregressive learning signal does not shrink <!-- cite:5 --> [[5]](references.md#ref-5). Reading Equation <!-- ref:J-2-2 -->[(9)](#eq-9) again with that in mind: the factors for the *prefix* tokens are $p_\theta(\mathrm{prefix}_j \mid \mathrm{prefix}_{<j})$, which is precisely ordinary left-to-right language modelling, unchanged. (The *suffix* factors are not — they condition on the prefix with the middle excised, which is a gap-conditioned continuation rather than a plain one, and is a genuinely different task.) So the permuted objective *contains* an ordinary autoregressive objective as a sub-task rather than competing with it. *(This last reading is an interpretation of the mechanism; the paper states the design choice and reports the empirical result, and does not present this chain-rule argument for why the result holds.)*

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-11"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-11 --> Empirically the claim is strong and bounded. Across eight models from 50M to 6.9B parameters trained on 100B tokens, a 50% FIM rate leaves the left-to-right loss curve superimposed on the 0% baseline, and a sweep of FIM rates finds no degradation up to 90% — but a clear degradation at 100% <!-- cite:5 --> [[5]](references.md#ref-5). The endpoint is the interesting part: at a rate of exactly 1 the model never sees an untransformed document, and the free lunch ends. The paper reports this boundary; it does not isolate the mechanism, and neither should a reader.

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-12"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-12 --> **Two details that matter in practice.** First, the split is uniform, so each of the three pieces is one third of the document in expectation — the lengths are the spacings induced by two uniform order statistics, and the three spacings are exchangeable, so each has mean $L/3$ for a document of length $L$. Second, there is a second ordering, suffix-prefix-middle (SPM), motivated by cache reuse: in SPM the suffix is encoded first, so appending to the prefix does not invalidate the cached keys and values for the suffix <!-- cite:5 --> [[5]](references.md#ref-5). The variant actually used places the sentinels so that the prefix and middle form one unbroken token run, which makes an SPM example indistinguishable from a PSM example whose sampled prefix happened to be empty — maximizing transfer between the two modes rather than splitting the model's capacity across them.

<a id="p-j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-13"></a><!-- para:j2-fill-in-the-middle-infilling-as-a-permuted-autoregressive-factorization-13 --> **The generalization.** InCoder's causal-masking objective is the same idea with the single hole replaced by several: a Poisson-distributed number of spans are each replaced in place by a numbered sentinel and moved to the end, so one sentinel marks the deletion site on first occurrence and the start of the moved span on its second <!-- cite:4 --> [[4]](references.md#ref-4). Fill-in-the-middle is the one-span case. The survey body treats which models adopted which; the mathematics is the permutation argument above, unchanged.

<!-- sec:J.3 -->
### <a id="sec-J.3"></a>J.3 Group-Relative Policy Optimization: Turning Tests Into a Gradient

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-1"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-1 --> **The setting.** A unit-test suite gives a verdict on a generated program that is cheap, automatic, and not a matter of taste. That makes code the natural home for reinforcement learning with a checkable reward, and it is why the alignment story for code diverges from the preference-learning story for chat. What follows derives the optimizer that frontier code-reasoning models are trained with, from the policy-gradient identity up.

<!-- sec:J.3-step-1 -->
<a id="sec-J.3-step-1"></a><a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-2"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-2 --> **Step 1 — the objective and its gradient.** Let $\pi_\theta(o \mid q)$ be the probability the model assigns to producing output $o$ for question $q$, and $r(o)$ the scalar reward. We want to maximize $J(\theta) = \mathbb{E}_{o \sim \pi_\theta}[r(o)]$. Differentiating and using $\nabla \pi_\theta = \pi_\theta \nabla \log \pi_\theta$,

<a id="eq-11"></a><!-- eq:J-3-1 -->
$$
\nabla_\theta J(\theta) \;=\; \sum_o r(o)\,\nabla_\theta \pi_\theta(o \mid q) \;=\; \mathbb{E}_{o \sim \pi_\theta}\!\left[r(o)\,\nabla_\theta \log \pi_\theta(o \mid q)\right]. \tag{11}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-3"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-3 --> This is estimable from samples, but its variance is severe: the reward multiplies the whole score function, so a run of high-reward samples pushes hard in one direction regardless of whether those samples were better *than usual*.

<!-- sec:J.3-step-2 -->
<a id="sec-J.3-step-2"></a><a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-4"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-4 --> **Step 2 — the baseline lemma, which is what makes everything else legal.** For any quantity $b$ that does not depend on $o$,

<a id="eq-12"></a><!-- eq:J-3-2 -->
$$
\mathbb{E}_{o \sim \pi_\theta}\!\left[b\,\nabla_\theta \log \pi_\theta(o \mid q)\right] \;=\; b \sum_o \pi_\theta(o \mid q)\,\frac{\nabla_\theta \pi_\theta(o \mid q)}{\pi_\theta(o \mid q)} \;=\; b\,\nabla_\theta \sum_o \pi_\theta(o \mid q) \;=\; b\,\nabla_\theta 1 \;=\; 0. \tag{12}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-5"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-5 --> The sum of the probabilities is identically one, so its gradient is zero. Therefore subtracting *any* such $b$ from the reward changes nothing in expectation:

<a id="eq-13"></a><!-- eq:J-3-3 -->
$$
\mathbb{E}\!\left[(r(o) - b)\,\nabla_\theta \log \pi_\theta(o \mid q)\right] \;=\; \nabla_\theta J(\theta). \tag{13}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-6"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-6 --> We are free to choose $b$, and the useful choice is one close to the typical reward for this question, so that $r - b$ measures *better or worse than usual* rather than *good or bad in absolute terms*. That difference is the advantage.

<!-- sec:J.3-step-3 -->
<a id="sec-J.3-step-3"></a><a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-7"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-7 --> **Step 3 — how PPO pays for its baseline, and what GRPO does instead.** The standard route trains a second network, a value function, to predict the expected reward and uses it as $b$. That network is typically the size of the policy, and it must itself be trained and kept current. Group-relative policy optimization removes it by exploiting a fact peculiar to this setting: we can sample the *same question* many times, cheaply. Draw a group of $G$ outputs $o_1,\dots,o_G$ for one question $q$, score them all, and use the group's own empirical mean as the baseline. Because every member of the group shares the same $q$, that mean is an unbiased Monte-Carlo estimate of the ideal per-question baseline $\mathbb{E}[r \mid q]$ — the thing the value network was being trained to approximate — obtained with no extra parameters at all.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-8"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-8 --> GRPO then standardizes rather than merely centring, dividing by the group's standard deviation <!-- cite:25 --> [[25]](references.md#ref-25):

<a id="eq-14"></a><!-- eq:J-3-4 -->
$$
A_i \;=\; \frac{r_i - \mathrm{mean}(\{r_1,\dots,r_G\})}{\mathrm{std}(\{r_1,\dots,r_G\})}. \tag{14}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-9"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-9 --> **A caveat worth stating, and it is not the obvious one.** It is tempting to say the lemma licenses subtracting the mean and only the division by the standard deviation is a heuristic. That is backwards about the more subtle half. The lemma's single hypothesis is that $b$ does **not** depend on the sampled output $o_i$ — and the group mean *contains* $r_i$, so it does. Working the expectation through, the cross terms for $j \neq i$ vanish because $r_j$ is independent of $o_i$ and $\mathbb{E}[\nabla \log \pi_\theta(o_i)] = 0$, leaving

<a id="eq-15"></a><!-- eq:J-3-8 -->
$$
\mathbb{E}\!\left[\left(r_i - \tfrac{1}{G}\textstyle\sum_j r_j\right)\nabla_\theta \log \pi_\theta(o_i \mid q)\right] = \frac{G-1}{G}\,\nabla_\theta J(\theta). \tag{15}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-10"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-10 --> So in-group centring is **not** exactly unbiased either: it shrinks the gradient by a factor $(G-1)/G$ — $0.5$ at $G=2$, $0.875$ at $G=8$ — which a Monte-Carlo check reproduces to three decimals. This is benign in practice: the factor is a positive scalar, so the gradient *direction* is preserved and the magnitude is absorbed by the learning rate. A leave-one-out mean, excluding $r_i$ from its own baseline, would be exactly licensed. Dividing by the standard deviation is a second, separate departure, and for the same reason — a random denominator correlated with the numerator. Both are sound engineering; neither is what the lemma proves.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-11"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-11 --> **The full objective, as published.** Assembling the pieces with PPO-style clipping on the importance ratio and a KL penalty toward a reference policy <!-- cite:25 --> [[25]](references.md#ref-25):

<a id="eq-16"></a><!-- eq:J-3-5 -->
$$
\mathcal{J}(\theta) = \mathbb{E}\Bigg[\frac{1}{G}\sum_{i=1}^{G} \min\!\Big(\rho_i A_i,\; \mathrm{clip}(\rho_i,\, 1-\varepsilon,\, 1+\varepsilon)\,A_i\Big) - \beta\, \mathbb{D}_{\mathrm{KL}}\!\left(\pi_\theta \,\Vert\, \pi_{\mathrm{ref}}\right)\Bigg], \qquad \rho_i = \frac{\pi_\theta(o_i \mid q)}{\pi_{\theta_{\mathrm{old}}}(o_i \mid q)} . \tag{16}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-12"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-12 --> The clipping bounds how far one update may move the policy from the one that generated the samples; without it, a large importance ratio on a high-advantage sample would take an arbitrarily large step off-distribution.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-13"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-13 --> **The KL term is not the textbook one.** The penalty is written <!-- cite:25 --> [[25]](references.md#ref-25)

<a id="eq-17"></a><!-- eq:J-3-6 -->
$$
\mathbb{D}_{\mathrm{KL}}\!\left(\pi_\theta \,\Vert\, \pi_{\mathrm{ref}}\right) = \frac{\pi_{\mathrm{ref}}(o_i \mid q)}{\pi_\theta(o_i \mid q)} - \log \frac{\pi_{\mathrm{ref}}(o_i \mid q)}{\pi_\theta(o_i \mid q)} - 1 . \tag{17}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-14"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-14 --> Setting $u = \pi_{\mathrm{ref}}/\pi_\theta$, this is $f(u) = u - \log u - 1$. It is worth confirming the property that makes it usable as a penalty: $f(1) = 0$, $f'(u) = 1 - 1/u$ vanishes only at $u = 1$, and $f''(u) = 1/u^2 > 0$, so $f$ is strictly convex with a unique minimum of zero at $u = 1$. The estimator is therefore non-negative sample by sample, unlike the naive log-ratio estimator, which is negative about half the time and needs many samples before its average is informative.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-15"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-15 --> Non-negativity alone would not make it a *KL* estimator, so it is worth closing that step too. Taking the expectation under $\pi_\theta$, the first term is $\mathbb{E}_{\pi_\theta}[\pi_{\mathrm{ref}}/\pi_\theta] = \sum_o \pi_{\mathrm{ref}}(o) = 1$ because $\pi_{\mathrm{ref}}$ is a distribution, and the second is $\mathbb{E}_{\pi_\theta}[\log(\pi_{\mathrm{ref}}/\pi_\theta)] = -\mathbb{D}_{\mathrm{KL}}(\pi_\theta \Vert \pi_{\mathrm{ref}})$ by definition. So $\mathbb{E}[f(u)] = 1 + \mathbb{D}_{\mathrm{KL}} - 1 = \mathbb{D}_{\mathrm{KL}}(\pi_\theta \Vert \pi_{\mathrm{ref}})$ exactly — it is an unbiased estimator of the very quantity it is named for, and its non-negativity is a bonus property rather than its justification.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-16"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-16 --> **Worked example.** Take $G = 4$ and a pass-or-fail unit-test reward, with two of the four sampled programs passing: $r = (1, 0, 1, 0)$. The mean is $0.5$ and the standard deviation is $0.5$ — **population** standard deviation, dividing by $G$ rather than $G-1$; the sample form would give $0.577$ and advantages $\pm 0.866$, so the basis has to be declared rather than assumed. With the population basis,

<a id="eq-18"></a><!-- eq:J-3-7 -->
$$
A = (1,\, -1,\, 1,\, -1). \tag{18}
$$

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-17"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-17 --> The two passing programs are reinforced and the two failing ones suppressed, with equal magnitude. Note what did *not* happen: no value network was consulted, and no human preference was involved. The compiler and the test suite produced the entire signal.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-18"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-18 --> **The failure mode this exposes.** Suppose all four programs pass, so $r = (1,1,1,1)$. Then the standard deviation is zero and Equation <!-- ref:J-3-4 -->[(14)](#eq-14) is $0/0$ — undefined. The same happens when all four fail. A question that is uniformly easy or uniformly hard for the current policy contributes **no gradient at all**. This is not an implementation wart; it is intrinsic to a group-relative baseline, and it means the effective training signal comes only from questions the model currently solves *sometimes*. Curriculum and difficulty filtering are therefore not refinements of this method but preconditions for it.

<a id="p-j3-group-relative-policy-optimization-turning-tests-into-a-gradient-19"></a><!-- para:j3-group-relative-policy-optimization-turning-tests-into-a-gradient-19 --> **Why the reward is a rule and not a network.** The natural alternative is to train a reward model on human judgments, as in preference-based alignment. DeepSeek-R1 declines to, and says why: neural reward models are susceptible to reward hacking under large-scale reinforcement learning, and retraining them adds cost and complexity <!-- cite:25 --> [[25]](references.md#ref-25). A compiler cannot be flattered. That is the whole argument for code as the setting where this style of training works — and, as the body of the survey records, the verifier being a *program* rather than a person moves the reward-hacking problem rather than eliminating it: a test suite can still be gamed.

<!-- sec:J.4 -->
### <a id="sec-J.4"></a>J.4 Sample-and-Select: Why Coverage Is Cheap and Selection Is Not

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-1"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-1 --> **The observation to explain.** AlphaCode draws up to a million samples per problem, discards roughly 99% of them using the problem's own public example tests, clusters what survives by behaviour on generated inputs, and submits one representative per cluster <!-- cite:40 --> [[40]](references.md#ref-40). That is an enormous amount of machinery in service of ten submissions. This subsection derives why the sampling works, and then why the machinery is needed.

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-2"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-2 --> **Coverage grows fast — the easy half.** From J.1, if each sample is independently correct with probability $p$, then drawing $k$ of them yields $\mathrm{pass@}k = 1 - (1-p)^k$. For small $p$ use $\log(1-p) \approx -p$:

<a id="eq-19"></a><!-- eq:J-4-1 -->
$$
\mathrm{pass@}k = 1 - e^{k \log(1-p)} \approx 1 - e^{-pk}. \tag{19}
$$

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-3"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-3 --> The curve is governed entirely by the product $pk$. It is flat until $k \approx 1/p$, turns over there, and saturates soon after. A caution about a common misreading, including an earlier draft of this appendix: a *single* problem's curve is a saturating sigmoid in $\log k$, not a straight line — its successive decade increments run $+0.029$, $+0.094$, $+0.221$, $+0.414$, $+0.216$, $+0.012$. The log-linearity that AlphaCode reports is an aggregate over a *population* of problems with widely differing $p$, where each decade of budget brings a new band of difficulty into range. That is a mixture effect, and it is a different mechanism from the single-problem curve derived here. Inverting for a target coverage $1 - \delta$:

<a id="eq-20"></a><!-- eq:J-4-2 -->
$$
k \;\ge\; \frac{\log \delta}{\log(1-p)} \;\approx\; \frac{1}{p}\log\frac{1}{\delta}. \tag{20}
$$

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-4"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-4 --> The cost is linear in $1/p$, so it is *exponential in problem difficulty* measured on a log-probability scale. Every factor of ten harder costs a factor of ten more samples.

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-5"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-5 --> **Put AlphaCode's own numbers in.** On the problems its 41B model solved at all, the average probability that a single sample passed the example tests was 1.47% <!-- cite:40 --> [[40]](references.md#ref-40). Equation <!-- ref:J-4-2 -->[(20)](#eq-20) with $\delta = 0.05$ gives $k \ge 202.29$, i.e. **203** samples (the bound is a $\ge$, and $k = 202$ reaches $0.94978$, just short). That is affordable. **Two caveats on that substitution, both of which this appendix elsewhere warns against.** First, $1.47\%$ is an *average* over problems, and $1 - (1-p)^k$ is concave in $p$, so substituting the mean understates the mean coverage — the same Jensen step <!-- secref:J.1 -->[§J.1](#sec-J.1) spends several paragraphs on, committed here in the other direction. Second, the reported rate is the probability of passing the *example* tests, not of being correct, so the figure bounds coverage of a weaker event than solving. Read $203$ as an order-of-magnitude anchor, not a budget. The reason the system draws a million instead is the other 99% of the difficulty distribution — on roughly one problem in ten, no sample from any model passes the example tests at all <!-- cite:40 --> [[40]](references.md#ref-40), and for those $p$ is so small that Equation <!-- ref:J-4-2 -->[(20)](#eq-20) prices coverage out of reach entirely.

| $p$ | $k$ for 95% coverage |
|---|---|
| 0.5 | 4.3 |
| 0.1 | 28.4 |
| 0.0147 | 202 |
| 0.01 | 298 |
| 0.001 | 2994 |

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-6"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-6 --> **Now the hard half.** Equation <!-- ref:J-4-1 -->[(19)](#eq-19) quietly assumes an *oracle*: pass@k counts a problem as solved if any of the $k$ samples is correct, which is only a legitimate score if you may submit all $k$. Real contests, and real users, permit a handful of attempts. AlphaCode reports a second metric, 10@k — draw $k$, submit only 10 — and the gap between the two curves is precisely the cost of not having an oracle. The paper's own summary of the shape is that solve rates scale log-linearly with more samples, with the 10@k curve bending down at high sample budgets <!-- cite:40 --> [[40]](references.md#ref-40). Coverage keeps improving; the ability to *find* the covered solution does not keep up. Beyond some budget the binding constraint stops being search and starts being selection.

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-7"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-7 --> **Selection is measurably unreliable when the verifier is the model itself.** The cheapest way to pick a candidate is to have the model write tests and keep the programs that pass them. Reflexion measures how often that endorsement is wrong — a program passes every self-written test and is still incorrect — and finds 16.3% on MBPP against 1.4% on HumanEval, the same method and the same base model <!-- cite:24 --> [[24]](references.md#ref-24). An order of magnitude, driven by the benchmark rather than the technique. The consequence is not merely a smaller gain: on MBPP, pass@1 moves from 0.80 to 0.77 — self-debugging against a flaky verifier lands *below* the baseline that did nothing <!-- cite:24 --> [[24]](references.md#ref-24). A generator and a verifier drawn from the same model share blind spots, and where a benchmark's tests are thin, that correlation is what the selection step is actually measuring.

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-8"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-8 --> This is the mechanism behind a general caution the survey applies throughout: an execution signal is only as good as the tests behind it, and "it passed the tests" is a claim about the tests as much as about the code.

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-9"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-9 --> **Where this leaves the machinery.** Two results bound the answer. Under the 2024 International Olympiad in Informatics rules, a hand-engineered pipeline — subtask decomposition, ten thousand samples per subtask, clustering on model-generated tests, a learned reranker — scored 213 points, where random selection under the same 50-submission cap scored 156; the selection apparatus was worth roughly 60 points <!-- cite:26 --> [[26]](references.md#ref-26). Against that, a later model evaluated under the *same* 50-submission limit, using only a simple top-score selection over 1,024 samples and none of the hand-built machinery, scored 395.64 — above the gold-medal threshold <!-- cite:26 --> [[26]](references.md#ref-26). The reported explanation is that the strategies the pipeline had to be given, such as writing brute-force implementations to cross-check an optimized one, emerged from end-to-end reinforcement learning instead <!-- cite:26 --> [[26]](references.md#ref-26).

<a id="p-j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-10"></a><!-- para:j4-sample-and-select-why-coverage-is-cheap-and-selection-is-not-10 --> Read together with J.3, this is the survey's central dynamic in miniature. Sampling buys coverage on a schedule set by Equation <!-- ref:J-4-2 -->[(20)](#eq-20). Converting coverage into a submission requires a verifier, and a verifier built from the same model inherits its blind spots. Scaffolding is the engineering response to that gap — and as the underlying model improves, the gap it was built to cover closes, and the scaffolding thins.
