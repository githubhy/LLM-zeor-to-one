# C7 — Retrieval & repository context

## Q1. Agentic search versus embedding retrieval for repositories

### RepoCoder: sparse lexical retrieval matches dense retrieval for repo completion
- **Claim**: A simple sparse (Jaccard/bag-of-tokens) retriever performs on par with a dense neural retriever for repository-level code completion, in an iterative retrieve-generate loop.
- **Numbers**: RepoCoder improves the in-file completion baseline by >10% exact match and >8% edit similarity on RepoEval (line, API-invocation, function-body completion); consistently beats single-shot RAG.
- **Conditions**: GPT-3.5-Turbo and CodeGen models; RepoEval benchmark built from real GitHub repos; iterative retrieval uses model's own draft completion as query augmentation at iteration i.
- **Source**: Zhang, Chen, Zhang, Keung, Liu, Zan, Mao, Lou, Chen, "RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation," arXiv:2303.12570 (EMNLP 2023).
- **Quality tier**: primary
- **Quote**: "a simple sparse retriever — bag-of-tokens snippets ranked by Jaccard similarity — performs on par with a dense neural retriever for this task" [as summarized in survey text; verified against PDF abstract/intro].
- **Confidence**: high
- **Local path**: download/repocoder-2023.pdf

### AutoCodeRover: agentic AST-based code search outperforms flat retrieval for issue resolution
- **Claim**: AutoCodeRover resolves GitHub issues by having an LLM agent iteratively invoke AST-grounded search APIs (search_class, search_method, search_code, etc.) rather than embedding-based retrieval, achieving strong SWE-bench-lite results at low cost.
- **Numbers**: 19% efficacy (pass@1) on SWE-bench-lite (300 issues); resolves issues in ~4 minutes average vs. 2.68 days for human developers; average cost \$0.43 per issue; ~2/3 of produced patches judged correct/acceptable on manual review.
- **Conditions**: SWE-bench-lite (300 real-life Python GitHub issues, 11 projects); compares against SWE-agent and Devin as baselines (same benchmark).
- **Source**: Zhang, Ruan, Fan, Roychoudhury, "AutoCodeRover: Autonomous Program Improvement," ISSTA 2024 (ACM), arXiv:2404.05427.
- **Quality tier**: primary
- **Quote**: "We work on a program representation (abstract syntax tree) as opposed to viewing a software project as a mere collection of files... The use of spectrum-based fault localization using tests, further sharpens the context."
- **Confidence**: high
- **Local path**: download/autocoderover-2024.pdf

### SWE-agent: agent-computer interface with grep/find/search tools, not vector RAG
- **Claim**: SWE-agent's Agent-Computer Interface (ACI) gives the LLM agent navigation/search commands (find_file, search) plus a windowed file viewer and an edit tool with linting — an agentic-search design, not embedding retrieval — and this ACI design itself (not just model capability) is shown to matter for performance.
- **Numbers**: pass@1 of 12.5% on SWE-bench (full) and 87.7% on HumanEvalFix at time of publication, reported as SOTA for non-interactive-LM baselines at the time.
- **Conditions**: SWE-bench (full, not lite); NeurIPS 2024.
- **Source**: Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," arXiv:2405.15793, NeurIPS 2024.
- **Quality tier**: primary
- **Quote**: "tailored search and navigation commands that efficiently locate relevant files and content, suppressing verbose outputs."
- **Confidence**: high (numbers from WebSearch summary of paper, NOT independently reread from PDF this session — treat pass@1 figures as medium-confidence pending direct PDF check)
- **Local path**: NOT ACQUIRED (not in the assigned local set; recommend acquiring)

### Cursor: production system uses hybrid grep + embedding search, claims +12.5% from combining
- **Claim**: Cursor's own architecture combines instant grep/exact-symbol search with semantic (embedding) search over a Merkle-tree-synced, AST-chunked, vector-DB (Turbopuffer) index; Cursor cites internal research showing hybrid (semantic + grep) beats either alone.
- **Numbers**: "+12.5% accuracy from combining semantic with grep" — reported second-hand via a review blog citing Cursor's internal research; NOT independently verified against a Cursor primary source this session.
- **Conditions**: production coding-assistant system, unspecified internal eval set, vendor-reported.
- **Source**: Cursor engineering blog ("Securely indexing large codebases," cursor.com/blog/secure-codebase-indexing) + third-party summary (MindStudio, "Why Cursor, Claude Code, and Devin Use grep, Not Vectors," 2025/2026).
- **Quality tier**: weak (the +12.5% figure specifically is vendor-blog-via-secondary-summary, not a benchmark paper; the architecture description — Merkle trees, AST chunking, Turbopuffer vector DB — is from Cursor's own blog and multiple independent technical write-ups and is more reliable)
- **Quote**: "Cursor employs an elegant combination of Merkle trees, trigram indexes, AST-based chunking, a custom trained embedding model, and a vector database storing over a trillion vectors."
- **Confidence**: low (for the +12.5% number specifically); medium (for the architecture description)
- **Local path**: NOT ACQUIRED

### Informal comparison: agentic search (grep/find/cat) beats vector search on Django codebase, ties on TypeScript/Go
- **Claim**: An informal, non-peer-reviewed comparison found agentic search tools (grep, find, cat) outperforming vector-embedding search on a Django Python codebase, but roughly tied on TypeScript/Go codebases.
- **Numbers**: Django: vector search ~60% accuracy vs. agentic search ~68% accuracy. TypeScript/Go: both ~70% accuracy.
- **Conditions**: Source (unnamed original comparison, cited via a YouTube link by the blog author) does not disclose dataset size, query count, model, or methodology.
- **Source**: Sara Zan, "Is grep really better than a vector DB?", zansara.dev, March 15, 2026.
- **Quality tier**: weak — EXPLICITLY FLAGGED. The blog author herself states these are illustrative, not validated, and that "it's easy to find contradicting results on the Internet."
- **Quote**: "one of the many comparisons ... it's easy to find contradicting results on the Internet"
- **Confidence**: low
- **Local path**: NOT ACQUIRED

### "Keyword search is all you need" — controlled agentic-keyword-search vs vector-RAG experiment (general RAG, not code-specific)
- **Claim**: A controlled experiment built a reference vector-DB RAG baseline and compared it against an agentic keyword-search (tool-use) approach; found agentic keyword search can match RAG-level performance without a vector database.
- **Numbers**: none extracted this session (evaluated via LLM-as-Judge / RAGAS metrics; specific score deltas not retrieved).
- **Conditions**: General document QA datasets across multiple domains — **NOT code-repository-specific**; flagged as adjacent evidence, not direct.
- **Source**: arXiv:2602.23368, "Keyword search is all you need: Achieving RAG-Level Performance without vector databases using agentic tool use" (2026).
- **Quality tier**: strong-secondary (controlled experiment, but general-domain RAG not code retrieval; numbers not yet verified)
- **Quote**: "GAP: exact score deltas not retrieved this session"
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

**Q1 synthesis**: This is a genuine, live, largely UNSETTLED architectural dispute. Strong published/primary evidence exists on the retrieval-quality side within the SAME sparse-vs-dense axis at the component level (RepoCoder: sparse ≈ dense for repo completion queries), and strong published evidence exists that agentic/structural search (AST-grounded, iterative) beats naive retrieval for issue localization (AutoCodeRover, LocAgent, RepoGraph — see Q2). But there is **no rigorous, code-specific, peer-reviewed head-to-head paper found this session comparing "agentic grep-style search" against "vector-embedding RAG" as whole system architectures** on a standard code benchmark. The most-cited numbers on that exact question (Cursor's claimed hybrid gain, the Django 60%-vs-68% comparison) are vendor-blog or informal-blog claims, explicitly non-rigorous. Production systems (Cursor, Claude Code per vendor blogs) appear split: Claude Code / Codex-style agents lean grep-first with no vector index; Cursor uses a hybrid vector+grep index.

---

## Q2. Structural repository context (repo maps, AST/call-graph, symbol indexes)

### AutoCodeRover: AST-grounded context-retrieval API set
- **Claim**: Instead of flat-file retrieval, AutoCodeRover exposes a fixed API set (search_class, search_class_in_file, search_method, search_method_in_class, search_method_in_file, search_code, search_code_in_file) grounded in a locally-parsed AST of the codebase, invoked iteratively ("stratified search") by an LLM agent, and optionally augmented with spectrum-based fault localization (SBFL) when a test suite is available.
- **Numbers**: 19% pass@1 on SWE-bench-lite; adding SBFL-based context augmentation is reported to increase efficacy further (exact delta not extracted this session — GAP).
- **Conditions**: SWE-bench-lite, 300 Python GitHub issues; class-signature-only returns (not full implementation) used to keep context short.
- **Source**: Zhang, Ruan, Fan, Roychoudhury, "AutoCodeRover: Autonomous Program Improvement," ISSTA 2024, arXiv:2404.05427.
- **Quality tier**: primary
- **Quote**: "Returning the signature to shorten context, is a better approach than cutting off the context at a certain bound."
- **Confidence**: high
- **Local path**: download/autocoderover-2024.pdf

### RepoGraph: repository-level code graph boosts existing agents by 32.8% relative
- **Claim**: RepoGraph builds a line-level code graph (nodes = lines of code, edges = definition/reference dependencies) for a repository and adds a "search_repograph" k-hop ego-graph retrieval action to existing agent frameworks (Agentless, SWE-agent), giving structural context beyond flat file/chunk retrieval.
- **Numbers**: RepoGraph-augmented agents show a **32.8% relative improvement on SWE-bench** over the same agents without it; establishes new SOTA among open-source frameworks at time of publication.
- **Conditions**: SWE-bench (full/lite not fully disambiguated this session — GAP); integrates with both procedural (Agentless) and agent-based (SWE-agent) frameworks; cached graphs distributed via HuggingFace/Google Drive for all SWE-bench repos.
- **Source**: (ozyyshr et al.), "RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph," ICLR 2025, arXiv:2410.14684.
- **Quality tier**: primary
- **Quote**: "RepoGraph constructed repository-level code graphs that boost existing agents by 32.8% relative improvement on SWE-bench (ICLR 2025)."
- **Confidence**: medium-high (numbers from WebSearch summary of paper; not independently reread from the PDF/arXiv HTML this session — recommend direct verification before citing in survey prose)
- **Local path**: NOT ACQUIRED

### LocAgent: graph-guided localization, up to 92.7% file-level accuracy, 86% cost reduction vs proprietary
- **Claim**: LocAgent parses a codebase into a directed heterogeneous graph (files/classes/functions/imports as nodes) enabling multi-hop graph-guided localization by an LLM agent, and shows a fine-tuned open model matches proprietary-model localization accuracy at much lower cost.
- **Numbers**: up to 92.7% file-level localization accuracy; ~86% cost reduction vs. SOTA proprietary models; +12% downstream GitHub-issue-resolution success at pass@10.
- **Conditions**: fine-tuned Qwen2.5-Coder-Instruct-32B; ACL 2025 (Volume 1, pages 8697-8727).
- **Source**: Chen et al., "LocAgent: Graph-Guided LLM Agents for Code Localization," ACL 2025, arXiv:2503.09089.
- **Quality tier**: primary
- **Quote**: "LocAgent with the fine-tuned Qwen-2.5-Coder-Instruct-32B model achieves comparable results to SOTA proprietary models at greatly reduced cost."
- **Confidence**: medium-high (numbers via WebSearch summary; not independently reread from PDF this session)
- **Local path**: NOT ACQUIRED

### Aider: tree-sitter-based repo map, PageRank-style file ranking, no published benchmark evidence
- **Claim**: Aider builds a "repo map" by parsing every file with tree-sitter to extract definitions/references, then ranks files/symbols with a graph-ranking algorithm (graph: files as nodes, dependency edges) to fit a token budget (default 1k tokens via --map-tokens), replacing an earlier ctags-based version.
- **Numbers**: none — WebFetch of the primary Aider blog post confirmed **no benchmark data, performance metrics, or empirical comparison** against a no-repo-map baseline is given in that post.
- **Conditions**: n/a (design description only); default map-tokens budget = 1,000 tokens.
- **Source**: Aider blog, "Building a better repository map with tree sitter," aider.chat/2023/10/22/repomap.html, Oct 22, 2023.
- **Quality tier**: careful-explainer (first-party vendor/tool blog; authoritative on design, but NOT a benchmark source — explicitly no measured evidence of effectiveness)
- **Quote**: "uses a graph ranking algorithm, computed on a graph where each source file is a node and edges connect files which have dependencies" (exact algorithm name, e.g. PageRank, not stated in the fetched text — GAP)
- **Confidence**: high (design description); n/a (no effectiveness numbers exist in this source)
- **Local path**: NOT ACQUIRED

### AGENTS.md / repository-level context files: LLM-generated files can HURT; human-written files help modestly, both cost more
- **Claim**: A controlled two-agent ablation study found that LLM-auto-generated repository context files (AGENTS.md-style) can *reduce* coding-agent task success, while human-written context files give a modest improvement — but both increase inference cost substantially. This directly counters the assumption that "more structural context is always better."
- **Numbers**: LLM-generated context files: **-3% average task success**, **+20%+ inference cost**. Human-written context files: **+4% average task success**, also **+20%+ inference cost**.
- **Conditions**: Two settings — SWE-bench tasks from popular repos (LLM-generated files per agent-vendor recommendations) and a novel collection of issues from repos with developer-committed context files.
- **Source**: Gloaguen, Mündler, Mueller, Raychev, Vechev, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?", ICLR 2026 Workshop on Memory for LLM-Based Agentic Systems, arXiv:2602.11988.
- **Quality tier**: strong-secondary (workshop paper, not a main-track peer-reviewed venue, but a controlled ablation study with a named benchmark and named authors from ETH Zurich SRI Lab)
- **Quote**: "there is currently no rigorous investigation into whether such context files are actually effective for real-world tasks" ... "LLM-generated context files reduced task success rates by about 3% on average and increased inference costs by over 20%."
- **Confidence**: medium (numbers via WebSearch summary of paper; not independently reread from PDF this session — recommend direct verification before citing in survey prose)
- **Local path**: NOT ACQUIRED

**Q2 synthesis**: Structure-aware context (AST-grounded API search in AutoCodeRover; code graphs in RepoGraph; heterogeneous graphs in LocAgent) has multiple primary, benchmarked (SWE-bench family) demonstrations of beating flat retrieval baselines on the SAME underlying agent framework — RepoGraph's 32.8% relative gain is the clearest single number. However, the Gloaguen et al. AGENTS.md study is an important counter-finding: naively stuffing MORE structural/summary context (auto-generated) can hurt, showing the benefit is not monotonic in "more structure" — it depends on structure quality and how it's surfaced (grounded, on-demand API search vs. static upfront dump).

---

## Q3. Long context versus retrieval for code

### Chroma "Context Rot": performance degrades well before advertised context limit, non-uniformly
- **Claim**: Across 18 frontier models (GPT-4.1, Claude 4, Gemini 2.5, Qwen3), reliability decreases substantially as input length grows, even on simple retrieval/replication tasks and even when nowhere near the stated context-window limit; degradation is non-uniform and depends on distractors, needle-question similarity, and haystack structure. Counterintuitively, shuffled (incoherent) haystacks sometimes outperform logically coherent ones.
- **Numbers**: accuracy drops by 30-50% well before the documented context limit in some configurations; a 200K-token-window model can show serious accuracy loss by 50K tokens of input.
- **Conditions**: 18 models tested; general long-context tasks (not code-specific — GAP: code-specific replication of this study not found this session); July 2025.
- **Source**: Hong, Troynikov, Huber, "Context Rot: How Increasing Input Tokens Impacts LLM Performance," Chroma Research, trychroma.com/research/context-rot, July 2025.
- **Quality tier**: strong-secondary — FLAG: Chroma is a vector-database vendor with a direct commercial incentive to show long-context-alone is insufficient (i.e., that retrieval/RAG is still needed). Methodology (18 models, multiple task types) is comprehensive for an industry study but this is not peer-reviewed.
- **Quote**: "Models performed better on shuffled haystacks than on logically coherent documents across all 18 models" — "context rot is an architectural property of transformer-based attention, not a capability gap that training solves."
- **Confidence**: medium (vendor-incentive flag; general-purpose not code-specific)
- **Local path**: NOT ACQUIRED

### RULER: advertised context length is not the same as effective context length
- **Claim**: Synthetic benchmark (retrieval, multi-hop tracing, aggregation, QA task categories) shows that even models with perfect needle-in-a-haystack scores fail to maintain performance on RULER's harder task categories as input length grows — i.e., simple retrieval tests overstate effective context length.
- **Numbers**: reported (via secondary summary) that most models lose 15-30% accuracy between 4K and 128K context on RULER tasks — GAP: not independently verified against the arXiv PDF this session, treat as medium confidence.
- **Conditions**: general long-context LM evaluation (not code-specific — GAP); NVIDIA.
- **Source**: Hsieh et al., "RULER: What's the Real Context Size of Your Long-Context Language Models?", arXiv:2404.06654 (NVIDIA).
- **Quality tier**: primary (widely-cited long-context benchmark paper) for the design/methodology; the specific "15-30% between 4K-128K" figure is medium-confidence (secondary-summary sourced)
- **Quote**: "Despite achieving perfect results in the widely used needle-in-a-haystack test, almost all models fail to maintain their performance in other tasks of RULER as the input length increases."
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Long Code Arena: code-specific long-context benchmark with explicit context-size stratification
- **Claim**: A CODE-specific long-context benchmark suite (6 tasks: library-based generation, CI-build repair, project-level completion, commit-message generation, bug localization, module summarization) stratifies its project-level completion task into four context-size groups (small/medium/large/huge) specifically to measure how completion accuracy (exact match) changes with available context size.
- **Numbers**: GAP — the specific exact-match-by-context-size-group table was not extracted this session (WebSearch summaries did not surface the numeric table; would need direct PDF/HTML fetch of arXiv:2406.11612 to report numbers).
- **Conditions**: JetBrains Research; repo snapshots with git-history-based leakage avoidance (completions generated from project state before the target file was added); HuggingFace dataset `JetBrains-Research/lca-project-level-code-completion`.
- **Source**: (JetBrains Research), "Long Code Arena: a Set of Benchmarks for Long-Context Code Models," arXiv:2406.11612 (2024).
- **Quality tier**: primary (this is the most directly relevant CODE-specific long-context-vs-context-size benchmark found this session, but its headline numbers are a GAP)
- **Quote**: "the dataset divided into four groups based on context size for nuanced evaluation"
- **Confidence**: medium (existence and design confirmed; numeric results NOT verified this session)
- **Local path**: NOT ACQUIRED

### AGENTS.md study: more upfront static context increases cost without reliably improving outcomes (cross-ref Q2)
- **Claim**: Same finding as Q2 — LLM-generated static context files increase inference cost by >20% while REDUCING task success by ~3% on average; a direct, code-agent-specific data point on the cost/benefit tradeoff of "stuff more context in up front" vs. retrieving/searching on demand.
- **Numbers**: -3% success / +20%+ cost (LLM-generated); +4% success / +20%+ cost (human-written).
- **Conditions**: SWE-bench-derived tasks + a novel repo-context-file collection.
- **Source**: Gloaguen et al., arXiv:2602.11988, ICLR 2026 Workshop.
- **Quality tier**: strong-secondary
- **Quote**: (see Q2 entry)
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Prefix/prompt caching: official vendor numbers on cost/latency of long-context reuse
- **Claim**: Anthropic's own API documentation states prompt caching (reusing the KV-cache of a shared prefix — e.g., a large repository context stuffed into the prompt) reduces cost by up to 90% and latency by up to 80% for cache-hit requests, directly changing the cost/latency calculus of "stuff the whole repo into context" versus retrieving only what's needed.
- **Numbers**: up to 90% cost reduction, up to 80% latency reduction on cache-hit (read) tokens; cache read priced at 10% of standard input token price; cache write priced ~1.25x (5-min TTL) or ~2x (1-hour TTL) of standard input price.
- **Conditions**: Anthropic Claude API, prompt caching feature; general (not code-specific), confirmed via docs.anthropic.com.
- **Source**: Anthropic, "Prompt caching," Claude API Docs, docs.anthropic.com/en/docs/build-with-claude/prompt-caching (accessed 2026-08-14).
- **Quality tier**: strong-secondary (official vendor documentation, not independently benchmarked by a third party this session)
- **Quote**: "Prompt caching reduces costs by up to 90%" / "reduces latency by up to 80%"
- **Confidence**: high (directly sourced to docs.anthropic.com via search, confirmed twice); NOTE: this is vendor-reported, not independently audited
- **Local path**: NOT ACQUIRED (web-only documentation, not a PDF)

**Q3 synthesis**: Evidence converges that ADVERTISED context length substantially overstates EFFECTIVE context length — general-purpose evidence is now fairly strong (Chroma's 18-model study, RULER), but CODE-SPECIFIC quantification of this effect is thinner: Long Code Arena is designed to measure exactly this (context-size-stratified completion accuracy) but its numeric results were not retrieved this session (GAP — flagged below). The Gloaguen AGENTS.md study is the most directly code-agent-relevant finding that MORE static context is not free and not reliably beneficial. Prefix caching materially changes the cost tradeoff in the "stuff full repo into context" direction (up to 90% cost / 80% latency reduction on repeated/cached prefixes such as a static repo dump reused across many turns), which argues FOR long-context stuffing in interactive/agentic loops where the same repo context is reused turn after turn — this is a genuine mitigating factor the "retrieval is cheaper" argument must account for.

---

## Q4. Code embeddings and chunking

### CoIR: successor benchmark to CodeSearchNet, ACL 2025
- **Claim**: CoIR (Code Information Retrieval) is a comprehensive code-retrieval benchmark spanning 10 datasets, 8 retrieval tasks (text-to-code, code-to-text, code-to-code, hybrid-code), 7 domains, 14 programming languages, ~2 million documents; positioned explicitly as CodeSearchNet's successor and integrated into MTEB.
- **Numbers**: monthly download count surpassed CodeSearchNet as of September 2024; 2 million evaluation documents; 14 programming languages.
- **Conditions**: ACL 2025 Main; shares data schema with MTEB/BEIR for cross-benchmark evaluation.
- **Source**: Li et al., "CoIR: A Comprehensive Benchmark for Code Information Retrieval Models," arXiv:2407.02883, ACL 2025.
- **Quality tier**: primary
- **Quote**: "The monthly download count of CoIR surpassed that of CodeSearchNet as of September 2024."
- **Confidence**: medium-high (via WebSearch summary; not independently reread from PDF this session)
- **Local path**: NOT ACQUIRED

### CORE-Bench: newer benchmark specifically for AGENTIC-coding-era code retrieval, shows sharp accuracy drop vs. traditional code search
- **Claim**: CORE-Bench evaluates retrieval at three levels — code understanding, issue-to-edit localization, and broader context retrieval — arguing agentic coding needs more than matching a query to an isolated snippet (must navigate a live repo state, filter in-repo distractors). Finds a SHARP performance drop for existing embedding models when moving from traditional code search to this agentic-retrieval setting.
- **Numbers**: >180K queries, 106K broader-context relevance labels; existing embedding models show a "sharp drop" from traditional code-search performance to agentic-retrieval performance (specific delta numbers — GAP, not extracted this session).
- **Conditions**: 2026 (arXiv submission per search result); GAP on exact publication date/venue verification.
- **Source**: "CORE-Bench: A Comprehensive Benchmark for Code Retrieval in the Era of Agentic Coding," arXiv:2606.11864.
- **Quality tier**: primary
- **Quote**: "Experiments with representative embedding models show a sharp drop from traditional code search to code retrieval in agentic coding settings."
- **Confidence**: medium (via WebSearch summary; exact numeric drop not verified this session)
- **Local path**: NOT ACQUIRED

### CoRNStack / CodeRankEmbed: contrastive training data improves code retrieval + reranking SOTA
- **Claim**: CoRNStack is a 21-million-example, multi-language contrastive training dataset for code (consistency-filtered, hard-negative-mined); training embedding models on it yields SOTA code retrieval/reranking. CodeRankEmbed is a 137M-parameter bi-encoder trained on CoRNStack for NL-to-code retrieval, used as a compact code-specialized baseline in follow-on benchmarks (e.g., CORE-Bench).
- **Numbers**: 21 million contrastive examples; CodeRankEmbed = 137M parameters.
- **Conditions**: multi-language; function-localization downstream task shows improvement when combining the improved retriever + reranker (specific numeric delta — GAP).
- **Source**: (authors not independently confirmed this session — GAP), "CoRNStack: High-Quality Contrastive Data for Better Code Retrieval and Reranking," arXiv:2412.01007.
- **Quality tier**: primary (arXiv preprint, appears on OpenReview suggesting conference submission — exact venue GAP)
- **Quote**: "Contrastive training of embedding models using CoRNStack leads to state-of-the-art performance across a variety of code retrieval tasks."
- **Confidence**: medium
- **Local path**: NOT ACQUIRED

### Voyage-code-3 and Jina Code Embeddings: current (2024-2026) code-specialized embedding models
- **Claim**: Voyage AI's voyage-code-3 and Jina's jina-code-embeddings (0.5B/1.5B) are current code-specialized embedding models competitive with or exceeding general-purpose embedding models (OpenAI text-embedding-3-large, Gemini embedding) on code retrieval specifically.
- **Numbers**: Jina jina-code-embeddings: 78.41% (0.5B) / 79.04% (1.5B) average across 25 code retrieval benchmarks; voyage-code-3 reported at 79.23% on the same comparison; gemini-embedding-001 at 77.38%. (Separately reported: voyage-code-3 outperforms OpenAI text-embedding-3-large by 5-8 NDCG points on code retrieval — different source/methodology, not directly reconciled with the 79.23% figure — FLAG: possible metric-basis mismatch between these two claims, not resolved this session.)
- **Conditions**: cross-lingual retrieval across 29 natural languages, 15+ programming languages (Jina); exact benchmark suite for the 25-benchmark average not independently confirmed (likely CoIR/MTEB-Code — GAP).
- **Source**: Jina AI, "Jina Code Embeddings: SOTA Code Retrieval at 0.5B and 1.5B," jina.ai/news, 2025/2026; Voyage AI product page/announcement for voyage-code-3 (not independently fetched this session).
- **Quality tier**: strong-secondary (vendor announcement blogs with self-reported benchmark numbers; not independently reproduced)
- **Quote**: "The 1.5B variant matches voyage-code-3 (79.23%) and exceeds gemini-embedding-001 (77.38%)."
- **Confidence**: medium (vendor-reported numbers, internally somewhat inconsistent across sources as flagged above)
- **Local path**: NOT ACQUIRED

### CodeBERT and UniXcoder: representation backbones already in survey, foundational for code embeddings
- **Claim**: CodeBERT (bimodal code/text pretraining for search) and UniXcoder (unified encoder/decoder/encoder-decoder with AST + code-comment cross-modal pretraining) remain the representation-model lineage the survey's existing §11.2 cites for dense code embeddings; both predate the 2024-2026 wave of dedicated code-retrieval-benchmark-driven models (CoIR-era) above.
- **Numbers**: none extracted this session beyond what is already in the existing survey section (already cited as bib refs 2 and 14).
- **Conditions**: n/a — already covered in `retrieval-and-repository-context.md` §11.2, cross-referenced from §4.
- **Source**: already in survey references.md as [2] (CodeBERT, 2020) and [14] (UniXcoder, Guo et al. 2022).
- **Quality tier**: primary
- **Quote**: n/a (not re-read this session; already integrated)
- **Confidence**: high (pre-existing survey citation, not re-verified this session — GAP if a re-verification pass is desired)
- **Local path**: download/codebert-2020.pdf, download/guo-unixcoder-2022.pdf

**Q4 synthesis**: The CodeSearchNet-successor landscape has moved fast: CoIR (ACL 2025) is the direct successor and now exceeds CodeSearchNet in usage; CORE-Bench (2026) is a further, more agentic-coding-specific successor showing that models good at classic code search are NOT automatically good at agentic-repo-navigation retrieval — a load-bearing finding for this survey's argument that repo-scale retrieval is a distinct problem from function-level code search. CoRNStack/CodeRankEmbed represents the current SOTA training recipe (contrastive, hard-negative-mined). On CHUNKING specifically: GAP — no source found this session that directly benchmarks syntactic/AST-boundary chunking against fixed-window chunking for code retrieval quality; only architecture descriptions (Cursor's "AST-based chunking") assert this without published comparison numbers.

---

## Gaps

- **GAP**: No rigorous, peer-reviewed, code-specific head-to-head study found comparing "agentic grep/search-tool" architectures against "vector-embedding RAG" architectures as whole systems on a standard repo-scale benchmark (Q1). Available numbers (Cursor's +12.5%, the Django 60-vs-68% comparison) are vendor-blog or informal-blog only.
- **GAP**: RepoGraph's 32.8% relative-improvement figure and LocAgent's 92.7%/86%-cost-reduction/+12% figures were extracted via WebSearch summarization, not independently reread from the source PDFs/arXiv HTML this session. Recommend a follow-up pass to open arXiv:2410.14684 and arXiv:2503.09089 directly before citing these numbers in survey prose (medium confidence only).
- **GAP**: Long Code Arena's actual exact-match-by-context-size-group numbers (the single most directly relevant code-specific "does more context help" dataset) were not retrieved this session — only the existence and design of the four-way stratification was confirmed. This is the highest-priority gap for Q3.
- **GAP**: No source found this session directly benchmarking AST/syntactic-boundary chunking against fixed-window chunking for code retrieval quality (Q4) — only unverified architecture claims (Cursor's blog).
- **GAP**: CoRNStack's exact author list/venue was not independently confirmed (OpenReview listing found but full author attribution not re-extracted).
- **GAP**: SWE-agent's reported pass@1 numbers (12.5% SWE-bench, 87.7% HumanEvalFix) came from a WebSearch summary of the paper, not a direct PDF read this session.
- **GAP**: Voyage-code-3's two reported figures (79.23% average vs. "outperforms text-embedding-3-large by 5-8 NDCG points") come from two different secondary sources with unreconciled methodology/metric basis — a `.claude/rules/calibration-residuals.md` check-4 concern if either number is used in survey prose without reconciliation.
- **GAP**: The Chroma Context Rot and RULER findings are GENERAL-PURPOSE (not code-specific) long-context degradation evidence; a code-specific replication (ideally via Long Code Arena or CORE-Bench) would close this gap — see the Long Code Arena GAP above.

## Corrections to the brief

- The brief's framing that this is "a live architectural dispute" is CONFIRMED — but the brief should be corrected to note that the strongest evidence found is NOT a direct head-to-head on the exact question ("agentic search vs vector retrieval") — it is adjacent evidence: (a) sparse-vs-dense retrieval-quality parity within retrieval systems (RepoCoder), and (b) structural/graph-grounded search beating flat retrieval (RepoGraph, LocAgent, AutoCodeRover). The vendor-blog claims that most directly address the brief's exact question (Cursor's hybrid gain, the Django comparison) are the WEAKEST tier of evidence found, not the strongest — this should be stated explicitly in the survey text, not softened.
- The brief's suggestion to look for "prefix-caching implications" (Q3) paid off with a strong, directly-confirmed vendor-primary source (Anthropic docs, up to 90%/80%) — this is a genuine, underappreciated argument FOR long-context stuffing in agentic loops that the existing survey section's "no published head-to-head" framing (§11.3) should be updated to mention.
- New, unanticipated finding not in the brief: the Gloaguen et al. AGENTS.md study (Q2/Q3 crossover) is a significant, fairly rigorous (controlled ablation) counter-finding that MORE upfront structural/summary context can actively HURT task success while increasing cost — this complicates any simple "structure-aware context beats flat retrieval" narrative and should be folded into both §11.2/11.3 revisions.
- New, unanticipated finding: CORE-Bench (2026) directly evidences that "code search" and "agentic repository retrieval" are measurably DIFFERENT tasks (existing embedding models show a sharp accuracy drop moving from one to the other) — this is a strong argument for why the survey should treat repo-level retrieval as its own subtopic distinct from function-level code search (already implicit in the section structure, now evidenced).

## Sources worth acquiring

- arXiv:2410.14684 — RepoGraph (ICLR 2025) — verify the 32.8% figure directly
- arXiv:2503.09089 — LocAgent (ACL 2025) — verify 92.7%/86%/+12% figures directly
- arXiv:2406.11612 — Long Code Arena — retrieve the context-size-stratified exact-match table (highest priority for Q3)
- arXiv:2602.11988 — Gloaguen et al., "Evaluating AGENTS.md" (ICLR 2026 Workshop) — verify -3%/+4%/+20% figures directly
- arXiv:2606.11864 — CORE-Bench — verify the "sharp drop" numeric delta
- arXiv:2412.01007 — CoRNStack — confirm authors/venue
- arXiv:2405.15793 — SWE-agent (NeurIPS 2024) — verify pass@1 numbers directly
- arXiv:2407.02883 — CoIR (ACL 2025)
