# Cluster C scratch — §8 Instruction Tuning & Alignment, §9 Reasoning & Test-Time Compute

Evidence collection for "LLMs for code" survey. Raw facts + locators only; main thread owns synthesis.

---

### Q1: Instruction-data generation for code (Self-Instruct, Code Alpaca, Evol-Instruct/WizardCoder, OSS-Instruct/Magicoder)

- **Findings**:
  - **Self-Instruct (lineage)**: bootstraps instruction data by applying SELF-INSTRUCT on ChatGPT from **21 seed tasks** (Magicoder relates work, p.2). Code Alpaca = Self-Instruct-style code instruction dataset (~20K samples) used as WizardCoder's *basic* seed set.
  - **Code Evol-Instruct (WizardCoder)**: adapts WizardLM's Evol-Instruct to code. *Method*: iteratively rewrites a seed instruction into a "Harder Task" via heuristics — (1) add constraints/requirements (~10 extra words), (2) replace a common requirement with a rarer one, (3) "if solvable in few logical steps, add more reasoning steps," (4) "provide a piece of erroneous code as a reference to increase misdirection," (5) "propose higher time or space complexity requirements." Tailored to code via: coding-task features, adversarial-sample heuristics, time/space complexity requirements, and evolving stop controls (p.3–4).
    - *Data*: start from Code Alpaca (~20k); after each evolution **round**, merge evolved data from all previous rounds + original, finetune; external dev set as stop control.
    - *Training*: batch size 512, seq len 2048, 200 finetune steps, 30 warmup, LR 2e-5, cosine, fp16.
    - *Gains (pass@1, single attempt)*: **WizardCoder-15B (base StarCoder-15B): HumanEval 57.3, MBPP 51.8** vs base StarCoder-15B HumanEval 33.6 (+23.7). **WizardCoder-34B (base CodeLlama-34B): HumanEval 71.5, MBPP 61.2** vs CodeLlama-Python-34B 53.7/56.2. 15B version beats Claude-Plus (59.8 vs 53.0) and Bard (59.8 vs 44.5) on HumanEval (p.1, Table 2–4).
  - **OSS-Instruct (Magicoder)**: generates instruction data by prompting an LLM (ChatGPT/GPT-3.5) with **real open-source code snippets** as inspiration to "produce diverse, realistic, controllable code instructions" — motivation is to mitigate the systematic bias of purely model-synthesized data.
    - *Data*: seed corpus = **starcoderdata** (filtered The Stack); collected **80K initial seed snippets** from 80K code documents (40K Python, 5K each of C++/Java/TypeScript/Shell/C#/Rust/PHP...); generated **75K synthetic instruction-response pairs**.
    - *Orthogonality*: OSS-Instruct is orthogonal to Evol-Instruct; combining them yields enhanced "MagicoderS."
    - *Gains (HumanEval pass@1, HumanEval+ in parens)*: base **CodeLlama-Python-7B 48.2 (40.9)** → **Magicoder-CL 60.4 (55.5)** → **MagicoderS-CL 70.7 (66.5)**; MagicoderS-CL on par with ChatGPT on HumanEval (70.7 vs 72.6), beats it on HumanEval+ (66.5 vs 65.9). On DeepSeek-Coder-Base-6.7B: **MagicoderS-DS 76.8 pass@1 HumanEval**, beats DeepSeek-Coder-Instruct-6.7B with 8× fewer finetuning tokens. Models ≤7B params, 75K data (p.1–2, Table 1).
- **Sources**:
  - Luo et al., "WizardCoder: Empowering Code LLMs with Evol-Instruct," ICLR 2024 (arXiv:2306.08568) — (local: download/wizardcoder-2023.pdf)
  - Wei et al., "Magicoder: Empowering Code Generation with OSS-Instruct," 2023 (arXiv:2312.02120) — (local: download/magicoder-2023.pdf)
  - Self-Instruct / Code Alpaca: described via WizardCoder & Magicoder related-work; primary papers not acquired (budget) — (abstract-only / secondary)
- **Confidence**: high (WizardCoder, Magicoder numbers read directly from tables/abstract). medium for Self-Instruct/Code Alpaca specifics (secondary attribution).
- **Gaps**: Self-Instruct (Wang et al. 2022) and Code Alpaca primary papers not in download/; exact Code Alpaca size (~20K) is from WizardCoder's description, not Code Alpaca repo.

---

### Q2: RL from EXECUTION feedback (CodeRL, RLEF, PPO with unit-test rewards, RLVR)

- **Findings**:
  - **CodeRL (Le et al. 2022)**: actor-critic RL for program synthesis. Pretrained LM = **actor** (stochastic policy); code generations = actions; unit-test results from the compiler = environment reward.
    - *Reward function* (Eqs. 4–7, p.6) — terminal reward on the full program $W^s$:
      `r(W^s) = -1.0` if cannot be compiled (compile error); `-0.6` if cannot be executed with unit tests (runtime error); `-0.3` if failed any unit test; `+1.0` if passed all unit tests.
    - *Critic*: a separate **error-predictor** model trained to predict one of **four outcomes {CompileError, RuntimeError, FailedTest, PassedTest}**; its token-level hidden states estimate per-token values/returns → enables *intermediate (token-level) returns* rather than only a sparse terminal reward.
    - *Objective*: minimize expected return $L_{rl}(\theta) = -\mathbb{E}_{W^s\sim p_\theta}[r(W^s)]$ (Eq. 2). Gradient (Eq. 10) uses a **baseline program** $W^b$ and *relative return* $(r(W^s)-r(W^b))$ weighting the token-level critic estimate $\hat q_\phi(w^s_t)$ — i.e. self-critical / advantage form to stabilize training.
    - *Backbone*: CodeT5; pretrained on GCPY (10.5B-token Python from github-code, 10× CodeSearchNet).
    - *Results*: new SOTA on **APPS** + zero-shot transfer SOTA on **MBPP**. CodeRL+CodeT5-770M reaches >2% pass@1, 6% pass@5, ~20% pass@1000 on APPS; on MBPP table CodeRL+CodeT5 770M: 40.00 / 15.67 / 17.90 / 20.98 vs CodeT5 baseline 35.20 / 13.15 / 13.51 / 17.63 (p.1, Table). Method is model-agnostic. Inference also adds a **program-repair / Critic Sampling** loop using error types + compiler messages.
  - **RLEF (Gehring et al. 2024, "Grounding Code LLMs in Execution Feedback")**: end-to-end RL teaching the model to **iteratively improve code over multiple turns** using automatic execution feedback (run code → feed test failures/errors back → revise). Reward grounded in test pass/fail across the multi-turn episode (full reward detail not in abstract).
    - *Models*: Llama 3.1 **8B and 70B**. *Results (CodeContests)*: 70B RLEF — validation 37.5→40.4, **test 41.2** (vs 38.0 with feedback limited to public tests); reported to beat prior SOTA **AlphaCodium ~29%**, while **reducing samples required by an order of magnitude (~10×)**. (numbers from abstract + web; full PDF not acquired — budget.)
  - **PPO with unit-test pass/fail rewards / RLVR**: the unifying idea is **Reinforcement Learning with Verifiable Rewards (RLVR)** — for code (and math) the reward is computed by an *executable oracle* (compiler + test suite) rather than a learned reward model, so the signal is deterministic, cheap, and not gameable by reward-model exploitation. CodeRL's discrete reward and RLEF's test-based reward are concrete instances; modern code RL commonly uses PPO/GRPO with a binary/graded test-pass reward. (RLVR term canonicalized by Tulu-3 / DeepSeek-R1 era work — see Q5 for R1's rule-based accuracy reward.)
- **Sources**:
  - Le et al., "CodeRL: Mastering Code Generation through Pretrained Models and Deep RL," NeurIPS 2022 (arXiv:2207.01780) — (local: download/coderl-2022.pdf)
  - Gehring et al., "RLEF: Grounding Code LLMs in Execution Feedback with RL," 2024 (arXiv:2410.02089) — (abstract-only; web: openreview.net/pdf?id=PzSG5nKe1q, arxiv.org/abs/2410.02089)
- **Confidence**: high (CodeRL reward eqs + values read directly). medium (RLEF — abstract + secondary web for the 41.2 / 29 / 10× figures, not the full PDF).
- **Gaps**: RLEF full PDF not acquired (would pin exact reward formulation and turn budget); RLVR has no single canonical paper in download/ — concept is synthesized from CodeRL + R1.

---

### Q3: Preference optimization for code (DPO on code; verifiable vs human-preference RLHF) — brief

- **Findings**:
  - **DPO (Direct Preference Optimization)** replaces the RLHF reward-model + PPO loop with a single classification-style loss on preference pairs $(y_w, y_l)$, implicitly fitting the reward via the policy itself — no separate reward model, no online sampling. Applied to code, the preference pairs can be sourced *cheaply and objectively from execution*: the chosen response = a program that **passes** the test suite, the rejected = one that **fails** (compile/runtime/wrong-output). This makes "preference" data verifiable rather than human-annotated. (Concept; primary DPO paper Rafailov et al. 2023 not in download/ — budget.)
  - **Key contrast — verifiable reward vs human-preference RLHF**:
    - *Human-preference RLHF* (e.g. InstructGPT): a learned reward model trained on human preference judgments approximates a subjective, noisy, gameable signal; PPO optimizes against it and can reward-hack the model.
    - *Verifiable reward (code/math, RLVR)*: the reward is an **executable oracle** (compiler + unit tests) → deterministic, objective, cheap to scale, not gameable by exploiting a learned RM. CodeRL's discrete `{-1.0,-0.6,-0.3,+1.0}` and DeepSeek-R1's rule-based accuracy reward are instances. The practical implication: for code you can run *RL (or DPO) at scale without human labels*, which is what enables the reasoning-model results in Q5.
- **Sources**:
  - DPO: Rafailov et al., "Direct Preference Optimization," NeurIPS 2023 (arXiv:2305.18290) — (abstract-only; not acquired, budget)
  - Verifiable-vs-RLHF contrast synthesized from CodeRL (local: download/coderl-2022.pdf) and DeepSeek-R1 (local: download/deepseek-r1-2025.pdf) reward designs.
- **Confidence**: medium (conceptual; DPO primary not in repo, but the contrast is grounded in two acquired reward designs).
- **Gaps**: No code-specific DPO paper acquired (e.g. Code-Optimise / PLUM-style work); DPO loss equation cited from general knowledge, not a read source — flag for main thread if a load-bearing DPO equation is needed.

---

### Q4: Test-time reasoning for code (CoT, Self-Debugging, Reflexion, sample-and-rerank / self-consistency)

- **Findings**:
  - **Chain-of-thought for code**: decompose the problem into NL reasoning / a plan before emitting code; raises pass@1 by surfacing intermediate logic. (Covered via the reasoning-model papers; no standalone CoT-for-code primary acquired.)
  - **Self-Debugging (Chen et al. 2023)**: teaches an LLM to debug its *own* predicted code via **few-shot prompting**, no finetuning, no human feedback. *Mechanism*: model investigates **execution results** and **explains the generated code in natural language** ("rubber-duck debugging") to localize its own mistakes, then revises. Two feedback regimes: (a) *simple* (just correctness/unit-test pass-fail), (b) *code explanation* (model narrates the code line-by-line) — explanation helps most where no unit tests exist.
    - *Gains*: SOTA on **Spider (text-to-SQL)**, **TransCoder (C++→Python)**, **MBPP**. On Spider (no unit tests): code-explanation improves baseline by **2–3%**, and **+9% on hardest-level** problems. On TransCoder & MBPP (unit tests available): improves baseline accuracy by **up to 12%**; >12% on TransCoder and ~8% on MBPP self-debugging gain (on par with Codex). Also improves **sample efficiency** by reusing failed predictions + feedback (abstract, p.1).
  - **Reflexion (Shinn et al. 2023)**: "verbal reinforcement learning" — reinforces a language agent **not by updating weights** but via **linguistic feedback** stored in an **episodic memory buffer** across trials. *Three-model formulation*: **Actor $M_a$** (generates text/actions), **Evaluator $M_e$** (scores outputs), **Self-Reflection $M_{sr}$** (turns binary/scalar feedback into verbal self-reflection that acts as a "semantic gradient" guiding the next attempt).
    - *Gains*: **HumanEval pass@1 91.0%**, beating prior SOTA **GPT-4 at 80.1%**; on Python programming "by as much as 11%." Other tasks: AlfWorld +22% (abs, 12 steps), HotPotQA +20%. (Table: HumanEval-PY 91.0 vs 80.1 GPT-4 / 65.8 CodeT+GPT-3.5; MBPP-PY 77.1 vs 80.1; HumanEval-RS 68.0, MBPP-RS 75.4) (abstract, p.1–3).
  - **Sample-and-rerank / self-consistency**: generate $k$ candidate programs, then *rerank/filter* — by executing against (visible) unit tests, by majority/self-consistency over outputs, or by a learned scorer — and return the best. This is the lever behind **pass@k** scaling (CodeRL: >2% pass@1 → ~20% pass@1000 on APPS, showing the large gap reranking can close) and the "RS" (reranked-sample) columns in Reflexion. The mechanism: cheap test-time compute (more samples + an execution-based selector) substitutes for model quality.
- **Sources**:
  - Chen et al., "Teaching Large Language Models to Self-Debug," 2023 (arXiv:2304.05128) — (local: download/self-debugging-2023.pdf)
  - Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," NeurIPS 2023 (arXiv:2303.11366) — (local: download/reflexion-2023.pdf)
  - pass@k / sampling scaling: CodeRL (local: download/coderl-2022.pdf) Table; self-consistency primary (Wang et al. 2022) not acquired — (abstract-only).
- **Confidence**: high (Self-Debugging, Reflexion numbers read directly). medium for generic CoT-for-code & self-consistency (no standalone primary acquired).
- **Gaps**: No standalone CoT (Wei et al. 2022) or self-consistency (Wang et al. 2022) primary in download/; AlphaCode-style large-scale sample+filter primary not acquired.

---

### Q5: Reasoning models for competitive-level code (DeepSeek-R1, o-series)

- **Findings (DeepSeek-R1, hard numbers from the paper):**
  - **DeepSeek-R1-Zero**: pure RL applied **directly to DeepSeek-V3-Base with no supervised fine-tuning (no SFT cold-start)**. RL framework = **GRPO (Group Relative Policy Optimization)**. Reward is **rule-based**, two components: **accuracy rewards** (is the final answer correct — e.g. math with deterministic answer checked against ground truth; code checked by compiler/tests) and **format rewards** (enforce `<think>…</think>` reasoning encapsulation). Deliberately **no neural reward model** for the main signal, to avoid reward hacking.
    - *Self-evolution / emergent behavior*: model naturally develops longer responses, self-verification, reflection, and exploration — the famous **"aha moment"** (Table 2): an intermediate R1-Zero version learns to *rethink/re-evaluate* in an anthropomorphic tone, with no explicit prompting.
    - *Numbers*: AIME 2024 **pass@1 jumps 15.6% → 77.9%** over RL training; with self-consistency (cons@16) reaches **86.7%**, surpassing average human competitors.
  - **DeepSeek-R1 (final)**: adds a small **cold-start** stage (collect "thousands of" human-aligned long-CoT examples) → RL → rejection-sampling SFT → final RL, to fix R1-Zero's poor readability/language-mixing. Test-time: **dynamically allocates compute** by generating hundreds–thousands of reasoning tokens (not majority-voting/MCTS).
    - *Benchmark table (Table 3, final R1 column; metric)*: **Codeforces Percentile 96.3, Codeforces Rating 2029**; **LiveCodeBench Pass@1-CoT 65.9**; **SWE-Bench Verified (Resolved) 49.2**; **Aider-Polyglot 53.3**; **AIME 2024 Pass@1 79.8**; **MATH-500 Pass@1 97.3**; **CNMO 2024 78.8**; GPQA-Diamond 71.5; MMLU 90.8. (R1-Zero baseline column on same table: Codeforces 80.4 pctile / 1444 rating, LiveCodeBench 50.0, SWE 43.2, AIME 77.9, MATH-500 95.9.)
  - **Significance**: R1 demonstrates competitive-programming-level reasoning *emerges from RL with verifiable (rule-based) rewards alone* — the strongest evidence for the RLVR thesis in Q2/Q3, and minimal human labeling.
- **Findings (o-series — official report / web only, with locator):**
  - **OpenAI o1** ("Learning to reason with LLMs," Sep 2024): on Codeforces, o1 reaches an **Elo ~1807**, placing it in roughly the **89th percentile** ("better than 93% of competitors" in the simulated-contest framing); compared to **GPT-4o at Elo 808 (11th percentile)**. A fine-tuned o1 (o1-ioi) ranked **49th percentile at IOI 2024** under competition rules. o1 also qualifies among top US AIME students.
  - **"Competitive Programming with Large Reasoning Models"** (OpenAI, arXiv:2502.06807, Feb 2025): reports **o3** reaching a Codeforces rating ~2706 / gold-medal-level IOI 2024 *without* hand-crafted inference pipelines (general RL scaling beats domain-specific o1-ioi scaffolding). (Exact o3 figure to be pinned from the report if load-bearing.)
- **Sources**:
  - DeepSeek-AI, "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via RL," 2025 (arXiv:2501.12948) — (local: download/deepseek-r1-2025.pdf)
  - OpenAI, "Learning to reason with LLMs," 2024 — (web: openai.com/index/learning-to-reason-with-llms/; official page 403 to direct fetch, figures via cached/secondary search of the official page)
  - OpenAI, "Competitive Programming with Large Reasoning Models," 2025 (arXiv:2502.06807) — (web; not acquired as PDF — budget)
- **Confidence**: high (all R1 numbers read directly from Table 3 + abstract/§2 of the local PDF). medium (o1/o3 figures — official-source claims relayed via web search, official page not directly fetchable, exact o3 rating not pinned from PDF).
- **Gaps**: o-series report PDF (2502.06807) not acquired (budget); o1 system card not acquired; the exact o3 Codeforces rating (~2706) should be confirmed against the report before becoming a load-bearing survey number.
