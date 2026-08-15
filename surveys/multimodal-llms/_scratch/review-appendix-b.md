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

Read after Part 1 was complete. Sources opened for verification:
`download/vandenoord-cpc-2018.pdf` (CPC App. A.1, Eq. 6–11) and
`download/zhai-siglip-2023.pdf` (Table 2). Both are `local:`-tagged in `references.md`.

**Headline.** Every *displayed equation* in §B.3 is correct as printed, and every worked
number checks out. The two defects are both in prose: the boxed `> **Note —**` **points at
the wrong step** and then **gives away a bound it did not have to give away**; and the
worked-example paragraph's interpretive argument is built on off-basis evidence.

---

### [ERROR] The boxed Note's conclusion — the $\log N$ form needs no assumption

**Survey claims** (line 56): "*the honest form of Equation (5) is the $N-1$ one, and the $N$
version needs a pointwise assumption nobody states*", concluding
$I \ge \log(N-1) - \mathcal{L}_{\mathrm{NCE}}$ is "*the unconditional statement*".

**My independent result.** The step is never used pointwise — it is used **inside an
expectation**, and there it is unconditionally valid. Set $u = -\log r$, so

$$
\log h(r) \;=\; \phi(u) \;=\; \log\!\bigl(e^{u} + N-1\bigr) - \log N ,
$$

a log-sum-exp, hence **convex** and increasing with $\phi(0)=0$. Jensen for a convex function
runs the opposite way to the concave case:

$$
\mathbb{E}\log h(r) \;=\; \mathbb{E}\phi(u) \;\ge\; \phi(\mathbb{E}u) \;=\; \phi\bigl(I(x_v;x_t)\bigr) \;\ge\; \phi(0) \;=\; 0 ,
$$

using $\mathbb{E}u = -\mathbb{E}\log r = I \ge 0$ — the survey's own Eq. (4) right-hand
equality. So $\mathbb{E}\log[1+r(N-1)] \ge \mathbb{E}\log[rN]$ for **every** distribution of
$r$ that can arise here, with **no condition on $r$ whatsoever**. Equality only in the
degenerate $I=0$ case.

**Delta.** The Note surrenders $\log\frac{N}{N-1}$ nats that were never at risk. The
diagnosis "the $N$ version needs a pointwise assumption nobody states" is **backwards**:
nobody states the assumption because nobody needs it. Numerically corroborated — 400k
adversarial two-point distributions of $u$ with $\mathbb{E}u = I \ge 0$, spread to $\pm 60$
nats, across $N \in \{2,8,64,1024,32768\}$: $\mathbb{E}\log h$ was **never** negative (minimum
$10^{-8}$ to $10^{-14}$, i.e. float noise at the degenerate point).

**Tightest unconditional statement** (strictly stronger than either form in the survey):

$$
\log N - \mathcal{L}^{\ast}_N \;\le\; I + \log\frac{N}{e^{I} + N - 1} .
$$

Its right side is $\le I$ (the MI bound) and $\to \log N$ as $I \to \infty$ (the ceiling). One
line, both results, no side conditions.

**Suggested repair.** Keep the pointwise observation — it is a genuinely nice piece of
analysis and correctly identifies that CPC's Eq. (10) is asserted bare. But retitle it: the
pointwise step needs $r \le 1$; the *expectation* step does not; therefore Eq. (5) as
published is fine and the $N-1$ retreat is unnecessary.

### [ERROR] The Note diagnoses the wrong step — the fatal one is the `≈`, and it points the wrong way

**Survey framing** (line 42): the sum-to-mean replacement is "*an approximation that sharpens
as $N$ grows, and the one place the source flags its own looseness*" — then the Note spends
its entire length on the *middle* inequality instead.

**My independent result.** Order of severity is inverted. With
$S = \sum_{x_j \in X_{\text{neg}}} p(x_j\mid x_v)/p(x_j)$, Eq. (3) is an exact identity, and
the replacement $S \rightsquigarrow N-1$ is, when made rigorous, **Jensen on the concave
$\log$**:

$$
\mathcal{L}^{\star} = \mathbb{E}\log(1 + rS) \;\le\; \mathbb{E}\log\bigl(1 + r(N-1)\bigr) .
$$

The argument needs a **lower** bound on $\mathcal{L}^{\star}$ (Eq. (5) rearranges to
$\mathcal{L} \ge \log N - I$). This step supplies an **upper** bound. So the chain
`A ≈ B ≥ C` yields nothing about `A ≥ C`: **as written, Eq. (4) proves the bound for a
quantity that dominates $\mathcal{L}^{\star}$, not for $\mathcal{L}^{\star}$.** Verified
numerically by exact enumeration: $\mathcal{L}^{\ast} \ge \mathcal{L}^{\mathrm{opt}}$ in
**8/8** random discrete problems.

Also unstated: "sharpens as $N$ grows" is an LLN claim that needs
$\operatorname{Var}_{x\sim p}[p(x\mid x_v)/p(x)] = \chi^2\bigl(p(\cdot\mid x_v)\,\Vert\,p\bigr) < \infty$.
High-dimensional density ratios are routinely heavy-tailed; the survey inherits CPC's
"*quickly becomes more accurate*" without the condition.

**Delta.** A note whose stated purpose is "the middle inequality does not hold pointwise"
walks past the step that actually breaks the deduction. Net effect: the survey repairs a
non-problem and leaves the real one unflagged.

**Source check (verbatim, `download/vandenoord-cpc-2018.pdf` App. A.1).** CPC's chain is
Eq. (6) identity → Eq. (8) `≈` (the sum-to-mean) → Eq. (10) `≥` (the $r\le1$ one) → Eq. (11).
CPC's own commentary is "*Equation 8 quickly becomes more accurate as N increases*". So the
survey's two attributions to the source are both **accurate**: the source does flag looseness
only at the `≈`, and does assert the `≥` bare with no condition. The misjudgement is the
survey's ranking of the two, not its reading of the paper.

**Note the result is still a theorem** — provable exactly, without either approximation.
Using $K \perp x_v$ and $K \perp X$ (Part 1 §b′), a two-way chain rule gives the identity

$$
\mathcal{L}^{\mathrm{opt}}_N \;=\; \log N - I(x_v;x_t) + I(X; x_v) ,
$$

so $\log N - \mathcal{L}_N \le I(x_v;x_t)$ **exactly and unconditionally**, with the slack at
the optimal critic equal to $I(X;x_v)$ — the MI between the *whole candidate set* and the
image. Verified by exact enumeration on six random discrete problems to
$\le 3.3\times10^{-16}$. This would be a strictly better derivation to present than CPC's, and
it makes the Note unnecessary rather than merely wrong.

### [CONFIRMED] All four of the Note's algebraic sub-claims

| Claim | Verdict |
|---|---|
| the step is equivalent to $1+r(N-1) \ge rN$, i.e. to $r \le 1$ | **correct** (pointwise) |
| $h(r) = \frac{1+r(N-1)}{rN} = \frac{1}{rN} + \frac{N-1}{N}$ | **correct**, max err $5.7\times10^{-14}$ over $r \in [10^{-6},10^{15}]$ |
| $h$ strictly decreasing with infimum $\frac{N-1}{N}$ | **correct**; infimum approached as $r\to\infty$, never attained |
| the step loses at most $\log\frac{N}{N-1}$ nats for every $r>0$ | **correct** as a pointwise worst case |
| $\log N - \log\frac{N}{N-1} = \log(N-1)$ | **correct** |

The algebra is clean. It is the *conclusion drawn from it* that is wrong — exactly the failure
class `[opt:MATH-REDERIVE]` exists to catch.

### [CONFIRMED] Every worked number

| Survey value | Recomputed | Verdict |
|---|---|---|
| $\log N = 10.4$ nats at $N=32768$ | $10.39720770839918$ | ✓ |
| $15.0$ bits | $\log_2 32768 = 15$ exactly | ✓ |
| $\log\frac{N}{N-1} = 3.1\times10^{-5}$ nats | $3.051804\times10^{-5}$ | ✓ (2 s.f.; $3.05\times10^{-5}$ is truer) |
| $\log N = 9.7$ nats at $N=16384$ | $9.70406$ | ✓ |
| SigLIP INet-0: $71.6, 73.2, 73.2, 73.2, 73.1$ | Table 2, exact | ✓ |
| SigLIP XM avg: $34.8, 34.9, 34.4, 33.6, 32.7$ | Table 2, exact | ✓ |
| "$2.2$-point decline from the peak at $32$k" | $34.9 - 32.7 = 2.2$ | ✓ |
| "flat to within $0.1$ points across a $7.5\times$ range" | $240/32 = 7.5$; $73.2 \to 73.1$ | ✓ |
| ¶7 "on the identical runs whose ImageNet column was flat" | both rows are Table 2 | ✓ |

### [CONFIRMED] (a) and (d)

$f^\star \propto p(x_t\mid x_v)/p(x_t)$, independent of $N$ — matches my Bayes derivation and
CPC §2.3 verbatim. Eq. (2) and Eq. (3) are both exact identities as printed.

$\mathbb{E}[\log r] = -I$ is **exact**, not approximate — it is the definition of mutual
information, and the InfoNCE positive is by construction a joint draw, so the loss supplies
precisely the expectation the definition wants. The survey's "*just $\mathbb{E}[\log r] = -I$
by definition*" is right. But see the next finding for the expectation's domain.

### [UNSTATED HYPOTHESIS] $\mathbb{E}_X$ omits the outer expectation over $x_v$

Eq. (3) and Eq. (4) both carry the operator $\mathbb{E}_X$, where §B.1 defines $X$ as the
*candidate set* at a **fixed** image $x_v$. Under that reading the right-hand equality of
Eq. (4) is false:

$$
\mathbb{E}_{x_t^{+} \sim p(\cdot\mid x_v)}[\log r] \;=\; -\,\mathrm{KL}\bigl(p(x_t\mid x_v)\,\Vert\,p(x_t)\bigr) ,
$$

which equals $-I(x_v;x_t)$ only **after** averaging over $x_v \sim p(x_v)$. The expectation
must run over the joint $p(x_v, x_t)$. This is load-bearing rather than cosmetic: over the
*product* $p(x_v)p(x_t)$ the same expression gives $+\mathbb{E}_{x_v}\mathrm{KL}(p \Vert p(\cdot\mid x_v))$
— a reverse KL, non-negative, and the bound would invert. CPC has the same shorthand, so the
survey inherits it, but §B.3 is explicitly the place where "*the derivation is worked here in
full rather than asserted*", so the shorthand should not survive. One-symbol fix:
$\mathbb{E}_{x_v, X}$.

### [UNSTATED HYPOTHESIS] The optimal-critic → arbitrary-critic step is dropped

Eq. (3) and Eq. (4) are about $\mathcal{L}^{\star}$, the loss **at the optimal critic**.
Eq. (5) states the bound for $\mathcal{L}_{\mathrm{NCE}}$, the loss at *whatever critic was
actually trained* — which is what a practitioner plugs a measured number into. The bridging
step ($\mathcal{L}_{\mathrm{NCE}} \ge \mathcal{L}^{\star}$ for every $f$, so the bound only
loosens) is never stated.

The direction happens to be safe, so this is a gap and not an error — but note the source
does supply it: CPC writes "*This trivially also holds for other $f$ that obtain a worse
(higher) $\mathcal{L}_N$*". The survey dropped a step the paper it is expanding took the
trouble to include.

Worth adding alongside it: with $f = \exp(\mathrm{sim}/\tau)$ and unit-norm embeddings, the
representable log-density-ratio is confined to $[-1/\tau, 1/\tau]$. At CLIP's learned
$\tau \approx 0.01$ that is $\pm 100$ nats — generous, but it is a *hard* capacity limit on
how closely $f^\star$ can be approached, and it is a concrete named candidate for the
"binding constraint is elsewhere" of ¶6.

### [OVERSTATEMENT] ¶6 — the ceiling argument, on four counts

**Survey claims** (line 60): "*the $\log N$ ceiling is not what stops batch scaling in
practice: at $32$k the bound still permits $10.4$ nats and the model has stopped improving
anyway*", and "*the bound ... explicitly does not explain the plateau*".

The conclusion is probably right. The argument given does not establish it.

**(i) Basis mismatch — nats versus accuracy points.** The ceiling constrains the estimator
$\hat I = \log N - \mathcal{L}_{\mathrm{NCE}}$, in nats. The evidence offered is ImageNet
zero-shot top-1, in percentage points. The survey never measures or cites
$\mathcal{L}_{\mathrm{NCE}}$, so it never establishes where the model actually sits relative
to $10.4$ nats. This is `.claude/rules/calibration-residuals.md` check 4 (reconcile the metric
basis before believing agreement *or* disagreement).

**(ii) The evidence does not discriminate between the two hypotheses.** Two regimes produce a
plateau: (A) $\hat I$ pinned at $\log N < I_{\text{true}}$ — the ceiling binds; (B)
$\hat I \to I_{\text{true}} \ll \log N$ — the ceiling is slack. Downstream accuracy is flat in
**both**. Only $\mathcal{L}_{\mathrm{NCE}}$ separates them, and note the direction is
counter-intuitive: a model with *near-perfect in-batch* discrimination has
$\mathcal{L} \to 0$ and therefore sits **at** the ceiling, so high accuracy is evidence *for*
the ceiling story, not against it.

**(iii) Wrong arm — the cited runs are sigmoid, not softmax.** SigLIP Table 2 is
"*Multilingual SigLIP results with various batch sizes*" — the **sigmoid** loss. §B.4 of this
same appendix states that SigLIP "*abandons the softmax of Equation (1) — and with it the
explicit $\log N$ MI bound*". So ¶6 argues about the InfoNCE ceiling using runs that, by the
survey's own account, are not governed by it. Self-contradiction between ¶6 and §B.4.

**(iv) The paper's softmax arm cuts the other way, and is omitted.** Same page, verbatim:
"*SigLIP performs best at batch size $32$ k, whereas the softmax loss required $98$ k for
optimal performance and still didn't outperform the sigmoid based variant.*" The softmax arm
— the one the $\log N$ bound *does* apply to — keeps paying to roughly $3\times$ the batch at
which the cited sigmoid arm saturates. That is the single most relevant datapoint in the
source for ¶6's thesis, it points against the thesis, and it is not reported. (The survey is
otherwise scrupulous about this: ¶7 volunteers the multilingual turn-over precisely because it
embarrasses the theory. Same discipline is owed here.)

**(v) ¶6 contradicts ¶5.** ¶5's second consequence reads "*returns to batch size must
diminish once $\log N$ exceeds the true $I$*". ¶6 then argues "*a caption simply does not
carry ten nats about its image*" — which **is** the condition $\log N > I_{\text{true}}$, i.e.
exactly regime (B), i.e. exactly the prediction ¶5 just made from the bound. So the theory
*does* predict the plateau, by the survey's own preceding paragraph; declaring it "*explicitly
does not explain the plateau*" and calling that "*the load-bearing correction*" is the
overstatement. What the theory genuinely fails to predict is the **non-monotone multilingual
decline** — and ¶7 already says so, correctly and well.

**Answer to the question posed.** Yes, the reasoning confuses a bound on *certifiable*
information with a bound on *achievable* performance — but the confusion is subtler than a
straight category error. ¶5 states the certification framing correctly ("*caps what one batch
can certify*"). ¶6 then adjudicates that certification claim using a *performance* measurement
without converting between the two bases, and reaches a verdict the measurement cannot
support in either direction.

**Suggested repair.** (1) Report the achieved $\mathcal{L}_{\mathrm{NCE}}$ or in-batch top-1,
or state plainly that it is not available and the ceiling's slack is therefore not measured
(explicit n/a beats silent absence). (2) Use the softmax arm, or disclose that the cited runs
are sigmoid and say why they still bear. (3) Report the $98$ k softmax datapoint. (4) Reframe
the conclusion: the bound *does* explain the plateau via $I_{\text{true}}$ saturation; what it
cannot explain is the decline.

### [CONFIRMED] ¶5 "the bound is tighter as $N$ grows"

Verified, and now with a mechanism the survey does not have. From the exact identity, the
slack is $I(X;x_v)$, and exact enumeration over three random problems with $N = 2,\dots,6$
shows it decreasing monotonically (e.g. at $I = 0.2633$ the slack runs
$0.1301 \to 0.0855 \to 0.0638 \to 0.0510 \to 0.0426$), with
$\log N - \mathcal{L}^{\mathrm{opt}}$ rising monotonically toward $I$. ¶5's claim holds.

One nuance worth adding: the slack stays strictly positive **even when $\log N$ far exceeds
$I$** (at $I = 0.263$, $N = 6$, $\log N = 1.79$, the bound still reads only $0.221$). So "the
bound still permits $10.4$ nats" in ¶6 does not mean the bound is near-tight at $32$k — the
ceiling being slack and the bound being tight are different properties.

### [Minor] Precision nits

- "*the step loses at most $\log\frac{N}{N-1}$ nats*" — the infimum of $h$ is not attained, so
  it is *strictly less than*. Immaterial, but the Note is otherwise exacting.
- "*That is true on average (it is what positive mutual information means)*" — true in the
  **geometric**-mean sense: the log-mean of $r$ is $e^{-I} \le 1$. The **arithmetic** mean is
  $\mathbb{E}[r] = 1$ exactly whenever $p(\cdot\mid x_v)$ has full support (and $\le 1$ in
  general), i.e. exactly at the boundary, not below it. Naming the mean would sharpen it.
- §B.1's "*the other $N-1$ are other captions from the batch*" silently assumes those are
  marginal draws. In a $32$k CLIP batch, semantically-matching captions for *other* images
  appear as negatives (false negatives), which violates the assumption in a direction that
  biases the estimator — and is another concrete candidate for ¶6's "binding constraint is
  elsewhere".

---

## Verdict

| Item | Verdict |
|---|---|
| Eq. (1), (2), (3) | correct identities |
| Eq. (4) first step (`≈`) | **wrong-direction Jensen** — breaks the deduction; flagged only as "an approximation" |
| Eq. (4) middle step (`≥`) | pointwise needs $r\le1$ (survey correct); **unconditionally valid in expectation** (survey wrong) |
| Eq. (5) | correct as published; the $N-1$ retreat is unnecessary |
| Boxed Note, algebra | all four sub-claims **correct** |
| Boxed Note, conclusion | **wrong** — gives away $\log\frac{N}{N-1}$ that was never at risk |
| Worked numbers | all **correct** |
| ¶5 | **correct**, mechanism improvable |
| ¶6 interpretive claim | **overstated** on four counts (basis, arm, omitted datapoint, self-contradiction with ¶5) |
| ¶7 | **correct and well-judged** |

**Two required edits:** rewrite the boxed Note (the $\log N$ form is unconditional; the real
soft spot is the `≈`), and rebuild ¶6's argument on a basis its evidence can carry.
**One recommended edit:** replace the CPC chain with the exact
$\mathcal{L}^{\mathrm{opt}}_N = \log N - I(x_v;x_t) + I(X;x_v)$ derivation, which needs no
approximation, no side condition, and no Note.
