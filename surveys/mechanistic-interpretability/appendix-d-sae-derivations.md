<!-- sec:D -->
## <a id="sec-D"></a>D Sparse-autoencoder derivations

<a id="p-d-sparse-autoencoder-derivations-1"></a><!-- para:d-sparse-autoencoder-derivations-1 --> Derivations for § <!-- secxref:6 -->[§6](method-inventory-dictionary.md#sec-6): the objective, the shrinkage bias, and the variant activations and their gradients.

<!-- sec:D.1 -->
### <a id="sec-D.1"></a>D.1 The objective and the L1 shrinkage bias

<a id="p-d1-the-objective-and-the-l1-shrinkage-bias-1"></a><!-- para:d1-the-objective-and-the-l1-shrinkage-bias-1 --> The ReLU SAE minimizes reconstruction plus a decoder-norm-scaled L1 penalty (Equation <!-- ref:6-2 -->[(2)](method-inventory-dictionary.md#eq-2)). To see the **shrinkage** that motivates every variant, isolate one active feature $f_i$ with unit-norm decoder column and hold the others fixed; the objective in $f_i$ is a quadratic-plus-L1,

<a id="eq-1"></a><!-- eq:D-1 -->
$$
\min_{f_i \ge 0}\ \tfrac12\,(f_i - f_i^{\star})^2 + \lambda\,f_i, \tag{1}
$$

<a id="p-d1-the-objective-and-the-l1-shrinkage-bias-2"></a><!-- para:d1-the-objective-and-the-l1-shrinkage-bias-2 --> where $f_i^{\star}$ is the value that would minimize reconstruction error alone. The stationarity condition $f_i - f_i^{\star} + \lambda = 0$ gives the **soft-thresholding** solution

<a id="eq-2"></a><!-- eq:D-2 -->
$$
f_i = \max\!\big(f_i^{\star} - \lambda,\, 0\big), \tag{2}
$$

<a id="p-d1-the-objective-and-the-l1-shrinkage-bias-3"></a><!-- para:d1-the-objective-and-the-l1-shrinkage-bias-3 --> so every active feature is *shrunk* below its reconstruction-optimal magnitude by $\lambda$ — the same LASSO bias that makes L1 a magnitude penalty, not a count penalty. This is the pathology Gated, TopK, and JumpReLU each remove by applying the sparsity pressure to a *different* quantity than the reconstruction magnitude.

<!-- sec:D.2 -->
### <a id="sec-D.2"></a>D.2 Variant activations and their gradients

<a id="p-d2-variant-activations-and-their-gradients-1"></a><!-- para:d2-variant-activations-and-their-gradients-1 --> Let $\boldsymbol{\pi} = W_{\text{enc}}(\mathbf{x}-\mathbf{b}_{\text{dec}})+\mathbf{b}_{\text{enc}}$ be the pre-activation.

- <a id="p-d2-variant-activations-and-their-gradients-2"></a><!-- para:d2-variant-activations-and-their-gradients-2 --> **TopK** <!-- cite:11 --> [[11]](references.md#ref-11): $\mathbf{f} = \mathrm{TopK}_k(\boldsymbol{\pi})$ keeps the $k$ largest entries and zeros the rest. There is no L1 term, so the surviving $k$ activations are *not* shrunk, and $L_0 = k$ exactly. The gradient flows only through the selected coordinates (a hard mask); dead latents are revived by an auxiliary loss on the top-$k_{\text{aux}}$ dead latents reconstructing the residual error.
- **Gated** <!-- cite:10 --> [[10]](references.md#ref-10): a gate path $\boldsymbol{\pi}_{\text{gate}}$ carries the L1 penalty and produces a binary mask $H(\mathrm{ReLU}(\boldsymbol{\pi}_{\text{gate}}))$; an unpenalized magnitude path sets the value. With weight tying it collapses to a JumpReLU.
- **JumpReLU** <!-- cite:12 --> [[12]](references.md#ref-12): a learned per-feature threshold $\boldsymbol{\theta}$,

<a id="eq-3"></a><!-- eq:D-3 -->
$$
\mathbf{f} = \boldsymbol{\pi}\odot H(\boldsymbol{\pi}-\boldsymbol{\theta}), \qquad \mathcal{L} = \mathbb{E}\big[\lVert\mathbf{x}-\hat{\mathbf{x}}\rVert_2^2\big] + \lambda\sum_i H(\pi_i - \theta_i), \tag{3}
$$

<a id="p-d2-variant-activations-and-their-gradients-3"></a><!-- para:d2-variant-activations-and-their-gradients-3 -->   which penalizes $L_0$ *directly* (the count of active features) rather than an L1 proxy — and leaves surviving values unshrunk. The obstacle is that both the JumpReLU gate and the Heaviside $L_0$ term have a derivative that is a Dirac delta at the threshold (zero a.e.), so $\boldsymbol{\theta}$ gets no gradient. The fix is a **straight-through estimator**: the backward pass substitutes a smooth pseudo-derivative supported in an $\varepsilon$-window around the threshold,

<a id="eq-4"></a><!-- eq:D-4 -->
$$
\frac{\partial \hat H}{\partial \theta_i}\Big|_{\text{STE}} = -\frac{1}{\varepsilon}\,K\!\Big(\frac{\pi_i-\theta_i}{\varepsilon}\Big), \tag{4}
$$

<a id="p-d2-variant-activations-and-their-gradients-4"></a><!-- para:d2-variant-activations-and-their-gradients-4 -->   with $K$ a kernel — interpretable as a kernel-density estimate of the true gradient density, giving $\theta_i$ a usable training signal whenever a pre-activation lands near its threshold <!-- cite:12 --> [[12]](references.md#ref-12).

<a id="p-d2-variant-activations-and-their-gradients-5"></a><!-- para:d2-variant-activations-and-their-gradients-5 --> **Matryoshka** <!-- cite:14 --> [[14]](references.md#ref-14) adds nested-prefix reconstruction losses so early latents must independently reconstruct coarse structure, directly countering feature absorption/splitting (§ <!-- secxref:6.5 -->[§6.5](method-inventory-dictionary.md#sec-6.5)); **BatchTopK** <!-- cite:13 --> [[13]](references.md#ref-13) relaxes the per-token $k$ to a per-batch budget.

<!-- sec:D.3 -->
### <a id="sec-D.3"></a>D.3 The fidelity–sparsity frontier and evaluation

<a id="p-d3-the-fidelitysparsity-frontier-and-evaluation-1"></a><!-- para:d3-the-fidelitysparsity-frontier-and-evaluation-1 --> Every SAE lives on a Pareto frontier of reconstruction fidelity vs. $L_0$; the variants above *shift the frontier*, they do not escape it. Fidelity is reported as cross-entropy **loss recovered** (Equation <!-- ref:6-3 -->[(3)](method-inventory-dictionary.md#eq-3)) rather than raw MSE because MSE is not comparable across layers. TopK's joint scaling law (Equation <!-- ref:6-4 -->[(4)](method-inventory-dictionary.md#eq-4)) makes the frontier's dependence on dictionary size $n$ and sparsity $k$ explicit. The decisive lesson of § <!-- secxref:10 -->[§10](evaluation-and-metrics.md#sec-10) and § <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2) is that a favorable position on *this* frontier does not imply downstream usefulness — which is why disentanglement benchmarks (RAVEL, SAEBench) and direct task comparisons against difference-in-means baselines, not the frontier alone, are the current evaluation standard.
