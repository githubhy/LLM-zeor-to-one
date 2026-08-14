# C3 — Evaluation & benchmarks (2025–26)

## Q1. The pass@k estimator, exactly

### Unbiased pass@k estimator (Codex paper, Eq. 1)
- **Claim**: Chen et al. (2021) define pass@k as the expected value, over problems, of the probability that at least one of k randomly chosen (without replacement) samples from n total generated samples passes the unit tests, and give a numerically stable unbiased estimator to compute it without enumerating all $\binom{n}{k}$ subsets.
- **Numbers**: n = 200 samples generated per task, k ≤ 100 (paper's evaluation range for pass@k reporting; HumanEval has 164 problems).
- **Conditions**: HumanEval (164 hand-written Python problems, avg 7.7 unit tests/problem), Codex model family (12M–12B params), nucleus sampling top-p=0.95, temperature swept (optimal T*=0.2 for pass@1, T*=0.8 for pass@100 on a 679M model).
- **Source**: Chen, Tworek, Jun, Yuan, et al. (OpenAI), "Evaluating Large Language Models Trained on Code," 2021, arXiv:2107.03374v2.
- **Quality tier**: primary
- **Quote**: "computing pass@k in this way can have high variance. Instead, to evaluate pass@k, we generate n ≥ k samples per task (in this paper, we use n = 200 and k ≤ 100), count the number of correct samples c ≤ n which pass unit tests, and calculate the unbiased estimator"
- **Confidence**: high
- **Local path**: download/chen-codex-evaluating-llms-code-2021.pdf

```
PASS@K ESTIMATOR (verbatim)

Definition (Section 2.1, Eq. 1), as printed:

    pass@k := E_Problems [ 1 - C(n-c, k) / C(n, k) ]

where the paper's own notation is:
    pass@k := \underset{\text{Problems}}{\mathbb{E}} \left[ 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}} \right]     (1)

Symbol definitions (verbatim from surrounding text, Section 2.1):
  n = total number of samples generated per task (paper uses n = 200)
  c = number of correct samples among the n, where c <= n, "which pass unit tests"
  k = the k in pass@k (paper evaluates k <= 100)
  C(n-c, k) i.e. \binom{n-c}{k} = number of size-k subsets of the n samples that
      contain ZERO correct samples (chosen from the n-c incorrect ones)
  C(n, k) i.e. \binom{n}{k}     = total number of size-k subsets of the n samples
  The fraction C(n-c,k)/C(n,k) is therefore the probability that a random
  size-k subset of the n samples contains no correct sample; 1 minus that is
  the probability at least one of the k samples is correct. The outer
  E_Problems averages this per-problem probability over the problem set.

Naive/biased alternative and why it is rejected (verbatim, Section 2.1):
  "One may be tempted to estimate pass@k with 1-(1-\hat p)^k where \hat p is
  the empirical estimate of pass@1, but we show that it is biased in
  Appendix A."
  (This is the naive "run k samples once, empirical pass-rate p-hat raised
  to a binomial-complement form" estimator; the paper shows it systematically
  over- or under-estimates the true pass@k because it does not account for
  sampling n>k draws WITHOUT replacement in a fixed pool of size n. The
  direct/naive way of computing pass@k -- i.e. literally drawing k samples
  per problem and checking if any pass -- "can have high variance" is the
  stated motivation (same paragraph) for using n>=k samples and the
  closed-form unbiased estimator above instead.)

Numerically stable implementation (Figure 3, verbatim as printed, a numpy
script the paper supplies to avoid computing the raw binomial-coefficient
ratio -- which "results in very large numbers and numerical instability" --
directly):

    def pass_at_k(n, c, k):
        """
        :param n: total number of samples
        :param c: number of correct samples
        :param k: k in pass@$k\$
        """
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

Caption (Figure 3, verbatim): "A numerically stable script for calculating
an unbiased estimate of pass@k."

Text immediately preceding Eq. 1 (verbatim, motivating context, Section 2.1):
  "To solve a problem in our test set, we generate multiple samples from the
  models, and check if any of them pass the unit tests. ... computing pass@k
  in this way can have high variance."
  And immediately after Eq. 1: "Calculating this estimator directly results
  in very large numbers and numerical instability. In Figure 3, we include a
  numerically stable numpy implementation that simplifies the expression and
  evaluates the product term-by-term."
```


## Q2. The SWE-bench family in 2026

### SWE-bench (original)
- **Claim**: The original SWE-bench collects real GitHub issue + PR pairs from 12 popular Python repositories, requiring a model to generate a patch that makes the repo's FAIL_TO_PASS tests pass without breaking PASS_TO_PASS tests.
- **Numbers**: 2,294 task instances (original full test set), 12 repositories, published ICLR 2024.
- **Conditions**: Python-only, repo-scale issue resolution, SWE-bench harness (Docker-based execution).
- **Source**: Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan, "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", ICLR 2024, arXiv:2310.06770.
- **Quality tier**: primary
- **Quote**: n/a (from search summary; local PDF download/swe-bench-2023.pdf available for direct verification of exact instance count in a follow-up pass)
- **Confidence**: medium (instance count from web search, not yet cross-checked against local PDF text in this session)
- **Local path**: download/swe-bench-2023.pdf (not opened this session — GAP, see below)

### SWE-bench Lite
- **Claim**: A 300-instance curated subset of the original test set, selected for self-contained functional bug fixes, used as a cheaper/faster proxy while retaining diversity across (11 of 12) repositories.
- **Numbers**: 300 task instances; as of ~Aug 2026 top public leaderboard score ~62.7% (Claude Opus 4.6) per pricepertoken.com leaderboard tracker.
- **Conditions**: Python, subset of original SWE-bench repos.
- **Source**: SWE-bench team (Princeton/Stanford — Jimenez et al. group), swebench.com / github.com/swe-bench/SWE-bench.
- **Quality tier**: strong-secondary (leaderboard number from a third-party tracker, not the primary paper)
- **Quote**: none (summarized)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED (variant-specific docs live on swebench.com, not in download/)

### SWE-bench Verified
- **Claim**: A 500-instance human-filtered subset created by OpenAI in collaboration with the SWE-bench authors; human annotators reviewed each instance for problem-statement clarity, correctness of the FAIL_TO_PASS test patch, and solvability, filtering out instances where an "ensemble label" of severity >= 2 flagged the problem statement or test patch as unreliable.
- **Numbers**: 500 instances (from original ~2,294); as of the OpenAI retirement announcement (2026), reported SOTA moved from 74.9% to 80.9% over roughly a 6-month window before OpenAI judged the benchmark saturated.
- **Conditions**: Python, same repos as original SWE-bench, human-verified subset, released August 2024.
- **Source**: OpenAI, "Introducing SWE-bench Verified," 2024, openai.com/index/introducing-swe-bench-verified/; OpenAI, "Why SWE-bench Verified no longer measures frontier coding capabilities," 2026, openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/.
- **Quality tier**: strong-secondary (official OpenAI blog posts, not peer-reviewed papers)
- **Quote**: "In an audit of a [subset of ~27.6%] of the dataset that models often failed to solve, OpenAI found that at least 59.4% of the audited problems have flawed test cases that reject functionally correct submissions." (paraphrase from search result summary of the OpenAI post; GAP — exact wording not verified against the primary page, only a search-engine synthesis)
- **Confidence**: medium (numbers consistent across multiple secondary write-ups of the same OpenAI post, but the OpenAI page itself was not directly fetched this session)
- **Local path**: NOT ACQUIRED

### SWE-bench Multimodal
- **Claim**: Extends the SWE-bench collection methodology to JavaScript/TypeScript repositories, selecting issues that include visual assets (screenshots, UI diagrams) so resolving them may require reasoning about images, not just text.
- **Numbers**: 510 task instances (evaluation set); integrated into the SWE-bench repo around January 2025.
- **Conditions**: JS/TS, visual-asset-bearing issues, tests multimodal (text+image) input handling by agents.
- **Source**: SWE-bench team, swebench.com (Multimodal track); GitHub swe-bench/SWE-bench repo.
- **Quality tier**: strong-secondary
- **Quote**: none (summarized)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Multi-SWE-bench (multilingual)
- **Claim**: A multilingual issue-resolving benchmark built by ByteDance Seed extending the SWE-bench task format across multiple programming languages beyond Python.
- **Numbers**: GAP — exact instance count and language list not verified this session (search snippet only surfaced the title/authorship, not the body numbers).
- **Conditions**: multi-language repo issue resolution.
- **Source**: ByteDance Seed, "Multi-SWE-bench: A Multilingual Benchmark for Issue Resolving," 2025, arXiv:2504.02605.
- **Quality tier**: primary (arXiv paper, not yet opened — treat numbers as GAP until fetched)
- **Quote**: none
- **Confidence**: low (title/venue only)
- **Local path**: NOT ACQUIRED

### SWE-bench Multilingual (SWE-bench-org variant, distinct from Multi-SWE-bench above)
- **Claim**: An official SWE-bench-org multilingual evaluation set covering 9 programming languages (JavaScript, TypeScript, C, C++, Go, Java, PHP, Ruby, Rust).
- **Numbers**: 300 task instances.
- **Conditions**: cross-language repo issue resolution, same collection methodology as original SWE-bench adapted per-language.
- **Source**: SWE-bench team, swebench.com (Multilingual track).
- **Quality tier**: strong-secondary
- **Quote**: none
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### SWE-bench Pro
- **Claim**: Scale AI's harder successor benchmark designed to be more contamination-resistant and to require substantially larger, longer-horizon changes than SWE-bench Verified; public set sourced from copyleft-licensed (e.g. GPL) repos specifically because strong copyleft license terms deter inclusion in commercial model-training corpora.
- **Numbers**: 1,865 total task instances (731 public + 858 held-out + 276 commercial) across 41 repositories (11 public, 12 held-out, 18 enterprise/startup); public-set tasks average 107.4 lines of code changed across 4.1 files; tasks framed as taking a professional engineer "hours to days."
- **Conditions**: Python, Go, JS/TS; long-horizon multi-file patches; three-tier split (public/held-out/commercial) specifically to manage contamination.
- **Source**: Scale AI, "SWE-Bench Pro: Can AI Agents Solve...", 2025, arXiv:2509.16941 (v2, Nov 2025).
- **Quality tier**: primary (arXiv paper; numbers from search synthesis of the paper, not yet directly opened this session — treat as medium confidence pending direct read)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### OpenAI's 2026 recommendation to move off SWE-bench Verified
- **Claim**: OpenAI publicly announced it would stop reporting SWE-bench Verified scores and recommended the industry adopt SWE-bench Pro instead, citing test-design flaws and saturation/contamination concerns; this recommendation was itself later partially retracted per a follow-up report.
- **Numbers**: SOTA on SWE-bench Verified moved from 74.9% to 80.9% "in the last 6 months" (as characterized by OpenAI, per secondary coverage) before being judged saturated; audit found >= 59.4% of a ~27.6% audited subset of hard problems had flawed tests rejecting correct submissions.
- **Conditions**: SWE-bench Verified, 500-instance set, frontier-model evaluation context, 2026.
- **Source**: OpenAI, "Why SWE-bench Verified no longer measures frontier coding capabilities," 2026, openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/; secondary corroboration: Investing.com, "OpenAI retracts SWE-Bench Pro coding benchmark recommendation," 2026; tessl.io blog, "OpenAI moves beyond SWE-bench Verified as coding benchmarks saturate," 2026.
- **Quality tier**: strong-secondary (official vendor blog; the retraction report is weaker-tier press coverage)
- **Quote**: none verbatim (GAP — WebFetch not spent on this page this session; recommend acquiring for a follow-up citation-audit pass)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Criticism: solution leakage and weak tests (SWE-Bench+)
- **Claim**: A systematic audit found a large fraction of SWE-bench "resolved" instances are resolved for reasons other than genuine capability: either the issue text/comments leak the solution, or the test suite is too weak to discriminate a correct patch from an incorrect one; filtering these out substantially drops measured agent performance.
- **Numbers**: 32.67% of successful patches show direct solution leakage; 31.08% pass due to inadequate test cases (per one framing); a stronger framing states 60.83% of "resolved" issues involve solution leakage where the solution was directly provided or indirectly hinted at in the issue/comments, and 47.93% of resolved issues are incorrectly marked resolved due to weak test cases. When these problematic instances are filtered out, three agents' resolution rate dropped from 42.1% to 21.8% (average) on SWE-bench Lite and from 51.7% to 25.9% (average) on SWE-bench Verified.
- **Conditions**: SWE-bench Lite and SWE-bench Verified, multiple unnamed agent systems, audit methodology using an LLM-based SolutionLeakDetector and TestEnhancer.
- **Source**: "SWE-Bench+: Enhanced Coding Benchmark for LLMs," OpenReview / arXiv:2410.06992, 2024/2025.
- **Quality tier**: primary (peer-reviewed venue submission / arXiv preprint; not yet directly opened this session)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium-high (numbers cross-corroborated across two independently-phrased search summaries of the same paper)
- **Local path**: NOT ACQUIRED

### Criticism: >15% of SWE-bench Verified instances need test augmentation
- **Claim**: A separate audit found over 15% of SWE-bench Verified instances require test-suite augmentation because the shipped test patches are incomplete and allow erroneous or partial model patches to pass the harness.
- **Numbers**: >15% of instances.
- **Conditions**: SWE-bench Verified (500-instance set).
- **Source**: likely "UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench," arXiv:2506.09289 (title suggests test-augmentation focus; GAP — attribution not directly confirmed by opening the paper this session, inferred from search context).
- **Quality tier**: primary (pending direct verification)
- **Quote**: none
- **Confidence**: low-medium (source attribution inferred, not confirmed)
- **Local path**: NOT ACQUIRED

### Criticism: flaky, non-deterministic test suites
- **Claim**: A measurable fraction of SWE-bench Lite problems have flaky test suites whose pass/fail outcome is not reproducible for a fixed candidate patch across repeated runs — flaky tests occasionally even mark the dataset's own gold/ground-truth solution as failing (e.g., issues involving unordered Python sets where the gold solution imposes explicit ordering but naive correct-looking model solutions don't, so they pass only on "lucky" runs).
- **Numbers**: 11.3% of SWE-bench Lite problems have flaky test suites.
- **Conditions**: SWE-bench Lite, repeated-sampling evaluation setting.
- **Source**: Brown, Juravsky, Ehrlich, et al., "Large Language Monkeys: Scaling Inference Compute with Repeated Sampling," 2024, arXiv:2407.21787.
- **Quality tier**: primary (arXiv preprint; not yet directly opened this session)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED


## Q3. Benchmarks beyond function-level code generation

| Benchmark | Task unit | Size | Metric | Contamination defence | Year | Source |
|---|---|---|---|---|---|---|
| LiveCodeBench | competitive-programming problem (code generation, self-repair, code execution, test-output prediction — 4 scenarios) | 500+ problems (as of the paper), collected continuously from LeetCode/AtCoder/CodeForces May 2023–May 2024 | pass@1 per scenario | Time-windowed collection: every problem is tagged with its original release date; evaluation can be restricted to a post-model-cutoff window so a model is only scored on problems released after its training cutoff | 2024 | Jain, Han, Gu, Li, Yan, Zhang, Wang, Solar-Lezama, Sen, Stoica, "LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code," arXiv:2403.07974v2 |
| BigCodeBench | function-call-composition task: implement a function that must correctly invoke a *sequence of diverse library function calls* (not just self-contained logic) to satisfy a complex natural-language instruction, verified by an average of 5.6 test cases per task at ~99% average branch coverage | 1,140 fine-grained tasks spanning 139 libraries and 7 domains; also a "BigCodeBench-Instruct" variant with docstrings automatically rewritten into short instructions | pass rate (execution-based); human ceiling reported as 97%, best LLMs up to ~60% | Not primarily a contamination-defence design; defends against a different failure mode — benchmark task realism/composability gap versus HumanEval/MBPP's short self-contained tasks | 2024 (ICLR 2025) | Zhuo, Vu, Chim, Hu, Yu, Widyasari, Yusuf, Zhan, He, Paul, Brunner, Gong, Hoang, Zebaze, Hong, Li, Kaddour, Xu, Zhang, Yadav, Jain, Gu, Cheng, Liu, Liu, Wang, Hui, Muennighoff, Lo, Fried, Du, de Vries, von Werra, "BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions," ICLR 2025, arXiv:2406.15877v4 |
| SWE-bench (family) | repo-scale GitHub issue -> patch (resolve real issue; FAIL_TO_PASS / PASS_TO_PASS tests) | 2,294 (original); 300 (Lite); 500 (Verified); 510 (Multimodal) | % resolved (patch makes FAIL_TO_PASS tests pass, PASS_TO_PASS tests still pass) | Weak/absent by default (sourced from popular public repos likely in pretraining data) — SWE-bench Pro addresses this with copyleft-only licensing to deter training inclusion, plus held-out/commercial splits | 2023-2024 (orig.); 2024-25 (variants) | Jimenez et al., ICLR 2024, arXiv:2310.06770 (see Q2 for variant sources) |
| SWE-bench Pro | repo-scale, long-horizon multi-file patch (professional-scale change, avg 107.4 LOC across 4.1 files) | 1,865 total (731 public + 858 held-out + 276 commercial) across 41 repos | % resolved | Public set restricted to strong-copyleft (e.g. GPL) licensed repos as a legal/practical deterrent against training-corpus inclusion; held-out and commercial splits never published | 2025 | Scale AI, "SWE-Bench Pro," arXiv:2509.16941v2 |
| SWE-Lancer | real Upwork freelance SE task, both individual implementation tasks and managerial (choose-the-best-proposal) tasks, graded by triple-verified end-to-end tests or against the real hired manager's decision | 1,400+ tasks, collectively valued at \$1M USD in real freelance payouts (individual task payouts ranged from \$50 bug fixes to \$32,000 feature implementations) | % tasks resolved and total dollar payout "earned" | Real, previously-unpublished freelance task corpus (Expensify-sourced); economic framing rather than an explicit decontamination mechanism | 2025 | OpenAI, "SWE-Lancer: Can Frontier LLMs Earn \$1 Million from Real-World Freelance Software Engineering?", arXiv:2502.12115 |
| Terminal-Bench | end-to-end terminal workflow (compiling, training a model, configuring a system, debugging an environment) executed inside a containerized Docker environment, graded by a programmatic verification test suite against a natural-language instruction and an oracle solution | 89 hand-crafted, human-verified tasks (v1.0, May 2025); Terminal-Bench 2.0 released Nov 2025 raising difficulty pre-emptively | task success rate | Hand-crafted novel tasks (not scraped from a public corpus of solved problems); v2.0 explicitly built to front-run saturation of v1.0 | 2025 | tbench.ai, "Introducing Terminal-Bench," 2025 (project site; primary paper GAP — not located this session) |
| Aider Polyglot | code-editing exercise across 6 languages (C++, Go, Java, JavaScript, Python, Rust), 2 attempts allowed (first attempt, then a retry after seeing failing unit-test output) — tests both raw problem-solving AND the model's ability to apply a code edit in the target format | 225 problems, hand-selected as the hardest from a pool of 697 Exercism problems (kept only problems that >=5 of 7 baseline frontier models failed on) | % problems solved (within 2 attempts); separately, an "edit format" compliance metric | Selection-for-difficulty against contemporary frontier models substitutes for an explicit time-window defence; problems sourced from Exercism (public), so not contamination-proof by construction | Dec 2024 | Paul Gauthier / Aider, "o1 tops aider's new polyglot leaderboard," aider.chat/2024/12/21/polyglot.html; dataset at github.com/Aider-AI/polyglot-benchmark |

### LiveCodeBench — contamination-free-by-design
- **Claim**: LiveCodeBench continuously collects new competitive-programming problems from LeetCode, AtCoder, and CodeForces, timestamps each with its original release date, and evaluates models only on problems released after the model's training cutoff to make a fair, contamination-controlled comparison; it also broadens the task beyond code generation to self-repair, code execution, and test-output prediction.
- **Numbers**: hosts >500 coding problems published between May 2023 and May 2024 at time of the paper; 18 base LLMs and 34 instruction-tuned LLMs evaluated.
- **Conditions**: LeetCode/AtCoder/CodeForces sourced problems; pass@1 metric; time-windowed evaluation (e.g. post-Sept-2023 or post-Nov-2023 windows used in the paper to fairly compare DeepSeek-Instruct-33B, GPT-4, GPT-4-O, Gemini-Flash-1.5).
- **Source**: Jain, Han, Gu, Li, Yan, Zhang, Wang, Solar-Lezama, Sen, Stoica (UC Berkeley/MIT/Cornell), "LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code," 2024, arXiv:2403.07974v2.
- **Quality tier**: primary
- **Quote**: "Live updates to prevent contamination. LLMs are trained on massive inscrutable corpora, and current benchmarks suffer from the risk of data contamination as they could be included in those training datasets."
- **Confidence**: high
- **Local path**: download/livecodebench-2024.pdf

### BigCodeBench — function-call composition, not contamination-focused
- **Claim**: BigCodeBench targets a different gap than contamination — it argues HumanEval/MBPP-style benchmarks are saturated AND unrealistic because real programming requires composing diverse library function calls under complex natural-language instructions, not writing short self-contained algorithms; it reports LLMs are "not yet capable of following complex instructions to use function calls precisely," topping out around 60% versus a 97% human baseline.
- **Numbers**: 1,140 tasks, 139 libraries, 7 domains, 5.6 average test cases per task, ~99% average branch coverage; 60 LLMs evaluated; best-LLM score up to 60% vs. human 97%.
- **Conditions**: Python, execution-based grading, both a docstring-style and an instruction-style ("BigCodeBench-Instruct") task variant.
- **Source**: Zhuo et al. (Monash, CSIRO Data61, and a large multi-institution author list including MIT, UC Berkeley, CMU, Hugging Face), "BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions," ICLR 2025, arXiv:2406.15877v4.
- **Quality tier**: primary
- **Quote**: "LLMs are not yet capable of following complex instructions to use function calls precisely, with scores up to 60%, significantly lower than the human performance of 97%."
- **Confidence**: high
- **Local path**: download/bigcodebench-2024.pdf

### SWE-Lancer — economic-value framing
- **Claim**: SWE-Lancer grades models on real, previously-priced Upwork freelance software-engineering tasks (sourced via Expensify), scoring both raw resolution rate and the total dollar amount of freelance payout a model could "earn"; it includes both hands-on implementation tasks and higher-level managerial tasks where a model must select the best of several competing technical proposals.
- **Numbers**: 1,400+ tasks; ~\$1M USD total real-world payout value; individual task payouts from \$50 to \$32,000; GPT-4o completes about 40% of tasks (per secondary source, not yet directly verified against the paper).
- **Conditions**: real Upwork/Expensify freelance tasks, end-to-end tests triple-verified by experienced engineers for individual tasks; managerial tasks graded against the real hiring manager's actual decision.
- **Source**: OpenAI, "SWE-Lancer: Can Frontier LLMs Earn \$1 Million from Real-World Freelance Software Engineering?", 2025, arXiv:2502.12115.
- **Quality tier**: primary (arXiv preprint; not yet opened directly this session — GAP for exact quotes)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Terminal-Bench — end-to-end terminal-workflow agent tasks
- **Claim**: Terminal-Bench evaluates agents on complete terminal workflows (compiling, training, configuring, debugging) inside a Docker container, each task specified by an instruction + environment + programmatic test suite + oracle solution; version 2.0 was released specifically to pre-empt saturation of version 1.0 after rapid frontier-lab adoption.
- **Numbers**: 89 hand-crafted human-verified tasks in v1.0 (May 2025); v2.0 released November 2025.
- **Conditions**: Docker-containerized execution context; task success is a binary pass/fail against the verification suite.
- **Source**: tbench.ai project site, "Introducing Terminal-Bench," 2025; corroborated in later arXiv papers citing it as "the standard benchmark for evaluating agents in terminal environments" (e.g. arXiv:2602.21193, "On Data Engineering for Scaling LLM Terminal Capabilities").
- **Quality tier**: strong-secondary (project announcement page; the benchmark's own founding paper was not directly located/opened this session — GAP)
- **Quote**: none verbatim
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Aider Polyglot — multi-language code-editing benchmark, difficulty-selected
- **Claim**: Aider Polyglot replaced Aider's original Python-only 133-exercise benchmark (saturated, Claude 3.5 Sonnet at 84.2%) with a harder, 6-language, 225-problem set drawn from the hardest Exercism exercises — specifically those that at least 5 of 7 baseline frontier models failed to solve — to restore differentiation between frontier models and to explicitly probe both raw problem-solving and code-edit-format compliance (2 attempts per problem, second attempt shown failing test output).
- **Numbers**: 225 problems selected from a pool of 697 Exercism problems, across C++, Go, Java, JavaScript, Python, Rust; 2 attempts per problem.
- **Conditions**: code-editing task (not fresh generation) — a model must correctly locate and apply diffs/edits in its designated edit format, not just produce correct logic.
- **Source**: Paul Gauthier (Aider creator), "o1 tops aider's new polyglot leaderboard," aider.chat, Dec 21 2024; dataset released at github.com/Aider-AI/polyglot-benchmark.
- **Quality tier**: strong-secondary (project blog + open dataset repo, not a peer-reviewed paper)
- **Quote**: none verbatim (search-summarized)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED


## Q4. Contamination, saturation, and reporting statistics

### (a) Evidence of contamination — HumanEval/MBPP found substantially present in pretraining corpora
- **Claim**: A Yale NLP study built a pipeline combining surface-level (string/edit-distance) and semantic-level (AST-based similarity) matching to exhaustively search for HumanEval/MBPP gold-solution matches inside large code pretraining corpora (The Pile, The Stack), and found substantial contamination even though The Stack had already gone through a string-matching-based decontamination step for these exact benchmarks.
- **Numbers**: 12.2% of HumanEval samples found present in The Pile and 18.9% in The Stack under string-matching-based detection; under the paper's own similarity-score methodology, 50.8% of Stack code samples reach >80 similarity score against MBPP gold solutions and 63.4% reach >80 similarity against HumanEval gold solutions; separately, a leakage-detection tool found 65.4% of MBPP test-set instances contaminated (figure sourced from a related citing work, not necessarily identical methodology — flagged for follow-up verification).
- **Conditions**: HumanEval (164 problems) and MBPP, checked against The Pile and The Stack pretraining corpora; despite The Stack's own prior string-based decontamination pass for these benchmarks.
- **Source**: (Yale NLP), "Quantifying Contamination in Evaluating Code Generation Capabilities of Language Models," ACL 2024 (long paper), arXiv:2403.04811.
- **Quality tier**: primary (ACL 2024 peer-reviewed; paper itself not yet directly opened this session — GAP, numbers from search-engine synthesis of the paper/its citations, recommend direct-read verification before final survey citation)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium (multiple independent secondary summaries converge on the 12.2%/18.9% figures, but the 65.4% MBPP figure appears attributed to a different/related tool in a citing paper and needs disambiguation)
- **Local path**: NOT ACQUIRED

### (a) Decontamination method: time-windowed collection (LiveCodeBench)
- **Claim**: LiveCodeBench's central contamination defense is not a similarity-matching filter but a design choice: continuously collect new problems, timestamp each with true release date, and only compare a model against problems released strictly after that model's training-data cutoff — sidestepping the arms race between contamination-detection and paraphrase-evasion entirely.
- **Numbers**: paper explicitly shows DeepSeek-Instruct-33B and GPT-4-O "perform considerably worse on problems released since September and November 2023" respectively (their release/cutoff dates) — direct empirical evidence of contamination effects on the *earlier* problem window for those two models.
- **Conditions**: LeetCode problems, May 2023–Feb 2024 release window, pass@1, code-generation and test-generation scenarios.
- **Source**: Jain et al., "LiveCodeBench," arXiv:2403.07974v2 (already cited in Q3).
- **Quality tier**: primary
- **Quote**: "While previous works have attempted decontamination using both exact and fuzzy matches..., it can be a non-trivial task ... and can be evaded with simple strategies like rephrasing... Notice that DeepSeek-Instruct-33B and GPT-4-O perform considerably worse on problems released since September and November 2023 (their release and cutoff dates respectively!) -- indicating potential contamination for the earlier problems."
- **Confidence**: high
- **Local path**: download/livecodebench-2024.pdf

### (a) Decontamination method landscape (general survey of techniques)
- **Claim**: Beyond time-windowing, the field uses several other decontamination approaches for code specifically: n-gram overlap (e.g. 50-gram matching against the Stack), hash-based/exact string filtering, embedding-based semantic similarity search, LLM-based paraphrase-robust detectors (the "LLM Decontaminator"), and — a code-specific mitigation rather than detection method — code refactoring (restructuring + variable renaming) applied to benchmark problems to break memorized surface forms.
- **Numbers**: none single-sourced; general survey-level claim compiled from search summaries across several papers (GAP — needs consolidation to one or two primary sources before citing directly in survey prose).
- **Conditions**: general code-LLM contamination-detection literature, not one benchmark.
- **Source**: multiple (search-synthesized; candidates include "LLM Benchmark Datasets Should Be Contamination-Resistant" arXiv:2605.19999, "CodeCleaner: Mitigating Data Contamination for LLM Benchmarking" (Internetware 2025/26), "Rethinking Benchmark and Contamination for Language Models with Rephrased Samples" arXiv:2311.04850).
- **Quality tier**: weak (survey-of-search-results only; none of these papers opened directly this session)
- **Quote**: none
- **Confidence**: low
- **Local path**: NOT ACQUIRED

### (a) Saturation evidence — SWE-bench Verified and Aider's original benchmark
- **Claim**: Both SWE-bench Verified and Aider's original Python-only 133-exercise benchmark are documented cases of benchmark saturation prompting the maintainers to retire or replace the benchmark: Aider's original benchmark reached 84.2% (Claude 3.5 Sonnet) and was replaced by Aider Polyglot; SWE-bench Verified moved from 74.9% to 80.9% SOTA over roughly 6 months before OpenAI publicly announced it no longer measures frontier capability and recommended SWE-bench Pro instead (see Q2 for full detail and sourcing).
- **Numbers**: see Q2 records ("SWE-bench Verified" and OpenAI 2026 recommendation entries) and Q3 Aider Polyglot entry.
- **Conditions**: as detailed in those entries.
- **Source**: see Q2/Q3 cross-references above.
- **Quality tier**: strong-secondary
- **Quote**: n/a (cross-reference)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### (b) Reporting practice — single-run, no-CI is common; some report average@k without CIs
- **Claim**: A body of methodology-critique papers converges on the same finding: many agentic-coding/agent benchmarks report a single run per agent per task with no confidence interval, standard error, or replication; where variance-reduction is attempted at all, it is often an "average@k" (e.g. k=3) mean over a handful of repeated runs, again without an accompanying confidence interval or significance test.
- **Numbers**: no single quantitative summary located this session (e.g. "N% of papers report a CI") — GAP; the audit paper below is the closest to a quantified answer but scores *disclosure* broadly, not narrowly the CI question.
- **Conditions**: general finding across multiple agent/agentic-coding benchmark methodology-critique papers, 2025-2026.
- **Source**: multiple, search-synthesized: "Stochasticity in Agentic Evaluations: Quantifying Inconsistency with Intraclass Correlation," arXiv:2512.06710; "Do Agent Benchmarks Measure Capability? Protocol Validity in the Age of Agentic AI," arXiv:2607.22368 (proposes the "ABC checklist" for task/outcome validity and transparent reporting, explicitly including CIs and baseline statistics as a checklist item); "The AI Benchmark Illusion: Why Your Agent's Test Scores Mean Nothing" (Medium, weak tier).
- **Quality tier**: strong-secondary for the arXiv items (not yet directly opened this session — GAP, recommend direct read before final citation), weak for the Medium post
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### (b) Reporting practice audit — quantified disclosure gap across 8 agent-benchmark papers
- **Claim**: A pilot audit of twelve canonical LLM-agent-benchmark papers (eight agentic, four classical/static) scored each paper's self-disclosure across five dimensions (benchmark identity, harness specification, inference settings, cost reporting, failure breakdown) on a 0-1 scale. Agent-benchmark papers disclosed substantially less than classical static benchmarks, and every zero-score was an *omission*, not a misstatement — the paper argues the fix is instrumenting the eval harness to auto-emit disclosures, not stricter review.
- **Numbers**: mean audit-disclosure score 0.38/1.0 across the 8 agent-benchmark papers vs. 0.66/1.0 across the 4 classical static benchmarks; the single largest gap category was cost — none (0/8) of the agent-benchmark papers disclosed inference cost in any form.
- **Conditions**: 12 canonical benchmark papers audited (8 agentic, 4 classical/static); five-dimension disclosure schema.
- **Source**: "What Twelve LLM Agent Benchmark Papers Disclose About Themselves: A Pilot Audit and an Open Scoring Schema," 2026, arXiv:2605.21404.
- **Quality tier**: primary (arXiv preprint; not yet directly opened this session — GAP for exact quotes and which 8/4 papers were in-scope)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium-high (directly on-topic for the survey's "does the field report CIs honestly" question)
- **Local path**: NOT ACQUIRED

### (b) A rigorous counter-example: Wilson-score + hierarchical bootstrap for stateful agent evals
- **Claim**: A methodology paper on Computer Use Agent (CUA) evaluation — a sibling domain to agentic coding, not code-specific — demonstrates that naive metric reuse from static code-gen benchmarks is actively misleading for stateful, multi-step agent tasks: it shows a "blind replay script" that never observes the screen can outperform frontier models on prominent static benchmarks, attributes this to non-principled environment design and to "misuse of pass@k for stateful UI interactions" (pass@k assumes independent, resample-able candidate artifacts; an agent rollout is a stateful execution trajectory, not a resample-able candidate). It proposes an aggregation framework pairing Wilson score confidence intervals with hierarchical bootstrap to correctly account for the benchmark's nested structure (tasks nested in configurations nested in environments).
- **Numbers**: benchmark introduced (DIGIWORLD) covers 15 realistic sandboxed mobile applications with >3.2 million verified unique configurations; exact quantitative gap between blind-replay-script and frontier-model performance not captured this session (GAP).
- **Conditions**: Computer-Use-Agent (GUI/mobile) evaluation, not code-agent evaluation directly — cited here as the most methodologically rigorous statistical treatment found in the adjacent agentic-eval literature, and directly transferable reasoning to agentic coding evals (an agent's SWE-bench trajectory is likewise a stateful execution, not an i.i.d. resample).
- **Source**: "Computer Use at the Edge of the Statistical Precipice," 2026, arXiv:2605.08261 (title deliberately echoes Agarwal et al., "Deep Reinforcement Learning at the Edge of the Statistical Precipice," NeurIPS 2021, arXiv:2108.13264 — the RL-benchmark statistical-rigor paper this lineage is built on).
- **Quality tier**: primary (arXiv preprint; not yet directly opened this session — GAP)
- **Quote**: "misuse of pass@k for stateful UI interactions" (paraphrase-level, from search synthesis — GAP, verbatim quote not yet confirmed against the PDF)
- **Confidence**: medium (highly relevant methodological point, but domain is CUA not code — must be clearly scoped as an analogy, not direct code-agent evidence, in survey prose)
- **Local path**: NOT ACQUIRED

### (b) Explicit good-practice example located
- **Claim**: At least one benchmark/evaluation write-up located in this search computes its headline metrics over 3 independent runs per model and reports 95% percentile bootstrap confidence intervals using 1,000 resamples over the (problems x runs) grid — cited by a search-engine synthesis as a positive counter-example to the single-run norm.
- **Numbers**: 3 independent runs per model; 95% CI; 1,000 bootstrap resamples.
- **Conditions**: unspecified in the search snippet which benchmark this describes — GAP, source paper/benchmark name not captured by the search summary.
- **Source**: GAP — could not attribute to a specific paper from the search snippet alone; flagged for a follow-up targeted search or WebFetch.
- **Quality tier**: weak (unattributed)
- **Quote**: none
- **Confidence**: low
- **Local path**: NOT ACQUIRED


### (b) UPDATE — attribution found for the "3-runs + bootstrap CI" good-practice example
- **Claim**: Follow-up search attributes the good-practice pattern above to (most likely) "DeepSWE: Measuring Frontier Coding Agents on Original, Long-Horizon Engineering Tasks," which reports results from four product configurations with three independent runs each (300 scored rollouts total), pass@1 with task-level 95% confidence intervals, run-level scores, and paired bootstrap comparisons; separately, for each task pass@k is computed from the 3 runs via the Codex paper's own unbiased combinatorial estimator (Q1 above), then bootstrapped over the cross-task mean to get a CI that reflects task-level variance. A practitioner-facing methodology explainer (Indeed Engineering Blog, July 2026) independently recommends exactly this recipe as general good practice for LLM eval: run each of N inputs k times (k=3 or 5), bootstrap-resample inputs with replacement carrying all k runs per resampled input, recompute the metric per resample, take the 2.5th/97.5th percentiles as the 95% interval.
- **Numbers**: 4 configurations x 3 runs = 300 scored rollouts (in the DeepSWE-attributed benchmark); recommended k=3 or 5 runs per input (Indeed blog).
- **Conditions**: agentic coding-agent evaluation (long-horizon engineering tasks); the estimator explicitly reuses Chen et al. 2021's unbiased pass@k formula (Q1) at the per-task level, then adds a second bootstrap layer across tasks — a two-level variance treatment.
- **Source**: "DeepSWE: Measuring Frontier Coding Agents on Original, Long-Horizon Engineering Tasks," 2026, arXiv:2607.07946 (attribution probable but not confirmed by direct read — GAP); Indeed Engineering Blog, "Bootstrap Confidence Intervals for LLM Evaluation," 2026, engineering.indeedblog.com.
- **Quality tier**: primary for DeepSWE (pending direct confirmation), careful-explainer for the Indeed blog (practitioner content, not peer-reviewed, but methodologically sound and specific)
- **Quote**: none verbatim yet (GAP)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

## Gaps

- Q1: fully resolved from primary source, high confidence. No gaps.
- Q2: original SWE-bench instance count (2,294) and the exact wording of the OpenAI "why we no longer evaluate SWE-bench Verified" post were not verified against primary sources this session (only search-engine synthesis of secondary write-ups) — `download/swe-bench-2023.pdf` exists locally and was NOT opened this session; recommend a follow-up pass reading it directly, plus WebFetch of the OpenAI blog post itself, before any number here is treated as final in survey prose.
- Q2: Multi-SWE-bench (ByteDance, arXiv:2504.02605) numbers are a placeholder (title/venue only) — needs a direct read.
- Q2: UTBoost (arXiv:2506.09289) attribution for the ">15% of SWE-bench Verified instances need test augmentation" claim is inferred from title relevance, not confirmed by reading the paper — flagged low-medium confidence, needs direct verification.
- Q3: SWE-Lancer (arXiv:2502.12115) and Terminal-Bench founding paper not directly opened — GPT-4o "~40%" figure is medium confidence (secondary source only).
- Q3: Terminal-Bench's own arXiv paper (as opposed to the project announcement page) was not located this session — GAP, may need a more targeted search (e.g. "Terminal-Bench: A Benchmark for AI Agents in Terminal Environments" or similar canonical title).
- Q4a: the Yale contamination paper (arXiv:2403.04811) numbers were not verified by direct read; the 65.4% MBPP figure in particular looks like it may come from a *different* tool/paper than the 12.2%/18.9% Pile/Stack figures and needs disambiguation before citing both in the same sentence.
- Q4a: general decontamination-method survey paragraph is weak-tier (search-synthesized across several unread papers) — needs consolidation to 1-2 directly-read primary sources.
- Q4b: no single paper was found that quantifies "what fraction of agentic coding-eval papers report a CI at all" — the closest is the 12-paper disclosure audit (arXiv:2605.21404), which scores broader methodological disclosure, not narrowly CI-reporting. This is itself worth stating explicitly in survey prose: the literature diagnoses the *problem* (single-run, no-CI is common) more than it *quantifies* it.
- None of the ten arXiv papers newly surfaced this session (SWE-Bench+, SWE-Bench Pro, SWE-Lancer, Multi-SWE-bench, UTBoost, the Yale contamination paper, the 12-paper disclosure audit, the intraclass-correlation stochasticity paper, the ABC-checklist protocol-validity paper, the Computer-Use statistical-precipice paper, DeepSWE) were acquired into `download/` this session — all currently NOT ACQUIRED. A `source-fetch` pass to acquire the highest-value subset (SWE-Bench+, SWE-Bench Pro, the Yale contamination paper, and the 12-paper disclosure audit) would materially raise confidence before this evidence is written into survey prose.

## Corrections to the brief

- The brief's suggested benchmark list for Q3 (LiveCodeBench, BigCodeBench, SWE-Lancer, Terminal-Bench, Aider polyglot) is confirmed as a reasonable and current set; no correction needed. One addition worth folding into the survey beyond the brief's list: **SWE-bench Pro** (Scale AI, arXiv:2509.16941) is a 2025 benchmark specifically engineered to be contamination-resistant (copyleft-only public set) and is now OpenAI's own recommended SWE-bench successor as of the 2026 retirement of SWE-bench Verified — this is a load-bearing fact for the "SWE-bench family in 2026" question (Q2) that the brief did not explicitly name but that dominates the current-state answer.
- The brief characterizes Q1 as "the single highest-value item in your cluster" — confirmed correct; the primary source cleanly answers it in full (exact equation, exact numpy implementation, exact n/k values, and the explicit statement of why the naive 1-(1-p_hat)^k estimator is biased, with the bias proof deferred to the paper's Appendix A, which was not read this session — GAP if the survey wants the appendix-level proof itself, not just the citation to its existence).
- No other factual corrections to the brief were found; the brief's unverified priors about which benchmarks exist and roughly what they test were directionally accurate.

## Sources worth acquiring

Priority order for a `source-fetch` follow-up, ranked by how load-bearing each is for cluster C3's eventual survey prose:

1. Chen et al., Codex paper — already local (`download/chen-codex-evaluating-llms-code-2021.pdf`); also fetch **Appendix A** content (already in the same PDF, pages beyond what was read this session) for the naive-estimator bias proof if the survey appendix wants to show it.
2. "SWE-Bench+: Enhanced Coding Benchmark for LLMs," arXiv:2410.06992 — the strongest, most-quantified criticism source for Q2.
3. Scale AI, "SWE-Bench Pro," arXiv:2509.16941 — now the field's recommended SWE-bench successor; central to Q2's "2026 state" answer.
4. Yale NLP, "Quantifying Contamination in Evaluating Code Generation Capabilities of Language Models," ACL 2024 / arXiv:2403.04811 — central to Q4a; numbers currently unverified.
5. "What Twelve LLM Agent Benchmark Papers Disclose About Themselves," arXiv:2605.21404 — central to Q4b's honest-reporting-practice answer; the 0.38 vs 0.66 disclosure-score finding is a strong, quotable statistic once verified.
6. SWE-bench original paper — already local (`download/swe-bench-2023.pdf`) but not opened this session; open it to verify the 2,294-instance count and original methodology directly rather than via secondary sources.
7. OpenAI, "Why SWE-bench Verified no longer measures frontier coding capabilities" (2026 blog post) — not a PDF-fetchable arXiv paper, but worth a direct WebFetch/archival capture given how load-bearing it is for the "2026 state of SWE-bench" narrative.
8. livecodebench-2024.pdf and bigcodebench-2024.pdf — already local and directly read this session; no further acquisition needed.
