# Frontier cluster E3-weight-space

## key
E3-weight-space

## headline
The survey has zero prior coverage of weight-space/parameter-reading methods (confirmed absent from method-inventory-dictionary.md and evaluation-and-metrics.md, including no mention of the foundational Gao et al. 2025 weight-sparse-transformer work these three 2026 papers all build on) — this is a genuinely new, coherent method family, not a variant of existing circuit analysis, but it splits into two sub-relationships to the survey's existing QK/OV circuit framework: paper 3 (SWD) directly extends the QK-circuit bilinear collapse (Elhage et al. 2021) by decomposing the pre-softmax attention score into sparse bottleneck-unit-pair terms and causally validates one pair end-to-end, while paper 2 (tiled SVD) operates on individual weight matrices in parallel to — and with zero citation of — the two-matrix QK/OV composite, making it the same general "read the weights, not activations" axis but a genuinely different decomposition target.

## records (11)

### 1
- **paper**: mi26-weight-sparse-parameters-interpretable.pdf
- **claim**: Robust per-weight interpretability rate (predicate holds reliably on held-out data) is far higher in weight-sparse transformers than in dense models of comparable or larger size, ordered: sparse-code > sparse-stories > dense-stories > dense-pretrained-control.
- **numbers**: Robust rate: Gao et al. 2025 sparse-code transformer 15.0±1.7%; Drori 2026 sparse (SimpleStories) 9.6±1.1%; Drori 2026 dense (same arch, no sparsity) 1.5±0.6%; Pythia-70m (dense pretrained control) 0.4±0.3%. (InterpA/InterpB in-sample/held-out single-slice rates are higher: 37.3%/35.3%, 21.4%/17.2%, 13.2%/9.0%, 12.0%/5.0% respectively.)
- **quote**: the two sparse models sit far above the dense controls — roughly 15% and 10% of their non-zero weights are robustly interpretable, against about 1% for the dense model and essentially none for the pretrained dense control (Table 1). This ordering is not an artifact of one threshold or one judge
- **locator**: Table 1 / §4.1, p.5
- **confidence**: high
- **conditions**: T=0.75 score threshold, coverage cap c=0.5; K=10 held-out slices per weight; auto-interp LLM = Gemini 3 Flash (headline results replicated with Claude Sonnet 4.5, GPT-5, GPT-4o in Appendix A.5); weights sampled uniformly across MLP layers of each model on a corpus matching its own training distribution
- **supersedes**: n/a — survey has no prior weight-space interpretability baseline to update

### 2
- **paper**: mi26-weight-sparse-parameters-interpretable.pdf
- **claim**: The object of study is a single scalar weight, not a circuit or a learned dictionary component; 'interpretable' is operationalized as: an automated LLM-generated short Python predicate over token context, credited only if it recovers the weight's ablation effect (recovery≈1) and its complement has none (inverse≈0) on data never used to generate the predicate — a quantitative causal metric, not a human-legibility judgment alone.
- **numbers**: score(f) = min(recovery(f), 1-inverse(f)) ≥ T=0.75, with coverage p(f) ≤ c=0.5; recovery(f) = 1 - (CE_f - CE_0)/ΔCE, inverse(f) = 1 - (CE_¬f - CE_0)/ΔCE
- **quote**: A weight is called interpretable at threshold T if its best predicate clears the score threshold and passes the coverage gate... We use T = 0.75 and c = 0.5 throughout the paper
- **locator**: §3.3, Eq.(1)-(3), p.4
- **confidence**: high
- **conditions**: conditional-zero ablation test scored via cross-entropy shift on held-out corpus; N=100 candidate predicates sampled per weight (saturation point, swept in Appendix A.4)
- **supersedes**: n/a

### 3
- **paper**: mi26-weight-sparse-parameters-interpretable.pdf
- **claim**: A hybrid architecture (sparse reasoning core coupled to a dense output head) recovers more of the loss-capability frontier than fully weight-sparse training, indicating the interpretability-vs-capability tradeoff of weight sparsity is architecture-dependent, not a fixed cost of the sparsity idea itself.
- **numbers**: qualitative only — no ΔCE or perplexity delta given in this paper for the hybrid vs fully-sparse comparison
- **quote**: Drori (2026) extends this with the SimpleStories sparse-and-dense pair, which couples a sparse reasoning core to a dense output head and recovers more of the loss-capability frontier than fully sparse training.
- **locator**: §2 Related work, p.2
- **confidence**: medium
- **conditions**: SimpleStories-scale models only; no numeric frontier plot reproduced in this paper (cites Drori 2026, unread)
- **supersedes**: n/a — nuances rather than contradicts the general 'weight-sparse training costs capability' framing

### 4
- **paper**: mi26-tiled-svd-weight-mechanisms.pdf
- **claim**: Introduces 'mechanism mounts' — a triple (trigger v, write u, strength σ) extracted per-tile via column-tiled SVD of a single linear weight matrix (not a composite two-matrix product) — as an identity-in-the-weight-rule alternative to learned proxy dictionaries (SAEs); evaluated by full-write energy lift against the site's actual write tensor rather than tile-local lift, which the paper shows is tautologically gameable.
- **numbers**: All 182/182 site-layers (7 linear maps × 26 layers) on Gemma-2-2B pass the pre-registered suite: residual writes (mlp.down, attn.o) get full A/B/C, 52/52; other 5 maps get A/B only, 130/130.
- **quote**: We propose extracting mechanism mounts directly from linear sites by column-tiled SVD: each mount is a triple (v, u, σ) read as trigger, write, and strength. Identity is the weight rule... Aggregate: 182/182 GO.
- **locator**: Abstract; §3.5 Aggregate verdict table, p.6-7
- **confidence**: high
- **conditions**: google/gemma-2-2b, 26 layers; WikiText-2 raw train, 16,384-token subsample (seed 0); tile width T=512 (residual/MLP), 256 (attn.k/v), 128 (attn.q, 64 fallback); k=2 modes/tile for A/C, k∈{1,2,4,8,16} for B
- **supersedes**: n/a

### 5
- **paper**: mi26-tiled-svd-weight-mechanisms.pdf
- **claim**: Per-tile SVD recovers substantially higher on-distribution write-energy directions than whole-matrix SVD, high-norm column sampling, or a random baseline, at every depth on both residual-write sites tested (except one near-tied layer) — evidence that local column structure in a weight matrix is not well summarized by its single global SVD.
- **numbers**: Example rows (full-write energy lift, tile vs whole vs cols vs rand): layer 6 attn.o: 0.346 vs 0.097 vs 0.007 vs ≈0; layer 18 attn.o: 0.383 vs 0.102 vs 0.011 vs ≈0; layer 6 mlp.down: 0.107 vs 0.016 vs 0.001 vs ≈0; layer 25 mlp.down: 0.013 vs 0.013 (tied, A4 still passes on ratio floor)
- **quote**: Local column structure in W is not well summarized by a single global SVD for on-distribution write energy. Tiling recovers higher-energy write directions under a fixed mount count on both residual writes.
- **locator**: §3.2 Experiment A, results table, p.5-6
- **confidence**: high
- **conditions**: same Gemma-2-2B / WikiText-2 setup as above; pass criterion A1: L_full(tile) > L_full(rand) + 0.005 (0.002 on effective-path sites)
- **supersedes**: n/a

### 6
- **paper**: mi26-tiled-svd-weight-mechanisms.pdf
- **claim**: This paper's method family has no citation to or engagement with the Elhage et al. 2021 QK/OV circuit framework — its reference list (5 entries) cites only prior single-matrix SVD-interpretability work (Millidge & Black 2022, Xue & Andrzejak ICML 2026, Ahmad et al. 2025) and SAE/dictionary-learning papers, not the composite-matrix circuit-collapse literature.
- **numbers**: n/a (bibliographic fact — 5-entry reference list, verified by full grep of the extracted text for 'Elhage'/'QK'/'OV circuit', zero hits)
- **quote**: In most such settings, however, SVD is used as a lens or circuit primitive [5], not as a fair test of which chunking of W yields usable on-distribution mechanisms.
- **locator**: §1 Introduction, p.1; References [1]-[5], p.9
- **confidence**: high
- **conditions**: n/a — this is a scope/citation observation, not a numeric result
- **supersedes**: n/a — clarifies rather than contradicts; the paper is a parallel decomposition target (single-matrix, not the QK/OV two-matrix product), not a rival or successor to the survey's Appendix A derivation

### 7
- **paper**: mi26-sparse-weight-decomposition.pdf
- **claim**: Sparse Weight Decomposition (SWD) reparameterizes a pretrained dense weight matrix W ≈ AB with A, B sparse (not just low-rank/dense-factor), post hoc and without training an auxiliary replacement network; at matched replacement fidelity it needs far less calibration data than trained baselines (Transcoder, VPD) and reaches the same circuit sufficiency/necessity targets with fewer active read/write edges.
- **numbers**: At matched pre-pruning CE (differing by ≤0.001), SWD uses <1% of the data used by the corresponding trained baseline; SWD (s=0.5) reaches low CE delta after 'a few thousand tokens' vs roughly 10^6 tokens for baselines on the GPT-2 Small layer-8 MLP output projection.
- **quote**: SWD matches the held-out fidelity achieved by Transcoder and other strong baselines while using less than 1% of the data that those baselines use to train their replacements. For matched replacement fidelity, SWD reaches the same circuit sufficiency and necessity targets with fewer active read/write edges
- **locator**: Abstract; §3.3 Single-matrix replacement, p.6-7
- **confidence**: high
- **conditions**: GPT-2 Small, Qwen2.5 (0.5B-3B), and Qwen3.5-27B; FineWeb-Edu calibration/eval split; DSF (Double Sparse Factorization / ADMM) solver; sparsity level s swept 0.125-0.875
- **supersedes**: n/a

### 8
- **paper**: mi26-sparse-weight-decomposition.pdf
- **claim**: Weight-sparse pretraining (Gao et al. 2025) is characterized as costing 100-1000x more training/inference compute than dense models of comparable capability; SWD's post-hoc full-model replacement (all 48 attention+MLP matrices of GPT-2 Small) reaches comparable held-out CE to a matched-budget weight-sparse-pretrained model using under 1% of its token budget after fixed-support fine-tuning — a direct capability-cost-of-interpretability tradeoff comparison.
- **numbers**: Sparse factorization alone (no fine-tune): held-out CE 3.90. SWD-FT (fixed-support fine-tune): CE 3.44, vs matched sparse-pretraining checkpoint's CE 3.45. Token budget: SWD-FT 20.6M tokens total (4.19M factorization + 16.38M fine-tune) vs 2.884B tokens for sparse pretraining (~140x fewer tokens). Matched active-weight budget: 26.77M active weights, ~68% sparsity relative to dense transformer-body weight matrices.
- **quote**: weight-sparse models require 100–1000× more training and inference compute than dense models of comparable capability (Gao et al., 2025)... The resulting SWD-FT replacement reaches CE 3.44, slightly below the matched sparse-pretraining checkpoint's 3.45, while using under 1% of its token budget
- **locator**: §1 Introduction p.2 (100-1000x claim); §3.4 Full-model replacement, p.9 (CE/token numbers); Table 2
- **confidence**: high
- **conditions**: GPT-2 Small, all 48 attention+MLP matrices replaced simultaneously; embeddings/LayerNorm/nonlinearities/LM head unchanged; comparison is against Gao et al. 2025's weight-sparse pretraining recipe at an approximately matched active-weight budget
- **supersedes**: n/a — this is the paper's own novel measurement, nothing in the survey to update

### 9
- **paper**: mi26-sparse-weight-decomposition.pdf
- **claim**: SWD's attention-side analysis directly extends the Elhage et al. 2021 QK-circuit decomposition rather than replacing it: because the pre-softmax attention score is bilinear in query/key inputs, substituting SWD's sparse-factored Q and K weights turns the score into an explicit sum over sparse bottleneck-unit-pair terms — i.e. the same bilinear QK-circuit object the survey's Appendix A already derives, refined with sparse read/write structure rather than a competing primitive.
- **numbers**: n/a for this specific claim (structural/methodological, not a headline metric) — see next record for the concrete worked numbers
- **quote**: The workflow here combines the QK-circuit decomposition of attention (Elhage et al., 2021), sparse weight-space attention decomposition for circuit tracing (Franco & Crovella, 2024), and feature-level QK attribution (Kamath et al., 2025). Because a pre-softmax attention score is bilinear in its query- and key-side inputs, an additive feature decomposition rewrites that score as a sum of query–key feature-pair terms... SWD supplies parameter-side query and key bottleneck units for the same analysis.
- **locator**: Appendix J, 'Attention Bottleneck Units: From Static QK Geometry to Prompt-Local Effects', p.43ish (unpaginated in extracted text; section J / J.1-J.3)
- **confidence**: high
- **conditions**: GPT-2 Small full-model-replacement factors (from §3.4); Q/K/V packed weight matrix attn.c_attn reconstruction error <4% in every layer (attn.c_proj up to ~6% in middle layers)
- **supersedes**: n/a — this is the direct evidentiary answer to the survey's own posed question about the tiled-SVD/QK-OV relationship, but for the SWD paper specifically, not the tiled-SVD paper (which does NOT make this connection — see the paired tiled-SVD record above)

### 10
- **paper**: mi26-sparse-weight-decomposition.pdf
- **claim**: A single SWD query-key bottleneck-unit pair (q266×k64, GPT-2 Small layer 9 head 3) is causally validated end-to-end: its signed static score contribution matches a coherent token-level attention story on a real prompt, and ablating the query-side unit reverses that exact behavior — closing the chain from weight-space geometry to a causal, prompt-level effect.
- **numbers**: Mean dense-to-SWD-reconstructed attention KL = 0.0405 (fidelity check). Static pair contribution z266(h_t)z64(h_u)γ^h_{266,64}: signed mean +4.26 over causally valid query-key positions. After removing q266: attention KL relative to intact reconstruction rises to 2.496; max attention-probability change = 0.775. Screen swept 12 layers × 12 heads × 5 top pairs × 3 prompts = 2,160 prompt-head-pair evaluations.
- **quote**: We then remove q266 from the reconstructed Q slice and recompute the head. Attention shifts sharply toward the first token: relative to the intact reconstructed pattern, mean attention KL rises to 2.496 and the maximum probability change is 0.775... This reversal agrees with the signed contribution map
- **locator**: Appendix J.3, 'Prompt Replay and Bottleneck-Unit Intervention'
- **confidence**: high
- **conditions**: GPT-2 Small, prompt 'When Mary gave John the book, he thanked' — single selected case, explicitly flagged by the authors as one example, not a systematic ablation sweep
- **supersedes**: n/a

### 11
- **paper**: mi26-sparse-weight-decomposition.pdf
- **claim**: The survey's existing framing of SAEs/Transcoders as the reference activation-space method for circuit extraction is the explicit baseline SWD is measured against; SWD is positioned as a strictly weight-space alternative that avoids training an auxiliary representation network at all, distinguishing it from parameter-decomposition methods (APD/SPD/VPD) that also require optimizing an additional model.
- **numbers**: n/a (taxonomic claim)
- **quote**: SAEs and Transcoders... fit a new activation dictionary or replacement network on an activation corpus, whereas SWD [obtains bottleneck units directly from pretrained weights, avoiding the cost of training an auxiliary representation]... We evaluate the effect of this distinction through the matched-fidelity Transcoder comparison.
- **locator**: §5 Related Work / Discussion, p.13 (paraphrase-quote boundary at 'whereas SWD')
- **confidence**: medium
- **conditions**: n/a — framing/positioning statement rather than a measured result; the measured result is the <1%-data / fewer-active-edges finding recorded above
- **supersedes**: n/a

## contradictions
No direct numeric contradictions among the three papers or against the survey's pre-2026 claims (nothing to supersede in the strict sense, since the survey has no weight-space baseline to contradict). The one tension worth flagging for the survey's SAE framing (SAEs strong at discovery, weak at action/steering): both SWD and the per-weight-interpretability paper report methods that are simultaneously interpretable-by-inspection (discovery) AND causally actionable (ablation/steering) at a fraction of SAE/Transcoder's training data — SWD matches Transcoder's held-out fidelity at <1% of its data and needs fewer active edges for matched sufficiency/necessity; this is evidence against, not for, the discovery/action split holding in weight space, but none of the three papers benchmarks head-to-head against an SAE on the same task, so it is a lead, not a closed comparison (calibration-residuals check 3: an independent implementation/method excludes hypotheses, it does not prove the split fails to generalize to weight-space methods).

## gaps
(1) No paper reports Gao et al. 2025's own capability/perplexity cost number for weight-sparse pretraining directly — SWD paper only characterizes it qualitatively as "100-1000x more training and inference compute than dense models of comparable capability," attributed to Gao et al. 2025 but not quoted with the underlying figure. (2) Tiled-SVD paper (paper 2) never engages with the QK/OV circuit framework (Elhage et al. 2021 not in its 5-entry reference list) — whether tiled SVD "mechanism mounts" applied to attn.q/attn.k could be composed into a QK-circuit-style bilinear object is unstated, left as an open question for the survey to raise rather than answer. (3) Paper 1's own stated limitation: predicates are token-local Python functions that cannot express semantic/multi-token/stateful features, so its 12-31% interpretable-weight figure is an explicit lower bound, and whether the finding holds for larger sparse-trained models with non-trivial multi-step behavior is named as future work, not yet measured. (4) None of the three papers benchmarks directly against an SAE on a matched task/model — the "beats SAE" framing is implicit (stated motivation, e.g. tiled-SVD abstract: "identity lives in the learned dictionary rather than in the network weights themselves") but not quantitatively tested against one. (5) SWD's zero-data variant (no calibration activations) trades behavioral fidelity for weight-fidelity (relative Frobenius error 0.366 vs 0.415 at s=0.75) — whether zero-data bottleneck units are equally circuit-useful is asserted qualitatively ("zero-data bottlenecks remain useful for task circuits," Appendix G.2) but the paper doesn't report a matched sufficiency/necessity number for zero-data vs calibrated SWD in the main text.

## critic
{
 "sufficient": false,
 "missing": [
  "**The survey already covers weight/SVD analysis** \u2014 the extraction's headline is false. `surveys/mechanistic-interpretability/method-inventory-observational.md` \u00a74.4 is literally titled \"Weight/SVD analysis and feature visualization [catalog-only]\", opens with \"Analyze weight matrices directly (singular structure of $W_{QK}$, $W_{OV}$)\", places it as \"the '0-layer' limit of circuit analysis\", and tags it \"*a supporting tool, not a primary method, for LM interpretability*\". The extraction checked only `method-inventory-dictionary.md` and `evaluation-and-metrics.md`. One grep recovers it. Everything downstream of \"zero prior coverage\" has to be re-decided.",
  "**Tiled SVD's own Discussion answers the new-family-vs-variant question, in the opposite direction** (p.8, \u00a74): \"**Novelty is thinner.** Singular vectors of transformer weights, detector-effector units, and unembed readouts already exist [3, 4, 5]. We do not claim human-readable concept names, and we do not claim to replace sparse autoencoders for concept discovery [1, 2]. The wedge is fair chunking, a negative result about tile-local metrics, coverage saturation, and a depth-conditioned causal check packaged as a reproducible suite.\" This is the single most decision-relevant sentence in the three papers and it is absent from the return.",
  "**Tiled SVD \u00a75 Limitations, absent entirely** (p.8): \"This study uses a single model family and size (Gemma-2-2B). ... The WikiText-2 subsample (16,384 of 86,109 tokens) may bias which mounts look strong. **Energy lift is not human meaning: mounts carry no semantic labels.** ... The C1 waiver for \u2113 < 6 ... remains a design choice\". The user asked explicitly whether the evidence is a human-legible story, a metric, or a downstream task; for [92] the paper's own answer is \"a metric, and explicitly not meaning\".",
  "**The 182/182 pass bars, which decide what that number is worth** (\u00a72.7 table, p.5): A1 passes when `L_full(tile) > L_full(rand) + 0.005` (0.002 on effective paths); **C1 passes when Spearman \u03c1 \u2265 0.05 OR top-20 Jaccard \u2265 0.05**, and is required only for residual writes at \u2113 \u2265 6. \"The judge is judge_paper_go in src/atlas/mount/paper_eval.py\" \u2014 the authors' own script. A 182/182 against a \u03c1\u22650.05 floor is not an interpretability result.",
  "**Tiled SVD Experiment C depth curve** (\u00a73.4 table, p.7) \u2014 the strongest causal evidence in the paper, omitted: mean Spearman of steered \u0394logits vs unembed(u) by band \u2014 early 0\u20135 \u2248 \u22120.03 to 0.07 (waived), onset 6\u20138 \u2248 0.07\u20130.52, late 18\u201324 \u2248 0.35\u20130.69, **final layer 25 \u2248 0.91 (mlp.down) and \u2248 0.75 (attn.o)**. This is what would let the survey say weight-read directions become logit-relevant with depth.",
  "**Paper [91]'s abstract headline \"12 to 31%\" has no in-body support.** `grep` finds the string exactly once, in the abstract (p.1). The body's headline is Table 1's robust rates (15.0 \u00b1 1.7 / 9.6 \u00b1 1.1 / 1.5 \u00b1 0.6 / 0.4 \u00b1 0.3 %) over *sampled nonzero MLP weights*, with p.5 stating \"The right-most column of Figure 1 (= 0) counts parameters that are exactly zero by construction, **and is excluded from all rates**\", plus \u00a74.1's \"roughly a quarter of their high-impact weights are robustly interpretable\". Three different bases; the extraction repeats the abstract number in `gaps` as though it were the paper's measured figure.",
  "**Paper [91]'s judge-LLM sensitivity** (\u00a74.2, p.6): \"We re-run the full evaluation under four different LLMs (Gemini 3 Flash, Claude Sonnet 4.5, GPT-5, GPT-4o): **absolute rates at T = 0.75 differ by up to \u223c30 percentage points**, with stronger LLMs higher, but the rate-vs-T shape and the cross-model rank order are preserved.\" Only the *ordering* replicates. The extraction's `conditions` says \"headline results replicated wi
