# References

Every entry ends with a **source tag** declaring where the acquired source lives, per the
`references.md` ↔ `download/` invariant (`.claude/rules/citation-integrity.md`): `(local: download/<file>)`
for full text held in the repo, `(spec: docs/specs/<path>)` for a formal spec, `(web)` for a live
web-only resource, `(abstract-only)` where only the abstract is held. `local:`/`spec:` are the strong
forms; `web`/`abstract-only` are weak and must not carry a load-bearing claim.

Entries are added during Phase 3 (acquisition) and Phase 4 (synthesis) with `<!-- bib:N -->` markers; the
paragraph anchor sits on the line **above** each `[N]` so `check-citation-sources.py` detects every entry.

<a id="ref-1"></a><!-- bib:1 -->
[1] A. Radford, J. W. Kim, C. Hallacy, et al., "Learning Transferable Visual Models From Natural Language Supervision," ICML 2021. arXiv:2103.00020. (local: download/radford-clip-2021.pdf)

<a id="ref-2"></a><!-- bib:2 -->
[2] A. Dosovitskiy, L. Beyer, A. Kolesnikov, et al., "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale," ICLR 2021. arXiv:2010.11929. (local: download/dosovitskiy-vit-2020.pdf)

<a id="ref-3"></a><!-- bib:3 -->
[3] J.-B. Alayrac, J. Donahue, P. Luc, et al., "Flamingo: a Visual Language Model for Few-Shot Learning," NeurIPS 2022. arXiv:2204.14198. (local: download/alayrac-flamingo-2022.pdf)

<a id="ref-4"></a><!-- bib:4 -->
[4] J. Li, D. Li, S. Savarese, S. Hoi, "BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models," ICML 2023. arXiv:2301.12597. (local: download/li-blip2-2023.pdf)

<a id="ref-5"></a><!-- bib:5 -->
[5] H. Liu, C. Li, Q. Wu, Y. J. Lee, "Visual Instruction Tuning," NeurIPS 2023. arXiv:2304.08485. (local: download/liu-llava-2023.pdf)

<a id="ref-6"></a><!-- bib:6 -->
[6] H. Liu, C. Li, Y. Li, Y. J. Lee, "Improved Baselines with Visual Instruction Tuning," CVPR 2024. arXiv:2310.03744. (local: download/liu-llava-1.5-2023.pdf)

<a id="ref-7"></a><!-- bib:7 -->
[7] P. Wang, S. Bai, S. Tan, et al., "Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution," 2024. arXiv:2409.12191. (local: download/wang-qwen2-vl-2024.pdf)

<a id="ref-8"></a><!-- bib:8 -->
[8] Chameleon Team (FAIR at Meta), "Chameleon: Mixed-Modal Early-Fusion Foundation Models," 2024. arXiv:2405.09818. (local: download/team-chameleon-2024.pdf)

<a id="ref-9"></a><!-- bib:9 -->
[9] Emu3 Team (BAAI), "Emu3: Next-Token Prediction is All You Need," 2024. arXiv:2409.18869. (local: download/wang-emu3-2024.pdf)

<a id="ref-10"></a><!-- bib:10 -->
[10] C. Zhou, L. Yu, A. Babu, et al., "Transfusion: Predict the Next Token and Diffuse Images with One Multi-Modal Model," 2024. arXiv:2408.11039. (local: download/zhou-transfusion-2024.pdf)

<a id="ref-11"></a><!-- bib:11 -->
[11] X. Yue, Y. Ni, K. Zhang, et al., "MMMU: A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark for Expert AGI," CVPR 2024. arXiv:2311.16502. (local: download/yue-mmmu-2023.pdf)

<a id="ref-12"></a><!-- bib:12 -->
[12] Y. Li, Y. Du, K. Zhou, et al., "Evaluating Object Hallucination in Large Vision-Language Models," EMNLP 2023. arXiv:2305.10355. (local: download/li-pope-2023.pdf)

<a id="ref-13"></a><!-- bib:13 -->
[13] OpenAI, "Hello GPT-4o," 2024-05-13. https://openai.com/index/hello-gpt-4o/ (web)

<a id="ref-14"></a><!-- bib:14 -->
[14] Adept, "Fuyu-8B: A Multimodal Architecture for AI Agents," 2023-10. https://www.adept.ai/blog/fuyu-8b (web)

<a id="ref-15"></a><!-- bib:15 -->
[15] X. Zhai, B. Mustafa, A. Kolesnikov, L. Beyer, "Sigmoid Loss for Language Image Pre-Training," ICCV 2023. arXiv:2303.15343. (local: download/zhai-siglip-2023.pdf)

<a id="ref-16"></a><!-- bib:16 -->
[16] A. van den Oord, O. Vinyals, K. Kavukcuoglu, "Neural Discrete Representation Learning," NeurIPS 2017. arXiv:1711.00937. (local: download/vandenoord-vqvae-2017.pdf)

<a id="ref-17"></a><!-- bib:17 -->
[17] P. Esser, R. Rombach, B. Ommer, "Taming Transformers for High-Resolution Image Synthesis," CVPR 2021. arXiv:2012.09841. (local: download/esser-vqgan-2021.pdf)

<a id="ref-18"></a><!-- bib:18 -->
[18] C. Wu, X. Chen, Z. Wu, et al., "Janus: Decoupling Visual Encoding for Unified Multimodal Understanding and Generation," 2024. arXiv:2410.13848. (local: download/wu-janus-2024.pdf)

<a id="ref-19"></a><!-- bib:19 -->
[19] A. Radford, J. W. Kim, T. Xu, et al., "Robust Speech Recognition via Large-Scale Weak Supervision," ICML 2023. arXiv:2212.04356. (local: download/radford-whisper-2022.pdf)

<a id="ref-20"></a><!-- bib:20 -->
[20] Y. Chu, J. Xu, X. Zhou, et al., "Qwen-Audio: Advancing Universal Audio Understanding via Unified Large-Scale Audio-Language Models," 2023. arXiv:2311.07919. (local: download/chu-qwen-audio-2023.pdf)

<a id="ref-21"></a><!-- bib:21 -->
[21] C. Tang, W. Yu, G. Sun, et al., "SALMONN: Towards Generic Hearing Abilities for Large Language Models," ICLR 2024. arXiv:2310.13289. (local: download/tang-salmonn-2024.pdf)

<a id="ref-22"></a><!-- bib:22 -->
[22] P. K. Rubenstein, C. Asawaroengchai, D. D. Nguyen, et al., "AudioPaLM: A Large Language Model That Can Speak and Listen," 2023. arXiv:2306.12925. (local: download/rubenstein-audiopalm-2023.pdf)

<a id="ref-23"></a><!-- bib:23 -->
[23] B. Lin, Y. Ye, B. Zhu, et al., "Video-LLaVA: Learning United Visual Representation by Alignment Before Projection," EMNLP 2024. arXiv:2311.10122. (local: download/lin-video-llava-2023.pdf)

<a id="ref-24"></a><!-- bib:24 -->
[24] Z. Chen, J. Wu, W. Wang, et al., "InternVL: Scaling up Vision Foundation Models and Aligning for Generic Visual-Linguistic Tasks," CVPR 2024. arXiv:2312.14238. (local: download/chen-internvl-2023.pdf)

<a id="ref-25"></a><!-- bib:25 -->
[25] J. Bai, S. Bai, S. Yang, et al., "Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond," 2023. arXiv:2308.12966. (local: download/bai-qwen-vl-2023.pdf)

<a id="ref-26"></a><!-- bib:26 -->
[26] S. Bai, K. Chen, X. Liu, et al., "Qwen2.5-VL Technical Report," 2025. arXiv:2502.13923. (local: download/bai-qwen2.5-vl-2025.pdf)

<a id="ref-27"></a><!-- bib:27 -->
[27] H. Laurençon, L. Tronchon, M. Cord, V. Sanh, "What matters when building vision-language models?" (Idefics2), NeurIPS 2024. arXiv:2405.02246. (local: download/laurencon-idefics2-2024.pdf)

<a id="ref-28"></a><!-- bib:28 -->
[28] L. Beyer, A. Steiner, A. S. Pinto, et al., "PaliGemma: A versatile 3B VLM for transfer," 2024. arXiv:2407.07726. (local: download/beyer-paligemma-2024.pdf)

<a id="ref-29"></a><!-- bib:29 -->
[29] M. Deitke, C. Clark, S. Lee, et al., "Molmo and PixMo: Open Weights and Open Data for State-of-the-Art Multimodal Models," 2024. arXiv:2409.17146. (local: download/deitke-molmo-2024.pdf)

<a id="ref-30"></a><!-- bib:30 -->
[30] P. Agrawal, S. Antoniak, E. B. Hanna, et al., "Pixtral 12B," 2024. arXiv:2410.07073. (local: download/agrawal-pixtral-2024.pdf)

<a id="ref-31"></a><!-- bib:31 -->
[31] H. Lu, W. Liu, B. Zhang, et al., "DeepSeek-VL: Towards Real-World Vision-Language Understanding," 2024. arXiv:2403.05525. (local: download/lu-deepseek-vl-2024.pdf)

<a id="ref-32"></a><!-- bib:32 -->
[32] W. Dai, N. Lee, B. Wang, et al., "NVLM: Open Frontier-Class Multimodal LLMs," 2024. arXiv:2409.11402. (local: download/dai-nvlm-2024.pdf)

<a id="ref-33"></a><!-- bib:33 -->
[33] H. Liu, C. Li, Y. Li, et al., "LLaVA-NeXT: Improved reasoning, OCR, and world knowledge," blog, 2024-01-30. https://llava-vl.github.io/blog/2024-01-30-llava-next/ (web)

<a id="ref-34"></a><!-- bib:34 -->
[34] W. Wang, Q. Lv, W. Yu, et al., "CogVLM: Visual Expert for Pretrained Language Models," 2023. arXiv:2311.03079. (abstract-only)

<a id="ref-35"></a><!-- bib:35 -->
[35] D. Zhu, J. Chen, X. Shen, X. Li, M. Elhoseiny, "MiniGPT-4: Enhancing Vision-Language Understanding with Advanced Large Language Models," 2023. arXiv:2304.10592. (abstract-only)

<a id="ref-36"></a><!-- bib:36 -->
[36] Q. Ye, H. Xu, G. Xu, et al., "mPLUG-Owl: Modularization Empowers Large Language Models with Multimodality," 2023. arXiv:2304.14178. (abstract-only)

<a id="ref-37"></a><!-- bib:37 -->
[37] H. Zhang, X. Li, L. Bing, "Video-LLaMA: An Instruction-tuned Audio-Visual Language Model for Video Understanding," EMNLP 2023 (Demo). arXiv:2306.02858. (abstract-only)

<a id="ref-38"></a><!-- bib:38 -->
[38] A. Défossez, L. Mazaré, M. Orsini, et al., "Moshi: a speech-text foundation model for real-time dialogue," Kyutai, 2024. https://kyutai.org/Moshi.pdf (web)

<a id="ref-39"></a><!-- bib:39 -->
[39] C. Schuhmann, R. Beaumont, R. Vencu, et al., "LAION-5B: An Open Large-Scale Dataset for Training Next Generation Image-Text Models," NeurIPS 2022 (Datasets & Benchmarks). arXiv:2210.08402. (local: download/schuhmann-laion5b-2022.pdf)

<a id="ref-40"></a><!-- bib:40 -->
[40] W. Zhu, J. Hessel, A. Awadalla, et al., "Multimodal C4: An Open, Billion-scale Corpus of Images Interleaved with Text," NeurIPS 2023 (Datasets & Benchmarks). arXiv:2304.06939. (local: download/zhu-mmc4-2023.pdf)

<a id="ref-41"></a><!-- bib:41 -->
[41] L. Chen, J. Li, X. Dong, et al., "ShareGPT4V: Improving Large Multi-Modal Models with Better Captions," ECCV 2024. arXiv:2311.12793. (local: download/chen-sharegpt4v-2023.pdf)

<a id="ref-42"></a><!-- bib:42 -->
[42] T. Yu, Y. Yao, H. Zhang, et al., "RLHF-V: Towards Trustworthy MLLMs via Behavior Alignment from Fine-grained Correctional Human Feedback," CVPR 2024. arXiv:2312.00849. (local: download/yu-rlhfv-2023.pdf)

<a id="ref-43"></a><!-- bib:43 -->
[43] F. Wang, W. Zhou, J. Y. Huang, et al., "mDPO: Conditional Preference Optimization for Multimodal Large Language Models," EMNLP 2024. arXiv:2406.11839. (local: download/wang-mdpo-2024.pdf)

<a id="ref-44"></a><!-- bib:44 -->
[44] J. Ho, A. Jain, P. Abbeel, "Denoising Diffusion Probabilistic Models," NeurIPS 2020. arXiv:2006.11239. (local: download/ho-ddpm-2020.pdf)

<a id="ref-45"></a><!-- bib:45 -->
[45] L. Chen, H. Zhao, T. Liu, et al., "An Image is Worth 1/2 Tokens After Layer 2: Plug-and-Play Acceleration for VLLM Inference" (FastV), ECCV 2024. arXiv:2403.06764. (local: download/chen-fastv-2024.pdf)

<a id="ref-46"></a><!-- bib:46 -->
[46] D. Bolya, C.-Y. Fu, X. Dai, et al., "Token Merging: Your ViT But Faster" (ToMe), ICLR 2023. arXiv:2210.09461. (local: download/bolya-tome-2023.pdf)

<a id="ref-47"></a><!-- bib:47 -->
[47] Y. Shang, M. Cai, B. Xu, et al., "LLaVA-PruMerge: Adaptive Token Reduction for Efficient Large Multimodal Models," 2024. arXiv:2403.15388. (local: download/shang-prumerge-2024.pdf)

<a id="ref-48"></a><!-- bib:48 -->
[48] L. Chen, J. Li, X. Dong, et al., "Are We on the Right Way for Evaluating Large Vision-Language Models?" (MMStar), NeurIPS 2024. arXiv:2403.20330. (local: download/chen-mmstar-2024.pdf)
