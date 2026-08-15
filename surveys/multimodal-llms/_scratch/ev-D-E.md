# Evidence extraction — Visual Tokenization & Unified Generation (Appendices D–E)

Sources read: download/vandenoord-vqvae-2017.pdf, download/esser-vqgan-2021.pdf,
download/zhou-transfusion-2024.pdf, download/team-chameleon-2024.pdf,
download/ho-ddpm-2020.pdf

---

## Q1 — VQ-VAE objective (vandenoord-vqvae-2017)

- **Posterior categorical distribution (nearest-neighbour lookup)** —
  $$q(z=k|x) = \begin{cases} 1 & \text{for } k = \operatorname{argmin}_j \lVert z_e(x) - e_j \rVert_2 \\ 0 & \text{otherwise} \end{cases}$$
  — *source:* `vandenoord-vqvae-2017.pdf` Eq. 1, p.3 — *quality:* verbatim

- **Quantization mapping** — $z_q(x) = e_k, \quad \text{where } k = \operatorname{argmin}_j \lVert z_e(x) - e_j \rVert_2$ — *source:* `vandenoord-vqvae-2017.pdf` Eq. 2, p.3 — *quality:* verbatim

- **Full three-term loss (reconstruction + codebook (VQ) + commitment)** —
  $$L = \log p(x|z_q(x)) + \lVert \operatorname{sg}[z_e(x)] - e \rVert_2^2 + \beta \lVert z_e(x) - \operatorname{sg}[e] \rVert_2^2$$
  — *source:* `vandenoord-vqvae-2017.pdf` Eq. 3, p.4 — *quality:* verbatim

- **Stop-gradient placement, exact** — Term 1 (reconstruction): no `sg` — uses $z_q(x)$ directly (the decoder input) inside $\log p(x|z_q(x))$. Term 2 (codebook/VQ loss): `sg` wraps the **encoder output** $z_e(x)$ — i.e. $\lVert \operatorname{sg}[z_e(x)] - e \rVert_2^2$ — so only the embeddings $e$ receive gradient from this term. Term 3 (commitment loss): `sg` wraps the **embedding** $e$ — i.e. $\lVert z_e(x) - \operatorname{sg}[e] \rVert_2^2$ — so only the encoder output $z_e(x)$ receives gradient from this term. — *source:* `vandenoord-vqvae-2017.pdf` Eq. 3 + surrounding text, p.4 — *quality:* verbatim (equation) / paraphrase (placement description)

- **`sg` operator definition** — "sg stands for the stopgradient operator that is defined as identity at forward computation time and has zero partial derivatives, thus effectively constraining its operand to be a non-updated constant." — *source:* `vandenoord-vqvae-2017.pdf` p.4, text immediately below Eq. 3 — *quality:* verbatim

- **Which loss term trains which parameters** — "The decoder optimises the first loss term only, the encoder optimises the first and the last loss terms, and the embeddings are optimised by the middle loss term." — *source:* `vandenoord-vqvae-2017.pdf` p.4 — *quality:* verbatim

- **β commitment coefficient — value used** — $\beta = 0.25$ in all experiments — *source:* `vandenoord-vqvae-2017.pdf` p.4 — *quality:* verbatim

- **Paper's robustness-to-β statement** — "We found the resulting algorithm to be quite robust to β, as the results did not vary for values of β ranging from 0.1 to 2.0. We use β = 0.25 in all our experiments, although in general this would depend on the scale of reconstruction loss." — *source:* `vandenoord-vqvae-2017.pdf` p.4 — *quality:* verbatim

- **Straight-through estimator statement (exact gradient-copy mechanism)** — "Note that there is no real gradient defined for equation 2, however we approximate the gradient similar to the straight-through estimator [3] and just copy gradients from decoder input $z_q(x)$ to encoder output $z_e(x)$. One could also use the subgradient through the quantisation operation, but this simple estimator worked well for the initial experiments in this paper." — *source:* `vandenoord-vqvae-2017.pdf` §3.2, p.3–4 — *quality:* verbatim

- **What is being approximated** — The paper states explicitly only that "there is no real gradient defined for equation 2" (the nearest-neighbour quantization $z_q(x)=e_k$) and that the straight-through copy is an approximation *of that gradient* — it does not use further qualifying language (e.g. "approximates the gradient of the quantization operation"). No additional claim (such as an approximation to a specific alternative estimator) is made beyond citing [3] (Bengio et al., straight-through estimator) and noting the subgradient alternative was not used. — *source:* `vandenoord-vqvae-2017.pdf` §3.2, p.3–4 — *quality:* paraphrase (of scope; underlying sentence quoted above is verbatim)

- **Codebook size K and latent field size — ImageNet 128×128×3 experiment** — $z = 32\times32\times1$ discrete space with $K=512$; "So a reduction of $\frac{128\times128\times3\times8}{32\times32\times9} \approx 42.6$ in bits." Figure 2 caption confirms: "reconstructions from a VQ-VAE with a 32x32x1 latent space, latent space, with K=512." — *source:* `vandenoord-vqvae-2017.pdf` §4.2, p.5 — *quality:* verbatim

- **Codebook size/field for CIFAR10 (§4.1 comparison experiment)** — "we use a field of 32 x 32 latents for ImageNet, or 8 x 8 x 10 for CIFAR10" (N discrete latents referenced generically here; K value not restated in this sentence — see K=512 used in the ImageNet/DM-Lab examples above and below). — *source:* `vandenoord-vqvae-2017.pdf` §3.2 (N discrete latents remark) and §4.1, p.4–5 — *quality:* verbatim (field sizes) / note (K not restated at this specific sentence)

- **Second-stage DM-Lab codebook** — "We use only three latent variables (each with K=512 and their own embedding space e) at the second stage for modelling the whole image ... compressing the image onto 3 x 9 bits." — *source:* `vandenoord-vqvae-2017.pdf` p.6 — *quality:* verbatim

- **Embedding dimensionality $D$ (numeric value)** — NOT FOUND in `vandenoord-vqvae-2017.pdf` pp.1–6 (main text). §3.1 defines the embedding space abstractly as $e \in \mathbb{R}^{K\times D}$ (Eq. context, p.3) but no experiment section on these pages states a numeric value for $D$; only the spatial field size (e.g. 32×32×1) and $K$ (e.g. 512) are given for the reported experiments. — *source:* `vandenoord-vqvae-2017.pdf` §3.1 p.3, §4.1–4.2 pp.4–6 — *quality:* verbatim (absence noted, not approximated)

- ⚠️ **DEFECT / note** — none identified in the transcribed equations/text on these pages; Eq. 3's dimensional structure (reconstruction log-likelihood term added to two squared-$\ell_2$ penalty terms) is as printed, no inconsistency observed.


---

## Q2 — VQGAN additions (esser-vqgan-2021)

- **Quantization (element-wise, per spatial code)** —
  $$z_{\mathbf q} := \mathbf q(\hat z) := \left( \operatorname{argmin}_{z_k \in \mathcal Z} \lVert \hat z_{ij} - z_k \rVert \right) \in \mathbb R^{h\times w \times n_z}$$
  — *source:* `esser-vqgan-2021.pdf` Eq. 2, p.4 — *quality:* verbatim

- **Reconstruction map** — $\hat x = G(z_{\mathbf q}) = G(\mathbf q(E(x)))$ — *source:* `esser-vqgan-2021.pdf` Eq. 3, p.4 — *quality:* verbatim

- **VQ loss $\mathcal L_{VQ}$ (base, pre-GAN term)** —
  $$\mathcal L_{VQ}(E,G,\mathcal Z) = \lVert x-\hat x \rVert^2 + \lVert \operatorname{sg}[E(x)] - z_{\mathbf q}\rVert_2^2 + \lVert \operatorname{sg}[z_{\mathbf q}] - E(x) \rVert_2^2$$
  "Here, $\mathcal L_{rec} = \lVert x-\hat x \rVert^2$ is a reconstruction loss, sg[·] denotes the stop-gradient operation, and $\lVert \operatorname{sg}[z_{\mathbf q}]-E(x)\rVert_2^2$ is the so-called 'commitment loss' [72]." — *source:* `esser-vqgan-2021.pdf` Eq. 4, p.4 — *quality:* verbatim

- ⚠️ **DEFECT / notational inconsistency** — The prose immediately before Eq. 4's section header states "we replace the $L_2$ loss used in [72] by a perceptual loss" (p.4, "Learning a Perceptually Rich Codebook" paragraph), yet Eq. 4 as printed still labels the first term $\mathcal L_{rec} = \lVert x - \hat x\rVert^2$ — the literal L2 form, not a labeled perceptual-loss expression. The perceptual substitution is only made explicit later and indirectly, in the adaptive-weight definition (Eq. 7) where the paper writes "$\mathcal L_{rec}$ is the perceptual reconstruction loss [81]" — i.e. the same symbol $\mathcal L_{rec}$ is silently overloaded between an $L_2$ definition (Eq. 4) and a perceptual (LPIPS, ref [81]) definition (Eq. 7 prose), with no intervening equation showing the perceptual form explicitly. — *source:* `esser-vqgan-2021.pdf` p.4 (prose above Eq. 4; Eq. 4; Eq. 7 prose) — *quality:* verbatim quotes, paraphrase of the inconsistency

- **Adversarial (patch-based discriminator) loss** —
  $$\mathcal L_{GAN}(\{E,G,\mathcal Z\}, D) = [\log D(x) + \log(1-D(\hat x))]$$
  — *source:* `esser-vqgan-2021.pdf` Eq. 5, p.4 — *quality:* verbatim

- **Complete objective (min-max over VQ + GAN, with adaptive weight $\lambda$)** —
  $$\mathcal Q^* = \operatorname*{argmin}_{E,G,\mathcal Z}\ \max_D\ \mathbb E_{x\sim p(x)}\big[\mathcal L_{VQ}(E,G,\mathcal Z) + \lambda \mathcal L_{GAN}(\{E,G,\mathcal Z\},D)\big]$$
  — *source:* `esser-vqgan-2021.pdf` Eq. 6, p.4 — *quality:* verbatim

- **Adaptive weight $\lambda$ — exact closed form with $\delta$ stabilizer** —
  $$\lambda = \frac{\nabla_{G_L}[\mathcal L_{rec}]}{\nabla_{G_L}[\mathcal L_{GAN}] + \delta}$$
  "where $\mathcal L_{rec}$ is the perceptual reconstruction loss [81], $\nabla_{G_L}[\cdot]$ denotes the gradient of its input w.r.t. the last layer $L$ of the decoder, and $\delta = 10^{-6}$ is used for numerical stability." — *source:* `esser-vqgan-2021.pdf` Eq. 7, p.4 — *quality:* verbatim

- **Backprop through non-differentiable quantization** — "Backpropagation through the non-differentiable quantization operation in Eq. (3) is achieved by a straight-through gradient estimator, which simply copies the gradients from the decoder to the encoder [3], such that the model and codebook can be trained end-to-end via the loss function" (leading into Eq. 4). — *source:* `esser-vqgan-2021.pdf` p.4 — *quality:* verbatim

- **Compression factor $f$ definition** — "We specify the amount of context encoded in terms of reduction factor in the side-length between image inputs and the resulting representations, i.e. a first stage encoding images of size $H\times W$ into discrete codes of size $H/f \times W/f$ is denoted by a factor $f$." "For $f=1$, we reproduce the approach of [8] and replace our VQGAN by a k-means clustering of RGB values with $k=512$." — *source:* `esser-vqgan-2021.pdf` §4.3, p.6 — *quality:* verbatim

- **Compression factors actually used / compared** — $f=1$ (pixel-space k-means baseline reproduction, $k=512$); $f=2$ (comparison of transformer-on-pixels vs. transformer-on-VQGAN-latent, CIFAR10, latent code size $16\times16=256$, "18.63% improvement in FID and $14.08\times$ faster sampling"); $f=8$ ("the overall structure of images can be approximated, but inconsistencies of facial features ... and of viewpoints ... arise"); $f=16$ ("Only our full setting of $f=16$ can synthesize high-fidelity samples") — the paper's main/full setting. — *source:* `esser-vqgan-2021.pdf` §4.3–4.4, pp.6–7 — *quality:* verbatim (quoted claims) / paraphrase (list assembly)

- **Resulting token count per image (main setting)** — Codebook size $|\mathcal Z| = 1024$ ("Based on initial experiments, we usually set $|\mathcal Z|=1024$"); transformer trained "to predict sequences of length $16\cdot 16$" — i.e. **256 tokens/image**, consistent with "image size $256\times256$, latent size $16\times16$" used in §4.1/§4.2 (implying $f = 256/16 = 16$). Training crops for a factor-$f$ first stage are sized $16f\times16f$ (so the transformer context is always $16\times16=256$ codes regardless of $f$). — *source:* `esser-vqgan-2021.pdf` p.5 ("Attention Is All You Need in the Latent Space" §4.1 opening) and §4.2/§4.3, pp.5–6 — *quality:* verbatim (quoted figures) / paraphrase (synthesis)


---

## Q3 — Transfusion joint objective (zhou-transfusion-2024)

- **DDPM loss form Transfusion reuses (reference: Ho et al. 2020, simplified training objective)** —
  $$L_{simple}(\theta) := \mathbb E_{t,\mathbf x_0,\epsilon}\Big[\big\lVert \epsilon - \epsilon_\theta(\sqrt{\bar\alpha_t}\mathbf x_0 + \sqrt{1-\bar\alpha_t}\epsilon,\, t)\big\rVert^2\Big]$$
  — *source:* `ho-ddpm-2020.pdf` Eq. 14, p.5 — *quality:* verbatim

- **Transfusion's own DDPM term (conditioned variant, §2.2)** —
  $$\mathcal L_{DDPM} = \mathbb E_{\mathbf x_0,t,\epsilon}\big[\lVert \epsilon - \epsilon_\theta(\mathbf x_t,t,c)\rVert^2\big]$$
  "the model often conditions on additional contextual information $c$, such as a caption when generating an image. The parameters of the noise prediction model are thus optimized by minimizing the mean squared error loss" — *source:* `zhou-transfusion-2024.pdf` Eq. 3, p.4 — *quality:* verbatim. This is the DDPM $L_{simple}$ form (Ho et al. Eq. 14) with the conditioning variable $c$ added.

- **Combined joint objective $\mathcal L_{Transfusion}$ (VERBATIM, exact form)** —
  "We combine the two losses by simply adding the losses computed over each modality with a balancing coefficient $\lambda$:
  $$\mathcal L_{Transfusion} = \mathcal L_{LM} + \lambda \cdot \mathcal L_{DDPM}$$"
  — *source:* `zhou-transfusion-2024.pdf` Eq. 4, p.6 (§3, "Training Objective" paragraph) — *quality:* verbatim

- **$\lambda$ value used** — "We set the $\lambda$ coefficient in the Transfusion objective (Equation 4) to **5** following preliminary experiments; we leave further tuning of $\lambda$ to future work." — *source:* `zhou-transfusion-2024.pdf` §"Model Configuration", p.8 — *quality:* verbatim

- **How LM vs. diffusion loss is scoped per-token/per-image** — "LM loss is computed per token while diffusion loss is computed per image, which may span multiple elements (image patches) in the sequence. Specifically, we add noise $\epsilon$ to each input latent image $\mathbf x_0$ according to the diffusion process to produce $\mathbf x_t$ before patchification, and then compute the image-level diffusion loss." Footnote 8: "When the input is a BOI token, we do not compute any loss." — *source:* `zhou-transfusion-2024.pdf` §3 "Training Objective", p.6 — *quality:* verbatim

- **Attention scheme — causal over text, BIDIRECTIONAL within each image (exact transcription)** — "Transfusion Attention. Language models typically use causal masking to efficiently compute the loss and gradients over an entire sequence in a single forward-backward pass without leaking information from future tokens. While text is naturally sequential, images are not, and are usually modeled with unrestricted (bidirectional) attention. Transfusion combines both attention patterns by applying causal attention to every element in the sequence, and bidirectional attention within the elements of each individual image. This allows every image patch to attend to every other patch within the same image, but only attend to text or patches of other images that appeared previously in the sequence. We find that enabling intra-image attention significantly boosts model performance (see §4.3)." — *source:* `zhou-transfusion-2024.pdf` §3 "Transfusion Attention", p.6 — *quality:* verbatim

- **Figure 4 (attention-mask illustration) caption** — "Expanding on the causal mask, Transfusion allows patches of the same image to condition on each other." — *source:* `zhou-transfusion-2024.pdf` Fig. 4 caption, p.5 — *quality:* verbatim

- **BOI/EOI boundary-token mechanism** — "For mixed-modal examples, we surround each image sequence with special *beginning of image* (BOI) and *end of image* (EOI) tokens before inserting it into the text sequence; thus, we arrive at a single sequence potentially containing both discrete elements (integers representing text tokens) and continuous elements (vectors representing image patches)." Inference-mode switch: "When we sample a BOI token, the decoding algorithm switches to *diffusion mode* ... Once the diffusion process has ended, we append an EOI token to the predicted image, and switch back to LM mode. This algorithm enables the generation of any mixture of text and image modalities." — *source:* `zhou-transfusion-2024.pdf` §3 "Data Representation" p.5, and §3 "Inference" p.6 — *quality:* verbatim

- **Patchification of the latent image — two stages** — Stage 1 (VAE): "We train an 86M parameter VAE following Esser et al. [2021]. We use a CNN encoder and decoder, and latent dimension 8. ... Our implementation reduces an image of $256\times256$ pixels to a $32\times32\times8$ tensor, where each latent 8-dimensional latent pixel represents (conceptually) an $8\times8$ pixel patch in the original image, and trains for 1M steps." Stage 2 (transformer-facing patch compression): "we experiment with two alternatives for compressing local windows of $k\times k$ patch vectors into a single transformer vector (and vice versa): (1) a simple linear layer and (2) up and down blocks of a U-Net." In the controlled Chameleon comparison (§4.2): "the Transfusion variant in these experiments uses simple linear image encoder/decoder with patch size $2\times2$, as well as bidirectional attention." Footnote 13: "Depending on the compression rate of the patch encoder (see Model Architecture in §3), each image will be represented by either 1024, 256, 64, or 16 elements in the sequence." — *source:* `zhou-transfusion-2024.pdf` §4.1 "Latent Image Representation" p.7, §3 "Model Architecture" p.5, §4.2 p.8, footnote 13 p.7 — *quality:* verbatim

- **Head-to-head numbers vs. Chameleon at matched compute (Table 3, 7B models, both trained on 0.5T tokens, controlled setting)** —

  | Model | C4 PPL ↓ | Wiki PPL ↓ | Llama Acc ↑ | MS-COCO CIDEr ↑ | MS-COCO FID ↓ | CLIP ↑ |
  |---|---|---|---|---|---|---|
  | Transfusion | **7.72** | **4.28** | **61.5** | **27.2** | **16.8** | **25.5** |
  | Chameleon | 8.41 | 4.69 | 59.1 | 18.0 | 29.6 | 24.3 |
  | Parity FLOP Ratio | 0.489 | 0.526 | 0.600 | 0.218 | **0.029** | 0.319 |

  "Parity FLOP Ratio is the relative amount of Transfusion FLOPs needed to match the results of Chameleon 7B." — *source:* `zhou-transfusion-2024.pdf` Table 3, p.9 — *quality:* verbatim (table transcription)

- **FLOP-parity headline claim** — "In every benchmark, Transfusion consistently exhibits better scaling laws than Chameleon. While the lines are close to parallel, there is a significant gap in Transfusion's favor. The difference in compute efficiency is particularly striking in image generation, where FID Transfusion achieves parity with Chameleon using **34× less compute**." — *source:* `zhou-transfusion-2024.pdf` §4.2 "Controlled Comparison with Chameleon", p.8 — *quality:* verbatim. Note: $1/0.029 \approx 34.5$, consistent with the printed Parity FLOP Ratio of 0.029 for MS-COCO FID in Table 3.

- **Controlled-comparison methodology note (FLOP proxy, confound removal)** — "We run a series of controlled experiments to compare Transfusion with Chameleon at different model sizes ($N$) and token counts ($D$), using the combination of both as a proxy for FLOPs ($6ND$)." Footnote 15: "Since Transfusion uses continuous representations of images, it can express a single image with significantly fewer tokens, shortening the average document length and thus the overall quadratic price of attention. Since this fact favors Transfusion, we remove this confounder by using the theoretical FLOP calculation." — *source:* `zhou-transfusion-2024.pdf` §4.2, p.8, footnote 15 — *quality:* verbatim

- ⚠️ **DEFECT / notable asymmetry** — none in the equations themselves; note that Table 3's "Parity FLOP Ratio" column is defined only as "relative amount of Transfusion FLOPs needed to match Chameleon 7B" — the caption does not state whether ratios <1 (e.g. 0.029) mean Transfusion needs *less* compute (consistent with the prose "34× less compute" claim, i.e. 1/0.029≈34.5) or the reverse; the direction is only recoverable by cross-referencing the prose paragraph above the table, not from the table/caption in isolation.


---

## Q4 — Chameleon unified AR (team-chameleon-2024)

- **Image tokenizer spec** — "We train a new image tokenizer based on Gafni et al. (2022), which encodes a $512\times512$ image into 1024 discrete tokens from a codebook of size 8192. For training this tokenizer, we use only licensed images. Given the importance of generating human faces, we up-sample the percentage of images with faces during pre-training by 2 times. A core weakness of our tokenizer is in reconstructing images with a large amount of text, therefore upper bounding the capability of our models, when it comes to heavy OCR-related tasks." — *source:* `team-chameleon-2024.pdf` §2.1 "Tokenization" / "Image Tokenization" paragraph, p.4 — *quality:* verbatim. Summary: **resolution 512×512 → 1024 tokens/image; codebook size $K=8192$.**

- **Combined vocabulary construction** — "We train a new BPE tokenizer (Sennrich et al., 2016) over a subset of the training data outlined below with a vocabulary size of **65,536**, which includes the **8192** image codebook tokens, using the sentencepiece library (Kudo and Richardson, 2018)." — *source:* `team-chameleon-2024.pdf` §2.1 "Tokenizer" paragraph, p.4 — *quality:* verbatim. Note the exact construction: the 8,192 image-codebook token IDs are a **subset of**, not **additive to**, the 65,536-entry combined vocabulary (text BPE tokens + image tokens share one unified ID space of size 65,536).

- **Scale/regime at which instability appears** — "It was challenging to maintain stable training when scaling the Chameleon models above 8B parameters and 1T tokens, with instabilities often only arising very late in training." — *source:* `team-chameleon-2024.pdf` §2.3 "Stability" opening, p.6 — *quality:* verbatim

- **Root-cause diagnosis of the divergence** — "We found that the standard LLaMa architecture showed complex divergences due to slow norm growth in the mid-to-late stages of training. We narrowed down the cause of the divergence to the softmax operation being problematic when training with multiple modalities of significantly varying entropy due to the translation invariant property of softmax (i.e., $softmax(z) = softmax(z+c)$). Because we share all weights of the model across modalities, each modality will try to 'compete' with the other by increasing its norms slightly; while not problematic at the beginning of training, it manifests in divergences once we get outside the effective representation range of bf16 (In Figure 6b, we show that ablations without image generation did not diverge). In a unimodal setting, this problem has also been named the logit drift problem (Wortsman et al., 2023). In Figure 5a, we plot the norms of the output of the last transformer layer as training progresses and we find that although training divergences can manifest after as much as even 20-30% of training progress, monitoring uncontrolled growth of output norms is strongly correlated with predicting future loss divergence." — *source:* `team-chameleon-2024.pdf` §2.3 "Architecture" paragraph, p.6 — *quality:* verbatim

- **Fix 1 — Query-Key normalization (QK-Norm)** — "The softmax operation appears in two places in transformers: the core attention mechanism and the softmax over the logits. As inspired by Dehghani et al. (2023) and Wortsman et al. (2023), we first deviate from the Llama architecture by using query-key normalization (QK-Norm). QK-Norm directly controls the norm growth of input to the softmax by applying layer norm to the query and key vectors within the attention." Evidence of necessity: "In Figure 5b, we show training loss curves for Chameleon-7B with and without QK-Norm, and the latter diverges after approximately 20% of a training epoch." — *source:* `team-chameleon-2024.pdf` §2.3 "Architecture" paragraph continuation, p.6–7; Fig. 5b caption, p.7 — *quality:* verbatim. No closed-form equation for QK-Norm itself is given beyond "applying layer norm to the query and key vectors within the attention" — the paper does not print a numbered LayerNorm formula at this point (standard LayerNorm is presumed, not restated).

- **Fix 2 — dropout after attention and feed-forward layers** — "We found that to stabilize Chameleon-7B by controlling norm growth, it was necessary to introduce dropout after the attention and feed-forward layers, in addition to QK-norm (see Figure 5c). However, this recipe was not enough to stabilize Chameleon-34B, which required an additional re-ordering of the norms." — *source:* `team-chameleon-2024.pdf` §2.3, p.7 — *quality:* verbatim. Stated dropout value (Optimization paragraph): "We use a dropout of 0.1 (Srivastava et al., 2014) for Chameleon-7B for training stability, but not for Chameleon-34B (see Figure 5c and 6c)."

- **Fix 3 — norm re-ordering (Swin-transformer-style post-norm), needed for 34B** — "Specifically, we use the strategy of normalization proposed in Liu et al. (2021, 2022), within the transformer block. The benefit of the Swin transformer normalization strategy is that it bounds the norm growth of the feedforward block, which can become additionally problematic given the multiplicative nature of the SwiGLU activation function. If $h$ represents the hidden vector at time-step $t$ after self-attention is applied to input $x$,
  $$\textbf{Chameleon-34B:}\quad h = x + \text{attention\_norm}(\text{attention}(x))$$
  $$\text{output} = h + \text{ffn\_norm}(\text{feed\_forward}(h))$$
  $$\textbf{Llama2:}\quad h = x + \text{attention}(\text{attention\_norm}(x))$$
  $$\text{output} = h + \text{feed\_forward}(\text{ffn\_norm}(h))$$"
  i.e. Chameleon-34B applies the norm **after** the sublayer (post-norm, inside the residual branch), while Llama2 applies the norm **before** the sublayer (pre-norm) — the norm and the sublayer function call are reversed in composition order for both the attention and the feed-forward sub-blocks. — *source:* `team-chameleon-2024.pdf` §2.3, p.7, unnumbered display equations — *quality:* verbatim (re-verified by a dedicated second read of the same page to resolve initial OCR ambiguity between `attention_norm(attention(x))` and `attention(attention_norm(x))`)

- **Interaction between norm-reordering and dropout, and the final per-model recipe** — "There was no difference in perplexity when training a model from scratch with and without the normalization re-ordering until the divergence of the LLaMa-2 parameterization. Additionally, we found that this type of normalization did not work well in combination with dropout and therefore, we train Chameleon-34B without dropout (Figure 6c). Furthermore, we retroactively found that Chameleon-7B can also be stably trained without dropout, when using norm-reordering, but QK-norm is essential in both cases." — *source:* `team-chameleon-2024.pdf` §2.3, p.7 — *quality:* verbatim

- **z-loss regularization (addresses final-softmax logit shift, not fixed by QK-Norm)** — "The application of QK-Norm while helping the inner softmaxes within the Transformer does not solve the problem of logit shift in the final softmax. Following Chowdhery et al. (2022); Wortsman et al. (2023), we apply z-loss regularization. Specifically, we regularize the partition function $Z$ of the softmax function $\sigma(x)_i = \frac{e^{x_i}}{Z}$ where $Z=\sum_i e^{x_i}$ by adding $10^{-5}\log^2 Z$ to our loss function." "For Chameleon-7B it was important to use both dropout and z-loss to achieve stability, while Chameleon-34B only required z-loss (Figure 6c)." — *source:* `team-chameleon-2024.pdf` §2.3 "Optimization" paragraph, p.7 — *quality:* verbatim

- **Table 1 — summary of core architecture/optimization deltas vs. LLaMA-1/2** —

  | Model | Params | Ctx Len | GQA | Tokens | LR | Epochs | Dropout | Zloss | Qknorm |
  |---|---|---|---|---|---|---|---|---|---|
  | LLaMA-1 | 7B | 2k | × | 1.0T | $3.0\times10^{-4}$ | 1.0 | 0.0 | 0.0 | × |
  | LLaMA-1 | 33B | 2k | × | 1.4T | $1.5\times10^{-4}$ | 1.0 | 0.0 | 0.0 | × |
  | LLaMA-2 | 7B | 4k | × | 2.0T | $3.0\times10^{-4}$ | 1.0 | 0.0 | 0.0 | × |
  | LLaMA-2 | 34B | 4k | ✓ | 2.0T | $1.5\times10^{-4}$ | 1.0 | 0.0 | 0.0 | × |
  | Chameleon | 7B | 4k | × | 4.4T | $1.0\times10^{-4}$ | 2.1 | 0.1 | $10^{-5}$ | ✓ |
  | Chameleon | 34B | 4k | ✓ | 4.4T | $1.0\times10^{-4}$ | 2.1 | 0.0 | $10^{-5}$ | ✓ |

  — *source:* `team-chameleon-2024.pdf` Table 1, p.8 — *quality:* verbatim (table transcription)

- ⚠️ **DEFECT / gap** — Table 1 (p.8) has no "norm-reordering" column, even though §2.3 states norm-reordering is required for Chameleon-34B stability and was "retroactively" also found compatible with Chameleon-7B. The table's Dropout/Zloss/Qknorm columns alone do not fully specify the stabilized recipe per §2.3's own prose (norm-reordering is a third necessary architectural change for 34B, alongside QK-Norm, and is omitted from the summary table). This is an internal completeness gap in the paper's own summary table, not a numeric error.

- ⚠️ **DEFECT / potential ambiguity** — the equation block on p.7 initially reads ambiguously between `attention_norm(attention(x))` and `attention(attention_norm(x))` for the Llama2 case at low image resolution; re-read at full resolution on this page confirms the Llama2 line is `h = x + attention(attention_norm(x))` (pre-norm: norm applied before the sublayer) versus Chameleon-34B's `h = x + attention_norm(attention(x))` (post-norm: norm applied after the sublayer) — i.e. the composition order of the two function calls is swapped between the two architectures. Flagging because the visual distinction between the two forms is subtle (a nested-parenthesis swap) and a casual read could transcribe them identically, which would silently erase the entire point of the section.

