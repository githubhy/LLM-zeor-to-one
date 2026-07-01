<!-- sec:12 -->
## <a id="sec-12"></a>12 State of the art & practice

<!-- sec:12.1 -->
### <a id="sec-12.1"></a>12.1 What frontier labs actually do

<a id="p-121-what-frontier-labs-actually-do-1"></a><!-- para:121-what-frontier-labs-actually-do-1 --> Dominant practice, mapped to the four-step loop (§ <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1)):

| Lab | Find features | Build circuits | Validate | Apply |
|---|---|---|---|---|
| **Anthropic** | SAEs → crosscoders → cross-layer transcoders <!-- cite:7 --> [[7]](references.md#ref-7), <!-- cite:8 --> [[8]](references.md#ref-8), <!-- cite:19 --> [[19]](references.md#ref-19) | attribution graphs <!-- cite:20 --> [[20]](references.md#ref-20), <!-- cite:21 --> [[21]](references.md#ref-21) | feature clamping, auto-interp | Golden-Gate steering, safety features <!-- cite:75 --> [[75]](references.md#ref-75) |
| **Google DeepMind** | JumpReLU SAE suite (Gemma Scope) <!-- cite:12 --> [[12]](references.md#ref-12), <!-- cite:65 --> [[65]](references.md#ref-65) | ACDC / EAP-IG <!-- cite:40 --> [[40]](references.md#ref-40), <!-- cite:41 --> [[41]](references.md#ref-41) | RAVEL, SAEBench-style <!-- cite:64 --> [[64]](references.md#ref-64) | probing for monitoring <!-- cite:67 --> [[67]](references.md#ref-67) |
| **OpenAI** | TopK SAEs at 16M latents on GPT-4 <!-- cite:11 --> [[11]](references.md#ref-11) | — (feature-first) | probe-based eval, auto-interp <!-- cite:68 --> [[68]](references.md#ref-68) | concept extraction |
| **EleutherAI / academia** | tuned lens, open SAE tooling <!-- cite:23 --> [[23]](references.md#ref-23) | ACDC, EAP, causal scrubbing <!-- cite:40 --> [[40]](references.md#ref-40), <!-- cite:38 --> [[38]](references.md#ref-38), <!-- cite:42 --> [[42]](references.md#ref-42) | Delphi auto-interp <!-- cite:69 --> [[69]](references.md#ref-69) | open reproductions |

<a id="p-121-what-frontier-labs-actually-do-2"></a><!-- para:121-what-frontier-labs-actually-do-2 --> The pattern: **feature-finding converged on SAE-family dictionary learning** (ReLU → Gated/TopK/JumpReLU), **circuit-building is bifurcating** into cheap automated discovery (ACDC/EAP on small models) and attribution graphs (frontier models), and **validation is the weak link** everyone is trying to strengthen. The one lab with a native frontier-scale circuit method (Anthropic, attribution graphs) is also the one with model-weight access — reinforcing the "model access is a cost axis" point of § <!-- secxref:11.1 -->[§11.1](comparison-and-tradeoffs.md#sec-11.1).

<!-- sec:12.2 -->
### <a id="sec-12.2"></a>12.2 The SAE debate (2024–2025)

<a id="p-122-the-sae-debate-20242025-1"></a><!-- para:122-the-sae-debate-20242025-1 --> The single most important development of the survey window is a **reckoning for sparse autoencoders**, and it is worth stating plainly because it inverts the 2023 optimism.

<a id="p-122-the-sae-debate-20242025-2"></a><!-- para:122-the-sae-debate-20242025-2 --> **The empirical case against.** On *downstream* tasks, SAE features do not beat simple baselines (<!-- secxref:Q.3 -->[§Q.3](appendix-q-reader-questions.md#sec-Q.3)). **AxBench** <!-- cite:66 --> [[66]](references.md#ref-66) (Gemma-2-2B/9B) finds that for steering, plain **prompting** wins and fine-tuning is second, with SAEs "not competitive"; for concept detection, **difference-in-means** wins. A DeepMind study on out-of-distribution probing (detecting harmful intent) reaches the same conclusion <!-- cite:67 --> [[67]](references.md#ref-67) and prompted a public post *deprioritising SAE research* on the team. This is not a minor ablation — it is a major lab stepping back from a whole method family after its own negative results.

<a id="p-122-the-sae-debate-20242025-3"></a><!-- para:122-the-sae-debate-20242025-3 --> **Why the objective is the culprit.** An SAE optimizes reconstruction + sparsity of a *static activation snapshot*, an objective decoupled from any downstream task. Where labeled contrast pairs already exist (steering, probing), a supervised direction fit *directly* on the task signal has no reason to lose to an unsupervised decomposition — and does not. SAEs' genuine advantage — *unsupervised discovery of concepts you did not know to look for* — does not transfer to tasks where the concept is already specified. The honest framing, echoed by a 2025 title, is "use SAEs to discover unknown concepts, not to act on known ones."

<a id="p-122-the-sae-debate-20242025-4"></a><!-- para:122-the-sae-debate-20242025-4 --> **Where the field is pivoting.**

- <a id="p-122-the-sae-debate-20242025-5"></a><!-- para:122-the-sae-debate-20242025-5 --> **Transcoders + attribution graphs** (§§ <!-- secxref:6.3 -->[§6.3](method-inventory-dictionary.md#sec-6.3), <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3)) — Paulo et al. argue transcoder features are simply more interpretable than SAE features <!-- cite:18 --> [[18]](references.md#ref-18), and attribution graphs are the frontier circuit substrate <!-- cite:20 --> [[20]](references.md#ref-20). This is a convergent bet from two directions: interpretability-metric superiority and circuit-tracing utility.
- **Better dictionary objectives** — matching-pursuit SAEs (MP-SAE <!-- cite:77 --> [[77]](references.md#ref-77)) replace the single-shot linear encoder with an iterative residual pursuit that yields a hierarchical, non-flat code, targeting the feature-splitting/absorption pathologies (§ <!-- secxref:6.5 -->[§6.5](method-inventory-dictionary.md#sec-6.5)); Matryoshka SAEs <!-- cite:14 --> [[14]](references.md#ref-14) lead SAEBench disentanglement.
- **Not a wholesale abandonment.** The verdict is genuinely *contested*: papers arguing SAEs *can* beat baselines with the right feature selection exist alongside the negative results, so the survey records this as a live, non-converged debate as of mid-2026, not a settled defeat. What *is* settled is that the sparsity–fidelity frontier (§ <!-- secxref:10.3 -->[§10.3](evaluation-and-metrics.md#sec-10.3)) is the wrong target.

<!-- sec:12.3 -->
### <a id="sec-12.3"></a>12.3 Quantitative SOTA — published SAE suites

<a id="p-123-quantitative-sota-published-sae-suites-1"></a><!-- para:123-quantitative-sota-published-sae-suites-1 --> The largest *open* artifacts, with eval conditions disclosed (scale figures are read from the primary in the citation-audit pass; suites differ enough that cross-row comparison is only qualitative):

| Suite | Model / site | # SAEs · features | Sparsity | Train tokens | Open weights | Source |
|---|---|---|---|---|---|---|
| **Gemma Scope** <!-- cite:65 --> [[65]](references.md#ref-65) | Gemma 2 2B/9B (all layers/sublayers), 27B (select); resid + MLP + attn | >400 SAEs · >30M features | JumpReLU, $L_0$ bands ~10–150 | 4B / 8B / 16B by width | yes (CC-BY-4.0, HF) | arXiv:2408.05147 |
| **OpenAI GPT-4 SAE** <!-- cite:11 --> [[11]](references.md#ref-11) | GPT-4 (+ GPT-2-small); resid stream | up to 16M latents | TopK ($L_0=k$) | 40B | no (paper open) | arXiv:2406.04093 |
| **Scaling Monosemanticity** <!-- cite:8 --> [[8]](references.md#ref-8) | Claude 3 Sonnet; mid-layer resid | ~1M / ~4M / ~34M features | L1 (ReLU SAE) | — | no | transformer-circuits.pub |

<a id="p-123-quantitative-sota-published-sae-suites-2"></a><!-- para:123-quantitative-sota-published-sae-suites-2 --> **Reading the table.** Gemma Scope is the open workhorse the academic field builds on (Neuronpedia hosts it interactively); OpenAI's is the largest single-model SAE but weights are closed; Anthropic's is the production-scale existence proof (§ <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4)) but closed. The **normalization caveat** is essential: these suites differ in model, site, architecture (JumpReLU vs. TopK vs. ReLU), and sparsity regime, so a raw "features" count is not comparable across rows — only within a suite's own sweep. The per-stage practice map (§ <!-- secref:12.1 -->[§12.1](#sec-12.1)) and the SAE debate (§ <!-- secref:12.2 -->[§12.2](#sec-12.2)) are the load-bearing SOTA statements; this table is the artifact inventory behind them.
