---
name: survey-explainer-fold
description: Fold a conceptual Q&A / chat explanation into a survey as TWO linked artifacts — a compact inline blockquote "Note" at the point of confusion, and a dedicated, anchored, well-structured section that holds the full answer almost verbatim — then run the mandatory renumber/validate/index sweep that guarantees the edit lands clean. Use whenever, while reading a survey/appendix, the user wants a just-answered "why/how is X like this?" explanation persisted into the document.
---

# Survey Explainer Fold

## Overview

When a reader asks "why is this built this way?" or "how big is X in practice?"
and gets a good answer, that answer should not evaporate into the chat. This
skill persists it into the survey as **two artifacts that always ship
together**:

1. **The inline Note** — a compact `> **Note — …**` blockquote placed at the
   exact equation/paragraph that triggered the question. It gives the
   one-paragraph answer and ends with a forward link to (2). It keeps the main
   derivation line terse.
2. **The dedicated section** — a new anchored subsection that holds the *full*
   answer almost verbatim, in the "answer format" (intro → the core artifact as
   a fenced block or table → term-by-term / row-by-row prose with linked refs →
   "what it buys" → intuition / tie-in). It is link-targetable, so the Note (and
   anything else) can point at it.

The two are wired both ways: Note → section (forward link), section → the
Note's host (back reference).

This is a **rigid** skill for the mechanics (templates, placement rules, the
validation sweep) and **flexible** only in the prose content of the answer.
Do not drop either artifact, and do not skip the sweep — that is the whole
point (see *How the update is guaranteed*).

## When to use

- While reading a survey/appendix, the user asks a conceptual "why/how is X
  like this?" question (or "how large is X in real models?"), gets an answer,
  and wants it folded into the document.
- The user says "fold this in", "put this in the survey", "keep this Q&A",
  "add a note + a section for this".
- Any time a chat explanation about an existing equation/section is worth
  making permanent and link-targetable.

Not for: brand-new derivations that belong in the main flow (write those as
ordinary numbered content); fixing prose in place (just edit it).

## How the update is guaranteed

Reliability comes from two pillars. The skill supplies the first; the repo
already enforces the second.

**Pillar 1 — deterministic output (this skill).** Fixed templates for both
artifacts, fixed placement rules, and a checklist mean every run produces the
same shape: both artifacts, both links, correct anchors. Nothing is left to
recall.

**Pillar 2 — blocking gates (the repo).** Correctness is not hoped for, it is
refused if wrong:

- The `PostToolUse` `lint-math` hook **blocks the edit** on any math-authoring
  violation (delimiters, blank-line-after-`$$`, column-0 markers, bare refs at
  the configured severity — currently `error`). A bad Note or section cannot
  even be written.
- `renumber-sections.py --check`, `renumber-paragraphs.py --check`,
  `renumber-equations.py --check`, and `validate-refs.py` catch any
  anchor / paragraph / equation / reference drift.
- `/check-survey <survey-slug>` is the delivery gate; it runs the survey-wide
  checks at error severity, so broken content does not sign off.

The skill's Step 6 runs the `--init` half of the sweep (which inserts the new
anchors and is deliberately **not** in the auto-hook), then the `--check` half
that proves it landed clean. Pillars 1+2 together are the guarantee: shape is
fixed, and the gates reject anything that is not.

## Inputs

- **The target file** — the survey/appendix being read (e.g.
  `surveys/llms-for-coding/appendix-a-qkv-first-principles.md`).
- **The host** — the equation or paragraph that triggered the question (where
  the Note goes).
- **The Q&A** — the question (becomes both the Note's lead and the section
  title, declaratively) and the answer body.

Before editing, Read `.claude/rules/math-authoring.md` (marker / anchor /
delimiter rules) and `.claude/rules/citation-integrity.md` (no external
citation from memory — the section must reuse only already-verified sources).
For a "how large / what value in practice?" fold, the integrity rule is
load-bearing: **every concrete number must be read from a source already in
`download/` and cited to its existing `references.md` entry**, never recalled.

## Workflow

### Step 1 — Locate the host and read the neighborhood

Find the triggering equation/paragraph. Read enough around it to (a) get the
exact text to match for the insert, and (b) learn the local equation IDs and
section-numbering scheme. In this repo's appendices the subsections are
**letter-dotted** (`A.1`, `A.10`, `B.7`) and each is anchored
`<a id="sec-A.1">` by `renumber-sections`; deeper levels (`A.10.1`) and bold
**landmark** phrases (`**Step 3 — …**`, `**Figure A.1.**`) are also anchored.
External-standard section numbers are bracket-wrapped (`[§7]`) and are **not**
anchored — this decides Step 3.

### Step 2 — Write the inline Note

Place a `> **Note — …**` blockquote immediately after the host equation/
paragraph, matching any sibling `Note —` asides in that section. Keep it to one
paragraph; use *italic mini-labels* for sub-points. End with the forward link.
Do **not** hand-write the paragraph anchor — Step 6 injects it.

```markdown
> **Note — <the question, as a short claim>.** <one-paragraph answer; italic
> mini-labels per sub-point; inline math `$...$` with conditional bars written
> `\mid`>. The full breakdown is in <!-- secref:A.13 -->[§A.13](#sec-A.13).
```

### Step 3 — Choose the dedicated section's home (placement rules)

These rules are load-bearing — they are why the edit stays cheap and clean:

- **The section must be a *numbered* subsection heading** (`A.X` / `B.X`, or a
  3-level `A.X.Y` if the appendix already uses them) — the only full,
  link-targetable section anchors. Never make the dedicated content a bare bold
  **landmark** or an external-spec `[§N]` ref; those cannot be a clean link
  *target* for the Note.
- **Append at the END of the relevant numbered block**, immediately before the
  next `##`/`###`/`####` sibling (or the end of the file). Do **not** insert
  mid-block: that would force renumbering every later sibling
  (`A.X → A.X+1 …`) — `renumber-sections` does not rewrite the *printed*
  heading number, so every shifted heading and its `secref`/`secxref` would
  need a manual edit corpus-wide. Appending one new highest-numbered heading
  shifts nothing.
- Pick the block whose topic owns the answer (e.g. a dimensions Q&A → the end of
  the appendix that defines those symbols), even if the host Note lives in a
  different part; the forward link spans the distance.

### Step 4 — Write the dedicated section in "answer format"

Write the heading with the marker + inline anchor exactly like its siblings
(`<!-- sec:A.13 -->` on the line above, then `### <a id="sec-A.13"></a>A.13
Title`), then the body. **Reproduce verbatim-sensitive math (program
statements, annotated equations) as fenced code blocks, NOT as numbered
`$$…$$` equations** — this keeps the answer verbatim AND avoids minting new
`\tag{N}` equations, which would cascade every later equation number through
the rest of the appendix. A **concrete-values table is a markdown table** (not
a numbered equation), so it is cascade-free; use one for "how large is X?"
folds. Reference existing equations with the marked+linked form
(`<!-- ref:A-3 -->[(3)](#eq-3)`) and existing sections with `secref`/`secxref`.

````markdown
<!-- sec:A.13 -->
### <a id="sec-A.13"></a>A.13 <Title — the question, declaratively>

<Intro: name the question; link back to the host's section with a secref;
state the one-line answer; reference the relevant equations with marked+linked
refs.>

| <concrete-values table — or a fenced ASCII block for verbatim math> |
|---|

**Row by row / Term by term.**

**1. ...** <prose; inline math `$...$`; linked eq/section refs; every cited
number carries its `<!-- cite:N -->[[N]](references.md#ref-N)` source.>

**What it buys / What to take away.**

- <consequence 1, linking the follow-on equation/section>
- <consequence 2>

**Intuition.** <tie-in to a companion figure, a limit, or an SP analogy>
````

Citation integrity: cite only sources already verified in the survey's
`references.md` (strong `local:`/`spec:` tags preferred); **never introduce a
new external citation from memory, and never write a concrete value you have
not read in an acquired source.** If a needed number is not in any acquired
source, acquire it first via the `source-fetch` skill, or mark the gap — do not
guess. Prove small lemmas inline instead of citing.

### Step 5 — Wire both links

- Note → section: the `<!-- secref:A.13 -->[§A.13](#sec-A.13)` added in Step 2.
- Section → host: a `secref` back to the host's subsection in the section's
  intro (or a bracket-wrapped `[§N]` only if the host is an external-spec ref).

### Step 6 — Run the mandatory sweep (the guarantee)

In order, on the target file (paths relative to repo root):

```bash
python viewer/tools/renumber-sections.py   FILE --init     # anchor the new section + promote secrefs
python viewer/tools/renumber-paragraphs.py FILE --init     # anchor the new Note + section paragraphs
python viewer/tools/renumber-sections.py   FILE --check     # must be clean
python viewer/tools/renumber-paragraphs.py FILE --check     # must be clean
python viewer/tools/renumber-equations.py  FILE --check     # tags still sequential (no cascade)
python viewer/tools/link-references.py      DIR  --check     # cite markers consistent (run on the survey dir)
python viewer/tools/validate-refs.py        DIR              # cross-file refs valid
python viewer/tools/validate-refs.py --bare-refs-only --severity=error DIR   # must exit 0
python viewer/tools/check-citation-sources.py DIR/references.md              # source tags intact
python viewer/tools/build-index.py          FILE             # rebuild the file's index if the repo uses per-file indices
```

`lint-math` already ran (and blocked, if needed) on each edit via the
`PostToolUse` hook. If any `--check` reports drift, fix it before finishing —
do not hand-renumber. A green `/check-survey <survey-slug>` is the equivalent
one-command gate.

### Step 7 — Log

Log the turn per `CLAUDE.md` Conversation Logging (one `## Conversation N`
entry in the session's `prompts/` file, with the `📒` indicator). Commit only
if the user asks.

## Checklist (create one todo per item)

- [ ] Read `math-authoring.md` + `citation-integrity.md`; locate host + local IDs.
- [ ] Inline Note written at the host, with forward link, no hand-written anchor.
- [ ] Section home chosen: numbered subsection, appended at end of its block.
- [ ] Section written in answer-format; verbatim math as fenced blocks / values as a table; refs marked+linked; every number read from an acquired source; no memory citations.
- [ ] Both links wired (Note→section, section→host).
- [ ] Sweep run: sections/paragraphs `--init` → all `--check` clean → equations `--check` no cascade → link-references/validate-refs/bare-refs/citation-sources clean → index rebuilt.
- [ ] Turn logged.

## Cross-references

- `.claude/rules/math-authoring.md` — equation/section/paragraph markers,
  anchors, inline-delimiter rules; enforced by the `lint-math` hook.
- `.claude/rules/citation-integrity.md` — no external citation from memory; the
  `references.md` ↔ `download/` source-tag invariant.
- `.claude/skills/source-fetch/SKILL.md` — acquire a source when a needed value
  is not yet in `download/`.
- `/check-survey <survey-slug>` — the gate that runs the `--check` suite.
- Worked instance (the pattern this skill generalizes): the
  `appendix-a-qkv-first-principles.md` A.1 compact Note + the `A.13` dedicated
  "Concrete Dimensions in Real-World Models" section, session
  `prompts/2026-06-17-viewer-sync.md`.

## Cross-link sign-off

The dedicated section this skill creates is a prime cross-link target (and
source). Before sign-off, run the `cross-link` skill (or
`crosslink.py check $SCOPE --changed`) over the new section and clear the
reported high-value gaps, or file a `todos/` entry for any left out of scope —
per `.claude/rules/cross-linking.md`.
