# Mechanistic-Interpretability Coverage Gaps in the LLMs-for-Coding Survey

*Reference note · 2026-07-01 · gap analysis for `surveys/llms-for-coding` · execution tracked in [`todos/2026-07-01-mi-coverage-gaps.md`](../todos/2026-07-01-mi-coverage-gaps.md), built out per [`plans/2026-07-01-mi-clusters-survey-buildout.md`](../plans/2026-07-01-mi-clusters-survey-buildout.md)*

## TL;DR

- The survey's mechanistic-interpretability (MI) content is **circuit/weight-level and strong** — it explains, from first principles, *what a head computes*: QK/OV circuits, gauge freedom, induction, cross-layer composition, the direct path to the logits, and one fully-solved circuit (grokking). That is more circuit-level MI than most architecture surveys carry.
- What is thin or absent is the **feature/activation half** of modern MI (superposition → sparse autoencoders), the **causal-intervention methodology** for *finding* circuits in real models, the **code-specific** representational findings, and the **payoff + epistemics** (steering/editing, safety, limitations).
- Priority additions, in order: **(1)** superposition → SAE / features; **(2)** what *code* models represent (execution-state / world-model probing); **(3)** the intervention toolkit + one discovered real-model circuit.
- Buckets A–C extend the existing anatomy appendices in-charter; D–E lean toward a new **Appendix I (Mechanistic Interpretability)** plus forward-links from the safety / design chapters. Every fold is citation-gated: acquire sources first, cite from the acquired source, never from memory.

## 1. What the survey already covers (so we don't re-add it)

The anatomy appendices already do circuit-level MI well, and this note credits that so the gaps below are real:

- **QK / OV circuits** — the query–key collapse $M = W_Q^{\top}W_K$ and output–value collapse $W_{OV}=W_O W_V$ ([§A.2], [§A.3]).
- **Gauge freedom** — why the raw projection matrices are not observable, only the collapsed circuits ([§A.4]); an SVD reading of a trained head ([§A.8]).
- **Induction, by hand** — a hand-built induction head ([§A.9]), multi-head as a sum of low-rank circuits ([§A.10]), Q/K/V-composition across layers ([§A.18]).
- **Direct path to the logits** — how a head's write reaches the output distribution ([§A.21]) — direct logit attribution in all but name.
- **Induction-as-ICL, causally** — induction heads and in-context learning with an **ablation** table and a measurable $\Delta_{\text{ICL}}$ ([§A.22]).
- **A fully-solved circuit** — grokking on modular addition, derived end to end ([§C.8]), with a one-line superposition mention added at [§C.10].

The through-line: the survey teaches *what circuits are* and *what one head computes*. It does not yet teach *how features are represented across the stream*, *how circuits are discovered and validated in a real model*, or *what a code model specifically represents*.

## 2. Bucket A — the representational half of MI (features, not just circuits)

Almost the entire MI treatment is circuit/weight-level; the feature/activation side is a single line at [§C.10].

- **Superposition & the linear-representation hypothesis** — features as directions in the residual stream; the toy-model account of feature *capacity*, *sparsity*, *interference*, and the *phase transition* between representing and dropping a feature. The survey gestures at it ($d>V$ ⇒ no superposition, [§C.10]) but never develops the math.
- **Sparse autoencoders / dictionary learning** — the single biggest omission. SAEs (with the gated / top-$k$ / JumpReLU variants) are the current standard for pulling monosemantic features out of a polysemantic stream; the reconstruction-plus-sparsity objective, the $L_0$/$L_1$ tension, and the evaluation (loss recovered vs feature interpretability) are all absent.
- **Features ≠ neurons / polysemanticity** as a systematic treatment — the survey's "neuron as a matched filter" ([§C.2], [§A.6]) is the *clean* case; the messy, polysemantic case is the point of modern MI.

## 3. Bucket B — the causal-intervention methodology

[§A.22] ablates heads to prove necessity, but the survey never lays out *how circuits are localized and validated*:

- **Activation patching / causal tracing, path patching, attribution patching, causal scrubbing, distributed alignment search (DAS)** — the causal family that turns "this component looks important" into a measured, counterfactual claim.
- **Logit lens / tuned lens** as *named* tools — the underlying math is latent in [§A.21] (a component's write, read through the unembedding), but reading *intermediate* residual states through the unembedding, and the tuned-lens correction, are not framed.

## 4. Bucket C — a discovered real-model circuit, and the head zoo

- **No reverse-engineered circuit in a trained model.** The survey *hand-builds* induction ([§A.9]) and *derives* grokking ([§C.8]) but never *discovers* a circuit that a real model learned on its own — the "we didn't design it, we found it" case (IOI, greater-than, docstring).
- **A thin head taxonomy.** Induction and previous-token heads are covered; the empirical menagerie is not — duplicate-token, name-mover / negative-name-mover, copy-suppression, successor heads.

## 5. Bucket D — code-specific MI (the highest-value gap for *this* survey)

This is a *coding* survey, and the MI of code models is where it can be differentiated rather than generic:

- **What code models represent** — syntactic / AST structure, variable binding and scope, types, control flow, and especially **execution-state / "world-model" probing**: do the activations track program state as the model reads code? The emergent-world-representation line is the natural anchor.
- **Code-relevant circuits** — bracket / indentation matching, variable tracking, and copy-from-context. [§A.22] notes induction underpins in-context copying but never specializes it to code completion or repository-context copying, which is the survey's own subject.

## 6. Bucket E — the payoff and the epistemics (bridges to existing chapters)

- **MI → control** — activation steering, representation engineering, and weight editing (ROME / MEMIT). The FFN-as-key-value-memory idea is latent at [§A.6] / [§C.2]; the *editing* payoff and the tie to the design-guidance chapter are not drawn.
- **MI → safety** — circuit-level auditing, backdoor / sleeper-agent detection, deception probes: the natural link from these appendices to the safety chapter, currently unlinked.
- **Scalable / automated interpretability** — neuron and feature auto-labeling, automated circuit discovery, attribution graphs / circuit tracing.
- **Limits & faithfulness** — interpretability illusions, ablation ≠ necessity, "attention weights are not explanations", and how MI claims are evaluated. The survey presents circuits confidently; the field's own caveats do not appear.

## 7. Priorities, placement, and the charter line

**If we add three things, in order:** (1) a **superposition → SAE / features** treatment — the representational half the survey is missing, already half-opened at [§C.10]; (2) a **code-representation & code-circuit** treatment — the domain-specific payoff; (3) the **intervention toolkit + one discovered real-model circuit** — so the survey teaches not just what circuits *are* but how they are *found and validated*.

**Placement.** Buckets A–C extend the existing anatomy appendices in-charter (they continue the §A / §C story). Buckets D–E lean toward new topics. The clean home for the net-new material is a dedicated **Appendix I — Mechanistic Interpretability** (I.1–I.9), with minimal forward-links added to §C.10 (→ superposition), §A.22 (→ intervention/head-zoo), and the safety chapter (→ auditing). This avoids mid-appendix insertion (which would cascade section numbers) — every new section is appended.

**Charter caveat.** The anatomy appendices are an *architecture* teardown that *uses* MI as a lens; they are not an interpretability survey. The additions above are scoped to keep that character: first-principles, math-rich, and tied back to the concrete toy / GPT-2 / Llama models the appendices already build.

## 8. Sources to acquire (pointers, not yet verified in-source)

Per the citation-integrity rule, none of the below is cited until its full text is acquired into `download/` and the specific claim is read there. This list is the acquisition target for the buildout plan, grouped by cluster; arXiv IDs are candidates to fetch and verify.

- **Superposition / SAE (A):** toy-models-of-superposition and the monosemanticity line (Anthropic transformer-circuits, web); SAEs-find-interpretable-features; top-$k$ SAEs; gated SAEs; JumpReLU SAEs.
- **Intervention (B):** locating-and-editing (causal tracing); interpretability-in-the-wild / IOI (path patching); automated circuit discovery; causal scrubbing (web); logit lens (web) and the tuned lens; distributed alignment search.
- **Circuits / head zoo (C):** in-context-learning-and-induction-heads; the greater-than circuit; the docstring circuit; successor heads; copy-suppression heads.
- **Code-specific (D):** emergent-world-representations (Othello) and its linear-probe follow-up; evidence-of-meaning in models trained on programs; probing pretrained models of source code; structural analysis of code language models.
- **Payoff / epistemics (E):** activation addition / steering; representation engineering; mass-editing memory (MEMIT); neuron-explanation automation (web); circuit tracing / attribution graphs (web); the interpretability-illusion and attention-is-not-explanation critiques.

The gaps in §2–§6 stand on the structure of the existing appendices; the *citations* that will support the buildout stand on the acquired sources above, verified at authoring time.
