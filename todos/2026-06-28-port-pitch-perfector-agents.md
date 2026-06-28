---
slug: port-pitch-perfector-agents
date_filed: 2026-06-28
status: closed
---

**Resolution (2026-06-28).** All three agents ported into `.claude/agents/`, re-adapted MIR→LLM:
- **`survey-enricher.md`** (opus) — "Staff Audio DSP & MIR" → "Staff LLM/AI Research Engineer";
  body constraints kept (domain-agnostic) + added explicit math-authoring / citation-integrity rule
  reads and the `references.md` ↔ `download/` source-tag invariant. By-name refs restored:
  `/enrich.md` Delegation now names `survey-enricher`; `method-eval` Derive stage now uses
  `agentType:'survey-enricher'` (review/test stages `agentType:'general-purpose'`, mirroring upstream).
- **`evidence-collector.md`** — model `haiku`→`sonnet` (deviation from upstream; per `CLAUDE.md`
  Agent Fan-Out "evidence-gathering against a fixed schema → Sonnet" + citation-integrity emphasis);
  venues ISMIR/TASLP/JASA/DAFx → NeurIPS/ICML/ICLR/ACL/EMNLP/TMLR/JMLR + model cards. Already
  referenced by `deep-research-survey` Phase 3 and the `skill-improvement` landscape workflow (now resolve).
- **`viewer-dev.md`** (sonnet) — de-MIR'd and de-"forthcoming"'d: this repo's viewer is complete, so the
  file now points at the real `viewer/` files + the `node:test`/Playwright suites; dropped the
  "eventual product pitch-tracking app" framing (no product app here); examples YIN/SWIPE/CREPE →
  attention/softmax/RoPE/scaling-law.

Added a `### Agents` catalog to `CLAUDE.md` (upstream has none, but this repo catalogs everything).
Leakage-clean. See `decisions/2026-06-28-04-port-and-readapt-pitch-perfector-agents.md`.

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
