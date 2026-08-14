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

---

## Phase B — diff against the target

Read `surveys/llms-for-coding/appendix-j-code-derivations.md` (264 lines, 19 tagged
equations). Verdict per equation / per load-bearing claim.

### J.1 — pass@k

| Ref | Claim | Verdict |
|---|---|---|
| Eq (1), line 27 | plug-in gives 0.6513 | **AGREE** — recomputed 0.65132156 |
| Eq (2), line 36 | definition of pass@k | **AGREE** — identical to my A.1 |
| Eq (3), line 45 | second derivative is minus k(k-1)(1-p)^(k-2), negative for k>1 | **AGREE on the sign** — matches my A.1 Step 3 exactly. The printed expression is correct and the concavity conclusion follows. See finding 12 for the p=1 edge |
| line 48 | plug-in "systematically underestimates" | **AGREE on direction** — confirmed by exact binomial expectation at five (n, p, k) points; bias is negative in every one |
| Eq (4), line 54 | conditional probability given c | **AGREE** |
| Eq (5), line 61 | the estimator | **AGREE** — but the existence condition n greater than or equal to k is never stated (finding 5) |
| line 64, Eq (6) | the unbiasedness argument | **IMPRECISE** — conclusion correct, argument has a missing step (finding 5) |
| line 71 | "exactly. No approximation, no large-n limit" | **AGREE — this "exact" is earned.** Verified to machine precision (max error 3.8e-15 over five configurations). Do **not** downgrade it |
| lines 77–79 | 0.6513 / 0.6602 / +0.0089 | **AGREE on the arithmetic**, **IMPRECISE on what it shows** (finding 6) |
| line 81 | "always in the same direction" | **AGREE, but unproven as stated** (finding 6) |
| Eq (7), line 87 | the product identity | **AGREE** — proven symbolically in A.1 Step 4 and verified over 4000 random (n, c, k) triples with zero mismatches, including the degenerate branch |
| line 90 | both sides equal 0.339774376237 | **AGREE** — reproduced to all twelve printed digits |
| line 92 | the numerical-stability rationale | **DISAGREE** (finding 3) |
| line 92 | product runs over c factors, cheaper when few pass | **AGREE in general**, but false at the appendix's own worked point (finding 13) |
| line 94 | "solves one time in a hundred ... both score pass@100 approximately 1" | **DISAGREE — the number is wrong** (finding 1) |

### J.2 — fill-in-the-middle

| Ref | Claim | Verdict |
|---|---|---|
| Eq (8), line 120 | PSM ordering | **AGREE** |
| Eq (9), line 129 | next-token factorization | **AGREE** — notation nit at finding 14 |
| Eq (10), line 136 | the middle factor conditions on prefix and suffix | **AGREE** — this is the causal-mask argument and it is right |
| line 139 | "the causal mask was never violated ... a sub-product of the ordinary chain rule" | **AGREE** — correct and well put |
| line 139 | product over j "gives exactly" the infilling distribution | **IMPRECISE** — exact as an identity about the model's own factorization, but the step from *the loss* to *the model learning the data conditional* is absent (finding 7) |
| line 141 | suffix factors are "precisely a left-to-right continuation task on the prefix" | **DISAGREE** (finding 2) |
| line 141 | the interpretation label | **AGREE — the label is in the right place.** That claim genuinely is unsourced interpretation. Its *content* is nonetheless wrong (finding 2) |
| line 143 | FIM-rate empirics (50M–6.9B, 100B tokens, 50%/90%/100%) | **UNCHECKED** — external sourcing, outside a math review; see "Not checked" below |
| line 145 | each piece is one third in expectation, spacings of two uniform order statistics, exchangeable | **AGREE** — matches my A.2 derivation including the exchangeability observation. This is the best-argued sentence in J.2 |
| line 145 | SPM cache-reuse rationale | **AGREE on the logic** — suffix first means prefix edits do not invalidate suffix KV |
| line 147 | InCoder generalization | **UNCHECKED** — external sourcing |

### J.3 — GRPO

| Ref | Claim | Verdict |
|---|---|---|
| Eq (11), line 159 | policy-gradient identity | **AGREE** — identical to my A.3 |
| Eq (12), line 169 | baseline lemma | **AGREE** — identical to my A.3, including the "gradient of 1 is 0" step |
| Eq (13), line 176 | subtracting any such b is unbiased | **AGREE** |
| line 182 | group mean is an unbiased MC estimate of E[r given q] | **AGREE as stated** — but it is deployed to imply something false (finding 4) |
| Eq (14), line 188 | standardized advantage | **AGREE** — matches the published outcome-supervision form |
| line 191 | "The baseline lemma licenses subtracting the mean" | **DISAGREE — this is wrong** (finding 4) |
| line 191 | std division is "no longer the exactly-unbiased gradient" | **AGREE on the conclusion**, too weak on the mechanism (finding 8) |
| Eq (15), line 197 | clipped objective with KL penalty | **AGREE** at the sequence level; the published form carries an inner per-token average, so this is a simplification (finding 15) |
| Eq (16), line 206 | KL written as an equality | **IMPRECISE** (finding 9) |
| line 209 | f(1)=0, f'(u)=1-1/u vanishes only at u=1, f''(u)=1/u^2 greater than 0, strictly convex, unique zero minimum | **AGREE — every derivative as printed is correct.** Identical to my A.3. The non-negativity conclusion follows validly |
| line 209 | naive log-ratio estimator is negative about half the time | **AGREE** |
| Eq (17), line 215 | mean 0.5, std 0.5, A = (1, -1, 1, -1) | **AGREE only under population std (ddof = 0)**; the convention is not declared (finding 10) |
| line 220 | all-equal rewards give 0/0, no gradient, intrinsic to a group-relative baseline | **AGREE** — matches my A.3 including the "intrinsic, not an implementation wart" reading. Practical nuance at finding 16 |
| line 222 | rule-vs-network reward rationale | **UNCHECKED** — external sourcing |

### J.4 — sample-and-select

| Ref | Claim | Verdict |
|---|---|---|
| Eq (18), line 233 | pass@k equals 1 minus exp(k log(1-p)), approximately 1 minus exp(-pk) | **AGREE** — first equality exact, approximation correct; direction of the error undisclosed (finding 11) |
| line 236 | "flat until k about 1/p ... which is exactly why solve rate against log k looks like a straight line" | **DISAGREE** (finding 3 companion — see finding 3b) |
| Eq (19), line 240 | k at least log(delta)/log(1-p), approximately (1/p) log(1/delta) | **AGREE** — the inequality direction (flipped by the negative log) is handled correctly |
| line 243 | cost linear in 1/p, exponential in difficulty on a log-probability scale | **AGREE** — with D defined as minus log p, 1/p is exp(D) |
| line 245 | k about 202 for 95% coverage | **DISAGREE — off by one; 202 samples reach 0.9498, not 0.95** (finding 5b) |
| line 245 | p = 1.47% is the example-test pass rate, then used as the correctness probability | **DISAGREE — basis mismatch** (finding 7b) |
| lines 249–253 | the k table | **AGREE on every arithmetic value** (all five reproduced), but they are real-valued bounds presented under an integer-sample heading (finding 5b) |
| line 255 | pass@k assumes an oracle; 10@k gap is the cost of not having one | **AGREE** — this is correct and is the appendix's sharpest observation |
| line 257 | Reflexion 16.3% / 1.4%, pass@1 0.80 to 0.77 | **UNCHECKED** — external sourcing |
| line 261 | IOI 213 vs 156, 395.64 | **UNCHECKED** — external sourcing; 213 minus 156 equals 57, consistent with "roughly 60 points" |

---

## Findings

### 1. `high` — pass@100 for a one-in-a-hundred model is 0.63, not approximately 1

> "A model that solves a problem one time in a hundred and a model that solves it every
> time both score $\mathrm{pass@}100 \approx 1$." (line 94)

With $p = 0.01$, $\mathrm{pass@}100 = 1 - 0.99^{100} = 0.6340$. The two models score
**0.63 and 1.00** — they are not close, and the sentence is the pedagogical payload of the
"what pass@k does not measure" paragraph. The point being made is correct and important;
the instance chosen refutes it.

**Correction.** Either raise the budget — with $p = 0.01$, $\mathrm{pass@}1000 = 0.99996$ —
or lower the difficulty: at $p = 0.05$, $\mathrm{pass@}100 = 0.9941$. Suggested rewrite:
"A model that solves a problem one time in twenty and a model that solves it every time
both score $\mathrm{pass@}100 > 0.99$."

### 2. `med` — the FIM sub-task claim names the wrong factors, and "precisely" is false

> "the factors for the *suffix* tokens are $p_\theta(\mathrm{suffix}_j \mid \mathrm{prefix}, \mathrm{suffix}_{<j})$,
> which is precisely a left-to-right continuation task on the prefix." (line 141)

It is **not** that task. In the original document the token following
$(\mathrm{prefix} \Vert \mathrm{suffix}_{<j})$ is not $\mathrm{suffix}_j$ — the *middle*
sits between them. So the suffix factors are next-token prediction on a **gapped**
document, which is a different (and strictly harder, differently-distributed) task from
ordinary left-to-right continuation.

The factors that *do* satisfy the claim are the **prefix** factors: each prefix token is
conditioned only on earlier prefix tokens, which is verbatim the ordinary autoregressive
task on the untransformed document. The paragraph's conclusion ("the permuted objective
contains an ordinary autoregressive objective as a sub-task") therefore survives — but it
is rescued by the factors the text does not cite, not the ones it does.

**Correction.** Point at the prefix factors, and describe the suffix factors honestly as
gap-conditioned continuation. The "interpretation" label stays; it is correctly placed.

### 3. `med` — the numerical-stability argument cites a coefficient the computation never forms, and at the worked point the naive route is exact

> "$\binom{200}{100} \approx 9.06 \times 10^{58}$ needs 59 significant digits to represent
> exactly, while a double carries about 16, so forming the ratio of two such integers in
> floating point discards information before the division happens." (line 92)

Equation (5) at $n = 200$, $k = 10$ forms $\binom{200}{10} = 2.245 \times 10^{16}$ and
$\binom{180}{10} = 7.628 \times 10^{15}$ — **17 and 16 digits**, not 59.
$\binom{200}{100}$ is the largest coefficient in that row and is never computed by the
estimator. Worse for the argument: I evaluated the naive float ratio at exactly the
appendix's operating point and its relative error against the exact rational is
**0.0** — bit-identical. The stated hazard does not bite where the appendix says it does.

The underlying concern is real but is **overflow at large $k$ near $n/2$**, not precision
loss at $k = 10$. As printed the paragraph is an overclaim propped up by a substituted
number.

**Correction.** Either state the regime where it bites ("for $k$ comparable to $n/2$ the
coefficients exceed the exponent range of a double") or drop the $\binom{200}{100}$
illustration, which does not describe this computation.

### 3b. `med` — a single-problem exponential is credited with an aggregate log-linear scaling law

> "It is flat until $k \approx 1/p$, turns over there, and saturates soon after — which is
> exactly why solve rate plotted against $\log k$ looks like a straight line over a couple
> of decades before bending." (line 236)

For a **single** $p$, $1 - e^{-pk}$ plotted against $\log k$ is a saturating sigmoid, not a
straight line. At $p = 0.0147$ the per-half-decade increments are
$+0.029, +0.094, +0.221, +0.414, +0.216, +0.012, 0.000$ — they rise and then collapse.
Nothing about that is linear over "a couple of decades".

The empirical log-linear solve-rate curve is a property of the **mixture over problems**:
a spread of per-problem $p$ values, each saturating at its own $k \approx 1/p$, sums to an
approximately log-linear aggregate. That is a different mechanism from the one the
sentence names, and "exactly why" asserts a derivation the appendix has not done. It is
also an **unlabelled interpretation**, in a document whose own preamble promises such
claims will be labelled.

Note also that "flat until $k \approx 1/p$" is loose: at $k = 1/p$ coverage is already
$1 - 1/e = 0.632$, and at a tenth of that budget it is $9.5\%$.

**Correction.** State that the single-problem curve saturates, and that the observed
log-linear scaling comes from the distribution of $p$ across problems — or label the
sentence as interpretation.

### 4. `high` — the GRPO caveat mis-attributes the loss of unbiasedness; the baseline lemma does **not** license subtracting the in-group mean

> "The baseline lemma licenses subtracting the mean. It does not license dividing by the
> standard deviation." (line 191)

The first sentence is false, and it is false for exactly the reason the second sentence
gives about the denominator. Equation (12) requires $b$ to **not depend on the sampled
$o$**. The group mean $\bar r = \frac1G\sum_j r_j$ **contains $r_i$**, so it depends on
$o_i$ and the lemma does not apply to it either.

The correct statement is quantitative, and I derived and then measured it. Using
$\mathbb E[\nabla\log\pi_\theta(o_i)] = 0$ for the $G-1$ independent cross terms:

$$\mathbb{E}\big[(r_i-\bar r)\,\nabla\log\pi_\theta(o_i)\big] \;=\; \frac{G-1}{G}\,\nabla_\theta J(\theta).$$

Monte-Carlo confirmation on a two-outcome policy (4M samples per setting): the measured
ratio to the true gradient was 0.5003 at $G=2$, 0.7497 at $G=4$, 0.8756 at $G=8$, against
the predicted 0.5, 0.75, 0.875.

So in-group mean-centering is **unbiased only up to the known positive scalar
$(G-1)/G$** — the *direction* is exactly preserved and the scalar is absorbed by the
learning rate, which is why nobody notices. The leave-one-out mean
$b_i = \frac{1}{G-1}\sum_{j\neq i} r_j$ *is* licensed by the lemma and is exactly
unbiased.

This is not a cosmetic correction: the sentence tells the reader that the mean is the safe
part and the denominator is the only compromise, and the appendix's whole framing of Step
3 ("the group's own empirical mean ... is an unbiased Monte-Carlo estimate of the ideal
baseline", line 182) is built on it. Being an unbiased estimate of $\mathbb E[r \mid q]$
and being a *valid baseline* are two different properties, and only the first holds.

**Correction.** Replace with: "The baseline lemma requires a baseline independent of the
sampled output. The group mean is not — it contains $r_i$ — and centering on it yields
exactly $\frac{G-1}{G}\nabla_\theta J$: unbiased up to a known positive scalar, so the
direction is preserved and the learning rate absorbs the rest. A leave-one-out mean would
be exactly unbiased. Dividing by the group standard deviation is a further and
qualitatively different departure, with no such scalar correction."

### 5. `med` — the unbiasedness argument is missing its load-bearing step, and n ≥ k is never stated

> "A uniformly random $k$-subset of $n$ independent draws from the model is itself
> distributed exactly as $k$ independent draws from the model ... Therefore
> $\mathbb{E}[\binom{n-c}{k}/\binom{n}{k}] = (1-p)^k$." (line 64) ... "This is the whole
> argument." (line 71)

The conclusion is right — I verified unbiasedness to machine precision — but the
"Therefore" is a jump. The distributional fact establishes
$\Pr(\text{no pass in } S) = (1-p)^k$. Getting from there to the *expectation of the
combinatorial ratio* needs the conditioning step
$\mathbb E_S[\mathbf 1\{\text{no pass in } S\} \mid X_{1:n}] = \binom{n-c}{k}/\binom{n}{k}$
followed by the tower property. That conditional expectation is *already on the page* as
Equation (4), fourteen lines earlier — the argument is one sentence from complete, and the
text instead declares "this is the whole argument".

Two smaller gaps in the same passage: the premise that the subset draw is **independent of
the outcomes** is stated informally ("tells you nothing about whether they passed") but
never named as the hypothesis it is; and the condition $n \ge k$ — without which
Equation (5) is undefined — appears nowhere in J.1.

**Correction.** One added sentence: "By Equation (4) this ratio is the conditional
probability given the outcomes, so taking expectations over $c$ and applying the tower
property gives $(1-p)^k$." Plus "for $n \ge k$" on Equation (5).

### 5b. `med` — 202 samples do not achieve 95% coverage; the required budget is 203

> "Equation (19) with $\delta = 0.05$ gives $k \approx 202$ samples for 95% coverage."
> (line 245), and the table row "0.0147 | 202" (line 251)

$\log(0.05)/\log(1-0.0147) = 202.2897$, and Equation (19) is an inequality
($k \ge \cdot$), so the sample count is the **ceiling**, 203. At $k = 202$ the coverage is
$0.94978$ — below the stated target. Every row of the table is the real-valued bound: 4.3,
28.4, 202.29, 298.07, 2994.23, whose ceilings are 5, 29, 203, 299, 2995. Two of the five
rows (0.5 and 0.1) are printed to one decimal and three (0.0147, 0.01, 0.001) are silently
truncated to integers, so the table also mixes two presentations.

The magnitude is trivial; the statement as written is nonetheless false, and the table
header "$k$ for 95% coverage" reads as a sample count.

**Correction.** Apply the ceiling in the prose ("203 samples") and either print all five
table entries to one decimal as the real-valued bound, or print all five as ceilings and
rename the column.

### 6. `med` — the worked table shows a realization difference, and the text reads it as the bias

> "| Difference | $+0.0089$ |" ... "Just under one point of pass@10, always in the same
> direction." (lines 79–81)

Two distinct quantities are being conflated. The derivation (Jensen, Equation (3)) proves
a statement about **expectations**: $\mathbb E[\text{plug-in}] < \mathrm{pass@}k$. The
table shows the **pointwise gap between two estimators at one realized $c$**. These are
different, and the appendix supplies no bridge between them.

The specific hazard here is sharp. At $n = 200$, $c = 20$ the empirical rate is exactly
$0.1$; *if* the true $p$ were $0.1$, the true $\mathrm{pass@}10$ would be $0.65132$ —
which is the **plug-in** number — and the unbiased estimate $0.6602$ would be the one
further from the truth in that draw. A reader who takes "+0.0089" as the size of the bias
is reading a coincidence: the actual bias at $n=200, p=0.1, k=10$ is $-0.00868$, a
different quantity that happens to be numerically close.

"Always in the same direction" *is* true, but for a reason the appendix never gives: the
pointwise inequality $\widehat{\mathrm{pass@}k}(c) \ge 1-(1-c/n)^k$ holds for every $c$
because $\binom{n-c}{k}/\binom{n}{k} = \prod_{i=0}^{k-1}\frac{n-c-i}{n-i} \le ((n-c)/n)^k$
term by term. I verified this over all $n \le 79$ and all valid $(k, c)$: zero violations.

**Correction.** Label the table row "Difference at this draw", and add the one-line
pointwise argument that actually justifies "always in the same direction". Keep the Jensen
result where it is, but do not let the worked example stand as its evidence.

### 7. `med` — J.2 derives the factorization but never the learning step

The derivation shows that $p_\theta(\mathrm{middle} \mid \mathrm{prefix}, \mathrm{suffix})$
is a sub-product of the chain rule on $z$ (correct, and exact as an identity about
$p_\theta$). It never shows why **training** makes that conditional a good model of the
*data* conditional. The missing step is one line: the population minimizer of the
cross-entropy in Equation (9) decomposes as entropy plus
$\mathrm{KL}(p_\star \Vert q_\theta)$, which is zero iff $q_\theta = p_\star$; and the
reordering is a **bijection**, so the joint law of the three pieces is unchanged and only
the factorization order moves.

Also unstated: the learned object is conditioned on the **sentinels and the FIM format**,
not on the bare document, and the equality with the natural conditional is an argument
(the bijection) rather than a triviality. And the population-optimum statement is
infinite-capacity and unconstrained-family — real models see a *mixture* of FIM and
ordinary examples at some FIM rate, which the appendix itself discusses at line 143 without
connecting it back.

Given the preamble's promise that "every step is shown", this omission is in scope.

### 7b. `med` — the AlphaCode substitution changes the meaning of p, twice

> "the average probability that a single sample passed the example tests was 1.47% ...
> Equation (19) with $\delta = 0.05$ gives $k \approx 202$ samples for 95% coverage."
> (line 245)

Two independent basis problems, both of which the appendix elsewhere knows to avoid.

**(a) Wrong event.** Throughout J.1 and J.4, $p$ is defined as the probability a sample is
**correct** (Equation (2), line 32; line 229). The AlphaCode figure is the probability a
sample **passes the public example tests** — a filtering-survival rate, and a strictly
weaker event. The resulting 202 is a budget for covering an example-test-passing sample,
not a solving one. Under `[opt:MATH-BASIS]` this needs an explicit declaration at the
point of use.

**(b) An averaged p in a nonlinear formula.** The figure is an **average across problems**,
inserted into $1-(1-p)^k$. That is precisely the Jensen error J.1 is written to warn
against: $\mathbb E_p[1-(1-p)^k] \neq 1-(1-\mathbb E[p])^k$. Because the function is
concave in $p$, using the mean $p$ **overstates** the coverage that the budget actually
buys across the population it is averaged over. J.1 spends fifteen paragraphs on this
fallacy and J.4 commits it eleven paragraphs later.

**Correction.** State the event ("probability of passing the public example tests, not of
solving") and note that a mean $p$ substituted into a concave function gives an optimistic
per-population coverage, so 203 is a floor for the average problem and not a budget for
the population.

### 8. `med` — the std-division caveat is directionally right but presents a contested effect as a benign one

> "It is a variance-reduction and scale-normalization heuristic — it puts easy and hard
> questions on a comparable gradient scale — and should be read as one." (line 191)

The conclusion (not exactly unbiased) is correct. The characterization is not neutral: the
documented critique of the $\hat\sigma$ term is that it induces a **question-difficulty
bias**, up-weighting prompts whose group rewards happen to have small spread. My Monte
Carlo shows the standardized estimator's ratio to the true gradient is 1.0006 at $G=2$,
1.618 at $G=4$, 1.871 at $G=8$ — it is not a rescaling by any constant, and the
distortion grows with $G$. "Puts easy and hard questions on a comparable gradient scale"
is the *intent*; the *effect* is a reweighting by $1/\hat\sigma$ that is itself an
unlabelled interpretation presented as fact.

**Correction.** Say that the estimator is unbiased for a **reward-spread-reweighted**
objective rather than for $\nabla J$, and note that removing the denominator is an active
line of work rather than settling the matter by calling it a heuristic.

### 9. `med` — Equation (16) equates a divergence with a single-sample random variable, and never establishes that it estimates the KL

Equation (16) is written as
$\mathbb{D}_{\mathrm{KL}}(\pi_\theta \Vert \pi_{\mathrm{ref}}) = u - \log u - 1$ with
$u$ evaluated at the sampled $o_i$. The left side is a deterministic divergence; the right
side is a random variable. They are equal only **in expectation** under $o \sim \pi_\theta$.

More substantively: the appendix proves $f \ge 0$ with a unique zero at $u = 1$ (correctly
— every derivative as printed is right), which establishes it is a valid *penalty*. It
never establishes the property that makes it a *KL estimator*, which is the one-line
argument $\mathbb E_{\pi_\theta}[u] = \sum_o \pi_\theta \cdot \pi_{\mathrm{ref}}/\pi_\theta = 1$,
hence
$\mathbb E[f(u)] = -\mathbb E[\log u] = \mathrm{KL}(\pi_\theta \Vert \pi_{\mathrm{ref}})$.
I verified this numerically on three random 6-outcome pairs: exact agreement to 1e-12.
The **direction** of the KL (forward, sampled under $\pi_\theta$) is also never stated.

**Correction.** Write it as $\hat{\mathbb D}_{\mathrm{KL}}$ or "an unbiased estimator of",
and add the one-line unbiasedness argument. Note also that the naive $-\log u$ estimator is
*equally* unbiased — the guaranteed sign, not the unbiasedness, is what this form buys.

### 10. `med` — "the standard deviation is 0.5" does not declare its basis

> "The mean is $0.5$ and the standard deviation is $0.5$, so $A = (1, -1, 1, -1)$."
> (lines 211–215)

For $r = (1,0,1,0)$: the **population** std (ddof = 0) is 0.5, giving $(1,-1,1,-1)$; the
**sample** std (ddof = 1) is 0.57735, giving $(0.866, -0.866, 0.866, -0.866)$. The printed
result is correct only under ddof = 0, and the convention is not stated. This is exactly
the two-bases case `[opt:MATH-BASIS]` and `viewer/tools/check-basis-declarations.py` exist
to catch, and the worked example is the appendix's only numerical instance of Equation (14).

**Correction.** "the population standard deviation (ddof = 0) is 0.5".

### 11. `low` — the small-p approximations are stated without their direction

Equations (18) and (19) both approximate without saying which way the error runs. Since
$-\log(1-p) = p + p^2/2 + \cdots > p$:

- Equation (19)'s $\frac1p\log\frac1\delta$ **over**-estimates the required $k$ (at
  $p = 0.0147$: 203.79 against the exact 202.29, a $+0.74\%$ relative over-estimate,
  matching the predicted $p/2 = 0.735\%$) — conservative, therefore safe.
- Equation (18)'s $1 - e^{-pk}$ **under**-estimates pass@k.

In a subsection whose neighbour (J.1) makes the direction of an estimator's error its
entire subject, dropping it here is a visible asymmetry.

### 12. `low` — the strictness conditions on the Jensen step

Equation (3) says $g''(p) < 0$ "for $k > 1$"; at $p = 1$ and $k > 2$ it is zero, so the
qualifier should be $k > 1$ **and** $p < 1$. Correspondingly, line 48's strict
$\mathbb E[g(\hat p)] < g(p)$ needs $\mathrm{Var}(\hat p) > 0$, i.e. $0 < p < 1$; at
$p \in \{0, 1\}$ the plug-in is exactly unbiased. Neither affects any conclusion.

### 13. `low` — the cost claim is false at the appendix's own worked point

> "the product runs over $c$ factors rather than $k$, so when few samples pass ... it is
> also the cheaper expression." (line 92)

Correct in general and correctly conditioned ("when few samples pass"), but at the worked
case $n = 200$, $c = 20$, $k = 10$ the product form runs over **20** factors against 10 for
the $k$-indexed form, so it is twice as expensive there. Worth a parenthetical, since the
reader has that example in hand.

### 14. `low` — notation slip in Equation (9)

Written $\log p(z) = \sum_t \log p_\theta(z_t \mid z_{<t})$ — the left side should be
$\log p_\theta(z)$. Equation (10) also elides the sentinel tokens from the conditioning
set, which is fine as an abstraction but is the same elision that finding 7 asks to be made
explicit.

### 15. `low` — Equation (15) is the sequence-level simplification of the published objective

The published GRPO objective carries an inner per-token average
$\frac{1}{\lvert o_i \rvert}\sum_t$ inside the group average, and places the KL penalty
inside it. Equation (15) presents the outcome-level form. Defensible for outcome
supervision, but it is a simplification of "the full objective, as published" (line 193)
and should say so. Flagged as a math-presentation nit; the exact published form is a
sourcing question I did not open the PDF to settle.

### 16. `low` — 0/0 is NaN in practice, not zero

Line 220 says the all-equal group "contributes **no gradient at all**". Strictly Equation
(14) is undefined there, and implementations add an $\varepsilon$ to the denominator to
*make* it zero. Without the $\varepsilon$ the result is NaN, which propagates through the
whole batch rather than contributing nothing. The distinction matters to anyone
implementing it, and the appendix's conclusion (curriculum and difficulty filtering are
preconditions) is unaffected and correct.

### Not checked

These are external-sourcing claims, outside a mathematics review. Reported as
**unchecked**, not as correct: the Codex paper "states the bias and defers the
demonstration to its appendix" (line 48); the FIM-rate sweep figures (line 143); the
InCoder Poisson-span description (line 147); the DeepSeek-R1 reward-hacking rationale
(line 222); AlphaCode's 1.47% and one-in-ten figures (line 245); Reflexion's 16.3% / 1.4%
and 0.80 to 0.77 (line 257); the IOI 213 / 156 / 395.64 figures (line 261). The arithmetic
that *is* internal to these — 213 minus 156 consistent with "roughly 60 points" — checks
out. These belong to a `citation-audit` pass.

### Overclaim audit

Every instance of "exact", "exactly", "precisely", "no approximation", "the whole
argument", "proves":

| Location | Phrase | Verdict |
|---|---|---|
| line 71 | "exactly. No approximation, no large-n limit" | **Earned.** Verified to 3.8e-15. Do not downgrade — add "for n at least k" |
| line 71 | "This is the whole argument" | **Overclaim** — finding 5 |
| line 64 | "distributed exactly as k independent draws" | True, but load-bearing premise unnamed — finding 5 |
| line 90 | "both sides equal 0.339774376237 to twelve digits" | **Earned** — reproduced exactly |
| line 139 | "gives exactly p(middle given prefix, suffix)" | **Earned as an identity about the model**; the learning step is missing — finding 7 |
| line 141 | "precisely a left-to-right continuation task" | **False** — finding 2 |
| line 236 | "which is exactly why solve rate ... looks like a straight line" | **False** — finding 3b |
| line 191 | "licenses subtracting the mean" | **False** — finding 4 |
| line 209 | "strictly convex with a unique minimum of zero" | **Earned** — all derivatives correct |
| line 220 | "intrinsic to a group-relative baseline" | **Earned** — holds for mean-only centering too |
| line 261 | "Two results bound the answer" | Loose ("bound" is not a bound), but the two figures are correctly attributed to different models |

### Interpretation-labelling audit

The appendix labels exactly one claim as interpretation (line 141), and **that label is in
the right place** — the "FIM for free" mechanism genuinely is unsourced reading. But the
labelled content is itself wrong (finding 2), and at least three unlabelled interpretations
remain: the log-linear-scaling mechanism (line 236, finding 3b); the characterization of
the std division as benign scale-normalization (line 191, finding 8); and the SPM
sentinel-placement rationale, "maximizing transfer between the two modes rather than
splitting the model's capacity" (line 145), which is a design rationale stated as fact.

---

## Numerical verification

Every number recomputed independently in `python3`. "Appendix" is the printed value.

| # | Quantity | Appendix | Recomputed | Status |
|---|---|---|---|---|
| 1 | plug-in pass@10, n=200 c=20 | 0.6513 | 0.65132156 | MATCH |
| 2 | unbiased pass@10, n=200 c=20 | 0.6602 | 0.660225623763 | MATCH |
| 3 | difference of the two | +0.0089 | +0.008904 | MATCH (but see finding 6) |
| 4 | identity check C(180,10)/C(200,10) | 0.339774376237 | 0.339774376237 | MATCH, all 12 digits |
| 5 | product form at same point | (same) | 0.339774376237 | MATCH |
| 6 | identity over random (n,c,k) | asserted | 4000 trials, 0 mismatches | CONFIRMED |
| 7 | identity, degenerate c>n-k | not stated | LHS=RHS=0 (n=10,c=8,k=5) | CONFIRMED, no case split needed |
| 8 | unbiasedness of Eq (5) | "exactly" | max abs error 3.8e-15 over 5 configs | CONFIRMED |
| 9 | plug-in bias direction | "underestimates" | -0.0832, -0.0087, -0.0144, -0.0250, -0.0073 | CONFIRMED negative in all 5 |
| 10 | unbiased(c) at least plug-in(c) pointwise | implied | 0 violations, all n up to 79 | CONFIRMED |
| 11 | pass@100 at p=0.01 | "approximately 1" | **0.633968** | **MISMATCH — finding 1** |
| 12 | pass@100 at p=0.05 | — | 0.994079 | (suggested replacement) |
| 13 | pass@1000 at p=0.01 | — | 0.999957 | (suggested replacement) |
| 14 | C(200,100) | 9.06e58, 59 digits | 9.0549e58, 59 digits | MATCH — but irrelevant, finding 3 |
| 15 | C(200,10) / C(180,10) | not stated | 2.245e16 (17 dig) / 7.628e15 (16 dig) | the actual operands |
| 16 | naive float relative error at n=200 k=10 | "discards information" | **0.0** (bit-exact) | **MISMATCH — finding 3** |
| 17 | E[FIM piece length] | L/3 each | L/3 each, spacings exchangeable | MATCH |
| 18 | GRPO group mean 0.5 | 0.5 | 0.5 | MATCH |
| 19 | GRPO group std, r=(1,0,1,0) | 0.5 | 0.5 (ddof=0) / 0.57735 (ddof=1) | MATCH only at ddof=0 — finding 10 |
| 20 | GRPO advantages | (1,-1,1,-1) | (1,-1,1,-1) ddof=0; (0.866,...) ddof=1 | MATCH only at ddof=0 |
| 21 | in-group-mean shrink factor | "licensed", i.e. 1 | 0.5003 / 0.7497 / 0.8756 at G=2/4/8 | **MISMATCH — finding 4**; predicted (G-1)/G |
| 22 | standardized estimator ratio | "no longer exactly unbiased" | 1.0006 / 1.618 / 1.871 at G=2/4/8 | CONFIRMED not unbiased; no constant — finding 8 |
| 23 | f''(u) for f=u-log u-1 | 1/u^2, greater than 0 | 1/u^2, greater than 0 | MATCH |
| 24 | f(1) | 0 | 0 | MATCH |
| 25 | E[f(u)] equals KL | not claimed | exact to 1e-12, 3 random pairs | CONFIRMED (finding 9: appendix omits it) |
| 26 | min of f over support | "non-negative" | 9.2e-3, 1.1e-2, 3.8e-3 (all positive) | CONFIRMED |
| 27 | k for 95% at p=0.5 | 4.3 | 4.3219 (ceil 5) | MATCH as real bound |
| 28 | k for 95% at p=0.1 | 28.4 | 28.4332 (ceil 29) | MATCH as real bound |
| 29 | k for 95% at p=0.0147 | 202 | 202.2897 (ceil **203**) | **MISMATCH as a sample count — finding 5b** |
| 30 | coverage at k=202, p=0.0147 | "95%" | **0.949785** | **MISSES 0.95** |
| 31 | coverage at k=203, p=0.0147 | — | 0.950523 | reaches it |
| 32 | k for 95% at p=0.01 | 298 | 298.0729 (ceil 299) | MATCH as real bound |
| 33 | k for 95% at p=0.001 | 2994 | 2994.2342 (ceil 2995) | MATCH as real bound |
| 34 | small-p approx at p=0.0147 | not given | 203.79 vs exact 202.29 | over-estimates by 0.74%, matches p/2 |
| 35 | single-p curve linear in log k | "a straight line" | increments +0.029,+0.094,+0.221,+0.414,+0.216,+0.012,0.000 | **MISMATCH — finding 3b** |
| 36 | IOI selection value | "roughly 60 points" | 213 - 156 = 57 | MATCH |

---

## Verdict

**The appendix is mathematically sound in its four core results, and two of its four
derivations are exactly right.** Equation (3)'s second derivative and its concavity /
Jensen conclusion are correct as printed, including the sign — I looked for an inversion
there and there is none. The pass@k estimator is genuinely unbiased and its "no
approximation, no large-$n$ limit" is an earned claim, verified to 3.8e-15; the product
identity of Equation (7) is exact, verified symbolically and over 4000 random triples
including the degenerate branch, and the printed twelve-digit check value is correct to the
last digit. The KL block (Equation (16), line 209) has every derivative right and its
convexity and non-negativity conclusions follow validly. The FIM causal-mask argument and
the $L/3$ spacing result are both correct, the latter including the exchangeability
observation. The all-equal-rewards degeneracy is correctly identified as intrinsic rather
than incidental.

**Two things must change before it ships.** First, finding 1: the claim that a
one-in-a-hundred model scores $\mathrm{pass@}100 \approx 1$ is false — the value is 0.63 —
and it sits in the sentence that carries J.1's main pedagogical point. Second, finding 4:
the GRPO caveat asserts that the baseline lemma "licenses subtracting the mean", which is
wrong for exactly the reason it correctly gives about the denominator. The in-group mean
contains $r_i$; centering on it yields $\frac{G-1}{G}\nabla_\theta J$, which I derived and
then measured (0.5003 / 0.7497 / 0.8756 against a predicted 0.5 / 0.75 / 0.875). The
conclusion GRPO practitioners rely on survives — the direction is preserved and the
learning rate absorbs the scalar — but the appendix currently tells the reader the mean is
the safe part, and that is the opposite of what the lemma says.

**Four more should change, and are cheap.** Finding 2 (the FIM sub-task claim names the
suffix factors, which are gap-conditioned continuation, when it wants the prefix factors);
finding 3 and 3b (a precision argument propped up by a coefficient the computation never
forms and which at the worked point has exactly zero error, and a single-problem
exponential credited with an aggregate log-linear scaling law it does not produce);
finding 5b (202 samples reach 0.9498, not 0.95 — the bound needs its ceiling); finding 10
(the worked GRPO std of 0.5 is population-basis and must declare it, per
`[opt:MATH-BASIS]`). Findings 5, 6, 7, 7b, 8 and 9 are gaps in argument rather than errors
in result — a missing tower step, a realization presented where a bias was derived, a
missing cross-entropy-to-conditional step, an averaged example-test rate substituted into a
concave function that J.1 itself warns against, and a KL estimator whose estimator property
is never established — and each is one or two sentences from closed. The interpretation
label at line 141 is correctly placed; three further unlabelled interpretations should
carry the same marking. Nothing I checked is wrong in a way that invalidates a result the
survey body depends on, and I found no sign error anywhere in the document.

