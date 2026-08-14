# C2 — Frontier results & deployed systems (2025-26)

## Q1. SWE-bench Verified — current state, provenance, top systems

### Original SWE-bench provenance (confirmed from local PDF)
- **Claim**: SWE-bench (the original, un-filtered benchmark) was introduced by a Princeton/University of Chicago team; SWE-bench Verified is a later human-filtered subset produced by OpenAI in collaboration with the SWE-bench authors.
- **Numbers**: Original SWE-bench = 2,294 task instances from 12 popular Python GitHub repos. Best model at publication (Claude 2) solved 1.96% of instances.
- **Conditions**: ICLR 2024 (published), arXiv:2310.06770v3, dated 11 Nov 2024 (this revision).
- **Source**: Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan, "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", ICLR 2024, arXiv:2310.06770.
- **Quality tier**: primary
- **Quote**: "we introduce SWE-bench, an evaluation framework consisting of 2,294 software engineering problems drawn from real GitHub issues and corresponding pull requests across 12 popular Python repositories... The best-performing model, Claude 2, is able to solve a mere 1.96% of the issues."
- **Confidence**: high
- **Local path**: download/swe-bench-2023.pdf

### SWE-bench Verified — creation, size, motivation (CORRECTS the brief's prior)
- **Claim**: SWE-bench Verified is a 500-instance human-annotated subset of the original SWE-bench, released by OpenAI (Preparedness team) in collaboration with the SWE-bench authors in August 2024 — not by the SWE-bench authors alone. It fixes three documented problems in the original set: incorrect grading of correct solutions, under-specified problem statements, and overly-specific/unfair unit tests.
- **Numbers**: 500 human-validated instances (subset of the 2,294-instance original). OpenAI also released human annotations for the full original test set enabling difficulty slicing: an "easy" subset of 196 tasks estimated <15 min to fix, and a "hard" subset of 45 tasks estimated >1 hour. NOTE: Epoch AI's evaluation harness (see below) reports using 484 of the 500 Verified instances, not the full 500 — this is a second, distinct provenance detail (a small number of instances apparently excluded/unusable in their harness) that needs a primary-source check before citing precisely.
- **Conditions**: Announced August 2024, supersedes the original SWE-bench and SWE-bench Lite test sets as the standard evaluation split.
- **Source**: OpenAI, "Introducing SWE-bench Verified", openai.com/index/introducing-swe-bench-verified/, Aug 2024; cross-confirmed by www.swebench.com/verified.html.
- **Quality tier**: strong-secondary (vendor announcement page, but corroborated by the benchmark's own official site swebench.com, which is maintained by the original academic authors)
- **Quote**: "a human-filtered subset of 500 instances from SWE-bench, created in collaboration with OpenAI" (swebench.com/verified.html, via WebFetch)
- **Confidence**: high (creation/size/motivation); medium (the 484-vs-500 detail, not independently confirmed against Epoch's own methodology page directly)
- **Local path**: NOT ACQUIRED (no local PDF; both are web pages, not papers — mark (web) tag if added to references.md)

### GPT-5 SWE-bench Verified score (OpenAI's own launch claim)
- **Claim**: OpenAI reported GPT-5 achieving 74.9% on SWE-bench Verified at its own launch, versus 69.1% for its predecessor o3, using a fixed n=477-task subset of Verified on OpenAI's internal harness.
- **Numbers**: GPT-5: 74.9%; o3: 69.1%. Harness subset: n=477 (OpenAI's own filtered count, distinct from both 500 and Epoch's 484 — a THIRD distinct instance count in circulation for "SWE-bench Verified", underscoring that the denominator itself varies by evaluator).
- **Conditions**: "gpt-5-thinking" variant, default API verbosity = medium, OpenAI's own eval infrastructure, launch date (GPT-5 introduced ~Aug 2025 per the "Introducing GPT-5" blog framing found in search).
- **Source**: OpenAI, "Introducing GPT-5", openai.com/index/introducing-gpt-5/, 2025; also referenced via OpenAI GPT-5 System Card (arXiv:2601.03267 per search results — NOT independently opened this session, so the arXiv id is UNVERIFIED, flagged below).
- **Quality tier**: weak-to-strong-secondary (self-reported vendor number; from the vendor's own launch blog, not independently reproduced this session)
- **Quote**: "GPT-5 sets a new state of the art in real-world coding with 74.9% on SWE-bench Verified" (via WebSearch synthesis of openai.com content — NOT a direct-fetched verbatim quote; treat with caution)
- **Confidence**: medium (search-synthesized, not directly fetched — WebFetch budget was exhausted on other pages this session)
- **Local path**: NOT ACQUIRED

### 2026 frontier leaderboard entries — UNVERIFIED, high caution
- **Claim**: Multiple WebSearch queries returned claims that, as of August 2026, the top SWE-bench Verified entries include "Claude Opus 5" (~96-97%), "DeepSeek V4 Pro 0813" (~96.4%), "Kimi K3" (~93.4%), "GPT-5.3-Codex" (mid-80s%), with intermediate Anthropic points "Claude Opus 4.5" (80.9%), "Opus 4.6" (80.84%), "Opus 4.7" (87.6%), "Opus 4.8" (88.6%).
- **Numbers**: See above; INTERNALLY INCONSISTENT across two independent search queries (one run returned "Claude Opus 5 leading at 96%" / "Claude Mythos 5 at 95.5%"; a second, separately-run query returned "Claude Opus 5 leading at 97.00%", "DeepSeek V4 Pro 0813 at 96.40%", "Kimi K3 at 93.40%" as the actual second/third place — the specific numeric value for the same claimed #1 system varied 96% vs 97% across runs of the SAME underlying search-summarization tool).
- **Conditions**: UNKNOWN — no direct fetch of the swebench.com/verified.html table succeeded (WebFetch returned only page prose, not the rendered/JS leaderboard table, both times attempted). No scaffold, date-of-submission, or attempt-count could be confirmed per entry.
- **Source**: WebSearch tool synthesis only, citing aggregator sites (morphllm.com/swe-bench-pro, benchlm.ai, localaimaster.com, steel.dev/leaderboards, llm-stats.com) and blog posts (vellum.ai, mindstudio.ai) — none independently opened this session.
- **Quality tier**: weak (search-engine-summarized secondary/tertiary aggregator content; NOT independently verified against a primary leaderboard render or vendor system card opened this session)
- **Quote**: n/a — do not quote, these are AI-search-tool paraphrases of aggregator pages, already showing internal numeric drift between two runs
- **Confidence**: low
- **Local path**: NOT ACQUIRED

**DO NOT put the "2026 frontier leaderboard entries" block into the survey's SOTA table without independent verification** — direct-browse swebench.com/verified.html (JS-rendered table, needs a headless-browser fetch, not a plain WebFetch) or fetch each vendor's own system card PDF via source-fetch. Flagged as a GAP requiring a dedicated verification pass, not filled further here per citation-integrity rule.

### SOTA table (only rows with a directly-opened or clearly-sourced primary/strong-secondary basis; unverified rows flagged)

| System | Base model | SWE-bench variant | Resolve % | Date | Source | Self-reported? |
|---|---|---|---|---|---|---|
| Claude 2 (original SWE-bench baseline) | Claude 2 | SWE-bench (original, 2,294) | 1.96% | Oct 2023 (arXiv v1) / ICLR 2024 | arXiv:2310.06770 (local PDF) | No — academic benchmark paper, third-party eval |
| GPT-5 ("gpt-5-thinking") | GPT-5 | SWE-bench Verified (OpenAI harness, n=477 subset) | 74.9% | 2025 (GPT-5 launch) | openai.com/index/introducing-gpt-5/ (via WebSearch synthesis, NOT directly fetched) | YES — vendor self-report |
| o3 | o3 | SWE-bench Verified (OpenAI harness) | 69.1% | pre-GPT-5 (2025) | same as above | YES — vendor self-report |
| "Claude Opus 5" | Claude Opus 5 | SWE-bench Verified | ~96-97% (two runs disagreed) | Aug 2026 (claimed) | UNVERIFIED aggregator/search synthesis | Unknown — GAP |
| "DeepSeek V4 Pro 0813" | DeepSeek V4 Pro | SWE-bench Verified | ~96.4% (claimed) | Aug 2026 (claimed) | UNVERIFIED aggregator/search synthesis | Unknown — GAP |
| "GPT-5.3-Codex" | GPT-5.3-Codex | SWE-bench Verified | mid-80s% (claimed, inconsistent) | 2026 (claimed) | UNVERIFIED aggregator/search synthesis | Unknown — GAP |

**Verdict on Q1**: the *provenance* facts (what SWE-bench Verified is, who made it, why, and the 500-instance size) are well-established and cross-confirmed (OpenAI announcement + official swebench.com page + academic original paper). The *current 2026 top-of-leaderboard numbers* are a GAP at publication quality — every number found this session traces only to WebSearch-tool AI summarization of secondary aggregator/blog pages, never to a directly-opened primary artifact (no vendor system card, no directly-rendered leaderboard table). This needs a dedicated follow-up with source-fetch + direct browser rendering before it can go in a cited SOTA table.


## Q2. Architecture of deployed 2025-26 coding agents

### Research-lineage baseline: SWE-agent (Agent-Computer Interface)
- **Claim**: SWE-agent (Princeton, NeurIPS 2024) established the "agent-computer interface" (ACI) pattern — a constrained, LM-friendly command set (navigate repo, search files, view files, edit lines) plus structured environment feedback — as opposed to giving the LM an unrestricted shell, and showed the interface design itself materially changes agent performance.
- **Numbers**: SWE-bench pass@1 = 12.5%; HumanEvalFix pass@1 = 87.7% (both state-of-the-art at time of publication, "far exceeding the previous state-of-the-art achieved with non-interactive LMs").
- **Conditions**: NeurIPS 2024, arXiv:2405.15793v3, dated 11 Nov 2024.
- **Source**: Yang, Jimenez, Wettig, Lieret, Yao, Narasimhan, Press, "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering", NeurIPS 2024, arXiv:2405.15793.
- **Quality tier**: primary
- **Quote**: "SWE-agent's custom agent-computer interface (ACI) significantly enhances an agent's ability to create and edit code files, navigate entire repositories, and execute tests and other programs."
- **Confidence**: high
- **Local path**: download/swe-agent-2024.pdf

### Research-lineage baseline: OpenHands (f.k.a. OpenDevin)
- **Claim**: OpenHands is an open, community-built (MIT-licensed) platform for building generalist coding/web agents that interact with a computer the way a human developer does (write code, use a CLI, browse the web), with support for sandboxed execution, multi-agent coordination, and pluggable evaluation benchmarks (SWE-bench, WebArena, and 13+ others).
- **Numbers**: 2.1K+ contributions from 188+ contributors (community scale, not a capability number); evaluated across 15+ tasks.
- **Conditions**: ICLR 2025, arXiv:2407.16741v3, dated 18 Apr 2025.
- **Source**: Wang, Li, Song, Xu, Tang, Zhuge, Pan, et al. (UIUC/CMU/Yale/UC Berkeley/Contextual AI/KAUST/ANU/HCMUT/Alibaba/All Hands AI), "OpenHands: An Open Platform for AI Software Developers as Generalist Agents", ICLR 2025, arXiv:2407.16741.
- **Quality tier**: primary
- **Quote**: "we introduce OpenHands (f.k.a. OpenDevin), a platform for the development of powerful and flexible AI agents that interact with the world in similar ways to those of a human developer: by writing code, interacting with a command line, and browsing the web."
- **Confidence**: high
- **Local path**: download/openhands-2024.pdf

### Claude Code (Anthropic) — deployed agent, documented loop and tool surface
- **Claim**: Claude Code's own documentation describes a minimal "agentic loop" architecture: the model itself decides when to call tools, which tools, and when it's done (explicitly "no DAGs, no classifiers, no RAG" per the docs/guide material found), built around a small fixed core toolset, extensible via the Model Context Protocol (MCP) for external systems (databases, internal APIs, docs, monitoring).
- **Numbers**: 8 core tools cited by secondary summaries (Bash, Read, Edit, Write, Grep, Glob, Task [sub-agents], TodoWrite) — this exact list was NOT directly fetched from code.claude.com this session (WebFetch budget exhausted), so treat the specific tool NAMES as medium confidence pending direct doc read.
- **Conditions**: Official docs domain is code.claude.com/docs/en/agent-sdk/overview ("Agent SDK overview"); MCP support confirmed as a design principle.
- **Source**: Anthropic, "Agent SDK overview", code.claude.com/docs/en/agent-sdk/overview (official docs); cross-referenced against an independent academic analysis "Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems", arXiv:2604.14228 (NOT directly opened this session — id captured from search result title only, UNVERIFIED).
- **Quality tier**: strong-secondary (official vendor docs page, found via search synthesis, not directly fetched this session — downgrade from primary until direct read)
- **Quote**: "Claude Code runs a while(tool_call) loop — no DAGs, no classifiers, no RAG, and the model itself decides when to call tools, which tools to call, and when it's done." (via WebSearch synthesis, paraphrase risk — NOT a confirmed verbatim quote from the primary doc)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Codex CLI (OpenAI) — deployed agent, documented loop, sandbox, and repo-context handling
- **Claim**: OpenAI has published its own technical walkthrough of the Codex agent loop ("Unrolling the Codex agent loop"), and Codex CLI is architecturally split into a thin TypeScript launcher (`codex-cli/`) and a Rust implementation (`codex-rs/`, 60+ crates covering CLI, TUI, core agent logic, sandboxing, auth, MCP). Sandboxing is scoped to the tool calls the agent executes (bubblewrap on Linux, Docker devcontainer support), not the orchestrating process itself. The system uses stateless request handling (for Zero Data Retention compliance), prompt-caching to make multi-turn cost near-linear rather than quadratic, and automatic context-window compaction across long tool-call sequences.
- **Numbers**: 60+ Rust crates (component count, not a capability metric); "hundreds of model-tool iterations" cited as the scale of multi-turn conversations the harness is designed to sustain.
- **Conditions**: Model cited in one secondary source as "GPT-5.1 Codex Max" combined with a "custom API layer" and IDE-extension/CLI harness.
- **Source**: OpenAI, "Unrolling the Codex agent loop", openai.com/index/unrolling-the-codex-agent-loop/ (official vendor technical blog post — NOT directly fetched this session, found via search); secondary corroboration via ZenML LLMOps Database write-up (zenml.io) and Agent Safehouse sandbox analysis (agent-safehouse.dev) — both independent third-party technical analyses, not vendor marketing.
- **Quality tier**: strong-secondary (the OpenAI blog post itself would be primary/strong-secondary; not directly fetched this session so downgraded; the ZenML and Agent Safehouse write-ups are independent technical analyses, also strong-secondary in nature but not opened directly either)
- **Quote**: "Codex sandboxes its own tool calls, not itself. The main Codex process runs unsandboxed; only the shell commands it executes for the AI are sandboxed." (via WebSearch synthesis)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Cursor — repo-context handling documented, architecture largely third-party
- **Claim**: Cursor (VS Code fork) builds a semantic vector index of the codebase (files chunked by function/class/logical block, embedded, searched via `@codebase`) to select context, and exposes three interaction modes of increasing autonomy (Tab completion, Chat, Composer/agent).
- **Numbers**: none found (no vendor-disclosed index size, latency, or accuracy numbers surfaced this session).
- **Conditions**: unspecified model backend (Cursor is model-agnostic / multi-model by design per general knowledge, not independently confirmed this session).
- **Source**: No official cursor.com/docs page surfaced in results this session — every source returned was a third-party guide/blog (myengineeringpath.dev, datalakehousehub.com, techjacksolutions.com, eastondev.com, educative.io). This is a genuine documentation gap relative to Claude Code / Codex / Copilot, which do have identifiable first-party doc pages.
- **Quality tier**: weak (all sources found are third-party explainer blogs, not vendor documentation or independent technical papers)
- **Quote**: n/a
- **Confidence**: low
- **Local path**: NOT ACQUIRED
- **GAP**: a direct fetch of docs.cursor.com (not searched this session, budget-limited) is needed before citing Cursor's architecture with any confidence.

### GitHub Copilot agent mode / coding agent — official vendor documentation exists
- **Claim**: GitHub/Microsoft has substantive first-party documentation for two related surfaces: "agent mode" in VS Code (synchronous, in-editor, multi-step: plan -> execute -> validate orchestration with parallel sub-agent background task delegation) and the separate "Copilot coding agent" / "cloud agent" (asynchronous, works from a GitHub-hosted environment, opens PRs). A Copilot code-review feature was re-shipped on an agentic architecture that "gathers full project context before analyzing a pull request."
- **Numbers**: code-review-on-agentic-architecture ship date = March 5, 2026 (a real dated product event, distinguishable from vague marketing).
- **Conditions**: VS Code Copilot agent mode announced as preview Feb 24, 2025 per the VS Code blog title/date found in search results.
- **Source**: GitHub/Microsoft, "Introducing GitHub Copilot agent mode (preview)", code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode; GitHub, "About GitHub Copilot cloud agent", docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent; GitHub Blog, "Agent mode 101", github.blog/ai-and-ml/github-copilot/agent-mode-101-all-about-github-copilots-powerful-mode/.
- **Quality tier**: strong-secondary (all three are first-party vendor documentation/blog domains — code.visualstudio.com, docs.github.com, github.blog — but none directly fetched this session, so treat specific phrasing as search-synthesized paraphrase, not verbatim)
- **Quote**: "an autonomous and agentic real-time, synchronous collaborator that performs multi-step coding tasks based on natural-language prompts" (via WebSearch synthesis of github.blog content)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Devin (Cognition) — vendor marketing dominant, technical detail thin
- **Claim**: Cognition's own materials describe Devin as a "compound AI system" ("a swarm of specialized models" rather than one model) operating in a sandboxed environment with its own shell, editor, and browser, designed for long-horizon multi-step autonomous execution. Critically, Cognition's initial launch announcement stated a more detailed technical report was forthcoming, and this session's search found no evidence such a detailed report has since been published — third-party sources explicitly note "a comprehensive official technical report may not be publicly available yet."
- **Numbers**: one secondary/press source claims Devin "now produces 25% of Cognition's [own] code" (dated Dec 30, 2025, financialcontent.com/tokenring wire syndication) — this is a THIRD-PARTY WIRE STORY, not a Cognition-published number; treat as unverified marketing-adjacent claim, not a benchmark result.
- **Conditions**: unspecified benchmark/eval basis for the "25%" figure — no methodology given in the snippet.
- **Source**: Cognition, "Introducing Devin, the first AI software engineer", cognition.com/blog/introducing-devin (vendor launch blog); cross-referenced against markets.financialcontent.com/wral/article/tokenring-2025-12-30 (wire/syndicated business-press piece, weak tier) and independent Medium technical deep-dive (also weak tier, unaffiliated author).
- **Quality tier**: weak (vendor marketing blog for the architecture claims; a syndicated wire story for the one number found — neither is a technical report or independent benchmark)
- **Quote**: "Devin operates on a compound AI system architecture and is not a single model but a swarm of specialized models orchestrating a workflow." (via WebSearch synthesis)
- **Confidence**: low
- **Local path**: NOT ACQUIRED
- **Explicit finding**: this session found NO evidence of a Cognition-published technical report or system card for Devin — this itself is a documented gap, not an oversight in search effort.

### Google Jules — official Google blog documentation, cloud-VM architecture
- **Claim**: Jules (Google Labs) is an asynchronous coding agent that clones a target repository into an isolated Google Cloud VM, plans with a Gemini model, executes edits/tests/iterations inside the VM, opens a pull request on completion, then tears the VM down. Google frames the cloud-VM isolation (vs. running synchronously on the developer's own machine) as the key architectural differentiator, enabling concurrent multi-task execution without consuming local resources. Google states Jules does not train on private code and isolates data within the execution environment.
- **Numbers**: none found (no published resolve-rate, latency, or benchmark numbers surfaced this session for Jules specifically).
- **Conditions**: model backend documented as having moved from Gemini 2.5 Pro to Gemini 3 Pro (staged rollout: Google AI Ultra subscribers first, then Pro plan).
- **Source**: Google, "Jules: Google's autonomous AI coding agent", blog.google/innovation-and-ai/models-and-research/google-labs/jules/ (official Google blog); Google Developers Blog, "Building with Gemini 3 in Jules", developers.googleblog.com/jules-gemini-3/.
- **Quality tier**: strong-secondary (official first-party vendor blogs, not directly fetched this session)
- **Quote**: "Running in a cloud VM is the single most important architectural choice Jules made, as synchronous tools run on your machine and compete for resources, whereas a Jules task takes nothing from you once it is submitted." (via WebSearch synthesis)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

**Cross-system pattern observed**: every deployed 2025-26 commercial agent (Claude Code, Codex CLI, Copilot agent mode, Jules) converges on the SAME architectural shape documented years earlier by the academic SWE-agent/OpenHands lineage: an LM-driven loop, a constrained/sandboxed tool surface, and iterate-until-done semantics — the commercial differentiation is in deployment surface (sync IDE-embedded vs async cloud-VM), sandboxing implementation, and context/compaction engineering, not in a fundamentally different agent loop shape. This is an interpretive synthesis by this agent, not a sourced claim from any one document — flag for the writing-stage author to decide whether/how to state it.

## Q3. Cost, latency, and token economics per resolved task

This axis is exactly as sparse as the brief predicted. One genuinely primary/academic source was found (Holistic Agent Leaderboard); everything else is vendor-adjacent blog arithmetic (weak tier). Reporting what exists; marking the rest GAP per instructions rather than filling with unsourced numbers.

### Holistic Agent Leaderboard (HAL) — standardized cost-tracked agent evaluation
- **Claim**: HAL is an academic benchmarking-infrastructure project that runs standardized agent harnesses across 9 benchmarks (including SWE-bench Verified Mini and USACO for coding) with centralized, methodologically-disclosed cost tracking (API costs plus GPU compute normalized to USD), explicitly to make cross-paper cost comparisons possible where none previously existed.
- **Numbers**: 21,730 total agent rollouts across 9 models x 9 benchmarks, total cost approx \$40,000 (≈\$1.84/rollout average, aggregate not per-coding-task). Cost-normalization rates disclosed: GPU compute at \$2.50/H100-hour, \$1.50/A10-hour. Per-model example on SWE-bench-Verified-Mini (50 tasks): SWE-Agent + o4-mini (low reasoning effort) = 54.0% accuracy at \$259.20 total run cost (≈ \$5.18/task); GPT-5 (medium reasoning effort) = 46.0% accuracy at \$162.93 total run cost (≈ \$3.26/task). Explicit finding: "higher reasoning effort reducing accuracy in the majority of runs" — i.e., cost and accuracy do NOT trade off monotonically in their data.
- **Conditions**: SWE-bench Verified Mini (a reduced-size variant of Verified — exact N not confirmed this session, flag as GAP), various models/scaffolds, HAL's own standardized harness (not each vendor's own harness) — this is a controlled, apples-to-apples comparison, which is rare in this literature.
- **Source**: "Holistic Agent Leaderboard: The Missing Infrastructure for AI Agent Evaluation", arXiv:2510.11977 (abstract page confirmed via search: arxiv.org/abs/2510.11977).
- **Quality tier**: strong-secondary (arXiv paper, methodologically disclosed cost accounting — NOT directly opened/read this session, so treat exact per-model \$ figures as medium confidence pending a direct PDF read)
- **Quote**: "21,730 agent rollouts across 9 models and 9 benchmarks ... with a total cost of about \$40,000" (via WebSearch synthesis, not a verbatim-confirmed quote)
- **Confidence**: medium (paper existence and topic: high; specific dollar figures per model: medium, not independently re-derived from primary text this session)
- **Local path**: NOT ACQUIRED — recommend acquiring via source-fetch for the survey's cost-economics subsection.

### METR — task-length / time-horizon as a capability-trajectory proxy (adjacent to, not the same as, \$ economics)
- **Claim**: METR (a third-party AI safety/evaluations research org, not a vendor) measured the length of tasks (as timed for human professionals, 30 seconds to 8+ hours) that frontier agents can complete at a 50% success rate, across ~230 tasks (mostly coding, some general reasoning), from models spanning 2019-2026(current). They report task length is highly correlated with agent success rate (R-squared = 0.83), and the "50% time horizon" has grown exponentially with a ~7-month doubling time over 2019-2025, ACCELERATING to a ~4-month doubling time within 2024-2025 specifically.
- **Numbers**: R² = 0.83 (task-length vs. success-rate correlation); doubling time ≈ 7 months (2019-2025 trend); doubling time ≈ 4 months (2024-2025 trend, i.e. faster than the long-run trend); ~230 tasks in the evaluation set.
- **Conditions**: METR's own task suite (not SWE-bench); "50% time horizon" = the task duration (in human-professional-equivalent time) at which the agent succeeds half the time — this is a capability/reliability metric, NOT a dollar-cost or token-count metric. One search snippet also mentioned a "\$20 budget" figure attributed to METR methodology in a DIFFERENT secondary source (a blog comparing to a "\$30-50/task" Gemini 2.5 Pro estimate) — this \$20 figure was NOT independently confirmed against metr.org directly this session; flag as unverified pending direct fetch.
- **Source**: METR, "Measuring AI Ability to Complete Long Software Tasks", metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/, and the companion paper "Measuring AI Ability to Complete Long Tasks", arXiv:2503.14499 (dated 19 Mar 2025 per HTML version found). Follow-on posts found but not opened: "How Does Time Horizon Vary Across Domains?" (metr.org, 14 Jul 2025) and "Time Horizon 1.1" (metr.org, 29 Jan 2026) — the latter suggests METR has an actively maintained/updated version of this metric through early 2026.
- **Quality tier**: strong-secondary (METR is an independent, non-vendor research org; this is their own published methodology page + arXiv paper — would be primary if directly opened; downgraded because not directly fetched this session)
- **Quote**: "the length of tasks that agents succeed at 50% of the time is growing exponentially with no evidence of plateauing" (via WebSearch synthesis)
- **Confidence**: medium-high (multiple independent search results corroborate the same R²=0.83 and doubling-time figures consistently across different query runs, which is a stronger consistency signal than the leaderboard-number searches in Q1)
- **Local path**: NOT ACQUIRED — strong candidate for source-fetch acquisition; this is likely one of the single best-evidenced quantitative claims found in this entire C2 pass and probably belongs in the survey's capability-trajectory discussion, not just a cost aside.

### Token-volume and cost-per-task blog estimates — weak tier, reported for completeness only
- **Claim**: multiple secondary/vendor-adjacent blogs (Vantage, Augment Code, MorphLLM, Doit, WhatLLM.org) offer cost-per-task and token-volume estimates for agentic coding sessions, but NONE were independently verified this session and they visibly disagree with each other by more than an order of magnitude.
- **Numbers** (all UNVERIFIED, reported only to show the spread): one source claims agentic coding tasks run \$0.03-\$2.60/task (mid-2026, "\$0.03-\$0.13/task depending on model/tool" in one narrower claim); another cites a 50-turn coding session at ~1M input tokens / 40K output tokens (≈25:1 input:output ratio); another (Gartner, cited secondhand, March 2026) claims agentic workflows burn 5-30x more tokens per task than a simple chatbot query; one specific large-scale claim: "Bun reported token consumption of 5.9 billion uncached input tokens, 690 million output tokens, and 72 billion cached input reads, for a total API-rate cost of approximately \$165,000" (a real named project — Bun, the JS runtime — but the claim traces to a secondary aggregator, not directly to Bun's own disclosure, this session).
- **Conditions**: heterogeneous, largely unstated — different models, different tools (Aider, Claude Code, OpenHands mentioned by name), different measurement windows. Not comparable to each other.
- **Source**: various — vantage.sh/blog/agentic-coding-costs; augmentcode.com/guides/ai-coding-cost-analysis-agent-token-spend; morphllm.com/ai-coding-costs; doit.com/blog/cost-per-task-vs-cost-per-token; whatllm.org/blog/agentic-ai-cost-per-task. None opened directly.
- **Quality tier**: weak (vendor blogs / cost-monitoring SaaS marketing content, not benchmark papers or vendor technical disclosures)
- **Quote**: n/a — internally inconsistent numbers across sources, do not quote as fact
- **Confidence**: low
- **Local path**: NOT ACQUIRED

### GAP: attempts-per-solve / pass@k economics for agentic (not sampling-based) coding
- No source found this session reporting an "attempts-per-solve" or retry-budget economics number specifically for AGENTIC coding tasks (as distinct from sampling-based pass@k on function-level code generation, which is a different, better-documented literature — see openai-competitive-programming-2025.pdf, NOT examined this session for this question but flagged as a locally-available source that likely covers pass@k economics for competitive programming, a related but distinct task type from SWE-bench-style repo agentic tasks).
- **GAP explicitly recorded, not filled.**

### GAP: wall-clock latency per resolved SWE-bench task
- No source found this session giving a clean wall-clock-minutes-per-task number tied to a specific model+SWE-bench-Verified result (e.g., "Claude Opus X takes N minutes median wall-clock per resolved instance"). The HAL paper likely has this data (it tracks rollouts) but the specific number was not surfaced in search snippets and the paper was not directly opened.
- **GAP explicitly recorded, not filled.**

## Q4. Autonomy-level taxonomies + human oversight / productivity evidence

### "Levels of Autonomy for AI Agents" — an actual peer-reviewed-adjacent taxonomy paper
- **Claim**: Feng, McDonald, and Zhang propose a 5-level autonomy taxonomy for AI agents generally (not coding-specific), defined not by capability but by the ROLE the human user takes when interacting with the agent: operator, collaborator, consultant, approver, observer (ascending autonomy). Their explicit thesis: autonomy level is a deliberate, separable DESIGN decision, not simply a function of the underlying model's capability or its deployment environment — i.e., two agents built on the same model can be deliberately configured to different autonomy levels.
- **Numbers**: 5 levels (operator / collaborator / consultant / approver / observer).
- **Conditions**: general AI-agent framework, not coding-specific; has at least a v2 revision on arXiv.
- **Source**: K. J. Kevin Feng, David W. McDonald, Amy X. Zhang, "Levels of Autonomy for AI Agents", arXiv:2506.12469 (v2), 2025.
- **Quality tier**: strong-secondary (arXiv preprint; author identities and abstract corroborated across independent listings — arXiv abstract page, ADS/Harvard astrophysics-data-system cross-index, Semantic Scholar — but the PDF itself not directly opened this session)
- **Quote**: "five levels of escalating agent autonomy, characterized by the roles a user can take when interacting with an agent: operator, collaborator, consultant, approver, and observer" (via WebSearch synthesis)
- **Confidence**: medium-high (paper identity/authors well corroborated across independent indices; framework description consistent across sources)
- **Local path**: NOT ACQUIRED — recommend acquiring for the survey; this looks like the most citable, non-coding-specific general autonomy taxonomy found.

### Coding-specific autonomy taxonomies — mostly informal/blog, one academic exception
- **Claim**: Multiple informal industry blog posts (tessl.io, swarmia.com, mindstudio.ai) explicitly propose a "5 levels of AI coding agent autonomy" framework EXPLICITLY analogized to SAE self-driving-car autonomy levels (0-5), running roughly: Level 0/1 = autocomplete-style suggestion (explicitly, GitHub Copilot's base completion mode is placed at "Level 1" by one source), up through chat-assist, supervised/reviewed agent, and fully autonomous ("dark factory" in one source's terminology for the top level). Separately, one ACADEMIC source — a survey on retrieval-augmented code generation — proposes a narrower, code-generation-specific 3-tier taxonomy: Level 0 = non-agent/static single-pass pipelines, Level 1 = partial-agent systems with an iterative feedback loop but no autonomous planning/tool orchestration, Level 2 = fully autonomous agents (implied, planning + tool orchestration — exact Level 2 description not captured in the snippet).
- **Numbers**: 5 informal levels (blog framework); 3 academic levels (RACG survey framework) — TWO DIFFERENT, NON-ALIGNED taxonomies exist in current use, not one canonical standard.
- **Conditions**: the informal 5-level framework is explicitly and self-consciously modeled on SAE J3016 driving-autonomy levels (the analogy the brief's UNVERIFIED PRIOR asked about is confirmed to exist in the wild, but its most visible instances are industry blogs, not standards bodies or peer-reviewed papers).
- **Source**: informal — tessl.io/blog/the-5-levels-of-ai-agent-autonomy-learning-from-self-driving-cars/; swarmia.com/blog/five-levels-ai-agent-autonomy/; mindstudio.ai/blog/agentic-coding-levels-explained. Academic — "Retrieval-Augmented Code Generation: A Survey with Focus on Repository-Level Approaches", arXiv:2510.04905.
- **Quality tier**: weak (the 5-level informal framework — vendor/industry blogs, no peer review, no canonical body); strong-secondary (the RACG survey's embedded 3-tier taxonomy, arXiv preprint, though not directly opened this session)
- **Quote**: "GitHub Copilot operates at Level 1 — it completes code as you type, one suggestion at a time" (via WebSearch synthesis, illustrating the informal framework's granularity)
- **Confidence**: medium (existence of both taxonomies: high, corroborated by multiple independent search hits; that they are NOT unified into one standard: this is an interpretive observation by this agent based on the search evidence, not a sourced claim)
- **Local path**: NOT ACQUIRED
- **CORRECTS the brief's framing**: there is no single dominant "the" autonomy taxonomy for coding agents in current use for evaluation purposes — what exists is (a) informal, non-peer-reviewed industry blog frameworks explicitly borrowing the driving-autonomy analogy, and (b) at least one narrower academic taxonomy embedded in a code-generation survey, plus (c) a general (non-coding) peer-reviewed-adjacent taxonomy (Feng/McDonald/Zhang) that could be, but was not found to be, specifically applied to coding-agent evaluation in any source surfaced this session.

### METR RCT — measured productivity effect of agentic AI coding tools (the strongest single finding in this cluster)
- **Claim**: METR ran a randomized controlled trial in which 16 experienced open-source developers (average ~5 years of prior experience in the specific repositories used) completed 246 real GitHub issues in repositories they already knew well, with each task randomly assigned to an "AI allowed" or "AI disallowed" condition. When AI was allowed, developers primarily used Cursor Pro with Claude 3.5 Sonnet or Claude 3.7 Sonnet (chat, agent mode, and autocomplete features available). The measured result: developers took 19% LONGER to complete tasks when AI tools were allowed (i.e., AI tools measurably slowed these experienced developers down on their own familiar codebases) — the opposite direction from the developers' own before-and-after beliefs: they predicted a 24% speedup beforehand and, even after completing the study and experiencing the slowdown, still estimated afterward that AI had made them approximately 20% faster.
- **Numbers**: N=246 tasks; N=16 developers; ~5 years average prior repo experience; measured effect = 19% SLOWER with AI allowed; pre-registered developer expectation = 24% faster; post-hoc developer self-estimate = 20% faster (i.e., a ~39-43 percentage-point gap between measured reality and developer perception, in both directions of the prediction).
- **Conditions**: early-2025 AI tooling (Cursor Pro + Claude 3.5/3.7 Sonnet — NOT the most current 2026 models); real-world, developer-familiar repositories (not a synthetic benchmark like SWE-bench); experienced professional developers, not students or novices. METR has since published a follow-up ("We are Changing our Developer Productivity Experiment Design", metr.org/blog/2026-02-24-uplift-update/) indicating the org is iterating on this experimental design as of Feb 2026 — suggesting they consider the original design to have limitations worth revising (specifics of what changed NOT captured this session).
- **Source**: Joel Becker, Nate Rush, Elizabeth Barnes, David Rein, "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity", METR, arXiv:2507.09089, July 2025 (also metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/).
- **Quality tier**: strong-secondary (METR is an independent, non-vendor research org; arXiv preprint with a clear RCT design — would be primary if directly opened; this session found the paper via search synthesis only, not a direct fetch, so treat the exact percentages as medium-high rather than fully verified confidence)
- **Quote**: "experienced developers completed real coding tasks 19% slower when allowed to use AI tools — yet afterwards, they estimated on average that AI had made them 20% faster" (via WebSearch synthesis of the paper's reported headline finding; corroborated near-identically across THREE independent search-result snippets — ScienceBlog.com, vibegraveyard.ai, and the WebSearch tool's own synthesis — which is a strong consistency signal, though none of the three is the primary text itself)
- **Confidence**: medium-high
- **Local path**: NOT ACQUIRED — this is the single highest-priority acquisition target from this entire C2 pass for the survey's human-oversight/productivity discussion; strongly recommend source-fetch of arXiv:2507.09089.

### Pull-request review burden and acceptance-rate data — a comparative academic study exists
- **Claim**: A study comparing pull requests authored by different AI coding agents found GitHub Copilot-authored PRs receive substantially MORE reviewer scrutiny (reviews per PR) than OpenAI Codex-authored PRs, while simultaneously having a LOWER acceptance rate — i.e., the two systems differ measurably in how much human review burden they impose and how often their output is ultimately accepted.
- **Numbers**: GitHub Copilot: 4.94 reviews/PR, 68.0% acceptance rate. OpenAI Codex: 1.39 reviews/PR, 77.9% acceptance rate.
- **Conditions**: "task-stratified" analysis (i.e., controlled/broken-down by task type) — exact task categories, repository population, and date range of the underlying PR data were NOT captured in the search snippet; flag as needing direct-source confirmation before citing precisely.
- **Source**: "Comparing AI Coding Agents: A Task-Stratified Analysis of Pull Request Acceptance", arXiv:2602.08915 (title and numbers found via WebSearch synthesis, paper NOT directly opened this session).
- **Quality tier**: strong-secondary (arXiv paper with a specific comparative empirical design; downgraded from primary because not directly opened this session and the arXiv id itself was surfaced only via search title, not independently cross-confirmed the way the METR and Feng/McDonald/Zhang papers were)
- **Quote**: "GitHub Copilot PRs receive substantially more reviews (4.94/PR) than OpenAI Codex PRs (1.39/PR), coinciding with lower acceptance rates (68.0% vs. 77.9%)" (via WebSearch synthesis)
- **Confidence**: medium (single-query surfacing, not cross-corroborated by a second independent search the way other Q4 findings were — treat with more caution than the METR RCT numbers)
- **Local path**: NOT ACQUIRED

### General GitHub Copilot acceptance-rate figures (baseline autocomplete, not agentic) — mixed-quality, illustrates the completion-vs-agent distinction
- **Claim**: Multiple sources report GitHub Copilot's baseline code-SUGGESTION acceptance rate (i.e., the autocomplete/completion tier, not agent mode) clustering around 21-31% across different studies, with one GitHub+Accenture enterprise study citing ~30% and up to 43-55% for chat-based or first-option suggestions specifically; a Communications of the ACM study is cited as reporting 21.2-23.5%, with a counter-intuitive finding that LESS experienced developers had a HIGHER acceptance rate (31.9%) than the MOST experienced developers (26.2%).
- **Numbers**: ~21-31% general acceptance rate range; 43% for chat; 55% for "first option, some users"; CACM study: 21.2-23.5% overall, 31.9% (less experienced) vs 26.2% (most experienced) split; Accenture: 15% increase in PR merge rate, 84% increase in successful builds (attributed to Copilot deployment, exact causal methodology not captured in snippet).
- **Conditions**: this data is about the COMPLETION/autocomplete tier of Copilot, explicitly NOT the agentic tier — important for the survey to keep this axis separate from the agent-mode PR-review-burden data above, since they measure different products/modes.
- **Source**: multiple secondary aggregator/statistics-roundup sites (wearetenet.com, quantumrun.com, gitnux.org, companieshistory.com) citing an unnamed "Communications of the ACM" study and an unnamed "GitHub + Accenture" study — NEITHER primary study was directly identified by title/author/year in the search snippets, only referenced secondhand.
- **Quality tier**: weak (secondary statistics-roundup blogs; the two underlying primary studies they cite were NOT independently located/verified this session — this is exactly the "memory-drift" risk the brief warned about, except here it is the search tool's sources drifting, not this agent's memory)
- **Quote**: n/a — do not cite the specific percentages without locating and opening the actual CACM paper and the actual GitHub/Accenture study first
- **Confidence**: low
- **Local path**: NOT ACQUIRED
- **GAP**: the primary CACM study and the primary GitHub/Accenture study need to be located by title/author before any of these acceptance-rate numbers can be cited in the survey.

## Gaps

1. **Q1 — current (Aug 2026) SWE-bench Verified top-of-leaderboard numbers**: NOT reliably established this session. Every specific 2026 leaderboard number found (Claude Opus 5, DeepSeek V4 Pro, Kimi K3, GPT-5.3-Codex, etc.) traces only to WebSearch-tool AI-summarized secondary/tertiary aggregator content, and the SAME underlying claim (top system's resolve %) varied between 96% and 97% across two independent search runs of ostensibly the same leaderboard. Both direct-fetch attempts at the two most authoritative pages (swebench.com/verified.html, epoch.ai/benchmarks/swe-bench-verified) returned page prose/methodology but not the rendered results table (likely JS-rendered, not captured by a plain-text WebFetch). **Needs a dedicated follow-up with either a headless-browser-capable fetch or vendor system-card acquisition via source-fetch.**
2. **Q1 — denominator inconsistency**: three different instance counts are in circulation for "SWE-bench Verified" evaluation runs: 500 (the original release size), 484 (cited for Epoch AI's harness), and 477 (cited for OpenAI's own GPT-5 harness). This is not necessarily an error — different evaluators may legitimately exclude different unusable instances — but the survey must not silently treat "SWE-bench Verified %" as a single comparable basis across vendors without checking each one's N. This is exactly the kind of metric-basis issue `.claude/rules/calibration-residuals.md` check 4 exists to catch.
3. **Q2 — Claude Code and Codex CLI official docs not directly fetched.** Both have identifiable first-party documentation pages (code.claude.com/docs/en/agent-sdk/overview; openai.com/index/unrolling-the-codex-agent-loop/) but this session's WebFetch budget (2 calls) was spent on the Q1 leaderboard attempts, which yielded no result. In retrospect, spending WebFetch on these two vendor doc pages instead would likely have produced primary-tier Q2 evidence; flagging for the next pass.
4. **Q2 — Cursor has no identifiable first-party architecture documentation.** Every source found was a third-party blog/guide. This is a genuine finding (not a search failure) worth stating in the survey: Cursor's public documentation posture is thinner than Claude Code / Codex / Copilot on architecture specifics, at least via search-engine discoverability.
5. **Q2 — Devin has no published technical report as of this session's search.** Cognition's 2024 launch post promised one; no evidence found that it has shipped. Worth an explicit statement in the survey rather than treating Devin's architecture as documented to the same standard as its competitors.
6. **Q3 — wall-clock latency per resolved SWE-bench task**: no source found. Likely exists inside the Holistic Agent Leaderboard (arXiv:2510.11977) dataset given it tracks full rollouts, but the specific number was not surfaced in search snippets.
7. **Q3 — attempts-per-solve / retry-budget economics for agentic (not sampling-based pass@k) coding**: no source found. `download/openai-competitive-programming-2025.pdf` (available locally, NOT examined this session for this specific question) plausibly covers pass@k economics for competitive programming, but that is a different task family from repo-level SWE-bench-style agentic tasks — do not conflate the two literatures without checking.
8. **Q3 — every specific \$/task and token-volume blog estimate is uncorroborated** and the blog sources disagree with each other by more than an order of magnitude (\$0.03-\$2.60/task claims from different posts). Do not cite any single one of these without independent verification; the HAL paper (arXiv:2510.11977) is the one credible quantitative anchor found and should be acquired and read directly.
9. **Q4 — the primary sources behind the "21-31% Copilot completion acceptance rate" and "Accenture 15%/84%" figures were never identified by title/author.** These numbers are currently third-hand (statistics-roundup blogs citing an unnamed CACM study and an unnamed GitHub/Accenture study). Do not cite until the underlying studies are located.
10. **Q4 — "Comparing AI Coding Agents: A Task-Stratified Analysis of Pull Request Acceptance" (arXiv:2602.08915)** was surfaced by only ONE search query, unlike the METR RCT and the Feng/McDonald/Zhang taxonomy paper, both of which were independently corroborated across multiple queries/indices. Treat its specific numbers (4.94 vs 1.39 reviews/PR; 68.0% vs 77.9% acceptance) as needing independent confirmation before the survey cites them.
11. **General**: NONE of the arXiv papers surfaced in Q1/Q3/Q4 (2510.11977, 2503.14499, 2507.09089, 2506.12469, 2602.08915) were directly opened/read this session — all evidence for them rests on WebSearch-tool synthesis of secondary pages describing them, not on this agent reading the primary text. This is disclosed per-record above (quality tier and confidence downgrades), but the parent survey process should treat every one of these as a HIGH-PRIORITY source-fetch + direct-read target before the survey cites specific numbers from them, per `.claude/rules/citation-integrity.md`.

## Corrections to the brief

- **Q1's UNVERIFIED PRIOR was CONFIRMED, with one refinement**: SWE-bench Verified is indeed a 500-problem human-validated subset, but produced by **OpenAI in collaboration with the original SWE-bench authors** (not "by OpenAI" alone, and not by the academic authors alone) — it is explicitly a joint effort, announced August 2024, and it fixed three specific documented problems: incorrect grading of correct solutions, under-specified problem statements, and overly-specific unit tests. The brief's phrasing "released by OpenAI in 2024" is directionally correct but slightly understates the SWE-bench-author involvement; use "OpenAI, in collaboration with the SWE-bench authors" in the survey.
- **Q4's autonomy-taxonomy prior needs correction**: the brief frames this as if a single established taxonomy exists ("completion -> chat -> supervised agent -> autonomous"). What was actually found is a FRAGMENTED landscape: an informal, explicitly SAE-driving-autonomy-inspired 5-level framework that lives only in industry blogs (weak tier, no single canonical source), a narrower 3-tier academic taxonomy specific to retrieval-augmented code generation (arXiv:2510.04905), and a general (non-coding-specific) 5-role taxonomy from an actual arXiv paper (Feng/McDonald/Zhang, arXiv:2506.12469) that was NOT found to be applied specifically to coding-agent evaluation by any source surfaced this session. The survey should present this fragmentation honestly rather than implying a settled taxonomy exists.
- **No correction needed, but worth flagging**: the brief's expectation that Q3 (cost economics) would be the sparsest axis was correct — it is the only question of the four where the majority of what was found had to be marked weak-tier or GAP rather than reported as citable evidence.

## Sources worth acquiring (precise arXiv ids / titles, for source-fetch)

1. **arXiv:2510.11977** — "Holistic Agent Leaderboard: The Missing Infrastructure for AI Agent Evaluation" — HIGH PRIORITY for Q3 (cost economics) and Q1 (a standardized alternative to vendor-reported SWE-bench numbers).
2. **arXiv:2503.14499** — METR, "Measuring AI Ability to Complete Long Tasks" (companion to the metr.org blog "Measuring AI Ability to Complete Long Software Tasks", 19 Mar 2025) — HIGH PRIORITY for Q3/Q4 (capability-trajectory / time-horizon evidence).
3. **arXiv:2507.09089** — Becker, Rush, Barnes, Rein, "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity" (METR) — HIGHEST PRIORITY overall; the single best-evidenced human-oversight/productivity finding in this cluster (RCT design, named authors, N=246 tasks / 16 developers).
4. **arXiv:2506.12469** (v2) — Feng, McDonald, Zhang, "Levels of Autonomy for AI Agents" — HIGH PRIORITY for Q4 (general autonomy taxonomy).
5. **arXiv:2602.08915** — "Comparing AI Coding Agents: A Task-Stratified Analysis of Pull Request Acceptance" — MEDIUM PRIORITY for Q4 (review-burden/acceptance-rate data); single-query corroboration only, verify the id resolves before citing.
6. **arXiv:2510.04905** — "Retrieval-Augmented Code Generation: A Survey with Focus on Repository-Level Approaches" — MEDIUM PRIORITY for Q4 (the 3-tier academic autonomy taxonomy) and possibly general C-cluster background.
7. Official vendor doc pages (not papers, but should be acquired/archived for citation stability): code.claude.com/docs/en/agent-sdk/overview (Claude Code / Agent SDK); openai.com/index/unrolling-the-codex-agent-loop/ (Codex agent loop); docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent and code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode (Copilot agent mode); blog.google/innovation-and-ai/models-and-research/google-labs/jules/ (Jules).
8. **NOT found / do not fabricate an id**: an arXiv id for the OpenAI GPT-5 System Card was reported by the search tool as "arXiv:2601.03267" but this was NEVER independently opened or cross-confirmed this session — verify this id resolves to the actual GPT-5 system card before using it in the survey; treat as unverified until checked directly (this is flagged, not asserted, per citation-integrity rule).

## Budget accounting

WebSearch calls used: 20 of 21 (1 remaining, unused — closed out with sufficient evidence per question rather than spending the last call speculatively). WebFetch calls used: 2 of 2 (both spent attempting direct leaderboard-table reads; both returned page prose rather than the rendered table — see Gap 1). Local PDFs read: swe-bench-2023.pdf, swe-agent-2024.pdf, openhands-2024.pdf (1 page each, front matter/abstract only). All 4 questions completed; no budget-exhaustion truncation occurred.
