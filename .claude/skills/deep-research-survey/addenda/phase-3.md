# Proposed-mode addendum — Phase 3 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set
(`P0-1`, `P1-1`, `P2-1`). **Exception: `[DRS-HARDEN]` below is DEFAULT-ON** (config
`evidence_agent_policy`), independent of `proposed`/`flags` — read and apply it whenever you
launch evidence agents, unless `agent_hardening: off`.

**[DRS-HARDEN] Evidence-agent hardening (default-ON safety net; toggle `agent_hardening: off`).**
This is a gotcha-#9 broken-original **rewrite**, not an additive enhancement: three measured
runs lost ~90% of clusters. The transcript-measured root cause was the per-agent
**iteration/STEP cap** (~36-40 tool calls) — NOT context size (a dead agent used ~58K of a 200K
window) and NOT model tier (Sonnet survivors produced gold output). Agents burned the step
budget on research (incl. 18 wasted Glob calls + full-page WebFetch) and were cut off mid-loop
(final message `stop_reason=tool_use`, empty text) before writing. Five rules (full text:
`config/operational-scale.json` `evidence_agent_policy.rules`):

1. **File-first deliverable** — the incrementally-written `survey/_scratch/<agent>.md` IS the
   graded deliverable (write after EACH question). A structured-output schema is OPTIONAL; if
   used in a Workflow `parallel()`/`pipeline()`, the `agent()` call MUST be `try/catch`-wrapped
   (a missing `StructuredOutput` call THROWS, it does not return `null`, so a null-only retry is
   jumped over — the original observed failure).
2. **No Glob / exact paths** — give agents exact file paths; forbid filesystem exploration.
3. **WebFetch ≤ 2** — prefer WebSearch snippets + targeted local-source `grep`/`Read` (the
   acquired papers in `download/` and any specs under `docs/specs/`).
4. **Empty-return-as-death** — the orchestrator treats an empty-string return as death
   (`if (!r || String(r).trim() === '')`), not success.
5. **Step-budget headroom** — ~3-4 questions/agent (~10+ tool calls/question of headroom under
   the cap); `questions_per_agent` is the upper bound. Splitting the same total questions across
   more agents raises per-question depth + breadth — it does not narrow or shallow coverage
   (synthesis still sees every file; R-COVER gates completeness).

`agent_hardening: off` restores the legacy schema-first / 5-question / unrestricted-Glob-WebFetch
path (the broken one; for A/B + backward-compat only). Refs: the evidence-agent-hardening bug +
decision + proposal. **Supersedes the structured-return deliverable framing in P0-1 / P1-1
below** (the file is the deliverable; the AttributeTree record is written as markdown structure
inside it).

**P0-1 — deterministic Workflow orchestration.** Collect evidence with a `Workflow`
`pipeline()` (one `evidence-collector` agent per section/subtopic, a structured-output
schema for each ledger row) instead of manual background `Agent` launches. The
runtime supplies completion handling and durable journaling, so the manual
scratch-file checkpoint and 15-minute dead-agent poll become a non-Workflow fallback
only. Keep the per-agent scope rule (5 or fewer questions per agent).
On the Workflow path, `agent()` returns `null` when a collector dies; apply the
`retry_policy` (`config/operational-scale.json`): collect the `null` clusters and
**re-fire them, bounded and escalating** — attempt 1 the same brief, attempt 2 trimmed
(drop to `standard` budget / split the cluster), each relaunch resuming from its
`_scratch/` ledger — then `.filter(Boolean)` and fall back to the main thread (with a
coverage-gap marker) only for clusters still dead after the 2-retry ceiling. Record the
`{deaths, retries, recovered-at-attempt}` telemetry for the Phase-5 footer.

**P1-1 — structured (AttributeTree) evidence.** Distill each source into a structured
record — `{claim, method, result, condition, source_url, quote, quality_tier,
confidence}` — at collection time (a natural fit for the Workflow output schema),
instead of free-text ledger cells. Synthesis then cites structured fields, not prose
recollection.

**[P2-1] Optional citation-graph evidence model.** For high-stakes surveys, organize
evidence as a citation/semantic graph stratified into Foundation / Development /
Frontier layers (or a taxonomy) instead of the flat ledger, so multi-aspect coverage
and cross-section synthesis are structural rather than manual. Keep optional.
