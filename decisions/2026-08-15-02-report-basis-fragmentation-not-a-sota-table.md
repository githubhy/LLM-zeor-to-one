---
id: 2026-08-15-02
title: Report the 2026-08 sweep as a basis-fragmentation finding rather than refreshing the SOTA table
status: accepted
date: 2026-08-15
plan: surveys/multimodal-llms/_scratch/brief-2026-08-15-expansion.md
---

## Context

The `multimodal-llms` max-mode expansion included a 2026-06 → 2026-08 frontier sweep, whose
stated purpose was to refresh §11.1's quantitative SOTA snapshot and §13's open problems
against seven weeks of drift. The evidence agent came back unable to do that, and said so
explicitly: *"insufficient evidence to state a single trustworthy 'current leading score'
for any of MMMU, MMMU-Pro, MathVista, or MMBench as of 2026-08 within this sweep's budget."*

What it found instead was that four sources reported four materially different "current
best" scores for a benchmark of the same name inside a two-week window — roughly $80\%$ to
$94\%$ — with an official vendor model card at the bottom of that range and a third-party
aggregator at the top. Separately, one public MathVista leaderboard's own metadata recorded
0 of 39 listed models as independently verified and 37 as vendor self-reported.

The plan assumed a refresh was possible. It was not, and the reason it was not is itself a
result. That is a plan-vs-reality conflict the brief did not pre-decide, so it is recorded
here.

## Decision

Publish the sweep as a **methodological finding about the evidence base** (new §11.4, plus
§13.1 item 7) and add **no ranked SOTA table**. Keep §11.1's existing snapshot, whose claims
are already stated conditionally on harness and protocol.

## Alternatives considered

- **Refresh §11.1 with the new numbers, caveated.** Rejected. The observed cross-source
  spread (~14 points) is *wider than most of the model-to-model differences such a table is
  used to argue about*, so the table's ordering would be substantially an artifact of which
  source each row came from. A caveat under a table does not stop readers using the table;
  the ordering is the payload, and here the ordering is not supported.
- **Pick the single most methodologically transparent source and table only that.** Rejected
  for now, though it is the closest call. One evaluator did disclose a protocol (question
  count, answer format, output-token cap) and would have been defensible. It was not used
  because a single-source table still reads as a field ranking, and this survey would then be
  asserting an ordering it could not reproduce. Recorded as the natural upgrade path: if a
  single independent harness is fetched and its protocol documented, a single-harness table
  becomes citable. Filed as `todos/2026-08-15-multimodal-sota-single-harness.md`.
- **Drop the sweep as a null result.** Rejected. "We looked and could not build the table"
  is exactly the kind of finding that gets silently dropped and then silently re-attempted;
  and the *reason* it could not be built bounds every comparative claim in §10 and §11, which
  makes it load-bearing rather than a process note.
- **Cite the specific text-only-solvability percentages the sweep surfaced** (a benchmark
  answerable from text alone at some measured rate). Rejected: the agent explicitly flagged
  those numbers as read via search-engine paraphrase rather than from the primary PDF, and
  recommended re-verification before they were stated as hard numbers. Using them would have
  been precisely the memory-citation failure `.claude/rules/citation-integrity.md` forbids,
  laundered through an agent's own caveat. The qualitative claim is made; the numbers are not.

## Consequences

- **Enables:** a defensible §11 that does not have to be re-litigated every time a
  leaderboard moves, and an open problem (§13.1 item 7) with a concrete, cheap remedy —
  report a single-frame or text-only control beside every multimodal result.
- **Forecloses:** this survey cannot be used to answer "which multimodal model is best in
  2026-08". That is the correct outcome; it could not answer it truthfully before either, it
  simply would not have said so.
- **Follow-up:** `todos/2026-08-15-multimodal-sota-single-harness.md` (the single-harness
  upgrade path), and `todos/2026-08-15-multimodal-residual-gaps.md` (the sweep's own
  unverified numbers, which need a primary-PDF pass before any of them is cited).
- **Precedent:** this is the same discipline `.claude/rules/calibration-residuals.md` check 4
  requires at the moment of *attribution*, applied one step earlier — at the moment of
  deciding whether a comparison can be published at all.

## Refs

- `surveys/multimodal-llms/_scratch/ev-frontier-eval.md` — the sweep's own ledger, including
  its "Basis conflicts" section and its explicit verdict.
- `surveys/multimodal-llms/state-of-the-art-and-practice.md` §11.4; `open-problems-and-roadmap.md` §13.1 item 7.
- `.claude/rules/sim-report-completeness.md` `[opt:SIM-REQBASIS]` / `[opt:SIM-REFPOP]` — the
  published-number-is-a-configuration-stack rule this instantiates for a survey rather than a report.
- Commit `83fe194`.
