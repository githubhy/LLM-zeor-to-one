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

## Evaluation-independence sub-pass `[opt:RIS-EVAL-INDEPENDENCE · default ON · toggle .claude/skill-options.json]`

Standing (default-ON) discipline; skip this section only if the registry sets it `off`. G0 (`RIS-DERIV`) makes the *derivation* independent — this extends the same discipline to the baseline *evaluation*. Each **load-bearing** baseline number (a headline threshold/margin, a ranking that decides the recommendation) gets a no-shared-code adversarial check before G2 sign-off:

1. **Re-verify with an independent oracle** (`[opt:ME-INDEPENDENCE-AUDIT]`) — a route that shares neither code nor the load-bearing assumption with the implementation that produced the number. List the shared surface; if the only confirmation reuses the code-under-test's arithmetic or its wrong premise, it is not evidence.
2. **Degenerate-case test** (`[opt:ME-ADVERSARIAL-METRIC]`) — name the trivial solution that would satisfy the baseline metric without solving the problem (a saturating offset that annihilates the messages; a constant output), construct it, and confirm the metric **rejects** it.
3. **Metric declaration** (`[opt:ME-METRIC-DECL · default ON · toggle .claude/skill-options.json]`) — every comparison in the §6 results and the §2 conformance matrix NAMES its metric axis (exact-match accuracy vs `pass@1` vs `pass@k` vs perplexity in bits vs win-rate vs tokens/s); "X beats Y" requires both on the same axis or an explicit stated bridge. (A `pass@k`-vs-`pass@1` cross-axis comparison produces a spurious "beats" verdict for free, because `pass@k` forgives one success among $k$.)

A baseline metric that rewards triviality, or a number confirmed only by an oracle sharing the implementation, **fails** the sub-pass. Motivating case (2026-07-10): a floor-limited-threshold baseline metric rewarded a trivial decoder (a large offset annihilating the messages) — caught late by hand, not by a gate. Record the sub-pass outcome in the Report's Verification suite (Section 5). *Off-behavior:* pre-2026-07-11, the baseline trusts its own metric and an oracle that may share the implementation.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or any of `flags: P0-2, P0-4, P1-4` is active, read `addenda/phase-3.md` and apply the active blocks (P0-2 pairwise significance, P0-4 confidence-driven Monte-Carlo for rate metrics, P1-4 measured complexity/runtime profiling). In `original` mode, skip — do not read it.
