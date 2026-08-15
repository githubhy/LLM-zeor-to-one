# Frontier cluster E2-sae-reevaluation

## key
E2-sae-reevaluation

## headline
The 2026 wave does not just add new discovery-vs-action data points — it undercuts the reliability of the *instruments used to grade both sides* of the survey's current line. On the discovery side, correlational recovery (cosine-similarity matching, the metric behind essentially every "SAE recovered feature X" claim) is shown to certify features that are causally inert at rates up to 77% in a degraded SAE and 9% even in a well-trained one, at cosine ≈ 1.000 (mi26-sae-geometric-to-causal-audit) — so "SAEs succeed at discovery" is true only under a metric now shown to be a weak proxy for whether the feature is real. On the action side, the standard causal-ablation readout itself is shown to be measurement-position-confounded (mi26-sae-position-selection-eval: 7.6-11.9% of "dictionary disagreement" variance collapses to ~0-2.4% once position is fixed, and does not improve with more data), and the one paper that head-to-head re-litigates "SAEs underperform dense steering at action" finds the answer is baseline-match-dependent, not a stable fact: the apparent SAE efficiency advantage at Gemma-2-9B reverses once the dense baseline is matched on intervention surface/basis rather than just perturbation norm, but the SAME recipe's advantage over an (unmatched) all-layer dense baseline remains large at Llama-3.1-8B and grows at Gemma-2-27B (mi26-sae-intervention-localization). A fourth paper shows causal-necessity findings for single-token features do not transfer across SAE families trained on the same base model (46× prevalence gap GemmaScope vs LlamaScope; LlamaScope features are causally redundant, recovering pre-ablation rank 96-98% of the time) and that this gap is not explained by activation function alone — training recipe is the residual, unresolved cause (mi26-sae-single-token-causal-necessity). A fifth paper shows SAE-induced similarity underperforms even a dense cosine baseline at a *discovery*-adjacent task (recovering human concept/typicality structure) and that SAE latent sets violate simple bag-of-features compositionality under controlled semantic edits (lost-latent rates 20-60%) (mi26-sae-set-level-instability). Net effect on the survey's line: the discovery/action distinction survives as a real phenomenon but must be reframed as measurement-fragile on both sides, and the "SAEs underperform at action" claim must be scoped to baseline-matching conditions and model scale rather than stated as a settled fact.

## records (20)

### 1
- **paper**: mi26-sae-geometric-to-causal-audit
- **claim**: Up to 77% of correlationally recovered features (cosine ≥ 0.90 match to ground-truth direction) in a degraded TopK SAE are causally inert (the matched decoder atom never fires when the feature is present); 9% are inert even in a well-trained SAE, including matches at cosine ≈ 1.000.
- **numbers**: 17/22 (77%) inert in degraded SAE (TopK k=13, precision 0.11); 2/22 (9%) inert in good SAE (TopK k=4, precision 1.00); deterministic re-audit: 3/22 (17%; 4 in ±1 band) vs 2/22 (9%); inert cosines up to 0.9997-0.9998
- **quote**: we find that up to 77% of features passing a standard recovery bar (cosine ≥ 0.90) in a degraded SAE—and 9% in a well-trained one—are causally inert: the matched atom never fires when the feature is present, including matches at cosine ≈ 1.000
- **conditions**: synthetic toy model, ground truth known, 128 dims / superposed features, 22 well-represented features audited per SAE, ablation + steering interventions, 3-seed multi-threaded original runs plus a deterministic single-threaded re-audit (Section 9)
- **confidence**: high
- **supersedes**: the implicit validation standard behind 'SAE recovered feature X' claims in the pre-2026 literature (Bricken et al. 2023 / Templeton et al. 2024 style correlational recovery), which the survey's current 'SAEs succeed at discovery' framing rests on

### 2
- **paper**: mi26-sae-geometric-to-causal-audit
- **claim**: The 77%/9% toy-model causal-inertness pattern replicates qualitatively but at much lower magnitude in a real production SAE, and the two regimes are explicitly stated as not numerically comparable.
- **numbers**: 7 of 83 hand-authored concepts cleared cosine ≥ 0.5 recovery bar; 1/7 (14%) causally inert (fired_frac=0); ablation specificity over recovered set: median 1.63, 95% CI [0.05, 5.34] (n=7)
- **quote**: Of 83 matched pairs, 7 cleared the bar; of those, 1 (14%) was causally inert (fired_frac = 0)... We do not treat a 14% single-layer, single-model inert rate as comparable to the toy regime's 77%/9% figures; the probe-direction proxy and the lowered cosine bar make the two regimes measure related but distinct quantities
- **conditions**: gpt2-small-res-jb SAE, blocks.8.hook_resid_pre (one hook layer), 83 hand-written concepts (8 positive/8 negative prompts each), cosine bar lowered from 0.90 (toy) to 0.5 (real model) to reflect weaker probe-direction proxy
- **confidence**: high
- **supersedes**: n/a — this is the paper's own explicit scope caveat, load-bearing for how the survey should (not) generalize the 77%/9% figures

### 3
- **paper**: mi26-sae-geometric-to-causal-audit
- **claim**: Causal inertness decomposes into two distinct causes with different scope: structural inertness (from antipodal-pair superposition geometry, present even in well-trained SAEs, not fixed by better training) vs competitive inertness (a TopK-selection pathology specific to degraded/under-capacity SAEs); and read-inertness (ablation-blind) dissociates completely from write-inertness (steering-impotent) for five antipodal feature pairs.
- **numbers**: 5 antipodal pairs show steering specificity 143-310 attached to ablation effect of exactly zero
- **quote**: causal inertness decomposes by cause into structural inertness (traceable to antipodal-pair superposition geometry and present in good SAEs) and competitive inertness (a TopK-selection pathology of degraded SAEs), and by direction into read-inertness and write-inertness, which five antipodal pairs dissociate completely—features that are unmonitorable yet steerable through the same atom, with steering specificities of 143–310 attached to ablation effects of exactly zero
- **conditions**: toy model, deterministic re-audit pipeline, TopK k=4/k=13 SAEs, 22 well-represented features
- **confidence**: high
- **supersedes**: n/a — new taxonomy, no prior instance in the survey's 2025 line to update

### 4
- **paper**: mi26-sae-geometric-to-causal-audit
- **claim**: A published production SAE contains a small number of decoder atoms that are the nearest correlational match for dozens of semantically unrelated concepts, replicated across independently constructed concept batches — real-model evidence of dictionary under-splitting.
- **numbers**: atom 14149 nearest match for 8/83 concepts (astronomy, cryptography, law, etc.) at cosine 0.30-0.70 both signs; atoms 4504 and 17413 each match 5 concepts; atom 17241 matches 4; replicated across n=33, 48, 83 concept batches
- **quote**: Atom 14149 is the nearest match for 8 of the 83 concepts—among them astronomy, cryptography, and law, domains sharing no obvious lexical or topical overlap... This is not an artifact of any one concept batch: the same handful of atoms recur as the nearest match across three independently constructed concept sets
- **conditions**: gpt2-small-res-jb SAE, one hook layer, hand-authored concept batches, ruled out as prompt-template artifact by a controlled negative case
- **confidence**: high
- **supersedes**: n/a — extends the feature-absorption literature (Chanin et al., cited by the paper) into a new observed pattern (atom collision across unrelated concepts), not superseding a specific prior number

### 5
- **paper**: mi26-sae-geometric-to-causal-audit
- **claim**: Direct quantitative test of L1 shrinkage in the TopK-vs-L1 SAE comparison (extending Gao et al. 2024): activation-magnitude refinement recovers most of the L1 SAE's reconstruction gap while substantially shifting its magnitudes, versus almost no shift for TopK.
- **numbers**: 91.2% of L1 SAE's reconstruction gap recovered by support-frozen magnitude refinement, with magnitudes shifted +22.5%, versus −0.05% shift for TopK
- **quote**: including direct quantitative evidence of L1 shrinkage (activation-magnitude refinement recovers 91.2% of the L1 SAE's reconstruction gap while shifting magnitudes +22.5%, versus −0.05% for TopK)
- **conditions**: from-scratch reproduction of Gao et al. (2024) TopK-vs-L1 Pareto comparison, matched L0≈4 (k=4 TopK vs λ=0.1 L1), identical superposed activations, 3 seeds
- **confidence**: high
- **supersedes**: Gao et al. (2024) — this paper's contribution is quantifying (not merely asserting) L1 shrinkage that Gao et al. described qualitatively

### 6
- **paper**: mi26-sae-single-token-causal-necessity
- **claim**: Single-token SAE features are causally necessary under zero-ablation at a strong significance rate across full model depth, in the model×SAE configurations tested.
- **numbers**: 178 of 208 full-layer conditions BH-significant (one-sided Mann-Whitney U, BH-corrected p<0.05 globally across all 208 tests), across 7 full-depth model×SAE configurations
- **quote**: Causal ablation across the seven full-depth model×SAE configurations confirms necessity under zero-ablation at the measured readouts: 178 of their 208 layers are BH-significant
- **conditions**: 6 models (GPT2-Small 124M, Gemma-2-2B, Gemma-2-9B, Gemma-3-1B, Llama-3.1-8B, DeepSeek-R1-8B), 3 SAE families (GemmaScope/res-jb, LlamaScope, community BatchTopK), 3.9M features analyzed via Neuronpedia; single-token features operationalized as activating on one vocabulary item + morphological variants
- **confidence**: high
- **supersedes**: n/a — new causal-necessity result, no direct 2025 predecessor in the survey

### 7
- **paper**: mi26-sae-single-token-causal-necessity
- **claim**: Causal-necessity findings for single-token features do not transfer across SAE families trained on the same base model: LlamaScope features are locally redundant (ablated feature's function is quickly recovered) while GemmaScope/BatchTopK features are causally anchored; this cross-family gap exceeds within-family scale effects.
- **numbers**: GemmaScope shows 46× higher single-token prevalence than LlamaScope at matched 8-9B scale; target token's rank recovers to within 2× baseline 96-98% of the time after LlamaScope ablation (vs. GemmaScope 62-71% recovery)
- **quote**: Cross-family causal differences exceed within-family scale effects: on the same base model, GemmaScope and BatchTopK features remain causally anchored, while LlamaScope features are locally redundant. The target token's rank recovers to within 2× baseline 96–98% of the time after the same ablation... Cross-family interpretability claims are therefore sensitive to training methodology, not just activation function or scale
- **conditions**: Gemma-2-9B vs Llama-3.1-8B comparable scale; recovery = fraction of features whose target-token rank after ablation stays within 2× baseline
- **confidence**: high
- **supersedes**: the assumption (implicit in citing a single-family SAE causal-necessity result as general) that causal-necessity findings port across SAE families on the same base model

### 8
- **paper**: mi26-sae-single-token-causal-necessity
- **claim**: Activation function alone does not explain the cross-SAE-family causal/prevalence gap: an activation-function-isolated controlled comparison (same model/layer/width) reverses the direction seen in the token-matched cross-family comparison, leaving training recipe as the unresolved residual cause.
- **numbers**: token-matched cross-family (N=627): BatchTopK > GemmaScope, p=1.2×10⁻¹⁸, r=0.36; activation-function-isolated controlled comparison (N=142, same model/layer/width): opposite direction, JumpReLU > TopK, p=0.036
- **quote**: token-matched (N = 627) shows BatchTopK > GemmaScope (p = 1.2×10−18, r = 0.36), but the activation-function-isolated controlled comparison on the same model/layer/width (N = 142) shows the opposite direction (JumpReLU > TopK, p = 0.036); opposite signs from the same model leave training-recipe factors as residual candidates
- **conditions**: Gemma-2-2B, community SAEs compared for activation-function isolation vs cross-family token-matched comparison
- **confidence**: high
- **supersedes**: n/a — methodological caution for any pre-2026 claim attributing a cross-family SAE performance/causal gap to activation function alone

### 9
- **paper**: mi26-sae-single-token-causal-necessity
- **claim**: Causal necessity and downstream anchoring show opposite layer-depth profiles: necessity strengthens monotonically with depth while anchoring (downstream cascade) concentrates in early layers — early and late features play complementary causal roles.
- **numbers**: necessity Spearman ρ = 0.61-0.97 (depth vs |∆logit|) across model/SAE combos, p<0.001; late layers show 13-30× more direct damage than early; anchoring Spearman ρ = −0.65, p<0.001; early-layer ablations cause 4-16× more downstream disruption than late-layer
- **quote**: Necessity damage (|∆logit|) increases monotonically with depth (Spearman ρ = 0.97 for BatchTopK, 0.70 for GemmaScope on Gemma-2-2B; p < 0.001), with late layers showing 13–30× more damage than early layers. In contrast, anchor damage (downstream propagation) is concentrated in early layers: early-layer ablations cause 4–16× more total downstream disruption than late-layer ablations
- **conditions**: Gemma-2-2B, Gemma-3-1B, BatchTopK and GemmaScope SAEs; Table 7 Q1(early)/Q4(late) quartile breakdown
- **confidence**: high
- **supersedes**: n/a — new layer-depth mechanism finding

### 10
- **paper**: mi26-sae-intervention-localization
- **claim**: The apparent efficiency/localization advantage of SAE feature ablation over dense activation steering for safety control on Gemma-2-9B disappears and reverses once the dense baseline is matched on intervention surface (same layer) and basis (projected onto SAE decoder span), not just on total perturbation norm.
- **numbers**: SAE deficit vs same-layer dense grows from −0.034 to −0.286 across matched perturbation bins; vs projected dense from −0.006 to −0.204; both largest gaps exclude zero under paired bootstrap over 6 seeds; SAE additionally worse on capability at highest bin (MMLU −0.020/−0.028, GSM8K −0.122/−0.112); reversal confirmed under HarmBench second judge
- **quote**: at every matched perturbation bin both fair baselines elicit more coherent harmful compliance than SAE ablation (up to −0.29 true-jailbreak), with SAE additionally paying a capability cost at high perturbation, and the reversal holds under a HarmBench second judge... The apparent perturbation-efficiency advantage in Table 4 is thus largely an artifact of comparing a single-layer intervention against an all-layer one
- **conditions**: Gemma-2-9B-it, Gemma Scope SAE, layer 20, top-k∈{400,800,1600}, 6 seeds; dense baselines: same-layer steering and dense-projected-onto-top-k-decoder-span (span coverage 0.68/0.75/0.84 of dense refusal direction at k=400/800/1600); primary judge Llama-Guard, second judge HarmBench
- **confidence**: high
- **supersedes**: the survey's current framing that SAEs 'underperform simple baselines at action (steering)' as if this were a fixed, baseline-independent fact — this paper shows the previously-reported SAE advantage itself was an artifact of an unmatched (all-layer) dense baseline, i.e. the direction of the discovery/action gap depends on baseline construction

### 11
- **paper**: mi26-sae-intervention-localization
- **claim**: The same reversal does not hold uniformly: SAE's efficiency advantage over an (unmatched, all-layer) dense baseline remains large on Llama-3.1-8B-Instruct and grows to Pareto-dominance at Gemma-2-27B-it — but the surface/basis-matched baselines that produced the 9B reversal were only run at 9B, an explicitly flagged limitation.
- **numbers**: Gemma-2-27B-it: SAE top1600 reaches true-jailbreak 0.75 at coherence 0.98 with relative perturbation 0.28, vs. smallest dense perturbation (β=0.05, rel-norm 0.60) reaching only 0.43 jailbreak at coherence 0.88
- **quote**: The advantage over all-layer dense steering remains large on Llama-3.1-8B and at 27B... The Llama-3.1-8B and Gemma-2-27B comparisons in Section 5 are reported against an all-layer dense baseline, and we label them as such throughout... we did not re-run the surface-matched baselines of Table 5 at this scale
- **conditions**: Llama-3.1-8B-Instruct (Llama Scope), Gemma-2-27B-it (4-bit, 3 seeds, capability benchmarks near floor so capability axis excluded); all against all-layer dense baseline only
- **confidence**: high
- **supersedes**: n/a — internal scope qualifier to the paper's own headline reversal (see contradictions field)

### 12
- **paper**: mi26-sae-intervention-localization
- **claim**: An SAE-ablation safety-steering recipe that appears clean (localized, low capability cost) at 8B/9B scale is destructive and largely a measurement artifact at 2B scale: severe capability collapse plus an apparent jailbreak advantage that a second judge does not corroborate.
- **numbers**: Gemma-2-2B-it: MMLU drops 0.12-0.19, GSM8K drops 0.44-0.50 (all significant, all bins); for SAE top1600, Llama-Guard gated jailbreak rate 0.477 vs HarmBench 0.008 (κ=0.01), while matched dense point has judges agreeing (0.423 vs 0.363, κ=0.46); same-source Llama-3.1-8B SAE points show judges agreeing (κ=0.35-0.43)
- **quote**: The same procedure that appears clean against an all-layer dense baseline in 8B/9B models is destructive in a 2B model: it halves GSM8K accuracy and its apparent jailbreak advantage is largely a single-judge artifact... Llama-3.1-8B controls for this: it uses the same prompt source, yet there the two judges agree on SAE points... The divergence is therefore specific to small-model SAE outputs, not an artifact of the prompt source or judge template
- **conditions**: Gemma-2-2B-it vs Gemma-2-9B/Llama-3.1-8B-Instruct comparison, judges Llama-Guard (primary) and HarmBench (second), 6 seeds
- **confidence**: high
- **supersedes**: n/a — new negative-transfer caution; relevant to any pre-2026 SAE-steering result validated only on small (≤2-3B) models

### 13
- **paper**: mi26-sae-position-selection-eval
- **claim**: In ablation-based SAE causal evaluation, the standard convention of measuring effect at the latent's own top-activating token confounds dictionary identity with measurement location: holding position fixed collapses most of the variance a naive comparison would attribute to dictionary disagreement.
- **numbers**: latent×arm variance component: 7.6% (per-arm position) → 0.0% (shared position) on Gemma-2-2B; 11.9% → 2.4% on Gemma-3-1B, on the same 93/53 identical latents; paired gain in generalizability coefficient Eρ² +0.130 [95% CI 0.074, 0.208] (Gemma-2-2B) and +0.138 [0.024, 0.290] (Gemma-3-1B)
- **quote**: Most of the variance such a comparison reads as these dictionaries disagree about this latent turns out to be the position instead: it falls from 7.6% and 11.9% of variance to near zero once every dictionary is measured at the same token
- **conditions**: 6 TopK SAEs sharing one initialisation (seed 0), each trained with one different fitting choice (decoder-free, soft-frozen τ=0.80/0.90, 10× lower LR, k=41 vs 82, reshuffled corpus), same 12M tokens; 240 shared live latents, uniform sample; evaluation corpus 384 sequences
- **confidence**: high
- **supersedes**: the implicit assumption behind any ablation-based causal-effect comparison across SAE dictionaries (e.g. the sort used in mi26-sae-single-token-causal-necessity's and pre-2025 SAE literature's cross-dictionary comparisons) that a top-activating-token measurement reflects the latent rather than the dictionary's own position choice

### 14
- **paper**: mi26-sae-position-selection-eval
- **claim**: The position-selection confound does not shrink with more evaluation data — across a sixteenfold range of corpus sizes, dictionaries agree LESS (not more) about where to measure a given latent, so scaling the eval corpus makes the problem worse, not better.
- **numbers**: sixteenfold range of corpus sizes tested; position agreement between arms falls monotonically on both Gemma-2-2B and Gemma-3-1B
- **quote**: More evaluation data does not rescue it. Across a sixteenfold range of corpus sizes the dictionaries agree less about where to measure, not more, so the problem grows with scale
- **conditions**: same 6-arm shared-initialisation design, corpus sizes spanning 16×
- **confidence**: high
- **supersedes**: n/a — methodological finding with no direct prior instance

### 15
- **paper**: mi26-sae-position-selection-eval
- **claim**: Two additional unreported evaluation choices — special-token (BOS) handling and normalization by intervention magnitude — can each independently flip the sign of a real comparison on identical data.
- **numbers**: raw KL vs per-unit-norm KL: raw says worse (Hodges-Lehmann HL=0.683, 95% CI [0.459, 0.961], p=0.039), per-norm says better (HL=1.687, [1.171, 2.498], p=0.011), both CIs exclude 1, identical latents/control; including BOS position moves a released Gemma Scope dictionary's explained variance from 0.863 to −3.5
- **quote**: asked whether a dictionary's rarest activation-frequency decile carries more causal mass than a frequency-matched decile of a tied-random dictionary, raw KL says worse... and KL per unit norm says better... both intervals excluding one... including position 0 moves the explained variance of a released Gemma Scope dictionary from 0.863 to −3.5
- **conditions**: released Gemma Scope dictionary; median perturbation norm ranges 3.60 (rarest decile) to 14.76 (most frequent decile)
- **confidence**: high
- **supersedes**: n/a — reporting-protocol finding; relevant to re-reading any 2025 SAEBench-style ablation-magnitude comparison the survey already cites

### 16
- **paper**: mi26-sae-position-selection-eval
- **claim**: An audit of five published papers that zero-ablate a single SAE latent and read a magnitude finds none of the confirmable methodologies report measuring more than one position per latent (a single curated token, the top-activating token, or a non-decomposed aggregate) — the position confound is essentially universal, unreported reporting practice in this literature.
- **numbers**: 5 papers audited (Table 2); position-per-latent count reported by confirmable methodologies: effectively 1 in every case
- **quote**: Of the five audited papers (Table 2), the ones whose methodology we could confirm in detail measure each latent at effectively one position per instance – a single curated token..., the top-activating token..., or an aggregate that is not itself decomposed by position... at 67.4% it is the largest term in the decomposition, and it is invisible unless the decomposition is run
- **conditions**: papers audited include Templeton et al. 2024, Gao et al. 2024, Cho et al. 2026 (mi26-sae-single-token-causal-necessity, this cluster); within-cell (position-within-latent) variance component = 67.4% of total decomposed variance
- **confidence**: high
- **supersedes**: n/a — this is itself the meta-finding that motivates re-reading pre-2026 ablation-magnitude results with a position caveat

### 17
- **paper**: mi26-sae-position-selection-eval
- **claim**: A same-cluster cross-check of mi26-sae-single-token-causal-necessity (Cho et al. 2026): its headline depth-necessity correlation survives an independent sensitivity bound, but an independent reimplementation of its single-token detector at its exact specification yields substantially lower prevalence than reported, at higher corpus size — an unexplained detector-level reproducibility gap, explicitly not attributed to the causal claim.
- **numbers**: Cho et al.'s headline depth correlation ρ=0.81 (their Table 21) confirmed to survive the sensitivity bound; independent reimplementation of their single-token detector at their exact spec (layer 12, Gemma-2-2B) yields 0.41-0.44× their reported prevalence at 4× their apparent corpus size
- **quote**: Their headline depth correlation (ρ = 0.81, their Table 21) survives a sensitivity bound on within-layer latent variance with room to spare and we did not find grounds to contest it; separately, our implementation of their single-token detector at their exact specification (layer 12, Gemma-2-2B) yields 0.41–0.44× their reported prevalence at four times their apparent corpus size: an unexplained reproducibility discrepancy we report about the detector, not their causal claim
- **conditions**: Gemma-2-2B, layer 12, independent reimplementation vs. Cho et al. 2026 original
- **confidence**: high
- **supersedes**: n/a — neither confirms nor refutes mi26-sae-single-token-causal-necessity; a genuine open discrepancy, see contradictions field

### 18
- **paper**: mi26-sae-set-level-instability
- **claim**: SAE-latent-set overlap (Jaccard) replicates the qualitative pattern of Shani et al. (2026)'s human-concept-boundary recovery finding but performs quantitatively worse than raw cosine similarity over dense embeddings — despite individual SAE latents being more interpretable.
- **numbers**: qualitative pattern preserved across categories; SAE-based similarity 'performs slightly worse' than raw cosine similarity (Section 4, static AMI ~0.1 range, Table 3/4 comparisons across models)
- **quote**: The qualitative picture is preserved: SAE-feature similarity broadly tracks human conceptual groupings. However, SAE-based similarity performs slightly worse than raw cosine similarity, despite the interpretability of individual latents
- **conditions**: multiple backbone models and SAE suites (GPT-2, Mistral 7B, Llama 3.1 8B, Gemma Scope variants including 16k/262k width, small/big sparsity); Shani et al. (2026) human category-boundary dataset replication
- **confidence**: high
- **supersedes**: complicates the survey's clean discovery/action split by showing SAE-based similarity underperforming a dense baseline on a discovery-adjacent task (recovering human conceptual structure), not just at action/steering

### 19
- **paper**: mi26-sae-set-level-instability
- **claim**: SAE activation-set similarity does not track human within-category typicality any more faithfully than dense embeddings; correlations with human typicality ratings remain weak across models/layers/SAE types, while SAE-Jaccard similarity DOES track the model's own residual-stream similarity structure closely.
- **numbers**: correlations between human typicality ratings and SAE-Jaccard similarity 'remain weak across models, layers, and SAE types'; cosine-vs-SAE-Jaccard correlation 'qualitatively positively correlated... but also not close to one' (exceptions: GPT-2 and Llama 3.1 8B SAEs fluctuate around zero)
- **quote**: SAE activation sets do not faithfully recover human conceptual typicality. Instead, they more closely track the model's internal similarity structure, which is known to differ from human judgments
- **conditions**: layer-dependent Spearman rank correlations, GPT-2 Small / Mistral 7B / Llama 3.1 8B, multiple Gemma Scope SAE widths/sparsities
- **confidence**: high
- **supersedes**: n/a — direct extension of Shani et al. (2026)'s dense-embedding finding to SAE latent sets, showing SAEs do not close this particular gap

### 20
- **paper**: mi26-sae-set-level-instability
- **claim**: SAE latent sets substantially violate simple bag-of-features/union-of-properties compositionality under controlled semantic modification (adding a compatible adjective to a noun): a large, depth-increasing fraction of the base-noun's active latents disappear rather than being preserved.
- **numbers**: lost-latent rate typically 20-60%, increasing with number of added adjectives (k) and with model depth; of lost latents, upstream-recoverable fraction is low in early layers, rises to ~60% in middle layers, decreases again in later layers
- **quote**: lost-latent rates are substantial, typically between 20% and 60%, increasing with k and often also with model depth... this directly contradicts the simple union-of-properties expectation, under which the more specific prompt should preserve object-related noun latents while adding adjective-related ones
- **conditions**: Gemma 3 270M with 16k-big SAE (primary reported figure); hand-curated noun+adjective dataset, kmax=5 adjectives per noun; additional models/SAE variants in appendix
- **confidence**: high
- **supersedes**: the union-consistency / bag-of-features compositionality assumption the paper attributes to prior SAE-set-based analysis work (Park et al. 2025b, Olson et al. 2025, Wattenberg & Viégas 2024, Olah 2024) — directly relevant if the survey cites SAE feature composability as an established discovery-side strength

## contradictions
(1) Within mi26-sae-intervention-localization itself: the SAE-vs-dense-steering "advantage" reverses at Gemma-2-9B once the baseline is surface/basis-matched, yet the SAME paper reports the advantage over an all-layer dense baseline "remains large" at Llama-3.1-8B and "grows" (Pareto-dominates) at Gemma-2-27B — but the surface/basis-matched baselines (the ones that produced the reversal) were only run at 9B; the paper explicitly flags this as an open limitation ("we did not re-run the surface-matched baselines of Table 5 at this scale"), so the 8B/27B "advantage" numbers and the 9B "reversal" number are not directly comparable claims about the same baseline. A survey citing this paper must not report "SAE underperforms dense steering" or "SAE beats dense steering" as a single verdict — both are true depending on scale and baseline construction. (2) mi26-sae-position-selection-eval both confirms and complicates mi26-sae-single-token-causal-necessity (Cho et al. 2026): it validates Cho et al.'s headline depth-correlation finding (ρ=0.81) as surviving its own sensitivity bound, but separately reports its own reimplementation of Cho et al.'s single-token detector, run at Cho et al.'s exact specification (layer 12, Gemma-2-2B), yields only 0.41-0.44× Cho et al.'s reported prevalence at 4× the corpus size — an "unexplained reproducibility discrepancy" the position-selection paper attributes to the detector, explicitly NOT to Cho et al.'s causal claim. This is a same-cluster, same-month cross-check that is neither a clean replication nor a refutation and should be reported as exactly that.

## gaps
(1) mi26-sae-geometric-to-causal-audit's central 77%/9% causal-inertness figures are measured in a small fully-synthetic toy model with known ground truth; the paper is explicit that these numbers are "a calibration point for the easy case, not a benchmark for a production model," and its own real-model census (GPT-2-small, 83 hand-authored concepts) finds 14% causally inert — the paper explicitly declines to treat 14% as comparable to 77%/9% because the probe-direction proxy and a lowered cosine bar (≥0.5 vs ≥0.90) make the regimes "measure related but distinct quantities." A survey must not report the toy-model percentages as a production-model rate. (2) None of the five papers report a matched, apples-to-apples comparison of SAE causal-necessity/localization findings across all three of {model family, SAE family, training recipe} simultaneously — mi26-sae-single-token-causal-necessity isolates activation function vs training recipe on one model (Gemma-2-2B) only, leaving training-recipe factors as an unresolved "residual candidate," not a demonstrated cause. (3) mi26-sae-intervention-localization's human coherence audit is explicitly "targeted and single-annotator rather than exhaustive or blinded" — supports its most important coherence-gating failure mode but is not a validated inter-annotator-agreement study. (4) mi26-sae-position-selection-eval's own account of what mechanistically distinguishes "where a latent prefers to fire" across dictionaries is explicitly unresolved ("that limits explanation, not the repair"); it demonstrates the confound and a fix, not the underlying cause. (5) None of the five papers cross-reference each other's evaluation-methodology fixes (position-selection, surface/basis-matching) into their own protocols — e.g. mi26-sae-single-token-causal-necessity's zero-ablation causal tests do not appear to control for the top-activating-token position confound that mi26-sae-position-selection-eval identifies as pervasive in exactly this class of ablation study, and mi26-sae-position-selection-eval's own audit table (Table 2) does not include mi26-sae-intervention-localization or mi26-sae-geometric-to-causal-audit — whether their causal readouts are position-confounded is not addressed by any of the five papers and should be filed as a survey-level open question, not resolved either way.

## critic
{
 "missing": [
  "**The returned payload is truncated mid-record.** It cuts off inside the second `mi26-sae-single-token-causal-necessity` record (`\"num`). Zero records were returned for three of the five papers \u2014 `mi26-sae-position-selection-eval`, `mi26-sae-intervention-localization`, `mi26-sae-set-level-instability` \u2014 even though all three carry numbers in the headline/contradictions/gaps prose. A section cannot be written from prose summaries with no backing records; re-emit the record list.",
  "**Geometric audit, Table 5 (the deterministic census) \u2014 the number that corrects the headline.** `p.13`: degraded SAE (TopK k=13) = **18/22 correlationally recovered, 3 inert (17%), 4 in the \u00b11 band**; good SAE (k=4) = 22/22 recovered, 2 inert (9%). Median ablation specificity 133.8 [107.0\u2013167.4] good vs 68.3 [22.0\u2013105.9] bad; median steering specificity 37.7 [33.1\u201341.8] vs 16.9 [14.2\u201321.3]. The extraction has the 17%/9% pair in a `numbers` field but leaves the abstract's 77% as the record's `claim`.",
  "**Geometric audit \u00a76.3 line: only ONE of the seventeen \"77%\" cases cleared the recovery bar.** Verbatim: \"One of the seventeen (feature 20) has cosine similarity 0.92\u2014above the \u2265 0.90 recovery bar used throughout.\" The paper's own contribution list (\u00a71) states the result correctly as \"17 of 22 **matched** features causally inert\" \u2014 matched, not recovered. The abstract's denominator ('features passing a standard recovery bar') is not the body's denominator.",
  "**Geometric audit, limitations \u00a7(p.19):** under the deterministic pipeline it is **1 seed per SAE**, 22 features, 2 SAE configurations; the bootstrap \"quantifies within-sample uncertainty, not across-seed variance\"; \"Exact specificity values \u2026 should be read as the shape of an effect measured once on this model, not tight estimates; the reproducible claim is qualitative.\" The five antipodal read/write pairs rest on \"one training run and one seed.\"",
  "**Position paper, \u00a75: position-within-latent is 67.4% of variance \u2014 \"larger than latent, arm, and their interaction combined \u2026 the paper's claim stated as a variance share.\"** This is the paper's most citable number and the strongest single statement in the cluster about evaluation mis-specification; it is absent from the headline, which reports only the 7.6\u21920.0 / 11.9\u21922.4 interaction collapse. Also absent: regressing it on relative position, activation magnitude and within-cell rank explains R\u00b2=0.005 \u2014 the confound is demonstrated but unexplained.",
  "**Position paper self-retraction (\u00a74, p.5).** \"An earlier version of this paper reported the per-arm numbers alone. Its conclusion, that causal importance is not a property of the latent, was measured under a protocol in which the dictionary chose the measurement location, and it does not survive controlling that.\" The survey must not cite the retracted stronger form \u2014 which is close to what a careless reading of this cluster would produce.",
  "**Position paper, released-dictionary evidence (does not depend on SAEs the authors trained).** Across 15 pairs of released Gemma Scope dictionaries, **no pair agrees on the measurement token for more than 48% of matched latents; restricting to near-identically-encoded latents reaches only 60.2%.** On their own arms, 13.9% same-token agreement against a 3.5% shuffle null (~4\u00d7 chance); median separation 118 tokens vs 137 under null; latents live at a median of 103 positions (range 31\u2013367).",
  "**Position paper: the collapse is partly rule-dependent, and the paper reports the range rather than the flattering half.** A second arm-symmetric selection rule gives **6.3% on Gemma-3-1B, not 2.4%** (0.0% either way on Gemma-2-2B). Also: the unrestricted per-arm latent\u00d7arm component is 18.4% / 24.8%; the 7.6% / 11.9% figures are the like-for-like restriction. And Gemma-3's 2.4% is the only sha
