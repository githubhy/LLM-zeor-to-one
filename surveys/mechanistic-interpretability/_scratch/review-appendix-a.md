# Independent re-derivation — appendix-a-transformer-circuits-math.md (A.5–A.9, eq. 7–17)

`[opt:MATH-REDERIVE]` adversarial review. **Phase 1 was written before the target file was
opened.** Reviewer: independent agent, Opus. Date: 2026-08-15.

Setting throughout: decoder-only transformer, residual width $d$, per-head width $d_{head}$,
$h$ heads, context $n$ (or $n_{ctx}$).

---

## Phase 1 — derivation from first principles (target NOT yet read)

### A1 — Softmax as the entropy-regularized relaxation of hard retrieval

**Program.** For scores $s\in\mathbb R^n$ and $\tau>0$,

$$p^\star=\arg\max_{p\in\Delta^{n-1}} f(p),\qquad f(p)=\sum_j p_j s_j+\tau H(p),\quad H(p)=-\sum_j p_j\log p_j,$$

with $\Delta^{n-1}=\{p:p_j\ge0,\ \sum_j p_j=1\}$ and the convention $0\log0=0$.

**Existence.** $f$ is continuous on the compact set $\Delta^{n-1}$, so a maximizer exists.

**(a) Are the non-negativity constraints active?** *They are inactive, and this must be argued,
not assumed.* The mechanism is that entropy has an **infinite inward gradient at the boundary**:
$\partial H/\partial p_j=-\log p_j-1\to+\infty$ as $p_j\to0^+$. Concretely, take any $p$ with
$p_j=0$ and $p_k>0$, and move mass $\varepsilon$ from $k$ to $j$:

$$\Delta f=\varepsilon(s_j-s_k)\;+\;\tau\big[-\varepsilon\log\varepsilon-(p_k-\varepsilon)\log(p_k-\varepsilon)+p_k\log p_k\big]
=\;-\tau\varepsilon\log\varepsilon+O(\varepsilon).$$

Since $-\varepsilon\log\varepsilon\gg\varepsilon$ as $\varepsilon\to0^+$, $\Delta f>0$ for all
sufficiently small $\varepsilon$ regardless of the sign of $s_j-s_k$. So **no maximizer has a zero
coordinate**; every maximizer is in the relative interior and the inequality constraints are
never active. Entropy acts as a barrier. Only then may the KKT inequality multipliers be dropped.
*(This is exactly what fails for other regularizers: with $-\tfrac12\|p\|_2^2$ in place of $H$ the
boundary gradient is finite, constraints DO activate, and the solution is **sparsemax**, not
softmax.)*

**Stationarity.** With only the equality constraint,
$L=\sum_j p_js_j-\tau\sum_j p_j\log p_j-\lambda(\sum_j p_j-1)$,

$$\frac{\partial L}{\partial p_j}=s_j-\tau(\log p_j+1)-\lambda=0
\;\Longrightarrow\; p_j=\exp\!\Big(\frac{s_j-\lambda}{\tau}-1\Big)
\;\Longrightarrow\; p_j=\frac{e^{s_j/\tau}}{\sum_k e^{s_k/\tau}}=\operatorname{softmax}(s/\tau)_j.$$

**(b) Unique global maximum — the concavity argument.** The linear term is affine (concave, not
strictly). $H$ is **strictly** concave on $\Delta^{n-1}$: on the relative interior its Hessian is
$-\operatorname{diag}(1/p_j)\prec0$, negative definite *on the whole tangent space* and in
particular on the constraint subspace $\{v:\mathbf 1^\top v=0\}$; and strict concavity extends to
the closed simplex by continuity. Hence $f$ is strictly concave for $\tau>0$, so the maximizer is
unique and the (unique) stationary point is the global maximum. **The hypothesis $\tau>0$ is
load-bearing** — at $\tau=0$ the objective is linear and the maximizer set is the whole face
spanned by $\arg\max_j s_j$.

**(c) Limits.**
- $\tau\to0^+$: $p^\star\to$ uniform on $\arg\max_j s_j$; a point mass iff the argmax is unique.
  This is hard retrieval — the relaxation's namesake.
- $\tau\to\infty$: $p^\star\to(1/n,\dots,1/n)$, uniform; the entropy term dominates and the scores
  are ignored.
- Note $\operatorname{softmax}(s/\tau)$ means the $1/\sqrt{d_k}$ scaling of attention **is** a
  temperature choice: unscaled dot products at $\tau=\sqrt{d_k}$ $\equiv$ scaled dot products at
  $\tau=1$. Worth stating explicitly; the two readings are the same object.

**(d) "Softmax is the UNIQUE maximizer" — does it hold?** *Yes for the stated program, and it is
an overstatement only if the scope is widened.* Precisely:
- ✅ For fixed $\tau>0$ and **this** objective, softmax is the unique maximizer (by (b)).
- ❌ Softmax is **not** uniquely characterized as "the" attention nonlinearity. The uniqueness is
  conditional on choosing Shannon entropy as the regularizer. Swap it and you get a different,
  equally-principled map: $-\tfrac12\|p\|_2^2\Rightarrow$ **sparsemax**; Tsallis
  $\alpha$-entropy $\Rightarrow$ **$\alpha$-entmax** (with $\alpha=1$ recovering softmax,
  $\alpha=2$ sparsemax). Any language of the form "softmax is forced" / "the only choice" is an
  OVERSTATEMENT; "softmax is what the *Shannon*-entropy regularizer forces" is correct.

---

### A2 — Softmax Jacobian and its trace

$p=\operatorname{softmax}(z)$, $p_i=e^{z_i}/Z$, $Z=\sum_k e^{z_k}$.

$$\frac{\partial p_i}{\partial z_j}=\frac{\delta_{ij}e^{z_i}Z-e^{z_i}e^{z_j}}{Z^2}=p_i\delta_{ij}-p_ip_j.$$

**Claim-by-claim verdict** (each verified independently; numerics in
`Numerical verification` below):

| # | Claim | Verdict | Note |
|---|---|---|---|
| 1 | $J=\operatorname{diag}(p)-pp^\top$ | ✅ TRUE | central-difference check: max abs err $4.2\times10^{-11}$ |
| 2 | $J$ is exactly $\operatorname{Cov}(e_I)$, $I\sim p$ | ✅ TRUE, exactly | $\mathbb E[e_I]=p$, $\mathbb E[e_Ie_I^\top]=\sum_j p_je_je_j^\top=\operatorname{diag}(p)$, so $\operatorname{Cov}=\operatorname{diag}(p)-pp^\top=J$ |
| 3 | $J\succeq0$ | ✅ TRUE | $v^\top Jv=\sum_jp_jv_j^2-(\sum_jp_jv_j)^2=\operatorname{Var}_p(v_I)\ge0$ (Jensen). Also immediate from #2 |
| 4 | $J\mathbf 1=0$ | ✅ TRUE | $J\mathbf 1=p-p(\mathbf 1^\top p)=p-p=0$. So $J$ is singular; $\operatorname{rank}J=\lvert\operatorname{supp}p\rvert-1$ |
| 5 | $\operatorname{tr}J=1-\lVert p\rVert_2^2$ | ✅ TRUE | $\sum_j(p_j-p_j^2)=1-\sum_jp_j^2$ |
| 6 | $\lVert J\rVert_2\le\operatorname{tr}J$ | ✅ TRUE **under PSD** | For PSD, $\lVert J\rVert_2=\lambda_{\max}\le\sum_i\lambda_i=\operatorname{tr}J$. **The PSD hypothesis is essential** and must be stated — the inequality is false for general matrices. See the tightness caveat below |
| 7 | $\operatorname{tr}J$ maximal at uniform, value $1-1/n$ | ✅ TRUE | maximize $1-\lVert p\rVert_2^2$ $\Leftrightarrow$ minimize $\lVert p\rVert_2^2$ on the simplex; strictly convex, unique minimizer $p=\mathbf 1/n$, value $1/n$ |
| 8 | $\operatorname{tr}J=0$ iff $p$ is a point mass | ✅ TRUE | $\lVert p\rVert_2^2\le\lVert p\rVert_1\lVert p\rVert_\infty=\lVert p\rVert_\infty\le1$, equality iff $\lVert p\rVert_\infty=1$ |

**Tightness caveat on #6 (worth flagging if the target leans on it).** $\lVert J\rVert_2=\operatorname{tr}J$
iff $\operatorname{rank}J\le1$ iff $\lvert\operatorname{supp}p\rvert\le2$. So the bound is **exactly
tight in the two-way-competition case** but **loose by a factor $\approx n$ for diffuse $p$**:
at uniform $p$, $\lambda_{\max}=1/n$ while $\operatorname{tr}J=1-1/n$ (measured ratios: $n=5\to4.0$,
$n=100\to99.0$). Consequence: using $\operatorname{tr}J$ as a *proxy for gradient magnitude* is an
**upper bound only**, and a bad one when attention is spread out. It is a fine proxy for the
saturated / two-way regime the appendix is presumably discussing.

**Two-outcome competition with score gap $\Delta$.** $p_1=\sigma(\Delta)=(1+e^{-\Delta})^{-1}$,
$p_2=1-p_1$, so

$$\operatorname{tr}J=1-p_1^2-p_2^2=2p_1p_2=2\sigma(\Delta)\big(1-\sigma(\Delta)\big)=2\sigma'(\Delta)=\tfrac12\operatorname{sech}^2(\Delta/2).$$

Sanity: $\Delta=0\Rightarrow\operatorname{tr}J=0.5=1-1/n$ with $n=2$ ✓ (matches claim #7).

| $\Delta$ | $p_1$ | $\operatorname{tr}J$ (4 s.f.) |
|---|---|---|
| $0$ | $0.5$ | $\mathbf{0.5000}$ |
| $1.414$ ($\approx\sqrt2$) | $0.80440$ | $\mathbf{0.3147}$ |
| $8.0$ | $0.99966$ | $\mathbf{6.705\times10^{-4}}$ |
| $11.314$ ($\approx8\sqrt2$) | $0.999988$ | $\mathbf{2.440\times10^{-5}}$ |

**Ratios I get** (these are the ones to check the target's "$\approx1.3\times10^4$" against):

- $\operatorname{tr}J(1.414)/\operatorname{tr}J(11.314)=\mathbf{1.290\times10^4}$ (12896.3)
- exact-argument version $\operatorname{tr}J(\sqrt2)/\operatorname{tr}J(8\sqrt2)=\mathbf{1.289\times10^4}$ (12890.9)
- $\operatorname{tr}J(1.414)/\operatorname{tr}J(8.0)=4.693\times10^2$ (a *different* comparison — flag if conflated)
- $\operatorname{tr}J(0)/\operatorname{tr}J(11.314)=2.049\times10^4$

So **"a factor of roughly $1.3\times10^4$" is correct** for the $\sqrt2$-vs-$8\sqrt2$ comparison
(true value $1.29\times10^4$, so "roughly 1.3e4" rounds honestly). It would be **wrong** if the
target instead compares $\sqrt2$ against $8.0$, or uniform ($\Delta=0$) against $8\sqrt2$.

**Basis note `[opt:MATH-BASIS]`:** $\Delta$ must be declared as the gap in **scaled** (post-$1/\sqrt{d_k}$)
or **unscaled** score units. $1.414$ is the scaled gap sd; $11.314$ is the unscaled gap sd. Comparing
$\operatorname{tr}J$ at those two numbers is a comparison of *with-scaling vs without-scaling*, and
that must be said, or the reader reads it as a claim about two different score gaps in one basis.

---

### A3 — Variance of a dot product

$q\cdot k=\sum_{i=1}^{d_k}q_ik_i$. Assumed: every component of $q$ and of $k$ has mean $0$,
variance $1$.

**Mean.** $\mathbb E[q\cdot k]=\sum_i\mathbb E[q_ik_i]$. This is $0$ **only if $q_i$ and $k_i$ are
uncorrelated** — i.e. the *cross*-vector assumption is already consumed here.

**Second moment.**
$$\operatorname{Var}(q\cdot k)=\mathbb E\Big[\big(\textstyle\sum_iq_ik_i\big)^2\Big]=\sum_{i,j}\mathbb E[q_iq_jk_ik_j].$$

Now the two hypotheses enter at *different* points:

1. **$q\perp k$ (cross-vector independence) — LOAD-BEARING, used twice.** It gives
   $\mathbb E[q_iq_jk_ik_j]=\mathbb E[q_iq_j]\,\mathbb E[k_ik_j]$ (the 4th cross-moment
   factorization) and, above, $\mathbb E[q_ik_i]=0$. *Yes, independence of $q$ **from** $k$ is
   needed.* **Counterexample proving it is not removable:** take $k=q$ with $q$ standard Gaussian.
   Then $q\cdot k=\lVert q\rVert^2\sim\chi^2_{d_k}$, whose variance is $2d_k$, not $d_k$ — off by
   a factor 2. The technically minimal version is weaker than full independence: it suffices that
   $\mathbb E[q_iq_jk_ik_j]=\mathbb E[q_iq_j]\mathbb E[k_ik_j]$ for all $i,j$ and
   $\mathbb E[q_ik_i]=0$.
2. **Within-vector structure — WEAKER than usually stated.** After factorization we need only
   $\mathbb E[q_iq_j]=\delta_{ij}$ and $\mathbb E[k_ik_j]=\delta_{ij}$, i.e. **pairwise
   uncorrelatedness + unit variance within each vector**. Full independence of the components
   *within* a vector is **not** consumed anywhere. Any text that says "assume the components are
   independent" is stating a hypothesis stronger than the proof uses; that is a NIT unless the
   text claims the assumption is necessary.

$$\operatorname{Var}(q\cdot k)=\sum_{i,j}\delta_{ij}\delta_{ij}=\sum_{i=1}^{d_k}1=d_k.$$

**Numbers at $d_k=64$.**
- sd of a **single** score: $\sqrt{d_k}=\mathbf{8.000}$.
- sd of the **gap** between two scores: $\operatorname{Var}(s_1-s_2)=2d_k=128$, so
  $\sqrt{2d_k}=\mathbf{11.3137}$ (4 s.f. $11.31$).
- After the $1/\sqrt{d_k}$ scaling the gap sd is $\sqrt{2d_k}/\sqrt{d_k}=\sqrt2=\mathbf{1.4142}$ —
  **independent of $d_k$**, which is the whole point of the scaling.

**UNSTATED-HYPOTHESIS trap to check in the target.** $s_1=q\cdot k_1$ and $s_2=q\cdot k_2$ are
**not independent** — they share the query $q$. Calling them "two independent scores" is wrong as
stated. What is actually true, and all the derivation needs, is that they are **uncorrelated**:
$\mathbb E[s_1s_2]=\sum_{i,j}\mathbb E[q_iq_j]\mathbb E[k_{1i}]\mathbb E[k_{2j}]=0$ when
$k_1\perp k_2$ and both are mean-zero. Uncorrelatedness suffices for
$\operatorname{Var}(s_1-s_2)=\operatorname{Var}s_1+\operatorname{Var}s_2$. So the *number* $\sqrt{2d_k}$
is right; the word "independent" is the defect.

---

### A4 — Concatenation of heads equals a sum of per-head terms

**Row-token layout.** $H_i\in\mathbb R^{n\times d_{head}}$ (row $t$ = head $i$'s output at token
$t$). Concatenation on the feature axis: $C=[H_1\mid\cdots\mid H_h]\in\mathbb R^{n\times hd_{head}}$.
$W^O\in\mathbb R^{hd_{head}\times d}$, partitioned by **rows** into $h$ vertically-stacked blocks
$W^O_{[i]}\in\mathbb R^{d_{head}\times d}$.

**Proof.** Index $m\in[1,hd_{head}]$ as $m=(i-1)d_{head}+a$, $a\in[1,d_{head}]$. Then
$C_{t,m}=(H_i)_{t,a}$ and $W^O_{m,c}=(W^O_{[i]})_{a,c}$, so

$$(CW^O)_{t,c}=\sum_{m=1}^{hd_{head}}C_{t,m}W^O_{m,c}
=\sum_{i=1}^{h}\sum_{a=1}^{d_{head}}(H_i)_{t,a}(W^O_{[i]})_{a,c}
=\sum_{i=1}^{h}\big(H_iW^O_{[i]}\big)_{t,c}. \qquad\blacksquare$$

Hence $\operatorname{Concat}(H_1,\dots,H_h)\,W^O=\sum_{i=1}^h H_iW^O_{[i]}$.

**Shapes that make it work:** $H_i:n\times d_{head}$; $C:n\times hd_{head}$;
$W^O:hd_{head}\times d$ (typically $hd_{head}=d$, but the identity does **not** require it);
$W^O_{[i]}:d_{head}\times d$; every summand $n\times d$.

**CONVENTION WARNING (`[opt:MATH-BASIS]`).** "Partitioned by ROWS" is correct **only** in the
row-token layout. In the column-vector layout ($x\in\mathbb R^d$ a column, $W^O\in\mathbb R^{d\times hd_{head}}$)
the identical statement requires partitioning $W^O$ by **columns**. A document that mixes layouts
between sections and says "rows" in both is wrong in one of them. The two must be declared.

**Interpretive payload (correct):** the residual-stream update is an unweighted **sum** of $h$
independent per-head terms, each of which reads and writes through its own $d_{head}$-dim
subspace. Heads are additive; $W^O$ does not mix them.

---

### A5 — Rank bounds on $W_{QK}$ and $W_{OV}$

$W_Q,W_K,W_V\in\mathbb R^{d_{head}\times d}$, $W_O\in\mathbb R^{d\times d_{head}}$; take
$d_{head}\le d$.

$$W_{QK}=W_Q^\top W_K\in\mathbb R^{d\times d},\qquad W_{OV}=W_OW_V\in\mathbb R^{d\times d}.$$

**Upper bound.** $\operatorname{rank}(AB)\le\min(\operatorname{rank}A,\operatorname{rank}B)$, and
each factor has rank $\le\min(d_{head},d)=d_{head}$. Hence
$\operatorname{rank}W_{QK}\le d_{head}$ and $\operatorname{rank}W_{OV}\le d_{head}$. Both are
$d\times d$ matrices with at most $d_{head}$ nonzero singular values.

**Is it exactly $d_{head}$?** *Only under a full-rank hypothesis.* By Sylvester's rank inequality
with inner dimension $d_{head}$: $\operatorname{rank}(W_Q^\top W_K)\ge r_Q+r_K-d_{head}$. If both
factors have full row rank $r_Q=r_K=d_{head}$, this gives $\ge d_{head}$, so equality:
$\operatorname{rank}W_{QK}=d_{head}$ **exactly**. Otherwise it can be anything down to
$\max(0,r_Q+r_K-d_{head})$.

**Verdict:** the honest statement is **"at most $d_{head}$; exactly $d_{head}$ generically (i.e.
iff both factors have full row rank)"**. Writing "the rank IS $d_{head}$" without the hypothesis
is an OVERSTATEMENT — and a substantive one for interpretability, since trained weights are not
guaranteed full rank and their *effective* rank (spectrum decay) is typically lower than the
algebraic rank. This matters for any downstream claim about "the head's $d_{head}$-dimensional
subspace".

**Ratio $d_{head}/d$ in real models** (to check any "1/10 to 1/100" claim):

| Model | $d$ | $h$ | $d_{head}$ | $d_{head}/d$ |
|---|---|---|---|---|
| GPT-2 small | 768 | 12 | 64 | 1/12 |
| GPT-2 medium | 1024 | 16 | 64 | 1/16 |
| GPT-2 large | 1280 | 20 | 64 | 1/20 |
| GPT-2 XL | 1600 | 25 | 64 | 1/25 |
| Llama-2-7B | 4096 | 32 | 128 | 1/32 |
| Llama-2-70B | 8192 | 64 | 128 | 1/64 |
| GPT-3 175B | 12288 | 96 | 128 | 1/96 |

**"1/10 to 1/100" is a fair and honest bracket** across this family (observed span 1/12 – 1/96).
Two caveats worth stating if the target does not: (i) the ratio is exactly $1/h$ whenever
$hd_{head}=d$, so the claim is really a statement about head counts, not about widths; (ii) it
breaks under GQA/MQA, where the *KV* head count differs from $h$ — the $d_{head}/d$ ratio for the
QK circuit is unchanged but the number of distinct OV subspaces is not.

---

### A6 — Tensor form and the "independent factors" claim

**Row-token layout**, $X\in\mathbb R^{n_{ctx}\times d}$ with rows $x_j^\top$, attention pattern
$A\in\mathbb R^{n_{ctx}\times n_{ctx}}$, $W_{OV}\in\mathbb R^{d\times d}$.

**Derivation.** Row $i$ of the head output is $y_i=\sum_j A_{ij}W_{OV}x_j$ (a column vector).
Transposing, $y_i^\top=\sum_jA_{ij}x_j^\top W_{OV}^\top$. Row $i$ of $AX$ is
$\sum_jA_{ij}x_j^\top$. Right-multiplying that by $W_{OV}^\top$ gives exactly $y_i^\top$. Stacking
over $i$:

$$Y=A\,X\,W_{OV}^\top,\qquad A:n_{ctx}\times n_{ctx},\ X:n_{ctx}\times d,\ W_{OV}^\top:d\times d.\qquad\blacksquare$$

Equivalently, as an operator on $\operatorname{vec}(X)$, the head is the **pure tensor**
$A\otimes W_{OV}$: $A$ acts on the position index, $W_{OV}$ on the feature index.

**Does "the attention pattern and the OV map are independent factors" follow from left/right
multiplication commuting?** **No — this argument is a non sequitur, and the conclusion as usually
worded is an overstatement.** Three separate points:

1. **The stated mechanism is wrong.** $(AX)W^\top=A(XW^\top)$ is *associativity*, which holds for
   every matrix triple whatsoever and therefore carries no information about this head. The real
   content is that the operator is a **single pure tensor** $A\otimes W_{OV}$ rather than a sum
   $\sum_r A_r\otimes W_r$ — i.e. it is rank-1 in the operator tensor product. That is a genuine
   structural fact; associativity is bookkeeping.
2. **"Independent" is false at the function level.** $A$ is itself a function of $X$:
   $A=\operatorname{softmax}\!\big(\text{mask}+XW_{QK}^\top X^\top/\sqrt{d_k}\big)$. So the head's
   input–output map is *not* a fixed linear operator and the two "factors" are not independent as
   functions of the input. The factorization holds **conditional on $A$** — the frozen-attention-
   pattern linearization. That hypothesis must be stated; it is the same "if we freeze the
   attention patterns, the transformer becomes linear" move the circuits literature makes
   explicitly.
3. **What IS defensibly independent:** the *parameters*. $A$ depends on $\{W_Q,W_K\}$ only, and
   the value-write map on $\{W_V,W_O\}$ only — disjoint parameter sets, no shared weights. That
   is the strong, true version of the claim, and it does not need any commutation argument.

**Correct wording:** "conditional on the attention pattern, the head acts as $A\otimes W_{OV}$ —
a pure tensor whose two factors are parameterized by disjoint weight sets, so *where* a head
reads and *what* it writes are governed by separate circuits."

---

### A7 — LayerNorm as projection + scalar rescale

$$\mathrm{LN}(x)=\gamma\odot\frac{x-\mu(x)\mathbf 1}{\sigma(x)}+\beta,\qquad
\mu(x)=\frac1d\sum_ix_i,\quad \sigma(x)=\sqrt{\frac1d\sum_i(x_i-\mu)^2},\qquad
P=I-\frac1d\mathbf 1\mathbf 1^\top.$$

**$P$ is the orthogonal projector onto $\mathbf 1^\perp$.** Symmetric ✓; and using
$\mathbf 1^\top\mathbf 1=d$,

$$P^2=I-\frac2d\mathbf 1\mathbf 1^\top+\frac1{d^2}\mathbf 1(\mathbf 1^\top\mathbf 1)\mathbf 1^\top
=I-\frac2d\mathbf 1\mathbf 1^\top+\frac1d\mathbf 1\mathbf 1^\top=P.$$

And $Px=x-\mu\mathbf 1$ ✓.

**The $\sigma=\lVert Px\rVert_2/\sqrt d$ step, checked carefully.** $\lVert Px\rVert_2^2=\sum_i(x_i-\mu)^2$
— this is the **un-normalized** sum of squares. The $1/d$ *is* inside the standard deviation
(LayerNorm uses the population/biased variance $\frac1d\sum$, not the sample $\frac1{d-1}\sum$).
Hence $\sigma^2=\lVert Px\rVert_2^2/d$ and

$$\sigma(x)=\frac{\lVert Px\rVert_2}{\sqrt d}\quad\Longrightarrow\quad
\frac{x-\mu\mathbf 1}{\sigma(x)}=\frac{Px}{\lVert Px\rVert_2/\sqrt d}=\sqrt d\,\frac{Px}{\lVert Px\rVert_2}.$$

The $\sqrt d$ ends up in the **numerator** of the normalized vector, i.e. LN maps onto the sphere
of radius $\sqrt d$ inside $\mathbf 1^\perp$. ✓ So

$$\boxed{\ \mathrm{LN}(x)=\gamma\odot\Big(\sqrt d\,\frac{Px}{\lVert Px\rVert_2}\Big)+\beta\ }$$

**Hypotheses this exact identity consumes** (all must be stated):
- $Px\ne0$, i.e. $x$ is not a constant vector (else $\sigma=0$ and LN is undefined).
- $\epsilon=0$. Real implementations use $\sqrt{\sigma^2+\epsilon}$ (or $\sqrt{\lVert Px\rVert^2/d+\epsilon}$),
  which makes the identity **approximate**, not exact. If the target calls it "exact", the
  $\epsilon$ must be declared as excluded.
- The biased ($\frac1d$) variance. With $\frac1{d-1}$ the constant becomes $\sqrt{d-1}$.
- **RMSNorm is a different object**: it omits the mean subtraction, i.e. drops $P$ entirely
  ($\mathrm{RMSNorm}(x)=\gamma\odot\sqrt d\,x/\lVert x\rVert$). Most modern LLMs (Llama, PaLM,
  Gemma) use RMSNorm, so a claim scoped to "LayerNorm in LLMs" needs that caveat.

**First-order relative error of freezing the scale.** Let $s(x)=\lVert Px\rVert_2$ and freeze at
$s_0=\lVert Px_0\rVert$. Perturb $x=x_0+\delta$:

$$s(x_0+\delta)=\sqrt{\lVert Px_0\rVert^2+2\langle Px_0,P\delta\rangle+\lVert P\delta\rVert^2}
=s_0\sqrt{1+\frac{2\langle Px_0,P\delta\rangle}{s_0^2}+\frac{\lVert P\delta\rVert^2}{s_0^2}}$$
$$=s_0\Big(1+\frac{\langle Px_0,P\delta\rangle}{s_0^2}+O\big(\lVert P\delta\rVert^2/s_0^2\big)\Big).$$

So the relative error of freezing is

$$\varepsilon(\delta)=\frac{s(x_0+\delta)-s_0}{s_0}\approx\frac{\langle Px_0,P\delta\rangle}{\lVert Px_0\rVert^2}
=\frac{\lVert Px_0\rVert\,\lVert P\delta\rVert\cos\theta}{\lVert Px_0\rVert^2}
=\frac{\lVert P\delta\rVert}{\lVert Px_0\rVert}\cos\theta.$$

**Expansion: correct.** **Final equality: correct — and $\theta$ MUST be the angle between
$Px_0$ and $P\delta$, i.e. between the *projected* vectors.** This is load-bearing, not pedantry:
a perturbation $\delta\parallel\mathbf 1$ has $P\delta=0$, so it has exactly zero effect (LN is
exactly invariant to mean shifts) — the projected-angle form captures that, an unprojected
$\angle(x_0,\delta)$ does not. If the target writes "$\theta$ = the angle between $x_0$ and
$\delta$" that is an **ERROR**.

Two further points to check against the target:
- $\langle Px_0,P\delta\rangle=\langle Px_0,\delta\rangle$ (since $P=P^\top=P^2$), so one $P$ may
  be dropped **inside the inner product** but **not** in the $\lVert P\delta\rVert\cos\theta$ form.
- The error is **first order** in $\lVert P\delta\rVert/\lVert Px_0\rVert$, not second order. So
  frozen-LN is a *controlled* approximation only for $\lVert P\delta\rVert\ll\lVert Px_0\rVert$,
  and it is **exact** only when $P\delta\perp Px_0$. Any claim that freezing the scale is "nearly
  free" needs that magnitude condition attached.

---

### Numerical verification (Phase 1, independent of the target)

Run with `numpy`, seed `default_rng(0)`, $n=7$, random logits:

```
J vs central-difference Jacobian: max|J - J_fd| = 4.20e-11        -> claim 1 ✓
eigenvalues of J: min = -4.2e-17 (i.e. 0), max = 0.30749           -> PSD ✓
|J @ 1|_inf = 5.55e-17                                             -> J1 = 0 ✓
tr(J) = 0.60725095107, 1 - ||p||^2 = 0.60725095107                 -> claim 5 ✓
||J||_2 = 0.30749 <= tr(J) = 0.60725                               -> claim 6 ✓
uniform p: n=2  tr=0.500000 (1-1/n ✓)  lam_max=0.500000  tr/lam = 1.00
           n=5  tr=0.800000 (1-1/n ✓)  lam_max=0.200000  tr/lam = 4.00
           n=100 tr=0.990000 (1-1/n ✓) lam_max=0.010000  tr/lam = 99.0
support-size-2 p: lam_max = tr = 0.42, rank(J) = 1                 -> tightness ✓
```

Two-outcome $\operatorname{tr}J$ and ratios (see A2 table). $\sqrt{d_k}=8.000$,
$\sqrt{2d_k}=11.3137$, $\sqrt{2d_k}/\sqrt{d_k}=1.41421$.

---

## Phase 2 — comparison against the target

Target: `surveys/mechanistic-interpretability/appendix-a-transformer-circuits-math.md`,
§A.5–§A.9, equations 7–17. §A.1–§A.4 read as context only.

**Headline.** The mathematics is in good shape. Every displayed equation 7–17 is **correct as
written** and matches my independent derivation line for line, including both quoted numerics
($\operatorname{tr}J=2.44\times10^{-5}$ and $0.315$ — I get $2.4408\times10^{-5}$ and $0.31465$).
The findings below are concentrated in the **prose glosses around the equations**, which is the
class an arithmetic oracle cannot see: two glosses state the right formula and then describe it
in the wrong basis, and one argument reaches a true conclusion by an invalid route.

Counts: **3 ERROR**, **4 UNSTATED HYPOTHESIS**, **3 OVERSTATEMENT**, **5 NIT**.

---

### E1 — ERROR (high) · §A.8 line 195 · $\theta$ is the angle between the PROJECTED vectors

**Target text:** "with $\theta$ the angle between the component's write and the current stream
direction."

**What I derived.** Equation (17) itself is exactly right. But the identity
$\langle P\mathbf x_0,P\boldsymbol\delta\rangle=\lVert P\mathbf x_0\rVert\lVert P\boldsymbol\delta\rVert\cos\theta$
forces $\theta=\angle(P\mathbf x_0,\,P\boldsymbol\delta)$ — the angle **after** mean-centering.
The gloss names $\angle(\mathbf x_0,\boldsymbol\delta)$, the angle before projection. These are
different angles and the substitution is not benign.

**Why it is load-bearing, not pedantry.** A write $\boldsymbol\delta\parallel\mathbf 1$ has
$P\boldsymbol\delta=0$, so LayerNorm is **exactly** invariant to it at all orders — yet
$\angle(\boldsymbol\delta,\mathbf x_0)$ can take any value. The projected form predicts zero error;
the stated form predicts an arbitrary one.

**It corrupts the section's actionable conclusion.** The very next sentence — "Direct logit
attribution is exact to first order for a component written *orthogonally* to the present residual
direction" — hands the practitioner the wrong test. The correct criterion is
$P\boldsymbol\delta\perp P\mathbf x_0$ (orthogonal after mean-centering), **not**
$\boldsymbol\delta\perp\mathbf x_0$. One $P$ may legitimately be dropped inside the inner product
($\langle P\mathbf x_0,P\boldsymbol\delta\rangle=\langle P\mathbf x_0,\boldsymbol\delta\rangle$, by
$P=P^\top=P^2$) — but that leaves $\langle P\mathbf x_0,\boldsymbol\delta\rangle$, never
$\langle\mathbf x_0,\boldsymbol\delta\rangle$. Both projectors cannot go.

**Propagation.** §A.9 line 212 makes eq (17) the inherited caveat for *every* DLA-based claim in
the survey, so the wrong criterion propagates corpus-wide.

**Correction.** "…with $\theta$ the angle between the **mean-centred** component write
$P\boldsymbol\delta$ and the **mean-centred** stream state $P\mathbf x_0$" and "…exact to first
order for a component whose mean-centred write is orthogonal to the mean-centred residual
direction (equivalently, $\langle P\mathbf x_0,\boldsymbol\delta\rangle=0$)."

---

### E2 — ERROR (high) · §A.6 line 147 · the $1.3\times10^{4}$ factor is stated in the wrong basis

**Target text:** "…$\operatorname{tr}(J)=2.44\times10^{-5}$ unscaled against $0.315$ scaled — a
factor of roughly $1.3\times10^{4}$ **in the gradient that reaches the query and key matrices** at
a one-standard-deviation score gap."

**What I derived.** The two $\operatorname{tr}J$ values and their ratio are right — I independently
get $2.4408\times10^{-5}$, $0.31465$, ratio $1.289\times10^{4}$, so "roughly $1.3\times10^{4}$" is
honest rounding. **But that ratio is $\partial\mathbf p/\partial\mathbf z$ — the sensitivity to the
softmax INPUT.** The gradient reaching $W_Q$ and $W_K$ flows through the raw dot product
$u=\mathbf q\cdot\mathbf k$, and the two architectures differ in that link as well:

| architecture | $\partial\mathbf z/\partial u$ | sensitivity scale $\partial\mathbf p/\partial u$ |
|---|---|---|
| unscaled | $1$ | $2.4408\times10^{-5}$ |
| scaled | $1/\sqrt{d_k}=1/8$ | $0.31465/8=3.9331\times10^{-2}$ |

Ratio in the $W_Q,W_K$ basis: $\mathbf{1.61\times10^{3}}$, **not** $1.3\times10^{4}$. The two
differ by exactly $\sqrt{d_k}=8$ — the scaling that buys the Jacobian back also attenuates the
chain rule, and the sentence claims the pre-attenuation figure post-attenuation. This is
`.claude/rules/calibration-residuals.md` check 4 / `[opt:MATH-BASIS]` precisely: a number correct
on one basis, attributed on another.

**The conclusion survives untouched** — $1.6\times10^{3}$ is still three orders of magnitude, so
"extremely small gradients" is fully vindicated. Only the number's basis is wrong.

**Correction (either is fine, but the basis must be named):**
- keep the number, fix the basis: "…a factor of roughly $1.3\times10^{4}$ **in the softmax
  Jacobian**, i.e. in the sensitivity of the attention pattern to its scores"; **or**
- keep the claim, fix the number: "…the gradient reaching $W_Q$ and $W_K$ is smaller by a factor
  of roughly $1.6\times10^{3}$ (the Jacobian ratio $1.3\times10^{4}$ divided by the $\sqrt{d_k}$
  that the scaling itself contributes to the chain rule)".

The second is stronger — it is the only place in the appendix where the two bases could be
confused, and stating both is the [MATH-BASIS] declaration the appendix already commits to at
line 12.

---

### E3 — ERROR (med) · §A.7 line 172 · "left and right multiplication always commute" is a vacuous premise

**Target text:** "Left and right multiplication always commute — $(AX)W_{OV}^{\top}=A(XW_{OV}^{\top})$
— so **where a head attends and what it moves are mathematically independent factors**."

**What I derived.** That displayed identity is *associativity of matrix multiplication*. It holds
for **every** conformable triple of matrices whatsoever, so it cannot distinguish an attention head
from any other product of three matrices and carries zero information about this operation. A
premise true of everything cannot support a conclusion true of something. (It is also not
"commutation" — nothing commutes here; the factors act on different indices.)

**The right argument, which reaches the same place.** The head's action on $\operatorname{vec}(X)$
is the **pure tensor** $A\otimes W_{OV}$ — rank one in the operator tensor product — rather than a
sum $\sum_r A_r\otimes W_r$. *That* is a non-trivial structural property of attention and it is
what licenses studying the two factors separately. The appendix already writes the tensor in
eq (15); the argument is one sentence away and currently rests on a triviality instead.

**Correction.** "…the head's action is a *single* tensor product $A\otimes W_{OV}$ — one operator
on the position index, one on the feature index — rather than an entangled sum of such products.
That is what lets each factor be studied with the other held fixed."

---

### U1 — UNSTATED HYPOTHESIS (med) · §A.6 line 147 · the two competing scores are not independent

**Target text:** "The gap between two competing *unscaled* scores is a difference of two such dot
products, with standard deviation $\sqrt{2d_k}\approx11.3$."

**What I derived.** $\sqrt{2d_k}=11.3137$ ✓ — the number is right. But the variance-addition step

$$\operatorname{Var}(s_1-s_2)=\operatorname{Var}(s_1)+\operatorname{Var}(s_2)$$

needs a joint hypothesis that the text supplies
nowhere. And the obvious one is **false**: $s_1=\mathbf q\cdot\mathbf k_1$ and
$s_2=\mathbf q\cdot\mathbf k_2$ **share the query**, so they are not independent.

What rescues it is that **uncorrelatedness suffices**, and uncorrelatedness does hold: with
$\mathbf k_1\perp\mathbf k_2$ both mean-zero,
$\mathbb E[s_1s_2]=\sum_{i,j}\mathbb E[q_iq_j]\mathbb E[k_{1i}]\mathbb E[k_{2j}]=0$.

This is the exact twin of the gap §A.9 line 208 congratulates itself on catching (the unstated
$\mathbf q\perp\mathbf k$). Having made that a headline finding, leaving its sibling silent one
section earlier is conspicuous.

**Correction.** "…a difference of two such dot products. The two scores share the query and so are
*not* independent, but under the same null model they are **uncorrelated** — which is all the
variance addition requires — giving standard deviation $\sqrt{2d_k}\approx11.3$."

---

### U2 — UNSTATED HYPOTHESIS (med) · §A.8 eq (16) · the $\epsilon$ and the biased variance

**Target text:** "$\sigma(\mathbf x)=\lVert P\mathbf x\rVert_2/\sqrt d$ **by definition of the
standard deviation**" and "attribution is exact there, with no approximation whatsoever".

**What I derived.** The step is right, and I checked the $\sqrt d$ placement specifically: the
$1/d$ **is** inside the standard deviation, $\sigma^2=\lVert P\mathbf x\rVert^2/d$, so
$\sigma=\lVert P\mathbf x\rVert/\sqrt d$ and the $\sqrt d$ lands in the numerator of the normalized
vector — LN maps onto the sphere of radius $\sqrt d$ in $\mathbf 1^{\perp}$. ✓ Confirmed.

Two hypotheses are hidden inside "by definition", and one of them is not universally true:

1. **Biased (population, $1/d$) variance.** With the sample ($1/(d-1)$) convention the constant is
   $\sqrt{d-1}$, not $\sqrt d$. PyTorch `nn.LayerNorm` uses biased, so the appendix is right — but
   "by definition" is doing the work of a convention declaration in an appendix that declares its
   other two conventions explicitly at line 12.
2. **$\epsilon=0$.** Real LayerNorm computes $\sqrt{\sigma^2+\epsilon}$ (PyTorch default
   $10^{-5}$). Equation (16) is then **approximate, not exact** — which matters because line 186
   sells exactness ("no approximation whatsoever") as the section's payload. Also eq (16) requires
   $P\mathbf x\ne\mathbf 0$; $\epsilon$ is exactly what keeps a constant-input token defined in
   practice.

Worth noting in the target's favour: the weaker claim "LN is exactly affine on every level set of
$\lVert P\mathbf x\rVert_2$" **does** survive $\epsilon>0$, since $\epsilon$ only changes the value
of the scalar, not its constancy on a level set. So the fix is narrow — attach $\epsilon$ to
eq (16), and keep the level-set claim as is.

---

### U3 — UNSTATED HYPOTHESIS (med) · §A.8 · scope is LayerNorm; most modern LLMs use RMSNorm

§A.8 is scrupulous about pre-LN vs post-LN (line 197, correctly sourced to the GPT-2 paper) but
never mentions **RMSNorm**, which drops the mean subtraction entirely — i.e. drops $P$, giving
$\gamma\odot\sqrt d\,\mathbf x/\lVert\mathbf x\rVert$. Llama, Mistral, Gemma and PaLM use it. Since
the whole payload of §A.8 is a DLA error term that §A.9 line 212 then applies to *every* DLA claim
in the survey — and § 9 is a cross-**model** section — the reader needs to know whether eq (17)
transfers. It mostly does (replace $P\to I$ throughout, and eq (17) becomes
$\langle\mathbf x_0,\boldsymbol\delta\rangle/\lVert\mathbf x_0\rVert^2$), which is a cheap sentence
to add and closes a real scope hole.

*(Flagged as a scope question — I did not read § 9 and am not asserting which models it covers.)*

---

### U4 — UNSTATED HYPOTHESIS (low) · §A.5 line 113 · the $\tau\to0$ limit on ties

"$\tau\to0$ recovers the hard lookup of Equation (7)" holds when the argmax is **unique**; on the
tie set the limit is uniform over $\arg\max_j s_j$, not a point mass. Measure-zero, and line 88
already flags the tie set as pathological for eq (7), so this is nearly self-consistent — but a
four-word parenthetical ("when the argmax is unique") would close it.

---

### O1 — OVERSTATEMENT (high) · §A.7 line 172 · "mathematically independent factors"

Separate from E3's broken *argument*, the *conclusion* is stronger than the mathematics supports.
$A$ is a **function of** $X$ — the appendix writes exactly that at line 12 and line 47,
$A=\operatorname{softmax}(XW_{QK}X^{\top}/\sqrt{d_k})$ — so as functions of the input the two are
not independent at all. The factorization holds **conditional on $A$**: it is the frozen-pattern
linearization, not an unconditional property.

The sentence "This is not a modelling convenience but a property of the operation" therefore has it
backwards, and the follow-on — "freezing $A$ at its observed values leaves a map that is exactly
linear in the values, **with no approximation in this factor at all**" — is true only under the
narrow reading "no approximation in the *OV* factor". The approximation is entirely in the frozen
$A$, and the sentence is positioned to read as though the freeze-attention trick were
approximation-free. §A.8 quantifies the frozen-*scale* error to first order and makes a virtue of
doing so; §A.7 asserts the frozen-*pattern* error away. The asymmetry stands out.

**What is genuinely independent, and needs no argument at all:** the **parameters**. $A$ depends
only on $\{W_Q,W_K\}$; the value-write depends only on $\{W_V,W_O\}$. Disjoint weight sets, no
sharing. That is the strong, true, citable claim.

**Correction.** "…so, *conditional on the attention pattern*, where a head attends and what it
moves are governed by disjoint parameter sets — $\{W_Q,W_K\}$ and $\{W_V,W_O\}$ share no weights —
and either can be studied with the other held fixed. The freeze-attention trick inherits exactly
one approximation, the frozen $A$; the OV factor contributes none."

---

### O2 — OVERSTATEMENT (med) · §A.5 line 113 · bilinearity does not close the *factored* form

**Target text:** "if the score is required to be bilinear in the two stream states … then
$s_{ij}=\langle W_Q\mathbf x_i,W_K\mathbf x_j\rangle=\mathbf x_i^{\top}W_{QK}\mathbf x_j$ **up to a
change of basis**."

**What I derived.** Bilinearity closes the form to $\mathbf x_i^{\top}M\mathbf x_j$ with
$M\in\mathbb R^{d\times d}$ **arbitrary** — full rank $d$ permitted. Writing $M=W_Q^{\top}W_K$ with
both factors in $\mathbb R^{d_{\text{head}}\times d}$ imposes $\operatorname{rank}M\le d_{\text{head}}$,
which is a **strictly stronger and logically independent** architectural choice — the low-rank
bottleneck the appendix itself makes a centrepiece of §A.7. Bilinearity does not imply it.

"Up to a change of basis" is also the wrong equivalence. Given $M$ of rank $r\le d_{\text{head}}$,
the factorization $M=W_Q^{\top}W_K$ exists but is non-unique under the gauge
$W_Q\mapsto S^{-\top}W_Q$, $W_K\mapsto SW_K$ for any $S\in GL(d_{\text{head}})$ — a gauge freedom
*inside the head*, not a change of basis of the residual stream. (This gauge is worth naming
anyway: it is why individual $W_Q$/$W_K$ entries are not interpretable while $W_{QK}$ is, which is
the standing justification for studying $W_{QK}$ as a single object.)

**Correction.** "…bilinearity closes the *form* to $\mathbf x_i^{\top}M\mathbf x_j$ for some
$M\in\mathbb R^{d\times d}$; the further factorization $M=W_{QK}=W_Q^{\top}W_K$ through a
$d_{\text{head}}$-dimensional bottleneck is a separate architectural choice, and one that costs
rank — see <!-- secref:A.7 -->§A.7. The factorization is unique only up to
$W_Q\mapsto S^{-\top}W_Q,\ W_K\mapsto SW_K$, which is why $W_{QK}$ and not its factors is the
interpretable object."

---

### O3 — OVERSTATEMENT (low) · §A.6 line 138/145 · $\operatorname{tr}J$ as "the total sensitivity"

The trace bound is used correctly and the PSD hypothesis is **explicitly named** at line 145
("Since $J\succeq0$, its spectral norm is bounded by its trace") — that is exactly right, and it is
the hypothesis most authors drop.

The unstated part is **tightness**. $\lVert J\rVert_2=\operatorname{tr}J$ iff
$\lvert\operatorname{supp}\mathbf p\rvert\le2$; for diffuse $\mathbf p$ the bound is loose by a
factor $\approx n$ (measured: at uniform $\mathbf p$, $\operatorname{tr}J/\lambda_{\max}$ is
$4.0$ at $n=5$ and $99.0$ at $n=100$). So $\operatorname{tr}J$ is an **upper bound** on
per-direction sensitivity, and calling it "the total sensitivity" (line 138) overstates it in the
spread-out regime.

**In the target's favour, and worth adding rather than removing:** §A.6's numerics are a
**two-way** competition, where the support has size 2 and the bound is **exactly tight** — I
verified $\lambda_{\max}=\operatorname{tr}J$ to machine precision at both $\Delta=1.4142$ and
$\Delta=11.3137$. So the section's use is not merely licensed, it is sharp. One clause converts a
loose-looking bound into a stated equality: "for a two-way competition the bound is an equality,
so the trace *is* the spectral norm here."

---

### NITs

- **N1 · §A.6 line 122 — hypothesis stronger than the proof consumes.** "Independence across
  coordinates makes the variances add" is sufficient but not necessary: given $\mathbf q\perp\mathbf k$,
  the derivation only needs $\mathbb E[q_iq_j]=\delta_{ij}$ and $\mathbb E[k_ik_j]=\delta_{ij}$ —
  pairwise **uncorrelatedness** within each vector. Since §A.9 makes a point of parsing the
  footnote's exact hypotheses, noting which are load-bearing is in character.
- **N2 · §A.6 line 138 — the justification for $J\mathbf 1=0$ is attached to the wrong fact.**
  "(the total probability cannot change)" is the reason for $\mathbf 1^{\top}J=0$ (column sums:
  probabilities always sum to one). $J\mathbf 1=0$ is the **row** sums, i.e. softmax's invariance
  under $\mathbf z\mapsto\mathbf z+c\mathbf 1$. $J$ is symmetric so both are true and the claim
  stands — only the stated mechanism is the other one's.
- **N3 · §A.7 eq (4) vs eq (14) — the symbol $\mathrm{head}$ denotes two different objects.** In
  eq (4) it is the **post**-$W_O$ write, a column vector in $\mathbb R^d$; in eq (14) it is the
  **pre**-$W_O$ per-head output, a matrix in $\mathbb R^{n\times d_v}$. Line 161 reconciles the
  *weights* ("the block $W^O_{[i]}$ is what §A.2 calls that head's $W_O^h$") but not the symbol.
  One clause. (The block algebra of eq (14) itself is correct — I re-derived it entrywise, and the
  row-partition is right **because** the appendix declared row-token layout at line 12; under
  column-token it would be a column partition. That declaration is doing real work and is a good
  example of the two-bases rule paying off.)
- **N4 · §A.6 / §A.2 — $d_k$ vs $d_{\text{head}}$ used interchangeably.** eq (4) scales by
  $\sqrt{d_{\text{head}}}$, §A.6 by $\sqrt{d_k}$. They coincide in standard MHA, but the appendix
  declares two other conventions explicitly and this third one is silent.
- **N5 · §A.5 line 113 — "any other normalization would be solving a different problem" is right
  but abstract.** Naming the concrete instances would strengthen it at no cost: the squared-norm
  regularizer $-\tfrac12\lVert\mathbf p\rVert_2^2$ gives **sparsemax** (whose non-negativity
  constraints *do* activate — the direct foil to line 99's infinite-slope argument), and Tsallis
  $\alpha$-entropy gives **$\alpha$-entmax**, with $\alpha=1$ softmax and $\alpha=2$ sparsemax.
  This converts "unique maximizer of *this* program" from a hedge into a demonstrated boundary.

---

### Cross-section consistency note (§A.1 eq (2) vs §A.8) — flagged, not scored

§A.1 eq (2) presents $\boldsymbol\ell=W_U\mathbf x_L$ as an exact identity ("Because the
unembedding is linear, the logits decompose the same way"). But GPT-2 is pre-LN **with a final
LayerNorm before the unembedding** — which line 197 itself quotes ("an additional layer
normalization was added after the final self-attention block"). So strictly
$\boldsymbol\ell=W_U\,\mathrm{LN}_f(\mathbf x_L)$, and eq (2) is exact only under the frozen-scale
linearization that §A.8 goes on to derive. §A.8 line 177 says "A LayerNorm sits on that path",
which is the acknowledgement — but eq (2) is never retro-qualified, and it is labelled "the
logit-attribution identity". §A.1 is outside my assigned scope; I raise it because §A.8 is inside
it and is the section that creates the tension. A forward pointer at eq (2)
("exact up to the final LayerNorm; see §A.8") would close it.

---

### Verified correct — explicitly, so the clean parts are on record

- eq (7)–(10): the entropy-regularized program, the inactive-constraint argument via infinite
  entropy slope (line 99, **correctly argued rather than assumed** — this is the step most
  treatments skip), the Lagrangian, and the strict-concavity uniqueness argument (line 106). All
  match my derivation.
- eq (11): $\operatorname{Var}(\mathbf q\cdot\mathbf k)=d_k$, $\operatorname{sd}=\sqrt{d_k}$. ✓
- eq (12): $J=\operatorname{diag}(\mathbf p)-\mathbf p\mathbf p^{\top}$ ✓ (central-difference check,
  max abs err $4.2\times10^{-11}$); the one-hot covariance identity ✓ **exact**; $J\succeq0$ ✓;
  $J\mathbf 1=0$ ✓.
- eq (13): $\operatorname{tr}J=1-\lVert\mathbf p\rVert_2^2$ ✓; maximal at uniform with value
  $1-1/n$ ✓; zero at a point mass ✓ (and I confirm the converse, which the target does not claim).
- **Numerics, all confirmed:** $\sqrt{2d_k}=11.3137\to$ "11.3" ✓; $\sqrt2=1.4142\to$ "1.41" ✓;
  $\operatorname{tr}J=2.4408\times10^{-5}\to$ "$2.44\times10^{-5}$" ✓; $0.31465\to$ "$0.315$" ✓;
  ratio $1.289\times10^{4}\to$ "roughly $1.3\times10^{4}$" ✓ honest rounding (**basis wrong — E2**).
- **$d_{\text{head}}/d$ "about 1/10 to 1/100"** ✓ honest bracket: I get 1/12 (GPT-2 small), 1/16,
  1/20, 1/25 (GPT-2 XL), 1/32 (Llama-2-7B), 1/64 (Llama-2-70B), 1/96 (GPT-3 175B). Sourced to
  Elhage et al., not asserted from memory. ✓
- eq (14): block algebra ✓ re-derived entrywise; the row-partition is correct under the declared
  row-token layout.
- **Rank bound stated as "at most $d_{\text{head}}$"** ✓ — the target does **not** overstate to
  "exactly", which is the trap here. (Generically it *is* exactly $d_{\text{head}}$, by Sylvester's
  rank inequality when both factors have full row rank $d_{\text{head}}$ — an optional
  strengthening, not a defect.)
- eq (15): $(A\otimes W_{OV})\cdot X=AXW_{OV}^{\top}$ with row $i$ equal to
  $\sum_j A_{ij}W_{OV}\mathbf x_j$ ✓ matches my derivation exactly.
- eq (16): the LayerNorm identity ✓ including the $\sqrt d$ placement, which I checked
  specifically (see U2).
- eq (17) **as an equation** ✓ — the expansion, the $O(\lVert P\boldsymbol\delta\rVert^2/s_0^2)$
  remainder, and both equalities are exactly what I derived. The defect is the prose gloss (E1).
- §A.9 line 208: the $\mathbf q\perp\mathbf k$ catch and the "initialization-time null model"
  scoping are **correct and well-made**. Optional quantification: at the extreme
  $\mathbf k=\mathbf q$, $\operatorname{Var}(\mathbf q\cdot\mathbf k)=2d_k$ rather than $d_k$ — the
  sd is inflated by exactly $\sqrt2$, which turns an unbounded caveat into a bounded one.

---

