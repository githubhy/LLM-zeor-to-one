# Review — MI-Observable Coverage of the Tiny-Transformer Induction Plan

**Type:** coverage audit (read-only review; no plan edits landed).
**Plan audited:** `plans/2026-06-30-tiny-transformer-induction-study.md`.
**Date:** 2026-07-02.
**Method:** multi-agent Workflow `mi-observable-coverage-audit` (305 agents, ~14.7M tokens). 11 Sonnet readers extracted 227 raw MI observables from the `surveys/mechanistic-interpretability/` method-inventory + math appendices + `appendix-i`; an Opus pass canonicalized them to a **146-observable rubric**; every observable was pipelined through a Sonnet coverage-tag → **Opus adversarial verify** (which tried to overturn each tag and judged in-scope-gap vs legitimately-out-of-scope); an Opus synthesizer produced §§1–5 below.

## Reviewer's critical note (read this first)

The audit is well-calibrated — spot-checked against the plan text, it correctly
classifies items the plan *touches but does not instrument* as **partial** (not
false "missing"): K-composition (H8/§A.18), the IOI circuit + duplicate-token /
name-mover / S-inhibition heads (Phase-4b census + IOI stretch), grokking
progress measures (H7), circuit completeness/minimality. It also correctly
buckets SAE/dictionary-learning, steering/editing, and superposition
toy-models as **out-of-scope** (owned by other studies).

Treat the **12 amendment bundles** (§3), not the raw "63 in-scope gaps," as the
unit of work. Reviewer's priority ranking over the synthesizer's:

- **Load-bearing core (do first): Bundles A, B, C.** The plan currently
  validates circuits by *structural match to §A.9 + necessity-only zero/mean
  ablation*. It is missing the entire **activation/path-patching + circuit-metric
  apparatus** (clean/corrupt pairs, indirect/total effect, logit-difference,
  faithfulness/completeness/minimality, causal scrubbing) and the **layer-wise
  decode lens + full direct-logit-attribution** family. This is the field-standard
  toolkit and is exactly what the plan's own IOI stretch (line 127) silently
  presumes. This is the single biggest methodological hole.
- **Hardens an existing claim: Bundle F's self-repair / Hydra check.** The
  plan's H8 rests on *single-head* ablation deltas, which are only a **lower
  bound** on importance (backup heads + self-repair compensate). Without a
  self-repair measurement the ablation-delta magnitudes are systematically
  understated and possibly mis-attributed — so this bundle is not "extra
  coverage," it *validates H8's core methodology*.
- **Medium:** D (Q/V-composition scores), E (probing/steering/directional
  ablation), G (automated discovery — ACDC/EAP-IG, also the named
  `mechinterp-ris-handoff` candidate), I (grokking metric completion).
- **Lower / advanced:** H (DAS/IIA), J (privileged-basis + MLP-neuron), K
  (max-activating examples / auto-interp), L (greater-than circuit).

Several bundles (E, F, G, H, K auto-interp) must be **source-gated** — a
`source-fetch` pass before any external anchor is written (citation-integrity),
mirroring the existing H9 gate.

---

# Coverage Audit — MI Observables vs the Tiny-Transformer Induction Study Plan

Plan audited: `plans/2026-06-30-tiny-transformer-induction-study.md`
Observable set: 146 verified per-observable verdicts (adversarially checked).

## 1. Headline verdict

**No — the plan does not yet cover all MI observables, but this is expected and largely by design.** Of 146 observables: **20 covered, 21 partial, 105 missing**. Of the **126 non-covered**, the split is an even **63 in-scope gaps** (partial + missing that genuinely belong in this study and are cheaply measurable on its toy → mini-GPT-2 → GPT-2-small ladder) vs **63 legitimately out-of-scope** (a different methodology family — SAE/dictionary-learning, transcoders, steering/RepE, knowledge-editing, superposition toy-models — owned by other studies).

| Bucket | Count |
|---|---|
| Covered | 20 |
| Partial | 21 |
| Missing | 105 |
| — of non-covered: in-scope gaps | 63 (21 partial + 42 missing) |
| — of non-covered: legitimately out of scope | 63 (all missing) |

Bottom line: the plan is a **strong weight-space QK/OV circuit microscope** with excellent coverage of its core (attention patterns, QK/OV circuits, induction/prev-token heads, ablation-necessity, grokking, universality). Its systematic blind spots are the **restorative/attribution causal-intervention family**, the **layer-wise decode lens family**, **representation-level probing/steering**, the **GPT-2 head-zoo + IOI** completion, and **automated circuit discovery** — all in-scope and closable with a bounded set of Phase-4/4b amendments.

## 2. Coverage by category

| Category | Covered | Partial (in-scope) | Missing in-scope | Missing OOS |
|---|---|---|---|---|
| **Observational** | Attention-pattern analysis; Activation inspection; Weight/SVD; Attention pattern $A^h_{ij}$; Discrete-Fourier embedding; Key-frequency ID | Direct logit attribution; Matched-filter logit score | Linear probing; Logit lens; Tuned lens; Max-activating dataset examples; World-model/execution-state; MLP-neuron basis | Feature visualization; Syntax/AST; Error node |
| **Causal** | Ablation; Node (mean) ablation; Zero ablation | Activation patching; Noising patch; Path patching; Causal scrubbing; Excluded loss | Interventional/causal probe; Causal-tracing heatmap; Denoising patch; AtP; AtP*; DAS; Boundless DAS; Distributed interchange; Edge ablation; Resample ablation; Directional ablation; Self-repair/Hydra; LayerNorm rescaling; Anti-erasure neurons | Local replacement model; Critical-layer range |
| **Transformer-circuits** | Virtual weights; QK; OV; QK/OV factorization; OV copying table; Copying head; Named head classes; Induction head; Prev-token head | Residual decomposition; QK bigram table; K-composition; Duplicate-token; S-Inhibition; Name-Mover; IOI; Angle-addition | Direct-path bigram; Q-composition; V-composition; Copy-suppression/neg name-mover; Backup name-mover; Successor heads; Greater-than circuit | MLP-as-associative-memory; Docstring circuit |
| **Universality** | Phase change / induction-head formation; Universality / circuit transport | — | — | — |
| **Evaluation/Metrics** | — | Restricted loss; Progress measures; Grokking phases; Circuit completeness; Circuit minimality | Probe selectivity; Indirect effect (IE); Total effect (TE); Scrubbed loss; IIA; Logit-difference metric; Circuit faithfulness; Interpretability illusions | SAE loss-recovered; L0; recon-loss; Pareto; TopK scaling law; dead/dense latents; auto-interp score; SAEBench; RAVEL; tracr; edit-success-vs-localization; sequential-edit degradation; ReLU toy recon-loss |
| **Superposition** | — | Privileged vs non-privileged basis | Linear-representation hypothesis | Feature splitting/absorption; shrinkage; dark matter; superposition; polysemanticity; $D_i$; capacity; phase diagram; pairwise interference; interference; activation density; antipodal; regular-polytope |
| **Dictionary/Features** | — | — | — | **All 14** (SAE variants, transcoder, skip transcoder, crosscoder, CLT, relative decoder norm) |
| **Steering/Editing** | — | — | Activation steering (ActAdd); Weight-baked directional ablation (abliteration) | CAA; LAT; RepE (+reading/contrast vector); LoRRA; Refusal direction; ROME (+v*); MEMIT; SAE-feature steering; SAE-TS |
| **Automation** | — | — | AtP-EAP; EAP-IG; ACDC; Auto-interp NL explanation | Sparse feature circuits; Attribution graph |

Two categories are **fully covered** at the category level (Universality) or have no in-scope gaps beyond what is listed; two categories (**Dictionary/Features**, most of **Superposition** and **Steering/Editing**) are legitimately absent because they require methodology the plan deliberately does not build.

## 3. Genuine IN-SCOPE gaps, ranked

The 63 in-scope gaps collapse into 12 amendment bundles (many observables share one tooling addition). Ranked by leverage (how much true coverage each bundle buys per unit of new work), all feasible on the plan's existing TransformerLens `run_with_cache` + hook stack.

### A. Restorative / bidirectional activation patching + effect metrics — **7 gaps, highest leverage**
Covers: Activation patching (46, partial), Denoising/sufficiency patch (50), Noising/necessity patch (51, partial), Indirect effect IE (47), Total effect TE (48), Causal-tracing heatmap (49), Logit-difference metric (139).
**Why it matters:** The plan's entire causal toolkit is *destructive* zero/mean-patch head ablation (necessity only). It never runs the canonical clean/corrupt-pair protocol, never computes IE/TE or the logit-difference effect size, and never produces a per-site (layer × position) localization map — the workhorse methods of modern circuit analysis, and the exact tooling the IOI stretch (line 127) silently presumes.
**Amendment:** Turn the Phase-4 ICL causal-ablation battery (line 118) into a **bidirectional** battery. Construct clean (valid repeat) / corrupt (prefix-match broken) induction pairs; add (a) denoising patch (clean→corrupt, sufficiency), (b) noising patch (corrupt→clean, necessity), (c) `IE(s)=M(corrupt; a_s←clean)−M(corrupt)`, `TE=M(clean)−M(corrupt)`, and the patched-fraction-of-TE, (d) logit-diff = `logit(correct)−logit(incorrect)` as the effect size (exposes suppressing components; also makes the IOI stretch's metric concrete). New figures: per-site (layer × position) causal-tracing heatmap; TE-attribution bar. Mirror on Phase-4b GPT-2. Verification anchor: ties recovered-TE fraction to the existing H8 ablation-delta magnitude.

### B. Circuit-validation metrics (faithfulness / completeness / minimality) + scrubbing — **8 gaps**
Covers: Circuit faithfulness (140), Completeness (141, partial), Minimality (142, partial), Causal scrubbing (58, partial), Scrubbed loss (59), Resample ablation (67), Edge ablation (66), Path patching (52, partial).
**Why it matters:** H3/H8 assert an induction circuit but never quantify *how much* of the metric the isolated circuit recovers, whether it is complete (subset-K sweeps that catch backup components), or minimal (no dead nodes). These are the standard tests that separate a validated circuit claim from a plausible story.
**Amendment:** Add to H8 (toy rung; mirror Phase-4b): define `C = {L1 prev-token head, L2 induction head, K-composition edge}`; report **recovered = F(C)/F(M)** (keep-only-C, mean-ablate complement), the **completeness** subset-K delta-vs-delta test, and the **minimality** node-necessity sweep. Add **resample ablation** (reference-distribution substitution) and **edge/path patching** (isolate the prev-token→induction K-edge via a third forward pass) as the causal-scrubbing-grade tests, reporting the **scrubbed-loss gap** with CIs. New figures: faithfulness bar; completeness scatter (y=x); minimality node bar. Anchors: Wang et al. (IOI completeness/minimality), Heimersheim & Nanda (causal scrubbing).

### C. Layer-wise decode lens + per-component logit attribution — **6 gaps**
Covers: Logit lens (3), Tuned lens (4), Residual-stream decomposition (14, partial), Direct-path bigram $W_U W_E$ (16), Direct logit attribution — MLP/embedding scope (7, partial), QK bigram table $W_E^\top W_{QK} W_E$ (21, partial).
**Why it matters:** The plan reads $W_U W_{OV}$ (one head's OV path) but never decodes the residual stream layer-by-layer, never verifies the exact additive path-sum, never computes the direct-path bigram baseline the induction circuit must beat, and folds $W_E$ into neither the QK nor the direct path (so vocabulary-legibility is implicit in the small_a shorthand, not measured).
**Amendment:** Add a Phase-2/4b step using `cache.decompose_resid`/`accumulated_resid`/`logit_attrs`: (a) verify `x_final = embed + Σheads + ΣMLP` to float tolerance (new verification anchor beside Eq 11/12); (b) per-component DLA bar (heads + each MLP + embedding) with sum-reconstruction check; (c) logit lens (final LN + $W_U$ on each block's residual at the induction query position) + a **tuned-lens** affine translator minimizing KL-to-final; (d) the direct-path bigram $W_U W_E$ heatmap (bigram baseline that cannot solve induction); (e) the QK bigram table $W_E^\top W_Q^\top W_K W_E$ in vocab×vocab coords with a top-pair prefix-match check. Anchors: §A.1, §A.8, §A.9.

### D. Composition-score census (Q/K/V) — **3 gaps**
Covers: K-composition weight-space score (24, partial), Q-composition (25), V-composition (26).
**Why it matters:** The plan names K-composition and ablates its path, but never assembles the virtual weight $W_K^B W_{OV}^A$ or an Elhage-style composition score, and never instruments Q- or V-composition at all — so the §A.3/§A.18 composition story is one-legged and the ablation cannot disambiguate K- from Q-/V-composition.
**Amendment:** Add a per-ordered-head-pair composition-score battery to the Phase-2 tooling (line 102): Frobenius-normalized $\lVert W_{\{Q,K,V\}}^B W_{OV}^A\rVert_F$ scores per §A.3 Eq.5, surfaced in the H4b census as a "composition profile" statistic and as a composition-score heatmap; confirm the induction pair is K-composition-dominant. Extend to Phase-4b GPT-2 head pairs.

### E. Representation-level probing → steering → directional ablation — **8 gaps**
Covers: Linear probing (1), Probe selectivity (2), Interventional/causal probe (13), World-model/execution-state (11), Linear-representation hypothesis (109), Activation steering/ActAdd (119), Directional ablation (69), Weight-baked directional ablation/abliteration (127).
**Why it matters:** The plan is entirely weight-space; it never tests whether induction-relevant concepts are *linearly decodable* from the residual stream, never does the write-then-verify causal-probe test that separates causal from correlational representations, and never does the additive-steering (sufficiency) or direction-projection (necessity) interventions. These are canonical, cheap at GPT-2-small, and there is a natural in-study variable (the to-be-copied token / is-repeat state).
**Amendment:** Add a source-gated H10 (representation-level) on Phase-4b: (a) train L2-regularized linear probes on frozen residual stream for is-repeat / copied-token-identity / relative-offset, report accuracy-vs-layer with Wilson CIs, a **shuffled-label control-task selectivity** (Hewitt & Liang), overlaid on the H8 co-emergence framing; (b) **causal probe** — overwrite the decoded direction with $s'$, verify the argmax follows $s'$ (intervention-success rate, random-direction control); (c) **ActAdd steering** — difference-in-means direction added at inference, ICL-score-vs-coefficient curve; (d) **directional ablation** ($P=I-vv^\top$ at every layer) and **abliteration** (permanent rank-one orthogonalization of residual-writers) as the runtime-vs-weight-baked necessity complements. Anchors: §I.1, §I.7 Eq.19, §I.8, fundamentals §2.3. Explicitly scope OUT full SAE/dictionary decomposition (defer to the SAE-frontier study via a `todos/` entry).

### F. GPT-2 head-zoo completion + IOI promotion + self-repair — **11 gaps**
Covers: Duplicate-token (33, partial), S-Inhibition (34, partial), Name-Mover (35, partial), Copy-suppression/negative name-mover (36), Backup name-mover (37), Successor heads (38), IOI circuit (39, partial), Self-repair/Hydra (76), LayerNorm rescaling (77), Anti-erasure neurons (78), Interpretability illusions (143).
**Why it matters:** Phase-4b's census names duplicate-token / S-inhibition / name-mover as figure labels but pre-registers no scoring metric for them; IOI is only a STRETCH; and copy-suppression, backup name-movers, successor heads, and the whole self-repair/Hydra family (single-ablation faithfulness is only a *lower bound*) are absent — despite GPT-2-small being their canonical home and the plan already loading it.
**Amendment:** (1) Extend the H4b battery with scored metrics for **duplicate-token** (attention to earlier occurrence of the query token), **negative-OV-eigenvalue copy-suppression**, and an **ordinal successor score** ($W_U W_{OV}$ onto a shared ordinal direction). (2) **Promote IOI to committed H10** (7-class path-patching, IO−S logit-diff, ≥~85% recovery acceptance) using the Bundle-A patching tooling. (3) Add **self-repair H8b**: after ablating a located head, re-measure every surviving head's DLA contribution; report single- vs iterative-ablation effect (Hydra), decomposed into **LayerNorm-rescaling** (norm-shift artifact) vs **anti-erasure** (learned compensation) terms; detect **backup name-movers** in the IOI ablation. (4) Add **interpretability-illusion** cross-corpus validity: re-run the census on a second held-out distribution, report a role-flip matrix. Anchors: Wang et al. (IOI/backup), McGrath et al. (self-repair), §I.6 (successor), arXiv 2310.04625 (copy-suppression, source-fetch first).

### G. Automated circuit discovery — **5 gaps**
Covers: AtP (53), AtP* (54), EAP (55), EAP-IG (56), ACDC (57).
**Why it matters:** The plan hand-picks heads; it never runs a gradient-cheap all-sites attribution or automated edge-pruning validated against its own ground-truth circuit — and induction + IOI on GPT-2-small are the canonical validation tasks for exactly these methods.
**Amendment:** Add a Phase-4b step: compute **AtP**/**AtP*** (QK-recompute correction) scores, **EAP**/**EAP-IG** edge rankings, and run **ACDC** (KL-threshold reverse-topological pruning). Pre-register that all recover the manual §A.9/§A.20 induction K-edge (and IOI classes) up to gauge; validate each against the Bundle-A/H8 ablation deltas (rank correlation + faithfulness-vs-edge-count figure). Source-fetch the AtP*/EAP-IG/ACDC references before writing anchors.

### H. DAS / causal-abstraction — **4 gaps**
Covers: DAS (60), Boundless DAS (61), Distributed interchange intervention (62), IIA (63).
**Why it matters:** The plan's only rotation is the §A.4 gauge-*invariance* test — the opposite of DAS, which *learns* a rotation whose subspace realizes a causal variable. Distributed interchange interventions + IIA are the strongest linear-encoding test and run on a frozen model with a light gradient loop.
**Amendment:** Add H8c: learn an orthogonal rotation $R$ over the L2 induction-head write so a coordinate-subset carries the copied-token identity; interchange-swap from a source run; report **IIA-vs-subspace-dimension** vs raw-patch and random-rotation controls (boundless variant learns the dimension). Cross-check the recovered subspace against the hand-built A.9 OV-copy circuit (should agree up to gauge — ties to A.4).

### I. Grokking sub-study completion — **6 gaps**
Covers: Excluded loss (70, partial), Restricted loss (71, partial), Progress measures (72, partial), Grokking phases (73, partial), Angle-addition circuit (44, partial), Matched-filter logit score (45, partial).
**Why it matters:** H7 tracks only the §C.8 Fourier-concentration measure; it never computes the Nanda et al. **restricted/excluded-loss** progress measures, never separates the three grokking phases on train-vs-test loss, never verifies the **angle-addition trig identity** per key frequency, and never reads off the **matched-filter logit** $\sum_k\cos(\omega_k(a+b-c))$.
**Amendment:** Extend the §6 grokking sub-study (line 159) with steps (e)–(h): restricted/excluded loss overlaid on flat val-accuracy; three-phase (memorization / circuit-formation / cleanup) boundary detectors + weight-norm cleanup evidence vs the wd=0 control; per-frequency angle-addition verification (product-to-sum); matched-filter logit-vs-$c$ overlay verifying $\arg\max_c = a+b \bmod p$. Anchors: §B.3 Eq.3/Eq.4, §C.8, Nanda et al. [68].

### J. MLP-neuron / privileged basis — **2 gaps**
Covers: MLP-neuron post-nonlinearity privileged basis (28), Privileged vs non-privileged basis (27, partial).
**Why it matters:** The §A.4 gauge test targets the QK factorization gauge, not the residual-stream $O(d)$ rotation; the contrastive half — the elementwise GELU making the neuron basis privileged — is never measured, despite a +MLP variant existing.
**Amendment:** Add a two-panel test: (1) random $R\in O(d_{\text{model}})$ conjugating all weights leaves logits bit-identical (no privileged residual basis); (2) the same $R$ does NOT leave post-GELU activations invariant (kurtosis/selectivity in standard vs rotated basis). Anchors: §I.1, fundamentals §2.1, alongside the existing §A.4 gauge test.

### K. Data-space head/neuron interp — **2 gaps**
Covers: Max-activating dataset examples (10), Auto-interp NL explanation (136).
**Why it matters:** The head-dump predicts what a head *should* prefer analytically; the plan never runs a corpus to surface the actual top-activating fragments (the auto-interp substrate), closing the weight-space↔data-space loop.
**Amendment:** Add a Phase-4b step: run a held-out corpus, record top-k activating fragments per located head / sampled MLP neuron; validate against the head-dump prediction (H6 rider); optional STRETCH auto-interp (LLM-generated firing description + simulation score, OpenAI protocol), source-gated. SAE-feature auto-interp stays OOS.

### L. Greater-than circuit — **1 gap** (lowest priority)
Covers: Greater-than circuit (40).
**Why it matters:** A second GPT-2-small MLP-circuit that would broaden Phase-4b beyond attention-head classes, but needs MLP-circuit tooling the plan lacks.
**Amendment:** Optional Phase-4b STRETCH beside IOI: year-comparison probe, path-patch the start-year-copying heads + mid-layer MLP threshold, plot probability-of-valid-years. Flag as a genuine stretch (requires MLP-circuit tooling). Hanna et al. 2023.

## 4. Legitimately OUT-OF-SCOPE (63)

Grouped; each requires methodology/models/tasks the plan deliberately does not build. None warrants a plan amendment — at most a one-line scope-exclusion note and a cross-reference (and a `todos/` pointer where the corpus lacks any owner).

- **SAE / dictionary-learning family (Dictionary/Features + related metrics + superposition pathologies) — ~36 observables.** SAE and all variants (Gated, TopK, JumpReLU, BatchTopK, Matryoshka), transcoder/skip transcoder/crosscoder/CLT, relative decoder norm, feature directions/sparse code/monosemanticity, loss-recovered/L0/recon-loss/Pareto/joint-scaling-law, dead/dense latents, activation shrinkage, dark matter, feature splitting/absorption, sparse feature circuits, attribution graph, local replacement model, error node, auto-interp score, SAEBench. **Reason:** all require training sparse dictionaries / transcoders on activations — infrastructure a weight-space circuit study does not build. **Owned by:** the **SAE/dictionary-learning frontier reference-implementation-study** (method-inventory-dictionary §6, evaluation §10.3, appendix-i §I.3).
- **Superposition toy-model geometry — ~11 observables.** Superposition, polysemanticity, feature dimensionality $D_i$, capacity ($\Sigma D_i\approx m$), phase diagram, pairwise interference, interference $(m-1)/d\cdot p\cdot s$, activation density, antipodal pair, regular-polytope geometry, ReLU toy recon-loss. **Reason:** need a dedicated ReLU-autoencoder sparse-feature-recovery model with known feature basis — a different architecture/task. **Owned by:** the **appendix-B toy-models-of-superposition study** (appendix-b §B.1–B.3).
- **Steering / RepE / knowledge-editing — 12 observables.** CAA, LAT, RepE (+reading/contrast vector), LoRRA, refusal direction, ROME (+v*), MEMIT, critical-layer range, edit-success-vs-localization, sequential-edit degradation, SAE-feature steering, SAE-TS. **Reason:** need contrastive concept datasets / factual-recall tasks / instruction-tuned models / weight-editing pipelines this induction/ICL study has none of. **Owned by:** the **steering-and-editing method-inventory study** (method-inventory-steering-editing §7).
- **Vision / code-model / bespoke-benchmark observables — 4 observables.** Feature visualization (input-optimization; needs continuous input space), syntax/AST probing (needs a code model + corpus), docstring circuit (bespoke 4-layer ACDC benchmark), tracr-compiled ground-truth (validates automated discovery via RASP compile), RAVEL (entity-attribute disentanglement), MLP-as-associative-memory (fact-storage localization). **Reason:** distinct model families / tasks / benchmarks. **Owned by:** respective dedicated studies (ACDC/circuit-discovery-benchmark study; code-model probing study; disentanglement/SAE-frontier study).

## 5. Minimal amendment set

To truthfully claim **"covers all MI observables (with explicit scope exclusions)"**, land these edits — they close all 63 in-scope gaps and convert the 63 OOS items from silent absence to explicit, owned exclusions:

1. **Bidirectional patching + effect metrics (Bundle A)** — rewrite Phase-4 line 118 into a clean/corrupt denoising+noising battery; add IE, TE, logit-diff, and a (layer×position) causal-tracing heatmap. *[7 gaps]*
2. **Circuit-validation metrics (Bundle B)** — add faithfulness/completeness/minimality + causal-scrubbing (resample ablation, scrubbed loss) + edge/path patching to H8. *[8 gaps]*
3. **Decode-lens + full DLA (Bundle C)** — add logit lens, tuned lens, exact residual-decomposition check, per-component DLA, direct-path bigram $W_U W_E$, QK bigram table. *[6 gaps]*
4. **Composition-score census (Bundle D)** — add Q/K/V Frobenius composition scores to Phase-2 tooling + H4b. *[3 gaps]*
5. **Representation probing → steering → directional ablation (Bundle E, source-gated H10)** — probes + selectivity + causal probe + ActAdd + directional/weight-baked ablation; explicitly defer full SAE decomposition. *[8 gaps]*
6. **GPT-2 head-zoo + IOI promotion + self-repair (Bundle F)** — extend H4b battery (duplicate-token, copy-suppression, successor), promote IOI to committed H10, add self-repair/Hydra (LN-rescaling vs anti-erasure), add cross-corpus illusion check. *[11 gaps]*
7. **Automated discovery (Bundle G, Phase-4b)** — AtP/AtP*/EAP/EAP-IG/ACDC validated against the manual + ablation circuit. *[5 gaps]*
8. **DAS/IIA (Bundle H, H8c)** — learned-rotation interchange interventions + IIA-vs-dimension. *[4 gaps]*
9. **Grokking completion (Bundle I)** — add restricted/excluded loss, three-phase decomposition, angle-addition verification, matched-filter logit overlay to the §6 sub-study. *[6 gaps]*
10. **Privileged-basis + MLP-neuron test (Bundle J)** + **data-space interp (Bundle K)** — residual-rotation-vs-post-GELU test; max-activating dataset examples + optional auto-interp. *[4 gaps]*
11. **Explicit scope-exclusion paragraph in §6/§7** — one block naming the SAE/dictionary, superposition-toy-model, steering/editing, and code-model/bespoke-benchmark families as out of scope, each with its owning study and (where the corpus has no owner) a `todos/` pointer. *[converts 63 OOS to explicit exclusions]*
12. **Optional STRETCH (Bundle L)** — greater-than circuit, flagged as needing MLP-circuit tooling. *[1 gap]*

Items 1–10 + 12 are all realizable on the plan's existing TransformerLens `run_with_cache` + hook stack at toy and GPT-2-small scale with no new training and no SAE/dictionary infrastructure; item 11 is a documentation edit. Landing items 1–11 makes the full-coverage claim true; several bundles (E, F, G, H, and the auto-interp half of K) should be **source-gated** (source-fetch the AtP*/EAP-IG/ACDC/IOI/copy-suppression/self-repair references per citation-integrity before writing anchors), mirroring the existing H9 gating pattern.