## 5 The Code Model Pipeline

<a id="p-5-the-code-model-pipeline-1"></a><!-- para:5-the-code-model-pipeline-1 --> A modern code assistant is the output of a pipeline with well-separated stages. Naming them once, here, gives a map for the rest of the survey: each subsequent section zooms into one stage. The pipeline is data → tokenization → pretraining → (optional) mid-training → alignment → serving, and the *deployment target* — inline autocomplete, chat, or autonomous agent — determines which stages are emphasized.

<!-- sec:5.1 -->
### <a id="sec-5.1"></a>5.1 The Stages

1. <a id="p-51-the-stages-1"></a><!-- para:51-the-stages-1 --> **Data curation** (Section 6). Source code is crawled at internet scale, filtered by license, deduplicated, quality-filtered, and decontaminated against benchmarks. This stage, more than architecture, separates strong code models from weak ones.
2. **Tokenization** (Section 4, Section 7). A byte-level BPE tokenizer tuned for code's whitespace and identifiers.
3. **Pretraining** (Section 7). Next-token prediction (the autoregressive objective of Section 4) combined with fill-in-the-middle, over trillions of tokens, increasingly with a repository-level phase that teaches cross-file structure and extends the context window.
4. **Alignment** (Section 8). Supervised instruction tuning followed by preference optimization or reinforcement learning, where code's executable reward (Section 2) enables learning from test outcomes rather than human labels.
5. **Reasoning / test-time scaling** (Section 9). At the frontier, additional RL and inference-time procedures (chain-of-thought, self-repair, sampling-and-selection) trade compute for correctness.
6. **Serving** (Section 10). Decoding, constrained generation, caching, and latency engineering deliver the model to a user.

<!-- sec:5.2 -->
### <a id="sec-5.2"></a>5.2 The Three-Stage Recipe in Practice

<a id="p-52-the-three-stage-recipe-in-practice-1"></a><!-- para:52-the-three-stage-recipe-in-practice-1 --> The clearest published instance of the modern recipe is Qwen2.5-Coder, which continues pretraining on top of a general base model in three explicit stages <!-- cite:11 --> [[11]](references.md#ref-11):

1. <a id="p-52-the-three-stage-recipe-in-practice-2"></a><!-- para:52-the-three-stage-recipe-in-practice-2 --> **File-level pretraining** on roughly 5.2T tokens with next-token prediction and FIM;
2. **Repository-level pretraining** on roughly 300B tokens, extending the context window to 128k via length extrapolation and applying FIM at the repository level;
3. **Alignment** via supervised fine-tuning followed by direct preference optimization, where the preference signal comes from a multilingual code sandbox that executes candidates — an execution-grounded reward rather than human annotation.

<a id="p-52-the-three-stage-recipe-in-practice-3"></a><!-- para:52-the-three-stage-recipe-in-practice-3 --> DeepSeek-Coder follows the same shape — 2T tokens across 87 languages, FIM, repository-level data organized by dependency order, then instruction tuning <!-- cite:10 --> [[10]](references.md#ref-10) — and StarCoder shows the serving-oriented variant: 1T tokens, an 8k window, FIM, and multi-query attention chosen specifically for fast large-batch inference <!-- cite:8 --> [[8]](references.md#ref-8). The recipe is now stable enough that the interesting variation is in *data* (Section 6) and *alignment* (Sections 8–9), not in the skeleton.

<!-- sec:5.3 -->
### <a id="sec-5.3"></a>5.3 Three Deployment Targets

<a id="p-53-three-deployment-targets-1"></a><!-- para:53-three-deployment-targets-1 --> The same base model is delivered in three quite different shapes, and the differences explain much of the engineering in later sections.

- <a id="p-53-three-deployment-targets-2"></a><!-- para:53-three-deployment-targets-2 --> **Inline autocomplete** is the original Copilot setting: the model completes code at the cursor, conditioned on the surrounding file. It depends on **FIM** (the cursor has code on both sides) and is brutally **latency-bound** — a completion must appear in well under a second — which favors smaller models and the serving tricks of Section 10. All three reports above tie FIM capability specifically to the completion deployment <!-- cite:8 --> [[8]](references.md#ref-8), <!-- cite:10 --> [[10]](references.md#ref-10), <!-- cite:11 --> [[11]](references.md#ref-11).
- **Chat / instruct assistants** come from the SFT + alignment stage (DeepSeek-Coder-Instruct, Qwen2.5-Coder-Instruct) and answer natural-language requests, explain code, and produce multi-file snippets <!-- cite:10 --> [[10]](references.md#ref-10), <!-- cite:11 --> [[11]](references.md#ref-11). They are interactive but turn-based, so latency budgets are looser than autocomplete.
- **Autonomous agents** (Section 12) wrap the model in a loop that observes a repository, takes actions (edit, run tests, search), and iterates. They are **throughput- and cost-bound** rather than latency-bound: a single task may consume many model calls and large contexts, and the dominant cost is total inference, not first-token time. The base-model reports above touch this only indirectly through serving features (multi-query attention, long context); the agent layer itself is built on top.

<a id="p-53-three-deployment-targets-3"></a><!-- para:53-three-deployment-targets-3 --> Holding the deployment target fixed in one's mind is the key to reading the tradeoff discussion of Section 14: the "best" model for sub-100-millisecond autocomplete and the "best" model for resolving a GitHub issue over many minutes are optimized against different objectives entirely.
