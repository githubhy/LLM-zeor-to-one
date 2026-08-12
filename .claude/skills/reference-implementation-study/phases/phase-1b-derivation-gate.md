# Phase 1.5: Derivation-Soundness Gate (G0)

`[opt:RIS-DERIV · default ON · toggle .claude/skill-options.json]`

**Standing gate.** Runs at the end of Phase 1, **before any Phase-2 code**. When `RIS-DERIV`
is `on` (default), G0 blocks Phase 2 until every candidate has a well-formed derivation ledger.
When `off`, skip this phase entirely — revert to trusting the survey's derivations via the
Prerequisites line (the pre-2026-07-04 flow).

## Why this gate exists

An RIS result rests on three separable claims:

| Claim | Gated by | Where |
|---|---|---|
| (a) the **derivation** is sound (ground-up, no missing step, correct sign/coefficient) | **G0 (this gate)** | Phase 1.5 |
| (b) the **code** computes the derived equation | eq↔function table | Report §4 |
| (c) the **implementation** matches an independent oracle | P0-5 `oracle_check` | G1 |

(b) and (c) both *anchor on the derived equation* — a dropped term or sign error is faithfully
coded (b passes) and confirmed by an oracle built from the same wrong math (c passes), yielding a
green report on a broken foundation (a wrong coefficient precedent,
`.claude/rules/citation-integrity.md`). G0 is the **upstream, independent** check that (b) and (c)
structurally cannot provide. Catching a derivation defect here also avoids contaminating Phases
2–5, where every downstream number would have to be recomputed.

## Goal

For each Phase-1 candidate, produce a **derivation ledger** proving the math was **independently
re-derived from first principles** — reproduced from axioms by a second pass, *not* re-read from
the survey. The ledger is the deliverable; G0 checks it is complete.

## Tiering — proportional to load-bearing-ness (don't over-gate)

Follow the R-GOV depth-tier principle:

- **`load-bearing`** — the candidate whose output *is* the ranked headline result (e.g. the
  Wiener-MMSE interpolator whose NMSE you report). **Full** treatment: independent re-derivation,
  no-missing-step, ≥1 reduction-to-known-limit check, explicit assumptions.
- **`catalog`** — a reference/baseline operator (e.g. linear interpolation as a floor). **Light**
  treatment: the derivation exists and reduces to the textbook form; you do **not** re-derive
  linear interpolation from Shannon. Only `survey_ref`/`spec_ref` + `no_missing_step` required.

## Deliverable

1. **`docs/<topic>-derivation-ledger.md`** — the human narrative: per candidate, the from-axioms
   derivation (or a pointer to the survey section it reproduces), the limit checks worked out, and
   the assumptions made explicit. This is where the actual re-derivation lives.
2. **A machine-checkable `derivation_ledger` block** in
   `artifacts/<study>/study-manifest.json` (or a standalone
   `artifacts/<study>/derivation-ledger.json` sidecar) — what G0 reads.
3. **The BACK-LINK, from the survey section to the ledger.** `[opt:RIS-BACKLINK · default ON ·
   toggle .claude/skill-options.json]` If the ledger is authored as a `wikis/*.md` derivation
   document, **add a reader-facing link to it from the survey section it attests, in the same
   turn that creates it.** Not in an HTML comment — in the prose, where a reader will meet it.

   This is not bookkeeping; it closes a hole this gate itself opens. `survey_ref` above makes
   the ledger cite the **survey** (provenance, and G0 checks it). *Nothing* makes the survey
   cite the **ledger** — so the linkage is one-way **by construction**, and the obligation has
   no owner in the survey→wiki direction. On 2026-07-08 this study produced three ICI derivation
   wikis (BEM, banded-MMSE, SIC) and **not one was linked from the survey it proves**;
   `ici-aware-banded-mmse-derivation.md`, the ledger for the *headline* §4.9, had **zero**
   mentions in the survey. The proofs existed, in the repo, unreachable — so §4.10 asserted
   DPS-BEM's "provably minimum" optimality while its proof sat two directories away, invisible.

   A derivation nobody can reach did not get written for the reader; it got written for the gate.
   Verify with `python viewer/tools/crosslink.py reach` (pre-push gate; `warn` by default).
   Cross-corpus link syntax — plain relative link, descriptive text, **no** `§` glyph, **no**
   `secxref` — is fixed by `.claude/rules/cross-linking.md`.

### `derivation_ledger` schema (one entry per candidate)

```json
"derivation_ledger": [
  {
    "candidate": "wiener_time",
    "tier": "load-bearing",
    "survey_ref": "data-channel §6.2.2 Eq (44)-(46)",
    "load_bearing_eqs": ["(44)", "(45)", "(46)"],
    "independent_rederivation": "verified",
    "no_missing_step": true,
    "limit_checks": [
      {"limit": "SNR -> inf, 2 pilots", "expect": "reduces to linear interp", "derived": "matches"},
      {"limit": "pilot density -> inf", "expect": "MSE -> 0", "derived": "matches"}
    ],
    "assumptions": ["WSSUS", "known R_HH", "Jakes Doppler spectrum"],
    "external_values": [
      {"value": "R_HH Bessel-J0 form", "source": "spec: docs/specs/38211-…", "reproduced": true}
    ]
  },
  {
    "candidate": "linear_freq",
    "tier": "catalog",
    "survey_ref": "data-channel §6.1.1",
    "no_missing_step": true
  }
]
```

- `survey_ref` / `spec_ref` — the survey/spec equation this operator realizes. **This becomes the
  left column of the Report §4 eq↔function traceability table** — filling the ledger front-loads
  Section-4 work, it is not net-new.
- `load_bearing_eqs` *(optional, load-bearing only)* — the machine-readable list of equation ids
  (matching the report's ```eqnmap``` `<eq_id>` tokens, paren/space-insensitive) that this candidate's
  math rests on. When present, `check-eqn-function-map.py --ledger <study-manifest.json>` asserts
  **every** listed equation has an eqnmap row — completeness, not just per-row integrity — and FAILs
  on an unmapped load-bearing equation. Advisory no-op when a ledger omits it (a study predating the
  index format is never FAILed by adding `--ledger`). Populate it to move a study's §4 completeness
  from `--min N` + reviewer judgment to a hard gate
  (`todos/2026-07-12-eqnmap-ledger-completeness-crosscheck`, decision `2026-07-12-07`).
- `independent_rederivation: "verified"` — a second pass reproduced the result from axioms. Note in
  the `.md` narrative *who/how* (a second agent, a hand-derivation).
- `no_missing_step: true` — every "it can be shown that" jump is filled (`.claude/rules/workflow.md`
  math-derivation rules; the linter enforces the authored form, this field attests the review).
- `limit_checks` — each formula collapses to its known special case; a derivation that fails a
  limit has a bug.
- `assumptions` — every assumption becomes a Phase-2/3 fixed sim-condition **and** a Report §2/§4
  idealization disclosure. A hidden derivation assumption is a hidden sim idealization.
- `external_values` (load-bearing) — a list, one entry per **imported** constant / coefficient /
  comparison value the derivation cites (a Bessel form, a table coefficient, a published margin),
  each `{value, source, reproduced: true}` where `source` is an **acquired** `local:`/`spec:` path
  (per `.claude/rules/citation-integrity.md`) and `reproduced` attests the number was *reproduced
  from that source*, not carried from the survey or memory. If the derivation imports **no** external
  value, write `"external_values": []` **and** an `external_values_note` saying so — explicit "none"
  beats silent absence. **Why this field is separate from `no_missing_step`.** The two documented
  appendix-derivation defects (a fabricated head-to-head comparison, a wrong-sign J-function
  coefficient) were *imported-value* errors, not *missing-step* errors — the derivations were
  step-complete. An independent re-derivation that is internally self-consistent and an oracle built
  from the same math both *pass* on a wrong imported constant; only reproducing the value from its
  source catches it. `no_missing_step` attests the chain has no gaps; `external_values` attests the
  chain's imported inputs are real. Both are required because they fail independently.

## Ledger auto-generation (the second-pass re-derivation)

The ledger's `independent_rederivation: "verified"` means a *second, independent* pass reproduced the
math from axioms. If a human author fills that field by re-**reading** the survey, the attestation is
worthless — re-reading is exactly the failure mode the gate exists to stop. So for **load-bearing**
candidates, *produce* the ledger with a two-agent pipeline that reuses `method-eval`'s
derive→adversarial-re-derive stages; G0 then gates the agents' output rather than a human's promise.

Both agents do **math under ambiguity where a wrong-but-plausible result would survive a casual
read** — keep them on **Opus** (the `CLAUDE.md` fan-out rule: Opus for derivations / adversarial
verification, never Sonnet here).

1. **Deriver** — agent type `survey-enricher` (Opus). For each load-bearing candidate, re-derive the
   operator from first principles into **`wikis/<topic>-<operator>-derivation.md`** (the durable,
   lint-math + citation-gated, `secxref`-cross-linkable home — *not* `artifacts/`, which is
   study-scoped regenerable output). Bind the agent verbatim to `.claude/rules/workflow.md`
   (math-derivation rules: every step shown, no "it can be shown") and
   `.claude/rules/citation-integrity.md` (**every imported constant reproduced from an acquired
   `local:`/`spec:` source, never from memory** — this is what fills `external_values`).
2. **Adversarial reviewer** — agent type `general-purpose` (Opus). **Independently re-derives from
   axioms first**, *then* compares to the deriver's wiki; where they disagree it re-derives the
   disputed constant from its source and **CORRECTS the wiki in place**. This is `method-eval`'s
   second-agent stage, and it is the pass that earns `independent_rederivation: "verified"` and each
   `external_values[*].reproduced: true`. A reviewer that merely *reads and agrees* has not verified.

After the reviewer signs off, emit the machine-checkable `derivation_ledger` block: the
`artifacts/<study>` ledger holds only the **attestation + a pointer** (`survey_ref` → the wiki
section, plus `independent_rederivation`, `no_missing_step`, `limit_checks`, `assumptions`,
`external_values`) — the re-derivation *content* lives in the wiki, never duplicated into
`artifacts/`. Run the authoring cross-link + `/check-survey` sweep on the new wiki as its sign-off.

**Discrimination is the same G0 check.** The auto-generated ledger is validated by
`validate_gate.py … G0 …` exactly as a hand-authored one — a wrong imported constant fails the
`external_values` check (reviewer could not set `reproduced: true` from the source), and a
non-independent pass fails `independent_rederivation`. The generator cannot emit a passing ledger for
broken math. For the **catalog** tier this whole pipeline is skipped: a `survey_ref` +
`no_missing_step` is enough (don't re-derive linear interpolation from Shannon). For the four
gap-size cases (confirm / small-gap / large-gap / novel-no-survey) see the next section.

## Gate G0

```bash
python .claude/skills/reference-implementation-study/validate_gate.py <study> G0 <topic>
```

Fails (blocks Phase 2) if: no ledger; a candidate module has no ledger entry; a bad `tier`; any
entry missing `survey_ref`/`spec_ref` or `no_missing_step`; or a **load-bearing** entry missing
`independent_rederivation == "verified"`, ≥1 `limit_checks`, a non-empty `assumptions` list, or a
well-formed `external_values` attestation (a list whose entries each carry a `source` + `reproduced:
true`, or an empty list paired with an `external_values_note`). Record the G0 result in the study doc
and the manifest iteration log, then proceed to Phase 2.

## When a candidate has no sound survey derivation to point at

G0 will (correctly) fail. Resolve by the gap size (see the RIS prerequisite discussion):

- **small / local** — derive the missing card *into the survey first* (`survey-enricher`), then
  point the ledger at it;
- **large** — run `deep-research-survey` first;
- **novel operator, no survey home** — derive it self-contained in Report §3 under the citation +
  math-authoring gates, set `survey_ref` to the report's own numbered equation, and file a
  `todos/` to back-port the derivation into a survey (a report is not a durable derivation home).
