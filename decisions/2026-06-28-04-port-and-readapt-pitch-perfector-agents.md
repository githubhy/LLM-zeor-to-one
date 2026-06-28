---
id: 2026-06-28-04
title: Port + re-adapt the three pitch-perfector subagents (and wire survey-enricher by name)
status: accepted
date: 2026-06-28
plan: null
---

## Context

The 2026-06-28 full-parity catch-up import from sibling `../pitch-perfector` deliberately scoped out
`.claude/agents/` (`decisions/2026-06-28-01`), genericizing the two consumers that named an agent
(`/enrich` Delegation; `method-eval` Derive stage) to "a subagent via the Agent tool" so nothing
dangled. The user then asked to **finish** that deferral
(`todos/2026-06-28-port-pitch-perfector-agents.md`). pitch-perfector has three agent definitions this
repo lacked: `survey-enricher` (opus), `evidence-collector` (haiku), `viewer-dev` (sonnet) — all
MIR/pitch-instantiated, and `viewer-dev` additionally written for a state where the viewer had **not
yet landed** ("forthcoming once the viewer client lands") and a separate "product pitch-tracking app"
existed. Neither assumption holds here: this repo's viewer is complete and there is no product app.

## Decision

Port all three into `.claude/agents/`, re-adapted MIR→LLM, and restore the by-name wiring:

- **`survey-enricher`** — domain reframed to Staff LLM/AI Research Engineer; body constraints kept
  (domain-agnostic) and strengthened with explicit `math-authoring` + `citation-integrity` rule reads
  and the source-tag invariant. Restored `survey-enricher` by name in `/enrich` Delegation and as
  `agentType:'survey-enricher'` on the `method-eval` Derive stage (review/test → `general-purpose`,
  mirroring upstream).
- **`evidence-collector`** — model **`haiku`→`sonnet`** (the one deliberate deviation from upstream),
  and MIR venues → LLM venues + model cards. Already named by `deep-research-survey` Phase 3 and the
  `skill-improvement` landscape workflow template — those references now resolve.
- **`viewer-dev`** — de-"forthcoming"'d and de-MIR'd to point at the real `viewer/` files + the
  `node:test`/Playwright suites; dropped the product-app framing; examples → attention/softmax/RoPE.

Added a `### Agents` catalog block to `CLAUDE.md` (upstream has none, but this repo catalogs every
skill/command/rule, so leaving agents undocumented would be inconsistent).

## Alternatives considered

- **Keep agents generic, close as wontfix** — rejected: `survey-enricher` has two real consumers and
  the user asked to finish, not to decide-against; a named domain-expert deriver is materially better
  than a default workflow subagent for enrichment.
- **Keep `evidence-collector` on haiku (upstream parity)** — rejected: `CLAUDE.md` Agent Fan-Out lists
  "evidence-gathering against a fixed schema" under **Sonnet**, and citation-integrity is load-bearing
  in this repo (fabricated/▴drifted citations are the exact guarded failure mode); Sonnet is the
  repo-consistent floor for citation-faithful evidence work. Recorded as an explicit deviation.
- **Copy `viewer-dev` verbatim** — rejected: its "forthcoming viewer" + "product app" premises are
  false here; shipping them would mislead any future dispatch.

## Consequences

- Enables: `/enrich` and `method-eval` dispatch a real domain-expert deriver; `deep-research-survey`
  Phase 3 and `skill-improvement` get a real `evidence-collector`; viewer work has a scoped agent.
- Forecloses: nothing. `cross-linking.md` was intentionally left alone (this repo lists the authoring
  *skills*, not `survey-enricher`, which is an agent — the upstream listing it among skills is a
  pitch-perfector quirk).
- Follow-up: none; todo closed.

## Refs

- Source: `../pitch-perfector/.claude/agents/{survey-enricher,evidence-collector,viewer-dev}.md`.
- `todos/2026-06-28-port-pitch-perfector-agents.md` (closed).
- `decisions/2026-06-28-01` (the catch-up import that scoped agents out).
- Consumers: `.claude/commands/enrich.md`, `.claude/skills/method-eval/SKILL.md`,
  `.claude/skills/deep-research-survey/addenda/phase-3.md`,
  `.claude/skills/skill-improvement/templates/wf-landscape.workflow.js`.
