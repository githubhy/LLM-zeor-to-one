# Todos Index

| date | slug | title | status | hook |
|---|---|---|---|---|
| 2026-06-17 | fix-serve-api-md-eisdir-crash | Fix serve.js /api/md/<empty-or-dir> EISDIR crash (upstream + re-sync) | open | one malformed GET kills the dev server; deferred per user, fix upstream then re-sync (bug 2026-06-17-01) |
| 2026-06-19 | port-multispan-highlight-fix-upstream | Port the multi-span inline-math highlight fix to the upstream viewer | open | local viewer.js fixed (bug 2026-06-19-01); same branch buggy upstream, port per convergence policy |
| 2026-06-26 | clean-residual-wireless-leakage-in-viewer-tools | Clean residual wireless example-strings in viewer/tools/ docstrings | open | /sync-upstream leakage grep caught 4 ntn/ldpc example paths from the 2026-06-13 bootstrap; cosmetic, retarget to LLM examples |
| 2026-06-26 | port-method-eval-and-figure-conventions | Consider porting upstream method-eval skill + figure-operating-conditions.md | open | DRS skill references both but they're outside the 71-file sync delta; genericized for now (sync branch batch 1) |
