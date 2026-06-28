# Multimodal Large Language Models: A First-Principles Survey

_A deep-research survey of models that extend a transformer language model to perceive and generate
image, video, and audio — the encoder→connector→LLM stack, training recipes, any-to-any generation,
evaluation, current practice, and open gaps._

**Status:** under construction (Phase 4 synthesis). Mode: proposed · scale: wide · audience: learner.
The section plan, research questions, and depth tiers live in `_scratch/outline.md`; the confirmed
research brief in `_scratch/brief.md`.

## Reading guide

This survey is written for a reader with strong mathematical maturity but light deep-learning / LLM
background (the **learner** register): prerequisites are derived from first principles, results are
motivated with intuition and signal-processing analogies before the algebra, and worked numerical
examples lead. Readers fluent in transformers can skim the fundamentals and start at the architecture
building blocks.

## Depth-tier legend (R-GOV)

Every method and load-bearing result carries one of three depth tiers:

- **Headline** — full first-principles derivation + worked numerical example + a conceptual figure.
- **Load-bearing** — derivation + intuition + complexity, without the full worked example.
- **Catalog-only** — stated result + a one-line applicability note, with an explicit `n/a (reason)` for
  each heavier artifact deliberately skipped.

Survey quality is measured as coverage over the headline and load-bearing items, not by prose volume.

## Notation contract

One symbol, one meaning, fixed convention — reused exactly in every section (this is the externalized
"symbol memory" of the memory-guided synthesis). Extended as sections are authored.

| Symbol | Meaning | Convention / units | Defined in |
|---|---|---|---|
| $x_t$ | a text token (discrete id) | integer index into the text vocabulary $V_t$ | Fundamentals |
| $x_v$ | a raw visual input (image) | tensor in $\mathbb{R}^{H \times W \times C}$, $C$ channels | Fundamentals |
| $P$ | patch side length (pixels) | image split into $(H/P)\,(W/P)$ square patches | Fundamentals |
| $N_v$ | number of visual tokens fed to the LLM | $N_v = HW/P^2$ before any resampling | Fundamentals |
| $d$ | model (residual-stream) width | per-token embedding dimension of the LLM | Fundamentals |
| $f_v(\cdot)$ | the (often frozen) vision encoder | maps $x_v$ to patch features in $\mathbb{R}^{N_v \times d_v}$ | Fundamentals |
| $g_\phi(\cdot)$ | the connector / projector | maps encoder features into the LLM token space $\mathbb{R}^{d}$ | Architecture |
| $p_\theta(\cdot)$ | the language model (decoder) | autoregressive token distribution, params $\theta$ | Fundamentals |
| $\tau$ | contrastive temperature | scalar $>0$ scaling cosine similarities (CLIP) | Fundamentals |
| $\mathrm{sim}(a,b)$ | cosine similarity | $a^\top b / (\lVert a \rVert\, \lVert b \rVert)$ | Fundamentals |
| $\mathcal{C}$ | the discrete codebook | $K$ learned vectors $e_k \in \mathbb{R}^{d_c}$ (VQ-VAE) | Generation |
| $z_q$ | quantized latent | nearest codebook vector to the encoder output $z_e$ | Generation |
| $\mathrm{nats}$ | log base for all entropies/losses | natural log unless a result states bits | global |

Throughout, **bold lowercase** denotes a column vector, **non-bold capital** a matrix, **non-bold lowercase**
a scalar (with the usual carve-outs, e.g. sequence length and head count). Logits are pre-softmax; losses are
per-token averages unless stated otherwise.

## Contents

The ordered section manifest is `order.json`. Heavy derivations live in Appendices A–F; a reader's-questions
Q&A is Appendix Q; all citations resolve in `references.md`.
