# Evidence Ledger C — Multimodal Connectors (Q-Former / Perceiver Resampler / Gated XAttn / Linear-MLP Projection)

Sources read (exact paths, per task instructions):
- `download/li-blip2-2023.pdf`
- `download/alayrac-flamingo-2022.pdf`
- `download/liu-llava-2023.pdf`
- `download/liu-llava-1.5-2023.pdf`

---

## Q1 — Q-Former (li-blip2-2023)

- **Query token count and dimension** — "we use 32 queries where each query has a dimension of 768 (same as the hidden dimension of the Q-Former)" — *source:* `li-blip2-2023.pdf` §3.1 (p.3, para under Fig. 2) — *quality:* verbatim
- **Q-Former total parameter count** — "In total, Q-Former contains 188M parameters. Note that the queries are considered as model parameters." — *source:* `li-blip2-2023.pdf` §3.1 (p.3) — *quality:* verbatim
- **Q-Former init** — "We initialize Q-Former with the pre-trained weights of BERT_base (Devlin et al., 2019), whereas the cross-attention layers are randomly initialized." — *source:* `li-blip2-2023.pdf` §3.1 (p.3) — *quality:* verbatim
- **Q-Former structure** — two transformer submodules sharing the same self-attention layers: (1) an image transformer that interacts with the frozen image encoder for visual feature extraction, (2) a text transformer that can function as both text encoder and text decoder. Queries interact with each other through self-attention layers, and interact with frozen image features through cross-attention layers "(inserted every other transformer block)". Queries can additionally interact with the text through the same self-attention layers. — *source:* `li-blip2-2023.pdf` §3.1 (p.3) — *quality:* paraphrase (structure) / verbatim (quoted phrase)

**Three stage-1 pretraining objectives and their attention masks** (Figure 2 right panel, "The self-attention masking strategy for each objective to control query-text interaction"):

  - **Image-Text Contrastive Learning (ITC)** — mask: **Uni-modal Self-Attention Mask** — "where the queries and text are not allowed to see each other." Aligns image representation Z (output query embeddings) and text representation t (`[CLS]` token embedding) by maximizing mutual information; computes pairwise similarity between each query output and t, selects the highest as the image-text similarity; uses in-batch negatives (not the momentum queue used in BLIP). — *source:* `li-blip2-2023.pdf` §3.2 "Image-Text Contrastive Learning (ITC)" + Fig. 2 (p.3) — *quality:* verbatim (mask name + quoted clause) / paraphrase (mechanism)
  - **Image-grounded Text Generation (ITG)** — mask: **Multi-modal Causal Self-Attention Mask** — "similar to the one used in UniLM (Dong et al., 2019)... The queries can attend to each other but not the text tokens. Each text token can attend to all queries and its previous text tokens." The `[CLS]` token is replaced with a new `[DEC]` token as the first text token "to signal the decoding task." Since the Q-Former architecture does not allow direct interactions between the frozen image encoder and text tokens, information for text generation must first be extracted by the queries and passed to text tokens via self-attention layers. — *source:* `li-blip2-2023.pdf` §3.2 "Image-grounded Text Generation (ITG)" + Fig. 2 (p.3) — *quality:* verbatim (mask name + quoted clauses)
  - **Image-Text Matching (ITM)** — mask: **Bi-directional Self-Attention Mask** — "all queries and texts can attend to each other." Binary classification (matched/unmatched); each output query embedding fed into a two-class linear classifier, logits averaged across all queries for the output matching score; hard negative mining strategy from Li et al. (2021; 2022) used to create informative negative pairs. — *source:* `li-blip2-2023.pdf` §3.2 "Image-Text Matching (ITM)" + Fig. 2 (p.3) — *quality:* verbatim (mask name + quoted clause)

- **Figure 2 label correspondence (exact transcription)** — Fig. 2 right panel shows three grids labeled left-to-right: "Bi-directional Self-Attention Mask" under "Image-Text Matching"; "Multi-modal Causal Self-Attention Mask" under "Image-Grounded Text Generation"; "Uni-modal Self-Attention Mask" under "Image-Text Contrastive Learning." — *source:* `li-blip2-2023.pdf` Fig. 2 caption/labels (p.3) — *quality:* verbatim

**Stage 2 — connecting Q-Former to the frozen LLM:**

- **Projection mechanism** — "we use a fully-connected (FC) layer to linearly project the output query embeddings Z into the same dimension as the text embedding of the LLM. The projected query embeddings are then prepended to the input text embeddings. They function as *soft visual prompts* that condition the LLM on visual representation extracted by the Q-Former." — *source:* `li-blip2-2023.pdf` §3.3 (p.4) — *quality:* verbatim
- **Two LLM types trained differently** — decoder-based LLMs (e.g. OPT): pre-trained with the language modeling loss, frozen LLM generates text conditioned on Q-Former's visual representation. Encoder-encoder-based LLMs (e.g. FlanT5): pre-trained with the prefix language modeling loss — text split into prefix (concatenated with visual representation, fed to LLM's encoder) and suffix (generation target for LLM's decoder). — *source:* `li-blip2-2023.pdf` §3.3 (p.4) and Fig. 3 — *quality:* paraphrase
- **What is frozen / trainable per stage** — Image encoder: frozen in BOTH stages. LLM: frozen in stage 2 (not used in stage 1). Q-Former: trainable in both stages (initialized once from BERT_base + random cross-attn, then continues training into stage 2). FC projection layer: introduced and trained in stage 2 only. Figs. 1/3 mark image encoder and LLM with a "snowflake" (frozen) icon in both stage diagrams; Q-Former/FC have no such icon. — *source:* `li-blip2-2023.pdf` Fig. 1, Fig. 3, §3.3 (pp.1,4) — *quality:* paraphrase

**Trainable-parameter comparison claims:**

- Table 1 (zero-shot results overview): BLIP-2 row lists **188M** "#Trainable Params", vs. Flamingo (Alayrac et al., 2022) row **10.2B** trainable params. Abstract: "our model outperforms Flamingo80B by 8.7% on zero-shot VQAv2, while using 54× fewer trainable parameters." — *source:* `li-blip2-2023.pdf` Table 1 (p.5) + Abstract (p.1) — *quality:* verbatim
- Table 2 (zero-shot VQA comparison) gives PER-CONFIGURATION trainable/total params that differ from the 188M figure above: BLIP-2 ViT-L OPT2.7B = 104M trainable / 3.1B total; BLIP-2 ViT-g OPT2.7B = 107M / 3.8B; BLIP-2 ViT-g OPT6.7B = 108M / 7.8B; BLIP-2 ViT-L FlanT5XL = 103M / 3.4B; BLIP-2 ViT-g FlanT5XL = 107M / 4.1B; BLIP-2 ViT-g FlanT5XXL = 108M / 12.1B. Flamingo rows for comparison: Flamingo3B = 1.4B trainable / 3.2B total; Flamingo9B = 1.8B / 9.3B; Flamingo80B = 10.2B / 80B. — *source:* `li-blip2-2023.pdf` Table 2 (p.5) — *quality:* verbatim (table transcription)

⚠️ **DEFECT / apparent inconsistency** — §3.1 states the Q-Former itself "contains 188M parameters" and Table 1's single "BLIP-2" row also reports 188M trainable params, but Table 2's per-configuration breakdown reports only 103M–108M trainable params for every individual ViT/LLM combination — none of which equals 188M. The paper does not reconcile this discrepancy in the visible text (pp.3–5); it is unclear whether Table 1's 188M is a stage-1-only Q-Former figure (pre stage-2 FC-layer/config-specific trimming) or a different aggregate. Recorded as found, not resolved. — *source:* `li-blip2-2023.pdf` §3.1 vs. Table 1 vs. Table 2 (pp.3–5)

---
## Q2 — Flamingo gated cross-attention (alayrac-flamingo-2022)

- **GATED XATTN-DENSE pseudocode (verbatim, Figure 4)** —

```
def gated_xattn_dense(
    y,  # input language features
    x,  # input visual features
    alpha_xattn,  # xattn gating parameter - init at 0.
    alpha_dense,  # ffw gating parameter - init at 0.
):
    """Applies a GATED XATTN-DENSE layer."""
    # 1. Gated Cross Attention
    y = y + tanh(alpha_xattn) * attention(q=y, kv=x)
    # 2. Gated Feed Forward (Dense) Layer
    y = y + tanh(alpha_dense) * ffw(y)
    # Regular self-attention + FFW on language
    y = y + frozen_attention(q=y, kv=y)
    y = y + frozen_ffw(y)
    return y  # output visually informed language features
```
— *source:* `alayrac-flamingo-2022.pdf` Fig. 4 (p.5) — *quality:* verbatim

- **Equation form (LaTeX transcription of the same update)** —
  $$y \leftarrow y + \tanh(\alpha_{\text{xattn}}) \cdot \mathrm{attention}(q=y,\; kv=x)$$
  $$y \leftarrow y + \tanh(\alpha_{\text{dense}}) \cdot \mathrm{ffw}(y)$$
  followed by the frozen LM's own (unmodified) self-attention and FFW sublayers applied to the result. — *source:* `alayrac-flamingo-2022.pdf` Fig. 4 pseudocode, p.5 — *quality:* paraphrase (LaTeX-ized from the verbatim code above)

- **Gate initialization value** — both $\alpha_{\text{xattn}}$ and $\alpha_{\text{dense}}$ are initialized to **0** ("alpha_xattn, # xattn gating parameter - init at 0."; "alpha_dense, # ffw gating parameter - init at 0."). Confirmed in prose: "$\alpha$ is a layer-specific learnable scalar initialized to 0 [4]." (ref [4] = Bachlechner et al., "ReZero is all you need") — *source:* `alayrac-flamingo-2022.pdf` Fig. 4 pseudocode + §2.2 (p.5) — *quality:* verbatim

- **Stated reason for the 0-init** — "To ensure that at initialization, the conditioned model yields the same results as the original language model, we use a tanh-gating mechanism [41]. This multiplies the output of a newly added layer by $\tanh(\alpha)$ before adding it to the input representation from the residual connection, where $\alpha$ is a layer-specific learnable scalar initialized to 0 [4]. Thus, at initialization, the model output matches that of the pretrained LM, improving training stability and final performance." — *source:* `alayrac-flamingo-2022.pdf` §2.2 "Interleaving new GATED XATTN-DENSE layers within a frozen pretrained LM" (p.5) — *quality:* verbatim

- **Ablation of the tanh-gating mechanism itself** — Table 3 row (iii) "Tanh gating": baseline (✓, gating present) vs ablated (✗, gating removed). "We ablate the use of the 0-initialized tanh gating when merging the cross-attention output to the frozen LM output in row (iii). Without it, we see a drop of 4.2% in our overall score. Moreover, we have noticed that disabling the 0-initialized tanh gating leads to training instabilities." Table 3 row (iii) values (Flamingo-3B, DEV validation, 4-shot): baseline overall score 67.3 (top-of-table row) vs. ✗ (no gating) overall score ≈66.5 with COCO CIDEr 78.4, OKVQA 40.5, VQAv2 52.9, MSVDQA 33.9, VATEX CIDEr 47.5 — *source:* `alayrac-flamingo-2022.pdf` Table 3 + §3.3 "Visual conditioning of the frozen LM" (p.8–9) — *quality:* verbatim (prose "drop of 4.2%") / transcription (table cells, read from a small-print table image — flagged for independent re-verification if load-bearing at high precision)

- **Model-size interleaving spec ("every N layers")** — Table 5 (Appendix A.3.4, p.28), "Parameter counts for Flamingo models": frequency of GATED XATTN-DENSE relative to the frozen LM blocks, given in parentheses:
  - *Flamingo-3B*: **every** (block) — frozen LM 1.4B, trainable GATED XATTN-DENSE 1.2B, Resampler 194M, total 3.2B
  - *Flamingo-9B*: **every 4th** — frozen LM 7.1B, trainable GATED XATTN-DENSE 1.6B, Resampler 194M, total 9.3B
  - *Flamingo (80B)*: **every 7th** — frozen LM 70B, trainable GATED XATTN-DENSE 10B, Resampler 194M, total 80B
  Confirmed in prose (Appendix B.1.1, p.29): "The Flamingo-3B model builds on top of a 1.4B frozen language model... Before each transformer block, we add a GATED XATTN-DENSE layer..." / "The Flamingo-9B model builds on top of a 7B frozen language model... Starting from the very first layer and before every fourth transformer blocks, we add a GATED XATTN-DENSE layer..." / "The Flamingo-80B model builds on top of the frozen Chinchilla 70B language model... Starting from the very first layer and before every seventh transformer blocks, we add a GATED XATTN-DENSE layer..." — *source:* `alayrac-flamingo-2022.pdf` Table 5 + §B.1.1 (pp.28–29) — *quality:* verbatim
  Cross-check against Table 4 (Appendix A.1.4, p.25) layer counts: Frozen-LM layers L = 24 (3B) / 40 (9B) / 80 (80B); GATED XATTN-DENSE layers L = 24 (3B) / 10 (9B) / 12 (80B). 24/24 = every layer (3B, matches "every"); 40/10 = every 4th (9B, matches exactly); 80/12 ≈ every 6.7th (80B — "every seventh" is the stated design rule, consistent with a non-integer ratio from insertion starting at the first layer).

⚠️ **DEFECT** — Parameter-count inconsistency between Table 5 and the Appendix B.1.1 prose bullets. Table 5 lists **1.2B** trainable GATED XATTN-DENSE parameters for Flamingo-3B and **1.6B** for Flamingo-9B. But the B.1.1 prose bullets (p.29) state the added GATED XATTN-DENSE layers account for **"1.4B additional learned parameters"** for Flamingo-3B and **"1.8B additional learned parameters"** for Flamingo-9B — each 0.2B higher than the corresponding Table 5 figure. (For Flamingo-80B the two sources agree exactly at 10B.) The paper does not reconcile this; recorded as found. — *source:* `alayrac-flamingo-2022.pdf` Table 5 (p.28) vs. §B.1.1 prose (p.29)

- **Masking scheme — text token attends only to the immediately-preceding image** — "The image-causal modelling introduced in Equation (1) is obtained by masking the full text-to-image cross-attention matrix, limiting which visual tokens the model sees at each text token. At a given text token, the model attends to the visual tokens of the image that appeared just before it in the interleaved sequence, rather than to all previous images (formalized and illustrated in Appendix A.1.3). Though the model only directly attends to a single image at a time, the dependency on all previous images importantly remains via self-attention in the LM." Formal definition (Appendix A.1.3, p.24): a function $\phi : [1,L] \mapsto [0,N]$ assigns to each text position the index of the last image/video appearing before that position (or 0 if none precedes). $y_{<\ell} \triangleq (y_1,\ldots,y_{\ell-1})$ (preceding tokens), $x_{\leq \ell} \triangleq \{x_i \mid i \leq \phi(\ell)\}$ (usable preceding images/videos). — *source:* `alayrac-flamingo-2022.pdf` §2.3 (p.6) + Appendix A.1.3 + Fig. 7 caption (p.24) — *quality:* verbatim

- **Ablation of the masking choice (single-image vs. all-previous-images attention)** — Appendix Table 10 row (ii) "Multi-img att": baseline "Only last" (i.e. attend only to the single most recent previous image) vs. changed "All previous". Baseline row ("Flamingo 3B model (short training)"): COCO CIDEr 86.5, OKVQA top1 42.1, VQAv2 top1 55.8, MSVDQA top1 36.3, VATEX CIDEr 53.4, **Overall score 70.7**. Row (ii) "All previous": COCO CIDEr 70.0, OKVQA top1 40.9, VQAv2 top1 52.0, MSVDQA top1 32.1, VATEX CIDEr 46.8, **Overall score 63.5** — a drop of 7.2 points, internally consistent with the prose statement below (70.7 − 63.5 = 7.2). — *source:* `alayrac-flamingo-2022.pdf` Table 10 (p.35) — *quality:* verbatim (table transcription; numbers cross-checked against the stated 7.2-point delta for consistency)
  Prose explanation (Appendix B.3.1, p.35–36): "In the interleaved image-text scenario, we ablate whether the model can only attend to the single most recent previous image, or to all the previous images (row (ii) of Table 10). We can see that the single image case leads to significantly better results (7.2% better in the overall score). One potential explanation is that when attending to all previous images, there is no explicit way of disambiguating between different images in the cross-attention inputs... We also explored more explicit ways to enable this while attending to all previous images by modifying the image tags to include an index (`<image 1>`, `<image 2>`, etc.) and/or learning absolute index embeddings added to the cross-attention features for each image. These strategies were not as robust as our method when the number of images per sequence changes between training and test time. Such a property is desirable to reduce the number of images per sequence during training for better efficiency (we use N = 5 at training time) while still generalizing to many images for few-shot evaluation (we go up to N = 32 at test time). For these reasons, we keep the single image cross-attention strategy for the Flamingo models." — *source:* `alayrac-flamingo-2022.pdf` §B.3.1 (p.35–36) — *quality:* verbatim

---

## Q3 — Perceiver resampler (alayrac-flamingo-2022)

- **Output token count (= number of learned latent queries R)** — "This module connects the vision encoder to the frozen language model... It takes as input a variable number of image or video features from the vision encoder and produces a fixed number of visual outputs **(64)**." Confirmed in Appendix A.1.1: "The number of output tokens of the Perceiver Resampler is equal to the number of learnt latent queries." — i.e. **R = 64** learned latent queries. — *source:* `alayrac-flamingo-2022.pdf` §2.1 "Perceiver Resampler" (p.5) + Appendix A.1.1 (p.23) — *quality:* verbatim

- **Architecture / pseudocode (verbatim, Figure 5)** —

```
def perceiver_resampler(
    x_f,            # The [T, S, d] visual features (T=time, S=space)
    time_embeddings, # The [T, 1, d] time pos embeddings.
    x,              # R learned latents of shape [R, d]
    num_layers,     # Number of layers
):
    """The Perceiver Resampler model."""
    # Add the time position embeddings and flatten.
    x_f = x_f + time_embeddings
    x_f = flatten(x_f)  # [T, S, d] -> [T * S, d]
    # Apply the Perceiver Resampler layers.
    for i in range(num_layers):
        # Attention.
        x = x + attention_i(q=x, kv=concat([x_f, x]))
        # Feed forward.
        x = x + ffw_i(x)
    return x
```
— *source:* `alayrac-flamingo-2022.pdf` Fig. 5 (p.23) — *quality:* verbatim

- **Concatenation of visual features with latents in K/V (the specific design choice)** — "We learn a predefined number of latent input queries, and cross-attend to the flattened visual features $X_f$... The visual features are then flattened and concatenated as illustrated in Figure 5. The number of output tokens of the Perceiver Resampler is equal to the number of learnt latent queries. **Unlike in DETR and Perceiver, the keys and values computed from the learnt latents are concatenated to the keys and values obtained from $X_f$, which we found to perform slightly better.**" I.e. for layer $i$: $\mathrm{attention}_i(q = x,\; kv = \mathrm{concat}(X_f, x))$ — the latents $x$ contribute to their OWN key/value set in addition to querying the visual features. — *source:* `alayrac-flamingo-2022.pdf` Appendix A.1.1 (p.23) — *quality:* verbatim

- **Number of layers** — Table 4 (Appendix A.1.4, p.25), Perceiver Resampler columns (L = layers, D = hidden dim, H = heads, Act. = FFW activation): **L = 6** for ALL three model sizes (Flamingo-3B, Flamingo-9B, Flamingo-80B), D = 1536, H = 16, Act. = Squared ReLU. (By contrast the GATED XATTN-DENSE and frozen-LM layer counts scale with model size — see Q2 table above — but the Resampler is held fixed.) — *source:* `alayrac-flamingo-2022.pdf` Table 4 (p.25) — *quality:* verbatim
  Confirmed in prose (Appendix B.1.1, p.28): "We use a Perceiver Resampler with approximately 200M parameters across all three model sizes." Table 5 gives the exact figure: **194M** parameters, constant across Flamingo-3B/9B/80B. — *source:* `alayrac-flamingo-2022.pdf` §B.1.1 (p.28) + Table 5 (p.28) — *quality:* verbatim

- **Ablation: Perceiver Resampler vs. plain Transformer vs. MLP** — Table 3 row (vi) "Resampler" (Flamingo-3B, DEV validation subsets, 4-shot; each row compared to the baseline top row, Overall score 67.3): 
  - **Perceiver** (baseline/original value; not a separate ablated row — inherits the top-of-table baseline: Param 3.2B, Step 1.74s, COCO CIDEr 86.5, OKVQA 42.1, VQAv2 55.8, MSVDQA 36.3, VATEX 53.4, **Overall 67.3**)
  - **MLP**: Param 3.2B, Step 1.85s, COCO CIDEr 78.6, OKVQA top1 42.2, VQAv2 top1 54.7, MSVDQA top1 35.2, VATEX CIDEr 44.7, **Overall 66.6**
  - **Transformer**: Param 3.2B, Step 1.81s, COCO CIDEr 83.2, OKVQA top1 41.7, VQAv2 top1 55.6, MSVDQA top1 33.0, VATEX CIDEr 48.3, **Overall 66.7**
  Prose (§3.3, p.9): "We further compare in row (vi) the Perceiver Resampler to a MLP and a vanilla Transformer given a parameter budget. Both underperform the Perceiver Resampler while also being slower." — *source:* `alayrac-flamingo-2022.pdf` Table 3 row (vi) + §3.3 "Compute/Memory vs. performance trade-offs" (p.8–9) — *quality:* verbatim (prose) / transcription (table cells, read from a small-print table image — flagged for independent re-verification if load-bearing at high precision)

⚠️ **Transcription-quality flag** — Table 3's per-cell numeric values in this ledger (rows iii–viii, including the (vi) Resampler comparison above) were read by direct visual inspection of the rendered PDF page at the tool's fixed rendering resolution; the print is small (8-column dense table) and digit-level misreads (e.g. a "3" read as "8", or vice-versa) cannot be fully ruled out. The prose-quoted deltas ("4.2%", "7.2%") were cross-checked arithmetically against the transcribed cells and found internally consistent, which increases confidence in those specific rows. A follow-up pass with a higher-resolution render or the arXiv HTML/LaTeX source is recommended before citing individual table cells to more than 1 decimal place in the survey body.

---
## Q4 — LLaVA linear vs LLaVA-1.5 MLP projection (liu-llava-2023, liu-llava-1.5-2023)

**LLaVA (original) — the linear projection equation:**

- **Equation (1)** — "For an input image $X_v$, we consider the pre-trained CLIP visual encoder ViT-L/14 [40], which provides the visual feature $Z_v = g(X_v)$. The grid features before and after the last Transformer layer are considered in our experiments. We consider a simple linear layer to connect image features into the word embedding space. Specifically, we apply a trainable projection matrix $W$ to convert $Z_v$ into language embedding tokens $H_v$, which have the same dimensionality as the word embedding space in the language model:"
  $$H_v = W \cdot Z_v, \quad \text{with } Z_v = g(X_v) \tag{1}$$
  "Thus, we have a sequence of visual tokens $H_v$. Note that our simple projection scheme is lightweight, which allows us to iterate data centric experiments quickly. More sophisticated schemes to connect the image and language representations can also be considered, such as gated cross-attention in Flamingo [2] and Q-former in BLIP-2 [28]. We leave exploring possibly more effective and sophisticated architecture designs for LLaVA as future work." — *source:* `liu-llava-2023.pdf` §4.1 "Architecture", Eq. (1) (p.4) — *quality:* verbatim

**LLaVA (original) — training-stage structure (frozen vs trainable):**

- **Stage 1 — Pre-training for Feature Alignment.** CC3M filtered to 595K image-text pairs. "In training, we keep both the visual encoder and LLM weights frozen, and maximize the likelihood of (3) with trainable parameters $\theta = W$ (the projection matrix) only. In this way, the image features $H_v$ can be aligned with the pre-trained LLM word embedding. This stage can be understood as training a compatible visual tokenizer for the frozen LLM." — *source:* `liu-llava-2023.pdf` §4.2 "Training" (p.5) — *quality:* verbatim
- **Stage 2 — Fine-tuning End-to-End.** "We always keep the visual encoder weights frozen, and continue to update both the pre-trained weights of the projection layer and LLM in LLaVA; i.e., the trainable parameters are $\theta = \{W, \phi\}$ in (3)." Two use cases: Multimodal Chatbot (158K instruction data) and Science QA. — *source:* `liu-llava-2023.pdf` §4.2 "Training" (p.5) — *quality:* verbatim
- **Summary table:** Visual encoder (CLIP ViT-L/14) frozen in BOTH stages; LLM (Vicuna) frozen in Stage 1, trainable in Stage 2; Projection $W$ trainable in BOTH stages.

**LLaVA-1.5 — what the projection was changed to:**

- **"MLP vision-language connector."** "Inspired by the improved performance in self-supervised learning by changing from a linear projection to an MLP [9, 10], we find that improving the vision-language connector's representation power with a two-layer MLP can improve LLaVA's multimodal capabilities, compared with the original linear projection." — *source:* `liu-llava-1.5-2023.pdf` §3.3 "Scaling the Data and Model" (p.3) — *quality:* verbatim
- **NOT FOUND** — an explicit numbered equation for the two-layer MLP projection (e.g. an $H_v = \mathrm{MLP}(Z_v)$-style display equation with layer widths/activation spelled out) was not located anywhere in the pages read (pp.1–11) of `liu-llava-1.5-2023.pdf`. The change is described only in the prose sentence above; no equation number, activation function, or hidden-dimension is given for the MLP in the main text or appendix pages read. Recorded as absent rather than approximated.

**LLaVA-1.5 — training-stage structure:**

- Table 9 (Appendix A.3 "Hyperparameters", p.10) is explicitly split into **Pretrain** and **Finetune** columns — the same two-stage naming as LLaVA — with hyperparameters: batch size 256 (pretrain) / 128 (finetune); lr 1e-3 (pretrain) / 2e-5 (finetune); lr schedule cosine decay (both); lr warmup ratio 0.03 (both); weight decay 0 (both); epoch 1 (both); optimizer AdamW (both); DeepSpeed stage 2 (pretrain) / 3 (finetune). — *source:* `liu-llava-1.5-2023.pdf` Table 9 + §A.3 (p.10) — *quality:* verbatim (table transcription)
- **"The latest Vicuna v1.5 [60] is used as the base LLM. LLaVA-1.5 uses the same set of hyperparameters as the original LLaVA, except that we halve the learning rate in pretraining due to the usage of the MLP projection layer instead of the original linear projection layer design."** — this is the paper's only explicit statement tying the MLP-vs-linear connector change to a training-protocol adjustment (the halved pretraining LR); it also confirms LLaVA-1.5 inherits LLaVA's stage structure rather than replacing it. — *source:* `liu-llava-1.5-2023.pdf` §A.3 "Hyperparameters" (p.10) — *quality:* verbatim
- Table 3 (p.5, main results comparison) gives the pretraining/finetuning sample-size columns for LLaVA-1.5: **Pretrain 558K, Finetune 665K** (both 7B and 13B rows; 558K/665K also for the 448²-resolution LLaVA-1.5-HD row). — *source:* `liu-llava-1.5-2023.pdf` Table 3 (p.5) — *quality:* verbatim
- **Frozen/trainable component list explicitly restated for LLaVA-1.5** — NOT FOUND as an explicit restatement (of the form "we keep the visual encoder frozen and train $\{W,\phi\}$") in the pages read (pp.1–11). The paper's §3.1 "Preliminaries" states LLaVA's own protocol ("LLaVA uses a single linear layer to project the visual features to language space, and optimizes the whole LLM for visual instruction tuning") as the framework being built on, and §A.3 confirms LLaVA-1.5 "uses the same set of hyperparameters as the original LLaVA" apart from the pretraining LR halving — strongly implying the same frozen-vision-encoder / two-stage freeze pattern carries over unchanged, with the MLP replacing $W$ as the trained connector — but no sentence in the read pages restates the freeze pattern explicitly for LLaVA-1.5 itself. Recorded as inferred-from-continuity, not verbatim.

**LLaVA-1.5's roadmap/ablation table isolating the connector change — Table 2 (p.4), "Scaling results on data, model, and resolution":**

Incremental build-up on GQA / MME / MM-Vet (all rows below use LLM=7B, Res.=224 unless noted; each row adds ONE change on top of the row above it):

| # | Change (cumulative) | LLM | Res. | GQA | MME | MM-Vet |
|---|---|---|---|---|---|---|
| — | InstructBLIP (14B) | 14B | 224 | 49.5 | 1212.8 | 25.6 |
| 0 | **LLaVA** | 7B | 224 | – | 809.6 | 25.5 |
| 1 | +VQA-v2 | 7B | 224 | 47.0 | 1197.0 | 27.7 |
| 2 | +Format prompt | 7B | 224 | 46.8 | 1323.8 | 26.3 |
| 3 | **+MLP VL connector** | 7B | 224 | **47.3** | **1355.2** | **27.8** |
| 4 | +OKVQA/OCR | 7B | 224 | 50.0 | 1377.6 | 29.6 |
| 5 | +Region-level VQA | 7B | 224 | 50.3 | 1426.5 | 30.8 |
| 6 | +Scale up resolution | 7B | 336 | 51.4 | 1450 | 30.3 |
| 7 | +GQA | 7B | 336 | 62.0* | 1469.2 | 30.7 |
| 8 | +ShareGPT | 7B | 336 | 62.0* | 1510.7 | 31.1 |
| 9 | +Scale up LLM | 13B | 336 | 63.3* | 1531.3 | 36.1 |

Row 9 = "LLaVA-1.5" (final model, all modifications). `*` = training images of GQA observed during training. — *source:* `liu-llava-1.5-2023.pdf` Table 2 (p.4) — *quality:* verbatim (table transcription)

- **The connector-change-alone row is row 3 ("+MLP VL connector"), delta from row 2 (its immediate predecessor, holding LLM/Res./all other changes fixed):**
  - GQA: 46.8 → 47.3 (**+0.5**)
  - MME: 1323.8 → 1355.2 (**+31.4**)
  - MM-Vet: 26.3 → 27.8 (**+1.5**)
  This is the paper's own incremental-ablation design (§3.3 text: "As shown in Table 2, by merely including VQAv2 [19] in training, LLaVA's performance on MME significantly improves (1323.8 vs 809.6) and outperforms InstructBLIP by 111 points" — note this specific quoted sentence compares row 0 vs a different combination, illustrating the paper's own reading convention for this table: each row's score is compared to its immediate predecessor to isolate that row's change). — *source:* `liu-llava-1.5-2023.pdf` Table 2 + §3.3 (p.3–4) — *quality:* verbatim (quoted sentence) / paraphrase (delta computation, arithmetic on the transcribed cells)

⚠️ **DEFECT / scope caveat** — Table 2's row 3 ("+MLP VL connector") isolates the connector-architecture change ONLY under the specific cumulative configuration already including "+VQA-v2" (row 1) and "+Format prompt" (row 2) — i.e., the +0.5/+31.4/+1.5 deltas are the MLP's marginal contribution **on top of** those two prior changes, not the MLP's effect on stock LLaVA (row 0) in isolation. The paper does not provide a separate ablation isolating linear-vs-MLP on the row-0 (bare LLaVA) configuration. This is exactly the kind of "a cause measured in one configuration is not established for the others" scoping the calibration-residuals rule flags — the connector-alone contribution reported above is scoped to the row-2→row-3 transition and should not be generalized to a different training-data configuration without re-measurement.

---

## Summary of gaps (NOT FOUND items) across all four questions

- Flamingo-3B's exact per-layer GATED XATTN-DENSE frequency ("every") is confirmed via Table 5, but no separate prose sentence states an "N-th layer" fraction for Flamingo-3B the way it does for 9B/80B (it is simply every block, consistent with Table 4's L=24=24).
- LLaVA-1.5's exact MLP projector equation/activation/hidden-width was NOT FOUND in the pages read (§3.3, Appendix A pp.1–11) — described only in prose as "a two-layer MLP".
- LLaVA-1.5's explicit restatement of which components are frozen/trainable (vision encoder frozen, connector+LLM trainable in stage 2) was NOT FOUND verbatim for LLaVA-1.5 itself in the pages read — inferred from "same hyperparameters as the original LLaVA" continuity language, not a direct quote.
- Table 3 (BLIP-2) and Table 10 (Flamingo main-text ablation table) and Table 2/3 (LLaVA-1.5) numeric cells were transcribed by direct visual inspection of small-print rendered PDF pages; several deltas were cross-checked arithmetically against paper prose (BLIP-2's "8.7%"/"54×" claims, Flamingo's "4.2%"/"7.2%" claims) and found internally consistent, which raises confidence in those specific rows, but individual untested cells carry residual transcription risk.

