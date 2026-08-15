---
slug: mi-survey-remaining-appendices
date_filed: 2026-08-15
status: closed
---

# Mechanistic-interpretability survey — appendices A, C, E and the remaining 2026 body updates

## Context

Max-mode expansion of `surveys/mechanistic-interpretability`, 2026-08-15. Phase 1–3 completed
in full: 19 sources acquired, references 81 → 100, 22 depth-tier labels, three figures, and
two orchestrated workflows (12-agent frontier sweep + 10-agent per-appendix derivation
extraction, 22 agents, 0 errors, 86 evidence records + 5 audited derivation sets).

Phase 4 delivered **Appendix D** (rewritten around a single derivation the sources do not
perform), **§5.7** (the 2026 reliability audit — a position change), and figure captions for
B/C/D. The remaining Phase-4 writing is listed here rather than left implied.

## What is left

### 1. Appendices A, C and E deepening — material already extracted and audited

All three have their derivation inputs sitting in the workflow result, each with an Opus audit
naming exactly what must be derived rather than transcribed. **The audits found real errors —
this material must not be written from the extraction alone.**

- **Appendix A** (`faithful: true`). Must-derive: the softmax-weighted-sum *form* of attention,
  which Vaswani gives as a definition and never derives. The audit specifies the route — a
  differentiable soft key-value lookup, hard argmax being non-differentiable, softmax over
  dot-product similarity as the entropy-regularized relaxation. Also two silent strengthenings
  to fix: "independent" was upgraded to "i.i.d.", and a row-wise-softmax inference was
  presented as transcription.
- **Appendix B** (`faithful: false`). **A load-bearing transcription error was caught**: the
  capacity exponent was transcribed as $e^{C(d/d')^2\delta^2}$ where the source prints
  $e^{C(d/d'^2)\delta^2}$ — the difference between capacity exponential in $d^2$ and in $d$.
  The auditor verified against the proof's own closing line. B's figure and §B.4 caption are
  landed; the prose deepening is not. **Use the corrected exponent.**
- **Appendix C** (`faithful: false`). One `equation_verbatim` is a silent stitch of two
  paragraphs with the seam hidden behind an ellipsis. Must-derive: the ratio-scale vs
  difference-scale reconciliation that no source performs — different papers define the effect
  decomposition on different scales and nobody maps between them. The audit explicitly ties
  this to `[opt:MATH-BASIS]`: declare the basis at each definition.
- **Appendix E** (`faithful: false`). Two source-level defects to repair rather than copy:
  ROME's objective hooks two *different* token positions that the extraction collapsed into
  one (publishing it would hook the wrong position), and **ROME Eq. 9 is dimensionally wrong
  as printed** — a scalar expanded into matrices, missing a trace. The audit supplies the
  repair and the matrix-calculus step the source performs invisibly.

### 2. Body updates from the frontier sweep

`§5.7` landed. Still to write, all with critiqued evidence in hand:

- **§6 / §12.2 — the 2026 SAE re-evaluation.** Critical: the citable figure is **9%**
  (well-trained SAE, geometric match that is causally inert), **not the 77%** the paper's own
  abstract implies — the critic showed the body and Table 5 contradict the abstract, and the
  77% is 17 of 22 matched pairs in a deliberately degraded toy SAE. Lead with 9%.
- **§12.2 — corroboration, not tension.** The multimodal model-diffing paper's own ablation
  table *strengthens* the survey's "SAEs underperform at action" line: a single SAE direction
  gives ΔVSR +2.63 against plain difference-in-means CAA at +8.96, i.e. the SAE direction
  loses to the simple baseline by ~2.4×. The extraction filed this as tension; it is support.
- **§4.4 — upgrade, not a new family.** The 2026 weight-space work belongs as a promotion of
  the existing `[catalog-only]` weight/SVD entry, plus per-weight auto-interp into §8 (whose
  novelty is a unit swap inside an existing pipeline). The Phase-1 brief originally called
  this "a new axis the survey lacks"; that was wrong and is corrected in the outline.
- **§7 / §13 — the knowing-vs-steering gap**, with its two constraining caveats (one model
  resisted steering entirely; a base-model sign flip).

### 3. R-MATHREV has not run

`[opt:MATH-REDERIVE]` requires one independent re-derivation of new numbered derivations
before they land. Appendix D added six numbered equations and has **not** had that pass. It is
owed before this survey is signed off.

## Acceptance

- Appendices A, C, E deepened, each using its audit's must-derive list, with the three
  identified source defects repaired rather than reproduced.
- §6/§12.2/§4.4/§7 updated, with 9% (not 77%) and model-diffing filed as corroboration.
- R-MATHREV run on Appendix D's derivation, on Opus, deriving before reading.

## Refs

- `surveys/mechanistic-interpretability/_scratch/00-max-mode-outline.md` — the brief and tier
  allocation (already corrected once, on the weight-space point).
- Workflow runs `wf_62ffb6fb-f63` (frontier) and `wf_e065a48c-998` (derivations).
- `bugs/2026-08-15-01` — why the critics' "zero records" verdicts were artifacts and their
  content corrections were not.

## Resolution

**Resolution.** Closed 2026-08-15. All three acceptance criteria met.

1. **Appendices A, B, C, E deepened** from their audits' must-derive lists. A: 754 → 3,886 words
   (6 → 17 equations), B: 940 → 2,792, C: 1,007 → 2,674, E: 610 → 2,351. Survey 29,446 → 41,437
   words. The three named source defects were **repaired, not reproduced**, and each was verified
   against the PDF rather than taken from the audit: the capacity exponent is $e^{C_1(d/d'^2)\delta^2}$
   (exponential in $d$, not $d^2$); ROME's Eq. 9 is dimensionally inconsistent as printed (scalar set
   equal to matrices, missing trace) so §E.2 derives in trace form; ROME's Eq. 4 hooks two distinct
   token positions, which §E.6 records without reproducing since the appendix never states that
   objective. The stitched Appendix-C equation was likewise never transcribed — §C.6/§C.7 were built
   from primary values read directly.

   A fourth defect surfaced that the audit had not named: Appendix E.3's MEMIT update was
   **non-conformable** and live on `main` (`bugs/2026-08-15-02`).

2. **Body updates landed** in §6.5, §12.2, §4.4, §8.1, §7.7 (new), §13.1, and §15.1 (two new open
   problems). The citable SAE figure is **9%**, with the abstract-vs-body denominator discrepancy
   stated explicitly. Model diffing is filed as **corroboration**: the paper's own Table 14 puts a
   single SAE direction at +2.63 ΔVSR against plain difference-in-means at +8.96. Weight-space was an
   **upgrade** of the existing `[catalog-only]` §4.4 entry to `load-bearing`, plus per-weight
   auto-interp into §8.1 — not a new family.

3. **R-MATHREV ran on five appendices**, not just D — every appendix that gained numbered equations,
   all on Opus, deriving before reading. Returned 12 ERROR / 15 UNSTATED HYPOTHESIS / 13 OVERSTATEMENT.
   **Every displayed equation was correct; the findings were in the prose around them**, which is the
   class the rule exists for. Three would have shipped a wrong conclusion — §C.7's synergy verdict was
   *inverted*, §B.8's metric-relativity thesis was false of the sections it named, and §B.7's linear
   contrast was 3× too large. All applied; raw reviews preserved in `_scratch/review-appendix-{a..e}.md`.

Two follow-ons filed rather than swept along: `todos/2026-08-15-web-native-source-upgrades.md` (the
remaining `(web)` references that are primary records) and `bugs/2026-08-15-03` (figure SVGs were not
byte-reproducible; fixed). Gates green: lint-math 0 errors, validate-refs OK, bare-refs 0, 102
references 0 errors, 22 depth-tier labels 0 violations, 0 TIER-DRIFT, 362 fragment links 0 dangling,
no cross-link gaps, record-ids consistent.

