# Connector Ablation — Reference Implementation Study (Track B2)

**Study:** `connector-ablation`  **Topic:** `implementation/connector/`
**Mode:** `proposed`. **Substrate:** frozen SmolVLM-256M SigLIP vision encoder + a small frozen
text decoder; **trainable connector only** (decision `2026-07-02-04`).
**Parent handoff:** `todos/2026-06-28-multimodal-llms-reference-impl-handoff.md` (candidate 2);
survey `surveys/multimodal-llms/architecture.md` §3.3.
**Sources:** MLP projector `(local: download/liu-llava-1.5-2023.pdf)`; Q-Former `(local:
download/*blip*)` — **read before citing specifics**.

## 0. Executive summary

> **Status: Phase 1 (scenario).** Execution decision recorded below.

## 1. Problem, scope & candidates

The connector maps frozen vision features → the LLM token space. Two families (survey §3.3):

- **MLP projector** (LLaVA-1.5): a 2-layer MLP maps *each* patch feature to one LLM token — high
  fidelity, token count = #patches (expensive).
- **Q-Former bridge** (BLIP-2): `q` learnable query tokens cross-attend the patch features → `q`
  tokens (q ≪ #patches) — cheap, but a bottleneck that may drop fine detail.

**Hypothesis (survey §3.3, qualitative → to quantify):** at matched/larger token budget the MLP
projector wins on **detail-sensitive** tasks (fine attributes) while the Q-Former wins on
token-efficiency; the fidelity–vs–budget tradeoff is the §3.3 claim to make numeric.

**Metric.** attribute-identification accuracy (Wilson CI) as a function of connector token budget
`q`, for MLP vs Q-Former; the detail-sensitivity gap = accuracy on fine-grained attributes.

**Substrate.** Frozen SigLIP vision features (from SmolVLM-256M) + a small frozen LM head; train
*only* the connector on a synthetic image→attribute task (controllable detail: color+shape+count).

## 2. Execution decision

Real-scale B2 (a Q-Former/MLP trained on a real image-text corpus, LLaVA-1.5 recipe) is **infeasible
on this offline host** — from-scratch connector *training* + a multi-GB image-text dataset exceed the
bandwidth/compute budget that already scoped A2/A3/B1 down (decision `2026-07-02-04`). Two honest paths:

- **(a) real-but-tiny** — freeze SmolVLM's SigLIP encoder, train an MLP projector vs a small
  learnable-query cross-attention (Q-Former-style) on synthetic image→attribute data, into a tiny
  frozen classification head; sweep `q`, measure the detail/budget tradeoff. Genuine but toy-scale.
- **(b) plan + defer** — this document + a `todos/` entry; execute on a GPU + bandwidth host.

**Status: see `todos/2026-07-02-connector-ablation.md`** — filed for tracking; execution path chosen
at run time based on the remaining session budget (real-but-tiny preferred if time allows, else defer;
no fabricated results either way).

## 3.–13. Phases 2–6

Pending the execution path. If run: module map (`implementation/connector/`), verification anchor =
the MLP projector at q=#patches must ≥ the Q-Former at q≪#patches on detail tasks (the §3.3
prediction); baseline accuracy vs `q` with Wilson CI; reproduce recipe + seeds; audit trail
(decision `2026-07-02-04`).
