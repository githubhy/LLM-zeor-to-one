# Citation-audit packet 06

1 source(s), 10 citation marker(s).

## Reference [8]

- **Source PDF:** `download/starcoder-2023.pdf`
- **Reference entry:** R. Li, L. Ben Allal, Y. Zi, N. Muennighoff, et al., "StarCoder: May the Source Be with You!" *TMLR 2023.* arXi
- **Cited in:** compute-cost-and-latency-tradeoffs, executive-summary, historical-evolution, inference-decoding-and-serving, pretraining-data, pretraining-objectives-and-scaling, safety-security-and-licensing, the-code-model-pipeline
- **Markers:** 10

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-6), [[8]](references.
2. `historical-evolution.md:27` — md#ref-7), [[8]](references.
3. `the-code-model-pipeline.md:27` — md#ref-10) — and StarCoder shows the serving-oriented variant: 1T tokens, an 8k window, FIM, and multi-query attention chosen specifically for fast large-batch inference [[8]](references.
4. `the-code-model-pipeline.md:34` — All three reports above tie FIM capability specifically to the completion deployment [[8]](references.
5. `pretraining-data.md:43` — StarCoder removes files containing docstrings or solutions from HumanEval and MBPP, docstrings from APPS, questions from GSM8K, or prompts from DS-1000 [[8]](references.
6. `pretraining-objectives-and-scaling.md:11` — 5, mixing PSM and an SPM variant equally [[8]](references.
7. `pretraining-objectives-and-scaling.md:21` — 5-Coder extends to 128k via length extrapolation (YARN) in its repository stage [[8]](references.
8. `inference-decoding-and-serving.md:23` — **Autocomplete** is latency-bound: it favors smaller models, FIM, multi-query or grouped attention for fast batched inference (StarCoder chose multi-query attention precisely for this [[8]](references.
9. `compute-cost-and-latency-tradeoffs.md:21` — **Inline autocomplete** is latency-bound: a completion must appear in well under a second, which favors small models, fill-in-the-middle, multi-query attention (StarCoder's explicit choice for fast batched inference [[8]](references.
10. `safety-security-and-licensing.md:21` — md#ref-7), [[8]](references.
