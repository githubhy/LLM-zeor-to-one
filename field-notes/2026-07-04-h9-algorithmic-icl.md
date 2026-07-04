# Field notes — 2026-07-04 — H9 algorithmic-ICL sub-study

## Context

Picked H9 (algorithmic ICL — the forward-pass-as-online-optimizer reading) off the runnable-on-
this-machine backlog after H15 shipped, and drove it end-to-end: an understand-phase workflow
(4 Opus source readers + 2 Sonnet scaffold mappers), a new `implementation/icl_regression/`
module (von Oswald construction + trained softmax regression transformer), a 14-section report,
the §A.23 appendix note, and the sign-off sweep. Several issues surfaced and were resolved inline.

## Issues found and resolved

- **The sources don't support one claim — they partition into two.** The whole design turned on
  the understand phase catching that "attention = gradient descent" is *exact* only for **linear**
  attention with **constructed** weights (von Oswald), while trained **softmax** models merely
  **behaviorally match** least-squares (Garg/Akyürek) and Dai's slogan is a relaxed-linear-
  attention dual form. Structuring H9 as a two-part contrast (exact Part A vs behavioral Part B)
  came directly from that reading — captured as decision `2026-07-04-02`. No-bug: this is a design
  win, not a defect; but it is the reason the pre-registration had to be written *after* the
  sources were read, not before.

- **macOS Accelerate/vecLib spurious FPE on matmul.** Every `np.matmul` / `lstsq` / `solve` in the
  construction and the closed-form learners raised `divide by zero` / `overflow` / `invalid`
  RuntimeWarnings — on *finite* inputs with *finite* outputs (the identity was exact, 2e-16).
  Verified spurious by asserting output finiteness under `np.seterr(all="raise")`. Resolved with a
  narrow `np.errstate(...)` suppression *plus* a finiteness assert (so a genuine non-finite value
  still fails loudly) in `construction.linear_self_attention` and a `task._quiet_blas` context for
  the learners. Lesson: on Apple-silicon numpy, FE flags on BLAS ops are not evidence of a bug —
  check the output, not the flag. (Sibling of the H15 MPS cost artifact — same "measured ≠ real"
  discipline.)

- **Variable-shadowing in the Part-A loop.** `for i in range(200): Xs, ys, _ = make_regression_batch(...)`
  clobbered the loop counter when I named the discarded teacher `_` — then `_ % 2` ran on an
  array and threw "truth value ambiguous". Renamed to `_w`. Caught by the `run.py --quick` smoke
  before the full run — the reason to always smoke-test orchestration on a tiny config first.

- **GD gradient-convention mismatch, caught by a cross-check test.** `task.gd_predict` used the
  literal MSE factor $2/k$ while `construction.gd_step_prediction` absorbed it into $\eta$, so the
  two disagreed by exactly 2× at matched step size. The K-step-construction-equals-gd_predict
  check flagged it (0.696 vs 1.392). Standardised both on $L=\tfrac{1}{2N}\lVert\cdot\rVert^2$
  (no factor of 2), making `gd_predict(lr=\eta)` bit-exact against the construction. Lesson: a
  cross-module equality test is the cheapest catch for silent convention drift.

- **Marker-at-line-start caught by the lint hook on a *scratch* draft.** The §A.23 note draft,
  hard-wrapped, put several `secref/ref/cite` comment markers at the start of a physical line —
  which CommonMark parses as an HTML block (the exact bug the math-authoring rule guards). The
  PostToolUse lint hook fired even on the scratch file and blocked it, so I rewrote the note as
  single-line paragraphs (the survey's own convention) *before* pasting into the survey. Drafting
  survey content in scratch first, letting the hook validate it, then pasting is a good pattern.

- **check-citation-sources false-positive on ordered lists.** The checker read the report's
  `1. 2. 3. 4.` do-NOT list items as bibliography entries `[1]`–`[4]` and flagged them untagged.
  Converted the list to bold-led bullets and added a proper `## Sources` section with `(local:)`
  tags (un-backticked so the line ends in `)`, which the checker requires). Lesson: in a docs/
  report scanned by the survey citation checker, avoid column-0 `N.` lists and end source-tag
  lines with `)` not a code-span backtick.

- **Stale H15 p-value in the parent report (cross-document drift).** While adding the H9 row to
  `docs/tiny-transformer-induction-study.md` §6, noticed the H15 summary row still showed the
  pre-audit pooled `p=5e-29` — the H15 pseudo-replication fix (bug `2026-07-03-02`) corrected the
  *study* to seed-level `p=0.024` but missed this *parent-report* one-liner. Fixed it to `p=0.024`
  in the same pass. No-bug (a one-line summary, not load-bearing), but a clean example of why a
  cross-document consistency scan belongs in an audit: fixing a number in the study doesn't
  propagate to every place that quotes it.

## Patterns / lessons

- **Read the sources before writing the pre-registration** when the literature's scope is the
  crux. H9's honest verdict *is* the scope boundary; a pre-registration written from memory would
  have mis-stated it.
- **Calibrate compute from data, not hope.** Three rounds of timing/convergence probes (MPS
  stalls, CPU ~22 steps/s for the 4-layer model, convergence to $\Delta_{\text{norm}}<0.02$ by 8k
  steps) set the budget; the full run then hit 0.009 with a tight 3-seed envelope. The probe's
  optimizer-reset pessimism made it a safe lower bound.
- **The honest unit is the trained model, not the eval task** — reported H9-B as a min–max
  envelope over 3 training seeds, not a bootstrap over 1024 eval tasks (the H15 pseudo-replication
  lesson, applied prospectively).
