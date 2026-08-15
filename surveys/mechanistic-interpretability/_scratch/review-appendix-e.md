# Independent re-derivation — Appendix E (steering directions & closed-form weight edits)

`[opt:MATH-REDERIVE]` adversarial review. **Phase 1 was written before the target file was
opened.** Reviewer derived from first principles; only then read
`appendix-e-steering-and-editing-math.md`.

Notation used throughout: vectors are columns; $d$ = residual-stream width; $D$ = key/input
width of the edited matrix; $H$ = output width; $U$ = number of simultaneous edits.

---

## Phase 1 — derivation from scratch (target unread)

### E1 — paired differences vs difference of means

**Setup.** Two indexed families $\{a^+_t\}_{t=1}^{n}$, $\{a^-_t\}_{t=1}^{n}$ in $\mathbb{R}^d$.

**Identity.** By linearity of a finite sum,

$$
\frac{1}{n}\sum_{t=1}^{n}\bigl(a^+_t - a^-_t\bigr)
= \frac{1}{n}\sum_{t=1}^{n} a^+_t - \frac{1}{n}\sum_{t=1}^{n} a^-_t
= \bar a^+ - \bar a^- .
$$

**Exact hypotheses.** Only three, and they are weaker than one expects:

1. the two families have **equal cardinality** $n$ (so a bijection exists and the paired
   difference is defined at all);
2. $n < \infty$ (finite sums commute freely);
3. the ambient set is a vector space (so $-$ and the scalar $1/n$ exist).

**No hypothesis about the pairing itself is needed.** For *any* bijection $\pi$,
$\frac1n\sum_t (a^+_t - a^-_{\pi(t)}) = \bar a^+ - \bar a^-$. Which items are paired with
which is **invisible to the first moment**. This is the whole content of the identity, and
it is the thing most easily over-claimed: pairing is a *variance-reduction* device, not a
*mean-changing* one.

**Do the three designs estimate the same quantity?** Model $A^+\sim P^+$, $A^-\sim P^-$;
estimand $\theta = \mathbb{E}[A^+] - \mathbb{E}[A^-] = \mu^+ - \mu^-$.

| design | estimator | bias | variance |
|---|---|---|---|
| single contrast pair | $a^+_1 - a^-_1$ | unbiased | $\Sigma^+ + \Sigma^- - 2C$ |
| mean over $n$ pairs | $\bar a^+ - \bar a^-$ | unbiased | $\tfrac1n(\Sigma^+ + \Sigma^- - 2C)$ |
| unpaired class means | $\bar a^+ - \bar a^-$ | unbiased **iff matched** | $\Sigma^+/n^+ + \Sigma^-/n^-$ |

with $C = \operatorname{Cov}(A^+, A^-)$ the *within-pair* covariance, which exists only in
the paired design.

So the claim **"they differ in sampling design and variance, not in estimand"** is
**defensible but conditional**, and the condition is not automatic:

- Pairing buys variance reduction exactly when $C \succ 0$ — which is the design intent of
  contrastive prompt pairs (same template, same topic, one attribute flipped, so the
  nuisance variation is *shared* and differences out). If $C \prec 0$ pairing would *hurt*.
  Either way the estimand is untouched. ✔ the claim holds here.
- **The one case where the unpaired design estimates something different.** Write
  $A = \mu_{\text{class}} + g(Z) + \varepsilon$ with $Z$ a nuisance covariate (topic, length,
  template, token position). Paired: $Z$ is *shared within the pair*, so
  $\mathbb{E}[a^+_t - a^-_t] = \mu^+-\mu^-$ **whatever** the law of $Z$. Unpaired, with
  $Z\sim Q^+$ in one set and $Z\sim Q^-$ in the other:

  $$
  \mathbb{E}[\bar a^+] - \mathbb{E}[\bar a^-]
  = (\mu^+-\mu^-) + \bigl(\mathbb{E}_{Q^+}[g(Z)] - \mathbb{E}_{Q^-}[g(Z)]\bigr).
  $$

  The bracket is a **confounding term**, nonzero whenever $Q^+ \neq Q^-$. Then the unpaired
  design's estimand is genuinely a *different quantity*.

  **Verdict:** "same estimand, different variance" is true **only under an unstated
  covariate-matching / exchangeability hypothesis** on the two unpaired sets. Under
  matching it is exactly right; without it the unpaired design is confounded. If the target
  asserts the claim without that qualifier → *UNSTATED HYPOTHESIS*.

- **Second qualifier.** A single pair is unbiased but has $O(1)$ variance and is therefore
  **not consistent** — no averaging is happening. "Estimates the same quantity" is true of
  the expectation only.
- **Third qualifier (bites in practice).** Steering vectors are usually **unit-normalized**.
  $\delta \mapsto \delta/\lVert\delta\rVert$ is nonlinear, so
  $\mathbb{E}[\hat\delta/\lVert\hat\delta\rVert] \neq \theta/\lVert\theta\rVert$ by Jensen —
  the *normalized* single-pair estimator is **biased as a direction**, with bias
  $O(\mathrm{tr}\Sigma / (n\lVert\theta\rVert^2))$ shrinking in $n$. So even the "same
  estimand" claim fails at the level of the object actually used, unless the claim is scoped
  to the unnormalized difference.

---

### E2 — the Gaussian discriminant

**Setup.** $p(x\mid +)=\mathcal{N}(x;\mu,\Sigma)$, $p(x\mid -)=\mathcal{N}(x;\nu,\Sigma)$,
**shared** $\Sigma\succ0$, equal priors.

$$
\log p(x\mid+)-\log p(x\mid-)
= -\tfrac12\Bigl[(x-\mu)^\top\Sigma^{-1}(x-\mu)-(x-\nu)^\top\Sigma^{-1}(x-\nu)\Bigr].
$$

The normalizing constants $-\tfrac12\log\det(2\pi\Sigma)$ are **identical** and cancel —
this needs the *shared* $\Sigma$. Expanding (using $\Sigma^{-1}=\Sigma^{-\top}$):

$$
(x-\mu)^\top\Sigma^{-1}(x-\mu) = x^\top\Sigma^{-1}x - 2\mu^\top\Sigma^{-1}x + \mu^\top\Sigma^{-1}\mu,
$$

and likewise for $\nu$. The $x^\top\Sigma^{-1}x$ terms **cancel** — again only because
$\Sigma$ is shared (different covariances leave a quadratic form and give QDA). Hence

$$
\log\frac{p(x\mid+)}{p(x\mid-)} = w^\top x + b,\qquad
\boxed{\,w=\Sigma^{-1}(\mu-\nu)\,},\quad
b=-\tfrac12(\mu+\nu)^\top\Sigma^{-1}(\mu-\nu).
$$

Fisher's criterion $\max_w (w^\top(\mu-\nu))^2/(w^\top\Sigma w)$ returns the same $w$ up to
positive scale, so LDA and the Bayes rule agree here.

#### (a) Exact condition for $\Sigma^{-1}(\mu-\nu) \parallel (\mu-\nu)$

Let $d=\mu-\nu\neq 0$. Claim: **$\Sigma^{-1}d\parallel d \iff d$ is an eigenvector of
$\Sigma$** (equivalently of $\Sigma^{-1}$).

*($\Leftarrow$)* $\Sigma d = \lambda d$ with $\lambda>0$ (positive since $\Sigma\succ0$ and
$d\neq0$: $\lambda = d^\top\Sigma d/\lVert d\rVert^2>0$). Then $\Sigma^{-1}d=\lambda^{-1}d$. ∎

*($\Rightarrow$)* Suppose $\Sigma^{-1}d = c\,d$. Since $\Sigma^{-1}$ is invertible and
$d\neq0$, $\Sigma^{-1}d\neq0$, so $c\neq0$. Apply $\Sigma$: $d = c\,\Sigma d$, i.e.
$\Sigma d = c^{-1}d$. ∎

Bonus, worth stating because it is a real constraint: in the parallel case the constant is
**strictly positive**, $c = d^\top\Sigma^{-1}d/\lVert d\rVert^2>0$. So detection and
mean-difference can never be *anti*-parallel; they either agree in direction or are
non-collinear.

#### (b) Is isotropy sufficient? necessary?

$\Sigma=\sigma^2 I$ makes **every** vector an eigenvector ⇒ **sufficient**. It is **not
necessary**, and the gap is enormous: $\Sigma=\mathrm{diag}(1,4,9)$ with $d=e_1$ satisfies
the exact condition. The correct necessary-and-sufficient statement is the *one-vector*
eigencondition of (a); isotropy is a global condition on all $d$ simultaneously and is
strictly stronger. Any text writing "the two coincide when the activations are isotropic"
states a sufficient condition as if it were the criterion — at best incomplete.

#### (c) *The key adversarial question.* "Optimal detection is $\Sigma^{-1}(\mu-\nu)$, natural steering displacement is $(\mu-\nu)$."

**This is well-posed only after a metric or an objective is named, and the two answers are
literally the same object in different metrics.**

Type analysis first: a linear classifier is a **covector** (it eats vectors and returns a
scalar); a steering intervention is a **vector** (it is added to an activation). Passing
between the two requires an inner product. There is no canonical one — and the model's own
geometry supplies $\Sigma$ (with dual metric $\Sigma^{-1}$).

Objectives under which $\mu-\nu$ **is** exactly right:

1. **Distribution transport.** The translation $x\mapsto x+(\mu-\nu)$ maps
   $\mathcal{N}(\nu,\Sigma)$ onto $\mathcal{N}(\mu,\Sigma)$ exactly; it is the unique
   translation doing so, and for shared $\Sigma$ it is the $L^2$-optimal (Monge–Brenier)
   transport map between the two Gaussians. If steering means "make the negative-class
   population look like the positive-class population, at minimum expected squared
   displacement", $\mu-\nu$ is **provably optimal**. ✔
2. **Minimum-Mahalanobis-cost purchase of log-odds.**
   $\min\ \delta^\top\Sigma^{-1}\delta$ s.t. $w^\top\delta=\Delta s$ gives
   $\delta\propto \Sigma w = \Sigma\Sigma^{-1}(\mu-\nu) = \mu-\nu$. ✔

Objectives under which $\mu-\nu$ is **wrong** and the answer is again $\Sigma^{-1}(\mu-\nu)$:

3. **Steepest Euclidean ascent of the discriminant.** $s(x)=w^\top x+b$, so
   $\nabla_x s = w = \Sigma^{-1}(\mu-\nu)$. Maximizing $w^\top\delta$ over
   $\lVert\delta\rVert_2 = 1$ gives $\delta\propto \Sigma^{-1}(\mu-\nu)$. ✘ for $\mu-\nu$.
4. **Minimum $\ell_2$-norm intervention achieving a target log-odds increase.**
   $\min\lVert\delta\rVert_2$ s.t. $w^\top\delta=\Delta s$ gives
   $\delta = \Delta s\, w/\lVert w\rVert^2 \propto \Sigma^{-1}(\mu-\nu)$. ✘ for $\mu-\nu$.

The reconciliation is exact and is the honest way to say it:

$$
\underbrace{\Sigma^{-1}(\mu-\nu)}_{\text{Euclidean gradient of }s}
\qquad\text{vs}\qquad
\underbrace{(\mu-\nu) = \Sigma\,\nabla_x s}_{\text{natural (}\Sigma\text{-metric) gradient of }s}.
$$

**They are one covector with its index lowered by two different metrics.** Under the
$\Sigma$-metric, "detection direction" and "mean difference" are the *same object*.

**Verdict on the claim.** Calling $\Sigma^{-1}(\mu-\nu)$ *optimal* for detection is
well-posed (Bayes / Fisher, both stated objectives). Calling $\mu-\nu$ the *natural*
steering displacement is **defensible but under-specified**, and becomes an **OVERSTATEMENT**
if written as *optimal* without naming an objective — because under the objective an
$\ell_2$-budgeted activation edit actually implements ("maximize class evidence per unit
intervention norm"), the correct displacement is $\Sigma^{-1}(\mu-\nu)$, i.e. the *same* as
detection. The target must either (i) name mean-transport / the $\Sigma$-metric as the
objective, or (ii) drop "optimal".

**And a further honesty point.** The reason practice uses $\mu-\nu$ (ActAdd, CAA,
difference-of-means / mass-mean probing) is largely **estimator stability**, not decision
theory: $\Sigma\in\mathbb{R}^{d\times d}$ with $d\sim 4096$ estimated from $n\sim 10^2$
contrast pairs is singular and $\Sigma^{-1}$ is dominated by noise in its small-eigenvalue
directions — exactly the directions $\Sigma^{-1}$ amplifies most. A justification framed as
"$\mu-\nu$ is the natural/optimal steering direction" hides a bias–variance argument behind
a geometric one.

---

### E3 — ROME's equality-constrained least squares

**Problem.** $\min_{\Delta\in\mathbb{R}^{H\times D}} \tfrac12\operatorname{tr}(\Delta C\Delta^\top)$
subject to $\Delta k = r$, with $C\in\mathbb{R}^{D\times D}$ symmetric positive definite,
$k\in\mathbb{R}^{D}$, $r\in\mathbb{R}^{H}$.

**Structural observation (makes everything easy).** Writing $\Delta$ by rows
$\delta_i^\top$, $(\Delta C\Delta^\top)_{ii}=\delta_i^\top C\delta_i$, so
$\operatorname{tr}(\Delta C\Delta^\top)=\sum_{i=1}^{H}\delta_i^\top C\delta_i$ and the
constraint reads $\delta_i^\top k = r_i$. **The problem decouples into $H$ independent
scalar-constrained quadratic programs sharing the same $C$ and $k$.** That alone forces the
rank-one answer.

#### (a) Lagrangian, matrix calculus explicit

$$
\mathcal{L}(\Delta,\Lambda)=\tfrac12\operatorname{tr}(\Delta C\Delta^\top)-\Lambda^\top(\Delta k - r),
\qquad \Lambda\in\mathbb{R}^{H}.
$$

Two derivative facts, each derived rather than quoted:

- $\dfrac{\partial}{\partial\Delta}\tfrac12\operatorname{tr}(\Delta C\Delta^\top) = \tfrac12\Delta(C+C^\top) = \Delta C$ (using $C=C^\top$). *Check by differentials:*

  $$
  \mathrm{d}\bigl[\tfrac12\operatorname{tr}(\Delta C\Delta^\top)\bigr]
  = \tfrac12\operatorname{tr}(\mathrm{d}\Delta\,C\Delta^\top)+\tfrac12\operatorname{tr}(\Delta C\,\mathrm{d}\Delta^\top)
  = \operatorname{tr}\bigl((\Delta C)^\top\,\mathrm{d}\Delta\bigr)
  $$

  by symmetry of $C$ and cyclicity of the trace. ✔
- $\dfrac{\partial}{\partial\Delta}\Lambda^\top\Delta k = \Lambda k^\top$.
  *Check:* $\Lambda^\top\Delta k=\operatorname{tr}(k\Lambda^\top\Delta)$, so the differential
  is $\operatorname{tr}(k\Lambda^\top \mathrm{d}\Delta)=\operatorname{tr}((\Lambda k^\top)^\top\mathrm{d}\Delta)$. ✔

Stationarity: $\Delta C - \Lambda k^\top = 0 \Rightarrow \Delta = \Lambda k^\top C^{-1} = \Lambda\,(C^{-1}k)^\top$, using $C^{-1}=C^{-\top}$.

#### (b) Rank one

$\Delta = \Lambda (C^{-1}k)^\top$ is an outer product of $\Lambda\in\mathbb{R}^H$ and
$C^{-1}k\in\mathbb{R}^D$, so $\operatorname{rank}\Delta\le1$, with equality iff $r\neq0$
(equivalently $\Lambda\neq0$). The rank-one structure is **forced by the constraint being a
single key vector**, not assumed.

#### (c) The multiplier and the closed form

$\Delta k = \Lambda (C^{-1}k)^\top k = \Lambda\,(k^\top C^{-1}k) = r$, hence

$$
\Lambda = \frac{r}{k^\top C^{-1}k},
\qquad
\boxed{\ \Delta^\star = \frac{r\,(C^{-1}k)^\top}{k^\top C^{-1}k}\ }.
$$

#### (d) Strict positivity of $k^\top C^{-1}k$

$C\succ0 \Rightarrow$ all eigenvalues $>0 \Rightarrow$ $C^{-1}$ has eigenvalues
$1/\lambda_i>0 \Rightarrow C^{-1}\succ0 \Rightarrow k^\top C^{-1}k>0$ **for every $k\neq0$**.

Hypotheses: (i) $C$ **strictly** positive definite — PSD is *not* enough, a singular PSD $C$
has no inverse at all; (ii) $k\neq 0$. If $k=0$ the constraint is infeasible unless $r=0$.
Practically relevant: $C=\mathbb{E}[kk^\top]$ estimated from $N$ samples is **singular**
whenever $N<D$, so the formula silently requires either $N\ge D$ with spanning keys or an
explicit damping $C+\lambda I$. A text writing "positive semi-definite" here would be wrong.

#### (e) Is the stationary point a minimum?

Yes, **globally and uniquely**, and it needs no second-order machinery. Direct argument: let
$\Delta'=\Delta^\star+E$ be any other feasible point, so $Ek=0$. Then

$$
f(\Delta')=f(\Delta^\star)+\operatorname{tr}(\Delta^\star C E^\top)+\tfrac12\operatorname{tr}(ECE^\top),
$$

and the cross term vanishes exactly:

$$
\operatorname{tr}(\Delta^\star C E^\top)=\operatorname{tr}(\Lambda (C^{-1}k)^\top C E^\top)
=\operatorname{tr}(\Lambda k^\top E^\top)=\operatorname{tr}(\Lambda (Ek)^\top)=0 .
$$

So $f(\Delta')-f(\Delta^\star)=\tfrac12\operatorname{tr}(ECE^\top)\ge 0$, with equality iff
$E=0$ (since $C\succ0$). ∎ Global minimum, unique.

The textbook phrasing is equivalent: $f$ is a **strictly convex quadratic** and the feasible
set $\{\Delta:\Delta k=r\}$ is a nonempty **affine** set, so any KKT/stationary point is the
unique global minimizer. (Slater is not needed — affine equality constraints give strong
duality unconditionally for a convex objective.)

#### (f) "A Lagrangian is minimized in its multiplier" — **false**

For an equality constraint, $\mathcal{L}$ is **affine (linear) in $\Lambda$**, so it has no
minimum in $\Lambda$ at all: unless $\Delta k - r = 0$ exactly, $\inf_\Lambda\mathcal{L}=-\infty$;
and when $\Delta k = r$, $\mathcal{L}$ is *constant* in $\Lambda$. The correct statements are:

- $\mathcal{L}$ is **stationary** in $\Lambda$, and $\partial\mathcal{L}/\partial\Lambda = 0$
  simply **recovers primal feasibility** $\Delta k = r$;
- the solution is a **saddle point**:
  $\mathcal{L}(\Delta^\star,\Lambda)\le\mathcal{L}(\Delta^\star,\Lambda^\star)\le\mathcal{L}(\Delta,\Lambda^\star)$
  — *minimized in the primal, maximized in the dual*;
- the **dual function** $g(\Lambda)=\inf_\Delta\mathcal{L}(\Delta,\Lambda)$ is **maximized**
  over $\Lambda$ (here $g(\Lambda)=\Lambda^\top r-\tfrac12(k^\top C^{-1}k)\lVert\Lambda\rVert^2$,
  a concave quadratic whose maximizer is $\Lambda^\star=r/(k^\top C^{-1}k)$ ✔ — consistent).

So the honest phrasing is "stationary in $\Lambda$ / maximized in the dual", never
"minimized in $\Lambda$".

---

### E5 — weight orthogonalization ≡ directional ablation

**Setup.** Unit vector $\hat r$, $\lVert\hat r\rVert=1$; projector $P=\hat r\hat r^\top$
($P^2=P$, $P^\top = P$); ablation operator $A=I-P$ (also idempotent, symmetric).

- **Inference-time directional ablation:** every time the residual stream is read, use $Ah$
  in place of $h$ (equivalently, project the stream after every write).
- **Weight-edit ("orthogonalization"):** every matrix $W_{\text{out}}$ that **writes** into
  the residual stream is replaced by $W' = (I-\hat r\hat r^\top)W_{\text{out}} = W_{\text{out}} - \hat r(\hat r^\top W_{\text{out}})$.

**Derivation.** The residual stream is by construction a *sum of writer contributions*:
$h_\ell = \sum_{j\le\ell} c_j$ with $c_j = W^{(j)}_{\text{out}}x_j$, where $x_j$ is whatever
component $j$ computed from what it read.

*Induction over writers in the causal/topological order (layer, then position).*

- **Base case.** Before the first edited writer the stream holds $h_{-1}$. Under the weight
  edit, $h'_{-1}=h_{-1}$; under ablation it is $Ah_{-1}$. These agree **iff $Ph_{-1}=0$.**
- **Step.** Suppose $h'_{j-1}=Ah_{j-1}$ at every position. Component $j$ reads exactly the
  same value in both runs, so it computes the same $x'_j=x_j$ (this needs **nothing** about
  the component — it may contain LayerNorm, softmax, GELU, cross-position attention; only
  *equality of inputs* is used). Its contribution is $c'_j = W'x_j = A W x_j = Ac_j$. Hence
  $h'_j = h'_{j-1}+c'_j = Ah_{j-1}+Ac_j = A(h_{j-1}+c_j)=Ah_j$. ∎

**The premise.** The base case is exactly the required premise: **the residual stream must
carry no component along $\hat r$ before the first edited writer**, i.e. $Ph_{-1}=0$. In a
standard transformer $h_{-1}=0$ and the *first writers are the token and positional
embedding matrices* — so the premise is discharged **only if the embeddings are counted
among the writers and edited too**.

**Is the premise necessary?** Two readings, both worth stating:

- *Necessary in general:* **yes.** Omit $W_E$ (or $W_{\text{pos}}$) from the edit set and the
  equivalence fails at layer 0 by exactly $P h_{-1}\neq0$, and the error then propagates
  (attention mixes it across positions).
- *Discharge-able two ways:* structurally (edit the embeddings — the stream then genuinely
  starts at $0$), or accidentally (if $\hat r^\top W_E = 0$ and $\hat r^\top W_{\text{pos}}=0$
  for the whole vocabulary, the embedding edit is a no-op and may be skipped). The second is
  a data-dependent coincidence, not a theorem.

**Hypotheses the equivalence quietly needs (the adversarial content):**

1. **Biases are writers.** $b_O$, $b_{\text{down}}$, and any additive bias written into the
   stream must be ablated too, $b' = Ab$. Editing only weight *matrices* breaks the
   equivalence by a constant offset that is *input-independent* and therefore easy to miss.
2. **Every write is edited, and ablation is applied at every layer and every position.** A
   partial ablation (e.g. "layers 10–20 only") is **not** reproducible by any such weight
   edit, because the edit is unconditional.
3. **Non-linearity is a non-issue, and the reason matters.** LayerNorm/RMSNorm does *not*
   commute with $A$. A proof that "pushes the projector through the network" would need
   commutation and is **wrong**. The sum-of-writers induction never needs it — it only needs
   *equality of the read values*. Any text justifying the equivalence by "the projection
   commutes with the layers" has the right conclusion by a wrong argument.
4. **Reading matrices need no edit.** $W_Q,W_K,W_V,W_{\text{in}}$, and the unembedding
   $W_U$ read from the stream; they see $Ah$ automatically. Editing them would be wrong (and
   would change behavior).
5. **Weight tying is benign** — worth checking because it looks dangerous. If $W_U=W_E^\top$
   and $W_E$ is edited to $AW_E$, then $W_U'=W_E^\top A$, and the logits become
   $W_E^\top A(Ah)=W_E^\top Ah$ — identical to the unedited readout on the ablated stream,
   **because $A$ is idempotent**. ✔ no correction needed.
6. **Finite precision (NIT-plus).** $A$ is idempotent only exactly. Inference-time ablation
   re-projects after every write and is self-correcting; the weight edit leaves an
   $O(\varepsilon)$ residual per writer that accumulates over depth. Immaterial in practice
   ($\sim10^{-7}$ relative) but it makes the equivalence exact-in-exact-arithmetic only.

---

### E4 — scale invariance: ROME yes, MEMIT no

#### (a) ROME under $C \mapsto \alpha C$, $\alpha>0$

Track each piece:

| piece | under $C$ | under $\alpha C$ | factor |
|---|---|---|---|
| $C^{-1}k$ | $C^{-1}k$ | $\alpha^{-1}C^{-1}k$ | $\alpha^{-1}$ |
| denominator $k^\top C^{-1}k$ | $k^\top C^{-1}k$ | $\alpha^{-1}k^\top C^{-1}k$ | $\alpha^{-1}$ |
| multiplier $\Lambda$ | $r/(k^\top C^{-1}k)$ | $\alpha\, r/(k^\top C^{-1}k)$ | $\alpha$ |
| product $\Lambda\,(\cdot)^\top$ | — | — | $\alpha\cdot\alpha^{-1}=1$ |

$$
\Delta^\star(\alpha C)
= \frac{r\,\bigl((\alpha C)^{-1}k\bigr)^\top}{k^\top(\alpha C)^{-1}k}
= \frac{\alpha^{-1}\,r\,(C^{-1}k)^\top}{\alpha^{-1}\,k^\top C^{-1}k}
= \frac{r\,(C^{-1}k)^\top}{k^\top C^{-1}k}
= \Delta^\star(C).
$$

**EXACTLY invariant** — an identity, not an approximation. The multiplier absorbs precisely
the factor the direction loses; equivalently, $\Delta^\star$ depends on $C$ only through the
$0$-homogeneous ratio $(C^{-1}k)/(k^\top C^{-1}k)$.

**The one-line reason, which is the honest statement of the result:** scaling a minimization
objective by a positive constant does not move the argmin of a *constrained* problem —
$\arg\min\{\alpha f(\Delta) : \Delta k = r\} = \arg\min\{f(\Delta):\Delta k=r\}$. The overall
scale of $C$ is a **gauge freedom** of ROME, not a hyperparameter. Practical corollary:
whether one estimates $C$ as $\sum_i k_ik_i^\top$ or $\tfrac1N\sum_i k_ik_i^\top$ is
irrelevant; only the *shape* (eigenvector directions and eigenvalue ratios) of $C$ matters.

**Scope of the invariance — do not over-claim it.** It is invariance under a **global
positive scalar** only. It is *not* invariance under $C\mapsto C+\lambda I$ (the damping
term real implementations add), nor under $C \mapsto C + \text{anything}$. Adding a ridge
genuinely changes $\Delta^\star$ by changing the eigenvalue *ratios*.

#### (b) MEMIT under $C_0 \mapsto \alpha C_0$

$$
\Delta(\alpha) = R\,K_1^\top\bigl(\alpha C_0 + K_1K_1^\top\bigr)^{-1}.
$$

**Shapes.** $K_1\in\mathbb{R}^{D\times U}$ (keys as columns), $R\in\mathbb{R}^{H\times U}$
(residuals as columns) $\Rightarrow$ $K_1^\top\in\mathbb{R}^{U\times D}$,
$RK_1^\top\in\mathbb{R}^{H\times D}$, $K_1K_1^\top$ and $C_0\in\mathbb{R}^{D\times D}$, so
$\Delta\in\mathbb{R}^{H\times D}$. ✔ conformable, and it matches the shape of the weight
matrix being edited.

**Nothing cancels**: $\alpha$ multiplies only *one* of the two summands, so it cannot be
pulled out of the inverse. The two terms are in tension and their *ratio* is physical.

A push-through (Woodbury) rearrangement makes both limits transparent. Using
$(\alpha C_0 + K_1K_1^\top)^{-1}K_1 = C_0^{-1}K_1(\alpha I + K_1^\top C_0^{-1}K_1)^{-1}$ and
transposing, with $G \equiv K_1^\top C_0^{-1}K_1 \in\mathbb{R}^{U\times U}$:

$$
\Delta(\alpha) = R\,(\alpha I + G)^{-1}K_1^\top C_0^{-1}.
$$

- **$\alpha\to0^+$:** $\Delta\to R\,G^{-1}K_1^\top C_0^{-1} = R\,(K_1^\top C_0^{-1}K_1)^{-1}K_1^\top C_0^{-1}$
  (needs $K_1$ full column rank, i.e. $U\le D$ with independent keys — the practical regime).
  Check the constraint: $\Delta K_1 = R\,(K_1^\top C_0^{-1}K_1)^{-1}K_1^\top C_0^{-1}K_1 = R$
  **exactly**. So the $\alpha\to0$ limit is the **equality-constrained, minimum-$C_0$-norm**
  update — i.e. precisely the multi-key generalization of ROME. At $U=1$ it reduces to
  $r(C_0^{-1}k)^\top/(k^\top C_0^{-1}k)$, the E3 formula, term for term.
  *Interpretation:* zero weight on preserving old behavior; the new facts are written in
  perfectly. **And this limit IS scale-invariant** (the $\beta$'s cancel:
  $(K_1^\top\beta^{-1}C_0^{-1}K_1)^{-1}K_1^\top\beta^{-1}C_0^{-1}$ is $\beta$-free).
- **$\alpha\to\infty$:** $\Delta(\alpha) = \tfrac1\alpha R K_1^\top C_0^{-1} + O(\alpha^{-2}) \to 0$.
  *Interpretation:* an infinitely-weighted preservation term freezes the weights — no edit
  happens at all. To leading order the edit magnitude is $\propto 1/\alpha$, so the scale of
  $C_0$ acts as an **inverse edit-strength / inverse learning-rate knob**.

#### (c) VERDICT and numerical check

**The asymmetry is real**, and the sharp statement of *why* is more informative than the
statement itself:

> ROME imposes the new fact as a **hard equality constraint**, so the objective's overall
> scale is a gauge freedom and $\Delta$ is exactly invariant to $C\mapsto\alpha C$. MEMIT
> **penalizes** deviation from old behavior instead of constraining, so the *relative*
> weight of the two terms is physical and $\alpha$ is a genuine, tunable hyperparameter.
> The distinction is **constrained vs penalized**, not "ROME vs MEMIT" as brands — MEMIT's
> own $\alpha\to0$ limit recovers the invariant, exactly-constrained regime.

**Numerics** (`numpy`, `default_rng(20260815)`, float64, $D=12$, $H=7$, $U=4$, random SPD
$C$ and $C_0$; the script is reproduced at the end of this file):

ROME, $\Delta$ recomputed with $C$ replaced by $\alpha C$, compared entrywise against
$\alpha=1$:

| $\alpha$ | $\max\lvert\Delta(\alpha C)-\Delta(C)\rvert$ | relative |
|---|---|---|
| $10^{-6}$ | 1.665e-16 | 5.81e-16 |
| 0.5 | 0.000e+00 | 0.000e+00 |
| 3 | 1.665e-16 | 5.81e-16 |
| $10^{3}$ | 1.110e-16 | 3.88e-16 |
| $10^{7}$ | 2.220e-16 | 7.75e-16 |

i.e. invariant **to float64 round-off over 13 decades of $\alpha$** — consistent with an
exact identity, not an approximation. Side checks: $\lVert\Delta k-r\rVert = 3.1\times10^{-17}$,
$\operatorname{rank}\Delta = 1$; and the tracked pieces scale as derived —
$(\alpha C)^{-1}k / (C^{-1}k) = 0.333333$ and denominator ratio $0.333333$ at $\alpha=3$
(predicted $1/\alpha$), multiplier ratio $3.000000$ (predicted $\alpha$).

MEMIT, same protocol ($\Delta$ has the predicted shape $7\times12$):

| $\alpha$ | $\max\lvert\Delta\rvert$ | $\max\lvert\Delta(\alpha C_0)-\Delta(C_0)\rvert$ | $\lVert\Delta K_1-R\rVert_F$ |
|---|---|---|---|
| $10^{-8}$ | 6.412e-01 | 8.82e-02 | 6.50e-07 |
| $10^{-3}$ | 6.412e-01 | 8.80e-02 | 7.24e-04 |
| 1 | 5.833e-01 | 0 | 5.93e-01 |
| 3 | 5.036e-01 | 1.01e-01 | 1.32e+00 |
| $10^{3}$ | 1.368e-02 | 5.71e-01 | 5.45e+00 |
| $10^{8}$ | 1.440e-07 | 5.83e-01 | 5.57e+00 |

**Not invariant** — the deviation is $O(1)$ relative to $\lVert\Delta\rVert$ itself, fourteen
orders of magnitude above ROME's. The limits are confirmed: $\lVert\Delta K_1-R\rVert_F\to0$
as $\alpha\to0$ (fact insertion becomes exact) and $\max\lvert\Delta\rvert\to0$ as
$\alpha\to\infty$ (no edit), with $\alpha\lvert\Delta\rvert \to RK_1^\top C_0^{-1}$ verified
to $7.6\times10^{-6}$ at $\alpha=10^{8}$. Convergence to the constrained limit is clean
first order in $\alpha$ (ratio $\lvert\Delta(\alpha)-\Delta(0)\rvert/\alpha$ flat at
$0.1074, 0.1098, 0.1100, 0.1101, 0.1101, 0.1108$ for $\alpha = 10^{-1}\ldots10^{-6}$), and
the closed-form limit satisfies $\Delta K_1 = R$ to $4.0\times10^{-15}$ and is scale-invariant
to $7.8\times10^{-16}$. The $U=1$ specialization of the MEMIT limit equals the ROME formula
to solver tolerance. (The larger residuals at $\alpha \le 10^{-12}$ in the first sweep are
float64 conditioning — $\operatorname{cond}(10^{-12}C_0 + K_1K_1^\top)\approx 10^{14}$ — not
a failure of the limit.)

---

## Phase 2 — comparison against the target

Target: `surveys/mechanistic-interpretability/appendix-e-steering-and-editing-math.md`,
read only after the above was written.

**Headline: the appendix is in good shape.** Every numbered equation is *correct as printed* —
Eq (2), (3), (5), (6), (7) reproduce my independent derivations term for term, including the
signs and the $\tfrac12$ in Eq (6), and the shape annotation on Eq (4) is conformable exactly
as I derived it. The two hardest calls in the brief both come out in the appendix's favour:
the eigenvector iff (E.4) is stated correctly in **both** directions with isotropy correctly
demoted to "sufficient but far from necessary", and the scale-invariance claim (E.5) is
**exactly** right, not approximately. The findings below are about *claims made around* the
equations, not the equations.

Counts: **3 ERROR · 3 UNSTATED HYPOTHESIS · 3 OVERSTATEMENT · 9 NIT**.

---

### ERROR-1 (severity: high) — the stated reason MEMIT is inexact is wrong, and the appendix contradicts itself two paragraphs later

**Target, § E.3 line 49:**

> "…which satisfies the constraints only approximately, since $u$ exact constraints on one
> matrix are generally infeasible."

**My derivation (E4b).** $\Delta K_1 = R$ is a *linear* system in $\Delta\in\mathbb{R}^{H\times D}$;
it decouples into $H$ systems of $u$ equations in $D$ unknowns. It is feasible whenever
$\operatorname{null}(K_1)\subseteq\operatorname{null}(R)$ — in particular **whenever $K_1$ has
full column rank, i.e. $u \le D$ with linearly independent keys**. That is not an edge case,
it is the underdetermined-and-therefore-solvable regime. Constructively, the $\lambda\to0$
limit of the appendix's own Eq (4) is

$$
\Delta \;\longrightarrow\; R\,(K_1^\top C_0^{-1}K_1)^{-1}K_1^\top C_0^{-1},
\qquad\text{which satisfies}\qquad \Delta K_1 = R \ \text{ exactly.}
$$

Verified numerically: $\lVert\Delta K_1 - R\rVert_F = 4.0\times10^{-15}$, and the finite-$\lambda$
family converges to it cleanly at first order in $\lambda$.

**So exact insertion is not the obstruction — MEMIT *chooses* not to impose it.** Eq (4)
replaces ROME's hard equality constraint with a quadratic *penalty* weighted by $C_0$; the
residual $\lVert\Delta K_1 - R\rVert_F$ it accepts is the price of buying preservation of old
associations, which is a design decision, not an infeasibility.

**The appendix already knows this** and says it correctly twice:

- line 51: "Equation (4) also quietly drops ROME's equality constraint… it minimizes a
  combined objective instead" ✔ — the *right* reason;
- line 96: "sending $\lambda\to0$ gives the minimum-norm fit to the new facts alone" — which
  presupposes the limit exists and fits the new facts, contradicting "generally infeasible".

**Correction.** Delete the causal clause in line 49 and let line 51 carry the point. E.g.
"…which satisfies the constraints only approximately — not because $u$ exact constraints are
infeasible (for $u \le D$ with independent keys they are, and the $\lambda\to0$ limit of
Eq (4) attains them exactly) but because Eq (4) *penalizes* rather than *constrains* the new
associations." Note $u \le D$ covers MEMIT's own headline batch sizes against MLP widths of
order $10^4$ — **check the exact $u$ and $d_{\text{mlp}}$ against the paper before quoting
them; this review did not open the source** (citation-integrity).

---

### ERROR-2 (severity: high) — "the same object RepE's LAT recovers as the top PCA component" is false as an identity

**Target, § E.1 line 11:**

> "…the same object RepE's LAT (§7.2) recovers as the top PCA component of paired differences."

**My derivation.** Let $d_t = \mathbf{a}^+_t - \mathbf{a}^-_t$ with mean $m$ and covariance $S$.
The mean difference is the **first moment** $m$. The top PCA component is a **second-moment**
object. On the *uncentered* second moment $M = \mathbb{E}[dd^\top] = S + mm^\top$:

- **Necessity is exact and easy.** If the top eigenvector of $M$ is $m/\lVert m\rVert$, then
  $Mm=\lambda m \Rightarrow Sm + \lVert m\rVert^2 m = \lambda m \Rightarrow Sm = (\lambda - \lVert m\rVert^2)m$,
  so **$m$ must be an eigenvector of the difference covariance $S$**.
- **Sufficiency needs one more condition.** If $Sm=\sigma m$ then $m$ is an eigenvector of $M$
  with eigenvalue $\sigma + \lVert m\rVert^2$; it is the *top* one only if
  $\sigma + \lVert m\rVert^2 > \lambda_{\max}\bigl(S|_{m^{\perp}}\bigr)$ — a signal-dominance
  condition.
- **If the PCA is centered** (the default in most implementations), it diagonalizes $S$ alone,
  from which $m$ has been *explicitly removed*. Then there is no relation at all: centered PCA
  finds the direction of maximal *variation* of the differences, not their mean.

So mean-difference and top-PC are **two different estimators that coincide under a condition**,
not one object. This matters more than usual here because it sits in a section whose entire
thesis is "these constructions are the same estimator" — an unearned identity in that list
weakens the earned ones.

**Correction.** "…closely related to what RepE's LAT recovers as the top principal component
of paired differences: on the *uncentered* second moment $M = S + mm^\top$ the two agree
exactly iff the mean difference $m$ is an eigenvector of the difference covariance $S$ and
dominates its remaining spectrum — structurally the *same* eigenvector condition as § E.4,
one moment up. Under centered PCA the mean is removed and the two are unrelated."
(That parallel is worth having: the appendix would then state one condition twice rather than
two claims once.)

---

### ERROR-3 (severity: med) — $\Lambda$ is called a scalar in § E.2 and a vector in § E.6

**Target, § E.2 line 37:** "the **scalar** $\Lambda$ enforces $\hat W\mathbf{k}_* = \mathbf{v}_*$ exactly."
**Target, § E.6 line 113:** "The source's Appendix A says '$\Lambda \in \mathbb{R}^{H}$ …'."

**My derivation (E3c).** $\Lambda = r/(k_*^\top C^{-1}k_*)$ is a **vector in $\mathbb{R}^H$** —
numerator $r = \mathbf{v}_* - W\mathbf{k}_*\in\mathbb{R}^H$, denominator a positive scalar. It
is *the scalar that is a scalar*: the denominator. And $\Lambda$ must be a vector for
$\Lambda(C^{-1}\mathbf{k}_*)^\top$ to be an $H\times D$ matrix at all — the appendix's own
rank-one argument (line 109: "outer product of two vectors") requires it. Eq (3) is correct;
only the word is wrong.

**Correction.** "the vector $\Lambda\in\mathbb{R}^H$ enforces…", or "the scale factor
$1/(\mathbf{k}_*^\top C^{-1}\mathbf{k}_*)$ enforces…".

---

### OVERSTATEMENT-1 (severity: med-high) — the detection-vs-steering gap is objective-dependent and is stated unconditionally

**Target, § E.4 line 78:**

> "Detection and control do not have the same optimal direction. To *detect* the class, project
> onto $\Sigma^{-1}(\mu-\nu)$; to *steer* … add a multiple of $\mu-\nu$ itself, since that is
> the displacement between the distributions. **These coincide only under the eigenvector
> condition above.** … the two tasks have different optima whenever the class-mean difference
> is not aligned with a principal axis."

**Assessment.** Better than the brief's worst case: the appendix *does* name a steering
objective ("move one class's activations onto the other's", "the displacement between the
distributions"), and under that objective $\mu-\nu$ is **provably optimal** — it is the unique
translation carrying $\mathcal{N}(\nu,\Sigma)$ to $\mathcal{N}(\mu,\Sigma)$, and for shared
$\Sigma$ it is the $L^2$-optimal Monge map. So the sentence is *well-posed*, not vacuous.

**But the conclusion drawn from it is not.** "The two tasks have different optima" is asserted
as a property of the tasks, when it is a property of the *objective chosen for steering*. Under
the other natural steering objective — **maximize the model's log-odds of the target class per
unit $\ell_2$ intervention norm**, which is what a norm-budgeted activation edit literally
implements — the optimum is

$$
\arg\max_{\lVert\delta\rVert_2 = 1} w^\top\delta \;\propto\; w \;=\; \Sigma^{-1}(\mu-\nu),
$$

i.e. **the same direction as detection, and the claimed gap disappears**. Same for
$\min\lVert\delta\rVert_2$ subject to a target log-odds increase. Conversely
$\min\ \delta^\top\Sigma^{-1}\delta$ subject to the same log-odds increase returns
$\delta\propto\Sigma(\Sigma^{-1}(\mu-\nu)) = \mu-\nu$.

So the honest statement is a **metric** statement, and it is stronger and cleaner than the one
printed:

$$
\underbrace{\Sigma^{-1}(\mu-\nu)}_{\text{Euclidean gradient }\nabla_{\mathbf{x}}s}
\qquad\text{and}\qquad
\underbrace{\mu-\nu \;=\; \Sigma\,\nabla_{\mathbf{x}}s}_{\text{natural (}\Sigma\text{-metric) gradient}}
$$

are **one covector with its index lowered by two different metrics**. A classifier is a
covector; a steering displacement is a vector; converting between them *requires* a metric,
and there is no canonical one. "Reading out" and "pushing in" therefore differ exactly by the
choice of metric on activation space — which is a first-principles reason to expect a gap
(the appendix's point survives) but **not** a reason to call one of them *the* optimum.

**Correction.** Add the conditioning clause and the reconciliation: "…different optima *under
the distribution-matching objective*; under an $\ell_2$-budgeted log-odds objective the optimal
displacement is instead $\Sigma^{-1}(\mu-\nu)$ and the two coincide. The two answers are the
same discriminant covector lowered by the Euclidean and the $\Sigma$ metric respectively, so
the read-out/push-in gap is a choice of metric, not two unrelated optima."

---

### OVERSTATEMENT-2 (severity: med-high) — "a first-order approximation otherwise" names no expansion parameter, and is uncontrolled in the regime that actually holds

**Target, § E.1 line 11:**

> "So difference-in-means is the optimal separating direction in the isotropic case and a
> **first-order approximation** otherwise."

**My derivation.** There is no small parameter in the statement. Supply one — write
$\Sigma = \sigma^2(I + E)$ with $E$ the anisotropy — and then

$$
\Sigma^{-1}(\mu-\nu) = \sigma^{-2}\bigl(I - E + O(\lVert E\rVert^2)\bigr)(\mu-\nu),
$$

so $\mu-\nu$ is the **zeroth-order** term (leading order in the anisotropy, up to the
irrelevant scale $\sigma^{-2}$), with **first-order error** $-\sigma^{-2}E(\mu-\nu)$. Calling it
"a first-order approximation" is off by one order under the only expansion that makes the
phrase mean anything.

**And the approximation is uncontrolled here.** LLM residual-stream covariances are strongly
anisotropic (heavy-tailed spectrum, a small number of very high-variance outlier directions),
so $\lVert E\rVert$ is not small and the expansion has no useful error bound. Worse, the angle
between $\mu-\nu$ and $\Sigma^{-1}(\mu-\nu)$ can approach $90^\circ$ when $\mu-\nu$ carries mass
in small-eigenvalue directions — precisely the directions $\Sigma^{-1}$ amplifies. "First-order
approximation" invites the reader to treat the gap as small; the appendix's own § E.4 line 78
argues the gap is large enough to matter. **The two sentences pull in opposite directions.**

**Correction.** "…and otherwise a *leading-order* stand-in whose error is first order in the
anisotropy of $\Sigma$ — a stand-in with no small parameter in real activation spaces, where
$\Sigma$ is strongly anisotropic (see § E.4 line 78 for the consequence)."

---

### OVERSTATEMENT-3 (severity: med) — the MEMIT $\lambda\to0$ limit is not a "minimum-norm fit"

**Target, § E.5 line 96:** "sending $\lambda \to 0$ gives the minimum-norm fit to the new facts alone."

**My derivation (E4b), numerically confirmed.** Three corrections, and the third is the
interesting one:

1. It is not a **fit** — it is an *exact interpolant*: $\Delta K_1 = R$ holds to
   $4.0\times10^{-15}$.
2. It is not the **Euclidean** minimum-norm solution but the **$C_0$-metric** one,
   $\Delta \to R\,(K_1^\top C_0^{-1}K_1)^{-1}K_1^\top C_0^{-1}$. Only the *scale* of $C_0$
   drops out in the limit; its *shape* survives and determines which of the infinitely many
   exact solutions is chosen. ("the new facts alone" reads as if $C_0$ has left entirely.)
3. Therefore **that limit is itself exactly scale-invariant** (verified to
   $7.8\times10^{-16}$), and at $u=1$ it reduces to Eq (3) term for term.

Point 3 is the cleanest possible proof of § E.5's own thesis and the appendix should take it:
**the dichotomy is constrained-vs-penalized, not ROME-vs-MEMIT.** The scale of the metric is a
gauge freedom of an *equality-constrained* problem and a genuine hyperparameter of a
*penalized* one — and MEMIT's own $\lambda\to0$ limit crosses back into the invariant regime.
That framing also makes § E.5's question ("why does one need the constant and the other not?")
answer itself in one sentence, and it kills ERROR-1 at the same time.

Add the rate for the other limit while there: $\Delta(\lambda) = \tfrac1\lambda R K_1^\top C_0^{-1} + O(\lambda^{-2})$,
so $\lambda$ acts as an **inverse edit-strength knob**, not merely as an on/off preservation
weight (verified to $7.6\times10^{-6}$ at $\lambda = 10^{8}$).

---

### UNSTATED HYPOTHESIS-1 (severity: med-high) — "not in estimand" needs covariate matching, and the cited construction is exactly the unmatched case

**Target, § E.4 line 65 (and the section title "Three steering estimators are one estimator"):**

> "So the three differ in **sampling design and variance, not in estimand** … Pairing reduces
> variance when the pair members share nuisance variation; it does not change what is being
> estimated."

**My derivation (E1).** Correct for the **paired** designs, and correct for the unpaired design
*only under an unstated matching hypothesis*. Write $A = \mu_{\text{class}} + g(Z) + \varepsilon$
with $Z$ a nuisance covariate (topic, length, template, token position). Paired, $Z$ is shared
within the pair, so $\mathbb{E}[\mathbf{a}^+_t - \mathbf{a}^-_t] = \mu-\nu$ **whatever** the law
of $Z$. Unpaired, with $Z\sim Q^+$ in one set and $Z\sim Q^-$ in the other:

$$
\mathbb{E}[\bar{\mathbf{a}}^{+}] - \mathbb{E}[\bar{\mathbf{a}}^{-}]
= (\mu-\nu) + \bigl(\mathbb{E}_{Q^+}[g(Z)] - \mathbb{E}_{Q^-}[g(Z)]\bigr),
$$

and the bracket is a **confounding term** — a genuinely different estimand whenever
$Q^+\neq Q^-$. Pairing is not only variance reduction; against an unmatched unpaired design it
is also **de-confounding**.

This is not hypothetical for the citation attached to the sentence: the "difference of class
means over harmful and harmless prompt sets" construction draws its two sets from *different
corpora*, which differ in length, topic and register — i.e. $Q^+\neq Q^-$ by construction.
So the one design in the list that most needs the caveat is the one the caveat is missing for.
(The final clause "how well matched" gestures at this but reads as a variance remark; the
strong "not in estimand" is stated flatly and is what a reader will carry away.)

**Correction.** "…differ in sampling design and variance, not in estimand — *provided the
unpaired sets are matched on the nuisance factors that drive activations*. When they are not
(distinct source corpora differing in length, topic or register), the unpaired difference
acquires a confounding term and estimates a different quantity; pairing is de-confounding as
well as variance-reducing."

Two smaller riders belong here: the $n=1$ case is unbiased but **not consistent**; and since
steering vectors are used **unit-normalized**, $\mathbb{E}[\hat\delta/\lVert\hat\delta\rVert] \neq \theta/\lVert\theta\rVert$
by Jensen, so the *normalized* single-pair estimator is biased as a direction (bias
$O(\operatorname{tr}\Sigma / (n\lVert\theta\rVert^2))$, vanishing in $n$). The equality in Eq (5)
is exact; the equality of the *objects actually used* is not.

---

### UNSTATED HYPOTHESIS-2 (severity: med) — the orthogonalization premise is discharged only by counting embeddings (and biases) among the "writers"

**Target, § E.4 line 80:**

> "The equivalence needs one premise … the stream must carry **no** $\hat{\mathbf{r}}$ component
> before the first such writer … Given that, an induction over writers in forward order shows
> the two procedures produce identical activations at every layer."

**My derivation (E5) agrees exactly** — same premise, same induction, and my induction step
confirms the appendix's claim in full. Two things it leaves the reader unable to act on:

1. **What discharges the premise.** In a standard transformer the first writers *are* the token
   and positional embedding matrices, so the premise holds **iff $W_E$ (and $W_{\text{pos}}$)
   are themselves in the edit set**. Stated as "the stream must carry no component", it reads
   like an assumption to be hoped for; stated as "the embeddings count as writers and are
   orthogonalized too", it is a construction. Omit them and the equivalence fails at layer 0 by
   exactly $P h_{-1} \ne 0$, and attention then spreads the error across positions.
2. **Biases are writers.** $b_O$, $b_{\text{down}}$ and any additive term written into the
   stream must be orthogonalized as well, $b' = (I - \hat{\mathbf{r}}\hat{\mathbf{r}}^\top)b$.
   Editing only weight *matrices* leaves an input-independent offset along $\hat{\mathbf{r}}$ —
   the easiest error of this kind to ship, because it is invisible on any input-varying check.

**Correction.** "…needs one premise — that the stream carries no $\hat{\mathbf{r}}$ component
before the first writer — which is *discharged by construction* provided the embedding matrices
(and every additive bias that writes to the stream) are counted among the writers and
orthogonalized too."

---

### UNSTATED HYPOTHESIS-3 (severity: low-med) — "checked numerically" with no number, seed, or artifact

**Target, § E.5 line 94:** "*(Checked numerically as well as algebraically: rescaling $C$ over
four orders of magnitude leaves the update unchanged to machine precision while the constraint
$\hat W\mathbf{k}_* = \mathbf{v}_*$ continues to hold exactly.)*"

This is the "validated, without the number" pattern `.claude/rules/release-documentation.md`
and `sim-report-completeness.md` both forbid: no seed, no tolerance, no script path, no
dimensions. It is also *understated* — my replication covers **13** decades, not four.

**Correction.** Quote the residuals and park the script. From this review (numpy float64,
`default_rng(20260815)`, $D=12$, $H=7$, random SPD $C$): entrywise deviation
$\le 2.2\times10^{-16}$ (relative $\le 7.8\times10^{-16}$) for
$\alpha \in \{10^{-6},\,0.5,\,3,\,10^{3},\,10^{7}\}$, with $\lVert\Delta\mathbf{k}_*-\mathbf{r}\rVert = 3.1\times10^{-17}$
and $\operatorname{rank}\Delta = 1$. Also: "continues to hold exactly" should be "to
$3\times10^{-17}$" — in float64 it is not exact, and the appendix is elsewhere careful about
this distinction.

---

### NITs

1. **§ E.2 line 37, "whitened".** $C^{-1}\mathbf{k}_*$ is not a whitening — whitening is
   $C^{-1/2}\mathbf{k}_*$. $C^{-1}\mathbf{k}_*$ is the key expressed in the precision (dual)
   metric. Suggest "expressed in the inverse-key-covariance metric".
2. **§ E.2 line 37, "Sherman–Morrison-style".** Sherman–Morrison is the rank-one update of an
   *inverse*; here the rank-one object is the update to $W$ itself. "Rank-one memory write" is
   already exact and does not need the borrowed name.
3. **§ E.3 line 42, "a rank-$u$ update".** $\operatorname{rank}\Delta \le u$, with equality
   generically. The appendix is scrupulous about exactly this at line 109 ("rank at most one,
   with equality when both are non-zero"); the two should match.
4. **Eq (5) conflates estimator with estimand.** The left side is a sample average; writing the
   right side as $\boldsymbol{\mu}-\boldsymbol{\nu}$ reuses the symbols Eq (6) assigns to the
   *population* Gaussian means. Use $\bar{\mathbf{a}}^{+}-\bar{\mathbf{a}}^{-}$ and say it
   *estimates* $\mu-\nu$ — in a section arguing about estimands, the notation should carry the
   distinction.
5. **§ E.4 line 76, missing sign refinement.** In the parallel case the constant is necessarily
   **positive**: $\Sigma^{-1}d = cd$ with $c = d^\top\Sigma^{-1}d/\lVert d\rVert^2 > 0$. So
   detection and mean-difference can never be *anti*-parallel — they either agree in direction
   or are non-collinear. One clause, and it forecloses a sign worry a reader may otherwise have.
6. **§ E.4 line 67, "equal priors" is not needed for Eq (6).** The log-*likelihood* ratio is
   prior-free; priors move only the offset, never the direction. Harmless, but the hypothesis
   list is tighter without it (it *is* needed to call the threshold-at-zero rule Bayes-optimal).
7. **§ E.6 line 113, "stationary in $\Lambda$" is right but half the statement.** My E3(f)
   agrees with the appendix completely — a Lagrangian is not minimized in its multiplier. Worth
   adding the positive half: the **dual** $g(\Lambda) = \inf_{\Delta}\mathcal{J}$ is *maximized*
   in $\Lambda$; here $g(\Lambda) = \Lambda^\top\mathbf{r} - \tfrac12(\mathbf{k}_*^\top C^{-1}\mathbf{k}_*)\lVert\Lambda\rVert^2$,
   a concave quadratic whose maximizer reproduces Eq (3)'s $\Lambda$ exactly.
8. **§ E.4 line 80, the induction dodges a trap worth naming.** LayerNorm/RMSNorm does **not**
   commute with $I - \hat{\mathbf{r}}\hat{\mathbf{r}}^\top$, so any "push the projector through
   the layers" argument is *wrong*. The sum-of-writers induction never needs commutation — only
   equality of the values each component *reads*. Saying so pre-empts the obvious wrong proof.
   (Related and reassuring: weight tying $W_U = W_E^\top$ is benign, because $I-\hat{\mathbf{r}}\hat{\mathbf{r}}^\top$
   is idempotent, so the tied readout sees the same logits either way.)
9. **§ E.5 invariance scope.** The invariance is under a global **positive scalar** $C \mapsto \alpha C$
   only. It is *not* invariance under $C \mapsto C + \lambda I$ — the damping real
   implementations add — which changes eigenvalue *ratios* and therefore changes $\Delta$. Worth
   one clause so a reader does not over-generalize "the constant is harmless" into "the
   regularizer is harmless".

---

### Explicitly checked and found CORRECT (no action)

- **Eq (2)** stationarity $\Delta C - \boldsymbol{\lambda}\mathbf{k}_*^\top = 0$ and both matrix
  derivatives — reproduced independently, including the symmetry step $\mathbf{k}_*^\top C^{-1} = (C^{-1}\mathbf{k}_*)^\top$.
- **Eq (3)** closed form and multiplier — identical to mine; denominator identification
  $(C^{-1}\mathbf{k}_*)^\top\mathbf{k}_* = \mathbf{k}_*^\top C^{-1}\mathbf{k}_*$ correct.
- **Eq (4) shapes** — $R\in\mathbb{R}^{H\times u}$, $K_1\in\mathbb{R}^{D\times u}$,
  $RK_1^\top\in\mathbb{R}^{H\times D}$ against a $D\times D$ inverse: **conformable exactly as
  written**, and the product has the shape of the edited weight matrix. Verified numerically
  ($7\times12$ for $H=7$, $D=12$, $u=4$). The brief's suspicion here is unfounded.
- **Eq (5)** and the "matched in size" hypothesis — correct; my E1 finds the hypothesis is in
  fact only *equal cardinality*, and notably **not** any property of the pairing itself.
- **Eq (6)** — matches my derivation term for term, signs and $\tfrac12$ included; the stated
  reason for the quadratic cancellation (shared covariance) is right, and the log-determinants
  cancel for the same reason.
- **§ E.4 line 76 iff** — correct in **both** directions, and the demotion of isotropy to
  "sufficient but far from necessary" is exactly my (b). This is the sharpest paragraph in the
  appendix.
- **Eq (7) and § E.5 lines 87–94** — the scale-invariance derivation is correct step by step,
  and the claim is **exactly** right (an identity), not approximately: confirmed to float64
  round-off across 13 decades of $\alpha$. The underlying reason — positive rescaling of a
  *constrained* objective cannot move the argmin — is worth stating in one line, since it makes
  the result obvious and delimits its scope (see NIT 9).
- **§ E.6 line 103** — the trace criticism of the source is correct: $\lVert\hat WK-V\rVert_F^2$
  is scalar, the printed expansion is matrix-valued, and the cross-term coefficient the
  appendix prints is the one the trace produces.
- **§ E.6 line 105** derivatives; **line 107** both guarantees ($C\succ0$ requiring the
  nondegeneracy assumption, and convex-quadratic-plus-affine sufficiency); **line 109** rank-one
  scoping to the weight update rather than the input–output map; **line 113** the
  Lagrangian/saddle-point correction — all correct and all independently reproduced.

### Out of scope for this review

§ E.5 line 85 and § E.6 line 111 make **external-source factual claims** (ROME's
"$C \propto \mathbb{E}[kk^\top]$" wording, MEMIT's $\lambda$ of $1.5\times10^{4}$ / $15{,}000$ /
$20{,}000$, ROME's two-token-position objective, the $1\times10^{2}$ KL coefficient). This was a
**mathematical** re-derivation and did not open any source PDF; per
`.claude/rules/citation-integrity.md` these are neither confirmed nor disputed here and should
be routed to `citation-audit`.

### Reproduction

The E4 numerics were run with `python3` + `numpy`, float64, `numpy.random.default_rng(20260815)`,
$D=12$, $H=7$, $u=4$, random SPD $C$ and $C_0$ (Wishart plus a positive diagonal shift). The
script is inline in this review's transcript; it recomputes the ROME closed form under
$\alpha C$, the MEMIT update under $\alpha C_0$, both limits, the $O(\alpha)$ convergence table,
and the $u=1$ MEMIT-to-ROME reduction.
