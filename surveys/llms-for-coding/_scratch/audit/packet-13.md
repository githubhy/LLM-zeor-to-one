# Citation-audit packet 13

4 source(s), 14 citation marker(s).

## Reference [30]

- **Source PDF:** `download/repocoder-2023.pdf`
- **Reference entry:** F. Zhang, B. Chen, Y. Zhang, J. Keung, et al., "RepoCoder: Repository-Level Code Completion Through Iterative 
- **Cited in:** retrieval-and-repository-context
- **Markers:** 4

### Claims to verify (each is a sentence from the survey that cites this source)

1. `retrieval-and-repository-context.md:11` — The canonical method is RepoCoder, which pairs a similarity-based retriever with a code model in an *iterative* retrieve-generate loop [[30]](references.
2. `retrieval-and-repository-context.md:11` — The key insight is that the unfinished code is a *poor* proxy for what the completion will need, so RepoCoder augments the query with its own previously generated completion and retrieves again: at iteration $i$ the retrieval uses the draft $\hat{Y}^{i-1}$ from iteration $i-1$, progressively closing the gap between "what I have written" and "what I am about to write" [[30]](references.
3. `retrieval-and-repository-context.md:11` — Strikingly, a simple sparse retriever — bag-of-tokens snippets ranked by Jaccard similarity — performs on par with a dense neural retriever for this task [[30]](references.
4. `retrieval-and-repository-context.md:11` — On the RepoEval benchmark (line, API-invocation, and function-body completion across real repositories), RepoCoder improves an in-file baseline by over 10% exact match and over 8% edit similarity, and consistently beats single-shot retrieval-augmented generation [[30]](references.

## Reference [45]

- **Source PDF:** `download/fan-llm-se-survey-2023.pdf`
- **Reference entry:** A. Fan, B. Gokkaya, M. Harman, M. Lyubarskiy, et al., "Large Language Models for Software Engineering: Survey 
- **Cited in:** open-problems-and-roadmap, scope-and-the-code-modality
- **Markers:** 4

### Claims to verify (each is a sentence from the survey that cites this source)

1. `open-problems-and-roadmap.md:6` — md#ref-44), [[45]](references.
2. `open-problems-and-roadmap.md:21` — Trust — knowing when to rely on a model's output — is the human-facing version of the same problem [[45]](references.
3. `open-problems-and-roadmap.md:31` — frames the open problems from a software-engineering rather than a model-centric view: deployment and maintenance of LLM-based tools, integration into real development workflows, human-AI collaboration, and the trust and reliability practices that production software demands [[45]](references.

## Reference [14]

- **Source PDF:** `download/guo-unixcoder-2022.pdf`
- **Reference entry:** D. Guo, S. Lu, N. Duan, Y. Wang, et al., "UniXcoder: Unified Cross-Modal Pre-training for Code Representation.
- **Cited in:** historical-evolution, retrieval-and-repository-context, scope-and-the-code-modality
- **Markers:** 3

### Claims to verify (each is a sentence from the survey that cites this source)

1. `scope-and-the-code-modality.md:31` — md#ref-2) and UniXcoder [[14]](references.
2. `historical-evolution.md:11` — CodeBERT (and its cross-modal successor UniXcoder [[14]](references.
3. `retrieval-and-repository-context.md:16` — md#ref-2), and UniXcoder unifies encoder, decoder, and encoder-decoder behavior with cross-modal pretraining (using AST and code-comment signals) to produce representations for code search and retrieval [[14]](references.

## Reference [40]

- **Source PDF:** `download/alphacode-2022.pdf`
- **Reference entry:** Y. Li, D. Choi, J. Chung, N. Kushman, et al., "Competition-Level Code Generation with AlphaCode." *Science 202
- **Cited in:** compute-cost-and-latency-tradeoffs, open-problems-and-roadmap, reasoning-and-test-time-compute
- **Markers:** 3

### Claims to verify (each is a sentence from the survey that cites this source)

1. `reasoning-and-test-time-compute.md:21` — This is the mechanism behind the pass@1-to-pass@k gap — AlphaCode generates orders of magnitude more samples and then *filters* on example tests before submitting (Section 13) [[40]](references.
2. `compute-cost-and-latency-tradeoffs.md:16` — md#ref-19), and AlphaCode's competition results require sampling thousands of candidates before filtering [[40]](references.
3. `open-problems-and-roadmap.md:11` — 3% competition ranking [[40]](references.
