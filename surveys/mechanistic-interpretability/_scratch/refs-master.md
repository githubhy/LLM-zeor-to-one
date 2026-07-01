# Master reference numbering (north star for in-text [N] citations)

Stable [N] → source map. Sections cite bare `[N]`; `references.md` is built from this list and
`link-references.py --init` promotes the bare forms. Tag plan: `local:` = arXiv PDF in download/
(fetch-corpus.sh / fetch-supp.sh); `web:` = web-native publication (transformer-circuits.pub /
distill / lab blog / alignment forum) — legitimate weak-form tag, citation IS the page;
`abstract:` = abstract-only fallback. Load-bearing claims must rest on local:/strong sources.

| N | Tag | Citation |
|---|---|---|
| 1 | web | Elhage et al. (2021), "A Mathematical Framework for Transformer Circuits," Transformer Circuits Thread. transformer-circuits.pub/2021/framework |
| 2 | web | Olah, Cammarata, Schubert, Goh, Petrov, Carter (2020), "Zoom In: An Introduction to Circuits," Distill. distill.pub/2020/circuits/zoom-in |
| 3 | local:elhage-toy-models-superposition-2022 | Elhage et al. (2022), "Toy Models of Superposition," Transformer Circuits Thread. arXiv:2209.10652 |
| 4 | local:park-lrh-geometry-2024 | Park, Choe, Veitch (2024), "The Linear Representation Hypothesis and the Geometry of Large Language Models," ICML 2024. arXiv:2311.03658 |
| 5 | local:engels-not-all-features-linear-2024 | Engels, Liao, Michaud, Gurnee, Tegmark (2024), "Not All Language Model Features Are Linear," ICLR 2025. arXiv:2405.14860 |
| 6 | web | Elhage et al. (2023), "Privileged Bases in the Transformer Residual Stream," Transformer Circuits Thread. transformer-circuits.pub/2023/privileged-basis |
| 7 | web | Bricken, Templeton, Batson, et al. (2023), "Towards Monosemanticity: Decomposing Language Models With Dictionary Learning," Transformer Circuits Thread. transformer-circuits.pub/2023/monosemantic-features |
| 8 | web | Templeton, Conerly, Marcus, Lindsey, et al. (2024), "Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet," Transformer Circuits Thread. transformer-circuits.pub/2024/scaling-monosemanticity |
| 9 | local:cunningham-saes-interpretable-features-2023 | Cunningham, Ewart, Riggs, Huben, Sharkey (2023), "Sparse Autoencoders Find Highly Interpretable Features in Language Models," ICLR 2024. arXiv:2309.08600 |
| 10 | local:rajamanoharan-gated-saes-2024 | Rajamanoharan, Conmy, Smith, Lieberum, Varma, Kramár, Shah, Nanda (2024), "Improving Dictionary Learning with Gated Sparse Autoencoders," arXiv:2404.16014 |
| 11 | local:gao-topk-saes-2024 | Gao, Dupré la Tour, Tillman, Goh, Troll, Radford, Sutskever, Leike, Wu (2024), "Scaling and Evaluating Sparse Autoencoders," arXiv:2406.04093 |
| 12 | local:rajamanoharan-jumprelu-saes-2024 | Rajamanoharan, Lieberum, Sonnerat, Conmy, Varma, Kramár, Nanda (2024), "Jumping Ahead: Improving Reconstruction Fidelity with JumpReLU Sparse Autoencoders," arXiv:2407.14435 |
| 13 | local:bussmann-batchtopk-saes-2024 | Bussmann, Leask, Nanda (2024), "BatchTopK Sparse Autoencoders," arXiv:2412.06410 |
| 14 | local:bussmann-matryoshka-saes-2025 | Bussmann, Leask, Nanda, et al. (2025), "Learning Multi-Level Features with Matryoshka Sparse Autoencoders," arXiv:2503.17547 |
| 15 | local:chanin-feature-absorption-2024 | Chanin, Wilken-Smith, Dulka, Bhatnagar, Bloom (2024), "A is for Absorption: Studying Feature Splitting and Absorption in Sparse Autoencoders," arXiv:2409.14507 |
| 16 | local:engels-dark-matter-saes-2024 | Engels, Riggs, Tegmark (2024), "Decomposing The Dark Matter of Sparse Autoencoders," arXiv:2410.14670 |
| 17 | local:dunefsky-transcoders-2024 | Dunefsky, Chlenski, Nanda (2024), "Transcoders Find Interpretable LLM Feature Circuits," NeurIPS 2024. arXiv:2406.11944 |
| 18 | local:paulo-transcoders-beat-saes-2025 | Paulo, Shabalin, Belrose (2025), "Transcoders Beat Sparse Autoencoders for Interpretability," arXiv:2501.18823 |
| 19 | web | Lindsey, Templeton, Marcus, Conerly, Batson, Olah (2024), "Sparse Crosscoders for Cross-Layer Features and Model Diffing," Transformer Circuits Thread. transformer-circuits.pub/2024/crosscoders |
| 20 | web | Anthropic Interpretability Team (2025), "Circuit Tracing: Revealing Computational Graphs in Language Models," Transformer Circuits Thread. transformer-circuits.pub/2025/attribution-graphs/methods.html |
| 21 | web | Anthropic Interpretability Team (2025), "On the Biology of a Large Language Model," Transformer Circuits Thread. transformer-circuits.pub/2025/attribution-graphs/biology.html |
| 22 | web | nostalgebraist (2020), "interpreting GPT: the logit lens," LessWrong |
| 23 | local:belrose-tuned-lens-2023 | Belrose, Ostrovsky, McKinney, Furman, Smith, Halawi, Biderman, Steinhardt (2023), "Eliciting Latent Predictions from Transformers with the Tuned Lens," arXiv:2303.08112 |
| 24 | local:alain-linear-classifier-probes-2016 | Alain, Bengio (2016), "Understanding intermediate layers using linear classifier probes," arXiv:1610.01644 |
| 25 | local:hewitt-probes-control-tasks-2019 | Hewitt, Liang (2019), "Designing and Interpreting Probes with Control Tasks," EMNLP-IJCNLP 2019. arXiv:1909.03368 |
| 26 | local:belinkov-probing-classifiers-2022 | Belinkov (2022), "Probing Classifiers: Promises, Shortcomings, and Advances," Computational Linguistics 48(1). arXiv:2102.12452 |
| 27 | local:li-othello-emergent-world-2022 | Li, Hopkins, Bau, Viégas, Pfister, Wattenberg (2022), "Emergent World Representations: Exploring a Sequence Model Trained on a Synthetic Task," ICLR 2023. arXiv:2210.13382 |
| 28 | local:nanda-emergent-linear-repr-2023 | Nanda, Lee, Wattenberg (2023), "Emergent Linear Representations in World Models of Self-Supervised Sequence Models," BlackboxNLP 2023. arXiv:2309.00941 |
| 29 | local:jain-attention-not-explanation-2019 | Jain, Wallace (2019), "Attention is not Explanation," NAACL-HLT 2019. arXiv:1902.10186 |
| 30 | local:wiegreffe-attention-not-not-explanation-2019 | Wiegreffe, Pinter (2019), "Attention is not not Explanation," EMNLP-IJCNLP 2019. arXiv:1908.04626 |
| 31 | local:meng-rome-2022 | Meng, Bau, Andonian, Belinkov (2022), "Locating and Editing Factual Associations in GPT," NeurIPS 2022. arXiv:2202.05262 |
| 32 | local:vig-causal-mediation-2020 | Vig, Gehrmann, Belinkov, Qian, Nevo, Singer, Shieber (2020), "Investigating Gender Bias in Language Models Using Causal Mediation Analysis," NeurIPS 2020. arXiv:2004.12265 |
| 33 | local:zhang-activation-patching-best-practices-2023 | Zhang, Nanda (2023), "Towards Best Practices of Activation Patching in Language Models: Metrics and Methods," ICLR 2024. arXiv:2309.16042 |
| 34 | local:heimersheim-activation-patching-guide-2024 | Heimersheim, Nanda (2024), "How to use and interpret activation patching," arXiv:2404.15255 |
| 35 | local:wang-ioi-2022 | Wang, Variengien, Conmy, Shlegeris, Steinhardt (2022), "Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small," ICLR 2023. arXiv:2211.00593 |
| 36 | local:goldowsky-dill-path-patching-2023 | Goldowsky-Dill, MacLeod, Sato, Arora (2023), "Localizing Model Behavior with Path Patching," arXiv:2304.05969 |
| 37 | web | Nanda (2023), "Attribution Patching: Activation Patching at Industrial Scale," neelnanda.io / AlignmentForum |
| 38 | local:syed-eap-2023 | Syed, Rager, Conmy (2023), "Attribution Patching Outperforms Automated Circuit Discovery," BlackboxNLP 2024. arXiv:2310.10348 |
| 39 | local:kramar-atp-star-2024 | Kramár, Lieberum, Shah, Nanda (2024), "AtP*: An Efficient and Scalable Method for Localizing LLM Behaviour to Components," arXiv:2403.00745 |
| 40 | local:conmy-acdc-2023 | Conmy, Mavor-Parker, Lynch, Heimersheim, Garriga-Alonso (2023), "Towards Automated Circuit Discovery for Mechanistic Interpretability," NeurIPS 2023. arXiv:2304.14997 |
| 41 | local:hanna-eap-ig-faithfulness-2024 | Hanna, Pezzelle, Belinkov (2024), "Have Faith in Faithfulness: Going Beyond Circuit Overlap When Finding Model Mechanisms," arXiv:2403.17806 |
| 42 | web | Chan, Garriga-Alonso, Goldowsky-Dill, Greenblatt, Nitishinskaya, Radhakrishnan, Shlegeris, Thomas (2022), "Causal Scrubbing: a method for rigorously testing interpretability hypotheses," AI Alignment Forum |
| 43 | local:geiger-das-2023 | Geiger, Wu, Potts, Icard, Goodman (2024), "Finding Alignments Between Interpretable Causal Variables and Distributed Neural Representations," CLeaR 2024. arXiv:2303.02536 |
| 44 | local:wu-boundless-das-2023 | Wu, Geiger, Icard, Potts, Goodman (2023), "Interpretability at Scale: Identifying Causal Mechanisms in Alpaca," NeurIPS 2023. arXiv:2305.08809 |
| 45 | local:geiger-causal-abstraction-2025 | Geiger, Ibeling, Zur, et al. (2025), "Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability," JMLR 26. arXiv:2301.04709 |
| 46 | local:turner-actadd-2023 | Turner, Thiergart, Udell, Leech, Mini, MacDiarmid (2023), "Activation Addition: Steering Language Models Without Optimization," arXiv:2308.10248 |
| 47 | local:rimsky-caa-2024 | Rimsky, Gabrieli, Schulz, Tong, Hubinger, Turner (2024), "Steering Llama 2 via Contrastive Activation Addition," ACL 2024. arXiv:2312.06681 |
| 48 | local:zou-repe-2023 | Zou, Phan, Chen, Campbell, et al. (2023), "Representation Engineering: A Top-Down Approach to AI Transparency," arXiv:2310.01405 |
| 49 | local:arditi-refusal-direction-2024 | Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda (2024), "Refusal in Language Models Is Mediated by a Single Direction," NeurIPS 2024. arXiv:2406.11717 |
| 50 | local:chalnev-sae-ts-2024 | Chalnev, Siu, Conmy (2024), "Improving Steering Vectors by Targeting Sparse Autoencoder Features," arXiv:2411.02193 |
| 51 | local:meng-memit-2023 | Meng, Sharma, Andonian, Belinkov, Bau (2023), "Mass-Editing Memory in a Transformer," ICLR 2023. arXiv:2210.07229 |
| 52 | local:gupta-editing-catastrophic-forgetting-2024 | Gupta, Rao, Anumanchipalli (2024), "Model Editing at Scale leads to Gradual and Catastrophic Forgetting," ACL Findings 2024. arXiv:2401.07453 |
| 53 | local:cohen-ripple-effects-2023 | Cohen, Biran, Yoran, Globerson, Geva (2023), "Evaluating the Ripple Effects of Knowledge Editing in Language Models," TACL 2024. arXiv:2307.12976 |
| 54 | local:hase-localization-editing-2023 | Hase, Bansal, Kim, Ghandeharioun (2023), "Does Localization Inform Editing? Surprising Differences in Causality-Based Localization vs. Knowledge Editing," NeurIPS 2023. arXiv:2301.04213 |
| 55 | local:nanda-grokking-progress-measures-2023 | Nanda, Chan, Lieberum, Smith, Steinhardt (2023), "Progress Measures for Grokking via Mechanistic Interpretability," ICLR 2023. arXiv:2301.05217 |
| 56 | local:hanna-greater-than-2023 | Hanna, Liu, Variengien (2023), "How Does GPT-2 Compute Greater-Than?: Interpreting Mathematical Abilities in a Pre-trained Language Model," NeurIPS 2023. arXiv:2305.00586 |
| 57 | web | Heimersheim, Janiak (2023), "A Circuit for Python Docstrings in a 4-Layer Attention-Only Transformer," AI Alignment Forum |
| 58 | local:bolukbasi-interpretability-illusion-bert-2021 | Bolukbasi, Pearce, Yuan, Coenen, Reif, Viégas, Wattenberg (2021), "An Interpretability Illusion for BERT," arXiv:2104.07143 |
| 59 | local:mcgrath-hydra-effect-2023 | McGrath, Rahtz, Kramár, Mikulik, Legg (2023), "The Hydra Effect: Emergent Self-repair in Language Model Computations," arXiv:2307.15771 |
| 60 | local:rushing-self-repair-2024 | Rushing, Nanda (2024), "Explorations of Self-Repair in Language Models," ICML 2024. arXiv:2402.15390 |
| 61 | local:mcdougall-copy-suppression-2023 | McDougall, Conmy, Rushing, McGrath, Nanda (2023), "Copy Suppression: Comprehensively Understanding an Attention Head in GPT-2 Small," arXiv:2310.04625 |
| 62 | local:miller-faithfulness-not-robust-2024 | Miller, Chughtai, Saunders (2024), "Transformer Circuit Faithfulness Metrics Are Not Robust," COLM 2024. arXiv:2407.08734 |
| 63 | local:karvonen-saebench-2025 | Karvonen, Rager, Lin, Tigges, Bloom, et al. (2025), "SAEBench: A Comprehensive Benchmark for Sparse Autoencoders in Language Model Interpretability," ICML 2025. arXiv:2503.09532 |
| 64 | local:huang-ravel-2024 | Huang, Wu, Potts, Geva, Geiger (2024), "RAVEL: Evaluating Interpretability Methods on Disentangling Language Model Representations," ACL 2024. arXiv:2402.17700 |
| 65 | local:lieberum-gemma-scope-2024 | Lieberum, Rajamanoharan, Conmy, Smith, Sonnerat, Varma, Kramár, et al. (2024), "Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2," BlackboxNLP 2024. arXiv:2408.05147 |
| 66 | local:wu-axbench-2025 | Wu, Arora, Geiger, Wang, Huang, Jurafsky, Manning, Potts (2025), "AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders," ICLR 2025. arXiv:2501.17148 |
| 67 | local:deepmind-saes-useful-sparse-probing-2025 | Kissane, Krzyzanowski, Nanda, Conmy, et al. (2025), "Are Sparse Autoencoders Useful? A Case Study in Sparse Probing," arXiv:2502.16681 |
| 68 | web | Bills, Cammarata, Mossing, Tillman, Gao, Goh, Sutskever, Leike, Wu, Saunders (2023), "Language Models Can Explain Neurons in Language Models," OpenAI |
| 69 | web | EleutherAI (2024), "Open Source Automated Interpretability for Sparse Autoencoder Features" (Delphi), blog.eleuther.ai/autointerp |
| 70 | local:hubinger-sleeper-agents-2024 | Hubinger, Denison, Mu, Lambert, et al. (2024), "Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training," arXiv:2401.05566 |
| 71 | web | MacDiarmid, Maxwell, Schiefer, et al. (2024), "Simple Probes Can Catch Sleeper Agents," Anthropic Alignment Science Blog |
| 72 | local:belrose-leace-2023 | Belrose, Schoots, Hollinsworth, Ostrovsky, Tigges, Frankle, Sharma, Biderman (2023), "LEACE: Perfect Linear Concept Erasure in Closed Form," NeurIPS 2023. arXiv:2306.03819 |
| 73 | local:li-wmdp-rmu-2024 | Li, Pan, Gopal, Yue, Berrios, et al. (2024), "The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning," ICML 2024. arXiv:2403.03218 |
| 74 | web | Chughtai (2024), "Unlearning via RMU is Mostly Shallow," AI Alignment Forum |
| 75 | web | Anthropic (2024), "Golden Gate Claude," Anthropic News |
| 76 | web | Amodei (2025), "The Urgency of Interpretability," darioamodei.com |
| 77 | local:costa-mp-sae-2025 | Costa, et al. (2025), "From Flat to Hierarchical: Extracting Sparse Representations with Matching Pursuit," NeurIPS 2025. arXiv:2506.03093 |
| 78 | local:vanderweij-sandbagging-2024 | van der Weij, Hofstätter, Jaffe, Brown, Ward (2024), "AI Sandbagging: Language Models Can Strategically Underperform on Evaluations," arXiv:2406.07358 |
| 79 | local:sundararajan-integrated-gradients-2017 | Sundararajan, Taly, Yan (2017), "Axiomatic Attribution for Deep Networks (Integrated Gradients)," ICML 2017. arXiv:1703.01365 |
| 80 | local:olsson-induction-heads-2022 | Olsson, Elhage, Nanda, Joseph, et al. (2022), "In-context Learning and Induction Heads," Transformer Circuits Thread. arXiv:2209.11895 |
| 81 | local:marks-sparse-feature-circuits-2024 | Marks, Rager, Michaud, Belinkov, Bau, Mueller (2024), "Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs in Language Models," ICLR 2025. arXiv:2403.19647 |

## Supplementary-fetch arXiv IDs (not in fetch-corpus.sh)
2311.03658 park-lrh-geometry-2024
2405.14860 engels-not-all-features-linear-2024
2004.12265 vig-causal-mediation-2020
1703.01365 sundararajan-integrated-gradients-2017
