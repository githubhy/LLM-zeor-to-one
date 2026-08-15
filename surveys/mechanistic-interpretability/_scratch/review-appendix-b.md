# Independent re-derivation — Appendix B (superposition capacity)

`[opt:MATH-REDERIVE]` adversarial review. **Phase 1 was written before the target file
was opened.** Reviewer derived B1–B4 from first principles; all numerics recomputed in
`python3` (transcripts inline).

---

## Phase 1 — derivation from scratch (target NOT yet read)

### B1 — Almost-orthogonal packing

#### (a) The concentration bound

Let $u,v$ be i.i.d. uniform on $S^{d-1}$. By rotational invariance condition on
$v=e_1$; then $\langle u,v\rangle = u_1$, whose density on $[-1,1]$ is
$\propto (1-t^2)^{(d-3)/2}$. Equivalently $u_1^2 \sim \mathrm{Beta}(\tfrac12,\tfrac{d-1}{2})$,
so the tail is exactly

$$P(|\langle u,v\rangle| > \varepsilon) = 1 - I_{\varepsilon^2}\!\left(\tfrac12,\tfrac{d-1}{2}\right)$$

with $I$ the regularized incomplete beta.

**The result being invoked is Lévy's isoperimetric / concentration-of-measure inequality
on the sphere**, applied to the 1-Lipschitz function $u \mapsto \langle u,v\rangle$ whose
median is $0$. The standard statement is

$$P(|f - \mathrm{med}\,f| > \varepsilon) \le 2\exp\!\left(-\tfrac{(d-1)\varepsilon^2}{2}\right),$$

i.e. with $d-1$, not $d$. Equivalently one may quote Ball's spherical-cap lemma
($\sigma\{u_1 \ge \varepsilon\} \le e^{-d\varepsilon^2/2}$).

**Verdict on the constant.** $2\exp(-d\varepsilon^2/2)$ is a *valid upper bound*, not an
equality, and the exponent constant is convention-dependent ($d$ vs $d-1$ vs $d-2$ appear
in different textbook statements; at $d=768$ they differ by $<2\%$). Numerically verified
that the $d$-form does upper-bound the exact tail everywhere tested:

```
d=768 eps=0.5 : exact 0            bound 4.062e-42
d=768 eps=0.3 : exact 0 (underflow) bound 1.958e-15
d=768 eps=0.1 : exact 5.511e-03    bound 4.299e-02   (bound loose by 7.8x)
d=768 eps=0.05: exact 1.660e-01    bound 7.658e-01   (bound loose by 4.6x)
stress d in {2,3,5,10,50,100} x eps in {0.1,0.3,0.5,0.9}: never violated
```

So: **an upper bound with a loose constant** (loose by a factor of ~5–8 in the regime
where the tail is not astronomically small — the sub-Gaussian form discards a
$\Theta(1/(\varepsilon\sqrt{d}))$ polynomial prefactor). It is *not* exact.

#### (b) Union bound

Draw $N$ points i.i.d. uniform on $S^{d-1}$. Let $A$ = "some pair has
$|\langle u_i,u_j\rangle| > \varepsilon$". Then

$$P(A) \le \binom{N}{2}\cdot 2e^{-d\varepsilon^2/2} \le \frac{N^2}{2}\cdot 2e^{-d\varepsilon^2/2} = N^2 e^{-d\varepsilon^2/2}.$$

$P(A) < 1$ (so the complement has positive probability, so a good configuration
**exists**) as soon as $N^2 < e^{d\varepsilon^2/2}$, i.e.

$$N < e^{d\varepsilon^2/4}.$$

The arithmetic supports the $/4$: it is the square root of the $/2$ in the tail exponent,
introduced by the $\binom{N}{2}\sim N^2$ pair count. (Keeping $N(N-1)$ rather than $N^2$
changes nothing to leading order.)

**What it guarantees, precisely:** *there exists* a set of $N$ unit vectors in
$\mathbb{R}^d$ with all pairwise $|\langle\cdot,\cdot\rangle| \le \varepsilon$. It is a
probabilistic **existence / lower** bound on the packing number. It says nothing about the
maximum.

#### (c) Numbers at $d=768$

```
eps=0.5: exponent 48.000  -> N = 7.017e20
eps=0.3: exponent 17.280  -> N = 3.196e07
eps=0.1: exponent  1.920  -> N = 6.82
```

#### (d) CRITICAL — is $6.8$ a statement about $\mathbb{R}^{768}$ at $\varepsilon=0.1$?

**No. The bound is simply vacuous there.** The $768$ standard basis vectors are *exactly*
orthogonal, hence trivially $0.1$-almost-orthogonal, so at least $768 \gg 6.8$ such vectors
exist. The union-bound estimate is a lower bound that happens to be far below a trivial
lower bound.

The crossover is sharp and computable: $e^{d\varepsilon^2/4} > d$ requires
$\varepsilon > 2\sqrt{\ln d / d}$, which at $d=768$ is $\varepsilon > 0.186$:

```
eps=0.05  -> 1.6      VACUOUS (weaker than the orthonormal basis)
eps=0.10  -> 6.8      VACUOUS
eps=0.186 -> 767      VACUOUS (crossover)
eps=0.20  -> 2.16e3   useful
eps=0.30  -> 3.20e7   useful
eps=0.50  -> 7.02e20  useful
```

So **any use of $\varepsilon \lesssim 0.19$ at $d=768$ is outside the formula's useful
range**, and quoting $\approx 7$ as "how many features fit" would be an error of
interpretation, not of arithmetic.

**Legitimate to call it a lower bound / existence result: yes.** Illegitimate to call it
"the capacity", "the number of features that fit", or an upper bound of any kind. The true
packing number is $\ge \max(d,\,e^{d\varepsilon^2/4})$; the known two-sided picture
(Alon-type results) is $\exp(c\,d\varepsilon^2) \le N_{\max} \le \exp(C\,d\varepsilon^2\log(1/\varepsilon))$
for $\varepsilon \gtrsim d^{-1/2}$ — so even the *exponential rate* is only pinned to
within a $\log(1/\varepsilon)$ factor.

#### (e) Is this the Johnson–Lindenstrauss lemma?

**Verdict: a corollary, not the lemma.** JL is a statement about a *given* point set:
any $n$ points in $\mathbb{R}^D$ embed into $\mathbb{R}^m$, $m=O(\varepsilon^{-2}\log n)$,
with all pairwise **distances** preserved to $(1\pm\varepsilon)$. The packing statement is
about the *existence of an almost-orthogonal system* — a different quantifier structure and
a different object (inner products, not distances).

They are linked in two ways:
1. **Same proof machinery** — concentration of a quadratic/linear form plus a union bound
   over $\binom{n}{2}$ pairs. This is why the exponents match.
2. **Genuine corollary** — apply JL to the $N$ standard basis vectors of $\mathbb{R}^N$.
   Preserved norms + preserved pairwise distances imply preserved inner products to
   $O(\varepsilon)$, so the $N$ images are $O(\varepsilon)$-almost-orthogonal in
   $\mathbb{R}^{d}$ with $d = O(\varepsilon^{-2}\log N)$, i.e. $N = e^{\Omega(d\varepsilon^2)}$.

So "by JL" is defensible shorthand (and is what Elhage et al. write), but a careful text
should say **"a JL-type argument"** or **"a corollary of JL"**. Writing "the JL lemma
states that $\mathbb{R}^d$ holds $e^{d\varepsilon^2/4}$ almost-orthogonal directions" would
be a misattribution — that is not what the lemma states.

---

### B2 — Interference in superposition

**Setup.** $m$ features, unit directions $w_1,\dots,w_m \in \mathbb{R}^d$; activations
$f_j$; the residual stream carries $x=\sum_j f_j w_j$. Read feature $i$ with its own
direction:

$$\hat f_i = \langle w_i, x\rangle = f_i\|w_i\|^2 + \sum_{j\ne i} f_j \langle w_i,w_j\rangle
= f_i + \sum_{j\ne i} f_j c_{ij}, \qquad c_{ij}\equiv\langle w_i,w_j\rangle.$$

$$\mathbb{E}\big[(\hat f_i - f_i)^2\big]
= \sum_{j\ne i}\mathbb{E}[f_j^2]\,\mathbb{E}[c_{ij}^2]
+ \sum_{j\ne k,\ j,k\ne i}\mathbb{E}[f_jf_k]\,\mathbb{E}[c_{ij}c_{ik}].$$

With $\mathbb{E}[f_j^2] = p\,s$ (active w.p. $p$, $\mathbb{E}[f_j^2\mid\text{active}]=s$),
$\mathbb{E}[c_{ij}^2]=1/d$, and the cross term killed:

$$\boxed{\ \mathbb{E}\big[(\hat f_i-f_i)^2\big] = \frac{(m-1)\,p\,s}{d}\ }$$

MC check of the key moment at $d=768$: $\mathbb{E}[\langle u,v\rangle^2] = 1.309\times10^{-3}$
vs $1/d = 1.302\times10^{-3}$ (200k samples). ✓

**Every hypothesis required** (this list is the deliverable — most write-ups state 2 of 6):

| # | Hypothesis | Why it is load-bearing |
|---|---|---|
| H1 | $\|w_j\| = 1$ for all $j$ | otherwise the signal term is $f_i\|w_i\|^2$, not $f_i$ |
| H2 | Directions i.i.d. uniform on $S^{d-1}$ (or i.i.d. Gaussian, normalized) | gives $\mathbb{E}[c_{ij}^2]=1/d$ **exactly** |
| H3 | **The cross terms vanish because $\mathbb{E}[c_{ij}c_{ik}]=0$**, not because the activations are uncorrelated | in the ReLU toy model $f_j\ge 0$, so $\mathbb{E}[f_jf_k]=p^2\bar f^2 > 0$ — the cross term is killed *only* by the randomness of the directions. This is the hypothesis most often left unstated. |
| H4 | Features (at least pairwise) independent, homogeneous $p$ and $s$ | else $\mathbb{E}[f_j^2]$ is not a common $ps$ |
| H5 | Read-out is the feature's **own** direction, not the dual-frame / optimal linear probe | the optimal probe (pseudo-inverse row) strictly beats this; the result is an upper bound on the error of a *particular* decoder |
| H6 | The result is an expectation **over the random frame**, not a guarantee for a given $W$ | for a fixed frame, $\sum_{j\ne k}c_{ij}c_{ik} = (\sum_{j\ne i}c_{ij})^2 - \sum_{j\ne i}c_{ij}^2 \ne 0$ in general |

**Sharpening worth noting (H2).** For a *tight frame* (the configuration a trained model
approaches), Welch gives average off-diagonal $\overline{c^2} = \frac{m-d}{d(m-1)}$, which
is $\le 1/d$ — strictly better than random. At $d=768$: $m=1000 \Rightarrow 0.23\times(1/d)$;
$m=5000 \Rightarrow 0.85\times$; $m=10^5 \Rightarrow 0.99\times$. So $1/d$ is an
**asymptotic ($m\gg d$) approximation that is conservative** for a trained/optimized frame.

**Capacity at required SIR $\tau$.**

$$\mathrm{SIR} = \frac{\mathbb{E}[f_i^2\mid i \text{ active}]}{\mathbb{E}[(\hat f_i-f_i)^2]}
= \frac{s}{(m-1)ps/d} = \frac{d}{(m-1)p} \ \ge\ \tau
\ \Longrightarrow\ \boxed{\ m_{\max} = 1 + \frac{d}{p\tau}\ }$$

**Does $s$ cancel? Yes** — signal and interference are both linear in $s$, so the capacity
is scale-invariant in the feature magnitude. Verified algebraically above.

**Basis caveat `[opt:MATH-BASIS]`.** $s$ cancels *only* because "signal" is defined
**conditional on the feature being active**. If signal were defined unconditionally
($\mathbb{E}[f_i^2] = ps$), then $\mathrm{SIR}=d/(m-1)$ and **$p$** would cancel instead,
giving $m_{\max}=1+d/\tau$ — a completely different (and $p$-independent) capacity. The
conditional basis is the right one (you decode a feature when it is on), but the choice
must be declared at the point of use.

---

### B3 — The recovery bound

**Compressed sensing.** A $k$-sparse $x\in\mathbb{R}^n$ is recoverable from $m$ linear
measurements when $m = \Omega\!\big(k\log(n/k)\big)$ (RIP + $\ell_1$ decoding; the same
rate is information-theoretically necessary up to constants).

**Substitute $k = pn$** (expected support size under i.i.d. activation probability $p$):

$$\log(n/k) = \log\!\big(n/(pn)\big) = \log(1/p) \quad\text{— exactly, by cancellation of } n.$$

$$m = \Omega\!\big(p\,n\log(1/p)\big) \quad\Longleftrightarrow\quad
\boxed{\ n = O\!\left(\frac{m}{p\log(1/p)}\right)\ } \ \xrightarrow{\ m=d\ }\
n_{\max} = O\!\left(\frac{d}{p\log(1/p)}\right).$$

**Multiplier $1/(p\log(1/p))$:**

```
p       ln          log2        log10
0.1     4.3429      3.0103      10.0
0.01    21.7147     15.0515     50.0
0.001   144.7648    100.3433    333.3
```

So $4.3 / 21.7 / 145$ is the **natural-log** evaluation. The base is not free — $\log_2$
gives $3.0/15.1/100$. `[opt:MATH-BASIS]`: the log base must be declared.

**Comparison of the two criteria.**

$$\frac{m^{\text{int}}_{\max}}{n^{\text{rec}}_{\max}}
= \frac{d/(p\tau)}{d/(p\ln(1/p))} = \frac{\ln(1/p)}{\tau}.$$

"Binding" = the **smaller** capacity = the active constraint. Therefore:

$$\ln(1/p) < \tau \ \Longrightarrow\ \text{ratio} < 1 \ \Longrightarrow\ \textbf{interference binds.}$$
$$\ln(1/p) > \tau \ \Longrightarrow\ \textbf{recovery binds.}$$

**At $\tau=10$, $p \ge 10^{-3}$:** $\ln(1/p) \le \ln 1000 = 6.908 < 10$, so the ratio is
$\le 0.69 < 1$ and **the interference criterion is the tighter (smaller) bound throughout
that range.** Absolute values at $d=768,\tau=10$:

```
p      interference m_max   recovery n_max   min (binding)
0.1    769.0                3335.4           interference
0.01   7681.0               16676.9          interference
0.001  76801.0              111179.4         interference
crossover: p = e^{-tau} = 4.54e-5; for p < that, recovery binds.
```

**Two caveats that limit how much this comparison can be claimed:**

- **C1 — apples to oranges.** $d/(p\tau)$ has an explicit constant; $d/(p\log(1/p))$ is
  $O(\cdot)$ with an unspecified constant (RIP constants for Gaussian matrices are
  typically $2$–$10$). A factor of $\ge 2$ in the recovery constant flips the verdict at
  $\tau=10,p=10^{-3}$ (ratio $0.69$ has only $1.45\times$ of margin). So the honest claim
  is *"interference binds at $\tau=10$ for $p\gtrsim10^{-3}$ **to within the unknown
  recovery constant**"* — not a hard verdict.
- **C2 — the decoder is not an $\ell_1$ solver.** The recovery bound presumes RIP plus a
  convex/greedy decoder. The model's actual read-out is one linear probe + a ReLU. So the
  recovery bound is an **information-theoretic possibility** ceiling that the architecture
  does not attain, while the interference bound describes the decoder actually used. They
  answer different questions; "which binds" compares a *feasibility* limit against an
  *achieved-SNR* limit.

---

### B4 — One-active-feature loss decomposition

**Model.** $W\in\mathbb{R}^{d\times m}$ with columns $W_i$; $h=Wx\in\mathbb{R}^d$;
$x' = \mathrm{ReLU}(W^\top W x + b)\in\mathbb{R}^m$;
$L=\sum_x\sum_i I_i (x_i-x'_i)^2$.

Condition on exactly one active feature $i$: $x = x_i e_i$, $x_i = t \sim U[0,1]$.

**Componentwise $W^\top W x$.** Since only coordinate $i$ of $x$ is nonzero,

$$(W^\top W x)_j = \sum_k \langle W_j,W_k\rangle x_k = \langle W_j, W_i\rangle\, t .$$

So

- $j=i$: $\ \|W_i\|^2 t \equiv n_i t$
- $j\ne i$: $\ c_{ji} t$ with $c_{ji}=\langle W_j,W_i\rangle$

**Outputs.** $x'_i = \mathrm{ReLU}(n_i t + b_i)$; $x'_j = \mathrm{ReLU}(c_{ji}t + b_j)$.

**Targets.** $x_i = t$ for the active coordinate; $x_j = 0$ for every $j\ne i$.

**Assembled loss** (density of $U[0,1]$ is $1$):

$$L_1(i) = \underbrace{I_i\!\int_0^1\!\big(t-\mathrm{ReLU}(n_i t + b_i)\big)^2 dt}_{\text{reconstruction}}
\;+\; \underbrace{\sum_{j\ne i} I_j\!\int_0^1\!\mathrm{ReLU}(c_{ji}t+b_j)^2\,dt}_{\text{interference}}$$

(times $P(\text{only } i \text{ active})$ if $L$ is written as an expectation.)

#### (a) When is the interference term exactly zero?

With $b_j=0$ and $t\ge 0$: $\mathrm{ReLU}(c_{ji}t)^2 = c_{ji}^2t^2$ if $c_{ji}>0$, and
**exactly $0$** if $c_{ji}\le 0$. So negative interference costs nothing — and, because the
ReLU is in its dead zone, the *gradient* is zero there too, which is what makes such
configurations stable, not merely cheap.

**Is "negative interference is free" exactly true? Yes — but only under four conditions,
all of which must be stated:**

1. **Exactly one feature active.** With $\ge 2$ active, the pre-activation at $j$ is
   $\sum_{k\in\text{active}} c_{jk}x_k + b_j$; a positive $c_{jk}$ from a second active
   feature can lift a negative $c_{ji}$ above zero, and the freeness is destroyed. The
   one-active regime dominates only when $\binom{m}{2}p^2 \ll mp$, i.e. $p \ll 2/m$ —
   a genuinely strong sparsity requirement, not "sparse-ish".
2. **$b_j \le 0$.** If $b_j>0$ then $\mathrm{ReLU}(c_{ji}t+b_j)>0$ for
   $t < b_j/|c_{ji}|$ even with $c_{ji}<0$, so it is *not* free.
3. **Non-negative activations** $x_i\ge0$ (as in $U[0,1]$). With signed features the sign
   of $c_{ji}x_i$ flips and the asymmetry disappears entirely.
4. It is free *at the interfered-with feature $j$*; it has no effect on $x'_i$ either way.

#### (b) Effect of $b_j < 0$ on the free region — exact condition

The $j$-integrand vanishes wherever $c_{ji}t+b_j \le 0$, i.e. $t \le -b_j/c_{ji}$ (for
$c_{ji}>0$). The whole integral vanishes iff $-b_j/c_{ji} \ge 1$:

$$\boxed{\ \text{interference } c_{ji} \text{ is entirely free} \iff c_{ji} \le -b_j = |b_j| \ }$$

So a negative bias **widens the free region from $\{c_{ji}\le0\}$ to
$\{c_{ji}\le|b_j|\}$ — by exactly $|b_j|$**: *positive* interference up to magnitude
$|b_j|$ becomes free too. Beyond that the residual cost has the closed form

$$\int_0^1 \mathrm{ReLU}(c t + b)^2\,dt = \frac{\max(0,\,c+b)^3}{3c}\quad (c>0),$$

verified numerically (`c=0.4,b=-0.1 -> 0.0225` both ways; `c=0.2,b=-0.3 -> 0` both ways;
all 12 test pairs agree to $10^{-8}$).

**The bias is not free, though** — it damages $j$'s *own* reconstruction. With $n_j=1$,
$b_j=-\beta$:

$$\int_0^1\!\big(t-\mathrm{ReLU}(t-\beta)\big)^2 dt = \frac{\beta^3}{3} + \beta^2(1-\beta)
= \beta^2\!\left(1-\tfrac{2\beta}{3}\right)$$

(numeric: $\beta=0.1 \to 0.0093333$ both ways ✓). So the optimum trades a **quadratic**
own-cost $\approx\beta^2$ against a **cubic** saving $\sum_j (c+b)^3/(3c)$ across many
interferers — which is exactly why trained toy models learn small negative biases rather
than large ones.

#### (c) Linear contrast (no ReLU)

$x'=W^\top Wx+b$, so $x'_j = c_{ji}t+b_j$ and

$$\int_0^1 (c_{ji}t+b_j)^2\,dt = \frac{c_{ji}^2}{3} + c_{ji}b_j + b_j^2
\ \xrightarrow{\ b_j=0\ }\ \frac{c_{ji}^2}{3}.$$

(numeric ✓ for $c=\pm0.4$, $b\in\{0,-0.2\}$.)

**Does "no free region" follow? Yes.** At $b=0$ the cost is $c_{ji}^2/3$ — an even
function of $c_{ji}$, so the sign asymmetry that created the free region is gone and
*every* nonzero off-diagonal is paid for. There is no $c$ with zero cost except $c=0$.
Note the mechanism is the ReLU's dead zone, not the bias: adding $b_j<0$ to the linear
model does **not** create a free region (it merely shifts the minimizing $c$; indeed
$c=-0.4,b=-0.2$ costs $0.173$, *more* than $b=0$'s $0.053$).

#### (d) Is "a model with $W^\top W$ invertible exhibits no superposition" correct?

**It is true but vacuous, and it is not the claim that should be made.**
$W\in\mathbb{R}^{d\times m}$ gives $\mathrm{rank}(W^\top W)\le d$. So $W^\top W$
(an $m\times m$ matrix) is invertible **iff $m\le d$ and $W$ has full column rank** — and
$m\le d$ is *the definition of not being in superposition*. The statement therefore
reduces to "if there are no more features than dimensions, there is no superposition,"
which is a tautology, not a result about the linear model.

**The correct statement** is about the *linear model's optimum*: with
$\mathbb{E}[xx^\top]=D$ diagonal (independent features) and importances $I$, minimizing
$\mathbb{E}\|I^{1/2}(x-Ax)\|^2$ over PSD $A=W^\top W$ of rank $\le d$ is a weighted
low-rank approximation whose solution (Eckart–Young) is the **diagonal projector onto the
$d$ largest $I_jD_{jj}$**. The optimal linear model stores the $d$ most important features
**orthogonally** and sets the rest to zero — no superposition, at any sparsity.

The sharpest way to say it: **in the linear model the sparsity $p$ enters only through
$D_{jj}=ps$, identically for every $j$, so it cannot change the ranking and therefore
cannot induce superposition.** Superposition in the ReLU model is *caused by* the
interaction of sparsity with the ReLU's free region — neither alone suffices.

<!-- PHASE-1-END -->

---

## Phase 2 — comparison against the target

Target: `surveys/mechanistic-interpretability/appendix-b-superposition.md`, §B.5–§B.8,
equations tagged 5–8. (§B.1–§B.4 read only as context; two findings touch §B.4's caption
because §B.6 compares against it.)

### Scoreboard on the three items flagged as high-inversion-risk

| Item | Verdict |
|---|---|
| The $e^{d\epsilon^2/4}$ numbers ($7\times10^{20}$ / $3\times10^7$ / $\approx 7$) | **CORRECT** — reviewer gets $7.017\times10^{20}$, $3.196\times10^{7}$, $6.821$ |
| "Which bound binds" direction | **CORRECT** — interference binds iff $\tau > \log(1/p)$; verified numerically, all three in-range $p$ |
| The multipliers $4.3 / 21.7 / 145$ | **CORRECT** — reviewer gets $4.3429 / 21.7147 / 144.765$ (natural log) |

No arithmetic error found in any published number. All findings below are about
*hypotheses, scope, and one algebraic drop*, not about the headline figures.

**Counts.** ERROR 4 · UNSTATED HYPOTHESIS 5 · OVERSTATEMENT 4 · NIT 6.

---

### ERROR-1 (high) — §B.8 applies a valid metric critique to metric-INVARIANT bounds

**Target (line 135, 137, 139):** "Every bound in §B.5 and §B.6 measures orthogonality by
the Euclidean inner product in the raw residual basis. That is a choice … So a capacity
theorem proved in the Euclidean metric bounds the number of *Euclidean*-almost-orthogonal
directions, and transporting it to a claim about features requires the two metrics to
agree, which nobody has shown they do. … It does mean the *numbers* in these bounds are
conditional on a basis choice that the model itself does not make."

**Derivation.** Let $M \succ 0$ define the causal inner product
$\langle u,v\rangle_M = u^\top M v$. The map $\Phi: u \mapsto M^{-1/2}u$ satisfies
$\langle \Phi u, \Phi v\rangle_M = u^\top M^{-1/2} M M^{-1/2} v = \langle u,v\rangle$.
$\Phi$ is therefore an **isometry** from $(\mathbb{R}^d,\langle\cdot,\cdot\rangle)$ onto
$(\mathbb{R}^d,\langle\cdot,\cdot\rangle_M)$: it carries unit vectors to $M$-unit vectors
and preserves every pairwise inner product exactly. Hence the packing number

$$N_{\max}(d,\epsilon) = \max\{N : \exists\, u_1..u_N,\ \lVert u_i\rVert=1,\ \lvert\langle u_i,u_j\rangle\rvert\le\epsilon\}$$

is **identical in every inner product on $\mathbb{R}^d$**. Equation (6) holds verbatim in
the causal metric; nothing needs transporting. The same is true of Equation (7): it counts
*measurements* ($m$) and *nonzeros* ($k$), both invariant under an invertible linear
reparametrization of the measurement space.

**What actually is metric-dependent** — and it is a real and worthwhile critique, just
aimed one section too far right:

- whether a **given trained** $W$'s columns are almost-orthogonal;
- §B.2's measured feature dimensionality $D_i$ (Equation (2)) and the interference
  functional $\sum_{i\ne j}(\hat W_i\cdot\hat W_j)^2$;
- §B.4's closed form $(m-1)ps/d$, whose $1/d$ is $\mathbb{E}[c_{ij}^2]$ under the
  *Euclidean* uniform measure on the sphere.

**Correction.** Retarget §B.8 from the existence bounds to the measured quantities. The
honest sentence is: *"The bounds themselves are metric-free — a packing number depends only
on the dimension. What is metric-relative is whether the model's actual directions realize
them, which is what §B.2's $D_i$ and §B.4's interference measure — and those are computed
in a basis the model does not privilege."* As written, the section's closing thesis is
false of the two sections it names.

---

### ERROR-2 (high) — "$W^\top W$ invertible exhibits no superposition" is vacuous, not checkable

**Target (line 128):** "…the crisp checkable version of it is that a model with
$W^{\top}W$ invertible exhibits no superposition."

**Derivation.** Under §B.1's own declared shape $W\in\mathbb{R}^{m\times n}$ with $m<n$,
$W^\top W$ is $n\times n$ with $\mathrm{rank}(W^\top W)=\mathrm{rank}(W)\le m<n$. It is
**singular for every $W$ in the superposition regime** — the hypothesis is unsatisfiable
exactly when the conclusion is interesting. "$W^\top W$ invertible" $\iff$ "$n\le m$ and
$W$ has full column rank" $\iff$ "there are no more features than dimensions", which *is*
the definition of no-superposition. The statement is a tautology.

It also fails to do the section's work in a second way: it does not mention the
nonlinearity, so it is equally true of the **ReLU** model (a ReLU model with $n\le m$ also
has $W^\top W$ invertible). A criterion that cannot distinguish the linear model from the
ReLU model cannot be "the formal content" of a linear-vs-ReLU contrast.

(The alternative reading $WW^\top$ invertible is worse: $WW^\top$ is $m\times m$ and is
generically invertible *in* superposition, making the statement false rather than vacuous.)

**Correction — the claim the section wants.** With $\mathbb{E}[\mathbf{x}\mathbf{x}^\top]=D$
diagonal (independent features) and importances $I$, the linear model minimizes
$\mathbb{E}\lVert I^{1/2}(\mathbf{x}-A\mathbf{x})\rVert^2$ over PSD $A=W^\top W$ of rank
$\le m$ — a weighted low-rank approximation whose Eckart–Young optimum is the **diagonal
projector onto the $m$ largest $I_jD_{jj}$**. The optimal linear model stores the $m$ most
important features orthogonally and drops the rest, **at every sparsity**. The sharp reason
sparsity cannot rescue it: $D_{jj}=\mathbb{E}[x_j^2]=ps$ is *identical for every $j$*, so
$p$ cannot change the ranking and therefore cannot induce superposition. That is crisp,
checkable, and actually about linearity.

---

### ERROR-3 (high-med) — the linear-contrast interference term is off by a factor of $3$, with $b_j$ silently dropped

**Target (line 128):** "Remove the nonlinearity and the same conditioning gives an
interference term $\sum_{i\ne j} I_j (W_j\cdot W_i)^2$ — a plain square, which charges for
non-orthogonality **in both signs and at every magnitude**."

**Derivation.** "The same conditioning" is Equation (8)'s: $x_i\sim U[0,1]$, integrated
$\int_0^1 \cdot\, dx_i$. Writing $c=W_j\cdot W_i$,

$$\int_0^1 (c\,x_i + b_j)^2\,dx_i = \frac{c^2}{3} + c\,b_j + b_j^2 \ \xrightarrow{\ b_j=0\ }\ \frac{c^2}{3}.$$

Numerically confirmed ($c=0.4,b=0 \Rightarrow 0.053333 = 0.16/3$). The published term is
$c^2$ — **three times too large** — because the $\int_0^1 x_i^2\,dx_i = 1/3$ was dropped
while every *other* term in the section keeps its integral. Equation (8) itself carries
$\int_0^1\!\cdots dx_i$ explicitly, so this is an internal inconsistency, not a change of
convention.

**Second defect in the same sentence: $b_j$ vanished.** The ReLU version keeps $b_j$; the
linear version drops it without saying so. This matters, because **the "both signs" claim
is exactly the $b_j=0$ special case**. With $b_j<0$ the linear cost
$c^2/3+cb_j+b_j^2$ is a parabola in $c$ centred at $c^\ast=-\tfrac{3}{2}b_j>0$, not at $0$
— so the *linear* model also prefers positive-signed interference once it has a negative
bias. Verified: $c=+0.4,b=-0.2 \Rightarrow 0.01333$ versus $c=-0.4,b=-0.2 \Rightarrow 0.17333$.

**Correction.** Write the term as $\sum_{i\ne j} I_j\big(\tfrac13 (W_j\cdot W_i)^2 + (W_j\cdot W_i)b_j + b_j^2\big)$
and state the sign-symmetry claim **at $b_j=0$**. The qualitative conclusion (no free
region, every nonzero off-diagonal is charged, since the cost vanishes only at
$c=-\tfrac32 b_j$ and is strictly positive on a set of full measure) survives — which is
precisely why this error would pass a casual read.

---

### ERROR-4 (high-med) — $m$ means two different things one line apart, in the paragraph that compares the two bounds

**Target.** §B.1 line 11: "$W\in\mathbb{R}^{m\times n}$ with $m<n$" — $m$ = bottleneck,
$n$ = features. Equation (2): $\sum_i D_i \approx m$ — bottleneck. §B.6 line 100:
"recoverable from an $m$-dimensional projection" and Equation (7) $m=\Omega(np\log(1/p))$
— bottleneck. But §B.4 line 60–62: "residual width $d=768$", "$(m-1)ps/d$",
"$m_{\max}=1+d/(p\tau)$", and the operating points "$(d,m,p)\in\{(64,200,0.05),\dots\}$"
— here $m$ = **feature count** and $d$ = bottleneck. Line 109 then puts both in adjacent
sentences: "Figure `F-B1` gives a capacity $m_{\max} = 1 + d/(p\tau)$; Equation (7) gives
$d/(p\log(1/p))$ in the same variables."

**Why it is an error and not a nit.** The clause "in the same variables" is doing a silent
renaming ($m_{\text{Eq }7}\to d$, $n_{\text{Eq }7}\to m$) five lines after Equation (7)
used $m$ for the other object. A reader checking the ratio has to guess which $m$ each
symbol denotes — in the one paragraph whose conclusion inverts if the ratio is taken the
other way up.

**Correction.** Fix one convention appendix-wide. Recommend $d$ = bottleneck / residual
width, $m$ = feature count (the §B.4/§B.5 convention, and the one the survey body uses),
and restate §B.1 as $W\in\mathbb{R}^{d\times m}$ with $d<m$ and Equation (7) as
$d=\Omega(mp\log(1/p)) \iff m=O(d/(p\log(1/p)))$.

---

### OVERSTATEMENT-1 (med-high) — the "which binds" verdict compares an explicit constant against an $O(\cdot)$

**Target (line 109):** "…so **the interference criterion binds whenever $\tau > \log(1/p)$**
and the recovery criterion binds otherwise. At the figure's operating point ($\tau = 10$)
and any $p \ge 10^{-3}$, $\log(1/p) \le 6.9 < 10$, so the interference bound is the tighter
of the two and the figure is the conservative statement."

**The direction is CORRECT** — independently derived:
$m^{\text{int}}_{\max}/n^{\text{rec}}_{\max} = \ln(1/p)/\tau$, and binding = *smaller*
capacity, so interference binds iff $\ln(1/p)<\tau$. Verified across
$\tau\in\{2,5,10\}$, $p\in\{10^{-1}\dots10^{-6}\}$; the crossover is $p=e^{-\tau}$
($=4.54\times10^{-5}$ at $\tau=10$). Absolute values at $d=768,\tau=10$:

```
p=0.1   interference 769.0    recovery 3335.4   -> interference binds
p=0.01  interference 7681.0   recovery 16676.9  -> interference binds
p=0.001 interference 76801.0  recovery 111179.4 -> interference binds
```

**The overstatement is the certainty, not the direction.** $1+d/(p\tau)$ has an explicit
constant; $d/(p\log(1/p))$ comes from an $\Omega(\cdot)$ whose constant is unspecified
(RIP constants for Gaussian measurement matrices are conventionally quoted in the range
$2$–$10$). The ratio at the *worst in-range point* ($\tau=10$, $p=10^{-3}$) is $0.691$ —
only $1.45\times$ of margin. **Any recovery constant $\ge 1.45$ flips the verdict at that
point**, and constants of that size are entirely ordinary. This is exactly
`.claude/rules/calibration-residuals.md` check 1 and check 4: an attribution stated without
the closure margin, comparing two quantities on different bases (exact vs asymptotic)
without reconciliation.

**Correction.** "…so the interference bound is the tighter of the two **to within the
unspecified constant in the recovery bound; at $\tau=10$ the two are within $1.45\times$
at $p=10^{-3}$ and a factor $\ge 1.45$ in that constant would reverse the ordering.**"
The paragraph's closing sentence ("they answer different questions") already points the
right way — it just needs the margin.

---

### OVERSTATEMENT-2 (med-high) — "Negative interference is free … costs nothing at all", stated unconditionally and contradicted by the section's own last paragraph

**Target (line 125):** "A feature direction that projects *negatively* onto another
therefore costs nothing at all — not 'little', exactly nothing."

**Derivation.** True, and exactly true, under **four** conditions, of which the target
states one:

1. **Exactly one feature active.** With $\ge 2$ active the pre-activation at $j$ is
   $\sum_{k\in\text{act}}c_{jk}x_k+b_j$; a positive $c_{jk}$ from a second active feature
   lifts a negative $c_{ji}$ out of the dead zone and the freeness is destroyed. The
   one-active regime dominates only when $\binom{n}{2}p^2\ll np$, i.e. $p\ll 2/n$.
2. **$b_j\le 0$.** The target's *condition* line is right ($c_{ji}x_i+b_j\le0$) but the
   *inference* drawn from it ("projects negatively $\Rightarrow$ costs nothing") needs
   $b_j\le0$, which is only introduced in the **next** numbered fact. The logical order is
   inverted.
3. **Non-negative activations** ($x_i\sim U[0,1]$).
4. Free at $j$; no effect on $x'_i$ either way.

**The section already refutes its own unqualified phrasing.** Line 130: "the controlling
quantity is the expected number of simultaneously active features $np$, not $p$ alone. At
the source's own experimental scale ($n=400$ with $p$ as large as $0.3$) that expectation
is well above one, so the one-active-feature term is the illustrative case, not the
operative one." At $np=120$, condition 1 fails by two orders of magnitude — so "costs
nothing at all" is asserted in the regime the section itself calls non-operative.

**Correction.** Scope fact 1 in place: "*Conditioned on exactly one active feature and with
$b_j\le0$*, negative interference costs exactly nothing — the ReLU is in its dead zone, so
both the loss **and its gradient** vanish there, which is what makes such configurations
stable rather than merely cheap. With two or more features simultaneously active the
cancellation is only partial; see the $np$ caveat below." (The gradient point is worth
adding — it is the actual reason the mechanism is load-bearing and the target does not make it.)

---

### UNSTATED-1 (med) — Equation (8) is missing the $P(\text{only } i \text{ active})$ weight

**Target (Equation (8), line 118–121)** presents $\mathcal{L}_1$ as the one-active-feature
term of the loss, as a bare $\sum_i\int_0^1(\cdots)dx_i$.

**Derivation.** Equation (1) defines
$\mathcal{L}=\mathbb{E}_{\mathbf{x}}\sum_i I_i(x_i-x'_i)^2$ — an expectation. Decomposing
by activation count, $\mathcal{L}=\sum_k \mathcal{L}_k$ requires

$$\mathcal{L}_1 = \sum_i \Pr(\text{only } i \text{ active})\left[\int_0^1 I_i(\cdots)^2 dx_i + \sum_{j\ne i}\int_0^1 I_j\,\mathrm{ReLU}(\cdots)^2 dx_i\right],$$

with $\Pr(\text{only } i\text{ active}) = p_i\prod_{k\ne i}(1-p_k)$. As printed,
$\mathcal{L}_1$ is not a term of $\mathcal{L}$; it is the conditional expectation, unnormalized.
Both bracketed terms carry the same weight so neither qualitative conclusion changes, but
the equation is not equal to the quantity it names.

**Related inconsistency:** line 116 writes $\mathcal{L}=\sum_{\mathbf{x}}\sum_i$ (a sum
over $\mathbf{x}$) where Equation (1) writes $\mathbb{E}_{\mathbf{x}}\sum_i$. The missing
weight lives in exactly that slot.

---

### UNSTATED-2 (med) — Equation (7) presumes a decoder the toy model does not have; and "if and only if" is not well-formed

**Target (line 100):** "The compressed-sensing result is that an $n$-dimensional $k$-sparse
vector is recoverable from an $m$-dimensional projection **if and only if**
$m=\Omega(k\log(n/k))$."

Two problems.

**(a) The biconditional.** $\Omega(\cdot)$ is a one-sided asymptotic class; "recoverable
iff $m=\Omega(\cdot)$" is not a well-formed statement. Necessity holds for uniform recovery
of all $k$-sparse vectors; sufficiency holds **given hypotheses** — the measurement matrix
satisfies RIP (or is drawn from a suitable random ensemble) and the decoder is $\ell_1$ /
a comparable nonlinear reconstruction. Neither hypothesis appears.

**(b) The material one: the model's decoder is not that decoder.** The toy model's read-out
is $\mathrm{ReLU}(W^\top h + b)$ — **one linear probe plus a pointwise nonlinearity**, not
an $\ell_1$ solver. Equation (7) is therefore an *information-theoretic feasibility ceiling
under a strictly stronger decoder than the architecture has*. This does not weaken §B.6's
conclusion — it strengthens it (the achievable count is $\le$ Equation (7)) — but it is the
mechanism by which Equation (7) is an upper bound, and naming it is what makes the section's
"linear, not exponential" verdict safe. §B.5's closing line ("they do not say a decoder can
recover the coefficients") gestures at this without stating that the *bound itself* assumes
one.

Similarly, RIP is a hypothesis on $W$; nothing establishes that a trained $W$ satisfies it.

---

### UNSTATED-3 (med) — log base never declared, and the quoted multipliers silently set the $O(\cdot)$ constant to $1$

**Target (line 107):** "the multiplier $1/(p\log(1/p))$ is about $4.3$ at $p=0.1$, about
$21.7$ at $p=0.01$, and about $145$ at $p=0.001$."

**All three numbers are correct — in natural log** (reviewer: $4.3429$, $21.7147$,
$144.765$). But:

```
p       ln        log2      log10
0.1     4.3429    3.0103    10.0
0.01    21.7147   15.0515   50.0
0.001   144.765   100.343   333.3
```

`[opt:MATH-BASIS]` (`.claude/rules/workflow.md`) requires a quantity measurable on two
bases to declare which at the point of use. Equation (7) writes a bare $\log$. The *bound*
is base-independent (the base is absorbed into the $O(\cdot)$); the *quoted numbers* are
not, and differ by $1.44\times$ between $\ln$ and $\log_2$.

**The sharper point:** quoting "$4.3$" from an $O(\cdot)$ expression fixes **both** the log
base **and** the hidden constant to $1$. The honest form is "$4.3$ times an unspecified
$O(1)$ constant". This is the same defect as OVERSTATEMENT-1 and it is upstream of it —
these are the very numbers the binding comparison rests on.

---

### OVERSTATEMENT-3 (med) — "$N=\exp(\Theta(d\epsilon^2))$" claims an upper bound the appendix disclaims two paragraphs later

**Target (line 91):** "The result to carry forward is the **scaling**,
$N=\exp(\Theta(d\epsilon^{2}))$, not the constant in the exponent."

$\Theta$ asserts matching upper *and* lower bounds. The appendix derives only the lower
(existence) side and says so explicitly at line 93: "**What none of these bounds establish.**
They are *existence* results about geometry." No upper bound on the packing number appears
anywhere in §B.5, and none is cited. Writing $\Theta$ where only $\Omega$ is established is
an internal contradiction with the paragraph two below it.

**Correction.** $N=\exp(\Omega(d\epsilon^2))$. (Reviewer's note, flagged for
`citation-audit` rather than asserted: the matching upper bound for the almost-orthogonal
packing number is, to this reviewer's recollection, known only up to an additional
$\log(1/\epsilon)$ factor in the exponent — but that recollection is an unverified prior and
must be checked against a source before it is written into the survey. The
internal-contradiction argument above needs no source and is sufficient on its own.)

---

### OVERSTATEMENT-4 (med-low) — "a random draw is valid with probability approaching one"

**Target (line 82):** "That is below one — so a valid configuration exists, and **in fact a
random draw is valid with probability approaching one** — as soon as $N<\exp(d\epsilon^2/4)$."

**Derivation.** The failure bound is $N^2e^{-d\epsilon^2/2} = \big(N/e^{d\epsilon^2/4}\big)^2$.
At $N=e^{d\epsilon^2/4}$ it equals **exactly $1$** — vacuous. For $N$ merely *less than*
the threshold it is $<1$ but can be $0.9999$. "Probability approaching one" requires a
margin: for $N\le\delta e^{d\epsilon^2/4}$ the success probability is $\ge 1-\delta^2$.

The sentence conflates the probabilistic method's "positive probability, hence existence"
with a with-high-probability statement — at the exact threshold where the two diverge.

**Correction.** "…a valid configuration exists as soon as $N<\exp(d\epsilon^2/4)$; and for
$N$ a fixed fraction $\delta$ of that threshold, a random draw succeeds with probability at
least $1-\delta^2$."

---

### UNSTATED-4 (low-med) — "half of the interference is not charged for" assumes a symmetry that training destroys

**Target (line 125):** "Half of the interference the geometry produces is simply not
charged for."

**Derivation.** For $c$ drawn from any **sign-symmetric** distribution,
$\mathbb{E}[\mathrm{ReLU}(c)^2]=\mathbb{E}[c^2\mathbf{1}\{c>0\}]=\tfrac12\mathbb{E}[c^2]$ —
so "half" is exactly right, **under sign symmetry**. Random directions on $S^{d-1}$ are
sign-symmetric; a **trained** $W$ is not, and §B.7's entire thesis is that training
deliberately breaks that symmetry by steering interference negative. So "half" describes
the model at initialization, and at the optimum the waived fraction should exceed one half
— the section quotes the number from the regime its own argument says the model leaves.

**Correction.** "For sign-symmetric (e.g. random) directions exactly half the mean-square
interference is waived — and a trained model does better than half, because arranging
negative projections is precisely what the free region rewards."

---

### UNSTATED-5 (low-med) — §B.5 counts a two-sided $\epsilon$; §B.7 shows only one side is charged

§B.5 counts directions with $\lvert\langle u,v\rangle\rvert\le\epsilon$ (two-sided — the
factor $2$ in Equation (5) and hence the $/4$ in Equation (6) both come from that). §B.7
then shows the ReLU model is charged **only for positive** interference. §B.2 even
anticipates this ("once the ReLU is restored, a one-sided squared-inner-product — see
§B.7") but the connection is never made back to §B.5.

Consequence: §B.5's counting criterion is **strictly stricter than what the mechanism
requires**, so Equation (6) understates the model-relevant capacity. Under a one-sided
criterion the tail bound loses its factor $2$ and the constraint set is far weaker. This is
a free strengthening of the appendix's own argument, currently left on the table. (Also a
small fidelity point: the source is quoted at line 71 as "$<\epsilon$ cosine similarity"
— signed — and the derivation silently substitutes the absolute value.)

---

### NITs

- **N1 — Equation (5) is unattributed and its looseness unquantified.** The result being
  invoked is Lévy concentration on the sphere applied to the $1$-Lipschitz map
  $u\mapsto\langle u,v\rangle$ (median $0$), or equivalently Ball's spherical-cap lemma.
  The textbook exponent constant is convention-dependent ($d$ vs $d-1$ vs $d-2$; $<2\%$
  apart at $d=768$). Verified the $d$-form is a valid upper bound at every
  $(d,\epsilon)$ tested, and quantified its slack: $7.8\times$ at $\epsilon=0.1$,
  $4.6\times$ at $\epsilon=0.05$ ($d=768$) — the sub-Gaussian form discards a
  $\Theta(1/(\epsilon\sqrt d))$ prefactor. Naming the theorem and quoting the slack costs
  one sentence and pre-empts the "is that constant right?" question.
- **N2 — "read that last number correctly" misses the decisive quantification.** The
  paragraph is right that the union bound is loose at $\epsilon=0.1$, but the knock-down
  argument is one line and absent: the $768$ **standard basis vectors** are exactly
  orthogonal, hence trivially $0.1$-almost-orthogonal, so the true count is $\ge 768$, not
  $\approx 7$ — a factor of $110$. And the crossover is exact: $e^{d\epsilon^2/4}>d$
  requires $\epsilon>2\sqrt{\ln d/d}=0.186$ at $d=768$, so **the formula is weaker than the
  trivial orthonormal bound for every $\epsilon<0.186$** (at $\epsilon=0.186$ it gives
  $767$). Quoting that threshold turns a qualitative "it is loose" into a checkable range
  of validity.
- **N3 — §B.4's "organized geometry can do better" is exactly quantifiable.** The Welch
  bound gives a tight frame average off-diagonal $\overline{c^2}=(m-d)/(d(m-1))$ versus
  $1/d$ for random directions — a factor $(m-d)/(m-1)$. At $d=768$: $0.232\times$ for
  $m=1000$, $0.847\times$ for $m=5000$, $0.992\times$ for $m=10^5$. So the $1/d$ closed
  form is a **conservative $m\gg d$ asymptote**, and the caveat can name the factor instead
  of gesturing.
- **N4 — §B.7 fact 2 gives the pointwise condition, not the checkable one.** "up to
  $(W_j\cdot W_i)x_i\le -b_j$" is a condition on $x_i$ as well as on $c_{ji}$. The clean
  form (worst case $x_i=1$) is: the interference is free over the **whole** range iff
  $c_{ji}\le -b_j$ — the free region widens from $\{c\le0\}$ to $\{c\le\lvert b_j\rvert\}$,
  by exactly $\lvert b_j\rvert$. Beyond it the residual has the closed form
  $\max(0,c+b)^3/(3c)$ (verified to $10^{-8}$ on 12 test pairs). Missing entirely is the
  **cost** of the bias: with $\lVert W_j\rVert=1$, $b_j=-\beta$ costs $j$'s own
  reconstruction $\beta^2(1-\tfrac{2}{3}\beta)$ (verified). Quadratic own-cost against
  cubic savings is why trained biases are *small* and negative — as written, "the learned
  bias is the width of the free region" invites the reader to think wider is always better.
- **N5 — line 109 never states the ratio's orientation.** "Their ratio is $\log(1/p)/\tau$"
  — of interference-capacity to recovery-capacity. In the one paragraph flagged as
  inversion-prone, naming the numerator is cheap insurance.
- **N6 — §B.4's closed form omits the hypothesis that actually kills the cross terms.**
  The caveat says "assumes *random* directions", which is right, but not *why* it is
  needed: the cross terms $\sum_{j\ne k}\mathbb{E}[f_jf_k]\mathbb{E}[c_{ij}c_{ik}]$ vanish
  because $\mathbb{E}[c_{ij}c_{ik}]=0$ over random directions, **not** because the
  activations are uncorrelated — in this model $f_j\ge0$, so
  $\mathbb{E}[f_jf_k]=p^2\bar f^2>0$. A reader who assumes feature independence does the
  job will mis-transport the formula to a fixed frame, where
  $\sum_{j\ne k}c_{ij}c_{ik}=(\sum_{j\ne i}c_{ij})^2-\sum_{j\ne i}c_{ij}^2\ne0$ in general.
  Related and also unstated: the $s$-cancellation in §B.4 §3 holds because signal is defined
  **conditional on the feature being active**; on the unconditional basis $\mathbb{E}[f_i^2]=ps$,
  it is $p$ that cancels and $m_{\max}=1+d/\tau$ — a $p$-independent capacity. §B.4's
  configuration block does declare $s$ as "typical squared magnitude of an *active* feature",
  so the basis is declared; the *dependence of the cancellation on that choice* is not.

---

### Items outside this reviewer's scope

- The multi-dimensional refinement attributed to reference [5] (line 91) — the
  $\tfrac{1}{d_{\max}}e^{C_1(d/d'^2)\delta^2}$ subspace-packing statement, and the
  $\delta\cdot d_{\max}<1$ hypothesis the appendix flags — was not verified against the
  source. **One internal consistency check does pass:** at $d'=1$ (one-dimensional
  subspaces = directions) the exponent reduces to $C_1 d\delta^2$, matching Equation (6)'s
  form. Route to `citation-audit`.
- The claim that the source's experimental scale is "$n=400$ with $p$ as large as $0.3$"
  (line 130) is a citation claim, not re-derived here. The arithmetic drawn from it
  ($np\gg1$) is correct given those values: $np=120$.

---

### Verification log for the two highest-severity findings

**ERROR-1 (metric invariance).** Random PD $M$ at $d=40$, $N=60$ Euclidean unit vectors,
$\Phi=M^{-1/2}$:

```
max |<u,v> - <Phi u, Phi v>_M| = 1.554e-15
max |1 - ||Phi u||_M^2|        = 1.554e-15
```

$\Phi$ is an exact isometry to machine precision, so the packing number is identical in
both metrics and Equation (6) transports verbatim. §B.8's claim about §B.5/§B.6 is false
as stated.

**ERROR-3 (factor of $3$, and $b_j$).** $\int_0^1(cx+b)^2dx$ by quadrature versus
$c^2/3+cb+b^2$ versus the published $c^2$:

```
b= 0.0  c=+0.4 : integral 0.053333  formula 0.053333  published c^2 = 0.160000
b= 0.0  c=-0.4 : integral 0.053333  formula 0.053333  published c^2 = 0.160000
b=-0.2  c=+0.4 : integral 0.013333  formula 0.013333  published c^2 = 0.160000
b=-0.2  c=-0.4 : integral 0.173333  formula 0.173333  published c^2 = 0.160000
argmin_c f  at b=-0.2 : +0.3000  (predicted -3b/2 = +0.3000)
```

Published value is $3\times$ the correct one at $b=0$; at $b=-0.2$ the cost is minimized at
$c=+0.30$, not $c=0$, confirming that the "charges in both signs" symmetry is the $b_j=0$
special case.

<!-- LOG-END -->

