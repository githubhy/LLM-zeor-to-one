<!-- sec:D -->
## <a id="sec-D"></a>D Visual tokenization: straight-through, EMA, and VQGAN

<a id="p-d-visual-tokenization-straight-through-ema-and-vqgan-1"></a><!-- para:d-visual-tokenization-straight-through-ema-and-vqgan-1 --> Section <!-- secxref:4.11 -->[§4.11](method-inventory.md#sec-4.11) gave VQ-VAE's quantization (Eq 1 there) and three-term loss (Eq 2 there); this appendix supplies the two pieces that make discrete visual tokens actually trainable and actually sharp — the straight-through gradient that lets backprop cross the non-differentiable codebook lookup, and the perceptual-adversarial upgrade (VQGAN) that makes a few hundred tokens decode to a high-resolution image.

<!-- sec:D.1 -->
### <a id="sec-D.1"></a>D.1 The straight-through estimator

<a id="p-d1-the-straight-through-estimator-1"></a><!-- para:d1-the-straight-through-estimator-1 --> The quantization $z_q(x) = e_k$, $k=\arg\min_j\lVert z_e(x)-e_j\rVert$ is a hard nearest-neighbor lookup with *no gradient*: the $\arg\min$ is piecewise-constant, so $\partial z_q/\partial z_e = 0$ almost everywhere and the encoder would never receive a learning signal from the reconstruction loss. The straight-through estimator <!-- cite:16 -->[[16]](#ref-16) resolves this by *defining* the gradient to pass through the lookup unchanged — the decoder's gradient at its input $z_q$ is copied to the encoder's output $z_e$:

<a id="eq-1"></a><!-- eq:D-1 -->
$$
\frac{\partial \mathcal{L}_{\mathrm{rec}}}{\partial z_e(x)} \;:=\; \frac{\partial \mathcal{L}_{\mathrm{rec}}}{\partial z_q(x)} \tag{1}
$$

<a id="p-d1-the-straight-through-estimator-2"></a><!-- para:d1-the-straight-through-estimator-2 --> In code this is the one-line trick $z_q = z_e + \mathrm{sg}[e_k - z_e]$: the forward pass yields $e_k$ (the stop-gradient $\mathrm{sg}$ freezes the difference), while the backward pass sees $z_q = z_e$ and so routes the gradient straight to the encoder. The estimator is *biased* — it pretends the quantization is the identity — but in practice the encoder and decoder share the same $d$-dimensional space, so the copied gradient still points in a useful direction, and it works. The codebook itself, which Equation <!-- ref:D-1 -->[(1)](#eq-1) leaves untouched, is then learned by the second and third terms of the § 4.11 loss: the codebook term pulls each code toward the encoder outputs assigned to it, and the commitment term ($\beta$) pulls encoder outputs toward their codes so the embedding space does not grow unboundedly.

<!-- sec:D.2 -->
### <a id="sec-D.2"></a>D.2 EMA codebook updates

<a id="p-d2-ema-codebook-updates-1"></a><!-- para:d2-ema-codebook-updates-1 --> A common alternative to learning the codebook by gradient on the second loss term is to update it as an **exponential moving average** of the encoder outputs assigned to each code <!-- cite:16 -->[[16]](#ref-16): each codebook entry drifts toward the running mean of the encoder vectors that most recently selected it, with a decay that smooths the estimate. This replaces the codebook-loss gradient with a $k$-means-like online centroid update and is, in classical terms, exactly the Linde-Buzo-Gray vector-quantizer design rule run online — the signal-processing reading of § 4.11 made literal. EMA updates tend to be more stable and to reduce codebook collapse (the failure where most codes go unused), which is why they are the default in most modern implementations.

<!-- sec:D.3 -->
### <a id="sec-D.3"></a>D.3 VQGAN: perceptual and adversarial losses

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-1"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-1 --> VQ-VAE's $L2$ reconstruction loss produces blurry images at high compression, because $L2$ rewards predicting the pixel-wise mean. VQGAN <!-- cite:17 -->[[17]](#ref-17) keeps the codebook and straight-through machinery and replaces the pixel loss with a **perceptual** loss (distance in a pretrained network's feature space, which tracks human-perceived similarity) plus an **adversarial** loss from a patch-based discriminator $D$ trained to tell real images from reconstructions. The full compression model is the saddle point

<a id="eq-2"></a><!-- eq:D-2 -->
$$
\mathcal{Q}^\star = \arg\min_{E,G,\mathcal{Z}}\,\max_{D}\;\mathbb{E}_{x\sim p(x)}\big[\mathcal{L}_{\mathrm{VQ}}(E,G,\mathcal{Z}) + \lambda\,\mathcal{L}_{\mathrm{GAN}}(\{E,G,\mathcal{Z}\}, D)\big] \tag{2}
$$

<a id="p-d3-vqgan-perceptual-and-adversarial-losses-2"></a><!-- para:d3-vqgan-perceptual-and-adversarial-losses-2 --> with $\mathcal{L}_{\mathrm{GAN}} = \log D(x) + \log(1-D(\hat{x}))$ and an adaptive weight $\lambda$ that balances the reconstruction and adversarial gradients. The effect is decisive: the discriminator forces the decoder to produce *locally realistic* texture rather than a blurry mean, so a small codebook can encode a high-resolution image at quality an $L2$ autoencoder could not reach — which is precisely what makes discrete-token generation (§ <!-- secxref:6.1 -->[§6.1](multimodal-generation.md#sec-6.1)) viable. VQGAN then trains an autoregressive transformer over the codebook indices, $p(s)=\prod_i p(s_i\mid s_{<i})$ — the same next-token modeling Chameleon and Emu3 inherit, now over visual codes. This is the tokenizer that sits, often unnamed, beneath every discrete-AR generation model in § <!-- secxref:6 -->[§6](multimodal-generation.md#sec-6).
