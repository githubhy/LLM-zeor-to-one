---
id: 2026-07-01-03
title: Fold in-context-learning inspection into the tiny-transformer plan as first-class hypotheses (H8 mechanistic + H9 source-gated algorithmic)
status: accepted
date: 2026-07-01
plan: plans/2026-06-30-tiny-transformer-induction-study.md
---

## Context

The reviewer asked whether the tiny-transformer induction study can *inspect
in-context learning (ICL)*. The plan already carried strong latent ICL hooks —
**H2** tests that the in-context loss (loss vs token position, explicitly named
"the ICL score" in the Phase-1 metrics) drops at a phase change, and Phase 2
makes TransformerLens a required analysis dependency (activation caching +
head ablation). But "we measure an ICL signature" was implicit, spread across
H2 and the metrics line, and the causal step (ablate the head → does ICL
collapse?) was tooling-available but never stated as an experiment. There are
also **two distinct senses** of ICL: (i) the *mechanistic* induction-copying
sense (Olsson et al. co-emergence, the survey's [60]) and (ii) the *algorithmic*
"forward pass ≈ gradient-descent / ridge step" sense (the `icl-as-online-
learning-intuition` todo, sources not yet fetched). The reviewer selected
"all" — fold both senses in, plus the real-scale GPT-2 ICL test.

## Decision

Promote ICL inspection to first-class scope with two new pre-registered
hypotheses: **H8 (mechanistic ICL)** — the ICL score co-emerges with the
induction head and is causally carried by it (ablation collapses it;
random-head control intact; generalization control rules out memorization),
measured on the from-scratch rungs (Phase 3 co-emergence overlay + Phase 4
ablation battery) and at the pretrained-GPT-2 rung (Phase 4b real-ICL
ablation); and **H9 (algorithmic ICL, source-gated)** — an in-context
linear-regression sub-study probing whether the forward pass tracks an explicit
online learner, added to §6 stretch as a **hard-gated** extension that may not
be executed until the `icl-as-online-learning-intuition` source-fetch todo
closes (no external claim from memory, per citation-integrity).

## Alternatives considered

- **Leave ICL implicit (H2 + metrics only).** Rejected: the causal ablation and
  the co-emergence overlay are the payoff that turns a correlational induction
  study into an ICL-mechanism study, and they were unstated.
- **Add only the mechanistic sense (H8), skip H9.** Rejected: the reviewer chose
  "all"; the algorithmic sense is a genuinely different and valuable reading —
  but it is real added scope (a new task + a new circuit), so it is scoped as
  stretch, not MVP.
- **Write H9 with its literature now (von Oswald / Akyürek / Dai / Garg).**
  Rejected outright by citation-integrity: those sources are not in `download/`;
  H9 is hard-gated on the existing source-fetch todo.
- **File H8's ablation as MVP.** Rejected: the co-emergence overlay (Phase 3)
  is MVP; the causal-ablation battery lives in Phase 4 (sensitivity/ablation),
  so MVP establishes H8's co-emergence part with the ablation strengthening it.

## Consequences

- **Enables:** a causal ICL story (ablate → collapse) on both toy and real
  weights, reusing the already-required TransformerLens hooks — near-zero new
  compute for H8.
- **Adds scope:** H9 introduces a new in-context-regression task and a
  GD/ridge-matching probe; it stays behind a hard source-fetch gate, so it
  cannot silently execute on memory-sourced citations.
- **Forecloses nothing;** the induction/QK-OV spine is unchanged.
- **Follow-up:** the H9 source-fetch is tracked in
  `todos/2026-06-28-icl-as-online-learning-intuition.md` (now also the plan's
  H9 hard gate). The plan remains a draft awaiting review.

## Refs

- Plan: `plans/2026-06-30-tiny-transformer-induction-study.md` §1, §2 (H8/H9),
  §3 Phase 1/3/4/4b, §6, §4, §9.
- Prior plan decisions: `decisions/2026-07-01-01` (GPT-2 ladder),
  `decisions/2026-07-01-02` (grokking derive-now/cite-later).
- Deferred: `todos/2026-06-28-icl-as-online-learning-intuition.md` (H9 gate).
- Survey anchors: §A.9, §A.18, §A.20, §A.11 (mechanistic); §A.6/§A.16
  (matched-filter *detection* vs stack-level optimization contrast for H9);
  published anchor [60] (induction↔ICL co-emergence).
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md`.
