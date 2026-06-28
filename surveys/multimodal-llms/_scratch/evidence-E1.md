# Evidence Ledger — Cluster E1: Benchmark & Evaluation Landscape
<!-- generated 2026-06-28 -->

---

## Q1 — MMMU: What it measures, disciplines, split sizes, metric, human-vs-model gap

### MMMU benchmark overview
- **value/result**: Measures multimodal understanding and reasoning across college-level, expert-required tasks. 11,550 questions; 6 disciplines (Art & Design 11%, Business 14%, Science 23%, Health & Medicine 17%, Humanities & Social Science 9%, Tech & Engineering 26%); 30 subjects; 183 subfields; 30 heterogeneous image types (diagrams, tables, charts, chemical structures, music sheets, medical images, etc.). Questions are ~94% multiple-choice, ~6% open-ended. Interleaved text-image inputs supported.
- **condition**: Dev/Validation/Test split = 150 / 900 / 10,500. Difficulty: Easy 28%, Medium 45%, Hard 27%.
- **source**: Yue et al., "MMMU: A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark for Expert AGI," 2023. arXiv:2311.16502v4 (local: download/yue-mmmu-2023.pdf, Table 1, p.4) · **tier**: A · **confidence**: high

### MMMU evaluation metric
- **value/result**: Micro-averaged accuracy. Rule-based answer extraction (regular expressions to extract key phrases from model responses); random selection as fallback for unanswerable multiple-choice.
- **condition**: Zero-shot evaluation; few-shot results in appendix.
- **source**: Yue et al. 2023, arXiv:2311.16502v4, §4 Experiments, p.5 · **tier**: A · **confidence**: high

### MMMU human-vs-model gap
- **value/result**: Human expert performance on validation set: worst 76.2%, median 82.6%, best 88.6%. Best open-source model at time of submission (BLIP-2 FLAN-T5-XXL): 34.0% test. GPT-4V: 56.8% validation / 55.7% test. GPT-4o*: 69.1% validation. Gemini 1.5 Pro*: 62.2% validation. The human best (88.6%) substantially exceeds all models. The human–GPT-4o gap is ~19.5 percentage points on validation.
- **condition**: Validation set (900 Qs) for human experts; 90 college senior students (3 per subject); textbooks allowed, no internet.
- **source**: Yue et al. 2023, arXiv:2311.16502v4, Table 2 and §4.2, pp. 5–6 · **tier**: A · **confidence**: high

### MMMU error analysis (GPT-4V)
- **value/result**: On 150 randomly sampled GPT-4V errors: Perceptual errors 35%, Lack of knowledge 29%, Reasoning errors 26%, Textual understanding 4%, Reject-to-answer 3%, Annotation error 2%, Answer extraction 1%.
- **condition**: 150 annotated GPT-4V error cases on MMMU; expert annotators assigned root causes.
- **source**: Yue et al. 2023, arXiv:2311.16502v4, §5 and Figure 5, p.8 · **tier**: A · **confidence**: high

---

## Q2 — POPE: object-hallucination probing method, metric, and findings

### POPE method overview
- **value/result**: Polling-based Object Probing Evaluation (POPE). Converts object-hallucination evaluation into a binary Yes/No classification task. Each question is "Is there a/an <object> in the image?" with ground-truth:negative ratio 1:1. Three negative sampling strategies: (1) Random — randomly sample objects absent from image; (2) Popular — top-k most frequent COCO objects absent from image; (3) Adversarial — top-k objects most frequently co-occurring with ground-truth objects in image but absent from it. Evaluated on 500 images (≥3 annotated objects each) from MSCOCO validation; 6 questions per image (l=6).
- **condition**: MSCOCO validation set, 500 images, 3,000 total questions per setting.
- **source**: Li et al., "Evaluating Object Hallucination in Large Vision-Language Models," arXiv:2305.10355v3, §5 and Figure 3 (local: download/li-pope-2023.pdf, pp. 6–7) · **tier**: A · **confidence**: high

### POPE metrics
- **value/result**: Accuracy, Precision, Recall, and F1 score. F1 is the primary metric. Also reports "Yes (%)" — the proportion of "Yes" responses — as a bias indicator.
- **condition**: Binary classification; balanced Yes/No label design.
- **source**: Li et al. 2023, arXiv:2305.10355v3, §5.1, p.7 · **tier**: A · **confidence**: high

### POPE findings — severity and patterns
- **value/result**: Most instruction-tuned LVLMs severely hallucinate even more than small VLPMs (e.g., LLaVA CHAIRS=32.7 vs. OSCARBase CHAIRS=13.0). Under POPE: LLaVA, MultiModal-GPT, mPLUG-Owl answer "Yes" ~99% of the time (extreme positive bias, F1 < 70 on all settings). InstructBLIP is least affected (F1=89.3 random, 83.5 popular, 78.5 adversarial). Performance consistently drops from Random → Popular → Adversarial settings, confirming LVLMs hallucinate frequently-appearing and co-occurring objects. Approximately 50% of hallucinated objects belong to the top-10 most frequent COCO objects (HRA@10 ≈ 0.45–0.55).
- **condition**: POPE on MSCOCO validation (500 images); also CHAIR metric on MSCOCO captions for comparison baseline.
- **source**: Li et al. 2023, arXiv:2305.10355v3, Tables 1 & 3, §3.2, §4.3, §5.2 (pp. 3–7) · **tier**: A · **confidence**: high


---

## Q3 — Per-benchmark one-liner: what it measures, metric, test-set size

### MMBench benchmark
- **value/result**: Evaluates 20 fine-grained visual-language ability dimensions (perception, cognition, etc.) via 3,217 multiple-choice questions. Uses a CircularEval strategy (each question appears in multiple circular permutations of options) plus GPT-4 for answer matching to handle limited instruction-following. Metric: accuracy.
- **condition**: ~3,217 questions; bilingual (English + Chinese versions available).
- **source**: Liu et al., "MMBench: Is Your Multi-modal Model an All-Around Player?" arXiv:2307.06281, 2023. ECCV 2024. · **tier**: A · **confidence**: high

### MME benchmark
- **value/result**: Comprehensive perception + cognition evaluation across 14 subtasks (existence, count, position, color, posters, celebrity, scene, landmark, artwork, OCR, commonsense reasoning, numerical calculation, text translation, code reasoning). Each subtask scored out of 200; total score summed across subtasks. Annotations are manually designed to avoid data leakage from public datasets. Metric: per-subtask total score (max 200 per subtask).
- **condition**: 14 subtasks; first systematic evaluation of MLLMs; 12 models evaluated in original paper.
- **source**: Fu et al., "MME: A Comprehensive Evaluation Benchmark for Multimodal Large Language Models," arXiv:2306.13394, 2023. · **tier**: A · **confidence**: high

### MMStar benchmark
- **value/result**: 1,500 human-selected, vision-indispensable challenge samples covering 6 core capabilities and 18 detailed axes. Eliminates text-solvable and leaked samples. Introduces Multi-modal Gain (MG) and Multi-modal Leakage (ML) metrics alongside accuracy to measure how much performance depends on genuine visual understanding vs. memorization.
- **condition**: 1,500 test samples; NeurIPS 2024.
- **source**: Chen et al., "Are We on the Right Way for Evaluating Large Vision-Language Models?" arXiv:2403.20330, NeurIPS 2024. · **tier**: A · **confidence**: high

### DocVQA benchmark
- **value/result**: Visual Question Answering on document images (invoices, forms, tables, figures within documents). ~50,000 questions on 12,000+ document images. Metric: ANLS (Average Normalized Levenshtein Similarity), capturing near-exact OCR-level matches.
- **condition**: ~50K questions / ~12K document images; test set held out for leaderboard.
- **source**: Mathew et al., "DocVQA: A Dataset for VQA on Document Images," arXiv:2007.00398, WACV 2021. · **tier**: A · **confidence**: high

### ChartQA benchmark
- **value/result**: Chart understanding and visual-logical reasoning over real-world charts. 9,608 human-written + 23,111 automatically generated questions across different chart types (bar, line, pie, etc.). Metric: relaxed accuracy (exact match with ±5% tolerance for numerical answers).
- **condition**: ~32,719 total QA pairs; split into human and augmented sets evaluated separately.
- **source**: Masry et al., "ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning," arXiv:2203.10244, ACL Findings 2022. · **tier**: A · **confidence**: high

### TextVQA benchmark
- **value/result**: OCR-grounded VQA requiring reading and reasoning about text in natural images (signs, labels, menus). 45,336 questions on 28,408 images; test set = 5,734 questions. Metric: accuracy (and ANLS).
- **condition**: Test set 5,734 questions; evaluated under open-vocabulary setting with 10 annotator answers.
- **source**: Singh et al., "Towards VQA Models That Can Read," arXiv:1904.08920, CVPR 2019. · **tier**: A · **confidence**: high

### AI2D benchmark
- **value/result**: Grade-school science diagram understanding and question answering. Over 5,000 diagrams annotated with 150,000+ structured labels; ~15,000 multiple-choice questions; standard MLLM eval subset = 3,088 QA pairs. Metric: multiple-choice accuracy.
- **condition**: 3,088-question eval subset commonly used in MLLM leaderboards; original dataset 15K+ questions.
- **source**: Kembhavi et al., "A Diagram Is Worth a Dozen Images," ECCV 2016; widely cited test split = 3,088 pairs. · **tier**: B · **confidence**: med

### MathVista benchmark
- **value/result**: Mathematical reasoning in visual contexts (figures, geometry, charts, tables, equations). 6,141 problems from 28 existing multimodal math datasets + 3 new collections (IQTest, FunctionQA, PaperQA), covering Figure QA, Geometry Problem Solving, Math Word Problems, Textbook QA, and VQA types. Metric: accuracy (per task-type sub-scores reported).
- **condition**: 6,141 total; 1,000-sample minitest widely used; evaluated zero-shot.
- **source**: Lu et al., "MathVista: Evaluating Mathematical Reasoning of Foundation Models in Visual Contexts," arXiv:2310.02255, ICLR 2024. · **tier**: A · **confidence**: high

### RealWorldQA benchmark
- **value/result**: Real-world spatial understanding; 765 images (vehicles and everyday scenarios) with questions about spatial relationships, requiring correct understanding of physical scenes. Released by xAI with Grok-1.5V. Metric: accuracy (multiple-choice).
- **condition**: 765 questions; multiple-choice with step-by-step reasoning prompting; no formal train split.
- **source**: xAI / Grok-1.5 Vision release, April 2024. https://x.ai/blog/grok-1.5v · **tier**: B · **confidence**: med

---

## Q4 — Main MLLM evaluation pitfalls

### Pitfall: benchmark contamination / data leakage
- **value/result**: Many MLLM benchmark samples are answerable without vision — e.g., GeminiPro achieves 42.9% on MMMU without any visual input; Sphinx-X-MoE achieves 43.6% on MMMU without images (surpassing its own LLM backbone by 17.9%). Broader contamination rates: image-only contamination up to 84.46% and image-text contamination up to 33.13% measured via CLIPScore across common pretraining datasets.
- **condition**: Measured on MMMU and other benchmarks; contamination estimated with CLIPScore image similarity to pretraining corpora.
- **source**: (a) Chen et al. "Are We on the Right Way for Evaluating Large Vision-Language Models?" arXiv:2403.20330, NeurIPS 2024 (vision-indispensable finding). (b) "Clean Evaluations on Contaminated Visual Language Models," arXiv:2410.07030, 2024 (contamination rates). · **tier**: A · **confidence**: high

### Pitfall: single-image / text-only-solvable bias (vision-indispensable gap)
- **value/result**: Many benchmark questions can be solved from question text + world knowledge alone, without looking at the image. MMStar explicitly addresses this by requiring all 1,500 samples to be "vision-indispensable." The gap between text-only LLM performance and full MLLM performance on such benchmarks is inflated by this bias.
- **condition**: Systematic finding in MMStar; affects MMBench, MMMU, SeedBench, and others.
- **source**: Chen et al. "Are We on the Right Way for Evaluating Large Vision-Language Models?" arXiv:2403.20330, NeurIPS 2024 · **tier**: A · **confidence**: high

### Pitfall: prompt sensitivity
- **value/result**: MLLM performance varies significantly with minor prompt changes. Models are vulnerable to deceptive or misleading prompt framings and generate erroneous responses. Benchmarks designed to test robustness (MMR, MAD-Bench) specifically probe this. Phrasing variations in evaluation questions can cause large, unpredictable scoring swings across models.
- **condition**: Documented in multiple 2024 evaluation surveys and adversarial evaluation benchmarks (MAD-Bench, MMR).
- **source**: "A Survey on Evaluation of Multimodal Large Language Models," arXiv:2408.15769, 2024 (secondary survey); "Promptception: How Sensitive Are Large Multimodal Models to Prompts?" arXiv:2509.03986, 2025 · **tier**: B · **confidence**: med

### Pitfall: LLM-judge bias in open-ended MLLM evaluation
- **value/result**: LLM/MLLM evaluators used as judges exhibit position bias (favoring first-listed answer), verbosity bias (preferring longer answers), self-enhancement bias (favoring outputs from the same model family), and stochastic variability. "MLLM-as-a-Judge" benchmark found significant divergence from human preferences in Scoring Evaluation and Batch Ranking tasks even for GPT-4V. LLM judges consistently miss logic errors caught by human experts.
- **condition**: Systematic analysis in MLLM-as-a-Judge benchmark (mllm-judge.github.io); also "A Survey on LLM-as-a-Judge," arXiv:2411.15594, 2024.
- **source**: (a) MLLM-as-a-Judge benchmark, https://mllm-judge.github.io/ · **tier**: B · **confidence**: high; (b) "A Survey on LLM-as-a-Judge," arXiv:2411.15594, 2024 · **tier**: B · **confidence**: high

