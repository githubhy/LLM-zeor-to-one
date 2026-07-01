<!-- sec:1 -->
## <a id="sec-1"></a>1 Introduction & scope

<!-- sec:1.1 -->
### <a id="sec-1.1"></a>1.1 What "mechanistic" means

<a id="p-11-what-mechanistic-means-1"></a><!-- para:11-what-mechanistic-means-1 --> Interpretability research asks what a neural network is doing on the inside. It splits into distinct
research programs by *what kind of answer* counts as an explanation, and mechanistic interpretability
occupies the most demanding corner.

- <a id="p-11-what-mechanistic-means-2"></a><!-- para:11-what-mechanistic-means-2 --> **Post-hoc attribution / classical XAI** (saliency maps, Integrated Gradients <!-- cite:79 --> [[79]](references.md#ref-79), SHAP, LIME)
  assigns an importance score to each *input* feature for a given prediction. It answers "which
  inputs mattered," but says nothing about the internal algorithm, and its scores are famously
  fragile.
- **Representational interpretability** (probing <!-- cite:24 --> [[24]](references.md#ref-24), <!-- cite:25 --> [[25]](references.md#ref-25), the linear-representation-hypothesis
  literature <!-- cite:2 --> [[2]](references.md#ref-2), <!-- cite:4 --> [[4]](references.md#ref-4)) asks what information is *encoded* in a layer's activations. It is about the
  network's *state*, and — as § <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1) makes
  precise — decodability is not use.
- **Mechanistic interpretability** asks for the *algorithm*: which components, connected how, compute
  the behavior, and via what intermediate features. Its explanatory unit is the **circuit** — a
  subgraph of the model's computation, expressed in features rather than raw neurons, that is claimed
  to *causally* implement a behavior. The claim is falsifiable: if the circuit is the mechanism, then
  ablating everything outside it should leave the behavior intact (**faithfulness**), and ablating
  parts inside it should break the behavior (**minimality**) — see
  § <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1).

<a id="p-11-what-mechanistic-means-3"></a><!-- para:11-what-mechanistic-means-3 --> The word "mechanistic" is doing real work: an MI explanation is expected to be *causal* and
*mechanism-level*, testable by intervention, not merely correlational or plausible. That standard —
and the many ways it is imperfectly met in practice — organizes this entire survey.

<!-- sec:1.2 -->
### <a id="sec-1.2"></a>1.2 Why it matters

<a id="p-12-why-it-matters-1"></a><!-- para:12-why-it-matters-1 --> Three motivations recur, in roughly increasing order of ambition.

1. <a id="p-12-why-it-matters-2"></a><!-- para:12-why-it-matters-2 --> **Debugging and science of deep learning.** A model that we can read is a model whose failures
   (hallucination, bias, brittle heuristics) we can localize and, sometimes, fix
   (§ <!-- secxref:13 -->[§13](applications.md#sec-13)). Reverse-engineering also turns deep learning
   into a natural science: the discovery that a toy transformer learns *modular addition by discrete
   Fourier transform* <!-- cite:55 --> [[55]](references.md#ref-55) is a mechanistic fact about what gradient descent finds, not a story.
2. **Auditing and monitoring.** If deceptive or dangerous cognition leaves an internal signature, a
   cheap internal probe can flag it even when black-box behavior looks benign — the "sleeper agent"
   result <!-- cite:70 --> [[70]](references.md#ref-70), <!-- cite:71 --> [[71]](references.md#ref-71) is the sharpest example (§ <!-- secxref:13.1 -->[§13.1](applications.md#sec-13.1)).
3. **Safety of advanced systems.** The strongest version of the motivation — a reliable "MRI for AI"
   that could certify a frontier model is not planning harm — is explicitly aspirational; Anthropic's
   own leadership frames it as a bet that is *5–10 years* from maturity and may not arrive before the
   capabilities it would police <!-- cite:76 --> [[76]](references.md#ref-76). This survey treats that gap as a fact to characterize, not a
   promise to repeat.

<!-- sec:1.3 -->
### <a id="sec-1.3"></a>1.3 Origins, scope, and exclusions

<a id="p-13-origins-scope-and-exclusions-1"></a><!-- para:13-origins-scope-and-exclusions-1 --> **Origins.** MI's lineage runs through the Distill *Circuits* thread on vision models — Olah et al.'s
claim that features are directions, that they wire up into circuits, and that circuits recur across
models ("universality") <!-- cite:2 --> [[2]](references.md#ref-2) — and was ported to transformers by the *Mathematical Framework for
Transformer Circuits* <!-- cite:1 --> [[1]](references.md#ref-1), which gave the residual-stream / QK-OV language the rest of the field now
speaks. The two subsequent inflection points are *Toy Models of Superposition* <!-- cite:3 --> [[3]](references.md#ref-3) (why features
hide) and *Towards Monosemanticity* <!-- cite:7 --> [[7]](references.md#ref-7) (how to pull them back out with dictionary learning).

<a id="p-13-origins-scope-and-exclusions-2"></a><!-- para:13-origins-scope-and-exclusions-2 --> **Scope of this survey.** The method inventory (§§ <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)–<!-- secxref:8 -->[§8](method-inventory-automation.md#sec-8))
is tiered by the depth-tier governor in `index.md`. The "across models" spine
(§ <!-- secxref:9 -->[§9](circuits-across-models.md#sec-9)) deliberately tracks *which model each
result was shown on and whether it transports* — toy and algorithmic models, GPT-2 (small/XL),
the Pythia suite, GPT-J, Gemma 2, and Claude 3 — with the field's InceptionV1/CLIP vision roots
kept as origin context <!-- cite:2 --> [[2]](references.md#ref-2). Evaluation (§ <!-- secxref:10 -->[§10](evaluation-and-metrics.md#sec-10)),
the comparison matrix (§ <!-- secxref:11 -->[§11](comparison-and-tradeoffs.md#sec-11)), current
practice and the SAE debate (§ <!-- secxref:12 -->[§12](state-of-the-art-and-practice.md#sec-12)),
applications (§ <!-- secxref:13 -->[§13](applications.md#sec-13)), design guidance
(§ <!-- secxref:14 -->[§14](design-guidance.md#sec-14)), and open problems
(§ <!-- secxref:15 -->[§15](open-problems-and-roadmap.md#sec-15)) close the arc.

<a id="p-13-origins-scope-and-exclusions-3"></a><!-- para:13-origins-scope-and-exclusions-3 --> **Exclusions (scope boundaries).**

- <a id="p-13-origins-scope-and-exclusions-4"></a><!-- para:13-origins-scope-and-exclusions-4 --> **Not general post-hoc XAI.** SHAP, LIME, Grad-CAM, and pure saliency are covered only as a
  contrast to MI's causal stance (§ <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1));
  Integrated Gradients <!-- cite:79 --> [[79]](references.md#ref-79) appears because attribution *patching* borrows its path-integral trick,
  not as an interpretability method in its own right.
- **Not a transformer-architecture survey.** The fundamentals cover only what MI needs — the
  residual stream and attention/MLP as read/write operations — not the full design space of attention
  variants, positional encodings, or normalization.
- **Not an alignment/training survey.** Safety *applications* of MI are in scope
  (§ <!-- secxref:13 -->[§13](applications.md#sec-13)); the RLHF/DPO/red-teaming machinery those
  applications sit next to is not.
- **Concept-based interpretability** (TCAV, prototype networks) is mentioned only where it clarifies
  the boundary of the linear-representation view.
