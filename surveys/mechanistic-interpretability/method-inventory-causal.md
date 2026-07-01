<!-- sec:5 -->
## <a id="sec-5"></a>5 Method inventory II — causal / interventional methods

<a id="p-5-method-inventory-ii-causal-interventional-methods-1"></a><!-- para:5-method-inventory-ii-causal-interventional-methods-1 --> This is the mechanistic core: methods that *change* internal state and measure the behavioral consequence, yielding causal rather than correlational evidence. The full mediation formalism and the attribution-patching error term are derived in Appendix <!-- secxref:C -->[§C](appendix-c-causal-interventions.md#sec-C).

<!-- sec:5.1 -->
### <a id="sec-5.1"></a>5.1 Activation patching / causal tracing [headline]

<a id="p-51-activation-patching-causal-tracing-headline-1"></a><!-- para:51-activation-patching-causal-tracing-headline-1 --> **One-line idea.** Copy a single internal activation from one run into another and measure how much of the behavior it restores (or destroys) — the atomic causal experiment of MI.

<a id="p-51-activation-patching-causal-tracing-headline-2"></a><!-- para:51-activation-patching-causal-tracing-headline-2 --> **Placement & lineage.** A special case of Pearl-style causal mediation analysis applied to activations, adapted to transformers by Vig et al. <!-- cite:32 --> [[32]](references.md#ref-32) (gender-bias mediation) and made a localization workhorse by ROME's "causal tracing" <!-- cite:31 --> [[31]](references.md#ref-31). Every downstream causal method (path, attribution, ACDC, EAP) is an optimization or approximation of this primitive; the practitioner how-to is Heimersheim & Nanda <!-- cite:34 --> [[34]](references.md#ref-34).

<a id="p-51-activation-patching-causal-tracing-headline-3"></a><!-- para:51-activation-patching-causal-tracing-headline-3 --> **Mechanism.** Run the model twice: a **clean** run on $x_{\text{clean}}$ (correct behavior) caching all activations, and a **corrupt** run on $x_{\text{corrupt}}$ (a counterfactual, e.g. a name-swapped prompt, or subject-token embeddings perturbed by Gaussian noise). Let $\mathcal{M}$ be a scalar metric — the **logit difference** $\mathcal{M} = \operatorname{logit}(\text{correct}) - \operatorname{logit}(\text{incorrect})$ is standard. Patching restores one activation at site $s$ (a layer, position, head, or MLP) from the clean run into the corrupt run and re-runs forward from there:

<a id="eq-1"></a><!-- eq:5-1 -->
$$
\mathrm{IE}(s) = \mathcal{M}\!\left(x_{\text{corrupt}};\; a_s \!\leftarrow\! a_s^{\text{clean}}\right) - \mathcal{M}\!\left(x_{\text{corrupt}}\right), \qquad \mathrm{TE} = \mathcal{M}(x_{\text{clean}}) - \mathcal{M}(x_{\text{corrupt}}). \tag{1}
$$

<a id="p-51-activation-patching-causal-tracing-headline-4"></a><!-- para:51-activation-patching-causal-tracing-headline-4 --> The **indirect effect** $\mathrm{IE}(s)$ is how much of the total effect $\mathrm{TE}$ a single site recovers; sweeping $s$ over all (layer, position) pairs yields the causal-tracing heatmap.

<a id="p-51-activation-patching-causal-tracing-headline-5"></a><!-- para:51-activation-patching-causal-tracing-headline-5 --> **Two choices that change the answer** <!-- cite:33 --> [[33]](references.md#ref-33). **Direction:** *denoising* (clean → corrupt patch, as above) tests **sufficiency** — is $s$ enough to restore correct behavior?; *noising* (corrupt → clean patch) tests **necessity** — is $s$ needed to maintain it? The two can disagree. **Corruption method:** symmetric token replacement (swap in another real prompt) keeps activations in-distribution and is preferred over Gaussian noising, which can push activations off-manifold and produce misleading effects.

<a id="p-51-activation-patching-causal-tracing-headline-6"></a><!-- para:51-activation-patching-causal-tracing-headline-6 --> **Worked anchor.** ROME's causal trace on GPT-2-XL localizes factual recall to the *last subject token* in *middle layers*. Against a total effect of $\mathrm{ATE}\approx 18.6\%$, the peak indirect effect of restoring an *individual hidden state* is $\approx 8.7\%$ at layer 15; decomposing by module, **MLP** contributions peak at $\approx 6.6\%$ while **attention** at the last subject token contributes only $\approx 1.6\%$ — the decisive-role-of-mid-layer-MLPs finding that motivates ROME's edit site <!-- cite:31 --> [[31]](references.md#ref-31) (§ <!-- secxref:7.4 -->[§7.4](method-inventory-steering-editing.md#sec-7.4)). *(Verified against [31] (Sec. 2.2, Fig. 2) in the citation-audit pass: the 8.7% figure is the individual-state peak, not the 6.6% MLP-specific peak — a distinction the evidence ledger had flagged.)*

<a id="p-51-activation-patching-causal-tracing-headline-7"></a><!-- para:51-activation-patching-causal-tracing-headline-7 --> **Metric subtlety.** Logit difference is preferred over correct-token probability because it isolates a specific correct-vs-incorrect contrast and can expose *negative* components (heads that suppress the answer), which softmax-normalized probability can mask <!-- cite:33 --> [[33]](references.md#ref-33).

<a id="p-51-activation-patching-causal-tracing-headline-8"></a><!-- para:51-activation-patching-causal-tracing-headline-8 --> **Complexity.** One forward pass **per site patched** — $O(\text{sites})$ forward passes — which is exactly the cost attribution patching (§ <!-- secref:5.3 -->[§5.3](#sec-5.3)) exists to avoid.

<a id="p-51-activation-patching-causal-tracing-headline-9"></a><!-- para:51-activation-patching-causal-tracing-headline-9 --> **Epistemic tag.** *The gold-standard causal primitive; expensive, and its "faithfulness" readout is subject to the self-repair caveat of § <!-- secxref:10.2 -->[§10.2](evaluation-and-metrics.md#sec-10.2).*

<!-- sec:5.2 -->
### <a id="sec-5.2"></a>5.2 Path patching [load-bearing]

<a id="p-52-path-patching-load-bearing-1"></a><!-- para:52-path-patching-load-bearing-1 --> **One-line idea.** Patch a single *edge* (sender → receiver) of the computational graph rather than a node, holding every other path fixed, to isolate a direct connection.

<a id="p-52-path-patching-load-bearing-2"></a><!-- para:52-path-patching-load-bearing-2 --> **Placement & lineage.** Generalizes activation patching from nodes to edges; introduced ad hoc to build the IOI circuit <!-- cite:35 --> [[35]](references.md#ref-35) and formalized as a reusable framework by Goldowsky-Dill et al. <!-- cite:36 --> [[36]](references.md#ref-36).

<a id="p-52-path-patching-load-bearing-3"></a><!-- para:52-path-patching-load-bearing-3 --> **Mechanism.** Where node patching lets a patched activation propagate through *all* downstream paths, path patching uses a **third** forward pass to freeze every off-target component at its clean value, so a corrupted sender's effect reaches the receiver along **one specified path only**. Iterating edge-by-edge is how Wang et al. assembled the IOI circuit as a directed graph of head classes (name-mover ← S-inhibition ← duplicate-token/induction heads), the canonical demonstration that a transformer behavior decomposes into a legible wiring diagram.

<a id="p-52-path-patching-load-bearing-4"></a><!-- para:52-path-patching-load-bearing-4 --> **Complexity & limits.** Three forward passes per edge tested; the edge count is quadratic in components, so hand-run path patching does not scale beyond small models — the motivation for automation (§ <!-- secref:5.4 -->[§5.4](#sec-5.4)). *Epistemic tag: precise, interpretable, does not scale unaided.*

<!-- sec:5.3 -->
### <a id="sec-5.3"></a>5.3 Attribution patching [load-bearing]

<a id="p-53-attribution-patching-load-bearing-1"></a><!-- para:53-attribution-patching-load-bearing-1 --> **One-line idea.** Approximate the patching effect of *every* site at once with a first-order Taylor expansion — two forward passes and one backward pass, independent of the number of sites.

<a id="p-53-attribution-patching-load-bearing-2"></a><!-- para:53-attribution-patching-load-bearing-2 --> **Placement & lineage.** The scalability fix for activation patching (Nanda <!-- cite:37 --> [[37]](references.md#ref-37)); extended to edges as **Edge Attribution Patching** (EAP) by Syed et al. <!-- cite:38 --> [[38]](references.md#ref-38) and corrected at attention by **AtP\*** <!-- cite:39 --> [[39]](references.md#ref-39).

<a id="p-53-attribution-patching-load-bearing-3"></a><!-- para:53-attribution-patching-load-bearing-3 --> **Mechanism.** Treat the corrupt run as a small perturbation of the clean run and linearize the metric in the activation at site $s$:

<a id="eq-2"></a><!-- eq:5-2 -->
$$
\widehat{\Delta\mathcal{M}}(s) \;\approx\; \big(a_s^{\text{corrupt}} - a_s^{\text{clean}}\big)^{\!\top}\, \nabla_{a_s}\mathcal{M}\big|_{a_s^{\text{clean}}}. \tag{2}
$$

<a id="p-53-attribution-patching-load-bearing-4"></a><!-- para:53-attribution-patching-load-bearing-4 --> The gradient $\nabla_{a}\mathcal{M}$ over *all* sites is obtained from a single backward pass and reused everywhere, so scoring millions of sites costs two forward passes plus one backward pass — Nanda's headline is scoring all ~4.7M neurons of a GPT-3-scale model in three passes <!-- cite:37 --> [[37]](references.md#ref-37). Unlike input×gradient saliency, the score multiplies the gradient by the *clean-minus-corrupt difference*, so it reflects the task-relevant counterfactual, not raw magnitude.

<a id="p-53-attribution-patching-load-bearing-5"></a><!-- para:53-attribution-patching-load-bearing-5 --> **Where it breaks.** The linearization fails at two transformer nonlinearities <!-- cite:39 --> [[39]](references.md#ref-39): **saturation** — a softmax attention pattern near 0 or 1 has a near-zero local gradient even when the true patched effect (a discrete jump in attention) is large, producing false negatives; and **cancellation** — direct and indirect effects that partly cancel in the true nonlinear computation are not captured by a first-order sum. AtP\* fixes the saturation case by recomputing the QK attention change exactly while keeping the rest linear. Empirically the approximation is good for small activations (head outputs) and poor for large ones (the full residual stream).

<a id="p-53-attribution-patching-load-bearing-6"></a><!-- para:53-attribution-patching-load-bearing-6 --> **Complexity & epistemic tag.** $O(1)$ passes for the whole graph. *A scalable approximation, not ground truth; verify shortlisted sites with exact patching.* Full first-order derivation and error term: Appendix <!-- secxref:C.2 -->[§C.2](appendix-c-causal-interventions.md#sec-C.2).

<!-- sec:5.4 -->
### <a id="sec-5.4"></a>5.4 Automated circuit discovery — ACDC and EAP [load-bearing]

<a id="p-54-automated-circuit-discovery-acdc-and-eap-load-bearing-1"></a><!-- para:54-automated-circuit-discovery-acdc-and-eap-load-bearing-1 --> **One-line idea.** Automate circuit finding by pruning the computational graph down to the edges whose removal least degrades the behavior.

<a id="p-54-automated-circuit-discovery-acdc-and-eap-load-bearing-2"></a><!-- para:54-automated-circuit-discovery-acdc-and-eap-load-bearing-2 --> **Placement & lineage.** ACDC (Conmy et al. <!-- cite:40 --> [[40]](references.md#ref-40)) is the greedy-search baseline; EAP (§ <!-- secref:5.3 -->[§5.3](#sec-5.3), <!-- cite:38 --> [[38]](references.md#ref-38)) is the gradient-approximated fast version; EAP-IG (Hanna et al. <!-- cite:41 --> [[41]](references.md#ref-41)) integrates the gradient to fix faithfulness.

<a id="p-54-automated-circuit-discovery-acdc-and-eap-load-bearing-3"></a><!-- para:54-automated-circuit-discovery-acdc-and-eap-load-bearing-3 --> **Mechanism.** **ACDC** starts from the full graph and, in reverse-topological order, deletes each edge whose removal changes a metric (default: $\mathrm{KL}$ from the full model) by less than a threshold $\tau$; the surviving subgraph is the discovered circuit. On GPT-2-small's ~32k-edge graph it recovered a 68-edge circuit whose edges had all been found by prior manual work, and it fully recovers tracr-compiled ground-truth circuits at any $\tau > 0$ <!-- cite:40 --> [[40]](references.md#ref-40). **EAP** replaces ACDC's per-edge forward-pass ablation with the single-pass attribution score of Equation <!-- ref:5-2 -->[(2)](#eq-2), ranking all edges at once — matching or beating ACDC's recovery AUC at a fraction of the cost <!-- cite:38 --> [[38]](references.md#ref-38).

<a id="p-54-automated-circuit-discovery-acdc-and-eap-load-bearing-4"></a><!-- para:54-automated-circuit-discovery-acdc-and-eap-load-bearing-4 --> **The faithfulness caveat (a key 2024 result).** Circuit *overlap* with a hand-found circuit is not the goal; *faithfulness* — recovering the behavior when everything outside the circuit is ablated — is. Hanna et al. <!-- cite:41 --> [[41]](references.md#ref-41) show plain EAP can produce circuits with 90%+ node overlap yet **0% faithfulness on IOI** (and 51% on Greater-Than), because gradient saturation mis-scores key edges; **EAP-IG** replaces the single-point gradient with an integrated-gradients path integral (borrowing <!-- cite:79 --> [[79]](references.md#ref-79)) and recovers faithfulness on many tasks. The methodological upshot — report faithfulness curves, not overlap — feeds directly into § <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1).

<a id="p-54-automated-circuit-discovery-acdc-and-eap-load-bearing-5"></a><!-- para:54-automated-circuit-discovery-acdc-and-eap-load-bearing-5 --> **Complexity & epistemic tag.** ACDC: $O(\text{edges})$ passes; EAP/EAP-IG: $O(1)$–$O(m)$ passes. *EAP-IG is the current practical default; validate the output circuit's faithfulness explicitly.*

<!-- sec:5.5 -->
### <a id="sec-5.5"></a>5.5 Causal scrubbing [load-bearing]

<a id="p-55-causal-scrubbing-load-bearing-1"></a><!-- para:55-causal-scrubbing-load-bearing-1 --> **One-line idea.** Formalize a circuit hypothesis as a correspondence between the model's graph and an abstract algorithm, then resample every activation the hypothesis says is irrelevant and check the behavior survives.

<a id="p-55-causal-scrubbing-load-bearing-2"></a><!-- para:55-causal-scrubbing-load-bearing-2 --> **Placement & lineage.** Redwood Research's rigorous falsification test <!-- cite:42 --> [[42]](references.md#ref-42); a stricter cousin of path patching that tests a *whole hypothesis* rather than one edge.

<a id="p-55-causal-scrubbing-load-bearing-3"></a><!-- para:55-causal-scrubbing-load-bearing-3 --> **Mechanism.** Given a claimed correspondence (which model components implement which abstract nodes), replace each non-hypothesized activation with its value on a *different input that is equivalent under the hypothesis* (recursive resampling ablation), and compare "scrubbed loss" to the original. If scrubbed loss $\gg$ original, the hypothesis is falsified; passing is *failure to falsify*, not proof. On induction heads a naive hypothesis recovered only ~35% of the loss while a refined one recovered ~89% <!-- cite:42 --> [[42]](references.md#ref-42).

<a id="p-55-causal-scrubbing-load-bearing-4"></a><!-- para:55-causal-scrubbing-load-bearing-4 --> **Limits & epistemic tag.** Two known failure modes: **cancellation** (per-input errors average out, hiding a wrong hypothesis) and inability to test **specificity** (it cannot distinguish extensionally-equivalent hypotheses). *A strict falsifier, asymmetric by design — it disproves, it cannot confirm.* Full derivation: `n/a (load-bearing; the recursive-resampling algorithm is summarized here and cross-referenced to <!-- cite:42 --> [[42]](references.md#ref-42), not re-derived)`.

<!-- sec:5.6 -->
### <a id="sec-5.6"></a>5.6 Distributed Alignment Search (DAS) [load-bearing]

<a id="p-56-distributed-alignment-search-das-load-bearing-1"></a><!-- para:56-distributed-alignment-search-das-load-bearing-1 --> **One-line idea.** Learn, by gradient descent, an orthogonal rotation of a representation such that intervening on a few rotated coordinates realizes an abstract causal variable — finding a *distributed* linear feature no hand-guess would.

<a id="p-56-distributed-alignment-search-das-load-bearing-2"></a><!-- para:56-distributed-alignment-search-das-load-bearing-2 --> **Placement & lineage.** DAS (Geiger et al. <!-- cite:43 --> [[43]](references.md#ref-43)), an instantiation of causal-abstraction theory <!-- cite:45 --> [[45]](references.md#ref-45); **Boundless DAS** <!-- cite:44 --> [[44]](references.md#ref-44) scales it to a 7B model by also learning the subspace size.

<a id="p-56-distributed-alignment-search-das-load-bearing-3"></a><!-- para:56-distributed-alignment-search-das-load-bearing-3 --> **Mechanism.** For a hypothesized high-level variable $v$, learn an orthogonal $R$ ($R^\top R = I$) so that a **distributed interchange intervention** — swap $k$ coordinates of $R\mathbf{x}_{\text{base}}$ with those of $R\mathbf{x}_{\text{source}}$, rotate back, continue the forward pass — makes the model's output match what the high-level causal model predicts. $R$ is trained to maximize **interchange-intervention accuracy (IIA)**, the fraction of (base, source) pairs on which the intervention reproduces the abstract model's behavior; high IIA means $v$ is linearly encoded in that learned subspace. Boundless DAS adds a learnable soft boundary that discovers $k$ jointly with $R$, letting it search many sites in Alpaca (7B) and locate an entity-tracking mechanism in specific attention-head subspaces <!-- cite:44 --> [[44]](references.md#ref-44).

<a id="p-56-distributed-alignment-search-das-load-bearing-4"></a><!-- para:56-distributed-alignment-search-das-load-bearing-4 --> **Limits & epistemic tag.** Supervised (needs a hypothesized causal model and its interventions); can *overfit* an alignment that IIA rewards without the model "really" using it that way — a concern the RAVEL benchmark (§ <!-- secxref:10.4 -->[§10.4](evaluation-and-metrics.md#sec-10.4)) was built to stress-test. *The most rigorous feature-localization method; supervision-hungry and validation-sensitive.*
