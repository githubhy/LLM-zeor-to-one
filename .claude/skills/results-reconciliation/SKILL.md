---
name: results-reconciliation
description: After results are folded into docs incrementally across many turns/sessions, adversarially audit every doc against the result-of-record artifacts (the data files, not memory or prose) and reconcile FRAMING-STALENESS — the "still-open / out-of-scope / not-measured / do-not-cite / X remains" sentences that go stale while the data blocks stay correct. Use when a report / survey / manifest has accreted results over many edits and you need to confirm the prose reflects the FINAL state before a sign-off or delivery gate. Complements citation-audit (external citations) and sim-report-completeness (section structure); domain-agnostic. Worked instance: a 20-finding audit (15 load-bearing) of a study report + its survey + its manifest.
---

# results-reconciliation — doc-vs-artifact consistency audit

## When to use

- A report / survey / manifest **accumulated results across many incremental edits** and the prose may
  now lag the data.
- Before a sign-off / delivery gate, or whenever asked "are the docs current with the results?"

Do NOT use for: a doc written in one pass; external-citation provenance (use `citation-audit`); section
presence / completeness (use `sim-report-completeness`).

## The failure mode it catches

After incremental result-folding, the **numbers land in the data blocks but the narrative goes stale**.
The tables/figures get edited when each result lands; what rots is the *connective* prose — "out of
scope", "still open", "not yet measured", "do-not-cite … not a synthesis result", "X remains" — true
when written, never reconciled after the result arrived. A casual read passes it because the *data* is
right; only a doc-vs-artifact cross-check surfaces it. This is a sibling of the citation-integrity /
sim-audit failure mode: plausible-but-stale surviving a casual read.

## Workflow

1. **Identify the result-of-record artifacts** — the JSON/CSV/data files that are *ground truth*, NOT
   prose and NOT memory. List the exact paths.
2. **Dispatch an adversarial auditor** (Opus — consistency/judgment under ambiguity) that reads every doc
   *and* the artifacts and returns a punch-list. Each finding: `[STALE | INCONSISTENT | INCOMPLETE]` —
   `file:section` — what it currently says — the artifact/correct value — severity (load-bearing vs nit) —
   with the offending text quoted. Instruct it: **do NOT edit**; be exhaustive; **flag the framing
   sentences explicitly** (still-open / out-of-scope / not-measured / do-not-cite / remaining); cross-check
   docs against *each other*; ground every verdict in an artifact, not the prose.
3. **Apply the punch-list on the main thread** — you wrote the edits, so the agent grades them; don't
   grade your own work. Fix STALE / INCONSISTENT first, then INCOMPLETE (a doc that should reflect a
   completed result but doesn't, e.g. a plan item that was quietly done).
4. **Re-gate**: run the doc's mechanical gates (lint / validate-refs / completeness) after the edits, and
   re-run the auditor once if the punch-list was large.

## Gotchas

- The auditor's ground truth **must be the artifacts**, not the prose — otherwise it can't catch a doc
  that is internally consistent but *collectively* stale against the data.
- **Watch the manifest / iteration-log**: its early entries routinely carry *superseded* numbers (an
  approximation later refined) that no subsequent edit revisited.
- The staleness lives in the connective "what remains / why it's out of scope" prose, scattered across
  the executive summary, scope boundary, conformance/limitations sections, roadmap, and do-not-cite
  clauses — audit those specifically, not just the results tables.
- An auto-registered skill / plan item marked "deferred" that was *actually completed* in a later turn is
  a common INCOMPLETE finding — reconcile the roadmap/status too.

## Cross-references

`citation-audit` (external-citation provenance), `sim-report-completeness` (section-spine completeness),
`accelerator-cost-study` (a frequent producer of incrementally-folded results).
