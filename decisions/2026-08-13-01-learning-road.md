---
id: 2026-08-13-01
title: The learning road — topic/experiment vocabulary, depth-first queueing, exit condition, compute posture
status: accepted
date: 2026-08-13
---

## Context

A `/grill-with-docs "the learning road"` session resolved what this repo's ongoing work
*is*, after fact-gathering surfaced two things that changed the question.

**The blocked-backlog umbrella was stale.** `todos/2026-07-03-blocked-backlog-consolidated.md`
parked five RIS study follow-ups under "another session's studies (RIS-program, PR #2) —
not ours to modify". PR #2 merged 2026-07-02; `implementation/` on `main` now carries
eight study packages (`tiny_transformer`, `eap_ig`, `steering`, `fastv`, `sae_frontier`,
`connector`, `icl_regression`, `induction_discovery`). The blocker's premise was false,
and had been for six weeks.

**Two central terms were doing double duty.** "Topic" named both a survey-sized area and a
study-sized question; "experiment" named both a single run and a whole study. The stated
cadence — about 5 USD per experiment, ten experiments, at least a month — only resolves
under one reading of each.

The road's two halves also conflict on their face: a curriculum wants breadth (seven of
the ten domains the `deep-research-survey` skill covers are untouched here, and the
coverage that exists is code-scoped inside `llms-for-coding`), while a capability ladder
wants ten experiments on one thing. At one topic per month these cannot both run at once.

## Decision

Six calls, settled in sequence:

1. **A topic is one study-sized falsifiable question; a survey is a prerequisite, not a
   topic.** Vocabulary recorded in `CONTEXT.md`.
2. **Depth-first.** Surveys are pulled in on demand by the current question rather than
   worked through as a syllabus. The curriculum half is satisfied by absorption, not by
   coverage.
3. **Shrink the GPT-2 reproduction** to a scale where the induction phase change is still
   visible inside a per-experiment budget; keep the 124M run as later confirmation rather
   than as the entry point.
4. **First topic: `todos/2026-07-02-tiny-transformer-gpu-host-rungs.md`, Rung 2** — a ~10M
   model trained from scratch, described in its own todo as "the emergence bridge between
   the toy and pretrained GPT-2". It *is* call 3's shrink, already scoped and implemented.
5. **Exit condition: a topic is understood when the survey section that raised the
   question cites your own measurements in place of the claim it originally cited.**
6. **A rented host is a compute worker, never a repo clone.**

Consequent bookkeeping: the umbrella todo is **closed** rather than rewritten, and the
other five study follow-ups are re-triaged when their month comes, not now.

## Alternatives considered

- **Breadth-first curriculum** (survey the seven uncovered domains, then resume the
  ladder) — rejected: roughly seven months of surveys before any experiment runs, and it
  strands five study follow-ups that already have running code. The existing surveys were
  never chosen from a syllabus anyway — interpretability was seeded by a *gap analysis of
  the coding survey*, which is demand-driven, and is the strongest of the three.
- **A topic = a survey** — rejected: a survey is ~25 files and ~40 evidence questions with
  no compute; it cannot be "ten experiments".
- **Drop the GPT-2 reproduction outright** — rejected: it is the only route to H2 (induction
  phase change) and H4 (seed permutation) at scale, both explicitly deferred by the
  tiny-transformer study. Shrinking preserves the question at a fraction of the cost, and
  a negative result (the phase change *needs* 124M) would itself be a finding about
  scale-dependence that justifies spending a whole month's budget on one run.
- **Spend the first topic-month on the 124M run** (~"tens of dollars", per its own todo) —
  held in reserve behind the shrunk run rather than rejected.
- **Exit condition = per-hypothesis PASS/FAIL in the report** — rejected as *sufficient*:
  `sim-report-completeness` §7 already mandates it, so it is produced for free and does
  not discriminate between a topic understood and a topic merely executed. Retained as
  necessary.
- **Exit condition = able to re-derive the mechanism unaided** — rejected: not
  externally checkable, so it cannot end a month.
- **Rewrite the umbrella as a live index** — rejected: it would recreate a second source
  of truth beside `todos/INDEX.md`, which is how it went stale. `INDEX.md` is the index.
- **Rented host as a repo clone** (git, gates, credentials on the rented box) — rejected
  per `.claude/rules/reset-durability.md`: a host torn down between billing slices is
  maximally reset-prone, and a gate-blocked commit there dies with the instance. It also
  puts the pre-push gate on a machine without the corpus.

## Consequences

- **Enables:** a costed, repeatable unit of work (about 50 USD per topic-month) and an exit
  condition that is a visible diff rather than a feeling.
- **Forecloses:** a coverage-driven survey programme. Uncovered domains are no longer
  tracked as gaps; a fourth survey happens when a question demands one.
- **Follow-up:** the first topic carries a **precondition** — `implementation/tiny_transformer/run_phase3.py`
  must checkpoint densely enough to resume a killed billing slice at zero recompute, with
  one writer per checkpoint file. Recorded in that todo; it is the first task of the month
  and precedes any spend.
- **Bookkeeping:** `todos/2026-07-03-blocked-backlog-consolidated.md` closed; five study
  follow-up todos (`h9`, `sae-frontier`, `eap-ig`, `steering`, `fastv`, `connector`) stay
  open and un-re-triaged by design.
- `CONTEXT.md` created — first entry in the repo's glossary, previously absent by design
  (`docs/agents/domain.md`: created lazily when terms actually resolve).

## Refs

- `CONTEXT.md` — the vocabulary this record settles.
- `todos/2026-07-02-tiny-transformer-gpu-host-rungs.md` — the first topic.
- `todos/2026-07-01-gpt2-training-reproduction.md` — the 124M run, held behind the shrink.
- `todos/2026-07-03-blocked-backlog-consolidated.md` — closed by this record.
- `.claude/rules/reset-durability.md`, `.claude/rules/workflow.md` — the compute posture.
- `.claude/rules/sim-report-completeness.md` §7 — the PASS/FAIL verdict retained as necessary.
- `decisions/2026-07-02-05` (tiny-transformer execution approach),
  `decisions/2026-07-02-04` (RIS-program offline-substrate scope) — the records whose
  "other session" framing this supersedes in fact.
- `prompts/2026-08-12-upstream-sync.md` Conversation 6.
