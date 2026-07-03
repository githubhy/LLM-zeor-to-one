# Reproduction & Verification Study — The Induction Head, Built and Broken

**Study:** `induction-tiny` · **Skill:** `reference-implementation-study` (mode: original)
**Drives:** `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` (the QK/OV survey) and its plan `plans/2026-06-30-tiny-transformer-induction-study.md`.
**Date:** 2026-07-02/03 · **Host:** Windows, CPU-only (18 cores), no GPU.

---

## 0. Executive summary

**A 2-layer attention-only transformer trained from scratch forms an induction head at a sharp phase change (~step 470, 95% CI [450, 490]); a 1-layer model provably cannot (induction accuracy 0.982, CI [0.974, 0.986] vs 0.145, CI [0.143, 0.147]; gap 0.837 over a 0.0156 chance floor; 5 seeds each). The trained circuit's copy behaviour matches Appendix-A §A.9, the mechanism transfers to pretrained GPT-2 small — where ablating the located induction heads spikes in-context loss by +5.36 nats (CI [+5.29, +5.43]) versus +0.03 for a random-head control — and the circuit survives int8 quantization losslessly and int4 gracefully.**

This is a *mechanism microscope*, not a SOTA artifact: the deliverable is a verified, reproducible account of the induction mechanism from first principles, plus an honest map of what a toy can and cannot show.

| Claim | Evidence | § |
|---|---|---|
| 1-layer can't, 2-layer can (H1) | 5+5 seeds; 0.982 vs 0.145; 1L never forms a prev-token head | 6 |
| Induction head emerges at a phase change (H2) | in-context loss 4.47→0.14; phase-change step ~470 | 6 |
| Fwd/bwd/AdamW math correct (H5) | G1: finite-diff gradient check + gauge + softmax-Jacobian + residual reconstruction | 5 |
| Trained copy circuit matches §A.9 (H3) | E·W_OV·U diagonal: every source token's top prediction is itself | 6 |
| Mechanism transfers to GPT-2 (H6) | located heads = canonical 5.1/5.5/6.9/7.2/7.10; OV self-rank top ~1% | 6 |
| Induction heads causally carry ICL (H8) | ablation Δ+5.36 CI[+5.29,+5.43] vs control +0.03 | 6 |
| Circuit survives quantization | int8 lossless; int4 graceful (per-channel > per-tensor) | 8 |

**Do not cite** the toy-rung *magnitudes* as scale-invariant facts, and see §10 for load-bearing caveats (toy localization is weak; several extended hypotheses are deferred).

---

## 1. Problem, scope & descent

The survey's Appendix A derives the QK circuit `M = W_Qᵀ W_K` ("where to look") and the OV circuit `W_OV = W_O W_V` ("what to bring"), and §A.9/§A.18 build an induction head by hand as a two-layer circuit: a previous-token head (layer 0) writes "what preceded me" into the residual stream, and a copy head (layer 1) reads it to attend back to the earlier occurrence of the current token and copy what followed (K-composition). This study trains that circuit from scratch, watches it emerge, and verifies the survey's math empirically.

**Pre-registered hypotheses (plan §2).** H1 depth threshold; H2 emergence/phase-change; H3 circuit-match to §A.9; H4/H4b role census; H5 fwd/bwd math; H6 GPT-2 transfer; H7 grokking; H8 mechanistic ICL; H9 algorithmic ICL (source-gated); H10 causal attribution/patching; H11 decode-lens; H12 composition census; H13 representation probing; H14 self-repair; H15 automated discovery; H16 DAS/IIA; H17 privileged basis; H18 IOI; H19 illusion-robustness.

**Scope executed (this pass).** The MVP core — H1–H6, H8, H10–H14 — at the toy rung, plus H6/H8 at the pretrained-GPT-2 rung and a quantization study (Phase 5). H7, H9, H15–H19 and Rung 2 (mini-GPT-2) are **deferred** (§11) — H15/H16/H18/H19 to a GPU host, H7/H9 as their own sub-studies. Decisions `2026-07-02-03/04` record the coverage plan and the execution approach.

---

## 2. Task, dataset & protocol anchors

**Task — synthetic induction (`data.py::make_induction_batch`).** Each sequence is a random-length prefix followed by a repeated random block, so the **repeat offset varies per sequence** (block length is a hidden function of the random prefix). A fixed-relative-offset positional head therefore cannot copy the correct token; genuine content-matching induction is required. (An earlier fixed-offset version let a 1-layer positional head "solve" the task — bug `2026-07-02-04`, high; caught by the H1 sanity check and fixed.) At an induction query the target is the token after the earlier occurrence of the current token.

**Protocol-vs-eval conformance.** This is a bespoke reproduction task (no external benchmark to conform to), so the matrix is short:

| Parameter | Status | Note |
|---|---|---|
| Task construction | EXACT (self-defined) | variable-offset repeat; ground-truth attend position known |
| Decoding | n/a | teacher-forced next-token CE; no sampling |
| Train/eval separation | EXACT | fresh random batches; eval RNG offset 10000+seed; random tokens unmemorizable |
| Model scale | **IDEALIZED (reduced)** | n_ctx=64, 800 steps (CPU) vs the plan's n_ctx=256/20k — deferred (§11) |
| GPT-2 probe | EXACT (audit-hardened) | variable-offset repeated-random probe (not fixed-offset) |

**Published anchor.** GPT-2-small's induction heads (5.1/5.5/6.9/7.2/7.10) are the canonical set reported in the induction-heads literature (`download/olsson-induction-heads-2022.pdf`); this study **locates them empirically** (read out of the model, not asserted from memory) and finds exactly this set.

---

## 3. Task model, candidates & conventions

**Model.** TransformerLens `HookedTransformer` (standard, GPT-2-compatible; full hook/cache access = the uniform analysis path with the GPT-2 rung, per plan §8.1), trained by a first-party torch AdamW loop. The hand-derived fwd/bwd/AdamW *math* is verified by the numpy Appendix-C toy (H5 reference, gradient-check rel-err 1.6e-9); decision `2026-07-02-04`.

**Configuration (toy, `config.py::PRESETS['induction']`).**

| Symbol | Value | | Setting | Value |
|---|---|---|---|---|
| layers L | 2 (1 for the control) | | optimizer | AdamW (0.9, 0.98) |
| heads h | 4 | | lr / warmup | 1e-3 / 200 |
| d_model | 128 (= h·d_head, §A.10) | | batch / steps | 128 / 800 |
| d_head (d_k=d_v) | 32 | | weight decay | 0 |
| vocab | 64 (chance 1/64 = 0.0156) | | seeds | 0–4 (×5) |
| context | 64 | | precision | fp32 |

**Convention.** The survey uses the column convention `x' = W x` (so `M = W_Qᵀ W_K`); the code uses the equivalent row convention `h' = h W` (so the QK bilinear form on embeddings is `W_Q W_Kᵀ` and the OV map is `W_V W_O`). These are exact transposes — singular values and eigenvalues are identical — and the vocab-space tables are internally consistent (verified by the sim-audit `theory` lens).

---

## 4. Implementation & math-to-code

`implementation/tiny_transformer/`: `config.py` (frozen dataclasses), `data.py` (task), `utils.py` (seeding, Wilson/bootstrap CIs, named safety floors `EPS_SOFTMAX/LN/LOG`), `circuits.py` (weight-space extraction), `model.py` (builder + first-party train loop + metrics), `analysis.py` (Phase-4 observables), `run_phase{3,4,4b,5}.py` (phase drivers). Tests in `tests/tiny_transformer/test_core.py`.

| Survey object | Code |
|---|---|
| QK circuit `M`, rank ≤ d_head (§A.2/§A.8) | `circuits.qk_circuit`, `effective_rank` |
| OV circuit, copying score (§A.4/§A.9) | `circuits.ov_circuit`, `copying_score`, `copying_score_diag` |
| K/Q/V composition (§A.3/§A.18) | `circuits.composition_score` |
| head dump (§A.9) | `circuits.head_dump` (QK "queries that prefer key"; OV "effect on logits") |
| next-token NLL (Eq 11), softmax-Jacobian (Eq 12) | `model.masked_ce`; `test_softmax_jacobian` |
| residual path-sum (§A.1/§A.20) | `test_residual_reconstruction` |

---

## 5. Verification & sanity anchors

**G1 gate — 9/9 tests pass** (`tests/tiny_transformer/test_core.py`): autograd-vs-finite-difference gradient check (H5); QK & OV gauge invariance (§A.4); softmax-Jacobian identity (Eq 12); residual-decomposition reconstruction to float tolerance (H11, §A.1/§A.20); QK rank ≤ d_head (§A.8, algebraic); the variable-offset regression for bug `2026-07-02-04`; Wilson CI. The hand-derived-math reference (the numpy Appendix-C toy) independently gradient-checks at rel-err 1.6e-9.

**Published-baseline anchor.** The empirically-located GPT-2 induction heads coincide exactly with the literature's canonical set — an external validity check the study did not tune toward.

---

## 6. Baseline results & verdict (per-hypothesis, with CIs)

| H | Claim | Result (5 seeds; CI) | Verdict |
|---|---|---|---|
| **H1** | depth threshold | 2L 0.982 [0.974, 0.986] vs 1L 0.145 [0.143, 0.147]; gap 0.837 | **PASS** |
| **H2** | emergence / phase change | in-context loss 4.47→0.14; phase-change step ~470 [450, 490] | **PASS** |
| **H3** | copy circuit matches §A.9 | E·W_OV·U diagonal: top-1-self = 1.00 (every source token predicts itself); head dump reproduced | **PASS** (via the diagonal metric) |
| **H4b** | role census | induction set = all 4 L1 heads every seed; feeder heads in L0 | **PASS** (distributed — see §10) |
| **H5** | fwd/bwd/AdamW math | G1 gradient check + gauge + softmax-Jacobian + residual reconstruction | **PASS** |
| **H6** | GPT-2 transfer | located 5.5/6.9/7.10/5.1/7.2 (variable-offset probe); OV median-self-rank 511/50257 (top ~1%) | **PASS** |
| **H8** | mechanistic ICL (GPT-2) | ablate located heads: ICL loss Δ **+5.36** [+5.29, +5.43] vs random-head control +0.03 | **PASS** |
| **H10** | causal attribution / patching | ablate induction set → acc 0.015 (chance 0.0156); IE/TE 0.96 | **PASS (set-level; localization weak, §10)** |
| **H11** | decode-lens | correct-token rank drops sharply after the induction layer | **PASS** |
| **H13** | representation probing | is-repeat linearly decodable; control-task selectivity 0.29 (L0) → 0.32 (L1) | **PASS** |
| **H12** | composition census | K/Q/V normalized-Frobenius scores 0.088–0.094 ≈ 1/√d noise floor | **INCONCLUSIVE (null; §10)** |
| H7, H9, H15, H16, H17(+MLP), H18, H19 | grokking / algorithmic-ICL / automated-discovery / DAS / privileged-basis / IOI / illusion | — | **DEFERRED (§11)** |

The headline causal claim (H8) is anchored on the **non-reduced pretrained GPT-2**, so it does not inherit the toy's reduced-scale caveat.

---

## 7. Sensitivity & ablation

**Set-based patching (H10, toy).** Mean-ablating the 4-head induction set drives induction accuracy to chance (0.015 vs 0.0156); mean-ablating the L0 feeder set likewise collapses it (0.046) — the two-layer K-composition is necessary in both legs. Clean/corrupt denoising patching of the induction set recovers 96% of the total effect (IE/TE 0.96). A single induction head's ablation drops accuracy only 0.014 (vs 0.966 for the set) — induction is **distributed** across all four top-layer heads.

**Self-repair (H14) — reframed.** At h=4/L=2 the single-vs-set gap is real redundancy, but it is **argmax-margin robustness among parallel same-layer heads**, not the active downstream compensation of the Hydra effect (there is no layer below L1 to compensate). The genuine self-repair / backup-head test belongs at the GPT-2 rung and is deferred.

---

## 8. Quantization (Phase 5, G4)

Post-training weight-only quantization (fake-quant: quantize→dequantize weights, fp32 activations/accumulation) vs fp32, 5 seeds:

| Precision | ind_acc [CI] | induction score | copy-diag | survives |
|---|---|---|---|---|
| fp32 | 0.981 [0.973, 0.987] | 0.779 | 1.00 | ✅ |
| int8 per-tensor | 0.981 [0.972, 0.987] | 0.779 | 1.00 | ✅ (lossless) |
| int8 per-group | 0.981 [0.972, 0.987] | 0.779 | 1.00 | ✅ |
| int4 per-tensor | 0.931 [0.924, 0.937] | 0.664 | 1.00 | ✅ (degraded) |
| int4 per-group | 0.959 [0.950, 0.965] | 0.717 | 1.00 | ✅ |

**Knee:** int8 is lossless; the induction *mechanism* survives to int4 but accuracy and induction score measurably degrade (score 0.78→0.66 at int4 per-tensor), and per-group beats per-tensor at int4 — the expected outlier-channel story. Caveats (§10): `copy-diag` is saturated (no downward headroom); the PTQ is weight-only (under-counts real int4 inference error); "per-channel" is per-leading-axis (per-group), not per-output-channel.

---

## 9. Recommendation

**Use the two-layer attention-only induction task as the reference mechanism microscope for QK/OV-circuit teaching and for validating interpretability tooling** — it is CPU-cheap, has a closed-form ground-truth circuit (§A.9), emerges reproducibly at a sharp phase change, and its trained circuit and GPT-2 transfer are both verifiable. **Conditions:** report the *variable-offset* task (never fixed-offset — it admits a positional shortcut); treat single-head ablations as lower bounds (induction is distributed); anchor causal/specificity claims on the GPT-2 rung, not the toy. **Do-not-cite:** the toy magnitudes as scale-invariant; H12/rank-cliff/eigenvalue-copying as empirical confirmations (they are null / algebraic / at-chance respectively, §10).

---

## 10. Limitations, red-team & flip (sim-audit `tiny-transformer-sim-audit`, 6 lenses)

The adversarial audit surfaced these; the cheap fixes were applied, the rest are disclosed:

**Fixed (this pass).** (1) GPT-2 probe was fixed-offset (same confound class as bug `2026-07-02-04`) → now variable-offset. (2) 1-layer control was n=1 → now 5 seeds (CI [0.143, 0.147]). (3) doc drift (800 steps).

**Load-bearing caveats (disclosed, not fully resolved at the toy rung).**
- **H10 localization is weak at toy scale.** Ablating *either* the 4-head induction set *or* the 4-head feeder set collapses accuracy to chance — nothing is spared, so set-level necessity does not localize a specific head. The single-head "specificity control" is one head (not size-matched to the 4-head set) and drops accuracy slightly *more* than the top induction head. The strong, size-matched specificity evidence is the **GPT-2 H8 result** (5 located heads → +5.36 vs 5 random heads → +0.03), not the toy.
- **H12 composition is a null result**, not a partial one: the normalized-Frobenius K/Q/V scores (0.088–0.094) sit within ~1–2σ of the random-matrix floor (1/√d ≈ 0.0883); the K-vs-Q gap (~0.001) is noise. The report claims no K-composition dominance. (The K-composition *mechanism* is nonetheless demonstrated causally — ablating the L0 feeder set breaks induction, H10.)
- **The rank-cliff (§A.8) check is algebraic, not empirical**: `M = W_Q W_Kᵀ` has rank ≤ d_head by construction; random weights give the same ~30. It confirms the factorization, not a learned prediction.
- **OV eigenvalue copying is at chance** (~0.5 positive-real fraction, dominated by null-space noise) at both rungs. The genuine copy evidence is the **E·W_OV·U diagonal** (toy: top-1-self = 1.0; GPT-2: median-self-rank in the top ~1%), not the residual-basis eigenvalues.
- **"Self-repair" at the toy is argmax-margin redundancy among parallel heads**, not the Hydra effect.
- **Quantization survival rests on the acc/score knee**; `copy-diag` is saturated and the weight-only PTQ under-counts real int4 error.
- **Statistics are descriptive:** 5-seed percentile bootstrap CIs are anti-conservative and range-bounded; verdicts gate on point-estimate means (margins are large enough that none flip). The non-reduced GPT-2 causal anchor is the inferential headline.

**Flip conditions (where the toy would mislead).** If read as "one head does induction" (false — distributed); if the fixed-offset task were used (a 1-layer model would falsely "pass"); if toy localization/specificity were cited without the GPT-2 anchor.

---

## 11. Roadmap → `todos/`

Deferred, tracked in `todos/2026-07-02-tiny-transformer-gpu-host-rungs.md` (GPU host) and the plan's §6: **Rung 2** mini-GPT-2 from scratch; **full-scale Rung 1** (n_ctx=256/20k, ≥5 seeds); **H7** grokking sub-study (modular addition + Fourier circuit); **H9** algorithmic ICL (source-gated); **H15** automated discovery (ACDC/EAP/EAP-IG/AtP*); **H16** DAS/IIA; **H17** privileged-basis contrast on the +MLP variant; **H18** IOI; **H19** interpretability-illusion cross-corpus; the auto-interp source-fetch (Bundle K). The GPT-2 rung already gives the causal specificity these will sharpen.

---

## 12. Reproduce recipe & reproducibility appendix

**Environment.** Python 3.13, torch (CPU), transformer-lens, transformers, numpy, scikit-learn; no GPU; 18 cores. All seeds explicit; runs deterministic and resumable (skip-if-exists).

**One command per phase** (from repo root, `PYTHONPATH=implementation`):
```
python -m pytest tests/tiny_transformer -q                              # G1
python implementation/tiny_transformer/run_phase3.py 2:0 2:1 2:2        # G2 (chunks; then 2:3 2:4 1:0..1:4)
python implementation/tiny_transformer/run_phase3.py --aggregate
python implementation/tiny_transformer/run_phase4.py                    # G3 (toy observables)
python implementation/tiny_transformer/run_phase4b.py                   # G3b (GPT-2 transfer)
python implementation/tiny_transformer/run_phase5.py                    # G4 (quantization)
```
Raw results: `artifacts/induction-tiny/phase{3,4,4b,5}/*.json`; manifest `artifacts/induction-tiny/study-manifest.json`. Seeds: models 0–4; eval batch 12345; corrupt 777; bootstrap 0.

---

## 13. Audit trail

- **Bugs:** `2026-07-02-04` (fixed-offset positional shortcut, high, fixed).
- **Decisions:** `2026-07-02-03` (full MI-observable coverage amendments), `2026-07-02-04` (execution approach: torch model + numpy H5 reference; MVP scope).
- **Todos:** `2026-07-02-tiny-transformer-gpu-host-rungs` (deferred rungs).
- **Verification:** `tiny-transformer-sim-audit` workflow (6 adversarial lenses) — 0 flaws survive the fixes; all remaining findings disclosed in §10.
- **Citation integrity:** the only external anchors are the survey's own §A.9/§A.18 (derived in-repo) and the GPT-2 induction-head set (`olsson-induction-heads-2022`, acquired) — which this study *locates empirically* rather than asserting from memory. No external value is recalled.
