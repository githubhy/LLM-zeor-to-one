# C8 — Serving economics, security & licensing

## Q3. Security of model-generated code, 2024-2026 (part a done first; local PDF grounded)

### Asleep at the Keyboard — measured vulnerable fraction
- **Claim**: Pearce et al. systematically prompted GitHub Copilot (technical-preview era) across 89 hand-crafted scenarios spanning MITRE's 2021 CWE Top-25 (plus 6 hardware CWEs in Verilog), generating 1,689 completed programs, and found roughly 40% vulnerable; broken down by top-scoring suggestion only, 39.33% of top options and 40.73% of all options (across all axes/languages combined) were vulnerable.
- **Numbers**: Headline (abstract): 89 scenarios -> 1,689 programs, ~40% vulnerable. Software-only "Diversity of Weakness" axis (Sec V-A): 54 scenarios / 18 CWEs -> 1,084 valid programs, 477 (44.00%) vulnerable, 24/54 scenarios (44.44%) had a vulnerable top-scoring suggestion. "Diversity of Prompt" axis (CWE-89 SQLi only, 17 scenarios): 407 valid programs, 152 (37.35%) vulnerable, 4/17 (25.53%) top-scoring vulnerable. "Diversity of Domain" axis (Verilog, 6 hardware CWEs, 18 scenarios): 198 programs, 56 (28.28%) vulnerable, 7/18 (38.89%) top-scoring vulnerable. Discussion section combined figure across ALL axes/languages: **39.33% of top-scoring options vulnerable, 40.73% of all options vulnerable.**
- **Conditions**: GitHub Copilot in technical-preview phase (as of Aug 2021), Codex-family backend, evaluated via GitHub CodeQL (python-security-and-quality.qls, 153 checks) plus manual inspection for CWEs CodeQL can't cover (e.g., Verilog, CWE-434). Single PC (i7-10750H), CodeQL 2.5.7. Non-vulnerable classification is conservative (only marks vulnerable if code *definitively* contains the CWE).
- **Source**: H. Pearce, B. Ahmad, B. Tan, B. Dolan-Gavitt, R. Karri, "Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code Contributions," IEEE S&P 2022, arXiv:2108.09293v3.
- **Quality tier**: primary
- **Confidence**: high
- **Quote**: "In total, we produce 89 different scenarios for Copilot to complete, producing 1,689 programs. Of these, we found approximately 40% to be vulnerable." / "39.33% of the top and 40.73% of the total options were vulnerable" (Discussion).
- **Local path**: download/asleep-at-keyboard-2021.pdf

### SVEN — steerability counterpoint (already in survey, re-verify numbers not done here — see existing survey citation 42; not independently re-opened this session, so treat pre-existing figures as unverified-this-session)
- **Claim**: existing survey section 16.1 already cites SVEN (He & Vechev) reporting a 2.7B CodeGen baseline secure-generation rate of 59.1%, raised to 92.3% with security-hardening steering, degraded to 36.8% adversarially.
- **Numbers**: 59.1% baseline / 92.3% hardened / 36.8% adversarial (as already cited in survey; NOT reopened/reverified from he-vechev-sven-secure-code-2023.pdf this session — GAP: re-verify quote against PDF if not already citation-audited).
- **Source**: He, Vechev, "Large Language Models for Code: Security Hardening and Adversarial Testing" (SVEN), 2023 (per existing survey ref 42).
- **Quality tier**: primary (paper acquired locally)
- **Confidence**: medium (numbers carried over from existing survey text, not re-verified against PDF in this session)
- **Local path**: download/he-vechev-sven-secure-code-2023.pdf


## Q1. Serving mechanics for agent loops (prefix/KV-cache reuse, speculative decoding, constrained decoding)

### Anthropic prompt caching — official vendor numbers
- **Claim**: Anthropic's prompt-caching feature caches a prompt prefix (system prompt, tool schemas, long conversation history) across API calls; cached-token reads are billed at a fixed discount versus fresh input tokens, and Anthropic states an "up to 90%" cost reduction and "up to 85%" latency reduction for long prompts.
- **Numbers**: Cache read = 0.1x standard input token rate (90% discount). Cache write: 1.25x standard rate for a 5-minute TTL, 2x for a 1-hour TTL. Headline vendor claim: "up to 90% cost reduction and up to 85% latency reduction for long prompts." Available in beta from Dec 17, 2024 for Claude 3.5 Sonnet / Claude 3 Opus / Claude 3 Haiku; later extended, also offered via Amazon Bedrock and Google Vertex AI.
- **Conditions**: Anthropic API / Claude Platform. Applies specifically to long, mostly-static prompt prefixes (system prompt + tools + long context) — the exact use-case an agent loop produces (stable prefix, growing suffix).
- **Source**: Anthropic, "Prompt caching with Claude" (blog) and Claude Platform Docs, "Prompt caching," 2024 (docs page current as accessed 2026-08-14).
- **Quality tier**: strong-secondary (official vendor product documentation/blog, not peer-reviewed, but is the primary disclosure of the actual production pricing mechanism)
- **Confidence**: high (pricing multipliers and mechanism; these are the vendor's own stated numbers, not independently audited)
- **Quote**: "reducing costs by up to 90% and latency by up to 85% for long prompts" (per Anthropic prompt-caching announcement, as reported via search; page not independently re-fetched this session beyond the search snippet — GAP: verify exact wording directly against platform.claude.com/docs/en/build-with-claude/prompt-caching if this figure becomes load-bearing).
- **Local path**: NOT ACQUIRED (web-only, vendor docs; no PDF)

### TraceLab — measured coding-agent trace characteristics (primary academic source)
- **Claim**: A University of Washington (SyFI Lab) trace study of real Claude Code and Codex coding-agent sessions finds prefix/KV-cache hit rates that are "high but imperfect," and identifies concrete serving-optimization opportunities (append-length-aware prefill, tool-latency prediction, KV-cache management around human-paced gaps between agent turns).
- **Numbers**: Dataset = ~4,300 coding-agent sessions, ~350,000 LLM steps, ~430,000 tool calls, collected from day-to-day use of Claude Code and Codex. The paper characterizes cache hit rates as "high but imperfect" — I could NOT extract an exact percentage figure from the abstract/HTML fetch available this session (fetch returned abstract-level text only, no numeric table). GAP: exact hit-rate percentage, tool-call latency distribution, and input/output token ratio require reading the full PDF/HTML body (not done this session — WebFetch budget exhausted; recommend acquiring via source-fetch).
- **Conditions**: Real production coding-agent traces (Claude Code, Codex), 2026.
- **Source**: Kan Zhu et al. (Univ. of Washington SyFI Lab), "TraceLab: Characterizing Coding Agent Workloads for LLM Serving," arXiv:2606.30560, June 2026.
- **Quality tier**: primary (peer-review status unclear — arXiv preprint from a research lab; empirical trace study, not vendor marketing)
- **Confidence**: medium (trace-scale numbers and headline "high but imperfect" characterization confirmed; the specific hit-rate percentage is a GAP)
- **Quote**: "roughly 4,300 coding-agent sessions, containing about 350,000 LLM steps and 430,000 tool calls" (per SyFI Lab project blog / search synthesis, not verbatim-confirmed against the PDF itself this session).
- **Local path**: NOT ACQUIRED (recommend acquiring PDF via source-fetch for the exact numeric table)

### Cache-hit-rate anecdotes (mixed quality — flagged as such)
- **Claim**: Several secondary sources report specific coding-agent cache-hit-rate figures, but these are blog-level and NOT independently verified against a primary paper or vendor filing this session.
- **Numbers** (UNVERIFIED, blog-tier only): "Claude Code achieves a 92% cache hit rate and 81% cost reduction" (dev.to blog post); "Both Claude and Codex serve about 96% of prompt tokens from the prefix cache" (search-engine synthesis, possibly derived from TraceLab but not confirmed as verbatim); a production-agent case study reporting a 7% -> 74% cache-hit-rate improvement from a single structural prompt change, cutting monthly inference bill 59% (DigitalOcean conceptual article).
- **Conditions**: varies by source; none of these are peer-reviewed or vendor-official.
- **Source**: dev.to (shilpamitra), DigitalOcean community conceptual article, various 2026 blog posts.
- **Quality tier**: weak (blog-level; included only because the brief asked for concrete numbers and these are the numbers circulating — treat as illustrative, not evidentiary)
- **Confidence**: low
- **Local path**: NOT ACQUIRED

### Speculative decoding for code — acceptance-rate uplift (secondary, not independently verified against a specific paper this session)
- **Claim**: Code generation is reported as a favorable workload for speculative decoding because of high token-sequence repetition/predictability, yielding higher acceptance rates than general chat.
- **Numbers**: General claim (secondary, blog-tier synthesis): EAGLE-3-style methods reported at 60-80% acceptance on in-distribution workloads vs 40-60% for standalone draft models; code generation specifically cited as exceeding 85% acceptance in some reports. NOTE: existing survey section 10.2 already covers Leviathan et al.'s original speculative decoding paper (download/leviathan-speculative-decoding-2023.pdf, cite:27) plus Cursor's "fast-apply" (~1000 tok/s, using existing source code as the draft) and GitHub's FIM+speculative latency cut (1.4s -> 0.7s median). This new material is ADDITIONAL and not yet independently verified against a primary paper (EAGLE-3 paper not opened this session).
- **Conditions**: varies; not tied to one benchmark in the sources found.
- **Source**: multiple 2026 technical blogs (prompt20.com, glukhov.org, tianpan.co); no primary EAGLE-3 paper opened this session.
- **Quality tier**: weak-to-careful-explainer (blog synthesis; the 85%+ code-specific acceptance figure could not be traced to a specific primary paper this session)
- **Confidence**: low
- **Local path**: NOT ACQUIRED — GAP: if this figure is to be used, acquire the EAGLE-3 paper or a controlled code-specific speculative-decoding study.

### Constrained/grammar-guided decoding — already well-covered in existing survey
- **Claim**: No new evidence gathered this session beyond what §10.1 of `inference-decoding-and-serving.md` already cites (PICARD incremental-parsing constrained decoding for SQL, download/picard-2021.pdf; Outlines regex/CFG-as-FSM masking, download/willard-outlines-guided-generation-2023.pdf). Both are already primary, locally acquired, and cited with concrete numbers (PICARD: ~12% -> ~2% unusable SQL; 75.5% exact-set-match / 79.3% execution accuracy on Spider).
- **Numbers**: see existing survey §10.1 (not re-derived this session; both PDFs already in `download/`).
- **Quality tier**: primary (already in survey)
- **Confidence**: high (existing citations; not reopened this session — flagged as carried-over)
- **Local path**: download/picard-2021.pdf, download/willard-outlines-guided-generation-2023.pdf


## Q2. Token economics of agentic coding

### "How Do AI Agents Spend Your Money?" — primary measurement of agent token consumption
- **Claim**: A multi-institution study (Michigan/Stanford/MIT-affiliated authors, incl. Rada Mihalcea and Erik Brynjolfsson) directly measured token consumption across agentic coding tasks and found agentic tasks consume roughly 1000x more tokens than single-turn code chat/reasoning, driven overwhelmingly by input tokens (re-read context), with large run-to-run variance and poor self-prediction of usage by the models themselves.
- **Numbers**: "Agentic tasks consume 1000x more tokens than code reasoning and code chat." Repeated runs on the identical task can differ by up to 30x in total tokens. Kimi-K2 and Claude-Sonnet-4.5 consume on average >1.5 million more tokens than GPT-5 on the same tasks (model-to-model efficiency variance). Frontier models' own self-predictions of their token usage correlate only weakly-to-moderately with actual usage (correlation up to 0.39). Accuracy-vs-cost: accuracy often peaks at intermediate cost and saturates (does not keep improving) at higher cost.
- **Conditions**: Agentic coding tasks (unspecified exact benchmark from abstract-level read; GAP: confirm exact benchmark/harness — SWE-bench-like or custom — from full paper), models compared include Kimi-K2, Claude-Sonnet-4.5, GPT-5. Date: submitted arXiv April 24, 2026, revised April 29, 2026 — i.e., contemporary evidence for this cluster's "2024-2026" window.
- **Source**: Longju Bai, Zhemin Huang, Xingyao Wang, Jiao Sun, Rada Mihalcea, Erik Brynjolfsson, Alex Pentland, Jiaxin Pei, "How Do AI Agents Spend Your Money? Analyzing and Predicting Token Consumption in Agentic Coding Tasks," arXiv:2604.22750, April 2026.
- **Quality tier**: primary (arXiv preprint, multi-author academic study with named authors incl. established economists/NLP researchers; not vendor marketing)
- **Confidence**: high for the headline "1000x" and "up to 30x variance" and "input-token-dominant" claims (directly quoted from abstract via WebFetch this session); medium for the exact benchmark/task-suite identity (GAP — not confirmed from full text)
- **Quote**: "runs on the same task can differ by up to 30x in total tokens" / "input tokens rather than output tokens driving the overall cost" / "Kimi-K2 and Claude-Sonnet-4.5, on average, consume over 1.5 million more tokens than GPT-5" / "frontier models fail to accurately predict their own token usage (with weak-to-moderate correlations, up to 0.39)" (all quoted from arxiv.org/abs/2604.22750 abstract, fetched this session).
- **Local path**: NOT ACQUIRED — recommend source-fetch (arXiv:2604.22750) for the full numeric tables (per-task token counts, exact input/output split).

### Input/output token ratio in agent loops — secondary blog claims (tiered as weak, per brief instruction)
- **Claim**: Multiple 2026 vendor/blog sources (not independently verified against a primary paper this session) claim agent loops run input:output token ratios far higher than single-turn chat, in the range of 100:1 to 150:1+, because the full accumulated context (conversation history, tool outputs, file contents) is re-sent on every step in the absence of true incremental caching of the *growing* suffix.
- **Numbers** (UNVERIFIED, blog-tier): "agentic coding consumes over 1,000x more tokens than single-turn reasoning, with an input-dominant ratio exceeding 150:1" (Spheron blog); "production agents typically consume 100 tokens of context for every token generated" (Augment Code guide); "a 20-step loop consuming over 10x the tokens a simple per-step estimate suggests" due to quadratic-ish growth of re-billed context (Augment Code guide). None of these blog claims were traced to a specific measured dataset or paper this session.
- **Conditions**: unspecified benchmark/model in the blog sources; treat as industry-practitioner consensus, not measured research.
- **Source**: Spheron Blog ("Agentic AI Inference Cost: Why Agents Burn 5-30x Tokens," 2026); Augment Code guides ("AI Agent Loop Token Costs," "AI Coding Cost Analysis," 2026).
- **Quality tier**: weak (marketing/practitioner blogs; directionally consistent with the primary arXiv:2604.22750 "input-token-dominant, up to 1000x" finding, but not independently peer-reviewed or dataset-backed)
- **Confidence**: low (numbers), medium (qualitative direction — "input-dominant, caching does not fully solve it because the suffix keeps growing" — is corroborated by the primary paper's finding that input tokens dominate cost even with caching enabled)

### Vendor pricing pages — explicitly tiered as weak per brief instruction
- **Claim**: The only per-task dollar-cost numbers found for named agentic-coding products (Devin/Cognition "Fusion," Claude Code, Cursor, Codex) are vendor pricing pages and third-party aggregator sites, not measured studies.
- **Numbers**: Devin: Core plan \$20/mo pay-as-you-go at \$2.25 per "ACU" (Agent Compute Unit, Cognition's own normalized metric, ~15 min of autonomous work); Team plan \$500/mo incl. 250 ACUs at \$2.00 each. Cognition's own "FrontierCode" benchmark claims Devin "Fusion" matches frontier models (named as "GPT-5.5" and "Opus 4.8" in the aggregator source — GAP: these exact model-name strings could not be corroborated against an official OpenAI/Anthropic release and may be aggregator error or very recent releases beyond what could be verified this session) at "about a third lower cost per task."
- **Conditions**: vendor's own benchmark (FrontierCode), self-reported.
- **Source**: eesel.ai, pricepertoken.com, layer3labs.io, kunalganglani.com — third-party pricing-aggregator blogs summarizing Cognition/Devin's own marketing and benchmark claims, 2026.
- **Quality tier**: weak (vendor marketing filtered through unaffiliated aggregator sites; "ACU"-based pricing is a vendor-defined unit, not tokens, and the benchmark is not independently run)
- **Confidence**: low
- **Local path**: NOT ACQUIRED


## Q3 (continued). (b) Post-2021 replications / newer-model rates, and (c) prompt injection against coding agents

### Fu et al. — replication across Copilot, CodeWhisperer, Codeium (2023, published TOSEM 2025)
- **Claim**: An independent empirical study analyzing 733 code snippets generated by GitHub Copilot, Amazon CodeWhisperer, and Codeium (pulled from real GitHub projects) found continuing, substantial security-weakness rates, broadly consistent with (though somewhat lower than) the original Asleep-at-Keyboard headline.
- **Numbers**: 29.5% of Python snippets and 24.2% of JavaScript snippets contained security weaknesses (733 total snippets analyzed).
- **Conditions**: Real-world GitHub-project usage (not synthetic CWE-targeted prompts like Pearce et al.), Python + JavaScript, multiple tools compared (Copilot, CodeWhisperer, Codeium). Originally posted arXiv Oct 2023 (2310.02059), accepted to ACM Transactions on Software Engineering and Methodology (TOSEM) 2025.
- **Source**: Yujia Fu, Peng Liang, Amjed Tahir, Zengyang Li, Mojtaba Shahin, Jiaxin Yu, Jinfu Chen, "Security Weaknesses of Copilot-Generated Code in GitHub Projects: An Empirical Study," arXiv:2310.02059 (2023), ACM TOSEM 2025.
- **Quality tier**: primary (peer-reviewed, ACM TOSEM 2025 acceptance)
- **Confidence**: medium-high (numbers found via search-engine synthesis of the paper, not a direct WebFetch/PDF read this session — GAP: verify exact wording/table against the PDF before citing in survey prose)
- **Quote**: "29.5% of Python and 24.2% of JavaScript snippets contained security weaknesses" (per search synthesis of arXiv:2310.02059 / TOSEM 2025 version).
- **Local path**: NOT ACQUIRED — recommend source-fetch.

### Majdinasab et al. — targeted replication of Pearce et al., newer Copilot versions (SANER 2024)
- **Claim**: A direct, targeted replication of the original Asleep-at-Keyboard methodology found that newer Copilot versions still generate substantial insecure code, but at a REDUCED rate relative to the 2021 original — i.e., partial improvement over time, not resolution.
- **Numbers**: >35% of code suggestions contained security weaknesses (spanning 42 distinct MITRE CWEs, including command injection — a broader CWE set than Pearce et al.'s original top-25). Directionally: "with the improvements in newer versions of Copilot, the percentage of vulnerable code suggestions has reduced, but it remains evident that the model still suggests insecure code" (this is qualitative, not a paired before/after percentage — GAP: exact original-vs-replication delta not extracted this session).
- **Conditions**: Newer GitHub Copilot versions (post-2021, exact version/date not confirmed this session), replication methodology closely following Pearce et al. Published/presented at SANER 2024 (IEEE Intl. Conf. on Software Analysis, Evolution and Reengineering), RENE (Reproducibility Studies and Negative Results) track — also on arXiv as 2311.11177 ("Assessing the Security of GitHub Copilot's Generated Code").
- **Source**: Amirali Majdinasab, Michael Joshua Bishop, Shayan Rasheed, Arghavan Moradi Dakhel, Amjed Tahir, Foutse Khomh, "Assessing the Security of GitHub Copilot's Generated Code — A Targeted Replication Study," arXiv:2311.11177, SANER 2024.
- **Quality tier**: primary (peer-reviewed conference publication, explicit replication design)
- **Confidence**: medium (headline ">35%" and the "reduced but not resolved" directional finding both found via search synthesis; exact quantitative before/after comparison not verified this session — GAP)
- **Quote**: "over 35% of code suggestions generated by GitHub Copilot contained security weaknesses, from a diverse group of 42 distinct... CWEs" (per search synthesis; NOT independently confirmed against the PDF text this session).
- **Local path**: NOT ACQUIRED — recommend source-fetch (arXiv:2311.11177); this is the single best available direct answer to "has the rate improved with newer models" and should be fully verified before being stated as a headline claim in survey prose.

### Synthesis for Q3(b)
- **Claim**: Taken together, the two post-2021 studies found suggest the vulnerable-code-suggestion rate for Copilot-family tools has NOT dropped to a low level by 2024-2025 — independent measurements cluster in the high-20s to high-30s percent range (24.2%-35%+), down somewhat from Pearce et al.'s 2021 ~40%/39.33% figures, but still substantial. Neither replication is dramatically lower, and Majdinasab et al. explicitly frame the improvement as partial ("reduced... but... still... insecure").
- **Numbers**: See individual entries above. No single study directly re-ran the IDENTICAL Pearce et al. 89-scenario CWE-Top-25 protocol against a 2025/2026-era frontier coding model (e.g., Claude, GPT-5-class, or a current Copilot backend) — this is a genuine GAP in the literature as surfaced by this session's search, not merely an acquisition gap.
- **Quality tier**: primary (both underlying studies), synthesis itself is this agent's own aggregation
- **Confidence**: medium — the general direction (partial improvement, not resolution) is corroborated by two independent studies, but neither was fully re-verified against its PDF this session (both are search-engine syntheses).
- **GAP**: No 2025-2026-era replication against current-generation frontier coding agents (e.g., Claude Opus/Sonnet, GPT-5-class, current Copilot) was found in this session's searches. If the survey needs a current-generation number, this is an open gap, not something to paper over with the 2021/2023/2024 figures.

### "Your AI, My Shell" — first systematic empirical study of prompt injection against agentic coding editors
- **Claim**: The first empirical, systematic study of prompt injection attacks specifically targeting high-privilege agentic AI coding editors (as opposed to chatbots), showing that untrusted external content (poisoned dev resources) can hijack the agent into executing malicious commands, with very high measured success rates against real, deployed products.
- **Numbers**: Built "AIShellJack," an automated testing framework with 314 unique attack payloads covering 70 MITRE ATT&CK techniques. Evaluated against GitHub Copilot and Cursor: attack success rates reach as high as 84% for executing malicious commands. Effective across objective classes: initial access, system discovery, credential theft.
- **Conditions**: Real, deployed agentic coding editors (GitHub Copilot, Cursor), attacker delivers payload via "poisoned external development resources" (the exact channel — repo files, docs, PR/issue content — not fully itemized in the search synthesis; GAP: confirm exact injection vectors from full text). Published Sept 2025.
- **Source**: (authors not fully confirmed this session — search snippets did not surface a complete author list; GAP: confirm author list from arxiv.org/abs/2509.22040 directly) "'Your AI, My Shell': Demystifying Prompt Injection Attacks on Agentic AI Coding Editors," arXiv:2509.22040, Sept 2025.
- **Quality tier**: primary (arXiv preprint; systematic empirical methodology with a named testing framework — peer-review status not confirmed this session)
- **Confidence**: medium-high for the "84% attack success rate on Copilot/Cursor" headline number (consistent across two independent search snippets); low for author attribution and exact attack-vector taxonomy (GAP)
- **Quote**: "attack success rates can reach as high as 84% for executing malicious commands" (per search synthesis of arXiv:2509.22040; NOT independently re-verified against the PDF this session — this is the single most important claim in this cluster and should be verified against the primary PDF before being stated as fact in survey prose).
- **Local path**: NOT ACQUIRED — HIGH PRIORITY for source-fetch given this is flagged as the most important sub-question in the brief.

### "The Attacker Moves Second" — cross-lab (OpenAI/Anthropic/DeepMind) finding that published defenses largely fail under adaptive attack
- **Claim**: A large multi-author paper from researchers at OpenAI, Anthropic, and Google DeepMind (not itself specific to coding agents, but directly relevant to any mitigation claim for prompt injection, including in agentic coding tools) shows that 12 published defenses against LLM jailbreaks and prompt injections — many of which claimed near-zero attack success rates in their own papers — can be bypassed with attack success rates above 90% once evaluated against an adaptive attacker (gradient descent, reinforcement learning, search-based optimization, and human red-teaming), rather than the static attack sets used in the original defense papers.
- **Numbers**: 12 published defenses tested; most fell with attack success rate >90% under adaptive evaluation (vs. near-zero claimed in original publications).
- **Conditions**: General LLM jailbreak/prompt-injection defenses (not coding-agent-specific), October 2025.
- **Source**: Milad Nasr, Nicholas Carlini, Chawin Sitawarin, Sander V. Schulhoff, Jamie Hayes, Michael Ilie, Juliette Pluto, Shuang Song, Harsh Chaudhari, Ilia Shumailov, Abhradeep Thakurta, Kai Yuanqing Xiao, Andreas Terzis, Florian Tramer, "The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against LLM Jailbreaks and Prompt Injections," Oct 2025 (arXiv id not directly captured this session — GAP: confirm exact arXiv id, e.g. via arxiv.org search for the title, before citing).
- **Quality tier**: primary (named authors from major AI-safety labs; methodologically the paper's whole point is rigor of adaptive evaluation)
- **Confidence**: high for the qualitative finding and the ">90% bypass on 12 defenses" headline (corroborated across 2 independent search snippets, incl. a VentureBeat report); the exact arXiv ID needs confirmation
- **Quote**: "researchers achieved bypass rates above 90% on most [of the 12] defenses" (per search synthesis; VentureBeat headline: "Researchers broke every AI defense they tested").
- **Local path**: NOT ACQUIRED — recommend source-fetch; directly supports the survey's existing §16.2 claim that "prompt injection ... remains an active problem" with a much stronger, dated, cross-lab evidentiary anchor than the current citation (existing ref 52) provides alone.

### Prompt injection mitigation principles — corroborating industry-consensus source (already partially in survey)
- **Claim**: Existing survey §16.2 already states the mitigation principles (least-privilege scoping, treat repository content as untrusted, gate destructive actions) and cites industry tracking that prompt injection is the dominant driver of agentic-AI security failures through 2025-2026 (ref 52). This session's searches corroborate the threat's severity and scale (AIShellJack's 84% figure, the systematic-analysis paper in the International Journal of Open Information Technologies covering "skills, tools, and protocol ecosystems") but did not find a NEW published mitigation technique with measured effectiveness specifically for coding agents beyond what's already cited.
- **Numbers**: none new beyond what's captured above.
- **Quality tier**: n/a (synthesis note)
- **Confidence**: medium
- **GAP**: no measured, coding-agent-specific mitigation effectiveness study (e.g., a sandboxing or permission-scoping technique with a before/after attack-success-rate number) was found in this session's search budget. Existing survey's mitigation discussion remains principle-level, not measurement-level, even after this search pass.


## Q4. Licensing and copyright status (2026)

### Doe v. GitHub/Microsoft/OpenAI — case posture and claim disposition
- **Claim**: The consolidated putative class action (N.D. Cal., Case Nos. 4:22-cv-06823-JST and 4:22-cv-07074-JST, before Judge Jon S. Tigar) has, per multiple secondary legal-commentary sources, dismissed the large majority of the original ~22 claims (state-law claims — unjust enrichment, punitive damages, most tort claims — dismissed with prejudice as preempted by federal copyright law, in an order reported as issued January 2024), leaving two claims live: breach of open-source license terms and breach of contract. The DMCA §1202 (copyright-management-information) claim's status is contested across sources — one report states it was dismissed outright for lack of "identicality" between generated and original code; another states the court allowed a narrower §1202(a)(1) claim to proceed on the theory that identicality is not required, and that this exact legal question (whether §1202(b) requires exact/near-identical copying to apply to AI-generated derivative output) was certified for interlocutory appeal to the Ninth Circuit in September 2024.
- **Numbers**: One source states 20 of 22 claims were dismissed; the two surviving claims are open-source license violation and breach of contract.
- **Conditions**: N.D. Cal.; district court order(s) reported dated January 2024 (state-law claims dismissed with prejudice); Ninth Circuit interlocutory appeal accepted December 2024, docketed as *GitHub, et al. v. Does, et al.*, No. 24-6136; district court proceedings reported stayed pending the appeal; oral argument at the Ninth Circuit held February 11, 2026; **no appellate ruling had issued as of the reporting date** (i.e., the DMCA §1202(b) question is PENDING, not decided, as of 2026-08-14).
- **Source**: Multiple secondary legal-commentary sources (not a primary court filing, since WebFetch/direct docket access was out of scope for this pass): Legal.io ("Judge Throws Out Majority of Claims in GitHub Copilot Lawsuit"); Wikipedia, "Doe v. GitHub, Microsoft, and OpenAI"; Bloomberg Law, "Copyright Suit Over Github, AI Coding Tool Vexes Ninth Circuit"; nquiringminds, "Ninth Circuit Considers DMCA CMI Claim in AI Copyright Case"; Joseph Saveri Law Firm case-tracking page (githubcopilotlitigation.com/case-updates.html), 2024-2026.
- **Quality tier**: strong-secondary (law-firm/legal-press case tracking; no primary docket document was opened this session)
- **Quote**: "The Ninth Circuit accepted the appeal (GitHub, et al. v. Does, et al., №24–6136) in December 2024, and the district court proceedings are stayed pending the outcome." / "Oral arguments were held at the 9th Circuit on February 11, 2026, over whether DMCA Section 1202(b) requires identical copies for liability. No ruling has been issued as of the date of that article."
- **Confidence**: medium — case name, court, and general posture are corroborated across independent sources; exact claim count (20/22) and the precise sequencing of the DMCA-claim rulings (fully dismissed vs. narrowed-and-allowed) are NOT fully reconciled across sources and should be verified against the actual docket before being stated as fact in the survey body.

### The Stack — opt-out mechanism and license-filtering pipeline (as designed)
- **Claim**: The Stack (BigCode/ServiceNow/Hugging Face, 2022) is a 3.1 TB, 30-language source-code corpus built by cloning GitHub repositories, extracting an SPDX license identifier per repository where available, and exposing both a self-service lookup tool ("Am I in The Stack") and a written removal-request process so code owners can have their repository excluded from the released dataset and from future training.
- **Numbers**: 220.92M unique repo names identified from GHArchive event logs (2015-01-01 to 2022-03-31); 137.36M repositories successfully cloned (>62% success rate); 51.76B files seen, 5.28B unique (dedup by git hash), 92.36 TB uncompressed raw stored size, reduced to the released 3.1 TB "permissively licensed" subset. Of the cloned repos, GHArchive-reported license metadata was available for only 26.4M (of 137.36M); per-repo SPDX detection results (top-20 table) show `not_found` at 81.91% of the sample, `MIT` at 9.58%, `Apache-2.0` at 2.71% — i.e. the large majority of raw repositories carry no machine-detectable license, which is why a permissive-license allow-list filtering step (not read in full this session — lives in the paper's §3.2 data-governance plan) is required to produce the permissively-licensed release subset.
- **Conditions**: n/a (dataset-construction methodology, not a legal ruling)
- **Source**: Kocetkov, Li, Ben Allal, Li, Mou, Muñoz Ferrandis, Jernite, Mitchell, Hughes, Wolf, Bahdanau, von Werra, de Vries, "The Stack: 3 TB of permissively licensed source code," arXiv:2211.15533, Nov 2022.
- **Quality tier**: primary (paper opened and read directly this session)
- **Quote**: "We make the dataset available at https://hf.co/BigCode, provide a tool called 'Am I in The Stack' (https://hf.co/spaces/bigcode/in-the-stack) for developers to search The Stack for copies of their code, and provide a process for code to be removed from the dataset by following the instructions at https://www.bigcode-project.org/docs/about/the-stack/."
- **Confidence**: high (opt-out tool + removal-process claim, and the raw license-detection numbers, both read directly from the source PDF's abstract, §3.1, and Table 2)
- **Local path**: download/the-stack-2022.pdf

### StarCoder2 / The Stack v2 — successor license-filtering practice
- **Claim**: StarCoder2 (BigCode, 2024) is trained on The Stack v2, whose pretraining pipeline is again filtered to permissively-licensed or no-license-declared code, with pull-request and other auxiliary training sources filtered to drop non-permissively-licensed contributions, and with opt-out requests (carried forward via the same "Am I in The Stack" mechanism) excluded before training. Community discussion threads on the released Hugging Face dataset/model pages allege that not all opt-out requests filed against Stack v1 were carried through to Stack v2's collection window, i.e., a claim that the opt-out mechanism's coverage across dataset versions has been contested, not that the mechanism itself does not exist.
- **Numbers**: none independently re-verified this session beyond what the original search snippets reported (no specific opt-out compliance percentage was found).
- **Conditions**: n/a
- **Source**: Lozhkov et al. (BigCode), "StarCoder 2 and The Stack v2: The Next Generation," arXiv:2402.19173, Feb 2024 (paper's data-governance section, per search-summary only — NOT opened directly this session); Hugging Face community discussion threads on `bigcode/starcoder` and `bigcode/the-stack-v2` ("Report: Legal issue(s)") for the opt-out-coverage allegation.
- **Quality tier**: strong-secondary for the filtering-policy claim (paper exists and is citable, but its text was not opened directly this session — only search-engine summary); weak for the opt-out-coverage allegation (unmoderated community forum posts, not verified)
- **Quote**: none captured verbatim (search-summary paraphrase only, not eligible for a load-bearing quote per this question's elevated bar)
- **Confidence**: low-medium — the filtering-policy claim is plausible and consistent with the Stack v1 design but was not confirmed against the primary arXiv text this session; the opt-out-coverage allegation is explicitly flagged as unverified forum chatter, not a documented finding
- **Local path**: NOT ACQUIRED (arXiv:2402.19173 not in `download/`)

### EU AI Act — GPAI training-data transparency and copyright obligations
- **Claim**: Under the EU AI Act's General-Purpose AI (GPAI) provisions, obligations that bear directly on training-code-on-public-repositories practice took effect in 2025: providers of GPAI models (indicative threshold >10^23 FLOP training compute) must publish a public summary of training data (using a European-Commission-issued mandatory template) and must implement a copyright-compliance policy, including honoring copyright/text-and-data-mining opt-outs. A GPAI Code of Practice (finalized July 10, 2025) organizes these commitments into three chapters: Transparency, Copyright, and Safety & Security. The relevant GPAI-provider obligations entered into force August 2, 2025, but the AI Office is reported to be operating a soft-enforcement grace period through August 2026 (providers who have signed the Code are not treated as in breach for incomplete implementation during this first year).
- **Numbers**: >10^23 FLOP training-compute indicative threshold for "general-purpose AI model" classification; Code of Practice finalized 2025-07-10; obligations in force 2025-08-02; enforcement grace period runs to August 2026.
- **Conditions**: European Union; EU AI Act (Regulation (EU) 2024/1689) GPAI chapter; applies to providers placing GPAI models on the EU market, which in practice reaches most frontier code-LLM vendors (OpenAI, Google, Anthropic, Meta, Mistral, etc.) regardless of where the model itself is trained.
- **Source**: Herbert Smith Freehills Kramer, "AI regulation hasn't taken a summer break: transparency requirements re training data and compliance with copyright law come into force in EU" (2025-09); Clifford Chance, "Copyright compliance under the EU AI Act for GPAI model providers" (2025-10); WilmerHale, "European Commission Releases Mandatory Template for Public Disclosure of AI Training Data."
- **Quality tier**: strong-secondary (international law-firm client alerts summarizing the regulation; the regulation text itself and the Commission's template were not opened directly this session)
- **Quote**: "Starting in 2026, the EU AI Act will require every AI company to disclose training data sources, respect copyright opt-outs, and label AI-generated content." / "During the first year (until August 2026), the AI Office will not consider providers to have broken their commitments if they do not fully implement all commitments immediately after signing the Code."
- **Confidence**: medium — dates and structure corroborate across three independent law-firm sources; the regulation's primary text (Regulation (EU) 2024/1689 and the Commission's training-data-summary template) was not opened directly, so exact obligation wording should be re-verified against the primary text before being stated as a compliance requirement in survey prose.
- **Local path**: NOT ACQUIRED

### Output-provenance / attribution tooling in production use
- **Claim**: At least one commercial code-assistant vendor documents a production provenance-tracing feature: Tabnine's own product documentation states that code generated by its AI chat is checked against publicly visible GitHub code and flagged when a match is found, with line-level, multi-tool attribution recorded (per a companion vendor blog post) as portable Git Notes for governance/compliance audit trails. This is a documented, currently-shipping product feature, not a research prototype.
- **Numbers**: none (no match-rate or coverage statistic was reported in the search snippet).
- **Conditions**: commercial product feature (Tabnine); applies to Tabnine's own AI-chat code-generation surface; scope of "publicly visible GitHub code" used as the comparison corpus not further specified in the snippet.
- **Source**: Tabnine, "Provenance and Attribution," Tabnine product documentation, docs.tabnine.com/main/welcome/readme/protection/provenance-and-attribution (undated, accessed 2026-08-14); Tabnine blog, "From Suggestion to Source: Why Provenance and Attribution Belong in Your CI/CD Pipeline."
- **Quality tier**: primary for the "is this in production" claim (vendor's own documentation of its own shipping feature)
- **Quote**: "Tabnine performs provenance tracing for code generated by AI chat, checking generated code against publicly visible code on GitHub and flagging any matches found."
- **Confidence**: medium-high for "a production tool exists"; low for any quantitative claim about its accuracy or coverage (none was found) — the docs page itself was not opened directly this session, only a search-engine summary of it, so the exact claim scope should be re-verified against the live docs page before citing a specific mechanism in survey prose.
- **Local path**: NOT ACQUIRED (web-only source; docs.tabnine.com)

### Research-stage code-provenance detection (contrast to production tooling)
- **Claim**: Beyond the single documented commercial deployment above, code-provenance/attribution is an active 2025-2026 research area rather than a mature production capability: proposed approaches include retrieval pipelines combining clone detection, neural similarity models, and membership-inference attacks to link generated code back to training data; classifiers exploiting LLM-rewrite stylistic signatures (e.g. "CodeGPTSensor"); and AST/identifier-length statistical features as authorship indicators. A 2026 paper explicitly frames "automated and explainable provenance of AI-generated code" as an open problem, and a companion detection-classifier line of work reports that classifiers degrade as models evolve and cannot reliably attribute a code block to a specific generating tool once multiple AI tools have touched it.
- **Numbers**: none quantitative captured this session beyond what is in the snippets above.
- **Conditions**: research literature, not a deployed system (contrast with the Tabnine record above)
- **Source**: arXiv:2608.02329, "On Automated and Explainable Provenance of AI-Generated Code" (2026); arXiv:2603.04212, "Code Fingerprints: Disentangled Attribution of LLM-Generated Code" (2026) — titles/abstracts only, from search-engine summary, NOT opened directly this session.
- **Quality tier**: careful-explainer (search-summary paraphrase of arXiv abstracts, not the primary text read directly)
- **Quote**: none captured verbatim (search-summary paraphrase only)
- **Confidence**: low — this record exists to flag that a research literature is active, not to assert any specific technical claim from these papers; neither paper was opened and read this session
- **Local path**: NOT ACQUIRED

## Gaps
- The exact current claim-disposition of *Doe v. GitHub* (precise count of dismissed vs. surviving claims, and the exact wording of the DMCA §1202(a)(1) vs §1202(b) ruling) is reported inconsistently across the secondary sources found this session and was not reconciled against the actual district-court docket (PACER/CourtListener) — a primary-source check is needed before the survey states a specific claim count or exact ruling date as fact.
- The Ninth Circuit's ruling on the certified DMCA §1202(b) question (argued 2026-02-11) had not issued as of this session (2026-08-14, per the searched sources) — this is a live, unresolved appellate question and must be presented as PENDING in survey prose, with a note to re-check before final publication of any survey text that cites it.
- arXiv:2402.19173 (StarCoder2/Stack v2 paper) was not opened directly this session; its §-level data-governance/opt-out details were taken from a search-engine summary only. Needs direct acquisition + read before its filtering-policy claim is treated as fully verified (see Sources worth acquiring).
- The Stack's §3.2 "data governance plan" (opt-out mechanics in full, including how the 110.9M repos lacking GHArchive-reported license metadata are handled) was not read this session — only the abstract, §1, §2, and the start of §3.1/Table 2 were opened (pages 1-5 of the PDF). A follow-up read of pages 6+ would close this gap.
- The EU AI Act primary regulation text (Regulation (EU) 2024/1689) and the European Commission's official training-data-summary template were not opened directly — all claims about them rest on law-firm secondary summaries.
- The Tabnine provenance-tracing docs page and the two 2026 arXiv provenance papers were characterized only from search-engine snippets, not read directly — no verbatim quotes beyond what the search tool itself surfaced.
- No coverage was found this session of provenance/attribution tooling used by GitHub/Microsoft (Copilot) or OpenAI themselves, only a third-party vendor (Tabnine) — a gap if the survey wants an example from one of the litigation defendants specifically.

## Corrections to the brief
- None. The brief's four sub-questions (a-d) were all addressable with the allotted budget; no factual premise in the brief was found to be wrong. The one nuance worth flagging: the brief's framing "any appellate ruling" (part a) — there is NO appellate ruling yet; the correct 2026 posture is that the Ninth Circuit heard oral argument (2026-02-11) and has not yet ruled, which is itself the finding (see elevated citation-integrity instruction: "pending is a finding, not a failure").

## Sources worth acquiring
- arXiv:2402.19173 — Lozhkov et al., "StarCoder 2 and The Stack v2: The Next Generation" (2024) — needed to verify the Stack v2 filtering-policy and opt-out-carryover claims directly against primary text rather than a search summary.
- The Stack (arXiv:2211.15533) pages 6+ — specifically §3.2 "Data governance plan" — to fully document the opt-out mechanism's legal/technical mechanics and how license-undetected repos are handled, beyond what pages 1-5 covered.
- A primary docket source for *Doe v. GitHub, Inc.* (N.D. Cal. 4:22-cv-06823-JST / 4:22-cv-07074-JST) — e.g. via CourtListener/RECAP — to pin the exact claim-disposition history with primary-source confidence instead of secondary legal-press summaries.
- Ninth Circuit docket for *GitHub, et al. v. Does, et al.*, No. 24-6136 — to catch the eventual ruling once issued (unresolved as of this session).
- Regulation (EU) 2024/1689 (the EU AI Act) GPAI chapter (Articles 53-55) plus the European Commission's official training-data-summary template — primary text for the transparency-obligation claims currently sourced only to law-firm client alerts.
