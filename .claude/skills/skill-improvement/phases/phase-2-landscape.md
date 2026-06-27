# Phase 2: Landscape scan

## Goal
Find the SOTA the skill competes with, so the proposal is grounded, not invented.

## Steps
- Enumerate 5-8 comparison families relevant to the skill's domain (e.g. for a survey skill:
  survey-gen systems, eval frameworks, citation-grounding; for an impl-study skill:
  reproducibility, benchmarking, sensitivity/DoE, finite-precision, comparative-study rigor).
- `full` mode: run `templates/wf-landscape.workflow.js` — one live-web evidence agent per
  family, pipelined into an adversarial-verify stage (flag fabrications/mis-citations) and a
  completeness critic (gaps + the missing practices = candidate improvements). Save `landscape.json`.
- `quick` mode: do the scan from parametric memory + a few targeted searches; still run a
  self-adversarial pass over your own claims.

## Output
`bench/<target>/landscape.json` (or an inline summary in `quick`). See gotcha #4: cite
mechanisms, not numbers.
