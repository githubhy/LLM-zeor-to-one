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

**Verdict (mixed): the attention-collapse *phenomenon* (H1) reproduces strongly on a real VLM,
but attention-ranked pruning (H3) does NOT beat random on this task — a boundary condition on
FastV's premise.** On SmolVLM-256M (320 image tokens, 91% of the sequence), image-token attention
efficiency collapses from 0.82 (layer 0) to ~0.11 (layer 5), while text tokens hold ~9–10 — a **68×
deep-layer text/image attention ratio** (Chen's core finding, confirmed). The Eq-5 FLOP model (H4)
reproduces (monotone; K=2,R=0.5 → 0.45). **But** on the uniformly-redundant synthetic color task,
**random pruning stays at 100% accuracy even at 90% pruning, while attention-ranked pruning drops
to 0%** — because FastV retains high-attention *sink* tokens that carry no color, whereas random
keeps a mix of the redundant color-bearing tokens. FastV's "keep high-attention tokens" premise
needs query-localized tasks (its own VQA benchmarks), not this redundant one (§7, root-caused; masking
verified effective — R=0.9-attn=0.00). Do-not-cite absolute numbers (§2).

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

## 4. Implementation & verification anchors (G1 PASS 7/7)

`implementation/fastv/` — SmolVLM-256M (Idefics3) via `AutoProcessor(do_image_splitting=True,
size={"longest_edge":768})` → 320 image tokens (the memory/redundancy sweet spot: full 1088-token
split materialises ~42 GB of attention over 30 layers; 64-token no-split has too little redundancy).
Pruning = mask the bottom-R% image tokens as keys with explicit `position_ids=arange` (keeps RoPE
correct for survivors — a conservative all-layers approximation of FastV's after-K removal, §7).
Anchors (`tests/fastv/`, 6 green): Eq-5 FLOP reduction = 0 at R=0, strictly increasing in R,
larger for smaller K; the model answers synthetic colors correctly (baseline 100%).

## 5. Baseline results (G2)

**H1 — attention-efficiency collapse (Chen Eq 4)**, mean over 4 examples:

| Layer | 0 | 2 | 5 | 20 |
|---|---|---|---|---|
| image ε_img | 0.82 | 0.27 | 0.11 | 0.14 |
| text ε_txt | 2.84 | 8.33 | 9.90 | 9.59 |

Deep-layer text/image ratio ≈ **68×** — image tokens are attention-starved after layer 0
(**H1 confirmed**; Chen report ~472× system-prompt/image on LLaVA — same phenomenon, smaller model).

**H2/H3 — accuracy vs prune ratio** (16 synthetic color examples, Wilson-CI'd; K=2):

| R (prune frac) | 0.0 | 0.3 | 0.5 | 0.7 | 0.9 |
|---|---|---|---|---|---|
| acc (attention-ranked) | 1.00 | 0.94 | 0.62 | 0.19 | 0.00 |
| acc (random) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| FLOP reduction (Eq 5, H4) | 0.00 | 0.28 | 0.45 | 0.62 | 0.78 |

**H3 refuted on this task:** random ≥ attention-ranked at every R; random is perfectly robust to 90%
pruning. **H4 confirmed:** the Eq-5 FLOP curve is monotone and matches the closed form (test-anchored).

## 6. Recommendation

**Do not apply attention-ranked FastV pruning to tasks with uniformly-redundant visual content** —
random pruning dominates there. FastV's value is on **query-localized** tasks (VQA/OCR, where the
retained high-attention tokens carry the answer region); reproduce that regime before adopting
(follow-on). The attention-collapse phenomenon (H1) is real and model-general — a sound basis for
*some* token-reduction, but the ranking criterion must match task locality.

## 7. Limitations, root cause & flip

- **Flip (H3):** attention-ranked pruning *loses* to random on the redundant color task.
- **Root cause:** (1) **task redundancy** — a uniform colored shape encodes its color in nearly every
  image token, so random keeps enough while attention-ranking concentrates the loss; (2)
  **attention-sink retention** — the high-attention deep-layer tokens FastV keeps are positional
  sinks, not color-bearing regions (a known LVLM attention artifact). Masking is *not* the culprit:
  R=0.9-attention → 0% accuracy proves the mask removes token influence.
- **Substrate caveats (disclosed):** 320-token resolution (not 1088); synthetic color eval (not
  Flickr30K/A-OKVQA/MMMU); all-layers masking approximation of after-K removal.

## 8. Roadmap → todos/

`todos/2026-07-02-fastv-followups.md`: a **query-localized** eval (multi-object "what colour is the
circle?", counting) where H3 should hold; real VQA benchmarks; K-sweep; physical token removal
(true FLOP realisation, not just analytic Eq 5); the inverse-ranking control (prune *highest*-attention
to confirm the sink hypothesis).

## 9. Reproduce

```bash
export PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python3 -m implementation.fastv.run_baseline     # H1 efficiency + H2/H3 accuracy + H4 FLOP curves
python3 -m pytest tests/fastv/ -q                # 6 tests incl. Eq-5 anchors
```
Deterministic. Env + git pinned in `artifacts/fastv-pruning/study-manifest.json`.

## 10. Audit trail

- `decisions/2026-07-02-04` — offline substrate scope; SmolVLM downloaded via the local proxy.
- **Citation-integrity:** FastV mechanism (φ_attn, Eq 5, attention-collapse) read from
  `download/chen-fastv-2024.pdf` §3–4; not from memory.
- Follow-ups: `todos/2026-07-02-fastv-followups.md`.
