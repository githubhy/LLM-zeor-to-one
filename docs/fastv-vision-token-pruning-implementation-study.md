# FastV Vision-Token Pruning — Reference Implementation Study

**Study:** `fastv-pruning`  **Topic module:** `implementation/fastv/`
**Mode:** `proposed` (all 13 items).
**Substrate:** **SmolVLM-256M-Instruct** (Idefics3; SigLIP vision + SmolLM2-135M text), a
*real* early-fusion VLM downloaded via the local proxy (decision `2026-07-02-04`); CPU/MPS.
**Parent handoff:** `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (candidate 1);
survey `surveys/multimodal-llms/inference-and-serving.md` §8.2, `open-problems-and-roadmap.md` §13.2.
**Primary source (read, not recalled):** Chen et al., *An Image is Worth 1/2 Tokens After Layer 2*
(FastV), ECCV 2024 — `(local: download/chen-fastv-2024.pdf)`; LLaVA-1.5 `(local: download/liu-llava-1.5-2023.pdf)`.

## 0. Executive summary

> **Status: Phase 1 (scenario) — pending compute.** Verdict reserved for the FLOP-reduction @
> accuracy-knee headline with CI once G2 lands.

## 1. Problem, scope & candidates (Phase 1)

**Problem.** In early-fusion LVLMs, image tokens dominate the sequence (LLaVA-1.5: 576 of ~660
input tokens, 64%) yet receive collapsing self-attention in deep layers — Chen et al. measure
image-token **attention efficiency** `ε_img = (Σ received attention)/|img|` at 0.21% of the
system-prompt's after layer 2 (vs ~50% in the first two layers). FastV exploits this: at a chosen
layer `K`, rank image tokens by average received attention and prune the last `R%`; deeper layers
run on the reduced set. This study reproduces (a) the attention-collapse phenomenon and (b) the
FLOP/accuracy Pareto knee, on a real but small VLM.

**Model under study.** SmolVLM-256M-Instruct (Idefics3): 12-layer SigLIP vision encoder + a
30-layer SmolLM2-135M decoder; images are encoded to visual tokens spliced into the decoder
sequence (early fusion) — the architecture FastV targets. `output_attentions=True` exposes the
per-layer attention needed to rank image tokens.

**Task & data.** Deterministic **synthetic ground-truth images** (rendered with matplotlib: colored
shapes, counts, simple scenes) + templated questions with known answers ("What color is the
circle?", "How many squares?"). Real images processed by a real vision encoder; answers are
ground-truth (a synthetic-oracle eval, disclosed — the production eval is Flickr30K/A-OKVQA/MMMU,
deferred). Metric: exact-match accuracy (+ Wilson CI).

**Candidate methods** (pruning criterion φ at layer `K`, ratio `R`):
1. `no_prune` — full visual tokens. *Baseline (upper accuracy, full FLOPs).*
2. `fastv_attn` — φ_attn: rank by average received attention, prune last R% after layer K. *Intervention.*
3. `random_prune` — φ_rand: random R% pruned after layer K. *Control (FastV's own ablation).*
4. `prune_at_0` — K=0 pruning (before the LLM). *Extreme control.*

**Metrics.** (a) exact-match accuracy ± Wilson CI; (b) **theoretical FLOP-reduction ratio** (Chen
Eq 5: per-layer `4nd²+2n²d+2ndm`, tokens `n→(1−R)n` after K over T layers); (c) per-layer
image-token attention efficiency `ε_img` (the phenomenon).

**Pre-registered hypotheses** (grounded in Chen §3.3, §4, Fig 1/3 — read from PDF):
- **H1 (Quantitative):** image-token attention efficiency collapses after the first ~2 layers
  (ε_img in deep layers ≪ ε_text; large system-prompt/image ratio). *The phenomenon.*
- **H2 (Quantitative):** `fastv_attn` holds accuracy within a small margin of `no_prune` up to a
  task-dependent (K,R) knee, then degrades — a Pareto-flat-then-cliff curve (Chen Fig 1).
- **H3 (Quantitative):** at matched FLOP budget, `fastv_attn` ≥ `random_prune` accuracy
  (attention ranking beats random — Chen §5 ablation).
- **H4 (Quantitative):** measured FLOP-reduction matches the closed form Eq 5 (theory-as-predictor).

## 2. Protocol-vs-spec conformance matrix

| Parameter | Paper | This study | Status | Impact |
|---|---|---|---|---|
| VLM | LLaVA-1.5-7B/13B, QwenVL, Video-LLaVA | SmolVLM-256M (Idefics3) | IDEALIZED | smaller real early-fusion VLM; mechanism-faithful; absolute numbers not comparable |
| Prune criterion φ_attn | avg received attention @ layer K | identical | EXACT | none |
| FLOP model | Eq 5 (MHA+FFN) | identical closed form | EXACT | none |
| (K,R) knobs | swept | swept | EXACT | none |
| Eval data | Flickr30K/A-OKVQA/MMMU/OCR-VQA | synthetic ground-truth images | IDEALIZED | controllable oracle; real-benchmark port deferred (todo) |
| Metric | task-specific (Cider/Acc) | exact-match Acc ± Wilson | APPROXIMATED | simpler; CI-disclosed |

**Do-not-cite clause.** Absolute accuracies/FLOP numbers are a 256M-scale synthetic-eval
reproduction; cite Chen et al. for production values. Certifies the *mechanism* (attention collapse
→ prune tolerance; attn-rank > random; Eq-5 FLOP model), not the paper's absolute Pareto curve.

## 3. Candidate methods & the pruning mechanism (Phase 1)

FLOP-reduction closed form (Chen Eq 5), tokens `n → n̂=(1−R)·n` after layer `K` over `T` layers:

$$
\mathrm{reduction}(K,R) = 1 - \frac{K\,(4nd^2 + 2n^2 d + 2ndm) + (T-K)\,(4\hat{n}d^2 + 2\hat{n}^2 d + 2\hat{n}dm)}{T\,(4nd^2 + 2n^2 d + 2ndm)}.
$$

Attention-efficiency of image tokens in layer $j$ (Chen Eq 4): $\varepsilon_{\text{img}}^{j} = \tfrac{1}{\lvert \text{img} \rvert}\sum_{i} \alpha_{\text{img}}^{i,j}$.

## 4.–13. Phases 2–6

Pending compute (Phase 2 implementation on the downloaded SmolVLM-256M; verification anchors =
FLOP closed form + attention-mass conservation; baseline/sensitivity/precision/report). Audit trail:
decision `2026-07-02-04`. Reproduce recipe + seeds and per-cell CIs land with each phase.
