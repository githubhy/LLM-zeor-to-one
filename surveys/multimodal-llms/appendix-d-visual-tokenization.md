<!-- sec:D -->
## <a id="sec-D"></a>D Visual tokenization: straight-through, EMA, and VQGAN

<a id="p-d-visual-tokenization-straight-through-ema-and-vqgan-1"></a><!-- para:d-visual-tokenization-straight-through-ema-and-vqgan-1 --> **Depth tier:** headline

<a id="p-d-visual-tokenization-straight-through-ema-and-vqgan-2"></a><!-- para:d-visual-tokenization-straight-through-ema-and-vqgan-2 --> Section <!-- secxref:4.11 -->[§4.11](method-inventory.md#sec-4.11) gave VQ-VAE's quantization (Eq 1 there) and three-term loss (Eq 2 there); this appendix supplies the two pieces that make discrete visual tokens actually trainable and actually sharp — the straight-through gradient that lets backprop cross the non-differentiable codebook lookup, and the perceptual-adversarial upgrade (VQGAN) that makes a few hundred tokens decode to a high-resolution image.

<!-- sec:D.1 -->
### <a id="sec-D.1"></a>D.1 The straight-through estimator

<a id="p-d1-the-straight-through-estimator-1"></a><!-- para:d1-the-straight-through-estimator-1 --> The quantization $z_q(x) = e_k$, $k=\arg\min_j\lVert z_e(x)-e_j\rVert$ is a hard nearest-neighbor lookup with *no gradient*: the $\arg\min$ is piecewise-constant, so $\partial z_q/\partial z_e = 0$ almost everywhere and the encoder would never receive a learning signal from the reconstruction loss. The straight-through estimator <!-- cite:16 -->[[16]](#ref-16) resolves this by *defining* the gradient to pass through the lookup unchanged — the decoder's gradient at its input $z_q$ is copied to the encoder's output $z_e$:

<a id="eq-1"></a><!-- eq:D-1 -->
$$
\frac{\partial \mathcal{L}_{\mathrm{rec}}}{\partial z_e(x)} \;:=\; \frac{\partial \mathcal{L}_{\mathrm{rec}}}{\partial z_q(x)} \tag{1}
$$

<a id="p-d1-the-straight-through-estimator-2"></a><!-- para:d1-the-straight-through-estimator-2 --> In code this is the one-line trick $z_q = z_e + \mathrm{sg}[e_k - z_e]$: the forward pass yields $e_k$ (the stop-gradient $\mathrm{sg}$ freezes the difference), while the backward pass sees $z_q = z_e$ and so routes the gradient straight to the encoder. The estimator is *biased* — it pretends the quantization is the identity — but in practice the encoder and decoder share the same $d$-dimensional space, so the copied gradient still points in a useful direction, and it works. The codebook itself, which Equation <!-- ref:D-1 -->[(1)](#eq-1) leaves untouched, is then learned by the second and third terms of the <!-- secxref:4.11 -->[§4.11](method-inventory.md#sec-4.11) loss: the codebook term pulls each code toward the encoder outputs assigned to it, and the commitment term ($\beta$) pulls encoder outputs toward their codes so the embedding space does not grow unboundedly.

<a id="p-d1-the-straight-through-estimator-3"></a><!-- para:d1-the-straight-through-estimator-3 --> **The stop-gradients are what make the three terms independent, and their placement is exact.** Writing the objective as printed <!-- cite:16 -->[[16]](#ref-16),

<a id="eq-2"></a><!-- eq:D-1b -->
$$
L = \log p(x \mid z_q(x)) + \big\lVert \operatorname{sg}[z_e(x)] - e \big\rVert_2^2 + \beta \big\lVert z_e(x) - \operatorname{sg}[e] \big\rVert_2^2 \tag{2}
$$

<a id="p-d1-the-straight-through-estimator-4"></a><!-- para:d1-the-straight-through-estimator-4 --> the operator $\operatorname{sg}$ "is defined as identity at forward computation time and has zero partial derivatives" <!-- cite:16 -->[[16]](#ref-16), so each squared term is a two-argument distance with **one argument frozen** — and which argument is frozen is what assigns the term to a parameter group. In term two the encoder output is frozen, so only the embeddings move; in term three the embedding is frozen, so only the encoder moves. The paper states the resulting partition exactly: "the decoder optimises the first loss term only, the encoder optimises the first and the last loss terms, and the embeddings are optimised by the middle loss term" <!-- cite:16 -->[[16]](#ref-16). Note that terms two and three are *the same distance* written twice with the freeze on opposite sides — not two different penalties. Without the stop-gradients they would collapse into a single term $(1+\beta)\lVert z_e - e\rVert^2$ pulling both arguments together at once, and the codebook could chase a drifting encoder into a degenerate solution. Splitting one distance into two one-sided pulls, with independent rates, is the whole mechanism.

<a id="p-d1-the-straight-through-estimator-5"></a><!-- para:d1-the-straight-through-estimator-5 --> That decoupling is also why $\beta$ is not delicate. It weights only the encoder's pull toward its code, and the source reports the algorithm "quite robust to $\beta$, as the results did not vary for values of $\beta$ ranging from 0.1 to 2.0", using $\beta = 0.25$ throughout while noting the right value "would depend on the scale of reconstruction loss" <!-- cite:16 -->[[16]](#ref-16) — a $20\times$ insensitive range, with the one stated caveat being a *scale* dependence rather than a tuning one. *[established]*

<a id="p-d1-the-straight-through-estimator-6"></a><!-- para:d1-the-straight-through-estimator-6 --> **Worked example — what the discretization actually buys.** For the source's ImageNet setting, a $128 \times 128 \times 3$ image at $8$ bits per channel is $128 \cdot 128 \cdot 3 \cdot 8 = 393{,}216$ bits. Its latent is a $32 \times 32$ field of indices into a codebook of $K = 512$, so each index costs $\log_2 512 = 9$ bits and the field costs $32 \cdot 32 \cdot 9 = 9{,}216$ bits. The ratio is $393{,}216 / 9{,}216 = 42.7$, matching the "reduction of $\ldots \approx 42.6$ in bits" the paper states <!-- cite:16 -->[[16]](#ref-16). The number worth carrying is the second one: **$1024$ tokens per image**, which is the figure <!-- secxref:6 -->[§6](multimodal-generation.md#sec-6) inherits and which every later tokenizer is trying to reduce.

<!-- sec:D.2 -->
### <a id="sec-D.2"></a>D.2 EMA codebook updates

<a id="p-d2-ema-codebook-updates-1"></a><!-- para:d2-ema-codebook-updates-1 --> A common alternative to learning the codebook by gradient on the second loss term is to update it as an **exponential moving average** of the encoder outputs assigned to each code. The source specifies this in its Appendix A.1 and flags in the main text that one "can alternatively also update the dictionary items as function of moving averages of $z_e(x)$", parenthetically noting it was "**not used for the experiments in this work**" <!-- cite:16 -->[[16]](#ref-16) — so the mechanism is the original paper's, while the empirical case for preferring it is not, a distinction worth keeping when the practice is described as standard.

<a id="p-d2-ema-codebook-updates-2"></a><!-- para:d2-ema-codebook-updates-2 --> **The target is a centroid, and the derivation starts there.** Let $\{z_{i,1},\dots,z_{i,n_i}\}$ be the $n_i$ encoder outputs currently closest to code $e_i$. The second loss term restricted to that code is $\sum_j \lVert z_{i,j} - e_i\rVert_2^2$, a sum of squared distances whose minimizer is available in closed form — differentiate and set to zero, giving

<a id="eq-3"></a><!-- eq:D-2-1 -->
$$
e_i = \frac{1}{n_i}\sum_{j=1}^{n_i} z_{i,j} \tag{3}
$$

<a id="p-d2-ema-codebook-updates-3"></a><!-- para:d2-ema-codebook-updates-3 --> the mean of the vectors assigned to it <!-- cite:16 -->[[16]](#ref-16). This is the $k$-means centroid step, and in classical terms exactly the Linde–Buzo–Gray vector-quantizer design rule — the signal-processing reading of <!-- secxref:4.11 -->[§4.11](method-inventory.md#sec-4.11) made literal. Equation <!-- ref:D-2-1 -->[(3)](#eq-3) cannot be applied directly under minibatch training, because $n_i$ and the assignment set are known only for the current batch. The online form keeps **two** exponentially-decayed accumulators per code — a count and a sum — with decay $\gamma \in (0,1)$:

<a id="eq-4"></a><!-- eq:D-2-2 -->
$$
N_i^{(t)} = \gamma\, N_i^{(t-1)} + (1-\gamma)\, n_i^{(t)}, \qquad m_i^{(t)} = \gamma\, m_i^{(t-1)} + (1-\gamma) \sum_{j} z_{i,j}^{(t)} \tag{4}
$$

<a id="p-d2-ema-codebook-updates-4"></a><!-- para:d2-ema-codebook-updates-4 --> and reads the code off as their ratio,

<a id="eq-5"></a><!-- eq:D-2-3 -->
$$
e_i^{(t)} = \frac{m_i^{(t)}}{N_i^{(t)}} \tag{5}
$$

<a id="p-d2-ema-codebook-updates-5"></a><!-- para:d2-ema-codebook-updates-5 --> with the source reporting $\gamma = 0.99$ to work well in practice <!-- cite:16 -->[[16]](#ref-16) — an effective window of $1/(1-\gamma) = 100$ minibatches.

<a id="p-d2-ema-codebook-updates-6"></a><!-- para:d2-ema-codebook-updates-6 --> **Why two accumulators and a division, rather than one EMA on the centroid?** This is the part that looks like bookkeeping and is not, and both reasons fall straight out of Equations <!-- ref:D-2-2 -->[(4)](#eq-4) and <!-- ref:D-2-3 -->[(5)](#eq-5). *First, it weights minibatches by evidence.* The obvious one-accumulator alternative, $e_i^{(t)} = \gamma e_i^{(t-1)} + (1-\gamma)\,\mathrm{mean}_j z_{i,j}^{(t)}$, gives a batch in which the code won a single vector the same influence as one in which it won five hundred; the ratio form does not, because the count rides in the denominator. That it converges to the right thing is immediate: hold $n_i$ and $\sum_j z_{i,j}$ fixed at $n$ and $S$, and the fixed point of Equation <!-- ref:D-2-2 -->[(4)](#eq-4) is $N_i^\star = n$, $m_i^\star = S$, so $e_i \to S/n$ — Equation <!-- ref:D-2-1 -->[(3)](#eq-3) recovered exactly. *Second, an unused code is handled with no special case at all.* If code $i$ wins nothing in step $t$, then $n_i^{(t)} = 0$ and the sum is empty, so **both** accumulators decay by the same factor $\gamma$ and the ratio is invariant:

<a id="eq-6"></a><!-- eq:D-2-4 -->
$$
e_i^{(t)} = \frac{\gamma\, m_i^{(t-1)}}{\gamma\, N_i^{(t-1)}} = e_i^{(t-1)} \tag{6}
$$

<a id="p-d2-ema-codebook-updates-7"></a><!-- para:d2-ema-codebook-updates-7 --> The entry is held exactly where it was rather than being pulled toward zero or left undefined — where the one-accumulator form would evaluate $0/0$ and need an explicit guard. That property is doing real work precisely in the failure mode this update is credited with mitigating: **codebook collapse**, the state in which most codes go unused. A code that is starving is exactly the code with $n_i^{(t)} = 0$ on most steps, and Equation <!-- ref:D-2-4 -->[(6)](#eq-6) says it neither drifts nor destabilizes while it waits. Note also what the whole construction removes: the codebook is no longer updated by a gradient at all, so the second loss term disappears from the objective and the codebook's adaptation rate is set by $\gamma$ rather than by the optimizer's learning rate and momentum — decoupled from the encoder's, which is the stability argument in one sentence. That EMA is consequently the default in most modern implementations is a claim about practice, not about the source, which as noted above did not run it. *[reported]*

<!-- sec:D.3 -->
### <a id="sec-D.3"></a>D.3 VQGAN: perceptual and adversarial losses

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-1"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-1 --> VQ-VAE's $L2$ reconstruction loss produces blurry images at high compression, because $L2$ rewards predicting the pixel-wise mean. VQGAN <!-- cite:17 -->[[17]](#ref-17) keeps the codebook and straight-through machinery and replaces the pixel loss with a **perceptual** loss (distance in a pretrained network's feature space, which tracks human-perceived similarity) plus an **adversarial** loss from a patch-based discriminator $D$ trained to tell real images from reconstructions. The full compression model is the saddle point

<a id="eq-7"></a><!-- eq:D-2 -->
$$
\mathcal{Q}^\star = \arg\min_{E,G,\mathcal{Z}}\,\max_{D}\;\mathbb{E}_{x\sim p(x)}\big[\mathcal{L}_{\mathrm{VQ}}(E,G,\mathcal{Z}) + \lambda\,\mathcal{L}_{\mathrm{GAN}}(\{E,G,\mathcal{Z}\}, D)\big] \tag{7}
$$

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-2"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-2 --> with $\mathcal{L}_{\mathrm{GAN}} = \log D(x) + \log(1-D(\hat{x}))$ and an adaptive weight $\lambda$ that balances the reconstruction and adversarial gradients.

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-3"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-3 --> **That weight is not a hyperparameter, and the reason is worth spelling out.** VQGAN sets it by a closed form recomputed every step <!-- cite:17 -->[[17]](#ref-17):

<a id="eq-8"></a><!-- eq:D-3 -->
$$
\lambda = \frac{\nabla_{G_L}\!\left[\mathcal{L}_{\mathrm{rec}}\right]}{\nabla_{G_L}\!\left[\mathcal{L}_{\mathrm{GAN}}\right] + \delta} \tag{8}
$$

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-4"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-4 --> where $\nabla_{G_L}[\cdot]$ is the gradient with respect to the decoder's **last layer** and $\delta = 10^{-6}$ guards the division <!-- cite:17 -->[[17]](#ref-17). Read Equation <!-- ref:D-3 -->[(8)](#eq-8) as a normalization rather than a weighting: multiplying the adversarial loss by the ratio of the two gradient magnitudes makes the adversarial contribution *arrive at the decoder with the same magnitude as the reconstruction contribution*, whatever those magnitudes happen to be. The balance is therefore held equal automatically across training, across resolutions, and across compression factors — none of which a fixed scalar could do, because a GAN loss's gradient scale moves by orders of magnitude as the discriminator gets better, while a reconstruction loss's does not. Two design details follow from the same reasoning. The gradient is taken at the last decoder layer because that is the one point both losses share and where their magnitudes are directly comparable; and $\delta$ matters most exactly when the discriminator is beaten, since $\nabla[\mathcal{L}_{\mathrm{GAN}}] \to 0$ there and an unguarded ratio would diverge — the stabilizer is doing real work in the regime the model is trying to reach, not merely guarding a measure-zero accident.

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-5"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-5 --> One caution for anyone reimplementing from the paper. The symbol $\mathcal{L}_{\mathrm{rec}}$ is used for two different quantities: the objective defines it as the plain squared error $\lVert x - \hat{x}\rVert^2$, while the text introducing Equation <!-- ref:D-3 -->[(8)](#eq-8) calls the same symbol "the perceptual reconstruction loss", after prose stating the $L_2$ loss was *replaced* by a perceptual one <!-- cite:17 -->[[17]](#ref-17). No intervening equation writes the perceptual form explicitly. The intended reading is clearly that $\mathcal{L}_{\mathrm{rec}}$ is perceptual everywhere after the replacement — but the printed equation is never updated to say so, and a reader implementing Equation <!-- ref:D-3 -->[(8)](#eq-8) from the displayed definitions alone would normalize against the wrong loss. The effect is decisive: the discriminator forces the decoder to produce *locally realistic* texture rather than a blurry mean, so a small codebook can encode a high-resolution image at quality an $L2$ autoencoder could not reach — which is precisely what makes discrete-token generation (§ <!-- secxref:6.1 -->[§6.1](multimodal-generation.md#sec-6.1)) viable. VQGAN then trains an autoregressive transformer over the codebook indices, $p(s)=\prod_i p(s_i\mid s_{<i})$ — the same next-token modeling Chameleon and Emu3 inherit, now over visual codes. This is the tokenizer that sits, often unnamed, beneath every discrete-AR generation model in § <!-- secxref:6 -->[§6](multimodal-generation.md#sec-6).
