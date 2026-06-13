# Phase 1: Scope

## Goal
Pin down subject, audience, depth, and output shape before any research begins.

## Constraints
- Fix the output contract before researching: survey, proposal, implementation plan, comparison, or executive brief.
- If the topic is too broad, narrow it by domain, layer, time horizon, geography, or implementation target.
- Only ask for clarification if it would materially change the result.

## Deliverable
A concrete scope statement with: subject, audience, depth, output format, exclusions, and source preferences.

## Tightening a Vague Request

If the user only says "do deep research on X", rewrite internally as:

```text
Produce a rigorous research survey on X. Start from first principles, build an
outline, research each section against explicit questions, track evidence by
section, compare main approaches on performance and implementation tradeoffs,
summarize SOTA vs actual practice, end with references, open gaps, and next steps.
```

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or `flags: P0-3` is active, read `addenda/phase-1.md` (P0-3 — research-brief / plan-preview gate) and apply it. In `original` mode, skip — do not read it.
