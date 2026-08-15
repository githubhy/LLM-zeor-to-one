# Frontier cluster E1-circuit-critique

## key
E1-circuit-critique

## headline
The four papers form a coherent 2026 audit of activation patching / circuit discovery — the survey's "gold-standard causal primitive" — and every one of them finds a load-bearing problem the survey does not currently carry, plus (in three of four cases) a proposed correction rather than a call to abandon the method. (1) Circuits are noisier than the survey's framing implies: resampling variance is real but reducible by a better scoring rule (CEAP), while rephrasing/template variance is NOT reducible (not even by sparsity) and the authors argue a template-invariant "comprehensive task circuit" may be structurally unattainable — directly undercutting the survey's implicit assumption that a discovered circuit generalizes across phrasings of a task. (2) The standard NIE estimand silently conflates a component's true isolated effect (PIE) with an interaction term (INT) that the residual stream's skip connections guarantee is present for every mediator (a "recanting witness"); this single confound explains BOTH known false-negative pathologies at once (backup heads suppressed under NIE; context-only heads erased under PIE) — no exact fix scales, so the paper reframes INT as a diagnostic. (3) The survey already documents self-repair qualitatively (§10.2) but has no number for how badly naive single-ablation scoring fails at finding backups (ROC-AUC 0.33, worse than several existing self-repair-aware corrections) nor a method that fixes it — conditional co-ablation (CoAx) reaches 0.91 AUC and demonstrably repairs attribution, knockout, and pruning downstream. (4) No paper in the corpus the survey currently cites puts a statistically rigorous, monitoring-robust confidence interval on a patching/fidelity number at all; doing so shows a headline "μ̂≈0.96, looks solid" IOI-circuit fidelity claim is actually resting on a confidence interval 14x looser than necessary, and that method/metric differences the field treats as settled can be statistically indistinguishable at realistic sample sizes.

## records (15)

### 1
- **paper**: mi26-circuit-discovery-variance.pdf
- **claim**: EAP-IG circuits are unstable under dataset resampling; CEAP (a new conductance-based scoring method with a proven order-preservation guarantee IG lacks) achieves pairwise-Jaccard-index (PJI) circuit-overlap stability higher than or on par with EAP-IG, at matched unfaithfulness — i.e. resampling variance is real but a fixable property of the scoring rule.
- **conditions**: GPT-2 small, GPT-2 XL, Pythia-160M, Pythia-2.8B; SVA/IOI/greater-than tasks; full dataset ~10,000 samples subsampled into 4 non-overlapping 1,000-sample sub-datasets (6 pairwise PJIs per template/edge-count); PJI = |E1∩E2|/|E1∪E2|
- **numbers**: 4 sub-datasets → 6 PJI pairs per condition; no single aggregate % improvement reported in prose (results given per-figure across Appendix F, dozens of model×dataset×template plots)
- **quote**: We show that such an instability is ameliorated by CEAP... Overall, we find that CEAP achieves PJI values that are higher than, or at least on par with, those of EAP-IG. ... Note that CEAP attains unfaithfulness comparable to EAP-IG, so its increased stability in circuit selection does not arise from choosing task-irrelevant circuits.
- **confidence**: high
- **supersedes**: survey's method-inventory-causal.md §5.4 frames EAP-IG as the 'current practical default' with only a faithfulness caveat (0% IOI faithfulness fixed by EAP-IG's integrated-gradients path integral); it carries no resampling-stability claim or alternative — this is new 2026 content, not a correction to a wrong prior number.

### 2
- **paper**: mi26-circuit-discovery-variance.pdf
- **claim**: Rephrasing (template) variance is large and essentially unmitigated: different prompt templates for the *same task* activate largely disjoint circuits, forming two near-non-overlapping template clusters; the authors argue finding one template-invariant 'comprehensive task circuit' may be an unattainable goal, directly threatening the reliability of circuit-based steering on unseen phrasings.
- **conditions**: GPT-2 small (also replicated GPT-2 XL/Pythia-160M/Pythia-2.8B in Appendix G) on SVA; 1,000 samples across ~30 templates (single_0..plural_14 etc.); circuit size fixed so mean unfaithfulness across all 1,000 samples < 0.2; CEAP scoring
- **numbers**: two clearly separated template clusters in UMAP+PJI-matrix visualization; within-group PJI substantial, between-group PJI 'almost zero' (no single digit given in extractable text — likely only in the figure image)
- **quote**: In the right panel, two clearly separated template groups emerge. Circuits within each group exhibit substantial overlap, while overlap between the two groups is almost zero. ... it follows that identifying a comprehensive circuit for a particular task may be an unattainable goal. This implication challenges one of the central aspirations of mechanistic interpretability: that, by adjusting the identified task circuits, we can reliably steer the model's behavior on that task in our preferred direction.
- **confidence**: high
- **supersedes**: n/a — genuinely new finding; the survey's causal-methods inventory has no existing rephrasing/template-variance content to update.

### 3
- **paper**: mi26-circuit-discovery-variance.pdf
- **claim**: Sparse training (claimed elsewhere to yield more compact, interpretable task circuits) does NOT solve template-induced circuit variance: apparent convergence of cross-template circuits at higher sparsity is matched by an equally large rise in cross-TASK circuit overlap, implicating rising polysemanticity rather than genuine task-circuit convergence.
- **conditions**: sparse coding-model architectures from Bricken/whichever cited sparsity work (their Appendix I/J models, customized for code); two new datasets single-double-quote and else-elif; sparsity swept over nonzero-parameter counts 0.9M-14.8M
- **numbers**: cross-template avg. PJI increases +23.7% (else-elif) and +11.9% (single-double-quote) at highest sparsity; cross-task avg. PJI increases comparably, +11.9%
- **quote**: the overlap of different template circuits increases substantially when we allow fewer nonzero parameters. Nevertheless, the average PJI for circuit pairs across different tasks (cross-task) also increases to an extent comparable to the mean cross-template PJI for single-double-quote. This suggests that the level of polysemanticity increases with sparsity... Our current observations do not indicate that sparsity resolves the issue discussed in this section.
- **confidence**: high
- **supersedes**: n/a — new finding; forecloses a plausible-sounding fix (sparsity) before the survey adopts it.

### 4
- **paper**: mi26-circuit-discovery-variance.pdf
- **claim**: Sample-wise variance in unfaithfulness (previously flagged as a reliability problem) is largely BENIGN: extreme per-sample unfaithfulness scores are explained by 'selective contribution scaling' — samples whose total conductance mass is small have heavier-tailed edge-importance distributions, so a fixed-size circuit captures a smaller fraction of their score mass — not by defects in the discovered circuit.
- **conditions**: GPT-2 small and Pythia-160M; all templates of SVA/IOI/greater-than; correlations verified across all swept graph sizes; both per-sample and per-template-averaged scoring
- **numbers**: qualitative causal chain verified across all conditions: |Q_G^n|↓ → μ^n (normalized momentum, heavy-tailedness) ↑ → R^n(m) (score-mass ratio captured) ↓ → unfaithfulness Ū ↑; no single correlation coefficient reported in the extracted text
- **quote**: we argue that it is largely benign: extremely poor unfaithfulness scores often stem from how unfaithfulness is defined, rather than from defects in the measured circuits. We show that the magnitude of unfaithfulness is affected by selective contribution scaling, a neural mechanism that accounts for the extremely poor scores sometimes observed.
- **confidence**: medium
- **supersedes**: n/a — new mechanistic explanation; not previously modeled in the survey's evaluation-and-metrics.md.

### 5
- **paper**: mi26-multiple-mediators-patching.pdf
- **claim**: Activation patching's natural indirect effect (NIE) decomposes as NIE = PIE + INT, where INT is a genuine interaction effect (not noise) that is structurally guaranteed to be nonzero for every transformer mediator because the residual-stream skip connection creates a 'recanting witness' (a bypass route around whatever is patched).
- **conditions**: general transformer architecture argument (theoretical, Theorem 3.2), instantiated empirically on GPT-2 small, Pythia-70m, Qwen2.5-0.5B
- **numbers**: n/a (structural/theoretical claim)
- **quote**: The transformer residual stream guarantees this condition for every mediator by construction: the skip connection at each layer routes information directly from earlier components to later ones, around whatever activation is being patched... Activation patching computes NIE = PIE +INT, where PIE is the pure indirect effect... INT has been present in every activation patching study.
- **confidence**: high
- **supersedes**: survey's method-inventory-causal.md §5.1 calls activation patching 'the gold-standard causal primitive' with the only caveat being the self-repair/faithfulness note; it does not carry any interaction-effect confound — this is a structural critique the survey has never stated.

### 6
- **paper**: mi26-multiple-mediators-patching.pdf
- **claim**: NIE and PIE (patching-with-vs-without the interaction term) give substantially different component rankings, with the divergence tracking how dissimilar the clean and counterfactual prompts are; rank agreement is near-perfect for small perturbations and drops sharply for realistic corruption schemes used in standard circuit papers.
- **conditions**: 144 attention heads; GPT-2 small, Pythia-70m, Qwen2.5-0.5B; 5 tasks/corruption schemes from Hanna et al. 2024's repository; exact (non-approximated) activation patching, not attribution patching/IG
- **numbers**: ρ(NIE,PIE) = 0.989 (SVA), 0.826 (Gender Bias), 0.919 (IOI, symmetric ABBA/BABA token-swap corruption) at the high end; ρ = 0.509 (IOI, pABC corruption) and 0.517 (Greater-Than) at the low end
- **quote**: At the high end, ρ = 0.989 for SVA... 0.826 for Gender Bias... and 0.919 for IOI... with symmetric corruption... On the other hand, ρ = 0.509 for IOI with pABC corruption and 0.517 for Greater Than... which use counterfactuals that are more substantially different from the clean prompt.
- **confidence**: high
- **supersedes**: n/a — new quantitative finding; the survey has no rank-correlation-based critique of NIE.

### 7
- **paper**: mi26-multiple-mediators-patching.pdf
- **claim**: NIE systematically under-ranks the GPT-2 IOI backup name-mover heads (self-repair) because their negative INT suppresses NIE relative to PIE, and this suppression is a GROUP effect invisible to pairwise interaction terms — the same failure mode Wang et al. (2023) could only find via combinatorial ablation.
- **conditions**: GPT-2 small, IOI task, N=1,000 prompts (pABC distribution), mean ablation baseline; k=26 (Wang et al. circuit size); 8 documented backup name-mover heads (BNMH)
- **numbers**: 7 of 8 BNMH rank in the top-26 nodes under PIE; under NIE the same 8 heads spread across ranks 11-116; pairwise INT between L9H9 (top name-mover) and any individual BNMH reaches at most 7.1% of L9H9's individual INT; cross-interaction between a backup head and the FULL name-mover-head group is up to 3.8x higher than that pairwise figure
- **quote**: The PIE rankings for seven of the eight backup name mover heads fall within the top 26 nodes, where 26 is the size of the Wang et al. [2023] IOI circuit. Under NIE, the same nodes are spread across ranks 11 to 116. Pairwise interaction alone does not reveal the backup mechanism either. For example, pairwise INT between L9H9 and any individual BNMH head reaches at most 7.1% of L9H9's individual INT. However, cross-interaction between each backup name mover head and the full NMH group is up to 3.8× higher.
- **confidence**: high
- **supersedes**: directly extends survey's evaluation-and-metrics.md §10.2 self-repair passage (which states self-repair makes single-ablation a lower bound, qualitatively) with a mechanistic, quantitative explanation of WHY NIE-based ranking specifically misses backups, and shows it is a group- not pairwise-order effect.

### 8
- **paper**: mi26-multiple-mediators-patching.pdf
- **claim**: The 'obvious fix' of removing INT and ranking purely by PIE creates its own, opposite failure: components whose contribution is entirely interaction-mediated (context-specific heads with near-zero solo effect) are excluded from PIE-based circuits even though NIE correctly places them near the top — so neither estimand alone is safe, and there is no scalable exact correction (full combinatorial/recursive search is intractable), leading the authors to recommend treating INT as a diagnostic rather than eliminating it.
- **conditions**: GPT-2 small IOI, pABC corruption, k=26; Duplicate-Token (DTH), Previous-Token (PTH), Induction heads
- **numbers**: under signed-mean NIE ranking: 3 Induction heads at ranks 2, 6, 7; 2 DTH heads at ranks 5, 9; PTH L4H11 at rank 12 (all top-12, i.e. inside the circuit); under PIE ranking, all excluded except Induction L5H5 (PIE=+0.020) which barely enters at rank 19
- **quote**: At k = 26, signed NIEmean places three Induction heads at ranks 2, 6, and 7; two DTH heads at ranks 5 and 9; and PTH L4H11 at rank 12 — this group occupies the top half of the circuit. However, PIE rankings exclude all of them except Induction L5H5 (PIE = +0.020)... The only methods guaranteed to control for INTs will require full combinatorial or recursive search over mediators, rendering exact methods intractable for contemporary models of interest... we instead follow Ikram and VanderWeele [2015] in advocating that INTs be embraced as a useful analysis tool in its own right.
- **confidence**: high
- **supersedes**: n/a — new finding; also mechanistically explains prompt-level faithfulness-score instability the survey does not currently derive (cross-interaction xINT 'accounts for nearly the entire gap between what individual heads contribute and what the circuit produces jointly', e.g. mean ΣPIE=+5.78 vs mean ΣxINT=−4.05 under pABC).

### 9
- **paper**: mi26-conditional-co-ablation-self-repair.pdf
- **claim**: Standard first-order/single-ablation node scoring — the primitive underlying EAP-IG, AtP*, attribution patching, and Wanda-style pruning — is close to blind to self-repair backup heads (ROC-AUC 0.33, essentially the weakest baseline tested); even the strongest existing self-repair-aware correction (AtP* with gradient-dropout, designed specifically to counter self-repair cancellation) only reaches 0.82. Conditional co-ablation (CoAx), a label-free second-order score measuring how much a remaining unit's ablation effect GROWS once primaries are removed, reaches 0.91 — a statistically significant, non-marginal improvement.
- **conditions**: GPT-2-small (124M), IOI task, 8 documented backup name-mover heads out of 141 candidate heads, ground truth from Wang et al. (2023); mean±std over 4 prompt seeds (std ≤ 0.04 for backup-discovery numbers)
- **numbers**: single ablation 0.33±0.00; AtP 0.60±0.03; GIM-style (seed-free) 0.63±0.05; EAP-IG 0.70±0.02; AtP* GradDrop 0.82±0.03; CoAx 0.91±0.00 (Table 1); significance: label-permutation p<10⁻⁴; hypergeometric top-k test p=9×10⁻⁵ (6/8 backups in top-20 of 141); paired DeLong test vs fair same-seed baseline (seeded GIM 0.63) p=2×10⁻³
- **quote**: C OA X raises backup-head recovery from 0.33 to 0.91 ROC-AUC, outperforming all baselines, including self-repair-aware gradient scores (best 0.82)... Table 1 is the central result. Backup name-movers are hard for every node-ranking baseline we test, including those explicitly designed for self-repair... The gap is not about conditioning or a smarter gradient but the node-additive form itself: a backup's contribution is a non-additive substitution that no additive score, however corrected, can model.
- **confidence**: high
- **supersedes**: directly extends survey's evaluation-and-metrics.md §10.2, which states self-repair qualitatively (McGrath et al., Rushing & Nanda LayerNorm-rescaling/Anti-Erasure decomposition, Wang et al. IOI backups as 'the canonical instance') but carries NO quantitative measure of how badly standard scoring fails to find backups, and no correction method — CoAx supplies both.

### 10
- **paper**: mi26-conditional-co-ablation-self-repair.pdf
- **claim**: Self-repair masks the large majority of a component's true causal effect under naive attribution: ablating just the documented IOI name-mover primaries drops logit-difference by only 0.22 from a clean value of 2.53 (~91% of the effect hidden); re-attributing with the CoAx-recovered backups included recovers a 1.76 drop — exceeding both a matched-random top-up and even the hand-curated documented-backup set.
- **conditions**: GPT-2-small, IOI task, logit-difference metric, 4 seeds, clean value 2.53
- **numbers**: primaries-only drop 0.22 (4-seed mean; single-seed value 0.11); +random top-up 1.0±0.7; +documented backups 1.15; +CoAx backups 1.76 (Table 3)
- **quote**: ablating the primaries alone drops the logit-difference by only 0.22 (four-seed mean, clean 2.53; the single-seed value is 0.11...), because their backups absorb the damage. Re-attributing the same set together with the C OA X backups recovers a 1.76 drop (Table 3) – the effect the redundancy had hidden... it exceeds a matched random top-up (1.0±0.7) and even the curated documented backups (1.15) at every seed.
- **confidence**: high
- **supersedes**: quantifies, for the first time in this evidence set, exactly how large the self-repair masking effect is in the canonical IOI case the survey already cites — the survey's §10.2 states self-repair makes ablation a 'lower bound' but gives no magnitude.

### 11
- **paper**: mi26-conditional-co-ablation-self-repair.pdf
- **claim**: A capability knockout using only the documented first-order circuit fails to disable the behavior (self-repair fully masks it); adding the label-free CoAx-recovered backups is required to actually knock the capability out, matching a hand-curated oracle, while an equal-SIZE extension using the finder's own next-ranked heads overshoots into the core circuit — demonstrating the value is in identifying WHICH heads compensate, not merely ablating more of them.
- **conditions**: GPT-2-small, IOI task, task accuracy metric, 4 seeds
- **numbers**: primaries-only accuracy 1.00→0.97 (barely moved); +CoAx backups → 0.70; documented-backup oracle → 0.72; +own (finder's next-ranked heads, same count) → 0.24 (Table 4)
- **quote**: Ablating the documented name-mover primaries – the heads a first-order analysis would call 'the circuit' – barely dents IOI accuracy (1.00 → 0.97); the behavior survives, fully masked... Adding the label-free C OA X backups is what brings accuracy down to 0.70, matching the documented-backup oracle (0.72)... extending the ablation by the same number of the model's own next-ranked heads overshoots to 0.24, cutting past the backups into the core name-movers.
- **confidence**: high
- **supersedes**: n/a — new downstream consequence for capability-knockout/red-teaming use of circuits, not previously covered in the survey.

### 12
- **paper**: mi26-conditional-co-ablation-self-repair.pdf
- **claim**: The label-free CoAx procedure generalizes across scale (GPT-2 medium/large) and, for a second redundant circuit (induction), across 8 further models spanning 6 architecture families — but explicitly does NOT transfer well to the MLP-dominated greater-than circuit at head granularity, which the authors attribute to a property of that circuit rather than a limitation of the method.
- **conditions**: scale: GPT-2 small/medium/large, output-norm ratio of recovered set under primary ablation, 2 seeds (std ≤0.01); architecture: induction heads, GPT-2-small plus 8 further models/6 families; failure case: greater-than circuit (Hanna et al. 2023), FFN-group probe
- **numbers**: scale: output-norm ratio 1.15 (small), 1.05 (medium), 1.13 (large) vs ≈1.00 for rest of model; induction on GPT-2-small: conditional causal drop 0.89 vs 0.05 random; induction log-prob drop 8.5 vs matched-random, ~10x; across 8 further models, attribution factors 2.1x–12x over random; greater-than: FFN-group probe recovers only ~1.5x over random, within 1 std
- **quote**: On every size the recovered set wakes up when the primaries are ablated – its output-norm ratio is 1.15, 1.05, and 1.13 (small, medium, large)... seeding the documented induction heads returns a compensating set that is necessary only once the primaries are gone (conditional causal drop 0.89 versus 0.05 random)... adding the discovered compensators drops it by 8.5, about 10× the matched-random control. This holds on eight further models spanning six architecture families... the head-level signal does not transfer to the MLP-dominated greater-than circuit... (a preliminary FFN-group probe recovers only 1.5× over random, within one std), suggesting greater-than carries much weaker recoverable self-repair at this granularity – a property of the circuit, not the unit.
- **confidence**: high
- **supersedes**: n/a — new scope/limitation finding; relevant to the survey's cross-model generalization discussion (circuits-across-models.md §9.5, referenced by the existing self-repair passage as 'frontier-scale behavior is open').

### 13
- **paper**: mi26-certified-interventional-fidelity.pdf
- **claim**: Certified Interventional Fidelity (CIF) turns any interventional-interpretability metric (patching recovery, abstraction fidelity) into a bounded causal estimand with anytime-valid confidence sequences (valid under monitoring/early-stopping/adaptive sampling), and its variance-adaptive betting-sequence construction reduces the sample size needed to certify a given fidelity threshold by 10-30x versus the transparent-but-conservative Hoeffding construction.
- **conditions**: MNIST neural-abstraction benchmark and GPT-2 Small IOI circuits; i.i.d. and adaptive sampling; 1-δ=0.95
- **numbers**: 10-30x certification-cost reduction (headline, restated in both Abstract and §5 Discussion); worked MNIST example: 27.3x-28.8x speedup at specific k/method settings (Table 2 area, e.g. Var.-based method, radius 342 vs 6,888 samples)
- **quote**: We instantiate CIF with Hoeffding-style sequences and variance-adaptive betting sequences, the latter reducing certification cost by 10–30× in our experiments... Betting CSs (Section 3.4) adapt to the data and reduce certification cost by 10–30× in our experiments, from thousands of samples to a few hundred.
- **confidence**: high
- **supersedes**: n/a — the survey's evaluation-and-metrics.md §10 has no statistical-validity / confidence-sequence machinery at all for interventional claims; this is a wholly new addition to the evaluation section.

### 14
- **paper**: mi26-certified-interventional-fidelity.pdf
- **claim**: On the canonical GPT-2-Small IOI circuit-fidelity task, all four evaluated circuit-discovery methods (ACDC, attribution patching, AtP*, the hand-identified Wang et al. circuit) report similarly high point-estimate recovery, but the standard (Hoeffding) confidence interval used to back such a claim is far looser than necessary — the honestly-tightest (betting) interval certifies the same threshold with far fewer samples, and the full 13-head circuit's headline claim (μ≥0.95) is NOT even certifiable within the paper's 2,000-sample budget under the Hoeffding construction, only under betting.
- **conditions**: GPT-2 Small (124M, 12L×12H, 768-dim residual stream), IOI task, logit-difference recovery score Δ, i.i.d. patching, 1-δ=0.95, budget n≤2,000
- **numbers**: point estimates μ̂ ∈ [0.959, 0.972] across circuits; at n=2,000, Hoeffding CS half-width ≈0.070 vs betting CS half-width ≈0.005; full 13-head circuit: certifies μ≥0.90 at n=102 (betting) vs n=1,875 (Hoeffding); certifies μ≥0.95 at n=357 (betting) vs NOT certified within n=2,000 (Hoeffding); 3-head name-mover circuit alone certifies μ≥0.90 in 110 samples (betting); at n=2,000 fixed, betting lower bound ranges 0.953 (7-head circuit) to 0.966 (13-head circuit)
- **quote**: Figure 3 shows that all evaluated circuits have high recovery estimates, µ̂ ∈ [0.959, 0.972]. The distinction is inferential: at n = 2,000, Hoeffding radii are about 0.070, while betting radii are about 0.005... The full 13-head circuit certifies µ ≥ 0.90 at n = 102 and µ ≥ 0.95 at n = 357 under betting; under Hoeffding, the corresponding requirements are n = 1,875 and more than the 2,000-sample budget. Even the 3-head name-mover circuit certifies µ ≥ 0.90 in 110 samples under betting.
- **confidence**: high
- **supersedes**: the survey's method-inventory-causal.md §5.1 epistemic tag calls activation patching the 'gold-standard causal primitive' with an implied high-confidence fidelity claim; this paper shows the standard way such a claim is (or isn't) supported statistically is itself under-scrutinized, i.e. a new axis of critique the survey does not carry.

### 15
- **paper**: mi26-certified-interventional-fidelity.pdf
- **claim**: Whether two interventional-fidelity metric choices are statistically distinguishable depends on intervention strength: at mild perturbation the metrics agree within noise (no detectable difference), but at aggressive perturbation the same metrics diverge into non-overlapping confidence sequences — meaning a 'method A beats method B' or 'metric X vs Y' conclusion in circuit/patching evaluation can flip from indistinguishable to significant purely as a function of an under-disclosed design choice (intervention strength), which point estimates alone would not reveal.
- **conditions**: fixed model/circuit; corruption/mask-swap probability p ∈ {0.05, 0.1, 0.2, 0.5}; three discrepancy metrics (0-1 loss, clipped KL, clipped L2); 1-δ confidence sequences
- **numbers**: at p≤0.2: Fb ∈ [0.94, 0.99], CS width 0.067, overlapping across all 3 metrics; at p=0.5: 0-1 loss Fb=0.674 vs clipped-KL Fb=0.578, non-overlapping CSs, gap ≈0.03
- **quote**: At mild perturbation (p ≤ 0.2), the three metrics yield overlapping CSs: Fb ∈ [0.94, 0.99] with CS width 0.067, so metric choice has no statistically detectable effect. At p = 0.5, the metrics separate: the 0–1 loss gives Fb = 0.674 while the clipped KL gives Fb = 0.578, and their CSs do not overlap (gap ≈ 0.03). At aggressive perturbation levels, the choice of discrepancy function can therefore change qualitative conclusions.
- **confidence**: high
- **supersedes**: n/a — new finding; directly relevant to any survey guidance on choosing a patching/fidelity metric, which the survey does not currently caveat by intervention strength.

## critic
{
 "sufficient": false,
 "missing": [
  "ALL records for mi26-conditional-co-ablation-self-repair.pdf (zero returned). The brief explicitly asked 'does conditional co-ablation recover it?' and the answer exists only as unsourced prose in headline_finding. Recoverable now: single-ablation saliency 0.33 ROC-AUC, attribution patching 0.60, seeded GIM 0.63, EAP-IG 0.70, AtP* GradDrop 0.82, CoAx 0.91 +/- 0.00 (Table 1); means over 4 prompt seeds, std <= 0.04; 6 of 8 documented backups in top-20 of 141 candidates, top-10 recall 4/8; label-permutation p<1e-4, hypergeometric 6/8-in-top-20 p=9e-5, paired DeLong vs seeded GIM p=2e-3.",
  "The CoAx SEED CAVEAT, which inverts the headline: 'C OA X completes; it does not discover from scratch... as a standalone finder that must detect its own seed, C OA X peaks at 0.60 (Appendix C.5.1), below the seed-free AtP* (0.82). The 0.91 headline is thus a completion result with documented primaries as the seed, not standalone discovery.' Also the authors' own baseline flag: an input-side co-activation score reaches 0.92 AUC on IOI -- HIGHER than CoAx -- 'so C OA X is not the only signal that finds them' (it is correlational, collapses to 0.32 on duplicate-token vs CoAx 0.97, and over-ablates as a completion signal).",
  "CoAx generalization evidence: IOI backups replicate across the GPT-2 family; label-free induction completion on 8 models from 6 families (GPT-2-S/L, Pythia-160M/410M/1.4B, Llama-3.1-8B, OLMo-2-7B, Qwen2.5-7B); repair-aware structured pruning beats every weight/magnitude/gradient baseline at 50% sparsity at every scale 124M-7B (WikiText-2 ppl). Ablation-value robustness: CoAx AUC 0.87-0.92 across four ablation values while single-ablation stays 0.33-0.39. Cost: conditional route 2|U|+1 forwards, 0 backwards, label-free, ~36x cheaper than the pairwise route.",
  "ALL records for mi26-certified-interventional-fidelity.pdf (zero returned). The brief explicitly asked what CIF certifies statistically and what the anytime-valid guarantee is. Recoverable: CIF writes the reported quantity as a causal estimand (expectation of a bounded score over a STATED input distribution and a STATED intervention distribution), then supplies fixed-budget Hoeffding CIs and anytime-valid confidence sequences (Theorem 1) valid under continuous monitoring and optional stopping, plus bounded-mixture importance weighting (b_n^IS with 1/(1-alpha) factor, delta_n = 6*delta/(pi^2 n^2)) so adaptive intervention sampling does not break coverage; ONS betting strategy for the variance-adaptive sequence; E4 is an explicit coverage-validation experiment.",
  "CIF Table 3 (GPT-2 Small IOI, i.i.d., 1-delta=0.95): mu-hat by circuit size = 3 heads 0.964, 7 heads 0.959, 9 heads 0.970, 11 heads 0.971, 13 heads 0.972; n to certify mu>=0.90 under betting = 110/118/104/104/102 vs Hoeffding 'not certified'/'not certified'/1973/1954/1875; n to certify mu>=0.95 under betting = 840/1545/413/369/357, none certified under Hoeffding within n=2000. Betting lower confidence bound ranges 0.953 (7-head) to 0.966 (13-head), 'suggesting diminishing returns after the core name-mover heads are included.' This is the survey-relevant result and it is absent.",
  "CIF Table 2 certification speedups (p=0.1, k=256): 13.1x-28.8x, with the negative results the abstract omits -- hard pruning NEVER certifies; several rows '--' (not certified within budget); adaptive mixture sampling roughly DOUBLES cost in the high-fidelity regime (131 vs 64 samples), i.e. adaptive proposals help find failures, not certify high fidelity. Also E1's actual indistinguishability instance: soft-intervention vs random pruning at k=256, estimated difference -0.033 with Hoeffding radius 0.067 and betting radius 0.016.",
  "Proposition 3.1(a)/(b) of the mediators paper -- the single most actionable result in the pass and entirely absent: 'Denoising computes PIE'; 'Noising computes NIE = PIE + INT'; TE = PIE + PDE + INT. The noising-vs-denoising choice IS the PIE-vs-NIE choice. 
