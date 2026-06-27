Run the full reference-implementation-study sign-off gate sequence for: $ARGUMENTS

`$ARGUMENTS` is `<study> [<topic>] [--gates G1,G2,REPORT] [--report <path>]`. `topic`
defaults to `study`; the runner tolerates `-`/`_` between the study slug
(e.g. `chinchilla-repro`) and the module directory (`chinchilla_repro`).

Steps:

1. Run `python .claude/skills/reference-implementation-study/signoff.py $ARGUMENTS` — runs
   the **mechanical** gates and prints one pass/fail board:
   - **G1–G4** (implementation / baseline / sensitivity / quantization) via `validate_gate.py`
   - **REPORT** (report completeness, `.claude/rules/sim-report-completeness.md` —
     `viewer/tools/check-report-completeness.py`)
   - **CITE** (citation source-tag invariant, `viewer/tools/check-citation-sources.py`;
     reported `n/a` when the report has no `## References`/`## Bibliography` section)
   Use `--gates` to select a subset when Phases 4/5 were skipped
   (e.g. `--gates G1,G2,REPORT`). Exit code 0 = all selected gates PASS.

2. If any gate **FAILS**, read the printed failing checks, fix, and re-run. A failing
   G3/G4 usually means that phase was skipped — drop it from `--gates` rather than
   forcing it.

3. Run the two **agent-driven** audits the script can only remind about (they need an
   agent, not a script):
   - the **`sim-audit`** skill — the untrusting 7-lens numerical-correctness audit; file
     any defects to `bugs/` and fold the per-lens verdict into the report's Audit-Trail
     section.
   - the **`citation-audit`** skill — verify every external citation against its acquired
     source (only if the report carries external citations).

4. Report: the sign-off board, plus whether the two agent-driven audits were run and came
   back clean. **Sign-off is complete only when the board is PASS and both audits have
   been run.**
