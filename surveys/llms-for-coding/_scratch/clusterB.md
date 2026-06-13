# Cluster B evidence — §5 Pipeline, §6 Pretraining Data, §7 Objectives/Tokenization/Scaling

Phase-3 evidence collection. All PDFs content-verified (title/authors checked against first page). Locators are paper-internal (section refs + verbatim snippets quoted from extracted text).

---

### Q1: End-to-end code-LLM pipeline (data → tokenization → pretrain CLM+FIM → mid-train/anneal → SFT/instruct → preference/RL → serving); autocomplete vs chat vs agent deployment.

- **Findings**:
  - **Qwen2.5-Coder three-stage pipeline (explicit)** (qwen25-coder §"three-stage training pipeline", Fig. 2): ① **File-level Pretrain ~5.2T tokens** → ② **Repo-Level Pretrain ~300B tokens** → ③ **Alignment = SFT & DPO** → Qwen2.5-Coder-Instruct. Continues pretraining on top of the Qwen2.5 base over "over 5.5 trillion tokens" (final dataset 5.2T after mixing). Objectives in pretraining: "next token prediction and fill-in-the-middle (FIM)".
  - **Qwen2.5-Coder alignment detail**: "After obtaining the SFT model, we further align ... with the help of offline **direct preference optimization (DPO)**"; preference signal from "a **multilingual code sandbox** to provide code execution feedback" (RL-from-execution-feedback style, not human labels). DPO citation = Rafailov et al. 2023.
  - **Qwen2.5-Coder long-context / serving prep**: repo-level stage uses YARN (Peng et al. 2023) "enabling the model to handle sequences up to **131,072 (128K) tokens**", "≈300B long-context code data", and "extended file-level FIM to the repo-level FIM". For SFT data with short length they "construct the instruction pair with the FIM format to keep the long context capability."
  - **DeepSeek-Coder recipe** (deepseek-coder §3): trained from scratch on **2T tokens / 87 languages**; objectives = next-token-prediction **+ FIM** ("incorporated the Fill-In-Middle (FIM) approach"); 16K context window; then "meticulous fine-tuning using instructional data" → DeepSeek-Coder-Instruct (beats GPT-3.5-Turbo on code tasks).
  - **StarCoder recipe** (starcoder abstract/§): StarCoderBase trained on **1T tokens** from The Stack (86 languages); then "fine-tuned StarCoderBase on **35B Python tokens**, resulting in ... StarCoder." Architecture geared for serving: 8K context, **FIM infilling**, **Multi-Query-Attention (MQA)** "for fast large-batch inference."
  - **Autocomplete vs chat vs agent (deployment differences)**: All three reports tie **FIM/infilling** capability to the *autocomplete/code-completion* deployment (StarCoder: "infilling capabilities through Fill-in-the-Middle"; DeepSeek: FIM "to further bolster the model's code completion capabilities"; Qwen: FIM "where a model predicts the missing parts of a code block"). **Chat/instruct** deployments come from the SFT/instruct stage on instruction datasets (DeepSeek-Coder-Instruct, Qwen2.5-Coder-Instruct). **Agent** angle is weaker in these three base-model reports; serving features for large-batch/long-context (MQA in StarCoder, 128K via YARN in Qwen) are what enable agentic/repo-scale use.
- **Sources**:
  - Hui, Yang, Cui et al., "Qwen2.5-Coder Technical Report," 2024 — (local: download/qwen25-coder-2024.pdf)
  - Guo, Zhu, Yang et al., "DeepSeek-Coder: When the LLM Meets Programming," 2024 — (local: download/deepseek-coder-2024.pdf)
  - Li, Ben Allal, Zi et al., "StarCoder: may the source be with you!" TMLR 2023 — (local: download/starcoder-2023.pdf)
  - Lozhkov, Li, Ben Allal et al., "StarCoder 2 and The Stack v2," 2024 — (local: download/starcoder2-2024.pdf)
- **Confidence**: high (pipeline stages, objectives, alignment all verbatim). Medium on the explicit "autocomplete vs chat vs **agent**" three-way contrast — base-model reports cover autocomplete (FIM) and chat (instruct) cleanly; the agent-deployment contrast is mostly implied via serving/long-context features rather than stated as a deployment taxonomy.
- **Gaps**: No dedicated "mid-training / annealing" stage named in DeepSeek/StarCoder (Qwen's repo-level 300B stage is the closest analogue). RLHF/PPO-for-code and explicit agent-serving (tool-loop) recipes are not in these reports; pull from a CodeRL / RLEF / agent-serving source for §5 agent deployment.

---

### Q2: Code pretraining corpora — The Stack v1 & v2: size, languages, GitHub sourcing, license filtering, opt-out/governance.

- **Findings — The Stack v1** (the-stack-2022):
  - Size: **"a 3.1 TB dataset consisting of permissively licensed source code in 30 programming languages"** (abstract). Full all-license collection: "the all-license dataset contains **over 29 TB** of data. Only selecting permissively licensed files reduces the dataset to **3.1 TB**, i.e. only roughly **10%** of the dataset is kept" (§Data per programming language).
  - GitHub sourcing: "We first collected a set of active GitHub repository names from **GHArchive**" (the public GitHub event timeline). License via GHArchive metadata for 26.4M repos; for the remaining **110.9M repos** they "run the **go-license-detector**" → SPDX identifier.
  - License distribution (SPDX, repos in M / %): not_found 112.51 / 81.91%; **MIT 13.16 / 9.58%; Apache-2.0 3.72 / 2.71%; BSD-3-Clause 0.76 / 0.55%**; GPL-3.0-only 0.55 / 0.4% (GPL excluded from permissive subset).
  - Biggest permissive languages: "HTML (746 GB), Javascript (486 GB), Java (271 GB), and C (222 GB)–consume more than 55% of the dataset size."
  - Opt-out/governance: "possibility to have their data removed ... details of this opt-out process in a data governance plan in Section 3.2" + removal-request URL. Title is "The Stack: 3 TB of permissively licensed source code."
- **Findings — The Stack v2** (starcoder2-2024 §2, abstract):
  - Built "In partnership with **Software Heritage (SWH)** ... on top of the digital commons of their source code archive." Spans **"619 programming languages"** plus GitHub PRs, Kaggle notebooks, documentation, intermediate representations (LLVM IR), etc.
  - Raw size: "The Stack v2 is **ten times larger** than its predecessor, yielding a **raw dataset of 67.5 TB**."
  - Unique training tokens: "**900B+ unique tokens**, **4× larger** than the first StarCoder dataset."
  - License: "extract repository-level license information from **GHArchive** ... When the repo-level license is not available, i.e., for **96.93% of repositories**, we use the **ScanCode Toolkit** to detect file-level licenses."
  - Training-subset sizes (Table): the-stack-v2-train-**smol** = 525.5B tokens (used by 3B/7B), the-stack-v2-train-**full** = 775.48B (used by 15B); + Pull requests 19.54B, Issues 11.06B, Jupyter structured 14.74B. Final per-model: 3B→622B+ unique; 7B→658B+; **15B→913B+ unique tokens**.
  - Opt-out: governance/opt-out tooling carried over ("an opt-out process for those who prefer to exclude their code"; "developers who requested to have their code removed").
- **Sources**:
  - Kocetkov, Li, Ben Allal et al., "The Stack: 3 TB of permissively licensed source code," 2022 — (local: download/the-stack-2022.pdf)
  - Lozhkov et al., "StarCoder 2 and The Stack v2," 2024 — (local: download/starcoder2-2024.pdf)
- **Confidence**: high (all numbers verbatim from extracted text).
- **Gaps**: None material for v1/v2 headline numbers. The Stack v1 "358 programming languages" total (vs 30 in the permissive release) is corroborated from the StarCoder v1 paper (§"From the 358 programming languages in The Stack, we selected 86").

---

### Q3: Dedup & quality — exact vs near-dedup (MinHash/LSH) vs semantic; benchmark decontamination; quality filtering & "data is the moat" / Phi-1 claims.

- **Findings — Dedup**:
  - **The Stack v1** (near-dedup pipeline): "compute the **MinHash** (Broder 2000) with **256 permutations** of all documents, and use **Locality Sensitive Hashing (LSH)** to find clusters of duplicates ... two files similar when their **Jaccard similarity exceeds 0.85**." Impact: "in the permissive license dataset, **38.6% of the files are just near-duplicates** ... and are removed." Finding: "**near-deduplicating the data significantly boosts performance across all experiments**."
  - **StarCoder v1**: same SantaCoder pipeline — "calculating the **MinHashes** ... followed by **LSH** to map similar code files to the same bucket. We used 5-[grams]..."
  - **StarCoder2 / Stack v2**: SantaCoder dedup; "**5-grams and a Jaccard similarity of 0.7**"; tiebreak by "files from repositories with higher star and fork counts or from the latest commit date" to preserve repo context.
  - **DeepSeek-Coder**: adds **repository-level deduplication** (dedup at repo granularity, not just file); pipeline = "data crawling, rule-based filtering, dependency parsing, repository-level deduplication, and quality screening."
- **Findings — Decontamination**:
  - **StarCoder / StarCoder2**: "remove files that contain **docstrings or solutions from HumanEval and MBPP, docstrings from APPS, questions from GSM8K, or prompts from DS1000**."
  - **DeepSeek-Coder n-gram filter**: "if a piece of code includes a **10-gram string identical to any in the test data, it is excluded** ... strings shorter than 10-grams but no less than **3-grams**, we use an **exact match** approach." Filters HumanEval, MBPP, GSM8K, MATH.
  - **Qwen2.5-Coder**: dedicated **Decontamination** section — "performed decontamination on all data, including both pre-training and post-training datasets. We removed key datasets such as HumanEval, MBPP, GSM8K, and MATH."
- **Findings — Quality / "data is the moat" / Phi-1** (phi-1-2023, "Textbooks Are All You Need"):
  - Model: "**phi-1** is a Transformer-based model with **1.3B parameters**, trained for **4 days on 8 A100s**, using a selection of **'textbook quality' data from the web (6B tokens)** and synthetically generated textbooks and exercises with **GPT-3.5 (1B tokens)**."
  - Headline result: "**phi-1 attains pass@1 accuracy 50.6% on HumanEval and 55.5% on MBPP**" — "Despite being several orders of magnitude smaller than competing models."
  - Training budget: "~**8 passes over 7B tokens** (slightly over 50B total tokens seen) followed by finetuning on **less than 200M tokens**." CodeTextbook (pretrain) = subset of The Stack + StackOverflow via a **LM-based classifier** (~6B tokens) + <1B synthetic GPT-3.5 textbooks; then finetune on **CodeExercises** → 51% HumanEval ("top performance of 51% on HumanEval").
  - phi-1-small: "**350M parameters** trained with the same pipeline ... still achieves **45% on HumanEval**."
  - "Data is the moat" thesis (verbatim): "**improving data quality can dramatically change the shape of the scaling laws, potentially allowing to match the performance of large-scale models with much leaner training/model**."
- **Sources**:
  - Kocetkov et al. 2022 — (local: download/the-stack-2022.pdf); Li et al. (StarCoder) 2023 — (local: download/starcoder-2023.pdf); Lozhkov et al. (StarCoder2) 2024 — (local: download/starcoder2-2024.pdf); Guo et al. (DeepSeek-Coder) 2024 — (local: download/deepseek-coder-2024.pdf)
  - Gunasekar, Zhang, Aneja et al., "Textbooks Are All You Need" (phi-1), 2023 — (local: download/phi1-2023.pdf)
- **Confidence**: high (every number verbatim).
- **Gaps**: "Semantic dedup" as a distinct technique is NOT used by these code corpora — they use exact + MinHash/LSH near-dedup (+ DeepSeek repo-level). For a true *semantic* dedup citation (embedding-based / SemDeDup) a separate source is needed; flag for §6.

---

### Q4: FIM implementation — FIM rate, PSM/SPM, context- vs document-level FIM; tokenizer design (vocab, byte-level BPE, whitespace/tabs, fertility).

- **Findings — FIM mechanics** (Bavarian et al. 2022, the canonical FIM paper, content-verified as "Efficient Training of Language Models to Fill in the Middle"):
  - Transform: split document into (prefix, middle, suffix); with **FIM rate p** reorder to (prefix, suffix, middle), concatenate with **sentinel tokens `<PRE>`, `<MID>`, `<SUF>`**.
  - "In document-level FIM, with a certain probability **p called the FIM rate (we use p = 0.5** for our main suite of models)."
  - **PSM** (prefix-suffix-middle) vs **SPM** (suffix-prefix-middle) vs **joint SPM+PSM** (paper §4.3); **context-level vs document-level FIM** (§3.2 / §4.4) — context-level applies the FIM split *after* chunking into the training context, document-level applies it per-document before packing.
  - **FIM-for-free property**: "**FIM can be learned for free**" — 50% vs 0% FIM rate gives same left-to-right test loss (Fig. 1), so infilling is a free capability add. Character-level FIM beats token-level on random-span infilling (token-level "never trained on cases where a token is broken into two parts").
- **Findings — FIM in the code models**:
  - **StarCoder v1**: "apply FIM at the **character-level** ... with a **FIM-rate of 0.5**, and use **PSM mode with probability .5 and SPMv2 mode with probability .5**."
  - **DeepSeek-Coder**: "**FIM rate of 0.5**, following the **PSM mode**", applied "**at the document level before the packing process**." Ablated 0% / 50% / 100% FIM-rate and 50% MSP (T5 Masked-Span-Prediction); chose 50% PSM ("with a 50% PSM rate, the model outperforms the MSP strategy"). FIM sentinels `<｜fim_begin｜>...<｜fim_hole｜>...<｜fim_end｜>` + `<|eos_token|>`.
  - **StarCoder2**: FIM (Bavarian et al. 2022) applied within repository context; FIM-in-repo format uses `<fim_prefix>`/`<fim_suffix>`/`<fim_middle>` interleaved with `<file_sep>` (FIM applied to one source file inside the repo concatenation).
  - **Qwen2.5-Coder**: special tokens `<|fim_prefix|>` (151659), `<|fim_middle|>`, `<|fim_suffix|>`, `<|fim_pad|>`; both **file-level FIM** and (long-context stage) **repo-level FIM** formats.
- **Findings — Tokenizer design**:
  - **StarCoder v1 & v2**: HF Tokenizers, **byte-level Byte-Pair-Encoding**, **vocab = 49,152 tokens** (incl. sentinels). "pre-tokenization step includes a **digit-splitter** and the regex splitter from the **GPT-2 pre-tokenizer**." StarCoder2 notes "increasing the vocabulary size to 100K did not improve performance" → kept 49,152.
  - **DeepSeek-Coder**: HF Tokenizer **BPE** (Sennrich et al. 2015), **vocab = 32,000**.
  - **Qwen2.5-Coder**: inherits Qwen2.5 vocab, **vocab = 151,646 tokens**, adds code/FIM special tokens.
- **Sources**:
  - Bavarian, Jun, Tezak, Schulman et al. (OpenAI), "Efficient Training of LMs to Fill in the Middle," 2022 — (local: download/fim-bavarian-2022.pdf) [present in download/ from a sibling cluster; content-verified here]
  - StarCoder 2023, StarCoder2 2024, DeepSeek-Coder 2024, Qwen2.5-Coder 2024 — (local: download/{starcoder-2023, starcoder2-2024, deepseek-coder-2024, qwen25-coder-2024}.pdf)
- **Confidence**: high on FIM rate/PSM-SPM/context-vs-doc and vocab sizes (all verbatim).
- **Gaps**: Explicit **fertility** numbers (tokens-per-character/byte for code) and detailed **whitespace/tab/indentation** handling (e.g. whitespace-run tokens) are NOT quantified in the extracted snippets — these papers state byte-level BPE + digit-splitter but do not give a fertility table. Flag for §7: a tokenizer-fertility comparison may need a dedicated tokenization-for-code source.

---

### Q5: Repo-level / long-context pretraining (repo concatenation, topological file ordering, context windows) + code scaling behavior & code:NL:math mixture ratios.

- **Findings — Repo-level concatenation & file ordering**:
  - **DeepSeek-Coder (topological sort — the key citation)**: "**Algorithm 1 describes a topological sort for dependency analysis** on a list of files within the same project." Parses imports ("'import' in Python, 'using' in C#, 'include' in C") to build a dependency graph (adjacency list + in-degrees), then "**each sequence's files are concatenated to form a single training sample**" with "a comment indicating the file's path added at the beginning of each file." Goal: "organize the pre-training data at the **repository level** to enhance ... cross-file [understanding] within a repository."
  - **StarCoder2 (random order)**: "Each example in the dataset is a **full repository with files arranged in a random order**." Repo concat format: `<repo_name>reponame<file_sep>filepath1\ncode1<file_sep>filepath2\ncode2 ... <|endoftext|>`. (Contrast: DeepSeek topological-sorts; StarCoder2 randomizes within repo.)
  - **Qwen2.5-Coder**: explicit **file-level + repo-level pretraining** stages; repo-level stage is 300B tokens.
- **Findings — Context window sizes**:
  - StarCoder v1: **8K (8192)** context (8K via training seq_len 8192). StarCoder2: **base 4K (4,096)**, then long-context continued pretrain on **200B tokens at 16,384 context with a 4,096 sliding window**, FlashAttention-2, increased RoPE θ.
  - DeepSeek-Coder: **16,384 (16K)** context window.
  - Qwen2.5-Coder: file-level 4K-ish base extended via **YARN to 131,072 (128K)** in repo-level stage.
- **Findings — Mixture ratios (code : NL : math)**:
  - **DeepSeek-Coder**: "**87% source code, 10% English code-related natural language corpus, and 3% code-unrelated Chinese natural language corpus**." (Code corpus 798 GB / 603M files.)
  - **Qwen2.5-Coder (key mixture-ablation result)**: ablated Code:Text:Math at 100:0:0, 85:10:5, 70:20:10 → "**the 7:2:1 ratio outperformed the others, even surpassing ... groups with a higher proportion of code**." Final: "**70% Code, 20% Text, and 10% Math** ... final training dataset comprises **5.2 trillion tokens**." Interpretation given: math/text data help code performance (counterintuitive — more code is not strictly better).
- **Findings — Code scaling**:
  - StarCoder2 trains 3B/7B/15B on **3.3 to 4.3 trillion tokens** (well past Chinchilla-optimal — over-training small models for inference efficiency); per-model epochs: 3B→4.98 ep / 3.1T, 7B→5.31 ep / 3.5T, 15B→4.49 ep / 4.1T.
  - phi-1 (Q3) is the headline *code-specific scaling* observation: data quality "can dramatically change the shape of the scaling laws."
- **Sources**:
  - Guo et al. (DeepSeek-Coder) 2024 — (local: download/deepseek-coder-2024.pdf) [topological sort, 87:10:3 mix, 16K]
  - Lozhkov et al. (StarCoder2) 2024 — (local: download/starcoder2-2024.pdf) [random repo order, 4K→16K, 3.3–4.3T]
  - Hui et al. (Qwen2.5-Coder) 2024 — (local: download/qwen25-coder-2024.pdf) [70:20:10 mix, 128K via YARN, file+repo stages]
  - Li et al. (StarCoder) 2023 — (local: download/starcoder-2023.pdf) [8K context]
- **Confidence**: high (topological sort, random-order, mixture ratios, context windows all verbatim).
- **Gaps**: No code-specific Chinchilla-style scaling-law *exponents* are derived in these reports (StarCoder2 over-trains but does not fit a scaling law). For a §7 code scaling-law treatment, a dedicated scaling source (e.g. a code-data-mixture or compute-optimal study) would be needed beyond these four model reports.

---

## Acquisition ledger (this cluster)
- (local: download/the-stack-2022.pdf) — 27pp, verified
- (local: download/starcoder-2023.pdf) — 55pp, verified
- (local: download/starcoder2-2024.pdf) — 61pp, verified
- (local: download/deepseek-coder-2024.pdf) — 23pp, verified
- (local: download/qwen25-coder-2024.pdf) — 32pp, verified
- (local: download/phi1-2023.pdf) — 26pp, verified
- (local: download/fim-bavarian-2022.pdf) — present from sibling cluster, content-verified here, used for Q4 PSM/SPM/context-vs-doc-FIM definitions
