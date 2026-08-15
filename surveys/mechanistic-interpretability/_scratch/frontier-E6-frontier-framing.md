# Frontier cluster E6-frontier-framing

## key
E6-frontier-framing

## headline
The 2026 field is pulling in two directions the survey's five-family taxonomy (observational / causal / dictionary / steering-editing / automation) does not fully capture. (1) Neurosymbolic rule-extraction and LLM+solver integration (NeSyFOLD, NeSyViT, Logic-LM, LLM-Modulo) is a materially distinct sixth family — entirely absent from the survey's inventory and files, per grep. (2) Model diffing, which the survey carries only as a "preliminary research update" aside inside crosscoders (method-inventory-dictionary.md §6.4), has matured into a primary, causally-validated discovery+control pipeline: MMDiff's own ablation (Table 7) proves the diffing step (decoder-rotation + visual-energy filtering against a base-LM SAE) is *necessary* — dropping it either destroys general capability (-24 to -26% VQA) or yields near-zero task effect — directly updating the "still preliminary" epistemic tag with 2026 quantitative evidence. Both findings are corroborated, not contradicted, by the survey's existing content; the 2026 survey (mi26) itself under-covers model diffing (absent from its own taxonomy) and treats ACDC/EAP/SAE-evaluation more shallowly than the target survey already does.

## records (10)

### 1
- **paper**: mi26-survey-circuits-sparse-symbolic.pdf
- **claim**: The 2026 survey's own taxonomy includes a neurosymbolic-AI family (rule extraction from trained networks, and LLM+external-solver integration) treated as a peer methodological pillar alongside circuits/SAEs/steering — a family entirely absent from the target survey's five-family inventory (observational/causal/dictionary/steering-editing/automation); grep across all survey .md files for 'neurosymbolic|nesy|logic-lm|rule extraction' returns zero hits.
- **numbers**: n/a (taxonomy/structural claim, not a metric)
- **quote**: Finally, the article touches on neuro-symbolic artificial intelligence (NeSy), an emerging paradigm that combines the computational power of deep learning with formal logic, enabling the translation of abstract neural representations into precise, executable rules.
- **conditions**: mi26 survey §1 (intro) and §6.1-6.3 (NeSyFOLD on CNNs via FOLD-SE-M/Answer Set Programs; NeSyViT extending rule extraction to ViTs via a sparse concept layer + L1/entropy/SupCon losses; Logic-LM and the LLM-Modulo framework for external-solver integration at inference time). Pages ~2, 15-16.
- **confidence**: high
- **supersedes**: n/a — this is a genuine taxonomy gap, not an update to an existing survey claim. Candidate new §8/§15 family; the target survey currently has no neurosymbolic content anywhere.

### 2
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: MMDiff's own controlled ablation shows the model-diffing step (filtering SAE features by decoder-rotation cosine + visual-energy against a base-LM SAE) is causally necessary for the discovered features to be both effective and selective — removing it either wrecks general capability or yields no task effect. This is direct 2026 evidence that model diffing is a distinct, load-bearing method step, not an optional refinement, updating the target survey's 'preliminary research update' epistemic tag on crosscoder model diffing (method-inventory-dictionary.md §6.4, cite:19, 2024).
- **numbers**: Full MMDiff pipeline (with adapted-feature filter): -12.3% VSR, -0.1% VQA. Firing-only (no adapted-feature filter): -15.1% VSR, -25.9% VQA. + visual-energy only: -15.9% VSR, -26.3% VQA. + adapted (no lexical filter): -1.0% VSR, -0.2% VQA. Random features (control): -0.5% VSR, -0.2% VQA. A from-scratch SAE with no base-LM warm start (no diffing index at all): top-10 spatial features by odds ratio fire on 100% of VSR samples and ablating them leaves VSR unchanged (mean +0.22, no feature beyond ±1.4) vs -10.11 for MMDiff features on the same model.
- **quote**: The causally effective set is therefore not recovered by conventional MLLM SAE training alone; it comes from the adapted-feature filter, which requires diffing.
- **conditions**: PaliGemma 2 (Gemma-2-2B backbone, Gemma-Scope JumpReLU SAE warm start), VQAv2 spatial subset vs. VSR eval, causal-removal protocol of §4 (orthogonal projection at all layers, text-token positions only). Table 7, §6.1, page ~8.
- **confidence**: high
- **supersedes**: method-inventory-dictionary.md §6.4 crosscoder model-diffing entry (cite:19, tagged 'A promising research tool, especially for model diffing; still preliminary (released as a research update)') — MMDiff is a 2026 primary paper with a controlled necessity ablation, materially strengthening that epistemic tag from 'preliminary' toward 'causally validated for this application (feature discovery + control), at ≤8B scale, single modality-adaptation setting'.

### 3
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: Causal removal of MMDiff-discovered spatial features degrades the targeted spatial-reasoning behavior selectively (large VSR drop, minimal VQA spillover) across three independent MLLM families, replicating the core diffing-then-ablate result across models rather than in a single configuration.
- **numbers**: Mean VSR accuracy drop from ablating top spatial features: -10.1% (MMDiff-Llama/LLaVA-MORE), -12.3% (MMDiff-Gemma/PaliGemma 2), -14.6% (MMDiff-Qwen/InternVL3.5-2B); range 6-31% across individual features; |ΔVQA| ≤ 1.5% in all cases; control-relation deltas (ΔCtrl) near zero.
- **quote**: Ablating top spatial features lowers VSR accuracy by 6-31%, with means of -10.1, -12.3 and -14.6% for MMDiff-Llama, MMDiff-Gemma and MMDiff-Qwen, while leaving general VQA nearly unchanged (|ΔVQA| ≤ 1.5%), the control deltas are near zero, supporting spatially specific causal involvement.
- **conditions**: Three backbones: LLaVA-MORE (LLaMA-3.1-8B, LLaMA-Scope TopK SAE), PaliGemma 2 (Gemma-2-2B, Gemma-Scope JumpReLU SAE), InternVL3.5-2B (Qwen3-1.7B backbone, Qwen-Scope TopK SAE). Eval: VQAv2 (ΔVQA control) + VSR dataset (target). Table 1, §5.1, page ~6.
- **confidence**: high
- **supersedes**: n/a — new primary result, no prior target-survey claim about multimodal spatial feature ablation exists to update.

### 4
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: Diffing-discovered unsafe features, when causally ablated, reduce multimodal-safety attack success rate with no measurable cost to general VQA or to a benign-input safety control — a targeted (not blanket-capability) safety intervention, at a scale (1,061 candidate features swept) larger than a handful of cherry-picked examples.
- **numbers**: Per-category top feature: ASR drop 17-28% (Table 4: Self-Harm -28.14%, Erotic -26.59%, Privacy -25.99%, Violent -24.43%, Hate -21.08%, Illegal Activity -17.96%), |ΔVQA| ≤ 1%, ΔCtrl ≤ 1%. Swept across 1,061 candidate safety features: mean ΔASR = -9.67%, ΔVQA Acc = -0.03%, ΔCtrl = +0.41%.
- **quote**: Each top feature reduces VLSBench ASR by 17-28% with |ΔVQA| ≤ 1% and ΔCtrl ≤ 1%, indicating that the safety reduction is targeted rather than a generic capability degradation.
- **conditions**: PaliGemma 2 only (Gemma-2-2B). VLSBench unsafe split (6 categories) as target, ASR judged by Qwen3-VL-8B-Instruct; controls: VQAv2 Yes/No subset and MSSBench safe split (76 embodied-action + 24 chat samples, baseline ASR ≈ 0). Table 4, §5.2, page ~7.
- **confidence**: high
- **supersedes**: n/a — new primary result; no prior target-survey claim on multimodal-safety feature ablation exists.

### 5
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: Diffing-discovered OCR-selective features (chosen via per-token contrastive firing against neutral prompts, ruling out lexical artifacts) causally ablate the targeted OCR-category behavior with minimal spillover to general VQA or non-OCR control, and 'lexical-artifact filtering' materially prunes the candidate set (~40% removed).
- **numbers**: Mean ΔCat (OCRBench category-subset drop) across 5 top features: -16.9%, |ΔVQA| ≤ 1.6%, |ΔCtrl| ≤ 1.8% (Table 5: Scene Text -28.0%/-16.5%, Non-Semantic -16.0%, Digit -14.0%, Irregular -10.0%). Contrastive firing on MMDiff-Gemma yields 1,070 OCR-selective features; on the spatial sweep ~60% of candidates pass the lexical filter (i.e. ~40% pruned as lexical artifacts).
- **quote**: Across five top features the mean ΔCat is -16.9% with |ΔVQA| ≤ 1.6% and |ΔCtrl| ≤ 1.8%, indicating targeted suppression of OCR capability without degrading general VQA performance.
- **conditions**: PaliGemma 2 (Gemma-2-2B), OCRBench official categories (Scene Text-centric VQA, Non-Semantic Text, Digit String, Irregular Text), VQA-clean non-OCR subset as control. Table 5, §5.3, page ~7.
- **confidence**: high
- **supersedes**: n/a — new primary result.

### 6
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: MMDiff-CAA (a diffing-derived SAE feature direction injected at its associated layer, combined with multi-layer backbone contrastive-activation-addition) improves steering accuracy over vanilla single-layer CAA on both spatial and OCR tasks, and the paper's own decomposition shows the gain is jointly attributable to layer targeting and the injected SAE direction, not the SAE direction alone.
- **numbers**: Spatial (10 features, PaliGemma 2 base): vanilla CAA mean +8.96% ΔVSR Acc → MMDiff-CAA mean +12.59% (peak +30.77% on 'ahead of', vs. CAA's +15.38% on the same feature). Decomposition: single-layer CAA +8.96 → CAA extended to discovered feature layers +10.78 → + injected decoder direction +12.59. OCR (5 features): vanilla CAA mean +2.21% → MMDiff-CAA mean +4.02% (peak +10.58% on L17/F13602; on L19/F10089 MMDiff-CAA is within 0.2% of vanilla CAA).
- **quote**: Decomposing the method on the same features, single-layer CAA gives +8.96, extending CAA to the discovered feature layers gives +10.78, and adding the feature's decoder direction gives +12.59, so layer selection and the injected direction contribute in comparable measure.
- **conditions**: PaliGemma 2 base model only; γ_f ∈ {1,3,10} for the injected feature-direction strength. Table 3 (spatial), Table 6 (OCR), §5.1/§5.3, pages ~6-8.
- **confidence**: high
- **supersedes**: Partial nuance to the target survey's SAE-underperforms-at-action framing (evaluation-and-metrics.md §10.4 RAVEL/SAEBench discussion, 'off-the-shelf SAEs generally underperform the supervised skyline'); see `contradictions` field — this does not clear the bar for a full supersede because the baseline compared against (single-layer CAA) is weaker than the strongest non-SAE alternative, and the paper's own decomposition attributes a comparable share of the gain to layer selection rather than the SAE feature itself.

### 7
- **paper**: mi26-multimodal-model-diffing.pdf
- **claim**: Cross-stage ablation (comparing the same SAE features ablated on a pretrained-only vs. instruction-tuned checkpoint of the same model) demonstrates model diffing can localize *when* in training a capability is acquired, not just *whether* a feature is causal — a diagnostic capability the target survey's crosscoder aside does not describe.
- **numbers**: Instruction tuning amplifies the causal contribution of the same features by roughly 3x on average (Table 2: e.g. layer 9/feature 387 'right side of' goes from Δ1pre=-2.08% to Δft=-30.62%; layer 14/feature 10561 'close to' from -7.53% to -18.28%). Two features (L13/F15219 'behind', L12/F2257 'facing') reverse sign entirely, from near-zero/positive pre-tuning (+1.55%, +3.27%) to clearly negative post-tuning (-8.04%, -6.86%).
- **quote**: Instruction tuning amplifies the causal contribution by roughly 3× on average. Two features (L13/F15219, L12/F2257) reverse sign, acting as noise before instruction tuning but producing clear negative deltas afterward, indicating that these spatial behaviors are introduced during multimodal training rather than inherited from the pretrained variant.
- **conditions**: PaliGemma 2 pretrained variant (pt-448, has vision encoder + projector, lacks instruction-tuning) vs. instruction-tuned (mix-448); same MMDiff-Gemma SAE features, same VSR evaluation, only the checkpoint differs. Table 2, §5.1, page ~6-7.
- **confidence**: high
- **supersedes**: n/a — new primary result and a new methodological capability (training-stage localization via diffing) not present in the target survey's crosscoder-diffing treatment.

### 8
- **paper**: mi26-survey-circuits-sparse-symbolic.pdf
- **claim**: The mi26 survey names 'Activation Oracles' (AOs) — training a separate LLM to answer natural-language questions about a target model's internal activations — as an emerging alternative to explicit circuit/feature mapping, with strong reported results on auditing (detecting emergent misalignment, hidden dangerous behavior, hidden knowledge post-fine-tuning) but a caveat that the oracle can produce plausible-but-incorrect explanations. This is second-hand (mi26 summarizing an Anthropic blog post) and not yet in the target survey's automation family.
- **numbers**: n/a — mi26 survey gives no quantitative auditing accuracy/precision numbers for AOs in the sections read; narrative claim only ('AOs have shown strong results in auditing').
- **quote**: Instead of manually searching for and reconstructing internal circuits, this approach feeds internal neural activations from a target model as additional input into a specially trained language model, the oracle. The oracle then learns to answer natural-language questions about what is happening inside the target model.
- **conditions**: mi26 survey §4.3 (Sparse Autoencoders section, presented as an SAE alternative). Cites Karvonen et al., 'Activation oracles: Training and evaluating LLMs as general-purpose activation explainers,' Anthropic Alignment Science Blog, 2025 (reference [38] in mi26 survey). Page ~10.
- **confidence**: medium
- **supersedes**: n/a — candidate new §8 (automation/frontier) addition, but flagged second-hand-of-second-hand (mi26 summarizing a 2025 blog post, not a peer-reviewed 2026 primary source) per the citation-integrity rule; do not cite mi26's paraphrase as the AO claim's source — fetch the Anthropic blog post directly before adding to the survey.

### 9
- **paper**: mi26-survey-circuits-sparse-symbolic.pdf
- **claim**: mi26 survey names 'WeightLens' and 'CircuitLens' (Golimblevskaia et al., 2026) as new automated tools for transcoder-based circuit analysis that go 'beyond activations' — a 2026 primary paper not yet reflected in the target survey's automation-family inventory, though mi26 gives no method detail or numbers for either tool in the sections read.
- **numbers**: n/a — mi26 survey states only that the tools were introduced, no benchmark or comparison numbers given in the excerpted passage.
- **quote**: Golimblevskaia et al. [43] introduce two new automated tools for transcoder analysis: WeightLens and CircuitLens.
- **conditions**: mi26 survey §4.4 (Sparse Feature Circuits / transcoders discussion). Cites Golimblevskaia, Jain, Puri, Ibrahim, Samek, Lapuschkin, 'Circuit insights: Towards interpretability beyond activations,' arXiv:2510.14936, 2026 (mi26 reference [43]). Page ~10.
- **confidence**: medium
- **supersedes**: n/a — candidate new §8 addition; second-hand mention only (one sentence, no mechanism described) — fetch arXiv:2510.14936 directly before citing any method claim about WeightLens/CircuitLens in the survey.

### 10
- **paper**: mi26-survey-circuits-sparse-symbolic.pdf
- **claim**: The mi26 survey's own stated central open question for the field in 2026 is explicitly the frontier-scaling question: whether interpretability techniques validated on narrow behaviors / small models generalize to frontier-scale systems — corroborating (not contradicting) the target survey's open-problems framing, and independently naming 'automated circuit discovery,' 'stronger evaluation benchmarks,' 'reliable causal-feature identification,' and 'interpretable-by-design' architectures as the priority directions.
- **numbers**: n/a — qualitative field-consensus statement, not a metric.
- **quote**: Its central open question is whether the techniques that work on narrow behaviors and smaller systems can scale to the complexity of frontier models. If they can, mechanistic interpretability may become one of the key foundations for AI safety and alignment. If they cannot, it risks remaining a set of elegant but limited demonstrations.
- **conditions**: mi26 survey §7.4 'Future Work' (closing section, immediately before References). Page ~17-18.
- **confidence**: high
- **supersedes**: n/a — corroborates the target survey's existing open-problems-and-roadmap.md framing rather than updating a specific claim; useful as an independent 2026 confirmation for §15 that the field has not resolved the scaling question, and that 'interpretable by design' (sparsity/modularity/concept-bottlenecks built into training, not post-hoc) is being actively floated as a 2026 alternative to post-hoc discovery.

## contradictions
Weak/partial tension only, flagged per calibration-residuals discipline (not a clean supersede): MMDiff-CAA (SAE-discovered feature direction + multi-layer backbone CAA) beats *vanilla single-layer CAA* by +3.6% (spatial) and +1.8% (OCR) on average (peak +15.4% / +10.58%) — §5.1 Table 3, §5.3 Table 6. This is in tension with the survey's framing that SAEs "underperform simple baselines at action" (steering), but the comparison is narrower than that framing requires: the baseline is single-layer CAA, not the strongest non-SAE steering method, and the gain is a decomposition where "extending CAA to the discovered feature layers gives +10.78, adding the feature's decoder direction gives +12.59" (i.e., much of the lift is *layer selection*, only partly the SAE feature itself, App. E.1 per §5.1 text) — so this does not clear the bar to say SAEs now win at action; it says a diffing-derived SAE feature can improve a weak CAA baseline when combined with layer targeting. Record it as a nuance for §12/15, not a reversal.

## gaps
(1) mi26 survey's Activation-Oracles and WeightLens/CircuitLens mentions carry no primary numbers reproducible from this paper alone — both are second-hand summaries (of an Anthropic blog post and of Golimblevskaia et al. 2026 respectively); the mi26 survey gives no benchmark figures for either, only narrative description, so §8 additions from these should be flagged second-hand-of-second-hand until the primary sources are fetched. (2) MMDiff discloses only 3 backbones (LLaMA-3.1-8B / Gemma-2-2B / Qwen3-1.7B, all ≤8B) and states safety+OCR were evaluated on PaliGemma 2 only (§8 Limitations) — no frontier-scale (>10B) validation, which is directly relevant to §15's "does this scale to frontier models" open question and should be stated as a scope limit, not silently generalized. (3) MMDiff's steering paragraph mentions seed/statistical procedure only via "Fisher's exact test with Benjamini-Hochberg correction" for feature selection significance (§4) — no seed count or CI is given for the reported deltas (Tables 1-6) in the sections read; do not state these as CIs. (4) mi26 survey provides no dedicated evaluation-rigor section comparable to the target survey's RAVEL/SAEBench treatment — its SAE-limitation claim rests on a single citation ([58] Makelov et al.) without a metric definition, so it corroborates but does not extend the target survey's existing (already more rigorous) §12.2/evaluation-and-metrics.md treatment.

## critic
{
 "sufficient": true,
 "missing": [
  "MMDiff Table 14 / App. E.1 \u2014 THE decisive omission. The full steering decomposition is: SAE feature direction ALONE = +2.63 \u0394VSR (single feature) and +3.66 (all ten); single-layer vanilla CAA = +8.96; multi-layer CAA = +10.78; MMDiff-CAA = +12.59. The paper's own sentence: 'SAE feature steering improves VSR by 2.63 with a single feature and 3.66 with all ten, well below either CAA variant, so the direction is not sufficient on its own.' The extraction reported only the +8.96\u2192+10.78\u2192+12.59 chain and dropped the two rows that arbitrate the SAE-vs-baseline question. Recoverable from the same PDF the agent cited (it named App. E.1).",
  "MMDiff Table 9 + App. C.5/E.2 cross-seed evidence \u2014 the extraction declared this a gap ('no seed count ... is given'); it is present and recovered. Two SAE training runs differing only in seed and data order, across the 8 layers hosting the top spatial features: mean same-index decoder cosine 0.93, median 0.955\u20130.962, 84% of features \u22650.9, cross-seed relocation 0.44% (\u224872 of 16,384 features/layer), top-10 reported features mean cosine 0.98. Plus Table 15 full-dictionary explicit matching (26 layers \u00d7 16,384): Preserved 96.41% (410,709), Rotated-in-place 3.36% (14,295), Relocated 0.00% (0), Emergent 0.23% (971), and '9 of our top 10 spatial features fall in the bottom quartile of their layer's rotation distribution.' This is directly load-bearing for the survey's SAE-instability thread in \u00a712/\u00a715. What IS absent is seeds/CIs on the reported causal deltas (Tables 1\u20136) \u2014 state that narrowly, not as 'no seed evidence'.",
  "MMDiff \u00a75.1 eval-set construction: 'each feature is scored on a VSR subset constructed from its top-activating samples, so that the evaluation directly targets the spatial behavior that the feature most strongly encodes.' Every \u0394VSR in Table 1 is measured on a per-feature curated subset, not a fixed held-out split. No record's `conditions` discloses this. It is the rig-precondition check (calibration-residuals #6) and it caps how the magnitudes may be described.",
  "MMDiff \u00a78 Limitations, two caveats omitted: (a) 'a minority of safety candidates cause generation collapse rather than refusal when ablated, and currently require a post-hoc filter to exclude' \u2014 a post-hoc filter sits behind the safety numbers in record 4; (b) 'MMDiff CAA assumes access to an instruction-tuned reference model from which the steering direction can be extracted; in settings where only the base or only the instruction-tuned model is available, the recipe reduces to standard SAE-feature steering' \u2014 a hard scope limit on record 6.",
  "MMDiff steering is measured on the BASE model, not a deployed MLLM. \u00a74: MMDiff-CAA 'combines two components on M_base', with the CAA directions 'extracted from M_vlm'; Tables 3, 6 and 14 are all captioned 'PaliGemma 2 base'. The experiment steers a pre-instruction-tuned model using directions harvested from its instruction-tuned sibling. Record 6's bare 'PaliGemma 2 base model only' does not convey this, and it is what the +12.59 actually means.",
  "Table 1(c) MMDiff-Qwen lists n=4 features vs n=10 for Llama and Gemma \u2014 the \u221214.6% mean is over 4 features. Record 3 asserts three-family replication without the n asymmetry. Relatedly, Table 10's MMDiff-Qwen '\u22482,800 discovered' carries a dagger: the lexical filter was run on a 400-feature sample and the count EXTRAPOLATED.",
  "Table 7 row omitted: '+ lexical' (F\u2713 L\u2713, no adapted filter) = \u221214.6% VSR / \u221224.4% VQA \u2014 this is the row proving the lexical filter alone does not prevent global disruption. Also \u00a76.1: 'Rotation without visual energy selects no features.' Both complete the necessity argument the headline rests on.",
  "mi26 survey \u00a77.3 'Neurosymbolic Rule Extraction and Its Limits' \u2014 not returned at all, and it is the passage that decid
