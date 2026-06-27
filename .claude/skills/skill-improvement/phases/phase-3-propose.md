# Phase 3: Compare & propose

## Goal
Turn the landscape + domain judgment into an actionable, tiered, testable proposal.

## Steps
- Build a comparison matrix: the skill (baseline) vs SOTA across the dimensions that matter,
  with the gap per dimension.
- Derive tiered improvements: **P0** (highest leverage), **P1**, **P2**. For EACH item record:
  what it changes, which phase it maps to, the gap it closes, its `test_type`
  (output_ablation | structural_check | needs_human), and how Phase 5 will verify it.
- Save `proposals/<target>-improvement-<date>.md` with a citation-integrity caveat (mechanisms,
  not unverified landscape numbers).

## Deliverable
The proposal markdown + (optionally) a `comparison-data.json`.
