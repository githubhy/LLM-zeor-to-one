# Independent re-derivation — Appendix C (causal mediation for LM interventions)

`[opt:MATH-REDERIVE]` adversarial review. **Phase 1 was derived with the target file
unopened**; Phase 2 is the comparison. Reviewer: independent, read-only.

Arithmetic verified with `python3` (transcript in the session log; every number below is
machine-checked, not hand-computed).

---

## Phase 1 — derivation from first principles (target NOT yet read)

### C1 — the three effect "scales"

Baseline response $y_0>0$, intervened response $y_1>0$. Three reporting conventions:

$$
P \;=\; \frac{y_1}{y_0}-1, \qquad
D \;=\; y_1-y_0, \qquad
L \;=\; \log y_1-\log y_0 .
$$

#### (a) exact log ↔ proportional relation

$$
L=\log\frac{y_1}{y_0}=\log(1+P)
\qquad\Longleftrightarrow\qquad
P=e^{L}-1 .
$$

Exact, no approximation, valid on the whole admissible domain $P\in(-1,\infty)$,
$L\in(-\infty,\infty)$. The small-effect expansion is
$L=P-\tfrac{P^2}{2}+\tfrac{P^3}{3}-\cdots$, so $L\approx P$ only to first order and the
second-order defect $P^2/2$ is **not** negligible at the magnitudes this appendix works
at ($P\sim 10^2$). At $P=130.9$, $L=4.88$ — the two numbers are not interchangeable in
any practical sense.

#### (b) "additivity on the log scale is multiplicativity on the raw scale"

**True as stated about ratios; loose as stated about "the raw scale".** Proof. For two
interventions with log effects $L_1,L_2$ and joint log effect $L_{12}$,

$$
L_{12}=L_1+L_2
\;\Longleftrightarrow\;
\log\frac{y_{12}}{y_0}=\log\frac{y_1}{y_0}+\log\frac{y_2}{y_0}
\;\Longleftrightarrow\;
\frac{y_{12}}{y_0}=\frac{y_1}{y_0}\cdot\frac{y_2}{y_0}.
$$

So what multiplies is the **fold-change** $y/y_0$, equivalently $(1+P)$ — *not* the raw
response. Explicitly $y_{12}=y_1y_2/y_0$, and $y_{12}\neq y_1y_2$ unless $y_0=1$. The
normalisation is load-bearing: "multiplicative on the raw scale" is only correct if "raw
scale" means the ratio-to-baseline, and it is wrong if it means $y$ itself. A precise
phrasing is *additive in log-fold-change = multiplicative in fold-change*.

#### (c) is log a third **distinct** scale? — NO, not informationally

$L=\log(1+P)$ is a **strictly monotone $C^\infty$ bijection** $(-1,\infty)\to\mathbb R$
that **does not depend on $y_0$**. Therefore:

* **Pointwise, for a single effect, $L$ and $P$ carry exactly the same information.** Each
  is recoverable from the other with no extra data. $L$ is a reparametrisation of $P$,
  not a new measurement.
* $D$ *is* informationally distinct in the relevant sense: $D=y_0P$, so converting
  between $D$ and $P$ requires the baseline $y_0$. The map $P\mapsto L$ is **universal**
  (one fixed function, identical for every model); the map $P\mapsto D$ is
  **baseline-dependent** (a different function per model). That is exactly why $P$ and
  $L$ are commensurable across the five models of C3 and $D$ is not.

So there are **two informationally distinct scales**, $\{P\cong L\}$ and $\{D\}$, in three
reporting conventions.

**The one precise caveat that rescues "three scales" partially.** Informational
equivalence is *pointwise*. Additivity is **not** preserved by a nonlinear monotone
reparametrisation: a set of effects that is additive in $L$ is generally not additive in
$P$, and vice versa. So as *measures of a single effect* $L$ and $P$ are the same thing;
as *combination rules across several effects* they induce genuinely different nulls (this
is the entire content of C3). The defensible statement is therefore:

> Two informationally distinct effect measures ($P\cong L$ vs $D$), but three distinct
> **additive structures** — $D$-additivity, $P$-additivity, and $L$-additivity
> (= $P$-multiplicativity) are three different hypotheses about how effects compose.

Calling them flatly "three scales" without that distinction invites the reader to think
the log scale contains information $P$ lacks. It does not.

#### (d) $y$ already a ratio of probabilities

Let $y=p(a)/p(b)$ (a likelihood/odds ratio — the standard MI response, e.g.
$p(\text{he})/p(\text{she})$). Then

$$
P=\frac{y_1}{y_0}-1
=\frac{p_1(a)/p_1(b)}{p_0(a)/p_0(b)}-1 .
$$

**Confirmed: a ratio of ratios, minus one.** Correspondingly $L$ is a *difference of
log-ratios*, i.e. a difference-in-differences of log-probabilities — the log-odds-ratio
analogue. Two consequences worth stating at point of use: (i) $P$ is then a
dimensionless second-order contrast, and calling it a "percentage change" is misleading
because the underlying object is already a contrast; (ii) $y\in(0,\infty)$ is unbounded
above even though $p\in[0,1]$, so there is no ceiling on $P$ — which matters for whether
the large values in C3 are saturating.

---

### C2 — the decomposition condition

Write the response as a function of treatment $x\in\{\text{null},\text{set}\}$ and
mediator $z$, with the four evaluable cells

$$
y_{\text{null}}=y(\text{null},z_{\text{null}}),\quad
y_{\text{set}}=y(\text{set},z_{\text{set}}),\quad
y_{\text{set},z_{\text{null}}}=y(\text{set},z_{\text{null}}),\quad
y_{\text{null},z_{\text{set}}}=y(\text{null},z_{\text{set}}).
$$

#### Derivation of the residual

$$
\begin{aligned}
D_{TE}-D_{NDE}-D_{NIE}
&=(y_{\text{set}}-y_{\text{null}}) -
(y_{\text{set},z_{\text{null}}}-y_{\text{null}}) -
(y_{\text{null},z_{\text{set}}}-y_{\text{null}})\\[2pt]
&=y_{\text{set}}-y_{\text{null}}-y_{\text{set},z_{\text{null}}}+y_{\text{null}} -
y_{\text{null},z_{\text{set}}}+y_{\text{null}}\\[2pt]
&=y_{\text{set}}-y_{\text{set},z_{\text{null}}}-y_{\text{null},z_{\text{set}}}+y_{\text{null}}.
\end{aligned}
$$

The two $-y_{\text{null}}$ terms cancel one $+y_{\text{null}}$ each, leaving exactly one
$+y_{\text{null}}$. The residual is the **2×2 interaction contrast** (second difference),
and it factors two equivalent ways:

$$
R=\underbrace{\big[y_{\text{set}}-y_{\text{set},z_{\text{null}}}\big]}_{\text{mediator effect with }x\text{ ON}} -
\underbrace{\big[y_{\text{null},z_{\text{set}}}-y_{\text{null}}\big]}_{\text{mediator effect with }x\text{ OFF}}
=\underbrace{\big[y_{\text{set}}-y_{\text{null},z_{\text{set}}}\big]}_{\text{treatment effect at }z_{\text{set}}} -
\underbrace{\big[y_{\text{set},z_{\text{null}}}-y_{\text{null}}\big]}_{\text{treatment effect at }z_{\text{null}}} .
$$

#### The iff

The decomposition holds exactly when the residual vanishes:

$$
D_{TE}=D_{NDE}+D_{NIE}
\iff R=0
\iff \big(y_{\text{set}}-y_{\text{set},z_{\text{null}}}\big)=\big(y_{\text{null},z_{\text{set}}}-y_{\text{null}}\big).
$$

**This is a genuine iff, not an implication.** The chain is pure algebra (an identity)
followed by "expression $=0$", with no side conditions, no positivity, no regularity, and
no distributional assumption. Both directions hold trivially. The only thing to check is
that all four cells are *defined* — which they are by construction here (see below).

#### Classification: NO-INTERACTION, not no-confounding

The condition equates *the effect of moving the mediator when the treatment is on* with
*the effect of moving the mediator when the treatment is off*. That is precisely absence
of treatment×mediator **effect modification** on the difference scale — i.e. the response
surface $f(x,z)$ is **additively separable**, $f(x,z)=g(x)+h(z)+c$. It is a statement
about the *functional form of the network's computation*, and it is empirically testable
by running the fourth cell.

**Why no-mediator–outcome confounding is NOT the relevant assumption here.** Confounding
assumptions in the mediation literature (VanderWeele's A1–A4: no unmeasured
exposure–outcome, mediator–outcome, or exposure–mediator confounding, and no
mediator–outcome confounder itself affected by the exposure) exist for exactly one
purpose: to license **identification** — to let a *cross-world* counterfactual such as
$Y(1,M(0))$, which is never jointly observed in any single world, be written in terms of
quantities estimable from observational data. Every element of that problem is absent in
a deterministic network with directly-settable mediators:

1. The network is a **deterministic function** of its inputs and its activations, so a
   counterfactual is a *function evaluation*, not an estimand.
2. Every mediator is **directly settable** by fiat (activation patching / ablation), so
   all four cells of the 2×2 are obtained by *running the model*, not by inference from a
   population. There is no sampling, hence nothing for a common cause to bias.
3. The cross-world quantity $y(\text{set},z_{\text{null}})$ — the one that makes classical
   mediation hard — is here **literally computable**: force $x$ to `set` and simultaneously
   overwrite $z$ with its baseline value. In Pearl's terms every nested counterfactual is
   point-identified with zero assumptions, because we operate in the $\mathrm{do}$-calculus's
   fully-interventional regime rather than recovering it from observation.
4. Even a genuinely confounded upstream path is **irrelevant**, because overwriting $z$
   severs every incoming edge to $z$. Confounding of $z$ cannot bias a quantity in which
   $z$ is externally clamped.

Hence the *only* thing standing between $D_{TE}$ and $D_{NDE}+D_{NIE}$ is whether the
network's computation happens to be additively separable in $(x,z)$. Invoking
no-confounding here would be a category error: it would import an identification
assumption into a setting with no identification problem, and — worse — it would make the
decomposition failure look like an unavoidable epistemic limitation when it is in fact a
**measurable property of the model** that a fourth forward pass settles.

#### The fix that removes the assumption entirely (worth flagging)

The residual $R$ arises only because **both** reported effects are *pure* (each evaluated
with the *other* factor at its null level). Using the standard VanderWeele pairing — one
pure, one total — makes the decomposition an **exact identity requiring no assumption at
all**:

$$
\begin{aligned}
\text{PNDE}&=y_{\text{set},z_{\text{null}}}-y_{\text{null}} &
\text{TNIE}&=y_{\text{set}}-y_{\text{set},z_{\text{null}}} &
&\Rightarrow\; D_{TE}=\text{PNDE}+\text{TNIE}\quad(\text{always}),\\
\text{TNDE}&=y_{\text{set}}-y_{\text{null},z_{\text{set}}} &
\text{PNIE}&=y_{\text{null},z_{\text{set}}}-y_{\text{null}} &
&\Rightarrow\; D_{TE}=\text{TNDE}+\text{PNIE}\quad(\text{always}).
\end{aligned}
$$

Both telescope trivially. The appendix's $D_{NDE}$ is PNDE and its $D_{NIE}$ is PNIE — the
**pure/pure** pairing, the one combination that is *not* an identity. Equivalently, the
exact three-way decomposition is

$$
D_{TE}=\text{PNDE}+\text{PNIE}+R,
$$

with $R=\text{TNIE}-\text{PNIE}$ the **mediated interaction**. So the no-interaction
condition is not a defect of causal mediation analysis — it is an artefact of choosing the
pure/pure pairing, and it is optional.

---

### C3 — the independence null on a proportional scale

Setup: $n$ mediators, single-mediator fold-changes $y_i/y_0=1+e_i$ with $e_i>-1$;
simultaneous intervention under independence gives $y_{\text{all}}/y_0=\prod_i(1+e_i)$.

#### (a) concurrent proportional effect

$$
\mathrm{NIE_{all}}=\frac{y_{\text{all}}}{y_0}-1=\prod_{i=1}^{n}(1+e_i)-1 .
$$

#### (b) the exponential form, and what must actually be small

$$
\prod_i(1+e_i)=\exp\!\Big(\sum_i\log(1+e_i)\Big)
\;\Longrightarrow\;
\mathrm{NIE_{all}}=\exp\!\Big(\sum_i\log(1+e_i)\Big)-1 .
$$

So $\mathrm{NIE_{all}}\approx\exp(\sum_ie_i)-1$ demands
$\sum_i\log(1+e_i)\approx\sum_ie_i$, i.e.

$$
\Delta \;=\; \sum_i\big[e_i-\log(1+e_i)\big]\;\approx\;\tfrac12\sum_i e_i^2 \;\ll\;1 .
$$

**"Small individual effects" is NOT the right condition.** What must be small is the
**sum of squares** $\sum_ie_i^2$ (the squared $\ell_2$ norm), not $\max_i|e_i|$. With $n$
equal effects of size $e$ the requirement is $ne^2/2\ll1$, i.e. $e\ll\sqrt{2/n}$ — the
tolerance *shrinks* as $\sqrt{1/n}$. Machine-checked at $\sum e_i=6.8$: $n{=}20,e{=}0.34$
gives $\Delta=0.95$; $n{=}10,e{=}0.68$ gives $\Delta=1.61$; $n{=}5,e{=}1.36$ gives
$\Delta=2.51$. At the magnitudes in play $\Delta$ is $O(1)$–$O(10)$, so the
approximation is **not** in its valid regime.

**A stronger and more useful fact — the inequality is universal and one-signed.** Since
$\log(1+e)\le e$ for all $e>-1$ with equality only at $e=0$,

$$
\boxed{\;\prod_i(1+e_i)\;\le\;\exp\Big(\sum_i e_i\Big)\;}
\qquad\text{hence}\qquad
\mathrm{NIE_{all}}^{\text{indep}}\;\le\;\exp(\mathrm{NIE_{sum}})-1,
$$

strictly unless all $e_i=0$. No non-negativity is needed; it holds on the whole domain
$e_i>-1$. Verified numerically over 200 000 random draws ($n\le20$,
$e_i\in(-0.999,5)$): $\max\big[\prod(1+e_i)-\exp(\sum e_i)\big]=0$, attained only at the
degenerate point.

**Therefore $\exp(\mathrm{NIE_{sum}})-1$ is not "the multiplicative null" — it is a
universal UPPER BOUND on it**, and the limiting case $n\to\infty$ with equal infinitesimal
shares.

**Corollary (this is the load-bearing one): $\prod_i(1+e_i)$ is NOT a function of
$\sum_ie_i$.** Given only $\mathrm{NIE_{sum}}=S$ (and $e_i\ge0$), the independence
prediction ranges over the whole interval

$$
\mathrm{NIE_{all}}^{\text{indep}}\;\in\;\big[\,S,\;e^{S}-1\,\big),
$$

with the lower end at $n=1$ (all mass in one mediator) and the upper end as
$n\to\infty$ equally split. Machine-checked spread at $S=6.8$:

| $n$ | 1 | 2 | 5 | 10 | 50 | $\to\infty$ |
|---|---|---|---|---|---|---|
| $\prod(1+S/n)^n-1$ | 6.8 | 18.4 | 72.2 | 178.1 | 586.4 | 896.8 |

Two orders of magnitude, all with **exactly zero interaction**. A single number quoted as
"the multiplicative prediction" from $S$ alone is therefore **ill-posed** — it is a range,
and the range is enormous.

#### (c) the identity $\sum_i e_i=\mathrm{NIE_{sum}}$

By definition $\mathrm{NIE_{sum}}=\sum_i(y_i/y_0-1)=\sum_ie_i$. So the exponential form
is $\exp(\mathrm{NIE_{sum}})-1$ — correct as an *upper envelope*, with the caveats of (b).

#### (d) $\exp(\mathrm{NIE_{sum}})-1$, to 1 d.p.

| $\mathrm{NIE_{sum}}$ | 6.8 | 4.0 | 3.5 | 2.1 | 2.9 |
|---|---|---|---|---|---|
| $\exp(S)-1$ | **896.8** | **53.6** | **32.1** | **7.2** | **17.2** |

#### (e) prediction vs measurement

| model | $\mathrm{NIE_{sum}}$ | $\exp(S)-1$ | measured $\mathrm{NIE_{all}}$ | direction | factor |
|---|---|---|---|---|---|
| M1 | 6.8 | 896.8 | 130.9 | **OVER**-predicts | $\times 6.85$ |
| M2 | 4.0 | 53.6 | 112.3 | **UNDER**-predicts | $\times 2.10$ |
| M3 | 3.5 | 32.1 | 116.0 | **UNDER**-predicts | $\times 3.61$ |
| M4 | 2.1 | 7.2 | 96.9 | **UNDER**-predicts | $\times 13.52$ |
| M5 | 2.9 | 17.2 | 225.2 | **UNDER**-predicts | $\times 13.11$ |

One over-prediction, four under-predictions. (Factor = larger/smaller, so it reads as
"off by this multiple" in the stated direction.)

The **additive** null is $S$ itself and is below every measurement, by
$\times19.3,\;28.1,\;33.1,\;46.1,\;77.7$ respectively.

#### (f) VERDICT — is $\mathrm{NIE_{sum}}$ vs $\mathrm{NIE_{all}}$ informative about synergy?

**Largely NO as posed, and the "brackets from opposite sides" framing is false for 4 of
the 5 models.**

**1. The additive comparison is a scale artefact, not a synergy test.** Summing
*proportional* effects is not the prediction of any independence model. Under **exact**
multiplicative independence — zero interaction by construction —
$\sum_iP_i\neq\prod_i(1+P_i)-1$, and the gap is large. Machine-checked examples with
literally no synergy: $n{=}10,e{=}0.5\Rightarrow S{=}5.0,\ \mathrm{NIE_{all}}{=}56.7$
($\times11.3$); $n{=}12,e{=}0.5\Rightarrow S{=}6.0,\ \mathrm{NIE_{all}}{=}128.7$
($\times21.5$); $n{=}20,e{=}0.3\Rightarrow S{=}6.0,\ \mathrm{NIE_{all}}{=}189.0$
($\times31.5$). The measured excesses ($\times19$–$\times78$) sit squarely in the range a
**perfectly independent** system produces. So "$\mathrm{NIE_{all}}\gg\mathrm{NIE_{sum}}$"
is *expected under independence* and is **not** evidence of synergy. The additive null on
the proportional scale is a straw man: it is not the C2 no-interaction condition (which
lives on the **difference** scale), and it is not implied by any causal hypothesis.

**2. The multiplicative null quoted as a single number is ill-posed.** Per (b), from $S$
alone the independence prediction is the interval $[S,\,e^S-1)$, not a point. The correct
independence prediction is $\prod_i(1+e_i)-1$, which is computable from **exactly the same
per-mediator data that produced $\mathrm{NIE_{sum}}$** — the appendix already has the
$e_i$, since it summed them. Quoting $\exp(\mathrm{NIE_{sum}})-1$ discards information
already in hand in exchange for a loose upper bound.

**3. "Brackets from opposite sides" — checked against all five, it fails 4/5.**

| model | additive $S$ | measured | $e^S-1$ | measured inside $[S,\,e^S-1)$? |
|---|---|---|---|---|
| M1 | 6.8 | 130.9 | 896.8 | **YES** — genuinely bracketed |
| M2 | 4.0 | 112.3 | 53.6 | NO — both nulls below |
| M3 | 3.5 | 116.0 | 32.1 | NO — both nulls below |
| M4 | 2.1 | 96.9 | 7.2 | NO — both nulls below |
| M5 | 2.9 | 225.2 | 17.2 | NO — both nulls below |

Bracketing holds for **exactly one of five**. For the other four **both** nulls lie below
the measurement; the multiplicative one merely undershoots by less. Stating bracketing as
a property of the result set is an overstatement of a 1/5 case. It is also
`.claude/rules/calibration-residuals.md`-forbidden phrasing ("brackets the reference"):
the honest form names the signed factor per model, which the table above does.

**4. The correctly-posed version of the test — and it inverts the reading.** Because
$e^S-1$ is a *universal upper bound* on any multiplicative-independent arrangement, a
measurement **exceeding** it cannot be produced by *any* independent configuration of
mediators summing to $S$. That is a clean, assumption-light refutation:

* **M2, M3, M4, M5 exceed the bound** ⇒ multiplicative independence is **refuted**;
  these four exhibit genuine **super-multiplicative synergy**. This is a strictly stronger
  claim than the appendix's, and it does not depend on knowing $n$ or the individual $e_i$.
* **M1 does not exceed the bound** ($130.9<896.8$) and lies inside $[6.8,\,896.8)$ ⇒
  **fully consistent with pure multiplicative independence**; synergy is **not**
  established for M1, and with $n\approx10$ equal shares the independence prediction
  ($178.1$) actually *exceeds* the measurement, hinting at mild **sub**-multiplicativity.

So the model the appendix presumably highlights as "the multiplicative null over-predicts
by about seven" is precisely the one where **no synergy is demonstrated**, and the four
where the null under-predicts are the ones where synergy **is** demonstrated. Any framing
that treats the over- and under-prediction cases symmetrically ("brackets") loses this
inference entirely.

**5. Residual caveats that must be stated with any of the above.**
   * Commensurability: the $e_i$ and $\mathrm{NIE_{all}}$ must share the same $y_0$, the
     same response definition, and the same $n$ (the mediator set summed must be the set
     jointly intervened). If $\mathrm{NIE_{sum}}$ sums over a different or larger set than
     $\mathrm{NIE_{all}}$ intervenes on, none of this is valid.
   * $n$ is never stated in the numbers given to me; without it the independence
     prediction cannot be pinned beyond the interval. **$n$ must be disclosed.**
   * No uncertainty accompanies any of the ten numbers. A factor-of-2.10 discrepancy (M2)
     is not distinguishable from noise without a CI; a factor of 13.5 probably is.
     Per `sim-report-completeness`, every cell needs an interval.

---

## Phase 2 — comparison against the target

Target: `surveys/mechanistic-interpretability/appendix-c-causal-interventions.md`,
sections C.5–C.8, equations 5/6/7. Model labels map as
M1 = distil, M2 = small, M3 = medium, M4 = large, M5 = xl.

### Verdict summary

**2 ERROR · 1 OVERSTATEMENT · 3 UNSTATED HYPOTHESIS · 4 NIT.**

The algebra of C.6 is exactly right and independently reproduced. The arithmetic of C.7
is exactly right — every quoted number checks out, including both "factor of about seven"
and "factor of about thirteen". The failures are **not** arithmetic: they are one false
empirical claim about the five-model data set, one over-corrected conclusion that discards
a result the data actually support, and a wrong validity condition on Equation (7).

### What checks out (verified, no action)

| Target claim | Check |
|---|---|
| Equation (6) RHS | expands to $y_{\text{set}}-y_{\text{set},z_{\text{null}}}-y_{\text{null},z_{\text{set}}}+y_{\text{null}}$ — **identical** to my independent derivation |
| "holds exactly when the two bracketed quantities are equal" | genuine iff; pure algebra, no side conditions — confirmed |
| "no mediator–outcome confounding … is the **wrong** condition here" | confirmed independently, and for the right reason (interventional regime, not identification) |
| ratios 19.2 / 28.1 / 33.1 / 46.1 / 77.7 | computed 19.25 / 28.07 / 33.14 / 46.14 / 77.66 — **all five match** |
| "predicts $896.8$ where $130.9$ was measured" | $e^{6.8}-1=896.847$ — correct |
| "over-predicts by a factor of about seven" (distil) | $896.8/130.9=6.85$ — correct |
| "predicts $7.2$ where $96.9$ was measured" | $e^{2.1}-1=7.166$ — correct |
| "under-predicts by a factor of about thirteen" (large) | $96.9/7.166=13.52$ — correct |
| "$y$ is itself already a ratio … ratio of ratios, minus one" | confirmed (my C1(d)) |
| worked example $13.1/0.14-1\approx 92.6$ | $93.571-1=92.571$ — correct |
| C.6 "divide through by $y_{\text{null}}(u)$ *per unit* before taking the expectation" | **correct and non-obvious**: $R(u)/y_{\text{null}}(u)=P_{TE}-P_{NDE}-P_{NIE}$ exactly, and the per-unit ordering matters because $\mathbb{E}[R/y_{\text{null}}]\neq\mathbb{E}[R]/\mathbb{E}[y_{\text{null}}]$. Credit. |
| C.4 forward-ref: independence gives **super**-additivity on the proportional scale | correct — $\prod(1+e_i)-1=\sum e_i+(\text{non-negative cross terms})$ |

C.1–C.4 were **not** audited (older context, and F-C1's numbers live in a generator +
JSON I did not open).

---

### Findings, ranked by severity

#### 1. ERROR — "bracket the measurement from opposite directions" is false for 4 of the 5 models

> **Target (C.7):** "The additive null and the multiplicative-independence null bracket the
> measurement from opposite directions, which means the gap between NIE-sum and NIE-all
> identifies neither interaction nor its absence"

**My derivation.** Bracketing requires
$\mathrm{NIE_{sum}}<\mathrm{NIE_{all}}<e^{\mathrm{NIE_{sum}}}-1$. Checked on all five:

| model | additive null | measured | multiplicative null | bracketed? |
|---|---|---|---|---|
| distil | 6.8 | 130.9 | 896.8 | **YES** |
| small | 4.0 | 112.3 | 53.6 | NO — both nulls below |
| medium | 3.5 | 116.0 | 32.1 | NO — both nulls below |
| large | 2.1 | 96.9 | 7.2 | NO — both nulls below |
| xl | 2.9 | 225.2 | 17.2 | NO — both nulls below |

Bracketing holds for **exactly one of five**. For the other four, *both* nulls lie below
the measurement; the multiplicative null merely undershoots by less than the additive one.
The target's own preceding sentence — "the null lands on both sides of the observation" —
is true (1 over, 4 under) and is quietly generalised one sentence later into a claim about
"the measurement", which is false for 80% of the cases.

This is **load-bearing**: bracketing is the stated premise for the conclusion that the
comparison "identifies neither interaction nor its absence".

**Correction.** Replace with the signed per-model factors (the table above), and note the
asymmetry explicitly: the multiplicative null over-predicts for distil alone and
under-predicts for the remaining four. Separately, "brackets" is a phrasing
`.claude/rules/calibration-residuals.md` forbids by name; the rule's honest form is the
per-case signed factor, which the table supplies.

#### 2. OVERSTATEMENT — "uninformative about synergy" over-corrects and discards a real result

> **Target (C.7):** "So the honest reading is that the reported comparison is uninformative
> about synergy."

**My derivation.** The conclusion is right about the *additive* comparison and wrong as a
blanket statement, because the multiplicative comparison is informative when read as the
**one-sided bound it actually is**. Since $\log(1+e)\le e$ for all $e>-1$,

$$
\prod_i(1+e_i)\;\le\;\exp\Big(\sum_i e_i\Big)
\qquad\Longrightarrow\qquad
\mathrm{NIE_{all}}^{\text{indep}}\;\le\;e^{\mathrm{NIE_{sum}}}-1 ,
$$

**universally** — no non-negativity needed, strict unless every $e_i=0$ (verified over
200 000 random draws with $n\le 20$ and $e_i\in(-0.999,5)$: max of
$\prod(1+e_i)-\exp(\sum e_i)$ is exactly $0$). A measurement **exceeding** that bound
therefore cannot be produced by *any* multiplicatively-independent arrangement of
mediators summing to $\mathrm{NIE_{sum}}$. Consequently:

* **small, medium, large, xl all exceed the bound** ⇒ multiplicative independence is
  **refuted**; these four show genuine **super-multiplicative synergy**. This holds without
  knowing $n$ or the individual $e_i$.
* **distil does not** ($130.9<896.8$, inside $[6.8,\,896.8)$) ⇒ **consistent with pure
  independence**; synergy is *not* established there. At $n\approx10$ equal shares the
  independence prediction is $178.1$, above the measurement — hinting at mild
  **sub**-multiplicativity.

So the reading **inverts the target's presentation**: distil, the model the target leads
with as the over-prediction, is precisely the one where no synergy is demonstrated, and
the four "under-predicted" models are where synergy *is* demonstrated. Treating over- and
under-prediction symmetrically ("brackets") is exactly what loses this inference.

**What the target gets right and should keep.** Its instinct that the *additive*
comparison is a scale artefact is correct, and I confirm it numerically: with **zero**
interaction, $n=12$ mediators at $e_i=0.5$ give $\mathrm{NIE_{sum}}=6.0$ and
$\mathrm{NIE_{all}}=128.7$ — a $21.5\times$ inflation from independence alone; $n=20$ at
$e_i=0.3$ gives $31.5\times$. The observed $19$–$78\times$ range sits squarely inside what
pure independence produces. The target asserts this ("the wrong aggregation for a
proportional scale") without demonstrating it; one line of arithmetic would make it
rigorous.

**Correction.** Split the verdict: *the additive comparison is uninformative (scale
artefact, demonstrated); the multiplicative comparison, read as a one-sided bound, refutes
independence for 4 of 5 models and fails to for distil.* That is both more honest and a
stronger result than the source's own prose.

#### 3. ERROR — Equation (7)'s stated validity condition is the wrong condition

> **Target (C.7), after Equation (7):** "the approximation holding for small individual
> effects."

**My derivation.** $\prod_i(1+e_i)=\exp\big(\sum_i\log(1+e_i)\big)$, so
$\exp(\sum_ie_i)$ is a valid proxy iff

$$
\Delta=\sum_i\big[e_i-\log(1+e_i)\big]\;\approx\;\tfrac12\sum_i e_i^2\;\ll\;1 .
$$

The controlling quantity is the **sum of squares** $\sum_ie_i^2$, not $\max_i|e_i|$. With
$n$ equal effects the requirement is $e\ll\sqrt{2/n}$ — the per-effect tolerance *shrinks*
as $\sqrt{1/n}$, so "small individual effects" is not sufficient without a constraint tying
$e$ to $n$. Machine-checked at $\sum e_i=6.8$: $n{=}20,e{=}0.34$ gives $\Delta=0.95$;
$n{=}10,e{=}0.68$ gives $\Delta=1.61$; $n{=}5,e{=}1.36$ gives $\Delta=2.51$ — all $O(1)$,
i.e. outside the valid regime.

**Calibrated impact — small.** The target elsewhere says the effects are "thousands of
near-zero single-neuron proportional effects". In that regime ($n\sim10^3$–$10^4$,
$e_i\sim10^{-3}$) one gets $\sum e_i^2/2\sim10^{-3}$, so the approximation is in fact
excellent and **the numerical conclusions stand**. The defect is that the stated condition
is not the one doing the work, and the regime that rescues it is mentioned three paragraphs
later as an aside rather than as Equation (7)'s hypothesis.

**Correction.** State the condition as $\sum_i e_i^2\ll1$, and note it is satisfied here
*because* $n$ is large and each $e_i$ is near zero. That one change simultaneously fixes
the condition, justifies quoting $896.8$ (see finding 5), and licenses the bound reading of
finding 2.

#### 4. UNSTATED HYPOTHESIS — "TE = NDE + NIE is not an identity" is convention-dependent, and the convention is never named

> **Target (C.6):** "$\mathrm{TE} = \mathrm{NDE} + \mathrm{NIE}$ is often quoted as though
> it were an identity. It is not; it is a hypothesis"

**My derivation.** True for the **pure/pure** pairing the target uses — its $D_{NDE}$ is the
*pure* NDE and its $D_{NIE}$ is the *pure* NIE, each evaluated with the other factor at its
null level — but **false in general**. Pairing one pure effect with one *total* effect makes
the decomposition an exact identity with **no assumption whatsoever**:

$$
\begin{aligned}
D_{TE}&=\underbrace{\big(y_{\text{set},z_{\text{null}}}-y_{\text{null}}\big)}_{\text{PNDE}} +
\underbrace{\big(y_{\text{set}}-y_{\text{set},z_{\text{null}}}\big)}_{\text{TNIE}},\\[2pt]
D_{TE}&=\underbrace{\big(y_{\text{set}}-y_{\text{null},z_{\text{set}}}\big)}_{\text{TNDE}} +
\underbrace{\big(y_{\text{null},z_{\text{set}}}-y_{\text{null}}\big)}_{\text{PNIE}} .
\end{aligned}
$$

Both telescope on sight. The exact three-way statement is
$D_{TE}=\mathrm{PNDE}+\mathrm{PNIE}+R$ with $R=\mathrm{TNIE}-\mathrm{PNIE}$ the **mediated
interaction** — which is precisely the target's Equation (6).

So the no-interaction condition is **the price of choosing pure/pure**, not an intrinsic
limitation of mediation decomposition. The target's framing ("it is a hypothesis") reads as
a general fact about the formalism and will mislead a reader transporting it elsewhere —
who is free to adopt the mixed pairing and pay nothing.

**Correction.** Name the convention ("both effects here are the *pure* natural effects"),
and add one sentence: the mixed pure/total pairings are exact identities, so the
no-interaction condition is convention-dependent and avoidable. This *strengthens* C.6 —
it sharpens "which hypothesis exactly" into "which hypothesis, and why this one".

#### 5. UNSTATED HYPOTHESIS — Equation (7) treats the multiplicative prediction as a function of NIE-sum; it is not

**My derivation.** $\prod_i(1+e_i)$ is **not** determined by $\sum_ie_i$. Given only
$\mathrm{NIE_{sum}}=S$ with $e_i\ge0$, the independence prediction spans the whole interval
$[\,S,\;e^{S}-1\,)$ — lower end at $n=1$, upper end as $n\to\infty$ with equal shares.
Machine-checked at $S=6.8$:

| $n$ | 1 | 2 | 5 | 10 | 50 | $\to\infty$ |
|---|---|---|---|---|---|---|
| $\prod(1+S/n)^n-1$ | 6.8 | 18.4 | 72.2 | 178.1 | 586.4 | 896.8 |

Two orders of magnitude, **all with exactly zero interaction**. Quoting $896.8$ as "the
null's prediction" is therefore only valid in the large-$n$ equal-share limit — which is
silently assumed. Related: the "$\approx$" in Equation (7) is really "$\le$", a one-sided
relation whose direction is the whole content of finding 2.

Two further gaps: the exact independence prediction $\prod_i(1+e_i)-1$ is computable from
**the very data that produced NIE-sum** (the per-neuron $e_i$ were summed, so they are in
hand) — the exponential form discards information already available; and $n$ is never
stated anywhere in C.7, without which a reader cannot place the prediction in the interval.

**Correction.** Write Equation (7) as $\prod_i(1+e_i)-1\le e^{\mathrm{NIE_{sum}}}-1$ with
equality in the large-$n$ infinitesimal-share limit; state $n$; and note the exact
prediction is computable from the same per-neuron data.

#### 6. UNSTATED HYPOTHESIS — C.8's "understates by about half" is orientation-dependent and unadjusted for regression attenuation

> **Target (C.8):** "a correlation of $R^2 = 0.27$ with a line of best fit of gradient
> $0.531$ — so it explains roughly a quarter of the variance and systematically
> *understates* effects by about half."

**My derivation.** "Explains roughly a quarter of the variance" from $R^2=0.27$ is fine.
The slope reading is not, for two reasons the text does not address:

1. **Orientation is unstated.** A slope of $0.531$ means "understates" only if the
   regression is attribution-on-exact. Regressing exact-on-attribution with the same data
   gives the opposite reading, and the target never says which was run.
2. **At $R^2=0.27$ the slope is attenuated, not a calibration factor.** For simple linear
   regression $b_{yx}\cdot b_{xy}=R^2$, so $b_{xy}=0.27/0.531=0.509$. **Both** regressions
   give a slope near one-half — the symmetric signature of errors-in-variables attenuation,
   not of a systematic bias one could correct by multiplying by $1.9$. Doing so would make
   the reverse regression demand the correction in the other direction.

So "systematically understates effects by about half" is not supported by a slope of
$0.531$ at $R^2=0.27$; the attenuation explanation fits at least as well, and the honest
statement is that attribution patching is **weakly correlated with, and poorly calibrated
against, exact patching** — which is anyway the conclusion the paragraph goes on to draw
("a screening instrument … never a calibrated effect size").

**Correction.** State the regression orientation; either quote a Deming / total-least-squares
slope or say the OLS slope is attenuated and is not a correctable gain. The paragraph's
final verdict is unaffected and arguably better supported.

#### 7. NIT — Equation (5)'s right-hand term is a tautology as written

> **Target (Eq. 5):** $\underbrace{\log y_1 - \log y_0}_{\text{log}} = \log\!\big(1 + \tfrac{y_1}{y_0} - 1\big)$

The $1+\cdots-1$ **cancels identically**, so the equation displays
$\log(y_1/y_0)=\log(y_1/y_0)$. It is correct and conveys nothing. The evident intent is
$L=\log(1+P)$ with $P$ the proportional effect — but inlining $P$'s definition destroys
exactly the connection the surrounding prose promises ("the log scale … is what connects
them"). Suggested form: define $P=y_1/y_0-1$ in the equation, then write $L=\log(1+P)$ and
its inverse $P=e^{L}-1$. Worth fixing because C.5's thesis rests on this equation
exhibiting the link.

#### 8. NIT — "three scales" is defensible only in the additivity sense, which should be said

Per my C1(c): $L=\log(1+P)$ is a strictly monotone bijection $(-1,\infty)\to\mathbb{R}$
that **does not depend on $y_0$**. So log and proportional are **informationally
equivalent** pointwise — one is a universal reparametrisation of the other, not a third
measurement. The difference scale is the genuinely distinct one, because $D=y_0P$ converts
only via the baseline, which differs per model.

The target's *usage* is nonetheless defensible: it invokes the three scales to say
"'the effects decompose additively' is three different claims", and additivity is
**not** preserved under nonlinear monotone reparametrisation — so there really are three
distinct additive structures. **Verdict: NIT, not an error.** But one sentence would make
it precise and would strengthen the section: *log and proportional carry the same
information about a single effect and differ only in what "additive" means across several.*
As written, a reader may infer the log scale carries information the proportional scale
lacks. It does not.

#### 9. NIT — "multiplicativity on the raw scale" multiplies fold-changes, not raw responses

> **Target (C.5):** "Additivity on the log scale is *multiplicativity* on the raw scale"

What multiplies is $y/y_0$ (equivalently $1+P$), giving $y_{12}=y_1y_2/y_0$ — **not**
$y_{12}=y_1y_2$. Under the conventional reading of "raw scale" as "before logs" the
sentence is fine; read literally it asserts something false. Precise form: *additive in
log-fold-change = multiplicative in fold-change.*

#### 10. NIT — "never near it", no CIs, no $n$

"Across the five models the null lands on both sides of the observation and never near it."
The closest is small at $2.10\times$ — on a scale where the additive null is off by
$28\times$, a factor of $2.1$ is arguably "near", and with **no uncertainty quoted anywhere
in C.7** it is not distinguishable from the error in Equation (7)'s own approximation.
Per `sim-report-completeness`, the table needs intervals; per finding 5, it needs $n$.
Suggest softening to "and only for small does it come within a factor of two".

---

### Net assessment

C.6 is mathematically sound and independently reproduced; its one gap (finding 4) makes it
*stronger*, not weaker. C.7's arithmetic is flawless but its two headline sentences — the
bracketing claim and the "uninformative" verdict — are respectively false for 4/5 models
and an over-correction that discards a defensible synergy result the same data support.
Findings 1 and 2 are coupled: fixing the first naturally produces the second, since
enumerating the signed factors per model is what reveals that four measurements sit above a
universal upper bound.

<!-- LOG-END-REVIEW -->

