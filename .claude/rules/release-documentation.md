# Release Documentation Rule

Loaded on demand by `CLAUDE.md`. Read this file before **releasing** a validated
numerical implementation as a self-contained package (under `implementation/`, `kernels/`, or a sibling delivery directory) — i.e. before writing or signing
off the release's **report and README**.

A release is not a code drop. It ships a **deliverable set** — two documents, each to a
standard, plus a cross-document sign-off — and this rule names that set so "how do I
release?" has one answer instead of three scattered ones.

## The rule

A release ships:

1. **An implementation / port report** — per `.claude/rules/sim-report-completeness.md`
   (the 14-section spine, the load-bearing [M] artifacts, gated by
   `viewer/tools/check-report-completeness.py`). When the release is the Phase-6 deliverable
   of a `reference-implementation-study`, that phase already produces it; when the release is
   a **cross-language port**, the port's sign-off report follows the same spine
   (`cross-language-port.md` cross-references it). Either way the report is a release
   deliverable, not an optional extra.

2. **A README that is the SOLE user-facing documentation of the shipped package.** A port's
   deliverable code is comment-free (`cross-language-port.md` §5), so the README must carry
   everything a user needs; even when the code is commented, the README — not the comments —
   is the documentation of record. The **release-README standard** — release-general, lifted
   from the three-port `cross-language-port.md` §5 where it was earned, and the single
   normative home for the list below:

   | Section | What it must carry |
   |---|---|
   | Install / environment | the exact runtime + version, and any missing-builtin fallback the package supplies |
   | Quick-start per mode | one runnable invocation for each supported entry point / mode |
   | Data model | every struct / record / return shape the API produces or consumes |
   | API reference | every public entry point, complete |
   | Scope + limitations | what it does **not** do, and the conventions a user must respect (index base, RNG non-portability, tie behaviour, …) |
   | Verification summary **with numbers** | what was gated, against which reference, to what tolerance — the *number*, never a bare "validated" |

   Worked examples: a kernel-port README whose Verification section states the ported kernels match the
   reference to machine epsilon, with the measured max-abs-difference quoted. "Numerically verified" without the number fails the
   last row, exactly as `sim-report-completeness.md` forbids "validated" without a CI.

3. **The release-doc sign-off** — the two documents must agree with each other and with the
   code and data. Two existing passes check this and no mechanical gate does:

   - **`results-reconciliation`** — audit the report ↔ README ↔ the **result-of-record
     artifacts** (the data files, not prose or memory), and reconcile framing-staleness
     ("X remains open" sentences that went stale as the numbers were finalized).
   - **`citation-audit` (CA-INTERNAL mode)** — the report's §4 equation↔function table and
     the source's `# survey-ref` comments must name the **right** equation, not merely a
     resolving one. (When the shipped deliverable is comment-free — the port case, per §5 —
     the audit runs on the pre-strip source the port was proven against.) Run the
     deterministic Tier-1 pre-filter first (`viewer/tools/check-internal-eq-refs.py`, plus
     `check-eqn-function-map.py` if the report carries an eqnmap), then the semantic
     arity/pushforward pass the mechanical gate is structurally blind to.

## Relationship to `cross-language-port.md`

The two rules are complementary, not overlapping. **Nearly every release to date is a
cross-language port** — every upstream release to date was one — so in practice both
rules apply together:

| `cross-language-port.md` owns | this rule owns |
|---|---|
| **how the code is proven** — scope-by-closure, verbatim transpile, golden gating, the cross-language hazard checklist, the string-aware comment strip re-verified byte-identical | **what documentation ships** — the report, the README standard, the sign-off passes |

For a **port**, read both: the port rule for how the code is proven, this rule for what
documentation accompanies it. For an **original** numerical release — nothing to port
against, e.g. a first-party `implementation/` package promoted to a standalone delivery —
the port rule's §1–§4 do not apply, but this rule's report + README standard and sign-off
still do. That original case has **not yet occurred**: every current release is a port, so
the README standard is *generalized but, today, exercised only by ports*. It is written
release-general so the first original release inherits it rather than re-deriving it — the
same reason the port rule's own README bullet was worth lifting out of the porting frame.

## What this rule is not

- **Not a skill.** A release-doc checklist is template-fill plus two existing sign-off passes
  and two existing gates — not a multi-phase orchestration. (Same reasoning
  `cross-language-port.md` is a rule: what recurs is a checklist, not a workflow.)
- **Not a report spec** — `sim-report-completeness.md` owns the 14-section spine; this rule
  points at it, it does not restate it.
- **Not a consistency workflow** — `results-reconciliation` owns the doc-vs-data audit; this
  rule names it as the release sign-off step, it does not re-specify it.

This rule's own content is exactly the **naming**: the deliverable set as one unit, and the
two sign-off passes as a release step — which `cross-language-port.md` §5 delegates here
rather than specifying as its own sign-off procedure.

## Cross-references

- `.claude/rules/sim-report-completeness.md` — the report standard (deliverable 1).
- `.claude/rules/cross-language-port.md` §5 — the README standard's origin, and the
  port-specific ship-clean discipline (comment-free, string-aware strip, byte-identical
  re-gate) this rule deliberately does not duplicate.
- `.claude/skills/results-reconciliation/SKILL.md` — the report ↔ README ↔ data sign-off.
- `.claude/skills/citation-audit/SKILL.md` — CA-INTERNAL: the code↔math-map correctness pass;
  `viewer/tools/check-internal-eq-refs.py` is its Tier-1 pre-filter.
- Worked example: a kernel-port README plus its sign-off report.
