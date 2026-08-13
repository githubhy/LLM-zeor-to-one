# Reader-Frontier Analysis — 2026-08-13

A measurement of the `you` column in the capability ladder
([development-timeline.md](development-timeline.md)), from the questions actually asked
across the project's history rather than from a quiz.

**Why this instrument.** A question *locates* you; an answer only *bounds* you. A correct
quiz answer proves you were at-or-above some point; a question asked spontaneously,
mid-read, marks exactly where the frontier was that day. A quiz also has a
conflict-of-interest problem here — the same agent would administer and grade it, against
answers the corpus wrote. The question record is pre-existing data neither party designed
for this purpose.

## Sources and fidelity

| Source | N | Fidelity |
|---|---|---|
| `prompts/*.md` `**Request**` lines | 221 across 14 session files | **Paraphrase.** These are agent-written summaries of each turn. Many quote the user verbatim (in quotes); the rest are compressions. Classification is therefore of the summaries, not of raw utterances. |
| `> **Note —**` folds in `surveys/` | 23 | **High.** `survey-explainer-fold` only fires on a real user question asked while reading, so each fold is a recorded question. |
| `appendix-q-reader-questions.md` | 9 | **Excluded.** Its own header says it answers "the questions the main text raises" — skill-synthesised, not user-asked. Using it would have measured the corpus again. |

## Classification scheme

Each request is either **OPS** (commit/push/sync/branch/harness/skill-invocation — no
evidence about subject understanding) or **LEARN** (a question about the subject matter).
LEARN questions carry a *kind* and a *rung*.

| Kind | Meaning | Weight |
|---|---|---|
| K1 | *What is this?* — terminology, notation, definition | lowest |
| K2 | *How does it work / where does it come from?* — derivation, missing steps | |
| K3 | *Why this way / why not otherwise?* — design rationale, unification | |
| K4 | *What breaks it / is this real?* — falsification, reality-check, correctness challenge | **highest** |
| K5 | *What else / what is missing?* — scope and gap questions | |

K4 is weighted highest because it is the standard set in [CONTEXT.md](../CONTEXT.md):
*you understand a mechanism when you can predict what breaks it.*

## Results

### Volume

Of 221 logged requests, **~59 are LEARN** (27%) and ~162 are OPS. The OPS share is
expected for a repo whose work is largely orchestration; it is not itself a finding.

### Rung distribution — two independent measures agree

| Rung | LEARN questions | Survey folds |
|---|---|---|
| L1 derive the mechanism | ~45 (76%) | 20 / 23 (87%) |
| L2 scale it | ~6 | 1 |
| L4 observe a trained model | ~6 | 0 |
| L5 measure across training | ~3 | 0 |
| L7 build from scratch | ~3 | 0 |

The fold distribution (`appendix-a` 14, `appendix-c` 6, `language-models` 2,
`appendix-e` 1, and **zero** in appendices D, F, G, H, I) was derived from file counts and
the request classification from prose, independently. They agree: the engaged frontier is
**L1, first-principles attention**, and it never moved far past it.

Appendices D–I — GPT-2, modern dense, scaling, MoE, synthesis, mechanistic
interpretability — produced no folds and few questions, despite being the larger half of
the corpus. Counts cannot separate *never read* from *read and satisfied* from *read and
did not think to ask*; the third is the one that matters and is invisible here.

### Kind distribution — the quality signal is good

Roughly 13 of 59 LEARN questions are **K4** (~22%), and several caught real defects:

- *"really no intermediate steps missing?"* — forced an audit of the NLL derivation
- *"The dimension convention of those matrices are correct?"*
- *"8?"* — challenged a `rank <= d_k = 8` claim in a figure caption
- *"Are the columns assigned like this?"* — the user annotated an equation with his own
  token layout and asked for confirmation
- *"How do you know the query at position 3 has own_A=1 and the key at position 2 has
  prev_A=1?"* — a comprehension challenge on a worked trace
- *"To what extent is M different from the whitening Sigma^-1?"* — a quantitative
  challenge to an analogy
- *"How large are d, T, d_k, d_v in real models?"* and *"how large a model can a 16GB
  laptop train?"* — reality-checks against real scale

A 22% K4 rate with several true-positive catches is a healthy signal. Where the questions
went, they went deep.

Signal-processing framing recurs and is self-generated, not prompted: the matched-filter
mapping, *"is it a good idea to map to an **adaptive** filter rather than a fixed matched
filter?"*, and *"So LLR is a special case of the logit?"*. These are K3 unification
questions from the L0 substrate, and they are the strongest evidence in the record of
independent reasoning rather than absorption.

### The trajectory — and the finding that matters

```
2026-06-13  ######                          6 LEARN
2026-06-17  ###########                    11
2026-06-20  .                               0   (infra session)
2026-06-26  .                               0   (sync session)
2026-06-28  ######                          6
2026-06-29  ############################   28   <- peak
2026-07-01  ########                        8
------------------------------------------------------------------
2026-07-02  .                               0
2026-07-03  .                               0
2026-08-12  .                               0
```

**Across the last three logged sessions — 2026-07-02 to 2026-08-13, 21 conversations —
there is not one subject-matter question.** Every request is orchestration: *proceed*,
*commit and push*, *what's the current status*, *go ahead at full speed automatically*.

That window is exactly when the study program was executed: H15, EAP-IG edge-level, the
two-head-softmax reproduction, SAE-frontier, steering, FastV, connector. **Eleven studies
produced zero questions.**

**The confound, stated plainly.** Those sessions ran under an explicit *"go ahead
end-to-end automatically unless you genuinely need my help"* mandate. Under that mode
there are structurally fewer user turns, so a low question count is partly an artifact of
the execution mode, not proof of disengagement.

But that is the finding, not a defence of it. **The execution mode is the mechanism.** A
mandate that removes the turn boundary removes the question surface with it; understanding
is not outsourced by a skill writing a document, it is outsourced by choosing a mode in
which no one has to ask anything. The surveys are the visible half of that; the studies are
the larger, quieter half.

## Verdict on the `you` column

| Rung | Corpus | Reader | Basis |
|---|---|---|---|
| L0 substrate | Done | **Done** | Predates the repo; visible in the self-generated SP unifications |
| L1 derive | Done | **Engaged, unfinished** | 76% of questions and 87% of folds land here, with real K4 catches — but K1 terminology questions ("what is L", "what is a logit", "what is W_OV called") were still appearing late in the deepest session |
| L2 scale | Done | **Thin** | ~6 questions, 1 fold; appendices D–H largely silent |
| L4 observe | Done | **Very thin** | ~6 questions, 0 folds — despite 11 studies |
| L5 trajectory | current | **Not started** | 3 questions, all agenda-setting (grokking, seed variation, ICL-from-training) rather than worked |
| L7 build | none | **Not started** | 3 questions, all feasibility-scoping |

L1 is genuinely engaged and genuinely unfinished. Everything above L1 is thinner in the
reader column than in the corpus column, and the gap widens with height.

## What this changes

1. **The execution mode is a learning variable, not just a speed knob.** "Go ahead
   end-to-end automatically" is the correct setting for harness work and the wrong one for
   a topic-month. Topic 1 should run with the turn boundary deliberately preserved at each
   decision point.
2. **Topic 1's rung choice is confirmed and its risk is now named.** L5/L7 is the right
   target, and the failure mode is precisely the one this analysis found: it could be
   executed autonomously and close with the corpus advancing and the reader not. The
   reader half of the exit condition in [CONTEXT.md](../CONTEXT.md) — predict before the
   run, explain the residual after — exists for this.
3. **The silent region (appendices D–I) is where a targeted probe is worth it.** Not a
   general quiz; a probe of the regions the question record shows as never-interrogated.
4. **Ask more K4 questions and fewer K1.** The K4 rate is already good; the leverage is in
   raising it where the record is silent, not in raising the total.

## Refs

- Source data: `prompts/*.md` (14 session files, 221 requests), the 23
  `> **Note —**` folds under `surveys/`.
- [CONTEXT.md](../CONTEXT.md) — the *understand = predict what breaks it* standard and the
  two-half exit condition.
- [development-timeline.md](development-timeline.md) — the capability ladder this measures.
- `prompts/2026-08-12-upstream-sync.md` Conversation 8.
