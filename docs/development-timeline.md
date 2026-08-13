# Development Timeline

The project's lightweight status board. Statuses are `Planned` / `Active` / `Blocked` /
`Done` only.

Vocabulary here — *topic*, *experiment*, *topic-month*, *understood* — is defined in
[CONTEXT.md](../CONTEXT.md) and was settled by
[decision 2026-08-13-01](../decisions/2026-08-13-01-learning-road.md). Read that first if
"topic" looks like it means "area"; it does not.

## Current Snapshot

| Field | Value |
|---|---|
| Phase | 3 — The Road (repeating topic-months) |
| Status | `Active` |
| Current topic | Topic 1 — does the induction phase change appear below 124M? |
| Current step | Precondition (local, unpaid). **Not started.** |
| Capability rung (corpus) | L5 — entering. L0–L4 done, L6 half, L7 not started (see ladder) |
| Capability rung (reader) | **Unmeasured** above L0. The surveys are skill-produced, so corpus status is not reader status; instrument named in the ladder section |
| Blocked on | Nothing external — the work is local bring-up |
| Compute rented to date | **None.** All 11 studies ran on this laptop |
| Budget shape | ~5 USD per experiment · ~10 per topic · ~50 USD per topic-month |
| Open todos | 13 — 5 future topics, 1 held, 3 harness upkeep, 4 study-internal |
| Last updated | 2026-08-13 |

## Visual Roadmap

```
PHASE 1 — SURVEY THE GROUND                                        Done
  llms-for-coding ................. 29 files   (first, broadest)
  mechanistic-interpretability .... 24 files   (seeded by a gap analysis
                                                of the coding survey)
  multimodal-llms ................. 23 files
  + 2 wikis (laptop-scale feasibility, MI coverage gaps)
  [attention-demo = tooling fixture, not research content]

PHASE 2 — STUDY WHAT THE SURVEYS RAISED                            Done (11)
  induction / emergence ... tiny-transformer-induction
  ICL as gradient descent . h9-algorithmic-icl, h9-softmax-two-head-gd
  circuit discovery ....... h15-automated-discovery
  attribution ............. eap-ig-faithfulness, eap-ig-edge-level
  sparse autoencoders ..... sae-frontier, sae-frontier-ext
  steering ................ steering-headtohead
  multimodal .............. fastv-vision-token-pruning, connector-ablation

  -- every one ran on this laptop. Nothing has been rented. --

PHASE 3 — THE ROAD                                                 Active
  repeating topic-months: ~10 experiments · ~5 USD each · >=1 month
  each ends when the survey section cites YOUR measurement


TOPIC 1 -- induction phase change below 124M -----------------------------

  >> [ ] PRECONDITION            <-- HERE.  local · unpaid · not started
         |- fix bugs/2026-08-13-01  (config-blind resume key, silent)
         |- add intra-run checkpointing + RNG state
         '- BUILD RUNG 2           (no code exists: model + text pipeline)
     [ ] rent · train ~10M from scratch · dense checkpoints
     [ ] analyse: ICL-score vs induction-head-strength overlay
     [ ] EXIT: appendix-A Claim 2 + MI survey 9.1 cite this
               instead of references [60] / [80]
```

## Capability Ladder

A different axis from the milestone table below: that tracks **what has shipped**, this
tracks **what can be done**. For a corpus that already carries full first-principles
derivations, a content curriculum ("learn attention, then transformers") is the wrong
axis — the content is derived. What progresses is *depth of engagement with the same
object*.

**Two columns, and they are not the same number.** The surveys were produced with the
`deep-research-survey` skill. A completed, gate-green, fully-cited survey is evidence
about the **corpus**, not about the **reader** — a document can be correct and its owner
still unable to re-derive it. Collapsing those two into one status is exactly the
wrong-but-plausible inference the repo's own rules warn about, so they are tracked apart.
The `you` column is **unmeasured**, not low: nothing here has measured it, and a guess
would be worth less than the blank.

```
                                                     corpus       you

L0  MATHEMATICAL SUBSTRATE                            Done         Done
    linear algebra · probability · optimization · info theory
    '- the signal-processing background predates the repo: the one
       rung that is genuinely personal, not skill-produced

L1  DERIVE THE MECHANISM FROM FIRST PRINCIPLES        Done         ?
    attention as QKV · softmax · two-layer composition ·
    backprop · Adam · the loss
    '- appendix-a-qkv-first-principles · appendix-b-kernel-regression-family
       appendix-c-toy-transformer

L2  SCALE IT — HOW A REAL MODEL IS ACTUALLY BUILT     Done         ?
    GPT-2 -> RMSNorm/RoPE/SwiGLU/GQA -> the 16N memory wall -> MoE
    '- appendix-d-gpt2 · appendix-e-modern-dense · appendix-f-scaling
       appendix-g-moe · appendix-h-synthesis

L3  THE SYSTEM AROUND THE MODEL                       Done         ?
    data · objectives & scaling · alignment · decoding & serving ·      (code-
    retrieval · agents · evaluation · cost                              scoped)
    '- the llms-for-coding body, 19 sections

L4  OBSERVE MECHANISM IN A TRAINED MODEL              Done         ?
    probing · activation patching · attribution · SAEs · steering ·
    automated circuit discovery
    '- the MI survey + all 11 studies

------------------------------------------------------------------------
L5  MEASURE MECHANISM ACROSS TRAINING            <-- CURRENT RUNG, both columns
    trajectory not snapshot · when circuits form · phase changes ·
    telling a real transition from a metric artifact
    '- toy rung only (0.17M). Nothing at real scale.

L6  PREDICT AND FALSIFY                               Half         Not started
    call the ablation outcome in advance · theory as a predictor
    of a curve, not a bound
    '- the *technique* exists (h15, eap-ig do causal work); it has never
       been used as a prediction.  <-- Topic 1 Claim 3

L7  BUILD IT FROM SCRATCH AT SCALE                    Not started  Not started
    own the whole loop: data -> tokenizer -> training -> checkpoints ->
    analysis, on rented compute
    '- 0.17M toy is the ceiling to date
```

### Measuring the `you` column

The instrument already exists and was written by the corpus for exactly this:
`surveys/mechanistic-interpretability/appendix-q-reader-questions.md` — nine questions of
the form *"why is it built this way / what breaks otherwise / why not the obvious
alternative"*. That is the same shape as the standard in [CONTEXT.md](../CONTEXT.md)
(*understand = predict what breaks it*), so answering them cold, before reading the
answers, is a real measurement rather than a feeling. The coding survey's appendix ladder
A–I admits the same treatment.

This is cheap, unscheduled, and does not consume topic budget. It is listed here so the
blank in the `you` column has a way to be filled rather than standing as a permanent
unknown.

### Why the split strengthens the road rather than undermining it

A skill can produce a survey. **A skill cannot run an experiment on your behalf in the
way that matters** — you drive it, it breaks, you debug it, you decide what the residual
means. Documents are far easier to outsource-without-understanding than experiments are,
which is precisely why the road's centre of gravity is topic-months rather than more
surveys. The correction invalidates the ladder's *measurement*; it confirms the road's
*direction*.

It does expose one hole in the topic exit condition, recorded against Topic 1: "the survey
cites your own measurements" is an edit a skill could also make. The personal half is to
write down, **before** the run, what you expect and why — then explain the residual
yourself afterwards. Claim 3's discipline, turned on the reader instead of the model.

**The asymmetry to be aware of.** Eleven studies, and not one model trained from scratch
beyond a 0.17M toy — every study to date analyses a model someone else trained. The
*corpus* is derivation-rich and build-poor, the reverse of the usual practitioner shape
(L3 plus some L4, no L1 at all). Note this is a statement about the corpus; the `you`
column's asymmetry is unmeasured until the instrument below is run.

**Topic 1 is where L5 and L7 arrive together.** A trajectory cannot be watched without
owning the training run that produces it. This is *why* the precondition turned out to be
"Rung 2 has no code" rather than "change a config" — the topic is quietly two rungs, not
one, and that is the reason its first weeks are engineering rather than science.

**L6 is the cheapest item on the board.** The causal tooling already exists; what is
missing is the discipline of writing the predicted outcome down *before* running the
ablation. It costs a line in a plan, and it is the difference between describing a
mechanism and understanding one — the standard set in [CONTEXT.md](../CONTEXT.md).

**Deliberately absent.** Breadth — pretraining/scaling laws, alignment, RAG, agents,
serving, evals, long-context, safety — is held at L3 and only through the code lens.
Under the depth-first goal these are not gaps but inventory, pulled when a question needs
them. Listed here so the absence stays a visible choice rather than an inherited one.

## Milestones

| # | Milestone | Status | Notes |
|---|---|---|---|
| M1 | Harness ported and gated | `Done` | Adapted from `../data-channel-receiver`; ~25 pre-push gates active |
| M2 | First survey — LLMs for coding | `Done` | 29 files; the appendix ladder A–I |
| M3 | Second survey — mechanistic interpretability | `Done` | Demand-driven: raised by a gap analysis of M2 |
| M4 | Third survey — multimodal LLMs | `Done` | 23 files |
| M5 | Reference-implementation study program | `Done` | 11 studies, 8 `implementation/` packages |
| M6 | The learning road defined | `Done` | Vocabulary, cadence, exit condition, compute posture |
| M7 | **Topic 1 precondition** | `Active` | Resume hardening + Rung-2 bring-up; gates all spend |
| M8 | Topic 1 — Rung 2 trained and analysed | `Planned` | First rented compute in the project's history |
| M9 | Topic 1 exit — survey cites own measurement | `Planned` | The first closed topic-month |
| M10 | Topic 2 | `Planned` | Pulled from the queue when M9 lands, not before |

### Topic queue (not scheduled — pulled on demand)

Depth-first is a deliberate choice: the next topic is chosen by what the current question
needs, not from a coverage checklist. These are candidates, deliberately **not**
re-triaged until their month comes.

| Candidate | Source todo |
|---|---|
| ICL follow-ons (trained two-head run, seed set, GD++) | `todos/2026-07-04-h9-followups.md` |
| SAE frontier at Gemma scale | `todos/2026-07-02-sae-frontier-followups.md` |
| EAP-IG edge-level completion | `todos/2026-07-02-eap-ig-followups.md` |
| Steering on a Gemma-2 substrate | `todos/2026-07-02-steering-followups.md` |
| FastV / connector at real scale | `todos/2026-07-02-fastv-followups.md`, `todos/2026-07-02-connector-ablation.md` |
| GPT-2 124M from scratch | `todos/2026-07-01-gpt2-training-reproduction.md` — **held** behind Topic 1's result |

## Update Log

**2026-08-13 — Capability ladder added; the goal stated as understanding.**
The goal was made explicit — understand these models, not use them well — and recorded in
`CONTEXT.md` as the premise depth-first queueing rests on. Topic 1's scope grew to include
Claim 3 (the ablation), since Claim 2 alone is a correlation. A capability ladder (L0–L7)
was folded into this document as the companion axis to the milestone table: milestones
track what shipped, the ladder tracks what can be done. It makes one asymmetry explicit —
the corpus is derivation-rich and build-poor — and explains why Topic 1's precondition was
larger than expected: L5 and L7 arrive together, because a trajectory cannot be watched
without owning the run that produces it.

The ladder's first draft was **wrong** and was corrected the same day. It marked L1–L4
"Done" from the existence of the survey artifacts — but those were produced with the
`deep-research-survey` skill, so they are evidence about the *corpus*, not about the
*reader*. The ladder now carries two columns, with the reader column recorded as
**unmeasured** rather than guessed, and names an existing instrument for filling it
(`appendix-q-reader-questions.md`, nine "why this way / what breaks otherwise" questions —
the same shape as the CONTEXT.md standard). The correction invalidates the ladder's
measurement and *confirms* the road's direction: a skill can write a survey, but it cannot
run an experiment on your behalf in the way that matters, which is why the road's centre of
gravity is topic-months rather than more surveys. It also exposed a hole in the topic exit
condition — "the survey cites your own measurements" is an edit a skill could make too — so
the personal half is to predict the result before the run and explain the residual after.

**2026-08-13 — Topic 1 precondition audited; it is bigger than it looked.**
Ran the resumability audit on `implementation/tiny_transformer/run_phase3.py`.
Single-writer-per-checkpoint passes by construction. Three gaps block spend: a
config-blind resume key that silently reuses reduced-config seeds
(`bugs/2026-08-13-01`, high), no intra-run checkpointing (a kill mid-seed loses the whole
seed — invisible at 800 steps, most of a billing slice at 20k), and **no Rung-2
implementation at all** (`build_toy` is the only model factory; `data.py` is
synthetic-only). Rung 2 is bring-up work, not the same code at a bigger config. Tracked
in `todos/2026-08-13-phase3-resumability-hardening.md`.

**2026-08-13 — The learning road settled; this timeline created.**
Nine questions resolved (`decisions/2026-08-13-01`): a topic is one study-sized
falsifiable question, a survey is a prerequisite rather than a topic, ~10 experiments at
~5 USD over at least a month, depth-first with surveys pulled on demand, a rented host is
a compute worker never a repo clone, and a topic is *understood* when the survey section
that raised the question cites your own measurements. `CONTEXT.md` created as the repo's
first glossary. The blocked-backlog umbrella closed as stale — its "another session's
studies" premise died when PR #2 merged on 2026-07-02 and had been false for six weeks.

**2026-08-12 — Inbound upstream sync; reachability to zero.**
Synced harness + viewer through upstream `cedfccb2`. Cross-link gaps cleared to zero and
both wikis linked from the survey sections they support, promoting
`.claude/reachability-severity` to `error`. Sync-back candidates filed.

**2026-07-05 — Host move to Mac unblocked the upstream-port backlog.**
The multi-span highlight fix, the `serve.js` EISDIR guard, and the citation T12 e2e
timeout all resolved and mirrored upstream (PR #36).

**2026-07-02 — The study program landed on `main`.**
PR #1 (mechanistic-interpretability survey) and PR #2 (reference-implementation program)
merged. Eight `implementation/` packages and the study reports became repo-wide property
— a fact that took until 2026-08-13 to be reflected in the tracking.

**2026-07-01 — Appendix I built out from a coverage gap.**
The MI coverage-gaps wiki drove five clusters into a new Appendix I of the coding survey
(22 equations, references [70]–[93]), with two citation errors caught and fixed by the
audit pass. The clearest instance of the demand-driven pattern later formalised as
depth-first.

## Maintenance

Per `.claude/rules/workflow.md`: update Current Snapshot whenever status, phase, dates, or
key notes change; update the visual roadmap only on phase reordering or structural change;
append to the Update Log for meaningful deliveries, blockers, or re-scopes.
