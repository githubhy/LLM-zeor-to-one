# Phase 5: Verify (A/B, not assertion)

## 5a — per-item (always)
Use `templates/wf-per-item-verify.py` as the pattern:
- **output items**: a controlled task with a KNOWN answer where the proposed mechanism should
  win (e.g. a planted interaction for a global-SA item; overlapping-CIs-yet-significant for a
  pairwise-significance item; a weight-flip for a multi-metric item). Deterministic where possible.
- **structural items**: build a PROPOSED artifact set and a BASELINE set and show the
  flag-gated check DISCRIMINATES (passes proposed, fails baseline).
- Mark any item the test can't fairly decide INCONCLUSIVE (gotcha #5).

## 5b — end-to-end (full mode)
Use `templates/wf-end-to-end-ab.workflow.js`:
- Drive the FULL target skill on a real scoped task, `original` vs `proposed`, each agent in a
  WORKTREE or namespaced sandbox (gotcha #2), RETURN-not-write.
- Score with a blind judge + any machine gate. TRUST-BUT-VERIFY: re-run the gates yourself
  (gotcha #3). Audit for strays; clean before committing.

## Deliverable
Per-item verdicts + (full) the end-to-end A/B result, all run-traceable.
