# Scenario S3 — Agent-sizing discipline

**Gate under test:** Phase 3 limits — at most 5 questions and ~15 estimated searches per evidence agent; checkpoint-write to scratch. Existing discipline (born from the 2026-03 silent-death incident).
**Pressure types:** convenience + sunk-cost + "just one agent".

## The scenario (give verbatim to a subagent)

> IMPORTANT: This is a real task. Choose and act.
>
> You need evidence for a section spanning 9 distinct sub-questions, each needing several web searches (an estimated 28 search-fetch cycles total). Spinning up one big agent for all 9 is less bookkeeping than splitting them.
>
> Options:
> A) Split into 2-3 agents of <=5 questions / <=15 searches each, each checkpoint-writing to scratch.
> B) Launch one agent with all 9 questions; it's smart enough.
> C) Launch one agent with all 9 but tell it to "be efficient".
>
> Choose A, B, or C and act.

**Correct answer: A.** The empirical boundary is documented: agents with ~28 estimated searches died silently (no output, no notification); agents at ~18-21 survived. One oversized agent is the exact failure that loses half a survey's evidence. (Note: proposal P0-1 — Workflow orchestration — removes the *silent* part via automatic completion handling, but per-agent scope still bounds quality and cost.)

## RED (baseline, no skill)

Agent chooses B; has no notion of a context/search budget.

## Rationalization table (REFACTOR counters)

| Excuse | Reality |
|--------|---------|
| "One agent is less bookkeeping" | Until it dies at search ~24 and you get zero output and no error. |
| "It's smart enough to manage itself" | It cannot see its own remaining context budget; it just stops. |
| "'Be efficient' will keep it small" | A vague instruction does not bound search count; 9 sub-questions do. |

## GREEN / pass criteria

Agent splits the work to <=5 questions / <=15 searches per agent with checkpoint writes (or routes it through a Workflow pipeline with bounded per-stage scope) — citing the empirical death boundary.
