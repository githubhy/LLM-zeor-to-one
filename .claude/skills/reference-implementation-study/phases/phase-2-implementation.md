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

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-1, P0-5, P2-1` is active, read `addenda/phase-2.md` and apply the active blocks (P0-1 determinism gate, P0-5 correctness-oracle gate, P2-1 data+metric contract). In `original` mode, skip — do not read it.
