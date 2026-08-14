# Context

Glossary for this repo's **learning road** — the vocabulary that governs how work is
organised, queued, and declared finished.

Scope note: per `docs/agents/domain.md` this file covers the harness and how work is
run, **not** survey content. A survey's technical claims are governed by its own
`order.json`, `references.md`, and the rules in `.claude/rules/`.

Settled 2026-08-13; the reasoning and the alternatives rejected are in
`decisions/2026-08-13-01-learning-road.md`.

## The goal

**To understand these models, not to use them well.** Stated explicitly 2026-08-13.

This is the premise the rest of this file rests on, and it is load-bearing rather than
decorative. Depth-first queueing only survives the breadth argument under this goal: a
*use* goal would want the practical stack — fine-tuning, RAG, agents, serving,
quantization, evals — none of which the current topic queue contains, and would have made
breadth-first correct instead. **If the goal ever changes, re-open the depth-first call
before re-planning anything else** — it is the decision that inverts.

The working standard for "understand", given a signal-processing background: **you
understand a mechanism when you can predict what breaks it.** A curve you can describe is
not yet a mechanism you understand; an ablation whose outcome you called in advance is.
This is why a topic's scope reaches for the falsifiable claim in its section, not only
the observable one.

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

**Understood** — the exit condition for a topic, in two halves.

*Corpus half*: **the survey section that raised the question cites your own measurements
in place of the claim it originally cited**. The per-hypothesis PASS/FAIL verdict in the
study report is necessary but not sufficient — it is produced automatically by the report
spine and has never by itself been the thing that produced understanding.

*Reader half*: **you wrote down what you expected before the run, and explained the
residual afterwards.** Added 2026-08-13, because the corpus half alone has a hole: a
survey edit is something a skill can also make, so a topic-month could close with the
corpus advancing and the reader not. Documents are easy to
outsource-without-understanding; a prediction made in advance is not. This is the same
discipline as the ablation-with-a-called-outcome that defines understanding above, turned
on the reader instead of the model.

**Corpus status is not reader status.** The surveys were produced with the
`deep-research-survey` skill, so a gate-green, fully-cited document is evidence about the
corpus alone. The capability ladder in `docs/development-timeline.md` tracks the two in
separate columns for this reason, and records the reader column as *unmeasured* rather
than inferring it from the artifacts.

## How work is queued

**Depth-first, pulled not pushed.** The next topic is chosen by what the current question
needs, not from a coverage checklist. Consequence: an uncovered domain is not a gap, and
a parked follow-up is not re-triaged until its month comes — re-planning work that will
not run this month produces plans that go stale before execution.

`todos/INDEX.md` is the single index of parked work. Do not maintain a second
consolidated index beside it; the one that existed went stale precisely because it
duplicated `INDEX.md`.

## How a study session runs

Settled 2026-08-13 (`decisions/2026-08-13-02`), against the evidence in
`docs/reader-frontier-2026-08-13.md`.

**The shape.** The session opens with **one old fold, re-answered from memory** — then a
short menu of topics drawn from the *measured* frontier. The reader takes one, or
overrides with whatever they actually want. Then: read, ask, the agent answers, the answer
gets folded in — and if a question needs an experiment, run one. Authoring surveys is not
required of the reader; **asking is the work.**

**Why it opens with recall** (added 2026-08-14, `decisions/2026-08-14-01`). *Fluency* —
following an answer with the corpus open — is not *storage strength*, and it produces a
convincing sense of mastery on its own. The whole reason the reader column of the ladder
had to be measured separately is that nothing in the session distinguished the two. One
fold recalled cold, oldest-first, is the cheapest instrument that does; a blank is a
better menu item than anything the ranking will produce.

**The pulse check — the only guardrail.** A study session that produces **zero folds did
not happen.** Questions were the metric that tracked frontier movement, and
`survey-explainer-fold` already records them, so the check costs nothing and leaves future
sessions the same measurement for free. It is a pulse, not a quota: one real question
folded in beats five manufactured ones.

**How the menu is drawn.** From the gaps the frontier analysis found, in order —
appendices D–I (zero folds ever recorded), then L2, then L4 (very thin despite eleven
studies). Never from what is easy to explain. It is also **gated to one rung above the
reader**: `.claude/study-prereqs` records what each document presumes, so the menu cannot
offer mechanistic interpretability at scale to someone whose attention derivation is still
open. Held-back documents are always reported, never silently dropped.

**What this replaced.** An earlier proposal made the reader the *author* and the agent a
reviewer. It was wrong, and the reader's own record refuted it: the single most productive
learning session on file (2026-06-29, 28 subject-matter questions, three times any other)
was pure read-ask-fold with the agent doing the writing. Authoring is a **proxy** for
engagement; the real variable is **who holds the thread**, and in this model the reader
holds it by choosing and asking. Autonomous end-to-end mode remains correct for harness
work and is **out of bounds inside a topic-month** — that mode is what removed the question
surface in the first place.

Creating a new survey mid-session is allowed when a question demands one; that is what
*pulled on demand* already means and is not a conflict with depth-first.

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
