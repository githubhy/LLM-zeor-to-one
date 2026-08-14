<!-- sec:C -->
## <a id="sec-C"></a>C Causal interventions

<a id="p-c-causal-interventions-1"></a><!-- para:c-causal-interventions-1 --> **Depth tier:** headline

<a id="p-c-causal-interventions-2"></a><!-- para:c-causal-interventions-2 --> Formalism for § <!-- secxref:5 -->[§5](method-inventory-causal.md#sec-5): mediation, the attribution-patching error term, and the attribution-graph replacement model.

<!-- sec:C.1 -->
### <a id="sec-C.1"></a>C.1 Activation patching as causal mediation

<a id="p-c1-activation-patching-as-causal-mediation-1"></a><!-- para:c1-activation-patching-as-causal-mediation-1 --> Treat the corruption as a *treatment*, the internal activation at site $s$ as a *mediator* $a_s$, and the metric $\mathcal{M}$ as the *outcome* <!-- cite:32 --> [[32]](references.md#ref-32). Let $a_s^{\text{clean}}$ and $a_s^{\text{corrupt}}$ be the mediator's values under the two inputs. The total effect is $\mathrm{TE} = \mathcal{M}(x_{\text{clean}}) - \mathcal{M}(x_{\text{corrupt}})$; the **indirect effect** of routing through $s$ (denoising direction) is the metric change from restoring $a_s$ to its clean value inside the corrupt run:

<a id="eq-1"></a><!-- eq:C-1 -->
$$
\mathrm{IE}(s) = \mathcal{M}\!\big(x_{\text{corrupt}};\, a_s\!\leftarrow\! a_s^{\text{clean}}\big) - \mathcal{M}(x_{\text{corrupt}}). \tag{1}
$$

<a id="p-c1-activation-patching-as-causal-mediation-2"></a><!-- para:c1-activation-patching-as-causal-mediation-2 --> **Denoising** ($a_s^{\text{corrupt}}\!\to\! a_s^{\text{clean}}$) measures *sufficiency*; **noising** ($a_s^{\text{clean}}\!\to\! a_s^{\text{corrupt}}$) measures *necessity*; the two need not agree because the network is nonlinear and other paths compensate (§ <!-- secxref:10.2 -->[§10.2](evaluation-and-metrics.md#sec-10.2)). **Path patching** (§ <!-- secxref:5.2 -->[§5.2](method-inventory-causal.md#sec-5.2)) restricts the mediator to a single edge by additionally freezing every off-path component at its clean value — the third forward pass.

<!-- sec:C.2 -->
### <a id="sec-C.2"></a>C.2 Attribution patching: first-order expansion and error

<a id="p-c2-attribution-patching-first-order-expansion-and-error-1"></a><!-- para:c2-attribution-patching-first-order-expansion-and-error-1 --> Exact patching (Equation <!-- ref:C-1 -->[(1)](#eq-1)) needs one forward pass per site. Attribution patching linearizes. Write the metric as a function of the activation, $\mathcal{M}(a_s)$, and Taylor-expand the patched value $\mathcal{M}(a_s^{\text{corrupt}})$ around the clean point:

<a id="eq-2"></a><!-- eq:C-2 -->
$$
\mathcal{M}(a_s^{\text{corrupt}}) = \mathcal{M}(a_s^{\text{clean}}) + \big(a_s^{\text{corrupt}} - a_s^{\text{clean}}\big)^{\!\top}\nabla_{a_s}\mathcal{M}\big|_{a_s^{\text{clean}}} + \tfrac12\,\Delta a_s^{\top} \mathbf{H}_s\, \Delta a_s + \cdots, \tag{2}
$$

<a id="p-c2-attribution-patching-first-order-expansion-and-error-2"></a><!-- para:c2-attribution-patching-first-order-expansion-and-error-2 --> with $\Delta a_s = a_s^{\text{corrupt}} - a_s^{\text{clean}}$ and $\mathbf{H}_s$ the Hessian. Dropping the second-order term gives the attribution-patching estimate of Equation [(2)](method-inventory-causal.md#eq-2) <!-- xref:5-2 -->: the linear term, computable for *all* sites from one backward pass. The **error is the discarded curvature** $\tfrac12\Delta a_s^{\top}\mathbf{H}_s\Delta a_s + O(\lVert\Delta a_s\rVert^3)$, which is large exactly where the metric is highly nonlinear in $a_s$: at a **saturated softmax** the local gradient $\nabla_{a}\mathcal{M}\approx 0$ even though the true patched effect (a discrete attention jump) is large — a false negative — and where direct and indirect effects **cancel** to first order. AtP\* <!-- cite:39 --> [[39]](references.md#ref-39) fixes the softmax case by recomputing the QK attention change exactly; EAP-IG <!-- cite:41 --> [[41]](references.md#ref-41) fixes it by integrating the gradient along the path from corrupt to clean,

<a id="eq-3"></a><!-- eq:C-3 -->
$$
\widehat{\Delta\mathcal{M}}_{\text{IG}}(s) = \Delta a_s^{\top}\int_{0}^{1}\nabla_{a_s}\mathcal{M}\big|_{a_s^{\text{clean}} + \alpha\,\Delta a_s}\,\mathrm{d}\alpha \;\approx\; \Delta a_s^{\top}\,\frac{1}{M}\sum_{m=1}^{M}\nabla_{a_s}\mathcal{M}\big|_{a_s^{\text{clean}} + \frac{m}{M}\Delta a_s}, \tag{3}
$$

<a id="p-c2-attribution-patching-first-order-expansion-and-error-3"></a><!-- para:c2-attribution-patching-first-order-expansion-and-error-3 --> the standard Integrated Gradients construction <!-- cite:79 --> [[79]](references.md#ref-79) applied per site, which recovers the true effect even when the endpoint gradient is near zero because it samples the steep transition region in between.

<!-- sec:C.3 -->
### <a id="sec-C.3"></a>C.3 Cross-layer transcoders and the local replacement model

<a id="p-c3-cross-layer-transcoders-and-the-local-replacement-model-1"></a><!-- para:c3-cross-layer-transcoders-and-the-local-replacement-model-1 --> Attribution graphs (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)) linearize the *whole* forward pass for one input. A **cross-layer transcoder** replaces the MLPs: sparse features whose activation at layer $\ell$ contributes to the MLP output at $\ell$ and every later layer. For a fixed prompt, build the **local replacement model** by substituting each true MLP output $\mathbf{y}_\ell$ with the CLT reconstruction plus an **error node** that makes the substitution exact:

<a id="eq-4"></a><!-- eq:C-4 -->
$$
\mathbf{y}_\ell = \underbrace{\textstyle\sum_{\ell'\le\ell} W_{\text{dec}}^{(\ell'\to\ell)}\,\mathbf{f}_{\ell'}}_{\text{CLT reconstruction}} + \underbrace{\mathbf{e}_\ell}_{\text{error node}}, \qquad \mathbf{e}_\ell \equiv \mathbf{y}_\ell - \text{CLT}_\ell, \tag{4}
$$

<a id="p-c3-cross-layer-transcoders-and-the-local-replacement-model-2"></a><!-- para:c3-cross-layer-transcoders-and-the-local-replacement-model-2 --> with attention patterns **frozen** at their real input-computed values. On this input the replacement reproduces the model's output exactly (the error nodes absorb the residual), and — crucially — the computation is now *linear* in the active features. The **attribution graph** is then the linear (Jacobian) map from each active feature/error/token to each downstream feature and to the logits, chained by the chain rule and pruned by influence. The two honest approximations are visible in the object itself: attention is frozen (not explained), and the error nodes are an explicit "unexplained residual" term — which is why the method is *faithful for this input* rather than a global circuit <!-- cite:20 --> [[20]](references.md#ref-20), <!-- cite:21 --> [[21]](references.md#ref-21).

<!-- sec:C.4 -->
### <a id="sec-C.4"></a>C.4 Figure — the two approximations patching relies on

<a id="p-c4-figure-the-two-approximations-patching-relies-on-1"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-1 --> ![Patching approximation error and sub-additivity](figures/appendix-c-patching-approximation.svg)

<a id="p-c4-figure-the-two-approximations-patching-relies-on-2"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-2 --> **F-C1 · Attribution patching is a near-operating-point instrument, and component effects do not add.**

<a id="p-c4-figure-the-two-approximations-patching-relies-on-3"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-3 --> **1 · Purpose and operating conditions.** **Closed forms**, no model run. The metric is modelled as a saturating readout $m = \sigma(z_0 + g\delta)$, which is what a logit difference through a softmax is. Parameters: clean operating point $z_0 = -0.4$; single-component sensitivity $g = 1.1$; two-component sensitivities $g_A = 1.1$, $g_B = 0.9$. Fully deterministic — no random number generator is used.

<a id="p-c4-figure-the-two-approximations-patching-relies-on-4"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-4 --> **2 · What it shows.** (a) Exact patching against its first-order (attribution) approximation, with relative error on the right axis: 1.0% at $\delta = 0.1$, 15.7% at $\delta = 2$, **82% at $\delta = 4$**. (b) The joint effect of patching two components against the sum of their singleton effects; the shaded gap is the interaction.

<a id="p-c4-figure-the-two-approximations-patching-relies-on-5"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-5 --> **3 · How to read it.** The interaction in (b) is **negative throughout** — components are sub-additive — so summing singleton ablation effects *overstates* what a pair does together: $-1.2\%$ of the joint effect at small displacement, $-13.3\%$ at moderate, $-77.2\%$ at large. Any greedy search that scores components singly and sums inherits that bias, and it grows precisely where the components matter most.

<a id="p-c4-figure-the-two-approximations-patching-relies-on-6"></a><!-- para:c4-figure-the-two-approximations-patching-relies-on-6 --> **4 · Caveats.** The relative error in (a) is **not monotone**: $\sigma$ is convex below its inflection and concave above, so the signed error changes sign near $\delta \approx 0.36$ at this $z_0$. What is monotone is the failure once the readout saturates. Crucially, this sub-additivity requires **no interaction in the network's computation** — it is a property of the nonlinear metric alone, which is exactly the distinction a circuit claim must make. Generator and persisted data: `figures/appendix-c-patching-approximation.py` / `.json`.
