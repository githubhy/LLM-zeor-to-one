---
slug: multimodal-sota-single-harness
date_filed: 2026-08-15
status: open
---

# Build a single-harness multimodal SOTA table

## Context

`decisions/2026-08-15-02` declined to refresh `surveys/multimodal-llms` §11.1 with 2026-08
leaderboard numbers, because the 2026-08-15 sweep measured a ~14-point spread across four
sources for a benchmark of the same name inside a two-week window, and found one public
leaderboard whose own metadata records 0 of 39 models independently verified against 37
vendor self-reported. §11.4 now publishes *why* no cross-source table is citable.

That is the honest state, not the desirable one. The decision recorded the upgrade path and
this file tracks it: **the fix is one harness, not more sources.** Adding sources makes the
spread better characterized and no more comparable.

The closest-call alternative the decision rejected was to table the single most
methodologically transparent evaluator found (it discloses question count, answer format, and
an output-token cap). That was deferred rather than dismissed — it becomes correct as soon as
its protocol is documented in-repo and the numbers are traceable, at which point the table is
a single-harness comparison rather than an assembled ranking.

## What is left

- Pick one harness and fetch its protocol documentation to `download/` (or `docs/specs/`), so
  the protocol itself is citable under the source-tag invariant rather than described.
- Record, per benchmark: split and size, shot count, decoding parameters, answer-extraction
  rule, harness version, and whether each row is that harness's own run or an ingested vendor
  number. A row that cannot state all of these does not go in the table.
- Add the table to §11.1 as an explicitly single-harness artifact, and rewrite §11.4 to point
  at it as the resolution rather than as an open condition (`results-reconciliation` will
  otherwise leave §11.4's framing stale — that is exactly the framing-staleness class).
- Re-check §13.1 item 7, part of whose claim is that no such table exists.

## Acceptance

- §11.1 carries a comparison in which every cell traces to one harness under one disclosed
  protocol, and the protocol is a repo-held source, not a URL description.
- §11.4 no longer says a citable table cannot be built, or says so only about *cross-source*
  tables, with the single-harness table cited as the counterexample.
- No number in the table is vendor self-reported without being labelled as such in its own cell.

## Refs

- `decisions/2026-08-15-02-report-basis-fragmentation-not-a-sota-table.md` — why this was deferred.
- `surveys/multimodal-llms/_scratch/ev-frontier-eval.md` — the sweep ledger, including its own
  recommendation to fetch an independent leaderboard directly rather than any secondary aggregator.
- `.claude/rules/sim-report-completeness.md` `[opt:SIM-REQBASIS]` — published number = reference
  performance + configuration stack.
