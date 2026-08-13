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
