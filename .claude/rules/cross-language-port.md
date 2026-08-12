# Cross-Language Port Rule

Loaded on demand by `CLAUDE.md`. Read this file before porting a validated numerical
implementation to another language (PyTorch -> Triton/CUDA, Python -> C++, PyTorch -> JAX, or any pair),
and before signing off such a port.

**Earned from three ports**, each of which independently re-derived the same hazard set
and the same golden-pin discipline because none of it was written down:
three upstream ports of validated numerical kernels into a second language, one of
them gated by 62 tests.

## The rule

**A port is a proof obligation, not a translation.** The deliverable is not "code that
looks like the reference" — it is code whose every kernel is pinned to the reference's
own output, whose scope is provable, and whose divergences are named and bounded.

---

## 1. Scope it provably

- **Derive the deliverable by call-graph closure** from named entry points. Follow **call
  edges AND function-handle edges** (`@pkg.func` / a bound method passed as a callable). A handle edge carries no trailing
  paren, so a naive extractor misses it — on 2026-07-16 that silently hid two kernels: the closure *looked* complete and was not. Sanity-check the
  closure against what the math must contain ("an attention kernel must apply a softmax").
- **Reachable is not needed.** A method reachable only through a branch your scope never
  takes is dead (a class reached only via an unused dispatch hook). Necessity-audit
  every member: who calls it, under what branch condition, is that branch taken.
- **Drop only what is edit-free.** If a live-path function *references* the target,
  dropping it turns into an **engine edit** — keep it instead (a trace object returned by the engine; a helper referenced by a dispatch branch). Reachability
  does not tell you this: **check the referencing sites**, not just the call graph.
- **Say which closure you shipped**: the *engine closure* (model/tokenizer injected by
  the caller) or the *standalone-runnable* set (input-builders included). They differ.
- Report the scope audit: N methods, packages touched, and an explicit "zero leakage into
  X/Y/Z" statement. A reviewer must be able to see that nothing extra rode along.

## 2. Port it verbatim

- **Prefer a deterministic transpiler to hand-retyping.** It preserves bodies byte-for-byte,
  is reproducible, and self-checks (a transpiler that reports **zero unmapped
  cross-references** has proven the closure is complete and self-contained).
- **Reduce file count by namespace collapse and dead-path removal ONLY. Never merge
  function bodies.** Fusing logic (inlining a kernel into the engine) is exactly where
  numeric drift from the reference hides, and it destroys per-kernel golden traceability.
- **Static methods preserve per-kernel testability; local/private functions do not.** In a
  class-based collapse, keep every ported function an individually-callable static method —
  that is what lets N files become 2 without weakening the guarantee. A single mega-function
  with local helpers cannot be golden-pinned per kernel.
- Subfunctions of the source become private methods, not free functions, for portability.

## 3. Gate it against goldens

- **Dump goldens from the UNMODIFIED reference.** Never hand-author an expected value;
  never eyeball equivalence. (Same discipline as `.claude/rules/citation-integrity.md`
  applies to numbers: a value you are confident about is a guess wearing a golden's clothes.)
- **Tolerance ladder** (the one all three ports converged on):

  | Class | Tolerance |
  |---|---|
  | integers, indices, flags, iteration counts, identity fast-paths | EXACT (`isequal`) |
  | deterministic non-FFT kernels | 1e-12 |
  | FFT-bearing / transcendental kernels | 1e-9 (do not tighten) |
  | bisection outputs (thresholds) | the bisection tolerance |

- **Every DECISION must be exact; only magnitudes carry tolerance.** `converged`,
  `n_iter`, and the selected threshold are comparisons — a real divergence cannot hide
  behind round-off there, so they are the load-bearing pins.
- **Cover the edge cases, not just the happy path**: identity/no-op fast paths (an offset
  of 0 must return the input byte-identically), boundary/tie inputs, and the extremes.
- **Localize a failing golden PORT-vs-SOURCE before blaming the port.** On 2026-07-16 a
  1.8e-6 `quantize` failure looked like a port bug; comparing the port against its *source*
  (0.000e+00, bit-identical) proved the residual belonged to the reference pair, not the
  translation. This is `.claude/rules/calibration-residuals.md` applied to a port: triage
  into {port bug | cross-language convention/boundary | reference gap} before attributing.
- **Static compatibility scan -> 0** forbidden constructs of the target language, on code
  lines only. A zero count is a checkable guarantee; a clean read is not.
- If the target runtime is unavailable, say so: verify on the strictest available superset
  and hand off exactly one command for native confirmation. Do not claim what you did not run.

## 4. Cross-language hazards (the measured, recurring set)

Each fired in more than one port. Check every one before sign-off.

- **Banker's rounding.** numpy `round` is half-to-even; many target languages round
  half-away-from-zero. Use a `round_half_even` helper wherever a `.5` tie is reachable
  (upstream decision 2026-06-16-10). Fired in **all three ports** — and is still an **open** bug
  in one kernel (upstream bug 2026-06-16-05, in one kernel), independently rediscovered
  on 2026-07-16.
- **RNG is not portable.** PCG64 != Mersenne-Twister. Validate MC by captured-noise replay
  (bit-exact) or CI overlap — **never** by bit-comparing across languages.
- **FFT reordering.** FFTW vs pocketfft reorder sums; pin FFT-bearing kernels at 1e-9 and
  do not tighten.
- **Index base.** 0-based -> 1-based conversion happens exactly once, at the boundary;
  membership tests stay in the source's base.
- **Accumulating scatter.** `accumarray` is the `np.add.at` equivalent; a plain scatter
  assignment silently DROPS colliding mass.
- **Grid/knot coincidences.** When a sample grid point lands exactly on a decision
  boundary (a dyadic grid aliasing onto half-integer quantizer knots), tie-routing can
  differ across languages by ~1e-6. Measure-zero, but it will fail a fixture: use a
  **non-dyadic grid** in goldens, and document the boundary behaviour rather than
  "fixing" a non-bug.
- **Chained indexing / slicing sugar** legal in the source language can be a **parse error** in the target ->
  `reshape(x(a), [], 1)` or a temporary.

## 5. Ship it clean

- **Deliverable code carries no comments.** Strip them with a **string-aware** stripper
  that tracks quoted strings and distinguishes the transpose operator from a string open —
  a naive strip corrupts `sprintf('...%.2f...')` format specs and `x = a(:)';`.
- **Re-run the full gate on the stripped files.** If the result is not byte-identical you
  did not strip comments, you edited code. (2026-07-16: 26/26 identical, which is the only
  thing that makes "comment removal is safe" a fact rather than a hope.)
- **The README is the sole documentation** once comments are gone; it must meet the
  release-README standard defined in `.claude/rules/release-documentation.md` (the single
  normative home — this section no longer restates the section list).
- **Keep the verification harness OUT of the deliverable**; report its evidence and state
  where it lives. If the guarantee must be re-runnable later, ship exactly one verify entry
  point — and make that an explicit, recorded decision.
- **The release deliverable set — report + README + sign-off — is governed by
  `.claude/rules/release-documentation.md`.** That rule holds the release-general README
  standard and names the two sign-off passes (`results-reconciliation`, `citation-audit`
  CA-INTERNAL); this section (§5) keeps only the *port-specific* ship-clean bits
  (comment-free deliverable, string-aware strip, byte-identical re-gate). Read both when
  shipping a port.

## Cross-references

- `.claude/rules/calibration-residuals.md` — the residual-attribution discipline §3 invokes.
- `.claude/rules/sim-report-completeness.md` — the report spine a port's sign-off report follows.
- `.claude/rules/release-documentation.md` — the release deliverable set (report + README +
  sign-off) a port ships; §5's README standard is lifted there in release-general form.
- `.claude/skills/kernel-bringup/SKILL.md` — the sibling "prove equivalence against a golden
  reference" workflow, for a model -> RTL representation change rather than a language change.
- Upstream decision 2026-07-16-01 — scope/verbatim trade-off worked example (kept two dead-path
  members verbatim rather than edit the engine).
- A port field-note recording the near-miss diagnosis is worth keeping alongside the report.

## What this rule is not

It is not a port *workflow* skill. What recurs across ports is a **hazard checklist plus a
verification protocol**, not a multi-phase orchestration — so this is a rule, read on
demand. If a future port shows that the checklist is insufficient and the work genuinely
needs orchestration, promote it then (`todos/2026-07-16-port-tooling-promotion.md`), with
the evidence that the rule was not enough.
