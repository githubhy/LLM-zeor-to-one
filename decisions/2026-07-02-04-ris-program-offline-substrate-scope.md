---
id: 2026-07-02-04
title: RIS program (A2/A3/B1/B2/C) — substrates under an offline host reached only via a local HTTPS proxy
status: accepted
date: 2026-07-02
plan: docs/eap-ig-faithfulness-implementation-study.md (A2), and per-track study docs
---

## Context
User goal: run `reference-implementation-study` in **proposed** mode on all five candidate
tracks nominated by the two survey handoffs — A2 (EAP-IG faithfulness), A3 (steering
head-to-head), B1 (FastV vision-token pruning), B2 (connector ablation), C (SAE-frontier
follow-ons) — autonomously, commit each step, then push → PR → merge.

Execution host reality (probed 2026-07-02):
- **Offline by default**: direct HTTPS to `huggingface.co` times out; direct is unusable.
- **A local proxy exists** (`http_proxy=https_proxy=http://127.0.0.1:10086`). Through it,
  `huggingface.co` + the Xet weight CDN (`us.aws.cdn.hf.co`) return 200; **downloads work but
  are slow (~214 KB/s)**. User directive on the multimodal blocker was explicitly "try the
  network again, check proxy settings" — the proxy is the resolution.
- **No CUDA**; Apple-Silicon MPS only, 16 GB unified RAM. `transformer_lens` not installed and
  unfetchable-fast. `gpt2` (124M) + `wikitext` are already cached; **no Gemma, no VLM cached**.

## Decision
Run each track on the **largest substrate that is faithful to the method's claim AND runnable
on this host**, mirroring the precedent set for the SAE study (decision 2026-07-02-01):

- **A2 (EAP-IG)** → **GPT-2-small + IOI/Greater-Than**. This is *not* a downscale: GPT-2-small is
  the actual substrate of Hanna et al. (2024) and the IOI/Greater-Than datasets are templated
  (self-generated, no download). EAP/EAP-IG/exact-patching implemented on the HF GPT-2 via manual
  hooks (no `transformer_lens`).
- **C (SAE follow-ons)** → extend `implementation/sae_frontier/` on synthetic + cached-GPT-2
  activations. Gemma-scale port stays deferred (already `todos/2026-07-02-sae-frontier-followups`).
- **A3 (steering)** → **GPT-2-small-scaled** (prompting vs diff-in-means vs SAE-feature clamp),
  SAE via the sae_frontier infra. User-confirmed (AskUserQuestion). Gemma/AxBench absolute scale
  → todo. Faithful to the *method-ordering* claim, not the absolute AxBench numbers.
- **B1 (FastV)** → **SmolVLM-256M (Idefics3)**, a real early-fusion VLM downloaded via the proxy
  (~518 MB PyTorch weights, onnx/ skipped). Faithful reproduction of the visual-token
  attention-decay → prune-tolerance mechanism at small scale; LLaVA-1.5/DocVQA absolute scale → todo.
- **B2 (connector ablation)** → real-but-tiny (frozen SmolVLM vision encoder + small LM, MLP vs
  Q-Former projector, small image-text task). If offline data acquisition or from-scratch connector
  training proves infeasible within the host's bandwidth/compute, **author the RIS plan + defer
  execution via a `todos/` entry** rather than fabricate results.

Every downscaled track carries a **do-not-cite clause** for absolute production numbers and files
the production-scale port as a `todos/` follow-on — same honesty contract as the SAE study.

## Alternatives considered
- **Refuse the GPU/offline-blocked tracks outright** — rejected: the proxy makes B1 feasible and
  the claims for A2/A3/C are substrate-relative, so real work is possible.
- **Synthetic toy-VLM for B1/B2** — superseded for B1 by the real SmolVLM download (strictly more
  faithful); retained only as the B2 fallback shape if data won't download.
- **Full Gemma-2 / LLaVA-1.5 / DocVQA reproduction** — rejected: ungettable-or-too-slow offline,
  too large for 16 GB / MPS. Deferred to a GPU+bandwidth host as todos.

## Consequences
- Enables: five genuine, reproducible studies on this host; A2 is fully faithful (paper's own
  substrate), B1 uses a real VLM.
- Forecloses: production-scale absolute numbers (flagged do-not-cite per study, Sec. 0/Sec. 2
  conformance IDEALIZED rows).
- Follow-up: production-scale ports + B2's fallback → `todos/` (filed per track at sign-off).

## Refs
- Precedent: decision `2026-07-02-01` (SAE substrate scope); `todos/2026-07-01-mechinterp-ris-handoff`,
  `todos/2026-06-28-multimodal-llms-reference-impl-handoff`.
- Env probe + proxy diagnosis: conversation log `prompts/2026-07-02-branch-cleanup.md`.
- Skill: `.claude/skills/reference-implementation-study` (proposed mode, all 13 items).
