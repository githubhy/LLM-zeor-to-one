# Independent re-derivation — `appendix-d-sae-derivations.md`

Protocol: `[opt:MATH-REDERIVE]` (`.claude/rules/workflow.md`). Phase 1 below was
written **before** the target file was opened. Reviewer: adversarial, read-only.

Setting as briefed: activation `x` in `R^n`, model `x ~= D f`, `D` is `n x M` with
unit-norm columns, `M >> n`, `f` in `R^M`, `f >= 0`.

---

## Phase 0 — a structural objection recorded before any derivation

The brief (and, presumably, the target) asks for the closed form "assume the
dictionary columns are mutually orthonormal, `D^T D = I`". Record this **before**
doing the algebra, because it conditions every result below:

```
D is n x M.  D^T D is M x M.  rank(D^T D) = rank(D) <= min(n, M) = n.
I_M has rank M.
So  D^T D = I_M  ==>  M <= n.
```

**`D^T D = I_M` is logically incompatible with the overcompleteness `M >> n` that
defines a sparse autoencoder.** An overcomplete dictionary cannot have mutually
orthonormal columns; at `M > n` the Gram matrix is singular by construction.

So every "exact closed form" below is exact only on a set of hypotheses that the
SAE regime violates. The honest readings available are:

- (R1) `M <= n` and `D` orthonormal — mathematically clean, but not an SAE;
- (R2) exact on a *support*: `D_S^T D_S = I_{|S|}` with `|S| <= n`, plus a
  separate argument that the selection step decouples (it does not, in general);
- (R3) approximate, controlled by mutual coherence
  `mu = max_{i != j} |d_i^T d_j|`; the closed form is the `mu -> 0` limit.

I will flag anywhere the target asserts (R1)-grade exactness while living in the
`M >> n` regime. This is the single most likely OVERSTATEMENT in the appendix, and
it is invisible to any value-checking oracle.

---

## D1 — exact inference solution for a fixed dictionary

### Statement of the problem

```
f* = argmin_{f >= 0}  J(f),     J(f) = ||x - D f||_2^2 + lambda ||f||_1
```

with `lambda > 0`. Write the pre-activation (matched-filter / correlation) vector

```
a = D^T x        (a_i = d_i^T x)
```

### Step 1 — expand, and identify the discarded constant

```
||x - D f||_2^2 = (x - Df)^T (x - Df)
                = x^T x  -  2 x^T D f  +  f^T (D^T D) f
                = ||x||_2^2  -  2 a^T f  +  f^T (D^T D) f
```

Only here does orthonormality enter. **With `D^T D = I`** the quadratic form
collapses to `f^T f = sum_i f_i^2`, and the coupling between coordinates
disappears:

```
J(f) = ||x||_2^2  +  sum_i [ f_i^2 - 2 a_i f_i + lambda f_i ]
```

**The discarded constant is `||x||_2^2`** — it does not depend on `f`, so it does
not move the argmin. (Equivalent bookkeeping: complete the square,
`J = ||x||^2 - ||a||^2 + sum_i [(f_i - a_i)^2 + lambda f_i]`; in the `M <= n`
orthonormal reading `||x||^2 - ||a||^2 = ||x - P x||^2` with `P = D D^T` the
orthogonal projector onto `span(D)`, i.e. the part of `x` no dictionary can
reach. Under this bookkeeping the discarded constant is the out-of-span residual
energy.)

**This separation is the whole load-bearing step.** Without `D^T D = I` the cross
terms `f_i (d_i^T d_j) f_j` survive and the problem is a coupled non-negative
lasso with no closed form (solved by ISTA/FISTA/coordinate descent).

### Step 2 — the scalar problem, and the shrinkage constant

Per coordinate, minimize over `t >= 0`:

```
g(t) = t^2 - 2 a t + lambda t          (convention A: no 1/2 on the squared error)
g'(t) = 2t - 2a + lambda
```

Unconstrained stationary point `t = a - lambda/2`. So:

```
CONVENTION A   J = ||x - Df||^2       + lambda ||f||_1   ==>  f_i* = ReLU(a_i - lambda/2)
CONVENTION B   J = (1/2)||x - Df||^2  + lambda ||f||_1   ==>  f_i* = ReLU(a_i - lambda)
```

Convention B check: `g(t) = (1/2)t^2 - a t + lambda t`, `g'(t) = t - a + lambda`,
so `t = a - lambda`. Confirmed.

**Both are correct; they are different problems.** The factor of 2 is not a
cosmetic normalization — it is the ratio between the two answers. The SAE
literature convention (Anthropic's `Towards Monosemanticity`, and the
sparse-coding tradition it inherits from) writes the loss with **no** `1/2`:
`L = ||x - x_hat||_2^2 + lambda * sum_i f_i ||d_i||_2`. Under that convention
**the threshold is `lambda/2`, not `lambda`.** A target that writes
`||x - Df||^2 + lambda||f||_1` and then reports `ReLU(a - lambda)` is off by a
factor of two.

### Step 3 — the boundary case, done properly (KKT)

`g` is a strictly convex quadratic (`g'' = 2 > 0`) on the convex feasible set
`[0, inf)`, so a KKT point is the unique global minimizer. Lagrangian with
multiplier `mu >= 0` for the constraint `-t <= 0`:

```
L(t, mu) = t^2 - 2 a t + lambda t - mu t

stationarity:            2t - 2a + lambda - mu = 0
primal feasibility:      t >= 0
dual feasibility:        mu >= 0
complementary slackness: mu * t = 0
```

Two exhaustive cases:

```
(i)  t > 0  ==> mu = 0     ==> t = a - lambda/2,  feasible iff a > lambda/2
(ii) t = 0  ==> mu = lambda - 2a >= 0  <==>  a <= lambda/2
```

The cases are exhaustive and their feasibility conditions partition the real line
at `a = lambda/2` (both give `t = 0` there, so the solution is continuous — no
jump). Hence

```
f_i* = max(0, a_i - lambda/2) = ReLU(d_i^T x - lambda/2)
```

Independent cross-check without KKT: `g'(0+) = lambda - 2a`. If `a <= lambda/2`
then `g'(0+) >= 0`, and since `g'` is increasing (convexity) `g` is
non-decreasing on all of `[0, inf)`, so the minimum over the feasible set is at
the left endpoint `t = 0`. Same answer. Good.

**Result D1.** `f* = ReLU(D^T x - (lambda/2) 1)` under convention A;
`ReLU(D^T x - lambda 1)` under convention B.

**Hypotheses D1 needs:** (h1) `D^T D = I_M` — which forces `M <= n` and is
therefore *false* for an overcomplete SAE; (h2) `lambda > 0`; (h3) the dictionary
is **fixed** (this is inference, not learning); (h4) no pre-encoder bias / the
data already centred, i.e. the model is `x ~= Df` and not `x ~= Df + b_dec`.
Under (h1) failing, the correct general statement is that the *proximal-gradient
(ISTA) step* from `f = 0` is
`ReLU((1/L) D^T x - lambda/(2L))` — an affine map followed by ReLU — and the true
optimum is its fixed point after infinitely many such steps, not one.

---

## D2 — is the ReLU encoder "the exact functional form of the constrained optimum"?

### The identification

A real SAE encoder is `f = ReLU(W_enc x + b_enc)` with `W_enc` (`M x n`) and
`b_enc` (`M`) **learned**. My D1 optimum is `ReLU(D^T x - (lambda/2) 1)`. The two
coincide **identically in `x`** iff

```
W_enc = D^T                      (weight tying: encoder rows ARE decoder columns)
b_enc = -(lambda/2) * 1          (a single SHARED, strictly NEGATIVE bias)
```

An affine map is determined by its linear part and its offset, so this
identification is not merely sufficient — it is necessary for pointwise equality
on an `x`-set spanning `R^n`. That makes the list of assumptions exhaustive and
checkable:

1. **`D^T D = I_M`.** Already shown impossible for `M > n` (Phase 0). Without it
   the exact optimum is not an affine-then-ReLU map at all, so no choice of
   `(W_enc, b_enc)` recovers it.
2. **Weight tying `W_enc = D^T`.** Modern SAEs untie encoder and decoder. Tying
   is a *choice*, and one the field largely abandoned; the untied encoder is
   generally not `D^T` even up to scaling (decoder columns are norm-constrained,
   encoder rows are not).
3. **A uniform bias.** `b_enc = -(lambda/2) 1` is one shared scalar threshold.
   Real SAEs learn a per-latent bias vector `b_enc in R^M`. A per-latent
   `b_i = -lambda_i/2` corresponds to a **weighted** L1 penalty
   `sum_i lambda_i f_i`, not the stated `lambda ||f||_1`. So even the tied,
   orthonormal SAE solves a different program than the one written.
4. **The bias must be non-positive.** Shrinkage can only subtract. A learned
   `b_enc` is free to be positive, and empirically often is; a positive entry has
   no preimage in the `lambda > 0` family and is outside the derivation entirely.
5. **No pre-encoder bias.** Real SAEs compute `ReLU(W_enc (x - b_dec) + b_enc)`.
   That is the optimum for `x - b_dec ~= Df`, a different model than `x ~= Df`.
6. **Amortization.** Even granting 1-5, the learned encoder is trained by SGD to
   minimize an *expected* loss, not to solve the per-`x` program exactly. The
   residual is the amortization gap (the LISTA framing: a one-layer network is a
   learned, truncated, unrolled ISTA — one step, not convergence).

### Verdict

**OVERSTATED.** The defensible claim is:

> The ReLU-with-negative-bias *functional form* is exactly the form of the exact
> non-negative-lasso solution in the orthonormal, tied-weight, uniform-threshold
> special case — and, in general, is exactly one proximal-gradient (ISTA) step
> from `f = 0`. This motivates the architecture; it does not force it.

The claim "**the ReLU encoder is not a design choice, it is the KKT optimum**" is
wrong as stated, for a reason that is decisive and easy to check: **if the
architecture were forced by the KKT conditions, then Gated SAEs, JumpReLU, TopK
and BatchTopK could not exist** — yet they are the same inference problem solved
with different nonlinearities, and they beat plain ReLU on the reconstruction /
sparsity frontier. A form that admits strictly better alternatives on the same
objective is by definition a design choice. The correct move is to keep the
derivation (it is a genuinely good motivation) and downgrade the modal verb:
"has the form of", not "is".

**Hypotheses D2 needs:** all of D1's, plus tying, plus a uniform non-positive
bias, plus no pre-encoder bias, plus exact (non-amortized) inference.

---

## D3 — TopK exactness

### The problem

```
minimize  ||x - D f||_2^2      subject to   ||f||_0 <= k,   f >= 0
```

still under `D^T D = I`, and with `a = D^T x` as before.

### Derivation

Complete the square as in D1 Step 1:

```
||x - Df||^2 = ||x||^2 - 2 a^T f + ||f||^2
             = ||x||^2 - ||a||^2 + sum_i (f_i - a_i)^2
```

Let `S = supp(f)`, `|S| <= k`. For `i not in S`, `f_i = 0` contributes `a_i^2`.
For `i in S`, minimize `(t - a_i)^2` over `t >= 0`:

```
a_i >  0  ==>  t = a_i,   contributes 0
a_i <= 0  ==>  t = 0,     contributes a_i^2   (the constraint BINDS)
```

Substituting, and noting `min_{t>=0}(t - a_i)^2 = a_i^2 - ReLU(a_i)^2`:

```
||x - Df||^2 = ||x||^2 - ||a||^2 + sum_{all i} a_i^2 - sum_{i in S} ReLU(a_i)^2
             = ||x||^2 - sum_{i in S} ReLU(a_i)^2
```

The `f`-dependence is now entirely in the last term, so the optimal support is

```
S* = argmax_{|S| <= k}  sum_{i in S} ReLU(a_i)^2
```

i.e. **the `k` coordinates with the largest `ReLU(a_i)^2`**, and the optimal
values are `f_i = ReLU(a_i)` on `S*`, `0` elsewhere. Since `t -> t^2` is
increasing on `[0, inf)`, "largest `ReLU(a_i)^2`" = "largest `ReLU(a_i)`".

### The three sharp answers the brief asks for

**Which `k`?** The `k` largest **signed** pre-activations `a_i`, **not** the `k`
largest `|a_i|`. This is the direct consequence of `f >= 0`.

**Does non-negativity change the answer? YES, and materially.** Drop `f >= 0` and
the same algebra gives `||x - Df||^2 = ||x||^2 - sum_{i in S} a_i^2`, so the
selection becomes the `k` largest `|a_i|` with values `f_i = a_i`. With `f >= 0`,
a strongly negative `a_i` — the most informative coordinate in the unsigned sense
— is **worthless**: including it contributes exactly `0` reduction, the same as
leaving it out. Consequences worth stating:

- If fewer than `k` coordinates have `a_i > 0`, the **effective `L0` is strictly
  less than `k`**, and the optimal support is non-unique (any padding with
  non-positive coordinates is equally optimal). The constraint is `<= k`, never
  `= k`.
- Ties at the `k`-th largest value make `S*` non-unique.

**No shrinkage.** The optimal values are `ReLU(a_i)`, *not* `ReLU(a_i - c)` for
any `c > 0`. This is exactly why TopK is proposed as a fix for the L1 shrinkage
bias of D6 — the hard `L0` constraint has no shrinkage term because the
constraint contributes no `f`-linear term to the objective.

### Does it survive without orthonormality? NO.

Drop `D^T D = I` and:

- the cross terms `f_i (d_i^T d_j) f_j` return, so the objective no longer
  decomposes over coordinates and the support cannot be chosen by ranking a
  per-coordinate score;
- **best-subset selection over a general dictionary is NP-hard**
  (Natarajan 1995; Davis-Mallat-Avellaneda 1997), so no polynomial rule —
  certainly not a sort — is the exact minimizer in general;
- even with the support handed to you for free, the optimal coefficients are the
  non-negative least squares solution on `D_S`, i.e. the projection of
  `(D_S^T D_S)^{-1} D_S^T x` onto the non-negative orthant — **not** `a_S`. They
  coincide only when `D_S^T D_S = I`.

What survives without orthonormality is a *guarantee*, not an identity: under a
mutual-coherence condition (`mu (2k-1) < 1`-type, Tropp / Donoho-Elad) plus a
dynamic-range condition on the nonzeros, thresholding recovers the correct
support. That is a recovery theorem with hypotheses, not "the exact minimizer".

**Hypotheses the "TopK is the exact minimizer" claim needs:**
(h1) `D^T D = I_M`, hence `M <= n` — again false in the SAE regime;
(h2) the objective is pure reconstruction, with the sparsity imposed as a hard
constraint, not a penalty;
(h3) `f >= 0`, which changes the rule from top-`k`-by-magnitude to
top-`k`-by-signed-value;
(h4) ties broken arbitrarily (minimizer non-unique on ties, and whenever fewer
than `k` pre-activations are positive);
(h5) selection performed on `D^T x` itself. Real TopK SAEs select on
`W_enc x + b_enc` with `W_enc` untied, so all of D2's amortization caveats ride
along.

Under (h1) the honest statement is: TopK is the exact minimizer **for an
orthonormal dictionary**, and is otherwise the first step of Matching Pursuit
(a.k.a. hard thresholding) — a greedy heuristic with coherence-conditional
guarantees.

---

## D4 — the scale degeneracy

### The orbit

Fix an index `i` and a scalar `c > 0`. Reparametrize

```
d_i -> c d_i        f_i -> f_i / c        (all other d_j, f_j unchanged)
```

### (a) Reconstruction — exactly invariant

```
D f = sum_j f_j d_j
    = (f_i / c)(c d_i) + sum_{j != i} f_j d_j
    = f_i d_i         + sum_{j != i} f_j d_j
    = D f     (unchanged)
```

So `||x - Df||_2^2` is **exactly** invariant, for every `c > 0` and every `x`.
Not approximately — the map is an exact symmetry of the reconstruction term.
(It is the standard scaling symmetry of any bilinear factorization.)

### (b) Penalty — strictly decreasing in `c`

```
||f||_1 = sum_j f_j     ->     (f_i / c) + sum_{j != i} f_j
```

Exact change:

```
Delta(||f||_1)      = f_i / c - f_i = f_i (1/c - 1) = - f_i (c - 1) / c
Delta(penalty term) = lambda f_i (1/c - 1)
```

### DIRECTION — derived, not assumed

`f_i >= 0` and `lambda > 0`, so the sign of `Delta` is the sign of `(1/c - 1)`:

```
c > 1  (column INFLATED)  ==>  1/c < 1  ==>  Delta < 0  ==>  PENALTY FALLS
c < 1  (column shrunk)    ==>  1/c > 1  ==>  Delta > 0  ==>  PENALTY RISES
```

**Inflating a decoder column lowers the L1 penalty.** The intuition: the penalty
is levied on the *coefficient*, and a longer basis vector needs a smaller
coefficient to do the same job. The magnitude of the reduction is
`lambda f_i (1 - 1/c)`, which increases monotonically in `c` to the finite limit
`lambda f_i`. I derived this direction before reading the target; it is the
direction the brief says the target claims, so on this point I expect agreement —
recording it explicitly so the agreement is evidence, not assumption.

### Unbounded below, or merely improvable? — the careful answer

Along the orbit,

```
J(c) = ||x - Df||^2 + lambda [ f_i / c + sum_{j != i} f_j ]
```

which is **strictly decreasing in `c`**, with

```
inf_{c > 0} J(c) = ||x - Df||^2 + lambda sum_{j != i} f_j     (as c -> infinity)
```

and the infimum is **not attained** at any finite `c` (`f_i/c > 0` for all finite
`c` whenever `f_i > 0`). Applying the orbit to every column simultaneously drives
the whole penalty to zero, so

```
inf over all orbits  =  ||x - Df||^2   >=  0
```

**Therefore: the objective is NOT unbounded below.** It is bounded below by `0`
(both terms are non-negative), and along the orbit it is bounded below by the
unpenalized reconstruction error. The pathology is different and more precise:

> The penalized problem **has no minimizer** — the infimum is approached only as
> `||d_i|| -> infinity`, `f_i -> 0`. The minimizing sequence escapes to infinity
> in parameter space. The L1 term can be made arbitrarily small at zero
> reconstruction cost, so it is **vacuous as a sparsity penalty** unless the
> column norms are pinned.

Saying "unbounded below" would be a real error, not a nit: it names the wrong
pathology (divergence of the objective value vs. non-existence of a minimizer /
non-coercivity of the parametrization) and would imply the reconstruction term
could be driven negative, which it cannot.

Note also what is *not* constraining `c`: nothing in the objective. The unit-norm
condition `||d_i||_2 = 1` stated in the setup is an **externally imposed
constraint**, and this derivation is exactly the reason it must be imposed. Under
`||d_i|| = 1` the orbit leaves the feasible set at any `c != 1`, and the
degeneracy is gone.

### The two standard fixes, and why they work

- **Norm constraint** `||d_i||_2 = 1`, re-projected after each step. Note the
  subtlety: projecting after a gradient step is *not* the same as constrained
  optimization — the gradient component parallel to `d_i` must also be removed,
  or the optimizer fights the projection.
- **Norm-aware penalty** `lambda sum_i f_i ||d_i||_2`. This is **exactly
  invariant** on the orbit: `f_i ||d_i|| -> (f_i/c)(c ||d_i||) = f_i ||d_i||`.
  This is the cleaner fix, and it makes the degeneracy disappear rather than
  merely forbidding it.

**Hypotheses D4 needs:** only `c > 0`, `f_i >= 0`, `lambda > 0`. Notably it does
**not** need orthonormality — this is the one result in the set that holds for a
general overcomplete dictionary, and it should be marked as such.

---

## D5 — dead latents and whether "death is absorbing"

### Which gradients vanish

Let latent `i` be **inactive on the whole data distribution**: `f_i(x) = 0` for
(almost) every `x` in `supp(P_x)`. Write the plain loss
`L = E_x[ ||x - D f(x)||^2 + lambda ||f(x)||_1 ]`, encoder
`f = ReLU(z)`, `z = W_enc x + b_enc`.

**Decoder column.** `x_hat = sum_j f_j d_j`, so

```
dL/dd_i = E_x[ -2 (x - x_hat) * f_i ]  =  0     since f_i == 0
```

The decoder column is multiplied by `f_i` in the forward pass, so a zero
coefficient zeroes its gradient exactly.

**Encoder row and bias.** By the chain rule through the ReLU,

```
df_i/dz_i = 1[z_i > 0]  =  0        (inactive means z_i <= 0)
dL/dw_i   = E_x[ (dL/df_i) * 1[z_i > 0] * x ]     = 0
dL/db_i   = E_x[ (dL/df_i) * 1[z_i > 0] ]         = 0
```

So **both** the encoder row and the decoder column receive exactly zero gradient.
Every parameter private to latent `i` is frozen. That is the absorbing argument,
and as far as it goes it is correct — and the brief's worry ("does the gradient
w.r.t. the ENCODER parameters really vanish, given the encoder is learned and not
literally `D^T`?") resolves **in favour of the claim**: the vanishing comes from
the ReLU derivative, not from any tie between `W_enc` and `D`. Untying does not
open a gradient path. Good.

### Is "absorbing" exactly true? — true modulo FIVE things

The claim is exactly true **for the parameters private to latent `i`, under the
plain loss, holding the input distribution and all shared parameters fixed.**
Each of those qualifiers is a real escape hatch:

1. **Shared parameters — the genuine revival path.** Real SAEs compute
   `z = W_enc (x - b_dec) + b_enc`. The pre-encoder bias `b_dec` is **shared**
   and receives gradient from every *live* latent. As `b_dec` moves,
   `z_i = w_i^T (x - b_dec) + b_i` moves **with `w_i` and `b_i` frozen**. So
   `z_i` can re-cross zero and the latent revives with no gradient of its own
   ever having been non-zero. Any shared preprocessing (input normalization,
   a shared scale) does the same. This is the one caveat I would insist a survey
   state, because it contradicts a literal reading of "absorbing".
2. **Input-distribution shift.** "Dead" is defined relative to `P_x`. Changing
   the activation-collection mixture, the layer, or the base model can revive a
   latent. In a training run with a streaming/shuffled activation buffer, `P_x`
   over a *batch* is not `P_x` over the corpus — a latent inactive on the current
   batch is not dead, and its gradient is not zero in expectation. The absorbing
   claim needs "inactive on the support", not "inactive on this batch".
3. **Weight decay / parameter regularization.** If the loss carries an L2 term on
   the weights, `dL/dw_i = 2 gamma w_i != 0`. The gradient is then **not** exactly
   zero — it shrinks the dead latent further toward the origin. Directionally this
   reinforces death, but it falsifies a literal "exactly zero gradient" if the
   optimizer uses decoupled or coupled weight decay (AdamW in practice).
4. **Optimizer state.** Adam carries exponential moving averages. A parameter whose
   gradient hits zero keeps moving for `O(1/(1-beta_1))` steps as the momentum
   drains, and the `eps`-regularized second-moment denominator makes the effective
   step non-zero. Death is absorbing in the *gradient*, not instantly in the
   *iterate*.
5. **Engineered revival.** Neuron resampling (Bricken et al.), ghost grads
   (Anthropic), and the AuxK auxiliary loss (Gao et al.) all exist **precisely
   because** the plain gradient is zero — they inject an artificial gradient into
   dead latents. Their existence is the strongest evidence the derivation is
   right; but any claim of the form "a dead latent can never revive" is false in
   any real SAE training run, all of which use one of these.

**Verdict:** the zero-gradient derivation is **sound**. "Absorbing" is sound as a
statement about the *plain* objective's gradient with shared parameters held
fixed, and is an OVERSTATEMENT if written as an unconditional dynamical claim.
The correct framing: *under the plain loss, a dead latent's own gradient is
identically zero, so nothing in the objective can revive it — which is why
revival must be engineered externally.* That framing is both true and more
useful, since it explains the fixes.

**Hypotheses D5 needs:** (h1) `f_i = 0` on the whole support of `P_x`, not merely
on a batch; (h2) plain reconstruction + L1 loss, no weight decay; (h3) shared
parameters (`b_dec`, normalization) held fixed, or the claim scoped to the
latent's *private* parameters; (h4) the ReLU subgradient at `0` taken as `0` (a
convention — measure-zero, but it is the exact point at which a latent sits when
it is on the boundary); (h5) no resampling / ghost-grad / AuxK term.

---

## D6 — the squared reconstruction cost of shrinkage

### Setup

Let `S` be the active set, `n_active = |S|`. From D1 the L1 solution is
`f_i = a_i - s` for `i in S`, with the shrinkage constant

```
s = lambda / 2      (convention A)          s = lambda   (convention B)
```

Compare against the **unshrunk** least-squares coefficients on the same support,
`f_i^LS = a_i` (which are the exact optimum of the reconstruction term alone,
under orthonormality — cf. D3, where the hard-`L0` solution has no shrinkage).

### Derivation

```
x_hat_LS - x_hat = sum_{i in S} (a_i - (a_i - s)) d_i = s * sum_{i in S} d_i
```

so the squared error injected by shrinkage is

```
|| x_hat_LS - x_hat ||^2 = s^2 || sum_{i in S} d_i ||^2
                         = s^2 [ sum_{i in S} ||d_i||^2  +  sum_{i != j in S} d_i^T d_j ]
```

### The hypothesis that makes the per-feature errors ADD

The cross-term `sum_{i != j in S} d_i^T d_j` must vanish. That requires

```
d_i^T d_j = 0   for all  i != j  in S       i.e.   D_S^T D_S = I_{n_active}
```

**the active decoder columns must be mutually orthogonal** (unit norm alone is
not enough — unit norm handles `||d_i||^2 = 1`, orthogonality handles the cross
terms). Only then:

```
|| x_hat_LS - x_hat ||^2 = s^2 * n_active
```

### Result

```
CONVENTION A:   shrinkage cost = n_active * lambda^2 / 4
CONVENTION B:   shrinkage cost = n_active * lambda^2
```

and, since the shrinkage error lies in `span(D_S)` while the residual
`x - P_S x` is orthogonal to it, the total decomposes by Pythagoras:

```
||x - x_hat||^2 = ||x - P_S x||^2  +  n_active * lambda^2 / 4
                  \-- support error --/   \-- shrinkage error --/
```

**Scaling: linear in `n_active`, quadratic in `lambda`.** Two properties worth
stating because they are the whole argument for TopK / Gated / JumpReLU SAEs:

- The cost is **independent of the `a_i`** — the bias is a constant offset per
  active feature, so it is proportionally most damaging for weakly-activating
  features and for low-norm activations `x`.
- It is **irreducible within the L1 formulation**: lowering `lambda` to reduce it
  raises `n_active`, which is the reconstruction/sparsity frontier. Removing the
  shrinkage requires changing the *program* (hard `L0`, or a decoupled
  gate/magnitude path), not tuning `lambda`.

If the active columns are only *near*-orthogonal with mutual coherence
`mu = max_{i != j in S} |d_i^T d_j|`, the cross term is bounded by
`n_active (n_active - 1) mu`, giving

```
s^2 n_active [ 1 - (n_active - 1) mu ]  <=  cost  <=  s^2 n_active [ 1 + (n_active - 1) mu ]
```

so the clean `n_active * lambda^2 / 4` is a first-order result whose error term
grows **quadratically** in `n_active`. In an overcomplete SAE `mu > 0` strictly
(Welch bound), so this is the operative regime, not the exact one.

**Hypotheses D6 needs:** (h1) `D_S^T D_S = I` on the active support — the
additivity hypothesis; (h2) the support is held fixed between the two solutions
(in truth shrinkage also *changes* which coordinates survive the threshold, so
this is a same-support comparison, not a full comparison of the two programs);
(h3) all `n_active` features are shrunk by the *same* constant, i.e. a single
shared `lambda` (a per-latent `lambda_i` gives `sum_i lambda_i^2 / 4`);
(h4) the convention for the `1/2` must match D1's, or the answer is off by `4x`.

---

## Phase 1 summary — my results, before reading the target

| # | Result I derived | Key hypothesis it needs |
|---|---|---|
| D1 | `f* = ReLU(D^T x - lambda/2)` with **no** `1/2` on the squared error; `ReLU(D^T x - lambda)` **with** it | `D^T D = I_M`, hence `M <= n` — false for an SAE |
| D2 | ReLU encoder has the *form* of the optimum under tying + uniform non-positive bias; it is one ISTA step, not the KKT optimum | tying, uniform bias, orthonormality, no amortization gap |
| D3 | top-`k` by **signed** `a_i` (not `abs`), values `ReLU(a_i)`, **no shrinkage**; effective `L0 < k` possible | `D^T D = I`; NP-hard without it |
| D4 | reconstruction exactly invariant; penalty **falls** by `lambda f_i (1 - 1/c)` when `c > 1`; objective **bounded below**, infimum **not attained** | none beyond `c > 0`, `f_i >= 0` |
| D5 | encoder row, encoder bias and decoder column all take exactly zero gradient; absorbing modulo shared `b_dec`, distribution shift, weight decay, momentum, resampling | inactive on the whole support, plain loss |
| D6 | `n_active * lambda^2 / 4` (convention A) | `D_S^T D_S = I` on the active support |

Phase 1 complete. Opening the target now.

---

# Phase 2 — comparison against the target

Target: `surveys/mechanistic-interpretability/appendix-d-sae-derivations.md`
(138 lines, six tagged equations, sections D through D.8).

## Headline

**Zero ERROR-class findings. The mathematics is correct throughout.**

Every numerical result I derived independently agrees with the target exactly:
the shrinkage constant, the convention it belongs to, the scale-degeneracy
direction *and* its exact magnitude, and the shrinkage-cost formula. The four
places the brief flagged as most likely to hide a load-bearing error are three
clean and one overstated. What the appendix owes is **hypotheses and modal
verbs**, not corrections.

I record the clean verdicts explicitly, because a re-derivation that only lists
complaints has thrown away half its evidentiary value.

### Clean verdicts (checked adversarially, found correct)

| Watchpoint | My independent result | Target | Verdict |
|---|---|---|---|
| Shrinkage constant | `lambda/2` under a no-`1/2` objective | `lambda/2`, from a no-`1/2` objective | **CORRECT** |
| Convention consistency | Eq (2) -> Eq (4) -> figure must agree | all three agree | **CORRECT** |
| Scale-degeneracy direction | penalty **falls** for `c > 1` | penalty falls | **CORRECT** |
| Scale-degeneracy magnitude | falls by `f_i (1 - 1/c)` | `f_i(1 - 1/c)` | **CORRECT, exact** |
| Shrinkage cost | `n_active * (lambda/2)^2` | `n_active(lambda/2)^2` | **CORRECT** |
| Coordinate separation | needs `D^T D = I`; const is `||x||^2 - ||a||^2` | separation correct | **CORRECT** |
| Overcompleteness objection | `D^T D = I` forces `M <= n`, contradicting the SAE regime | **stated prominently**, D.1 para 9 | **CORRECT, and pre-empted** |

The last row deserves emphasis. My Phase-0 objection — written before opening the
file, and the thing I most expected to find buried — is stated by the target
itself, unprompted, in its own voice, as *"the honest caveat, stated here rather
than buried"*. That is the correct call and it is correctly placed. It is also
what makes findings 2 and 4 below fair game: the appendix knows the hypothesis
matters, so the places it *omits* it are omissions, not innocence.

### Two arithmetic checks worth recording

The factor-of-two chain, verified end to end (this was the brief's top concern):

```
Eq (2):  ||x - Df||^2 + lambda ||f||_1        <- NO 1/2 on the squared error
Eq (3):  derivative  2(f_i - a_i) + lambda = 0
Eq (4):  f_i = ReLU(a_i - lambda/2)           <- consistent with the no-1/2 form
F-D1:    lambda = 0.6  =>  shrinkage 0.3      <- consistent (0.6/2)
F-D1(b): n_active (lambda/2)^2                <- consistent
```

All four agree. Had Eq (2) carried a `1/2`, Eq (4) would need `lambda`; it does
not, and it does not claim to. **No off-by-two anywhere.**

The scale-degeneracy sign, verified independently before reading:

```
Mine:   Delta(||f||_1) = f_i(1/c - 1) = -f_i(1 - 1/c)   =>  falls by f_i(1 - 1/c)
Target: "||f||_1 falls by f_i(1 - 1/c)"
```

Identical. The brief instructed me not to accept the target's direction — I
derived it independently and it is right.

---

## Findings, ranked by severity

### 1. OVERSTATEMENT (moderate-high) — "the ReLU encoder is not a design choice"

Target, D.1 bullet 1:

```
**The ReLU encoder is not a design choice.** It is the exact functional form of
the constrained optimum — the KKT condition for f_i >= 0 — which is why the
earliest sparse autoencoders used it and why it works at all.
```

**What I derived (D2).** The exact optimum is `ReLU(D^T x - (lambda/2) 1)`. A
real encoder is `ReLU(W_enc x + b_enc)`. These are the same function **iff**
`W_enc = D^T` and `b_enc = -(lambda/2) 1` — necessary as well as sufficient, since
an affine map is pinned by its linear part and offset. That identification is
four separate assumptions, none of which holds in a modern SAE: weight tying
(abandoned), a single shared threshold (real SAEs learn a per-latent bias vector,
which is a *weighted* L1 penalty, not the `lambda ||f||_1` written in Eq (2)), a
non-positive bias (learned biases may be positive, which has no preimage in the
`lambda > 0` family), and no pre-encoder bias (real SAEs use `x - b_dec`).

**The decisive objection is internal to the appendix.** If the ReLU form were
forced by the KKT conditions rather than chosen, then Gated, JumpReLU, TopK and
BatchTopK could not exist — yet D.2, the very next section, derives them as
better solutions to the same problem. A functional form that admits strictly
better alternatives on the same objective is a design choice by definition. The
appendix argues against its own bullet one section later.

**Mitigating.** D.1 para 4 does say the encoder *amortizes* the problem and
outputs "an approximate solution", and para 9 supplies the orthonormality caveat.
So the surrounding text is more careful than the bullet. The bullet is the part a
reader quotes.

**Correction.** Demote the modal verb and keep everything else:

```
The ReLU encoder is not an arbitrary choice: with tied weights and a single
shared threshold it has exactly the functional form of the constrained optimum,
and in general it is exactly one proximal-gradient (ISTA) step from f = 0. That
is why it was the natural starting point — not why it is the only option, as
D.2 shows.
```

### 2. UNSTATED HYPOTHESIS (moderate-high) — TopK "exact minimizer" carries no hypothesis

Target, D.2, TopK paragraph:

```
This is the exact minimizer of the reconstruction objective under a hard L_0 <= k
constraint rather than an L_1 relaxation
```

**What I derived (D3).** Under `D^T D = I` the objective collapses to
`||x||^2 - sum_{i in S} ReLU(a_i)^2`, so top-`k` selection is exactly optimal.
**Without orthonormality the claim is false, and not marginally so:** best-subset
selection over a general dictionary is NP-hard (Natarajan 1995;
Davis-Mallat-Avellaneda 1997), so no sort can be the exact minimizer. Worse, even
*given* the optimal support, the optimal coefficients are the non-negative least
squares solution on `D_S`, not the pre-activations `a_S`; they coincide only when
`D_S^T D_S = I`.

**Why this is the most load-bearing finding.** The orthonormality caveat in D.1
para 9 is scoped, in its own words, to *"Equation (4)"*. The TopK exactness claim
is a **separate** claim, made two sections later, stated flatly, with no
hypothesis attached and no back-reference to the caveat. A reader who accepted
the D.1 caveat as discharged for D.1 has no signal that D.2's stronger claim
inherits the same fatal hypothesis. This is exactly the shape that survives a
casual read: correct under a hypothesis stated elsewhere for a different result.

D.2's closing paragraph does say *"None of them removes the underlying difficulty,
which is that the dictionary is overcomplete and the coordinate problems are
coupled"* — a gesture in the right direction, but it is a remark about *cost*,
not a retraction of *exactness*, and it does not name TopK.

**Correction.** One clause: `"...is the exact minimizer of the reconstruction
objective under a hard L_0 <= k constraint — under the same orthonormal-dictionary
assumption as Equation (4); with a general overcomplete dictionary, subset
selection is NP-hard and TopK is the hard-thresholding heuristic for it."`

### 3. UNSTATED HYPOTHESIS (moderate) — the encoder identification is never written down

Distinct from finding 1, which is about the modal verb; this is about a missing
algebraic step. The appendix moves from `f* = ReLU(D^T x - lambda/2)` (Eq 4) to
talking about "the ReLU encoder" without ever writing `f = ReLU(W_enc x + b_enc)`
or stating the correspondence `W_enc = D^T`, `b_enc = -(lambda/2) 1`.

That correspondence is where every one of finding 1's assumptions lives, and it is
also the sentence that makes the appendix's central move legible: **the learned
bias plays the role of the sparsity coefficient.** That is a genuinely
illuminating identity (it is why `b_enc` wants to be negative, and why a
per-latent bias is a per-latent `lambda`), and the appendix currently gets no
credit for it because it is left implicit.

**Correction.** Add one line after Eq (4) giving the correspondence explicitly,
with the four assumptions named. This simultaneously fixes finding 1 and turns an
omission into the appendix's best paragraph.

### 4. UNSTATED HYPOTHESIS (low-moderate) — F-D1 panel (b) additivity

Target, D.8 section 2 and section 4:

```
(b) The reconstruction error contributed by shrinkage alone, n_active (lambda/2)^2.
...
The clean separation in (a) holds exactly only for an orthonormal dictionary
```

**What I derived (D6).** The shrinkage error is
`s^2 || sum_{i in S} d_i ||^2 = s^2 [ n_active + sum_{i != j in S} d_i^T d_j ]`.
Collapsing to `n_active * s^2` requires the cross terms to vanish, i.e.
**`D_S^T D_S = I` on the active support** — mutual orthogonality of the *active*
decoder columns. Unit norm alone is not enough: unit norm kills `||d_i||^2 = 1`,
orthogonality kills the cross terms, and those are two different assumptions.

The caveat as written is explicitly scoped to panel **(a)** ("The clean separation
in (a)"). Panel (b) needs its own, arguably stronger, hypothesis, and the error
term is not benign: with coherence `mu` the bound is
`s^2 n_active [1 +/- (n_active - 1) mu]`, so the correction grows **quadratically**
in `n_active` while the stated quantity grows only linearly. At realistic
`n_active` and the `mu > 0` forced by the Welch bound in an overcomplete
dictionary, that is the operative regime, not a fussy edge case.

**Correction.** Change "in (a)" to "in (a), and the additivity in (b)", and add
that (b) needs the active columns mutually orthogonal, not merely unit-norm.

### 5. UNSTATED HYPOTHESIS (low-moderate) — the zero-gradient argument is run on the wrong encoder

Target, D.5:

```
The mechanism is straightforward from Equation (4): a feature whose projection
a_i sits below lambda/2 on every input receives f_i = 0 always, hence **zero
gradient**, hence no way to recover. Death is absorbing.
```

**What I derived (D5).** The conclusion is **right**, and I want to be clear that
I attacked it and it held: the brief asked whether the gradient really vanishes
for a *learned* encoder that is not literally `D^T`, and the answer is yes — but
for a reason the target does not give. Eq (4) is the exact-inference solution in
terms of `D^T x`; the appendix derives death "from Equation (4)", i.e. from the
tied, idealized encoder. The claim that actually matters concerns
`f_i = ReLU(w_i^T x + b_i)`, and it holds because

```
df_i/dz_i = 1[z_i > 0] = 0   =>   dL/dw_i = 0,  dL/db_i = 0
dL/dd_i   = E[-2(x - x_hat) f_i] = 0            (decoder column, since f_i == 0)
```

The vanishing comes from the **ReLU derivative**, not from any tie between
`W_enc` and `D`. So untying does not open a gradient path — the argument is
robust, but the appendix's stated route to it (via Eq (4)) is not the route that
carries the weight.

**Second gap: one genuine revival path is unmentioned.** Real SAEs compute
`z = W_enc(x - b_dec) + b_enc`, and `b_dec` is **shared** and receives gradient
from every *live* latent. So `z_i` can move — and re-cross zero — with `w_i` and
`b_i` frozen at zero gradient forever. "No way to recover" is therefore true of
the latent's *private* parameters and false as an unconditional dynamical claim.
Two lesser caveats: weight decay makes the gradient not *exactly* zero (AdamW in
practice), and Adam momentum keeps the iterate moving after the gradient hits
zero.

**Credit where due.** The target correctly scopes death to "on every input" — the
whole data distribution, not a batch. That is precisely the right hypothesis (my
D5 h1), and it is the one an inattentive author gets wrong. And D.5 para 2's
auxiliary-loss remedy is consistent: the plain objective cannot revive a latent,
so the fix changes the objective. Internally coherent.

**Correction.** Two clauses: derive the zero gradient from the ReLU derivative on
the learned encoder rather than from Eq (4), and note that a shared pre-encoder
bias is the one path by which a dead latent can revive without ever receiving a
gradient of its own.

### 6. OVERSTATEMENT (low) — "raising lambda costs reconstruction quadratically"

Target, D.8 section 3:

```
In (b), buying sparsity by raising lambda costs reconstruction *quadratically*
```

The quantity plotted is `n_active (lambda/2)^2`, which is quadratic in `lambda`
**at fixed `n_active`**. But raising `lambda` buys sparsity *precisely by
reducing* `n_active` — that is the mechanism — and the product
`n_active(lambda) * lambda^2 / 4` therefore has two competing factors. The
sentence names `lambda` as the free variable while silently holding fixed the very
quantity `lambda` controls.

The total error also has a second term I derived in D6 that the sentence ignores:
`||x - x_hat||^2 = ||x - P_S x||^2 + n_active * lambda^2 / 4`, and raising
`lambda` *raises* the first term (a smaller support explains less). So "costs
reconstruction quadratically" is not the net statement.

**Correction.** "at a given `n_active`, the shrinkage contribution grows
quadratically in `lambda`".

### 7. OVERSTATEMENT (low) — "k is directly interpretable as the sparsity"

Target, D.2: `"k is directly interpretable as the sparsity rather than being an
opaque trade parameter."`

From D3: the constraint is `||f||_0 <= k`, and under `f >= 0` a coordinate with
`a_i <= 0` contributes exactly zero reduction — so if fewer than `k`
pre-activations are positive, the effective `L0` is strictly **less** than `k` and
the optimal support is non-unique. `k` is an **upper bound** on the achieved
sparsity, not the achieved sparsity. (In deployed TopK SAEs, which select top-`k`
then apply ReLU, this is the operative behaviour, not a corner case.) The
contrast with `lambda` is still fair and worth keeping — `k` is a far more legible
knob — but "directly is" should be "directly bounds".

Related and unstated: the non-negativity constraint is what makes the rule
"top-`k` by **signed** pre-activation" rather than "top-`k` by `|a_i|`". The target
says "the k largest pre-activations", which is correct as written; it is worth one
half-sentence saying *why* it is not magnitude, since that is a real consequence
of `f >= 0` and the only place in the appendix where non-negativity does visible
work.

### 8. NIT — notation collision: `n` means two different things

D.1: `x in R^n` with `M >> n` dictionary directions, so `n` is the **activation
dimension** and `M` the dictionary size.

D.3: `"a published joint scaling law relating loss to dictionary size n and
sparsity k"` — here `n` is the **dictionary size**, i.e. D.1's `M`.

Same appendix, opposite meanings, and the reader has no warning. This is worth
fixing precisely because the appendix is otherwise scrupulous about notation — it
carries an explicit warning two sentences later that the scaling law's `gamma`
collides with the Gated literature's `gamma`. The `n` collision is the more
confusing of the two and is unflagged. Rename D.3's to `M` (or flag it in the same
parenthetical that already handles `gamma`).

### 9. NIT — Eq (3)'s `const` is never identified

The brief asked what the discarded constant is; the target writes `+ const`.
It is `||x||^2 - ||a||^2`, which in the `M <= n` orthonormal reading is exactly
`||x - Px||^2` with `P = D D^T` — the energy of `x` that **no** dictionary code
can reach. Naming it is one clause and it is genuinely informative: it separates
"error because the dictionary cannot span this" from "error because the code was
shrunk", which is the same decomposition D.8 panel (b) relies on. Also, `const` is
written inside the per-coordinate `min`, where it is global rather than
per-coordinate; harmless, but the placement is loose.

### 10. NIT — "impossible when `M >> n`"

D.1 para 9. Orthonormal columns are impossible when `M > n` (the Gram matrix is
rank-deficient the moment `M` exceeds `n`). `M >> n` is the regime under
discussion, so nothing is wrong, but the sharp statement is stronger and free.

### 11. NIT — "the KKT condition for `f_i >= 0`"

ReLU is the *solution obtained from* the KKT system, not itself a KKT condition.
Also mildly inconsistent with the argument actually given two lines earlier, which
is the convexity/projection one ("convex parabola ... the constrained minimum sits
on the boundary") — a perfectly valid argument, and arguably the better one to
name. Either say "the KKT solution" or point at the convexity argument.

### 12. NIT — D.4's pathology is non-attainment, not divergence

Target: `"the objective can be driven down without changing a single
reconstruction ... a free lunch"`.

This is accurate and the target does **not** claim the objective is unbounded
below — I checked specifically, because that is the tempting wrong statement. For
completeness, the precise fact from my D4: the objective is bounded below by `0`,
and along the orbit by the unpenalized reconstruction error; what fails is
*attainment* — the infimum is approached only as `||d_i|| -> infinity`,
`f_i -> 0`, so the penalized problem has **no minimizer**. "Free lunch" is a fair
gloss; adding "the infimum is never attained — the minimizing sequence escapes to
infinity" would make it exact at no cost.

---

## Out of scope for this pass (stated so the clean verdict is not over-read)

This was a mathematical re-derivation of the six tagged equations and their
surrounding claims. I did **not** verify, and my clean verdict does **not** cover:

- the JumpReLU straight-through-estimator attributions in D.2 (the KDE
  equivalence, the `H(0) := 1/2` convention, the `E[x^2] = 1` kernel
  normalization) — these are source claims requiring `citation-audit`;
- the joint scaling law's functional form and the `gamma` collision claim in D.3;
- the Gated/JumpReLU equivalence hypotheses in D.2 (single feature, no decoder
  bias, non-negative threshold) — though I note the appendix states these
  hypotheses explicitly and attaches them to the claim, which is exactly the
  discipline finding 2 says is missing for TopK. The author clearly knows how to
  do this; TopK is an inconsistency, not a blind spot;
- whether `figures/appendix-d-sae-shrinkage.py` computes what F-D1's caption says.

## Summary

```
ERROR                 : 0
UNSTATED HYPOTHESIS   : 3   (findings 2, 3, 4, 5 -- 4 items, 3 distinct classes)
OVERSTATEMENT         : 3   (findings 1, 6, 7)
NIT                   : 5   (findings 8-12)
```

Restated exactly: **0 ERROR, 4 UNSTATED HYPOTHESIS (2, 3, 4, 5), 3 OVERSTATEMENT
(1, 6, 7), 5 NIT (8-12).**

Only two findings are worth blocking on: **finding 1** (the "not a design choice"
bullet, which the appendix's own next section refutes) and **finding 2** (TopK
exactness with no orthonormality hypothesis, where the appendix states the
hypothesis for a weaker claim two sections earlier and drops it for the stronger
one). Both are one-clause fixes. Everything else is polish.

The appendix's core arithmetic is correct, its convention is consistent end to
end, and its central honesty move — stating the overcompleteness obstruction in
its own voice rather than burying it — is the right call, correctly placed.

