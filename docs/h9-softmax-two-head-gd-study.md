# H9 follow-on — two-head softmax as approximate gradient descent (von Oswald §A.9)

*A constructive reproduction: a single softmax attention head cannot match the one-GD-step
update; two sign-reversed heads cancel the offset and recover it — imperfectly, with an error that
vanishes as context grows.*

Study code: `implementation/icl_regression/softmax_construction.py`, `softmax_run.py`,
`softmax_figure.py`; gates `tests/icl_regression/test_softmax_construction.py`; artifact
`artifacts/icl-regression-softmax/summary.json`. Parent: H9 (`docs/h9-algorithmic-icl-study.md`),
todo `todos/2026-07-04-h9-followups.md`. Source: von Oswald et al. 2023, §A.9 (Eq 14–21).

---

## 0 · Executive summary

**Verdict: REPRODUCED.** von Oswald §A.9's single-vs-two-head softmax result reproduces
constructively (deterministic, no training) on the in-context linear-regression task
(`d = 8`, `η = 0.5`, context `N = 20`, `B = 2000` tasks, seed 1):

- **The mechanism is exact.** The idealized two-head construction (their Eq 19–21: linearize the
  softmax, subtract two sign-reversed heads) reproduces the one-GD-step prediction to
  **`3.1e-15`** — machine precision, for every score scale `β`. This is the softmax-side analog of
  H9-A's `1.3e-15` linear-attention identity.
- **A single head fails at the headline `N`.** Best-case (closed-form optimal output scale `c*`,
  tuned over `β`) a single softmax head has a **`0.587`** normalized error vs the GD step at
  `N = 20` — a floor that is irreducible *under `(c,β)` tuning at fixed `N`* (not a fundamental
  wall; see below). It is **offset-limited at small `β`**: the query-independent Eq-17 term is
  **`0.996`** of its output at `β = 0.02`, but only **`0.177`** at its best-case `β ≈ 0.57`, where
  hard-max over-sharpening — not the offset — is the limiter. The single head's failure is the
  `β`-tradeoff between the two.
- **Two heads recover it, imperfectly.** Two sign-reversed heads cut the error **`4.5×`** to
  **`0.130`** (bootstrap 95% CI `[0.118, 0.142]`) — "good but not as precise as linear" (their
  Fig 12). The residual is a small **`O(1/N)` centering floor** (the unequal-denominator term their
  "PV subsumes the softmax divisor, equal per head" assumption idealizes away); the predicted
  centering term explains **`98.3%`** of it.
- **The advantage is a convergence-*rate* gap.** Across `N ∈ {10,20,40,80,160}` **both** floors
  decline — but the two-head floor is `O(1/N)` (asymptotically; `two-head × N` plateaus at `~3.0`
  for `N ≥ 40`, with finite-`N` corrections at `N = 10,20`) while the single-head floor falls more
  slowly (crossing the `0.30` mark near `N ≈ 160`). So the single/two ratio *widens* `3.1×→15.1×`:
  the two head is not the only one that recovers, it recovers *faster*.

**Claims → evidence.** mechanism-exact → §5 anchor 1 (`3.1e-15`) + `test_idealized_two_head_...`;
single-head-fails (at `N = 20`) → §6 β-sweep + §5 anchor 3 (offset `0.996` small-`β` / `0.177`
best-`β`); two-head-recovers → §6 headline +
CI; residual-root-caused → §5 anchor 2 (centering `98.3%`) + §7 N-scaling; not-a-training-artifact
→ this is a *constructive* result (the honest softmax with the paper's constructed weights), so no
optimizer confound.

**Do not cite** any number here as a claim about a *trained* softmax transformer — this study
reproduces the §A.9 *construction/analysis*, not the Fig-12 *training* run (a documented,
deferred secondary leg; see §9, §11).

---

## 1 · Problem & scope

H9-A established that a *linear* self-attention layer's forward pass **is** one GD step, exactly
(von Oswald Prop 1). Real transformers use *softmax* attention. §A.9 of the same paper argues, and
shows empirically (Fig 12), that (a) a single softmax head *cannot* match the GD step, and (b) two
heads *approximately* can, via a Taylor-expansion offset-cancellation. The H9 study deferred this
softmax-side mechanistic leg (`todos/2026-07-04-h9-followups.md`). This study closes it.

**Pre-registered hypotheses** (numeric thresholds, tested in §6):

| # | Hypothesis | Threshold | Kind |
|---|---|---|---|
| H-S1 | Idealized two-head construction = GD | max abs residual `< 1e-10` | Quantitative |
| H-S2 | Single softmax head cannot match GD at fixed `N = 20` | best-case norm. error `> 0.30` | Directional+magnitude |
| H-S3 | Two heads recover GD far better | error `< 0.25` and single/two `> 2.5` | Quantitative |
| H-S4 | The two-head residual is the centering term | unexplained `< 0.10` | Quantitative |
| H-S5 | The residual is asymptotic-only (`O(1/N)`) | two-head floor strictly ↓ in `N` | Directional |

**Scope.** A *constructive* reproduction (the paper's constructed weights with a softmax swapped
in), not a *trained* one. Correctly scoped to the §A.9 analytical argument (Eq 14–21) and the
single-layer single-vs-two-head contrast (Fig 12), on isotropic-Gaussian in-context regression.

---

## 2 · The mechanism & conformance (source-cited)

**Setup** (concatenated layout `e_j = (x_j, y_j)`, value `v_i = y_i − W0·x_i`, `W0 = 0`; shared
`(1/2N)` loss convention so one `η` means the same GD step as H9-A and `task.gd_predict`).

**Softmax Taylor-expands** (von Oswald Eq 14–16). With scores `s_i = x_iᵀx_q` (the `W_KQ = I`
construction) and score scale `β`:

$$
\mathrm{softmax}(\beta s)_i \;=\; \frac{e^{\beta s_i}}{\sum_{i'} e^{\beta s_{i'}}}
\;\approx\; \frac{1 + \beta s_i}{\sum_{i'} (1 + \beta s_{i'})}. \tag{1}
$$

The leading `1` is a **query-independent additive offset** (their Eq 17) — a single head is stuck
with it and cannot reproduce the pure linear score the GD construction needs.

**Two heads subtract the offset** (their Eq 18–21). With sign-reversed scores (`β`, `−β`) and
opposite output signs (`P₂V₂ = −P₁V₁`), the two `1`s cancel:

$$
(1 + \beta s_i) - (1 - \beta s_i) \;=\; 2\beta s_i. \tag{2}
$$

leaving the pure linear score. With the matched output scale `c = η/(2β)` this is exactly the
one-GD-step update — **provided** the two heads share a denominator (their stated "PV subsumes the
softmax divisor and is equal per head" assumption).

**Conformance matrix** (this constructive eval vs the paper's §A.9 objects). "Protocol-faithful"
is graded, not binary.

| Item | Status | Note / metric impact |
|---|---|---|
| Linearize softmax to `1 + βs` (Eq 16) | `IDEALIZED` | exact as `β→0`; the honest run keeps full `exp` — the deviation is the measured two-head error |
| Equal per-head denominator (Eq 19–21 assumption) | `IDEALIZED` | the idealized predictor forces divisor `N`; the honest predictor keeps the real per-head divisors → the `O(1/N)` centering floor (§5, §7) |
| `W_{1,KQ} − W_{2,KQ}` diagonal (Prop-1 weights) | `EXACT` | reproduced via `s_i = x_iᵀx_q` with sign-reversal |
| Softmax over the `N` context tokens (Eq-14 sum) | `IDEALIZED` | isolates the offset mechanism; a full-sequence softmax adds a query-self term orthogonal to §A.9's argument (that variant belongs to the trained leg, §11) |
| Single/two-head trained emergence (Fig 12) | `DEVIATED` | not run here — this is the *construction/analysis*, not the *training*. Deferred (§9, §11) |
| Data distribution | `EXACT` | isotropic Gaussian `x_i, w ~ N(0, I_d)`, matching Garg/von Oswald |

**External anchor at point of use.** The `1 + βs` offset (Eq 17) and the two-head subtraction
(Eq 19–21) are read from `download/vonoswald-transformers-icl-gradient-descent-2023.pdf` §A.9,
not recalled.

---

## 3 · Task, candidates & conventions

- **Task.** One-GD-step in-context regression: given `{(x_i, y_i)}` and query `x_q`, predict the
  one-step-GD-from-zero prediction `gd_step_prediction(X, y, x_q, W0=0, η)` (the H9-A / `task.py`
  oracle, exact).
- **Candidates.** (1) single honest softmax head `c·Σ softmax(βs)_i v_i`; (2) two honest heads
  `c·[Σ softmax(βs)_i v_i − Σ softmax(−βs)_i v_i]`; (3) idealized two-head (Eq-16 linearization +
  equal divisor). Output scale: `c*` fit closed-form for the single head (fairest best-case),
  `c = η/(2β)` matched for both two-head variants.
- **Metric.** Normalized RMSE to the GD step, `sqrt(Σ(pred − gd)² / Σ gd²)` (Akyürek-style, `= 0`
  iff identical). Bootstrap 95% CI over examples (`n_boot = 10000`).
- **Decoding params.** n/a — this is a closed-form constructive study, no sampling/decoding.
- **Notation.** `β` score scale (inverse temperature); `c` output scale; `N` context length; `d`
  input dim; `η` GD learning rate; `s_i = x_iᵀx_q`; `v_i = y_i − W0·x_i` value.

---

## 4 · Implementation & math-to-code

| Source object | Code |
|---|---|
| softmax Taylor / offset (Eq 16–17) | `softmax_construction.single_head_predict`, `offset_term` |
| two-head subtraction (Eq 18) | `softmax_construction.two_head_predict` |
| idealized construction (Eq 19–21) | `softmax_construction.two_head_ideal_predict` |
| matched scale `c = η/(2β)` | `softmax_construction.matched_scale` |
| centering term `−(η/N)·s̄·Σv` | `softmax_construction.centering_term` |
| GD oracle (H9-A) | `construction.gd_step_prediction` |
| β-sweep / N-sweep / verdict | `softmax_run.py` |

**Numerical safety.** stable softmax (subtract max); spurious Apple Accelerate matmul FPE flags
suppressed at each entry point with finiteness assertions retained; float64 throughout.

---

## 5 · Verification (correctness anchors — G1, 7 tests)

Verification (fixed known relations) vs validation (the reproduction result) are kept separate.
Three anchors, each measured and persisted to `summary.json` (not asserted in prose):

- **Anchor 1 — idealized two-head = GD to machine precision** — max abs residual **`3.1e-15`**
  across `β ∈ {0.02,0.1,1,3}` and `W0 ∈ {0, random}`. A `β`-independent algebraic identity: it
  proves the Eq-19–21 mechanism exactly. (`test_idealized_two_head_equals_gd_machine_precision`.)
- **Anchor 2 — the two-head residual IS the centering term** — the predicted `−(η/N)·s̄·Σv`
  explains **`98.3%`** (unexplained `0.017`) of the honest small-`β` two-head residual. This
  root-causes the floor to the unequal-denominator idealization, an *asymptotic-only* effect, not a
  bug. (`test_centering_term_explains_two_head_residual`.)
- **Anchor 3 — the single head is offset-limited at small `β` (not at best-case)** — the
  query-independent Eq-17 term is **`0.996`** of the single head's output at `β = 0.02` (where the
  head is worst), but only **`0.177`** at its best-case `β ≈ 0.57`, where hard-max over-sharpening —
  not the offset — limits it. The failure is the small-`β`-offset / large-`β`-sharpening tradeoff,
  offset-dominated only in the small-`β` regime.
  (`test_single_head_offset_dominates_at_small_beta_not_best_case`.)

Plus: softmax normalization + uniform-at-`β=0` sanity; single-head large-floor gate; two-head
beats-single-by-wide-margin gate; linearizing-reduces-two-head-error monotonicity. **7/7 pass.**

---

## 6 · Results & verdict (bootstrap 95% CI on headline + N-sweep cells; full per-cell CIs in `summary.json`)

**β-sweep at `N = 20`** (single-head best-case error / two-head matched error vs the GD step;
representative 95% bootstrap CIs shown, all 12 cells in the artifact):

| `β` | single-head best-case | two-head (matched) | idealized (abs RMS) |
|---|---|---|---|
| 0.020 | `0.994` | `0.130` `[0.118, 0.142]` | `7.6e-16` |
| 0.107 | `0.883` | `0.135` | `4.2e-16` |
| 0.247 | `0.670` | `0.181` | `3.2e-16` |
| 0.570 | `0.587` `[0.563, 0.612]` | `0.346` | `3.4e-16` |
| 1.316 | `0.671` | `0.608` | `3.2e-16` |
| 2.000 | `0.706` | `0.721` | `3.2e-16` |

The single head is U-shaped in `β` (uniform attention at small `β`, hard-max at large `β`) with a
best-case floor `0.587`; the two head is monotone (best at small `β`, where the linearization is
tightest), floor `0.130`. The idealized line sits at machine precision throughout — **theory as a
predictor, not a bound**: it is the closed-form GD prediction overlaid on the honest curve, and the
honest-minus-idealized gap is fully accounted for by the §5 centering term.

**N-sweep** (best-case floors, both with 95% bootstrap CI):

| `N` | single floor `[95% CI]` | two-head floor `[95% CI]` | ratio | two-head × `N` |
|---|---|---|---|---|
| 10 | `0.645` `[0.615, 0.675]` | `0.211` `[0.195, 0.228]` | `3.1×` | 2.11 |
| 20 | `0.587` `[0.563, 0.612]` | `0.130` `[0.118, 0.142]` | `4.5×` | 2.59 |
| 40 | `0.493` `[0.469, 0.517]` | `0.076` `[0.070, 0.082]` | `6.5×` | 3.05 |
| 80 | `0.412` `[0.392, 0.434]` | `0.040` `[0.037, 0.043]` | `10.3×` | 3.19 |
| 160 | `0.307` `[0.288, 0.331]` | `0.020` `[0.018, 0.023]` | `15.1×` | 3.26 |

The two-head floor is **asymptotically `O(1/N)`**: `two-head × N` plateaus at `~3.0` for `N ≥ 40`,
with visible finite-`N` corrections at `N = 10, 20` (the consecutive-doubling ratio is `0.62, 0.59,
0.52, 0.51`, approaching `½` only in the tail). The **single-head floor also declines** with `N`
(`0.645 → 0.307`, crossing the `0.30` verdict threshold near `N ≈ 160`) — so "single head fails" is
a *fixed-`N`* statement (the Fig-12 regime), not a fundamental wall. Both heads recover as
`N → ∞`; the two head does so *faster* (`O(1/N)` vs the single head's slower decline), which is why
the single/two ratio *widens* `3.1×→15.1×`. Figure:
`artifacts/icl-regression-softmax/figures/h9-softmax-two-head.png`.

**Hypothesis verdicts:** H-S1 PASS (`3.1e-15 < 1e-10`) · H-S2 PASS (`0.587 > 0.30` at `N = 20`) ·
H-S3 PASS (`0.130 < 0.25`, ratio `4.5 > 2.5`) · H-S4 PASS (unexplained `0.017 < 0.10`) · H-S5 PASS
(two-head floor strictly ↓; single-head floor also ↓, more slowly). **`reproduced = True`** at the
headline `N = 20`.

---

## 7 · Sensitivity & ablation

- **Score scale `β`** (§6 β-sweep): single-head best at `β ≈ 0.57`; two-head best as `β → 0`. The
  two objects prefer opposite regimes — the single head needs enough `β` to break uniformity but
  then over-sharpens; the two head wants the linearization exact.
- **Context length `N`** (§6 N-sweep): the two-head floor is `O(1/N)` and the single-head floor
  declines more slowly; the reproduction's *contrast* (ratio `> 3` everywhere, growing to `15×`) is
  robust across the whole grid, but the binary "single head fails" gate (`floor > 0.30`) is
  `N`-specific — it holds at the Fig-12 regime (`N ≤ ~150`) and would flip in the large-`N` tail
  where both heads have recovered. The honest invariant is the *rate gap*, not a single-head wall.
- **Output scale.** The single head gets its *closed-form optimal* `c*` (a fairness ceiling —
  no hand-tuning can beat it at fixed `β`); it still fails. The paper's "we tuned the learning rate
  and weight init and found no significant difference" is reproduced by construction.

---

## 8 · Quantization

**n/a (explicit).** This is a float64 constructive study; no reduced-precision compute or storage
is in scope. Reduced-precision realization of the ICL constructions is tracked as a deferred item
(`todos/2026-07-04-h9-followups.md`).

---

## 9 · Recommendation

**Treat the two-head softmax result as a *mechanistic* reproduction of §A.9, not a *behavioral*
one.** The construction proves *why* two heads suffice (offset cancellation, exact under the
paper's idealization) and quantifies the honest gap (an `O(1/N)` centering floor). Cite it for the
mechanism and the single-vs-two-head contrast. Do **not** present it as evidence that a *trained*
softmax transformer learns this (that is the Fig-12 training run, deferred). Conditions: isotropic
Gaussian regression, single layer, `W0 = 0`, `d = 8`.

---

## 10 · Limitations, red-team & flip

- **Where "single head fails" flips.** The `floor > 0.30` gate is `N`-specific: the single-head
  floor also declines with `N` (`0.645 → 0.307` over `N = 10..160`, crossing `0.30` near `N ≈ 160`),
  so at large `N` both heads clear the bar and the binary "fails" verdict flips. The durable claim
  is the *convergence-rate* gap (two-head `O(1/N)` vs the single head's slower decline), not that
  the single head is fundamentally incapable — disclosed so the reproduction is not read as a
  stronger negative result than the data supports.
- **Where the two-head loses to "linear".** At large `β` (`> 1`) the two-head error *exceeds* the
  single-head floor (β-sweep bottom rows: `0.72` vs `0.71` at `β = 2`) — the linearization has
  broken down and the offset cancellation no longer holds. The two-head advantage is a small-`β`
  phenomenon, disclosed.
- **Where the single head "wins".** If the residuals were exactly mean-zero (`Σv_i = 0`) the Eq-17
  offset would vanish and a single head would do far better — the offset is a property of the data
  statistics, not softmax alone. The reproduction uses honest random tasks where `Σv_i ≠ 0`.
- **Constructive, not trained.** The strongest threat: a trained softmax head might find a
  *different* (non-GD) solution that scores well. This study does not claim otherwise — it
  reproduces the paper's *analysis*, and explicitly defers the training run (§9, §11).
- **Single-instance vs batched.** The honest-minus-idealized gap is not monotone per task (it mixes
  the vanishing Taylor remainder with the constant centering term); only the *batched* error is
  monotone in `β`. The G1 monotonicity gate is batched for this reason (caught during the build).

---

## 11 · Roadmap → todos

Deferred items are tracked in `todos/2026-07-04-h9-followups.md` (updated by this study):
the **trained** single-layer 1-head-vs-2-head run (literal Fig 12, the DEVIATED conformance row);
the full-sequence-softmax variant; a reduced-precision pass; larger `d` / Garg-scale. No new
"further study" claim is left untracked.

---

## 12 · Reproduce

#### reproduce

```
PYTHONPATH=$PWD python3 -m implementation.icl_regression.softmax_run     # -> summary.json
PYTHONPATH=$PWD python3 -m implementation.icl_regression.softmax_figure  # -> figure + data.json
PYTHONPATH=$PWD python3 -m pytest tests/icl_regression/test_softmax_construction.py -q
```

Deterministic: every result is a pure function of the fixed seed (`SEED = 1` for the sweeps;
per-cell bootstrap seeds `100+i / 200+i / 300+N / 400+N`; verification seeds fixed in
`_verification`). No wall-clock, no unseeded randomness. Env recorded in `summary.json.env`
(`python`, `numpy`, `platform`). Raw per-example arrays regenerate the figure without recomputation.

---

## 13 · Audit trail

- **Decision:** `decisions/2026-07-04-04-h9-softmax-two-head-scope.md` (constructive-first scope;
  the honest-vs-idealized two-object structure; the centering-floor root-cause).
- **Field notes:** `field-notes/2026-07-04-h9-softmax-two-head.md` (the non-monotone
  single-instance gap; the centering-term derivation; the `gd_step_prediction` FPE guard).
- **Pre-sign-off adversarial audit** (3 Opus lenses: math re-derivation / code+numbers /
  report-honesty+citation). Math and numbers confirmed sound — an independent reimplementation
  reproduced every `summary.json` value to the last digit, the centering term's sign/form/`O(1/N)`
  order re-derived, citations verified against §A.9. Applied findings (all honest-framing, no
  correctness/verdict change): scoped "single head fails" to fixed `N` (both floors decline; §6,
  §10); re-measured the offset at the *actual* best-case `β` (`0.177`, not the `0.50`-at-`β=0.26`
  mislabel) plus the small-`β` value (`0.996`; §5 Anchor 3); softened `O(1/N)` to *asymptotic* with
  finite-`N` corrections; corrected two CIs (`[0.56,0.61]`, `[0.070,0.082]`) and two roundings.
- **Citation integrity.** Every §A.9 relation (Eq 14–21) was read from the acquired source
  `download/vonoswald-transformers-icl-gradient-descent-2023.pdf`, not recalled. No new external
  numbers are introduced; the only reference is [94] von Oswald (already `local:`-tagged in the
  H9 survey references).

---

## Sources

- **[94]** J. von Oswald, E. Niklasson, E. Randazzo, J. Sacramento, A. Mordvintsev, A. Zhmoginov,
  M. Vladymyrov, "Transformers learn in-context by gradient descent," ICML 2023, §A.9, Eq 14–21.
  (local: `download/vonoswald-transformers-icl-gradient-descent-2023.pdf`)
