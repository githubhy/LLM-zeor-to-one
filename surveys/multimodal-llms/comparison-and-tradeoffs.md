<!-- sec:10 -->
## <a id="sec-10"></a>10 Comparison and tradeoffs

<a id="p-10-comparison-and-tradeoffs-1"></a><!-- para:10-comparison-and-tradeoffs-1 --> The method inventory of § <!-- secxref:4 -->[§4](method-inventory.md#sec-4) catalogued systems one at a time; this section reads them *across*, as positions in the design space of § <!-- secxref:3.1 -->[§3.1](architecture-building-blocks.md#sec-3.1). Two synthesis artifacts do the work: a master comparison matrix that places every full-system method on the same axes, and a decision table that inverts it — given a deployment target, which design to reach for. This is a headline-depth synthesis: the matrix is the single load-bearing table the whole survey builds toward, and the decision table is its actionable inverse.

<!-- sec:10.1 -->
### <a id="sec-10.1"></a>10.1 The master comparison matrix

<a id="p-101-the-master-comparison-matrix-1"></a><!-- para:101-the-master-comparison-matrix-1 --> Each row is a full multimodal system; the columns are the axes of § 3 plus the training and cost facts that decide deployment. "Generates" marks whether the model can *emit* a non-text modality, not merely read one. Component encoders (CLIP, SigLIP, ViT — § <!-- secxref:4.1 -->[§4.1](method-inventory.md#sec-4.1)–<!-- secxref:4.3 -->[§4.3](method-inventory.md#sec-4.3)) and the VQ tokenizer (§ <!-- secxref:4.11 -->[§4.11](method-inventory.md#sec-4.11)) are not rows — they are the shared parts the rows are built from.

| System | Entry point | Connector | Fusion | Resolution | Generates | Trained vs frozen | Defining cost / assumption |
|---|---|---|---|---|---|---|---|
| Flamingo | CLIP-style encoder | Perceiver Resampler (64) | deep cross-attn | fixed | text only | LM frozen | many new cross-attn params; many-image native |
| BLIP-2 | frozen encoder | Q-Former (32) | early (soft prompt) | fixed | text only | encoder + LM frozen | Q-Former needs its own pretraining; detail loss |
| LLaVA-1.5 | CLIP encoder | MLP projector | early concat | 336 fixed | text only | LLM fine-tuned | tokens grow with resolution; forgetting risk |
| LLaVA-NeXT | CLIP encoder | MLP + AnyRes tiles | early concat | AnyRes (tiled) | text only | LLM fine-tuned | tile count multiplies the token bill |
| Qwen2-VL | native-res ViT | MLP + windowed | early concat | native dynamic | text only | fine-tuned | M-RoPE; token count varies with image size |
| InternVL | large (≈6B) encoder | MLP projector | early concat | tiled | text only | staged tuning | a vision tower at LLM scale to train/serve |
| Fuyu | none (raw patches) | linear patch proj. | native-as-input | arbitrary | text only | trained | no CLIP prior; more data to reach quality |
| Chameleon | none (VQ tokens) | none | native-token | 512 fixed | image + text | from scratch | full pretrain; image quality capped by VQ |
| Emu3 | none (VQ tokens) | none | native-token | fixed | image+text+video | from scratch | full pretrain; pure next-token |
| Transfusion | VAE latents | linear / U-Net | AR text + diffusion image | latent | image + text | from scratch | two objectives + a sampler to balance |
| Janus | SigLIP + VQ (dual) | dual adaptors | AR (decoupled) | 384 | image + text | staged | two visual encoders to maintain |

<a id="p-101-the-master-comparison-matrix-2"></a><!-- para:101-the-master-comparison-matrix-2 --> Reading the matrix top to bottom traces the field's history and its tradeoff structure at once. The frozen-LM designs (Flamingo, BLIP-2) buy stability and many-image capability at the price of new parameters and a language model that cannot adapt to vision. The early-fusion projector designs (the LLaVA line, Qwen2-VL, InternVL) dominate open practice because they are simple and strong, and they differ mainly in *how they buy resolution* — fixed, tiled, or native — which is the same § <!-- secxref:8.1 -->[§8.1](inference-and-serving.md#sec-8.1) token-cost decision under three names. The from-scratch designs (Chameleon, Emu3, Transfusion) are the ones that can *generate*, and they split on the § <!-- secxref:6.4 -->[§6.4](multimodal-generation.md#sec-6.4) axis — discrete-AR for unification, diffusion for fidelity — while Janus refuses to pick a single visual representation at all. No row dominates; each is a different point on the capability-versus-cost-versus-forgetting surface § <!-- secxref:3.5 -->[§3.5](architecture-building-blocks.md#sec-3.5) named.

<!-- sec:10.2 -->
### <a id="sec-10.2"></a>10.2 The decision table

<a id="p-102-the-decision-table-1"></a><!-- para:102-the-decision-table-1 --> Inverting the matrix gives the practitioner's view: start from the target, read off the design. The recommendations below are the survey's load-bearing engineering claims, each tracing to the section that justifies it.

| Deployment target | Reach for | Why (section) |
|---|---|---|
| Documents, OCR, charts, small text | high-resolution early fusion (LLaVA-NeXT AnyRes or Qwen2-VL native), MLP projector, *no* aggressive token reduction | detail lives below the patch scale; it needs tokens (§ 2.2, § 8.1) |
| Many images / few-shot / interleaved prompts | deep fusion (Flamingo-style) or a token-reducing resampler | per-image token cost must stay bounded (§ 3.3, § 3.4) |
| The LLM must stay frozen (no fine-tuning budget) | deep fusion (Flamingo) or the Q-Former bridge (BLIP-2) | both keep the LM's weights untouched (§ 3.5) |
| Any-to-any generation, unification first | native-token AR (Chameleon / Emu3) | one vocabulary, one loss reads and writes (§ 6.1) |
| Any-to-any generation, image quality first | a diffusion hybrid (Transfusion) | no lossy tokenizer in the image path (§ 6.2) |
| Strong at *both* understanding and generation | decoupled encoders (Janus) | one encoder is a compromise between the two (§ 6.3) |
| Edge / tight token or memory budget | resampler connector plus LLM-side pruning (FastV) | fewest visual tokens carried, then fewest attended (§ 8.2) |
| Audio understanding | a Whisper encoder plus a projector (Qwen-Audio) or window-Q-Former (SALMONN) | reuse the pretrained speech front-end (§ 7.1) |

<a id="p-102-the-decision-table-2"></a><!-- para:102-the-decision-table-2 --> Two cross-cutting rules of thumb fall out of the table. First, *resolution is bought in tokens, and tokens are paid for quadratically* — so every "improve quality" lever (higher resolution, more tiles, more frames) is also a "raise cost" lever, and the right design is the cheapest one that clears the task's detail threshold, not the highest-resolution one available. Second, *the freezing schedule follows the data budget*: with little instruction data and a precious LLM, freeze it and adapt through a connector or cross-attention; with enough data to fine-tune safely, early fusion's simplicity wins. These two rules, plus the § <!-- secxref:6.4 -->[§6.4](multimodal-generation.md#sec-6.4) generation dichotomy, are most of what a designer needs to place a new requirement on the map. The design-guidance section turns them into a step-by-step procedure.
