# Citation Integrity Rule

Loaded on demand by `CLAUDE.md`. Read this file before writing or
expanding any document that carries external citations — surveys,
appendices, reports, proposals — and before dispatching a subagent to do
so.

## The rule

**Never write an external citation from memory.** Every citation —
author, year, title, venue, section or page, and every value attributed
to it — must be traceable to a source that has actually been opened and
read. A claim you are "confident" appears in a paper is not a citation; it
is a guess wearing a citation's clothes.

This is a prevention rule. The after-the-fact verification workflow is the
`citation-audit` skill — but prevention is cheaper than audit, and an
audit only runs when someone invokes it. The discipline below applies to
every citation at the moment it is written.

## Why

Citations recalled from parametric memory fail in ways that survive a
casual read:

- **Plausible-but-wrong attribution** — the right idea credited to the
  wrong paper.
- **Fabricated specifics** — a section number, a theorem, or a result
  that does not exist in the cited work.
- **Drifted values** — a coefficient, sign, or magnitude close enough to
  look right and wrong enough to corrupt a derivation.

This is not hypothetical. Subagent-authored citations in a scaling-laws /
RLHF survey appendix credited a scaling-law exponent to Kaplan et al.
(2020) when the result was actually Hoffmann et al. (2022), with the
exponent value itself drifted from what either paper reports. The
plausible-but-wrong attribution and the drifted value were caught only by
an after-the-fact audit of the subagent-authored survey appendix.

## What "verified" means

A citation is verified when all three hold:

1. The source file exists in the repo — `download/` for papers (and
   optionally a formal-spec path like `docs/specs/` for technical specs) —
   acquired via the `source-fetch` skill.
2. The cited section or page has been read, and the specific claim the
   document makes is actually made there.
3. Every cited number has been reproduced from the source.

Until all three hold, do not write the citation. Write the prose without
it, or mark the gap explicitly for a later pass.

## The `references.md` ↔ `download/` invariant

Every entry in a document's reference list must end with a **source tag** —
a trailing parenthetical declaring where the acquired source is. The tag is
the last element of the entry, placed after any descriptive parenthetical
or `[link]`. Four forms:

| Tag | Meaning |
|---|---|
| `(local: download/<file>)` | Full text held in the repo (`download/`, or another tracked path). |
| `(spec: docs/specs/<path>)` | A formal technical specification held in the repo (e.g. an RFC or the Model Context Protocol spec). |
| `(web)` | A live web resource — vendor IP page, blog, calculator, standards-body landing page — where the citation *is* the page and there is no fetchable document. The entry's `[link]` carries the URL. |
| `(abstract-only)` | A paper, patent, or book whose full text is genuinely not held; the citation rests on the abstract alone. |

`local:` and `spec:` are the **strong** forms — the cited source is in the
repo and was read. `web` and `abstract-only` are **weak** forms: they
satisfy the invariant (the entry is not an unverified memory citation), but
they are exactly what the `citation-audit` skill scrutinises, and a
load-bearing claim must not rest on a weak-form reference.

No reference entry may exist without a source tag. The invariant is
mechanically checked by `viewer/tools/check-citation-sources.py`, which
flags any untagged entry and any `local:` / `spec:` tag whose file is
missing from disk — an error of the same class as a `lint-math` violation.
The checker runs as a step of `/check-survey`.

## Subagent propagation

A subagent dispatched to write or expand cited content does not inherit
this rule automatically. Any implementer or writer subagent prompt for
survey, appendix, report, or proposal work must:

- include this rule, verbatim or by reference;
- instruct the subagent to acquire sources via the `source-fetch` skill
  before citing;
- forbid citing from memory and require the gap-marking fallback instead;
- require the subagent to report, on return, which citations it verified
  against an acquired source and which it could not.

## When a full audit is mandatory

Running this rule at authoring time is not a substitute for the
`citation-audit` skill. Run the full audit when:

- cited content was produced before this rule was in force;
- cited content was produced by a subagent;
- a cited document reaches a delivery, sign-off, or plan-acceptance gate.

## Cross-references

- `.claude/skills/citation-audit/SKILL.md` — the verification and
  impact-audit workflow this rule front-stops.
- `.claude/skills/source-fetch/SKILL.md` — paper and book acquisition.
