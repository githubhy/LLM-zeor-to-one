# Citation-audit packet 01

1 source(s), 15 citation marker(s).

## Reference [11]

- **Source PDF:** `download/qwen25-coder-2024.pdf`
- **Reference entry:** B. Hui, J. Yang, Z. Cui, J. Yang, et al., "Qwen2.5-Coder Technical Report." 2024. arXiv:2409.12186. (local: do
- **Cited in:** executive-summary, historical-evolution, instruction-tuning-and-alignment, language-models-from-first-principles, pretraining-data, pretraining-objectives-and-scaling, retrieval-and-repository-context, the-code-model-pipeline
- **Markers:** 15

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-10), [[11]](references.
2. `language-models-from-first-principles.md:175` — 5\mathrm{T}\$ [[11]](references.
3. `language-models-from-first-principles.md:244` — md#ref-10), [[11]](references.
4. `historical-evolution.md:29` — 2T tokens), repository-level long-context pretraining (300B tokens, 128k window), then SFT + DPO alignment [[11]](references.
5. `the-code-model-pipeline.md:21` — 5-Coder, which continues pretraining on top of a general base model in three explicit stages [[11]](references.
6. `the-code-model-pipeline.md:34` — md#ref-10), [[11]](references.
7. `the-code-model-pipeline.md:35` — md#ref-10), [[11]](references.
8. `pretraining-data.md:43` — 5-Coder runs a dedicated decontamination pass over both pretraining and post-training data for the same key benchmarks [[11]](references.
9. `pretraining-objectives-and-scaling.md:11` — 5-Coder carries FIM into the repository-level stage with dedicated sentinel tokens [[11]](references.
10. `pretraining-objectives-and-scaling.md:16` — 5's 151,646-token vocabulary and adds code/FIM special tokens [[11]](references.
11. `pretraining-objectives-and-scaling.md:21` — md#ref-10), [[11]](references.
12. `pretraining-objectives-and-scaling.md:26` — 5-Coder ablates code:text:math ratios and finds that 70:20:10 outperforms higher-code mixtures — more code is not strictly better, because math and natural-language data improve code performance [[11]](references.
13. `instruction-tuning-and-alignment.md:31` — 5-Coder uses exactly DPO in its alignment stage [[11]](references.
14. `instruction-tuning-and-alignment.md:33` — 5-Coder's DPO preferences come from a code sandbox rather than human labels [[11]](references.
15. `retrieval-and-repository-context.md:21` — 5-Coder's 128k window via length extrapolation [[11]](references.
