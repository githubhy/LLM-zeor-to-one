<!-- sec:6 -->
## <a id="sec-6"></a>6 Method inventory III — dictionary learning (sparse autoencoders)

<a id="p-6-method-inventory-iii-dictionary-learning-sparse-autoencoders-1"></a><!-- para:6-method-inventory-iii-dictionary-learning-sparse-autoencoders-1 --> If superposition (§ <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)) is why features hide, dictionary learning is how they are pulled back out. This family dominated 2023–2024 MI and is also the subject of the field's sharpest current debate (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)). Full objective and Pareto-frontier derivations: Appendix <!-- secxref:D -->[§D](appendix-d-sae-derivations.md#sec-D).

<!-- sec:6.1 -->
### <a id="sec-6.1"></a>6.1 Sparse autoencoders (SAEs) [headline]

<a id="p-61-sparse-autoencoders-saes-headline-1"></a><!-- para:61-sparse-autoencoders-saes-headline-1 --> **One-line idea.** Learn an overcomplete dictionary that reconstructs a layer's activations as a sparse sum of interpretable feature directions — solving the superposition inverse problem post hoc.

<a id="p-61-sparse-autoencoders-saes-headline-2"></a><!-- para:61-sparse-autoencoders-saes-headline-2 --> **Placement & lineage.** Classical sparse coding / dictionary learning (Olshausen & Field) applied to transformer activations; introduced for LM interpretability concurrently by Bricken et al. ("Towards Monosemanticity" <!-- cite:7 --> [[7]](references.md#ref-7)) and Cunningham et al. <!-- cite:9 --> [[9]](references.md#ref-9), then scaled to a production model by Templeton et al. ("Scaling Monosemanticity" <!-- cite:8 --> [[8]](references.md#ref-8)).

<a id="p-61-sparse-autoencoders-saes-headline-3"></a><!-- para:61-sparse-autoencoders-saes-headline-3 --> **Mechanism.** For an activation $\mathbf{x}\in\mathbb{R}^{d}$, an SAE has a linear encoder with a ReLU, a linear decoder, and an overcomplete hidden width $d_{\text{sae}} = R\,d$ ($R$ the expansion factor):

<a id="eq-1"></a><!-- eq:6-1 -->
$$
\mathbf{f} = \mathrm{ReLU}\!\big(W_{\text{enc}}(\mathbf{x}-\mathbf{b}_{\text{dec}}) + \mathbf{b}_{\text{enc}}\big), \qquad \hat{\mathbf{x}} = W_{\text{dec}}\,\mathbf{f} + \mathbf{b}_{\text{dec}}. \tag{1}
$$

<a id="p-61-sparse-autoencoders-saes-headline-4"></a><!-- para:61-sparse-autoencoders-saes-headline-4 --> It is trained to reconstruct $\mathbf{x}$ under a sparsity penalty. The load-bearing subtlety is that a naive L1 penalty on $\mathbf{f}$ can be gamed by shrinking decoder-column norms while inflating activations, so the canonical objective scales each feature's penalty by its decoder-column norm (equivalently, unit-normalize decoder columns and penalize $\lVert\mathbf{f}\rVert_1$):

<a id="eq-2"></a><!-- eq:6-2 -->
$$
\mathcal{L} = \mathbb{E}_{\mathbf{x}}\Big[\; \lVert \mathbf{x} - \hat{\mathbf{x}} \rVert_2^2 \;+\; \lambda \sum_{i} f_i \, \lVert W_{\text{dec},i} \rVert_2 \;\Big]. \tag{2}
$$

<a id="p-61-sparse-autoencoders-saes-headline-5"></a><!-- para:61-sparse-autoencoders-saes-headline-5 --> The decoder columns $\mathbf{d}_i = W_{\text{dec},i}/\lVert W_{\text{dec},i}\rVert$ are the dictionary atoms of Equation <!-- ref:2-4 -->[(4)](fundamentals.md#eq-4); a well-trained SAE makes them individually monosemantic where the neuron basis was polysemantic. Bricken et al. found a large majority of learned features human-interpretable on a one-layer model <!-- cite:7 --> [[7]](references.md#ref-7); Templeton et al. scaled to Claude 3 Sonnet's residual stream with dictionaries of ~1M, ~4M, and ~34M features, surfacing abstract multilingual/multimodal features (the Golden Gate Bridge feature) and safety-relevant features (deception, sycophancy) <!-- cite:8 --> [[8]](references.md#ref-8). *(The exact feature counts and "alive"-feature figure are read from <!-- cite:8 --> [[8]](references.md#ref-8) in the citation-audit pass; the residual stream is chosen over MLP/attention because it is lower-dimensional and accumulates all upstream writes.)*

<a id="p-61-sparse-autoencoders-saes-headline-6"></a><!-- para:61-sparse-autoencoders-saes-headline-6 --> **Worked example — the loss-recovered metric.** SAE fidelity is measured by how much of the model's next-token loss survives when the SAE reconstruction is spliced back in. With original CE $\mathcal{L}_{\text{orig}}$, zero-ablation CE $\mathcal{L}_{\text{zero}}$ (activation replaced by $\mathbf{0}$), and reconstructed CE $\mathcal{L}_{\text{rec}}$:

<a id="eq-3"></a><!-- eq:6-3 -->
$$
\text{loss recovered} = \frac{\mathcal{L}_{\text{zero}} - \mathcal{L}_{\text{rec}}}{\mathcal{L}_{\text{zero}} - \mathcal{L}_{\text{orig}}}. \tag{3}
$$

<a id="p-61-sparse-autoencoders-saes-headline-7"></a><!-- para:61-sparse-autoencoders-saes-headline-7 --> Illustratively, with $\mathcal{L}_{\text{orig}} = 3.0$, $\mathcal{L}_{\text{zero}} = 6.0$, $\mathcal{L}_{\text{rec}} = 3.3$ nats, loss recovered $= (6.0-3.3)/(6.0-3.0) = 90\%$ — a perfect reconstruction scores $100\%$, a zero reconstruction $0\%$, and a reconstruction *worse* than deletion scores negative. This metric, L0, and auto-interp are defined in § <!-- secxref:10.3 -->[§10.3](evaluation-and-metrics.md#sec-10.3).

<a id="p-61-sparse-autoencoders-saes-headline-8"></a><!-- para:61-sparse-autoencoders-saes-headline-8 --> **Limits & epistemic tag.** SAEs give an *unsupervised, correlational* feature basis — a decomposition, not a circuit; they suffer several pathologies (§ <!-- secref:6.5 -->[§6.5](#sec-6.5)); and their downstream usefulness is now contested (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)). *Epistemic status: a genuine advance for feature discovery, under active re-evaluation for feature action.*

<!-- sec:6.2 -->
### <a id="sec-6.2"></a>6.2 SAE architecture variants [load-bearing]

<a id="p-62-sae-architecture-variants-load-bearing-1"></a><!-- para:62-sae-architecture-variants-load-bearing-1 --> Every variant targets the same pathology: the L1 penalty in Equation <!-- ref:6-2 -->[(2)](#eq-2) is a *magnitude* penalty, so it biases the surviving activations downward ("shrinkage") — a soft-thresholding bias familiar from LASSO. Each variant decouples the sparsity signal from the reconstruction magnitude a different way.

- <a id="p-62-sae-architecture-variants-load-bearing-2"></a><!-- para:62-sae-architecture-variants-load-bearing-2 --> **Gated SAE** <!-- cite:10 --> [[10]](references.md#ref-10) — splits the encoder into a **gate** path (a Heaviside decision of *which* features fire, carrying the L1 penalty) and an unpenalized **magnitude** path (*how much* they fire). With weight tying it reduces to a JumpReLU. Pareto-improves reconstruction-vs-L0 over the ReLU SAE on GELU-1L, Pythia-2.8B, Gemma-7B at ~$2 d_{\text{sae}}$ extra parameters.
- **TopK SAE** <!-- cite:11 --> [[11]](references.md#ref-11) — replaces ReLU+L1 with a hard $\mathbf{f} = \mathrm{TopK}(W_{\text{enc}}(\mathbf{x}-\mathbf{b}))$, keeping only the $k$ largest pre-activations. This sets $L_0 = k$ exactly (no $\lambda$ to tune) and removes shrinkage on the surviving $k$. OpenAI fit clean joint scaling laws for reconstruction loss in dictionary size $n$ and sparsity $k$:

<a id="eq-4"></a><!-- eq:6-4 -->
$$
L(n,k) = \exp\!\big(\alpha + \beta_k \log k + \beta_n \log n + \gamma \log k \log n\big) + \exp\!\big(\zeta + \eta \log k\big), \tag{4}
$$

<a id="p-62-sae-architecture-variants-load-bearing-3"></a><!-- para:62-sae-architecture-variants-load-bearing-3 -->   with fitted $\alpha=-0.50,\ \beta_k=0.26,\ \beta_n=-0.017,\ \gamma=-0.042,\ \zeta=-1.32,\ \eta=-0.085$ <!-- cite:11 --> [[11]](references.md#ref-11), trained up to 16M latents on GPT-4-family models with an auxiliary "AuxK" loss (weight $\alpha_{\text{aux}}=1/32$, $k_{\text{aux}}=512$) that keeps the dead-latent rate to ~7% at the largest scale. *(Constants are transcribed from <!-- cite:11 --> [[11]](references.md#ref-11) Eq. 3 and re-verified against the PDF in the citation-audit pass, since dense multi-parameter equations are exactly where OCR drift bites.)*
- <a id="p-62-sae-architecture-variants-load-bearing-4"></a><!-- para:62-sae-architecture-variants-load-bearing-4 --> **JumpReLU SAE** <!-- cite:12 --> [[12]](references.md#ref-12) — a learned per-feature threshold $\theta$: $\mathbf{f} = \boldsymbol{\pi}\odot H(\boldsymbol{\pi}-\boldsymbol{\theta})$ with pre-activation $\boldsymbol{\pi}=W_{\text{enc}}(\mathbf{x}-\mathbf{b}_{\text{dec}})+\mathbf{b}_{\text{enc}}$, trained against an L0 target using straight-through estimators (a kernel-density pseudo-gradient in an $\varepsilon$-window). Matches or beats Gated and TopK on Gemma 2 9B; it is the architecture behind the open Gemma Scope suite (§ <!-- secxref:12.3 -->[§12.3](state-of-the-art-and-practice.md#sec-12.3)).
- **BatchTopK** <!-- cite:13 --> [[13]](references.md#ref-13) *[catalog-only]* — relaxes TopK's per-token $k$ to a per-*batch* budget, letting hard tokens use more features. Reconstruction: `n/a (catalog; beats TopK, ≈ JumpReLU, exact deltas in <!-- cite:13 --> [[13]](references.md#ref-13))`.
- **Matryoshka SAE** <!-- cite:14 --> [[14]](references.md#ref-14) *[catalog-only]* — trains nested dictionary prefixes so early latents capture broad concepts, directly targeting feature absorption/splitting (§ <!-- secref:6.5 -->[§6.5](#sec-6.5)); it leads SAEBench's disentanglement metrics (§ <!-- secxref:10.4 -->[§10.4](evaluation-and-metrics.md#sec-10.4)). Full derivation: `n/a (catalog)`.

<a id="p-62-sae-architecture-variants-load-bearing-5"></a><!-- para:62-sae-architecture-variants-load-bearing-5 --> The threshold/STE and shrinkage derivations are in Appendix <!-- secxref:D.2 -->[§D.2](appendix-d-sae-derivations.md#sec-D.2).

<!-- sec:6.3 -->
### <a id="sec-6.3"></a>6.3 Transcoders [load-bearing]

<a id="p-63-transcoders-load-bearing-1"></a><!-- para:63-transcoders-load-bearing-1 --> **One-line idea.** Instead of reconstructing a layer's activations from themselves (SAE), approximate a sublayer's *input→output function* with a wide sparse map — sparsifying the *computation*, not just the representation.

<a id="p-63-transcoders-load-bearing-2"></a><!-- para:63-transcoders-load-bearing-2 --> **Placement & lineage.** Dunefsky et al. <!-- cite:17 --> [[17]](references.md#ref-17); **skip transcoders** (Paulo et al. <!-- cite:18 --> [[18]](references.md#ref-18)) add an affine skip so the sparse part need only model the nonlinear residual. The key enabler of attribution graphs (§ <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)).

<a id="p-63-transcoders-load-bearing-3"></a><!-- para:63-transcoders-load-bearing-3 --> **Mechanism.** A transcoder for an MLP learns $\hat{\mathbf{y}} = W_{\text{dec}}\,\mathrm{ReLU}(W_{\text{enc}}\mathbf{x}+\mathbf{b})+\mathbf{b}_{\text{dec}} \approx \mathrm{MLP}(\mathbf{x})$, reconstructing the *output* $\mathbf{y}$ from the *input* $\mathbf{x}$ under an L1 penalty. Because $\hat{\mathbf{y}}$ is linear in the sparse code, circuit tracing can route a linear path *through* the MLP — an input feature → output feature edge — which plain SAEs (giving features only before and after the nonlinearity) cannot. This is why the frontier moved from SAEs to transcoders for circuit work; Paulo et al. argue transcoder features are also simply *more interpretable* than SAE features at matched sparsity <!-- cite:18 --> [[18]](references.md#ref-18).

<a id="p-63-transcoders-load-bearing-4"></a><!-- para:63-transcoders-load-bearing-4 --> **Epistemic tag.** *Rising default for circuit-level work; the substrate under attribution graphs.*

<!-- sec:6.4 -->
### <a id="sec-6.4"></a>6.4 Crosscoders [load-bearing]

<a id="p-64-crosscoders-load-bearing-1"></a><!-- para:64-crosscoders-load-bearing-1 --> **One-line idea.** One shared sparse dictionary that reads/writes *several layers at once* (or two *models* at once), collapsing cross-layer feature duplication and enabling model diffing.

<a id="p-64-crosscoders-load-bearing-2"></a><!-- para:64-crosscoders-load-bearing-2 --> **Placement & lineage.** Anthropic <!-- cite:19 --> [[19]](references.md#ref-19); the follow-up model-diffing update <!-- cite:19 --> [[19]](references.md#ref-19) (same thread). Motivated by the observation that a feature persisting across layers is re-discovered as a near-duplicate by each per-layer SAE, fragmenting circuits.

<a id="p-64-crosscoders-load-bearing-3"></a><!-- para:64-crosscoders-load-bearing-3 --> **Mechanism.** A crosscoder encodes one shared code $\mathbf{f} = \mathrm{ReLU}\big(\sum_\ell W_{\text{enc}}^{(\ell)}\mathbf{x}^{(\ell)} + \mathbf{b}\big)$ and reconstructs each layer with a per-layer decoder $\hat{\mathbf{x}}^{(\ell)} = W_{\text{dec}}^{(\ell)}\mathbf{f}+\mathbf{b}^{(\ell)}$, with the L1 penalty summed over (feature, layer) so a feature "pays once" for appearing at many layers. Swap the layer axis for a model axis (model A vs. model B at the same layer) and each latent's **relative decoder norm** between the two models classifies it as shared vs. model-exclusive — the **model-diffing** application (e.g. base vs. fine-tuned), where exclusive features tend to be more polysemantic <!-- cite:19 --> [[19]](references.md#ref-19).

<a id="p-64-crosscoders-load-bearing-4"></a><!-- para:64-crosscoders-load-bearing-4 --> **Epistemic tag.** *A promising research tool, especially for model diffing; still preliminary (released as a "research update").*

<!-- sec:6.5 -->
### <a id="sec-6.5"></a>6.5 SAE pathologies [load-bearing]

<a id="p-65-sae-pathologies-load-bearing-1"></a><!-- para:65-sae-pathologies-load-bearing-1 --> Five well-documented failure modes bound what SAE features can be trusted to mean:

- <a id="p-65-sae-pathologies-load-bearing-2"></a><!-- para:65-sae-pathologies-load-bearing-2 --> **Feature splitting** <!-- cite:7 --> [[7]](references.md#ref-7) — as $d_{\text{sae}}$ grows, one coarse feature splits into several specific children (a Base64 feature → three Base64 sub-features); no single width is canonically "correct," so a feature's identity is resolution-dependent.
- **Feature absorption** <!-- cite:15 --> [[15]](references.md#ref-15) — under sparsity pressure a specific child feature silently *absorbs* a general parent's job, so a seemingly monosemantic "starts-with-L" feature fails to fire on cases it logically covers; precision/recall trade directly against L0.
- **Dead & dense features** — dead latents never fire (wasted capacity; mitigated by resampling, ghost gradients, geometric-median decoder-bias init), dense latents fire almost always (uninterpretable leftover directions).
- **Activation shrinkage** — the L1 bias of § <!-- secref:6.2 -->[§6.2](#sec-6.2), the shared target of Gated/TopK/JumpReLU.
- **"Dark matter"** <!-- cite:16 --> [[16]](references.md#ref-16) — even a good SAE leaves a large residual error that is *structured*, not noise: about half the error vector and >90% of its norm is linearly predictable from the original activation, meaning the sparse code systematically misses directions a linear probe already sees.

<a id="p-65-sae-pathologies-load-bearing-3"></a><!-- para:65-sae-pathologies-load-bearing-3 --> These pathologies are why SAE *evaluation* (§ <!-- secxref:10.3 -->[§10.3](evaluation-and-metrics.md#sec-10.3)) needs disentanglement metrics beyond the sparsity–fidelity frontier, and they are part of the empirical case in the SAE debate (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)).
