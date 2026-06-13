---
name: citation-audit
description: Verify every external citation in a document against its actual source, then trace whether wrong citations affect the derivations. Use after a survey, appendix, report, or proposal with external citations is drafted or substantially expanded — especially subagent-authored or memory-sourced content — and before any delivery or sign-off gate.
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

**The four layers** (applied per tier above):

1. **Bibliographic** — author, year, title, venue match the real source.
2. **Locational** — the cited section / chapter / page / equation number
   exists and is on-topic.
3. **Claim** — the specific statement the document attributes to this
   source is actually made there. Read the cited pages; do not infer from
   the title or abstract.
4. **Value** — for every cited number (a table constant, an equation
   coefficient, a sign, a threshold) reproduce it from the source. This
   layer catches what memory cannot: a flipped sign, a wrong magnitude,
   the right value lifted from the wrong table.

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

### Phase 5 — Citation-impact audit

For every row that is not `correct`, trace the citation downstream and
decide load-bearing vs decorative:

- **Decorative** — the citation labels or motivates, but no derivation,
  value, or result depends on it. Fix the citation; the mathematics is
  untouched.
- **Load-bearing** — a derivation step, a numeric result, or a method
  choice consumes the cited value or claim. The wrong citation may have
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
- **The ledger is the deliverable of record.** Keep it current so a
  halted audit is resumable.

## Standalone usage

```
/citation-audit surveys/transformer-attention/appendix-a.md
```

Run Phases 1–6 on the named file; report the per-tag counts and the impact
findings.
