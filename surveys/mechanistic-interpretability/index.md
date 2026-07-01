# Mechanistic Interpretability: A First-Principles Survey

_A deep-research survey of the program that reverse-engineers the internal computations of neural
networks — chiefly transformer language models — into human-understandable **features** and
**circuits**: the mathematical fundamentals (residual-stream framework, the linear representation
hypothesis, superposition), the full method inventory (probing and lenses, causal patching,
automated circuit discovery, sparse autoencoders and their variants, steering and model editing,
circuit tracing), worked circuit case studies across models (toy → GPT-2 → Pythia → Gemma 2 →
Claude 3, with the field's vision-model roots), evaluation, current frontier practice, and open
problems._

**Status:** under construction. Mode: `proposed` · scale: `wide` · audience: `practitioner`.
The confirmed research brief and section plan live in `_scratch/brief.md` and `_scratch/outline.md`;
the section-level evidence ledgers in `_scratch/ev-*.md`.

## Reading guide

This survey is written for a reader with strong mathematical maturity and working deep-learning
background (the **practitioner** register): standard ML/DL prerequisites are assumed or
forward-referenced, each load-bearing result carries one intuition box, and worked numerical
examples follow a derivation as a self-checking oracle. Where a signal-processing analogy sharpens
a result — the matched filter behind an induction head's readout, basis pursuit / overcomplete
dictionaries behind sparse autoencoders, the discrete Fourier transform behind the grokking
circuit — it is stated as a tight one-liner, not as the primary scaffolding.

Read the **fundamentals** (residual stream, QK/OV circuits, linear representations, superposition)
first: every later method is an operation on that substrate. Readers already fluent in the
transformer-circuits framework can skim it and start at the **methodology & taxonomy**, then the
**method inventory**.

## Depth-tier legend (R-GOV)

Every method and load-bearing result carries one of three depth tiers. Survey quality is measured
as coverage over the headline and load-bearing items, **not** by prose volume.

- **Headline** — full first-principles derivation + worked numerical example + a conceptual figure.
  (residual-stream/QK-OV framework; superposition/toy models; activation patching; sparse
  autoencoders; induction-head & IOI circuits.)
- **Load-bearing** — derivation + intuition + complexity, without a full worked example.
  (logit/tuned lens; attribution patching; ACDC/EAP; DAS; SAE variants; steering / RepE; ROME;
  transcoders/crosscoders; auto-interp; attribution graphs.)
- **Catalog-only** — stated result + a one-line applicability note, with an explicit `n/a (reason)`
  for each heavier artifact deliberately skipped. (probing micro-variants; BatchTopK / Matryoshka;
  causal-scrubbing internals; feature visualization / vision heritage.)

## Notation contract

One symbol, one meaning, fixed convention — reused in every section. Throughout, **bold lowercase**
is a column vector, **non-bold capital** a matrix, **non-bold lowercase** a scalar (with the usual
count carve-outs: layer count $L$, head count $H$, dimensions $d$, sparsity $k$, sample size $n$).
Logits are pre-softmax; losses are per-token averages in nats unless a result states otherwise.

| Symbol | Meaning | Convention / units | Defined in |
|---|---|---|---|
| $\mathbf{x}$ | a residual-stream activation (one position) | column vector in $\mathbb{R}^{d}$ | Fundamentals |
| $d$ | residual-stream width (model dimension) | $d_{\text{model}}$; per-token embedding size | Fundamentals |
| $L$, $\ell$ | number of layers; layer index | integers, $\ell = 1,\dots,L$ | Fundamentals |
| $W_E$, $W_U$ | embedding, unembedding matrices | token space $\leftrightarrow \mathbb{R}^{d}$; $\lvert V\rvert$ = vocab size | Fundamentals |
| $H$, $h$ | heads per layer; head index | integers | Fundamentals |
| $d_{\text{head}}$ | per-head dimension | typically $d/H$ | Fundamentals |
| $W_Q^h, W_K^h, W_V^h, W_O^h$ | per-head query/key/value/output maps | each rank $\le d_{\text{head}} \ll d$ | Fundamentals |
| $W_{QK}^h$ | query–key circuit | $W_Q^h (W_K^h)^\top$; $d\times d$, rank $\le d_{\text{head}}$ | Fundamentals |
| $W_{OV}^h$ | output–value circuit | $W_O^h W_V^h$; $d\times d$, rank $\le d_{\text{head}}$ | Fundamentals |
| $A$ | attention pattern | row-stochastic; $A_{ij}$ = weight dest $i$ on src $j$ | Fundamentals |
| $\mathbf{f}$ | dictionary / SAE feature-activation vector | column vector in $\mathbb{R}^{d_{\text{sae}}}$, sparse, $\ge 0$ | Dictionary learning |
| $\mathbf{d}_i$ | dictionary atom (SAE decoder column) | unit-norm direction in $\mathbb{R}^{d}$ | Dictionary learning |
| $d_{\text{sae}}$ | dictionary size (SAE width) | $d_{\text{sae}} = R\,d$; $R$ = expansion factor | Dictionary learning |
| $W_{\text{enc}}, W_{\text{dec}}$ | SAE encoder, decoder | matrices; $\hat{\mathbf{x}} = W_{\text{dec}}\mathbf{f} + \mathbf{b}_{\text{dec}}$ | Dictionary learning |
| $\lambda$ | sparsity-penalty coefficient | scalar $\ge 0$ (L1 weight) | Dictionary learning |
| $L_0$ | sparsity | mean nonzero features / token, $\mathbb{E}\lVert\mathbf{f}\rVert_0$ | Evaluation |
| $k$ | TopK sparsity | exact active-feature count / token | Dictionary learning |
| $\theta$ | JumpReLU threshold | per-feature scalar $\ge 0$ | Dictionary learning |
| $\mathcal{M}$ | behavioral metric | scalar; e.g. logit difference correct$-$incorrect | Causal methods |
| $x_{\text{clean}}, x_{\text{corrupt}}$ | paired inputs for patching | clean prompt vs. counterfactual/corrupted | Causal methods |
| $\mathbf{v}$, $c$ | steering vector; steering coefficient | $\mathbf{v}\in\mathbb{R}^{d}$ added to stream; $c$ scalar | Steering |
| $\mathbf{k}_*, \mathbf{v}_*$ | ROME key, value vectors | column vectors (MLP hidden, residual) | Editing |
| $C$ | ROME preserved-key second moment | $C = KK^\top$ over corpus keys | Editing |
| $R$ | DAS rotation matrix | orthogonal, $R^\top R = I$ | Causal methods |

## Contents

The ordered section manifest is `order.json`. Fundamentals and the five-file method inventory carry
the main exposition; heavy derivations live in Appendices A–E; a reader's-questions Q&A is Appendix
Q; every external citation resolves in `references.md` under the source-tag invariant.
