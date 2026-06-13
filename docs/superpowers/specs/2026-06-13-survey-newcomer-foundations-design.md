# Design Spec — Newcomer Foundations Enrichment for the LLMs-for-Code Survey

**Date:** 2026-06-13
**Topic:** Add first-principles, newcomer-friendly foundations (basics, architectures/structures, training methods) to `surveys/llms-for-coding/`.
**Status:** approved design (pending spec review).

## Goal & Audience

The survey is strong for an ML-literate reader but assumes the reader already knows tokens, embeddings, the Transformer, attention, and modern training. Enrich it so a newcomer can build the foundations from first principles.

Target reader (from user): **signal-processing background — very comfortable with math, almost no DL/LLM knowledge.** Implications:
- Use math freely (linear algebra, probability, optimization, Fourier).
- Explain DL/LLM machinery from scratch (what a neural net / embedding / attention / Transformer is; pretrain to fine-tune to align).
- Lean on SP analogies the reader owns: autoregressive LM as a learned nonlinear generalization of AR(p); self-attention as data-dependent / adaptive filtering with correlation-based weights (contrast fixed-kernel convolution); softmax as soft arg-max; positional encodings (sinusoidal, RoPE) as Fourier basis / phase; cross-entropy as negative log-likelihood / KL; tokenization as discretization.

## Approach (user-selected: 2 + 3)

**Option 2 — new standalone primer section, AND Option 3 — distributed intuition/diagrams.**

### A. New Section 3 — "Language Models from First Principles" (the primer)

Inserted after Section 2 (Scope), before History (so History's encoder/decoder/FIM references are already grounded). The existing FIM/pass@k "Conceptual and Mathematical Fundamentals" section is **folded in** as the primer's closing subsections (general foundations build up to the code-specific machinery in one unified section).

Subsections:
1. **3.1 A language model is an autoregressive predictor.** Define p(next token | previous tokens); the next-token training objective as maximum likelihood / cross-entropy (equiv. negative log-likelihood / KL). Analogy: AR(p) predictive models generalized to a learned, nonlinear, discrete-output system. Worked example: predicting the next token of a code line. (Subsumes the old code-AR-objective material.)
2. **3.2 Tokens and embeddings.** Text -> discrete symbols (tokenization as quantization/symbol mapping); embedding as a learned vector in R^d. Tiny example tokenizing a short function signature.
3. **3.3 Attention and the Transformer.** Self-attention as data-dependent weighted averaging; weights = softmax of query-key dot-product similarities (matched-filter / correlation intuition); contrast fixed-kernel convolution. Q/K/V, multi-head, the block (attention + MLP + residual + normalization). Diagram + small numeric attention example.
4. **3.4 Architectural structures.** Encoder-only vs decoder-only vs encoder-decoder, and why code LLMs are decoder-only. Brief variants: MHA/MQA/GQA, mixture-of-experts, positional encodings (sinusoidal and RoPE, framed via Fourier/phase). Architecture family-tree diagram.
5. **3.5 How a model is trained.** The arc pretrain -> fine-tune -> align at intuition level (optimization of a loss; what each stage changes). Pipeline diagram + autoregressive generation-loop diagram. Forward-pointers to the detailed sections.
6. **3.6 Scaling laws (fuller mathematical treatment).** Power-law scaling of loss in parameters N, data D, and compute C (Kaplan et al.): L ~ X^(-alpha) forms. The Chinchilla parametric loss L(N,D) = E + A/N^alpha + B/D^beta; the compute budget C ~= 6ND; and the compute-optimal allocation derived as a constrained optimization (Lagrange multiplier) giving N_opt, D_opt ~ C^0.5 and the "tokens ~ 20x params" rule. All exponents and constants reproduced from the acquired Kaplan and Chinchilla papers (mandatory acquisition; load-bearing numbers). Figure: a log-log loss-vs-compute power law and the IsoFLOP / compute-optimal frontier (ASCII, since mermaid does not plot functions). Connects forward to the code-data-mixture and deliberate-over-training points in the pretraining sections (SP analogy: bias-variance / rate-distortion-style tradeoff between model capacity and data).
7. **3.7 Tokenization for code.** (Folded from old fundamentals.) Whitespace/indentation pressure; byte-level BPE; whitespace-run tokens; vocab sizes.
8. **3.8 Fill-in-the-middle.** (Folded.) The document-rewriting transform (PSM/SPM), sentinels, FIM-for-free; the numbered FIM equation.
9. **3.9 Measuring correctness: pass@k.** (Folded.) The unbiased estimator and the numerically stable form; why functional correctness over BLEU.

### B. Distributed enrichment (option 3)

Targeted, non-duplicating additions where the detailed treatment already lives — each ~2-3 sentence SP-flavored intuition opener plus (where useful) one diagram:
- **Pretraining sections** — a data -> tokens -> objective intuition + small diagram.
- **Alignment section** — RL as optimization against a reward; DPO as a classification loss (intuition).
- **Reasoning section** — test-time compute as trading inference cost for accuracy (intuition).
- Use a consistent bold "Intuition." callout lead-in so newcomers can skim.

### C. Diagrams & examples

~8-10 diagrams. **Mermaid** (structure/flow, renders in the viewer and on GitHub, fenced so the math linter skips it): Transformer block; attention as data-dependent weighted combination; causal vs bidirectional attention masks (decoder vs encoder); architecture family tree; mixture-of-experts routing; training pipeline (pretrain -> SFT -> align); autoregressive generation / KV-cache loop; plus the distributed-section diagrams. **Non-mermaid** (function plots, as ASCII since mermaid cannot plot functions): a log-log loss-vs-compute scaling curve and the IsoFLOP / compute-optimal frontier. ~3-4 concrete worked numeric examples (tokenization, attention numbers, next-token prediction, a compute-optimal allocation calculation). Net new content ~4-6k words.

### D. New citations (acquired full-text, never from memory)

Acquire via source-fetch and append as references [54]+ (append-only; no renumber of existing refs):
- Vaswani et al., "Attention Is All You Need" (the Transformer) — mandatory.
- Kaplan et al. 2020 and Hoffmann et al. 2022 (Chinchilla) — **mandatory and load-bearing** for the scaling-laws math (3.6); the power-law exponents, the parametric-loss constants, and the compute-optimal rule are reproduced from the PDFs (not memory).
- Su et al., RoPE — positional encodings.
- Optionally a mixture-of-experts primary (e.g., Switch Transformer / Shazeer et al.) if 3.4's MoE treatment cites specifics.
The user welcomes additional citations: acquire any further primaries the content needs (e.g., BERT/GPT for encoder/decoder if leaning on them beyond the existing CodeBERT [2] / Codex [1]). Every new numeric/claim citation is verified against the acquired PDF locus before it lands.

### E. Renumber + verification mechanism

Net section change: insert primer at 3, fold old fundamentals into it, so **only History shifts (3 -> 4)**; Section 5 through Section 18 keep their numbers; References stays last (TOC 19).

Steps:
1. Create the new primer file; add it to `order.json` at index 3 (after scope, before history); remove the old fundamentals file from `order.json`.
2. Move the FIM/pass@k/code-tokenization content into the primer as subsections 3.7-3.9; relabel its eq markers from the 4-x to the 3-x id space (alongside the new equations in 3.6).
3. History file: renumber heading and subsections 3 -> 4 (3.x -> 4.x) and its prose self-references.
4. Prose cross-reference swap across all files: "Section 3" (History) -> "Section 4"; "Section 4" (old fundamentals / FIM / pass@k) -> "Section 3". First confirm no `secref`/`secxref` linked forms exist (grep); the survey uses plain "Section N" prose refs.
5. `index.md` TOC: insert primer at 3, History -> 4, drop the standalone fundamentals line.
6. Run the cross-link init pass (renumber-sections/paragraphs --init, link-references --init), then the full `/check-survey` gate, then a cross-reference verification (every "Section N" mention resolves to a real section; every equation/section anchor exists). Under ultracode, run the verification as a fan-out check and citation-audit the new refs.

## Acceptance criteria

- New Section 3 primer reads coherently for the target reader: each DL concept introduced from first principles with an SP analogy, math intact, at least the diagrams and examples listed.
- FIM/pass@k content preserved (no loss) as the primer's closing subsections; equations still numbered and referenced correctly.
- Scaling-laws subsection (3.6) gives the power-law forms, the Chinchilla parametric loss, and the compute-optimal derivation as numbered equations, with all exponents/constants reproduced from the acquired Kaplan and Chinchilla papers (citation-audited).
- Only History changed number (3 -> 4); Section 5-18 numbers unchanged; all prose "Section N" cross-refs resolve to the intended sections.
- Distributed intuition added to the named sections without duplicating the primer.
- `/check-survey` green (lint-math, equation/section/paragraph anchors, cross-file links, bare-refs at error severity, reference source tags).
- New references are full-text `local:` and citation-audited (numbers reproduced from source).

## Out of scope

- No change to the survey's overall coverage or conclusions; this is an additive pedagogical layer.
- No vendor/product comparisons; no offline-vendoring of the CDN math libs.
- Existing staff-level depth in later sections is preserved, not diluted.
