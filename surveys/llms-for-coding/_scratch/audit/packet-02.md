# Citation-audit packet 02

1 source(s), 14 citation marker(s).

## Reference [10]

- **Source PDF:** `download/deepseek-coder-2024.pdf`
- **Reference entry:** D. Guo, Q. Zhu, D. Yang, Z. Xie, et al., "DeepSeek-Coder: When the Large Language Model Meets Programming — Th
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, pretraining-data, pretraining-objectives-and-scaling, the-code-model-pipeline
- **Markers:** 14

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-8), [[10]](references.
2. `language-models-from-first-principles.md:175` — DeepSeek-Coder reports both of its stages in tokens — pretraining (the cross-entropy objective of Equation [(2)](#eq-2)) on $2\times 10^{12}$ tokens versus instruction-tuning on $2\times 10^{9}$, a $1000\times$ gap, which is why almost all compute is spent in pretraining [[10]](references.
3. `language-models-from-first-principles.md:244` — md#ref-9), [[10]](references.
4. `historical-evolution.md:28` — 5-Turbo on code tasks [[10]](references.
5. `the-code-model-pipeline.md:27` — DeepSeek-Coder follows the same shape — 2T tokens across 87 languages, FIM, repository-level data organized by dependency order, then instruction tuning [[10]](references.
6. `the-code-model-pipeline.md:34` — md#ref-8), [[10]](references.
7. `the-code-model-pipeline.md:35` — 5-Coder-Instruct) and answer natural-language requests, explain code, and produce multi-file snippets [[10]](references.
8. `pretraining-data.md:33` — DeepSeek-Coder adds **repository-level** deduplication — dedup at the granularity of whole projects rather than individual files — to preserve cross-file structure [[10]](references.
9. `pretraining-data.md:43` — DeepSeek-Coder applies an n-gram filter: any code containing a 10-gram identical to test data is excluded, with exact matching for 3-to-10-gram overlaps, covering HumanEval, MBPP, GSM8K, and MATH [[10]](references.
10. `pretraining-objectives-and-scaling.md:11` — 5 FIM rate in PSM mode applied at the document level before packing, and ablates 0%, 50%, and 100% FIM rates plus a masked-span-prediction alternative, settling on 50% PSM as the best trade between infilling and left-to-right quality [[10]](references.
11. `pretraining-objectives-and-scaling.md:16` — DeepSeek-Coder uses 32,000 tokens [[10]](references.
12. `pretraining-objectives-and-scaling.md:21` — DeepSeek-Coder performs dependency-aware ordering: it parses import statements (`import` in Python, `using` in C#, `#include` in C) to build a file dependency graph, runs a topological sort, and concatenates files so that a file appears after its dependencies, prepending each with a path comment [[10]](references.
13. `pretraining-objectives-and-scaling.md:21` — md#ref-9), [[10]](references.
14. `pretraining-objectives-and-scaling.md:26` — DeepSeek-Coder uses 87% source code, 10% code-related English, and 3% other natural language [[10]](references.
