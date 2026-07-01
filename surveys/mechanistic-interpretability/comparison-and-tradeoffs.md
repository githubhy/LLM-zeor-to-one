<!-- sec:11 -->
## <a id="sec-11"></a>11 Comparison & tradeoffs

<!-- sec:11.1 -->
### <a id="sec-11.1"></a>11.1 Master comparison matrix

<a id="p-111-master-comparison-matrix-1"></a><!-- para:111-master-comparison-matrix-1 --> Every method in the inventory (§§ <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)–<!-- secxref:8 -->[§8](method-inventory-automation.md#sec-8)), scored on fixed axes. "Evidence" is Axis 1 (observational vs. interventional); "Grain" is Axis 2 (Rep/Feat/Circuit); "Cost" is order-of-magnitude compute (forward/backward passes or training); "Access" is what you must have (activations, gradients, weights, or a trainable copy); "Assumptions & failure cost" is the extra data/compute the method needs and how it misleads when its assumption breaks.

| Method | Evidence | Grain | Superv. | Cost | Access | Assumptions & failure cost |
|---|---|---|---|---|---|---|
| Linear probing (§ <!-- secxref:4.1 -->[§4.1](method-inventory-observational.md#sec-4.1)) | obs | Rep | labels | 1 fit | activations | LRH + right label frame; *decodable ≠ used* |
| Logit/tuned lens (§ <!-- secxref:4.2 -->[§4.2](method-inventory-observational.md#sec-4.2)) | obs | Rep | self (tuned) | 1 pass (+train) | activations | stable basis; shows recoverable, not committed |
| Attention/head analysis (§ <!-- secxref:4.3 -->[§4.3](method-inventory-observational.md#sec-4.3)) | obs | Circuit | none | 1 pass | attn weights | attention ≠ explanation without a causal check |
| Activation patching (§ <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1)) | interv | Circuit | pairs | O(sites) | activations | good corrupt distribution; self-repair dilutes |
| Path patching (§ <!-- secxref:5.2 -->[§5.2](method-inventory-causal.md#sec-5.2)) | interv | Circuit | pairs | O(edges) | activations | edge count explodes; hand-run only small models |
| Attribution patching (§ <!-- secxref:5.3 -->[§5.3](method-inventory-causal.md#sec-5.3)) | interv | Circuit | pairs | O(1) passes | gradients | linearization fails at softmax saturation |
| ACDC / EAP-IG (§ <!-- secxref:5.4 -->[§5.4](method-inventory-causal.md#sec-5.4)) | interv | Circuit | pairs | O(edges)/O(1) | grad/acts | overlap ≠ faithfulness; verify the output circuit |
| Causal scrubbing (§ <!-- secxref:5.5 -->[§5.5](method-inventory-causal.md#sec-5.5)) | interv | Circuit | hypothesis | O(resamples) | activations | disproves only; cancellation false-positives |
| DAS (§ <!-- secxref:5.6 -->[§5.6](method-inventory-causal.md#sec-5.6)) | interv | Feat | supervised | train rotation | activations | can overfit an alignment; needs a causal model |
| Sparse autoencoder (§ <!-- secxref:6.1 -->[§6.1](method-inventory-dictionary.md#sec-6.1)) | obs | Feat | none | train SAE | activations | superposition + LRH; shrinkage, absorption, dark matter |
| SAE variants (§ <!-- secxref:6.2 -->[§6.2](method-inventory-dictionary.md#sec-6.2)) | obs | Feat | none | train SAE | activations | each fixes L1 shrinkage; disentanglement still weak |
| Transcoders (§ <!-- secxref:6.3 -->[§6.3](method-inventory-dictionary.md#sec-6.3)) | obs→circ | Feat/Circ | none | train TC | activations | sublayer sparsifiable; error residual left over |
| Crosscoders (§ <!-- secxref:6.4 -->[§6.4](method-inventory-dictionary.md#sec-6.4)) | obs | Feat/Circ | none | train XC | multi-layer acts | features align across layers/models; preliminary |
| Steering vectors (§ <!-- secxref:7.1 -->[§7.1](method-inventory-steering-editing.md#sec-7.1)) | interv | Feat | pairs | 1 pass | activations | LRH; coefficient tuning, coherence cost |
| RepE (§ <!-- secxref:7.2 -->[§7.2](method-inventory-steering-editing.md#sec-7.2)) | interv | Feat | pairs | scan + edit | acts/weights | PCA-separable concept; same coherence risk |
| Refusal direction (§ <!-- secxref:7.3 -->[§7.3](method-inventory-steering-editing.md#sec-7.3)) | interv | Feat | pairs | 1 pass/edit | acts/weights | one-direction claim is per-model empirical |
| ROME (§ <!-- secxref:7.4 -->[§7.4](method-inventory-steering-editing.md#sec-7.4)) | interv | Feat (wts) | 1 fact | closed form | weights | MLP-as-memory; edit success ≠ localization |
| MEMIT (§ <!-- secxref:7.5 -->[§7.5](method-inventory-steering-editing.md#sec-7.5)) | interv | Feat (wts) | facts | batched solve | weights | catastrophic forgetting under enough edits |
| Auto-interp (§ <!-- secxref:8.1 -->[§8.1](method-inventory-automation.md#sec-8.1)) | obs | Feat | LLM-labeled | LLM calls | features | predicts activations ≠ causal role |
| Sparse feature circuits (§ <!-- secxref:8.2 -->[§8.2](method-inventory-automation.md#sec-8.2)) | interv | Circuit | none | O(1) + SAE | grad/acts | inherits SAE + attribution-patching failure modes |
| Attribution graphs (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)) | interv | Circuit | none | train CLT | full model | frozen attention approx; error nodes; per-input |

<a id="p-111-master-comparison-matrix-2"></a><!-- para:111-master-comparison-matrix-2 --> Reading the matrix: **cost falls and scale rises left-to-right within the causal family** (patching → attribution patching → automated discovery → attribution graphs), always **trading exactness for coverage**; the **dictionary family is unsupervised but correlational** and only becomes causal when paired with patching (sparse feature circuits, attribution graphs); and **model access is a real cost axis** — probing/patching need only activations, editing needs weights, attribution graphs need to train modules against the full model, which is why frontier-scale work lives at labs with model access.

<!-- sec:11.2 -->
### <a id="sec-11.2"></a>11.2 Selection / decision table

<a id="p-112-selection-decision-table-1"></a><!-- para:112-selection-decision-table-1 --> Given a concrete question, the first-choice method, and what *not* to reach for:

| Your question | Use | Not | Why |
|---|---|---|---|
| Is concept $F$ linearly present at layer $\ell$? | linear probe with selectivity control | raw probe accuracy | control task strips the capacity confound <!-- cite:25 --> [[25]](references.md#ref-25) |
| Does component $H$ *cause* behavior $B$? | activation/path patching | probing, attention maps | only intervention licenses a causal claim (§ <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1)) |
| Find the circuit for $B$ in a small model | path patching, then EAP-IG to scale | plain EAP | overlap ≠ faithfulness; verify with knockout <!-- cite:41 --> [[41]](references.md#ref-41) |
| Discover features unsupervised at scale | SAE (JumpReLU/TopK) + auto-interp | a single per-neuron read | superposition makes neurons polysemantic (§ <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)) |
| Build a legible circuit over features | sparse feature circuits / attribution graphs | neuron-level ACDC | features are more monosemantic than neurons |
| Turn a behavior up/down at inference | difference-in-means steering vector | SAE-feature clamping (by default) | baselines beat naive SAE steering <!-- cite:66 --> [[66]](references.md#ref-66) |
| Remove refusal / add a guardrail direction | refusal-direction ablation/addition | full fine-tune | one-direction edit, minimal capability loss <!-- cite:49 --> [[49]](references.md#ref-49) |
| Edit a specific fact in the weights | ROME (one) / MEMIT (many) | iterated ROME at scale | spreading avoids catastrophic forgetting <!-- cite:51 --> [[51]](references.md#ref-51), <!-- cite:52 --> [[52]](references.md#ref-52) |
| Localize an abstract causal variable | DAS / MDAS | unsupervised SAE alone | supervised skyline beats SAEs on RAVEL <!-- cite:64 --> [[64]](references.md#ref-64) |
| Explain one full forward pass in a frontier model | attribution graphs | GPT-2 circuit porting | circuits do not transport; run on the target <!-- cite:21 --> [[21]](references.md#ref-21) |

<a id="p-112-selection-decision-table-2"></a><!-- para:112-selection-decision-table-2 --> The single most important decision rule, restated: **observation generates hypotheses; only intervention confirms them, and only a faithfulness/completeness check (§ <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1)) — read against the self-repair caveat — turns a confirmed intervention into a trustworthy circuit.**
