# Evidence extraction — Appendix A/B (multimodal-llms survey)

Sources read: download/dosovitskiy-vit-2020.pdf (ViT), download/radford-clip-2021.pdf (CLIP),
download/zhai-siglip-2023.pdf (SigLIP), download/vandenoord-cpc-2018.pdf (CPC/InfoNCE).

## Q1 — ViT patch embedding + encoder (dosovitskiy-vit-2020)

- **Patch-embedding / sequence-construction equation (Eq. 1)** — verbatim:
  $$\mathbf{z}_0 = [\mathbf{x}_{\text{class}}; \mathbf{x}_p^1\mathbf{E}; \mathbf{x}_p^2\mathbf{E}; \cdots; \mathbf{x}_p^N\mathbf{E}] + \mathbf{E}_{pos}, \quad \mathbf{E}\in\mathbb{R}^{(P^2\cdot C)\times D}, \; \mathbf{E}_{pos}\in\mathbb{R}^{(N+1)\times D}$$
  — *source:* `dosovitskiy-vit-2020.pdf` Eq. 1, p.4 — *quality:* verbatim

- **MSA / MLP block equations (Eqs. 2–4)** — verbatim:
  $$\mathbf{z}'_\ell = \mathrm{MSA}(\mathrm{LN}(\mathbf{z}_{\ell-1})) + \mathbf{z}_{\ell-1}, \quad \ell = 1\ldots L$$
  $$\mathbf{z}_\ell = \mathrm{MLP}(\mathrm{LN}(\mathbf{z}'_\ell)) + \mathbf{z}'_\ell, \quad \ell = 1\ldots L$$
  $$\mathbf{y} = \mathrm{LN}(\mathbf{z}_L^0)$$
  Paper text: "The MLP contains two layers with a GELU non-linearity." — *source:* `dosovitskiy-vit-2020.pdf` Eqs. 2–4, p.4 — *quality:* verbatim

- **Definition of N** — "we reshape the image $\mathbf{x}\in\mathbb{R}^{H\times W\times C}$ into a sequence of flattened 2D patches $\mathbf{x}_p\in\mathbb{R}^{N\times(P^2\cdot C)}$, where $(H,W)$ is the resolution of the original image, $C$ is the number of channels, $(P,P)$ is the resolution of each image patch, and $N=HW/P^2$ is the resulting number of patches, which also serves as the effective input sequence length for the Transformer." — *source:* `dosovitskiy-vit-2020.pdf` §3.1, p.3 — *quality:* verbatim

- **[class] token construction** — "Similar to BERT's `[class]` token, we prepend a learnable embedding to the sequence of embedded patches ($\mathbf{z}_0^0 = \mathbf{x}_{\text{class}}$), whose state at the output of the Transformer encoder ($\mathbf{z}_L^0$) serves as the image representation $\mathbf{y}$ (Eq. 4)." — *source:* `dosovitskiy-vit-2020.pdf` §3.1, p.3 — *quality:* verbatim

- **Position embeddings — how added, and 1-D default** — "Position embeddings are added to the patch embeddings to retain positional information. We use standard learnable 1D position embeddings, since we have not observed significant performance gains from using more advanced 2D-aware position embeddings (Appendix D.4). The resulting sequence of embedding vectors serves as input to the encoder." — *source:* `dosovitskiy-vit-2020.pdf` §3.1, p.3 — *quality:* verbatim

- **ViT-Base/Large/Huge config table (Table 1)** — verbatim table:

  | Model | Layers | Hidden size D | MLP size | Heads | Params |
  |---|---|---|---|---|---|
  | ViT-Base | 12 | 768 | 3072 | 12 | 86M |
  | ViT-Large | 24 | 1024 | 4096 | 16 | 307M |
  | ViT-Huge | 32 | 1280 | 5120 | 16 | 632M |

  Note: Table 1 has **no explicit "patch size" column** — patch size is encoded in the model name suffix (e.g. ViT-L/16 = "Large" variant with 16×16 input patch size), per paper text: "we use brief notation to indicate the model size and the input patch size: for instance, ViT-L/16 means the 'Large' variant with 16×16 input patch size. Note that the Transformer's sequence length is inversely proportional to the square of the patch size, thus models with smaller patch size are computationally more expensive." — *source:* `dosovitskiy-vit-2020.pdf` Table 1 + surrounding text, p.5 — *quality:* verbatim

- **Positional-embedding ablation — Table 8 results (ViT-B/16, ImageNet 5-shot linear)** — verbatim table:

  | Pos. Emb. | Default/Stem | Every Layer | Every Layer-Shared |
  |---|---|---|---|
  | No Pos. Emb. | 0.61382 | N/A | N/A |
  | 1-D Pos. Emb. | 0.64206 | 0.63964 | 0.64292 |
  | 2-D Pos. Emb. | 0.64001 | 0.64046 | 0.64022 |
  | Rel. Pos. Emb. | 0.64032 | N/A | N/A |

  — *source:* `dosovitskiy-vit-2020.pdf` Table 8, p.17 — *quality:* verbatim

- **Ablation conclusion (what the paper actually says)** — "Table 8 summarizes the results from this ablation study on a ViT-B/16 model. As we can see, while there is a large gap between the performances of the model with no positional embedding and models with positional embedding, there is little to no difference between different ways of encoding positional information. We speculate that since our Transformer encoder operates on patch-level inputs, as opposed to pixel-level, the differences in how to encode spatial information is less important. More precisely, in patch-level inputs, the spatial dimensions are much smaller than the original pixel-level inputs, e.g., 14 × 14 as opposed to 224 × 224, and learning to represent the spatial relations in this resolution is equally easy for these different positional encoding strategies." — *source:* `dosovitskiy-vit-2020.pdf` §D.4, p.18 — *quality:* verbatim. So: 2-D-aware position embeddings gave **no significant gain** over 1-D; the paper therefore defaults to 1-D everywhere else.

- **2-D positional embedding construction (as defined for the ablation)** — "2-dimensional positional embedding: Considering the inputs as a grid of patches in two dimensions. In this case, two sets of embeddings are learned, each for one of the axes, X-embedding, and Y-embedding, each with size $D/2$. Then, based on the coordinate on the path in the input, we concatenate the X and Y embedding to get the final positional embedding for that patch." — *source:* `dosovitskiy-vit-2020.pdf` §D.4, p.17 — *quality:* verbatim (note: source PDF says "path" where "patch" is clearly meant — OCR/typo artifact of the printed source, reproduced verbatim)

⚠️ DEFECT — the phrase "based on the coordinate on the path in the input" in §D.4 (p.17) appears to be a typo for "patch" in the original printed/arXiv text; reproduced verbatim above since this is what the source states.


## Q2 — CLIP contrastive objective (radford-clip-2021)

- **Loss as stated in prose** — "CLIP is trained to predict which of the $N \times N$ possible (image, text) pairings across a batch actually occurred. To do this, CLIP learns a multi-modal embedding space by jointly training an image encoder and text encoder to maximize the cosine similarity of the image and text embeddings of the $N$ real pairs in the batch while minimizing the cosine similarity of the embeddings of the $N^2 - N$ incorrect pairings. We optimize a symmetric cross entropy loss over these similarity scores." — *source:* `radford-clip-2021.pdf` §2.3, p.4 — *quality:* verbatim

- **Figure 3 pseudocode — transcribed verbatim**:
  ```
  # image_encoder - ResNet or Vision Transformer
  # text_encoder  - CBOW or Text Transformer
  # I[n, h, w, c] - minibatch of aligned images
  # T[n, l]       - minibatch of aligned texts
  # W_i[d_i, d_e] - learned proj of image to embed
  # W_t[d_t, d_e] - learned proj of text to embed
  # t             - learned temperature parameter

  # extract feature representations of each modality
  I_f = image_encoder(I) #[n, d_i]
  T_f = text_encoder(T)  #[n, d_t]

  # joint multimodal embedding [n, d_e]
  I_e = l2_normalize(np.dot(I_f, W_i), axis=1)
  T_e = l2_normalize(np.dot(T_f, W_t), axis=1)

  # scaled pairwise cosine similarities [n, n]
  logits = np.dot(I_e, T_e.T) * np.exp(t)

  # symmetric loss function
  labels = np.arange(n)
  loss_i = cross_entropy_loss(logits, labels, axis=0)
  loss_t = cross_entropy_loss(logits, labels, axis=1)
  loss   = (loss_i + loss_t)/2
  ```
  Caption: "Figure 3. Numpy-like pseudocode for the core of an implementation of CLIP." — *source:* `radford-clip-2021.pdf` Figure 3, p.5 — *quality:* verbatim

- **Temperature parameter τ — parameterization and clipping (quoted)** — "Finally, the temperature parameter which controls the range of the logits in the softmax, $\tau$, is directly optimized during training as a log-parameterized multiplicative scalar to avoid turning into a hyper-parameter." — *source:* `radford-clip-2021.pdf` §2.3 (end), p.4 — *quality:* verbatim
  Additional clipping statement: "The learnable temperature parameter $\tau$ was initialized to the equivalent of 0.07 from [Wu et al., 2018] and clipped to prevent scaling the logits by more than 100 which we found necessary to prevent training instability." — *source:* `radford-clip-2021.pdf` §2.5, p.5 — *quality:* verbatim

- **Batch size** — "We use a very large minibatch size of 32,768." — *source:* `radford-clip-2021.pdf` §2.5, p.5 — *quality:* verbatim

- **Embedding dim d_e** — NOT FOUND as a single explicit numeric value in the main text (pp.1-6) read. The pseudocode (Figure 3) uses the symbolic placeholder `d_e` for the joint multimodal embedding dimension, and the text states only that per-encoder outputs $I_f\,[n,d_i]$ and $T_f\,[n,d_t]$ are linearly projected into the shared space — no numeric $d_e$ was stated on the pages read; a per-model value may exist in an appendix hyperparameter table not read within this call budget.

- **Image encoder variants (§2.4)** — "We consider two different architectures for the image encoder. For the first, we use ResNet-50 ... as the base architecture for the image encoder ... We also replace the global average pooling layer with an attention pooling mechanism [a single layer of 'transformer-style' multi-head QKV attention where the query is conditioned on the global average-pooled representation of the image]. ... For the second architecture, we experiment with the recently introduced Vision Transformer (ViT) ... We closely follow their implementation with only the minor modification of adding an additional layer of normalization to the combined patch and position embeddings before the transformer and use a slightly different initialization scheme." — *source:* `radford-clip-2021.pdf` §2.4, pp.4-5 — *quality:* verbatim (bracketed clause paraphrased from adjacent sentence for compactness, flagged)
  Concrete variants trained (§2.5): "We train a series of 5 ResNets and 3 Vision Transformers. For the ResNets we train a ResNet-50, a ResNet-101, and then 3 more which follow EfficientNet-style model scaling and use approximately 4x, 16x, and 64x the compute of a ResNet-50. They are denoted as RN50x4, RN50x16, and RN50x64 respectively... For the Vision Transformers we train a ViT-B/32, a ViT-B/16, and a ViT-L/14. We train all models for 32 epochs." — *source:* `radford-clip-2021.pdf` §2.5, p.5 — *quality:* verbatim

- **Text encoder** — "The text encoder is a Transformer (Vaswani et al., 2017) with the architecture modifications described in Radford et al. (2019). As a base size we use a 63M-parameter 12-layer 512-wide model with 8 attention heads. The transformer operates on a lower-cased byte pair encoding (BPE) representation of the text with a 49,152 vocab size (Sennrich et al., 2015). For computational efficiency, the max sequence length was capped at 76." — *source:* `radford-clip-2021.pdf` §2.5, p.5 — *quality:* verbatim

- **Why contrastive (not predictive/generative) — with the efficiency figure quoted** — "Both these approaches share a key similarity. They try to predict the *exact* words of the text accompanying each image. This is a difficult task due to the wide variety of descriptions, comments, and related text that co-occur with images. Recent work in contrastive representation learning for images has found that contrastive objectives can learn better representations than their equivalent predictive objective (Tian et al., 2019). Other work has found that although generative models of images can learn high quality image representations, they require over an order of magnitude more compute than contrastive models with the same performance (Chen et al., 2020a). Noting these findings, we explored training a system to solve the potentially easier proxy task of predicting only which text as a whole is paired with which image and not the exact words of that text. Starting with the same bag-of-words encoding baseline, we swapped the predictive objective for a contrastive objective in Figure 2 and observed a further 4x efficiency improvement in the rate of zero-shot transfer to ImageNet." — *source:* `radford-clip-2021.pdf` §2.3, p.4 — *quality:* verbatim
  Figure 2 caption + data: "Figure 2. **CLIP is much more efficient at zero-shot transfer than our image caption baseline.** Although highly expressive, we found that transformer language models are relatively weak at zero-shot ImageNet classification. Here, we see that it learns 3x slower than a baseline which predicts a bag-of-words (BoW) encoding of the text (Joulin et al., 2016). Swapping the prediction objective for the contrastive objective of CLIP further improves efficiency another 4x." Plot annotations on Fig. 2 read "4X efficiency" (Bag of Words Contrastive (CLIP) vs Bag of Words Prediction) and "3X efficiency" (Bag of Words Prediction vs Transformer Language Model), x-axis "# of images processed" (2M to 400M), y-axis "Zero-Shot ImageNet Accuracy" (0-40%). — *source:* `radford-clip-2021.pdf` Figure 2 + caption, p.3 — *quality:* verbatim


## Q3 — SigLIP sigmoid loss (zhai-siglip-2023)

- **Softmax contrastive loss (baseline, §3.1, unnumbered display eq.)** — verbatim:
  $$-\frac{1}{2|\mathcal{B}|}\sum_{i=1}^{|\mathcal{B}|}\left(\underbrace{\log\frac{e^{t\mathbf{x}_i\cdot\mathbf{y}_i}}{\sum_{j=1}^{|\mathcal{B}|}e^{t\mathbf{x}_i\cdot\mathbf{y}_j}}}_{\text{image}\to\text{text softmax}} + \underbrace{\log\frac{e^{t\mathbf{x}_i\cdot\mathbf{y}_i}}{\sum_{j=1}^{|\mathcal{B}|}e^{t\mathbf{x}_j\cdot\mathbf{y}_i}}}_{\text{text}\to\text{image softmax}}\right)$$
  "where $\mathbf{x}_i = \frac{f(I_i)}{\lVert f(I_i)\rVert_2}$ and $\mathbf{y}_i = \frac{g(T_i)}{\lVert g(T_i)\rVert_2}$... Note that due to the asymmetry of the softmax loss, the normalization is independently performed two times: across images and across texts [citing CLIP, 36]. The scalar $t$ is parametrized as $\exp(t')$, where $t'$ is a global freely learnable parameter." — *source:* `zhai-siglip-2023.pdf` §3.1, p.3 — *quality:* verbatim

- **Sigmoid pairwise loss equation (§3.2, unnumbered display eq.)** — verbatim:
  $$-\frac{1}{|\mathcal{B}|}\sum_{i=1}^{|\mathcal{B}|}\sum_{j=1}^{|\mathcal{B}|}\underbrace{\log\frac{1}{1+e^{z_{ij}(-t\mathbf{x}_i\cdot\mathbf{y}_j+b)}}}_{\mathcal{L}_{ij}}$$
  "where $z_{ij}$ is the label for a given image and text input, which equals 1 if they are paired and $-1$ otherwise." — *source:* `zhai-siglip-2023.pdf` §3.2, p.3 — *quality:* verbatim

- **Learnable bias b and temperature — quoted rationale and init values** — "At initialization, the heavy imbalance coming from the many negatives dominates the loss, leading to large initial optimization steps attempting to correct this bias. To alleviate this, we introduce an additional learnable bias term $b$ similar to the temperature $t$. We initialize $t'$ and $b$ to $\log 10$ and $-10$ respectively. This makes sure that the training starts roughly close to the prior and does not require massive over-correction." — *source:* `zhai-siglip-2023.pdf` §3.2, p.3 — *quality:* verbatim

- **Algorithm 1 — Sigmoid loss pseudo-implementation, transcribed verbatim**:
  ```
  # img_emb      : image model embedding [n, dim]
  # txt_emb      : text model embedding [n, dim]
  # t_prime, b   : learnable temperature and bias
  # n            : mini-batch size

  t = exp(t_prime)
  zimg = l2_normalize(img_emb)
  ztxt = l2_normalize(txt_emb)
  logits = dot(zimg, ztxt.T) * t + b
  labels = 2 * eye(n) - ones(n)  # -1 with diagonal 1
  l = -sum(log_sigmoid(labels * logits)) / n
  ```
  — *source:* `zhai-siglip-2023.pdf` Algorithm 1, p.3 — *quality:* verbatim

- **How sigmoid differs from softmax-InfoNCE — no global normalization → no all-gather (quoted)** — "Instead of the softmax-based contrastive loss, we propose a simpler alternative that does not require computing global normalization factors. The sigmoid-based loss processes every image-text pair independently, effectively turning the learning problem into the standard binary classification on the dataset of all pair combinations, with a positive labels for the matching pairs $(I_i, T_i)$ and negative labels for all other pairs $(I_i, T_{j\neq i})$." — *source:* `zhai-siglip-2023.pdf` §3.2, p.3 — *quality:* verbatim
  On the all-gather/memory consequence (§3.3): "Computing the loss when data is split across $D$ devices necessitates gathering all embeddings [59] with expensive all-gathers and, more importantly, the materialization of a memory-intensive $|\mathcal{B}|\times|\mathcal{B}|$ matrix of pairwise similarities. The sigmoid loss, however, is particularly amenable to a memory efficient, fast, and numerically stable implementation that ameliorates both these issues." Figure 1 caption: "**Efficient loss implementation** demonstrated via a mock setup with 3 devices and a global batch size of 12. There are no all-gathers, and at any point in time only the bright yellow square (size $4\times4$) is materialized in memory." — *source:* `zhai-siglip-2023.pdf` §3.3 + Fig. 1 caption, p.3 — *quality:* verbatim
  Abstract statement: "Unlike standard contrastive learning with softmax normalization, the sigmoid loss operates solely on image-text pairs and does not require a global view of the pairwise similarities for normalization." — *source:* `zhai-siglip-2023.pdf` Abstract, p.1 — *quality:* verbatim

- **Batch-size findings — SigLiT (Figure 2 left / §4.1 text)** — "We perform a study over a wide range of batch sizes, from 512 to 1M... When the batch size is smaller than 16k, sigmoid loss outperforms softmax loss by a large margin. With growing batch sizes, we observe that softmax loss quickly catches up and potentially slightly underperforms sigmoid loss with a large enough batch size... We successfully trained an SigLiT model at one million batch size. To our surprise, the performance saturates at 32k batch size, further scaling up the batch size only gives a minor boost, and the model peaks at 256k batch size. Our best SigLiT with a $B$-sized text model achieves 84.7% zero-shot transfer accuracy on ImageNet, while the original LiT paper reports a slightly better 85.2% score with a 10 times larger $g$-sized text model." — *source:* `zhai-siglip-2023.pdf` §4.1, pp.4-5 — *quality:* verbatim

- **Batch-size findings — SigLIP saturation numbers (§4.2)** — "As batch size increases, the gap between the sigmoid and the softmax losses diminish. SigLIP performs best at batch size 32k, whereas the softmax loss required 98k for optimal performance and still didn't outperform the sigmoid based variant. Scaling further, a larger batch size like 307k hurts both losses." — *source:* `zhai-siglip-2023.pdf` §4.2, p.5 — *quality:* verbatim
  Memory-efficiency datapoint (§4.2): "with four TPU-v4 chips, we could fit a batch size of 4096 with a Base SigLIP but only 2048 with a corresponding CLIP model." — *source:* `zhai-siglip-2023.pdf` §4.2, p.5 — *quality:* verbatim

- **Table 1 — SigLiT and SigLIP results (verbatim)**:

  | | Image | Text | BS | #TPUv4 | Days | INet-0 |
  |---|---|---|---|---|---|---|
  | SigLiT | ❄ B/8 | L* | 32k | 4 | 1 | 79.8 |
  | SigLiT | ❄ g/14 | L | 20k | 4 | 2 | 84.5 |
  | SigLIP | 🔓 B/16 | B | 16k | 16 | 3 | 71.0 |
  | SigLIP | B/16 | B | 32k | 32 | 2 | 72.1 |
  | SigLIP | B/16 | B | 32k | 32 | 5 | 73.4 |

  Footnote: "* We use a variant of the L model with 12 layers." ❄ = frozen public checkpoint; 🔓 = public unlocked checkpoint. — *source:* `zhai-siglip-2023.pdf` Table 1, p.1 — *quality:* verbatim

- **Table 2 — Multilingual SigLIP batch-size sweep (verbatim, 30B seen examples)**:

  | | 16k | 32k | 64k | 128k | 240k |
  |---|---|---|---|---|---|
  | INet-0 | 71.6 | 73.2 | 73.2 | 73.2 | 73.1 |
  | XM avg | 34.8 | 34.9 | 34.4 | 33.6 | 32.7 |

  (partial table; full table has per-language rows XM de/en/hi/ru/zh) — *source:* `zhai-siglip-2023.pdf` Table 2, p.5 — *quality:* verbatim


## Q4 — InfoNCE as a mutual-information bound (vandenoord-cpc-2018)

- **Mutual information definition (Eq. 1)** — verbatim:
  $$I(x;c) = \sum_{x,c} p(x,c)\log\frac{p(x|c)}{p(x)}. \tag{1}$$
  Context: "...in a way that maximally preserves the mutual information of the original signals $x$ and $c$ defined as [Eq. 1]. By maximizing the mutual information between the encoded representations (which is bounded by the MI between the input signals), we extract the underlying latent variables the inputs have in common." — *source:* `vandenoord-cpc-2018.pdf` §2.1, Eq. 1, p.3 — *quality:* verbatim

- **Architecture setup (§2.2)** — "a non-linear encoder $g_{enc}$ maps the input sequence of observations $x_t$ to a sequence of latent representations $z_t = g_{enc}(x_t)$, potentially with a lower temporal resolution. Next, an autoregressive model $g_{ar}$ summarizes all $z_{\leq t}$ in the latent space and produces a context latent representation $c_t = g_{ar}(z_{\leq t})$." — *source:* `vandenoord-cpc-2018.pdf` §2.2, p.3 — *quality:* verbatim

- **Density-ratio target (Eq. 2)** — verbatim:
  $$f_k(x_{t+k}, c_t) \propto \frac{p(x_{t+k}|c_t)}{p(x_{t+k})} \tag{2}$$
  "where $\propto$ stands for 'proportional to' (i.e. up to a multiplicative constant). Note that the density ratio $f$ can be unnormalized (does not have to integrate to 1). Although any positive real score can be used here, we use a simple log-bilinear model:" — *source:* `vandenoord-cpc-2018.pdf` §2.2, Eq. 2 + surrounding text, p.3 — *quality:* verbatim

- **Log-bilinear critic (Eq. 3)** — verbatim:
  $$f_k(x_{t+k}, c_t) = \exp\left(z_{t+k}^T W_k c_t\right), \tag{3}$$
  "In our experiments a linear transformation $W_k^T c_t$ is used for the prediction with a different $W_k$ for every step $k$." — *source:* `vandenoord-cpc-2018.pdf` §2.2, Eq. 3, p.3 — *quality:* verbatim

- **InfoNCE loss (Eq. 4)** — verbatim: "Given a set $X = \{x_1, \ldots x_N\}$ of $N$ random samples containing one positive sample from $p(x_{t+k}|c_t)$ and $N-1$ negative samples from the 'proposal' distribution $p(x_{t+k})$, we optimize:"
  $$\mathcal{L}_{\mathrm{N}} = -\mathbb{E}_X\left[\log\frac{f_k(x_{t+k}, c_t)}{\sum_{x_j\in X} f_k(x_j, c_t)}\right] \tag{4}$$
  "Optimizing this loss will result in $f_k(x_{t+k}, c_t)$ estimating the density ratio in equation 2." — *source:* `vandenoord-cpc-2018.pdf` §2.3, Eq. 4, p.3 — *quality:* verbatim

- **Derivation that the optimal critic ∝ density ratio (§2.3, Eq. 5)** — verbatim prose: "The loss in Equation 4 is the categorical cross-entropy of classifying the positive sample correctly, with $\frac{f_k}{\sum_X f_k}$ being the prediction of the model. Let us write the optimal probability for this loss as $p(d=i|X,c_t)$ with $[d=i]$ being the indicator that sample $x_i$ is the 'positive' sample. The probability that sample $x_i$ was drawn from the conditional distribution $p(x_{t+k}|c_t)$ rather than the proposal distribution $p(x_{t+k})$ can be derived as follows:"
  $$p(d=i|X,c_t) = \frac{p(x_i|c_t)\prod_{l\neq i}p(x_l)}{\sum_{j=1}^{N}p(x_j|c_t)\prod_{l\neq j}p(x_l)} = \frac{\frac{p(x_i|c_t)}{p(x_i)}}{\sum_{j=1}^{N}\frac{p(x_j|c_t)}{p(x_j)}}. \tag{5}$$
  "As we can see, the optimal value for $f(x_{t+k},c_t)$ in Equation 4 is proportional to $\frac{p(x_{t+k}|c_t)}{p(x_{t+k})}$ and this is independent of the choice of the number of negative samples $N-1$." — *source:* `vandenoord-cpc-2018.pdf` §2.3, Eq. 5, p.4 — *quality:* verbatim

- **Mutual-information bound statement (§2.3, unnumbered display eq.)** — verbatim: "Though not required for training, we can evaluate the mutual information between the variables $c_t$ and $x_{t+k}$ as follows:"
  $$I(x_{t+k}, c_t) \geq \log(N) - \mathcal{L}_{\mathrm{N}},$$
  "which becomes tighter as N becomes larger. Also observe that minimizing the InfoNCE loss $\mathcal{L}_N$ maximizes a lower bound on mutual information. For more details see Appendix." — *source:* `vandenoord-cpc-2018.pdf` §2.3 (end), p.4 — *quality:* verbatim. This is the explicit forward-reference to the Appendix that the question asks about; the referenced material is Appendix §A.1, transcribed below.

- **Appendix A.1 "Estimating the Mutual Information with InfoNCE" — the full deferred derivation (Eqs. 6–11), transcribed verbatim**:
  Lead-in text: "By optimizing InfoNCE, the CPC loss we defined in Equation 4, we are maximizing the mutual information between $c_t$ and $z_{t+k}$ (which is bounded by the MI between $c_t$ and $x_{t+k}$). This can be shown as follows. As already shown in Section 2.3, the optimal value for $f(x_{t+k},c_t)$ is given by $\frac{p(x_{t+k}|c_t)}{p(x_{t+k})}$. Inserting this back into Equation 4 and splitting $X$ into the positive example and the negative examples $X_{\mathrm{neg}}$ results in:"

  $$\mathcal{L}_{\mathrm{N}}^{\mathrm{opt}} = -\mathbb{E}_X\log\left[\frac{\frac{p(x_{t+k}|c_t)}{p(x_{t+k})}}{\frac{p(x_{t+k}|c_t)}{p(x_{t+k})} + \sum_{x_j\in X_{\mathrm{neg}}}\frac{p(x_j|c_t)}{p(x_j)}}\right] \tag{6}$$

  $$= \mathbb{E}_X\log\left[1 + \frac{p(x_{t+k})}{p(x_{t+k}|c_t)}\sum_{x_j\in X_{\mathrm{neg}}}\frac{p(x_j|c_t)}{p(x_j)}\right] \tag{7}$$

  $$\approx \mathbb{E}_X\log\left[1 + \frac{p(x_{t+k})}{p(x_{t+k}|c_t)}(N-1)\,\mathbb{E}_{x_j}\frac{p(x_j|c_t)}{p(x_j)}\right] \tag{8}$$

  $$= \mathbb{E}_X\log\left[1 + \frac{p(x_{t+k})}{p(x_{t+k}|c_t)}(N-1)\right] \tag{9}$$

  $$\geq \mathbb{E}_X\log\left[\frac{p(x_{t+k})}{p(x_{t+k}|c_t)}N\right] \tag{10}$$

  $$= -I(x_{t+k}, c_t) + \log(N), \tag{11}$$

  "Therefore, $I(x_{t+k},c_t)\geq \log(N) - \mathcal{L}_{\mathrm{N}}^{\mathrm{opt}}$. This trivially also holds for other $f$ that obtain a worse (higher) $\mathcal{L}_{\mathrm{N}}$. Equation 8 quickly becomes more accurate as $N$ increases. At the same time $\log(N) - \mathcal{L}_{\mathrm{N}}$ also increases, so it's useful to use large values of $N$." — *source:* `vandenoord-cpc-2018.pdf` Appendix §A.1, Eqs. 6–11, p.13 — *quality:* verbatim

- **Appendix A.1 continuation — relation to MINE (Eqs. 12–15), transcribed verbatim**: "InfoNCE is also related to MINE [54]. Without loss of generality let's write $f(x,c) = e^{F(x,c)}$, then"

  $$\mathbb{E}_X\left[\log\frac{f(x,c)}{\sum_{x_j\in X}f(x_j,c)}\right] = \mathbb{E}_{(x,c)}\big[F(x,c)\big] - \mathbb{E}_{(x,c)}\left[\log\sum_{x_j\in X}e^{F(x_j,c)}\right] \tag{12}$$

  $$= \mathbb{E}_{(x,c)}\big[F(x,c)\big] - \mathbb{E}_{(x,c)}\left[\log\left(e^{F(x,c)} + \sum_{x_j\in X_{\mathrm{neg}}}e^{F(x_j,c)}\right)\right] \tag{13}$$

  $$\leq \mathbb{E}_{(x,c)}\big[F(x,c)\big] - \mathbb{E}_{c}\left[\log\sum_{x_j\in X_{\mathrm{neg}}}e^{F(x_j,c)}\right] \tag{14}$$

  $$= \mathbb{E}_{(x,c)}\big[F(x,c)\big] - \mathbb{E}_{c}\left[\log\frac{1}{N-1}\sum_{x_j\in X_{\mathrm{neg}}}e^{F(x_j,c)} + \log(N-1)\right] \tag{15}$$

  "is equivalent to the MINE estimator (up to a constant). So we maximize a lower bound on this estimator. We found that using MINE directly gave identical performance when the task was non-trivial, but became very unstable if the target was easy to predict from the context (e.g., when predicting a single step in the future and the target overlaps with the context)." — *source:* `vandenoord-cpc-2018.pdf` Appendix §A.1, Eqs. 12–15, p.13 — *quality:* verbatim

- **What the main body defers vs. what §2.3 already shows** — main-text §2.3 shows: (a) the loss is categorical cross-entropy for classifying the positive sample (prose only, no eq. number), (b) the optimal-critic derivation (Eq. 5) proving $f^{\mathrm{opt}} \propto p(x_{t+k}|c_t)/p(x_{t+k})$, and (c) states the bound $I(x_{t+k},c_t)\geq\log(N)-\mathcal{L}_N$ **without proof**, with an explicit "For more details see Appendix." Appendix §A.1 supplies: the full derivation of that bound (Eqs. 6–11, substituting the optimal critic back into the loss) and a secondary derivation relating InfoNCE to the MINE mutual-information estimator (Eqs. 12–15). — *source:* `vandenoord-cpc-2018.pdf` §2.3 p.4 + Appendix A.1 p.13 — *quality:* paraphrase (structural summary of what is deferred where)

⚠️ DEFECT — possible unstated pointwise assumption at the Eq. 9 → Eq. 10 step (own mathematical check while transcribing, not stated by the paper). Writing $r \equiv p(x_{t+k})/p(x_{t+k}|c_t)$, the claimed inequality $\log[1+r(N-1)] \geq \log[rN]$ is equivalent (since $\log$ is monotonic and $r>0$) to $1+r(N-1)\geq rN$, i.e. to $r\leq 1$, i.e. to $p(x_{t+k}|c_t)\geq p(x_{t+k})$ for the specific positive sample drawn inside the outer $\mathbb{E}_X[\cdot]$. The paper does not state or justify this pointwise density-ratio condition anywhere in §2.3 or Appendix A.1 — it moves directly from Eq. 9 to Eq. 10 with a bare "≥" and no accompanying remark (contrast with the "≈" step Eq. 7→8, where the paper explicitly comments "Equation 8 quickly becomes more accurate as N increases"). If $p(x_{t+k}|c_t) < p(x_{t+k})$ can occur for a drawn positive sample (i.e., the context transiently lowers the density at the realized future value, which is not excluded by the setup), the pointwise step would fail for that sample, and the paper does not show the inequality survives in expectation over $X$ despite this (e.g. via a version of Jensen's inequality) — no such argument appears on the page. Flagging for independent re-derivation per `.claude/rules/workflow.md` Math Derivation Rules before this exact step is relied upon in the survey's Appendix B.

