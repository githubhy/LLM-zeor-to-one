# H9 softmax two-head study — CODE + NUMBERS audit

## Reproduction of headline numbers (all EXACT vs summary.json)
Independent from-scratch reimplementation (own einsum GD + softmax), same seeds:
- beta=0.02 two_head err = 0.129616 ✓ ; single c*=0.28368, err=0.993918 ✓
- min-over-beta two_floor@N20 = 0.1296159660699112 ✓ ; single_floor@N20 = 0.5870908724050045 ✓
- N-sweep single_floor [0.6446,0.5871,0.4928,0.4125,0.3073] ✓
- N-sweep two_floor [0.2105,0.1296,0.0763,0.0399,0.0204] ✓ ; ratio/two*N ✓
- verification: idealized_identity 3.109e-15 ✓ ; centering_unexplained 0.01728 ✓ ; offset_frac 0.50135 ✓
=> summary.json is NOT stale. Tests: 7 passed.

## Math correctness (verified)
- GD (W0=0): (eta/N) sum_i y_i (x_i.x_q). matched_scale c=eta/(2beta) ✓.
- ideal two-head == GD algebraically for GENERAL W0 (two genuinely different code paths:
  attention-sum vs weight-update). Identity test is a real cross-check, NOT tautological.
- centering_term = -(eta/N) s_bar sum_i v_i derived + confirmed (explains 98.3% of residual).
- softmax numerically stable (max-subtract). No overflow; RuntimeWarnings are the suppressed
  Apple-Accelerate matmul quirk, not real.
- single-head best c* = (ps·gd)/(ps·ps) IS the least-squares-optimal scalar; fair best case.
- Bootstrap _boot_ratio_ci: paired resample of (num_per,den_per) with SAME idx; ratio-of-sums
  matches point estimate. Correct. (Minor: c* not re-estimated per resample => negligibly tight.)
- Two-head best-cased over beta only (c tied via matched_scale) while single best-cased over
  (c,beta): this is CONSERVATIVE for the two-head-wins claim, not inflation.

## PRIMARY FINDING — "irreducible" single-head failure is N=20-specific (overclaim)
single_floor (study's OWN metric + OWN 12-beta grid) vs N:
  N=160 -> 0.3073  (fails>0.3 = True)
  N=240 -> 0.2510  (fails>0.3 = FALSE)   <-- verdict flag flips here
  N=320 -> 0.2359  (False)
  N=480 -> 0.1963  (False)
  N=1280-> 0.1207
Mechanism: offset ~ c*sum(v)/Z ~ O(1/sqrt(N)) relative to O(1) GD signal => normalized error ->0.
Study measures NORMALIZED PREDICTION ERROR, and by that metric the single head DOES recover GD as
N grows (just ~1/sqrt(N), vs two-head 1/N). So:
- softmax_run.py:5-6 "large IRREDUCIBLE normalized-error floor" — the normalized floor is reducible.
- softmax_run.py:175 `fails = single_floor > 0.3` — N-fragile, flips False by N=240.
- test_softmax_construction.py:94/98 test name `..._has_large_irreducible_floor`, assert floor>0.3.
Verdict reproduced=True stays valid AT N_headline=20; the FUNDAMENTAL-limitation framing is the
overclaim. Fix: scope to small N, drop/qualify "irreducible" (= irreducible by (c,beta) tuning at
fixed N), rename test.

## SECONDARY — one-sided asymptotic disclosure
n_sweep advertises two_floor->0 (O(1/N)) + ratio widening 3->15 as the two-head advantage but never
discloses single_floor ALSO ->0 (0.64->0.31 over grid, ->0.12 by N=1280). The widening ratio is a
CONVERGENCE-RATE gap (1/N vs 1/sqrt(N)), not the single head being stuck. Reader concludes only the
two head recovers. Fix: report single_floor decay (e.g. single_floor*sqrt(N)) beside two_floor*N.

## Non-issues checked & cleared
- summary.json stale: NO. - matched_scale: correct. - softmax stability: correct.
- bootstrap: correct. - tests tautological: NO (identity is cross-path). - two-head recovers:
  robust (0.13 vs 0.25, min at grid edge beta=0.02 would only go lower). - c* fair: yes.
- construction.py diff: errstate wrap only, numerics unchanged.
