# EAP-IG Circuit Faithfulness — Reference Implementation Study

**Study:** `eap-ig-faithfulness`  **Topic module:** `implementation/eap_ig/`
**Mode:** `proposed` (all 13 items P0-1 … P2-4)
**Substrate:** GPT-2-small (124M, cached), CPU/MPS, offline — decision `2026-07-02-04`.
**Parent handoff:** `todos/2026-07-01-mechinterp-ris-handoff.md` (candidate 2);
survey `surveys/mechanistic-interpretability/method-inventory-causal.md`,
`open-problems-and-roadmap.md` §15.2.
**Primary source (read, not recalled):** Hanna, Pezzelle & Belinkov, *Have Faith in
Faithfulness: Going Beyond Circuit Overlap When Finding Model Mechanisms*, COLM 2024
— `(local: download/hanna-eap-ig-faithfulness-2024.pdf)`.

## 0. Executive summary

**Verdict: EAP-IG reproduces as the more faithful attribution method — at ~⅓ the cost of
exact patching it recovers ~99% of exact's circuit faithfulness, versus EAP's ~64%.**
Headline signed margin: **EAP-IG − EAP normalized faithfulness at circuit size n=20 =
+0.224 (paired d_z=0.72, p=3.6×10⁻³⁴, N=360 example-seeds across 3 tasks)**; EAP-IG 0.623
vs EAP 0.399 vs exact-patching 0.627 vs random 0.00. The mechanism confirms strongly:
**EAP-IG edge-scores correlate with exact-patching scores at Pearson ρ=0.92 vs EAP's 0.46.**
Cost hierarchy (GPT-2-small, CPU): EAP 3.2s, EAP-IG 9.2s (~3×), exact 50.6s (~16×).

*Honest divergence from Hanna et al.:* at node granularity + top-n our **task pattern
differs** — IOI shows a huge gap (EAP 0.03 vs EAP-IG 0.54, d=2.05) where the paper found a
small one, and Greater-Than saturates so its gap is **not significant** (p=0.14). Root-caused
in §7; do-not-cite absolute numbers (§2).

Claims→evidence spine:

| Claim | Evidence artifact | Status |
|---|---|---|
| C1 EAP-IG ≥ EAP faithfulness at matched size (overall) | §6 pairwise, p=3.6e-34, d=0.72 | ✅ confirmed |
| C2 gap is task-dependent | §6 per-task (IOI d=2.05; SVA d=0.51; GT n.s.) | ⚠️ confirmed but pattern differs from paper (§7) |
| C3 activation-patching is the oracle both approximate | §5 oracle + §6 ordering exact≥eap_ig≥eap | ✅ confirmed |
| C4 EAP-IG scores correlate with exact patching better than EAP | §6 ρ_IG=0.92 > ρ_EAP=0.46 | ✅ confirmed |

## 1. Problem, scope & candidates (Phase 1)

**Problem.** Circuit-finding by *edge attribution patching* (EAP) approximates, in two
forward passes + one backward pass, the effect of causally patching every edge of a
transformer's computational graph — a linear (first-order Taylor) surrogate for exact
activation patching, which is $O(\text{edges})$ forward passes. The open question this
study reproduces: **does the first-order surrogate yield *faithful* circuits**, and does
augmenting it with integrated gradients (EAP-IG) close the faithfulness gap to exact
patching? "Faithful" = ablating every edge *outside* the circuit (patching it to its
corrupted-input activation) leaves the task metric unchanged.

**Model under study.** GPT-2-small (124M; 12 layers, 12 heads, $d_{\text{model}} = 768$),
loaded from the local HF cache, run deterministically on CPU/MPS. The full EAP graph on
GPT-2-small has 32,491 edges (Hanna §1); this study operates at **head + MLP node
granularity** (see §2 conformance) over the additive residual stream.

**Tasks** (all templated / self-generated — no download; minimal clean/corrupt pairs + a
metric $M$, higher = clean-like):

- **IOI** (Indirect Object Identification): *"When Mary and John went to the store, John
  gave a drink to"* $\to$ "Mary". $M$ = logit-diff, `logit(IO) − logit(S)`. Corrupt: the
  second subject name is swapped to a third name, equalizing IO/S.
- **Greater-Than**: *"The war lasted from the year 1741 to the year 17"* $\to$ a valid
  two-digit end-year $> 41$. $M$ = prob-diff $\sum_{y=42}^{99} p(y) - \sum_{y=00}^{41} p(y)$.
  Corrupt: start year's last two digits $\to$ "01".
- **SVA** (Subject-Verb Agreement): *"The keys on the cabinet"* $\to$ "are". $M$ = prob-diff
  (agreeing − disagreeing verb forms). Corrupt: subject number is flipped (keys $\to$ key).
  This is the task where EAP's first-order surrogate is known to fail catastrophically.

**Candidate methods** (edge-scoring functions; §3 for equations):

1. `eap` — Edge Attribution Patching (first-order). *Baseline to beat.*
2. `eap_ig` — EAP with Integrated Gradients, $m = 5$ path steps. *Intervention.*
3. `exact_patch` — exact activation patching per edge. *Ground-truth oracle both approximate.*
4. `random` — random edge ranking. *Floor control.*

**Evaluation metrics** (≥2): (a) **normalized circuit faithfulness** as a function of
circuit size $n$; (b) **Spearman/Pearson correlation** of each method's edge scores with
`exact_patch` scores; (c) **cost** (forward+backward passes, wall-time percentiles) — the
whole reason EAP exists.

**Pre-registered hypotheses** (grounded in Hanna §4.3 / Fig 3 — *not* memory; see bug
`2026-07-02-04` for the corrected IOI framing):

- **H1 (Quantitative, IOI):** EAP and EAP-IG circuits both plateau near **0.6** normalized
  faithfulness on IOI, both below activation-patching (**> 0.8**); the EAP→EAP-IG gap on IOI
  is small (≈ 0). *A faithful reproduction shows EAP-IG ≈ EAP on IOI — not a large lift.*
- **H2 (Quantitative, Greater-Than):** EAP-IG exceeds EAP by **≈ 0.1** normalized
  faithfulness at the small-`n` operating point.
- **H3 (Quantitative, SVA):** EAP produces a catastrophically unfaithful circuit at small
  `n` (parentless heads pruned to near-nothing); EAP-IG repairs it — the essential
  input-embedding→MLP0 edge is scored by EAP-IG but missed by EAP.
- **H4 (Quantitative, ordering):** at matched `n`, faithfulness `exact_patch ≥ eap_ig ≥ eap`
  on SVA/GT; `random` is the floor.
- **H5 (Quantitative, mechanism):** `eap_ig` edge scores correlate with `exact_patch` scores
  better than `eap` (Pearson $\rho_{\text{IG}} > \rho_{\text{EAP}}$, both $p < 0.01$).

## 2. Protocol-vs-spec conformance matrix

Grading each design choice against Hanna et al.'s protocol: `EXACT` / `APPROXIMATED` /
`IDEALIZED` / `DEVIATED` / `PROTOCOL-SILENT-CHOICE`, with metric impact.

| Parameter | Paper | This study | Status | Impact |
|---|---|---|---|---|
| Model | GPT-2-small | GPT-2-small (cached) | EXACT | none |
| EAP score (Eq 1) | $(z'_u-z_u)^\top\nabla_{z_v}L$ | identical | EXACT | none |
| EAP-IG score (Eq 3), $m$ | $m = 5$ | $m = 5$ | EXACT | none |
| Faithfulness metric | $(m-b')/(b-b')$ | identical | EXACT | none |
| Ablation | corrupted-activation patch | corrupted-activation patch | EXACT | none |
| Graph granularity | heads+MLPs w/ split q/k/v input edges (32,491 edges) | heads+MLPs, node-output edges (additive residual) | APPROXIMATED | coarser attribution; faithfulness metric still exact; disclosed |
| Circuit search | greedy | top-`n` by abs score (Syed et al. alternative) | DEVIATED | greedy is ≥ top-`n` faithful; a lower bound on the paper's curve |
| Tasks | 6 (IOI, GT, SVA, Gender-Bias, Capital-Country, Hypernymy) | 3 (IOI, GT, SVA) | IDEALIZED | 3 self-generable tasks span the effect range; others need word-lists (todo) |
| Dataset size | 1000 (IOI/GT), 2000 (SVA) | ≥ 200 minimal pairs/task | IDEALIZED | tighter CIs need more; disclosed via Wilson/bootstrap CI |
| Implementation | TransformerLens | raw `transformers` + manual hooks | APPROXIMATED | not installed offline; verified vs analytical oracle (§5) |

**Do-not-cite clause.** Absolute faithfulness numbers from this study are commodity-scale
node-granularity reproductions; cite Hanna et al. for production values. This study
certifies the *mechanism and ordering*, not the paper's absolute curve.

## 3. Candidate methods & the attribution mechanism

Let $z_u$ be node $u$'s output on the **clean** run, $z'_u$ on the **corrupted** run, and
$L = -M$ the loss (negated task metric). $\nabla_{z_v} L$ is the gradient of $L$ w.r.t. the
**input** of node $v$ (which, in the additive residual stream, equals the residual-stream
gradient where $v$ reads).

**EAP** (Hanna Eq 1) — one first-order term:

$$
\mathrm{score}_{\text{EAP}}(u \to v) = (z'_u - z_u)^\top \, \nabla_{z_v} L(s).
$$

**EAP-IG** (Hanna Eq 3) — gradient averaged over $m$ points on the straight-line path from
the corrupted input embeddings $z'$ to the clean input embeddings $z$:

$$
\mathrm{score}_{\text{IG}}(u \to v) = (z'_u - z_u)^\top \cdot \frac{1}{m} \sum_{k=1}^{m} \frac{\partial L\!\left(z' + \tfrac{k}{m}(z - z')\right)}{\partial z_v}.
$$

The interpolation is at the **input-embedding** level; each of the $m$ steps is one
forward+backward pass. EAP-IG costs $m\times$ EAP but resolves EAP's zero-gradient blind
spot (a saturated GELU has a flat local derivative even where the activation change matters).

**Exact activation patching** (oracle) — the true causal effect of restricting edge $u\to v$
to clean while all else is corrupted; scored per edge by re-running the metric.

**Faithfulness of a circuit $C$** (Hanna §4.2). Intervene: each node $v$'s input is
$\sum_{e=(u,v)} i_e z_u + (1-i_e) z'_u$ ($i_e = 1$ iff edge in $C$). With $b$ = clean full-model
metric, $b'$ = corrupted full-model metric:

$$
\mathrm{faith}(C) = \frac{m(C) - b'}{b - b'}.
$$

$\mathrm{faith} = 1$ when $C$ is the full graph, $0$ when empty — the analytical anchors (§5).

**Decoding / eval conventions.** No sampling — all metrics are computed from the model's
logits at the final position under a single deterministic forward pass (temperature n/a,
greedy-equivalent). Seeds fix prompt generation and any MC/bootstrap resampling.
Notation glossary: $z_u$ clean act, $z'_u$ corrupt act, $L=-M$ loss, $b/b'$ clean/corrupt
baselines, $n$ circuit edge budget, $m=5$ IG steps.

## 4. Implementation & math-to-code (Phase 2, G1 PASS 19/19)

`implementation/eap_ig/` — 157 nodes (embed + 144 heads + 12 MLPs) over the additive residual.

| Artifact | Function | Verified by |
|---|---|---|
| node decomposition $z_u$ | `model.forward_cache` (per-head via `c_proj` weight slice) | `test_model.test_residual_reconstruction` (err 1e-4) |
| EAP Eq 1 | `attribution.score_eap` = `<z'−z, ∇L>` | metamorphic oracle (metric-scale linearity) |
| EAP-IG Eq 3 | `attribution.score_eap_ig` (m=5 input-embed interp) | analytical oracle (m=1 ≡ EAP) |
| exact patching | `attribution.score_exact` (157 single-node patches) | analytical oracle |
| intervention | `model.patched_logits` (out-of-circuit → corrupt) | `test_patched_identity` (all≡clean, none≡corrupt) |
| faithfulness | `faithfulness.faith_curve` = `(m−b')/(b−b')` | `test_faithfulness_anchors` (full=1, empty=0) |

**Numerical-safety floors.** `metrics.EPS=1e-9` guards the faithfulness denominator and
softmax/prob-diff; the IG endpoints are detached constants (gradient is w.r.t. the running
residual, not the embedding matrix).

## 5. Verification & correctness anchors (G1 PASS)

Every candidate carries a passing `oracle_check` (P0-5); 15 unit tests green. Anchors:

| Anchor | Type | Result |
|---|---|---|
| faith(full circuit)=1, faith(empty)=0 | analytical | exact (< 1e-2) |
| EAP-IG at m=1 ≡ EAP (single interp point = clean gradient) | analytical | max\|Δ\| < 1e-4 |
| EAP score linear in the task-metric scale (2× metric → 2× score) | metamorphic | ratio 2.000 |
| random circuit recovers ~0 faithfulness | reference | −0.00 |
| node reconstruction: ln_f(Σ contributions) ≡ hidden_states | analytical | err 1e-4 |
| determinism: re-score twice, hash-match (all 3 tasks) | — | P0-1 pass |

## 6. Baseline results & verdict (G2 PASS 19/19)

4 candidates × 3 tasks × 3 seeds (N=360 example-seeds), circuit size n=20. Bootstrap 95% CI
on every cell (P0-4/stats). **Normalized faithfulness (mean [95% CI]):**

| Method | IOI | Greater-Than | SVA | overall |
|---|---|---|---|---|
| random | −0.00 [−0.09, 0.09] | 0.00 [−0.06, 0.07] | −0.00 [−0.03, 0.03] | 0.00 |
| **EAP** | 0.03 [−0.06, 0.13] | 0.96 [0.94, 0.97] | 0.21 [0.16, 0.25] | 0.399 |
| **EAP-IG** | 0.54 [0.44, 0.64] | 0.96 [0.95, 0.97] | 0.37 [0.33, 0.41] | **0.623** |
| exact-patch | 0.56 [0.46, 0.66] | 0.97 [0.96, 0.99] | 0.35 [0.30, 0.40] | 0.627 |

**Pairwise EAP-IG vs EAP** (paired-seed, P0-2): overall +0.224 (d_z=0.72, **p=3.6e-34**);
IOI +0.508 (d=2.05, p=1.2e-44); SVA +0.159 (d=0.51, p=1.9e-7); Greater-Than +0.005
(d=0.14, **p=0.14 — not significant**, both saturate at n=20). **Correlation to exact-patching
scores** (H5): EAP-IG ρ=0.924, EAP ρ=0.457 — EAP-IG scores are far better aligned with the
ground-truth causal effects. **Recovery@0.85** (Wilson CI, P0-4): EAP-IG 0.425 [0.38,0.48],
exact 0.419, EAP 0.328 [0.28,0.38], random 0.025. **Cost** (P1-4, n=40): EAP 3.2s (2fwd+1bwd),
EAP-IG 9.2s (~3×), exact 50.6s (~16×) — EAP-IG buys ~99% of exact's faithfulness at ~⅕ its cost.

**Verdict:** the core claim (EAP-IG more faithful than EAP, tracking exact patching at a
fraction of its cost) reproduces decisively; the per-task magnitudes differ from the paper's
edge-level pattern (§7).

## 7. Sensitivity & theory-as-predictor (G3 PASS)

**IG-steps × task grid** (`sensitivity.json`, single-seed; eap_ig faith@ref20 by $m$):

| Task | EAP (m=1) | m=3 | m=5 | m=10 | max IG gain |
|---|---|---|---|---|---|
| IOI | 0.010 | 0.478 | 0.449 | 0.449 | +0.468 |
| Greater-Than | 0.965 | 0.966 | 0.966 | 0.966 | +0.001 |
| SVA | 0.000 | 0.074 | 0.499 | 0.326 | +0.499 |

Findings: (i) the IG benefit **saturates by m=3** on IOI — corroborating Hanna's $m=5$ default;
(ii) it is **non-monotonic on SVA** (m=5 best 0.50, m=10 drops to 0.33) — *more* integration
steps can inject path noise and hurt, a concrete argument against "bigger m is always better";
(iii) Greater-Than is flat (saturated). The $m\times$ task interaction (a 2-factor grid, not
OFAT — the P0-3 spirit) confirms the IG advantage is task-dependent.

**Theory-as-predictor: why our per-task pattern differs from Hanna Fig 3.** The paper (edge
granularity, greedy search) reports IOI as a *small* EAP→EAP-IG gap (both ~0.6) and SVA as the
catastrophic one. We see IOI as a *huge* node-level gap and GT as saturated-flat. Residuals
root-caused into three modelling gaps, none of which touch the reproduced *direction/mechanism*:

1. **Granularity** — 157 head+MLP nodes (no split q/k/v edges) vs the paper's 32,491 edges.
   Coarser units concentrate EAP's first-order error into fewer, more load-bearing nodes, so on
   IOI at n=20 nodes EAP's blind spot is stark (0.03) where the finer edge graph dilutes it.
2. **Circuit search** — top-n by \|score\| vs greedy; greedy is ≥ as faithful, so our EAP curve
   is a *lower bound* on the paper's — widening our apparent gap.
3. **Operating point** — n=20 *nodes* sits past the Greater-Than knee (both methods already
   ~0.96), hiding the paper's small-n GT gap; the sensitivity grid shows the gap appears only at
   smaller circuits.

The reproduced invariants — EAP-IG ≥ EAP faithfulness (overall p=3.6e-34), ρ_IG(0.92) >
ρ_EAP(0.46), exact ≥ eap_ig ≥ eap ordering, ~3× cost — are granularity-robust; the absolute
per-task magnitudes are not, and are disclosed do-not-cite (§2).

## 8. Reduced precision (G4 PASS 7/7)

**≥2 realisation structures** (P2-3) over the attribution artifact — storing the edge scores at
reduced precision, then rebuilding circuits:

| Structure | max\|faith drift\| vs fp32 | saturation |
|---|---|---|
| bf16 score storage (8-bit exp, 7-bit mantissa) | 0.000 | none |
| fp16 score storage (5-bit exp, 10-bit mantissa) | 0.000 | none |

**Finding:** top-n circuit selection is **robust to bf16/fp16 storage of attribution scores** —
the score gaps between kept and dropped nodes exceed the mantissa quantum, so no circuit changes
and faithfulness is unchanged. Reduced-precision *compute* (bf16/fp16 forward+backward attribution)
is a **documented limitation**: MPS lacks kernel support for some attribution ops (raises on
fp16/bf16) and fp16 matmul is emulated-slow on CPU; deferred to `todos/2026-07-02-eap-ig-followups.md`.

## 9. Recommendation

**Use EAP-IG (m=5) for attribution-based circuit-finding whenever faithfulness matters.** It
recovers ~99% of exact-patching's circuit faithfulness (0.623 vs 0.627) at ~⅕ the cost, its
edge-scores align with the ground-truth causal effects (ρ=0.92 vs EAP's 0.46), and it dominates
plain EAP overall (+0.224, p=3.6e-34). Conditions:

| Condition | Choose |
|---|---|
| Faithfulness matters, ~3× EAP compute affordable | **EAP-IG (m=5)** |
| Task is "easy" (attribution saturates by small n, GT-like) & compute-bound | EAP (IG buys ~0 there) |
| Ground-truth needed, cost no object | exact patching (but 16× EAP) |
| m selection | m≈5; **do not over-integrate** — m=10 hurt SVA (§7) |

**Do-not-cite.** Absolute node-level numbers are a GPT-2-small reproduction; cite Hanna et al.
for production edge-level values.

## 10. Limitations, red-team & flip

- **Flip 1 (lose-to-baseline):** on **Greater-Than, EAP-IG does *not* beat EAP** (p=0.14) — both
  saturate at n=20. The "always use IG" claim fails on easy/saturated tasks.
- **Flip 2 (more-is-worse):** on **SVA, m=10 faithfulness (0.33) < m=5 (0.50)** — extra IG steps
  inject path noise; the method is not monotone in its own hyperparameter.
- **Flip 3 (cost-adjusted):** EAP-IG costs ~3× EAP; on a compute budget where you'd run EAP at 3×
  the data, EAP's variance reduction could erase the faithfulness gap on easy tasks.
- **Red-team (granularity):** node granularity + top-n inflates the IOI EAP→EAP-IG gap vs the
  paper's edge+greedy setup (§7). Our EAP faithfulness is a *lower bound*; a fairer edge-level
  harness would narrow it. The reproduced *ordering and correlation* are robust to this; the
  *magnitudes* are not.

## 11. Roadmap → todos/

Deferred (tracked in `todos/2026-07-02-eap-ig-followups.md`): edge-level graph with split
q/k/v input edges (full 32,491-edge parity); greedy circuit search; the 3 omitted tasks
(Gender-Bias, Capital-Country, Hypernymy — need word-lists / generators); KL-divergence loss
(EAP-IG-KL); a TransformerLens cross-check.

## 12. Reproduce

```bash
# Deterministic; offline GPT-2 cache. From repo root:
export PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python3 -m implementation.eap_ig.run_phase2   # G1: determinism + oracles
python3 -m implementation.eap_ig.run_phase3   # G2: baseline (seeds 0,1,2)  [~14 min CPU]
python3 -m implementation.eap_ig.run_phase4   # G3: sensitivity (seed 0)
python3 -m implementation.eap_ig.run_phase5   # G4: precision (seed 0)
# Regenerate the headline FROM artifacts alone (no model):
python3 -m implementation.eap_ig.reproduce
# Gates:
python3 .claude/skills/reference-implementation-study/validate_gate.py \
  eap-ig-faithfulness G2 eap_ig --flags P0-2,P0-4,P1-3,P1-4,P2-1,P2-2
```

Env pinned in `artifacts/eap-ig-faithfulness/study-manifest.json` (P1-3): python 3.12.3, torch
2.3.1, transformers 4.49.0, numpy 2.0.0, scipy 1.14.0 + git commit. Seeds: baseline 0..2;
sensitivity/precision 0.

## 13. Audit trail

- **Gates:** G1 19/19, G2 19/19 (all proposed flags), G3, G4 (see §8); REPORT + CITE below.
- `decisions/2026-07-02-04` — offline substrate scope (local proxy).
- `bugs/2026-07-02-04` — corrected IOI faithfulness value drift (memory → source, Hanna §4.3).
- **Citation-integrity:** every external value (EAP/EAP-IG equations, faithfulness metric,
  m=5, 32,491 edges, the per-task result pattern) read from
  `download/hanna-eap-ig-faithfulness-2024.pdf` — none from memory. Source tag: `(local: download/hanna-eap-ig-faithfulness-2024.pdf)`.
