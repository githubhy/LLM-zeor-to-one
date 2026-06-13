# Scaling-law evidence (verbatim from acquired PDFs) — for primer subsection 3.6

All numbers copied from the source loci; do not write any figure into the survey not on this page.

## Kaplan et al. 2020 — ref [55] (download/kaplan-scaling-laws-2020.pdf)

- **Eq (1.1):** L(N) = (N_c / N)^{α_N}; **α_N ≈ 0.076**, N_c ≈ 8.8×10^13 non-embedding parameters. (trained to convergence on large data)
- **Eq (1.2):** L(D) = (D_c / D)^{α_D}; **α_D ≈ 0.095**, D_c ≈ 5.4×10^13 tokens. (limited data, early stopping)
- **Eq (1.3):** L(C_min) = (C_c^min / C_min)^{α_C^min}; **α_C^min ≈ 0.050**, C_c^min ≈ 3.1×10^8 PF-days. Also Eq (3.3) L(C) ≈ (C_c/C)^{α_C}.
- **Compute estimate:** C ≈ 6·N·B·S (non-embedding; B batch size, S steps). [≈ 6ND per the C=6ND form when BS≈D tokens]
- Headline: test loss is a smooth power law in N, D, C over >6 orders of magnitude; depends strongly on scale, weakly on architectural shape.

## Hoffmann et al. 2022 (Chinchilla) — ref [56] (download/hoffmann-chinchilla-2022.pdf)

- **Eq (10) parametric loss:** L(N,D) = E + A/N^{0.34} + B/D^{0.28}, with **E = 1.69, A = 406.4, B = 410.7**. (so α=0.34 on params, β=0.28 on data)
- **Compute constraint:** "FLOPs(N,D) ≈ 6ND (Kaplan et al., 2020)" / "C = 6DN"; minimize L̂ s.t. this constraint → N_opt ∝ C^a, D_opt ∝ C^b.
- **Compute-optimal exponents:** Approaches 1 & 2: **a = 0.50, b = 0.50**. Approach 3 (parametric fit): **a = 0.46, b = 0.54**. Conclusion: model size and training tokens should be scaled in approximately **equal proportions**.
- **Concrete result:** Chinchilla = **70B** params trained on **1.4 trillion tokens** (4× more data than Gopher at the *same* compute budget). 70B / 1.4T ≈ **20 tokens per parameter**. Chinchilla outperforms Gopher (280B), GPT-3 (175B), Jurassic-1 (178B), MT-NLG (530B).
- Headline: prior large models were significantly **under-trained** (too many params for too few tokens).

## Use in 3.6
Present Kaplan power laws (Eqs for L(N), L(D), L(C) with the three exponents), then Chinchilla Eq (10) + C≈6ND, then the Lagrange-constrained-optimization derivation giving N_opt,D_opt ∝ C^{~0.5} (equal scaling) and the Chinchilla 70B/1.4T ≈ 20-tokens/param example. Tie to over-training (StarCoder2) and data mixture (Qwen) in later sections.
