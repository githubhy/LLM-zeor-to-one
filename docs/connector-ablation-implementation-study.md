# Connector Ablation — Reference Implementation Study (Track B2)

**Study:** `connector-ablation`  **Topic:** `implementation/connector/`
**Mode:** `proposed`. **Substrate:** frozen SmolVLM-256M SigLIP vision encoder + a small frozen
text decoder; **trainable connector only** (decision `2026-07-02-04`).
**Parent handoff:** `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (candidate 2);
survey `surveys/multimodal-llms/architecture.md` §3.3.
**Sources:** MLP projector `(local: download/liu-llava-1.5-2023.pdf)`; Q-Former `(local:
download/*blip*)` — **read before citing specifics**.

## 0. Executive summary

**Verdict (null result with a direction-consistent trace): connector token budget `q` is NOT the
bottleneck at this toy scale — both an MLP-pool projector and a Q-Former bridge reach ~100% on both
the coarse (colour) and detail (left/right colour-binding) axes at every budget q∈{1,4,16,64},
including q=1.** The one §3.3-consistent signal: on the **detail (binding)** axis the learned
Q-Former holds **1.00 at all q** while the fixed avg-pool MLP dips to **0.992 at low q** — i.e.
learned pooling ≥ avg-pool for spatial detail, but the effect is near-noise because a 4-colour /
16-combo synthetic task lacks the fine detail that makes budget matter. **The survey §3.3
fidelity-vs-budget tradeoff genuinely requires detail-heavy real benchmarks (DocVQA/TextVQA)** —
deferred (`todos/2026-07-02-connector-ablation.md`). Do-not-cite absolute numbers (§2).

## 1. Problem, scope & candidates

The connector maps frozen vision features → the LLM token space. Two families (survey §3.3):

- **MLP projector** (LLaVA-1.5): a 2-layer MLP maps *each* patch feature to one LLM token — high
  fidelity, token count = #patches (expensive).
- **Q-Former bridge** (BLIP-2): `q` learnable query tokens cross-attend the patch features → `q`
  tokens (q ≪ #patches) — cheap, but a bottleneck that may drop fine detail.

**Hypothesis (survey §3.3, qualitative → to quantify):** at matched/larger token budget the MLP
projector wins on **detail-sensitive** tasks (fine attributes) while the Q-Former wins on
token-efficiency; the fidelity–vs–budget tradeoff is the §3.3 claim to make numeric.

**Metric.** attribute-identification accuracy (Wilson CI) as a function of connector token budget
`q`, for MLP vs Q-Former; the detail-sensitivity gap = accuracy on fine-grained attributes.

**Substrate.** Frozen SigLIP vision features (from SmolVLM-256M) + a small frozen LM head; train
*only* the connector on a synthetic image→attribute task (controllable detail: color+shape+count).

## 2. Execution decision

Real-scale B2 (a Q-Former/MLP trained on a real image-text corpus, LLaVA-1.5 recipe) is **infeasible
on this offline host** — from-scratch connector *training* + a multi-GB image-text dataset exceed the
bandwidth/compute budget that already scoped A2/A3/B1 down (decision `2026-07-02-04`). Two honest paths:

- **(a) real-but-tiny** — freeze SmolVLM's SigLIP encoder, train an MLP projector vs a small
  learnable-query cross-attention (Q-Former-style) on synthetic image→attribute data, into a tiny
  frozen classification head; sweep `q`, measure the detail/budget tradeoff. Genuine but toy-scale.
- **(b) plan + defer** — this document + a `todos/` entry; execute on a GPU + bandwidth host.

**Status: see `todos/2026-07-02-connector-ablation.md`** — filed for tracking; execution path chosen
at run time based on the remaining session budget (real-but-tiny preferred if time allows, else defer;
no fabricated results either way).

## 2a. Conformance matrix

| Parameter | Survey §3.3 / BLIP-2 / LLaVA | This study | Status |
|---|---|---|---|
| Vision encoder | CLIP/SigLIP (frozen) | SmolVLM SigLIP (frozen) | EXACT |
| MLP projector | 2-layer, per-patch → LLM token | 2-layer, avg-pool→q then MLP | APPROXIMATED |
| Q-Former | learnable queries × cross-attn | q queries × 1 cross-attn layer | APPROXIMATED |
| Downstream | frozen LLM decoder | frozen linear 2-head classifier | IDEALIZED |
| Eval | DocVQA/TextVQA (detail-heavy) | synthetic colour-binding | IDEALIZED |
| Metric | task score (Cider/Acc) | exact-match Acc ± Wilson | APPROXIMATED |

Do-not-cite absolute numbers; certifies the connector *implementations + budget-sweep methodology*,
not the §3.3 tradeoff (which needs the deferred detail-heavy eval).

## 3. Implementation & verification (G1 PASS 7/7)

`implementation/connector/` — frozen SmolVLM SigLIP features (1024×768) → MLP-pool (avg-pool to q +
2-layer MLP) or Q-Former (q learnable queries cross-attend) → mean-pool → 2 linear heads
(left-colour, right-colour). Task: two differently-coloured shapes (left / right half); recovering
each side's colour is the spatial-**binding** detail that a global/raster pool cannot separate.
Trained on frozen features (fast). 5 tests green (connector output shapes; two-head classifier;
**learns on linearly-separable features** — the verification anchor).

## 4. Results (G2)

Accuracy (3 seeds, Wilson-CI'd on 128 test images) vs token budget `q`:

| | q=1 | q=4 | q=16 | q=64 |
|---|---|---|---|---|
| MLP colour (coarse) | 1.00 | 1.00 | 1.00 | 1.00 |
| Q-Former colour | 1.00 | 1.00 | 1.00 | 1.00 |
| **MLP binding (detail)** | **0.992** | 0.992 | 0.995 | 1.00 |
| **Q-Former binding** | **1.00** | 1.00 | 1.00 | 1.00 |

**Budget is not the bottleneck** — q=1 already suffices (SigLIP features are position-rich, so even
a global pool retains binding). The only structure: Q-Former ≥ MLP on the detail axis (+0.005–0.008),
MLP-avgpool dipping at low q — the §3.3 direction (learned bridge preserves detail), at near-noise
magnitude.

## 5. Recommendation

At small scale and for coarse visual tasks, **connector choice/budget barely matters** — a cheap
MLP-pool suffices. The learned Q-Former's edge appears only on the detail axis and only marginally
here; to see the survey's real fidelity-vs-budget tradeoff, **evaluate on detail-heavy benchmarks
(DocVQA/TextVQA)** with a real LLM head (deferred). Do not over-invest in a Q-Former for coarse tasks.

## 6. Limitations & flip

- **Null result:** the intended fidelity-vs-budget curve is flat — the toy task is too easy
  (4 colours, 16 combos) for q to bind. A DocVQA-style fine-text task is needed.
- **Frozen-head proxy:** a linear classifier head, not a real LLM decoder — the connector's job of
  feeding an autoregressive LM is only approximated.
- Direction-consistent but not significant: Q-Former ≥ MLP on detail, within ~1 point.

## 7. Roadmap → todos/

`todos/2026-07-02-connector-ablation.md`: real connectors into a real LLM, DocVQA/TextVQA,
matched-FLOP comparison — the real-scale port on a GPU + bandwidth host.

## 8. Reproduce

```bash
export PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python3 -m implementation.connector.run_baseline   # extract SigLIP feats (cached) + sweep q
python3 -m pytest tests/connector/ -q               # 5 tests incl. learns-on-separable anchor
```
Deterministic (seeds 0..2). Env + git pinned in `artifacts/connector-ablation/study-manifest.json`.

## 9. Audit trail

- `decisions/2026-07-02-04` — offline substrate scope; real-but-tiny path chosen over defer.
- Citation-integrity: connector designs (MLP projector / Q-Former) read from
  `download/liu-llava-1.5-2023.pdf` and the survey §3.3; abstract-only for BLIP-2 specifics.
- Follow-ups: `todos/2026-07-02-connector-ablation.md`.
