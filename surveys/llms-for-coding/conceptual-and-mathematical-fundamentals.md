## 4 Conceptual and Mathematical Fundamentals

<a id="p-4-conceptual-and-mathematical-fundamentals-1"></a><!-- para:4-conceptual-and-mathematical-fundamentals-1 --> This section builds the minimum formal apparatus the rest of the survey relies on: the training objective, how code is tokenized, the fill-in-the-middle transform that gives causal models the ability to infill, and the pass@k estimator that defines how code ability is measured. A reader new to the area can treat each subsection as "the intuition, then the equation."

<!-- sec:4.1 -->
### <a id="sec-4.1"></a>4.1 The Autoregressive Objective on Code

<a id="p-41-the-autoregressive-objective-on-code-1"></a><!-- para:41-the-autoregressive-objective-on-code-1 --> A code language model is, at bottom, an ordinary autoregressive Transformer. Given a token sequence $x = (x_1,\dots,x_T)$ produced by a tokenizer, the model factorizes the joint probability left to right and is trained to minimize the negative log-likelihood

<a id="eq-1"></a><!-- eq:4-1 -->
$$
\mathcal{L}(\theta) = -\sum_{t=1}^{T} \log p_\theta\!\left(x_t \mid x_{<t}\right) \tag{1}
$$

<a id="p-41-the-autoregressive-objective-on-code-2"></a><!-- para:41-the-autoregressive-objective-on-code-2 --> where the sequences $x$ "happen to be source code." No code-specific loss is needed for the base capability: CodeGen and InCoder are explicitly trained to maximize the likelihood of a corpus of code <!-- cite:3 --> [[3]](references.md#ref-3), <!-- cite:4 --> [[4]](references.md#ref-4), and Codex is a GPT-family model fine-tuned on code <!-- cite:1 --> [[1]](references.md#ref-1). Everything code-specific — infilling, repository structure, execution feedback — is layered on top of Equation <!-- ref:4-1 -->[(1)](#eq-1), not substituted for it.

<!-- sec:4.2 -->
### <a id="sec-4.2"></a>4.2 Tokenization for Code

<a id="p-42-tokenization-for-code-1"></a><!-- para:42-tokenization-for-code-1 --> Code stresses a tokenizer in ways prose does not: significant indentation, runs of whitespace, and long compound identifiers. Two design responses recur. CodeGen extends the GPT-2 byte-pair vocabulary with special tokens for repeated runs of tabs and spaces, compressing Python's indentation <!-- cite:3 --> [[3]](references.md#ref-3). InCoder instead trains a byte-level BPE tokenizer that allows merges to cross whitespace (excluding newlines), so an idiom like `import numpy as np` can become a single token; this reduces the tokens needed to encode its corpus by 45% relative to GPT-2's tokenizer <!-- cite:4 --> [[4]](references.md#ref-4). Modern code models use byte-level BPE with vocabularies tuned for the code mixture — 49,152 for StarCoder, 32,000 for DeepSeek-Coder, 151,646 for Qwen2.5-Coder <!-- cite:9 --> [[9]](references.md#ref-9), <!-- cite:10 --> [[10]](references.md#ref-10), <!-- cite:11 --> [[11]](references.md#ref-11) — a point developed in Section 7. The byte-level fallback also guarantees that arbitrary identifiers and Unicode never produce out-of-vocabulary tokens.

<!-- sec:4.3 -->
### <a id="sec-4.3"></a>4.3 Fill-in-the-Middle: Teaching a Causal Model to Infill

<a id="p-43-fill-in-the-middle-teaching-a-causal-model-to-infill-1"></a><!-- para:43-fill-in-the-middle-teaching-a-causal-model-to-infill-1 --> A purely left-to-right model can only condition on context to its left, which prevents it from filling a hole that has committed code on both sides — the common case when editing. A masked (BERT-style) model sees both sides but is trained to predict only a small fraction of tokens and cannot generate freely. Fill-in-the-middle (FIM) reconciles the two with a strikingly simple idea: rewrite a fraction of training documents so the model still trains autoregressively, yet learns to infill. Split a document into three pieces and move the middle to the end <!-- cite:5 --> [[5]](references.md#ref-5):

<a id="eq-2"></a><!-- eq:4-2 -->
$$
(\text{prefix},\ \text{middle},\ \text{suffix}) \;\longrightarrow\; \langle\text{PRE}\rangle\,\text{prefix}\,\langle\text{SUF}\rangle\,\text{suffix}\,\langle\text{MID}\rangle\,\text{middle} \tag{2}
$$

<a id="p-43-fill-in-the-middle-teaching-a-causal-model-to-infill-2"></a><!-- para:43-fill-in-the-middle-teaching-a-causal-model-to-infill-2 --> The reordered form in Equation <!-- ref:4-2 -->[(2)](#eq-2) is the **prefix-suffix-middle (PSM)** layout, concatenated with sentinel tokens. At inference the model is prompted with everything up to and including $\langle\text{MID}\rangle$ and samples the middle until it emits an end token. A **suffix-prefix-middle (SPM)** ordering also exists and is preferred for key-value cache reuse, because appending tokens to the prefix does not invalidate the cached suffix <!-- cite:5 --> [[5]](references.md#ref-5). The transform is applied at the character level so completions remain sensible when a prefix ends mid-token, and the best results come from training jointly on PSM and SPM <!-- cite:5 --> [[5]](references.md#ref-5). The defining empirical result is "FIM-for-free": training with a 50% FIM rate leaves the left-to-right loss unchanged, so infilling is acquired at no measurable cost to ordinary generation <!-- cite:5 --> [[5]](references.md#ref-5). Production code models adopt FIM almost universally (Section 7).

<!-- sec:4.4 -->
### <a id="sec-4.4"></a>4.4 Measuring Correctness: The pass@k Estimator

<a id="p-44-measuring-correctness-the-passk-estimator-1"></a><!-- para:44-measuring-correctness-the-passk-estimator-1 --> Because code is executable (Section 2), it is judged by *running it*, not by string overlap with a reference. The standard metric is **pass@k**: generate $k$ samples for a problem and count it solved if any sample passes the problem's unit tests. Estimating this naively — draw exactly $k$ samples and report the solved fraction — is high-variance. Codex instead draws $n \geq k$ samples per problem (the paper uses $n = 200$, $k \leq 100$), counts the number $c \leq n$ that pass, and computes the unbiased estimator <!-- cite:1 --> [[1]](references.md#ref-1)

<a id="eq-3"></a><!-- eq:4-3 -->
$$
\text{pass@}k := \mathbb{E}_{\text{problems}}\!\left[\,1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}\,\right] \tag{3}
$$

<a id="p-44-measuring-correctness-the-passk-estimator-2"></a><!-- para:44-measuring-correctness-the-passk-estimator-2 --> The bracketed term in Equation <!-- ref:4-3 -->[(3)](#eq-3) is one minus the probability that a size-$k$ subset of the $n$ samples contains *no* correct sample. It is tempting to instead estimate pass@k as $1-(1-\hat{p})^k$ from an empirical pass@1 of $\hat{p}$, but Codex shows this is biased <!-- cite:1 --> [[1]](references.md#ref-1). Evaluating Equation <!-- ref:4-3 -->[(3)](#eq-3) directly overflows for large $n$, so it is computed in the numerically stable product form

<a id="eq-4"></a><!-- eq:4-4 -->
$$
\text{pass@}k = 1 - \prod_{i=n-c+1}^{n}\left(1 - \frac{k}{i}\right) \tag{4}
$$

<a id="p-44-measuring-correctness-the-passk-estimator-3"></a><!-- para:44-measuring-correctness-the-passk-estimator-3 --> Two consequences matter for the whole survey. First, pass@k separates a model's *generation* quality (pass@1) from the leverage of *sampling many candidates and selecting* (the gap up to pass@100), which is precisely what reranking and test-time methods exploit (Section 9). Second, the metric is only as honest as the test suite behind it — a theme that drives the test-adequacy critique of Section 13. Functional correctness is "the most convincing" criterion because it is the one human developers use <!-- cite:1 --> [[1]](references.md#ref-1), but it inherits the coverage of whatever tests define it.
