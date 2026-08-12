# Phase 2: Reference Implementation

## Goal
Implement each candidate with a uniform interface and shared utilities.

## Constraints
- Each candidate as a **frozen dataclass** with uniform call interface (`.generate(x)`, `.run(x)`, `.predict(x)`, `.score(x)`, `.forward(x)` — pick what fits).
- Return `(output, telemetry_dict)` so callers can inspect internals (logits, attention stats, token counts, retrieval hits).
- Support `.replay(x, state_history)` when the method has time-varying internal state (e.g. an autoregressive KV-cache or streaming decode state).
- All implementations must be **pure**: deterministic given config + input, explicit random seeds and decoding params, no hidden mutable state.
- Named constants for numerical-safety floors (`EPSILON_DIV = 1e-12`, softmax / log-sum-exp / normalisation epsilons, etc.).
- Input validation at construction time (`__post_init__`).

## File Layout
- `implementation/<topic>/<module>.py` — one module per candidate
- `implementation/<topic>/utils.py` — shared helpers (quantization, prompt/data generators, metric functions)
- `tests/<topic>/test_<module>.py` — unit tests

## Gate G1
Before proceeding to Phase 3, run `pytest tests/<topic>/ -v`. All candidates must pass. Record gate result in study doc.

## RED-first tests `[opt:RIS-RED-FIRST · default ON · toggle .claude/skill-options.json]`

Standing (default-ON) discipline; skip only if the registry sets it `off`. Adopt TDD's iron law
explicitly: each candidate's regression tests are written **RED-first** — shown to FAIL against a
stub/known-wrong implementation *before* the real implementation makes them GREEN — so a test is
known to *discriminate*, not merely to pass. Record the red→green transition in the report's
Verification suite (Section 5) as a red-green column. The session's *fixes that stuck* (a guard, a
quantize-symmetry correction) were RED-first; the checks that could never fail were not.
*Off-behavior:* pre-2026-07-11, tests are written after the implementation and only their green state
is recorded, so a test that cannot fail is indistinguishable from one that discriminates.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-1, P0-5, P2-1` is active, read `addenda/phase-2.md` and apply the active blocks (P0-1 determinism gate, P0-5 correctness-oracle gate, P2-1 data+metric contract). In `original` mode, skip — do not read it.
