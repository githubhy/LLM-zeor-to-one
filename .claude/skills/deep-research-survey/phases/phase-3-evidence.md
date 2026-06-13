# Phase 3: Evidence Collection

## Goal
Collect section-level evidence against the outline with source quality discipline.

## Constraints
- Collect evidence against the outline, not against the topic abstractly.
- Prefer primary sources: original papers, official model/technical reports, reference implementations.
- LLM research moves fast: enforce a recency threshold (flag SOTA claims older than ~12–18 months), and watch for **benchmark contamination and saturation** — a leaderboard number is not a capability claim.
- Every factual claim must cite a specific source. No vague attributions.
- Prefer the arXiv version of record but cite the peer-reviewed venue when one exists; pin the arXiv id and version (papers get revised).

## Source Quality Rubric (LLM-tuned)

1. **Primary** — original papers (arXiv + peer-reviewed: NeurIPS, ICML, ICLR, ACL, EMNLP, COLM), official model cards & technical reports (GPT-4, Llama 3, Claude, Gemini, DeepSeek, Qwen, Mistral), reference implementations and their docs (Hugging Face Transformers, vLLM, PyTorch, Megatron, JAX), official API/framework documentation.
2. **Strong secondary** — reputable lab/vendor engineering blogs (Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral), eval-harness documentation (lm-evaluation-harness, HELM, BIG-bench), live leaderboards/arenas (LMSYS Chatbot Arena, Open LLM Leaderboard, SWE-bench), well-run reproductions.
3. **Careful explainers** — high-quality secondary surveys, well-cited blog explainers (e.g. Lilian Weng, *The Illustrated Transformer*), course notes, OpenReview discussion. Useful for orientation; trace every load-bearing claim back to a Tier-1 source.
4. **Weak** — marketing posts, launch hype, benchmark cherry-picks, unsourced threads.

Downgrade if stale, derivative, promotional, contamination-suspect, or missing traceable evidence. A model card's self-reported eval is Tier 1 for *what the lab claims* but not neutral evidence of capability — corroborate with an independent eval where it matters.

## Evidence Ledger

Track evidence in a compact section-wise ledger:

| Section | Question | Key findings | Best sources | Confidence | Gaps |
| --- | --- | --- | --- | --- | --- |
| [section] | [what must be answered] | [facts or comparisons] | [links or citations] | [high/medium/low] | [what is still missing] |

## Agent Sizing Rules

When using background agents for parallel evidence collection:

- **Questions per agent**: 5 or fewer (hard limit)
- **Estimated searches per agent**: 15 or fewer (soft limit)
- If estimated searches exceed 15, split the agent or move excess to main thread
- **Checkpoint writes**: instruct every agent to write intermediate results to `survey/_scratch/<agent-name>.md` after each question
- **Staggered launch**: launch 2-3 agents for must-have evidence first (foreground), then remaining as background
- **15-minute dead-agent check**: if no output and no task notification, check scratch file; if empty, assume dead and do research on main thread
- **Synthesis always on main thread** — agents collect raw evidence only

Agent brief quality: each agent gets a numbered list of specific questions, concrete expected output format, a stop condition, and the checkpoint instruction. See `templates/agent-brief.md`.

## Full-Text Acquisition

Most LLM papers are open-access — the `source-fetch` skill resolves an arXiv id, title, or DOI to a PDF in `download/` (Semantic Scholar → OpenAlex → arXiv direct → Crossref). Fetch full text whenever the abstract is insufficient for a load-bearing claim (a method's exact objective, a table constant, a scaling-law exponent, an ablation result) — the abstract routinely omits the number you need to cite. Cap downloads at ~50/day, reserve ~10–15 as holdback for Phase 4 gaps. See `source-fetch` skill for workflow.

**LLM-search caution.** A broad query ("survey of X") returns hundreds of arXiv hits, and an agent that tries to triage them all burns its search budget and dies. Give each agent a *narrow* question and a stop condition ("the 3–5 most-cited / most-recent works on Y; stop after 3 searches"). Prefer survey papers and well-maintained "Awesome-X" / paperlists as entry points, then pull the primary sources they point to.

## Deliverable
A populated evidence ledger with sources, confidence ratings, and identified gaps.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-1, P1-1, P2-1` is active, read `addenda/phase-3.md` (P0-1 Workflow orchestration, P1-1 AttributeTree evidence, P2-1 citation-graph evidence) and apply the active blocks. In `original` mode, skip — do not read it.
