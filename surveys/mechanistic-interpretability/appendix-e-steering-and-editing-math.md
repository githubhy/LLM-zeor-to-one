<!-- sec:E -->
## <a id="sec-E"></a>E Steering and editing mathematics

<a id="p-e-steering-and-editing-mathematics-1"></a><!-- para:e-steering-and-editing-mathematics-1 --> Derivations for § <!-- secxref:7 -->[§7](method-inventory-steering-editing.md#sec-7): why difference-in-means is the natural steering direction, and the closed-form ROME/MEMIT updates.

<!-- sec:E.1 -->
### <a id="sec-E.1"></a>E.1 Difference-in-means as a discriminant

<a id="p-e1-difference-in-means-as-a-discriminant-1"></a><!-- para:e1-difference-in-means-as-a-discriminant-1 --> Steering (Equation <!-- ref:7-1 -->[(1)](method-inventory-steering-editing.md#eq-1)) and the refusal direction (§ <!-- secxref:7.3 -->[§7.3](method-inventory-steering-editing.md#sec-7.3)) both use the class-mean difference $\mathbf{v} = \boldsymbol{\mu}^{+} - \boldsymbol{\mu}^{-}$. This is not arbitrary: under the Gaussian model with shared covariance $\Sigma$, the Bayes-optimal linear discriminant direction is $\Sigma^{-1}(\boldsymbol{\mu}^{+}-\boldsymbol{\mu}^{-})$, which reduces to the raw difference-in-means exactly when activations are whitened ($\Sigma \propto I$). So difference-in-means is the optimal separating direction in the isotropic case and a first-order approximation otherwise (<!-- secxref:Q.5 -->[§Q.5](appendix-q-reader-questions.md#sec-Q.5)) — the same object RepE's LAT (§ <!-- secxref:7.2 -->[§7.2](method-inventory-steering-editing.md#sec-7.2)) recovers as the top PCA component of paired differences. Adding $c\,\mathbf{v}$ moves the activation along the concept axis; **directional ablation** (Equation <!-- ref:7-2 -->[(2)](method-inventory-steering-editing.md#eq-2)) instead removes the component along $\hat{\mathbf{v}}$, i.e. projects onto the orthogonal complement, which is why it *disables* rather than *shifts* the behavior.

<!-- sec:E.2 -->
### <a id="sec-E.2"></a>E.2 ROME as a constrained least-squares update

<a id="p-e2-rome-as-a-constrained-least-squares-update-1"></a><!-- para:e2-rome-as-a-constrained-least-squares-update-1 --> Treat the MLP down-projection $W$ as a linear associative memory. ROME inserts $(\mathbf{k}_*, \mathbf{v}_*)$ by finding the update $\Delta = \hat W - W$ that satisfies the new association *exactly* while disturbing the memory's response to existing keys as little as possible. With $C = KK^{\top}$ the (uncentered) second moment of corpus keys, and $\mathbf{r} = \mathbf{v}_* - W\mathbf{k}_*$ the residual the update must supply, the problem is

<a id="eq-1"></a><!-- eq:E-1 -->
$$
\min_{\Delta}\ \tfrac12\,\mathrm{tr}\!\big(\Delta\, C\, \Delta^{\top}\big) \quad \text{subject to} \quad \Delta\,\mathbf{k}_* = \mathbf{r}. \tag{1}
$$

<a id="p-e2-rome-as-a-constrained-least-squares-update-2"></a><!-- para:e2-rome-as-a-constrained-least-squares-update-2 --> The objective penalizes the update in the metric of the key distribution (a large $\Delta$ along well-represented key directions disturbs many stored facts). Form the Lagrangian with multiplier vector $\boldsymbol{\lambda}$ and set the matrix derivative to zero:

<a id="eq-2"></a><!-- eq:E-2 -->
$$
\mathcal{J} = \tfrac12\,\mathrm{tr}\!\big(\Delta C\Delta^{\top}\big) - \boldsymbol{\lambda}^{\top}\big(\Delta\mathbf{k}_* - \mathbf{r}\big), \qquad \frac{\partial\mathcal{J}}{\partial\Delta} = \Delta C - \boldsymbol{\lambda}\,\mathbf{k}_*^{\top} = 0 \ \Rightarrow\ \Delta = \boldsymbol{\lambda}\,\mathbf{k}_*^{\top}C^{-1}. \tag{2}
$$

<a id="p-e2-rome-as-a-constrained-least-squares-update-3"></a><!-- para:e2-rome-as-a-constrained-least-squares-update-3 --> So $\Delta$ is **rank one** — an outer product. Substituting into the constraint $\Delta\mathbf{k}_* = \mathbf{r}$ solves for the multiplier, $\boldsymbol{\lambda} = \mathbf{r}\,/\,(\mathbf{k}_*^{\top}C^{-1}\mathbf{k}_*)$, and using $\mathbf{k}_*^{\top}C^{-1} = (C^{-1}\mathbf{k}_*)^{\top}$ (as $C$ is symmetric) recovers the closed form of Equation <!-- ref:7-3 -->[(3)](method-inventory-steering-editing.md#eq-3):

<a id="eq-3"></a><!-- eq:E-3 -->
$$
\hat W = W + \Lambda\,(C^{-1}\mathbf{k}_*)^{\top}, \qquad \Lambda = \frac{\mathbf{v}_* - W\mathbf{k}_*}{(C^{-1}\mathbf{k}_*)^{\top}\mathbf{k}_*}. \tag{3}
$$

<a id="p-e2-rome-as-a-constrained-least-squares-update-4"></a><!-- para:e2-rome-as-a-constrained-least-squares-update-4 --> The update direction $C^{-1}\mathbf{k}_*$ is the new key *whitened* by the inverse key covariance, which is what makes the edit minimally-disruptive; the scalar $\Lambda$ enforces $\hat W\mathbf{k}_* = \mathbf{v}_*$ exactly. This is a Sherman–Morrison-style rank-one memory write, and it is why the method is named **R**ank-**O**ne **M**odel **E**diting.

<!-- sec:E.3 -->
### <a id="sec-E.3"></a>E.3 MEMIT: batched, spread over layers

<a id="p-e3-memit-batched-spread-over-layers-1"></a><!-- para:e3-memit-batched-spread-over-layers-1 --> MEMIT <!-- cite:51 --> [[51]](references.md#ref-51) generalizes Equation <!-- ref:E-3 -->[(3)](#eq-3) two ways. **Batched:** insert $u$ facts at once by replacing the single constraint with $\Delta K_1 = R$ ($K_1$ the new keys, $R$ their residuals), whose weighted least-squares solution is a **rank-$u$** update $\Delta = R\,(C + K_1 K_1^{\top})^{-1}K_1$ (satisfying the constraints approximately, since $u$ exact constraints on one matrix are generally infeasible). **Spread:** rather than force the whole residual $\boldsymbol{\delta}_i = \mathbf{z}_i - \mathbf{h}_i^{L}$ into the last critical layer $L$, distribute it evenly across the critical range so each layer absorbs $\boldsymbol{\delta}_i/(L-\ell+1)$, keeping every layer's perturbation small. Small per-layer perturbations are why MEMIT tolerates ~10,000 edits where iterated single-layer ROME induces catastrophic forgetting far sooner (§ <!-- secxref:7.5 -->[§7.5](method-inventory-steering-editing.md#sec-7.5)).
