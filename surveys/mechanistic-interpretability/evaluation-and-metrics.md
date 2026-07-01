<!-- sec:10 -->
## <a id="sec-10"></a>10 Evaluation & metrics

<a id="p-10-evaluation-metrics-1"></a><!-- para:10-evaluation-metrics-1 --> An interpretability result is a *claim*, and this section is how the field checks it. Two themes recur: the headline numbers are less robust than they look, and the network fights back (self-repair). Getting evaluation right is not bookkeeping — it is what separates a mechanism from a plausible story.

<!-- sec:10.1 -->
### <a id="sec-10.1"></a>10.1 Faithfulness, completeness, minimality [headline]

<a id="p-101-faithfulness-completeness-minimality-headline-1"></a><!-- para:101-faithfulness-completeness-minimality-headline-1 --> A circuit $C$ hypothesized to implement a behavior of model $M$ is scored on three axes, introduced for IOI <!-- cite:35 --> [[35]](references.md#ref-35) and formalized by ACDC <!-- cite:40 --> [[40]](references.md#ref-40). Let $\mathcal{F}(\cdot)$ be a scalar task metric (for IOI, mean logit difference).

- <a id="p-101-faithfulness-completeness-minimality-headline-2"></a><!-- para:101-faithfulness-completeness-minimality-headline-2 --> **Faithfulness** — does $C$ alone reproduce $M$'s behavior? Run $C$ with everything outside it ablated (typically mean-ablated over a reference distribution) and report the **recovered fraction**:

<a id="eq-1"></a><!-- eq:10-1 -->
$$
\text{recovered} = \frac{\mathcal{F}(C)}{\mathcal{F}(M)}. \tag{1}
$$

- <a id="p-101-faithfulness-completeness-minimality-headline-3"></a><!-- para:101-faithfulness-completeness-minimality-headline-3 --> **Completeness** — for every subset $K\subseteq C$, knocking out $K$ from both $C$ and $M$ should move the metric similarly ($\mathcal{F}(C\setminus K)\approx\mathcal{F}(M\setminus K)$); this catches a circuit that silently omits a component which only matters once something else is ablated — exactly what backup heads violate (§ <!-- secref:10.2 -->[§10.2](#sec-10.2)).
- **Minimality** — every node in $C$ should matter in some context; a node whose removal never changes the metric is dead weight.

<a id="p-101-faithfulness-completeness-minimality-headline-4"></a><!-- para:101-faithfulness-completeness-minimality-headline-4 --> **The non-robustness result (a load-bearing caution).** These numbers are not stable to implementation choices. Miller et al. <!-- cite:62 --> [[62]](references.md#ref-62) show the same IOI circuit's "logit-difference recovered" swings by more than 50 points depending on **node- vs. edge-ablation** (edge-ablation can push it to ~150%, i.e. the isolated circuit scores *above* the full model), on the **order of averaging** (mean-of-ratios $\ne$ ratio-of-means), and on prompt format. There is, as of writing, no single agreed operational faithfulness metric — a fact the survey treats as a genuine open problem (§ <!-- secxref:15.1 -->[§15.1](open-problems-and-roadmap.md#sec-15.1)), not a footnote. When this survey cites a faithfulness percentage, it names the ablation convention or flags that the primary must be consulted.

<!-- sec:10.2 -->
### <a id="sec-10.2"></a>10.2 Interpretability illusions and self-repair [load-bearing]

<a id="p-102-interpretability-illusions-and-self-repair-load-bearing-1"></a><!-- para:102-interpretability-illusions-and-self-repair-load-bearing-1 --> Two mechanisms make naive single-intervention conclusions mislead.

<a id="p-102-interpretability-illusions-and-self-repair-load-bearing-2"></a><!-- para:102-interpretability-illusions-and-self-repair-load-bearing-2 --> **Interpretability illusions** <!-- cite:58 --> [[58]](references.md#ref-58). A neuron (or direction) can look like a clean detector for a concept on one corpus and fail entirely on another — an artifact of the corpus occupying a narrow slice of activation space, not a real semantic unit. The methodological fix is to test any claimed concept direction across distributionally-different datasets before trusting it.

<a id="p-102-interpretability-illusions-and-self-repair-load-bearing-3"></a><!-- para:102-interpretability-illusions-and-self-repair-load-bearing-3 --> **Self-repair / the Hydra effect** <!-- cite:59 --> [[59]](references.md#ref-59). Ablating a component causes *other* components to compensate, so the measured metric drop **understates** the ablated component's true importance — every single-ablation faithfulness number is a *lower bound*. McGrath et al. <!-- cite:59 --> [[59]](references.md#ref-59) find downstream attention layers restore much of an ablated layer's effect (plus a late-MLP "counterbalancing" that downregulates whatever is now over-predicted); Wang et al.'s IOI backup heads <!-- cite:35 --> [[35]](references.md#ref-35) are the canonical instance (knocking out the main name-movers barely dents the logit difference because backups activate). Rushing & Nanda <!-- cite:60 --> [[60]](references.md#ref-60) decompose self-repair into two sub-mechanisms — **LayerNorm rescaling** (removing a component changes the residual norm, rescaling every other component's logit contribution: an artifact, not learned repair) and **Anti-Erasure neurons** (a genuine trained compensatory circuit) — and find it is real, general, but *imperfect and noisy*. This directly explains why the § <!-- secref:10.1 -->[§10.1](#sec-10.1) node-vs-edge faithfulness gap exists: different ablation granularities let different amounts of self-repair happen.

<a id="p-102-interpretability-illusions-and-self-repair-load-bearing-4"></a><!-- para:102-interpretability-illusions-and-self-repair-load-bearing-4 --> **Consequence.** A single ablation is a *lower bound* on importance; a robust conclusion requires the completeness check above, or a method (causal scrubbing, § <!-- secxref:5.5 -->[§5.5](method-inventory-causal.md#sec-5.5)) that resamples rather than deletes. *(Self-repair magnitudes are largely GPT-2/Chinchilla-era; frontier-scale behavior is open, § <!-- secxref:9.5 -->[§9.5](circuits-across-models.md#sec-9.5).)*

<!-- sec:10.3 -->
### <a id="sec-10.3"></a>10.3 SAE evaluation metrics [load-bearing]

<a id="p-103-sae-evaluation-metrics-load-bearing-1"></a><!-- para:103-sae-evaluation-metrics-load-bearing-1 --> SAEs are judged on metrics that trade off against each other; reporting one alone is a red flag.

- <a id="p-103-sae-evaluation-metrics-load-bearing-2"></a><!-- para:103-sae-evaluation-metrics-load-bearing-2 --> **Sparsity $L_0$** — mean nonzero features per token, $L_0 = \mathbb{E}_{\mathbf{x}}\lVert\mathbf{f}(\mathbf{x})\rVert_0$; the direct empirical target the L1 penalty only approximates.
- **Reconstruction** — MSE $\lVert\mathbf{x}-\hat{\mathbf{x}}\rVert_2^2$, or scale-invariant explained variance $1 - \mathrm{Var}(\mathbf{x}-\hat{\mathbf{x}})/\mathrm{Var}(\mathbf{x})$.
- **Cross-entropy loss recovered** — the downstream metric of Equation <!-- ref:6-3 -->[(3)](method-inventory-dictionary.md#eq-3): how much of the LM's next-token loss survives splicing the SAE reconstruction back in, relative to zero-ablation.
- **Auto-interp score** — the explain-simulate-correlate proxy of § <!-- secxref:8.1 -->[§8.1](method-inventory-automation.md#sec-8.1).

<a id="p-103-sae-evaluation-metrics-load-bearing-3"></a><!-- para:103-sae-evaluation-metrics-load-bearing-3 --> The core lesson of the field's re-evaluation (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)) is that the classic sparsity–fidelity frontier (loss recovered vs. $L_0$) does **not** track what matters downstream — interpretability, disentanglement, usefulness — which is what the benchmarks in § <!-- secref:10.4 -->[§10.4](#sec-10.4) were built to measure.

<!-- sec:10.4 -->
### <a id="sec-10.4"></a>10.4 Interpretability benchmarks [load-bearing]

- <a id="p-104-interpretability-benchmarks-load-bearing-1"></a><!-- para:104-interpretability-benchmarks-load-bearing-1 --> **SAEBench** <!-- cite:63 --> [[63]](references.md#ref-63) — evaluates 200+ SAEs across 8 metrics in 4 categories (concept detection, interpretability, reconstruction, feature disentanglement), on Pythia-160M and Gemma-2-2B. Its headline finding falsifies the sparsity-only view: **Matryoshka SAEs** (§ <!-- secxref:6.2 -->[§6.2](method-inventory-dictionary.md#sec-6.2)) lead on disentanglement even though they are not best on raw reconstruction, and the advantage grows with SAE width. *(The "who wins" ranking is already contested by newer 2025 variants — flagged in the evidence ledger, treated as unsettled in § 12.2.)*
- **RAVEL** <!-- cite:64 --> [[64]](references.md#ref-64) — evaluates *any* interpretability method's ability to intervene on one entity attribute (a city's country) without disturbing an entangled one (its continent), scoring a **Disentangle** = mean(Cause, Isolation). It brackets methods between raw neurons (weak baseline) and supervised **DAS** (§ <!-- secxref:5.6 -->[§5.6](method-inventory-causal.md#sec-5.6)) as a skyline; off-the-shelf SAEs generally underperform the supervised skyline — the same message as SAEBench. RAVEL is now also a SAEBench sub-metric.

<a id="p-104-interpretability-benchmarks-load-bearing-2"></a><!-- para:104-interpretability-benchmarks-load-bearing-2 --> **Takeaway.** The move from "reconstruct activations well" to "disentangle causally" is the single most important shift in how the field evaluates features, and it is what turned the SAE mood from optimism to scrutiny (§ <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2)).
