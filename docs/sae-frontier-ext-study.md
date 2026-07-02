# SAE Frontier — Adaptive-Count Extension Study (Track C)

**Study:** `sae-frontier-ext`  **Extends:** `docs/sae-frontier-implementation-study.md`
**Mode:** `proposed`; reuses the verified `implementation/sae_frontier/` base (SAE class, train,
metrics, synthetic oracle) unchanged.
**Parent handoff:** `todos/2026-07-02-sae-frontier-followups.md`.

## 0. Executive summary

**Verdict: the parent study's red-team prediction is *refuted* at commodity scale — the
adaptive-count SAEs (BatchTopK, Matryoshka) do NOT beat exact-k TopK on the fidelity–sparsity
frontier, on either sparse or dense synthetic activations.** Mean explained-variance gap vs TopK
at matched k∈{4,8,16} (3 seeds): BatchTopK −0.017 (sparse) / −0.019 (dense); Matryoshka −0.004 /
−0.003. TopK remains the recommendation. Secondary result: the **orthonormal shrinkage curve**
confirms the H2 mechanism (ReLU shrinks, threshold methods do not) and the new **AdaptiveJumpReLU**
is the closest-to-unbiased threshold method (ratio 1.09 vs plain JumpReLU 1.17).

## 1. Problem, scope & candidates

Three new candidates added (survey Appendix D method inventory), scored on the same
synthetic-oracle substrate (S1) and metric set (P2-1) as the parent study:

- **BatchTopK** (Bussmann 2024) — one threshold per batch (k·B total actives) → variable
  per-example sparsity.
- **Matryoshka** (Bussmann 2025) — nested-prefix reconstruction; early atoms carry coarse structure.
- **AdaptiveJumpReLU** — STE bandwidth = 0.5·std(pre) (data-adaptive; closes bug `2026-07-02-01`,
  where a fixed bandwidth left θ gradient-starved / bandwidth-conditional).

**Hypothesis (from the parent red-team, Sec. 10):** BatchTopK/Matryoshka beat exact-k TopK on
heavy-tailed / DENSE activations. Tested on two substrates: sparse (feature_prob=0.05) and dense
(0.25).

## 2. Conformance

| Parameter | Parent | This study | Status |
|---|---|---|---|
| Substrate | synthetic S1 + GPT-2 S2 | synthetic S1 (sparse + dense) + orthonormal | IDEALIZED (no S2 here; catalog extension) |
| Metrics | L0 / EV / MMCS / shrinkage | identical | EXACT |
| Base SAE / train | `saes.py` / `train.py` | reused unchanged | EXACT |
| Seeds | 5 | 3 | IDEALIZED (fewer; CIs wider) |

Do-not-cite absolute EV values (32-dim toy); the study certifies the *ordering* (TopK ≥ adaptive).

## 3. Results

**Head-to-head EV gap vs TopK** (mean over k∈{4,8,16}, 3 seeds; + = adaptive better):

| Substrate | BatchTopK − TopK | Matryoshka − TopK |
|---|---|---|
| sparse (fp=0.05) | −0.017 | −0.004 |
| dense (fp=0.25) | −0.019 | −0.003 |

Both are **negative on both substrates** — the red-team's "dense favours adaptive-count" prediction
does not hold here. Approximate **95% CI** on the 3-seed gap: BatchTopK−TopK dense = −0.019
[−0.023, −0.015] (**excludes 0 → significantly *worse***); Matryoshka−TopK dense = −0.003
[−0.007, +0.001] (**includes 0 → indistinguishable**). No adaptive-count variant's CI reaches a
positive gap on either substrate. Exact-k TopK's fixed budget is already near-optimal on this
oracle; BatchTopK's variable budget slightly hurts EV at matched mean-k, and Matryoshka's nested
loss buys interpretability structure, not frontier EV. Per-cell EV ± std (bootstrap-ready per-seed
values) in `artifacts/sae-frontier-ext/baseline/summary.json`.

**Orthonormal shrinkage curve (H2 mechanism, verification anchor).** Mean (SAE activation /
least-squares-optimal) over active features (<1 ⇒ shrinkage; ≈1 ⇒ unbiased):

| ReLU+L1 | TopK | JumpReLU | AdaptiveJumpReLU |
|---|---|---|---|
| 0.96 (shrinks) | 1.45 | 1.17 | **1.09** |

ReLU is the only method that shrinks below 1 (the survey Eq D-2 soft-threshold bias); threshold
methods do not shrink downward, and the adaptive-bandwidth variant is closest to unbiased. (Single
seed; the parent todo notes the empirical ratio is noisy — a fuller multi-seed curve remains open.)

## 4. Verification & anchors

- `tests/sae_frontier/test_ext.py` (4 tests, green): BatchTopK avg-L0≈k + variable per-example
  sparsity; Matryoshka's 3 nested-prefix losses; **bug 2026-07-02-01 regression** — θ is not
  gradient-starved (L0 drops 12.5→10.0, θ 0.11→0.14 under a stronger penalty at 1500 steps).
- Reuses the parent study's verified SAE base, oracle, and metrics (G1-anchored there).

## 5. Recommendation

**Keep TopK as the frontier recommendation** (parent study's verdict stands); BatchTopK/Matryoshka
do not improve EV at this scale — adopt Matryoshka only for its interpretability (nested structure),
not fidelity. Use **AdaptiveJumpReLU** over fixed-bandwidth JumpReLU when a learned threshold is
wanted (less bandwidth-conditional, closer to unbiased). Gemma-scale re-test of the adaptive-count
claim remains open (heavy-tailed real activations may still favour BatchTopK — untested here).

## 6. Reproduce

```bash
export PYTHONPATH=$PWD
python3 -m implementation.sae_frontier.run_ext          # frontier + orthonormal shrinkage
python3 -m pytest tests/sae_frontier/test_ext.py -q     # 4 tests incl. bug regression
```

Deterministic (seeds 0..2, steps 1200). Env + git pinned in
`artifacts/sae-frontier-ext/study-manifest.json`.

## 7. Audit trail

- `bugs/2026-07-02-01` — JumpReLU STE bandwidth (adaptive-bandwidth variant + regression test close it).
- `decisions/2026-07-02-04` — offline substrate scope; `todos/2026-07-02-sae-frontier-followups.md`
  (Gemma-scale port + widen-S2 remain open).
