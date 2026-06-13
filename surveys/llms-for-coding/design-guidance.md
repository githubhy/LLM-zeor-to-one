## 17 Design Guidance

<a id="p-17-design-guidance-1"></a><!-- para:17-design-guidance-1 --> This section converts the survey into decisions. It is deliberately prescriptive: given a goal, what does the evidence recommend? The recommendations follow from earlier sections and are cross-referenced to them rather than re-argued.

<!-- sec:17.1 -->
### <a id="sec-17.1"></a>17.1 Choose the Deployment Mode First

<a id="p-171-choose-the-deployment-mode-first-1"></a><!-- para:171-choose-the-deployment-mode-first-1 --> The deployment mode (Section 5) is the decision everything else hangs on, because it sets the binding resource (Section 14).

- <a id="p-171-choose-the-deployment-mode-first-2"></a><!-- para:171-choose-the-deployment-mode-first-2 --> **Inline autocomplete** when the value is keystroke-level acceleration inside an editor. This demands fill-in-the-middle and sub-second latency, which points to a smaller, fast-serving model with speculative decoding and caching (Section 10), not the largest available model.
- **Chat / assistant** when the value is answering questions, explaining code, and generating snippets on request. An instruction-tuned model (Section 8) at moderate size is usually the sweet spot; latency budgets are looser than autocomplete.
- **Autonomous agent** when the value is completing whole tasks — resolving an issue, implementing a feature across files. This needs the strongest reasoning model you can afford (Section 9), a well-designed agent-computer interface (Section 12), and a tolerance for per-task cost and latency measured in dollars and minutes (Section 14).

<!-- sec:17.2 -->
### <a id="sec-17.2"></a>17.2 Choose the Model

<a id="p-172-choose-the-model-1"></a><!-- para:172-choose-the-model-1 --> Three sub-decisions recur:

- <a id="p-172-choose-the-model-2"></a><!-- para:172-choose-the-model-2 --> **Open-weight versus frontier.** The open-weight lines (StarCoder, DeepSeek-Coder, Qwen-Coder) track the frontier closely on function- and repository-level tasks (Sections 3, 15) and win on cost, latency control, data governance, and self-hosting. Reach for a proprietary frontier model when the task is hard agentic work where the top of the leaderboard meaningfully outperforms and the solve rate justifies the cost.
- **Size and sparsity.** Parameter count is a weak proxy for capability; mixture-of-experts sparsity and deliberate over-training decouple capability from inference cost (Section 14), so evaluate on *your* task and serving budget rather than on nominal size.
- **When to fine-tune.** Prefer prompting and retrieval (Section 11) first. Fine-tune when you have a narrow, stable distribution and quality data — and remember the data-quality lesson (Section 6): a small, carefully constructed instruction set (Evol-Instruct, OSS-Instruct, Section 8) beats a large generic one. Security behavior is itself steerable with lightweight methods (SVEN, Section 16) without full retraining.

<!-- sec:17.3 -->
### <a id="sec-17.3"></a>17.3 Build an Evaluation Strategy

<a id="p-173-build-an-evaluation-strategy-1"></a><!-- para:173-build-an-evaluation-strategy-1 --> Do not trust a single public number (Section 13). For any serious adoption:

- <a id="p-173-build-an-evaluation-strategy-2"></a><!-- para:173-build-an-evaluation-strategy-2 --> Evaluate by **execution**, not text overlap — the modality's whole point (Section 2).
- Use **adequate tests**: weak test suites inflate scores by ~20–29% (EvalPlus, Section 13), so augment or use adequately-tested benchmarks.
- Guard against **contamination**: prefer time-windowed or held-out evaluation (LiveCodeBench, Section 13) and a private task set drawn from your own codebase.
- Match the **granularity** to the deployment: function-level pass@k for autocomplete quality, repository-level resolved-rate (SWE-bench-style) for agents.

<!-- sec:17.4 -->
### <a id="sec-17.4"></a>17.4 A Decision Checklist

1. <a id="p-174-a-decision-checklist-1"></a><!-- para:174-a-decision-checklist-1 --> What is the unit of value — keystroke, answer, or task? (Section 5 → mode.)
2. What resource binds — latency, throughput, or total cost? (Section 14.)
3. Open-weight or frontier, and at what active-parameter cost? (Sections 14, 15.)
4. Prompt-and-retrieve, or fine-tune? (Sections 8, 11.)
5. How will you evaluate on *your* distribution, with adequate tests and contamination control? (Section 13.)
6. What is the security and permissions posture, especially for agents? (Section 16.)

<a id="p-174-a-decision-checklist-2"></a><!-- para:174-a-decision-checklist-2 --> Answering these in order yields a configuration; skipping to "which model is best" without them does not, because — as Section 14 argued — there is no single best model independent of the axis you are optimizing.
