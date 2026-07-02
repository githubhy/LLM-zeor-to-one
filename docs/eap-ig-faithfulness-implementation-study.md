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

> **Status: Phases 1–3 pending compute.** Verdict line reserved — it will state the
> headline signed margin (EAP-IG − EAP normalized faithfulness at the small-`n`
> operating point) with its 95% CI, per task, on the first line once G2 lands.

Claims→evidence spine (filled per phase):

| Claim | Evidence artifact | Status |
|---|---|---|
| C1 EAP-IG ≥ EAP faithfulness at matched circuit size | §6 baseline curve + pairwise CI | pending |
| C2 gap is task-dependent (large SVA, ~0.1 GT, ≈0 IOI) | §6 per-task table | pending |
| C3 activation-patching is the oracle both approximate | §5 oracle + §6 ordering | pending |
| C4 EAP-IG scores correlate with exact patching better than EAP | §7 correlation | pending |

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

## 4. Implementation & math-to-code (Phase 2 — pending)

Module map, equation↔function table, numerical-safety floors. `implementation/eap_ig/`.

## 5. Verification & correctness anchors (G1 — pending)

Analytical anchors: `faith(full)=1`, `faith(empty)=0`; EAP = first-order limit of exact
patching as the corrupt→clean perturbation $\to 0$ (metamorphic: scaling $(z'-z)$ scales the
EAP score linearly); IG Riemann sum → exact path integral as $m\to\infty$. Reference anchor:
top EAP-IG edges on IOI include known name-mover heads (Wang et al.). Per-candidate
`oracle_check` (P0-5).

## 6. Baseline results & verdict (G2 — pending)

Per-task faithfulness curves; pairwise paired-seed significance (P0-2); Wilson/bootstrap CI
on every cell (P0-4); cost profiling (P1-4); margin-accounting table.

## 7. Sensitivity (G3 — pending)

Sweep $m$ (IG steps), $n$ (circuit size), ablation type, dataset size; global/variance SA (P0-3).

## 8. Reduced precision (G4 — pending)

fp32 → fp16/bf16 attribution-score stability; ≥2 quantization structures (P2-3).

## 9. Recommendation (Phase 6 — pending)

Reserved: one imperative verdict + conditions table + do-not-cite clause.

## 10. Limitations, red-team & flip (Phase 6 — pending)

## 11. Roadmap → todos/ (Phase 6 — pending)

Greedy circuit search; split q/k/v edge granularity; the 3 omitted tasks; TransformerLens
parity check.

## 12. Reproduce (Phase 6 — pending)

One-command recipe + env + seed map (deterministic, seeds 0..4).

## 13. Audit trail

- `decisions/2026-07-02-04` — offline substrate scope.
- `bugs/2026-07-02-04` — corrected IOI faithfulness value drift (memory → source).
- Citation-integrity: every external value read from `download/hanna-eap-ig-faithfulness-2024.pdf`.
