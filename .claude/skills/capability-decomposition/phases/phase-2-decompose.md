# Phase 2 — Decompose + verify

## Goal
For each module, fill the step-level leaf tree from the actual source, then adversarially confirm every absent/partial claim against `path:line`.

## The workflow

Invoke `assets/cap_decompose.workflow.js` once per module via the Workflow tool:

```
Workflow({ scriptPath: ".../assets/cap_decompose.workflow.js",
           args: { module: "client",
                   root: "/abs/path/to/src/acme/client",
                   units: [ {key:"session", prompt:"Files: session/... Classes: ... Procedures to break to steps: ..."},
                            ... ] } })
```

It runs a `pipeline()`: each unit → **decompose** agent (schema-validated leaf tree, `schema/leaf.schema.json`) → **verify** agent (adversarial). Returns `{ units: [{unit, data, verification}] }`.

### Decompose stage
Each agent reads the real source and fills, per public class, every PROCEDURE → its ordered STEPS, each leaf `{step, status, detail, evidence: path:line, why}`, plus `classLevelAbsent` and `moduleLevelAbsent`. The workflow's shared prompt already carries the grain stop-rule and the "be RUTHLESS about what is NOT in the box" instruction — your per-unit `prompt` just supplies the files, class list, and procedure hints.

- **Every partial/absent leaf MUST carry a `why`** — the IS-vs-ISN'T rationale (what *is* implemented and what is *not*). `schema/leaf.schema.json` now requires `why` for `status ∈ {partial, absent}`, and `render_module.py` prints a `WARNING` for any legacy leaf that lacks it. (a gate against legacy leaves authored before the `why` requirement.)
- **Describe each operation in the repo's ACTUAL framework/API.** Never import terminology from a different library or a framework the code doesn't use — e.g. writing `tf.*` / TensorFlow prose for a codebase that doesn't use it (a common porting artifact). State what the cited code really does, in its real API.

### Verify stage (the gate) — PRECISION
A second, independent agent re-opens the cited `path:line` for the ~6 highest-stakes leaves — **every absent/partial status and every surprising present variant** — and confirms or refutes against the real code, defaulting to refuted/uncertain when the line doesn't support the claim. It returns `{checked, corrections, verdict}`. This checks **precision**: are the marks the tree *makes* earned (tree → source)?

### Recall pass (the gate) — COMPLETENESS
The verify stage cannot catch a capability the decomposition **never enumerated** — it only re-checks claims that exist. Run a complementary **recall pass** (source → tree) before sign-off: enumerate the module's public surface and confirm each item is represented.

- **Method.** AST-enumerate every public class (and substantive public method) in the module's source roots; match each against the decomposed `classes[].name` + cited `file` paths. The unmatched set is the candidate-miss list; audit each — a substantive, user-facing capability with **no** tree node is a recall miss (add it as a present/partial/absent leaf). Trivial getters, abstract bases, enums, dataclasses, and framework overrides are legitimately excludable.
- **Tooling.** `assets/recall_check.py <module-dir> --units <module>_units.json` prints the public-class/method coverage and the unmatched candidates. A recall pass typically finds near-complete class coverage but the occasional missed method — e.g. an inverse operation (a `reset_*()` where the matching `set_*()` was covered) — exactly the omission class this pass exists to catch.
- **Honesty.** Recall is **search-bounded** (a capability under different terminology or in an unsearched sibling could be invisible to both the tree and this pass). Report the coverage fraction as agreement-at-this-search-depth, not a closed-world proof.

## On completion (per module)
- Confirm every unit's `verification.verdict` is **TRUSTWORTHY** (phrasing varies — "HIGH TRUSTWORTHINESS" counts; match loosely, don't string-equal `"TRUSTWORTHY"`).
- Scan `verification.corrections`. Minor line-drift (±a few lines) needs no action — note it in methodology. A **refuted** check or a status flip is material: fix the leaf in the data (or re-run that unit) before rendering.
- Save the `result.units` array to `<module>_units.json` for the renderer.

## Cost & resilience
- ~`2 × N_units` agents per module. Run **one module workflow at a time** (8–18 agents) to stay well under concurrency/rate limits; the completion notification drives the loop.
- If a workflow dies on a session/rate limit, re-launch it (cached agents return instantly via `resumeFromRunId`); commit completed modules so nothing is lost.

## Deliverable
Per module: a verified `<module>_units.json` (the `result.units` array).
