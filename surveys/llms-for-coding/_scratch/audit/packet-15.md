# Citation-audit packet 15

10 source(s), 16 citation marker(s).

## Reference [32]

- **Source PDF:** `download/swe-agent-2024.pdf`
- **Reference entry:** J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, et al., "SWE-agent: Agent-Computer Interfaces Enable Automated S
- **Cited in:** executive-summary, historical-evolution
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:15` — A purpose-built agent-computer interface, not just a bigger model, drives much of agentic performance [[32]](references.
2. `historical-evolution.md:38` — SWE-agent (2024) then showed that a purpose-built agent-computer interface — not just a bigger model — drives most of the gain (Section 12) [[32]](references.

## Reference [38]

- **Source PDF:** `download/swe-bench-2023.pdf`
- **Reference entry:** C. E. Jimenez, J. Yang, A. Wettig, S. Yao, et al., "SWE-bench: Can Language Models Resolve Real-World GitHub I
- **Cited in:** historical-evolution, open-problems-and-roadmap
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `open-problems-and-roadmap.md:11` — 96% of real issues [[38]](references.

## Reference [39]

- **Source PDF:** `download/livecodebench-2024.pdf`
- **Reference entry:** N. Jain, K. Han, A. Gu, W.-D. Li, et al., "LiveCodeBench: Holistic and Contamination Free Evaluation of Large 
- **Cited in:** open-problems-and-roadmap, state-of-the-art-and-practice
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `state-of-the-art-and-practice.md:11` — On the contamination-resistant LiveCodeBench (Section 13), which time-windows fresh problems, the frontier band is reported near 90% [[39]](references.
2. `open-problems-and-roadmap.md:16` — The roadmap item is durable, contamination-resistant, adequately-tested, repository-realistic evaluation that tracks capability faster than it saturates — LiveCodeBench's time-windowing (Section 13) is a template, not a final answer [[39]](references.

## Reference [41]

- **Source PDF:** `download/asleep-at-keyboard-2021.pdf`
- **Reference entry:** H. Pearce, B. Ahmad, B. Tan, B. Dolan-Gavitt, R. Karri, "Asleep at the Keyboard? Assessing the Security of Git
- **Cited in:** safety-security-and-licensing
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `safety-security-and-licensing.md:11` — 33% of the top-ranked suggestions specifically [[41]](references.
2. `safety-security-and-licensing.md:11` — The top suggestion matters most because users tend to accept the "best" completion, so a 40% vulnerability rate in first suggestions is a direct security concern, not an edge case [[41]](references.

## Reference [42]

- **Source PDF:** `download/he-vechev-sven-secure-code-2023.pdf`
- **Reference entry:** J. He, M. Vechev, "Large Language Models for Code: Security Hardening and Adversarial Testing." *ACM CCS 2023.
- **Cited in:** safety-security-and-licensing
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `safety-security-and-licensing.md:11` — SVEN formulates "controlled code generation," using lightweight property-specific prefixes (continuous vectors, with the model's weights frozen) to steer generation toward secure or, adversarially, insecure code across 9 CWEs [[42]](references.
2. `safety-security-and-licensing.md:11` — 8%, demonstrating that the same lever cuts both ways [[42]](references.

## Reference [54]

- **Source PDF:** `download/vaswani-attention-is-all-you-need-2017.pdf`
- **Reference entry:** A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, et al., "Attention Is All You Need." *NeurIPS 2017.* arXiv:17
- **Cited in:** language-models-from-first-principles
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `language-models-from-first-principles.md:89` — Attention compares each query to every key by a dot product, normalizes the comparisons into weights with a softmax, and returns the weighted average of the values [[54]](references.
2. `language-models-from-first-principles.md:137` — The original Transformer adds fixed **sinusoidal** features of varying frequency — literally a Fourier-style positional basis [[54]](references.

## Reference [13]

- **Source PDF:** `download/semdedup-2023.pdf`
- **Reference entry:** A. Abbas, K. Tirumala, D. Simig, S. Ganguli, A. S. Morcos, "SemDeDup: Data-Efficient Learning at Web-Scale Thr
- **Cited in:** pretraining-data
- **Markers:** 1

### Claims to verify (each is a sentence from the survey that cites this source)

1. `pretraining-data.md:33` — These corpora use exact and near-duplicate (MinHash/LSH) deduplication; *semantic* deduplication by embedding similarity, as in SemDeDup [[13]](references.

## Reference [15]

- **Source PDF:** `download/self-instruct-2022.pdf`
- **Reference entry:** Y. Wang, Y. Kordi, S. Mishra, A. Liu, et al., "Self-Instruct: Aligning Language Models with Self-Generated Ins
- **Cited in:** instruction-tuning-and-alignment
- **Markers:** 1

### Claims to verify (each is a sentence from the survey that cites this source)

1. `instruction-tuning-and-alignment.md:21` — Self-Instruct established the template: bootstrap a large instruction set from a small seed pool by prompting a strong model, then fine-tune on the result [[15]](references.

## Reference [18]

- **Source PDF:** `download/dpo-rafailov-2023.pdf`
- **Reference entry:** R. Rafailov, A. Sharma, E. Mitchell, S. Ermon, et al., "Direct Preference Optimization: Your Language Model is
- **Cited in:** instruction-tuning-and-alignment
- **Markers:** 1

### Claims to verify (each is a sentence from the survey that cites this source)

1. `instruction-tuning-and-alignment.md:31` — Direct Preference Optimization (DPO) simplifies this substantially — it shows the RLHF objective can be optimized with "only a simple classification loss," a binary-cross-entropy objective that fits an implicit reward model whose optimal policy is available in closed form, eliminating the separate reward model and the unstable online RL loop [[18]](references.

## Reference [21]

- **Source PDF:** `download/chain-of-thought-2022.pdf`
- **Reference entry:** J. Wei, X. Wang, D. Schuurmans, M. Bosma, et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Langu
- **Cited in:** reasoning-and-test-time-compute
- **Markers:** 1

### Claims to verify (each is a sentence from the survey that cites this source)

1. `reasoning-and-test-time-compute.md:21` — Chain-of-thought prompting elicits intermediate reasoning steps that improve performance on tasks requiring multi-step logic [[21]](references.
