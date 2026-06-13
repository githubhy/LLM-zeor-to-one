# deep-research-survey skill fork (v2) — minimal implementation of the proposal

A minimal, auditable fork of `.claude/skills/deep-research-survey/` that **implements
two proposal changes** so the harness can A/B the *current* skill against an
*updated* skill end-to-end:

- `phase-4-synthesis.v2.md` — replaces the blind UNION-merge with **memory-guided
  sequential synthesis** (proposal P1-2).
- `phase-5-report.v2.md` — adds a mandatory **self-evaluation rubric gate** before
  sign-off (proposal P0-2).

Phases 1–3 are unchanged (the baseline files are reused verbatim). The v2 skill =
baseline phases 1–3 + these two v2 phases.

## How the end-to-end A/B is run (credit-free)

The earlier blocker — `run-integration-test.sh` driving a nested headless `claude -p`
that returned "Credit balance is too low" — is avoided by running the skill
**in-session through the Workflow budget** instead. The runner
(`skill_ab.workflow.js`, launched via the Workflow tool) feeds each arm the full
skill instruction set (baseline vs v2) on one frozen topic, generates the surveys,
and scores them with a single-blind judge. Same acceptance test, no headless CLI,
no added credits.

## Honest scope

This runs the skill's **process** (scope → outline → memory-guided synthesis →
self-eval gate → report) on a small topic with **domain-knowledge evidence (no live
web)**, since the changes under test live in the synthesis/report phases, not the
evidence phase. It is a faithful end-to-end run of the real SKILL.md instructions —
a large step up from the earlier isolated-mechanism toy tests — but it is not the
full multi-agent web-research skill on a 90-page survey. Results and the comparison
are in `../scenarios/RESULTS-2026-05-30.md` (Update 7).

## SUPERSEDED (2026-05-30)

The standalone fork here is superseded by the in-skill mode switch implemented in
`.claude/skills/deep-research-survey/` (commit `af86f98`): the real `SKILL.md` now
has a `## Mode` selector (`original` default | `proposed`) with additive
Proposed-mode addenda per phase. Run the real skill in `proposed` mode instead of
this fork. Kept here as the historical first implementation + the credit-free
`skill_ab.workflow.js` runner. Verification of the in-skill switch: RESULTS Update 9.
