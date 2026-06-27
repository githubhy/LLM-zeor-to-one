# Phase 6: Report & merge

## Goal
Consolidate honestly and (full) land the work.

## Steps
- Write `reports/<target>-improvement-implementation-<date>.md`: a per-item verdict table
  (verified / weak / null / inconclusive / structural), the end-to-end result, an explicit
  scope-and-limits section, and a recommendation (which flags to adopt; what stays default).
- Keep a RESULTS-style ledger under `bench/<target>/` (every run, with numbers).
- Fold the verdicts back into the proposal's per-item lines.
- `full` mode: merge `skill-analysis/<target>` to main (resolve INDEX conflicts by keeping
  both sides), delete the branch local + remote, and clean strays. Never `git clean` runtime
  dirs (gotcha #7). Mark all stages done in `PROGRESS.md`.

## Deliverable
The report + ledger + (full) a clean merge.
