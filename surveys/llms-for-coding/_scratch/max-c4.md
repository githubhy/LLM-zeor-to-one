# C4 — Code pretraining: objectives & data

## Q1. Fill-in-the-middle, exactly (+ InCoder comparison)

### FIM document transformation (exact)
- **Claim**: FIM applies a data-only transformation that splits a document into three contiguous pieces (prefix, middle, suffix) split at two random positions, then reorders them to prefix-suffix-middle (PSM) or suffix-prefix-middle (SPM), joined with sentinel tokens, so a standard causal/autoregressive LM can be trained on it unchanged.
- **Numbers**: FIM rate p = 0.5 for the main suite of 8 models (50M–6.9B params); document split uniformly at random so prefix/middle/suffix are each 1/3 of the document length in expectation; ablation sweep over FIM rates {0, 0.25, 0.5, 0.75, 0.9, 1.0} on 6 "large" models trained for 50B tokens; main scans trained on 100B tokens; context length 2048 for all 8 models.
- **Conditions**: OpenAI GPT-3/Codex-architecture causal decoder-only transformers, relative attention (Shaw et al. 2018 / Dai et al. 2019) instead of learned positional embeddings, trained from random init (not finetuned from GPT-3/Codex), code models trained on the same 159GB Python dataset used for Codex (scraped May 2020, predates HumanEval so no train/test leak); natural-language models trained on the GPT-3 dataset. July 2022 (arXiv v1 28 Jul 2022).
- **Source**: Bavarian, Jun, Tezak, Schulman, McLeavey, Tworek, Chen (OpenAI), "Efficient Training of Language Models to Fill in the Middle," 2022, arXiv:2207.14255
- **Quality tier**: primary
- **Quote**: "The key to our approach... is a transformation applied to a fraction of our dataset, in which we split documents into three pieces at random and move the middle piece to the end: document → (prefix, middle, suffix) → (prefix, suffix, middle) We then concatenate the three pieces using sentinel tokens."
- **Quote (document-level split)**: "In document-level FIM, with a certain probability p called the FIM rate (we use p = 0.5 for our main suite of models), we cut each document into three parts: prefix, middle, and suffix. We perform this split prior to tokenization, when the document is still a sequence of characters. We split uniformly at random, which means the lengths of prefix, middle, and suffix are each 1/3 of the full document in expectation."
- **Confidence**: high
- **Local path**: download/fim-bavarian-2022.pdf

```
FIM TRANSFORMATION (verbatim)

Document split (character-level, before tokenization):
  document -> (prefix, middle, suffix) -> (prefix, suffix, middle)

PSM encoding (equation, p.7):
  <PRE> ∘ Enc(prefix) ∘ <SUF> ∘ Enc(suffix) ∘ <MID> ∘ Enc(middle)      (PSM)
  where ∘ = concatenation. Loss is kept on ALL THREE sections (prefix,
  middle, suffix) plus the <EOT> boundary token — FIM does not mask any
  loss relative to plain AR training.

PSM inference prompt:
  <PRE> ∘ Enc(prefix) ∘ <SUF> ∘ Enc(suffix) ∘ <MID>                    (PSM inference)
  (model samples until it emits <EOT>, signaling it has "joined" prefix
  and suffix)

SPM mode (swap order of prefix and suffix; motivated by KV-cache reuse
during inference — appending to the prefix in SPM mode does not
invalidate the suffix's cached keys/values):

  SPM variant 1 (natural, NOT used in main runs):
    <SUF> ∘ Enc(suffix) ∘ <PRE> ∘ Enc(prefix) ∘ <MID> ∘ Enc(middle) ∘ <EOT>

  SPM variant 2 (the one actually used, Appendix D):
    <PRE> ∘ <SUF> ∘ Enc(suffix) ∘ <MID> ∘ Enc(prefix) ∘ Enc(middle) ∘ <EOT>

  Rationale for variant 2 over variant 1 (verbatim): "The reason that we
  do not use the former is that it creates a separation between PSM and
  SPM, which may result to less transfer between them ... the second
  variant SPM data occurs naturally as part of PSM training since when
  we split a document uniformly at random, sometimes the chosen prefix
  will be empty." I.e. variant 2 makes Enc(prefix)∘Enc(middle) one
  contiguous unbroken token run (no sentinel between them), same as a
  PSM example whose sampled prefix happens to be empty — maximizing
  cross-mode transfer.

Joint training: FIM rate p is split 50/50 between PSM and SPM
formatting ("each mode inherits half of the total FIM rate p"), so a
model sees both orderings at inference.

Context-level FIM (production default, Sec 3.2): apply the transform
AFTER chunking to the model's context length rather than at the raw
document level, splitting a packed context on its <EOT> boundary
tokens, turning some sub-documents into FIM examples at rate p, then
rejoining with <EOT> and trimming/padding to context length. Motivation:
document-level FIM on a long document risks the prefix or suffix being
cut off entirely by chunking, fragmenting the FIM signal. Adopted for
"all our main FIM runs in this work."
```

### FIM-for-free claim, exact statement + evidence
- **Claim**: Training with a FIM-transformed fraction of the data (up to 90%) does not degrade the original left-to-right (autoregressive) capability relative to a 0%-FIM baseline, when measured by loss, standard downstream benchmarks, and sampling-based evals — so infilling can be added "for free" during pretraining (contrasted with finetuning, which is NOT free).
- **Numbers**: verified across 8 models 50M–6.9B params, 100B tokens each, at FIM rate 50% (main comparison); a further ablation of 6 large models at rates {0, 0.25, 0.5, 0.75, 0.9, 1.0} for 50B tokens shows AR loss is flat up to 90% FIM rate and only degrades at 100%; NL and code left-to-right test loss curves for 0% vs 50% FIM are visually superimposed in Fig. 1; HumanEval pass@1/pass@10 curves for 0% vs 50% FIM are likewise superimposed (Fig. 3b).
- **Conditions**: same 8-model / 100B-token suite as above; downstream NL evals: PIQA, Winograd, WinoGrande, DROP, QuAC, HellaSwag, LAMBADA, StoryCloze (few-shot except DROP/QuAC); code eval: HumanEval pass@k, temperature 0.8, 400 samples/task.
- **Source**: Bavarian et al., "Efficient Training of Language Models to Fill in the Middle," 2022, arXiv:2207.14255
- **Quality tier**: primary
- **Quote (title claim, Fig.1 caption)**: "FIM can be learned for free. We pretrain language models with 50% and 0% FIM rates on two domains, natural language and code, and evaluate the test loss of all the final snapshots. All models are trained on 100B tokens of data. We observe that joint FIM training incurs no cost as the original left-to-right loss trend remains the same even though the models see the original data only 50% of the time and the models are learning a new capability."
- **Quote (abstract)**: "We show that autoregressive language models can learn to infill text after we apply a straightforward transformation to the dataset, which simply moves a span of text from the middle of a document to its end. While this data augmentation has garnered much interest in recent years, we provide extensive evidence that training models with a large fraction of data transformed in this way does not harm the original left-to-right generative capability... Given the usefulness, simplicity, and efficiency of training models to fill-in-the-middle (FIM), we suggest that future autoregressive language models be trained with FIM by default."
- **Quote (stronger form / finetuning inefficiency)**: "learning FIM in pretraining is free while leaving it to finetuning is surprisingly costly... While FIM can be learned for free during pretraining, learning FIM during finetuning requires a significant amount of additional compute to reach similar levels of performance as pretraining."
- **Quote (limit of free-ness)**: "a FIM rate even up to 90% does not cause any degradation in left-to-right capabilities. However, there is a clear sign of degradation in ordinary AR test loss with 100% FIM rate."
- **Confidence**: high
- **Local path**: download/fim-bavarian-2022.pdf

### Why FIM-transformed data is still a valid autoregressive likelihood (derivation scaffolding — what is permuted / conditioned on)
- **Claim**: FIM is not a new loss or architecture — it is a fixed, document-level *reordering* of the token sequence (prefix, suffix, middle instead of prefix, middle, suffix) with sentinel-token boundary markers; the model is trained with the ordinary next-token cross-entropy loss on this permuted sequence, so nothing about the autoregressive factorization changes — only the joint distribution being factorized is over "PSM-formatted documents" instead of "natural left-to-right documents." Loss is kept on prefix, middle, AND suffix tokens (not masked on any of them), so the model still learns to predict the suffix immediately after the prefix (as in ordinary AR) while ALSO learning, later in the same sequence, to predict the middle span conditioned on both the prefix (already generated, in context) and the suffix (already generated, in context) — this is what makes P(middle | prefix, suffix) learnable within a strictly left-to-right causal model.
- **Numbers**: none (conceptual/architectural point — no new numbers beyond the transformation formula above)
- **Conditions**: applies identically to PSM and SPM, document-level and context-level FIM
- **Source**: Bavarian et al., "Efficient Training of Language Models to Fill in the Middle," 2022, arXiv:2207.14255, §3 and §2.2
- **Quality tier**: primary
- **Quote**: "We reiterate that we keep the loss on all three sections prefix, middle, and suffix, so FIM training does not cause a decrease in the autoregressive learning signal." Also: "To create FIM tests, we apply the FIM transformation to the examples from the AR test sets with a FIM rate of 100%. Using the same underlying examples in FIM and AR test sets allows us to compare FIM and AR test losses... we create a masked version of these test sets where we only measure the loss on the middle span tokens. The latter test sets are used to measure P(middle | prefix, suffix) for FIM models and P(middle | prefix) for AR models."
- **Confidence**: high
- **Local path**: download/fim-bavarian-2022.pdf

### InCoder: causal-masking infilling vs FIM — how they differ
- **Claim**: InCoder's "causal masking" (CM) objective generalizes FIM's single 3-way prefix/middle/suffix split to MULTIPLE, variable-length, independently-located masked spans per document (span count ~ Poisson(mean=1), truncated to [1,256]; spans rejected/resampled on overlap), each replaced in-place by a distinct sentinel token `<Mask:k>` and moved to the end of the document, so the sentinel serves double duty: its FIRST occurrence (in the main body) marks the deletion site, its SECOND occurrence (at the end, prepended to the moved span) marks where generation of that span begins, terminated by an explicit `<EOM>` (end-of-mask) token per span. FIM (single split at two random positions) is a special case of this — one span, always the "middle" of the document. InCoder also decontaminates its pretraining corpus by removing overlap with its own eval datasets, and shows CM training matches plain left-to-right training on standard synthesis benchmarks while substantially beating left-to-right-only baselines (single-candidate and reranking) on zero-shot infilling.
- **Numbers**: InCoder-6.7B trained on 159GB of code (52GB Python, 28 languages total) + 57GB StackOverflow content; span-count distribution Poisson(mean=1) truncated to [1,256]; HumanEval-derived single-line infilling: CM infilling pass rate 69.0 vs L-R single 48.2 vs L-R reranking 54.9 (exact match 56.3 / 38.7 / 44.1); multi-line infilling: CM 38.6 vs L-R single 24.9 vs L-R reranking 28.2 (exact match 20.6/15.8/17.6); CodeXGLUE Python docstring generation (zero-shot) BLEU: CM infilling 18.27 vs L-R single 16.05 vs L-R reranking 17.14, approaching the fully-finetuned CodeBERT baseline (19.06).
- **Conditions**: InCoder-6.7B (Fairseq dense-model architecture per Artetxe et al. 2021); nucleus sampling p=0.95; published as ICLR 2023 (arXiv 9 Apr 2023, orig. April 2022).
- **Source**: Fried, Aghajanyan, Lin, Wang, Wallace, Shi, Zhong, Yih, Zettlemoyer, Lewis (FAIR/UW/Berkeley/TTI-Chicago/CMU), "InCoder: A Generative Model for Code Infilling and Synthesis," ICLR 2023, arXiv:2204.05999
- **Quality tier**: primary
- **Quote (objective)**: "At training time, the causal masking procedure samples a number of spans of contiguous tokens in each document to mask... We sample the number of spans from a Poisson distribution with a mean of one, truncated to the support [1, 256]... Once spans are sampled, each span k is replaced with a special mask sentinel token, <Mask:k>. The sequence of tokens in the span is then moved to the end of the document, with the mask sentinel token prepended and a special end-of-mask token <EOM> token appended. In other words, when a mask token appears for the first time in the left-to-right ordering, it marks the location the span was removed from; when it appears for the second time, it marks the start of the moved span text."
- **Quote (equation 1)**: "log P([Left; <Mask:0>; Right; <Mask:0>; Span; <EOM>])" where Span = D_{i:j} is the sampled span, Left = D_{0:i}, Right = D_{j:N}.
- **Quote (relation to prior masked/causal LM work)**: "In this paper, we adopt the recently proposed causal masking objective (Aghajanyan et al., 2022a), which aims to combine the strengths of both causal and masked language models." (Note: causal masking as an objective predates InCoder — InCoder cites Aghajanyan et al. 2022a as the source of the technique; InCoder is the first LARGE generative code model to apply it. FIM (Bavarian et al., OpenAI, July 2022) and InCoder (Fried et al., orig. April 2022 per arXiv id 2204.05999) are contemporaneous / InCoder slightly predates FIM's arXiv date, though both build on the general "move a span to the end with sentinels" family — GAP: I did not verify a direct citation of one paper by the other from the FIM paper's related-work section (not read in this pass); do not assert priority beyond the arXiv timestamps.)
- **Confidence**: high (mechanism and numbers); medium (priority/lineage claim relative to FIM — flagged as a gap)
- **Local path**: download/incoder-2022.pdf

## Q2. Repo-level pretraining and context construction

| Model | Params | Tokens | Context len | Repo-level packing | FIM? | Source |
|---|---|---|---|---|---|---|
| StarCoder2 | 3B / 7B / 15B | 3.3–4.3T tokens (3B: 622.09B unique tokens over ~5.3 epochs; 7B: 658.58B unique; 15B: 913.23B unique, 4× StarCoderBase's set) | 4k base pretrain -> 16k via continued fine-tune | Files from the same repo are grouped and concatenated in **RANDOM order** within the repo's context window (explicitly NOT dependency-sorted) | Yes — "repo-context file-level FIM": whole repos are 50%-chance FIM candidates; repo text is split into chunks by `<endoftext>`/`<file_sep>`; FIM transform then applied per chunk at 50% probability; repo name + file paths prepended with 50% probability | Lozhkov et al., "StarCoder 2 and The Stack v2," 2024, arXiv:2402.19173 |
| DeepSeek-Coder | 1.3B / 6.7B / 33B | 2 trillion tokens (from-scratch); source mix 87% code + 10% English code-related NL + 3% Chinese NL | 16K window | **Dependency-aware ordering**: parses import/using/include statements per file, builds a per-repo file dependency graph, runs a custom topological sort (Algorithm 1 — modified to select min-in-degree nodes so it tolerates cycles) that places a file after the files it depends on, then concatenates the sorted files into one training sample with a path-comment prepended to each file | Yes — PSM only, FIM rate 0.5, applied at the document level *before* packing, sentinel tokens `<|fim_start|>`,`<|fim_hole|>`,`<|fim_end|>`; ablated against 0%/50%/100% FIM rate and a T5-style Masked-Span-Prediction (MSP) alternative on a 1.3B model — 50% PSM chosen as best completion/infilling trade-off (100% FIM rate gave the *weakest* code-completion capability despite best FIM-only score) | Guo, Zhu, Yang, Xie, Dong, Zhang et al. (DeepSeek-AI), "DeepSeek-Coder: When the Large Language Model Meets Programming," 2024, arXiv:2401.14196 |
| Qwen2.5-Coder | 0.5B/1.5B/3B/7B/14B/32B | 5.5T tokens total, staged: 5.2T at file-level + ~300B at repo-level (final data mixture 70% code : 20% text : 10% math, chosen empirically over 100:0:0 and 85:10:5 — see Q4) | File-level stage: 8,192 tokens. Repo-level stage: context extended 8,192 -> 32,768 tokens (RoPE base 10,000 -> 1,000,000), then YARN extrapolation to 131,072 (128K) tokens | Repo-level stage concatenates multiple files of a repo under dedicated `<\|repo_name\|>` and `<\|file_sep\|>` sentinel tokens (repo name once, then each file prefixed by its path) — ordering within the repo is not stated as dependency-sorted in the excerpt read; FIM is applied to the LAST file in the packed repo context | Hui, Yang, Cui, Yang et al. (Qwen Team, Alibaba), "Qwen2.5-Coder Technical Report," 2024, arXiv:2409.12186 |

### StarCoder2 / The Stack v2 — repo packing detail
- **Claim**: StarCoder2 deliberately packs same-repo files together (repository-context) but orders them RANDOMLY rather than by dependency, unlike DeepSeek-Coder's topological-sort approach; FIM is applied per-chunk within these repo contexts ("repo-context file-level FIM"), a variant selected after "explor[ing] several FIM variants in preliminary experiments."
- **Numbers**: the-stack-v2-train-smol = 525.5B unique tokens (17 mainstream languages + doc/config languages), used for 3B model (622.09B total unique tokens incl. extras); the-stack-v2-train-full = 775.48B unique tokens (619 languages), used for 15B model (913.23B total incl. extras, "4× the size of the training dataset for StarCoderBase"); extras breakdown: pull requests 19.54B, issues 11.06B, Jupyter structured 14.74B, Jupyter scripts 16.29B, Kaggle scripts 1.68B, documentation 1.6B, OpenWebMath 14.42B, Wikipedia 6.12B, StackOverflow 10.26B, ArXiv 30.26B, LHQ 5.78B, intermediate representations 6B tokens.
- **Conditions**: StarCoder2-3B/7B/15B, trained 3.3–4.3T tokens (i.e., multiple epochs over the unique-token pool, capped at <5 epochs per Muennighoff et al. 2023 repetition-scaling guidance); context 4k base -> 16k finetune. Feb 2024 (TMLR submission, arXiv 29 Feb 2024).
- **Source**: Lozhkov, Li, Allal, Cassano, Lamy-Poirier, Tazi et al. (BigCode / Hugging Face / ServiceNow), "StarCoder 2 and The Stack v2: The Next Generation," 2024, arXiv:2402.19173
- **Quality tier**: primary
- **Quote (repo ordering)**: "Starcoder1 was trained with file-context, i.e., the setting where random files are joined into the context window. In this work, we explore training with repository-context, wherein files from the same repository are grouped together. While we considered various methods for grouping files within the repository, we ultimately arranged them in a random order within the same repository."
- **Quote (FIM)**: "To enable the model to perform code infilling tasks, we apply the fill-in-the-middle transformation (FIM...) to the source code. While we explored several FIM variants in preliminary experiments, we opted for repo-context file-level FIM in the StarCoder2 models. In this FIM variant, repositories are selected with a 50% chance of being candidates for FIM. The selected repository examples are split by `<\|endoftext\|>` and `<file_sep>` tokens. Next, we apply the FIM transformation to each chunk with a 50% probability."
- **Quote (over-training)**: "we push the number of training tokens far beyond the compute-optimal number suggested by Chinchilla (Harm's law; de Vries, 2023) and train relatively small models within the range of 3.3 to 4.3 trillion tokens."
- **Confidence**: high
- **Local path**: download/starcoder2-2024.pdf

### DeepSeek-Coder — dependency-aware repo packing detail
- **Claim**: DeepSeek-Coder is the first (their claim) code-LLM pretraining pipeline to explicitly order files within a repository sample by cross-file import dependency via a topological sort over a parsed dependency graph, rather than concatenating files in arbitrary/random order, specifically to teach cross-file context understanding.
- **Numbers**: 2 trillion tokens from scratch; 87 programming languages; raw GitHub crawl (repos created before Feb 2023) reduced to 32.8% of original size by StarCoder-style rule filters; final cleaned corpus 798GB / 603M files (Table 1) before the 87%/10%/3% code/English/Chinese mixture is drawn; repo-level near-dedup applied (treats a whole concatenated repo as one dedup unit, not per-file, "to ensure the integrity of the repository structure"); decontamination via exact 10-gram match (or exact match for <10-gram test strings) against HumanEval, MBPP, GSM8K, MATH.
- **Conditions**: DeepSeek-Coder-Base 1.3B/6.7B/33B, decoder-only Transformer w/ RoPE, 33B variant uses GQA (group size 8), FlashAttention v2, AdamW optimizer, HAI-LLM training framework. Jan 2024 (arXiv 26 Jan 2024, this is v2).
- **Source**: Guo et al. (DeepSeek-AI), "DeepSeek-Coder: When the Large Language Model Meets Programming — The Rise of Code Intelligence," 2024, arXiv:2401.14196
- **Quality tier**: primary
- **Quote**: "in previous works, large language models for code are mainly pre-trained on file-level source code, which ignores the dependencies between different files in a project. However, in practical applications, such models struggle to effectively scale to handle entire project-level code scenarios. Therefore, we will consider how to leverage the dependencies between files within the same repository in this step. Specifically, we first parse the dependencies between files and then arrange these files in an order that ensures the context each file relies on is placed before that file in the input sequence... we only consider the invocation relationships between files and use regular expressions to extract them, such as 'import' in Python, 'using' in C#, and 'include' in C."
- **Quote (FIM sentinel format)**: "< | fim_start | >f_pre< | fim_hole | >f_suf< | fim_end | >f_middle<|eos_token|>" — PSM mode, FIM rate 0.5, applied "at the document level before the packing process, as proposed in the original work by Bavarian et al. (2022)."
- **Quote (FIM-rate ablation finding)**: "the model demonstrates peak performance on the HumanEval-FIM with a 100% FIM rate, this configuration also results in the weakest code completion capability. This indicates a trade-off between FIM and code completion abilities. Moreover, we observe that with a 50% PSM rate, the model outperforms the MSP strategy. To achieve a balance between FIM efficiency and code completion proficiency, we ultimately choose the 50% PSM rate."
- **Confidence**: high
- **Local path**: download/deepseek-coder-2024.pdf

### Qwen2.5-Coder — staged file-level → repo-level pretraining with context/RoPE extension
- **Claim**: Qwen2.5-Coder uses an explicit three-stage pipeline (file-level pretrain -> repo-level pretrain -> alignment/SFT+DPO) where the repo-level stage's PRIMARY purpose is extending usable context length (8,192 -> 32,768 native, -> 131,072 via YARN extrapolation) on ~300B tokens of long-context code data, and extends file-level FIM into a repo-level FIM task using dedicated `<\|repo_name\|>` / `<\|file_sep\|>` sentinel tokens so the model learns to infill conditioned on multiple concatenated files of the same repository, not just one file.
- **Numbers**: file-level stage: 8,192-token sequences, 5.2T tokens; repo-level stage: ~300B tokens, context 8,192->32,768 (RoPE base 10,000->1,000,000), YARN extends to 131,072 (128K); total pretraining tokens 5.5T (matches per-size "# Trained Tokens" in architecture Table 1); vocabulary 151,646 tokens (inherited from Qwen2.5) plus added special tokens `<\|fim_prefix\|>`(151659), `<\|fim_middle\|>`(151660), `<\|fim_suffix\|>`(151661), `<\|fim_pad\|>`(151662), `<\|repo_name\|>`(151663), `<\|file_sep\|>`(151664).
- **Conditions**: Qwen2.5-Coder-0.5B/1.5B/3B/7B/14B/32B, architecture derived directly from Qwen2.5; decontamination via 10-gram overlap against HumanEval, MBPP, GSM8K, MATH, applied to both pretrain AND post-train data. Nov 2024 (arXiv 12 Nov 2024, v3).
- **Source**: Hui, Yang, Cui, Yang, Liu, Zhang, Liu, Zhang, Yu, Lu, Dang, Fan, Zhang, Miao, Quan, Feng, Zheng, Miao, Ren, Ren, Zhou, Lin (Qwen Team, Alibaba), "Qwen2.5-Coder Technical Report," 2024, arXiv:2409.12186
- **Quality tier**: primary
- **Quote (repo-level stage)**: "After file-level pretraining, we turn to repo-level pretraining, aimed at enhancing the model's long-context capabilities. In this stage, the context length is extended from 8,192 tokens to 32,768 tokens, and RoPE's base frequency is adjusted from 10,000 to 1,000,000. To further leverage the model's extrapolation potential, we applied the YARN mechanism, enabling the model to handle sequences up to 131,072 (128K) tokens. In this stage, we used a large amount of high-quality, long-context code data (≈300B) and extended file-level FIM to the repo-level FIM followed by methods described in Lozhkov et al. (2024) [StarCoder2]."
- **Quote (repo-level FIM format, Figure 4, verbatim structure)**: "<\|repo_name\|>{repo_name} / <\|file_sep\|>{file_path1} / {file_content1} / <\|file_sep\|>{file_path2} / {file_content2} / <\|file_sep\|>{file_path3} / <\|fim_prefix\|>{code_pre}<\|fim_suffix\|>{code_suf}<\|fim_middle\|>{code_fim}<\|endoftext\|>" — i.e. earlier files in the repo are given in full, and FIM is applied only within the LAST file listed.
- **Confidence**: high
- **Local path**: download/qwen25-coder-2024.pdf

## Q3. Code data curation

### The Stack — near-deduplication (MinHash/LSH), license filtering
- **Claim**: The Stack (predecessor to The Stack v2 used by StarCoder2) builds a 3.1 TB, 30-language permissively-licensed source-code corpus from a 220.92M-repo GitHub crawl, and finds that near-deduplication (as opposed to exact-dedup only) removes a very large fraction of the data (38.6% of files / 53.7% of volume in the permissive subset) via MinHash+LSH clustering, and that near-dedup "significantly boosts performance across all experiments" on 350M-parameter decoder-only models trained on Python subsets.
- **Numbers**: 220.92M unique repo names collected (GHArchive events, Jan 2015–Mar 2022); 137.36M repos successfully cloned (62% success rate); 51.76B files stored across all repos, only 5.28B unique by git hash (~10%); uncompressed stored size 92.36 TB before language/permissive filtering; final released dataset 3.1 TB across 30 languages (Table 1 total 3135.95 GB, vs CodeParrot 872.95GB, AlphaCode 715.1GB, CodeGen 314.1GB, PolyCoder 253.6GB — "more than three times the size of CodeParrot, the next-largest released code dataset"); license detection (go-license-detector) found NO license for >80% of repos; top detected: MIT 9.6%, Apache-2.0 2.7% of total repos (Table 2 breakdown, e.g. MIT 13.16M repos/9.58%, Apache-2.0 3.72M/2.71%, various GPL variants each ~0.4%); near-dedup via MinHash (256 permutations) + Locality-Sensitive Hashing, Jaccard similarity threshold 0.85 for "similar"; result: 38.6% of files in the permissive-license dataset are near-duplicates and removed, representing 53.7% of the dataset's volume.
- **Conditions**: BigCode project (ServiceNow + Hugging Face), Nov 2022 (arXiv:2211.15533, v1 20 Nov 2022); ablation models are 350M-parameter decoder-only transformers trained on Python subsets (near-dup vs not).
- **Source**: Kocetkov, Li, Ben Allal, Li, Mou, Muñoz Ferrandis, Jernite, Mitchell, Hughes, Wolf, Bahdanau, von Werra, de Vries (ServiceNow Research / Hugging Face), "The Stack: 3 TB of permissively licensed source code," 2022, arXiv:2211.15533
- **Quality tier**: primary
- **Quote (near-dedup method)**: "We first split the files into words/tokens based on non-alphanumeric characters and remove files with fewer than 10 tokens. Next, we compute the MinHash... with 256 permutations of all documents, and use Locality Sensitive Hashing... to find clusters of duplicates. We further reduce these clusters by ensuring that each file in the original cluster is similar to at least one other file in the reduced cluster. We consider two files similar when their Jaccard similarity exceeds 0.85. We find that in the permissive license dataset, 38.6% of the files are just near-duplicates of other files and are removed, they also represent 53.7% of the volume of the dataset."
- **Quote (headline finding)**: "We train 350M decoder-only transformers on several python subsets of the data and find that removing near-duplicates significantly boosts performance in all experiments. We show it is possible to reproduce text2code performance of Codex and CodeGen by only using permissively licensed data."
- **Confidence**: high
- **Local path**: download/the-stack-2022.pdf

### DeepSeek-Coder — repo-level (not file-level) near-dedup, quality screening, benchmark decontamination
- **Claim**: DeepSeek-Coder performs near-deduplication at the WHOLE-REPOSITORY level (concatenating all files of a repo into one unit before applying the same near-dedup algorithm), arguing file-level dedup (as used in prior work) can "disrupt the structure of the repository" by removing some files but not others from a coherent project; it also applies a compiler + quality model + heuristic rules on top of the StarCoder-style basic filters, and decontaminates against HumanEval/MBPP/GSM8K/MATH via exact 10-gram (or exact match for shorter strings) filtering.
- **Numbers**: raw GitHub crawl (repos created before Feb 2023, 87 languages) reduced to 32.8% of original size by basic StarCoder-style filters (line-length >100 avg or >1000 max removed; <25% alphabetic-char files removed; language-specific XML/HTML/JSON/YAML rules); final Table 1 cleaned corpus: 798GB total / 603M files across 87 languages (e.g. Java 148.66GB/134.4M files, C++ 90.87GB/36.0M, Python 120.68GB/75.2M, PHP 58.92GB/40.6M, C# 58.56GB/53.7M); training mixture 87% source code / 10% English code-related NL (GitHub Markdown + StackExchange) / 3% Chinese NL.
- **Conditions**: DeepSeek-Coder 1.3B/6.7B/33B, 2 trillion total training tokens; Jan 2024.
- **Source**: Guo et al. (DeepSeek-AI), "DeepSeek-Coder," 2024, arXiv:2401.14196
- **Quality tier**: primary
- **Quote**: "We perform deduplication at the repository level of code, rather than at the file level, as the latter approach may filter out certain files within a repository, potentially disrupting the structure of the repository. Specifically, we treat the concatenated code from the repository level as a single sample and apply the same near-deduplication algorithm to ensure the integrity of the repository structure."
- **Quote (decontamination)**: "we've implemented an n-gram filtering process. This process involves the removal of any code segments that match specific criteria... if a piece of code includes a 10-gram string identical to any in the test data, it is excluded from our training data. In cases where the test data comprises strings that are shorter than 10-grams but no less than 3-grams, we use an exact match approach for filtering."
- **Confidence**: high
- **Local path**: download/deepseek-coder-2024.pdf

### StarCoder2 / The Stack v2 — permissive-license policy + governance (SWH-scale)
- **Claim**: StarCoder2's Stack v2 (built on the Software Heritage archive) uses a stricter, file-level license-detection pipeline (ScanCode Toolkit + regex license-file discovery + propagation to same-path files) than v1, classifies files into permissive / non-permissive(copyleft) / unlicensed, and — departing from v1 — INCLUDES both permissively-licensed AND unlicensed files (still excluding copyleft and commercial-restricted licenses), reasoning that unlicensed code is legally closer to "all rights reserved" than to permissive but is nonetheless included after a policy decision (full rationale not captured in the pages read — GAP).
- **Numbers**: SWH graph dataset snapshot 2023-09-06; repo-level license available from GHArchive for only 3.07% of repos (i.e. license not available for 96.93%, requiring the ScanCode fallback); language detection identifies 658 unique languages, reduced to 619 after a manual visual-inspection sprint (BigCode community, 15 annotators, ~1000 extensions inspected, 130 excluded); Table 1 comparison: The-Stack-v1-dedup 875.85GB/181.00M files vs The-Stack-v2-dedup 6,457.14GB/784.30M files vs the-stack-v2-swh-full (post additional filtering) 1,922.82GB/528.44M files, across the 32 languages tabulated.
- **Conditions**: BigCode project, Feb 2024.
- **Source**: Lozhkov et al. (BigCode), "StarCoder 2 and The Stack v2," 2024, arXiv:2402.19173
- **Quality tier**: primary
- **Quote (license policy change from v1)**: "We consider three types of files: permissively licensed, non-permissively licensed (e.g., copyleft), and unlicensed files. The main difference between the Stack v2 and the Stack v1 is that we include both permissively licensed and unlicensed files. We exclude commercial licenses since their creators do not intend their code to be used for commercial purposes. We also exclude copyleft-licensed code due to uncertainty regarding the community's stance on using such data for LLM training and its relatively low volume."
- **Confidence**: high
- **Local path**: download/starcoder2-2024.pdf

### phi-1 — synthetic "textbook + exercises" data, quality filtering via LLM-annotated classifier
- **Claim**: phi-1 (1.3B params) attains 50.6% HumanEval pass@1 and 55.5% MBPP pass@1 — competitive with much larger models — using an aggressively small, curated pretraining set (<7B tokens total: ~6B "filtered code-language" tokens + <1B synthetically-generated "textbook" tokens) plus a 180M-token synthetic "CodeExercises" finetuning set, arguing standard large code corpora (The Stack, StackOverflow) are not "textbook quality" (self-contained, instructive, balanced) and that curating for those properties changes the shape of the scaling curve rather than only shifting it.
- **Numbers**: filtering pipeline: GPT-4 annotates ~100k samples from The Stack (deduplicated Python subset) + StackOverflow (>35M files/samples, >35B tokens total) for "educational value... for a student whose goal is to learn basic coding concepts"; those annotations train a random-forest classifier (features = output embedding from a pretrained codegen model) that scores/filters the full corpus down to the ~6B-token "filtered code-language" dataset; synthetic textbook dataset <1B tokens (GPT-3.5-generated); synthetic exercises ("CodeExercises") ~180M tokens; ablation: 350M model trained on UNFILTERED deduped-Stack+StackOverflow saturates at 12.19% HumanEval even after 96k steps (~200B tokens / ~28 epochs over the ~7B set implied); the FILTERED subset alone reaches 17.68% HumanEval after only 36k steps; filtered + synthetic textbook (="CodeTextbook") reaches 20.12% (this is phi-1-base at 350M); phi-1-base at 1.3B (trained on CodeTextbook, 51 GPU-days) reaches 29%; phi-1 (=phi-1-base finetuned on the 180M-token CodeExercises) reaches the reported 50.6%; phi-1-small (350M, same pipeline) reaches 45% HumanEval.
- **Conditions**: phi-1: 1.3B params, trained ~4 days on 8 A100s; Transformer decoder. Oct 2023 (arXiv v2, orig. Jun 2023).
- **Source**: Gunasekar, Zhang, Aneja, Mendes, Del Giorno, Gopi, Javaheripi, Kauffmann, de Rosa, Saarikivi, Salim, Shah, Behl, Wang, Bubeck, Eldan, Kalai, Lee, Li (Microsoft Research), "Textbooks Are All You Need," 2023, arXiv:2306.11644
- **Quality tier**: primary
- **Quote (thesis)**: "We introduce phi-1, a new large language model for code... Despite this small scale, phi-1 attains pass@1 accuracy 50.6% on HumanEval and 55.5% on MBPP." / "in fact the effect of high quality data extends well past [smaller datasets or more passes]: improving data quality can dramatically change the shape of the scaling laws, potentially allowing to match the performance of large-scale models with much leaner training/models."
- **Quote (data drawbacks motivating curation)**: listed drawbacks of standard code datasets: samples "not self-contained," "do not involve any meaningful computation," algorithmic logic "buried inside complex or poorly documented functions," and topic distribution "skewed... resulting in an unbalanced distribution of coding concepts and skills."
- **Quote (filtering ablation numbers)**: "for 350M parameter models trained on unfiltered Stack (deduplicated python) and StackOverflow, the HumanEval performance saturates at 12.19% even after training for 96k steps (∼200B tokens), while training on the filtered subset achieves 17.68% on HumanEval after 36k steps. We further improve this to 20.12%... by training on a combination of the filtered dataset and the synthetic textbooks dataset."
- **Confidence**: high
- **Local path**: download/phi1-2023.pdf

### SemDeDup — semantic deduplication technique (correction: NOT demonstrated on code in the paper)
- **Claim**: SemDeDup uses embeddings from a pretrained foundation model (CLIP for images, OPT for language) plus k-means clustering (to make the O(n²) pairwise-similarity problem tractable at web scale) to find and remove "semantic duplicates" — pairs that are semantically near-identical but not exact/near-surface duplicates, which exact/n-gram/MinHash dedup cannot catch — and shows removing 50% of LAION-440M this way costs almost no accuracy while roughly halving training time, and gives a 15% efficiency gain on C4 (text) with sometimes-improved performance.
- **Numbers**: LAION-440M: 50% removable with "minimal performance loss," 2x training-speed improvement to reach the same zero-shot ImageNet top-1 accuracy; C4: "beating prior SoTA deduplication while providing efficiency gains of 15%, sometimes even improving performance"; clustering complexity reduction from O(n²) ≈ 1.9×10^17 pairwise comparisons (naive, for LAION-440M) to O(n²/k) ≈ 4.6×10^12 with k=50,000 clusters (CLIP embeddings) or k=11,000 clusters (OPT/language embeddings) — a claimed 5-order-of-magnitude reduction.
- **Conditions**: image experiments use CLIP embeddings on LAION; language experiments use OPT embeddings on C4 (a general web-text corpus, NOT a code corpus). Mar 2023 (arXiv:2303.09540).
- **Source**: Abbas, Tirumala, Simig, Ganguli, Morcos (Meta AI FAIR / Stanford), "SemDeDup: Data-efficient learning at web-scale through semantic deduplication," 2023, arXiv:2303.09540
- **Quality tier**: primary
- **Quote**: "we apply SemDeDup to C4, a large text corpus, beating prior SoTA deduplication while providing efficiency gains of 15%, sometimes even improving performance."
- **Confidence**: high (mechanism and LAION/C4 numbers); **CORRECTION FLAGGED** — the brief's phrasing implied SemDeDup was demonstrated on code; the paper (pages 1-4 read; abstract, intro, method, LAION results) evaluates only LAION (image/text) and C4 (general text), never a code corpus. I did not find a code-specific SemDeDup application in this pass. If a code-pretraining paper (e.g. a DeepSeek-Coder-V2 or Qwen2.5-Coder ablation) claims to USE SemDeDup, that claim needs its own citation — GAP: not checked in the pages read from deepseek-coder-v2 or qwen25-coder (their dedup sections were not the pages fetched in this session for V2; qwen25-coder's dedup approach was not detailed beyond "weak model based classifiers" for text-code grounding data, no semantic-embedding dedup mentioned in pages 1-10).
- **Local path**: download/semdedup-2023.pdf

### Decontamination — cross-model comparison (from Q2/Q3 sources)
- **Claim**: All three modern code-pretraining papers read in this session (DeepSeek-Coder, Qwen2.5-Coder) use essentially the SAME decontamination recipe: n-gram (specifically 10-gram) overlap filtering of training data against benchmark test sets (HumanEval, MBPP, GSM8K, MATH), with an exact-match fallback for shorter strings. StarCoder2's decontamination approach was not captured in the pages read this session (GAP).
- **Numbers**: DeepSeek-Coder: 10-gram identical match => excluded; 3–9-gram test strings => exact match filtering. Qwen2.5-Coder: "10-gram overlap method, where any training data with a 10-gram word-level overlap with the test data was removed," applied to BOTH pretraining and post-training (SFT/DPO) data, against HumanEval, MBPP, GSM8K, MATH.
- **Conditions**: n/a (methodology description).
- **Source**: Guo et al., "DeepSeek-Coder," arXiv:2401.14196; Hui et al., "Qwen2.5-Coder Technical Report," arXiv:2409.12186
- **Quality tier**: primary
- **Quote (Qwen2.5-Coder)**: "To ensure that Qwen2.5-Coder does not produce inflated results due to test set leakage, we performed decontamination on all data, including both pre-training and post-training datasets. We removed key datasets such as HumanEval, MBPP, GSM8K, and MATH. The filtering was done using a 10-gram overlap method, where any training data with a 10-gram word-level overlap with the test data was removed."
- **Confidence**: high
- **Local path**: download/deepseek-coder-2024.pdf, download/qwen25-coder-2024.pdf

## Q4. Scaling for code specifically

> **COVERAGE GAP — restart-intensity ceiling reached.** This question was assigned to two
> successive agents; both hit the per-agent step cap before reaching it (original run died
> after Q2, trimmed retry died after Q3). Per `config/operational-scale.json`
> `safety_net_invariants`, respawning stops here and the subtopic is marked rather than
> retried a third time. The session WebSearch pool was also near exhaustion, so a
> main-thread web pass was not available either.
>
> **What IS answered, from evidence collected in other questions of this cluster:**
>
> - *(b) code fraction in the mix* — Qwen2.5-Coder's final pretraining mixture is
>   **70% code : 20% text : 10% math**, and the report states this was chosen
>   empirically against 100:0:0 and 85:10:5 alternatives (C4 Q2, primary,
>   `download/qwen25-coder-2024.pdf`). DeepSeek-Coder uses **87% code / 10% English
>   code-related NL / 3% Chinese NL** (C4 Q2/Q3, primary).
> - *(a) different scaling behaviour* — two concrete data points rather than a code
>   scaling law: StarCoder2 states it deliberately trains "far beyond the compute-optimal
>   number suggested by Chinchilla," i.e. code practice knowingly departs from the
>   compute-optimal frontier in favour of inference-cheap small models (C4 Q2, primary);
>   and phi-1 claims data quality "can dramatically change the SHAPE of the scaling laws,"
>   which is a claim about the curve, not a point on it (C4 Q3, primary).
>
> **What is NOT answered and must not be asserted:** whether code has a genuinely
> *different* compute-optimal token-to-parameter ratio than natural language — no fitted
> code scaling law was located in this pass.
>
> **(c) The folklore check is UNRESOLVED and this matters.** The claim "training on code
> improves general reasoning" is very widely repeated. No source opened in this cluster
> *measures* it. The Qwen2.5-Coder mixture ablation is the closest thing found, and it
> measures the effect of the mixture on **code and math benchmark performance**, not a
> transfer effect from code to general reasoning. Treat the claim as **unverified in the
> acquired corpus** — the survey must say so explicitly rather than repeat it, and must not
> resolve it in favour of the popular answer. Tracked for a dedicated acquisition pass.

## Gaps

- Q4(a): no fitted code-specific scaling law located. Q4(c): the code-improves-reasoning
  claim is unverified in the acquired corpus (see the coverage-gap block above).
- StarCoder2's decontamination method was not captured in the pages read (Q3).
- SemDeDup has **no** demonstrated code application in its own paper (see corrections).

## Corrections to the brief

- **The brief implied SemDeDup was demonstrated on code. It was not.** The paper evaluates
  LAION (image/text) and C4 (general web text) only; no code corpus appears in it. Any
  claim that a code-pretraining pipeline uses semantic dedup needs its own separate
  citation. This correction was produced by the agent overriding the brief, as instructed.

## Sources worth acquiring

- A fitted code-specific scaling law, if one exists, for Q4(a).
- A primary source that *measures* code-to-reasoning transfer, for Q4(c) — the highest
  value acquisition in this cluster, because the claim is currently folklore in this corpus.
