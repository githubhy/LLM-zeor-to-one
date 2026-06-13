# Phase 2: Outline

## Goal
Build a section outline with explicit research questions before deep expansion.

## Constraints
- Each section must have a concrete research question.
- Classify questions as **must-have** (blocks section writing) or **nice-to-have** (enriches but does not block). This drives agent mode selection in Phase 3.
- For large or high-stakes topics, offer the outline for user confirmation before expanding.

## Default Output Structure

1. Executive summary
2. Scope and problem definition
3. Mathematical or conceptual fundamentals (e.g. the attention operator, autoregressive likelihood, scaling laws)
4. System architecture and decomposition (e.g. tokenizer → embedding → transformer stack → decoding; or training → alignment → serving pipeline)
5. Complete method and variant inventory
6. Derivations or governing equations for important methods
7. Performance, quality, compute, and cost tradeoffs (params, FLOPs/token, latency, throughput, memory, $/1M tokens)
8. State of the art and what is actually used in practice (frontier vs open-weight; research vs production)
9. Design guidance or decision framework
10. Open problems and future roadmap
11. References

## LLM Method Taxonomy (coverage checklist)

Most LLM surveys draw their method inventory (section 5) from these axes — use it to test the outline for coverage gaps. Include the axes the topic touches; omission of a relevant axis is a quality defect.

- **Architecture** — transformer variants, attention (MHA/MQA/GQA, sparse, linear, FlashAttention), positional encodings (RoPE, ALiBi), normalization, MoE/sparse experts, state-space models (Mamba), long-context methods.
- **Pretraining** — objectives (causal LM, MLM, FIM), data curation & dedup, tokenization (BPE, SentencePiece), scaling laws (Kaplan, Chinchilla), optimization (AdamW, schedules), distributed training (DP/TP/PP/ZeRO, FSDP).
- **Adaptation & alignment** — SFT/instruction tuning, RLHF (PPO), preference optimization (DPO, IPO, KTO), RLAIF/Constitutional AI, PEFT (LoRA/QLoRA, adapters, prefix/prompt tuning).
- **Inference & serving** — KV-cache & paged attention (vLLM), quantization (GPTQ, AWQ, GGUF, FP8), speculative/parallel decoding, continuous batching, distillation, sampling (temperature, top-p, beam).
- **Retrieval & tools** — RAG (chunking, embeddings, rerankers, vector DBs), tool/function calling, structured output, MCP.
- **Agents** — planning (ReAct, ToT), memory, multi-agent orchestration, code/computer use.
- **Evaluation** — benchmarks (MMLU, GSM8K, HumanEval, SWE-bench, MMMU), LLM-as-judge, contamination & saturation, human eval, arenas (LMSYS).
- **Multimodality** — vision-language (CLIP, ViT fusion), audio/speech, any-to-any, diffusion ↔ LLM bridges.
- **Safety & interpretability** — red-teaming, jailbreaks & guardrails, hallucination & calibration, watermarking, mechanistic interpretability (SAEs, probing).
- **Systems & efficiency** — hardware (GPU/TPU), kernels (Triton, CUDA), memory/communication tradeoffs, training/inference cost.

## Deliverable
A section outline where every section has a research question and must-have/nice-to-have classification, checked against the taxonomy above for omitted axes.
