# Section Outline + Research Questions — Mechanistic Interpretability

Legend: **[MH]** must-have (blocks section) · **[NH]** nice-to-have (enriches).
Depth tiers (R-GOV): **H** headline · **LB** load-bearing · **C** catalog-only.

Coverage-gap (MAST specification) check applied: every taxonomy axis MI touches has a home
below; the LLM-method-taxonomy axes not central to MI (pretraining, serving, agents) are
out-of-scope by design and cross-linked, not silently dropped.

---

## order.json (proposed manifest)

```
index.md
executive-summary.md
introduction-and-scope.md
fundamentals.md
methodology-and-taxonomy.md
method-inventory-observational.md
method-inventory-causal.md
method-inventory-dictionary.md
method-inventory-steering-editing.md
method-inventory-automation.md
circuits-across-models.md
evaluation-and-metrics.md
comparison-and-tradeoffs.md
state-of-the-art-and-practice.md
applications.md
design-guidance.md
open-problems-and-roadmap.md
appendix-a-transformer-circuits-math.md
appendix-b-superposition.md
appendix-c-causal-interventions.md
appendix-d-sae-derivations.md
appendix-e-steering-and-editing-math.md
appendix-q-reader-questions.md
references.md
```
(The five `method-inventory-*` files are one logical §5 split for the file-split threshold;
merge/split finalised in Phase 4 by size.)

---

## 1. Executive summary
- [MH] What is the 60-second verdict: what MI can and cannot do today, and the single most
  important shift (circuits → features/SAEs → attribution graphs)?

## 2. Introduction & scope
- [MH] What precisely is "mechanistic" interpretability vs representational / behavioral /
  post-hoc XAI? What is the falsifiable-circuit claim?
- [MH] Why does it matter (safety, science-of-DL, debugging)? What are the field's origin
  points (Distill circuits → transformer circuits)?
- [NH] The sociology: which labs, why the recent acceleration.

## 3. Fundamentals (H)
- [MH] The transformer as a computational graph: residual stream as the central object;
  attention & MLP as **read/write** operations into a shared linear space (Elhage 2021).
- [MH] QK vs OV circuits; the decomposition of attention into where-to-move vs what-to-move;
  virtual weights / composition. (full derivation → Appendix A)
- [MH] The **linear representation hypothesis**: features as directions; superposition as
  the reason a $d$-dim space holds $\gg d$ features; privileged vs non-privileged basis;
  polysemanticity vs monosemanticity. (toy-model derivation → Appendix B)
- [MH] The MI epistemics: what counts as an *explanation*; faithfulness vs plausibility.
- [NH] Signal-processing analogies (matched filter / basis pursuit / overcomplete
  dictionaries) for the learner register.

## 4. Methodology & taxonomy
- [MH] The canonical MI loop: observe → hypothesize → **intervene** → validate. Why causal
  intervention is the load-bearing step (correlation-vs-causation, the probing critique).
- [MH] A 2-D taxonomy: (observational ↔ interventional) × (feature-level ↔ circuit-level ↔
  representation-level); where each method family lands.
- [NH] The "levels of analysis" framing (Marr) and how MI targets the algorithmic level.

## 5. Method inventory (R-CARD cards; split across 5 files)

### 5a. Observational methods (`method-inventory-observational.md`)
- [MH] **Linear probing** (LB) — diagnostic classifiers; what a probe does/does not license;
  the causal critique. Applied: BERT/GPT-2, "world models" probes (Othello-GPT).
- [MH] **Logit lens** (LB) & **Tuned lens** (LB, Belrose) — reading the residual stream
  through the unembedding; the affine-probe fix.
- [MH] **Attention-pattern & head analysis** (LB) — previous-token, induction, name-mover
  heads; how to read attention maps and their pitfalls (attention ≠ explanation).
- [NH] **Direct weight / SVD analysis** (C) — eigen/singular structure of OV & QK.
- [NH] **Feature visualization** (C) — the vision-model heritage (InceptionV1, Olah);
  `n/a` for LM-native worked example (image-space optimization).

### 5b. Causal / interventional methods (`method-inventory-causal.md`)
- [MH] **Activation patching / causal tracing** (H) — interchange interventions; denoising
  vs noising; clean/corrupt pairs; the logit-diff metric. (derivation → Appendix C)
- [MH] **Path patching** (LB, Wang IOI) — restricting the intervention to graph edges.
- [MH] **Attribution patching** (LB, Nanda/Syed) — the first-order Taylor approximation that
  makes patching scale; where the linear approximation breaks. (derivation → Appendix C)
- [MH] **Automated circuit discovery** (LB) — **ACDC** (Conmy) edge-pruning + **EAP** /
  EAP-IG (gradient-based).
- [LB] **Causal scrubbing** (LB, Redwood) — hypothesis-as-resampling validation.
- [LB] **Distributed Alignment Search (DAS)** (LB, Geiger) — learned interchange subspace.
- [NH] **Causal mediation analysis** (C) — Vig/Pearl framing, the statistical ancestor.

### 5c. Dictionary learning / features (`method-inventory-dictionary.md`)
- [MH] **Sparse autoencoders** (H) — the objective (reconstruction + L1), the monosemanticity
  claim (Bricken "Towards Monosemanticity"), scaling to a frontier model (Templeton "Scaling
  Monosemanticity", Claude 3 Sonnet). (derivation → Appendix D)
- [MH] SAE architecture variants (LB, each a nested card): **Gated** (Rajamanoharan),
  **TopK** (Gao/OpenAI), **JumpReLU** (Rajamanoharan); (C): BatchTopK, Matryoshka, p-annealing.
- [MH] **Transcoders** (LB) — sparse MLP replacement; skip transcoders.
- [MH] **Crosscoders** (LB, Anthropic) — features shared across layers / across models.
- [NH] Classic **dictionary learning / sparse coding** (C) — the sparse-coding ancestor (the
  SP analogy home: basis pursuit / matching pursuit / overcomplete dictionaries).

### 5d. Steering & editing (`method-inventory-steering-editing.md`)
- [MH] **Activation steering / steering vectors** (LB) — ActAdd, Contrastive Activation
  Addition (CAA); adding a direction at inference.
- [MH] **Representation engineering (RepE)** (LB, Zou) — reading + controlling
  representations top-down; the **refusal direction** (Arditi) as the crisp case study.
- [MH] **Model editing** (LB) — **ROME** rank-one update + **MEMIT** mass-editing; locate-
  then-edit; the causal-tracing → edit bridge. (derivation → Appendix E)
- [NH] SAE-feature steering (C) — clamping SAE features ("Golden Gate Claude").

### 5e. Automation & scaling (`method-inventory-automation.md`)
- [MH] **Automated interpretability** (LB, Bills/OpenAI) — LLMs labeling neurons/features;
  auto-interp scoring for SAE features.
- [MH] **Sparse feature circuits** (LB, Marks) — circuits built over SAE features not neurons.
- [MH] **Circuit tracing / attribution graphs** (H, Anthropic 2025 "Biology of an LLM" +
  "Circuit Tracing") — cross-layer transcoders → attribution graphs; the current frontier.
- [NH] Scalable-oversight framing: interpretability agents.

## 6. Circuits across models (the "various models" spine)
- [MH] **Induction heads** (Olsson) — toy → GPT-2 → larger; the in-context-learning bump.
- [MH] **IOI circuit** (Wang) — GPT-2 small, the canonical end-to-end circuit.
- [MH] **Grokking / modular addition** (Nanda, "Progress measures") — a *fully* reverse-
  engineered algorithm in a toy transformer; the Fourier-multiplication mechanism (SP-native).
- [MH] **Factual recall** (Meng ROME) — GPT-2 XL / GPT-J; MLP-as-key-value-memory.
- [MH] **Scaling monosemanticity** (Templeton) — Claude 3 Sonnet features (safety-relevant).
- [NH] **Greater-than**, **docstring**, **Othello-GPT world model** (C) — breadth.
- [MH cross-cutting] **Universality & transport**: does a method/circuit survive GPT-2 →
  Gemma 2 → frontier scale? Where it does and does not.

## 7. Evaluation & metrics
- [MH] What makes an interpretation *good*: faithfulness, completeness, minimality; the
  interpretability-illusion failure mode (Bolukbasi).
- [MH] **SAE metrics** — reconstruction (MSE), sparsity (L0), downstream **loss recovered**
  / KL, auto-interp interpretability score; pathologies: **feature splitting**, **feature
  absorption**, dead features, "dark matter"/shrinkage.
- [MH] **Causal metrics** — logit-difference recovered, faithfulness curves, minimality.
- [MH] Benchmarks — **SAEBench**, **RAVEL**, IOI-style circuit benchmarks; contamination /
  cherry-picking hazards. (Figures/tables gated by figure-operating-conditions rule.)

## 8. Comparison & tradeoffs (R-SURVEY §7 master matrix)
- [MH] Master comparison matrix: rows = every inventory method; columns = declared axes
  (causal faithfulness · scalability · automation · model-access needed · compute cost ·
  supervision/data needed · granularity) + an **assumptions & cost** column.
- [MH] Selection / decision table: "for question X, use method Y, not Z, because …".

## 9. State of the art & practice (R-SURVEY §8)
- [MH] What frontier labs actually do now (Anthropic / DeepMind / OpenAI / EleutherAI);
  per-stage dominant-practice map (find features → build circuits → validate → apply).
- [MH] The **SAE debate** (2024–25): do SAEs deliver? matching-pursuit/e2e critiques,
  "are SAEs the right abstraction?", the shift toward transcoders/attribution graphs.
- [MH] Quantitative SOTA results table (published SAEs: Gemma Scope, OpenAI GPT-4 SAEs,
  Claude features) with eval conditions + source tags + normalization notes.

## 10. Applications
- [MH] **Safety**: deception / sandbagging / sleeper-agent probes, refusal control,
  monitoring; the case for MI as a safety tool + its current limits.
- [MH] **Model editing / knowledge update**; **unlearning**; **debugging & bias**.
- [NH] Steering products ("Golden Gate Claude"), feature-based classifiers.

## 11. Design guidance
- [MH] A decision framework: given a question (is feature F represented? does head H cause
  behavior B? what algorithm computes task T?), which method, in which order, at what cost.
- [NH] Practical pitfalls checklist (interpretability illusions, backup/self-repair,
  distribution of the corrupt prompt, metric choice).

## 12. Open problems & roadmap (R-SURVEY §10 + RIS handoff)
- [MH] Named open problems (superposition/feature geometry, missing "dark matter",
  circuit completeness at scale, evaluation ground-truth, automation faithfulness).
- [MH] Reference-implementation handoff: study-ready methods with baseline-to-beat +
  predicted margin + hypothesis (e.g. TopK vs JumpReLU SAE on the fidelity–sparsity frontier
  for a fixed model; attribution patching vs exact patching faithfulness). → file `todos/`.

## Appendices (heavy derivations, H)
- **A** — Transformer circuits math: residual stream linear algebra, QK/OV factoring,
  virtual weights, attention-head composition (Q/K/V-composition), the free-form vs
  privileged basis argument.
- **B** — Superposition: the ReLU-output toy model, feature importance/sparsity phase
  diagram, geometry (antipodal pairs → polytopes), capacity, the SP dictionary analogy.
- **C** — Causal interventions: interchange-intervention formalism, the patching metric
  family, the attribution-patching first-order derivation + error term.
- **D** — SAE derivations: the loss, ReLU/Gated/TopK/JumpReLU objectives and their gradients,
  the L0-vs-fidelity Pareto frontier, shrinkage/bias of L1, auto-interp scoring math.
- **E** — Steering & editing math: steering-vector derivation (difference-in-means),
  ROME's constrained rank-one update (least-squares closed form) + MEMIT extension.
- **Q** — Reader's questions Q&A (survey-explainer-fold seeds).

---

## Research questions dispatched to Phase-3 evidence agents (grouped, ≤3–4 Q/agent, wide)

Clusters (each → one hardened evidence agent, file-first `_scratch/<id>.md`, exact-source-first):
1. **Foundations** — residual-stream framework; QK/OV; linear representation hypothesis. (3Q)
2. **Superposition** — toy models; feature geometry; polysemanticity; capacity. (3Q)
3. **Probing & lenses** — linear probes + critique; logit lens; tuned lens; Othello-GPT. (4Q)
4. **Patching** — activation/causal tracing; path patching; attribution patching. (3Q)
5. **Automated circuits** — ACDC; EAP/EAP-IG; causal scrubbing; DAS. (4Q)
6. **SAEs core** — objective + Towards/Scaling Monosemanticity; metrics (L0/loss-recovered). (3Q)
7. **SAE variants** — Gated; TopK; JumpReLU; BatchTopK/Matryoshka; feature splitting/absorption. (4Q)
8. **Transcoders/crosscoders/attribution graphs** — Biology-of-LLM, circuit tracing. (3Q)
9. **Steering & RepE** — ActAdd/CAA; RepE; refusal direction; SAE steering. (4Q)
10. **Model editing** — ROME; MEMIT; knowledge editing eval; locate-then-edit critique. (3Q)
11. **Circuits case studies** — induction heads; IOI; grokking/modular addition; greater-than. (4Q)
12. **Evaluation** — faithfulness/completeness; SAEBench; RAVEL; interpretability illusions. (3Q)
13. **SOTA & debate** — lab practice; SAE debate 2024–25; Gemma Scope/OpenAI SAEs. (3Q)
14. **Applications & safety** — deception/sleeper-agent probes; unlearning; steering products. (3Q)

~14 clusters × ~3–4 Q = ~45 research questions. All must-have questions above are represented
(coverage-gap check: PASS). Nice-to-have questions absorbed into the nearest cluster.
