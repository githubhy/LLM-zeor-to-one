# Large Language Models for Code: From Codex to Agentic Software Engineering

<a id="p-large-language-models-for-code-from-codex-to-agentic-software-engineering-1"></a><!-- para:large-language-models-for-code-from-codex-to-agentic-software-engineering-1 --> A deep-research survey of the end-to-end stack for code LLMs — the code modality, a first-principles primer on language models (for readers new to deep learning), the historical arc, the training pipeline from data to alignment and reasoning, serving and retrieval, agents, evaluation, and the practical and societal layer. The organizing thesis is that code is a distinct modality because its correctness is *executable and verifiable*, and that this single property explains the field's trajectory from autocomplete to autonomous software-engineering agents. Every external claim and number traces to a primary source acquired and read for this survey.

## Contents

1. <a id="p-contents-1"></a><!-- para:contents-1 --> [Executive Summary](executive-summary.md)
2. [Scope and the Code Modality](scope-and-the-code-modality.md)
3. [Language Models from First Principles](language-models-from-first-principles.md)
4. [Historical Evolution](historical-evolution.md)
5. [The Code Model Pipeline](the-code-model-pipeline.md)
6. [Pretraining Data](pretraining-data.md)
7. [Pretraining Objectives and Scaling](pretraining-objectives-and-scaling.md)
8. [Instruction Tuning and Alignment](instruction-tuning-and-alignment.md)
9. [Reasoning and Test-Time Compute](reasoning-and-test-time-compute.md)
10. [Inference, Decoding, and Serving](inference-decoding-and-serving.md)
11. [Retrieval and Repository Context](retrieval-and-repository-context.md)
12. [Agentic Coding Systems](agentic-coding-systems.md)
13. [Evaluation and Benchmarks](evaluation-and-benchmarks.md)
14. [Compute, Cost, and Latency Tradeoffs](compute-cost-and-latency-tradeoffs.md)
15. [State of the Art and Practice](state-of-the-art-and-practice.md)
16. [Safety, Security, and Licensing](safety-security-and-licensing.md)
17. [Design Guidance](design-guidance.md)
18. [Open Problems and Roadmap](open-problems-and-roadmap.md)
19. [Appendix A — Query, Key, and Value from First Principles](appendix-a-qkv-first-principles.md)
20. [Appendix B — The Kernel-Regression Family](appendix-b-kernel-regression-family.md)
21. [Appendix C — A Transformer Top-to-Neuron: a Worked Toy Model](appendix-c-toy-transformer.md)
22. [Appendix D — GPT-2 Scale: the Toy, Grown Up](appendix-d-gpt2.md)
23. [Appendix E — The Modern Dense Block: a 7B Llama-Family Model](appendix-e-modern-dense.md)
24. [Appendix F — Scaling the Dense Block: 33B–70B](appendix-f-scaling.md)
25. [Appendix G — Frontier Mixture-of-Experts: DeepSeek-V3](appendix-g-moe.md)
26. [Appendix H — Synthesis: One Architecture, Nine Orders of Magnitude](appendix-h-synthesis.md)
27. [Appendix I — Mechanistic Interpretability: Reading the Trained Model](appendix-i-mechanistic-interpretability.md)
28. [Appendix J — Code-Specific Derivations](appendix-j-code-derivations.md)
29. [References](references.md)

## Notation

This table is the survey's **single declaration point** for symbols. One table in
`index.md` serves every body file (`.claude/rules/math-authoring.md` § "Symbol
Declaration"); `lint-math.py` check #12 resolves it from here for each of them.

**Conventions used throughout.** **Bold capital** = matrix ($\mathbf{W}$, $\mathbf{X}$);
**bold lowercase** = vector ($\mathbf{x}$, $\mathbf{h}$); *unbolded indexed* = a scalar
component or index ($x_t$, $W_{ij}$). $\top$ is transpose, $\lVert \cdot \rVert$ a norm,
$\Vert$ concatenation, and $\lvert S \rvert$ the size of a set. Losses are in **nats**
unless a line says bits; a loss quoted in bits is the same quantity divided by $\ln 2$.

### Model geometry and the forward pass

| Symbol | Meaning | Where introduced |
|---|---|---|
| $x_t$ | the token at position $t$; $x_{<t}$ is its prefix | [Language Models from First Principles](language-models-from-first-principles.md) |
| $T$ | context length, in **tokens** — the number of columns of $\mathbf{X}$ | [Language Models from First Principles](language-models-from-first-principles.md) |
| $d$, $d_{\text{model}}$ | residual-stream width | [Appendix A](appendix-a-qkv-first-principles.md) |
| $d_k$, $d_v$ | per-head key and value widths | [Appendix A](appendix-a-qkv-first-principles.md) |
| $h$ | number of query heads (**and** the head index) | [Language Models from First Principles](language-models-from-first-principles.md) |
| $L$ | layer count | [Language Models from First Principles](language-models-from-first-principles.md) |
| $\mathbf{E}$ | token-embedding matrix; $\hat{E}_k$ is its $k$-th Fourier component | [Appendix C](appendix-c-toy-transformer.md) |
| $\mathbf{W}^Q,\mathbf{W}^K,\mathbf{W}^V$ | the per-head query / key / value projections | [Appendix A](appendix-a-qkv-first-principles.md) |
| $W_{QK}$, $W_{OV}$ | the composed query–key and output–value circuits | [Appendix I](appendix-i-mechanistic-interpretability.md) |
| $\mathbf{h}_\ell$ | the residual stream at layer $\ell$ | [Appendix I](appendix-i-mechanistic-interpretability.md) |
| $\mathbf{b}_U$ | the unembedding bias — the slot absorbing the target unigram base-rate | [Appendix C](appendix-c-toy-transformer.md) |

### Training, scaling and objectives

| Symbol | Meaning | Where introduced |
|---|---|---|
| $L$ | the **scalar training loss** (negative log-likelihood) | [Language Models from First Principles](language-models-from-first-principles.md) |
| $N$ | parameter count — **declare non-embedding vs total at the point of use** | [Language Models from First Principles](language-models-from-first-principles.md) |
| $D$ | token budget — **declare unique corpus tokens vs tokens seen** | [Language Models from First Principles](language-models-from-first-principles.md) |
| $C$ | compute budget, $C = 6ND$ | [Language Models from First Principles](language-models-from-first-principles.md) |
| $E$ | the **irreducible loss** floor in the scaling law $L = E + A/N^\alpha + B/D^\beta$ | [Language Models from First Principles](language-models-from-first-principles.md) |
| $\alpha$, $\beta$ | the scaling-law exponents on $N$ and $D$ | [Language Models from First Principles](language-models-from-first-principles.md) |
| $\theta$ | model parameters | [Language Models from First Principles](language-models-from-first-principles.md) |
| $\pi_\theta$, $\pi_{\mathrm{ref}}$ | the policy under optimization and the frozen reference policy | [Appendix J](appendix-j-code-derivations.md) |
| $\beta$ | the **KL coefficient** in the DPO / RLHF objective | [Appendix J](appendix-j-code-derivations.md) |

### Evaluation, decoding and interpretability

| Symbol | Meaning | Where introduced |
|---|---|---|
| $\mathrm{pass}@k$ | the probability at least one of $k$ samples is correct | [Appendix J](appendix-j-code-derivations.md) |
| $p$ | per-problem success probability | [Appendix J](appendix-j-code-derivations.md) |
| $n$, $c$ | samples drawn per problem, and how many are correct | [Appendix J](appendix-j-code-derivations.md) |
| $k$ | the sample count in $\mathrm{pass}@k$, and the $k$ of top-$k$ decoding | [Appendix J](appendix-j-code-derivations.md) |
| $o_i$, $r_j$ | a sampled output and its reward | [Appendix J](appendix-j-code-derivations.md) |
| $f_i$ | activation of dictionary feature $i$ | [Appendix I](appendix-i-mechanistic-interpretability.md) |
| $W_{\mathrm{dec}}$ | the SAE decoder dictionary | [Appendix I](appendix-i-mechanistic-interpretability.md) |
| $L_0$ | the sparsity count (active features per token) | [Appendix I](appendix-i-mechanistic-interpretability.md) |
| $h$ | the kernel **bandwidth** of the smoothing family | [Appendix B](appendix-b-kernel-regression-family.md) |
| $r_k(\mathbf{x})$ | distance from $\mathbf{x}$ to its $k$-th nearest neighbour | [Appendix B](appendix-b-kernel-regression-family.md) |
| $p$ | the **modulus** of the modular-addition task $c=(a+b) \bmod p$ | [Appendix C](appendix-c-toy-transformer.md) |

### Deliberate reuses, and where each one is local

Everything reused below is reused **on purpose**, and each meaning is individually
standard in its own sub-field — which is exactly why a bare glossary would not catch
them. Anything reused and *not* named here is a defect, not a convention.

- **$L$** — the training loss everywhere except the architecture sections, where it is the
  layer count. Disambiguated by context: $L$ appears with $h$ and $d_{\text{model}}$ when
  it means depth, and inside $\nabla_\theta L$ when it means loss.
- **$E$** — the token-embedding matrix (bold $\mathbf{E}$, Appendix C) versus the scalar
  irreducible-loss floor $E$ in the scaling law. The bold/unbolded rule separates them, and
  that is the *only* thing that does.
- **$h$** — the attention head count throughout the model sections; the kernel bandwidth
  **only inside Appendix B**, which never discusses heads.
- **$\beta$** — a scaling-law exponent in the first-principles section; the KL coefficient
  **only inside Appendix J**'s preference-optimization derivations.
- **$p$** — a probability nearly everywhere; the group modulus **only inside Appendix C**'s
  modular-addition worked example, where it carries no probabilistic sense.
- **$k$** — the sample count of $\mathrm{pass}@k$ and the $k$ of top-$k$ decoding
  (Appendix J); a neighbour rank in Appendix B; a slice or Fourier index in Appendix C.
  Always an index or a count, never a dimension.
- **$V$** — the value projection $\mathbf{W}^V$ (bold, a matrix) versus the vocabulary
  whose size is written $\lvert V \rvert$ (unbolded, a set). Never the bare letter alone.

**Two-bases note.** $N$ and $D$ are the survey's live `[opt:MATH-BASIS]` cases: $N$ is
ambiguous between non-embedding and total parameters, and $D$ between unique corpus tokens
and tokens seen. Neither has one survey-wide answer — the scaling-law literature is split —
so each *use* declares its basis, and `viewer/tools/check-basis-declarations.py` gates it.
