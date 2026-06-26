# Pre-flight Workload Estimation Checklist

Fill in this checklist before launching research agents. The goal is to
prevent silent agent death by keeping each agent within empirically safe
bounds.

## Hard Limits

- [ ] Each agent within the active scale's question limit (`config/operational-scale.json`: standard **≤5**, wide **≤7**)
- [ ] Each agent's estimated searches within the active scale's limit (standard **≤15**, wide **≤40**; wide is provisional, above the empirical ~28-search death boundary)
- [ ] Every agent brief includes a **checkpoint write instruction**
- [ ] Every agent brief includes a **stop condition** per question

## Agent Roster

| # | Agent Name | Mode | Questions | Est. Searches | Phase |
|---|-----------|------|-----------|--------------|-------|
| 1 | | fg/bg | /5 | /15 | A/B/C |
| 2 | | fg/bg | /5 | /15 | A/B/C |
| 3 | | fg/bg | /5 | /15 | A/B/C |
| 4 | | fg/bg | /5 | /15 | A/B/C |

## Calibration Reference

Use these illustrative data points (an LLM-survey-shaped agent roster) to
gut-check your estimates. The empirical boundary is task-agnostic — it is
about search/tool-call volume per agent, not the topic:

| Agent | Questions | Est. Searches | Actual Calls | Tokens | Duration | Outcome |
|-------|-----------|--------------|-------------|--------|----------|---------|
| Attention variants (MQA/GQA/sparse) | 5 | ~14 | 58 | 70K | 14 min | Completed |
| RLHF vs DPO method inventory | 5 | ~15 | 71 | 88K | 16 min | Completed (at limit) |
| Inference-serving SOTA (vLLM/quant/spec-decode) | 7 | ~22 | 79 | 95K | 18 min | Completed (borderline) |
| "Survey all LLM eval benchmarks" (too broad) | 8 | ~30 | — | — | — | **Dead** |
| "All RAG papers since 2020" (unbounded) | 7 | ~28 | — | — | — | **Dead** |

**Empirical boundary:** agents with ≤~21 estimated searches survive; agents
that try to sweep an unbounded arXiv query (≥~28) die silently. The 15-search
soft limit provides margin. The two dead rows share a failure shape — a *broad*
question with no stop condition — not a hard topic; narrow the question instead
of adding budget.

## Launch Sequence

- [ ] **Phase A:** Launch foreground agents for must-have data (2–3 max)
- [ ] Wait for at least 1 Phase A agent to complete
- [ ] Assess results — adjust remaining briefs if topic is harder than expected
- [ ] **Phase B:** Launch background agents for nice-to-have data (1–2 max)
- [ ] Start 15-minute dead-agent timer
- [ ] **Phase C:** If needed, launch remaining agents or absorb into main thread

## Dead-Agent Recovery

After 15 minutes, for each background agent:

- [ ] Check output file — is it 0 bytes?
- [ ] Check scratch file — any partial results?
- If partial results exist → integrate and re-scope remainder for main thread
- If no scratch file → assume dead, do research on main thread
