---
id: 2026-07-02-01
title: SAE-frontier study scoped to synthetic-oracle + GPT-2-small (not Gemma-2-2B)
status: accepted
date: 2026-07-02
plan: docs/sae-frontier-implementation-study.md
---

## Context
The RIS handoff (`todos/2026-07-01-mechinterp-ris-handoff.md` candidate 1) named **Gemma-2-2B via
Gemma Scope** as the substrate for the SAE fidelity–sparsity frontier reproduction. Reality: the
execution host is a 17 GB Apple-Silicon Mac (MPS, no CUDA); Gemma-2 is gated, and a Gemma-Scope-scale
SAE *training* reproduction (millions of latents, billions of tokens) does not fit RAM/time. User
confirmed (AskUserQuestion) `proposed` mode + the synthetic-oracle + GPT-2-small substrate.

## Decision
Run the study on **S1 (synthetic superposition, ground-truth oracle) + S2 (GPT-2-small residual
activations)** at commodity scale. The hypotheses (H1–H4) are *architecture-relative* — the shrinkage
mechanism and the Pareto ordering are testable wherever superposed activations exist — so this is a
faithful test of the mechanism, fully reproducible on commodity hardware. The Gemma-scale run becomes
a Phase-6 recommendation + a `todos/` follow-on (GPU host).

## Alternatives considered
- **Full Gemma-2-2B reproduction** — rejected: infeasible on 17 GB / MPS; gated.
- **Pretrained Gemma Scope eval-only** — rejected for now: ~5 GB+ weights strain RAM, gated, slow/fragile.
- **Synthetic-only** — rejected: drops the survey's headline loss-recovered metric (S2 adds real-model realism).

## Consequences
- Enables: a rigorous, deterministic, fully-reproducible study **with a ground-truth feature-recovery
  oracle S1 that even Gemma-scale studies cannot measure** (a strength, not just a compromise).
- Forecloses: production-scale absolute numbers — flagged with a do-not-cite clause (report Sec. 0).
- Follow-up: `todos/2026-07-02-sae-frontier-followups.md` (Gemma-scale port).

## Refs
- Report `docs/sae-frontier-implementation-study.md` Sec. 1, Sec. 2 (conformance IDEALIZED row).
- Conversation log `prompts/2026-07-01-mechinterp-survey.md`.
