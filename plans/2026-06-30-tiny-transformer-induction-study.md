# Plan — Tiny-Transformer Induction Study (reproduce & verify Appendix A)

**Status:** draft, awaiting review (do not implement until approved).
**Date:** 2026-06-30
**Slug:** tiny-transformer-induction-study
**Drives:** `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` (the QK/OV survey) → a `reference-implementation-study`.

## 1. Objective

Train a *very small* transformer from scratch, watch an **induction head emerge**, **reproduce its head dump**, and **verify Appendix A's QK/OV-circuit math empirically** — converting the derivations the survey already contains into hands-on intuition. The deliverable is understanding (a mechanism microscope), not a SOTA artifact.

Because induction heads are the canonical mechanism of **in-context learning (ICL)**, this doubles as an **ICL-mechanism microscope**: the in-context loss (the *ICL score*) switches on together with the head at the phase change (H8), ablating the head switches it back off (a causal, not just correlational, ICL claim), and a source-gated stretch (H9) reaches toward the deeper *forward-pass-as-optimizer* reading of ICL.

This is a **reproduction / mechanistic-interpretability** study, so the standard skill's "competing candidates" become **ablations** (depth, wrappers, seeds, task) and the "metrics" become **circuit-formation and theory-match** measures.

**Scaling the study to GPT-2 (the toy→real ladder).** The from-scratch toy is the foundation, not the whole study: it is the only rung with a *closed-form ground-truth circuit* (§A.9) to verify against and with *training dynamics* to watch (emergence, seed-permuted head roles). To reach a real model without a training-compute cliff, the study climbs a three-rung ladder — **toy (~0.17M, from scratch) → mini-GPT-2 (~10M, from scratch) → pretrained GPT-2 small (124M, weights loaded, not trained)** — verifying Appendix-A's QK/OV math at each rung and showing it *transfers* to real weights. Why 124M is loaded rather than trained (a laptop finishes a 124M run in weeks, which is not the emergence story we want) is worked out in [`wikis/laptop-scale-training-feasibility.md`](../wikis/laptop-scale-training-feasibility.md).

## 2. Pre-registered hypotheses (each = an Appendix-A claim to test)

| ID | Type | Claim | Appendix anchor |
|---|---|---|---|
| H1 | Directional | A 1-layer attention-only model cannot solve a synthetic induction task (no *prev* block); a 2-layer one can. | §A.18 |
| H2 | Quantitative | The 2-layer model forms an induction head whose attention concentrates the majority of its weight on the prefix-match position; the in-context loss (loss vs token position) drops at a visible phase change during training. | §A.9, §A.20, §A.11 |
| H3 | Quantitative | The trained head's circuits match the hand-built ones up to gauge: $M$ routes *own*→*prev* (prefix matching), $W_{OV}$ copies; the OV eigenvalues are predominantly positive (high copying score). | §A.9, §A.20, §A.8, §A.4 |
| H4 | Directional | Head→role assignment is seed-dependent: across seeds the induction-head *index* permutes while the circuit recurs. | §A.11 |
| H5 | Verification | The forward/loss path reproduces the math: logits $\mathbf{z}=W_U\mathbf{x}^{\text{(out)}}$, loss = next-token NLL (Eq 11), softmax-Jacobian (Eq 12) confirmed by gradient check. | §A.21, §A.11 |
| H6 | Directional | The QK/OV structure verified on the toy **transfers** to pretrained GPT-2 small: real induction heads exhibit previous-token QK matching and a positive-eigenvalue OV copying score, and the head dump reproduces on real weights. | §A.8, §A.9, §A.11 |
| H7 | Quantitative | On modular addition with weight decay, the toy **groks** (delayed generalization); the grokked circuit is the Fourier-multiplication algorithm ($M$/$W_{OV}$ sparse in the DFT basis), and a Fourier-concentration progress measure rises *before* the validation-accuracy jump; grokking slows/vanishes at weight decay 0. | §C.8 |
| H8 | Quantitative | **Mechanistic ICL.** The *ICL score* (the in-context loss's decrease with token position) turns on **at** the induction-head phase change (co-emergence: ICL-score-vs-step tracks induction-head-strength-vs-step), and it is *causally carried by the induction circuit* — ablating the layer-2 induction head, or the layer-1 previous-token head that feeds it (K-composition), collapses the ICL score, while a random-head control leaves it intact and a held-out-symbol / longer-context control confirms genuine in-context use rather than memorization. | §A.9, §A.18, §A.20, §A.11, [60] |
| H9 | Quantitative (source-gated) | **Algorithmic ICL.** On an in-context linear-regression task the model's per-step predictions track an explicit online learner (one or a few gradient-descent steps, or the closed-form ridge solution), the match tightening with depth and context length — the "forward pass as an online optimizer" reading, distinct from induction copying. **Gated on a `source-fetch` pass** (todo `icl-as-online-learning-intuition`) before any external claim is written. | post-fetch (§A.6/§A.16 contrast) |

Prefer Quantitative wherever a closed form exists (per `sim-report-completeness`): overlay the analytic prediction (e.g. rank-$\le d_k$ of $M$; $1/\sqrt{d_k}$ temperature) on the measured curve with residuals.

**Rung applicability.** H1–H4 (depth threshold, phase-change emergence, circuit-match-to-theory, seed-permutation) live on the *from-scratch* rungs (toy + mini-GPT-2), which alone have ground truth and training dynamics. H5 (forward/loss math) holds on every rung and gets a stronger check at the GPT-2 rung (logits match a reference implementation bit-close). H6 is the transfer claim, tested only at the pretrained-GPT-2 rung. H7 (grokking) is a separate toy-rung study on the modular-addition task — a second closed-form circuit, derived in §C.8 and scoped as the sub-study in §6. H8 (mechanistic ICL — co-emergence + causal ablation) rides on the from-scratch rungs and extends to the pretrained-GPT-2 rung via Phase 4b's real-ICL ablation. H9 (algorithmic ICL-as-optimization) is a source-gated stretch sub-study requiring a new in-context-regression task (§6).

## 3. Phase plan (maps to the `reference-implementation-study` gates)

### Phase 1 — Scenario (define task, model, metrics)
- **Primary task:** synthetic induction — random token sequences containing repeated subsequences; the model must predict the continuation of a repeat (the canonical induction probe). Ground truth is known, so the circuit is verifiable.
- **Secondary tasks (stretch):** modular addition (the grokking task, a known interpretable circuit) and a char-level corpus (tiny-shakespeare) as a "real-ish" sanity check.
- **Model (Appendix-A column convention, §A.1):** tiny — all dimensions pinned in the **configuration table** at the end of this phase (primary: $L=2$, $h=4$, $d=128$, $d_k=d_v=32$, $T=256$, $\lvert\mathcal{V}\rvert=64$). **Attention-only** for the induction study (the analyzable circuits setting of §A.8/§A.9); a **+MLP + Add & Norm** variant for realism — the block diagram below is drawn in the original *post-norm* "Add & Norm" style, while the modern *pre-norm* form (§A.19's "what a real layer adds") applies the norm before each sublayer (a config choice — see §8).
- **Metrics:** induction-task loss/accuracy; **in-context loss** (loss as a function of token position — the ICL score); **induction-head attention concentration**; **circuit-match-to-theory** ($M$/$W_{OV}$ vs the §A.9 hand-built circuits, OV copying score); **phase-change training step**; **ICL co-emergence** (ICL-score-vs-step overlaid on induction-head-strength-vs-step); **ICL-ablation delta** (drop in the ICL score when the induction / previous-token head is ablated, vs a random-head control).
- **Constraints:** laptop CPU or one small GPU; fully deterministic (seed everything); reproducible from one command.
- **Ablation grid:** {1-layer, 2-layer, 3-layer} × {attention-only, +MLP+LN} × {≥5 seeds}; plus a "no previous-token-head capacity" control.

**Concrete configuration (proposed defaults — pin at review).** Architecture, in the Appendix-A symbols of §A.13:

| Parameter | Symbol | Induction (primary) | +MLP/LN | Grokking (mod-add) | Char-level |
|---|---|---|---|---|---|
| layers | $L$ | 2 | 2 | 1 | 4 |
| heads | $h$ | 4 | 4 | 4 | 4 |
| model width | $d$ | 128 | 128 | 128 | 256 |
| head width | $d_k=d_v$ | 32 | 32 | 32 | 64 |
| FFN width | $d_{\text{ff}}$ | n/a (attn-only) | 512 | 512 | 1024 |
| vocab | $\lvert\mathcal{V}\rvert$ | 64 | 64 | 114 ($p=113$) | ~65 (chars) |
| context | $T$ | 256 | 256 | 3 | 256 |
| KV heads | $h_{kv}$ | 4 (MHA) | 4 | 4 | 4 |
| positional | — | learned abs | learned abs | learned abs | RoPE |
| ≈ params | $N$ | ~0.17M | ~0.43M | ~0.2M | ~3M |

Every column satisfies $d=h\,d_k$ (§A.10); $d_{\text{ff}}=4d$ where present. Training:

| Setting | Induction | Grokking | Char-level |
|---|---|---|---|
| optimizer | AdamW | AdamW | AdamW |
| learning rate | 1e-3 | 1e-3 | 3e-4 |
| betas | (0.9, 0.98) | (0.9, 0.98) | (0.9, 0.95) |
| weight decay | 0 | 1.0 (grokking needs it) | 0.1 |
| batch size | 256 | full-batch | 64 |
| steps | ~20k | ~3e5 | ~50k |
| dropout | 0 | 0 | 0.1 |
| precision | fp32 (int8/int4 in Phase 5) | fp32 | fp32 |
| seeds | 0–4 (≥5) | 0–4 | 0–2 |

All values are proposed defaults for review (§8); seed everything and store every config in JSON (artefact rules). These sit well inside the real-model ranges of §A.13 ($d$ 512→7168, $L$ 6→62, $h$ 8→56, $d_k$ 64/128) — deliberately one to two orders of magnitude smaller so the whole study runs on a laptop while keeping $d=h\,d_k$ and $d_k$ in the same regime.

**Three-rung toy→real ladder (model scale).** The configuration above is the *toy* rung; two further rungs climb toward a real model without a training-compute cliff (full accounting: [`wikis/laptop-scale-training-feasibility.md`](../wikis/laptop-scale-training-feasibility.md)):

| Rung | Model | Params | Vocab | Trained? | Role |
|---|---|---|---|---|---|
| 1 | Toy (attn-only / +MLP) | ~0.17–0.43M | 64 | from scratch | closed-form ground truth; watch emergence (H1–H4) |
| 2 | Mini-GPT-2 | ~10M | ~65–8k (small) | from scratch | real-ish LM on tiny-shakespeare; emergence at a GPT-2-like shape |
| 3 | GPT-2 small | 124M | 50,257 (BPE) | **pretrained (loaded)** | verify QK/OV + head-dump transfer on real weights (H5–H6) |

Rung 2 keeps a **small vocabulary on purpose**: at ~10M params GPT-2's 50,257-token embedding table would otherwise dominate the parameter budget (~19M for the table alone at width 384), leaving little for the attention circuits under study. Rung 3 is **loaded, never trained** — a 16 GB laptop needs ~3 weeks to train 124M from scratch, so the released weights are used for circuit verification instead.

**Architecture, drawn in the Figure C.1 style.** The model is redrawn as a three-panel zoom — *whole model → one decoder block → one attention head* — matching the toy-model anatomy figure of §C.1: light-alpha semantic-coloured boxes (blue = embedding, purple = attention, green = FFN, grey = LayerNorm/IO, amber = unembedding), thin forward arrows, and grey dashed **residual skips** into the "+" adds. It is decoder-only (masked self-attention, no encoder or cross-attention); the $h=4$ heads run in parallel and their writes are summed into the residual stream. Dimensions are the primary induction config from the table above. The modern **pre-norm** variant (§A.19) applies LayerNorm *before* each sublayer, and the attention-only induction MVP drops the FFN and its residual add.

![Three-panel zoom of the tiny transformer in the Figure C.1 style: (left) the whole model bottom-to-top — input tokens, embedding, decoder block times L, final LayerNorm, unembedding, softmax and loss; (middle) one decoder block — pre-norm LayerNorm, masked multi-head attention, residual add, LayerNorm, FFN, residual add; (right) one attention head — Q/K/V projections, scaled masked scores, row-wise softmax, value mix, and the concat-and-W_O write.](figures/tiny-transformer-anatomy.svg)

**Figure 1.** The induction-study model from the whole architecture down to one attention head, in the style of Figure C.1 (§C.1). *Left:* the whole model — token ids → embedding $\mathbf{h}^0=E[x]+P$ → decoder block $\times L$ → final LayerNorm → unembedding → softmax/loss. *Middle:* one decoder block — a pre-norm masked-attention sublayer and a pre-norm FFN sublayer, each wrapped in a residual add (the dashed skips). *Right:* one attention head — the two circuits $M=W_Q^{\top}W_K$ (QK, *where to look*) and $W_{OV}=W_O W_V$ (OV, *what to bring*), dissected in §A.2–A.10. Config: $L=2$, $h=4$, $d=128$, $d_k=d_v=32$, $d_{\text{ff}}=512$, $\lvert\mathcal{V}\rvert=64$, $T=256$. Regenerate via `plans/figures/tiny-transformer-anatomy.py`.

**Block → Appendix-A map.** Input Embedding + Positional Encoding and the residual stream → §A.1, §A.20 · Add & Norm (LayerNorm) and Feed Forward → §A.19, §C.2 · Masked Multi-Head Attention → §A.2–A.10 (circuits $M$/$W_{OV}$ §A.3/§A.4/§A.8, the $1/\sqrt{d_k}$ scale §A.7, softmax-as-posterior §A.16) · Linear + Softmax (the unembedding $W_U$ → logits → probabilities) → §A.21 (Eq 33), §A.16 · training loss → Eq 11, §A.11. Here $V=\lvert\mathcal{V}\rvert=64$.

**The attention head** is panel 3 of Figure 1: per head it forms the query/key/value projections, the scaled scores $S=\mathbf{q}^{\top}\mathbf{k}/\sqrt{d_k}$ under the causal mask, a row-wise softmax, and the value mix $\mathbf{o}=\sum_j A_{ij}\mathbf{v}_j$, then writes $\Delta\mathbf{x}$ through $W_O$.

The head's two **circuits** are the only observables: $M = W_Q^{\top}W_K$ (QK — *where to look*) and $W_{OV}=W_O W_V$ (OV — *what to bring*). The **MLP** sublayer is $\Delta x = W_{\text{out}}\,\mathrm{GELU}(W_{\text{in}}\,x)$ with $W_{\text{in}}:d\to d_{\text{ff}}$, $W_{\text{out}}:d_{\text{ff}}\to d$.

### Phase 2 — Implementation (Gate G1)
- **Reuse the repo's Appendix-C toy** (`appendix-c-toy-transformer` already derives forward/backward/Adam) as the math-faithful core; wrap it in a frozen-dataclass config with explicit seeds. **TransformerLens is a required dependency of the analysis path** — used for activation caching (`run_with_cache`), attention-pattern capture, and head ablation across *all* rungs (our trained toy models, loaded into a `HookedTransformer`, and the pretrained GPT-2 via `from_pretrained`). **The training loop stays strictly first-party** (the Appendix-C toy); TransformerLens never touches training, only analysis.
- **Circuit-extraction tooling (first-party):** compute per head $M=W_Q^\top W_K$ and $W_{OV}=W_O W_V$; their SVD/eigenvalues; a **head-dump generator** that reproduces the small_a-style table (`"Queries that prefer key"` = QK, `"Effect on logits"` = $W_U W_{OV}$) for *our* model — directly reusing the parser pattern from this session.
- **Tests (`tests/tiny-transformer/`):** finite-difference gradient check vs the Appendix-C backward math; **gauge-invariance test** (a random $\mathrm{GL}(d_k)$ reparam leaves attention bit-identical, §A.4); softmax-Jacobian identity (Eq 12); numerical-safety floors (softmax/log-sum-exp epsilons).
- **G1:** imports clean, all tests pass.

### Phase 3 — Baseline (Gate G2)
- Train 2-layer attention-only on the induction task across **≥5 seeds**. Record: final induction accuracy, the in-context loss-drop curve, the **phase-change step**, induction-head attention concentration — each with CIs (Wilson for rates, bootstrap for curves).
- **1-layer vs 2-layer** head-to-head (H1): the 1-layer should fail, the 2-layer succeed; margin-accounting table with CI on every cell.
- **Rung 2 — mini-GPT-2 (~10M) from scratch** on tiny-shakespeare (small vocab): confirm an induction head forms at a GPT-2-like architecture; reproduce the head dump; measure the in-context loss-drop. ≥3 seeds (the transfer bridge, not the ground-truth rung).
- **ICL co-emergence (H8):** record the ICL score (in-context loss vs token position) across training and overlay ICL-score-vs-step on induction-head-strength-vs-step; both should turn on together at the phase-change step (the "induction bump").
- **G2:** CI on every result; ≥5 seeds (3 minimum, 5 preferred).

### Phase 4 — Sensitivity (Gate G3)
- Sweeps: depth (1/2/3), head count, $d_k$, context length, learning rate, task difficulty (vocab size, repeat structure).
- **Seed-dependence of head→role (H4):** which head index becomes the induction head across seeds; show the role recurs, the index permutes.
- **Theory-as-predictor overlays:** the rank-$\le d_k$ singular-value cliff of $M$ (§A.8); the $1/\sqrt{d_k}$ softmax-temperature behavior (§A.7) — analytic prediction overlaid on measurement with residuals.
- **ICL causal-ablation battery (H8):** with TransformerLens hooks, ablate (zero- or mean-patch) the layer-2 induction head — the ICL score should collapse; ablate the layer-1 previous-token head that feeds it (K-composition, §A.18) — induction breaks, so the ICL score collapses too; a **random-head control** leaves the ICL score intact (specificity); a **generalization control** (held-out symbols / longer contexts / unseen repeats) confirms genuine in-context use, not memorization. Report the ICL-ablation delta with CIs.
- **G3.**

### Phase 4b — Real-scale transfer rung (pretrained GPT-2 small, Gate G3b)
- **Load** GPT-2 small (124M) weights via TransformerLens (`HookedTransformer.from_pretrained`); **do not train** (see the feasibility wiki). Verify the forward pass reproduces a reference implementation's logits bit-close (H5 at real scale).
- **Find the induction heads** empirically (the previous-token → induction-head composition path) — head indices are read out of the model at analysis time, never asserted from memory (citation-integrity). Reproduce the small_a-style head dump for the real heads.
- **Circuit-transfer check (H6):** for the identified heads, confirm the QK circuit $M$ concentrates weight on the previous-token / prefix-match position and the OV circuit $W_{OV}$ has predominantly positive eigenvalues (copying score), matching Appendix-A's structure up to gauge.
- **Real-scale ICL ablation (H8 at scale):** measure a real ICL score (the in-context loss's decrease with position on natural text, and/or a few-shot pattern-completion probe) at the GPT-2 rung, then ablate the *located* induction heads — the ICL score should degrade; a random-head control leaves it intact. This ties the ICL mechanism to real weights, extending H6's structural transfer to a causal ICL claim.
- **Stretch:** reproduce a second published circuit (IOI — name-mover / S-inhibition / duplicate-token head classes) as a broader transfer demonstration.
- **G3b:** induction heads located; QK/OV structure matches theory; forward-logit parity with the reference implementation; ablating the located induction heads degrades the real ICL score (random-head control intact).

### Phase 5 — Precision / Quantization (Gate G4, in scope)
- Quantize the trained tiny model to **int8 and int4** (post-training; per-tensor and per-channel weight quantization, against an fp32/bf16 baseline) and test whether the **induction circuit survives**: does the head dump still show the induction head, does the QK previous-token match hold, does the OV copying score stay positive? Report a **float-vs-low-bit knee table** (fp32 → bf16 → int8 → int4) with induction accuracy + copying-score CIs per cell (`sim-report-completeness` §8); saturation/clipping and outlier-channel checks. In scope for this study — not deferred.

### Phase 6 — Report (+ citation & cross-link gates)
- Consolidate per the 14-section `sim-report-completeness` spine: executive verdict; per-hypothesis PASS/FAIL/INCONCLUSIVE; **our model's head dump vs small_a vs the hand-built §A.9 circuit**; the phase-change figure; circuit-match-to-theory; the **mechanism-vs-scale caveat** (what a toy teaches and what it cannot — scaling laws, emergent abilities, systems/efficiency); red-team (where the toy misleads); theory-as-predictor overlays; one-command reproduce block; audit trail.
- **Citation gate:** run `citation-audit` (the induction-emergence / ICL phase-change claim traces to the survey's [60]; the head-dump methodology to [59]).
- **Cross-link sign-off:** `/cross-link` over the new study + any survey touch-ups.

## 4. Deliverables & layout

- `implementation/tiny-transformer/` — model, training loop, circuit-extraction, config dataclasses, `utils.py`.
- `artifacts/induction-tiny/` — per-phase: training traces, head dumps (JSON), figures; `study-manifest.json` (versioned iteration log).
- `reports/` — the Phase-6 report (conforms to `sim-report-completeness`).
- `tests/tiny-transformer/` — gradient check, gauge invariance, softmax-Jacobian.
- **Figures (each with a 4-section caption + numeric operating conditions per `figure-operating-conditions`):** induction phase-change (in-context loss vs step); head-dump heatmaps; $M$/$W_{OV}$ SVD spectra; in-context-loss-vs-position; 1-vs-2-layer comparison; seed-permutation of the induction-head index; the **ICL co-emergence** overlay (ICL-score-vs-step over induction-head-strength-vs-step); the **ICL-ablation delta** bar chart (induction vs previous-token vs random-head control).

## 5. Verification anchors (closed-form / published, per `sim-report-completeness` §5)
- **§A.9 / §A.20 hand-built circuits** — the closed-form target the trained $M$/$W_{OV}$ should approximate (up to gauge).
- **§A.4 gauge** — invariance test.
- **Eq 11 / Eq 12** — loss + softmax-Jacobian gradient check.
- **§A.7** — $1/\sqrt{d_k}$ temperature curve.
- **§A.8** — rank-$\le d_k$ singular-value cliff.
- **Published anchor:** induction-head emergence ↔ ICL phase change ([60]); head-dump methodology ([59]).

## 6. Scope / MVP vs stretch

- **MVP (target first):** **Rung 1** — 2-layer attention-only on synthetic induction, ≥5 seeds; head-dump generator; phase-change figure; circuit-match-to-§A.9; gradient + gauge tests (establishes H1–H3, H5, and H8's ICL co-emergence — the ICL causal-ablation battery lands in Phase 4). **Rung 3** — pretrained GPT-2 small: locate induction heads, reproduce the head dump, QK/OV transfer check (H6), and the real-scale ICL ablation (H8 at scale). Rung 3 is the "understand GPT-2" payoff and is cheap because nothing is trained.
- **Stretch:** **Rung 2** — mini-GPT-2 (~10M) from-scratch on tiny-shakespeare (the emergence bridge); the **grokking second-circuit sub-study** (modular addition; detailed below); the IOI circuit on GPT-2 small; Phase-5 quantization; H4 seed-permutation study at scale.

**Grokking second-circuit sub-study (H7).** Promote modular addition from a bare task to a defined study, run on the toy rung (config in the Phase-1 table: $p=113$, weight decay 1.0, full-batch): (a) confirm delayed generalization — train accuracy → 100% early, validation-accuracy plateau, then a late jump; (b) reverse-engineer the grokked circuit and verify it is the Fourier-multiplication algorithm derived in §C.8 (the embedding's DFT is sparse; $M$/$W_{OV}$ concentrate on the key frequencies); (c) track the Fourier-concentration progress measure of §C.8 and show it rises *before* the validation jump; (d) ablate weight decay to 0 and confirm grokking slows or vanishes (the §C.8 prediction). Deliverables: the grokking curve, the DFT-of-embedding figure, the progress-measure overlay. This yields a second closed-form circuit alongside induction and imports the progress-measure methodology into H2.

**ICL-as-implicit-optimization sub-study (H9, source-gated).** A second, deeper sense of in-context learning: the forward pass *implementing a learning algorithm* rather than copying by pattern-match. Add an in-context linear-regression task — sequences of (x, y) pairs drawn from a randomly sampled linear map, with the model asked to predict y for a fresh x — and probe whether its per-step predictions track an explicit online learner (one or a few gradient-descent steps, or the closed-form ridge solution), the match tightening as depth and context length grow. This is the *algorithmic* ICL reading, contrasted with the induction *detection* mechanism of §A.6/§A.16 (the "one head detects" vs "a stack optimizes" levels). **Prerequisite (hard gate):** a `source-fetch` pass on the ICL-as-gradient-descent literature — no external claim is written from memory (citation-integrity); tracked in todo `icl-as-online-learning-intuition`, which must close before H9 is executed. Deliverables (post-fetch): the in-context-regression loss-vs-example-count curve, and the model-vs-online-learner prediction overlay with residuals.

## 7. Risks & caveats
- **Toy ≠ scale** — headline caveat in the report; do not generalize toy findings to frontier behavior (scaling laws, emergent abilities, systems concerns are out of reach).
- **Phase change may be gradual** at tiny scale — measure the curve, don't assume a sharp knee.
- **Compute** — keep it laptop-feasible; cap model size and steps; everything seeded and deterministic (no wall-clock seeding, per `workflow.md`).
- **Determinism / data** — fixed RNG, stored configs, regenerable figures.

## 8. Open decisions for the reviewer
1. **Framework — RESOLVED (core per decision 2026-07-01-01; TransformerLens now required):** first-party core for *training* (reuse the Appendix-C toy) and for weight-space circuits ($M$, $W_{OV}$); **TransformerLens is a required dependency for the analysis path** — activation caching, attention-pattern capture, and ablation on our trained toy models *and* the pretrained-GPT-2 rung (`from_pretrained`, `run_with_cache`, per-head $W_Q/W_K/W_O/W_V$). Not optional.
2. **GPT-2 scope — RESOLVED (decision 2026-07-01-01):** *augment* (toy + GPT-2) via the three-rung ladder; GPT-2 small is **pretrained, not trained** (feasibility wiki); full 124M training reproduction is deferred (todo `2026-07-01-gpt2-training-reproduction`).
3. **Tasks:** induction MVP (rung 1) + pretrained GPT-2 (rung 3) as the base; mini-GPT-2 on tiny-shakespeare (rung 2) and grokking modular addition as stretch — confirm at review.
4. **Quantization (Phase 5) — RESOLVED: in scope.** int8 + int4 post-training quantization of the trained toy model; measure induction-circuit survival (head dump, QK match, OV copying score) with a float-vs-low-bit knee table + CIs (Gate G4 is now a required gate, not optional).
5. **Execution mode — RECOMMENDED: direct execution, structured by the `reference-implementation-study` phases/gates** (G1–G4 + REPORT + CITE); opt into a multi-agent workflow only for the parallelizable, non-compute stages — Phase-4 sensitivity authoring, the `sim-audit` multi-lens verification, and the Phase-6 report synthesis. *Rationale:* the dominant cost is **compute** (single-laptop training), which agent fan-out does not parallelize; the correctness-critical first-party training loop + finite-difference/gauge tests want tight sequential authoring behind the gates, not farming to parallel agents. Say "use a workflow" / "ultracode" to instead run the whole study multi-agent.

## 9. Refs
- Survey: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` (§A.1–A.21); `appendix-c-toy-transformer.md` §C.8 (grokking, first-principles derivation).
- Skill: `.claude/skills/reference-implementation-study/SKILL.md` (phases, gates).
- Rules: `sim-report-completeness.md`, `figure-operating-conditions.md`, `citation-integrity.md`, `cross-linking.md`, `workflow.md`.
- Feasibility: [`wikis/laptop-scale-training-feasibility.md`](../wikis/laptop-scale-training-feasibility.md) — why 124M is loaded not trained, and the toy→real ladder.
- Decisions: `decisions/2026-07-01-01-augment-tiny-transformer-study-with-gpt2-ladder.md`; `decisions/2026-07-01-03-fold-icl-inspection-into-tiny-transformer-plan.md` (this ICL amendment). Deferred: `todos/2026-07-01-gpt2-training-reproduction.md`; `todos/2026-06-28-icl-as-online-learning-intuition.md` (the H9 source-fetch hard gate).
- Session context: `prompts/2026-07-01-tiny-transformer-progressive-build.md` (this session); `prompts/2026-06-29-viewer-serve-launcher.md` (the head-dump parse + Appendix-A enrichment thread).
