# C6 — Reasoning & test-time compute for code

## Q1. Sample-and-select scaling for code (AlphaCode)

### Massive sampling + filtering removes ~99% of samples
- **Claim**: AlphaCode draws up to millions of samples per problem, then filters using the problem's public example tests, which eliminates roughly 99% of samples before any further selection.
- **Numbers**: "Filtering removes approximately 99% of model samples" (§4.5). Table 9 (1,000,000 samples drawn per problem, per model): % problems with ≥1 sample passing example tests — 300M: 82.05%, 1B: 87.18%, 3B: 87.18%, 9B: 89.74%, 41B: 92.31%. Average p(pass example tests) on ALL problems — 300M: 0.39%, 1B: 0.59%, 3B: 0.49%, 9B: 0.76%, 41B: 0.73%. Average p(pass example tests) on SOLVED problems only — 300M: 1.18%, 1B: 1.40%, 3B: 0.98%, 9B: 1.52%, 41B: 1.47%. On ~10% of problems, no single sample of any model passes the example tests at all.
- **Conditions**: CodeContests validation set; 10^6 samples/problem; models 300M–41B (encoder-decoder, multi-query attention); temperature-based sampling (T'=0.25 with tempering+GOLD).
- **Source**: Li et al. (DeepMind), "Competition-Level Code Generation with AlphaCode," 2022, arXiv:2203.07814v1.
- **Quality tier**: primary
- **Quote**: "Filtering removes approximately 99% of model samples, although the exact amount depends on the problem and model, and filtering can still leave tens of thousands of candidate samples for many problems... on approximately 10% of problems our models cannot find a single such program."
- **Confidence**: high
- **Local path**: download/alphacode-2022.pdf

### Clustering step (post-filter selection)
- **Claim**: After filtering, AlphaCode clusters the surviving (still numerous) candidate programs by execution behavior on model-generated test inputs, then submits one representative from each cluster, largest cluster first, to make efficient use of a strict 10-submission budget.
- **Numbers**: none additional beyond above; clustering + filtering raises 10@100k solve rate from 15.2% (no enhancements) to 24.1% (full enhancement stack including clustering) per Table 8 ablation (95% CI reported, e.g. 10@100k: 24.1% [23.2-25.0]).
- **Conditions**: 1B model ablation, CodeContests validation, ≥3 fine-tuned models per setting, 95% CIs via subsampling+bootstrapping.
- **Source**: same as above.
- **Quality tier**: primary
- **Quote**: "We cluster the remaining samples based on their behaviour on generated test inputs, to make the most of the evaluation budget... After clustering on program behaviour we found that selecting one solution from each cluster from largest to smallest performed best."
- **Confidence**: high
- **Local path**: download/alphacode-2022.pdf

### Scaling curve shape: log-linear in samples, tapering in 10@k
- **Claim**: Solve rate scales approximately log-linearly with the number of samples drawn (both pass@k, the unlimited-submission oracle metric, and 10@k, the realistic filtered/clustered-selection metric under a fixed submission budget), but the 10@k curve bends down (diminishing returns) at high sample budgets, showing selection quality — not just search/coverage — becomes the bottleneck.
- **Numbers**: Figure 6 sweeps sample budget 10^0–10^6 across model sizes 300M/1B/3B/9B/41B. Larger models show higher log-linear slopes: "a better model with a higher slope can reach the same solve rate with exponentially fewer samples than worse models." Figure 7 shows solve rate also scales log-linearly with training compute (7a) and with sampling compute (7b, TPU-seconds/problem), though larger models take more compute per sample.
- **Conditions**: CodeContests validation set, 10@k and pass@k metrics defined in §2.2 (pass@k = submit all k samples; 10@k = submit only 10 of the k samples, so 10@k also measures the filtering/clustering selection quality).
- **Source**: same as above.
- **Quality tier**: primary
- **Quote**: "Solve rates scale log-linearly with more samples... with the 10@k curve bending down slightly at high sample budgets... However, improving solve rate requires exponentially increasing amounts of samples and the costs quickly become prohibitive."
- **Confidence**: high
- **Local path**: download/alphacode-2022.pdf

### Headline solve-rate numbers (CodeContests, Table 5) and Codeforces ranking
- **Claim**: AlphaCode's best system (41B + clustering) solves 34.2% of CodeContests validation problems at 10@1M and achieves an average top-54.3% ranking (est. Codeforces rating 1238) across 10 live-simulated Codeforces contests when capped at 10 submissions/problem; ranking improves to top 48.8% when submissions are uncapped (avg. 28.8 submissions per solved problem vs 2.4 when capped).
- **Numbers**: see table below; Codeforces: top 54.3% avg (10-submission cap, avg 2.4 submissions/solved problem), top 48.8% (uncapped, avg 28.8 submissions/solved problem); estimated rating 1238 (top 28% of active users). CodeContests (existing datasets) false-positive rate reduced from 30-60% to 4%.
- **Conditions**: Codeforces: 10 contests, Dec 2021, >5,000 participants each, ensembled 41B (used alone + clustering was best, beating the 41B+9B ensemble). CodeContests: 41B model, with/without clustering, validation and test sets (temporally disjoint).
- **Source**: same as above.
- **Quality tier**: primary
- **Quote**: "Our system achieved an average ranking of top 54.3%... with an actual average of 2.4 submissions for each problem solved... When allowed more than 10 submissions per problem... AlphaCode achieved a ranking of top 48.8%, with an actual average of 28.8 submissions for each problem solved."
- **Confidence**: high
- **Local path**: download/alphacode-2022.pdf

**Sample-budget vs solve-rate table (Table 5, CodeContests, exact reported values):**

| Samples n | Metric | Value | Conditions |
|---|---|---|---|
| 1,000 | 10@1k | 16.9% | 9B model, validation set |
| 10,000 | 10@10k | 22.6% | 9B model, validation set |
| 100,000 | 10@100k | 27.1% | 9B model, validation set |
| 1,000,000 | 10@1M | 30.1% | 9B model, validation set |
| 1,000 | 10@1k | 16.9% | 41B model, validation set |
| 10,000 | 10@10k | 23.9% | 41B model, validation set |
| 100,000 | 10@100k | 28.2% | 41B model, validation set |
| 1,000,000 | 10@1M | 31.8% | 41B model, validation set |
| 1,000 | 10@1k | 21.0% | 41B + clustering, validation set |
| 10,000 | 10@10k | 26.2% | 41B + clustering, validation set |
| 100,000 | 10@100k | 31.8% | 41B + clustering, validation set |
| 1,000,000 | 10@1M | 34.2% | 41B + clustering, validation set (headline number) |
| 1,000 | 10@1k | 16.4% | 41B + clustering, TEST set |
| 10,000 | 10@10k | 25.4% | 41B + clustering, TEST set |
| 100,000 | 10@100k | 29.6% | 41B + clustering, TEST set |


## Q2. Execution-based selection vs self-consistency for code

### Execution-based selection taxonomy: majority vote vs learned reranking
- **Claim**: For code specifically, selecting among n candidate samples is done either by majority vote over execution results (grouping programs that produce identical outputs on some inputs and picking the largest group) or by learned/heuristic reranking; when problem-provided unit tests exist, programs are first filtered to only those that pass, before the execution-based majority vote is applied.
- **Numbers**: none in this excerpt (survey/related-work paragraph, not a new experiment).
- **Conditions**: n/a — background section citing Chen et al. 2019, Li et al. 2022 (=AlphaCode), Shi et al. 2022 for majority-vote-of-execution-results; Zhang et al. 2022, Ni et al. 2023, Yin & Neubig 2019, Zeng et al. 2022 for reranking schemes.
- **Source**: Chen, Lin, Schärli, Zhou (Google DeepMind), "Teaching Large Language Models to Self-Debug," 2023, arXiv:2304.05128v2.
- **Quality tier**: strong-secondary (survey/related-work claim within a primary paper, not itself a head-to-head experiment)
- **Quote**: "For code generation tasks, we can utilize code execution to select the final prediction... One line of work selects the predicted code with the majority vote of execution results..., while other works design reranking schemes to improve the performance... When unit tests are presented in the problem description, we filter out programs that do not pass the unit tests before performing the execution-based majority vote."
- **Confidence**: high
- **Local path**: download/self-debugging-2023.pdf

### CodeT: dual execution agreement using model-generated tests
- **Claim**: CodeT has the LLM itself generate both code candidates and test cases, then selects the candidate program via "dual execution agreement" — clustering by agreement between (a) execution against the generated tests and (b) output agreement with other code samples — substantially beating plain sampling/pass@1 without this selection.
- **Numbers**: CodeT reaches 65.8% pass@1 on HumanEval, "an absolute improvement of 18.8% over the code-davinci-002 model" (baseline ungated pass@1). Evaluated across HumanEval, MBPP, APPS, and CodeContests with five pretrained code models.
- **Conditions**: code-davinci-002 backbone (+CodeT selection); HumanEval pass@1; exact MBPP/APPS/CodeContests pass@1 deltas not captured in this pass (abstract-level only — see Gaps).
- **Source**: Chen, Zhang, Nguyen, Zan, Lin, Lou, W. Chen (Microsoft), "CodeT: Code Generation with Generated Tests," arXiv:2207.10397 (submitted 2022-07-21, revised 2022-11-23).
- **Quality tier**: strong-secondary (verified via arXiv abstract page fetch, not the full PDF body — numbers are from the abstract only, not independently cross-checked against a table)
- **Quote**: "CodeT... achieves 65.8%... an absolute improvement of 18.8% over the code-davinci-002 model" (per arXiv abstract).
- **Confidence**: medium (abstract-sourced, not full-text verified; not locally acquired — flagged in Sources worth acquiring)
- **Local path**: NOT ACQUIRED (verified via WebFetch of arXiv abstract page only)

### Reliability of self-generated tests as verifiers: quantified false-positive rate (Reflexion)
- **Claim**: When an LLM writes its own test suite to verify its own code (the verifier and the generator share the same model and the same blind spots), the resulting execution-based selection is measurably unreliable, and the unreliability is benchmark-dependent — Reflexion directly measures this via "false positive" test executions (all generated tests pass but the real, hidden-test solution is actually incorrect).
- **Numbers**: False-positive test-execution rate (P(fails real pass@1 | passes all self-generated tests)): **16.3% on MBPP Python** vs **1.4% on HumanEval Python** — an order-of-magnitude difference on the same method, same model (GPT-4), attributed by the authors to test-suite quality/diversity differences between benchmarks. Reflexion pass@1 on HumanEval Python rises from an 0.80 baseline to 0.91 (TP=0.99, FN=0.40, FP=0.01, TN=0.60 in the paper's confusion-style table); on MBPP Python it rises only 0.80→0.77 (i.e. self-debugging with a flaky verifier can even *underperform* the plain baseline: TP=0.84, FN=0.59, FP=0.16, TN=0.41).
- **Conditions**: Reflexion + self-generated unit-test-suite verification (CoT-generated tests filtered for syntactic validity via AST parse, n≤6 tests sampled per problem); GPT-4 base model; HumanEval and MBPP, Python and Rust (via MultiPL-E translation); pass@1, max 1 experience in memory.
- **Source**: Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao, "Reflexion: Language Agents with Verbal Reinforcement Learning," 2023, arXiv:2303.11366v4.
- **Quality tier**: primary
- **Quote**: "We acknowledge that self-reflecting code-generation agents are bound to their ability to write diverse, comprehensive tests... if the model produces an incorrectly written test suite, it is possible for some of the tests to fail on a correct solution... Given the implementation of Reflexion, false negatives are preferred over false positives... we observe a notable discrepancy between the false positive labels produced by internal test execution... the false positive test execution rate for MBPP Python is 16.3% while the rate for HumanEval Python is a mere 1.4%."
- **Confidence**: high
- **Local path**: download/reflexion-2023.pdf

### Self-consistency: the general (non-code-specific) majority-vote baseline
- **Claim**: Self-consistency (sample-and-marginalize: sample diverse chain-of-thought reasoning paths, then take the most common final answer) is the general-purpose ancestor of execution-based code selection, but the original paper's evaluation is over arithmetic/commonsense QA benchmarks (GSM8K, SVAMP, AQuA, StrategyQA, ARC-challenge), not code — its "answer" is a discrete final value that can literally be counted by string match, unlike a program that must be executed. Self-debugging (above) explicitly frames execution-based majority vote as the code-domain analogue.
- **Numbers**: +17.9% (GSM8K), +11.0% (SVAMP), +12.2% (AQuA), +6.4% (StrategyQA), +3.9% (ARC-challenge) absolute accuracy gains over greedy chain-of-thought, using PaLM-540B/GPT-3-175B. No code benchmark numbers reported in this paper.
- **Conditions**: PaLM-540B, GPT-3-175B, LaMDA-137B, UL2-20B; sample-and-marginalize decoding vs single greedy CoT decode; arithmetic/commonsense reasoning tasks only.
- **Source**: Wang, Wei, Schuurmans, Le, Chi, Narang, Chowdhery, Zhou (Google Research), "Self-Consistency Improves Chain of Thought Reasoning in Language Models," ICLR 2023, arXiv:2203.11171v4.
- **Quality tier**: primary (for its own non-code claims); not direct evidence for the code-specific question
- **Quote**: "self-consistency boosts the performance of chain-of-thought prompting with a striking margin on a range of popular arithmetic and commonsense reasoning benchmarks... GSM8K (+17.9%), SVAMP (+11.0%), AQuA (+12.2%), StrategyQA (+6.4%) and ARC-challenge (+3.9%)."
- **Confidence**: high (paper does not claim to cover code — noted as a scope gap, not a code-domain finding)
- **Local path**: download/self-consistency-2022.pdf


## Q3. Reasoning models on code

### OpenAI o1 / o1-ioi / o3 on Codeforces: RL scaling vs hand-crafted test-time strategy
- **Claim**: Across OpenAI's o-series, Codeforces competitive-programming rating rises sharply with (a) more RL training compute, (b) added hand-crafted domain-specific test-time strategy (clustering + reranking, modeled on AlphaCode), and (c) — the load-bearing comparison — scaling general-purpose RL alone (o3) eventually matches or beats the hand-engineered pipeline (o1-ioi) without any domain-specific test-time strategy.
- **Numbers**: CodeForces rating/percentile: gpt-4o 808/11th; o1-preview 1258/62nd; o1 1673/89th; o1-ioi (RL-only, no test-time strategy) 1807/93rd; o1-ioi + public-test filtering 2092/96th; o1-ioi + full hand-crafted test-time strategy (clustering+reranking+learned scorer) 2214/98th; o3 (early checkpoint, general RL, no hand-crafted strategy) **2724/99.8th**.
- **Conditions**: Simulated Codeforces Division 1 contests from 2024 and Dec 2023 (post pretraining/RL data cutoff, contamination-checked via OpenAI embedding API); full test suite + time/memory constraints per problem.
- **Source**: OpenAI, "Competitive Programming with Large Reasoning Models," 2025, arXiv:2502.06807v2.
- **Quality tier**: primary
- **Quote**: "o3 does not depend on coding-specific test-time strategies defined by humans. Instead, we found that complex test-time reasoning strategies emerged naturally from end-to-end RL, leading to unprecedented performance on competitive programming benchmarks."
- **Confidence**: high
- **Local path**: download/openai-competitive-programming-2025.pdf

### IOI 2024 head-to-head: hand-crafted scaffold (o1-ioi) vs scaled general RL (o3) — the load-bearing comparison
- **Claim**: At the live 2024 IOI, o1-ioi under real competition rules (50 submissions) needed its full hand-engineered pipeline (subtask decomposition, 10,000 samples/subtask, model-generated-test clustering, learned reranker) to reach only 213 points (49th percentile) — well short of the ~360-point gold threshold; only when submission limits were relaxed to 10,000/problem (i.e., abandoning selection entirely) did the same raw sampling reach 362.14 points, just above gold. o3, evaluated retrospectively under the *same* strict 50-submission IOI rules but using only a simple top-score-by-test-time-compute selection over 1,024 samples (no subtask decomposition, no clustering, no learned reranker), scored **395.64 points — above gold — without any of the hand-crafted machinery**. o3's own emergent test-time behavior (e.g., writing brute-force solutions to cross-check its optimized ones) reproduces part of what o1-ioi's designers had to hand-engineer.
- **Numbers**: o1-ioi: 213 pts (50 submissions, hand-crafted strategy, 49th pct) → 362.14 pts (10K submissions, no strategy). o3: 395.64 pts (50 submissions, simple top-k-by-test-time-compute over 1,024 samples). Gold medal threshold ≈ 360 points (of 600 max). Random 50-submission baseline for o1-ioi: 156 points average (so the hand-crafted selection strategy itself was worth "nearly 60 additional points" under the 50-submission constraint).
- **Conditions**: 2024 IOI, 6 problems, 10 hours, official rules (≤50 submissions/problem); o1-ioi sampled 10,000 solutions/subtask; o3 sampled only 1,024 solutions per problem from a single whole-problem prompt (no subtask decomposition).
- **Source**: same as above (OpenAI, arXiv:2502.06807v2).
- **Quality tier**: primary
- **Quote**: "o3 achieved 395.64 points, surpassing the gold threshold even under the 50-submission limit... the sophisticated test-time techniques that emerged during o3 training, such as generating brute-force solutions to verify outputs, served as a more than adequate replacement and eliminated the need for the hand-engineered clustering and selection pipelines required by o1-ioi... large-scale RL training alone can achieve state-of-the-art coding and reasoning performance."
- **Confidence**: high
- **Local path**: download/openai-competitive-programming-2025.pdf

### o-series on real-world software engineering (HackerRank Astra, SWE-bench Verified)
- **Claim**: The reasoning gains are not confined to competitive programming — o1/o3 also show large, monotonically increasing improvements on more realistic, multi-file/project-scale software-engineering benchmarks, and the RL-scaling advantage over hand-crafted scaffolding shows up there too (o3 beats o1's Agentless-scaffold result by a wide margin on SWE-bench Verified).
- **Numbers**: HackerRank Astra (65 project-based challenges) pass@1 / avg score: gpt-4o 50.91% / 69.52%; o1-preview 60.89% / 75.55% (+9.98 pp pass@1 vs gpt-4o); o1 63.92% / 75.80% (+3.03 pp pass@1 vs o1-preview). SWE-bench Verified (500 human-validated tasks, 5 attempts/task, avg of 3 trials): gpt-4o 33.2%; o1-preview 41.3% (+8.1 pp); o1 48.9% (+8.6 pp over o1-preview); o3 (early checkpoint) **71.7%** (+22.8 pp over o1).
- **Conditions**: o1-preview used the "Agentless" open-source scaffold since it was not trained to use code-execution/file-editing tools; no specialized test-time strategy used for SWE-bench (unlike IOI/Codeforces).
- **Source**: same as above.
- **Quality tier**: primary
- **Quote**: "o3, which was trained with significantly greater compute resources than o1, delivers an impressive 22.8% improvement over o1. These results underscore that enhanced reasoning skills extend beyond competitive programming challenges, proving their applicability to real-world tasks like software engineering."
- **Confidence**: high
- **Local path**: download/openai-competitive-programming-2025.pdf

### DeepSeek-R1: code-benchmark trajectory across training stages
- **Claim**: DeepSeek-R1's published ablation table shows code-benchmark performance (LiveCodeBench, Codeforces, SWE-bench Verified, Aider-Polyglot) rising across its multi-stage RL/SFT pipeline (R1-Zero → Dev1 → Dev2 → Dev3 → final R1), with the largest single jump on Codeforces rating coming from the pure-RL Dev1→Dev2 stage, and the paper explicitly notes only "marginal" further code/math gains from the final mixed-data RL stage (Dev3→R1), whose main benefit was general instruction-following (AlpacaEval2.0 +25%, ArenaHard +17%) rather than code/math.
- **Numbers** (Table 3, exact values): LiveCodeBench (Pass@1-COT): R1-Zero 50.0, Dev1 57.5, Dev2 63.5, Dev3 64.6, **R1 65.9**. Codeforces (Rating): R1-Zero 1444, Dev1 1534, Dev2 1687, Dev3 1746, **R1 2029**. Codeforces (Percentile): R1-Zero 80.4, Dev1 84.5, Dev2 90.5, Dev3 92.1, **R1 96.3**. SWE-bench Verified (Resolved): R1-Zero 43.2, Dev1 39.6, Dev2 44.6, Dev3 45.6, **R1 49.2**. Aider-Polyglot (Acc.): R1-Zero 12.2, Dev1 6.7, Dev2 25.6, Dev3 44.8, **R1 53.3**.
- **Conditions**: DeepSeek-V3-Base backbone; GRPO RL algorithm; DeepSeek-R1-Zero = pure RL, no SFT; Dev1/Dev2/Dev3 = intermediate checkpoints; benchmarks per §4: MMLU family, SWE-Bench Verified, Aider, LiveCodeBench (2024-08 to 2025-01 window), Codeforces, AIME 2024, CNMO 2024; statistical significance denoted by t-test p<0.01 (bold values only, per table note — most Code-row deltas across stages are NOT marked bold/significant in the excerpt captured).
- **Source**: DeepSeek-AI, "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning," 2025 (arXiv:2501.12948v2, this PDF revision dated 4 Jan 2026 per header).
- **Quality tier**: primary
- **Quote**: "Marginal improvements occurred in code and mathematics benchmarks, as substantial reasoning-specific RL was done in prior stages. The primary advancements in the final DeepSeek-R1 were in general instruction-following and user-preference benchmarks, with AlpacaEval 2.0 improving by 25% and ArenaHard by 17%."
- **Confidence**: high
- **Local path**: download/deepseek-r1-2025.pdf

### GAP — 2025-26 successor models' explicit thinking-budget vs code-accuracy/latency/cost curves
- **Claim**: NOT independently verified this session. Web search surfaced claims (o3 exposes a `reasoning_effort` parameter with low/medium/high settings; o4-mini uses a fixed internal budget; reported plateau behavior at high effort) but these came only from a search-engine synthesis of secondary/blog sources (chatforest.com, Medium, devtoollab.com) and one blocked primary fetch (openai.com returned HTTP 403). Do not cite the specific numbers ("97% accuracy... 8% more tokens", "o4-mini 92.7% vs o3 88.9% on AIME 2025") as verified — they are UNCONFIRMED against a primary source this session.
- **Numbers**: none verified
- **Conditions**: n/a
- **Source**: none verified (see Sources worth acquiring)
- **Quality tier**: weak
- **Quote**: n/a — declining to quote unverified secondary synthesis as fact
- **Confidence**: low
- **Local path**: NOT ACQUIRED


## Q4. Where does inference-time scaling stop paying?

### AlphaCode's own scaling curve already shows the bend (primary, cross-referenced from Q1)
- **Claim**: AlphaCode's own published curves are themselves a diminishing-returns / negative-result data point: the *filtered-and-selected* solve-rate metric (10@k, the realistic regime under a fixed submission budget) bends down at high sample budgets even though the *unlimited-submission* oracle metric (pass@k) keeps climbing log-linearly — meaning that past a certain sample budget, the bottleneck shifts from "can the model find a solution" (search/coverage) to "can filtering+clustering correctly identify it among the candidates" (selection). The paper states the cost explicitly: sample budget must grow exponentially for each further linear gain in solve rate, and calls this "quickly ... prohibitive."
- **Numbers**: 41B+clustering CodeContests validation solve rate: 10@1k=21.0% → 10@10k=26.2% → 10@100k=31.8% → 10@1M=34.2% (i.e., ~1000x more samples, from 10^3 to 10^6, buys +13.2 points, with visibly shrinking marginal gain per decade: +5.2 pts for the first 10x, +5.6 for the next 10x, +2.4 for the last 10x — the last decade of compute buys less than half the gain of the first).
- **Conditions**: CodeContests validation set, 41B model + clustering, 10@k metric (10-submission cap, filtered+clustered selection).
- **Source**: Li et al. (DeepMind), "Competition-Level Code Generation with AlphaCode," 2022, arXiv:2203.07814v1.
- **Quality tier**: primary
- **Quote**: "Both the 10@k and pass@k solve rates scale approximately log-linearly with k, with the 10@k curve bending down slightly at high sample budgets... However, improving solve rate requires exponentially increasing amounts of samples and the costs quickly become prohibitive."
- **Confidence**: high
- **Local path**: download/alphacode-2022.pdf

### Reflexion's flaky-verifier result is itself a negative/bounding result (primary, cross-referenced from Q2)
- **Claim**: Reflexion's MBPP-Python result is a direct instance of "more sampling/more iteration does not straightforwardly help, and can hurt, when the verifier is unreliable": with a 16.3% false-positive rate on self-generated tests, iterative self-debugging driven by that verifier moved pass@1 from 0.80 baseline to only 0.77 — i.e. the treatment *underperformed doing nothing*, because the agent's self-reflection loop is only as good as its (here, unreliable) success signal.
- **Numbers**: MBPP Python pass@1: base model 0.80 → Reflexion 0.77 (negative delta of −0.03); false-positive test-execution rate 16.3%. Contrast: HumanEval Python pass@1: base 0.80 → Reflexion 0.91 (+0.11) with only 1.4% false-positive rate.
- **Conditions**: GPT-4, self-generated unit-test-suite verification (AST-filtered, ≤6 tests/problem), max 1 experience in memory.
- **Source**: Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao, "Reflexion: Language Agents with Verbal Reinforcement Learning," 2023, arXiv:2303.11366v4.
- **Quality tier**: primary
- **Quote**: "we observe a notable discrepancy between the false positive labels produced by internal test execution... the false positive test execution rate for MBPP Python is 16.3% while the rate for HumanEval Python is a mere 1.4%" (§4.3, discussing MBPP Python as the one benchmark where "Reflexion... [is] except for MBPP Python" the case underperforming baseline GPT-4).
- **Confidence**: high
- **Local path**: download/reflexion-2023.pdf

### Inference Scaling fLaws: resampling has a hard ceiling under an imperfect verifier
- **Claim**: A dedicated theoretical + empirical study argues resampling-based inference scaling for code generation is fundamentally capped: when the verifier (e.g., unit tests) has any nonzero false-positive rate, that rate does not shrink with more resampling, so accuracy has an upper bound independent of compute spent; on HumanEval/MBPP (limited unit-test coverage) the false-positive rate correlates strongly with the model's own single-sample accuracy, so a weak model cannot be resampled into matching a strong model's single-sample accuracy; empirically the *optimal* number of sampling attempts is reported to often be **under 10**, because past that point the added false-positive risk outweighs the added coverage, bending the scaling curve down (not just flattening it).
- **Numbers**: "optimal sampling attempts are often fewer than 10" (per search-engine synthesis of the paper, not independently verified against the PDF text this session).
- **Conditions**: HumanEval, MBPP; resampling with an execution-based (unit-test) verifier.
- **Source**: Stroebl, Kapoor, Narayanan (Princeton), "The Limits of Inference Scaling Through Resampling" / revised as "Inference Scaling fLaws: The Limits of LLM Resampling with Imperfect Verifiers," arXiv:2411.17501 (v1: 2024-11; v2 retitled), accepted ICLR 2026.
- **Quality tier**: strong-secondary (identified and characterized via WebSearch synthesis of the arXiv listing/abstract; full PDF not opened this session — numbers not independently cross-checked against the source table)
- **Quote**: n/a — no verbatim text captured (search synthesis only, not the primary document)
- **Confidence**: medium (real, findable paper with a specific arXiv ID and ICLR 2026 acceptance corroborated by an OpenReview-adjacent listing and a GitHub repo (`benediktstroebl/inference-scaling-limits`) in the same search results — but exact numbers should be re-verified against the PDF before being stated as fact in the survey)
- **Local path**: NOT ACQUIRED — highest-priority acquisition target for this cluster (see Sources worth acquiring)

### Train-time vs test-time compute allocation: a landmark result exists, but not verified as code-specific
- **Claim**: A widely surfaced result (Snell et al.) argues that for a fixed inference compute budget, optimally allocated test-time compute can outperform a much larger pretrained model — i.e., test-time compute can substitute for some train-time/parameter compute — with a claimed 2-4x efficiency improvement from compute-optimal (vs. naive) test-time allocation. **This is a math-benchmark (MATH) result in the paper as commonly reported, not a code-generation result**; citing it for code would be a metric-basis violation (calibration-residuals check 4) unless a code-specific number from the actual paper is verified.
- **Numbers**: "efficiency of test-time compute scaling can be improved by a factor of 2-4x" via compute-optimal (adaptive, prompt-difficulty-aware) allocation vs. a fixed strategy (per search synthesis only).
- **Conditions**: unknown/unverified this session (benchmark, model family, exact allocation strategy not confirmed from primary text).
- **Source**: (attributed in search results to) "Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters," arXiv:2408.03314, ICLR 2025 (OpenReview id 4FWAwZtd2n).
- **Quality tier**: strong-secondary (paper's existence/venue corroborated via arXiv ID + OpenReview listing in search results; full text and code-specificity NOT verified this session)
- **Quote**: n/a
- **Confidence**: low-medium — flagged explicitly: do not cite this for a code-domain claim without opening the PDF and confirming which benchmarks it covers
- **Local path**: NOT ACQUIRED

### Self-debugging: spending compute on iterative refinement vs. raw resampling (compute-allocation comparison, code-specific, primary)
- **Claim**: As a directly code-specific, directly-read data point on "spend compute differently rather than just sampling more": Self-Debugging (iterative execution-feedback-driven refinement of a single candidate) is reported to match or beat baseline models that instead spend the compute on sampling 10x+ more independent candidates — i.e., iterative test-time refinement can be more sample-efficient than parallel resampling for the same benchmarks.
- **Numbers**: "matches or outperforms baseline models that generate more than 10x candidate programs" (qualitative comparison in the abstract; exact accuracy-vs-sample-count curve not captured in the pages read this session — see Gaps).
- **Conditions**: code-davinci-002, gpt-3.5-turbo, gpt-4, StarCoder; Spider (text-to-SQL), TransCoder (C++→Python translation), MBPP (text-to-Python).
- **Source**: Chen, Lin, Schärli, Zhou (Google DeepMind), "Teaching Large Language Models to Self-Debug," 2023, arXiv:2304.05128v2.
- **Quality tier**: primary
- **Quote**: "SELF-DEBUGGING improves sample efficiency, and can match or outperform baseline models that generate more than 10× candidate programs."
- **Confidence**: high (for the qualitative claim); the precise cost-per-marginal-solve curve is a GAP
- **Local path**: download/self-debugging-2023.pdf

