---
slug: blocked-backlog-consolidated
date_filed: 2026-07-03
status: open
---

# Blocked backlog — items correctly tracked-but-blocked (umbrella)

## Context

During the 2026-07-02/03 research sessions (tiny-transformer induction study + the
concurrent RIS-program), a set of follow-ups was identified that **cannot be
executed on the current host** (Windows, CPU-only, no GPU, no upstream-repo
checkout, and — for another session's studies — not ours to modify). For each,
the *correct* disposition is a documented blocker + unblock condition, not a
forced attempt. This umbrella is the single place a future session (or a
GPU/upstream-equipped one) looks for "what's parked and why." Each item keeps its
own detailed todo; this file is the consolidated index + rationale.

## What is left (grouped by blocker)

### 1. GPU-gated — needs a rented multi-GPU host

- **`gpt2-training-reproduction`** (`todos/2026-07-01-gpt2-training-reproduction.md`)
  — reproduce GPT-2 124M training from scratch at real scale (~3 wk on a laptop;
  needs multi-GPU to watch 124M emergence, H2/H4).
- **Tiny-transformer compute-heavy rungs**
  (`todos/2026-07-02-tiny-transformer-gpu-host-rungs.md`) — **Rung 2** mini-GPT-2
  (~10M from scratch), **full-scale Rung 1** (`n_ctx=256`, 20k steps, ≥5 seeds; the
  CPU pass used `n_ctx=64`/800), and the auto-interp source-fetch (Bundle K).
  - *Unblock:* GPU host → run `implementation/tiny_transformer/run_phase3.py` at the
    full config, then re-run Phase 4/4b/5; also enables the heavier deferred
    hypotheses (H15/H16/H18 at scale) the study report §11 defers.

### 2. Another session's studies (RIS-program, PR #2) — not ours to modify

Touching these risks conflicts with the owning session; they need substrates this
host lacks. Owned/tracked by their own todos:

- **`eap-ig-followups`** — edge-level graph (q/k/v split, 32,491-edge parity),
  greedy search, 3 omitted tasks, EAP-IG-KL, TransformerLens cross-check.
- **`steering-followups`** — LLM-judge coherence, generation-level success, **Gemma-2
  substrate + GemmaScope SAEs**.
- **`fastv-followups`** — query-localized eval, **real VQA**, K-sweep, physical token
  removal (H3 failed on the synthetic task).
- **`sae-frontier-followups`** — **Gemma-scale** port, JumpReLU STE robustness,
  BatchTopK/Matryoshka, widen S2.
- **`connector-ablation`** — real-scale port (real LLM head + **DocVQA/TextVQA**).
  - *Unblock:* the owning session picks them up (or an explicit handoff) + GPU /
    Gemma-2 / real-VQA-dataset access.

### 3. Upstream-repo ports — need `../data-channel-receiver` and/or the viewer e2e env

- **`port-multispan-highlight-fix-upstream`** — port the local `viewer.js` multi-span
  inline-math highlight fix (bug `2026-06-19-01`) to the upstream viewer.
- **`fix-serve-api-md-eisdir-crash`** — `serve.js /api/md/<dir>` EISDIR crash (bug
  `2026-06-17-01`); fix upstream then re-sync.
- **`citation-t12-e2e-timeout`** — a viewer e2e test whose `page.goto` never settles
  (likely env, not a regression).
  - *Unblock:* the upstream repo checked out (for the ports) + a working Playwright
    viewer e2e harness (for the timeout).

## Acceptance

Each sub-item is resolved in its own todo (this umbrella is superseded/closed when
all three groups clear). Until then it stays `open` as the living index of parked
work; picking any item up means editing *its* todo, not this one.

## Refs

- Individual todos listed above; study report `docs/tiny-transformer-induction-study.md` §11.
- Decisions `2026-07-02-04` (RIS-program offline-substrate scope, other session),
  `2026-07-02-05` (tiny-transformer execution approach).
- Conversation log `prompts/2026-06-29-viewer-serve-launcher.md` (Conv 70–71).
