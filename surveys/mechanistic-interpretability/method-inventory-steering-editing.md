<!-- sec:7 -->
## <a id="sec-7"></a>7 Method inventory IV — steering and model editing

<a id="p-7-method-inventory-iv-steering-and-model-editing-1"></a><!-- para:7-method-inventory-iv-steering-and-model-editing-1 --> These methods do not just *read* a mechanism; they *use* it to control the model — at inference (steering) or in the weights (editing). They are the most application-facing corner of MI and the clearest evidence that the linear-representation hypothesis has causal teeth. Full steering-vector and ROME/MEMIT derivations: Appendix <!-- secxref:E -->[§E](appendix-e-steering-and-editing-math.md#sec-E).

<!-- sec:7.1 -->
### <a id="sec-7.1"></a>7.1 Activation steering / steering vectors [load-bearing]

<a id="p-71-activation-steering-steering-vectors-load-bearing-1"></a><!-- para:71-activation-steering-steering-vectors-load-bearing-1 --> **One-line idea.** Compute a concept direction from contrasting examples and add it to the residual stream at inference to turn the behavior up or down — no weight updates.

<a id="p-71-activation-steering-steering-vectors-load-bearing-2"></a><!-- para:71-activation-steering-steering-vectors-load-bearing-2 --> **Placement & lineage.** ActAdd (Turner et al. <!-- cite:46 --> [[46]](references.md#ref-46)) from a single contrastive prompt pair; **Contrastive Activation Addition** (CAA, Rimsky et al. <!-- cite:47 --> [[47]](references.md#ref-47)) generalized to a dataset difference-in-means. The operational face of the LRH (§ <!-- secxref:2.3 -->[§2.3](fundamentals.md#sec-2.3)).

<a id="p-71-activation-steering-steering-vectors-load-bearing-3"></a><!-- para:71-activation-steering-steering-vectors-load-bearing-3 --> **Mechanism.** From $N$ contrastive pairs $\{(\mathbf{a}^+_i, \mathbf{a}^-_i)\}$ (positive vs. negative behavior, activations read at a chosen layer $\ell$), form the difference-in-means direction and add it, scaled, at inference:

<a id="eq-1"></a><!-- eq:7-1 -->
$$
\mathbf{v}_\ell = \frac{1}{N}\sum_{i=1}^{N}\big(\mathbf{a}^+_{\ell,i} - \mathbf{a}^-_{\ell,i}\big), \qquad \mathbf{h}_\ell \leftarrow \mathbf{h}_\ell + c\,\mathbf{v}_\ell. \tag{1}
$$

<a id="p-71-activation-steering-steering-vectors-load-bearing-4"></a><!-- para:71-activation-steering-steering-vectors-load-bearing-4 --> Averaging over the dataset cancels per-pair idiosyncrasy that a single-pair ActAdd vector carries. CAA on Llama-2-7B-chat steers sycophancy with $c = \pm 2$ at layer 13; ActAdd steers GPT-2-XL/GPT-J/Llama-13B with hand-found layer/coefficient pairs <!-- cite:46 --> [[46]](references.md#ref-46), <!-- cite:47 --> [[47]](references.md#ref-47). *(Reported TruthfulQA deltas are search-derived; verified in the citation-audit pass.)*

<a id="p-71-activation-steering-steering-vectors-load-bearing-5"></a><!-- para:71-activation-steering-steering-vectors-load-bearing-5 --> **Limits & epistemic tag.** Layer and coefficient need tuning; too large a $c$ degrades coherence. *A cheap, robust control method; the difference-in-means baseline that SAE-feature steering must beat (§ <!-- secref:7.6 -->[§7.6](#sec-7.6)).*

<!-- sec:7.2 -->
### <a id="sec-7.2"></a>7.2 Representation engineering (RepE) [load-bearing]

<a id="p-72-representation-engineering-repe-load-bearing-1"></a><!-- para:72-representation-engineering-repe-load-bearing-1 --> **One-line idea.** A top-down framework: locate a concept's representation with a PCA-style scan over contrastive stimuli, then read or control it.

<a id="p-72-representation-engineering-repe-load-bearing-2"></a><!-- para:72-representation-engineering-repe-load-bearing-2 --> **Placement & lineage.** Zou et al. <!-- cite:48 --> [[48]](references.md#ref-48); generalizes steering from a single mean-difference to a population-level "representation reading + control" methodology borrowed from cognitive neuroscience.

<a id="p-72-representation-engineering-repe-load-bearing-3"></a><!-- para:72-representation-engineering-repe-load-bearing-3 --> **Mechanism.** **Linear Artificial Tomography (LAT)** designs stimulus pairs that isolate a concept (honesty, power-seeking), collects end-token hidden states, and extracts the dominant separating direction(s) by **PCA** over the paired differences. Control then uses that direction three ways: a static **reading vector** (add it, as in § <!-- secref:7.1 -->[§7.1](#sec-7.1)), a dynamic **contrast vector** (run the input twice with opposing instructions and subtract in real time), or **LoRRA** (a low-rank fine-tune that moves representations toward the direction). Unsupervised honesty control via RepE improved Llama-2 TruthfulQA by +18.1 points over zero-shot, SOTA at the time; the LoRRA fine-tune raises Llama-2-Chat TruthfulQA by +11.3 points (7B, 31.0→42.3) and +11.6 points (13B, 35.9→47.5) <!-- cite:48 --> [[48]](references.md#ref-48). *(Verified against [48] Table 2 in the citation-audit pass; a +6.6/+13.1 figure from a secondary source did not match the primary and was corrected.)*

<a id="p-72-representation-engineering-repe-load-bearing-4"></a><!-- para:72-representation-engineering-repe-load-bearing-4 --> **Epistemic tag.** *A unifying framework for read+control; PCA-over-differences is the recurring extraction primitive.*

<!-- sec:7.3 -->
### <a id="sec-7.3"></a>7.3 The refusal direction [load-bearing]

<a id="p-73-the-refusal-direction-load-bearing-1"></a><!-- para:73-the-refusal-direction-load-bearing-1 --> **One-line idea.** Refusal — comply with benign, decline harmful — is mediated by a *single* residual-stream direction; ablate it to jailbreak, add it to induce refusal.

<a id="p-73-the-refusal-direction-load-bearing-2"></a><!-- para:73-the-refusal-direction-load-bearing-2 --> **Placement & lineage.** Arditi et al. <!-- cite:49 --> [[49]](references.md#ref-49); the crispest necessity-and-sufficiency result for a single behavioral direction, and a striking cross-model universality claim (13 open chat models, up to 72B, across Llama/Qwen/Gemma/Yi).

<a id="p-73-the-refusal-direction-load-bearing-3"></a><!-- para:73-the-refusal-direction-load-bearing-3 --> **Mechanism.** Extract the direction $\mathbf{r}$ by difference-in-means (§ <!-- secref:7.1 -->[§7.1](#sec-7.1)) over harmful vs. harmless instructions. **Directional ablation** removes $\mathbf{r}$'s component from the stream at every layer, so the model can never represent "refuse":

<a id="eq-2"></a><!-- eq:7-2 -->
$$
\mathbf{h}' = \mathbf{h} - \frac{\mathbf{h}^\top \hat{\mathbf{r}}}{\lVert \hat{\mathbf{r}}\rVert^2}\,\hat{\mathbf{r}}, \qquad \hat{\mathbf{r}} = \mathbf{r}/\lVert\mathbf{r}\rVert. \tag{2}
$$

<a id="p-73-the-refusal-direction-load-bearing-4"></a><!-- para:73-the-refusal-direction-load-bearing-4 --> Applied uniformly, this bypasses refusal on harmful prompts; adding $c\,\mathbf{r}$ instead induces refusal on harmless ones (sufficiency). The ablation can be **baked into the weights** by orthogonalizing every matrix that writes to the stream against $\mathbf{r}$ (a rank-one edit per matrix), producing a permanently non-refusing checkpoint — the technique behind community "abliteration" tooling <!-- cite:49 --> [[49]](references.md#ref-49).

<a id="p-73-the-refusal-direction-load-bearing-5"></a><!-- para:73-the-refusal-direction-load-bearing-5 --> **Limits & epistemic tag.** A dual-use result (it *is* a white-box jailbreak); "single direction" is a strong claim that holds well on the models tested but is an empirical, per-model finding. *One of MI's cleanest and most reproducible causal results.*

<!-- sec:7.4 -->
### <a id="sec-7.4"></a>7.4 ROME — locating and editing a fact [load-bearing]

<a id="p-74-rome-locating-and-editing-a-fact-load-bearing-1"></a><!-- para:74-rome-locating-and-editing-a-fact-load-bearing-1 --> **One-line idea.** Localize a fact to a mid-layer MLP by causal tracing, then insert a new fact with a closed-form rank-one weight update that treats the MLP as an associative memory.

<a id="p-74-rome-locating-and-editing-a-fact-load-bearing-2"></a><!-- para:74-rome-locating-and-editing-a-fact-load-bearing-2 --> **Placement & lineage.** Meng et al. <!-- cite:31 --> [[31]](references.md#ref-31); the bridge from causal tracing (§ <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1)) to a weight edit, and the case study Hase et al. <!-- cite:54 --> [[54]](references.md#ref-54) later used to show localization does not validate editing.

<a id="p-74-rome-locating-and-editing-a-fact-load-bearing-3"></a><!-- para:74-rome-locating-and-editing-a-fact-load-bearing-3 --> **Mechanism.** Causal tracing localizes factual recall to the down-projection $W$ of a mid-layer MLP at the last subject token (§ <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1)). Treating $W$ as a linear associative memory ($W\mathbf{k}\approx\mathbf{v}$ over many stored key→value pairs), ROME computes a key $\mathbf{k}_*$ (the MLP input at the subject token, averaged over prefixes) and a value $\mathbf{v}_*$ (found by gradient descent so the model outputs the new object), then solves for the minimal-interference update that satisfies $\hat W\mathbf{k}_* = \mathbf{v}_*$ exactly while preserving the response to a corpus of other keys (second moment $C = KK^\top$). The constrained least-squares solution is a **rank-one update**:

<a id="eq-3"></a><!-- eq:7-3 -->
$$
\hat W = W + \Lambda\,(C^{-1}\mathbf{k}_*)^{\!\top}, \qquad \Lambda = \frac{\mathbf{v}_* - W\mathbf{k}_*}{(C^{-1}\mathbf{k}_*)^{\!\top}\mathbf{k}_*}. \tag{3}
$$

<a id="p-74-rome-locating-and-editing-a-fact-load-bearing-4"></a><!-- para:74-rome-locating-and-editing-a-fact-load-bearing-4 --> The update direction $C^{-1}\mathbf{k}_*$ is the key whitened by the preserved-memory covariance, so the edit disturbs other facts as little as possible; the scalar $\Lambda$ enforces the constraint exactly. Full Lagrange-multiplier derivation: Appendix <!-- secxref:E.2 -->[§E.2](appendix-e-steering-and-editing-math.md#sec-E.2).

<a id="p-74-rome-locating-and-editing-a-fact-load-bearing-5"></a><!-- para:74-rome-locating-and-editing-a-fact-load-bearing-5 --> **Limits & epistemic tag.** Single-fact; fragile under iterated edits (§ <!-- secref:7.5 -->[§7.5](#sec-7.5)); and — the deep caveat — **editing success does not validate the localization**: Hase et al. <!-- cite:54 --> [[54]](references.md#ref-54) find edit success is ~equally good at layers far from the causally-traced site (a regression of edit success on layer gets $R^2\approx 0.585$; adding the causal-tracing effect size improves it by at most 0.03), so "ROME works at layer $\ell$" is *not* evidence the fact is "stored at" $\ell$. *A landmark method whose main lesson is a methodological warning.*

<!-- sec:7.5 -->
### <a id="sec-7.5"></a>7.5 MEMIT — mass editing [load-bearing]

<a id="p-75-memit-mass-editing-load-bearing-1"></a><!-- para:75-memit-mass-editing-load-bearing-1 --> **One-line idea.** Spread the required residual change across a *range* of mid-layer MLPs and solve a batched least-squares insert, so thousands of facts can be edited at once without breaking the model.

<a id="p-75-memit-mass-editing-load-bearing-2"></a><!-- para:75-memit-mass-editing-load-bearing-2 --> **Placement & lineage.** Meng et al. <!-- cite:51 --> [[51]](references.md#ref-51); the scalable successor to ROME.

<a id="p-75-memit-mass-editing-load-bearing-3"></a><!-- para:75-memit-mass-editing-load-bearing-3 --> **Mechanism.** For each fact, optimize the target hidden state $\mathbf{z}_i$ at the last critical layer $L$ (as in ROME), take the residual delta $\boldsymbol{\delta}_i = \mathbf{z}_i - \mathbf{h}_i^{L}$, and spread it evenly across the critical layer range (for GPT-J, $R=\{3,\dots,8\}$ from causal tracing) so each layer absorbs a small share. At each layer it solves a **rank-$u$** batched generalization of Equation <!-- ref:7-3 -->[(3)](#eq-3) for a batch of $u$ facts, using the same $C = KK^\top$ preservation term. Spreading keeps each layer's perturbation small, which is why MEMIT scales to ~10,000 edits on GPT-J/GPT-NeoX where iterated ROME breaks far sooner <!-- cite:51 --> [[51]](references.md#ref-51).

<a id="p-75-memit-mass-editing-load-bearing-4"></a><!-- para:75-memit-mass-editing-load-bearing-4 --> **Limits & epistemic tag.** Still degrades under enough sequential editing — catastrophic forgetting has a measured onset (~1,400 edits in one stress test <!-- cite:52 --> [[52]](references.md#ref-52), where MEMIT forgets ~3× fewer prior facts than ROME). *The practical knowledge-editing default; not a substitute for retraining.*

<!-- sec:7.6 -->
### <a id="sec-7.6"></a>7.6 SAE-feature steering [catalog-only]

<a id="p-76-sae-feature-steering-catalog-only-1"></a><!-- para:76-sae-feature-steering-catalog-only-1 --> **One-line idea.** Clamp a single SAE feature to a large value to steer behavior in the feature basis (the Golden-Gate-Claude demo).

<a id="p-76-sae-feature-steering-catalog-only-2"></a><!-- para:76-sae-feature-steering-catalog-only-2 --> **Stated result + applicability.** Clamping the Golden Gate Bridge feature made Claude 3 Sonnet redirect nearly any conversation to the bridge <!-- cite:8 --> [[8]](references.md#ref-8), <!-- cite:75 --> [[75]](references.md#ref-75). Whether feature clamping *beats* a plain difference-in-means vector is contested: systematic evaluations find naive SAE steering does **not** beat simple baselines <!-- cite:66 --> [[66]](references.md#ref-66), while SAE-*informed* methods (SAE-TS <!-- cite:50 --> [[50]](references.md#ref-50), which uses the SAE to *target* a steering vector rather than clamp a feature) claim a better steering-vs-coherence trade-off. See § <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2).

- <a id="p-76-sae-feature-steering-catalog-only-3"></a><!-- para:76-sae-feature-steering-catalog-only-3 --> Full derivation: `n/a (catalog; the clamp is a special case of the addition in Equation` <!-- ref:7-1 -->[(1)](#eq-1) `applied in the SAE basis)`.
- Worked example: `n/a (catalog; head-to-head numbers are contested and are treated in § 12.2)`.

<a id="p-76-sae-feature-steering-catalog-only-4"></a><!-- para:76-sae-feature-steering-catalog-only-4 --> **Epistemic tag.** *A vivid demo and an open research question; not an established win over difference-in-means.*
