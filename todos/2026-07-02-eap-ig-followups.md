---
slug: eap-ig-followups
date_filed: 2026-07-02
status: open
---

# EAP-IG faithfulness study — follow-on work

## Context
The `eap-ig-faithfulness` reference-implementation study (`docs/eap-ig-faithfulness-implementation-study.md`,
G1+G2 PASS, EAP-IG reproduced as more faithful than EAP: +0.224 @ n=20, p=3.6e-34, ρ=0.92 vs 0.46)
ran at **head+MLP node granularity + top-n circuits** on GPT-2-small (decision 2026-07-02-04). Its
§7 root-causes the per-task divergence from Hanna et al.'s edge-level Fig 3 into granularity /
search / operating-point; these are the deferred items to close that gap.

## What is left
- **Edge-level graph** with split q/k/v input edges (full 32,491-edge parity with the paper); the
  node-level reduction is what inflates the IOI gap and hides the GT small-n gap.
- **Greedy circuit search** (Hanna §4.2) instead of top-n by |score| — greedy is ≥ as faithful, so
  the current EAP curve is a lower bound.
- **The 3 omitted tasks** (Gender-Bias, Capital-Country, Hypernymy) — need word-list generators or a
  small download; would complete the 6-task spectrum.
- **EAP-IG-KL** (KL-divergence loss variant, Hanna): applicable to all tasks, non-zero gradient on
  the clean input.
- **TransformerLens cross-check** once installable (network/pip) — parity vs the paper's own harness.
- **Reduced-precision *compute*** (bf16/fp16 forward+backward attribution) — Phase 5 only tested
  reduced-precision score *storage* (bf16/fp16 quant of scores, zero drift); compute-precision was
  blocked (MPS lacks fp16/bf16 support for some attribution ops; fp16 matmul emulated-slow on CPU).
  Re-run on a CUDA host for real compute-precision drift/saturation.

## Acceptance
An edge-level + greedy re-run reproduces Hanna Fig 3's per-task ordering (IOI small gap, SVA
catastrophic-until-large-n), closing the §7 divergence; or a documented reason it cannot on GPT-2-small.

## Refs
- Study `docs/eap-ig-faithfulness-implementation-study.md` §7, §11; code `implementation/eap_ig/`.
- Parent handoff `todos/2026-07-01-mechinterp-ris-handoff.md` (candidate 2); bug `2026-07-02-04`.
- Source `download/hanna-eap-ig-faithfulness-2024.pdf`.
