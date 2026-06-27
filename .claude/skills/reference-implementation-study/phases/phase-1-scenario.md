# Phase 1: Scenario & Requirements

## Goal
Define the evaluation scenario before any coding begins.

## Deliverables
Write up in `docs/<topic>-implementation-study.md`:

- **Task & data distribution**: the task (what the model must produce — next-token prediction, QA, code generation, summarization, preference judgement), the input distribution (dataset, prompt format, few-shot k, domain mix), the evaluation setting (benchmark, decoding params, harness version), and the difficulty / budget axis being studied (compute N·D, context length, decoding temperature). State the model(s) under study.
- **Evaluation metrics**: at least two from accuracy / pass@k / perplexity / win-rate / calibration / latency (TTFT, tokens/s) / throughput / resource cost (FLOPs, memory, KV-cache).
- **Constraints**: bit-width (quantization), latency budget, memory / VRAM / KV-cache, compute (FLOPs), context length — whichever apply.
- **Candidate methods**: minimum 2, recommend 3-4, selected from the survey inventory (e.g. attention variants, samplers / decoding strategies, quantization schemes, RAG retrievers).
