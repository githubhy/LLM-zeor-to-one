---
slug: port-pitch-perfector-agents
date_filed: 2026-06-28
status: open
---

# Port (or decide against) the three pitch-perfector subagents

## Context

During the 2026-06-28 full-parity catch-up import from sibling `../pitch-perfector`, the
agreed scope (commands / skills / rules / hooks / scripts) **did not include `.claude/agents/`**.
pitch-perfector has three agent definitions this repo lacks (this repo's `.claude/agents/` is
empty / absent):

- **`survey-enricher.md`** — referenced by the ported `/enrich` command's Delegation section
  and by the `method-eval` skill's pipeline (both were **genericized** here to "a subagent via
  the Agent tool" / default workflow subagent to avoid a dangling reference).
- **`evidence-collector.md`** — a survey evidence-gathering agent (MIR-instantiated).
- **`viewer-dev.md`** — a viewer-development agent (viewer-instantiated).

The genericized references read correctly, but the richer named-agent capability is absent,
and `/enrich` + `method-eval` would benefit from a real `survey-enricher`.

## What is left

- Decide whether to port `survey-enricher` (highest value — two consumers reference it) and
  optionally `evidence-collector` / `viewer-dev`, re-adapting MIR→LLM (and viewer specifics).
- If `survey-enricher` is ported, restore the by-name `agentType: 'survey-enricher'` reference
  in `method-eval` and the named-agent delegation in `/enrich`.

## Acceptance

Either: `survey-enricher` (at least) ported + adapted + referenced by name in `/enrich` and
`method-eval`, leakage-clean; OR a decision recorded to keep agents generic (close as wontfix).

## Refs

- Source: `../pitch-perfector/.claude/agents/{survey-enricher,evidence-collector,viewer-dev}.md`.
- `decisions/2026-06-28-01-catch-up-import-from-pitch-perfector.md` (agents out of agreed scope).
- Genericized consumers: `.claude/commands/enrich.md` (Delegation), `.claude/skills/method-eval/SKILL.md`.
