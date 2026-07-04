# Plan — H9: Algorithmic ICL (forward-pass-as-online-optimizer)

**Date:** 2026-07-04 · **Status:** pre-registration (execute end-to-end) ·
**Parent:** `plans/2026-06-30-tiny-transformer-induction-study.md` §2 (H9), §6 ·
**Gate cleared:** `todos/2026-06-28-icl-as-online-learning-intuition.md` (4 sources acquired + verified) ·
**Decision:** `decisions/2026-07-01-03-fold-icl-inspection-into-tiny-transformer-plan.md`

## 0. One-line

Close H9 at commodity scale: show — with correctly separated evidence — that (A) a
*linear* self-attention layer with the von Oswald construction *is* one gradient-descent
step (bit-exact), and (B) a small *trained softmax* transformer's in-context predictions on
linear regression *behaviorally* track least-squares (OLS/ridge), tightening with context
length and depth — while **not** claiming the trained softmax model mechanistically runs GD.
The contrast between (A) and (B) is the deliverable.

## 1. Why this is the honest scope (source-grounded)

The four acquired sources partition into two evidence classes (understand-phase ledgers in
`_scratch/h9-understand/`, quotes with page numbers):

| Source | Attention | Weights | Evidence | What it licenses |
|---|---|---|---|---|
| von Oswald 2023 | **linear** (softmax fails 1-head) | constructed + trained-converge | **mechanistic** (Prop 1, exact) | 1-LSA-layer = 1 GD step; K layers ≈ K GD / GD++ |
| Akyürek 2023 | softmax (approx, GeLU-mult) | constructed + trained | mixed | softmax *can be constructed* to do GD/ridge; trained *matches* OLS/ridge by regime |
| Garg 2022 | softmax | trained | **behavioral** | trained ICL *tracks* min-norm OLS (0.02@k=d); **not** ridge, **not** GD-mechanism |
| Dai 2022 | relaxed-linear | pretrained | behavioral | dual-form GD only w/o softmax; real-GPT = finetuning-similarity, not regression |

**Load-bearing do-NOT list** (the citation-integrity guardrail, enforced in the report §10
red-team + the §A.23 note):
- Do **not** claim a trained *softmax* transformer mechanistically implements GD. The exact
  mechanism is *linear* attention + constructed weights (von Oswald); single-head softmax
  explicitly fails (§A.9).
- Do **not** attribute ridge/OLS *closed-form* to von Oswald (its comparator is k-step GD/GD++).
- Do **not** cite Garg for a *mechanism* (behavioral only; internals left to future work).
- Do **not** cite Dai for the linear-regression setting (it disclaims it) — it is the
  over-claim-slogan boundary marker only.

## 2. Pre-registered hypotheses (numeric)

- **H9-A (Quantitative, mechanistic).** With the von Oswald Prop-1 weights hand-set into a
  1-layer linear self-attention over tokens $e_j=(x_j,y_j)$, the layer's update to the query
  prediction equals one GD step on the in-context MSE loss to **machine precision**
  (max abs diff $< 10^{-5}$, float64). Stacking $K$ such layers reproduces $K$ GD steps
  (per-step max abs diff $< 10^{-5}$). **PASS iff** both hold; this is an exact identity, not
  a fit.
- **H9-B (Quantitative, behavioral).** A small trained *softmax* regression transformer's
  in-context prediction error on held-out tasks (i) decreases with context length $k$ and
  (ii) approaches the OLS/ridge oracle: normalized deviation from the best-matching classical
  learner $\Delta_{\text{norm}} < 0.10$ at $k = 2d$ (Garg reports 0.0006 at 9.5M/500k; we
  scale down and pre-register the looser 0.10 bar honestly). **PASS iff** (i) monotone-ish
  decrease *and* (ii) $\Delta_{\text{norm}}<0.10$ at $k=2d$.
- **H9-C (Directional, contrast).** At the trained model's operating context length, the
  model's predictions are **closer to OLS/ridge than to a single GD step** (agreement gap
  favors the closed-form learner), consistent with Garg/Akyürek behavioral-OLS and *against*
  a naive "one GD step" reading of a shallow trained softmax model. **PASS iff** the model's
  prediction-agreement to OLS ≥ its agreement to 1-step GD.
- **H9-D (Directional, tightening).** The behavioral OLS-match tightens with model **depth**
  (a deeper model tracks the closed-form learner at least as well as a shallower one) — the
  Akyürek depth-phase direction, tested at 2–3 depths.

## 3. Task, model, baselines

**Task (Garg setup, scaled).** $w\sim\mathcal N(0,I_d)$, $x_i\sim\mathcal N(0,I_d)$,
$y_i = w^\top x_i$ (noiseless main; a noisy variant $y=w^\top x+\varepsilon$ for the
ridge-vs-OLS contrast). Prompt token stream interleaves $(x_1,y_1,\dots,x_k,y_k,x_q)$; the
model predicts $y_q$. Squared loss averaged over all query prefixes (as Garg). $d=8$
(scaled from 20), $k$ up to $2d{+}$; explicit seeds; eval tasks use an offset seed stream
(train/eval non-collision, mirroring `train_toy`).

**Model (new `implementation/icl_regression/`, softmax).** Purpose-built small causal
decoder: linear **read-in** $\mathbb R^{d+1}\!\to d_{\text{model}}$ (real $(x,y)$ tokens,
$y$-slot zeroed for $x$-only query token), $N$ pre-norm softmax attention+MLP blocks, learned
positional embedding, linear **read-out** $d_{\text{model}}\!\to\mathbb R$ read at $x$-query
positions, MSE loss. Config scaled for MPS/CPU: $d_{\text{model}}\approx 64$–128, $N\in\{1,2,4\}$
(for the depth sweep), heads 2–4, ~few-thousand AdamW steps. Reuse `tiny_transformer`
**patterns** (frozen-dataclass config, AdamW+warmup loop skeleton, `bootstrap_ci`,
determinism), not the token `HookedTransformer`.

**Part-A module (linear, constructed).** A tiny linear self-attention layer whose
$W_K,W_Q,W_V,P$ are **settable**; hand-set to the von Oswald block form (eq 8) and verify the
identity. No training. Pure float64 linear algebra.

**Classical baselines (closed form, from the same task arrays).** min-norm OLS
$\hat w=X^+y$; ridge $\hat w=(X^\top X+\lambda I)^{-1}X^\top y$ (Bayes $\lambda=\sigma^2/\tau^2$
in the noisy variant); $j$-step batch GD on the in-context MSE from $w_0=0$ with tuned step
(von Oswald comparator); GD++ (preconditioned) optional. Prediction-agreement metric:
normalized squared prediction difference (Akyürek SPD-style), reported per learner.

## 4. Deliverables

1. **`implementation/icl_regression/`** — `task.py` (regression batch + closed-form learners),
   `model.py` (softmax regression transformer + MSE train loop), `construction.py` (von Oswald
   LSA + GD-step identity, Part A), `run.py` (train + evaluate + save artifact), `figure.py`.
2. **`artifacts/icl-regression/`** — `summary.json` (H9-A/B/C/D verdicts + metrics + CIs +
   seeds + env), `curves.npz` (loss-vs-k, per-learner agreement), figures + `.data.json`.
3. **`docs/h9-algorithmic-icl-study.md`** — reproduction/eval report under
   `sim-report-completeness` (14-section spine; drop [M] n/a explicitly). Theory-as-predictor:
   overlay OLS/ridge/GD curves on the model curve with residuals.
4. **`surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.23** — the
   "forward-pass-as-online-optimizer" intuition subsection, cited to [94]–[97], `secref` back
   to §A.22's out-of-scope sentence + forward-links to §A.6/§A.16 (the "opposite" per-head
   detection reading). Contrasts mechanistic-linear vs behavioral-softmax explicitly.
5. **`references.md` [94]–[97]** — von Oswald, Garg, Akyürek, Dai with `(local: download/…)`
   tags (PDFs already acquired; **no source-fetch needed** — verified present).
6. **`tests/icl_regression/`** — G1 gate: the Part-A identity to machine precision;
   closed-form-learner correctness (OLS recovers $w$ noiseless at $k\ge d$); task determinism;
   train-loss-decreases smoke; agreement-metric properties.

## 5. Sequence

1. Task + closed-form learners + tests (zero citation risk, pure math). 
2. Part A: von Oswald construction + machine-precision identity test (fast, exact).
3. Part B: softmax regression transformer + train loop; depth sweep; evaluate agreement.
4. `run.py` → artifact; `figure.py` → overlays.
5. Report (completeness gate) + §A.23 note + refs [94]–[97] (citation gate).
6. **Adversarial audit** (citation-scope lens especially — the linear/softmax,
   constructed/trained boundary; stats lens; re-derivation of the Part-A identity).
7. Sign-off: `/check-survey llms-for-coding` (the §A.23 edit touches the survey),
   completeness + citation gates on the report, `pytest tests/icl_regression -q`, `/cross-link`.

## 6. Scale-down honesty (pre-registered)

Garg trains 9.5M params / 500k steps; we train a smaller model for fewer steps on MPS/CPU.
The behavioral-match claim is **curve-shape + operating-point**, robust to scale-down; the
report discloses the exact config numerically (figure-operating-conditions rule) and frames
H9-B as "an eval of *this* small configuration tracks OLS," not "the benchmark mandates it."
If the scaled model misses the $\Delta_{\text{norm}}<0.10$ bar, that is an honest INCONCLUSIVE
on H9-B (report it; Part A / H9-A is unaffected, being an exact identity).

## 7. Out of scope → `todos/`

Mechanistic probing of the trained softmax model (does layer $\ell$ compute a GD step? — the
Akyürek §5 / von Oswald weight-space analysis); the two-head-softmax approximate-GD
reproduction (§A.9); GD++ preconditioning fit; larger $d$ / Garg-scale training; the kernel
(MLP+LSA) extension (von Oswald Prop 2). File on sign-off.
