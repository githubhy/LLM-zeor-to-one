---
name: spec-provenance
description: Trace a claim about why a model, method, benchmark, or protocol is built the way it is — a value, a rationale, a default, a "why is it like this" — to the primary record (the published version, the model/system card, the benchmark's defining paper, the harness release), and gate every preprint / draft / blog-post number against the CURRENT published artifact before it is stated as fact. Use when a survey/report/proposal asserts why a design chose X (including why a whole family of related options exists — "why so many PEFT variants", "why N quantization formats"), or attributes a value/default to a paper, model card, or spec, and that claim reaches a sign-off gate. Composes with source-fetch and citation-audit.
---

# Spec Provenance

## Overview

Verify that a *design-rationale claim* is faithful to the primary record, and
that every number in it reflects the **current published** artifact — not a
superseded preprint, a blog post, or an early model-card revision. Distinct from
`citation-audit`:

- **`citation-audit`** asks: does the *named source* say what we claim it says?
  (verify a citation against its own document).
- **`spec-provenance`** asks: is this claim about *why/what the design does*
  traceable to the primary record, and is its value the one the **current
  published version** actually carries? (trace a claim up the ladder, then gate
  it against the current artifact).

This skill exists because of one recurring, expensive failure mode: **a draft's
number read as if it were the published one**. In LLM work the draft layer is
unusually thick and unusually citable:

- **arXiv v1 vs vN.** Numbers move between submission and camera-ready — an
  ablation is rerun, a baseline is fixed, a table is corrected. A citation to
  "arXiv:XXXX.XXXXX" without a version pin silently means "whatever is there
  today", which is not what was read.
- **Model cards are edited in place.** A reported benchmark score, a context
  length, a license, or a training-token count can change without a version
  bump and without a changelog.
- **Blog-post numbers precede the paper** and frequently differ from it.
- **Harness defaults drift.** The same benchmark, the same model, a different
  eval-harness release: a changed prompt template or answer-extraction rule
  moves the score by points, with no change to either the model or the benchmark.

The always-on prevention discipline is `.claude/rules/citation-integrity.md`
(never cite from memory; every value reproduced from an acquired source). This
skill is the *trace-and-gate* workflow that front-stops the draft-as-published
failure that rule does not, by itself, name.

## When to use

- A survey/report/proposal asserts **why** a design chose something ("RoPE is
  used because it makes relative position a rotation", "GQA exists to shrink the
  KV cache"), or attributes a **value/default** to a paper, model card, or spec
  ("the context length is 128K", "the model saw 15T tokens").
- A survey/report asserts why a *family* of related options exists — "why so many
  PEFT variants", "why N quantization formats", "why several RoPE-scaling
  schemes". This is a **taxonomy-level why** (the Phase-0 `taxonomy` type): not
  one claim but a decomposition into per-member rationale traces plus one
  synthesized root cause. Match this **shape** for any phrasing ("why so many X",
  "why N formats", "why not just one"), not the literal string.
  `[opt:SP-FAMILYWHY · default ON · toggle .claude/skill-options.json]`
- The claim is about to reach a sign-off / delivery / plan-acceptance gate.
- A rationale was hardened from a preprint, a blog post, a release thread, or a
  model card — anywhere a *draft* number could have leaked in.
- Standalone: the user asks to trace / source / "find the actual reason for" a
  claim, or to verify a claim is "still true for the current release".

## The provenance ladder

Climb from the claim to the primary record. Authority splits two ways: the
**current published artifact is the authority on what is true now**; the
**drafts, threads, and design docs are the authority on why**. Acquire and read
in this order:

| Rung | Source | Holds | Acquire via |
|---|---|---|---|
| 0 | **Current published artifact** — the peer-reviewed/camera-ready paper, the current model card, the tagged spec release (e.g. an MCP spec version), the pinned harness release | the *adopted* value/behavior — ground truth | `source-fetch`; `docs/specs/` for formal specs |
| 1 | **The artifact's own appendix / system card / eval section** | the rationale of record, and the configuration behind every headline number | `source-fetch` |
| 2 | **Earlier versions and their diffs** — arXiv v1…vN, model-card revision history, the PR/commit that introduced a default | the *why* — arguments, alternatives, what changed and when | `source-fetch --version`; the repo's history |
| 3 | **Release notes / changelog / reviewer-facing record** (OpenReview threads, accepted-version diff, a spec's changelog) | what was *accepted*, vs merely proposed | web + `source-fetch` |
| 4 | **The originating research agenda** — the prior work the design answers, the position paper that framed the problem | *why this was a goal at all* | `source-fetch` |
| 5 | **The benchmark's defining paper + its official harness config** | the requirement the design is measured against, and the protocol that operationalizes it | `source-fetch`; `/add-dataset` |
| 6 | **External formal standards** where relevant (IETF RFC, W3C, a published spec) | the mandate outside any one lab | `docs/specs/` |

The cheapest route to the primary rationale is the artifact's **own reference
list and appendix** (rung 1) — a paper cites the work it answers, and its
appendix carries the configuration the headline table used. When you must
discover what changed, the arXiv version listing and a model card's commit
history are the diff surface.

**Rungs 0–3 answer "why this design"; rungs 4–6 answer "why this was a goal at
all."** `[opt:SP-CHARTER · default ON · toggle .claude/skill-options.json]` A
"why" trace does not have to stop at the paper (rung 1): the paper exists because
a **research agenda** framed the problem (rung 4); that agenda targets a
**benchmark or capability requirement** (rung 5); which may rest on an external
standard (rung 6). The chain is **self-citing** — each rung names the one above
it in its own reference list, so the cheapest way to climb is to read the current
doc's citations. Climbing higher trades **specificity for generality** — rung 6
is "an interoperable tool-call format", rung 2 is the exact design rule — so stop
at the rung that actually carries the claim and cite the rest as context.

## Phase 0 — classify the claim

Name what kind of claim it is before tracing; the type sets the rungs you need.

| Type | Shape | Rungs |
|---|---|---|
| `value` | "the context length is 128K", "trained on 15T tokens" | 0 (+1 for the configuration) |
| `rationale` | "GQA exists to shrink the KV cache" | 1–2, then 0 to confirm it is still true |
| `default` | "temperature defaults to 1.0", "the harness uses 5-shot" | 0 + 5 (the harness config is the artifact) |
| `taxonomy` | "why so many PEFT variants" `[opt:SP-FAMILYWHY]` | per-member 1–2, then one synthesized root cause |
| `charter` | "why long context became a priority" `[opt:SP-CHARTER]` | 4–6 |

## Phase 1 — acquire, and pin the version

Acquire via `source-fetch`. **Pin the version at acquisition time**, because that
is the only moment the pin is free:

- arXiv → record the **version** (`arXiv:2205.14135v2`), not the bare ID.
- Model card → record the **revision/commit hash** and the date read.
- Harness → record the **release tag or commit**.
- Spec → record the **dated version** (`MCP 2025-06-18`).

An unpinned reference is a citation to a moving target. Record the pin in the
reference entry itself, so a later reader can tell whether the number they see is
the number that was read.

**A load-bearing claim needs a strong source tag.**
`[opt:SP-LOADBEARING-LOCAL · default ON · toggle .claude/skill-options.json]` If
the trace ends at a `(web)` page for a claim a derivation or headline depends on,
that is not finished: acquire the document into `download/` and re-tag `(local:)`.
Weak-form tags are for claims that genuinely have no fetchable document (see
`.claude/rules/citation-integrity.md`).

**An HTTP error is not proof that a source is unavailable.**
`[opt:SP-FILE403 · default ON · toggle .claude/skill-options.json]` A 403/418 on
one fetch is frequently a **bot filter or a rate limit, not a paywall**. Confirm
by fetching a sibling document from the same host, or by retrying with a browser
User-Agent, before recording a source as inaccessible and downgrading to a weak
tag. Recording "member-only"/"paywalled" when the document is in fact public is
the failure this check exists for.

**A value that lives only in a figure is not extractable text.**
`[opt:SP-IMAGECITE · default ON · toggle .claude/skill-options.json]` When the
number you need appears only inside a plot, a rendered table image, or a
screenshot in the PDF, do **not** burn budget on extraction and do **not**
transcribe it by eye into the survey's voice. Either cite the axis-readable
value explicitly as *read from a figure* with its uncertainty, or find the same
number in the artifact's text/appendix. A digitized figure value is an estimate;
label it as one.

## Phase 2 — the draft-vs-published gate

**Every number sourced from a rung ≥ 2 artifact is gated against rung 0 before it
is stated as fact.** `[opt:SP-DRIFT · default ON · toggle .claude/skill-options.json]`

1. Find the same quantity in the **current published** artifact.
2. If it agrees → tag `PUBLISHED`, cite rung 0 for the value and the draft only
   for the *why*.
3. If it differs → the draft value is **`DRAFT`**: cite it only as a labeled,
   dated, superseded alternative, never in the artifact's voice. State both.
4. If the current artifact does not carry the quantity at all → the claim is
   **`UNADOPTED`**: it was proposed and did not land. Say so explicitly rather
   than letting a proposal read as a description.

**The same authors' preprint and published version can disagree.**
`[opt:SP-SAMECOMPANY-DRIFT · default ON · toggle .claude/skill-options.json]`
Common authorship is *not* evidence that two documents carry the same number —
the whole point of revision is that something changed. Never reconcile a
discrepancy by assuming the same group would not contradict itself; gate each
document against rung 0 on its own.

**Proposal vs adoption is the distinction the gate turns on.** A method proposed
in a paper, an option discussed in a spec thread, and a default actually shipped
in a release are three different facts. A survey that writes a proposal in the
present indicative ("the format uses X") when only a draft proposed X has made a
claim the record does not support.

## Phase 3 — synthesize

- For a `rationale`, state the reason **and** the rung it came from, and confirm
  at rung 0 that the design still works that way.
- For a `taxonomy` `[opt:SP-FAMILYWHY]`, trace each member to its own rationale,
  then name the **one** pressure that produced the family (usually a
  cost/quality/compatibility trade that different groups resolved differently).
  A list of members is not an answer to "why so many".
- For a `charter` `[opt:SP-CHARTER]`, name the rung you stopped at and why that
  rung carries the claim.

## Phase 4 — record and fix

- Write the corrected claim, with its rung-0 value and version pin.
- Update `references.md` entries to the pinned form and the right source tag.
- **For a study that touches many values across several artifacts, maintain a
  standing provenance ledger** `[opt:SP-LEDGER · default ON · toggle
  .claude/skill-options.json]` — one row per traced value: `claim | rung | source
  (pinned) | published value | draft value (if any) | status ∈ {PUBLISHED, DRAFT,
  UNADOPTED} | where used`. The ledger is what catches a cross-version drift that
  a per-claim trace cannot see, and it is the artifact a later audit reads
  instead of re-tracing.
- File a `bugs/` entry for any claim that was stated as fact from a draft value
  (severity per `CLAUDE.md`: `high` if a derivation or headline depends on it).

## Rules

- **Never cite from memory.** `.claude/rules/citation-integrity.md` governs; this
  skill does not relax it.
- **Pin the version, always.** An unpinned arXiv ID or an undated model card is
  not a citation to a fixed object.
- **A proposal is not an adoption**, and a preprint is not a publication. Tag
  accordingly.
- **Stop at the rung that carries the claim.** Climbing further is context, not
  evidence, and it dilutes the citation.
- **An inaccessible source is a finding, not an excuse** — record it, downgrade
  the tag honestly, and do not let the claim keep its confident phrasing.

## Cross-references

- `.claude/rules/citation-integrity.md` — the always-on prevention rule this
  skill front-stops.
- `.claude/skills/citation-audit/SKILL.md` — the sibling: verifies a citation
  against *its named source*; this one traces *why* and gates the version.
- `.claude/skills/source-fetch/SKILL.md` — acquisition.
- `.claude/rules/sim-report-completeness.md` — `[opt:SIM-REQBASIS]` /
  `[opt:SIM-REFPOP]`, the report-side use of a traced reference value.
- `.claude/commands/add-dataset.md` — benchmark/harness registration (rung 5).
