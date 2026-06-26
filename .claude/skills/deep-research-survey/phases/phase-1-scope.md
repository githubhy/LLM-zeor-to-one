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

## Audience register (exposition axis)

The scope's *audience* drives the **exposition register** (`config/audience-register.json`), orthogonal to both depth tier and `scale`. Resolve it with this precedence and record the result in the scope statement / brief:

1. an explicit `audience: <value>` invocation argument (`learner` / `practitioner` / `expert`);
2. else explicit register language in the request — "for someone learning the field" / "from the very basics" → `learner`; "expert-terse" / "for specialists" → `expert`;
3. else default to `practitioner` (the current Staff-level register) — and ask only if the audience would materially change the depth of the fundamentals and the request is silent.

Downstream: R-GOV (Phase 2) reads the register for the fundamentals floor (`learner` pins the basics at `headline`; `expert` demotes them to recap); R-DEPTH (Phase 4) reads it for derivation granularity, intuition density, worked-example role, and term definitions. The register changes exposition only — it never alters a boxed result, a worked-oracle number, or an epistemic tag, and never drops a load-bearing derivation step (config `register_invariants`). Default `practitioner` reproduces current behavior exactly.

## Proposed-mode addendum

Loaded on demand (token discipline). If `proposed` or `flags: P0-3` is active, read `addenda/phase-1.md` (P0-3 — research-brief / plan-preview gate) and apply it. In `original` mode, skip — do not read it.
