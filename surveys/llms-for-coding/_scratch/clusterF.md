# Cluster F — Tradeoffs, SOTA & Practice, Safety/Security/Licensing, Design Guidance, Roadmap

Evidence collected 2026-06-13. Covers §14–§18. PDFs verified with pymupdf; SOTA numbers are date-stamped and recency-flagged.

**RECENCY WARNING (applies to all SOTA claims below).** LLM-for-code leaderboards go stale in weeks. Several 2026 web leaderboards surfaced model names that look fictional / unverifiable (e.g. "Claude Mythos", "Claude Fable 5", "DeepSeek-V4-Pro-Max", "Claude Opus 4.8") alongside credible late-2025 entries. Treat any single web leaderboard number as a dated snapshot, not ground truth, and prefer the credible *band* (frontier SWE-bench Verified ~80–81% late-2025) over a specific headline. Primary model reports should replace these before survey sign-off.

---

### Q1: Compute/cost/latency tradeoffs (model-size vs capability, open vs frontier, autocomplete latency vs agent throughput, USD/task economics, test-time compute)

- **Findings**:
  - **Model-size vs capability (MoE efficiency, open-weight).** DeepSeek-Coder-V2 (June 2024) is an MoE with **236B total / 21B active** params and a **16B total / 2.4B active** "Lite" variant; supports **338 programming languages** and **128K context** (abstract + §1.1 Contributions, p.1-2, deepseek-coder-v2-2024.pdf). The Lite (2.4B active) matches DeepSeek-Coder-Base **33B** on Python completion and **7B** on Java completion — i.e. MoE activation sparsity buys ~10x effective param reduction at iso-capability for completion ("active parameters … comparable to DeepSeek-Coder-Base 33B model" passage). This is the canonical open-weight-vs-frontier datapoint: V2 is explicitly framed as "Breaking the Barrier of Closed-Source Models," reaching GPT-4-Turbo-comparable code performance with open weights (title + abstract).
  - **Cost-per-task economics of agentic coding (concrete numbers).** On a SWE-bench-Verified-Mini cost-vs-accuracy leaderboard: **GPT-5 Medium (Aug 2025): 46% accuracy for USD 162.93 per 50-task run** (approx USD 3.26/task); **Gemini 2.0 Flash (Feb 2025): 24% accuracy for USD 4.72 per 50-task run** (approx USD 0.09/task) (web, morphllm / artificialanalysis coding-agents, snapshot 2026). The two-order-of-magnitude cost-per-task spread at a ~2x accuracy spread is the headline tradeoff: frontier agentic runs cost ~30–40x more per task than cheap models for roughly double the solve rate.
  - **Test-time / inference-time compute.** Test-time-compute orchestration for SWE-bench is an active area: accuracy is now reported *against a max-cost constraint in USD/item* (x-axis), i.e. the Pareto frontier is cost-vs-solve-rate, not raw solve-rate (web, ai21.com/blog/test-time-compute-swe-bench). Implication for the survey: agentic solve-rate gains are increasingly bought with more inference passes (multi-sample, self-repair loops), so cost-per-task and latency rise super-linearly near the frontier.
  - **Autocomplete latency vs agent throughput (qualitative).** Survey framing: autocomplete (IDE inline completion) is latency-bound (sub-100ms expectation, favors small/fast models), whereas agentic SWE is throughput/total-cost-bound (favors large models + many inference passes). No single hard latency number sourced to a primary report — see Gaps.
- **Sources**:
  - Zhu, Guo, Shao et al., "DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence," 2024 — (local: download/deepseek-coder-v2-2024.pdf)
  - SWE-bench-Verified-Mini cost/accuracy figures; test-time-compute Pareto framing — (web: morphllm.com/best-ai-model-for-coding, artificialanalysis.ai/agents/coding-agents, ai21.com/blog/test-time-compute-swe-bench; snapshot 2026-06)
- **Confidence**: medium-high for DeepSeek-Coder-V2 specs (primary PDF); medium for cost-per-task numbers (single dated web leaderboard, plausible magnitudes); low for autocomplete latency (no primary number).
- **Gaps**: No primary-sourced autocomplete latency (ms) number — Cursor/Copilot inline-completion latency is usually only in vendor blogs. No primary cost-per-task from a model card. Recommend main thread source one autocomplete latency figure and one vendor-reported agentic-run cost.

---

### Q2: Current SOTA & deployment, date-stamped (frontier vs open-weight on SWE-bench Verified & LiveCodeBench; what is DEPLOYED)

- **Findings**:
  - **SWE-bench Verified, late-2025 frontier band (CREDIBLE):** **Claude Opus 4.5 ≈ 80.9%** and **Gemini 3 Pro ≈ 80.6%** (web, theunwindai.com + llm-stats, dated late-2025). This is the defensible "frontier ~80–81%" anchor. **Contamination caveat (important):** reporting indicates every major frontier model could reproduce verbatim gold patches for some SWE-bench Verified tasks because the 500 Python tasks predate benchmark publication and appear in training data — so headline ~80% scores carry a documented contamination asterisk (web, multiple 2026 leaderboard analyses). Higher 2026 numbers (90%+) are sourced only to leaderboards listing unverifiable/likely-fictional model names — FLAGGED, do not cite as fact.
  - **SWE-bench Verified historical anchor (PRIMARY, for the progression curve):** DeepSeek-Coder-V2 scored **SWE-Bench 12.7**, **LiveCodeBench 43.4**, HumanEval 90.2, MBPP+ 76.2 (Figure 1, p.2, deepseek-coder-v2-2024.pdf; June 2024). The jump from ~13% (mid-2024 open model) to ~80% (late-2025 frontier agents) on SWE-bench Verified is the single most vivid "eval-progression / saturation" datapoint and IS primary-sourced on the 2024 end.
  - **LiveCodeBench frontier (web, 2026 snapshot):** Gemini 3 Pro Preview ≈ 91.7%, Gemini 3 Flash (Reasoning) ≈ 90.8%, DeepSeek V3.2 ≈ 89.6% (web, artificialanalysis.ai/evaluations/livecodebench). LiveCodeBench is explicitly contamination-resistant (fresh LeetCode/AtCoder/Codeforces problems released after training cutoffs), so its numbers are more trustworthy than SWE-bench for raw capability — but the *specific* model names are again partly unverifiable; treat the ~90% frontier band as the claim.
  - **What is DEPLOYED (production patterns):** Three deployment modes are live and documented: (1) **IDE inline autocomplete** (GitHub Copilot, latency-bound); (2) **chat/assistant**; (3) **autonomous agents**. OWASP's 2026 tracking notes the five fastest-growing agentic tools are **Claude Code, Gemini CLI, Codex, Cline, and Aider**, and 28/53 tracked agentic projects are coding agents (web, helpnetsecurity 2026-06-11) — i.e. agentic coding is now the dominant deployed agentic category.
- **Sources**:
  - DeepSeek-Coder-V2 Figure 1 (SWE-Bench 12.7 / LiveCodeBench 43.4, June 2024) — (local: download/deepseek-coder-v2-2024.pdf)
  - Late-2025 frontier band (Opus 4.5 80.9%, Gemini 3 Pro 80.6%) + contamination caveat — (web: theunwindai.com/p/claude-opus-4-5-scores-80-9-on-swe-bench, llm-stats.com/benchmarks/swe-bench-verified; dated late-2025)
  - LiveCodeBench ~90% frontier band — (web: artificialanalysis.ai/evaluations/livecodebench; snapshot 2026)
  - Deployed agentic-tool landscape — (web: helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures; 2026-06-11)
- **Confidence**: high for the 2024 primary anchor and for the existence of the contamination caveat; medium for the late-2025 ~80% band (credible, web-only); low for any specific 2026 model name above ~81% SWE-bench.
- **Gaps**: No primary model-card PDF for the late-2025 frontier scores (Anthropic/Google system cards would be the strong source). Main thread should replace web leaderboard numbers with primary system-card numbers before sign-off.

---

### Q3: Security — insecure code generation, secure-code eval, malware/dual-use, prompt injection in agentic coding

- **Findings**:
  - **Pearce et al. "Asleep at the Keyboard" (exact figures + setup):** Assessed GitHub Copilot (Codex-family backend). **Setup:** authors built **89 distinct scenarios** spanning MITRE "Top 25" CWEs across three axes (diversity of weaknesses, of prompts, of domains), producing **1,689 programs**. **Headline:** "we found **approximately 40%** to be vulnerable" (abstract, p.1). More precisely: **39.33% of the top-ranked suggestions** and **40.73% of total options** were vulnerable (Results, p.~6/§ near offset, asleep-at-keyboard-2021.pdf). Authors note the top suggestion's security matters most because "novice users may have more confidence to accept the 'best' suggestion." (verbatim).
  - **Memorization angle (links to Q4):** Pearce theorizes the variable security stems from the nature of community-contributed GitHub training code.
  - **Malware / dual-use & prompt injection in agentic coding (web, 2025–2026):** Documented, active threat class. **Indirect prompt injection** is the dominant agentic-coding attack vector: untrusted repo content — issue titles, PR descriptions, code comments, commit messages, external docs/API responses — gets interpolated into the agent's prompt and treated as trusted instructions (web, securecodewarrior.com; cloudsecurityalliance lab note on Claude Code GitHub Action). Consequence amplifier: agents granted broad workflow permissions (`id-token: write`, `contents: write`) turn a successful injection into OIDC token theft / direct repo writes (web, CSA lab note). OWASP (2026-06): prompt injection still drives most agentic-AI security failures in production; production systems from Microsoft, Google, GitHub, OpenAI all exploited via prompt injection in 2025–2026 (web, helpnetsecurity 2026-06-11). Academic corroboration exists (arXiv 2603.21642 "Are AI-assisted Development Tools Immune to Prompt Injection?"; arXiv 2509.05372 "Adversarial Bug Reports … in LLM-Based Automated Program Repair") — not fetched as PDF, cite as web/abstract if used.
- **Sources**:
  - Pearce, Ahmad, Tan, Dolan-Gavitt, Karri, "Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code Contributions," 2021 (IEEE S&P 2022) — (local: download/asleep-at-keyboard-2021.pdf)
  - Agentic prompt-injection threat — (web: securecodewarrior.com/article/prompt-injection-and-the-security-risks-of-agentic-coding-tools, labs.cloudsecurityalliance.org research-note Claude-Code-GitHub-Action, helpnetsecurity.com/2026/06/11; dated 2025–2026-06)
  - (abstract-only, not fetched): arXiv:2603.21642; arXiv:2509.05372
- **Confidence**: high (Pearce figures verified verbatim in PDF); high for prompt-injection threat existence (multiple dated web sources + named CSA/OWASP).
- **Gaps**: No dedicated *secure-code-generation evaluation* paper acquired (e.g. CyberSecEval / SecurityEval / SVEN-style). No malware-generation/dual-use primary study acquired — both currently web/abstract only. Recommend main thread fetch one secure-code-gen benchmark PDF if §16 needs a primary eval.

---

### Q4: Licensing / copyright / memorization (copyleft training, Copilot litigation, verbatim memorization)

- **Findings**:
  - **GitHub Copilot litigation — Doe v. GitHub (status + claims, web/dated):** Class action filed Nov 2022 (Butterick et al.) against GitHub/Microsoft/OpenAI; originally **22 claims**. By the **June 24, 2024** ruling the court **dismissed most claims with prejudice**, leaving **two surviving claims: open-source license violation and breach of contract** (web, pearlcohen 2024-07-30; bakerlaw "The Copilot Litigation"; theregister 2024-01). **DMCA §1202(b)** (copyright-management-information removal) was **dismissed** because the court found no evidence Copilot generated code *identical* to plaintiffs' work — it "rarely memorized code" except with lengthy similar excerpts, and a cited duplication study "did not specifically address Copilot." Unjust enrichment and punitive damages also dismissed (CA law). Case stayed pending **interlocutory appeal certified Sep 27, 2024** to the **Ninth Circuit**.
  - **Memorization (directly load-bearing for the licensing argument):** The court's own finding — Copilot "rarely memorized code" / output not "identical enough" — is itself the key memorization datapoint and is *why* the DMCA claim failed. This ties the legal question to the technical verbatim-memorization literature: the strength of a copyright claim hinges on demonstrable verbatim regurgitation, which the court found insufficient on the evidence presented.
  - **Copyleft/GPL training:** The surviving "open-source license violation" claim is the live legal theory that training on (and emitting) copyleft/GPL-licensed code without attribution/license-propagation may breach OSS licenses — still unresolved, on appeal. Frame as open legal question, not settled law.
- **Sources**:
  - Doe v. GitHub status, DMCA §1202(b) dismissal, surviving claims, memorization finding — (web: pearlcohen.com/copyright-claims-against-github-microsoft-and-openai-largely-dismissed [2024-06-24 ruling / 2024-07-30 article], bakerlaw.com/the-copilot-litigation, theregister.com/2024/01/12/github_copilot_copyright_case_narrowed)
- **Confidence**: high for litigation status/claims (multiple consistent dated legal sources, primary ruling date); medium for the technical memorization framing (drawn from the court's characterization, not a measurement paper).
- **Gaps**: No primary verbatim-memorization measurement paper for code acquired (e.g. Carlini-style extraction on code models, or "Quantifying Memorization"). The Stack / StarCoder licensing-by-construction (opt-out, permissive-only) is in the existing corpus (the-stack-2022.pdf, starcoder-2023.pdf, starcoder2-2024.pdf already in download/) and should be cross-referenced by main thread for the "license-clean training data" counter-pattern. No Ninth Circuit decision yet (appeal pending as of data collection).

---

### Q5: Open problems & roadmap (future-directions from recent code-LLM surveys)

- **Findings (from Jiang, Wang, Shen et al., "A Survey on Large Language Models for Code Generation," 2024 — §6 "Challenges & Opportunities," p.53-55):** Six explicitly enumerated challenge themes, verbatim subheads:
  1. **Enhancing complex code generation at repository and software scale.** LLMs handle function-level snippets but struggle with repo/software-level, unseen problems. Survey cites AlphaCode's top-54.3% competition ranking and SWE-bench's finding that the best model at the time (Claude 2) solved only **1.96%** of real GitHub issues; root causes given as weak reasoning, complex internal/external dependencies, and context-length limits. (Directly = the "long-horizon SWE reliability / repo-scale reasoning" open problem.)
  2. **Innovating model architectures tuned to code structure** (AST/tree-based nets, IR/compiler-theory representations vs flat sequential Transformers).
  3. **Curating high-quality code data** for pre-training/fine-tuning (scarcity of large, diverse, high-quality datasets; mining + synthesis + industry partnerships).
  4. **Developing comprehensive benchmarks and metrics for coding-proficiency evaluation.** Survey explicitly argues HumanEval is a saturated/unrepresentative de-facto standard that "can't reflect practical development" — this is the **eval-saturation** open problem, primary-sourced.
  5. **Ensuring code safety and aligning LLM outputs with human coding preferences.** Calls for **integrating formal verification tools into the LLM pipeline** (= the "verification + LLMs" open direction) plus alignment-learning frameworks for ethical/security norms.
  6. **Reducing the carbon impact of generative-AI inference** (environmental cost of deployment).
- **Sources**:
  - Jiang, Wang, Shen, Kim, Kim, "A Survey on Large Language Models for Code Generation," 2024 (ACM, 70pp) — (local: download/code-llm-survey-2024.pdf), §6 Challenges & Opportunities (p.53-55)
- **Confidence**: high (verbatim subheads and the 1.96% / 54.3% figures extracted directly from the PDF).
- **Gaps**: Only one survey's future-directions section pulled (the request allowed 1–2). A second complementary survey (e.g. Fan et al. ICSE-FoSE 2023 "LLMs for software engineering: survey and open problems," cited as ref [74] in this survey) was NOT acquired — would add an SE-practitioner angle (deployment gaps, maintenance, trust). Recommend optional fetch if §18 needs a second roadmap source. The "deployment gaps" theme is better covered by the Q2/Q3 web evidence (production agent adoption + security) than by this survey.

---

## Acquisition summary
- **NEW PDFs this cluster (all verified):**
  - download/asleep-at-keyboard-2021.pdf (Pearce, 15pp) — verified title/figures
  - download/deepseek-coder-v2-2024.pdf (19pp) — verified, V2 (note: pre-existing download/deepseek-coder-2024.pdf is V1, distinct)
  - download/code-llm-survey-2024.pdf (Jiang et al., 70pp) — verified
- **PDF budget used: 3 of 6.** Pre-existing corpus already holds chen-codex, code-llama, codebert, codegen, coderl, deepseek-coder(V1), deepseek-r1, fim, incoder, magicoder, mbpp, phi1, qwen25-coder, reflexion, self-debugging, starcoder, starcoder2, the-stack, wizardcoder.
- **Web-only (record URL+date in references):** SWE-bench Verified late-2025 band (~80%, contamination caveat); LiveCodeBench ~90% band; agentic cost-per-task economics; agentic prompt-injection threat; Doe v. GitHub litigation status.
