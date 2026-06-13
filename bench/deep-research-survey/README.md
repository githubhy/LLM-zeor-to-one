# deep-research-survey benchmark harness

A test/verify harness to compare the `deep-research-survey` skill **before vs after** the improvements in `proposals/deep-research-survey-improvement-2026-05-30.md`.

It combines two traditions:

- **Process / behaviour** — borrowed from `obra/superpowers` (parse the session transcript and assert behaviour; pressure-test discipline gates). This is the rigorous, cheap, near-deterministic half.
- **Output quality** — borrowed from the survey-generation eval frameworks the proposal surveyed (SurveyEval, SurveyBench, SurGE, SGSimEval, SurveyLens, DeepSurvey-Bench): a multi-dimension rubric plus citation Recall/Precision/F1. Superpowers has no equivalent of this half, because its skills are discipline skills with downstream real tests; a *generative* survey skill needs both.

## The honest constraint

A `SKILL.md` is agentic instructions, not deterministic code — you can only measure it by running real surveys and scoring the outputs, and LLM runs are noisy. So: pin one generator model across both arms (the only variable is the `SKILL.md`), repeat each topic N>=3 times, and report deltas with confidence intervals. A single before/after pair is an anecdote.

## What it measures

| Tier | Metric | How | Validates proposal item | Cost |
|---|---|---|---|---|
| **Process** | skill invoked, evidence dispatched, **silent-agent-death rate**, citation gate ran, survey written, agent-sizing, synthesis-on-main-thread | `assert_transcript.py` (parse `.jsonl`) | P0-1, citation gate | near-free |
| **Process** | per-agent tokens + cost | `analyze_tokens.py` | P0-1, P2-2 | near-free |
| **Quality (mechanical)** | consistency (duplicate/orphan equation IDs), reference integrity, citation traceability | `mechanical_metrics.sh` (wraps `renumber-equations.py --check`, `validate-refs.py`, `check-citation-sources.py`) | P1-2, P1-1 | near-free |
| **Quality (rubric)** | Coverage / Structure / Relevance / Synthesis / Critical-Analysis (1-5) + Citation R/P/F1 | `score_rubric.py` -> separate judge model | P0-2 | a few judge calls |
| **Compliance** | does each discipline gate survive pressure (RED-GREEN-REFACTOR) | `scenarios/*.md` run on a subagent | citation gate, P0-2, P0-3 | a few subagent calls |

## Files

```
bench/deep-research-survey/
├── README.md                 # this file
├── topics.json               # frozen benchmark topics + gold-reference surveys
├── scenarios/                # superpowers-style pressure tests (RED-GREEN-REFACTOR)
│   ├── S1-citation-gate-under-time-pressure.md
│   ├── S2-synthesis-on-main-thread.md
│   ├── S3-agent-sizing-discipline.md
│   ├── S4-research-brief-plan-gate.md       # tests proposal P0-3
│   └── S5-self-eval-score-gate.md           # tests proposal P0-2
├── assert_transcript.py      # process metrics: parse .jsonl, assert behaviour     [runnable now]
├── analyze_tokens.py         # cost/latency: per-agent token + cost from .jsonl     [runnable now]
├── mechanical_metrics.sh     # quality (mechanical): wraps repo validators          [runnable now]
├── score_rubric.py           # quality (rubric): assemble the LLM-judge prompt       [runnable now; judging needs a model]
├── ab_compare.py             # aggregate N runs/arm -> delta table with CIs          [runnable now]
└── run-integration-test.sh   # headless run + score, one topic/arm                   [needs `claude` CLI; expensive]
```

## How to run

**Process metrics on any existing session transcript (free, now):**

```bash
SID=<session-id>
T="$HOME/.claude/projects/$(echo "$PWD" | sed 's|/|-|g')/$SID.jsonl"
python3 bench/deep-research-survey/assert_transcript.py "$T"
python3 bench/deep-research-survey/analyze_tokens.py "$T"
```

**Mechanical quality on a produced survey (free, now):**

```bash
bash bench/deep-research-survey/mechanical_metrics.sh surveys/rag-systems-survey.md
```

**Rubric prompt for the judge (free to assemble; judging needs a separate model):**

```bash
python3 bench/deep-research-survey/score_rubric.py surveys/rag-systems-survey.md --out /tmp/judge.txt
# then feed /tmp/judge.txt + the schema to a DIFFERENT model via the Agent tool or a Workflow agent({schema})
```

**Full headless A/B (needs the `claude` CLI; expensive):**

```bash
# baseline arm, 3 repeats
for r in 1 2 3; do
  bash bench/deep-research-survey/run-integration-test.sh --arm baseline \
    --topic-id "rag-r$r" --prompt "$(python3 -c 'import json;print(json.load(open("bench/deep-research-survey/topics.json"))["topics"][0]["prompt"])')"
done
# repeat with the improved SKILL.md checked out, --arm improved
python3 bench/deep-research-survey/ab_compare.py results/*.result.json
```

## A/B protocol

1. Freeze `topics.json` (gold references are the repo's own surveys — the ReportBench "reverse-engineer the prompt from a gold survey" method).
2. Run each topic through the **baseline** `SKILL.md` and the **improved** `SKILL.md`, same generator model, N>=3 repeats each.
3. Collect process + mechanical + rubric metrics per run; aggregate with `ab_compare.py`.
4. Prefer **ablation**: to attribute a delta to one change, test that change against *its* target metric (P1-2 -> consistency only; P0-1 -> silent-death + cost only). Cheaper and cleaner than scoring whole surveys end-to-end.

## RED-GREEN-REFACTOR (the scenarios)

Each `scenarios/*.md` is a pressure test, run exactly as superpowers prescribes:

- **RED** — dispatch the scenario to a subagent that does NOT have the skill/gate; watch it fail; capture rationalizations verbatim.
- **GREEN** — give the subagent the skill (or the proposed gate); confirm it now complies.
- **REFACTOR** — for any new rationalization, add an explicit counter to the gate's rules + the scenario's rationalization table; re-test until no new rationalization appears.

S1-S3 guard *existing* discipline; S4 and S5 are the RED/GREEN acceptance tests for landing proposal P0-3 and P0-2 (a gate nobody follows under pressure is worthless).

## Already demonstrable from this session (no new survey runs)

- **P0-1 orchestration:** this session's two Workflow runs collected evidence across **23 agents with 0 silent deaths**; the documented baseline (`proposals/agent-research-strategy.md`) had **2 of 4 = 50%**. Run `analyze_tokens.py` on this session's transcript to see the main-thread cost; the workflow subagent transcripts live under the run's transcript dir.
- **P1-3 adversarial verification:** the verify stage caught ~7 fabrications a single pass would have shipped — a countable "errors caught the baseline misses."
- **P1-2 consistency tooling:** `mechanical_metrics.sh` runs today on any survey; the duplicate-equation-ID count is the exact metric the change targets.

## Caveats (do not skip)

- **Nondeterminism** — repeats + CIs always; `ab_compare.py` flags only disjoint-CI deltas, and with small N prefer a real test and more runs.
- **Judge bias** — the rubric judge MUST be a different model than the generator; anchor with the gold reference; spot-check with a human.
- **Ground-truth subjectivity** — reference-based scoring penalizes valid novelty; do not reward citation density for its own sake.
- **Cost** — a full A/B is a real token budget; lead with the free mechanical + process tiers, which already settle P0-1 / P1-1 / P1-2.
- **Recursion** — the Tier-2 rubric judge *is* proposal P0-2, so building this harness and shipping that improvement are the same work.
- **RED-baseline isolation** — pressure-test RED arms must be CONTEXT-ISOLATED (a fresh temp project via `run-integration-test.sh`, no repo CLAUDE.md and no skill loaded). In-session subagents inherit repo norms and contaminate the baseline — observed 2026-05-30, where RED agents already cited the skill's own rules and chose correctly. See `scenarios/RESULTS-2026-05-30.md`.

## Provenance

- Process method + transcript schema: `obra/superpowers` v5.1.0 — `docs/testing.md`, `skills/writing-skills/testing-skills-with-subagents.md`, `tests/claude-code/analyze-token-usage.py`.
- Quality rubric: the survey-generation eval cluster in `proposals/deep-research-survey-comparison-data.json`.
- Metric-to-proposal mapping: `proposals/deep-research-survey-improvement-2026-05-30.md`.
