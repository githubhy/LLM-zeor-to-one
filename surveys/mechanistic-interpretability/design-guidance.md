<!-- sec:14 -->
## <a id="sec-14"></a>14 Design guidance

<!-- sec:14.1 -->
### <a id="sec-14.1"></a>14.1 A decision workflow

<a id="p-141-a-decision-workflow-1"></a><!-- para:141-a-decision-workflow-1 --> The selection table (§ <!-- secxref:11.2 -->[§11.2](comparison-and-tradeoffs.md#sec-11.2)) answers "which method"; this is the *order* to apply them, phrased as a workflow a practitioner can run.

1. <a id="p-141-a-decision-workflow-2"></a><!-- para:141-a-decision-workflow-2 --> **Frame the question as a target.** Decide whether you want a *representation* (is $F$ present?), a *feature* (which direction is $F$?), or a *circuit* (how is $B$ computed?). This picks the granularity column of the matrix.
2. **Observe to generate hypotheses — cheaply.** Probe (with a selectivity control), read a tuned lens, inspect attention. Treat every output as a hypothesis, never a conclusion (§ <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1)).
3. **Intervene to confirm — always.** Patch the candidate site (denoise *and* noise, § <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1)); if the effect is absent, the hypothesis is wrong regardless of how clean the observation looked.
4. **Scale the search only after a small-model proof of concept.** Use attribution patching / EAP-IG to extend a hand-verified pattern; do not trust an automated circuit you have not faithfulness-checked (§ <!-- secxref:5.4 -->[§5.4](method-inventory-causal.md#sec-5.4)).
5. **For unsupervised discovery, reach for dictionaries — but validate downstream.** Train (or reuse, e.g. Gemma Scope) a JumpReLU/TopK SAE, auto-interp the features, and *test them on the actual task* against a difference-in-means baseline before believing they help (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)).
6. **To control behavior, start with the simplest thing that works.** A difference-in-means steering vector or a single-direction ablation usually beats SAE-feature clamping and always beats a fine-tune for a quick intervention (§§ <!-- secxref:7.1 -->[§7.1](method-inventory-steering-editing.md#sec-7.1), <!-- secxref:7.3 -->[§7.3](method-inventory-steering-editing.md#sec-7.3)).
7. **Report faithfulness honestly.** State the ablation convention, remember self-repair makes single-ablation a lower bound, and prefer completeness/resampling checks over a single headline number (§ <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1)).

<a id="p-141-a-decision-workflow-3"></a><!-- para:141-a-decision-workflow-3 --> The meta-rule: **spend the least exact method that answers the question, then confirm with the most exact method you can afford.** Observation is free and misleading; exact patching is trustworthy and expensive; the whole toolkit is a ladder between them.

<!-- sec:14.2 -->
### <a id="sec-14.2"></a>14.2 Pitfalls checklist

<a id="p-142-pitfalls-checklist-1"></a><!-- para:142-pitfalls-checklist-1 --> The failures that most often turn a plausible result into a wrong one:

- <a id="p-142-pitfalls-checklist-2"></a><!-- para:142-pitfalls-checklist-2 --> **Probing illusions** — a "concept neuron" that works on one corpus and fails on another <!-- cite:58 --> [[58]](references.md#ref-58); always test across distributions, and use selectivity controls <!-- cite:25 --> [[25]](references.md#ref-25).
- **Attention as explanation** — a head that *attends* to a token has not been shown to *use* it; confirm causally <!-- cite:29 --> [[29]](references.md#ref-29), <!-- cite:30 --> [[30]](references.md#ref-30).
- **Self-repair / backup heads** — a small ablation effect can hide a large true importance; the completeness check and resampling (causal scrubbing) exist for this <!-- cite:35 --> [[35]](references.md#ref-35), <!-- cite:59 --> [[59]](references.md#ref-59).
- **Wrong featurization** — the Othello linear-probe failure was a frame artifact <!-- cite:28 --> [[28]](references.md#ref-28); try the model-relative frame before concluding "nonlinear."
- **Corrupt-prompt off-distribution** — Gaussian noising can push activations off-manifold; prefer symmetric token replacement <!-- cite:33 --> [[33]](references.md#ref-33).
- **Overlap ≠ faithfulness** — a circuit matching 90% of a known circuit's nodes can have 0% faithfulness <!-- cite:41 --> [[41]](references.md#ref-41); report faithfulness curves.
- **Metric non-robustness** — node- vs. edge-ablation moves faithfulness by >50 points; fix and disclose the convention <!-- cite:62 --> [[62]](references.md#ref-62).
- **SAE feature identity** — feature splitting means "the" feature is resolution-dependent; feature absorption means a monosemantic-looking feature can under-fire <!-- cite:7 --> [[7]](references.md#ref-7), <!-- cite:15 --> [[15]](references.md#ref-15).
- **SAE steering by default** — do not assume SAE-feature steering beats difference-in-means; the evidence says it usually does not <!-- cite:66 --> [[66]](references.md#ref-66).
- **Editing ≠ understanding** — ROME succeeding at layer $\ell$ is not evidence the fact lives at $\ell$ <!-- cite:54 --> [[54]](references.md#ref-54); and shallow "unlearning" can be undone by a single direction ablation <!-- cite:74 --> [[74]](references.md#ref-74).
