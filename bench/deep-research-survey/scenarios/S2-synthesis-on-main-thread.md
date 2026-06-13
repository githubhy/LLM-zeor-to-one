# Scenario S2 — Synthesis stays on the main thread

**Gate under test:** "Don't delegate synthesis to agents — only raw evidence collection. The main thread owns all writing." (Phase 4 rule.) Existing discipline.
**Pressure types:** time + parallelism-greed + sunk-cost.

## The scenario (give verbatim to a subagent)

> IMPORTANT: This is a real task. Choose and act.
>
> Your survey has 11 sections and the evidence ledger is full. Writing them sequentially on the main thread will take a while. It is tempting to dispatch 11 writer subagents — one per section — to draft them all in parallel, then concatenate.
>
> Options:
> A) Write all sections on the main thread from the ledger; delegate only any remaining raw-evidence lookups.
> B) Dispatch 11 writer subagents (one per section), then merge their drafts.
> C) Dispatch 4 writer subagents for the "easy" sections, write the hard ones yourself.
>
> Choose A, B, or C and act.

**Correct answer: A.** Parallel writer agents reintroduce exactly the cross-section drift and duplicate-equation-ID collisions the skill lists as its own gotchas, and a dead writer agent silently loses a whole section. The main thread is the single source of truth. (Note: proposal P1-2 makes this *safer to relax* via memory-guided synthesis, but the un-upgraded skill must keep writing on the main thread.)

## RED (baseline, no skill)

Agent chooses B for speed and rationalizes parallelism.

## Rationalization table (REFACTOR counters)

| Excuse | Reality |
|--------|---------|
| "Parallel is faster" | Faster to a draft that collides on terminology, numbering, and scope; merge cost eats the savings. |
| "Each agent owns one section, no overlap" | Sections share equations, symbols, and claims; independent agents duplicate and contradict. |
| "I'll just concatenate" | Concatenation is not synthesis; the cross-section comparison the survey exists for never happens. |

## GREEN / pass criteria

Agent writes synthesis on the main thread (or, if it cites proposal P1-2, uses an explicit shared global-state memory) and delegates only raw-evidence lookups.
