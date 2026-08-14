# Citation-audit packet 10

2 source(s), 14 citation marker(s).

## Reference [12]

- **Source PDF:** `download/phi1-2023.pdf`
- **Reference entry:** S. Gunasekar, Y. Zhang, J. Aneja, C. C. T. Mendes, et al., "Textbooks Are All You Need." 2023. arXiv:2306.1164
- **Cited in:** executive-summary, open-problems-and-roadmap, pretraining-data, pretraining-objectives-and-scaling
- **Markers:** 7

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:12` — Architecture is largely shared with general LLMs; what separates strong code models is corpus construction — licensing, deduplication, quality filtering, decontamination — and the phi-1 result that data quality can reshape the scaling curve [[12]](references.
2. `pretraining-data.md:38` — 5-generated textbooks and exercises [[12]](references.
3. `pretraining-data.md:38` — 5% on MBPP — "several orders of magnitude" smaller than competing models at comparable scores [[12]](references.
4. `pretraining-data.md:38` — A 350M-parameter sibling trained the same way still reaches 45% on HumanEval [[12]](references.
5. `pretraining-data.md:38` — The paper's thesis, stated plainly, is that "improving data quality can dramatically change the shape of the scaling laws" [[12]](references.
6. `pretraining-objectives-and-scaling.md:26` — Notably, none of these reports fit a code-specific scaling law with explicit exponents; the strongest scaling claim in the corpus is phi-1's qualitative one (Section 6), that data quality changes the shape of the curve rather than just shifting along it [[12]](references.
7. `open-problems-and-roadmap.md:26` — **Data**: high-quality and synthetic code data remains the dominant lever (Section 6), and the phi-1 result that data quality reshapes the scaling curve [[12]](references.

## Reference [19]

- **Source PDF:** `download/coderl-2022.pdf`
- **Reference entry:** H. Le, Y. Wang, A. D. Gotmare, S. Savarese, S. C. H. Hoi, "CodeRL: Mastering Code Generation through Pretraine
- **Cited in:** compute-cost-and-latency-tradeoffs, executive-summary, instruction-tuning-and-alignment, language-models-from-first-principles, reasoning-and-test-time-compute
- **Markers:** 7

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:14` — Because tests are an executable oracle, code supports reinforcement learning with verifiable rewards (RLVR), which underlies both execution-feedback RL and the reasoning-model breakthroughs [[19]](references.
2. `language-models-from-first-principles.md:175` — 5-Coder's DPO data size is unreported, while CodeRL's executable-reward RL runs over only $\approx 10^4$ APPS problems [[19]](references.
3. `instruction-tuning-and-alignment.md:38` — CodeRL casts program synthesis as actor-critic RL: the pretrained model is the policy, generated programs are actions, and the compiler/test environment returns a terminal reward [[19]](references.
4. `instruction-tuning-and-alignment.md:45` — A separate critic is trained to predict one of four outcomes — compile error, runtime error, failed test, passed test — and its token-level estimates turn the sparse terminal reward of Equation [(1)](#eq-1) into intermediate, per-token returns, optimized with a self-critical baseline that weights by the relative return against a baseline program [[19]](references.
5. `instruction-tuning-and-alignment.md:45` — CodeRL set new results on APPS and transferred zero-shot to MBPP [[19]](references.
6. `reasoning-and-test-time-compute.md:21` — md#ref-40), and CodeRL shows the same model rising from ~2% pass@1 to roughly 20% at pass@1000 on APPS purely by sampling more [[19]](references.
7. `compute-cost-and-latency-tradeoffs.md:16` — The lever is visible in the pass@k gap: CodeRL rises from ~2% pass@1 to ~20% pass@1000 on APPS purely by sampling more [[19]](references.
