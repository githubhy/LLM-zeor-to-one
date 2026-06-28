---
name: method-eval
description: Rigorously evaluate a candidate LLM/AI method (an attention or positional-encoding variant, a decoding/sampling method, a quantization scheme, a KV-cache or speculative-decoding trick, a retriever or reranker, a PEFT variant) through an independent N-agent pipeline (derive from first principles -> independent math review + implementation -> independent implementation review + test), score it against fixed oracles on a fixed viability rubric, and archive the result as a uniform dossier in a method-search register. Use when deciding whether a proposed method is viable (accurate enough, fast enough, simple enough — clears a hard target) before adopting or rejecting it — a fast accept/reject gate UPSTREAM of a full reference-implementation-study. The register narrative lives under surveys/<survey>/method-search/, prototype code under sim/<survey>/method-search/prototypes/.
---

# method-eval — rigorous candidate-method evaluation

## When to use

A candidate method has been proposed ("could we make attention cheaper with linear/kernel X?", "is
speculative decoding scheme Y a viable latency win?", "does int4 quantization Z hold accuracy?",
"does retriever W beat BM25 on the RAG split?") and you need a TRUSTWORTHY accept/reject, not a
plausible guess. The discipline below is what makes the verdict reliable — it is exactly the kind of
review that catches math/code bugs (a softmax computed over the wrong axis, an off-by-one in the
causal mask, a pass@k estimator that double-counts, a CI computed over prompts instead of samples)
behind otherwise-convincing conclusions.

This is a **fast viability gate**, complementary to the heavier skills: run `method-eval` to
accept/reject a candidate *before* committing to a full `reference-implementation-study` (which then
drives the accepted method through comparative eval, sensitivity, quantization, and a recommendation),
and use `sim-audit` to adversarially audit either one's experiment once drafted.

Do NOT use for: a method already known/standard with no open viability question; a one-line
sanity check; tasks with no measurable oracle.

## The register (where results land)

A method is tied to a SURVEY, and every evaluation is for that survey — the layout reflects it.
The register **narrative** (`README.md` with methodology + per-method analysis, and `REGISTER.md`
the append-only scorecard) lives UNDER THE SURVEY at `surveys/<survey>/method-search/`; the
**runnable prototype code** lives under the implementation study at
`sim/<survey>/method-search/prototypes/NN-<slug>/` (so it imports `common.*` natively). For a given
survey (e.g. an attention-architectures survey → `surveys/attention/method-search/` +
`sim/attention/method-search/prototypes/`), create the pair the same way and swap the oracles (see
"Adapting" below); everything else is identical.

## The dossier (what one evaluation produces)

| Artifact | Home | Purpose |
|---|---|---|
| `wikis/<slug>-derivation.md` | tracked | first-principles derivation + code review |
| `decisions/<date>-NN-<verdict>-<slug>.md` | tracked | the accept / reject / redundant / adopt decision |
| `bugs/<date>-NN-...` | tracked | any math or code defect found (file even if verdict unaffected) |
| `sim/<survey>/method-search/prototypes/NN-<slug>/*.py` | sim (tracked) | the runnable experiment scripts (copied out of gitignored `temp/`) |
| one `REGISTER.md` row + one `README` Section 4.x | survey register | the comparative record |

## Procedure

### 1. Frame (before any agent)

State explicitly: the **question** (what would "viable" mean?), the **baseline** to beat, the
**oracles** (fixed measuring sticks with known values), and the **viability rubric**. For an LLM
register these live in `surveys/<survey>/method-search/README.md` Sections 1–2: oracles = a fixed
eval harness (e.g. `lm-eval-harness` / `EvalPlus`) on a frozen benchmark split (e.g. MMLU / GSM8K /
HumanEval) with published model-card / paper numbers to anchor against, an analytic anchor (a
closed-form attention identity, the softmax Jacobian, a scaling-law power-law prediction, the FLOPs/
KV-memory cost model), and an exact reference kernel on a synthetic fixture; rubric = {correct vs
oracles (matches the harness metric — accuracy / pass@k / perplexity — on the anchor split, and the
analytic prediction within tolerance)? clears the hard target (e.g. HumanEval pass@1 `>= 0.40`, or
`<= 1%` accuracy drop vs fp16)? within the latency / throughput budget (tokens/s, real-time factor,
KV-memory)? sub-quadratic (or the claimed complexity) in sequence length? survives the long-context /
low-resource / adversarial-prompt tail? holds up under quantization (int8 / int4) without a metric
cliff?}.

### 2. Run the N-agent pipeline (Workflow)

Three INDEPENDENT stages — independence is the whole point (a second agent must re-derive from
scratch, not rubber-stamp). Launch with the Workflow tool; one pipeline item per candidate (run
multiple candidates as parallel items). Skeleton:

```js
export const meta = { name: '<slug>-eval', description: '...', phases: [{title:'Derive'},{title:'Review+Implement'},{title:'Test+Verdict'}] }
const SHARED = `READ: the register README methodology + oracles; the prior decisions/wikis. RULES: wikis follow .claude/rules/math-authoring.md (the lint hook BLOCKS bad .md); derive from first principles per .claude/rules/citation-integrity.md (cite nothing from memory); prototypes under sim/<survey>/temp/ (gitignored); do NOT git commit — the orchestrator commits. An honest NEGATIVE result is valid and valuable.`
const out = await pipeline([TOPIC],
  (t) => agent(`FIRST-PRINCIPLES DERIVER for ${t.title}. ${t.derive} Write wikis/${t.slug}-derivation.md (math-authoring rules, \\tag{N}). Predict viability. ${SHARED}`, {phase:'Derive', agentType:'survey-enricher'}),
  (prev,t) => agent(`MATH REVIEWER + IMPLEMENTER for ${t.title}. Prior derivation summary: """${prev}""". (1) Independently re-derive and CORRECT the wiki in place. (2) Implement a prototype at sim/<survey>/temp/${t.slug}_eval.py with a self-validation harness (seeded numpy/torch; score with the reference eval harness). ${t.implement} ${SHARED}`, {phase:'Review+Implement', agentType:'general-purpose'}),
  (prev,t) => agent(`IMPLEMENTATION REVIEWER + TESTER for ${t.title}. Implementer report: """${prev}""". (1) Review code against the corrected math; hunt bugs the self-validation misses (softmax/axis errors, causal-mask off-by-one, pass@k estimator bias, long-context degradation, low-resource tail, CI over the wrong axis). RUN it. (2) Test on the rubric: ${t.test}. Return a FINAL VERDICT (adopt/reject/redundant) with NUMBERS (harness accuracy / pass@k / perplexity + Wilson/bootstrap CIs, tokens/s latency). ${SHARED}`, {phase:'Test+Verdict', agentType:'general-purpose'}),
)
return out
```

Avoid the literal strings `Date.now`, `new Date`, or `Math` + `.random` anywhere in the script —
the Workflow validator rejects them (use seeded numpy/torch inside the python prototypes instead).
Per `CLAUDE.md` Agent Fan-Out model selection, keep the derive / review / verdict stages on Opus
(they gate correctness); a purely mechanical extraction stage could drop to Sonnet.

### 3. On completion (orchestrator does this — agents do NOT commit)

1. **Validate** each wiki: `python viewer/tools/lint-math.py <wiki>` (0 errors) and
   `python viewer/tools/renumber-equations.py <wiki> --check`.
2. **File the decision** `decisions/<date>-NN-<verdict>-<slug>.md` (Context / Decision / Evidence
   with NUMBERS / Alternatives / Consequences / Refs) and its `INDEX.md` row.
3. **Keep the agents' filed bugs**; verify they have `INDEX.md` rows.
4. **Archive prototypes**: `cp sim/<survey>/temp/<scripts>` into
   `sim/<survey>/method-search/prototypes/NN-<slug>/` (temp/ is gitignored — without this the
   evidence is lost). Code stays in the sim tree so it keeps running; the survey register only
   links it.
5. **Append the `REGISTER.md` row** (above the NEXT-CANDIDATE marker, under the survey register)
   and **add a README Section 4.x** analysis (pros / cons / why, measured) and update the
   Section 3 scorecard.
6. **Reconcile logs**: if subagents wrote a stray `prompts/YYYY-MM-DD-<slug>.md`, consolidate into
   the session log per the per-session logging rule; revert the stray file.
7. **Commit + push** the dossier.

## Adapting to a new question

The machinery is question-agnostic. To evaluate candidates for a DIFFERENT survey's kernel/method
(e.g. a long-context-attention survey, a quantization survey, a RAG-retriever survey): create the
survey's register `surveys/<survey>/method-search/` (narrative) and its
`sim/<survey>/method-search/prototypes/` (code), write the `README.md` Sections 1–2 with the new
**oracles** (the relevant eval harness + benchmark split, the analytic / cost-model anchor, the
published baseline) and **rubric** (the accuracy / pass@k / perplexity target + latency + complexity
+ quantization tolerance for that question), and run the same pipeline pointed at them. Only the
oracles and the viability questions change; the survey-vs-sim layout, the
derive/review+implement/review+test discipline, and the dossier are fixed.

## A command, if you want a one-word trigger

This is a SKILL (a multi-step, judgment-laden procedure) rather than a command. A thin
`.claude/commands/method-eval.md` that just invokes this skill with the candidate as `$ARGUMENTS`
is a reasonable add if a slash trigger is preferred — but the substance lives here.

## Cross-references

- `.claude/skills/reference-implementation-study/SKILL.md` — the heavier downstream pipeline that
  takes an *accepted* candidate through comparative eval, sensitivity, quantization, and a final
  recommendation. `method-eval` is the fast viability gate upstream of it.
- `.claude/skills/sim-audit/SKILL.md` — the adversarial multi-lens audit to run on the experiment
  once drafted (the verdict's numbers and CIs are exactly what it re-checks).
- `.claude/rules/math-authoring.md`, `.claude/rules/citation-integrity.md` — the wiki + citation rules.
- `superpowers:test-driven-development`, `superpowers:systematic-debugging` — the testing/debug discipline the reviewer stages apply.
