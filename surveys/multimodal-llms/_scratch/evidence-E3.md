# Evidence Ledger E3 — Quantitative SOTA: Closed Frontier + Deployment Gap
<!-- cluster: E3 | date: 2026-06-28 | collector: evidence-agent -->

---
## Q1 — GPT-4o and GPT-4V: MMMU, DocVQA, MathVista

### GPT-4V multimodal benchmark scores
- **value/result**: MMMU (val) ≈ 53.8–56.8% (range across secondary sources); DocVQA (ANLS) 87.2%; MathVista (testmini) 49.4%
- **condition**: 0-shot or few-shot as per official evaluation; exact protocol not confirmed from primary read
- **source**: OpenAI GPT-4V(ision) System Card, Sep 2023, https://openai.com/research/gpt-4v-system-work; GPT-4 Technical Report arXiv:2303.08774 · **tier**: B · **confidence**: med — specific numbers reproduced across multiple secondary sources but not read from GPT-4V system card directly in this session; mark as UNVERIFIED for load-bearing use

### GPT-4o multimodal benchmark scores (Hello GPT-4o announcement, May 2024)
- **value/result**: MMMU (val) — commonly cited as 69.1% in the Hello GPT-4o blog post (2024-05-13); DocVQA 92.8%; MathVista (testmini) 63.8%
- **condition**: 0-shot; MMMU 69.1% is from the model's launch announcement; the Aug-2024 system card snapshot may differ
- **source**: OpenAI, "Hello GPT-4o", 2024-05-13, https://openai.com/index/hello-gpt-4o/; OpenAI GPT-4o System Card, 2024-08-08, https://openai.com/index/gpt-4o-system-card/ (PDF: https://cdn.openai.com/gpt-4o-system-card.pdf) · **tier**: B · **confidence**: med — report URL confirmed; individual benchmark numbers reproduced from secondary sources and consistent across them but not read from the PDF in this session; treat all numbers as UNVERIFIED for any load-bearing derivation

### GPT-4o vs GPT-4V improvement pattern
- **value/result**: GPT-4o gains ~15–16 pp on MMMU over GPT-4V, ~5 pp on DocVQA, ~14 pp on MathVista
- **condition**: Comparing the numbers cited above across both model generations
- **source**: Derived from secondary-source comparison tables; consistent with MMMU leaderboard trends · **tier**: C · **confidence**: med


---
## Q2 — Gemini 1.5 Pro / 2.0 and Claude 3.5 Sonnet: MMMU, DocVQA, MathVista

### Gemini 1.5 Pro benchmark scores (v1 February 2024)
- **value/result**: MathVista (testmini) 52.1% (v1, Feb 2024) → 63.9% (v2, May 2024 improved model); DocVQA: described as achieving SOTA results; MMMU (val) ~58.5% — exact value not confirmed from primary PDF read in this session
- **condition**: 0-shot evaluation on public test splits; v1 vs v2 refers to arXiv revision dates reflecting model updates
- **source**: Reid et al. 2024, "Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context", arXiv:2403.05530 (v1 2024-02-23, v2 2024-05-23); PDF: https://arxiv.org/pdf/2403.05530 · **tier**: B · **confidence**: med — arXiv paper confirmed; MathVista 52.1%→63.9% trajectory confirmed in search snippets; MMMU value is UNVERIFIED from direct PDF read

### Gemini 2.5 Pro benchmark scores (proxy for current Gemini 2.x generation)
- **value/result**: MMMU (val) 81.7%; Gemini 2.5 Flash MMMU 79.7%
- **condition**: From the Gemini 2.5 technical report (arXiv:2507.06261); split/shot details not confirmed from primary read
- **source**: Google DeepMind, "Gemini 2.5: Pushing the Frontier with Advanced Reasoning, Multimodality, Long Context, and Next Generation Agentic Capabilities", arXiv:2507.06261, 2025; HTML: https://arxiv.org/html/2507.06261v6 · **tier**: B · **confidence**: low — numbers appeared in search snippets; paper URL confirmed; individual metric values are UNVERIFIED from direct read; note: the question asks for Gemini "2.0", but only Gemini 2.5 numbers surfaced in search; Gemini 2.0 Flash specific numbers were not found

### Gemini Ultra (1.0) multimodal scores (baseline reference)
- **value/result**: MMMU (val) 59.4% (pass@1); DocVQA (ANLS) 90.9%; MathVista 53.0%
- **condition**: From Gemini 1.0 technical report (Anil et al. 2023); 0-shot conditions assumed
- **source**: Anil et al. 2023, "Gemini: A Family of Highly Capable Multimodal Models", arXiv:2312.11805 — URL confirmed in earlier literature; numbers came from search snippet · **tier**: B · **confidence**: low — numbers appeared in search snippet only; UNVERIFIED from direct PDF read in this session

### Claude 3.5 Sonnet vision benchmark scores
- **value/result**: MMMU (val, 0-shot) 68.3%; MathVista (testmini, 0-shot) 67.7%; DocVQA (test, 0-shot, ANLS) 95.2%
- **condition**: 0-shot on all three; MMMU and MathVista use chain-of-thought reasoning before final answer
- **source**: Anthropic, "Claude 3.5 Model Card Addendum", 2024, https://www-cdn.anthropic.com/fed9cc193a14b84131812372d8d5857f8f304c52/Model_Card_Claude_3_Addendum.pdf · **tier**: B · **confidence**: med — PDF URL confirmed; numbers appeared in a search snippet quoting the document directly; UNVERIFIED from direct in-session PDF read; treat as tier-B not load-bearing


---
## Q3 — Published-vs-deployed deployment gap: why open-weight models dominate practitioner use

### Deployment gap thesis — cost and data-sovereignty drivers
- **value/result**: The cost of GPT-4-equivalent performance dropped from ~$20/M tokens (late 2022) to ~$0.40/M tokens (early 2026); open-weight deployments allow self-hosting at commodity compute cost and keep sensitive data fully on-premises. Enterprise practitioners route cost-sensitive or privacy-sensitive tasks to self-hosted open-weight multimodal models (e.g., LLaVA family, Qwen2-VL, Llama-Vision) even when closed API models score higher on MMMU/DocVQA.
- **condition**: Reflects 2024–2026 enterprise deployment patterns; quantitative cost gap is from a secondary industry survey
- **source**: "Open Source vs Closed LLMs: Technical Comparison 2026", https://hakia.com/compare/open-vs-closed-llms/ (2026); "Open vs. Closed LLMs in 2025: Strategic Tradeoffs for Enterprise AI", Medium/Data Science Collective, https://medium.com/data-science-collective/open-vs-closed-llms-in-2025-strategic-tradeoffs-for-enterprise-ai-668af30bffa0 · **tier**: C · **confidence**: med

### Deployment gap — performance parity on domain tasks vs public benchmarks
- **value/result**: The performance gap between open and closed source LLMs on knowledge benchmarks narrowed from ~17.5 pp (end of 2023) to ~0 pp on MMLU-Pro by early 2026, with 3–5 pp remaining on reasoning tasks. MMMU/DocVQA/MathVista scores of closed frontier models thus overstate the deployment-relevant advantage in domain-specific multimodal tasks where fine-tuned open-weight models close the gap.
- **condition**: Benchmark gap estimate from industry survey; not a peer-reviewed finding
- **source**: "Open Source vs Closed LLMs: Technical Comparison 2026", https://hakia.com/compare/open-vs-closed-llms/ · **tier**: C · **confidence**: low — secondary industry survey, not a primary research finding; use for framing only

### Deployment gap — LLaVA framework dominance and open training paradigm
- **value/result**: LLaVA, LLaVA-Next, and LLaVA-OneVision established the open-weight multimodal fine-tuning paradigm (visual instruction tuning); their public training data and code enabled the practitioner community to train and fine-tune custom vision-language models. Despite a growing performance gap vs. closed frontier models, the LLaVA paradigm dominates self-hosted deployments because full model weights + training recipes are available (enabling domain fine-tuning) whereas closed API models provide no such access.
- **condition**: Observation from LLaVA-OneVision-1.5 paper and community literature
- **source**: LLaVA-OneVision-1.5, arXiv:2509.23661, 2025, https://arxiv.org/html/2509.23661v1; "Large Multimodal Models: Notes on CVPR 2023 Tutorial", arXiv:2306.14895 · **tier**: B · **confidence**: med — paper URLs confirmed; specific claim about deployment dominance is UNVERIFIED from direct read; treat as contextual framing

### Deployment gap — Molmo near-parity result (open-weight counterexample to gap)
- **value/result**: Molmo (open-weight) achieved near-parity with GPT-4V on academic benchmarks and user preference evaluations through careful architectural choices, refined training pipeline, and high-quality data — demonstrating that the deployment gap is not an intrinsic open-vs-closed divide but reflects training-data and compute investment.
- **condition**: Comparison vs. GPT-4V (not GPT-4o); user preference evaluation methodology not specified in search snippet
- **source**: Mentioned in LLaVA-OneVision-1.5 survey, arXiv:2509.23661, https://arxiv.org/html/2509.23661v1 · **tier**: B · **confidence**: low — secondary citation; Molmo primary paper (Allen Institute, 2024) not directly accessed in this session; use as supporting point only

