# Field notes — 2026-07-04 — H9 softmax two-head approximate-GD build

## Context

Built the constructive reproduction of von Oswald §A.9 (single softmax head fails GD; two
sign-reversed heads recover it) as an H9 follow-on (`docs/h9-softmax-two-head-gd-study.md`,
`implementation/icl_regression/softmax_*.py`). Verification-driven, like H9-A/#1. Issues found and
resolved inline:

## Issues found and resolved

- **The paper's "≈" hides a `β`-independent centering term — and it changed the study design.**
  Working Eq 14–21 honestly (real `exp`, real per-head denominators, softmax over the `N` context
  tokens) gives a two-head difference `2β(s_i − s̄)/N`, not the paper's clean `2βs_i/N`. The extra
  `−s̄` is the unequal-denominator effect the paper's "PV subsumes the divisor, equal per head"
  assumption idealizes away, leaving a residual `−(η/N)·s̄·Σv` that does **not** vanish as `β→0`.
  So "honest two-head → GD as `β→0`" is *false*; the honest error plateaus at an `O(1/N)`
  centering floor. Turned this from a bug-suspicion into the study's richest result: an *idealized*
  object (exact, `3.1e-15`) + an *honest* object (approximate, root-caused floor). No-todo: it
  reshaped the deliverable, captured in decision `2026-07-04-04`.

- **A G1 monotonicity test failed because it asserted the wrong convergence.** First wrote
  `test_honest_two_head_approaches_ideal_as_beta_shrinks` expecting `|honest − ideal| → 0`. It
  failed non-monotonically (`[0.284, 0.0056, 0.0139]`) because honest − ideal → the *constant*
  centering term, not 0. The test was right to fail — my premise was wrong. Fixed to a *batched*
  assertion that the honest two-head *error* falls as `β` shrinks (toward the centering floor);
  the per-task gap mixes the vanishing Taylor remainder with the constant centering term and is
  not monotone (only the batched error is). Lesson: when a monotonicity test fails, check whether
  the quantity actually converges to what you assumed before relaxing the tolerance.

- **The exact idealized identity is the derivation check.** Rather than trust my Eq-19–21 algebra,
  `two_head_ideal_predict` computes the construction explicitly (`(1±βs)/N`, subtract, scale
  `c=η/(2β)`) and the G1 test asserts it equals `gd_step_prediction` to `<1e-10` for *every* `β`.
  It came out `3.1e-15` first try — the code *is* the proof that the linearised two-head mechanism
  reproduces the GD step. Same discipline as H9-A's `1.3e-15` and #1's edge→node identity: gate an
  error-prone derivation on an identity it must satisfy.

- **The centering term is not just named, it's *verified*.** `centering_term` predicts the honest
  residual; a G1 test confirms it explains `98.3%` of the honest small-`β` two-head residual. This
  turns "the floor is probably the denominator asymmetry" into a measured root-cause — the residual
  is `asymptotic-only`, not a harness bug. The N-sweep (floor halves per `N` doubling; ratio
  `3.1×→15.1×`) is the independent confirmation.

- **`gd_step_prediction` leaked spurious Accelerate FPE warnings.** The H9-A oracle wasn't wrapped
  in the `_quiet_blas` errstate guard the rest of the module uses, so a many-task loop spammed
  divide-by-zero/overflow RuntimeWarnings on finite matmul (the known numpy-on-macOS-arm64 quirk).
  Guarded it (numerics unchanged, finiteness still asserted) — a strict improvement; all 11 H9
  tests stay green.

- **Two mechanical checker adaptations.** (1) The completeness/citation checker treats any
  top-level `N.` list item as a reference entry (`ENTRY_RE`), so §5's numbered anchor list tripped
  3 false "untagged [1]/[2]/[3]" errors → converted to bold-headed bullets (the edge-level report's
  convention). (2) `save_json` here is `tiny_transformer.utils`' `(obj, path)` order — the opposite
  of `eap_ig.utils`' `(path, obj)` that bit #1's figure; used the right order first this time.

## Patterns / lessons

- **Read the "≈" — a paper's approximation sign often hides a term that becomes the interesting
  result.** The centering floor (the thing the idealization drops) is what reproduces the paper's
  own "not as precise as linear" caveat and gives the `O(1/N)` asymptotic story.
- **A failing test can mean the assertion is wrong, not the code.** The monotonicity test caught my
  misconception (honest → ideal) rather than a code bug — the fix was to the *claim*, batched.
- **Idealized identity + honest approximation + root-caused residual** is a reusable three-part
  shape for reproducing an "approximate mechanism" paper (H9-A construction/behavior; here
  idealized/honest/centering). Gate the exact part on machine precision; verify the residual is the
  named term; show it's asymptotic-only.
- **The pre-sign-off audit's catch was a *scope* overclaim, not a wrong number** (the numbers all
  reproduced to the last digit). Two of my framings — "single head has an *irreducible* floor" and
  "offset-dominated at its *best-case*" — were true only at *fixed small `N`* / *small `β`*, and I
  had stated them as general. The single-head floor also declines with `N` (both heads recover; the
  two-head just faster, `O(1/N)`), and at the actual best-case `β ≈ 0.57` the offset is `0.17`, not
  `0.50` (measured at `β = 0.26`, an off-minimum point I mislabeled "best-case"). Lesson: after a
  reproduction "passes", re-read the *adjectives* — "irreducible / fundamental / best-case / halves"
  are exactly the words that quietly generalize a fixed-operating-point result. Two independent audit
  lenses flagged the same offset mislabel, which is the signal it was real, not a nit. The honest
  fix (both-recover, rate-gap) is a *stronger* result than the wall I'd claimed.
