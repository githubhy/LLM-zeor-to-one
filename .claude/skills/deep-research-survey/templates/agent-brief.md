# Agent Brief Template

Use this template when constructing a research agent brief. Fill in each
field before launching the agent. Delete this instruction block when using.

> **Hardened by default (`agent_hardening: on`, `config/operational-scale.json`
> `evidence_agent_policy`).** The five rules below are the default-on safety net that
> fixed the 2026-06-25 step/iteration-cap failure (three runs lost ~90% of clusters).
> Set `agent_hardening: off` only to restore the legacy schema-first / 5-question path.

---

## Agent: {{agent-name}}

**Mode:** {{foreground | background}}
**Deliverable file (this IS the graded output):** `survey/_scratch/{{agent-name}}.md`

### Hardening rules (include the substance verbatim in the agent prompt)

1. **Your deliverable is the FILE, not your chat reply.** Build
   `survey/_scratch/{{agent-name}}.md` incrementally with your write tool, appending each
   question's answer the moment you finish it. Do NOT hold results to dump at the end. Your
   chat reply is a 2-line confirmation (file path + `N/M questions written`).
2. **No Glob / no exploration — use the EXACT paths below.** Hunting for files with Glob was
   the single largest waste of the per-agent step budget. Exact paths:
   - Exemplar to mirror: `{{path to a gold-standard _scratch file, if any}}`
   - Local primary source(s): `{{exact paper/model-card/eval path(s) in download/ or docs/specs/, or "none"}}`
3. **WebFetch ≤ 2.** Prefer WebSearch result snippets and `grep`/`Read` of the local-source
   line ranges. A full-page WebFetch is both a step and a context-bulk sink.
4. **Write after EVERY question** (rule 1) so a step-cap cutoff leaves partial work on disk.
5. **Stay under the step budget.** ~3–4 questions/agent leaves ~10+ tool calls of headroom per
   question under the ~36–40-call cap; more questions risks being cut off mid-research.

> **Orchestrator note (not for the agent prompt):** treat an **empty-string return as death**
> (`if (!r || String(r).trim() === '')`), not success — a step-capped agent completes with an
> empty final message. If a structured-output schema is used in a Workflow `parallel()` /
> `pipeline()`, wrap the `agent()` call in `try/catch` (a missing `StructuredOutput` call
> THROWS, it does not return `null`).

### Questions ({{N}}, target ≤3–4)

1. {{Question 1}}
   - **Expected output (file section):** {{e.g., "## Q1 with a findings paragraph + an evidence bullet list: claim — value/eq — source+locator — tier — confidence"}}
   - **Stop condition:** {{e.g., "if not found in 3 searches, write a Gap line and move on"}}

2. {{Question 2}}
   - **Expected output:** {{description}}
   - **Stop condition:** {{description}}

3. {{Question 3}}
   - **Expected output:** {{description}}
   - **Stop condition:** {{description}}

4. {{Question 4 (optional — only if it keeps ~10 tool calls/question of headroom)}}
   - **Expected output:** {{description}}
   - **Stop condition:** {{description}}

### Pre-flight Estimate

| Metric | Value |
|--------|-------|
| Questions | {{N}} (target ≤3–4; hard cap = `questions_per_agent`) |
| Est. searches/question | {{N}} (~2–3) |
| Est. total tool calls | {{N}} (keep < ~30 to stay under the step cap) |
| WebFetch budget | {{N}} (≤2) |
| Classification | {{must-have / nice-to-have}} |

### Checkpoint + Resume Instruction

Include this verbatim in the agent prompt — it is **load-bearing**: the file-first deliverable
and the retry policy's bounded loss + idempotent resume (`config/operational-scale.json`
`retry_policy`, `evidence_agent_policy`) depend on it. The 2026-06-25 runs lost whole clusters
because agents hit the per-agent **step/iteration cap** during research and were cut off before
writing — *not* context exhaustion (a dead agent used only ~58K of a 200K window).

> **Checkpoint.** After answering EACH question, *immediately* append your findings to
> `survey/_scratch/{{agent-name}}.md` — do NOT batch them to the end. If you are cut off
> (step-cap or a transient fault), only the in-progress question is lost, not the whole run.
>
> **Resume.** Before you start, READ `survey/_scratch/{{agent-name}}.md` if it exists. If
> earlier answers are already there, you are a relaunch after a death — continue from the
> first UNanswered question and do not redo the answered ones.
