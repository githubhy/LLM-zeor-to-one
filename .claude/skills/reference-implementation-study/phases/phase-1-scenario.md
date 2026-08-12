# Phase 1: Scenario & Requirements

## Goal
Define the evaluation scenario before any coding begins.

## Deliverables
Write up in `docs/<topic>-implementation-study.md`:

- **Task & data distribution**: the task (what the model must produce — next-token prediction, QA, code generation, summarization, preference judgement), the input distribution (dataset, prompt format, few-shot k, domain mix), the evaluation setting (benchmark, decoding params, harness version), and the difficulty / budget axis being studied (compute N·D, context length, decoding temperature). State the model(s) under study.
- **Evaluation metrics**: at least two from accuracy / pass@k / perplexity / win-rate / calibration / latency (TTFT, tokens/s) / throughput / resource cost (FLOPs, memory, KV-cache).
- **Constraints**: bit-width (quantization), latency budget, memory / VRAM / KV-cache, compute (FLOPs), context length — whichever apply.
- **Candidate methods**: minimum 2, recommend 3-4, selected from the survey inventory (e.g. attention variants, samplers / decoding strategies, quantization schemes, RAG retrievers).

- **Reference performance — published-benchmark studies only** `[opt:RIS-REFPERF · default ON · toggle .claude/skill-options.json]`: if the study's success criterion is an **externally published number** (a model card's reported accuracy, a leaderboard entry, a paper's headline `pass@k`), that number is **reference performance + a configuration stack** (prompt template, few-shot $k$ and exemplar pool, decoding params, harness version, answer-extraction rule) — it is **not** a bare capability measurement. Before computing any margin:
  1. Establish the underlying **reference performance** — the number as produced under a stated configuration — via the `spec-provenance` skill and `source-fetch`; it lives in the paper's appendix or the model card's eval section, not in the headline table alone. Record it in the provenance ledger (`[opt:SP-LEDGER]`).
  2. Benchmark your run against the **reference performance reproduced under your own harness**, and state the decomposition `published = reference + configuration delta` explicitly; a margin against your own reproduction is a real delta, a margin against the published number is mostly harness and prompt difference.
  3. **Escape (never silent):** if the reference genuinely cannot be reproduced, say so and benchmark against the published value *with the configuration-stack caveat disclosed* — never treat the published number as a like-for-like target by default.

  Studies with no external published target skip this. The report-side disclosure is gated by `[opt:SIM-REQBASIS]` (`.claude/rules/sim-report-completeness.md` § 2).
