# Plan — LLM-Anatomy Appendix Series (Appendices C–H)

**Goal.** A deep, first-principles anatomy of LLM structure, climbing the size
ladder from a toy model to a frontier MoE. Each chapter dissects one model
top-structure to single-neuron, with end-to-end math (forward + full backward +
one optimizer step, no step missing), deep intuition, and many diagrams.

**Status.** Plan increment. Outline below drives the build; chapters land one per
increment, each `/check-survey`-green + `citation-audit`ed + committed.

## Locked decisions (user, 2026-06-19)

1. **Placement** — appendix series in the existing `llms-for-coding` survey
   (`appendix-c…appendix-h`), extending Appendix A, sharing `references.md`, no
   main-text renumbering. Each appendix is one letter with `C.1`, `D.1`, … subsections.
2. **Structure** — *scale-primary*: one chapter per model size, each a complete
   top-to-neuron anatomy.
3. **Math scope** — forward + full backprop + optimizer (Adam), end-to-end.
4. **Model set** — code-LLMs already in `download/` PLUS general frontier models
   (GPT-2/GPT-3, Llama-2/3, DeepSeek-V3).

**Repetition handling (default, to honor "no step missing" without 5x copy-paste).**
The toy chapter (C) derives every invariant in full. Chapters D–G are complete
anatomies of their model but fully re-derive only what is *distinctive* at that
rung (new components / new dials); identical invariant derivations are
cross-linked back to C with `secxref`. Every step is therefore derived and
reachable across the corpus, established once.

## Anatomy template (every chapter follows this top-to-neuron walk)

1. Whole-model view: token IDs → embedding → `L` decoder blocks → final norm →
   unembedding → logits → softmax/loss; the residual stream; parameter/FLOP/memory accounting.
2. One decoder block: pre-norm, attention sublayer, FFN sublayer, residual adds.
3. One attention head: QKV projections, scores, mask, softmax, OV; multi-head; (variant: MHA/MQA/GQA).
4. The FFN down to one neuron: the two linear maps, the nonlinearity/gating, what a single hidden unit computes.
5. Norm + positions + output head: the chapter's norm and positional scheme; unembedding/tying.
6. Forward worked end-to-end, then **backward** module-by-module, then **one Adam step**.
7. Intuition box per module (signal-processing analogies for the SP reader).

## Chapter ladder

- **C — toy transformer (calibration).** 1–2 layers, char-level, tiny explicit
  numbers. The full from-scratch build: every forward step, every gradient, one
  Adam update, all worked with concrete arithmetic. Figures: whole-model schematic;
  block zoom; attention head with a worked score/softmax; FFN → single neuron;
  the backward pass (gradient flow); one Adam step. Mostly first-principles (minimal external sourcing).
- **D — GPT-2 scale (124M–1.5B).** Canonical dense decoder: learned positional
  embeddings, pre-norm LayerNorm, GELU MLP, tied unembedding. Sources: GPT-2 (+GPT-3 for scale).
- **E — 7B modern dense (Llama-class).** Distinctive: RMSNorm, RoPE (rotation /
  relative-position property), SwiGLU gating, grouped-query attention — each derived in full. Sources: Llama-2/3, RMSNorm, SwiGLU, RoPE (have).
- **F — 33B–70B dense scaling.** DeepSeek-Coder-33B (have) / Llama-3-70B: what
  grows vs stays as depth/width/heads scale; the accounting at this rung.
- **G — frontier MoE.** DeepSeek-V3 / DeepSeek-Coder-V2 (have V2): the MoE block,
  router + top-k gating derived, sparse vs total/active params, MLA, long context.
- **H — synthesis + scaling accounting.** The ladder side by side; parameter /
  FLOP / memory formulas toy→frontier; "same anatomy, different dials" table +
  figures; link to scaling laws (section 3.6). Final whole-series citation-audit.

## Per-chapter build pipeline

outline → source concrete values (citation-integrity; `download/` + `source-fetch`)
→ derive math in the marked / `aligned` style (the `/enrich-equation` discipline)
→ write intuition → design+build figures (workflow judge + adversarial-audit →
deterministic `.py`→`.svg`) → embed → wire `order.json` + `index.md` → full
renumber/validate sweep (`/check-survey`) → `citation-audit` → commit.

Parallelize evidence extraction, figure-design panels, and faithfulness audits via
workflows; keep all synthesis/writing in the main thread (deep-research-survey rule).

## Sourcing to acquire (Appendix #26 task)

GPT-2, GPT-3, Llama-2, Llama-3, DeepSeek-V3, RMSNorm, GLU/SwiGLU, LayerNorm, Adam.
Already present: RoPE (`su-rope`), Switch-Transformer (MoE), DeepSeek-Coder-V2,
Chinchilla/Kaplan (scaling), DeepSeek-Coder-33B, Qwen/StarCoder2 dims, Vaswani.

## Increment order

0 (this): plan + decisions committed. 1: Appendix C (calibration) — build complete,
review point. 2–6: D, E, F, G one per increment (source just-in-time). 7: H +
series-wide citation-audit. Refs: decisions `2026-06-19-01`; tasks #25–#32.
