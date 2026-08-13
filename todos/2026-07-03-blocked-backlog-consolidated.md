---
slug: blocked-backlog-consolidated
date_filed: 2026-07-03
status: closed
---

# Blocked backlog — items correctly tracked-but-blocked (umbrella)

**Resolution.** Closed 2026-08-13, not rewritten — none of the three blockers below
still holds, and **group 2 below is factually wrong; read it as history, not status.**

- **Group 3** cleared 2026-07-05 (Windows → Mac host move); already marked ✅ in place.
- **Group 2's premise died on 2026-07-02**, when PR #2 merged. The five RIS studies are
  not "another session's, not ours to modify" — `implementation/` on `main` carries all
  eight study packages. The blocker outlived its truth by six weeks because nothing
  re-reads an umbrella when the world changes underneath it.
- **Group 1 is no longer a blocker but the next piece of work**: per
  `decisions/2026-08-13-01`, `tiny-transformer-gpu-host-rungs` Rung 2 is the first
  topic, and `gpt2-training-reproduction` is shrunk and held behind it.

Not rewritten as a live index because that is what made it stale: a second consolidated
index beside `todos/INDEX.md` drifts from it. `INDEX.md` is the index. Each item below
keeps its own todo, which is where status actually lives.

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

### 3. Upstream-repo ports — ✅ CLEARED 2026-07-05 (Mac host)

**Unblocked** by the Windows→Mac host move: `../data-channel-receiver` is now
checked out and the Playwright viewer e2e harness works. All three resolved this
session:

- **`port-multispan-highlight-fix-upstream`** — ✅ closed; ported to upstream
  `viewer.js` (branch byte-identical to local), spec green, proven red-without-port.
- **`fix-serve-api-md-eisdir-crash`** — ✅ closed; `/api/md/` isFile() guard applied
  to both copies (byte-convergent), regression test proven red-without-fix (bug
  `2026-06-17-01` → fixed).
- **`citation-t12-e2e-timeout`** — ✅ closed; confirmed environmental (deterministic
  on Mac), hardened T12 goto → `domcontentloaded` + content wait, mirrored upstream.

## Acceptance

Each sub-item is resolved in its own todo (this umbrella is superseded/closed when
all three groups clear). Until then it stays `open` as the living index of parked
work; picking any item up means editing *its* todo, not this one.

## Refs

- Individual todos listed above; study report `docs/tiny-transformer-induction-study.md` §11.
- Decisions `2026-07-02-04` (RIS-program offline-substrate scope, other session),
  `2026-07-02-05` (tiny-transformer execution approach).
- Conversation log `prompts/2026-06-29-viewer-serve-launcher.md` (Conv 70–71).
