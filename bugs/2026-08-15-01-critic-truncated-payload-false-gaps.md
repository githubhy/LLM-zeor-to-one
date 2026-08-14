---
id: 2026-08-15-01
title: A workflow critic handed a sliced payload reports false "zero records" gaps, confidently and with remediation advice
severity: med
status: fixed
date: 2026-08-15
component: Workflow orchestration (deep-research-survey Phase-3 extract→critique pattern)
---

## Symptom

In the mechanistic-interpretability 2026 frontier sweep, four of six Opus completeness
critics reported that specific papers had returned **zero evidence records**, and three
recommended re-running those agents:

> "SEND IT BACK. Two of the four papers … returned ZERO evidence records; their numbers
> appear only as unsourced prose … Re-run at minimum for CoAx and CIF."

> "the payload is truncated (three papers have no records at all)"

> "paper 2 has zero records (payload truncates mid-record-11)"

**Every paper had records.** The run returned 86 records across all 19 papers, and the
specific numbers a critic called "unsourced prose" were present in full — e.g. the
conditional-co-ablation ladder it asked to be re-extracted:

```
single ablation 0.33±0.00 ; AtP 0.60±0.03 ; GIM-style 0.63±0.05 ;
EAP-IG 0.70±0.02 ; AtP* GradDrop 0.82±0.03 ; CoAx 0.91±0.00  (Table 1)
```

Acting on the advice would have re-run roughly a dozen agents to recover data already on
disk.

## Root cause

The critique stage embeds the extraction result inline in the critic's prompt:

```js
${JSON.stringify(res, null, 1).slice(0, 15000)}
```

That slice is the whole defect. Measured payload sizes against the 15,000-char window:

| Cluster | records payload | critic saw |
|---|---|---|
| E1 circuit-critique | 25,466 | 59% |
| E2 SAE re-evaluation | 26,629 | 56% |
| E4 theory | 21,678 | 69% |
| E5 steering/control | 22,319 | 67% |
| E6 frontier framing | 16,002 | 94% |
| E3 weight-space | 15,075 | 100% |

The correlation is exact: **every cluster whose critic alleged missing records is one whose
payload exceeded the window, and the only critic that alleged none (E3) is the only one that
saw ~100%.**

The critic behaved correctly given its input. `JSON.stringify` emits records in array order,
so a slice truncates the *tail* — and the truncation lands mid-record, which reads exactly
like a died-mid-write agent. The critic then did the reasonable thing and reported a
production failure. It could not distinguish "the agent did not extract this" from "the
orchestrator did not show me this", because nothing in the prompt said the payload was
abridged.

**This is a false-green inversion**: the usual failure is a gate reporting success it did not
verify; here a gate reported *failure that did not occur*. Both come from the same root —
the checker's view is not the artifact.

## Fix

The content critiques are unaffected and were kept: the critics' corrections to records they
*did* see were correct and valuable (a 77%-vs-9% figure that would have shipped wrong, a
model-scope error, a section-coverage negative asserted from the wrong files, and one
position reversal). Only the *"re-run this"* verdicts were discarded, after verifying
directly that the data existed.

For the pattern going forward, either:

1. **Write the extraction to a file and pass the critic the path**, so it reads the whole
   artifact with its own tool budget — this is the same file-first discipline DRS-HARDEN
   already mandates for evidence agents, applied one stage later; or
2. if inlining, **state the abridgement in the prompt** — "you are seeing the first N of M
   records; absence from this excerpt is not evidence of absence" — so the critic scopes its
   verdict to what it can see.

Option 1 is preferred and is the same reasoning that made `_scratch/<agent>.md` the graded
deliverable in the first place: a mid-stage artifact that only exists inside a prompt is one
truncation away from being invisible.

## Regression test

none — this is orchestration-script shape, not repo code. The durable control is the
convention above; recorded here because the symptom (an agent "returning nothing") has a
well-known and *different* usual cause — the ~36–40 tool-call step cap — and this instance
would have been misattributed to it. `CLAUDE.md` § Agent Fan-Out already warns that the step
cap is the seductive default hypothesis; this is a second, distinct cause with the same
surface presentation, and it is on the orchestrator's side rather than the agent's.

## Refs

- Run: `wf_62ffb6fb-f63` (mechanistic-interpretability 2026 frontier sweep), 12 agents,
  0 errors, 86 records.
- `CLAUDE.md` § Agent Fan-Out — Sizing and Failure Diagnosis — "diagnose by reading the dead
  agent's transcript … never by pattern-matching to a plausible cause". Applied here to the
  orchestrator rather than the agent.
- `.claude/skills/deep-research-survey/config/operational-scale.json`
  `evidence_agent_policy.rules.deliverable_file_first` — the same principle, one stage
  earlier.
- `field-notes/2026-08-15-mi-survey-expansion.md`.
