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
