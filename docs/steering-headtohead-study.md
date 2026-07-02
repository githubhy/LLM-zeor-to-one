# Steering Head-to-Head — Reference Implementation Study (Track A3)

**Study:** `steering-headtohead`  **Topic:** `implementation/steering/`
**Mode:** `proposed`. **Substrate:** GPT-2-small (cached), CPU — user-approved scaled
reproduction of the AxBench steering ranking (decision `2026-07-02-04`).
**Parent handoff:** `todos/2026-07-01-mechinterp-ris-handoff.md` (candidate 3).
**Primary source:** Wu et al., *AxBench* (steering) `(local: download/wu-axbench-2025.pdf)`;
CAA/diff-in-means `(local: download/rimsky-caa-2024.pdf)`, ActAdd `(local: download/turner-actadd-2023.pdf)`.

## 0. Executive summary

**Verdict (partial reproduction): naive SAE-feature clamping is the *worst* steering method —
reproducing AxBench's headline — but on GPT-2-small the prompting-vs-diff-in-means order is
*flipped* from AxBench, a metric-and-model-dependent divergence.** At matched coherence
(KL=0.445, prompting's budget): **diff_in_means +3.97 [3.78, 5.04] > prompting +1.30 [0.86, 1.78]
> sae_clamp −0.93 [−1.67, −0.19]** (bootstrap 95% CI over eval prompts; all non-overlapping).
SAE-clamp's CI is entirely negative (counterproductive at matched coherence). Root cause of the
prompting/diff-in-means flip in §7.

## 1. Problem, scope & candidates

Steer GPT-2-small toward positive sentiment; measure steering **success** vs **coherence cost**.
Concept = sentiment (positive vs negative), self-generated contrast text (offline). Candidates:

- **prompting** — prepend "Write something very positive and cheerful."
- **diff_in_means** — add α·(mean_pos − mean_neg) residual vector at layer 6 (CAA / ActAdd).
- **sae_clamp** — train a TopK SAE (k=32) on layer-6 activations, clamp the most concept-selective
  latent (feature #1841) to a value (reuses `implementation/sae_frontier`).

**Metrics.** success = Δ(log-prob of positive − negative sentiment tokens) at the next position;
coherence cost = KL(steered ‖ base) over the vocabulary. **Ranking at matched coherence** =
interpolate each swept method's success at prompting's KL budget.

**Hypothesis (AxBench):** prompting ≥ diff_in_means ≥ naive SAE-clamp at matched coherence.

## 2. Conformance

| Parameter | AxBench | This study | Status |
|---|---|---|---|
| Model | Gemma-2-2B/9B | GPT-2-small | IDEALIZED |
| Methods | prompt / diff-mean / SAE | identical set | EXACT |
| Concept | many (AxBench suite) | sentiment (1, self-gen) | IDEALIZED |
| Coherence | LLM-judge fluency | next-token KL vs base | DEVIATED (no judge offline) |
| Success | judge concept-rating | next-token sentiment-logprob Δ | DEVIATED (direction-aligned) |

Do-not-cite absolute numbers; certifies the *method comparison shape* under these metrics, not
AxBench's judge-based values.

## 3. Results

Ranking at matched coherence (KL=0.445), bootstrap **95% CI** over the 10 eval prompts:

| Method | success @ matched coherence | 95% CI | verdict |
|---|---|---|---|
| **diff_in_means** | **+3.97** | [3.78, 5.04] | best (this metric) |
| prompting | +1.30 | [0.86, 1.78] | middle |
| sae_clamp | −0.93 | [−1.67, −0.19] | **worst (counterproductive)** |

CIs are non-overlapping → the ordering is statistically clear. `sae_clamp < 0` means clamping the
concept latent at matched coherence *reduced* sentiment success — the naive single-feature clamp is
ineffective on GPT-2-small (feature-splitting / polysemanticity), reproducing AxBench's finding that
naive SAE steering underperforms. Full Pareto in `artifacts/steering-headtohead/baseline/`.

## 4. Verification & anchors

- `tests/steering/test_steering.py` (4 green, G1 PASS 7/7): α=0 ⇒ zero change (analytical anchor);
  diff-in-means raises success at a KL cost; per-prompt success array (bootstrap-ready); SAE-clamp
  setup returns a valid feature index.

## 5. Recommendation

**On a small, non-instruction-tuned model, prefer diff-in-means (CAA) over prompting for reliable
concept steering; avoid naive single-SAE-feature clamps** (worst here). The AxBench "prompting wins"
result is coherence-metric-dependent (judge-rated fluency), which this offline scaled study cannot
replicate — re-test on Gemma-2 with an LLM judge before generalising (todo).

## 6. Limitations & flip

- **Flip vs AxBench:** diff_in_means > prompting here, opposite to AxBench (§7).
- **Metric alignment:** the next-token success metric is aligned with the diff-in-means direction,
  structurally favouring it; a generation-level judge would be fairer.
- **Weak base model:** GPT-2-small (124M, no instruction tuning) follows prompts poorly, depressing
  prompting's score.

## 7. Root cause of the divergence

Three modelling gaps, none of which touch the reproduced *SAE-clamp-is-worst* result:
(1) success = next-token sentiment-logprob is **collinear with the diff-in-means steering
direction**, so diff-in-means scores highly almost by construction; (2) **coherence = KL**, not
judge-rated fluency — at high α diff-in-means degenerates into repeated positive tokens that a judge
would penalise but KL under-penalises; (3) **GPT-2-small ignores instructions**, so prompting is
weak here where AxBench's Gemma-2 follows them. The *SAE-clamp-is-worst* conclusion is robust to all
three (deferred: `todos/2026-07-02-steering-followups.md`).

## 8. Reproduce

```bash
export PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python3 -m implementation.steering.run_baseline      # Pareto + matched-coherence ranking
python3 -m pytest tests/steering/ -q                 # 4 tests, G1 anchors
```
Deterministic (seed 0). Env + git pinned in `artifacts/steering-headtohead/study-manifest.json`.

## 9. Audit trail

- `decisions/2026-07-02-04` — offline substrate scope (GPT-2 vs Gemma).
- Citation-integrity: AxBench ordering + method definitions read from the acquired PDFs
  (`download/wu-axbench-2025.pdf`, `rimsky-caa-2024.pdf`, `turner-actadd-2023.pdf`).
- Follow-ups: `todos/2026-07-02-steering-followups.md` (Gemma-2 + LLM-judge coherence + generation-level success).
