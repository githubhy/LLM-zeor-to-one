# Frontier cluster E5-steering-control

## key
E5-steering-control

## headline
Two 2026 arXiv preprints (2606.24952, 23 Jun 2026; 2608.08168, 8 Aug 2026 — both non-peer-reviewed) give the survey its first post-2025 content. (1) "Perfect Detection, Failed Control" gives a precise geometric protocol on Gemma-2-2B-it (replicated on Llama-3.2-1B, Qwen-2.5-1.5B, Gemma-2-9B-it) showing perfect linear detectability (AUC=1.000) and causal controllability can be almost fully dissociated: the hallucination-detection direction sits at cos=0.12 (~83°) from the refusal/intervention direction, present already pretraining (base vs IT: 0.1197 vs 0.1200) and stable across 4 models (cos∈[0.12,0.20]). SAE-feature amplification (up to 50x) produces zero steering effect — a clean new 2026 data point directly supporting the survey's existing "SAE strong at discovery, weak at action" position. Crucially, the paper explicitly tests and REJECTS reading its own cosine as a general a-priori steerability oracle (§8) — steerability is functional (does the controlling direction also detect?), not a static angle — so this must be folded into the survey with that caveat, not as a bare "detection≠control" slogan. A 15° rotation only partially recovers control (13%→60% on the hardest sub-case), and a data-driven intervention direction can actively backfire, complicating any blanket "causal interventions are reliable" framing. (2) "Thinking vs. NoThinking" gives the survey its first reasoning-model interpretability content: Top-K SAEs on DeepSeek-R1-Distill-Qwen-7B layer 13 show Thinking mode runs a sparse/high-intensity, difficulty-invariant feature regime vs. NoThinking's diffuse/difficulty-adaptive one; causal suppression of the top-3 reasoning features shows reasoning and output-formatting (LaTeX/boxed-answer) share representations rather than being modular, with a compensatory-verbosity failure mode and non-redundant, fragile feature coordination. This second paper's Table 4 has a real reporting gap: the suppression strength α underlying its headline numbers is never stated despite a defined {0.1,0.3,0.5,1.0} sweep.

## records (18)

### 1
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Hallucination is detected with perfect linear separability while the detecting direction is nearly orthogonal (~83°) to the direction that causes refusal — the paper's headline detection-intervention gap.
- **numbers**: AUC = 1.000 (linear probe, from layer 5); cos(d_det, d_ref) = 0.12 (~83°)
- **quote**: The model detects whether an entity is real with perfect linear separability (AUC = 1.000 from layer 5), yet the direction carrying that signal sits at cos = 0.12 — about 83◦ — from the direction that produces a refusal
- **confidence**: high
- **conditions**: Gemma 2-2B-it (26 layers, 2304-dim residual stream), fp16, inference-time forward hooks, no fine-tuning; hand-picked (lm_head-derived) detection direction vs hand-picked refusal/intervention direction; N=100 stimulus set (50 fake + 50 real entities)
- **locator**: Abstract p.1; §4.3 'The geometric bottleneck', p.9-10
- **supersedes**: n/a — net-new 2026 result; survey has no post-2025 content and does not appear to discuss the Arditi et al. (2024) refusal-direction result this paper builds on (grep of method-inventory-causal.md / evaluation-and-metrics.md for 'arditi' returned no hits)

### 2
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: A second, independently-built (data-driven, no hand-chosen tokens) detection direction also fails to align with the intervention direction, and the two detection directions are themselves nearly orthogonal despite both reaching near-perfect detection — detection is a high-dimensional class, not one direction.
- **numbers**: cos(d_DiM, d_ref) = -0.06; cos(d_HP-det, d_DiM-det) = 0.11 (~83°); chance-level cosine in 2304 dims ≈ 1/sqrt(2304) = 0.02
- **quote**: cos(ddet , dref ) = 0.12, cos(dDiM , dref ) = −0.06 ... in 2304 dimensions two unrelated directions sit at cos ≈ 1/√2304 = 0.02 by chance. The HP–HP value of 0.12 is a small but reproducible positive... about 6× that floor... the cross-method −0.06 is essentially at the floor.
- **confidence**: high
- **conditions**: Gemma 2-2B-it, layer-25 last-prompt-token residual projections, N=100 stimulus set
- **locator**: §4.3, p.9-10
- **supersedes**: n/a

### 3
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Positive control: output-format behavior (JSON vs markdown fencing) IS a case where one direction both detects and controls — adding it eliminates fencing on 100% of queries at negligible magnitude, and activation transplant fully swaps the behavior.
- **numbers**: α=3.5 on L20-25 → 0% fencing (sharp sigmoid: 100% below α=2.5, 0% above α=3.5), 100% valid JSON, 100% correct answers, intervention magnitude = 0.6% of activation norm; transplant success 10/10 across Gemma 2-2B and Gemma 3-1B
- **quote**: adding dformat at L20–25 with α = 3.5 eliminates fencing on 100% of queries — a sharp sigmoid (100% fencing below α = 2.5, 0% above α = 3.5), 100% valid JSON, 100% correct answers, at an intervention magnitude of 0.6% of the activation norm.
- **confidence**: high
- **conditions**: Gemma 2-2B-it; 32 arithmetic queries, matched fencing/no-fencing prompts; controls: 0/100 random directions, 0/10 irrelevant token-pair directions had any effect
- **locator**: §3.2-3.3, p.7-8
- **supersedes**: n/a

### 4
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Using the detection direction directly as an intervention only partially reduces fabrication; the data-driven detection direction actively backfires (increases fabrication); SAE feature amplification and neuron ablation on the detection signal produce no behavioral change.
- **numbers**: Hand-picked detection-as-intervention, α=15, L20-25: fabrication on 100 fake entities ~70%→~40% (p<0.001), 0 false refusals on 50 real (N=150 total). SAE feature F15356 amplification up to 50x: no change in refusal, 2 real answers lost as collateral. Neuron ablation (top 500 discriminative neurons, L15): no behavioral change.
- **quote**: DiM goes in the wrong direction for intervention: applying it reduces refusals, increasing fabrication... at α = 15 on L20–25, fabrication on the 100 fake entities drops from ~70% to ~40% (p < 0.001), with 0 false refusals... SAE feature amplification (F15356, up to 50×): no change in refusal (small collateral — 2 real answers lost). Neuron ablation (top 500 discriminative neurons at L15): no behavioral change.
- **confidence**: high
- **conditions**: Gemma 2-2B-it, hallucination set N=150 (50 Type1 fake + 50 Type2 fake + 50 real); SAE feature from Gemma Scope (Google DeepMind 2024)
- **locator**: §4.2 'Intervention: detection directions are weak or backfire', p.9
- **supersedes**: n/a — new 2026 empirical instance that extends (does not contradict) the survey's existing SAE-underperforms-at-action position; concrete citable datapoint for method-inventory-dictionary.md.

### 5
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: A weight-cosine between a detection direction and an intervention direction is explicitly tested and REJECTED as an a priori steerability oracle — steerability is functional (does the intervention direction itself also detect?), not readable from a static angle.
- **numbers**: Format: intervention direction also detects at AUC≈1 (aligned/steerable). Hallucination: intervention (refusal) direction detects at only AUC≈0.7, even though the dedicated detection direction reaches AUC=1.000.
- **quote**: Measured the same independent way ... the cosine sits near the high-dimensional chance level (≈1/√2304 = 0.02) for both format and hallucination... For format it does [also detect]: the same direction doubles as a near-perfect detector (AUC ≈ 1). For hallucination it does not (AUC ≈ 0.7)... That difference — whether the controlling direction also reads the behavior — is a fact about behavior under intervention, invisible to a static angle.
- **confidence**: high
- **conditions**: Gemma 2-2B-it; independently-constructed (data-driven) detector cosine, both format and hallucination behaviors
- **locator**: §8 'The shortcut that fails: a weight-cosine is not a steerability oracle', p.17-18
- **supersedes**: n/a — methodological caveat that should travel WITH record 1 so the survey doesn't oversimplify into 'cosine predicts steerability'.

### 6
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: A 15° rotation from the detection direction toward the intervention direction partially bridges the gap on held-out hard cases — recovers much, not all, of refusal behavior, with a small false-positive cost.
- **numbers**: Stress test N=115 (30 Type1 fake, 30 Type2 fake, 55 real). ROT-15° at α=15: Type 1 refusal 40%→73%; Type 2 refusal 13%→60%; Real easy 100%→100%; Real obscure 100%→95%; Real tricky-sounding 60%→60%; false positives 0/55→1/55 (1.8%). At α=10: 0 FP, Type1 40%→57%, Type2 13%→33%.
- **quote**: Type 1 (obvious fake) 40% refuse → 73% refuse ... Type 2 (subtle fake — dates, numbers) 13% refuse → 60% refuse ... False positives 0/55 → 1/55 (1.8%)... At α = 10: zero false positives, Type 1 40%→57%, Type 2 13%→33%.
- **confidence**: high
- **conditions**: Gemma 2-2B-it, α=15 unless noted; N=115 held-out stress-test, distinct from the underpowered N=20 exploratory sweep set used to pick the 15° angle
- **locator**: §6.2-6.3 'Bridging the Gap: The 15° Rotation', p.12-13
- **supersedes**: n/a

### 7
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: The detection-intervention gap generalizes across model families/scales and predates instruction tuning.
- **numbers**: cos ∈ [0.12, 0.20]: Gemma 2-2B-it 0.12, Llama-3.2-1B 0.20, Qwen-2.5-1.5B 0.16, Gemma 2-9B-it 0.13; base vs IT Gemma 2-2B: cos=0.1197 (base) vs 0.1200 (IT), diff 0.0003
- **quote**: Across four models from three families and two scales (1B–9B), cos stays in [0.12, 0.20]; it is identical before and after instruction tuning (0.1197 vs 0.1200), so the geometry is laid down in pretraining.
- **confidence**: high
- **conditions**: Gemma 2-2B-it/base, Gemma 2-9B-it, Llama-3.2-1B-Instruct, Qwen-2.5-1.5B-Instruct; each model's own lm_head-derived directions
- **locator**: Abstract p.1; §7.1 (four-model table), p.14; §7.5, p.16
- **supersedes**: n/a

### 8
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Mechanism: an entity-copy computation in the output mapping dominates the (large) detection signal by roughly an order of magnitude, so detection barely affects the emitted token despite being ~7x a random-direction baseline.
- **numbers**: Detection gap (fake vs real projection) at L25 = +49.8, 6.9x the mean gap of 2000 random unit directions; refusal gap along same axis = -24.9 (wrong direction); orthogonal (entity-copy) component ~12x larger than detection component (median, fake set); MLP carries 5.66x more detection signal than attention (+42.3 vs +7.5 cumulative gap)
- **quote**: The detection gap between fake and real entities at L25 is +49.8 — an enormous signal, 6.9× the mean gap of 2000 random unit directions. But the refusal gap along the same axis is only −24.9, in the wrong direction... the part orthogonal to the detection direction — dominated by the entity copy... is roughly an order of magnitude larger (median ~12× across the fake set).
- **confidence**: high
- **conditions**: Gemma 2-2B-it, L25 last-prompt-token residual projections; signal decomposed via pre-/post-feedforward hooks
- **locator**: §4.3 'Why the detection signal doesn't produce refusal', p.10; §5.1, p.11
- **supersedes**: n/a

### 9
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Cross-model causal replication: the lm_head-derived direction has bidirectional causal power in other model families, but the α magnitude needed does not transfer.
- **numbers**: Llama 3.2-1B: baseline 100% fake-refuse → α=-1, 80% fabricate, 0/15 real damage. Qwen 2.5-1.5B: baseline 40% fake-refuse → α=+5, 93% refuse, 0/15 FP. (N=15 fake + 15 real per model, exploratory)
- **quote**: Llama 3.2-1B 100% baseline fake refuse, α = −1, 80% fabricate, 0/15 real damage. Qwen 2.5-1.5B 40% baseline, α = +5, 93% refuse, 0/15 FP... α magnitude does not transfer: Gemma needs α = 15, Llama needs |α| = 1, Qwen needs α = 5.
- **confidence**: medium
- **conditions**: Llama-3.2-1B-Instruct, Qwen-2.5-1.5B-Instruct; exploratory N=15+15 per model — paper itself does not claim statistical power here
- **locator**: §7.3 'Causal power is bidirectional', p.15
- **supersedes**: n/a

### 10
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: Llama-3.2-1B shows a double dissociation: despite near-identical near-orthogonal geometry to Gemma (cos=0.20), it refuses fake entities by default — evidence detection and action are separable computations, not one faculty that occasionally fails.
- **numbers**: cos=0.20 (same order as Gemma's 0.12); Llama refuses fake entities 100% by default vs Gemma's ~70% fabrication
- **quote**: Llama sharpens this into a double dissociation. It cannot be routing its refusal through the detection direction — that direction is as orthogonal to refusal as Gemma's — so its correct behavior must travel a separate path. We thus have detection without action (Gemma) and action that does not flow from detection (Llama)...
- **confidence**: high
- **conditions**: Llama-3.2-1B-Instruct vs Gemma 2-2B-it; the underlying routing mechanism for Llama's refusal is explicitly left open by the authors
- **locator**: §8 'Detection and action are independent faculties', p.17
- **supersedes**: n/a

### 11
- **paper**: Perfect Detection, Failed Control (arXiv:2606.24952)
- **claim**: SECONDHAND POINTER (not independently verified): this paper's own Related Work reports a contemporaneous 2026 result (Kazemi et al.) finding a single MLP neuron whose suppression bypasses safety alignment across many models and which also serves as a near-perfect harmful-prompt detector — the opposite pole (detection≈control) from this paper's hallucination case.
- **numbers**: 91.7% attack success on JailbreakBench across 7 models (1.7B-70B), no training required; AUROC ≈ Llama-Guard-3-8B for the same neuron as a harmful-prompt detector (as characterized by this paper, not independently verified)
- **quote**: Kazemi et al. (2026) refined this to single-neuron granularity: suppressing one MLP neuron suffices to bypass safety alignment across 7 models from 1.7B to 70B (91.7% attack success on JailbreakBench, no training required). Crucially, the same neuron serves as a near-perfect harmful-prompt detector (AUROC ≈ Llama-Guard-3-8B)
- **confidence**: low
- **conditions**: As characterized secondhand in §9 Related Work of mi26-perfect-detection-failed-control.pdf; Kazemi et al. 2026 itself was NOT read for this pass and is not currently in download/
- **locator**: §9 Related Work, p.19
- **supersedes**: n/a — flagged as a candidate NEW primary source to acquire before citing per citation-integrity.md; do not cite these numbers into the survey from this secondhand mention alone.

### 12
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Study setup: Top-K SAEs trained separately for Thinking and NoThinking inference modes on DeepSeek-R1-Distill-Qwen-7B's layer-13 residual stream, using DeepMath-103K, evaluated across three math-difficulty tiers.
- **numbers**: Layer 13 target; C=2^16=65,536 features per SAE; Thinking-mode training corpus 108M tokens (seq len 1024); NoThinking-mode training corpus 65M tokens; Adam lr=1e-3, β1=0.9, β2=0.999, ε=6.25e-10; Top-K anneal K:200→20 over first 50% of epoch 1; Thinking: batch 1024, 4 epochs; NoThinking: batch 128, 3 epochs
- **quote**: We employ the DeepSeek-R1-Distill-Qwen-7b model on the DeepMath-103K corpus and extract activations from the residual stream of the 13th layer, chosen as a representative intermediate layer... we train a Top-K Sparse Autoencoder for each mode with C = 2^16 feature vectors.
- **confidence**: high
- **conditions**: DeepSeek-R1-Distill-Qwen-7B (init: Qwen2.5-Math-7B, distilled from DeepSeek-R1); benchmarks AMC23 (easy, 40 problems), AIME24+AIME25 (medium, 60 problems), OlympiadBench (hard, 8,476 problems)
- **locator**: §4.1.1-4.1.3, p.4
- **supersedes**: n/a — net-new topic area; survey has zero prior content on reasoning-mode / thinking-vs-nonthinking interpretability.

### 13
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Observationally, Thinking mode uses a sparse, high-intensity, difficulty-invariant activation regime; NoThinking mode uses a diffuse, difficulty-adaptive regime with more distributed feature composition.
- **numbers**: Thinking: mean≈9.0, max≈75.0, std≈19.0 (roughly constant across difficulty). NoThinking: mean≈11.7, max≈60.0, std≈17.5. Feature composition of top-100 highest-activation tokens (Table 1): Thinking F4416 82%(easy)→96%(medium)→100%(hard); NoThinking F10770 37%(easy)→83%(medium)→100%(hard)
- **quote**: Thinking mode exhibits a relatively low mean activation of approximately 9.0 across all difficulty levels. However, its maximum activation consistently reaches high values around 75.0, accompanied by a high standard deviation of approximately 19.0... NoThinking mode maintains a significantly higher mean activation of approximately 11.7, with a lower maximum activation stabilizing around 60.0.
- **confidence**: high
- **conditions**: DeepSeek-R1-Distill-Qwen-7B, layer 13, top-20 TAV-ranked features per mode, three difficulty tiers
- **locator**: §4.2.1, p.6; Table 1, p.6
- **supersedes**: n/a

### 14
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Token-category analysis: Thinking mode leans toward verbal/logical-connective 'reasoning' tokens, NoThinking leans toward symbolic/math-notation tokens at easy difficulty; both converge toward more word-tokens and fewer number-tokens as difficulty increases.
- **numbers**: Reasoning tokens at Easy: Thinking 6.1% vs NoThinking 2.9%. Math-symbol tokens at Easy: NoThinking 22.3% vs Thinking 15.6%. Number tokens: Thinking 17.0%(easy)→8.0%(hard); NoThinking 16.0%(easy)→5.9%(hard). Word tokens: Thinking 28.2%(easy)→37.7%(hard); NoThinking 21.7%(easy)→36.1%(hard). [Table 2]
- **quote**: In easy tasks, the proportion of these [reasoning] tokens in Thinking mode is nearly double that of NoThinking mode... Its usage rate of 22.3% in simple tasks [math symbol, NoThinking] significantly exceeds the 15.6% observed in Thinking mode... In Thinking mode, the frequency of number tokens declines from 17.0% to 8.0%, while word tokens increase from 28.2% to 37.7%.
- **confidence**: high
- **conditions**: Same setup as prior record; percentages over all tokens activating the top-20 SAE features per mode-difficulty pair
- **locator**: §4.2.2, Table 2, p.7
- **supersedes**: n/a

### 15
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Causal suppression of the top-3 TAV-ranked Thinking-mode features (F28634, F4416, F8893) — applied only during thinking-block generation — consistently destroys mathematical formatting regardless of which feature is suppressed, implying reasoning and structural output share representations rather than being modular.
- **numbers**: LaTeX density Δ: F28634 -40.28, F4416 -35.22, F8893 -29.54 (per 1,000 tokens). Boxed Answer Retention: F28634 0%, F4416 10%, F8893 0%. [Table 4]
- **quote**: we observe a consistent drop in LATEX density of −29.54 to −40.28 per 1,000 tokens alongside a near-total failure to format solutions where Boxed Answer Retention frequently fell to 0%. These findings suggest that the sparse features driving the Chain-of-Thought... simultaneously encode the structural representations required for formal output, indicating that reasoning and formatting are not processed by independent modules.
- **confidence**: medium
- **conditions**: DeepSeek-R1-Distill-Qwen-7B, layer-13 suppression hook restricted to thinking-block tokens. GAP: the exact suppression strength α underlying Table 4 is never stated in the text despite the paper defining a sweep α∈{0.1,0.3,0.5,1.0}; no seed/repeat count or variance reported for these deltas.
- **locator**: §4.3 'Coupling of Reasoning and Syntactic Structure', Table 4, p.8
- **supersedes**: n/a

### 16
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Suppressing the core reasoning feature F28634 triggers compensatory over-generation: the model expands the response with more metacognitive markers rather than terminating, while lexical diversity collapses — a runaway, low-information failure mode.
- **numbers**: F28634 suppression: output length +454%, Distinct-1 -63%, metacognitive density Δ +34.17, uncertainty density Δ +9.25 (per 1,000 tokens). [Table 4]
- **quote**: When the core reasoning feature F28634 is suppressed, the model does not terminate generation but instead exhibits an expansion of the output sequence. This is evidenced by a 454% increase in output length... lexical diversity (Distinct-1) declines by 63%... suppressing F28634 leads to a significant increase in metacognitive density (+34.17).
- **confidence**: medium
- **conditions**: Same α-unspecified caveat as prior record; single reported run, no variance/CI stated
- **locator**: §4.3 'Compensatory Sequence Extension', Table 4, p.8
- **supersedes**: n/a

### 17
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Different suppressed features shift metacognitive density in OPPOSITE directions (F28634 up, F4416 down) while structural collapse is consistent across all three — evidence of fragile, non-redundant, distributed coordination among a small set of specialized reasoning features.
- **numbers**: Metacognitive density Δ: F28634 +34.17, F4416 -19.38, F8893 -4.33. Uncertainty density Δ: F28634 +9.25, F4416 -4.16, F8893 -0.99. Output length change: F28634 +454%, F4416 +410%, F8893 +107%. Distinct-1 change: F28634 -63%, F4416 -37%, F8893 -42%. [full Table 4]
- **quote**: suppressing feature 28634 increases metacognitive density by 34.17 while suppressing feature 4416 decreases the same metric by 19.38. This contrast shows that different features regulate the process in opposite directions. Despite these divergent internal effects, the structural indicators collapsed consistently... disrupting any single feature drives the model into distinct failure modes such as uncontrolled verbosity.
- **confidence**: medium
- **conditions**: Same as prior two records; all three features F28634/F4416/F8893, α unspecified
- **locator**: §4.3 'Fragile Coordination under Feature Suppression', Table 4, p.8
- **supersedes**: n/a

### 18
- **paper**: Thinking vs. NoThinking (arXiv:2608.08168)
- **claim**: Qualitative role identification (from context inspection, not further causal test): dominant Thinking-mode feature F4416 acts as a 'reasoning monitor' (exploratory/self-correction epistemic language); dominant NoThinking-mode feature F10770 acts as a 'structural formatter' (LaTeX syntax, formal notation).
- **numbers**: n/a (qualitative characterization)
- **quote**: F4416 serves as a semantic proxy for exploratory reasoning and self-correction. It exhibits strong activation during intermediate computational steps (e.g., '8.97 squared is...') and aligns with epistemic markers such as 'Let's see' or 'isn't working'... F10770 functions primarily as a syntactic formatter. Its activations are densely concentrated on LaTeX syntax... and formal notation.
- **confidence**: high
- **conditions**: DeepSeek-R1-Distill-Qwen-7B, layer 13; method is manual context inspection of maximally-activating tokens (Table 3), not a separate intervention
- **locator**: §4.2.2 'Qualitative Context Analysis', Table 3, p.7-8
- **supersedes**: n/a

## contradictions
No direct numeric contradiction against a pre-2026 value confirmed to be in the survey (I only grepped method-inventory-causal.md and evaluation-and-metrics.md for the keyword "arditi" — zero hits — I did not read their full prose, per the task's "at most two, do not go exploring" constraint). Two conceptual tensions worth flagging to the survey editors rather than asserted as resolved: (1) Perfect-Detection-Failed-Control shows a data-driven (difference-in-means) causal-intervention direction can actively BACKFIRE (increase the very behavior it targets for suppression), which complicates framing causal interventions as uniformly "the field's reliable instruments" without qualifying which direction-construction method was used — reliability here is construction-method-dependent, not intrinsic to "causal intervention" as a class. (2) The paper's §8 explicitly tests and REJECTS reading its own headline cosine-gap metric as an a-priori steerability predictor. If the survey's evaluation-and-metrics.md treats probe/steering-vector geometric alignment as a general steerability diagnostic anywhere, this paper is a direct, citable counter-argument — but I could not confirm from the two grepped files whether the survey currently makes that specific claim, so this is flagged, not asserted as a live contradiction.

## gaps
Paper 1 (Perfect Detection, Failed Control): sample sizes are modest throughout (N=20-150 per condition for the primary model; N=15 per model for cross-model causal replication, explicitly called "exploratory" by the authors) — the paper itself flags this in its Limitations. Only decoder-only transformers 1B-9B tested; no encoder-decoder or >10B-parameter replication (authors flag lm_head-linearity assumptions may not hold at larger scale). Single behavior deep-dive (hallucination) plus one positive control (format) — whether the ~78-83° gap holds for other behaviors (sycophancy, deception, jailbreak refusal per se) is explicitly left to future work. The entity-copy mechanism's specificity to entity-centric QA vs. a general property of the output map is explicitly called "untested" by the authors. Gemma-2-9B-it is reported to "resist steering" qualitatively (§8) with no comparable intervention table given — an asymmetry in the cross-model results the survey should not smooth over. Kazemi et al. 2026 (single-neuron jailbreak/detection≈control result) is mentioned only secondhand inside this paper's Related Work and was not independently read for this pass; needs its own acquisition + citation-audit before any numbers from it enter the survey.

Paper 2 (Thinking vs. NoThinking): the suppression strength α underlying Table 4's headline causal numbers is never stated in the main text, despite the paper defining a 4-point dose-response sweep α∈{0.1,0.3,0.5,1.0} earlier — a genuine reporting gap in the source, not an extraction miss (confirmed by a targeted second grep). No error bars, seed count, or repeat-run variance is reported for any of the density-metric deltas in Table 1/2/4 — all read as single-run point estimates. Single model (DeepSeek-R1-Distill-Qwen-7B) and single layer (13) — no cross-model or cross-layer replication (contrast with paper 1's explicit 4-model triangulation). Math-only domain (AMC23/AIME/OlympiadBench); unclear whether the Thinking/NoThinking mechanistic split generalizes to non-math reasoning tasks. The Thinking-mode and NoThinking-mode SAEs are trained as two separate dictionaries (not a shared/joint dictionary), so feature IDs (e.g., F4416 vs. F10770) are not directly comparable across modes by construction — a design choice the authors do not flag as a limitation in the text extracted. Both papers are unreviewed arXiv preprints (2606.24952, 2608.08168) posted within the last ~2 months of the survey's "today" date — treat as fast-moving, not yet community-vetted evidence.

## critic
{
 "sufficient": false,
 "missing": [
  "PAPER 2 HAS NO RECORDS AT ALL. The returned JSON truncates mid-record-11 (the Kazemi secondhand pointer, cut at 'suffices to bypass safety alignment acros'). Every visible record is on paper 1. The Thinking-vs-NoThinking evidence exists only inside the `headline_finding` prose \u2014 no quote, no locator, no conditions, no confidence. As delivered it cannot be cited under citation-integrity. Re-surface paper-2 records with quotes and locators (Table 4 is p.8; \u00a74.1.3 training details p.4; \u00a74.1.6 intervention protocol p.5; Table 1 p.6; Table 2 p.7; Table 3 p.8; Appendix A.1-A.4 pp.10-11).",
  "Paper 1 \u00a78, p.16 \u2014 THE 9B MODEL WAS NEVER STEERED, and the paper says the intervention FAILS there: 'Gemma 2-9B-it reproduces the geometry (Section 7.1, cos = 0.13) but resists steering \u2014 the same intervention is suppressed rather than amplified at 9B \u2014 so we report its geometry but not a comparable intervention. Whether larger models systematically damp this steering is left to future work.' The extraction's headline says the result was 'replicated on ... Gemma-2-9B-it' with no hint of this. The one scale-up datapoint on the *fix* is negative, and it is the single most consequential omission in the payload.",
  "Paper 1 \u00a77.5, p.16 \u2014 THE BASE-MODEL RESULT IS HALF-OMITTED AND ITS OMITTED HALF INVERTS THE MEANING. Record 7 returns cos 0.1197 vs 0.1200 but not: 'In the base model the ordering is backwards \u2014 real entities project further along it, as if more uncertain than the fakes (gap \u221223.2). Instruction tuning flips it the sensible way: now the fake entities are the ones that look uncertain (gap +49.8).' Only the lm_head AXIS predates instruction tuning; the detection SIGNAL is reversed before tuning. Recoverable in one sentence, and without it the survey will write a false sentence.",
  "Paper 1 \u00a74.1, p.9 \u2014 the six-detector table, which is literally 'the detection metric' the brief asked for. Only one row (linear probe AUC=1.000) came back. Full table: logit-lens top-5 entropy, unsupervised, L25, AUC=0.913; linear probe, supervised, L5+, AUC=1.000; single MLP neuron N578, unsupervised, L15, acc=88%; SAE feature F15356, unsupervised, L22, 88% fake / 0% real; embedding norm, unsupervised, input layer, acc=83%; single attention head L9H2, supervised, L9, AUC=1.000. The embedding-norm row matters most: a label-free input-embedding statistic reaches 83% before any computation, which is what makes 'detection is cheap, control is not' the actual story.",
  "Paper 1 \u00a74.1, p.9 \u2014 the graded-detection defense: L9H2 separates OBSCURE-real from COMMON-real entities at AUC=0.993, 'so its detector tracks how well it knows an entity, not merely whether the entity exists.' This is the paper's own rebuttal to 'the probe reads prompt-surface features', and the survey needs it to justify quoting AUC=1.000 at all.",
  "Paper 1 \u00a75.2, p.11-12 \u2014 the franken-forward attention-ablation table, entirely absent. Zeroing attention output from L17 onward IMPROVES honesty: MLP-only L17-25 gives 75% fake refuse vs 60% baseline (+15pp) at 95% real correct; kill L17+L21 = 60%; kill L20-25 = 65%; MLP-only L13-25 destroys the model (5% / 0%). A causal-intervention datapoint that belongs in \u00a77 and appendix C.",
  "Paper 1 \u00a75.3, p.12 \u2014 the self-gating NEGATIVE result, absent and high-value for \u00a713: 'the detection gap at any single MLP layer output is ~0.01 \u2014 far too small to use as a gate. The cumulative gap of ~50 exists only as the sum across all layers. No single layer is a reliable thermometer.' 9 gating conditions, all equal to baseline. This is the citable engineering answer to 'can we wire a probe into an internal hallucination monitor?'",
  "Paper 1 \u00a77.4 p.15 + Appendix A.4 p.23 \u2014 the coefficient-non-transfer evidence: \u03b1/residual-norm ratios 0.21 (Gemma) / 0.056 (Llama) / 0.023 (Qwen), 'The ratios span nearly 1
