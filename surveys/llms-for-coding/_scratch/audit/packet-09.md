# Citation-audit packet 09

2 source(s), 15 citation marker(s).

## Reference [25]

- **Source PDF:** `download/deepseek-r1-2025.pdf`
- **Reference entry:** DeepSeek-AI, "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning." 2025. arXiv
- **Cited in:** executive-summary, historical-evolution, reasoning-and-test-time-compute, state-of-the-art-and-practice
- **Markers:** 8

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:14` — md#ref-20), [[25]](references.
2. `historical-evolution.md:36` — 3rd percentile on Codeforces (Section 9) [[25]](references.
3. `reasoning-and-test-time-compute.md:31` — DeepSeek-R1 is the clearest open account [[25]](references.
4. `reasoning-and-test-time-compute.md:31` — Its R1-Zero variant applies RL directly to a base model with **no supervised fine-tuning**, using Group Relative Policy Optimization and a purely **rule-based reward** with two parts — an accuracy reward (is the final answer correct, checked by tests for code or by ground truth for math) and a format reward (keep reasoning inside delimiters) — deliberately avoiding a neural reward model to prevent reward hacking [[25]](references.
5. `reasoning-and-test-time-compute.md:31` — 7% with self-consistency [[25]](references.
6. `reasoning-and-test-time-compute.md:31` — 2% on SWE-bench Verified [[25]](references.
7. `state-of-the-art-and-practice.md:11` — 2% on SWE-bench Verified in early 2025 [[25]](references.

## Reference [3]

- **Source PDF:** `download/codegen-2022.pdf`
- **Reference entry:** E. Nijkamp, B. Pang, H. Hayashi, L. Tu, et al., "CodeGen: An Open Large Language Model for Code with Multi-Tur
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, scope-and-the-code-modality
- **Markers:** 7

### Claims to verify (each is a sentence from the survey that cites this source)

1. `scope-and-the-code-modality.md:17` — A naive text tokenizer wastes capacity on these; code models therefore add whitespace-run tokens (CodeGen extends the GPT-2 byte-pair vocabulary with tokens for repeated tabs and spaces [[3]](references.
2. `scope-and-the-code-modality.md:24` — md#ref-1), [[3]](references.
3. `scope-and-the-code-modality.md:25` — md#ref-1) and CodeGen's multi-turn program synthesis [[3]](references.
4. `language-models-from-first-principles.md:244` — 1) trained on code — CodeGen and InCoder maximize the likelihood of a code corpus [[3]](references.
5. `language-models-from-first-principles.md:244` — CodeGen extends the GPT-2 byte-pair vocabulary with special tokens for repeated runs of tabs and spaces, compressing Python's indentation [[3]](references.
6. `historical-evolution.md:23` — 28% HumanEval pass@1 [[3]](references.
