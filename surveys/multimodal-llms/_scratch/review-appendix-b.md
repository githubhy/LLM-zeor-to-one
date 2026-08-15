# Independent re-derivation — Appendix B (contrastive / InfoNCE)

`[opt:MATH-REDERIVE]` — `.claude/rules/workflow.md`.
Reviewer: independent agent. Date: 2026-08-15.
Target: `surveys/multimodal-llms/appendix-b-contrastive-infonce.md` §B.3, Eq. (3)–(5),
and the boxed `> **Note —**` on the pointwise step.

**PART 1 below was written BEFORE the target file was opened.** Part 2 is the comparison.

---

## Part 1 — My own derivation (target unread)

### Setup and notation

Context $c \sim p(c)$. A candidate tuple $X = (x_1,\dots,x_N)$ is formed by drawing an
index $K$ uniformly from $\{1,\dots,N\}$, setting $x_K \sim p(\cdot \mid c)$, and drawing
the remaining $N-1$ entries i.i.d. from the marginal $p(x)$. A critic $f(x,c) > 0$ scores
candidates. The loss is the categorical cross-entropy of identifying $K$:

$$
\mathcal{L}_N(f) \;=\; -\,\mathbb{E}\!\left[\log \frac{f(x_K,c)}{\sum_{j=1}^{N} f(x_j,c)}\right],
$$

the expectation over $c$, $K$, and all $N$ candidates. Define the density ratio and its
reciprocal at the positive:

$$
s(x,c) \;=\; \frac{p(x\mid c)}{p(x)}, \qquad
r \;=\; \frac{1}{s(x_K,c)} \;=\; \frac{p(x_K)}{p(x_K \mid c)} .
$$

Throughout, $\log$ is natural (nats).

### (a) The optimal critic

Condition on $(X, c)$. The prior on $K$ is uniform; given $K=k$ the tuple has density
$p(x_k\mid c)\prod_{j\neq k} p(x_j)$. Bayes:

$$
P(K = i \mid X, c)
= \frac{p(x_i\mid c)\prod_{j\neq i} p(x_j)}
       {\sum_{k} p(x_k\mid c)\prod_{j\neq k} p(x_j)}
\;\;\overset{\div \prod_j p(x_j)}{=}\;\;
\frac{s(x_i,c)}{\sum_k s(x_k,c)} .
$$

By the tower property,
$\mathbb{E}[-\log q_K \mid X,c] = -\sum_i P(K{=}i\mid X,c)\log q_i = H(P,q) \ge H(P)$,
with equality iff $q = P$. The softmax family can realise $q = P$ pointwise, so

$$
\boxed{\,f^\star(x,c) \;=\; \alpha(c)\,\frac{p(x\mid c)}{p(x)}\,}, \qquad \alpha(c) > 0 .
$$

Three facts worth stating explicitly:

1. **$N$ does not appear.** The optimal critic is the density ratio for every batch size.
   $N$ changes the *value* of the optimal loss, never the *argmin*.
2. **Uniqueness only up to $\alpha(c)$** — a multiplicative constant that may depend on $c$
   but not on $x$ or on the index — because the softmax is shift-invariant in the logit.
   It is also only pinned on $\operatorname{supp} p$.
3. **The optimum is generally outside the model class.** A temperature-scaled cosine critic
   $f = \exp(z_x^\top z_c/\tau)$ with unit-norm embeddings cannot represent an arbitrary
   density ratio. So real $\mathcal{L}$ sits strictly above $\mathcal{L}^{\mathrm{opt}}$, and
   every bound below is loose by that amount too.

### (b) The MI bound — the textbook (CPC) chain, and what is actually an identity in it

Substituting $f^\star$ (take $\alpha \equiv 1$) and writing $S = \sum_{j\neq K} s(x_j,c)$:

$$
\mathcal{L}^{\mathrm{opt}}_N
= \mathbb{E}\!\left[\log\frac{s(x_K,c) + S}{s(x_K,c)}\right]
= \mathbb{E}\!\left[\log\bigl(1 + r\,S\bigr)\right] .
\tag{i}
$$

Step (i) is an **identity**. The next step is not:

$$
\mathbb{E}_{\text{negs}}[S] = (N-1)\,\mathbb{E}_{x\sim p}\!\left[\tfrac{p(x\mid c)}{p(x)}\right] = N-1 ,
\qquad\text{so CPC replaces } S \rightsquigarrow N-1 .
\tag{ii}
$$

$\mathbb{E}_{x\sim p}[s] = \int p(x)\frac{p(x\mid c)}{p(x)}\,dx = 1$ is exact, but moving the
mean *inside* $\log$ is not. **$\log$ is concave**, so conditioning on $(c, x_K)$ (the
negatives are independent of the positive given $c$) Jensen gives

$$
\mathcal{L}^{\mathrm{opt}}_N \;=\; \mathbb{E}\log(1 + rS)
\;\le\; \mathbb{E}\log\bigl(1 + r(N-1)\bigr) \;=:\; \mathcal{L}^{\ast}_N .
\tag{iii}
$$

**This is the load-bearing problem with the CPC chain, and it is not the $r\le 1$ step.**
The target of the argument is a *lower* bound on $\mathcal{L}$ (we want
$\mathcal{L} \ge \log N - I$, which rearranges to $I \ge \log N - \mathcal{L}$). Step (ii)
delivers an **upper** bound on $\mathcal{L}^{\mathrm{opt}}$. Whatever is subsequently proved
about $\mathcal{L}^{\ast}$ therefore does **not** transfer to $\mathcal{L}^{\mathrm{opt}}$.
The chain, taken literally, proves nothing.

Continuing the chain anyway (this is what CPC does): with $h(r) := \frac{1+r(N-1)}{rN}$,

$$
\mathcal{L}^{\ast}_N = \mathbb{E}\log(rN) + \mathbb{E}\log h(r)
= \log N + \mathbb{E}[\log r] + \mathbb{E}\log h(r) .
\tag{iv}
$$

and by (d) below $\mathbb{E}[\log r] = -I(x;c)$ exactly, so

$$
\mathcal{L}^{\ast}_N \;=\; \log N - I(x;c) + \mathbb{E}\log h(r) .
\tag{v}
$$

The bound $I \ge \log N - \mathcal{L}^{\ast}$ therefore holds **iff $\mathbb{E}\log h(r) \ge 0$** —
which is exactly question (c).

### (b′) The bound is nevertheless a theorem — via a different, exact route

The CPC chain is broken, but the *result* is true, and there is a short exact proof that
also hands you the slack. Take $f = f^\star$ and let $P_k$ be the joint law of $(c,X)$ given
$K=k$, $\bar P = \frac1N\sum_k P_k$ the marginal.

- $K \perp c$ by construction.
- $K \perp X$ **marginally**, since

$$
P(X\mid K=k) = \int p(c)\,p(x_k\mid c)\prod_{j\neq k}p(x_j)\,dc = \prod_j p(x_j),
$$

which does not depend on $k$.

Hence $\log N - \mathcal{L}^{\mathrm{opt}}_N = \mathrm{KL}(P_1 \Vert \bar P) = I(K; c, X)$, which expands as $I(K;c) + I(K;X\mid c) = I(K;X\mid c)$ and equally as $I(K;X) + I(K;c\mid X) = I(K;c\mid X)$. Then chain-rule the same quantity two ways:

$$
I(K,X;c) = I(X;c) + I(K;c\mid X) = I(K;c) + I(X;c\mid K) = 0 + I(x;c),
$$

the last equality because given $K=1$ only $x_1$ carries information about $c$. Therefore

$$
\boxed{\;\mathcal{L}^{\mathrm{opt}}_N \;=\; \log N - I(x;c) + I(X;c)\;}
\quad\Longrightarrow\quad
\log N - \mathcal{L}_N \;\le\; \log N - \mathcal{L}^{\mathrm{opt}}_N \;=\; I(x;c) - I(X;c) \;\le\; I(x;c).
$$

Exact, unconditional, no approximation anywhere. The slack of the InfoNCE bound at the
optimal critic is **exactly $I(X;c)$**, the mutual information between the *whole candidate
tuple* and the context. Verified by exact enumeration on six random discrete problems
(machine precision, `err ~ 1e-16`; see numerics below). It also gives the $\log N$ ceiling
for free, since $\mathcal{L}^{\mathrm{opt}} \ge 0$.

### (c) THE KEY QUESTION — is $\mathbb{E}\log[1+r(N-1)] \ge \mathbb{E}\log[rN]$ valid?

**Pointwise.** $1 + r(N-1) \ge rN \iff 1 + rN - r \ge rN \iff r \le 1$. So the *pointwise*
inequality holds **iff $r \le 1$**, i.e. iff $p(x_K) \le p(x_K\mid c)$ at the positive. That
condition fails on a set of positive probability for essentially every non-degenerate
$p(x\mid c)$ — positives that are *less* likely under the conditional than under the
marginal are ordinary events.

**Pointwise repair.** $h(r) = \frac{1+r(N-1)}{rN} = \frac{1}{rN} + \frac{N-1}{N}$ is strictly
decreasing on $(0,\infty)$, with $\inf_{r>0} h(r) = \frac{N-1}{N}$ approached as
$r\to\infty$ and never attained. So $\log h(r) > -\log\frac{N}{N-1}$ for every $r>0$, giving
the unconditional-in-$r$ statement

$$
\mathcal{L}^{\ast}_N \;>\; \log N - I - \log\tfrac{N}{N-1} \;=\; \log(N-1) - I
\;\Longrightarrow\; I \;\ge\; \log(N-1) - \mathcal{L}^{\ast}_N .
$$

Worst-case loss $\log\frac{N}{N-1}$ nats. **All of this is correct** — but it is the *weakest*
correct answer, because it throws away the constraint that ties $r$ to a probability ratio.

**The strong answer: the step is UNCONDITIONALLY valid in expectation — no $r\le1$ needed.**
The step is never used pointwise; it is used inside an expectation. Substitute
$u := -\log r$, so that $h = \frac{e^u + N - 1}{N}$ and

$$
\log h \;=\; \phi(u) \;:=\; \log\!\bigl(e^{u} + N - 1\bigr) - \log N .
$$

$\phi$ is a log-sum-exp, hence **convex** in $u$, and increasing, with $\phi(0)=0$. Jensen
for a *convex* function runs the other way:

$$
\mathbb{E}\log h(r) \;=\; \mathbb{E}\,\phi(u) \;\ge\; \phi\bigl(\mathbb{E}u\bigr) \;=\; \phi\bigl(I(x;c)\bigr)
\;=\; \log\frac{e^{I} + N - 1}{N} \;\ge\; \phi(0) \;=\; 0 ,
$$

using $\mathbb{E}u = \mathbb{E}[-\log r] = I(x;c) \ge 0$ from (d). **So
$\mathbb{E}\log[1+r(N-1)] \ge \mathbb{E}\log[rN]$ holds for every distribution of $r$ arising
in this setting, with no side condition at all**, and the full $I \ge \log N - \mathcal{L}^{\ast}$
survives. Equality only in the degenerate case $I=0$ ($r\equiv1$ a.s.).

An adversarial numerical search over 400k two-point distributions of $u$ with
$\mathbb{E}u = I \ge 0$ (spread up to $\pm 60$ nats, $N \in \{2,8,64,1024,32768\}$) never found
$\mathbb{E}\log h < 0$; the minimum always sits at the degenerate point ($\sim 10^{-8}$ to
$10^{-14}$, i.e. zero to float noise).

**Tightest unconditional statement.** Combining (v) with $\mathbb{E}\phi(u) \ge \phi(I)$:

$$
\mathcal{L}^{\ast}_N \;\ge\; \log\!\bigl(e^{I} + N - 1\bigr) - I
\quad\Longleftrightarrow\quad
\log N - \mathcal{L}^{\ast}_N \;\le\; I + \log\frac{N}{e^{I} + N - 1} .
$$

This single line delivers **both** results at once: the RHS is $\le I$ (the MI bound) and
$\to \log N$ as $I \to \infty$ (the ceiling). It is strictly stronger than
$\min(I, \log N)$-style statements.

**Summary answer to (c):** the step is *pointwise* invalid unless $r\le1$; but the step is
only ever *used* in expectation, where it is **unconditionally valid**. The tightest
unconditional bound is not $I \ge \log(N-1) - \mathcal{L}$ — it is $I \ge \log N - \mathcal{L}$ itself, and in fact the sharper $\log N - \mathcal{L}^{\ast} \le I + \log\frac{N}{e^I+N-1}$. The $\log\frac{N}{N-1}$ worst-case loss is real for the *pointwise* patch, but the pointwise patch is unnecessary.

### (d) Is $\mathbb{E}[\log r] = -I(x;c)$ exact?

**Exact, by definition, and it is not an approximation of anything.**

$$
I(x;c) = \mathbb{E}_{p(x,c)}\!\left[\log\frac{p(x,c)}{p(x)p(c)}\right]
       = \mathbb{E}_{p(x,c)}\!\left[\log\frac{p(x\mid c)}{p(x)}\right]
       = -\,\mathbb{E}_{p(x,c)}[\log r] .
$$

The expectation is over the **joint** $p(x,c) = p(c)\,p(x\mid c)$ — i.e. $c \sim p(c)$ and the
*positive* $x_K \sim p(\cdot\mid c)$. Two things this hinges on:

- The positive in InfoNCE is by construction a joint draw, so the expectation the loss
  supplies is exactly the one the MI definition wants. No approximation, no asymptotics.
- The negatives marginalise out: $r$ is a function of $(c, x_K)$ only.
- It would be **wrong** under the product $p(x)p(c)$: that gives
  $\mathbb{E}_c\,\mathrm{KL}\!\left(p \Vert p(\cdot\mid c)\right) \ge 0$, a reverse KL, not $-I$.
  So "the expectation is over the joint" is load-bearing, not decoration.

### Numerics run (all before opening the target)

| Check | Result |
|---|---|
| $h(r) = \frac1{rN}+\frac{N-1}{N}$ identity | max err $5.7\times10^{-14}$ over $r\in[10^{-6},10^{15}]$, $N\in\{2,8,32768\}$ |
| $h$ strictly decreasing | true on all grids |
| $\inf h = \frac{N-1}{N}$, not attained | $h(10^{15}) \to (N-1)/N$ from above; $\log h \to -\log\frac{N}{N-1}$ |
| $\phi(u)=\log(e^u+N-1)-\log N$ convex, increasing, $\phi(0)=0$ | 0 violations on 801-point grid, all $N$ |
| adversarial search for $\mathbb{E}\log h < 0$ | 400k trials × 5 values of $N$: **never negative**; min $\approx 10^{-8}\!-\!10^{-14}$ (degenerate) |
| identity $\mathcal{L}^{\mathrm{opt}}_N = \log N - I(x;c) + I(X;c)$ | exact enumeration, 6 random discrete problems, err $\le 3.3\times10^{-16}$ |
| direction of step (ii) | $\mathcal{L}^{\ast} \ge \mathcal{L}^{\mathrm{opt}}$ in **8/8** cases — approximation is an upper bound |
| $\ln 32768$ | $10.39720770839918$ nats |
| $\log_2 32768$ | $15.0$ bits exactly |
| $\ln\frac{32768}{32767}$ | $3.051804\times10^{-5}$ nats ($4.40\times10^{-5}$ bits) |

---

## Part 2 — Comparison against the target

(appended after reading `appendix-b-contrastive-infonce.md`)
