---
slug: connector-ablation
date_filed: 2026-07-02
status: open
---

# Connector ablation (B2) — execution tracking

**Update 2026-07-02.** The **real-but-tiny** path LANDED — study `connector-ablation`
(`docs/connector-ablation-implementation-study.md`, G1 PASS): MLP-pool vs Q-Former across q on
frozen SigLIP features. Null result (budget not the bottleneck at toy scale; Q-Former ≥ MLP on the
detail axis by ≤0.008). The **real-scale port** below (real LLM head + DocVQA/TextVQA) remains open.

## Context
Candidate 2 of the multimodal-LLMs handoff. Real-scale (Q-Former/MLP trained on a real image-text
corpus, LLaVA recipe) is infeasible offline (decision 2026-07-02-04). Chosen path: **real-but-tiny**
— frozen SmolVLM-256M SigLIP features (1024×768) + small trainable MLP-pool vs Q-Former connectors +
a 2-head classifier, on synthetic color/shape data; sweep token budget q.

## What is left (real-scale port, deferred to a GPU + bandwidth host)
- Real connectors into a real LLM (not a linear classifier head) trained on a real image-text corpus.
- Real detail-sensitive benchmarks (DocVQA / TextVQA — the survey §3.3 target).
- Matched-FLOP / matched-training-compute comparison, not just matched token budget.

## Acceptance
The toy study lands (`docs/connector-ablation-implementation-study.md`, G1 + report); the real-scale
port reproduces the §3.3 MLP-fidelity-vs-Q-Former-budget tradeoff on DocVQA/TextVQA.

## Refs
- Study `docs/connector-ablation-implementation-study.md`; code `implementation/connector/`.
- Parent handoff `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (candidate 2).
