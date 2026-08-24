# Source-Authority Precedence Rule

Loaded on demand by `CLAUDE.md`. Read this file before resolving a disagreement between two
**published, current** sources that both bear on the same claim — a model card and the paper it
accompanies, a benchmark's defining paper and the eval harness that implements it, a leaderboard
and the harness it runs, a reference implementation and the spec it implements.

This is **not** the draft-vs-published problem (`.claude/skills/spec-provenance/SKILL.md` owns
that) and not the memory-vs-source problem (`.claude/rules/citation-integrity.md` owns that). Both
of those have an obviously-wrong side. Here **both sides are current, both are authoritative in
their own domain, and they disagree** — so the question is not which one is *right* but which one
is *authoritative for this particular field*.

## The rule

**Declare the layer split before you need it, and follow the downstream source's own declaration of
where its values come from.**

Three parts:

1. **Split authority by layer, explicitly.** Two sources that overlap rarely overlap completely.
   Write down which one owns which question — and write it down *before* a conflict, because the
   moment you need it you will be tempted to pick the answer you prefer. The recurring LLM split:
   the **benchmark's defining paper** owns task identity, split definition, and the metric's
   definition; the **eval harness** owns the prompt template, the answer-extraction rule, and the
   scored denominator; the **model card** owns what configuration the vendor ran.
2. **A source that declares its own upstream is downstream by its own statement.** When a document
   says in its own text where a value comes from and how it is derived, a disagreement about that
   value is a **stale derived copy**, not two competing claims. This is the strongest available
   arbiter and it costs one grep to find — look for the derivation sentence ("we report the
   *k*-shot number from …", "scores computed with harness vX") before arguing from plausibility.
3. **A conflict is recorded, never erased.** Carry *both* values and the derivation in the
   artifact. Rewriting the losing side to match produces a clean-looking record that hides a live
   disagreement, and the next reader cannot tell a reconciled conflict from an agreement.

And the consequence that bites:

4. **Every published number names which layer it is measured against.** Where the sources form a
   *chain* — reference performance → published headline → leaderboard entry, each adding a
   configuration allowance — a number quoted at one level and read at another silently pockets the
   allowance between them. That is `.claude/rules/calibration-residuals.md` check 4 (metric-basis
   reconciliation) applied to a document hierarchy rather than to a measurement, and it is the same
   chain `.claude/rules/sim-report-completeness.md` `[opt:SIM-REQBASIS]` decomposes.

## Why "declare it before you need it"

A precedence applied consistently but never written down is indistinguishable, to the next reader,
from an ad-hoc preference. It also cannot be *checked*: nothing fails when someone silently applies
it the other way.

Upstream measured this on a conformance campaign that had, correctly and for months, used one
standards body's document for case identity and another's for requirement values — and had stated
that split nowhere. It stayed harmless while the two agreed. Then one case turned up labelled
differently by each, and resolving it took a full trace to answer a question the rule would have
answered in a line. An audit of all comparable cases found that to be the *only* mismatch — which
is a reason to write the rule down, not a reason not to: a conflict rare enough to be forgotten is
exactly the one that will be re-derived from scratch.

The LLM shape is the same: a benchmark paper and a harness agree on the score for years, until one
model's answer format makes the extraction rule matter, and nothing on record says which document
arbitrates.

## How to find the arbiter (in order of strength)

1. **The downstream source's own derivation sentence.** A leaderboard that states "all scores
   produced with `lm-eval-harness` v0.4.x, 5-shot" has declared its direction: it computes *from*
   the harness, so a disagreement with the harness is the leaderboard being stale.
2. **Internal consistency of each side.** A value that contradicts its own document's other fields
   is the stale one — a reported accuracy sitting under a table captioned for a different
   few-shot $k$ than its own column header.
3. **The version diff.** If earlier releases are held, diff the row. A number unchanged across a
   revision while its *label* changed is the signature of a **label correction**, not a
   redefinition; a genuine change of configuration would move the number.
4. **A control.** Check the arithmetic on an *undisputed* sibling row before believing it on the
   disputed one.

Note what is *not* on this list: which source is more familiar, which produces the more convenient
answer, and which one a tool happens to parse. Note also what **cannot** arbitrate — a check that
returns the same result under both readings. Ask of every piece of evidence: *would this have come
out differently under the other hypothesis?* If not, it is corroboration, not arbitration. This is
`.claude/rules/calibration-residuals.md` check 6's "know WHY a control agrees" at the document
layer.

## What "record, don't erase" looks like

The losing value, the winning value, the derivation, and what would invert it — in the artifact a
consumer reads, not only in a `decisions/` file:

```json
"config": {
  "few_shot_k": 5,
  "declared_by": "decisions/<id>.md",
  "source_disagreement": "The model card reports 0-shot CoT; the benchmark's defining paper
     fixes 5-shot for this split and the harness implements 5-shot. We port against 5-shot
     because the harness's own README declares it computes the paper's protocol; inverts if
     the vendor publishes a 5-shot number that disagrees with our reproduction."
}
```

Two properties make that more than prose: the override **names a decision record and refuses if it
is missing**, and a test asserts **both** values plus the derivation survive — so erasing the
conflict fails a gate rather than merely looking tidier.

## When the sources are versioned differently

Check whether you hold the same release of both. A precedence argument that compares version *N* of
one against version *N+1* of the other is comparing across two variables. If one side's newer
release is not held, say so and name the acquisition (via `.claude/skills/source-fetch/SKILL.md`) —
the conclusion may be right under the declared pin and still invert when the pin moves.

## Cross-references

- `.claude/skills/spec-provenance/SKILL.md` — the *draft-vs-published* problem, and how to trace a
  claim to the primary record when neither local source arbitrates.
- `.claude/rules/citation-integrity.md` — never write a value from memory; this rule assumes both
  values were read from acquired sources.
- `.claude/rules/calibration-residuals.md` check 4 — metric-basis reconciliation, of which part 4
  above is the document-hierarchy form.
- `.claude/rules/sim-report-completeness.md` `[opt:SIM-REQBASIS]` — `published = reference +
  configuration delta`, the chain part 4 protects.
