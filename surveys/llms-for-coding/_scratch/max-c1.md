# C1 — Agent loop, protocols, context (2025–26)

## Q1. Agent-computer interface evolution past SWE-agent (2024)

### SWE-agent's four ACI design principles (baseline, confirmed from PDF)
- **Claim**: SWE-agent (Princeton, NeurIPS 2024) defines four ACI design principles: (1) actions should be simple and easy to understand for agents, (2) actions should be compact and efficient, (3) environment feedback should be informative but concise, (4) guardrails (e.g. a syntax linter wired into the edit command) mitigate error propagation and hasten recovery.
- **Numbers**: SWE-agent w/ GPT-4 Turbo resolves 12.47% (286/2,294) of full SWE-bench test set, 18.00% (54/300) of SWE-bench Lite; vs. 3.8% for prior non-interactive RAG baseline; Shell-only (raw bash, no custom ACI) gets 11.00% Lite; ablating the custom edit command drops Lite from 18.0% to 10.3% (edit action alone, no linting: 15.0%, w/ linting: 18.0%); "No edit" ablation gives 10.3% (a 7.7-point drop). Claude 3 Opus via same ACI: 10.46% full / 13.00% Lite.
- **Conditions**: GPT-4 Turbo (gpt-4-1106-preview) and Claude 3 Opus (claude-3-opus-20240229); SWE-bench full test set (2,294 instances) and SWE-bench Lite (300 instances); pass@1 = %Resolved.
- **Source**: Yang, Jimenez, Wettig, Lieret, Yao, Narasimhan, Press, "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," NeurIPS 2024, arXiv:2405.15793v3.
- **Quality tier**: primary
- **Quote**: "1. Actions should be simple and easy to understand for agents... 2. Actions should be compact and efficient... 3. Environment feedback should be informative but concise... 4. Guardrails mitigate error propagation and hasten recovery."
- **Confidence**: high
- **Local path**: download/swe-agent-2024.pdf

### Claude's SWE-bench agent: two-tool minimalism (Anthropic, Jan 2025)
- **Claim**: Anthropic's own SWE-bench agent scaffold for Claude 3.5 Sonnet (new) deliberately narrowed the action space to just two tools — a persistent Bash tool and an `str_replace_editor` edit tool using string-replacement diffs — on the stated philosophy of giving "as much control as possible to the language model itself" while keeping scaffolding minimal, a step further than SWE-agent's more elaborate multi-command ACI (search_file, search_dir, find_file, scroll, goto, edit).
- **Numbers**: Claude 3.5 Sonnet (new) resolves 49% on SWE-bench Verified, vs. 45% prior SOTA, 33% for Claude 3.5 Sonnet (old), 22% for Claude 3 Opus.
- **Conditions**: SWE-bench Verified (the human-filtered subset of SWE-bench released by OpenAI/Princeton in 2024); pass@1 = %Resolved; date of post: January 6, 2025 (per WebFetch extraction).
- **Source**: Anthropic Engineering, "Raising the bar on SWE-bench Verified," anthropic.com/engineering/swe-bench-sonnet, Jan 2025.
- **Quality tier**: strong-secondary (official vendor engineering blog, not peer-reviewed, but describes Anthropic's own production system with concrete numbers/quotes)
- **Quote**: "Our design philosophy when creating the agent scaffold optimized for updated Claude 3.5 Sonnet was to give as much control as possible to the language model itself, and keep the scaffolding minimal." / "We experimented with several different strategies for specifying edits to existing files and had the highest reliability with string replacement, where the model specifies `old_str` to replace with `new_str`."
- **Confidence**: high (direct WebFetch of primary org blog, corroborated numbers)
- **Local path**: NOT ACQUIRED (web-only artifact, no PDF)

### mini-SWE-agent: the action space collapses to bash-only (SWE-agent org, 2025)
- **Claim**: The same Princeton/Stanford team behind SWE-agent released mini-SWE-agent, a ~100-line agent that strips the action space down to bash-only (no dedicated edit/search/view commands at all — the model must use cat/grep/sed directly), reversing SWE-agent's 2024 thesis that a custom ACI beats the raw shell, and still scores competitively as base models got stronger.
- **Numbers**: mini-SWE-agent reported >74% on SWE-bench Verified (GitHub README); a separate paper reports the mini-swe-agent v2 bash-only slice at 75.4% on SWE-bench Verified and 45.8% on SWE-Bench Pro with Claude 4.5.
- **Conditions**: SWE-bench Verified; bash-only tool (Docker-sandboxed shell, no custom edit/search commands); base model Claude 4.5 for the 75.4%/45.8% figures.
- **Source**: SWE-agent org, "mini-swe-agent" GitHub repo (github.com/SWE-agent/mini-swe-agent); cross-referenced via arXiv papers citing it as a baseline (e.g. arxiv.org/html/2511.02230v1, "trace from mini-swe-agent").
- **Quality tier**: weak (GitHub README self-report) for the >74% figure; strong-secondary for the 75.4%/45.8% figure (cited inside an arXiv preprint, not independently verified by me against that PDF)
- **Quote**: "The 100 line AI agent that solves GitHub issues or helps you in your command line. Radically simple, no huge configs, no giant monorepo—but scores >74% on SWE-bench verified!"
- **Confidence**: medium (numbers are consistent across two independent search snippets but I did not open the underlying arXiv PDF or GitHub repo directly)
- **Local path**: NOT ACQUIRED

### OpenAI Codex CLI: apply_patch envelope + shell tool (OpenAI, April 2025)
- **Claim**: OpenAI's Codex CLI (released April 2025) uses a two-primitive action space — a shell/`container.exec` tool for read/search/test operations (cat, grep, find, run tests/linters/git) and a separate strict `apply_patch` envelope reserved for file mutation, explicitly steering the model toward minimal, surgical diffs rather than whole-file rewrites; Codex can also be exposed as an MCP server for orchestration by other agents.
- **Numbers**: none (design-description search snippet; no resolve-rate numbers surfaced in this query)
- **Conditions**: Codex CLI, released April 2025; local or sandboxed/hosted container execution.
- **Source**: OpenAI Developer docs ("Apply Patch | OpenAI API," developers.openai.com/api/docs/guides/tools-apply-patch) and Wikipedia "OpenAI Codex (AI agent)" cross-referenced via WebSearch snippets.
- **Quality tier**: strong-secondary (official API docs) / weak (Wikipedia corroboration only, not independently opened)
- **Quote**: "the prompt teaches a shell-first toolkit (read via cat, search via grep/find, run tests/linters/git) and reserves file mutation for a strict apply_patch envelope, pushing the model toward minimal, surgical diffs rather than whole-file rewrites."
- **Confidence**: medium (from search snippet only, did not open the primary doc page directly)
- **Local path**: NOT ACQUIRED

### LSP-based and semantic code-search tools augment the action space (2025)
- **Claim**: Beyond bash/edit primitives, a 2025 trend adds structured code-intelligence tools to the agent action space: LSP-backed symbol/reference lookup (compiler-level knowledge of definitions, references, types) and AST/tree-sitter-based semantic chunking/retrieval (e.g. the Serena toolkit, exposed as an MCP server) to answer conceptual queries LSP alone cannot ("where is the payment processing logic").
- **Numbers**: none found in this snippet.
- **Conditions**: general description, not tied to a specific benchmark run.
- **Source**: cocoindexio Substack, "We Launched a Code Search CLI for AI Agents... LSP, Semantic Search"; Serena MCP server listing (lobehub.com/mcp/oraios-serena) — both surfaced via WebSearch snippet, not independently opened.
- **Quality tier**: weak (blog/vendor listing, not a paper)
- **Quote**: "LSP cannot answer conceptual questions—an agent cannot ask 'where is the payment processing logic' because LSP operates on exact symbols, not meaning, making semantic search essential."
- **Confidence**: low (secondary blog snippet only; flagging as a lead, not a verified architectural claim)
- **Local path**: NOT ACQUIRED

## Q2. Model Context Protocol (MCP)

### MCP core primitives, roles, and transport (official spec, version 2025-06-18)
- **Claim**: MCP is an open protocol, released by Anthropic, standardizing how LLM applications connect to external data sources and tools via JSON-RPC 2.0 messages between three roles — Hosts (LLM applications that initiate connections), Clients (connectors within the host, 1:1 with a server), and Servers (services that provide context/capabilities). Servers expose three primitives to clients — Resources (context/data), Prompts (templated messages/workflows), Tools (functions the model can execute) — and clients may expose three primitives back to servers — Sampling (server-initiated agentic/recursive LLM calls), Roots (server-initiated inquiries into URI/filesystem boundaries), and Elicitation (server-initiated requests for more user info). MCP explicitly took inspiration from the Language Server Protocol (LSP).
- **Numbers**: none (protocol definition, not an empirical result).
- **Conditions**: spec version 2025-06-18 (the version fetched); earlier versions: 2024-11-05 (initial release, stdio + SSE transports) and 2025-03-26 (introduced Streamable HTTP, deprecated SSE — kept for backward compatibility only).
- **Source**: Model Context Protocol official specification, modelcontextprotocol.io/specification/2025-06-18 (fetched directly).
- **Quality tier**: primary (official protocol specification document)
- **Quote**: "MCP provides a standardized way for applications to: Share contextual information with language models; Expose tools and capabilities to AI systems; Build composable integrations and workflows... Servers offer any of the following features to clients: Resources... Prompts... Tools... Clients may offer the following features to servers: Sampling... Roots... Elicitation..."
- **Confidence**: high (direct WebFetch of the official spec page)
- **Local path**: NOT ACQUIRED — no `docs/specs/` directory exists in this repo (checked directly; directory absent). Recommend acquiring for `docs/specs/mcp/` per the citation-integrity convention.

### MCP origin date and organization (Anthropic, Nov 25 2024)
- **Claim**: MCP was introduced by Anthropic on November 25, 2024, as an open-source standard (MIT license) with SDKs in Python, TypeScript, C#, and Java, created by Anthropic engineers David Soria Parra and Justin Spahr-Summers, explicitly to solve the "N×M data integration problem" (every model needing a custom integration to every tool/data source).
- **Numbers**: none beyond the date.
- **Conditions**: n/a — announcement date.
- **Source**: Anthropic, "Introducing the Model Context Protocol," anthropic.com/news/model-context-protocol, Nov 25 2024 — corroborated by Wikipedia "Model Context Protocol" entry (both surfaced via WebSearch snippet; the Anthropic announcement itself was not independently opened this session, only its snippet).
- **Quality tier**: strong-secondary (official vendor announcement, snippet-verified, not independently opened as a full page) — CORRECTS my unverified prior of "~late 2024" to the exact date Nov 25, 2024.
- **Quote**: "The Model Context Protocol (MCP) is an open-source standard released by Anthropic on November 25, 2024, for connecting AI assistants to systems where data lives, including content repositories, business tools, and development environments."
- **Confidence**: medium (search-snippet corroborated, not a direct primary-page fetch — the fetch budget was spent on the spec text itself)
- **Local path**: NOT ACQUIRED

### MCP adoption in coding agents and governance transfer (2025-2026)
- **Claim**: By 2025-2026 MCP is supported by essentially every major coding-agent product — Claude Code, Cursor, Cline, OpenCode, Continue.dev, Roo Code, Kilo Code, Windsurf, Codex CLI, and others — used to attach tools such as GitHub, filesystem, Postgres, and browser-automation (Playwright) servers; in December 2025 Anthropic donated MCP's governance to the Linux Foundation under a new "Agentic AI Foundation" (AAIF) co-founded by Anthropic, Block, and OpenAI, and by Q2 2026 the ecosystem reportedly had roughly 9,400 published servers across major registries (~1,300 "production-ready").
- **Numbers**: ~9,400 published MCP servers (major registries, by close of Q2 2026); ~1,300 "production-ready" servers; Claude Code reported at 980 distinct users in one usage study, OpenCode at 558K session events from 358 users (1,560 events/user).
- **Conditions**: these usage/ecosystem-size numbers come from a third-party blog analysis (qaby.ai "1.42M MCP Tool Calls Compared"), not an official Anthropic/Linux-Foundation report — treat as informal telemetry, not benchmark-grade.
- **Source**: multiple WebSearch-surfaced secondary sources: a "Best MCP Servers in 2026" blog roundup (totalum.app), and qaby.ai's "Claude Code vs Cursor vs Opencode: 1.42M MCP Tool Calls Compared." None independently opened as full pages this session.
- **Quality tier**: weak (blog/analytics posts, self-reported telemetry, not opened directly — snippet only)
- **Quote**: "In December 2025, Anthropic donated MCP to the Linux Foundation, establishing it under the Agentic AI Foundation (AAIF), co-founded by Anthropic, Block, and OpenAI."
- **Confidence**: low-medium (the governance-transfer claim is plausible and specific enough to be checkable, but I did not open a primary source confirming it — flagging for verification)
- **Local path**: NOT ACQUIRED

### MCP security/landscape academic treatment
- **Claim**: There is at least one arXiv preprint specifically surveying MCP's security landscape and threat model, suggesting MCP has already drawn dedicated academic attention beyond vendor documentation.
- **Numbers**: none extracted (title/abstract-level only; not opened).
- **Conditions**: n/a
- **Source**: "Model Context Protocol (MCP): Landscape, Security Threats," arXiv:2503.23278 (title/link surfaced via WebSearch; PDF not opened this session).
- **Quality tier**: weak (title-only, unverified content — this is a LEAD, not a confirmed finding)
- **Quote**: n/a — did not open the PDF
- **Confidence**: low (title/existence only; content not verified)
- **Local path**: NOT ACQUIRED — candidate for acquisition if Q2 needs a peer-reviewed-style anchor beyond the vendor spec

## Q3. Long-horizon context management in coding agents

### Anthropic's "context engineering" framework: compaction, structured memory, sub-agents (Sept 2025)
- **Claim**: Anthropic's official engineering guidance frames "context engineering" as the successor to prompt engineering — curating the optimal token set across an agent's full working state, not just the prompt — and names four concrete mechanisms for long-horizon tasks: (1) **compaction** (LLM-based summarization when approaching the context window limit, described elsewhere as firing near ~98% of the effective window in Claude Code specifically), (2) **structured/persistent memory** (a memory tool that creates, reads, updates, and deletes memory files outside the context window so information survives compaction), (3) **sub-agent architectures** (delegating bounded subtasks to sub-agents that return only compact summaries), and (4) **context editing / context awareness** (rule-based pruning inside the scaffold, plus giving the model real-time feedback on remaining context capacity after each tool call).
- **Numbers**: compaction can reduce context token count by 90-99% per a related secondary source (Zylos Research); Claude Code's auto-compact is reported to trigger at approximately 98% of the effective context window (total window minus reserved output tokens) per a third-party "Inside Claude Code" technical breakdown — NOT an Anthropic-stated number, flagging as secondary.
- **Conditions**: Anthropic's own agent products (Claude Code, the Claude Developer Platform "memory tool"); blog post published September 2025.
- **Source**: Anthropic Engineering, "Effective context engineering for AI agents," anthropic.com/engineering/effective-context-engineering-for-ai-agents, Sept 2025; corroborating secondary detail (98% trigger point, 90-99% reduction) from Zylos Research and "Inside Claude Code" technical blog (y-agent.github.io/inside-claude-code), both accessed only via WebSearch snippet.
- **Quality tier**: strong-secondary (the Anthropic post itself, official vendor engineering content) for the four-mechanism taxonomy; weak (independent blogs) for the specific 98%-trigger and 90-99%-reduction numbers.
- **Quote**: "Memory tools enable persistent storage and retrieval across conversations through creating, reading, updating, and deleting memory files." / "Context awareness provides the model with real-time feedback on remaining context capacity after each tool invocation."
- **Confidence**: medium (four-mechanism framework read from multiple corroborating search snippets of the same primary post; the specific numeric triggers are third-party, not Anthropic-stated, and were not independently opened)
- **Local path**: NOT ACQUIRED

### Sub-agent delegation as context isolation (Claude Code Task tool; Hermes-agent)
- **Claim**: Sub-agent delegation in current coding-agent scaffolds is implemented as a context-isolation mechanism, not just a division of labor: a delegated sub-agent starts with a fresh conversation carrying zero knowledge of the parent's history or prior tool calls, receiving only an explicit `goal`/`context` payload the parent populates, and the delegation call requires the parent to state `delegated_scope` (work being handed off) and `kept_work` (work retained) — an explicit infinite-recursion guard that forces each delegation level to be a strict reduction in scope.
- **Numbers**: none.
- **Conditions**: described for Claude Code's "Task tool" and separately for NousResearch's open-source Hermes-agent delegation feature; both are implementation/product documentation, not peer-reviewed papers.
- **Source**: NousResearch, "Subagent Delegation," hermes-agent.nousresearch.com/docs/user-guide/features/delegation (and its GitHub mirror), surfaced via WebSearch; a "claude-howto" community GitHub doc on Claude Code subagents (luongnv89/claude-howto).
- **Quality tier**: weak (product documentation / community how-to, not a paper; not independently opened)
- **Quote**: "Subagents start with a completely fresh conversation with zero knowledge of the parent's conversation history, prior tool calls, or anything discussed before delegation—their only context comes from the goal and context fields the parent agent populates."
- **Confidence**: low-medium (mechanism description is specific and plausible but drawn from an unopened doc snippet; treat the "infinite-recursion guard" framing as a lead to verify against primary Claude Code docs)
- **Local path**: NOT ACQUIRED

### Persistent instruction files: AGENTS.md formalized as a cross-vendor open standard (Aug 2025)
- **Claim**: AGENTS.md — a plain-markdown, schema-free "README for agents" file placed at a repo root to give persistent project-level instructions to a coding agent (distinct from per-turn context) — was formalized in August 2025 through collaboration between OpenAI, Google, Cursor, Factory, and Sourcegraph, and by the time of writing (search snippets accessed 2026-08-14) is supported by OpenAI Codex, Cursor, Google Jules/Gemini, GitHub Copilot (added Aug 2025), Factory, Amp, Windsurf, Zed, and RooCode; in Dec 2025 it became one of three inaugural projects (alongside MCP and Block's "goose") under the Linux Foundation's new Agentic AI Foundation (AAIF).
- **Numbers**: adoption claims vary by source — one source states "over 20,000 repositories," another "over 60,000 open-source projects" — this discrepancy is itself a finding (self-reported/blog-estimated adoption counts are not reconciled across sources and should not be cited as a single precise figure).
- **Conditions**: cross-vendor open standard, not a single company's product; the two conflicting adoption numbers were not traced to a common methodology or date.
- **Source**: agents.md (official site, surfaced via snippet); PRPM.dev "agents.md: The Complete Guide"; BrightCoding blog "AGENTS.md – An Open Format..."; all accessed only via WebSearch snippet, not opened directly.
- **Quality tier**: weak (blog/vendor-adjacent sources; the "official" agents.md site itself was not independently opened, only its snippet appeared secondhand via aggregator blogs)
- **Quote**: "AGENTS.md has emerged as the de facto open standard for guiding AI coding assistants... formalized in August 2025 through collaboration between OpenAI, Google, Cursor, Factory, and Sourcegraph."
- **Confidence**: medium for the existence/date/formalizing-orgs claim (repeated consistently across independent snippets); low for the specific adoption-count numbers (conflicting, unreconciled)
- **Local path**: NOT ACQUIRED

### Published academic surveys covering agent context management
- **Claim**: Peer-reviewed-style academic treatment of coding-agent context management exists as of 2025-2026, distinct from vendor blogs: a general survey of AI agentic programming explicitly covers "context management" as one of its named technique categories, and a separate survey specifically covers retrieval-augmented code generation at the repository level (the "retrieval-on-demand" mechanism named in this question).
- **Numbers**: none extracted (abstract/title level only).
- **Conditions**: n/a
- **Source**: Wang, Gong, Zhang, Xu, Wang, "AI Agentic Programming: A Survey of Techniques, Challenges, and Opportunities," arXiv:2508.11126 (submitted Aug 15 2025, revised Sept 15 2025) — abstract confirms coverage of "planning, context management, tool integration, execution monitoring, and benchmarking"; and a second paper, "Retrieval-Augmented Code Generation: A Survey with Focus on Repository-Level Approaches," arXiv:2510.04905 (title/abstract level only, not opened).
- **Quality tier**: primary-candidate (arXiv preprint surveys; abstract-level confirmation only in this session, full PDFs NOT opened — so treat specific internal claims from these two papers as unverified until acquired and read)
- **Quote**: "The survey introduces a taxonomy of agent behaviors and system architectures and examines relevant techniques for planning, context management, tool integration, execution monitoring, and benchmarking datasets" (arXiv:2508.11126 abstract, via search snippet).
- **Confidence**: medium (existence, authors, dates, and abstract topic-coverage are corroborated by multiple independent search-result snippets including arXiv's own abstract page and a HuggingFace papers mirror; internal content NOT verified — full PDF not opened this session)
- **Local path**: NOT ACQUIRED — both are strong acquisition candidates (see Sources worth acquiring)

## Q4. Multi-agent vs single-agent coding architectures

### Coding-specific multi-agent systems report gains over single-agent baselines, WITH same-model ablations (self-reported)
- **Claim**: Several multi-agent coding-agent papers report head-to-head ablations against a single-agent baseline while holding the base model fixed, and the ablations they report are positive for the multi-agent design: (a) **AgentForge** reports 40.0% resolve rate on SWE-bench Lite, a claimed +26.0 point improvement over its single-agent baseline, with an ablation showing that removing the Planner role (collapsing the pipeline to one unstructured coder step) drops performance back down to near the single-agent baseline; (b) **CodeR** (issue resolving with multi-agent + task graphs) resolves 28.33% of SWE-bench Lite issues (a separate snippet gives 22%), with an ablation showing removal of the multi-agent/task-graph structure drops the resolved rate from 22% to 10%; (c) **SWE-Debate** (competitive multi-agent debate), using DeepSeek-V3-0324, reports 41.4% success, a claimed +6.0 point improvement over "SWE-Search" and +2.6 points over "SWE-Agent" using the same base model; (d) **AgentCoder** (programmer / test-designer / test-executor roles) reports 96.3%/91.8% pass@1 on HumanEval/MBPP with GPT-4 vs. a stated 90.2%/78.9% SOTA baseline, with ablations showing that removing the Test Designer or Test Executor agent significantly degrades pass@1.
- **Numbers**: AgentForge 40.0% (SWE-bench Lite) vs single-agent baseline (delta stated as +26.0 pts, absolute single-agent baseline value not independently extracted); CodeR 28.33% (one source) / 22%→10% in its own ablation (a second, possibly inconsistent, source) on SWE-bench Lite, vs. SWE-agent+GPT-4 18.00% and Aider 26.33% (both already in the existing survey section); SWE-Debate 41.4% success (DeepSeek-V3-0324), +6.0 pts over "SWE-Search," +2.6 pts over "SWE-Agent" same model; AgentCoder 96.3%/91.8% pass@1 (HumanEval/MBPP, GPT-4) vs 90.2%/78.9% SOTA baseline.
- **Conditions**: dates and venues NOT verified this session (only titles/abstracts/numbers surfaced via WebSearch snippets — none of these four papers' PDFs were opened). CodeR's two numbers (28.33% vs 22%→10%) are INTERNALLY INCONSISTENT across the search snippets and were not reconciled — flag as unverified until the PDF is read directly.
- **Source**: AgentForge, "Execution-Grounded Multi-Agent LLM Framework for Autonomous Software Engineering," arXiv:2604.13120; CodeR, "Issue Resolving with Multi-Agent and Task Graphs," arXiv:2406.01304; SWE-Debate, "Competitive Multi-Agent Debate for Software Issue Resolution," arXiv:2507.23348; AgentCoder, "Multi-Agent-based Code Generation with Iterative Testing and Optimisation," arXiv:2312.13010 — all title/number-level via WebSearch snippet, none opened directly.
- **Quality tier**: weak (snippet-only; NONE of these PDFs independently opened this session — numbers not verified against source tables, and per `.claude/rules/sim-report-completeness.md`'s baseline-scrutiny principle, all four are self-reported by the team proposing the multi-agent method, i.e. the "baseline is under test too" caveat applies directly: none of these ablations were run by an independent third party)
- **Quote**: "Ablation studies reveal that removing the Planner—reducing the pipeline to a single unstructured coder step—drops performance to near the single-agent baseline, confirming that structured decomposition is not merely cosmetic." (AgentForge, via search snippet)
- **Confidence**: low (numbers plausible and specific but entirely unverified against primary PDFs; CodeR's internal inconsistency is a concrete red flag for this whole batch — do NOT cite these numbers in the survey without opening the source PDFs first)
- **Local path**: NOT ACQUIRED — all four are acquisition candidates if this evidence is to be used

### Independent (non-coding-specific) evidence that single-agent matches or beats multi-agent under equal compute/token budget
- **Claim**: Outside the coding domain specifically, at least two 2026 papers report a NEGATIVE/null result for multi-agent orchestration when the comparison controls for compute: (1) "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets" runs a budget-controlled comparison across 2 datasets (FRAMES, MuSiQue), 3 model families (Qwen3, DeepSeek, Gemini), and 5 multi-agent architectures (Sequential, Debate, Ensemble, Parallel-roles, Subtask-parallel), and finds that a single-agent system matches or outperforms multi-agent systems once total computation/thinking-token budget is normalized. (2) "The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided Homogeneous Multi-Agent Debate" reports that unguided homogeneous multi-agent debate is beaten by isolated (single-agent) self-correction in its controlled comparison.
- **Numbers**: none extracted beyond the architecture/dataset/model counts above (title/abstract level only; the actual accuracy deltas were not surfaced in the snippet).
- **Conditions**: multi-hop QA reasoning tasks (FRAMES, MuSiQue), NOT coding/SWE-bench — this is the load-bearing caveat: these are the strongest "equal-budget, controlled" negative results found this session, but neither is a coding benchmark, so they establish only that the multi-agent-tax pattern recurs in a *related* domain, not that it holds for SWE-bench-style tasks specifically.
- **Source**: "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets," arXiv:2604.02460; "The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided Homogeneous Multi-Agent Debate," arXiv:2605.00914 — both title/abstract-level via WebSearch snippet, neither opened directly.
- **Quality tier**: weak-to-strong-secondary (both appear to be controlled, budget-normalized ablations by design — exactly the comparison Q4 asked for — but neither PDF was opened, so the actual effect sizes and statistical treatment are unverified)
- **Quote**: "...testing them across two datasets (FRAMES, MuSiQue), three model families (Qwen3, DeepSeek, Gemini), and five different MAS architectures (Sequential, Debate, Ensemble, Parallel-roles, Subtask-parallel), showing that SAS matches or outperforms MAS when computation is normalized."
- **Confidence**: medium (the existence and design of the comparison is corroborated by a specific, detailed snippet; the numeric result and coding-domain applicability are NOT verified)
- **Local path**: NOT ACQUIRED — arXiv:2604.02460 is the single best "controlled ablation with a null result" lead found this session and is a priority acquisition target

### GAP — no coding-specific, third-party (non-inventor), same-base-model null result found
- **Claim**: This session did NOT find a coding-specific, third-party-run, base-model-held-fixed head-to-head study concluding that multi-agent orchestration does NOT beat a single well-scaffolded agent on SWE-bench or an equivalent coding benchmark. Every positive multi-agent-vs-single-agent coding comparison found was self-reported by the multi-agent method's own authors (AgentForge, CodeR, SWE-Debate, AgentCoder); every controlled negative/null result found was from a non-coding domain (multi-hop QA). "Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures" (arXiv:2604.03515) surfaced as a title suggesting a possible cross-system architectural comparison, but was not opened and its content is unverified.
- **Numbers**: none (this is a gap statement).
- **Conditions**: n/a
- **Source**: absence-of-evidence finding across searches #15, #16, #19, #20 in this session's log.
- **Quality tier**: n/a (meta-finding about the evidence base, not a claim from a source)
- **Quote**: n/a
- **Confidence**: high (confidence in the absence claim, i.e. that this session's search budget did not surface such a paper — NOT confidence that no such paper exists)
- **Local path**: n/a

## Gaps

1. **Q1**: The mini-SWE-agent >74%/75.4% numbers and the OpenAI Codex CLI apply_patch architecture description were read only from search snippets, not from the GitHub repo or OpenAI docs page directly — recommend a direct read before citing in survey prose.
2. **Q1**: The LSP/semantic-search/Serena claim rests on a single blog snippet (cocoindexio Substack) — this is a lead, not a verified architectural trend; needs a stronger source (e.g., a paper on tool-augmented code retrieval) before it appears as a claim in the survey.
3. **Q2**: The MCP origin-date/org claim (Nov 25, 2024) and the Dec 2025 Linux-Foundation/AAIF governance-transfer claim were both corroborated only via WebSearch snippets of secondary sources (Wikipedia, blog roundups), not by opening the Anthropic announcement or Linux Foundation press release directly. The core protocol-primitives claim (Q2's main deliverable) WAS verified via direct WebFetch of the official spec and is solid.
4. **Q2**: arXiv:2503.23278 ("MCP: Landscape, Security Threats") is a title-only lead — content unverified.
5. **Q3**: The Claude Code "98% auto-compact trigger" and "90-99% token reduction" numbers are third-party (Zylos Research, an independent technical blog), not Anthropic-stated — flagged as such in the record, do not upgrade to "Anthropic reports" in survey prose.
6. **Q3**: AGENTS.md adoption counts conflict across sources (20,000 vs 60,000 repos) and neither was traced to a primary, dated count — do not cite a specific number without reconciling.
7. **Q3**: Both academic survey papers found (arXiv:2508.11126, arXiv:2510.04905) were verified only at the abstract/title level — their internal claims about specific context-management mechanisms are NOT verified and must not be attributed to them in survey prose until the PDFs are read.
8. **Q4**: This is the thinnest-evidence question. All four coding-specific multi-agent-beats-single-agent results are self-reported (inventor-run) and unverified against source PDFs; the two controlled null results are from a non-coding domain (multi-hop QA) and also unverified at the number level. **Per the assignment's explicit instruction to flag insufficient evidence: Q4 currently has 0 quality-A/B sources with independently-verified numbers for the coding domain specifically** — everything is "weak" tier by this ledger's own grading. This question needs a second collection pass with PDF-level verification before any Q4 claim goes into survey prose.

## Corrections to the brief

- **Q1 prior CONFIRMED, not corrected**: SWE-agent's four ACI design principles were verified verbatim against the PDF (`download/swe-agent-2024.pdf`, page 4): "1. Actions should be simple and easy to understand for agents. 2. Actions should be compact and efficient. 3. Environment feedback should be informative but concise. 4. Guardrails mitigate error propagation and hasten recovery." This matches the brief's "simple+few actions, compact actions, concise informative feedback, guardrails" characterization exactly — no correction needed.
- **Q2 prior CORRECTED**: The brief said "introduced ~late 2024" as an unverified prior. Search snippets (corroborated across two independent sources — an Anthropic-announcement-derived snippet and Wikipedia) give an exact date: **November 25, 2024**. The originating org (Anthropic) was confirmed correct.
- **Q2 prior on spec content CONFIRMED via direct fetch**: The brief's description ("an open protocol for connecting models to tools/data sources") is directionally correct but incomplete — the officially fetched spec (version 2025-06-18) shows MCP defines SIX primitives split across two directions (server→client: Resources, Prompts, Tools; client→server: Sampling, Roots, Elicitation), not just "tools/data sources." The brief's framing under-states the protocol's scope (it also standardizes server-initiated agentic sampling and user-consent/elicitation flows, which are security/trust primitives, not just data connectors).
- **Q2 — "docs/specs/" check**: The brief asked me to check whether a local MCP spec copy exists under `docs/specs/`. **The directory does not exist at all** in this repo (`ls` returned "No such file or directory"). This is not a correction to a prior per se, but confirms there is currently NO local acquisition of the MCP spec — it should be acquired per `.claude/rules/citation-integrity.md` before the survey cites spec details.

## Sources worth acquiring

Priority order, for Phase-4 acquisition:

1. **MCP official specification** (modelcontextprotocol.io/specification/2025-06-18, plus the schema.ts it references) — load-bearing for Q2's core claim; currently NOT ACQUIRED and no `docs/specs/` directory exists yet.
2. **arXiv:2508.11126** — "AI Agentic Programming: A Survey of Techniques, Challenges, and Opportunities" (Wang, Gong, Zhang, Xu, Wang, Aug 2025) — general survey covering context management, planning, tool integration; strong candidate to anchor Q1 and Q3 claims with a peer-reviewed-style source instead of vendor blogs.
3. **arXiv:2510.04905** — "Retrieval-Augmented Code Generation: A Survey with Focus on Repository-Level Approaches" — anchors Q3's retrieval-on-demand mechanism.
4. **arXiv:2604.02460** — "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets" — the best controlled-ablation null result found for Q4; even though non-coding, it is the strongest methodological anchor for "what would a rigorous multi-agent-vs-single-agent ablation look like."
5. **arXiv:2406.01304** (CodeR) — needed to resolve the internal 28.33%/22%/10% numeric inconsistency flagged above before any CodeR number is cited.
6. **arXiv:2604.13120** (AgentForge), **arXiv:2507.23348** (SWE-Debate), **arXiv:2312.13010** (AgentCoder) — the remaining self-reported multi-agent-coding papers; all four (with CodeR) should be verified against source PDFs before Q4 claims are written into survey prose, per the self-report caveat above.
7. **Anthropic, "Introducing the Model Context Protocol"** (anthropic.com/news/model-context-protocol, Nov 25 2024) — primary announcement, currently only snippet-corroborated.
8. **Anthropic, "Effective context engineering for AI agents"** (anthropic.com/engineering/effective-context-engineering-for-ai-agents, Sept 2025) — primary source for Q3's four-mechanism taxonomy, currently only snippet-corroborated.
