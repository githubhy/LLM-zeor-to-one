# Frontier cluster E4-theory

## key
E4-theory

## headline
Three 2026 preprints supply exactly the first-principles math the appendices need. (1) Dhor & Chen prove the first finite-sample identifiability theorem for any MI primitive — a Koopman-spectral fingerprint of the transformer's depth recurrence is recoverable at the parametric rate M^{-1/2} (matching minimax lower bound) — and use it to PROVE that SAE run-to-run/seed/width variability is a structural, non-fixable consequence of the reconstruction+L1 objective (Corollary 9.5), not a tuning artifact; they also prove Koopman modes and PCA directions must diverge whenever the system is non-normal (Theorem 8.1), which is empirically ~saturated on all three tested models. (2) D'Angelo et al. give an exact closed form (Proposition 3.1, Eq. 8) for what a two-layer induction-head circuit computes beyond the hard-attention/exact-match limit: a softmax-weighted interpolation over context-match patterns that provably reduces to add-α/Dirichlet smoothing (BOS, β→∞) and to a cumulative-count analogue of Jelinek–Mercer interpolation (finite β) — this is a genuinely new mathematical layer on top of (not a contradiction of) the survey's causal-circuit induction-head story. (3) Basu Roy Chowdhury & Weiner prove tight two-sided bounds on the superposition/sparsity loss for power-activation autoencoders, min(pd^m, dp^{1/m}) ≲ sup_W L̃(W) ≲ min(pd^m, d), formalizing Elhage et al. (2022)'s empirical toy-model picture into a provable regime transition — while explicitly leaving the tight order across the transition as an open problem.

## records (12)

### 1
- **paper**: mi26-spectral-identifiability.pdf
- **claim**: The Koopman-operator spectrum of a transformer's depth recurrence (attention as control input, MLP as autonomous dynamics), fit via the EDMDc estimator from M layer-token calibration samples, converges to the true spectrum up to a permutation at the parametric rate M^{-1/2}, with explicit finite-sample bounds on both eigenvalues and eigenvectors and a stated sample-size threshold M0.
- **numbers**: M0 = (c0 κ0^2 L^4 (1+||A||_2)^2 / (η_Ψ^2 Δ^2)) · (N + log(1/δ)); eigenvalue bound max_k|λ_k(Â_M) − λ_{π(k)}(A)| ≤ (c1 κ0 L^2(1+||A||_2)/η_Ψ) · sqrt((N+log(1/δ))/M); eigenvector bound has an extra 1/Δ factor and quadratic κ0
- **quote**: For every δ ∈ (0, 1/2) and every M ≥ M0 there exists a permutation πM of {1, . . . , N}, determined by ÂM, such that with probability at least 1 − δ: max_k |λk(ÂM) − λπM(k)(A)| ≤ c1κ0L^2(1+‖A‖2)/ηΨ × sqrt((N+log(1/δ))/M)
- **confidence**: high
- **conditions**: Assumptions 1-3 (K-invariance, persistent excitation, spectral gap Δ, condition number κ0), regularity conditions (22)-(23) and (33)-(34), centred controls E_ν[u]=0, EDMDc regularization γ=0; evaluated on GPT-2 small, Gemma-2-2B, Qwen3-8B-Base with calibration corpus WikiText-103 (train split)
- **locator**: Section 6.1, Theorem 6.1, Eqs. 35-37 (Sections 2, A/B-equivalent formal appendix; pdftotext lines ~1050-1150)
- **supersedes**: n/a — authors' own claim: first identifiability theorem for any mechanistic-interpretability primitive

### 2
- **paper**: mi26-spectral-identifiability.pdf
- **claim**: A matching minimax lower bound shows the M^{-1/2} rate of Theorem 6.1 is optimal — no estimator can do better — and the lower bound is dimension-free (no N-dependence), which does not yet meet the upper bound's N-dependent prefactor.
- **numbers**: inf over estimators, sup over A in the class A(Δ,κ0): E[min_π max_k |λk(Â)−λπ(k)(A)|] ≥ σ / (8 g1 sqrt(M)), valid for M with σ/(sqrt(2) g1 M) ≤ Δ/2, where g1 := E_μ|ψ1(x)|^2
- **quote**: Theorem 7.1 (Minimax optimality in M). For every M with σ/√2g1M ≤ ∆/2, inf sup E[min_π max_k |λk(Â)−λπ(k)(A)|] ≥ σ / 8√g1M, the infimum running over all measurable estimators.
- **confidence**: high
- **conditions**: noisy-invariance observation model y_i = AΨ(x_i)+Bu_i+e_i, e_i~N(0,σ^2 I_N); A ranges over class A(Δ,κ0) of diagonalizable matrices with simple spectrum separated by Δ and κ2(V)≤κ0; proof via Le Cam two-point method
- **locator**: Section 7.1, Theorem 7.1, Eqs. 57-58; Remark 6.9 notes the upper/lower bound prefactors 'do not currently meet' (open gap)
- **supersedes**: n/a — establishes optimality of the newly-proven rate; the N-dependence gap vs. the lower bound is itself an open problem stated by the authors

### 3
- **paper**: mi26-spectral-identifiability.pdf
- **claim**: Whenever the fitted Koopman realisation is non-normal (κ2(V)>1), its eigenvector basis (the identifiable 'Koopman modes') provably cannot coincide with the variance-ordered principal-component basis of the lifted system's stationary covariance; an explicit 2x2 family shows this misalignment saturates toward orthogonality at rate κ2(V)^{-1}, and measured condition numbers on all three tested models are far into the saturated regime.
- **numbers**: measured κ2(V̂) = 78.7 (GPT-2 small), 38.2 (Gemma-2-2B), 494.7 (Qwen3-8B-Base); at κ2≈500 the misalignment angle between the minor principal direction and the nearest Koopman mode is 89.7°; on the IOI task PCA removes 60% of the logit difference at j=8 ablated directions vs. Koopman modes' 25%, with the Koopman-mode advantage decaying 4.1x per unit depth-distance
- **quote**: If some orthonormal eigenbasis of Σ consists of eigenvectors of A, then A is normal; equivalently, κ2(V) = 1. ... The measured condition numbers are κ2(V̂) ∈ {78.7, 38.2, 494.7} on GPT-2 small, Gemma-2-2B and Qwen3-8B-Base respectively ... all far above 1 — so the theorem says that on every model in our suite the identifiable Koopman modes must differ from the variance-ordered principal directions.
- **confidence**: high
- **conditions**: applies to the lifted linear recurrence Ψ_{ℓ+1}=AΨ_ℓ+Bu_ℓ under white controls (stationary covariance solves discrete Lyapunov equation Σ=AΣA*+BG_uB*), A diagonalizable with simple spectrum; IOI ablation numbers measured specifically on Qwen3-8B-Base, j=8 ablated directions
- **locator**: Section 8, Theorem 8.1, Proposition 8.2, Remark 8.3; Sections 11.3-11.4 for the empirical IOI numbers
- **supersedes**: n/a — new result; cautions that 'directions of high activation variance' and 'directions carrying information across depth' are provably distinct objects whenever the dynamics are non-normal

### 4
- **paper**: mi26-spectral-identifiability.pdf
- **claim**: Sparse autoencoders trained with the standard reconstruction+L1 objective generically fail the K-invariance condition (DR2) that Theorem 6.1's identifiability guarantee requires; therefore different seeds converge to inequivalent dictionaries whose spectra are provably NOT identifiable, and this bias does not vanish as calibration samples M→∞ — i.e. SAE run-to-run variability is structural to the objective, not an optimization/tuning artifact. An explicit invariance-penalty remedy is proposed.
- **numbers**: remedy: L(D,A_D,z) = ||x−Dz||_2^2 + λ||z||_1 + γ||Ψ_D(F(x,u)) − A_D Ψ_D(x) − B_D u||_2^2 (Eq. 66); measured to reduce split-half spectral distance by 41% at matched sparsity, while degrading reconstruction and cross-seed [stability] (exact companion cost figure not located in extracted text)
- **quote**: In general DSAE satisfies (DR1) but not (DR2). Consequently Theorem 6.1 does not apply to DSAE, and the run-to-run variability documented by [20, 23, 22] is a structural consequence of the objective's failure to enforce K-invariance rather than an artefact of implementation.
- **confidence**: high
- **conditions**: DSAE trained via the standard reconstruction+L1 objective (Eq. 3); ΨD is the dictionary's post-activation code σ(W_enc x + b_enc) with the dictionary's own nonlinearity (ReLU/JumpReLU/TopK), explicitly NOT the pre-activation linear map — the paper states this distinction is load-bearing for the §11.5 measurement; remedy swept in Section 11.6
- **locator**: Section 9.2, Corollary 9.5, Eq. 66; Sections 11.5-11.6 for the 41% measurement
- **supersedes**: Narrows the survey's method-inventory-dictionary.md §6.5 framing of SAE feature-splitting/absorption/seed-variability (citing e.g. Matryoshka SAE as a mitigation) as an empirical/engineerable pathology; this 2026 result proves it is a structural non-identifiability of the standard objective that no width, seed, or hyperparameter choice removes, with only one theorem-backed remedy at a measured cost.

### 5
- **paper**: mi26-spectral-identifiability.pdf
- **claim**: The predicted M^{-1/2} convergence exponent is empirically attained on Qwen3-8B-Base but not on GPT-2 small, where the observed exponent sits well above -1/2 despite four candidate explanations being tested and ruled out (exponent essentially unchanged under all four).
- **numbers**: Qwen3-8B-Base, layer 18, spectral dictionary: exponent −0.506 ± 0.031 (matches Theorem 6.1's predicted −1/2); GPT-2 small at M_max=399,974: −0.286 ± 0.007 (spectral dictionary), −0.290 ± 0.011 (random dictionary); the four tested explanations leave the exponent at −0.245, −0.265, −0.243, −0.294
- **quote**: On GPT-2 small at Mmax = 399,974 the exponents are −0.286 ± 0.007 (spectral) and −0.290 ± 0.011 (random). On Qwen3-8B-Base at layer 18 the spectral dictionary converges at −0.506 ± 0.031 - the value Theorem 6.1 [predicts].
- **confidence**: high
- **conditions**: calibration corpus WikiText-103 (train split); log-log slope of matched spectral error vs. M; per-model, per-layer measurement (layer 18 for Qwen3-8B-Base)
- **locator**: Section 11 (empirical validation), pdftotext lines ~2632-2686
- **supersedes**: n/a — first empirical test of the theorem's predicted rate on real transformers; result is only partially confirmatory (GPT-2 small diverges from the prediction for reasons the authors could not isolate)

### 6
- **paper**: mi26-induction-heads-interpolate-ngrams.pdf
- **claim**: An explicit two-layer disentangled transformer (k attention heads in layer 1, one head in layer 2, RPE) exactly realizes a closed-form next-token estimator for order-k Markov chains: a softmax-normalized sum over ALL context-match subsets M⊆[k], each weighted by e^{|β|_M} times the exact-match-pattern count N_M(m), plus an optional BOS additive pseudo-count term e^κ/|V|. This is the paper's central closed-form result, going beyond the hard-attention/exact-match-only characterization of prior induction-head literature.
- **numbers**: T(x)(m) = [e^κ/|V| + Σ_{M⊆[k]} e^{|β|_M} N_M^(T)(m)] / [e^κ + Σ_{M⊆[k]} e^{|β|_M} N_M^(T)], where |β|_M = Σ_{i∈M} β_i, β=(β1,...,βk)∈R^k, κ∈R free parameters; κ≠−∞ only when a BOS token is prepended (Equation 8)
- **quote**: There exists a two-layer disentangled transformer T with RPE using k attention heads in the first layer and a single attention head in the second layer, such that for any input sequence x ∈ V^T, the model is a probability distribution T(x) ∈ Δ^{|V|−1} over V given by [Equation 8]... First, prepending a BOS token enables an additive constant (pseudo-count) term e^κ/|V|, yielding an add-α-type smoothing of the empirical counts. Second, for finite attention-weight parameters β, the factors e^{|β|_M} induce an interpolation across context orders, producing a Jelinek–Mercer-style estimator.
- **confidence**: high
- **conditions**: order-k Markov-chain generated sequences; disentangled transformer architecture (Friedman et al. 2023: no MLPs, concatenative residual stream); construction is exact (existence proof), separately confirmed to be recovered by trained standard transformers in Section 5
- **locator**: Section 3.1, Proposition 3.1, Equation 8 (feeds the appendix on the mathematical characterization of the induction-head circuit)
- **supersedes**: Extends, does not contradict, the survey's causal-circuit description of induction heads (method-inventory-causal.md, IOI/path-patching/causal-scrubbing framing at ~35%→~89% loss-recovery, component level). This paper adds a closed-form statistical-estimator characterization at the level of the head's actual output distribution, going beyond the hard-attention/exact-match limit that the induction-head literature the paper itself cites as prior work (Bietti et al. 2023; Nichani et al. 2024; Chen et al. 2024; Ekbote et al. 2026) was restricted to.

### 7
- **paper**: mi26-induction-heads-interpolate-ngrams.pdf
- **claim**: In the β→∞ limit with a specific reparameterization tying κ to β and a symmetric prior α, the BOS-augmented transformer estimator converges EXACTLY to add-α (Dirichlet-posterior-mean) smoothing of the empirical order-k transition counts — a precise Bayesian interpretation of what the BOS-token architectural convention computes.
- **numbers**: lim_{β→∞} T(x)(m) = (N_{u_T}^(T)(m) + α) / (N_{u_T}^(T) + α|V|) — Equation 10, with κ = kβ + ln(α|V|), β = β·1_k
- **quote**: Corollary 4.1 (Add-α-Type Smoothing via BOS Token). Set κ = kβ + ln(α|V|) and β = β1k for α = α1 with α > 0 (symmetric prior). The transformer estimator in Equation (8) implements add-α-type smoothing in the limit of β → ∞: lim_{β→∞} T(x)(m) = (N_uT^(T)(m) + α) / (N_uT^(T) + α|V|). ... Crucially, this add-α smoothing is enabled by the BOS token acting as a fixed, sequence-independent sink.
- **confidence**: high
- **conditions**: requires a BOS token prepended; κ and β tied via the stated reparameterization; symmetric Dirichlet prior α
- **locator**: Section 4.1, Corollary 4.1, Equation 10 (proof in Appendix D)
- **supersedes**: n/a — novel closed-form result connecting an architectural convention (BOS token) to a specific classical smoothing/Bayesian rule

### 8
- **paper**: mi26-induction-heads-interpolate-ngrams.pdf
- **claim**: At finite, uniform β (no BOS, κ=−∞), the estimator rewrites exactly in terms of CUMULATIVE (nested, partial/non-contiguous-match) counts K_M rather than exact-match counts N_M, with mixing parameter γ=e^β−1, and admits a hierarchical mixture-of-n-grams interpretation directly analogous to classical Jelinek–Mercer interpolation — but interpolating over cumulative counts rather than the contiguous suffix orders that JM smoothing uses.
- **numbers**: T(x)(m) = [Σ_{M⊆[k]} γ^{|M|} K_M^(T)(m)] / [Σ_{M⊆[k]} γ^{|M|} K_M^(T)] with γ=e^β−1 (Equation 12); classical JM: P_JM(m|u_T) = Σ_{i=0}^k λ_i p̂_i(m|u_T^(i)), Σλ_i=1 (Equation 11)
- **quote**: Lemma 4.1 (Sub-n-gram interpolation). The estimator in Equation (8) can be equivalently rewritten with parameter γ = e^β − 1 when κ = −∞, β = (β, . . . , β): T(x)(m) = Σ_{M⊆[k]} γ^{|M|} K_M^(T)(m) / Σ_{M⊆[k]} γ^{|M|} K_M^(T). ... The transformer implements an analogous scheme, but interpolates over cumulative counts rather than contiguous suffix orders.
- **confidence**: high
- **conditions**: κ=−∞ (no BOS contribution), β uniform across all k positions (β=(β,...,β))
- **locator**: Section 4.2, Lemma 4.1, Corollary 4.2, Equations 11-12
- **supersedes**: n/a — the paper's core mathematical contribution: identifies a genuinely new middle ground (cumulative/partial-match interpolation) between pure ML k-gram counting (the prior induction-head literature's hard-attention characterization) and classical contiguous-suffix Jelinek-Mercer interpolation

### 9
- **paper**: mi26-induction-heads-interpolate-ngrams.pdf
- **claim**: Trained transformers (both disentangled and standard architectures) empirically reproduce the predicted attention patterns and match or outperform fixed add-α baselines, especially in the hierarchical-Dirichlet setting where partial-context matches carry structured evidence; a minimal 2-parameter (β1, β2) hand construction already matches fully-trained transformer performance.
- **numbers**: qualitative only in extracted text — no numeric KL-divergence or accuracy values located; Figure 3 (hierarchical Dirichlet) is cited as showing 'all three model families track each other closely and substantially outperform every fixed add-α baseline'
- **quote**: Figure 3 shows all three model families track each other closely and substantially outperform every fixed add-α baseline (dashed). With only two trainable scalars β1, β2, the minimal construction already matches the fully trained transformers, supporting soft context matching as the key mechanism.
- **confidence**: medium
- **conditions**: independent-Dirichlet and hierarchical-Dirichlet order-k Markov chain tasks; T=64 sequence length (per the companion Figure 5 caption); construction vs. trained standard/disentangled transformer comparison
- **locator**: Section 5 (Empirical Validation), pdftotext lines ~2030-2080
- **supersedes**: n/a

### 10
- **paper**: mi26-sparsity-superposition-loss.pdf
- **claim**: For the one-layer tied-weight autoencoder with power activation ϕ(t)=t^m (m odd ≥1) and p-sparse inputs, the population reconstruction-gain L̃(W) obeys tight two-sided bounds — a general upper bound of order pd^m and a lower bound of order min(pd^m, dp^{1/m}) — tightened under strong log-concavity of the per-coordinate input distribution to an O(d) upper bound, yielding the combined bound min(pd^m, dp^{1/m}) ≲ sup_W L̃(W) ≲ min(pd^m, d).
- **numbers**: C1·min(p d^m, d p^{1/m}) ≤ sup_W L̃(W) ≤ C2·p d^m (general); sup_W L̃(W) ≤ C3·d under (K^{-1},K)-strong log-concavity of µ (density ∝ e^{-v(x)}, v''(x)∈[K^{-1},K]); combined: min(pd^m,dp^{1/m}) ≲ sup_W L̃(W) ≲ min(pd^m,d); valid for d>d0, n>d^m
- **quote**: Theorem 2.2. There are some constants C1, C2, C3, d0 depending only on m and µ such that the following holds for all d > d0 and n > d^m: 1. We have the bounds C1 min(pd^m, dp^{1/m}) ⩽ sup_W L̃(W) ⩽ C2 pd^m. 2. If in addition ... µ is (K^{−1}, K)-strongly log-concave ... then sup_W L̃(W) ⩽ C3 d, so that in combination with the above we have min(pd^m, dp^{1/m}) ≲ sup_W L̃(W) ≲ min(pd^m, d).
- **confidence**: high
- **conditions**: input x=(ξ1 b1,...,ξn bn), ξi~µ iid symmetric mean-zero with all finite moments, bi~Bernoulli(p) iid; tied-weight enc(x)=Wx, dec(y)=ϕ(W^T y); squared-L2 population loss; 'equal-importance' case only (all features equally important); log-concavity generalization (Remark 2.3/Theorem 3.2) does not require iid coordinates, only that (ξ1,...,ξn)~ν strongly log-concave and (b1,...,bn) arbitrary sparsity-pattern distribution
- **locator**: Section 2, Theorem 2.2 (proof occupies Sections 3-4); pdftotext lines ~200-235
- **supersedes**: Puts Elhage et al. (2022)'s empirically-motivated toy-model account of the superposition/sparsity loss tradeoff (the paper's own cited seminal reference) on a provably tight footing for power-activation autoencoders; upgrades a heuristic/empirical loss-curve picture into a proven two-sided bound with an explicit regime structure.

### 11
- **paper**: mi26-sparsity-superposition-loss.pdf
- **claim**: As a reference baseline, when the autoencoder is constrained to be 'unsuperposed' (A=W^TW diagonal, i.e. orthogonal feature directions, at most d nonzero), the optimal achievable population reconstruction-gain is exactly of order pd — establishing the no-superposition curve that the pd^m / d superposition bounds of Theorem 2.2 are measured against.
- **numbers**: sup_{unsuperposed W} L̃(W) = Θ(pd) (Equation 10), derived from L̃(W) = p·Σ_i[2µ_{m+1}·A_ii^m − µ_{2m}·A_ii^{2m}] = O(pd) via 2c1t^m−c2t^{2m} ≤ c1^2/c2 = O(1)
- **quote**: sup_{unsuperposed W} L̃(W) = Θ(pd).
- **confidence**: high
- **conditions**: A=W^TW constrained diagonal; rank A ≤ d (at most d of n diagonal entries nonzero); same p-sparse input model as Theorem 2.2
- **locator**: Section 2, Equations 9-10, pdftotext lines ~135-155
- **supersedes**: n/a — baseline derivation used as the comparison curve for Theorem 2.2

### 12
- **paper**: mi26-sparsity-superposition-loss.pdf
- **claim**: The 'very sparse' regime is governed by a first-order objective F(B)=tr(2B̃−B̃^2) over PSD matrices B of rank ≤ d (B̃ the entrywise m-th Hadamard power), which the paper proves is bounded by d^m via a rank argument on the m-fold tensor lift, achieved up to constants by an explicit construction; the paper's own schematic (Figure 2) places the regime transition between the pd^m-scaling ('very sparse') branch and the d-saturating branch at sparsity p between d^{-m} and d^{1-m}. The true tight order of sup_W L̃(W) across this transition is explicitly left as an OPEN PROBLEM — not resolved by this paper.
- **numbers**: F(B) = tr(2B̃−B̃^2) ≤ r ≤ rank(B̃) ≤ d^m (since B̃=Ṽ^T Ṽ with Ṽ∈R^{d^m×n} the m-fold tensor lift of V, where B=V^TV); Figure 2 schematic axis labels: p-axis marks d^{-m} and d^{1-m}, loss-axis marks d^{1/m} and d
- **quote**: Since, at least for small enough p, the first order should be dominant, this is an important objective to optimize, and the answer to this problem should dictate the very sparse limit. ... Consequently, r ⩽ d^m, and thus F(B) can be at most d^m. ... Perhaps the most interesting question is the true correct order of sup_W L̃(W), under natural conditions on µ. Note that our O(d) upper bound, which is really the only piece that we can expect to be loose, does not rely on the particular form of ϕ considered here.
- **confidence**: medium
- **conditions**: Figure 2 is explicitly stated by the authors to be 'purely schematic, since our results hide constants'; iid-coordinate + strong-log-concavity case only; the first-order-objective argument is heuristic ('at least for small enough p, the first order should be dominant') rather than a proven characterization of the exact crossover point
- **locator**: Section 2 (Figure 2), Section 4 (Eq. 23, first-order objective), Section 5 Open Problems items 1 and 3-4
- **supersedes**: n/a — presented by the authors as an open problem; the survey should not cite the pd^m-vs-d crossover location as resolved, only as a proven asymptotic regime structure with the precise transition point left open

## contradictions
No contradictions found among the three papers, and none found against the survey's existing (pre-2026) content directly. The closest thing to friction: paper 1's Corollary 9.5 does not contradict but sharply narrows the survey's likely framing (per method-inventory-dictionary.md §6.5, which discusses feature splitting/absorption and Matryoshka SAEs as mitigations) of SAE seed/width variability as an engineerable pathology — it is reframed as a proven structural non-identifiability of the standard objective that no width/seed/hyperparameter choice removes, with only one theorem-backed remedy (an explicit invariance penalty, Eq. 66) that trades off against reconstruction/cross-seed stability. Paper 2's closed-form estimator characterization of induction heads operates at a different level (statistical-estimator/output-distribution) than the survey's circuit-localization framing (IOI, path patching, causal scrubbing) and is complementary, not contradictory.

## gaps
Paper 1: the Gemma-2-2B numeric convergence exponent was not located in the extracted text (only GPT-2 small and Qwen3-8B-Base exponents were found verbatim); Theorem 9.2's intervention-calculus completeness is explicitly stated by the authors as empirically untested in this paper (Remark 9.4); whether sparsity and K-invariance are "jointly satisfiable in interesting regimes" is stated as open. Paper 2: no exact numeric KL-divergence or log-likelihood values for the "match or outperform add-α baselines" claim were found in the extracted text — only a qualitative statement referencing Figure 3/Figure 5, so the magnitude of outperformance is not transcribable from text alone; characterizing the population-loss-optimal β, κ parameters of Eq. 8 is stated as an explicit open question. Paper 3: the true tight order of sup_W L̃(W) across the pd^m-vs-d transition is explicitly unresolved (Open Problem 1); whether gradient descent actually converges to the (fairly involved) constructions that achieve the lower bound is explicitly flagged as unlikely/unresolved (Open Problem 4); the Figure 2 regime-boundary axis labels (p ~ d^{-m} to d^{1-m}) are presented by the authors as "purely schematic, since our results hide constants" — do not cite as a precise crossover formula.

## critic
{
 "sufficient": false,
 "missing": [
  "**The payload is truncated.** The `records` array is cut mid-string inside record 7 (`\"In the \u03b2\u2192\u221e limit with a specific reparameteriz`). Paper 3 (`mi26-sparsity-superposition-loss.pdf`) has **zero records** \u2014 it exists only as a sentence in `headline_finding`. For the half of the brief that asked for the loss-versus-sparsity functional form verbatim, nothing usable was returned.",
  "**Paper 3, everything.** All of the following is on p.2\u20135 of the PDF and none was transcribed: the loss decomposition `L(W) = E\u2016\u03d5(W^T W x) \u2212 x\u2016\u00b2 = pn\u03bc\u2082 \u2212 L\u0303(W)` (Eq. 6) with `L\u0303(W) := 2\u00b7E\u27e8x, \u03d5(W^T W x)\u27e9 \u2212 E\u2016\u03d5(W^T W x)\u2016\u00b2` (Eq. 7) \u2014 **`L\u0303` is not the loss, it is the term being maximized**, so the sign is inverted relative to the headline's phrasing; the model (tied weights `enc(x)=Wx`, `dec(y)=\u03d5(W^T y)`, `\u03d5(t)=t^m` with **m \u2a7e 1 odd integer**, `x=(\u03be\u2081b\u2081,\u2026,\u03be\u2099b\u2099)`, `\u03be\u223c\u03bc` symmetric mean-zero with all finite moments, `b\u223cBernoulli(p)` i.i.d., equal-importance, **no bias term**); the hypothesis conditions of Theorem 2.2 (**`d > d\u2080` and `n > d^m`**); the split of the two upper bounds (`C\u2082pd^m` unconditionally; `C\u2083d` **only** if \u03bc is `(K\u207b\u00b9,K)`-strongly log-concave); Remark 2.3's generalization (non-i.i.d. coordinates, arbitrary sparsity-pattern distribution).",
  "**Paper 3's baseline \u2014 the number that makes 'superposition helps' quantitative.** Eqs. (9)\u2013(10): for unsuperposed `W` (i.e. `A := W^T W` diagonal), `sup L\u0303(W) = \u0398(pd)`; the linear case `\u03d5(x)=x` gives `L\u0303(W) = p\u03bc\u2082\u00b7tr(2A \u2212 A\u00b2) \u2a7d p\u03bc\u2082\u00b7d`, also order `pd`. Without this the two-sided bound is uninterpretable \u2014 the *gain* from superposition is `min(pd^m, d)/pd`, i.e. up to `d^{m\u22121}` in the very sparse regime and capped at `1/p`. This is the derivable content the appendix actually needs.",
  "**Paper 3's numerics and their stated limits.** Figure 3: `d = 10, 15`, `m = 3`, `n = 6000`, plotting `log_d(L\u0303)` vs `log_d(p)`; caption states \"at small p the data suggests a linear relationship, as proved by the tight upper and lower bounds above in this case. **For larger p, the situation remains ambiguous.**\" The slope-1/3 lines are drawn to fit the data at `p = d^{-m}`, not fitted independently.",
  "**Paper 1: the Gemma-2-2B convergence exponent was declared unrecoverable and is in a table.** Raw-text lines ~2715\u20132745 give the full grid: GPT-2 small spectral **\u22120.286 \u00b1 0.007** / random **\u22120.290 \u00b1 0.011** (\u03ba\u2080 236.5 / 28.8; \u0394 3.0e\u22123 / 4.4e\u22123; Mmax/M0eig 0.04 / 3.03); Gemma-2-2B spectral **\u22120.329 \u00b1 0.024** / random **\u22120.240 \u00b1 0.025** (\u03ba\u2080 130.0 / 35.2; \u0394 3.4e\u22123 / 7.5e\u22123; 0.05 / 0.67); Qwen3-8B-Base spectral **\u22120.506 \u00b1 0.031** / random **\u22120.406 \u00b1 0.030** (\u03ba\u2080 53.2 / 117.9; \u0394 2.7e\u22123; 0.23 / 0.05). This changes the record: the predicted \u22121/2 is attained on **one of three** models and missed on two, and on GPT-2 the *random* dictionary converges at the same rate as the spectral one.",
  "**Paper 1: the invariance-penalty cost figures were declared unrecoverable and are in \u00a711.6 verbatim.** \u03b3: 0\u21921 at GPT-2 layer 8, width 4d = 3072, three seeds. Invariance residual 0.438 \u2192 0.333 (24%); split-half spectral distance 0.0170 \u2192 0.0101 (41%) at matched `L0 = 32`; **cost:** FVU 0.222 \u2192 0.255, live-feature fraction 0.77 \u2192 0.58, cross-seed mean-max-cosine between dictionaries **0.526 \u2192 0.428 (moves the wrong way)**, and at \u03b3 = 10 all three seeds collapse below the 4%-alive guard. **ReLU does not replicate the mechanism:** invariance residual 0.413 \u2192 0.435 at the guard-selected operating p
