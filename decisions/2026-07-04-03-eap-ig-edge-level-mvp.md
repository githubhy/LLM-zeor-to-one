---
id: 2026-07-04-03
title: EAP-IG edge-level built on raw `transformers` (reimplemented split-qkv forward), MVP = IOI+SVA
status: accepted
date: 2026-07-04
plan: plans/2026-07-04-eap-ig-edge-level.md
---

## Context

The `eap-ig-faithfulness` study's §7 divergence from Hanna Fig 3 needed an edge-level engine
(32,491 q/k/v-split edges + greedy). The existing engine (`implementation/eap_ig/`) is node-level
and, deliberately, does **not** use TransformerLens (which is offline-unavailable here). Two
judgment calls the plan flagged: how to obtain the per-(head, q/k/v)-slot residual-input
gradients (Hanna Eq 1 takes the gradient w.r.t. the downstream node's *input*), and how much of
the 6-task spectrum to run.

## Decision

- **Reimplement the split-qkv forward on raw `transformers`.** Compute each head's q/k/v from a
  separate grad-retained copy of the block's residual input (replicating TransformerLens's
  `split_qkv_input`), reusing the model's own `ln_1`/`ln_2`/`ln_f`/`mlp`/`c_proj`/`lm_head`
  modules so autograd handles the LayerNorm and the forward reproduces GPT-2 (verified to 9e-5).
  This avoids both the TransformerLens dependency and a manual LayerNorm-Jacobian.
- **MVP = IOI + SVA** (the two Fig-3 anchors that close the divergence) + greedy + recursive
  edge-ablation + the verification gates + `sim-audit`. Defer the 3 extra tasks, EAP-IG-KL,
  TransformerLens cross-check (offline), and reduced-precision to `todos/2026-07-02-eap-ig-followups`.
- **Validate against the trusted node engine** via the edge→node identity
  (`node_score(u) == Σ_v edge_score(u→v)`, holds to 5e-7) plus the ablation boundary checks
  (all-in==clean, all-out==corrupt, exact) — rather than against TransformerLens.

## Alternatives considered

- **Manual LayerNorm-Jacobian mapback** from the c_attn-output gradient to residual space.
  Rejected: error-prone (the LN Jacobian is position-dependent) and unnecessary — per-head
  residual copies get it from autograd for free.
- **Wait for TransformerLens** (network install). Rejected: offline host; and the raw
  reimplementation is independently verifiable (logits-match + edge→node identity), which is
  stronger evidence than trusting an opaque dependency.
- **Full 6-task + EAP-IG-KL now.** Rejected for MVP: IOI+SVA are the two tasks Hanna Fig 3's
  ordering hinges on; they suffice to close §7. The rest is breadth, filed as deferred.
- **Edge-level exact patching** as a third anchor. Rejected: 32,491 single-edge patches is
  intractable; node-level exact patching remains the ground-truth anchor.

## Consequences

- The divergence closes (IOI EAP≈EAP-IG gap 0.024; SVA EAP catastrophic, EAP-IG faithful, the
  embed→m0 rank-1-vs-74 smoking gun) — `docs/eap-ig-edge-level-study.md`, verdict
  `divergence_closed=True`.
- The reimplemented forward carries a ~1e-3 float-accumulation offset vs GPT-2 (disclosed §10);
  metrics match to 4 dp, so it does not affect any verdict.
- Single-seed / n_examples=15 / 2-of-6-tasks are IDEALIZED/DEVIATED in the conformance matrix;
  the *ordering* (the acceptance criterion) is claimed, absolute magnitudes are do-not-cite.

## Refs

- Plan `plans/2026-07-04-eap-ig-edge-level.md`; report `docs/eap-ig-edge-level-study.md`.
- Code `implementation/eap_ig/edges.py`, `edge_model.py`, `edge_attribution.py`, `edge_greedy.py`,
  `edge_run.py`, `edge_figure.py`; tests `tests/eap_ig_edge/` (16 gates).
- Sources `download/hanna-eap-ig-faithfulness-2024.pdf`, `download/syed-eap-2023.pdf`.
- Parent decision `2026-07-02-04` (node-level scope); todo `2026-07-02-eap-ig-followups`;
  field-note `field-notes/2026-07-04-eap-ig-edge-level.md`.
