---
id: 2026-06-17-02
title: "Q/K/V appendix: self-contained math + non-load-bearing web citations for the circuit framing"
status: accepted
date: 2026-06-17
plan: (ad-hoc request — fold the trained-Q/K/V derivation into surveys/llms-for-coding as Appendix A)
---

## Context

Appendix A derives what trained attention `W_Q, W_K, W_V` mean. Three external
works are relevant: the attention mechanism (Vaswani et al. 2017, ref [54],
held locally in `download/`) and the framing this appendix leans on — the
QK/OV-circuit decomposition (Elhage et al. 2021) and induction heads (Olsson et
al. 2022). The latter two are published only on `transformer-circuits.pub`
(no arXiv/PDF), so they can only carry the **weak `(web)` source tag**, which
`.claude/rules/citation-integrity.md` forbids load-bearing claims from resting
on. The question was how to credit the framing honestly without violating that
rule.

## Decision

Present every derivation as **self-contained first-principles math** — the
QK/OV collapse (Eqs 3–4), the gauge-freedom proof (Eq 5), the kernel-regression
and matched-filter readings, the `√d_k` second-moment argument (Eq 7), the SVD
routing decomposition (Eq 8), the hand-built induction head (Eq 9), and the
softmax-gradient co-adaptation (Eqs 11–12) — so **no claim is load-bearing on a
weak reference**. Cite [54] (strong/local) for the mechanism, the `√d_k`
footnote, and the multi-head structure; cite [59] Elhage 2021 and [60] Olsson
2022 (weak/web) only for the QK/OV-circuit *terminology* and the *empirical
existence* of induction heads, explicitly non-load-bearing. All three sources
were read before citing (Vaswani PDF pp. 3–5; both web articles WebFetched with
verbatim quotes confirming the attributed phrasing).

## Alternatives considered

- **Fetch arXiv/PDF versions of [59]/[60] to upgrade them to `local`.**
  Rejected: neither is on arXiv; they are native web publications.
- **Drop the QK/OV-circuit terminology entirely (pure descriptive names).**
  Rejected: the terminology credits the originating literature and helps a
  reader connect the appendix to mechanistic-interpretability work; the cost
  (two web refs) is acceptable once they are non-load-bearing.
- **Make A.9 an empirical claim resting on [60].** Rejected: kept the induction
  head a *constructive* first-principles demonstration (`M` and `W_OV` built by
  hand, no training), so the section's math stands alone and [60] only supplies
  the "this is observed in real models" motivation.

## Consequences

- The appendix is robust to the weak-reference scrutiny of the `citation-audit`
  skill: the review workflow's citation arm passed it, and
  `check-citation-sources.py` is green (60 entries; 50 strong / 9 web / 1
  abstract-only; 0 errors).
- Establishes a reusable pattern for survey sections that lean on web-only
  interpretability sources: derive the math self-contained, cite the web source
  for terminology/empirics only.

## Refs

- `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` (refs [54],[59],[60]).
- review workflow run `wf_7fba1273-8b7` (citation-accuracy arm: PASS).
- field-note `field-notes/2026-06-17-qkv-appendix.md`.
- conversation log `prompts/2026-06-17-viewer-sync.md` (Conversation 5).
