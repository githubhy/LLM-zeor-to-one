# Phase 3: Baseline Comparative Study

## Goal
Run all candidates against the same scenario across multiple random seeds with statistical aggregation.

## Constraints
- **N independent random seeds** (default 5, minimum 3) — sampling / eval-order seeds.
- Compute every Phase 1 metric per candidate per seed.
- Aggregate: **mean**, **standard deviation**, **95% confidence interval** (`scipy.stats.t.interval`; bootstrap for non-normal metrics).
- Per-seed results in a long-form table; aggregated statistics in summary table.

## Artifacts (under `artifacts/<study-name>/baseline/`)
- **Persistent data** (`.npz` for scores; `.jsonl` for per-item eval traces / model generations) — full numerical results for every seed
- **Summary** (`.json`) — config + per-method per-seed metrics + aggregated statistics
- **Interactive figure** (`.html` via Plotly) — zoom, pan, hover; error bars (CI) on primary chart (e.g. a quality-vs-budget curve: benchmark metric vs compute / context length / temperature)

## Gate G2
`artifacts/<study>/baseline/summary.json` exists and valid; every metric present for every candidate; `.npz` loadable; manifest updated.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-2, P0-4, P1-4` is active, read `addenda/phase-3.md` and apply the active blocks (P0-2 pairwise significance, P0-4 confidence-driven Monte-Carlo for rate metrics, P1-4 measured complexity/runtime profiling). In `original` mode, skip — do not read it.
