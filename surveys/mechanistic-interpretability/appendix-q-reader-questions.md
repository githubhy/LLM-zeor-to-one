<!-- sec:Q -->
## <a id="sec-Q"></a>Q Reader's questions

<a id="p-q-readers-questions-1"></a><!-- para:q-readers-questions-1 --> Short, self-contained answers to the "why is it built this way / what breaks otherwise / why not the obvious alternative" questions the main text raises. Each is anchored for citation and folding.

<!-- sec:Q.1 -->
### <a id="sec-Q.1"></a>Q.1 Why decompose activations into feature *directions* instead of just reading neurons?

<a id="p-q1-why-decompose-activations-into-feature-directions-instead-of-just-reading-neurons-1"></a><!-- para:q1-why-decompose-activations-into-feature-directions-instead-of-just-reading-neurons-1 --> Because superposition (§ <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)) makes individual neurons polysemantic: a model represents far more concepts than it has neurons by storing them as non-orthogonal directions, so any single neuron is a coordinate that several unrelated features load onto. Reading neuron $i$ therefore tells you about a *mixture* of concepts. The interpretable unit is the direction that a dictionary-learning method (an SAE) recovers, not the neuron — that is the whole reason § <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6) exists.

<!-- sec:Q.2 -->
### <a id="sec-Q.2"></a>Q.2 A probe reads the concept with 99% accuracy — isn't that enough?

<a id="p-q2-a-probe-reads-the-concept-with-99-accuracy-isnt-that-enough-1"></a><!-- para:q2-a-probe-reads-the-concept-with-99-accuracy-isnt-that-enough-1 --> No. High probe accuracy shows the concept is *decodable* from the layer, not that the model's forward computation *reads it out and acts on it* (§ <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1)). A sufficiently expressive probe even hits high accuracy on random-label control tasks <!-- cite:25 --> [[25]](references.md#ref-25). Only a causal intervention — remove or change the information and watch the behavior move — licenses the mechanistic claim. This "decodable ≠ used" gap is the reason the survey's center of gravity is the causal-methods family.

<!-- sec:Q.3 -->
### <a id="sec-Q.3"></a>Q.3 If SAEs find interpretable features, why do people say they "failed"?

<a id="p-q3-if-saes-find-interpretable-features-why-do-people-say-they-failed-1"></a><!-- para:q3-if-saes-find-interpretable-features-why-do-people-say-they-failed-1 --> They did not fail at *discovery* — they surface genuinely interpretable features at scale <!-- cite:7 --> [[7]](references.md#ref-7), <!-- cite:8 --> [[8]](references.md#ref-8). They underperformed at *action*: on steering and probing tasks, SAE features lose to prompting and difference-in-means baselines <!-- cite:66 --> [[66]](references.md#ref-66), <!-- cite:67 --> [[67]](references.md#ref-67). The reason is that the SAE objective (reconstruct a static activation snapshot under sparsity) is decoupled from any downstream task, so where a concept is already specified by labels, a supervised direction fit directly on it has no reason to lose. The lesson (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)) is "use SAEs to discover unknown concepts, not to act on known ones."

<!-- sec:Q.4 -->
### <a id="sec-Q.4"></a>Q.4 Why do attribution graphs *freeze* attention?

<a id="p-q4-why-do-attribution-graphs-freeze-attention-1"></a><!-- para:q4-why-do-attribution-graphs-freeze-attention-1 --> Because attention's softmax nonlinearity is much harder to sparsify and linearize than an MLP's (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)). Freezing attention at its real, input-computed values keeps the rest of the replacement model linear (<!-- secxref:C.3 -->[§C.3](appendix-c-causal-interventions.md#sec-C.3)) in the transcoder features, which is exactly what makes the end-to-end Jacobian attribution possible. It is an honest, visible approximation — attention is "used but not explained" in the graph — and relaxing it is active follow-up work.

<!-- sec:Q.5 -->
### <a id="sec-Q.5"></a>Q.5 Why does adding a single mean-difference vector steer behavior at all?

<a id="p-q5-why-does-adding-a-single-mean-difference-vector-steer-behavior-at-all-1"></a><!-- para:q5-why-does-adding-a-single-mean-difference-vector-steer-behavior-at-all-1 --> Because of the linear representation hypothesis (§ <!-- secxref:2.3 -->[§2.3](fundamentals.md#sec-2.3)): many concepts are directions, so moving the activation along a concept's direction moves the behavior along that concept. The mean-difference direction is, under an isotropic-covariance Gaussian model, the Bayes-optimal linear discriminant (Appendix <!-- secxref:E.1 -->[§E.1](appendix-e-steering-and-editing-math.md#sec-E.1)) — so it is not a heuristic, it is the optimal separating direction when activations are whitened, and a good first approximation otherwise.

<!-- sec:Q.6 -->
### <a id="sec-Q.6"></a>Q.6 ROME edits a fact successfully at layer $\ell$ — doesn't that prove the fact is stored there?

<a id="p-q6-rome-edits-a-fact-successfully-at-layer-ell-doesnt-that-prove-the-fact-is-stored-there-1"></a><!-- para:q6-rome-edits-a-fact-successfully-at-layer-ell-doesnt-that-prove-the-fact-is-stored-there-1 --> No, and this is one of MI's most important cautionary results. Hase et al. <!-- cite:54 --> [[54]](references.md#ref-54) show edit success is roughly *equally good* at layers far from the causally-traced site: a regression of edit success on edit layer already explains ~58% of the variance, and adding the causal-tracing importance improves it by at most 0.03. "Where you can successfully write a new association" and "where the model reads the fact during recall" are different questions with different answers (§ <!-- secxref:7.4 -->[§7.4](method-inventory-steering-editing.md#sec-7.4)) — editing success does not validate the localization.

<!-- sec:Q.7 -->
### <a id="sec-Q.7"></a>Q.7 What is the difference between a feature and a circuit?

<a id="p-q7-what-is-the-difference-between-a-feature-and-a-circuit-1"></a><!-- para:q7-what-is-the-difference-between-a-feature-and-a-circuit-1 --> A **feature** is a *direction* standing for a concept (the noun); a **circuit** is a *subgraph of components* that composes features into an algorithm (the verb). Dictionary learning (§ <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6)) finds features; patching and automated discovery (§ <!-- secxref:5 -->[§5](method-inventory-causal.md#sec-5)) and attribution graphs (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)) wire features into circuits. The field's arc is exactly the movement from hand-built neuron circuits, to unsupervised features, and back to circuits *built on* those features.

<!-- sec:Q.8 -->
### <a id="sec-Q.8"></a>Q.8 Faithfulness is just "what fraction of the behavior the circuit recovers" — why is it "not robust"?

<a id="p-q8-faithfulness-is-just-what-fraction-of-the-behavior-the-circuit-recovers-why-is-it-not-robust-1"></a><!-- para:q8-faithfulness-is-just-what-fraction-of-the-behavior-the-circuit-recovers-why-is-it-not-robust-1 --> Because the fraction depends on *how* you ablate everything outside the circuit. Miller et al. <!-- cite:62 --> [[62]](references.md#ref-62) show the same IOI circuit's recovered-fraction swings by more than 50 points between node- and edge-ablation (edge-ablation can exceed 100%), and changes again with the order of averaging and the prompt format. On top of that, self-repair (§ <!-- secxref:10.2 -->[§10.2](evaluation-and-metrics.md#sec-10.2)) makes any single-ablation number a *lower bound* on true importance. So a bare faithfulness percentage is only meaningful with its ablation convention stated — which is why this survey flags the convention wherever it cites one.
