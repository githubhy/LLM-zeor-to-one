<!-- sec:4 -->
## <a id="sec-4"></a>4 Method inventory I — observational methods

<a id="p-4-method-inventory-i-observational-methods-1"></a><!-- para:4-method-inventory-i-observational-methods-1 --> Observational methods read a model's state or weights and produce *correlational* evidence. Per § <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1), their outputs are hypotheses to be causally confirmed, not conclusions. Each card follows the uniform template (idea → placement/lineage → mechanism → limits → complexity → epistemic tag); depth follows the `index.md` tier in brackets.

<!-- sec:4.1 -->
### <a id="sec-4.1"></a>4.1 Linear probing [load-bearing]

<a id="p-41-linear-probing-load-bearing-1"></a><!-- para:41-linear-probing-load-bearing-1 --> **One-line idea.** Train a simple classifier on frozen activations to test whether a concept is linearly decodable from a layer.

<a id="p-41-linear-probing-load-bearing-2"></a><!-- para:41-linear-probing-load-bearing-2 --> **Placement & lineage.** The oldest interpretability tool for deep nets; introduced as "diagnostic classifiers" / linear classifier probes by Alain & Bengio <!-- cite:24 --> [[24]](references.md#ref-24) to chart how linearly-separable task information becomes with depth. Its modern role in MI is as a *representation* observer (Axis 2) whose central weakness — decodability ≠ use — motivated the entire causal-methods family.

<a id="p-41-linear-probing-load-bearing-3"></a><!-- para:41-linear-probing-load-bearing-3 --> **Mechanism.** For layer $\ell$, fit $g(\mathbf{x}) = \sigma(\mathbf{w}^\top \mathbf{x}_\ell + b)$ on a labeled set to predict a property $y$; the probe's held-out accuracy is read as evidence the property is (linearly) present at $\ell$. The **selectivity** control of Hewitt & Liang <!-- cite:25 --> [[25]](references.md#ref-25) is essential rigor: a high-capacity probe attains high accuracy even on a *control task* with randomly-permuted labels, so one reports selectivity = (real-task accuracy) $-$ (control-task accuracy), and prefers the lowest-capacity probe that still succeeds, because a linear probe has far higher selectivity than an MLP probe that can memorize an arbitrary map.

<a id="p-41-linear-probing-load-bearing-4"></a><!-- para:41-linear-probing-load-bearing-4 --> **The Othello-GPT lesson.** Probing's most instructive episode: Li et al. <!-- cite:27 --> [[27]](references.md#ref-27) trained a GPT on legal Othello moves and found a *non-linear* (MLP) probe could reconstruct the board while a linear probe could not — apparent evidence for non-linear world models. Nanda et al. <!-- cite:28 --> [[28]](references.md#ref-28) showed the linear failure was an artifact of the *featurization*: re-labeling each square as "mine vs. theirs" (relative to the player to move) rather than "black vs. white" makes a **linear** probe succeed, and the discovered directions support causal edits that change the model's move predictions. The lesson is double: probing can mislead about *linearity* when the frame is wrong, and a probe becomes a mechanistic claim only when paired with an intervention.

<a id="p-41-linear-probing-load-bearing-5"></a><!-- para:41-linear-probing-load-bearing-5 --> **Limits & epistemic tag.** Correlational by construction; sensitive to probe capacity and to the label frame (Othello); establishes presence, never use <!-- cite:26 --> [[26]](references.md#ref-26). *Epistemic status: mature, well-understood, correctly scoped as hypothesis generation.*

<!-- sec:4.2 -->
### <a id="sec-4.2"></a>4.2 Logit lens and tuned lens [load-bearing]

<a id="p-42-logit-lens-and-tuned-lens-load-bearing-1"></a><!-- para:42-logit-lens-and-tuned-lens-load-bearing-1 --> **One-line idea.** Decode an intermediate residual state through the model's own unembedding to see "what it is predicting so far," and fix the lens per layer to remove basis drift.

<a id="p-42-logit-lens-and-tuned-lens-load-bearing-2"></a><!-- para:42-logit-lens-and-tuned-lens-load-bearing-2 --> **Placement & lineage.** A representation observer that exploits the residual-stream picture directly (§ <!-- secxref:2.1 -->[§2.1](fundamentals.md#sec-2.1)): if every layer writes into the same space the unembedding reads, then applying the unembedding early should be meaningful. The **logit lens** (nostalgebraist <!-- cite:22 --> [[22]](references.md#ref-22)) is the raw version; the **tuned lens** (Belrose et al. <!-- cite:23 --> [[23]](references.md#ref-23)) is the calibrated successor.

<a id="p-42-logit-lens-and-tuned-lens-load-bearing-3"></a><!-- para:42-logit-lens-and-tuned-lens-load-bearing-3 --> **Mechanism.** The logit lens computes $\operatorname{softmax}(W_U\,\mathrm{LN}_{\text{final}}(\mathbf{x}_\ell))$ at each layer $\ell$, treating the intermediate state as if final. This works on GPT-2 (predictions sharpen monotonically with depth) but is *biased* on GPT-Neo, OPT, BLOOM, whose layers use a rotated/shifted basis the final unembedding does not undo. The tuned lens learns a per-layer affine "translator" $(A_\ell, \mathbf{b}_\ell)$ minimizing $\mathrm{KL}$ between the translated decode $\operatorname{softmax}(W_U\,\mathrm{LN}(A_\ell \mathbf{x}_\ell + \mathbf{b}_\ell))$ and the model's *own final* distribution — a distillation-style calibration, not a task probe. It is a linear probe (§ <!-- secref:4.1 -->[§4.1](#sec-4.1)) whose target is the model's final belief, so it inherits the same "decodable ≠ used" caveat.

<a id="p-42-logit-lens-and-tuned-lens-load-bearing-4"></a><!-- para:42-logit-lens-and-tuned-lens-load-bearing-4 --> **Findings & values.** The tuned lens produces uniformly lower, lower-variance per-layer perplexity than the logit lens on Pythia and GPT-NeoX-20B, and its trajectory of latent predictions can flag anomalous inputs <!-- cite:23 --> [[23]](references.md#ref-23). *(A reported figure — a logit-lens KL bias of "≈4–5 bits" on GPT-Neo-2.7B — is search-derived in the evidence ledger and is verified against <!-- cite:23 --> [[23]](references.md#ref-23) in the citation-audit pass before it is treated as load-bearing.)*

<a id="p-42-logit-lens-and-tuned-lens-load-bearing-5"></a><!-- para:42-logit-lens-and-tuned-lens-load-bearing-5 --> **Limits & epistemic tag.** A lens shows what is *linearly recoverable* by layer $\ell$, not what the model commits to there. *Epistemic status: mature; tuned lens is the recommended default.*

<!-- sec:4.3 -->
### <a id="sec-4.3"></a>4.3 Attention-pattern and head analysis [load-bearing]

<a id="p-43-attention-pattern-and-head-analysis-load-bearing-1"></a><!-- para:43-attention-pattern-and-head-analysis-load-bearing-1 --> **One-line idea.** Read attention maps and per-head OV/QK behavior to name a head's function (previous-token, induction, name-mover, copy-suppression).

<a id="p-43-attention-pattern-and-head-analysis-load-bearing-2"></a><!-- para:43-attention-pattern-and-head-analysis-load-bearing-2 --> **Placement & lineage.** A circuit-level observer built directly on the QK/OV factorization (§ <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2)). It is how most named head classes were first spotted — previous-token and induction heads <!-- cite:80 --> [[80]](references.md#ref-80), the IOI head zoo <!-- cite:35 --> [[35]](references.md#ref-35), copy-suppression heads <!-- cite:61 --> [[61]](references.md#ref-61).

<a id="p-43-attention-pattern-and-head-analysis-load-bearing-3"></a><!-- para:43-attention-pattern-and-head-analysis-load-bearing-3 --> **Mechanism.** Inspect $A^h_{ij}$ for structure (a "shift-by-one" diagonal = previous-token head; attending to the token after a prior copy of the current token = induction head), and read the OV copying table $W_U W_{OV}^h W_E$ to see which tokens a head promotes when attended.

<a id="p-43-attention-pattern-and-head-analysis-load-bearing-4"></a><!-- para:43-attention-pattern-and-head-analysis-load-bearing-4 --> **The load-bearing caveat.** Attention weights are *not*, by themselves, an explanation. Jain & Wallace <!-- cite:29 --> [[29]](references.md#ref-29) showed one can construct alternative attention distributions that leave the output unchanged (non-identifiability), and that attention correlates weakly with gradient importance; Wiegreffe & Pinter <!-- cite:30 --> [[30]](references.md#ref-30) rebutted that *trained* attention is more constrained than post-hoc adversarial search suggests. The MI resolution is not to settle the 2019 debate but to *require causal confirmation*: a head's named role is a hypothesis until patching or ablation (§ <!-- secxref:5 -->[§5](method-inventory-causal.md#sec-5)) confirms it. (Both papers studied single-layer RNN/LSTM attention; extending their conclusions to deep multi-head transformer attention is itself an open extrapolation.)

<a id="p-43-attention-pattern-and-head-analysis-load-bearing-5"></a><!-- para:43-attention-pattern-and-head-analysis-load-bearing-5 --> **Epistemic tag.** *Indispensable for hypothesis generation, invalid as standalone causal evidence.*

<!-- sec:4.4 -->
### <a id="sec-4.4"></a>4.4 Weight/SVD analysis and feature visualization [catalog-only]

<a id="p-44-weightsvd-analysis-and-feature-visualization-catalog-only-1"></a><!-- para:44-weightsvd-analysis-and-feature-visualization-catalog-only-1 --> **One-line idea.** Analyze weight matrices directly (singular structure of $W_{QK}$, $W_{OV}$), or synthesize inputs that maximally activate a unit.

<a id="p-44-weightsvd-analysis-and-feature-visualization-catalog-only-2"></a><!-- para:44-weightsvd-analysis-and-feature-visualization-catalog-only-2 --> **Placement & lineage.** Direct-weight analysis is the "0-layer" limit of circuit analysis (Appendix <!-- secxref:A -->[§A](appendix-a-transformer-circuits-math.md#sec-A)); **feature visualization** is the vision-model heritage of the whole field — optimizing an input image to maximize a channel, the technique behind InceptionV1 curve detectors <!-- cite:2 --> [[2]](references.md#ref-2).

<a id="p-44-weightsvd-analysis-and-feature-visualization-catalog-only-3"></a><!-- para:44-weightsvd-analysis-and-feature-visualization-catalog-only-3 --> **Stated result + applicability.** The eigen/singular structure of a head's OV circuit reveals whether it copies (positive eigenvalues on a token-identity subspace) or suppresses; direct-weight reading is cheap and input-independent but blind to what actually activates in distribution.

- <a id="p-44-weightsvd-analysis-and-feature-visualization-catalog-only-4"></a><!-- para:44-weightsvd-analysis-and-feature-visualization-catalog-only-4 --> Full derivation: `n/a (catalog-only; the OV/QK linear algebra is derived once in Appendix <!-- secxref:A.2 -->[§A.2](appendix-a-transformer-circuits-math.md#sec-A.2))`.
- Worked example: `n/a (catalog-only)`.
- Feature visualization worked example: `n/a (image-space optimization is a vision-model technique; LM features are read via dictionary learning in § <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6) instead)`.

<a id="p-44-weightsvd-analysis-and-feature-visualization-catalog-only-5"></a><!-- para:44-weightsvd-analysis-and-feature-visualization-catalog-only-5 --> **Epistemic tag.** *Foundational for vision circuits; a supporting tool, not a primary method, for LM interpretability.*
