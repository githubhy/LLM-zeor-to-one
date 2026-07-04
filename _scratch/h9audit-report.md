# H9 softmax two-head GD study — REPORT HONESTY + CITATION audit

Target: `docs/h9-softmax-two-head-gd-study.md`
Sources of truth: `artifacts/icl-regression-softmax/summary.json`, von Oswald §A.9,
`tests/icl_regression/test_softmax_construction.py`, `implementation/icl_regression/softmax_run.py`,
`softmax_construction.py`, survey `appendix-a-qkv-first-principles.md §A.23`.

## PASSES (verified sound)
- **7 G1 tests pass** (`pytest ... -q` → `7 passed`). Report's "7 tests / 7/7 pass" correct.
- **Headline numbers match summary.json**: 3.1e-15 (idealized_identity_maxabs 3.1086e-15); single
  floor 0.587 (0.58709); offset 0.50 (0.50135); 4.5× (ratio_headline 4.5295); two floor 0.130
  (0.12962); two CI [0.118,0.142] (two_head[0].err_ci); 98.3% explained (1−0.017284); ratios
  3.1×→15.1× (3.06/15.07); centering unexplained 0.017.
- **β-sweep table cells** (single err, two err, ideal RMS) all match summary at indices 0,4,6,8,10,11.
- **N-sweep two floors, ratios, two×N** match (except N=80 single & N=10 two×N rounding, below).
- **Citation [94]**: PDF exists (2.29 MB). Eq 14–21 read from source verified: Eq16 linearization
  `(1+x·W_KQ·x)/Σ(1+…)`, Eq17 "+1" offset ("softmax induces a linear offset"), Eq18 two-head sum,
  Eq19 `(1+s1)−(1+s2)=x(W1−W2)x`, Eq21 `∝ PV K^T q`, and the equal-denominator assumption
  ("PV subsumes the dividing factor of the softmax … same for each head"). Report's math is a
  faithful sign-reversed-score realization of the source. Matched scale c=η/(2β) verified against
  two_head[i].c (β=0.02→12.5, β=2→0.125, β=0.5696→0.4389). Centering formula −(η/N)·s̄·Σv matches
  `centering_term`.
- **Conformance matrix** honestly graded (IDEALIZED for linearization + equal-denominator + N-token
  softmax; EXACT for diagonal weights + data dist; DEVIATED for Fig-12 trained). Matches source.
- **Do-not-cite clause** present (§0, §9) and correct; **no overclaim** that a *trained* model does
  this. Survey **§A.23 Claim 2** accurate ("approximate, empirical, two-headed, not the clean
  identity"), does not overclaim trained behavior. Anchor-1 β set {0.02,0.1,1,3} + W0∈{0,random}
  matches `softmax_run.py:106` (NOT the test's superset — report describes the run correctly).

## FINDINGS

### F1 (med) — "0.50 offset at its best-case operating point" mislabels the operating point
Exec summary L26 and §5 anchor 3 L163: single head "offset-dominated: the Eq-17 term is 0.50 of its
output **at its best-case operating point**." But `single_offset_fraction`=0.5013 is computed at
`beta_s = 0.26` (`softmax_run.py:119-123`). The single-head **best-case** (min-error) β is ≈0.57
(single_floor_headline 0.587 at β=0.5696; at β≈0.25 single err = 0.670, well above the floor). The
code comment (`softmax_run.py:118`) and test comment (`test_...py:133`) also call β=0.26 "best-case
beta", contradicted by the study's own β-sweep. The 0.50 value is real but its "best-case operating
point" attribution is wrong; the exec summary juxtaposes the 0.587 floor (β≈0.57) with the 0.50
offset (β=0.26) as if same operating point.

### F2 (med) — two §6 CIs do not match summary.json (rounded outward)
- §6 β-sweep L180, single-head floor: report `0.587 [0.55, 0.62]`. summary `single_best[8].err_ci`
  = [0.563218, 0.611658] → [0.56, 0.61]. Both bounds wrong (0.5632→0.55 not 0.56; 0.6117→0.62 not
  0.61).
- §6 N-sweep L196, N=40 two-head floor: report `0.076 [0.068, 0.085]`. summary `two_floor_ci[2]`
  = [0.070395, 0.082480] → [0.070, 0.082]. Both bounds wrong (0.0704→0.068; 0.0825→0.085).
Both are rounded *outward* (wider), inconsistent with the nearest-rounded exec-summary CI
[0.118,0.142]. No disclosed rounding convention. Doesn't flip any verdict.

### F3 (low) — two rounded-wrong values in §6 N-sweep table
- L197 N=80 single floor `0.413`. summary `single_floor[3]` = 0.4124586 → 0.412. Off by 0.001.
- L194 N=10 two×N `2.10`. summary `two_floor_x_N[0]` = 2.105299 → 2.11 (round-half-up). Report rounds
  down.

### F4 (low) — §6 header "CI on every result" overclaims vs the tables
Header L171 "(CI on every result)". But N-sweep single-floor column shows **no** CIs (all 5 cells),
and two-head CIs are omitted for N=80/160 — though `single_floor_ci` and `two_floor_ci` (all 5) and
`single_best`/`two_head` err_ci (all 12 β) exist in summary.json. β-sweep shows CI on only 2 of 12
cells. Headline results do carry CIs, so the intent of sim-report-completeness §6 is largely met, but
the "every result" claim is not honored by the tables.

## Verdict: issues_found (all med/low; no critical/high; no verdict flips, no citation fabrication)
