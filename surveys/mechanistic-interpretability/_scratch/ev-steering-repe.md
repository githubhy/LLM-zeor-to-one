# Evidence: Steering Vectors & Representation Engineering (RepE)

Scratch evidence file for mechanistic-interpretability survey. Format: one block
per question. Status: 4/4 questions answered (Q1-Q4 complete; see per-question
Gaps/caveats for follow-up reads still needed).

## Q1: Activation steering / steering vectors — adding a direction to the residual stream at inference; the difference-in-means construction (Turner et al. 2023 ActAdd; Rimsky et al. 2024 CAA)

- **Finding:** Two closely related but distinct methods establish "add a vector to
  the residual stream at inference time, no gradient steps" as a control technique.
  (1) **ActAdd** (Turner et al. 2023, arXiv:2308.10248, "Activation Addition:
  Steering Language Models Without Optimization" — earlier title "Steering
  Language Models With Activation Engineering") computes a steering vector from a
  **single contrastive prompt pair** (e.g. `"Love"` vs `"Hate"`) by taking the
  difference of residual-stream activations at a chosen layer for the two prompts,
  then adds that vector (scaled by a coefficient) to the residual stream at that
  layer for all forward passes on new prompts. (2) **CAA** (Rimsky et al. 2024,
  arXiv:2312.06681, "Steering Llama 2 via Contrastive Activation Addition")
  generalizes this to a **difference-in-means over a dataset of many contrastive
  pairs** (positive vs negative behavioral examples, e.g. sycophantic vs
  non-sycophantic multiple-choice answers): the steering vector is the mean
  activation on the positive set minus the mean activation on the negative set,
  computed at the answer-token position at a specific layer, then added at all
  token positions after the user's prompt during generation with a signed
  multiplier to increase or decrease the behavior.
- **Mechanism / derivation notes:**
  - ActAdd: pick a layer $\ell$ and a contrastive prompt pair $(p^+, p^-)$ (e.g.
    "Love" / "Hate"). Run both prompts through the model, read off the residual
    stream activation at layer $\ell$ at the final token position for each:
    $\mathbf{a}^+_\ell$, $\mathbf{a}^-_\ell$. Steering vector
    $\mathbf{v}_\ell = \mathbf{a}^+_\ell - \mathbf{a}^-_\ell$. At inference on a new
    prompt, the forward pass is modified so the residual stream at layer $\ell$
    becomes $\mathbf{h}_\ell \leftarrow \mathbf{h}_\ell + c\,\mathbf{v}_\ell$ for a
    scalar coefficient $c$ (can be applied at every token position going forward).
    Only 1-2 contrastive prompt samples needed (vs "dozens to hundreds" for related
    optimization-based methods, per the abstract).
  - CAA (difference-in-means): construct a dataset of $N$ contrastive pairs
    $\{(x_i^+, x_i^-)\}$ representing a behavior (e.g., A/B multiple-choice answer
    pairs where one option exhibits sycophancy and the other doesn't). For each
    pair, take the residual-stream activation at the token position corresponding
    to the answer letter, at a fixed layer $\ell$, for both the positive and
    negative completion. The steering vector is
    $\mathbf{v}_\ell = \frac{1}{N}\sum_i \mathbf{a}^+_{\ell,i} - \frac{1}{N}\sum_i \mathbf{a}^-_{\ell,i}$
    (mean-difference over the dataset, i.e. "difference-in-means" — this averages
    out per-pair idiosyncratic noise that a single-pair ActAdd vector would carry).
    At generation time the vector is added at **all token positions after the
    user's prompt** (not just one position) with multiplier $c \in \{-2, +2\}$ (sign
    flips to suppress vs amplify the behavior).
  - Both methods rely on the empirical finding that many high-level behavioral /
    semantic concepts are linearly represented as directions in residual-stream
    activation space (the "linear representation hypothesis"), so a single
    direction addition can shift the concept's expression without an optimization
    loop over the model weights.
- **Values:**
  - ActAdd (Turner et al. 2023): demonstrated on **GPT-2-XL**, replicated on
    **Llama-13B** and **GPT-J-6B**. Example vectors: `"Love" − "Hate"` injected
    before **attention layer 6** with coefficient **+5**; `" wedding" − " "`
    injected before **attention layer 15** with coefficient **+5.23** — quote:
    "Love vector is most effective inserted at layer 6, while more abstract
    vectors like the Conspiracy vector are better inserted later, at layer 23."
    Suitable steering prompts found with as few as 2 samples.
  - CAA (Rimsky et al. 2024): steering applied on **Llama 2 7B Chat** at
    **layer 13** with multipliers **+2 / −2** on the sycophancy vector. Baseline
    (no steering): unmodified Llama-2-7B-chat assigns an average of **80%**
    probability to the sycophantic A/B answer token in few-shot sycophancy tests.
    Subtracting the sycophancy vector improves TruthfulQA performance by **+0.01**;
    adding it worsens TruthfulQA performance by **−0.05** (exact metric-unit
    unclear from snippet — flagged as gap below, needs the paper's Table for the
    precise TruthfulQA scale).
- **Sources:**
  - Turner, A. M., Thiergart, L., Udell, D., Leech, G., Mini, U., MacDiarmid, M.
    (2023), "Activation Addition: Steering Language Models Without Optimization"
    (earlier title: "Steering Language Models With Activation Engineering"),
    arXiv:2308.10248 | tier=Primary | confidence=H
  - Rimsky, N., Gabrieli, N., Schulz, J. [also listed as Wuschel Schulz], Tong, M.,
    Hubinger, E., Turner, A. M. (2023/2024), "Steering Llama 2 via Contrastive
    Activation Addition", arXiv:2312.06681 (ACL 2024, aclanthology.org/2024.acl-long.828) |
    tier=Primary | confidence=H
  - turntrout.com/gpt2-steering-vectors (Turner's own explainer for ActAdd, matches
    arXiv content) | tier=Explainer | confidence=M
  - turntrout.com/llama2-steering-vectors ("Steering Llama-2 with Contrastive
    Activation Additions", author blog matching CAA arXiv content) | tier=Explainer
    | confidence=M
- **Gaps/caveats:** Did not verify exact TruthfulQA metric definition/scale for
  the ±0.01/−0.05 CAA sycophancy numbers from search snippets alone (would need
  the PDF table) — recorded as approximate/needs-verification. ActAdd's toxicity
  reduction / sentiment control "state-of-the-art" claim is from a 2023 paper;
  possibly superseded by 2024-2026 steering literature (not checked against
  later benchmarks in this pass). Both papers' full quantitative tables (e.g.
  CAA's full behavioral dataset results across corrigibility, power-seeking,
  etc.) not fully extracted — only sycophancy numbers captured.

## Q2: Representation Engineering (Zou et al. 2023, arXiv:2310.01405) — Linear Artificial Tomography (LAT), reading and controlling representations of concepts like honesty/power

- **Finding:** Representation Engineering (RepE) is a "top-down" framework (population-level
  representations as the unit of analysis, borrowing from cognitive neuroscience) with two
  halves: **Representation Reading** (find where/how a high-level concept, e.g. honesty,
  power, is linearly encoded) via **Linear Artificial Tomography (LAT)**, and
  **Representation Control** (use the discovered direction to steer generation) via three
  baselines — **Reading Vector**, **Contrast Vector**, and **LoRRA (Low-Rank Representation
  Adaptation)**. Applied to Llama-2 models, unsupervised honesty control improves TruthfulQA
  accuracy by +18.1 percentage points over zero-shot, described as SOTA at the time; LoRRA
  gives +6.6% honesty improvement on Llama-2-7B and +13.1% on Llama-2-13B.
- **Mechanism / derivation notes:**
  - **LAT scan (Representation Reading):** (1) design a stimulus/task that elicits
    orthogonal (concept-isolated) neural activity — construct paired prompts that evoke
    opposing instances of the concept (e.g., "Pretend you're an honest/dishonest person and
    answer..."); typical set sizes are 5-128 contrastive pairs; (2) run the model on both
    members of each pair, collect the hidden-state representation at each layer at the
    **end token position**; (3) apply an unsupervised linear-modeling technique — primarily
    **PCA** (occasionally K-means) — over the collected activation differences to extract
    the dominant direction(s) that separate the two concept poles at each layer. This
    produces a per-layer reading direction (e.g. "honesty direction") without needing labeled
    data beyond the paired stimulus design.
  - **Representation Control — Reading Vector:** take the direction found via
    Representation Reading (e.g. LAT's honesty direction) and directly add/subtract it from
    the hidden state at generation time to increase/decrease the concept's expression
    (same mechanical idea as ActAdd/CAA in Q1, but the direction is extracted via PCA over
    a LAT scan rather than a raw mean-difference).
  - **Representation Control — Contrast Vector:** instead of a pre-computed static
    direction, run the *same input* through the model twice with two contrasting
    instruction prefixes in real time (e.g. "Be honest" vs "Be deceptive" prepended to the
    same query), and subtract the resulting hidden states at inference to get a per-input
    contrast vector — a dynamic, input-conditioned version of the steering vector.
  - **Representation Control — LoRRA (Low-Rank Representation Adaptation):** a
    finetuning-based control baseline — instead of directly editing activations at inference,
    LoRRA adapts a low-rank set of parameters so the model's own representations move toward
    the desired direction, without using additional preference data beyond the RepE-derived
    signal (contrasted with RLHF-style methods that need human preference labels).
- **Values:**
  - TruthfulQA: honesty control (unsupervised) improves accuracy by **+18.1 percentage
    points** over zero-shot baseline — quote: "By increasing model honesty in a fully
    unsupervised manner, the work achieves state-of-the-art results on TruthfulQA, improving
    over zero-shot accuracy by 18.1 percentage points and outperforming all prior methods."
  - LoRRA honesty improvement: **+6.6%** on **Llama-2-7B**, **+13.1%** on **Llama-2-13B**
    (exact metric/baseline for these percentages not fully disambiguated from snippet — likely
    also TruthfulQA-style honesty eval; flagged as gap).
  - LAT contrastive-pair set sizes: "generally between 5 and 128 such pairs" per stimulus
    design.
  - Concepts covered per the paper's abstract: honesty, harmlessness, power-seeking,
    "and more" (emotion, morality, utility, also mentioned in secondary sources but not
    directly quote-verified here).
- **Sources:**
  - Zou, A., Phan, L., Chen, S., Campbell, J., et al. (incl. Kolter, J.Z.; Hendrycks, D.)
    (2023), "Representation Engineering: A Top-Down Approach to AI Transparency",
    arXiv:2310.01405 | tier=Primary | confidence=H
  - GRATH: "Gradual Self-Truthifying for Large Language Models", arXiv:2401.12292 (secondary
    paper citing Zou et al. 2023's TruthfulQA +18.1pp and LoRRA +6.6%/+13.1% numbers as
    comparison baselines) | tier=Strong-secondary | confidence=M
  - alignmentforum.org, "An Introduction to Representation Engineering" (explainer,
    describes LAT scan procedure and PCA/K-means construction matching arXiv content) |
    tier=Explainer | confidence=M
  - arxiv.org/html/2502.17601v1, "Representation Engineering for Large-Language Models:
    Survey and Research Challenges" (secondary survey, used only for corroboration of
    baseline names Reading Vector / Contrast Vector / LoRRA) | tier=Strong-secondary |
    confidence=M
- **Gaps/caveats:** The +6.6%/+13.1% LoRRA numbers were sourced from a secondary paper
  (GRATH) citing Zou et al., not independently confirmed against the primary PDF's tables in
  this pass — flagged for confirmation if load-bearing. Did not verify the exact PCA
  procedure (e.g. whether it's PCA on paired *differences* vs PCA on pooled activations then
  labeled by concept sign) at derivation-level rigor from the snippets alone; the primary
  PDF (arxiv.org/pdf/2310.01405) should be consulted directly for the precise LAT math if a
  synthesizer needs the formal derivation. Full list of concepts studied (honesty,
  harmlessness, power-seeking "and more") not exhaustively enumerated here.

## Q3: The refusal direction (Arditi et al. 2024, arXiv:2406.11717) — single-direction finding, directional ablation to bypass refusal, adding it to induce refusal, and which models it was shown on

- **Finding:** Refusal — the behavior where a chat model complies with benign requests but
  declines harmful ones — is mediated by a **single, one-dimensional direction** in the
  residual stream, consistently found across **13 popular open-source chat models up to
  72B parameters** (spanning the Llama, Qwen, Gemma, and Yi model families, per secondary
  sources). **Erasing** (directionally ablating) this direction from every layer's residual
  stream causes the model to comply with harmful instructions it would otherwise refuse;
  **adding** the same direction (scaled) to the residual stream causes the model to refuse
  even harmless instructions. This is presented as a necessity+sufficiency result: the
  direction is both necessary for refusal (remove it → refusal stops) and sufficient to
  induce it (add it → refusal appears on benign inputs). The paper turns this into a
  practical **white-box jailbreak**: a rank-one weight edit (orthogonalizing the model's
  weight matrices against the refusal direction) that permanently disables refusal with
  "minimal effect on other capabilities."
- **Mechanism / derivation notes:**
  - **Direction extraction (difference-in-means):** collect a small set of contrastive
    instruction pairs — harmful instructions vs harmless instructions — run each through the
    model, and take the **difference in means** of the residual-stream activations
    (harmful-instruction mean activation minus harmless-instruction mean activation) at a
    given layer $L$ and token position, producing a direction $\mathbf{r}(L)$ (same
    difference-in-means construction as CAA in Q1, applied specifically to a
    harmful/harmless contrast rather than a behavior-trait contrast).
  - **Directional ablation (inference-time or weight-level projection):** given the direction
    $\mathbf{r}(L)$ (normalized), remove its component from the hidden state at every layer via
    the projection formula found in search snippet:

    $$
    \mathbf{h}'(L) = \mathbf{h}(L) - w_L \cdot \big(\mathbf{h}(L)\cdot \mathbf{r}(L)/\lVert \mathbf{r}(L)\rVert^2\big)\,\mathbf{r}(L)
    $$

    i.e. subtract the projection of the hidden state onto $\mathbf{r}(L)$, scaled by a per-layer
    ablation weight $w_L$. This zeroes out the component of the residual stream along the
    refusal direction at every layer/position, so the model can never represent "refuse" via
    that direction regardless of the input — this is why it works uniformly across all
    prompts rather than needing per-prompt intervention.
  - **Activation addition (inducing refusal):** the mirror operation — add
    $c\,\mathbf{r}(L)$ to the residual stream at layer $L$ (same mechanical form as ActAdd/CAA
    in Q1) — causes refusal to fire even on harmless instructions, demonstrating sufficiency.
  - **White-box jailbreak via weight orthogonalization:** rather than intervening at
    inference time (which requires runtime hooks), the authors permanently bake the ablation
    into the weights by orthogonalizing the model's weight matrices (e.g. the output
    projections that write into the residual stream) against $\mathbf{r}(L)$ — a rank-one
    edit to each relevant weight matrix so its output can never have a component along the
    refusal direction, producing a new checkpoint that never refuses without needing any
    runtime activation patching. This weight-orthogonalization technique underlies later
    "abliteration" community tooling that strips refusal from open-weight chat models.
  - The paper also mechanistically analyzes how adversarial suffixes (jailbreak prompts)
    achieve the same effect indirectly — by suppressing propagation of the refusal-mediating
    direction through the network, rather than by removing/ablating it directly.
- **Values:**
  - **13** open-source chat models tested, parameter range up to **72B**; model families
    named in secondary sources: **Llama, Qwen, Gemma, Yi** (and others) — exact enumerated
    list of all 13 not independently confirmed from the primary PDF in this pass.
  - Evaluation harness: **100 harmful instructions from JailbreakBench** used to measure
    refusal rate under no intervention vs. under directional ablation. Quote (secondary
    source paraphrase): "Under no intervention, chat models refuse nearly all harmful
    requests, yielding high refusal and safety scores. Ablating the refusal direction ...
    reduces refusal rates and elicits unsafe completions."
  - Downstream capability preservation, per a citing paper's own re-evaluation of the
    ORTHO/weight-orthogonalization jailbreak: **<1% average performance drop** on MMLU, ARC,
    and GSM8K after the rank-one weight edit (this specific number is from a secondary
    source describing the method's effect, not independently verified as appearing verbatim
    in Arditi et al.'s own tables — flagged as a gap).
  - **Exact refusal-rate percentages before/after ablation (e.g. "reduces refusal from X% to
    Y%") were NOT found** in the abstract or in search snippets after 5 searches + 1
    WebFetch of the arXiv abstract page; the abstract itself contains no quantitative
    numbers (confirmed by direct fetch). The precise per-model refusal-rate table lives in
    the paper body/figures, not the abstract — flagged as a gap requiring a follow-up PDF
    read if load-bearing for the survey.
- **Sources:**
  - Arditi, A., Obeso, O., Syed, A., Paleka, D., Panickssery, N., Gurnee, W., Nanda, N.
    (2024), "Refusal in Language Models Is Mediated by a Single Direction", arXiv:2406.11717,
    NeurIPS 2024 (proceedings.neurips.cc/paper_files/paper/2024/hash/f545448535dfde4f9786555403ab7c49-Abstract-Conference.html)
    | tier=Primary | confidence=H (abstract directly fetched and quoted verbatim; author list
    from search snippets, not independently re-verified against the PDF header in this pass)
  - github.com/andyrdt/refusal_direction — official code + results repo accompanying the
    paper (per search result title) | tier=Primary (code artifact) | confidence=M (not
    opened directly, only its existence/title confirmed via search)
  - learnmechinterp.com/topics/refusal-direction/ (explainer matching the difference-in-means
    + orthogonalization description) | tier=Explainer | confidence=M
  - Secondary paper citing the <1% MMLU/ARC/GSM8K capability-preservation number for the
    ORTHO weight-orthogonalization jailbreak (exact title not captured — snippet only; needs
    re-identification if load-bearing) | tier=Strong-secondary | confidence=L
- **Gaps/caveats:** The single biggest gap: **exact refusal-rate numbers (before/after
  ablation, per-model or averaged) were not recoverable from search snippets or the abstract**
  — only the qualitative claim ("reduces refusal rates and elicits unsafe completions") and
  the eval harness (100 JailbreakBench instructions) are confirmed. The full enumerated list
  of all 13 models (exact names/sizes) was not independently confirmed — only the family
  names (Llama/Qwen/Gemma/Yi) from secondary sources. The <1% capability-drop number is
  from an uncertain secondary source and its exact provenance (own paper vs a citing paper's
  reproduction) needs disambiguation. If any of these numbers become load-bearing for the
  survey's quantitative claims, a direct read of the arXiv PDF body (not just the abstract)
  is needed — this was not done here to stay within the search budget.

## Q4: SAE-feature steering vs steering vectors — clamping an SAE feature (Golden Gate Claude); does feature-level steering beat difference-in-means directions?

- **Finding:** Anthropic's "Scaling Monosemanticity" work (2024, transformer-circuits.pub)
  demonstrated **feature clamping** — forcibly setting a single SAE-discovered feature's
  activation to an artificially high (or low) value during the forward pass — as a steering
  mechanism, popularized by the public "Golden Gate Claude" demo (clamping the Golden Gate
  Bridge feature caused Claude 3 Sonnet to self-identify as the bridge in conversation, live
  on Anthropic's site for about a week). Whether SAE-feature steering **beats**
  difference-in-means / CAA-style steering vectors is contested and appears to depend on
  task and method refinement: naive SAE-feature steering does not straightforwardly beat
  simple difference-in-means baselines in some later systematic evaluations (SAEs "fail to
  outperform simple baselines" on steering and concept-detection tasks per one 2025 paper),
  while a refined SAE-**informed** method (SAE-TS, targeting SAE features to construct a
  better steering vector rather than clamping the SAE feature directly) reports better
  steering-vs-coherence trade-offs than both plain CAA and plain SAE feature steering.
- **Mechanism / derivation notes:**
  - **Feature clamping (Anthropic):** train a sparse autoencoder (SAE) on the residual
    stream at a middle layer of Claude 3 Sonnet (scaled up to ~34M features per search
    snippet) to decompose activations into a large overcomplete basis of (mostly)
    monosemantic features. To steer, identify the SAE latent corresponding to a target
    concept (e.g. "Golden Gate Bridge"), then during the forward pass **clamp** that
    latent's activation to a fixed (often much higher than natural) value — i.e. override
    the SAE's inferred coefficient for that feature — before reconstructing/injecting back
    into the residual stream, rather than adding a raw direction vector as in ActAdd/CAA.
    This is steering *in the SAE's decomposed feature basis* rather than in raw
    activation space.
  - **Difference-in-means / CAA baseline (contrast):** as in Q1 — a single dense direction
    from mean-activation differences over contrastive pairs, added directly to the residual
    stream. No decomposition step; the direction is whatever separates the two prompt/label
    sets on average, which may be a superposed mixture of multiple underlying features
    rather than a single monosemantic one.
  - **Why SAE-feature steering might underperform:** the SAE's reconstruction objective +
    sparsity constraint impose an information bottleneck — reconstructing from a sparse code
    loses some activation information relevant to precisely steering behavior, so a method
    built on the SAE's lossy reconstruction can be a noisier controller than a directly
    computed contrastive mean-difference vector that uses the full untouched activation
    space.
  - **SAE-TS (a middle path):** rather than directly clamping an SAE feature (or using it
    as the steering vector verbatim), SAE-TS uses the SAE to *measure* the causal effect of
    a candidate steering vector on downstream feature activations (turning the SAE into an
    evaluation/targeting tool), then optimizes a steering vector construction that targets a
    desired SAE feature outcome while explicitly trading off coherence — i.e. SAE feature
    space is used as the objective/metric, not as the vector source itself.
- **Values:**
  - SAE scale in Scaling Monosemanticity: up to **~34 million features** trained on Claude 3
    Sonnet's middle-layer residual stream (scaling laws used to guide hyperparameter
    selection, per search snippet — exact SAE width/model layer not independently confirmed
    against the primary transformer-circuits.pub page in this pass).
  - Golden Gate Claude: public demo live for about a week (~May 2024) — exact date range and
    quantitative "how much clamping" coefficient not captured from snippets.
  - Head-to-head verdicts (qualitative, no precise numeric deltas captured):
    - "Four baselines, including logistic regression and prompting, outperform the SAE" on
      concept detection (probing); "Prompting and finetuning both outperform SAE-based
      steering" on model steering — from "Use Sparse Autoencoders to Discover Unknown
      Concepts, Not to Act on Known Concepts" (2025, arXiv:2506.23845).
    - "SAE-TS balances steering effects with coherence better than CAA (contrastive
      activation addition) and SAE feature steering when evaluated on a range of tasks" —
      from "Improving Steering Vectors by Targeting Sparse Autoencoder Features"
      (arXiv:2411.02193).
    - A companion paper title found directly contradicts the above in the other direction:
      "Steering LLMs? Actually, Sparse Autoencoders can outperform simple baselines"
      (arXiv:2605.31183) — title only captured, content not read; flags that the field's
      verdict is actively contested / non-converged as of 2026.
  - No precise numeric steering-effect / coherence-score tables were extracted from any of
    these papers in this pass (all findings above are qualitative verdict statements from
    search snippets, not table values) — flagged as the main gap.
- **Sources:**
  - Anthropic Interpretability Team (2024), "Scaling Monosemanticity: Extracting
    Interpretable Features from Claude 3 Sonnet", transformer-circuits.pub/2024/scaling-monosemanticity/
    | tier=Primary | confidence=M (URL and headline claims confirmed via search snippet;
    page itself not directly fetched in this pass — recommend a direct fetch if the exact
    SAE width / clamping mechanics become load-bearing)
  - Chalnev, S., et al. (2024), "Improving Steering Vectors by Targeting Sparse Autoencoder
    Features" (SAE-TS), arXiv:2411.02193, code: github.com/slavachalnev/SAE-TS | tier=Primary
    | confidence=M
  - (2025), "Use Sparse Autoencoders to Discover Unknown Concepts, Not to Act on Known
    Concepts", arXiv:2506.23845 | tier=Primary | confidence=M (title/thesis and specific
    baseline-outperforms-SAE claims confirmed via search snippet, not independently
    re-verified against the PDF body in this pass)
  - "A Comparative Analysis of Sparse Autoencoder and Activation Difference in Language
    Model Steering", arXiv:2510.01246 (defines MeanActDiff vs SAE-basis steering methods,
    used for the mechanism contrast above) | tier=Primary | confidence=M
  - "Steering LLMs? Actually, Sparse Autoencoders can outperform simple baselines",
    arXiv:2605.31183 (title only, contradicts the above — flags contested state of the
    field) | tier=Primary | confidence=L (not read beyond title)
  - "SAEs Are Good for Steering – If You Select the Right Features", arXiv:2505.20063 (title
    suggests a reconciling middle position — feature *selection* quality matters more than
    SAE-vs-vector in the abstract — not read in depth) | tier=Primary | confidence=L
- **Gaps/caveats:** This is the least numerically-grounded of the four questions — the
  qualitative verdict ("does SAE-feature steering beat difference-in-means?") is **actively
  contested in the 2025-2026 literature**, with papers on both sides found in the same
  search pass (arXiv:2506.23845 says baselines beat SAEs; arXiv:2605.31183's title says the
  opposite; arXiv:2411.02193's SAE-TS claims a reconciling "best of both" method). No
  specific quantitative metric values (e.g. exact coherence scores, steering-success rates)
  were extracted for any of these comparisons — a synthesizer should treat this section as
  "there is a live head-to-head debate, here are the named combatant papers" rather than a
  settled numeric comparison, and budget a follow-up read of at least arXiv:2411.02193 and
  arXiv:2506.23845 in full if the survey needs a definitive numeric table. The exact
  mechanics of Anthropic's clamping op (e.g. what value features were clamped to, whether
  clamping is pre- or post-nonlinearity) were not independently confirmed against the
  primary transformer-circuits.pub page — recommend a direct fetch of that page if the
  derivation-level mechanism becomes load-bearing (this pass used its 2 allotted WebFetch
  calls on Q3's arXiv abstract instead, per the question priority order).
