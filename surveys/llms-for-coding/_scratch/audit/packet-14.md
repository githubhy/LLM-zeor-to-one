# Citation-audit packet 14

7 source(s), 15 citation marker(s).

## Reference [55]

- **Source PDF:** `download/kaplan-scaling-laws-2020.pdf`
- **Reference entry:** J. Kaplan, S. McCandlish, T. Henighan, T. B. Brown, et al., "Scaling Laws for Neural Language Models." 2020. a
- **Cited in:** language-models-from-first-principles
- **Markers:** 3

### Claims to verify (each is a sentence from the survey that cites this source)

1. `language-models-from-first-principles.md:223` — (forward and backward passes cost about six floating-point operations per parameter per token) [[55]](references.

## Reference [16]

- **Source PDF:** `download/wizardcoder-2023.pdf`
- **Reference entry:** Z. Luo, C. Xu, P. Zhao, Q. Sun, et al., "WizardCoder: Empowering Code Large Language Models with Evol-Instruct
- **Cited in:** instruction-tuning-and-alignment
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `instruction-tuning-and-alignment.md:23` — ** Rather than sampling new instructions flatly, WizardCoder iteratively *evolves* seed instructions into harder ones — adding constraints, increasing reasoning steps, requesting higher time/space complexity, or injecting buggy reference code as misdirection — then fine-tunes on the accumulated set [[16]](references.
2. `instruction-tuning-and-alignment.md:23` — 2%, with the 15B model surpassing contemporaneous Claude and Bard numbers on HumanEval [[16]](references.

## Reference [17]

- **Source PDF:** `download/magicoder-2023.pdf`
- **Reference entry:** Y. Wei, Z. Wang, J. Liu, Y. Ding, L. Zhang, "Magicoder: Empowering Code Generation with OSS-Instruct." *ICML 2
- **Cited in:** instruction-tuning-and-alignment
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `instruction-tuning-and-alignment.md:24` — ** Instead of evolving model-invented instructions, Magicoder grounds generation in *real* open-source code: it prompts a model with 80k seed snippets drawn from filtered Stack data to produce 75k realistic instruction-response pairs, reducing the systematic bias of purely synthetic data [[17]](references.
2. `instruction-tuning-and-alignment.md:24` — 8% with eight times fewer fine-tuning tokens than the official instruct model [[17]](references.

## Reference [23]

- **Source PDF:** `download/self-debugging-2023.pdf`
- **Reference entry:** X. Chen, M. Lin, N. Schärli, D. Zhou, "Teaching Large Language Models to Self-Debug." *ICLR 2024.* arXiv:2304.
- **Cited in:** reasoning-and-test-time-compute
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `reasoning-and-test-time-compute.md:26` — Self-Debugging teaches a model to debug its predicted code via few-shot prompting alone — no fine-tuning, no human feedback — by having it investigate execution results and explain its code in natural language ("rubber-duck debugging") to localize mistakes, then revise [[23]](references.
2. `reasoning-and-test-time-compute.md:26` — The gains are consistent: on the Spider text-to-SQL task (which has no unit tests) code explanation improves the baseline by 2–3% overall and up to 9% on the hardest problems, and where unit tests are available (TransCoder, MBPP) self-debugging improves accuracy by up to 12% while also improving sample efficiency by reusing failed attempts [[23]](references.

## Reference [24]

- **Source PDF:** `download/reflexion-2023.pdf`
- **Reference entry:** N. Shinn, F. Cassano, E. Berman, A. Gopinath, et al., "Reflexion: Language Agents with Verbal Reinforcement Le
- **Cited in:** reasoning-and-test-time-compute
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `reasoning-and-test-time-compute.md:26` — Reflexion generalizes this into "verbal reinforcement learning": rather than updating weights, an Actor generates attempts, an Evaluator scores them, and a Self-Reflection module converts the feedback into linguistic notes stored in an episodic memory that guides the next attempt [[24]](references.

## Reference [27]

- **Source PDF:** `download/leviathan-speculative-decoding-2023.pdf`
- **Reference entry:** Y. Leviathan, M. Kalman, Y. Matias, "Fast Inference from Transformers via Speculative Decoding." *ICML 2023.* 
- **Cited in:** compute-cost-and-latency-tradeoffs, inference-decoding-and-serving
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `inference-decoding-and-serving.md:18` — **Speculative decoding** breaks the serial dependency: a small, cheap draft model proposes several tokens, and the large target model verifies them in a single parallel forward pass, accepting the longest correct prefix — producing identical output to the target model at a fraction of the wall-clock cost [[27]](references.
2. `compute-cost-and-latency-tradeoffs.md:21` — 7 seconds [[27]](references.

## Reference [28]

- **Source PDF:** `download/picard-2021.pdf`
- **Reference entry:** T. Scholak, N. Schucher, D. Bahdanau, "PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding 
- **Cited in:** inference-decoding-and-serving
- **Markers:** 2

### Claims to verify (each is a sentence from the survey that cites this source)

1. `inference-decoding-and-serving.md:13` — PICARD demonstrates the idea for SQL: during beam search it incrementally parses each candidate's detokenized output and rejects tokens that would make the query inadmissible, with checking modes ranging from lexing to full parsing with schema-aware guards [[28]](references.
2. `inference-decoding-and-serving.md:13` — 3% execution accuracy on Spider [[28]](references.
