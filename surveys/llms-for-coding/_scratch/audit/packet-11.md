# Citation-audit packet 11

3 source(s), 16 citation marker(s).

## Reference [6]

- **Source PDF:** `download/code-llama-2023.pdf`
- **Reference entry:** B. Rozière, J. Gehring, F. Gloeckle, S. Sootla, et al., "Code Llama: Open Foundation Models for Code." 2023. a
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, pretraining-objectives-and-scaling, retrieval-and-repository-context, scope-and-the-code-modality
- **Markers:** 6

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-4), [[6]](references.
2. `scope-and-the-code-modality.md:26` — md#ref-5), [[6]](references.
3. `language-models-from-first-principles.md:175` — md#ref-9) pretraining; Code Llama $\approx 5\mathrm{B}$ instruction tokens [[6]](references.
4. `historical-evolution.md:26` — 0% reported in the same table [[6]](references.
5. `pretraining-objectives-and-scaling.md:11` — 9, half PSM and half SPM, and notably suppresses the leading space that its SentencePiece tokenizer would otherwise insert, to limit the train/inference distribution shift between ordinary generation and infilling [[6]](references.
6. `retrieval-and-repository-context.md:21` — md#ref-11), Code Llama's 100k extension [[6]](references.

## Reference [2]

- **Source PDF:** `download/codebert-2020.pdf`
- **Reference entry:** Z. Feng, D. Guo, D. Tang, N. Duan, et al., "CodeBERT: A Pre-Trained Model for Programming and Natural Language
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, retrieval-and-repository-context, scope-and-the-code-modality
- **Markers:** 5

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — Encoder models like CodeBERT [[2]](references.
2. `scope-and-the-code-modality.md:31` — - **Code understanding and retrieval** — non-generative tasks such as code search and summarization, the province of encoder models like CodeBERT [[2]](references.
3. `language-models-from-first-principles.md:123` — This yields rich *representations* for understanding tasks (classification, search) but cannot generate left to right; CodeBERT [[2]](references.
4. `historical-evolution.md:11` — CodeBERT (2020) is an encoder-only model — "exactly the same model architecture as RoBERTa-base," 125M parameters — trained bimodally on paired natural language and programming language [[2]](references.
5. `retrieval-and-repository-context.md:16` — The representation-model line of Section 4 supplies these: CodeBERT produces bimodal code/text embeddings for search [[2]](references.

## Reference [43]

- **Source PDF:** `download/deepseek-coder-v2-2024.pdf`
- **Reference entry:** Q. Zhu, D. Guo, Z. Shao, D. Yang, et al., "DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in 
- **Cited in:** compute-cost-and-latency-tradeoffs, executive-summary, historical-evolution, state-of-the-art-and-practice
- **Markers:** 5

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-11) — that matched and then closed the gap to closed models, culminating in open mixture-of-experts systems comparable to GPT-4-class models [[43]](references.
2. `historical-evolution.md:31` — DeepSeek-Coder-V2 (2024), a 236B-total / 21B-active mixture-of-experts model over 338 languages, was explicitly framed as "breaking the barrier of closed-source models," reaching GPT-4-Turbo-comparable code performance with open weights [[43]](references.
3. `compute-cost-and-latency-tradeoffs.md:11` — 4B active parameters match the dense DeepSeek-Coder-33B on Python completion, an order-of-magnitude reduction in active compute at comparable capability [[43]](references.
4. `compute-cost-and-latency-tradeoffs.md:11` — Together these explain how open-weight models reached frontier-comparable code performance — DeepSeek-Coder-V2 is explicitly framed as closing the gap to closed models [[43]](references.
5. `state-of-the-art-and-practice.md:11` — 7% on SWE-bench in mid-2024 [[43]](references.
