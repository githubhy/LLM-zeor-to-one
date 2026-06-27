# Todos Index

| date | slug | title | status | hook |
|---|---|---|---|---|
| 2026-06-17 | fix-serve-api-md-eisdir-crash | Fix serve.js /api/md/<empty-or-dir> EISDIR crash (upstream + re-sync) | open | one malformed GET kills the dev server; deferred per user, fix upstream then re-sync (bug 2026-06-17-01) |
| 2026-06-19 | port-multispan-highlight-fix-upstream | Port the multi-span inline-math highlight fix to the upstream viewer | open | local viewer.js fixed (bug 2026-06-19-01); same branch buggy upstream, port per convergence policy |
| 2026-06-26 | clean-residual-wireless-leakage-in-viewer-tools | Clean residual wireless example-strings in viewer/tools/ docstrings | closed | resolved in sync batch 2 — lint-math/build-index/test_lint_math retargeted to LLM examples; full-harness grep clean |
| 2026-06-26 | port-method-eval-and-figure-conventions | Consider porting upstream method-eval skill + figure-operating-conditions.md | closed | RESOLVED 2026-06-28: both ported in pitch-perfector catch-up + restored by-name refs in phase-2/sim-audit/sim-report-completeness (decision 2026-06-28-01) |
| 2026-06-28 | import-viewer-figure-pipeline-from-upstream | Import viewer non-config deltas from upstream main (figure-pipeline.js + sionna viewer gates) | open | config sync excludes viewer/lib + serve.js; main 9b118d3 advanced via PR#13/#14 viewer code; needs a viewer wholesale-sync |
| 2026-06-28 | port-pitch-perfector-agents | Port (or decide against) the 3 pitch-perfector subagents (survey-enricher, evidence-collector, viewer-dev) | open | agents out of agreed catch-up scope; /enrich + method-eval reference survey-enricher genericized |
