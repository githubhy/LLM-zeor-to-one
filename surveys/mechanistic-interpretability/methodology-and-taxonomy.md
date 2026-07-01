<!-- sec:3 -->
## <a id="sec-3"></a>3 Methodology & taxonomy

<!-- sec:3.1 -->
### <a id="sec-3.1"></a>3.1 The canonical loop, and why intervention is load-bearing

<a id="p-31-the-canonical-loop-and-why-intervention-is-load-bearing-1"></a><!-- para:31-the-canonical-loop-and-why-intervention-is-load-bearing-1 --> Almost every mechanistic result is produced by the same four-step loop:

1. <a id="p-31-the-canonical-loop-and-why-intervention-is-load-bearing-2"></a><!-- para:31-the-canonical-loop-and-why-intervention-is-load-bearing-2 --> **Observe** — look at activations, attention patterns, or weights and form a guess about what a
   component represents or does (probes, lenses, attention maps; § <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)).
2. **Hypothesize** — state a candidate feature or circuit: "head 9.9 copies the indirect-object name,"
   "this direction encodes refusal," "these MLP layers store the fact."
3. **Intervene** — change the internal state (patch, ablate, steer, edit) and measure the effect on a behavioral metric (§ <!-- secxref:5 -->[§5](method-inventory-causal.md#sec-5) and § <!-- secxref:7 -->[§7](method-inventory-steering-editing.md#sec-7)).
4. **Validate** — check the intervention's effect matches the hypothesis, quantitatively
   (§ <!-- secxref:10 -->[§10](evaluation-and-metrics.md#sec-10)).

<a id="p-31-the-canonical-loop-and-why-intervention-is-load-bearing-3"></a><!-- para:31-the-canonical-loop-and-why-intervention-is-load-bearing-3 --> Step 3 is what makes the loop *mechanistic* rather than merely *representational*, and the reason is the
single most important methodological fact in the field: **decodability is not use.** A probe that reads
a concept from a layer with high accuracy establishes only that the information is *present and linearly
recoverable* — not that the model's forward computation actually reads it out and acts on it <!-- cite:26 --> [[26]](references.md#ref-26). The
gap is not hypothetical: Hewitt & Liang <!-- cite:25 --> [[25]](references.md#ref-25) show that a sufficiently expressive probe attains high
accuracy even on a *control task* with randomly-assigned labels, so probe accuracy alone measures the
probe's capacity as much as the representation's content; their **selectivity** metric (real-task minus
control-task accuracy) is designed to strip that confound out. Only a causal intervention — remove the
information and watch the behavior change — licenses the mechanistic claim. This is why the survey's
center of gravity is the causal-methods family, and why observational methods
(§ <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)) are framed as hypothesis
*generators* whose outputs must be causally confirmed.

<!-- sec:3.2 -->
### <a id="sec-3.2"></a>3.2 A two-axis taxonomy of methods

<a id="p-32-a-two-axis-taxonomy-of-methods-1"></a><!-- para:32-a-two-axis-taxonomy-of-methods-1 --> The method inventory (§§ <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)–<!-- secxref:8 -->[§8](method-inventory-automation.md#sec-8))
is large; it is easiest to navigate along two orthogonal axes. **Axis 1 — epistemic status:** is the
method *observational* (reads state, yields correlational evidence) or *interventional* (changes state,
yields causal evidence)? **Axis 2 — granularity:** does it target a *representation* (what a layer
encodes), a *feature* (a single interpretable direction), or a *circuit* (how components compose)? A
third practical dimension cuts across both: *supervision* — does the method need labels or contrast
pairs (probing, DAS, steering vectors), or is it unsupervised (SAEs, ACDC)?

| Method family | Axis 1 (evidence) | Axis 2 (granularity) | Supervision | Section |
|---|---|---|---|---|
| Linear probing | observational | representation | supervised | § <!-- secxref:4.1 -->[§4.1](method-inventory-observational.md#sec-4.1) |
| Logit / tuned lens | observational | representation | self-supervised (tuned) | § <!-- secxref:4.2 -->[§4.2](method-inventory-observational.md#sec-4.2) |
| Attention / weight analysis | observational | circuit | none | § <!-- secxref:4.3 -->[§4.3](method-inventory-observational.md#sec-4.3) |
| Activation / path patching | interventional | circuit | contrastive pairs | §§ <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1)–<!-- secxref:5.2 -->[§5.2](method-inventory-causal.md#sec-5.2) |
| Attribution patching, ACDC, EAP | interventional | circuit | contrastive pairs | §§ <!-- secxref:5.3 -->[§5.3](method-inventory-causal.md#sec-5.3)–<!-- secxref:5.4 -->[§5.4](method-inventory-causal.md#sec-5.4) |
| Causal scrubbing, DAS | interventional | circuit / feature | hypothesis / supervised | §§ <!-- secxref:5.5 -->[§5.5](method-inventory-causal.md#sec-5.5)–<!-- secxref:5.6 -->[§5.6](method-inventory-causal.md#sec-5.6) |
| Sparse autoencoders + variants | observational (of features) | feature | unsupervised | § <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6) |
| Transcoders / crosscoders | observational → circuit | feature / circuit | unsupervised | §§ <!-- secxref:6.3 -->[§6.3](method-inventory-dictionary.md#sec-6.3)–<!-- secxref:6.4 -->[§6.4](method-inventory-dictionary.md#sec-6.4) |
| Steering vectors, RepE | interventional | feature | contrastive pairs | §§ <!-- secxref:7.1 -->[§7.1](method-inventory-steering-editing.md#sec-7.1)–<!-- secxref:7.2 -->[§7.2](method-inventory-steering-editing.md#sec-7.2) |
| Model editing (ROME/MEMIT) | interventional | feature (weights) | single fact | §§ <!-- secxref:7.4 -->[§7.4](method-inventory-steering-editing.md#sec-7.4)–<!-- secxref:7.5 -->[§7.5](method-inventory-steering-editing.md#sec-7.5) |
| Auto-interp | observational | feature | LLM-labeled | § <!-- secxref:8.1 -->[§8.1](method-inventory-automation.md#sec-8.1) |
| Attribution graphs | interventional | circuit | unsupervised (via transcoders) | § <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3) |

<a id="p-32-a-two-axis-taxonomy-of-methods-2"></a><!-- para:32-a-two-axis-taxonomy-of-methods-2 --> The taxonomy also explains the field's *arc*: early work lived in the top-right (hand-built circuits
from observation + patching), then dictionary learning opened the unsupervised-feature quadrant at
scale, and the current frontier (attribution graphs) is an attempt to get back to *circuits* — but
built on unsupervised features rather than hand-labeled neurons. The method cards that follow use a
uniform template (one-line idea → placement/lineage → derivation → intuition → limits → complexity →
failure modes → epistemic tag) so entries stay decision-comparable regardless of quadrant.
