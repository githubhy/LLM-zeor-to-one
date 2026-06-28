# Evidence Ledger E2 — Quantitative SOTA (Open-Weight Multimodal Models)
<!-- created 2026-06-28; cluster E2; questions 1-2 (RETRY-TRIMMED) -->

---
## Q1 — Qwen2.5-VL and Qwen2-VL benchmark scores

### Qwen2.5-VL-72B core benchmark scores
- **value/result**: MMMU(val)=70.2 | MathVista(testmini)=74.8 | MMBench-EN(test)=88.6 | MMBench-V1.1-EN(test)=88.4 | DocVQA(test)=96.4 | ChartQA(test avg)=89.5 | AI2D=88.7
- **condition**: Qwen2.5-VL 72B; Table 3 (general) + Table 5 (OCR/doc); standard val/test splits
- **source**: Bai et al. "Qwen2.5-VL Technical Report" 2025, arXiv:2502.13923 (local: download/bai-qwen2.5-vl-2025.pdf pp.10-12) · **tier**: A · **confidence**: high

### Qwen2.5-VL-7B core benchmark scores
- **value/result**: MMMU(val)=58.6 | MathVista(testmini)=68.2 | MMBench-EN(test)=83.5 | DocVQA(test)=95.7 | ChartQA(test avg)=87.3 | AI2D=83.9
- **condition**: Qwen2.5-VL 7B; Table 3 + Table 5
- **source**: Bai et al. 2025, arXiv:2502.13923 (local: download/bai-qwen2.5-vl-2025.pdf pp.10-12) · **tier**: A · **confidence**: high

### Qwen2.5-VL-3B core benchmark scores
- **value/result**: MMMU(val)=53.1 | MathVista(testmini)=62.3 | MMBench-EN(test)=79.1 | DocVQA(test)=93.9 | ChartQA(test avg)=84.0
- **condition**: Qwen2.5-VL 3B; Table 3 + Table 5
- **source**: Bai et al. 2025, arXiv:2502.13923 (local: download/bai-qwen2.5-vl-2025.pdf pp.10-12) · **tier**: A · **confidence**: high

### Qwen2-VL-72B core benchmark scores
- **value/result**: MMMU(val)=64.5 | MathVista(testmini)=70.5 | MMBench-EN(test)=86.5 | MMBench-CN(test)=86.6 | DocVQA(test)=96.5 | ChartQA(test)=88.3 | AI2D=88.1
- **condition**: Qwen2-VL 72B; Table 2; standard val/test splits
- **source**: Wang et al. "Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution" 2024, arXiv:2409.12191 (local: download/wang-qwen2-vl-2024.pdf p.8) · **tier**: A · **confidence**: high

### Qwen2-VL-7B core benchmark scores
- **value/result**: MMMU(val)=54.1 | MathVista(testmini)=58.2 | MMBench-EN(test)=83.0 | DocVQA(test)=94.5 | ChartQA(test)=83.0 | AI2D=83.0
- **condition**: Qwen2-VL 7B; Table 2
- **source**: Wang et al. 2024, arXiv:2409.12191 (local: download/wang-qwen2-vl-2024.pdf p.8) · **tier**: A · **confidence**: high

### Qwen2-VL-2B core benchmark scores
- **value/result**: MMMU(val)=41.1 | MathVista(testmini)=43.0 | MMBench-EN(test)=74.9 | DocVQA(test)=90.1 | ChartQA(test)=73.5 | AI2D=74.7
- **condition**: Qwen2-VL 2B; Table 2
- **source**: Wang et al. 2024, arXiv:2409.12191 (local: download/wang-qwen2-vl-2024.pdf p.8) · **tier**: A · **confidence**: high

### Qwen2.5-VL SOTA claims
- **value/result**: Qwen2.5-VL-72B claims SOTA on MMMU(val)=70.2 (first open-source to match GPT-4o-0513's 69.1 on this benchmark); SOTA on DocVQA(test)=96.4 surpassing InternVL2.5-78B(95.1) and Qwen2-VL-72B(96.5); SOTA on MathVista(testmini)=74.8 surpassing InternVL2.5-78B(72.3) and Qwen2-VL-72B(70.5)
- **condition**: Qwen2.5-VL 72B vs open-source competitors; Table 3 claims per paper
- **source**: Bai et al. 2025, arXiv:2502.13923 (local: download/bai-qwen2.5-vl-2025.pdf pp.10-13) · **tier**: A · **confidence**: high


---
## Q2 — InternVL (v2/v2.5), Molmo, Pixtral-12B benchmark scores

### InternVL2.5-78B core benchmark scores
- **value/result**: MMMU(val)=70.1 (w/ CoT) | MathVista(testmini)=72.3 | MMBench-EN(test)=88.3 | DocVQA(test)=95.1 | ChartQA(test avg)=88.3 | AI2D=89.1
- **condition**: InternVL2.5 78B; comparison data from Qwen2.5-VL paper Table 3 + Table 5; matches arXiv:2412.05271 reported values confirmed via web search
- **source**: Chen et al. "Expanding Performance Boundaries of Open-Source Multimodal Models with Model, Data, and Test-Time Scaling" 2024, arXiv:2412.05271; values cross-confirmed in Bai et al. 2025 (local: download/bai-qwen2.5-vl-2025.pdf pp.10-12) · **tier**: A · **confidence**: high

### InternVL2-8B core benchmark scores (from Molmo comparison table)
- **value/result**: MMMU(val)=51.2 | MathVista(testmini)=58.3 | AI2D(test)=83.8 | ChartQA(test)=83.3 | DocVQA(test)=91.6 | InfoQA(test)=74.8
- **condition**: InternVL2-8B; Table 1 from Molmo paper (open-weights category)
- **source**: Deitke et al. "Molmo and PixMo: Open Weights and Open Data for State-of-the-Art Multimodal Models" 2024, arXiv:2409.17146 (local: download/deitke-molmo-2024.pdf p.5) · **tier**: A · **confidence**: high

### InternVL2-Llama3-76B core benchmark scores (from Molmo comparison table)
- **value/result**: MMMU(val)=58.2 | MathVista(testmini)=65.5 | AI2D(test)=87.6 | ChartQA(test)=88.4 | DocVQA(test)=94.1 | InfoQA(test)=82.0
- **condition**: InternVL2-Llama3-76B; Table 1 from Molmo paper (open-weights category)
- **source**: Deitke et al. 2024, arXiv:2409.17146 (local: download/deitke-molmo-2024.pdf p.5) · **tier**: A · **confidence**: high

### Molmo-72B core benchmark scores
- **value/result**: MMMU(val)=54.1 | MathVista(testmini)=58.6 | AI2D(test)=96.3 | ChartQA(test)=87.3 | DocVQA(test)=93.5 | InfoQA(test)=81.9 | Elo=1077 (rank 2 of 28 models)
- **condition**: Molmo-72B; Table 1; Elo rank based on 15k human pairwise evaluations (~870 annotators, >325k ratings)
- **source**: Deitke et al. 2024, arXiv:2409.17146 (local: download/deitke-molmo-2024.pdf p.5) · **tier**: A · **confidence**: high

### Molmo-7B-D core benchmark scores
- **value/result**: MMMU(val)=45.3 | MathVista(testmini)=51.6 | AI2D(test)=93.2 | ChartQA(test)=84.1 | DocVQA(test)=92.2 | Elo=1056 (rank 6 of 28)
- **condition**: Molmo-7B-D; Table 1
- **source**: Deitke et al. 2024, arXiv:2409.17146 (local: download/deitke-molmo-2024.pdf p.5) · **tier**: A · **confidence**: high

### Molmo-7B-O core benchmark scores
- **value/result**: MMMU(val)=39.3 | MathVista(testmini)=44.5 | AI2D(test)=90.7 | ChartQA(test)=80.4 | DocVQA(test)=90.8 | Elo=1051 (rank 9 of 28)
- **condition**: Molmo-7B-O; Table 1; NOTE: Molmo's MMMU scores are notably lower than Qwen2-VL-7B (54.1) despite similar Elo — paper notes benchmark eval can vary ~10% on protocol
- **source**: Deitke et al. 2024, arXiv:2409.17146 (local: download/deitke-molmo-2024.pdf p.5) · **tier**: A · **confidence**: high

### Pixtral-12B core benchmark scores (Pixtral own evaluation protocol)
- **value/result**: MMMU(val)=52.0 (CoT) | MathVista(testmini)=58.3 (CoT) | ChartQA(test)=81.8 (CoT) | DocVQA(test)=90.7 (ANLS) | LMSys-Vision Elo=1076
- **condition**: Pixtral-12B; Table 2 from Pixtral paper; evaluated with "Explicit" prompts (different protocol than typical; standard-protocol scores from Molmo Table 1 are MMMU=52.5, DocVQA=90.7, ChartQA=81.8, AI2D=79.0, MathVista=58.0 — consistent)
- **source**: Agrawal et al. "Pixtral 12B" 2024, arXiv:2410.07073 (local: download/agrawal-pixtral-2024.pdf p.5) · **tier**: A · **confidence**: high

### Pixtral-12B SOTA claim vs. same-scale open models
- **value/result**: Pixtral-12B claims best open-source performance at ~12B scale on MM-MT-Bench (6.05 vs Qwen2-VL-7B 5.45, Llama-3.2-11B 4.79) and highest-ranked Apache 2.0 model on LMSys Vision leaderboard (Oct 2024 Elo=1076). On standard benchmarks MMMU and MathVista Pixtral-12B (52.0, 58.3) matches Qwen2-VL-7B at comparable scale.
- **condition**: Pixtral 12B; Oct 2024 LMSys snapshot; multi-turn instruction-following focus
- **source**: Agrawal et al. 2024, arXiv:2410.07073 (local: download/agrawal-pixtral-2024.pdf pp.1,5) · **tier**: A · **confidence**: high

