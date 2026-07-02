---
slug: fastv-followups
date_filed: 2026-07-02
status: open
---

# FastV vision-token pruning (B1) — follow-on work

## Context
The `fastv-pruning` study (`docs/fastv-vision-token-pruning-implementation-study.md`, G1 PASS)
confirmed FastV's attention-collapse phenomenon (H1: 68× deep-layer text/image ratio) on real
SmolVLM-256M, but **refuted H3** (attention-ranked pruning lost to random) on a uniformly-redundant
synthetic color task, root-caused to task-redundancy + attention-sink retention. FastV needs a
query-localized regime to show its advantage.

## What is left
- **Query-localized eval** — multi-object images ("what colour is the *circle*?"), counting, or
  OCR-style tasks where the answer lives in a specific region; H3 (attn > random) should hold there.
- **Inverse-ranking control** — prune the *highest*-attention tokens; if accuracy is preserved, it
  confirms the retained high-attention tokens are semantically-empty sinks (the §7 hypothesis).
- **Real VQA benchmarks** (Flickr30K / A-OKVQA / MMMU) via a bandwidth host — the paper's own suite.
- **K-sweep** (prune after layers {0,2,5,10}) — the paper's second knob.
- **Physical token removal** (not attention-masking) — realise the Eq-5 FLOP savings, not just the
  analytic curve; requires re-indexing positions + pixel-value bookkeeping.
- **Full 1088-token split** with a memory-efficient per-layer attention reduction (hook + reduce to
  received-attention, discard the (T,T) matrix) — restores the high-redundancy regime.

## Acceptance
On a query-localized task, attention-ranked FastV pruning holds accuracy above random at matched
FLOP-reduction up to a knee (reproducing Chen Fig 1); or a documented reason SmolVLM-256M cannot.

## Refs
- Study `docs/fastv-vision-token-pruning-implementation-study.md`; code `implementation/fastv/`.
- Parent handoff `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (candidate 1).
- Source `download/chen-fastv-2024.pdf`.
