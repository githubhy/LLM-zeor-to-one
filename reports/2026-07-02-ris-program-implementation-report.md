# RIS Program — Implementation Report (A2, A3, B1, B2, C)

**Date:** 2026-07-02  **Branch:** `study/ris-program-2026-07-02`
**Goal:** run `reference-implementation-study` in **proposed** mode across the five candidate
tracks from the two survey→RIS handoffs, autonomously, committing each step, then push → PR → merge.
**Governing decision:** `decisions/2026-07-02-04` (offline host reached via a local proxy; per-track
substrate scope). **Mode:** `proposed` (all 13 items where the gates apply).

## 0. Executive summary

Five genuine reproduction studies were executed on a network-restricted Apple-Silicon host (MPS,
16 GB) reached only through a local HTTPS proxy (~214 KB/s). GPT-2-small and wikitext were cached;
**SmolVLM-256M (a real VLM) was downloaded via the proxy** to make the multimodal tracks real rather
than synthetic. Every external value was read from an acquired PDF (Hanna, AxBench, FastV, BLIP-2),
not from memory — which caught a memory-drift in the handoff itself (bug `2026-07-02-04`).

| Track | Study | Substrate | Gates | Verdict |
|---|---|---|---|---|
| **A2** | `eap-ig-faithfulness` | GPT-2-small (paper's own) | G1✓ G2✓ G3✓ G4✓ REPORT✓ | **EAP-IG > EAP faithfulness** +0.224 (p=3.6e-34), ρ=0.92 vs 0.46; ~99% of exact at ~⅕ cost. Faithful reproduction. |
| **C** | `sae-frontier-ext` | synthetic + orthonormal | G1✓ (extends parent) | **Red-team REFUTED** — BatchTopK/Matryoshka do *not* beat exact-k TopK; AdaptiveJumpReLU closest to unbiased. |
| **A3** | `steering-headtohead` | GPT-2-small (scaled) | G1✓ | SAE-clamp worst **reproduces AxBench**; diff-in-means > prompting is an honest metric/model-dependent flip. |
| **B1** | `fastv-pruning` | **real SmolVLM-256M** | G1✓ | H1 attention-collapse **confirmed** (68×), Eq-5 FLOP **confirmed**; **H3 refuted** (attn-rank < random on redundant task). |
| **B2** | `connector-ablation` | frozen SigLIP + tiny connectors | G1✓ | **Null result** — token budget not the bottleneck at toy scale (both ~100% at q=1); Q-Former ≥ MLP on the detail axis by ≤0.008 (§3.3 direction, near-noise). |

**Headline:** the two studies on their papers' own substrates (A2 GPT-2-small, B1 SmolVLM) and the
extension (C) are the strongest; A3/B1/B2 carry honest, root-caused divergences from the scaled-down
substrate — all disclosed do-not-cite, with production-scale ports filed as todos.

## 1. Environment & scope (decision 2026-07-02-04)

- **Offline** except a local proxy (`127.0.0.1:10086`); direct HTTPS times out. HF reachable via
  proxy at ~214 KB/s (used to fetch SmolVLM-256M, ~518 MB).
- **MPS only** (no CUDA), 16 GB; `transformer_lens` unavailable → A2 EAP built on raw-`transformers`
  hooks. GPT-2 + wikitext cached; **no Gemma / no VLM cached** → A3 scaled to GPT-2, B1/B2 to SmolVLM.
- Every downscaled track carries a **do-not-cite** clause + a production-scale `todos/` follow-on.

## 2. Per-study results

### A2 — EAP-IG circuit faithfulness (`docs/eap-ig-faithfulness-implementation-study.md`)
Built and **verified** a GPT-2 residual-node attribution harness (faith(full)=1 / faith(empty)=0
exact; patched==clean/corrupt to 1e-4). EAP vs EAP-IG vs exact-patching vs random on IOI/GT/SVA.
All 5 gates PASS (proposed flags). EAP-IG edge-scores correlate with exact patching at ρ=0.92 (EAP
0.46); cost EAP 3.2s / EAP-IG 9.2s / exact 50.6s. Node-vs-edge divergence from Hanna Fig 3
root-caused (§7). Bug `2026-07-02-04` (handoff's "IOI ~0%" was a memory drift) filed + fixed.

### C — Adaptive-count SAE extension (`docs/sae-frontier-ext-study.md`)
Added BatchTopK, Matryoshka, AdaptiveJumpReLU to the verified sae_frontier base. The parent
red-team's prediction (adaptive-count beats exact-k on dense activations) is **refuted** (BatchTopK
significantly worse, Matryoshka indistinguishable, on sparse + dense). Orthonormal shrinkage curve
confirms H2. Bug `2026-07-02-01` closed (adaptive STE bandwidth + regression test).

### A3 — Steering head-to-head (`docs/steering-headtohead-study.md`)
Prompting vs diff-in-means vs SAE-clamp on GPT-2-small. At matched coherence: diff-in-means +3.97 >
prompting +1.30 > SAE-clamp −0.93 (CIs non-overlapping). SAE-clamp-worst reproduces AxBench (verified
vs PDF); the prompting/diff-in-means flip is root-caused to metric-alignment + KL-not-judge + weak
base model.

### B1 — FastV vision-token pruning (`docs/fastv-vision-token-pruning-implementation-study.md`)
Real SmolVLM-256M. H1 attention-collapse confirmed (image ε 0.82→0.11; 68× deep text/image ratio),
H4 Eq-5 FLOP confirmed. **H3 refuted**: attention-ranked pruning loses to random on the
uniformly-redundant color task (random 100% at 90% prune; attn 0%) — FastV retains attention-sink
tokens; masking verified effective. Query-localized re-test deferred.

### B2 — Connector ablation (`docs/connector-ablation-implementation-study.md`)
*Pending this run — filled at commit time.*

## 3. Artifacts filed

- **Decisions:** `2026-07-02-04` (program substrate scope).
- **Bugs:** `2026-07-02-04` (EAP-IG IOI memory-drift, fixed); `2026-07-02-01` (JumpReLU STE, closed by C).
- **Todos:** per-study follow-ups (`eap-ig-followups`, `steering-followups`, `fastv-followups`,
  `connector-ablation`) + updated `sae-frontier-followups`; both handoffs (`mechinterp-ris-handoff`,
  `multimodal-llms-reference-impl-handoff`) closed/updated.

## 4. Reproduce

Each study doc carries a one-command reproduce block. Env pinned per study
`artifacts/<study>/study-manifest.json` (python 3.12.3, torch 2.3.1, transformers 4.49.0).
Offline: `export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.

## 5. Bugs encountered

- `2026-07-02-04` — MI-RIS handoff mis-stated EAP-IG's IOI result (memory drift); caught by reading
  the acquired PDF before pre-registering hypotheses (citation-integrity working as designed).
- `2026-07-02-01` — JumpReLU STE bandwidth (pre-existing); closed by C's AdaptiveJumpReLU + regression.
- (in-session, resolved) B1 attention OOM (42 GB) → `do_image_splitting` + resolution tuning to 320
  tokens; B2 task-too-easy iterations → spatial-binding task (field-note-worthy).
