<!-- sec:8 -->
## <a id="sec-8"></a>8 Method inventory V — automation and the current frontier

<a id="p-8-method-inventory-v-automation-and-the-current-frontier-1"></a><!-- para:8-method-inventory-v-automation-and-the-current-frontier-1 --> Circuit analysis by hand does not scale; this family automates the labeling of features and the construction of circuits, culminating in attribution graphs — the current frontier artifact.

<!-- sec:8.1 -->
### <a id="sec-8.1"></a>8.1 Automated interpretability (auto-interp) [load-bearing]

<a id="p-81-automated-interpretability-auto-interp-load-bearing-1"></a><!-- para:81-automated-interpretability-auto-interp-load-bearing-1 --> **One-line idea.** Use an LLM to write a natural-language explanation of a feature/neuron, then score the explanation by how well a second LLM can predict the feature's activations.

<a id="p-81-automated-interpretability-auto-interp-load-bearing-2"></a><!-- para:81-automated-interpretability-auto-interp-load-bearing-2 --> **Placement & lineage.** Bills et al. (OpenAI <!-- cite:68 --> [[68]](references.md#ref-68)) for neurons; adapted to SAE features by the SAE papers and open-sourced as EleutherAI's Delphi <!-- cite:69 --> [[69]](references.md#ref-69). The only way to interpret millions of SAE features at all.

<a id="p-81-automated-interpretability-auto-interp-load-bearing-3"></a><!-- para:81-automated-interpretability-auto-interp-load-bearing-3 --> **Mechanism.** Three stages: (1) **explain** — show an LLM (e.g. GPT-4) the top-activating text fragments for a feature and have it describe when the feature fires; (2) **simulate** — show a second LLM the explanation plus held-out fragments and have it predict per-token activations; (3) **score** — correlate simulated vs. actual activations. High correlation ⇒ the feature's behavior is captured by a short description ⇒ "interpretable." Delphi drops the cost of auto-interpreting ~1.5M GPT-2 features from ~\$200k (GPT-4-driven) to ~\$1,300 (open-model-driven) <!-- cite:69 --> [[69]](references.md#ref-69). *(Cost figures are from <!-- cite:69 --> [[69]](references.md#ref-69); verified in the citation-audit pass.)*

<a id="p-81-automated-interpretability-auto-interp-load-bearing-4"></a><!-- para:81-automated-interpretability-auto-interp-load-bearing-4 --> **Limits & epistemic tag.** An explanation that predicts activations is not a guarantee of causal role; auto-interp scores can reward superficially-consistent-but-shallow labels. *Indispensable at scale; a proxy for interpretability, not a proof of it.*

<!-- sec:8.2 -->
### <a id="sec-8.2"></a>8.2 Sparse feature circuits [load-bearing]

<a id="p-82-sparse-feature-circuits-load-bearing-1"></a><!-- para:82-sparse-feature-circuits-load-bearing-1 --> **One-line idea.** Build circuits whose nodes are *SAE features* rather than neurons or heads, connected by (attribution-)patched edges — a human-interpretable causal graph in the feature basis.

<a id="p-82-sparse-feature-circuits-load-bearing-2"></a><!-- para:82-sparse-feature-circuits-load-bearing-2 --> **Placement & lineage.** Marks et al. <!-- cite:81 --> [[81]](references.md#ref-81); the synthesis of dictionary learning (§ <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6)) with causal patching (§ <!-- secxref:5 -->[§5](method-inventory-causal.md#sec-5)), and the conceptual precursor to attribution graphs.

<a id="p-82-sparse-feature-circuits-load-bearing-3"></a><!-- para:82-sparse-feature-circuits-load-bearing-3 --> **Mechanism.** Replace each component's activations with their SAE decomposition, then use attribution patching (§ <!-- secxref:5.3 -->[§5.3](method-inventory-causal.md#sec-5.3)) to score edges *between features*, keeping those above a threshold. Because features are (more) monosemantic than neurons, the resulting graph is far more legible than a neuron-level circuit, and — the practical payoff — editing the discovered features can remove unintended behaviors (e.g. spurious cues) with minimal collateral damage <!-- cite:81 --> [[81]](references.md#ref-81).

<a id="p-82-sparse-feature-circuits-load-bearing-4"></a><!-- para:82-sparse-feature-circuits-load-bearing-4 --> **Epistemic tag.** *The bridge from feature dictionaries back to circuits; superseded in scale by attribution graphs but conceptually foundational.*

<!-- sec:8.3 -->
### <a id="sec-8.3"></a>8.3 Circuit tracing / attribution graphs [headline]

<a id="p-83-circuit-tracing-attribution-graphs-headline-1"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-1 --> **One-line idea.** Replace every MLP with a cross-layer transcoder, build an input-specific *linear* replacement model, and read off an end-to-end causal graph of a single forward pass in a frontier model.

<a id="p-83-circuit-tracing-attribution-graphs-headline-2"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-2 --> **Placement & lineage.** Anthropic's March-2025 pair — the methods paper "Circuit Tracing" <!-- cite:20 --> [[20]](references.md#ref-20) and the case-study paper "On the Biology of a Large Language Model" <!-- cite:21 --> [[21]](references.md#ref-21) — applied to Claude 3.5 Haiku. This is the state of the art in circuit-level MI and the destination of the SAE→transcoder pivot (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)).

<a id="p-83-circuit-tracing-attribution-graphs-headline-3"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-3 --> **Mechanism, in three moves.**

1. <a id="p-83-circuit-tracing-attribution-graphs-headline-4"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-4 --> **Cross-layer transcoder (CLT).** Generalize the single-layer transcoder (§ <!-- secxref:6.3 -->[§6.3](method-inventory-dictionary.md#sec-6.3)): one bank of sparse features whose activation at layer $\ell$ contributes to the MLP output at layer $\ell$ *and all later layers*, matching the fact that real MLP computations spread across depth.
2. **Local replacement model.** For one fixed prompt, swap each true MLP for its CLT reconstruction, **freeze attention patterns (<!-- secxref:Q.4 -->[§Q.4](appendix-q-reader-questions.md#sec-Q.4))** at their real values (attention is left nonlinear because it is harder to sparsify), and add a per-layer **error node** equal to (true output $-$ CLT output). By construction this replacement reproduces the original model's output *exactly on that input* — "local" meaning input-specific and faithful even where the CLT is imperfect.
3. **Attribution graph.** Because the replacement model is now linear in its active features (given frozen attention and fixed error nodes), the direct effect of every feature on every downstream feature and on the logits is a single linear (Jacobian) attribution; chaining these gives a full causal graph, pruned by influence to a navigable size and explored interactively.

<a id="p-83-circuit-tracing-attribution-graphs-headline-5"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-5 --> **Worked case studies.** On Claude 3.5 Haiku the graphs reveal genuine multi-step computation: for "the capital of the state containing Dallas," the model internally represents **Texas** as an intermediate before answering **Austin** (a two-hop circuit); in poetry it plans a **rhyme target** (e.g. "rabbit") *before* writing the line, and suppressing that internal representation makes it re-plan to a different rhyme ("habit") <!-- cite:21 --> [[21]](references.md#ref-21). These are causal claims validated by intervention on the graph, not stories about attention.

<a id="p-83-circuit-tracing-attribution-graphs-headline-6"></a><!-- para:83-circuit-tracing-attribution-graphs-headline-6 --> **Limits & epistemic tag.** Attention is frozen (an approximation follow-up work is already relaxing); error nodes absorb whatever the CLT misses (a legible "we don't fully explain this" term); graphs are per-input, not a global circuit. *The current frontier — the most complete causal picture of a production model to date, and a fast-moving target (open-sourced mid-2025).* Full CLT/replacement-model formalism: Appendix <!-- secxref:C.3 -->[§C.3](appendix-c-causal-interventions.md#sec-C.3).
