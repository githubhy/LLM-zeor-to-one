# Context

Glossary for this repo's **learning road** — the vocabulary that governs how work is
organised, queued, and declared finished.

Scope note: per `docs/agents/domain.md` this file covers the harness and how work is
run, **not** survey content. A survey's technical claims are governed by its own
`order.json`, `references.md`, and the rules in `.claude/rules/`.

Settled 2026-08-13; the reasoning and the alternatives rejected are in
`decisions/2026-08-13-01-learning-road.md`.

## The road

The repo pursues two goals at once, and they are **the same artifact seen twice**:

- **Curriculum** — breadth across LLM/AI methods.
- **Capability ladder** — the ability to run and defend a real experiment.

They are not scheduled separately. A topic advances both: the ladder produces a
measurement, the curriculum absorbs it.

## Glossary

**Topic** — *one study-sized, falsifiable question*, worth roughly a month.
Not a field, not a survey. `docs/h9-algorithmic-icl-study.md` is the template: one
question ("is in-context learning doing gradient descent?"), several hypotheses, one
report. A topic is the unit the cadence below is measured in.

Avoid using "topic" for an *area* (interpretability, alignment, serving). Those are
**domains**, and a domain contains many topics.

**Experiment** — one run against one hypothesis, costing about **5 USD** of rented
compute. Not a whole study. A topic is about **ten** experiments.

**Topic-month** — the working unit: ~10 experiments, about **50 USD**, at least one
calendar month. The month is a floor, not a target; the exit condition below is what
actually ends it.

**Survey** — a **prerequisite**, never a topic. A survey carries no experiments; it is
what you read and write to find the question worth a topic-month. Surveys are pulled in
**on demand** by the question at hand, not worked through as a syllabus.

**Study** — the executed topic: a plan, an `implementation/<name>/` package, artifacts,
and a `docs/` report to the `sim-report-completeness` spine.

**Rung** — a scale step within a study (toy → mini → pretrained). The rung ladder is how
a topic stays inside the per-experiment budget while still reaching a real model.

**Understood** — the exit condition for a topic. A topic is understood when **the survey
section that raised the question cites your own measurements in place of the claim it
originally cited**. The per-hypothesis PASS/FAIL verdict in the study report is
necessary but not sufficient — it is produced automatically by the report spine and has
never by itself been the thing that produced understanding.

## How work is queued

**Depth-first, pulled not pushed.** The next topic is chosen by what the current question
needs, not from a coverage checklist. Consequence: an uncovered domain is not a gap, and
a parked follow-up is not re-triaged until its month comes — re-planning work that will
not run this month produces plans that go stale before execution.

`todos/INDEX.md` is the single index of parked work. Do not maintain a second
consolidated index beside it; the one that existed went stale precisely because it
duplicated `INDEX.md`.

## Compute posture

A rented host is a **compute worker**, never a repo clone. Inputs ship in, checkpoints
ship out; every commit is made from the local machine, where the corpus and the pre-push
gate live.

This follows from `.claude/rules/reset-durability.md`: origin is the only durable store,
and a box torn down between billing slices is the most reset-prone host in the project.

**Precondition on any study before it rents anything** — its driver must checkpoint
densely enough that a killed slice resumes at zero recompute, with exactly one writer per
checkpoint file (`.claude/rules/workflow.md`). A driver that cannot resume cannot be run
inside a per-experiment budget, and fixing that is the first task of the month, before
any compute is bought.
