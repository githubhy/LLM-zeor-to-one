# Plan — H9 follow-on: two-head softmax approximate-GD (von Oswald §A.9)

**Date:** 2026-07-04 · **Parent:** H9 (`docs/h9-algorithmic-icl-study.md`), todo `todos/2026-07-04-h9-followups.md`
**Source (read, not memory):** von Oswald et al. 2023 §A.9, Eq 14–21 (`download/vonoswald-transformers-icl-gradient-descent-2023.pdf`).

## Goal

Close the tracked "two-head-softmax approximate-GD" gap: reproduce §A.9's result that a **single**
softmax self-attention head cannot match the one-GD-step update (an irreducible additive offset,
Eq 17), while **two sign-reversed** heads cancel that offset (Eq 18–21) and recover the linear-GD
construction. This is the softmax-side mechanistic counterpart to H9-A (the *linear*-attention
exact identity).

## The mechanism (from the source)

Softmax Taylor-expands (Eq 16): `softmax(Kᵀq)_i ≈ (1 + xᵢᵀW_KQ x_j) / Σ(1 + …)`. The leading `1`
is a query-independent **additive offset** (Eq 17) — a single head is stuck with it. Two heads with
`W_{1,KQ} − W_{2,KQ}` diagonal and `P₂V₂ = −P₁V₁` subtract the offsets (Eq 19–20), leaving the pure
linear score `∝ PV Kᵀq` (Eq 21) = the GD construction, **exactly** under the paper's stated
"`PV` subsumes the softmax denominator and is equal per head" assumption.

## Structure (mirrors H9-A: exact identity + honest approximation)

- **Exact idealized identity** — linearize (Eq 16) + equal-denominator-`N` assumption ⇒ two-head
  difference `= 2βsᵢ/N` exactly ⇒ with `c = η/(2β)` reproduces `gd_step_prediction` to **machine
  precision for every β**. (The mechanism, provably.)
- **Honest full softmax** — real `exp`, real per-head denominators, softmax over the `N` context
  tokens (isolates the Eq-16 offset; documented conformance choice):
  - **Single head, best-case** (closed-form best output scale `c*`, tuned over β): irreducible
    normalized-error floor `O(1)` — the offset (Eq 17).
  - **Two head, matched** (`c = η/(2β)`, `β₂ = −β₁`): normalized error ≪ single-head, approaching a
    small `O(1/N)` **centering floor** `(η/N)·s̄·Σvᵢ` (the unequal-denominator term the paper's
    assumption idealizes away). Reproduces Fig-12's "good but not as precise as linear."
  - **Root-cause + N-scaling**: verify the honest two-head residual matches the predicted centering
    term; show the floor shrinks as `N` grows (asymptotic-only, not a harness bug).
  - **Offset diagnostic**: decompose the single-head error, show the Eq-17 offset `(c/Z)Σvᵢ`
    dominates it.

## Deliverables

- `implementation/icl_regression/softmax_construction.py` — the numpy core (reuses `task.py`,
  `construction.gd_step_prediction`). Pure, deterministic, BLAS-FPE-guarded.
- `tests/icl_regression/test_softmax_construction.py` — G1 gates: softmax sanity; **idealized
  two-head == GD to <1e-10 (all β)**; single-head floor > two-head; centering-term identity;
  β-monotonicity; offset-dominance.
- `implementation/icl_regression/softmax_run.py` — β-sweep + N-sweep study, bootstrap CIs,
  verdict, `artifacts/icl-regression-softmax/summary.json`.
- `implementation/icl_regression/softmax_figure.py` — error-vs-β (single floor / two-head / ideal)
  + N-scaling of the two-head/single gap. Static, persisted data.
- `docs/h9-softmax-two-head-gd-study.md` — completeness-conformant report (theory-as-predictor =
  the idealized-line-at-0 overlay; conformance matrix grades the constructive vs trained-Fig-12
  scope; explicit n/a for quantization/decoding).
- Survey note `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.24 (after §A.23),
  reusing ref [94] von Oswald.

## Optional secondary (assess after core)

Trained single-layer 1-head-vs-2-head softmax SA (literal Fig 12) — CPU, seeded, small. Included
only if quick/clean; otherwise the residual "trained emergence" stays in the h9-followups todo.

## Verdict (divergence-closing analog)

`single_head_fails ∧ two_head_recovers ∧ exact_idealized_identity ∧ centering_floor_explained`.

## Sign-off

G1 tests green · `check-report-completeness.py` PASS · `check-citation-sources.py` 0 errors ·
lint-math clean · adversarial audit (Workflow) · records (decision, field-note, todo update) ·
cross-link the new §A.24 · commit + push.
