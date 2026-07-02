---
slug: steering-followups
date_filed: 2026-07-02
status: open
---

# Steering head-to-head (A3) — follow-on work

## Context
The `steering-headtohead` study (`docs/steering-headtohead-study.md`, G1 PASS) reproduced
AxBench's *SAE-clamp-is-worst* result on GPT-2-small but **flipped** the prompting-vs-diff-in-means
order (diff-in-means > prompting here). §7 root-causes the flip to metric alignment + KL-not-judge
coherence + GPT-2-small's weak instruction-following. AxBench's ordering (prompt > diff-mean > SAE
for steering) was verified from `download/wu-axbench-2025.pdf` §Abstract/§2.

## What is left
- **LLM-judge coherence + generation-level success.** Replace next-token-logprob success with a
  judged rating of a generated continuation, and KL-coherence with judge-rated fluency — the AxBench
  protocol. This is the specific gap that flips the prompting/diff-in-means order.
- **Gemma-2-2B/9B substrate** (AxBench's own models, instruction-tuned) via a GPU host — prompting
  should recover its lead there.
- **GemmaScope SAEs** for the SAE-clamp method (vs the toy TopK SAE trained here on 280 samples).
- **Multi-concept** (AxBench suite) instead of the single sentiment concept.

## Acceptance
On Gemma-2 with an LLM judge, reproduce AxBench's prompt > diff-mean > SAE steering ordering; or a
documented reason GPT-2-small cannot.

## Refs
- Study `docs/steering-headtohead-study.md`; code `implementation/steering/`.
- Parent handoff `todos/2026-07-01-mechinterp-ris-handoff.md` (candidate 3).
- Source `download/wu-axbench-2025.pdf`.
