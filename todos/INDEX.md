# Todos Index

| date | slug | title | status | hook |
|---|---|---|---|---|
| 2026-06-17 | fix-serve-api-md-eisdir-crash | Fix serve.js /api/md/<empty-or-dir> EISDIR crash (upstream + re-sync) | open | one malformed GET kills the dev server; deferred per user, fix upstream then re-sync (bug 2026-06-17-01) |
| 2026-06-19 | port-multispan-highlight-fix-upstream | Port the multi-span inline-math highlight fix to the upstream viewer | open | local viewer.js fixed (bug 2026-06-19-01); same branch buggy upstream, port per convergence policy |
| 2026-06-26 | clean-residual-wireless-leakage-in-viewer-tools | Clean residual wireless example-strings in viewer/tools/ docstrings | closed | resolved in sync batch 2 — lint-math/build-index/test_lint_math retargeted to LLM examples; full-harness grep clean |
| 2026-06-26 | port-method-eval-and-figure-conventions | Consider porting upstream method-eval skill + figure-operating-conditions.md | closed | RESOLVED 2026-06-28: both ported in pitch-perfector catch-up + restored by-name refs in phase-2/sim-audit/sim-report-completeness (decision 2026-06-28-01) |
| 2026-06-28 | import-viewer-figure-pipeline-from-upstream | Import viewer non-config deltas from upstream main (figure-pipeline.js + sionna viewer gates) | closed | RESOLVED 2026-06-28: figure-pipeline subsystem + sionna scroll/anchor gates imported, re-domained, 298 unit + 15 e2e green (decision 2026-06-28-03) |
| 2026-06-28 | port-pitch-perfector-agents | Port (or decide against) the 3 pitch-perfector subagents (survey-enricher, evidence-collector, viewer-dev) | closed | RESOLVED 2026-06-28: all 3 ported+re-adapted, by-name refs restored in /enrich + method-eval, Agents catalog added (decision 2026-06-28-04) |
| 2026-06-28 | multimodal-llms-reference-impl-handoff | Multimodal-LLMs survey → reference-implementation study handoff | open | two study-ready methods (FastV pruning; connector ablation) nominated by survey §13.2 |
| 2026-06-28 | multimodal-llms-crosslink-polish | Multimodal-LLMs survey — cross-link polish pass | open | residual low-cosine candidates + body→appendix forward-link conversions |
| 2026-06-28 | sync-upstream-scope-candidates | Decide which additional infra paths to add to /sync-upstream inbound scope | closed | RESOLVED 2026-06-28: added bench/ .gitignore .viewerignore; held .github/.claude-sync.yml, viewer.content/manifest.json, tools/ |
