---
name: citation-audit
description: Verify every external citation in a document against its actual source, then trace whether wrong citations affect the derivations — and, in internal-reference mode, verify every internal `# survey-ref` / eqnmap / `§X.Y` / `Eq. (N)` pointer names the equation the code or claim actually computes, not merely one that resolves. Use after a survey, appendix, report, or proposal with external citations is drafted or substantially expanded — especially subagent-authored or memory-sourced content — and before any delivery or sign-off gate.
---

# Citation Audit

## Overview

Verify that every external citation in a document actually says what the
document claims it says, then trace whether any wrong citation has
contaminated the derivations. Two stages:

- **Citation audit** — is each citation faithful to its real source?
- **Citation-impact audit** — does a wrong citation change any result?

This skill exists because citations attributed from parametric memory are
unreliable. Author, year, title, section number, and — especially —
numeric values (table constants, equation coefficients, signs) drift when
recalled instead of read. This skill is the after-the-fact verification;
the always-on prevention discipline is `.claude/rules/citation-integrity.md`
— read that too.

## When to use

- After a survey, appendix, report, or proposal with external citations is
  drafted or substantially expanded.
- Whenever cited content was produced by a subagent, or written before
  `citation-integrity.md` was in force.
- Before any delivery, sign-off, or plan-acceptance gate on a cited document.
- Standalone, when the user asks to verify the citations / audit the
  references of a named file.
- **Internal-reference mode** `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]` — after
  an implementation report's equation↔function map, a sim's `# survey-ref` code comments, or any prose that
  cites the local survey corpus by `§X.Y` / `Eq. (N)` is written or substantially edited (especially by a
  subagent). The mechanical gates (`chk_eq_code_correspondence.py`, `chk_survey_traceability.py`,
  `check-eqn-function-map.py`) prove an anchor *resolves*; none proves it names the *right* equation — the
  wrong-but-resolving failure mode this mode audits. When off, internal refs are out of scope.

## Workflow

### Phase 1 — Build the citation ledger (with materiality)

Enumerate every external citation in the target document. One ledger row
per cited work: citation key, claimed author/year/title/venue, the
document location(s) that cite it, the specific claim each in-text
citation attributes to it — a value, a method, a theorem, a section
pointer — **and a materiality tag**:

- `numeric-load-bearing` — a coefficient, sign, threshold, or value that a
  derivation/result/comparison consumes. The class memory-drift corrupts
  invisibly; this is the reason the gate exists.
- `claim-load-bearing` — a non-numeric method/result the document's
  correctness depends on.
- `decorative` — labels, motivates, or attributes background; no value or
  derivation depends on it.

Be conservative: tag `load-bearing` on any doubt. The materiality tag
drives the effort tiering in Phases 2–3 (it does *not* let any citation go
unexamined — see Phase 3).

**Internal references.** `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]` Enumerate
internal refs alongside external citations, each ledger row tagged `class: internal` and carrying a
**code-locus** (`path:line` of the `# survey-ref` / eqnmap / prose site) in addition to the survey
`file#anchor` it names — because an internal ref's Phase-5 impact usually terminates in a **code kernel**,
not in downstream prose. The materiality tags apply unchanged (an equation a kernel consumes is
`claim-load-bearing`; a coefficient it consumes is `numeric-load-bearing`).

Write the ledger to `reports/citation-audit-<doc>-<date>.md` and keep it
current through every phase. A halted audit must leave the ledger as the
recoverable artifact.

### Phase 2 — Acquire the actual source

For each cited work, obtain the real full text:

- Already in the repo (`download/`, or a formal-spec path like `docs/specs/`)? Use it.
- Otherwise invoke the `source-fetch` skill (papers/books) — do not
  reinvent acquisition. Place the file in `download/`.
- If unobtainable, tag the row `unverifiable` and carry it to Phase 4;
  never silently pass it.
- **Internal refs** `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]` skip acquisition —
  the "source" is the survey file already in the repo. Read the cited section directly; this phase is a
  no-op for `class: internal` rows.

### Phase 3 — Verify, in layers (effort tiered by materiality)

Verify in increasing strictness; stop at the first failure and record it.
**Read the cited locus, not the whole source** — and tier the depth by the
Phase-1 materiality tag. Every citation is examined; what differs is how
much is read and whether a source-opening verifier runs.

**Tiering:**

- **`decorative`** — runs the cheap tier only: the mechanical
  `check-citation-sources.py` presence+tag check **plus a page-1 identity
  probe** (PDF: read only page 1; spec: grep the title line) confirming the
  file is the cited work, **plus a one-line bibliographic spot-check**. No
  full source-opening verifier. (This cheap identity probe is what catches a
  *mislabeled* decorative source — a real failure mode; never skip it.)
- **`claim-load-bearing`** — a locus-targeted verifier: identity probe
  (page 1), then read only the cited span to confirm the claim.
- **`numeric-load-bearing`** — a locus-targeted verifier that **must reach
  the value layer**: identity probe, then read only the locus holding the
  number and reproduce it. Locus-targeting narrows the read; it never skips
  the value check, even if the source is a large PDF.

**Locus-targeted reading.** Use the ledger's location pointer. For a spec
`.txt`: `grep -n` the clause number or the cited value, then read a tight
window (`±N` lines) — ~50 lines, not ~50,000. For a PDF: `Read` a narrow
`pages` range computed from the cited page/section (or `pdftotext | grep`
to locate the page first), never the whole document. Widen only if the
targeted read fails to contain the claim — escalation, not default.

**Ledger-first shortcut (document authored from evidence ledgers).** `[opt:CA-LEDGER · default ON · toggle .claude/skill-options.json]` When the
survey/report was written from structured evidence ledgers that already record,
per claim, `{source, location, quote, verified-value}` (the `deep-research-survey`
Phase-3 output), the CHEAP first pass is **document-value vs. ledger-value** — no
source re-open. A number that matches its ledger entry (itself source-verified at
collection time) is confirmed; only a document↔ledger MISMATCH, or a claim the
ledger flagged `GAP`/unverified that the document nonetheless states as fact,
escalates to a source-opening verifier. This is the materiality triage applied one
level up: the ledger is a trusted intermediary, so source-reads are spent only
where the document diverged from what was actually collected. (2026-07-04
channel-estimation audit: 18/18 load-bearing numbers cleared against ledgers with
zero PDF re-opens; the one adversarial trap — a value the ledger flagged unverified
— was caught precisely because the ledger flagged it.)

**The four layers** (applied per tier above):

1. **Bibliographic** — author, year, title, venue match the real source.
   `[opt:CA-BYLINE · default ON · toggle .claude/skill-options.json]`
   **Check the byline against the *filename*, not only the in-text citation:** a
   `download/` slug can misname the author (2026-07-04: `bihan-*.pdf` is authored
   Li et al.; `maltsev-*.pdf` is authored Yu et al.). Cite by the byline on the
   paper's own title page, never the filename; a filename≠byline mismatch is a
   finding to record (and file a `bugs/` entry for the mislabeled `download/` file).
2. **Locational** — the cited section / chapter / page / equation number
   exists and is on-topic.
3. **Claim** — the specific statement the document attributes to this
   source is actually made there. Read the cited pages; do not infer from
   the title or abstract.
4. **Value** — for every cited number (a table constant, an equation
   coefficient, a sign, a threshold) reproduce it from the source. This
   layer catches what memory cannot: a flipped sign, a wrong magnitude,
   the right value lifted from the wrong table.

**Internal-reference verification (the arity / pushforward discriminator).** `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]`
For a `class: internal` ref, layers 1–2 (Bibliographic / Locational) collapse to *"the anchor resolves"* —
which the mechanical gates already prove, and which is **necessary but never sufficient**. The audit lives in
layers 3–4, and the accept/reject rule is:

- **ACCEPT** — the cited equation is a **single-argument deterministic map on a discrete support** (a grid),
  and the code evaluates *that same closed form* pointwise at each grid element. The code **is** the scalar
  formula genuinely evaluated at its grid points; no arithmetic mismatch is possible by construction.
- **REJECT (mismatch)** — the code's actual computation takes **multiple independent random variables** as
  arguments: an **order statistic** (min / max / order-$k$ of $N$ draws), a **survival-function product**
  across $N$ trials, or a **convolution** of $N$ densities. It implements a density-level **pushforward** — a
  distribution transform over a joint/product space — that shares *no arithmetic* with the cited
  single-variable equation (different operator, different arity, a different mathematical object), even when
  the cited equation is topically about the same quantity. The citation is wrong *regardless of whether its
  anchor resolves*.

Two submodes recur: **wrong-but-resolving** (the anchor/locus is real — it would pass every `--check` — but
the equation *at* that locus is not what the code computes; e.g. a min-sum CN update citing the continuum
order statistic $f_M(t)=\sum_j f_j(t)\prod_{k\ne j}(1-F_k(t))$ while the code computes the tie-exact discrete
survival difference $\prod_k P(\ge t)-\prod_k P(>t)$), and **right-section-wrong-appendix** (the cited section
is topically correct but is the *special-case-only* locus — e.g. a uniform-only appendix — while the code's
actual regime is defined in a different section of the same survey).

**Tier-1 deterministic pre-filter (run it first).** `python viewer/tools/check-internal-eq-refs.py <paths>`
flags any `# survey-ref: file#sec-S ... Eq. N` whose cited equation `N` does not live in section `S` of the
survey — the high-volume copy-paste class (one wrong number replicated across a decoder family). It is
**detect-only / advisory with a rejection ledger** (legitimate cross-section equation reuse is a real
false-positive source) and is **necessary-not-sufficient**: it is structurally blind to the
*present-but-wrong* residue (the cited number *is* in the section, but the code computes a different object),
which only the arity/pushforward discriminator above catches. Clear the mechanical class with the pre-filter;
spend the semantic pass on the residue.

**Orchestration (when fanning out across agents).** Group verifiers by
*source file*, not by citation — open a multi-cited source once and verify
all its loci in one context load. Cap concurrent verify agents at 4–6: high
fan-out with large reads provokes a tool-channel fault whose symptom is
empty tool output. An agent that gets empty output must return
`tool-unavailable` (a retry signal, re-queued serially) and **never**
`unverifiable` (which is a source finding) — conflating the two hides real
problems behind environmental false negatives.

### Phase 4 — Classify

Tag every ledger row exactly one of:

- `correct` — faithful at every layer.
- `wrong-source` — the claim is real but credited to the wrong work.
- `wrong-value` — right work, wrong number or wrong section.
- `fabricated` — the cited content does not exist in the source at all.
- `unverifiable` — source unobtainable; downgrade the in-text use to an
  abstract-level claim or escalate to the user.

`[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]` The two internal-ref submodes reuse
these tags — no sixth tag: **wrong-but-resolving** → `wrong-value` (right locus, wrong equation);
**right-section-wrong-appendix** → `wrong-source` (the operator's real definition is in a different section).

### Phase 5 — Citation-impact audit

For every row that is not `correct`, trace the citation downstream and
decide load-bearing vs decorative:

- **Decorative** — the citation labels or motivates, but no derivation,
  value, or result depends on it. Fix the citation; the mathematics is
  untouched.
- **Load-bearing** — a derivation step, a numeric result, a method
  choice, **or an implementation kernel** consumes the cited value or
  claim. `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]` For an internal ref the
  dependent content is usually **code**: trace whether the function whose `# survey-ref` names the wrong
  equation actually computes the right thing — the ref can be wrong while the code is correct (a
  documentation defect), or the wrong ref can mark a real code defect. The wrong citation may have
  propagated a wrong result. Re-derive or re-verify the dependent content.

This phase is judgment-heavy. Deciding whether a derivation depends on a
citation needs domain understanding, not a mechanical scan — run it with a
capable model and the document's full technical context. Do not mark a
citation decorative without naming what would break if it were
load-bearing and confirming that thing is independently sound.

### Phase 6 — Fix and record

- Correct the citations in the document.
- File a `bugs/` entry for any `wrong-value` or `fabricated` citation that
  was load-bearing (severity per the `CLAUDE.md` bug guide); file a
  `decisions/` entry if a fix involved a real choice.
- Finalize the audit report: the ledger, the per-tag counts, the impact
  findings, and the source files added to `download/`.
- If the audit ran as part of a plan, mark the audit task done in the plan
  with a pointer to the report.

## Rules

- **Read, do not recall.** A citation is verified only when its source has
  been opened and the cited pages read. "I am confident this is in
  [author]" is not verification.
- **A resolving anchor is necessary, never sufficient (internal refs).** `[opt:CA-INTERNAL · default ON · toggle .claude/skill-options.json]`
  Every mechanical gate on an internal `# survey-ref` / eqnmap / `§X.Y` ref checks only that the anchor
  *resolves* to a real section/equation; a ref that resolves to the *wrong* equation passes all of them. The
  only check that catches it is opening the cited locus and confirming the equation there is what the code or
  claim actually computes — the arity/pushforward discriminator in Phase 3.
- **Values are the priority.** A bibliographic mismatch is visible; a
  wrong coefficient inside a correct-looking citation is not. Always reach
  Phase 3 layer 4 for any cited number.
- **Tier effort, never coverage.** Materiality tiering (Phase 1/3) decides
  how much is read per citation, not whether a citation is examined. Every
  citation gets at least the cheap identity+mechanical tier; every
  load-bearing value gets a locus-targeted value read. The savings come
  from reading the *locus* not the whole source, and from not running a
  full verifier on decorative attributions — not from skipping checks.
  (Validated directionally: A/B run `wf_26ff1cdb-821` cut audit tokens
  3.65x at equal detection — both planted mislabeled-source violations
  caught, the decorative one by the page-1 identity probe. See
  `proposals/2026-05-31-citation-audit-token-efficiency.md`.)
- **No silent passes.** Every ledger row ends in one of the five Phase-4
  tags. `unverifiable` is a valid outcome; an unexamined citation is not.
- **Reuse, don't rebuild.** Acquisition is the `source-fetch` skill's
  job. Bug and decision capture follow `CLAUDE.md`.
- **Spec/standardization claims are a sibling job.** This skill verifies a
  citation against *its named source*. A claim about *why a specification or a
  model was built a certain way*, or a value attributed to a formal spec or a
  model card, needs the `spec-provenance` skill instead — it climbs the
  provenance ladder (published version / preprint / the versioned artifact that
  actually carries the value) and runs the **draft-vs-published gate** that
  catches a preprint's number being stated as the published one (a failure mode
  this skill, keyed on the named source, does not catch). Run both on a
  survey/report hardened from a primary record: citation-audit for the papers,
  spec-provenance for the spec / version-drift claims.
- **The ledger is the deliverable of record.** Keep it current so a
  halted audit is resumable.

## Standalone usage

```
/citation-audit surveys/transformer-attention/appendix-a.md
```

Run Phases 1–6 on the named file; report the per-tag counts and the impact
findings.
