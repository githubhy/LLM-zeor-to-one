# Independent re-derivation review — `appendix-j-code-derivations.md`

**Reviewer role.** Adversarial mathematics reviewer under `[opt:MATH-REDERIVE]`
(`.claude/rules/workflow.md`) / `[R-MATHREV]`. I did not author the target.
Phase A below was written **before** the target file was opened.

---

## Phase A — independent derivations (written before reading the target)

### A.1 The unbiased pass@k estimator

**Setup.** For one problem, draw $n$ samples i.i.d. from the model. Each sample passes
the unit tests independently with probability $p$ (the *per-sample success probability*
for that problem). Let $c=\sum_{i=1}^n X_i$ with $X_i\stackrel{iid}\sim\mathrm{Bern}(p)$,
so $c\sim\mathrm{Bin}(n,p)$. Define the estimand

$$\mathrm{pass@}k \;=\; \Pr(\text{at least one of } k \text{ i.i.d. samples passes}) \;=\; 1-(1-p)^k .$$

**Step 1 — a randomised sub-sample.** Let $S$ be a uniformly random $k$-subset of
$\{1,\dots,n\}$ ($n\ge k$), drawn **independently of** $X_{1:n}$. For any *fixed*
$s\subset\{1,\dots,n\}$, $|s|=k$, the vector $(X_i)_{i\in s}$ is exactly $k$ i.i.d.
$\mathrm{Bern}(p)$ variables (that is just a marginal of an i.i.d. product law). Because
this law is the *same* for every fixed $s$, and $S\perp X$, mixing over $S$ gives the
same product law. Hence

$$\Pr\big(\exists i\in S: X_i=1\big) = 1-(1-p)^k = \mathrm{pass@}k. \tag{A.1}$$

*Two independent premises are doing work here:* (i) exchangeability/i.i.d. of $X$, and
(ii) $S\perp X$. Neither alone suffices. And note the subset is drawn **without
replacement** — it is *distributed as* $k$ i.i.d. draws only because the underlying
$X_i$ already are.

**Step 2 — Rao–Blackwellise (this is the step that actually gives unbiasedness).**
Condition on $X_{1:n}$. The number of $k$-subsets containing no passing index is
$\binom{n-c}{k}$, out of $\binom{n}{k}$ total, so

$$\mathbb{E}_S\big[\mathbf 1\{\text{no pass in } S\}\ \big|\ X_{1:n}\big] \;=\; \frac{\binom{n-c}{k}}{\binom{n}{k}} . \tag{A.2}$$

By the tower property together with (A.1),

$$\mathbb{E}_X\!\left[\,1-\frac{\binom{n-c}{k}}{\binom{n}{k}}\,\right] \;=\; \Pr(\exists i\in S: X_i=1) \;=\; 1-(1-p)^k. \tag{A.3}$$

So $\widehat{\mathrm{pass@}k} = 1-\binom{n-c}{k}\big/\binom{n}{k}$ is **exactly unbiased**
for every $n\ge k$ and every $p$. Conventions: $\binom{m}{k}:=0$ for $m<k$, so $c>n-k$
gives $\widehat{\mathrm{pass@}k}=1$.

**Critical note for Phase B.** The distributional fact in Step 1 is *necessary but not
sufficient*. On its own it says only that a random $k$-subset has the right success
probability; it does **not** say that $1-\binom{n-c}{k}/\binom{n}{k}$ is that
probability. The bridge is (A.2) — a combinatorial conditional expectation — plus the
tower property. A derivation that stops after Step 1 has not proven unbiasedness.

**Step 3 — the plug-in estimator is biased DOWNWARD.** Let $\hat p=c/n$ (unbiased for
$p$) and $g(x)=1-(1-x)^k$. Then

$$g'(x)=k(1-x)^{k-1},\qquad g''(x)=-k(k-1)(1-x)^{k-2}\;\le\;0\quad\text{on }[0,1],\ k\ge 2 .$$

So $g$ is **concave**. Jensen gives $\mathbb E[g(\hat p)]\le g(\mathbb E[\hat p])=g(p)=\mathrm{pass@}k$,
with strict inequality whenever $k\ge2$, $0<p<1$, $n\ge2$ (so $\mathrm{Var}(\hat p)>0$ and
$g$ is strictly concave on the support). Therefore

$$\boxed{\ \mathbb{E}\!\left[1-(1-c/n)^k\right] \;<\; \mathrm{pass@}k\ }$$

the plug-in **under**-estimates. (At $k=1$, $g$ is affine and the plug-in is exactly
unbiased.) The sign is fixed by $g''<0$; any text that prints $g''(x)=+k(k-1)(1-x)^{k-2}$
or argues *convexity* has the sign inverted.

*Caveat I will hold the target to:* a **single realisation** where plug-in $<$ unbiased is
not evidence of the bias direction — the bias is a statement about $\mathbb E$. The
direction must come from Jensen, not from one worked pair of numbers.

**Step 4 — the product identity.** Claim
$\dfrac{\binom{n-c}{k}}{\binom{n}{k}}=\prod_{i=n-c+1}^{n}\left(1-\dfrac{k}{i}\right)$.

LHS $=\dfrac{(n-c)!}{k!\,(n-c-k)!}\cdot\dfrac{k!\,(n-k)!}{n!}=\dfrac{(n-c)!\,(n-k)!}{(n-c-k)!\,n!}$.

RHS, re-indexing the numerator by $j=i-k$ (so $j$ runs $n-c-k+1$ to $n-k$):

$$\prod_{i=n-c+1}^{n}\frac{i-k}{i}
=\frac{\prod_{j=n-c-k+1}^{n-k} j}{\prod_{i=n-c+1}^{n} i}
=\frac{(n-k)!/(n-c-k)!}{n!/(n-c)!}
=\frac{(n-c)!\,(n-k)!}{(n-c-k)!\,n!}.$$

**Identical to the LHS.** $\square$

*Degenerate case (worth stating):* if $c>n-k$ then $n-c<k\le n$, so $i=k$ falls inside the
product range and contributes the factor $1-k/k=0$; RHS $=0=$ LHS. The identity is
therefore exact on the whole range $0\le c\le n$, $1\le k\le n$ — no case split needed.
Its purpose is numerical (avoid overflow of $\binom{200}{10}$-scale factorials), not
mathematical.

---

### A.2 Fill-in-the-middle

**The transform.** Split a document $x$ into three contiguous spans
$x=(P,M,S)$ (prefix, middle, suffix) and emit the training sequence (PSM ordering)

$$T \;=\; \langle\mathrm{PRE}\rangle\, P \,\langle\mathrm{SUF}\rangle\, S \,\langle\mathrm{MID}\rangle\, M \,\langle\mathrm{EOT}\rangle .$$

**Why a causal mask is no obstacle.** A causal mask constrains attention by **sequence
position**, not by **document order**. In $T$, every token of $P$ and every token of $S$
occupies a position *strictly earlier* than every token of $M$. So the causal-mask
condition at middle position $t$ is

$$P_\theta\big(m_t \mid \langle\mathrm{PRE}\rangle,P,\langle\mathrm{SUF}\rangle,S,\langle\mathrm{MID}\rangle,m_{<t}\big),$$

which already contains all of $P$ and all of $S$. No architectural change is required;
the *data* was permuted, not the model. This is the whole trick.

**Why the optimum is the true conditional.** The ordinary next-token CE loss restricted to
the middle span is

$$\mathcal L_M(\theta)=\mathbb E_{(P,M,S)}\Big[-\textstyle\sum_t \log q_\theta(m_t\mid \cdot)\Big]
= \mathbb E\big[H(p_\star)\big] + \mathbb E\big[\mathrm{KL}(p_\star \Vert q_\theta)\big],$$

where $p_\star$ is the data conditional. $\mathrm{KL}\ge0$ with equality iff
$q_\theta=p_\star$, so over an *unconstrained* family the population minimiser is
$q_\theta(\cdot)=P(M\mid P,S,\text{format})$, and chaining over $t$ recovers the whole
conditional $P(M\mid P,S)$. Since the permutation $(P,M,S)\mapsto(P,S,M)$ is a
**bijection** on the data, no information is destroyed and the joint law of $(P,M,S)$ is
unchanged; only the factorisation order changes.

**Three honest caveats (I will check whether the target states them).**
1. The optimum is $P(M\mid P,S,\text{sentinels})$ — conditioned on the *FIM format*, not
   the bare document conditional. Equality with the natural conditional holds because the
   sentinel-marked reordering is a bijection, but that is an argument, not a triviality.
2. "The model therefore learns $P(M\mid P,S)$" is a **population-optimum, infinite-capacity,
   unconstrained-family** statement. Real models are finite-capacity and trained on a
   *mixture* of AR and FIM examples (a FIM rate), so this is an idealisation. Any claim that
   this is achieved *exactly* is an overclaim.
3. Middle **length** is not supplied at inference; termination is learned via the
   $\langle\mathrm{EOT}\rangle$ sentinel. That is a real modelling burden, not a free
   consequence of the derivation.

**Expected span lengths under two independent uniform split points.** Let the document
have length $L$ and draw $U_1,U_2\stackrel{iid}\sim\mathrm{Unif}(0,L)$; set
$a=\min(U_1,U_2)$, $b=\max(U_1,U_2)$. Then $|P|=a$, $|M|=b-a$, $|S|=L-b$.
$\mathbb E[a]=L/3$, $\mathbb E[b]=2L/3$, so

$$\mathbb E|P| = \mathbb E|M| = \mathbb E|S| = L/3 .$$

Stronger and worth saying: the three **spacings** of two uniform order statistics on
$[0,L]$ are *exchangeable* — each is marginally $L\cdot\mathrm{Beta}(1,2)$, density
$\tfrac2L(1-x/L)$ on $[0,L]$ — so all three pieces have the *same distribution*, not merely
the same mean. Note the mode of each is $0$: **short middles dominate**, and the mean $L/3$
is a poor summary of a distribution whose density is maximal at zero. (Discretely, drawing
from $\{0,\dots,L\}$ with replacement allows $U_1=U_2$, i.e. an empty middle, with
probability $1/(L+1)$.)

---

### A.3 Group-relative policy optimisation

**Policy-gradient identity.** With $J(\theta)=\mathbb E_{o\sim\pi_\theta}[r(o)]=\sum_o \pi_\theta(o)r(o)$
over the (finite, discrete) set of output sequences,

$$\nabla_\theta J=\sum_o r(o)\,\nabla_\theta\pi_\theta(o)
=\sum_o \pi_\theta(o)\,r(o)\,\nabla_\theta\log\pi_\theta(o)
=\mathbb E_{o\sim\pi_\theta}\!\big[r(o)\nabla_\theta\log\pi_\theta(o)\big].$$

Uses $\nabla\pi=\pi\nabla\log\pi$ (valid where $\pi_\theta(o)>0$; outputs with
$\pi_\theta(o)=0$ contribute $0$ to both sides for a softmax policy, where $\pi_\theta>0$
everywhere anyway) and exchange of $\nabla$ with a finite sum.

**Baseline lemma.** For any $b$ that is **not a function of the sampled $o$** (it may depend
on $\theta$ and on the prompt):

$$\mathbb E_{o\sim\pi_\theta}\big[b\,\nabla\log\pi_\theta(o)\big]
= b\sum_o \pi_\theta(o)\frac{\nabla\pi_\theta(o)}{\pi_\theta(o)}
= b\,\nabla\!\sum_o \pi_\theta(o) = b\,\nabla 1 = 0 .$$

Hence $\mathbb E[(r(o)-b)\nabla\log\pi_\theta(o)]=\nabla J$ for **any** such $b$: variance
changes, bias does not. The load-bearing hypothesis is *independence from the sampled
output*, and it is exactly what GRPO breaks.

**Is the GRPO standardised advantage unbiased? No — and for two separate reasons.**

*(i) The in-group mean alone costs an exact factor $(G-1)/G$.* Let $o_1,\dots,o_G$ be i.i.d.
from $\pi_\theta(\cdot\mid q)$ and $\bar r=\frac1G\sum_j r_j$. Since $\bar r$ **contains**
$r_i$, the baseline lemma does not apply. Compute directly, using
$\mathbb E[\nabla\log\pi_\theta(o_i)]=0$ and independence across $j\neq i$:

$$\mathbb E\big[\bar r\,\nabla\log\pi_\theta(o_i)\big]
=\tfrac1G\,\mathbb E\big[r_i\nabla\log\pi_\theta(o_i)\big]
+\tfrac1G\!\!\sum_{j\neq i}\!\mathbb E[r_j]\,\underbrace{\mathbb E[\nabla\log\pi_\theta(o_i)]}_{=0}
=\tfrac1G\nabla J .$$

Therefore

$$\mathbb E\big[(r_i-\bar r)\nabla\log\pi_\theta(o_i)\big]=\Big(1-\tfrac1G\Big)\nabla J
=\frac{G-1}{G}\,\nabla J . \tag{A.4}$$

So mean-centering with the **in-group** mean is unbiased *only up to the known positive
scalar* $(G-1)/G$ — the **direction is exactly preserved**, and the scalar is absorbed by
the learning rate. Using the **leave-one-out** mean $b_i=\frac1{G-1}\sum_{j\ne i}r_j$
restores exact unbiasedness. This is a precise, quantified statement; "no longer exactly
unbiased" without it under-delivers.

*(ii) Dividing by the group standard deviation is a genuine bias with no scalar fix.*
$\hat\sigma$ is a nonlinear function of the whole group, hence a function of $o_i$ itself,
and is **correlated** with $\nabla\log\pi_\theta(o_i)$. There is no constant $c$ with
$\mathbb E[(r_i-\bar r)/\hat\sigma\cdot\nabla\log\pi_\theta(o_i)]=c\,\nabla J$ in general:
the effective weight on a prompt is $\approx 1/\hat\sigma$, so prompts whose group rewards
happen to have small spread get their gradients amplified. This is a *prompt-difficulty
reweighting*, i.e. the estimator is unbiased for a **different, reward-spread-reweighted
objective**, not for $\nabla J$. (This is the documented "Dr. GRPO" critique of the $\hat\sigma$
term.) A caveat that names only "not exactly unbiased" without separating (i) from (ii) is
too weak; a caveat claiming the *direction* is destroyed by mean-centering would be too
strong.

*(iii) Further bias sources in deployed GRPO,* which a derivation from $J(\theta)$ must not
silently skip: the importance ratio $\pi_\theta/\pi_{\theta_\text{old}}$ with PPO-style
**clipping** (a surrogate, not $\nabla J$), off-policy staleness when $\pi_\text{old}\neq\pi_\theta$,
and the KL penalty (which changes the objective, so its gradient is not meant to be $\nabla J$).

**Degenerate group: all $G$ rewards equal.** Then $r_i-\bar r=0$ for every $i$ **and**
$\hat\sigma=0$: the advantage is $0/0$. Implementations add $\varepsilon$ to the denominator,
giving $A_i=0$ and hence **zero gradient contribution from the entire group** — the group is
wasted compute. This is exactly the all-pass / all-fail group, i.e. problems that are
saturated or hopeless for the current policy; it is the motivation for dynamic sampling
(DAPO) and for difficulty-filtered curricula. Without the $\varepsilon$, the result is NaN,
which poisons the whole batch.

**KL estimator $f(u)=u-\log u-1$, $u=\pi_\text{ref}(o)/\pi_\theta(o)>0$.**

$$f'(u)=1-\tfrac1u,\qquad f''(u)=\tfrac{1}{u^2}>0\ \ \forall u>0 .$$

So $f$ is **strictly convex** on $(0,\infty)$; the unique stationary point is $u=1$
($f'(1)=0$), and $f(1)=1-0-1=0$. A strictly convex function with an interior stationary
point attains its global minimum there, so $f(u)\ge0$ with equality **iff** $u=1$.
Unbiasedness: $\mathbb E_{o\sim\pi_\theta}[u]=\sum_o\pi_\theta\frac{\pi_\text{ref}}{\pi_\theta}=1$, so

$$\mathbb E_{\pi_\theta}[f(u)] = 1-\mathbb E_{\pi_\theta}\!\big[\log\tfrac{\pi_\text{ref}}{\pi_\theta}\big]-1
=\mathbb E_{\pi_\theta}\!\big[\log\tfrac{\pi_\theta}{\pi_\text{ref}}\big]=\mathrm{KL}(\pi_\theta\Vert\pi_\text{ref})\ge0 .$$

So it is an **unbiased, always-non-negative** estimator of the *forward* KL
$\mathrm{KL}(\pi_\theta\Vert\pi_\text{ref})$ — the naive single-sample estimator
$-\log u$ is also unbiased but can be negative, so the guaranteed sign (not the
unbiasedness) is what buys the variance reduction. **The direction of the KL matters** and
must be stated: $\mathrm{KL}(\pi_\theta\Vert\pi_\text{ref})$, sampling under $\pi_\theta$.
If the target prints $f''(u)=-1/u^2$, $f''(u)=1/u$, or claims $f$ is concave, the sign is
inverted.

---

### A.4 Sample-and-select scaling

With per-sample success probability $p$ and $k$ independent samples, coverage (probability
at least one sample is correct) is $1-(1-p)^k$. Requiring coverage $\ge 1-\delta$:

$$(1-p)^k\le\delta \iff k\log(1-p)\le\log\delta \iff k \;\ge\; \frac{\log\delta}{\log(1-p)}=\frac{\ln(1/\delta)}{-\ln(1-p)}$$

(the inequality flips because $\log(1-p)<0$), so the **integer** requirement is

$$k^\star=\left\lceil \frac{\ln(1/\delta)}{-\ln(1-p)}\right\rceil . \tag{A.5}$$

**Small-$p$ approximation.** $-\ln(1-p)=p+\tfrac{p^2}2+\tfrac{p^3}3+\cdots > p$, so

$$k^\star \;\approx\; \frac{\ln(1/\delta)}{p},\qquad\text{and since } -\ln(1-p)>p,\quad
\frac{\ln(1/\delta)}{p} \;>\; \frac{\ln(1/\delta)}{-\ln(1-p)} .$$

i.e. **the small-$p$ approximation over-estimates $k$** — it is conservative (safe), and the
relative over-estimate is $\approx p/2$. Stating the approximation without its direction is
an omission; stating it as "exact" is wrong.

**Scaling law.** $k^\star=\Theta(1/p)$ — inversely proportional to the per-sample success
rate, and only **logarithmic** in the failure tolerance $1/\delta$. Equivalently, coverage
at budget $k$ is $1-e^{-kp}$ to first order: the *failure* probability decays exponentially
in $k$, so coverage is log-linear in budget and each further halving of $\delta$ costs a
**fixed additive** $\ln 2/p$ samples, not a multiplicative factor. Both framings are the
same fact; the honest statement of "diminishing returns" is the first-order one.

**Numbers to check at $p=0.0147$, $\delta=0.05$.**
$-\ln(1-0.0147)=0.0148091\ldots$; $\ln 20 = 2.995732\ldots$; quotient $=202.29\ldots$
**Ceiling $=203$**, not 202 — at $k=202$ the coverage is $1-(1-0.0147)^{202}\approx0.9498<0.95$.
A target that reports "$k\approx202$" as the number of samples *needed* has taken a floor
where a ceiling is required, and the resulting budget **misses** the stated coverage.
(To be verified numerically in the section below.)

<!-- PHASE-A-END: nothing below this line was written before the target was read -->
