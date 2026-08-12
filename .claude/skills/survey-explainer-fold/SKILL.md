---
name: survey-explainer-fold
description: Fold a conceptual Q&A / chat explanation into a survey at the point of confusion — in one of three shapes selectable per request: the default two-artifact fold (a compact inline blockquote "Note" plus a dedicated, anchored section holding the full answer almost verbatim), a note-only inline gloss, or a plain-prose insert straight into the main flow (no note box, no section) — then run the mandatory renumber/validate/index sweep that guarantees the edit lands clean. Use whenever, while reading a survey/appendix, the user wants a just-answered "why/how is X like this?" explanation persisted into the document.
---

# Survey Explainer Fold

## Overview

When a reader asks "why is this built this way?" or "how big is X in practice?"
and gets a good answer, that answer should not evaporate into the chat. This
skill persists it into the survey. Its **default (`full`) mode** ships **two
artifacts that always ship together**:

1. **The inline Note** — a compact `> **Note — …**` blockquote placed at the
   exact equation/paragraph that triggered the question. It gives the
   one-paragraph answer and ends with a forward link to (2). It keeps the main
   derivation line terse.
2. **The dedicated section** — a new anchored subsection that holds the *full*
   answer almost verbatim, in the "answer format" (intro → the core artifact as
   **untagged `$$` display math** (or a table) → term-by-term / row-by-row prose
   with linked refs → "what it buys" → **physical meaning** → intuition / tie-in).
   It is link-targetable, so the Note (and anything else) can point at it.

The two are wired both ways: Note → section (forward link), section → the
Note's host (back reference).

Two lighter modes drop one or both artifacts when the answer does not warrant
them — **`note-only`** (the inline Note alone) and **`prose`** (plain main-flow
paragraphs at the host, no box, no section). See *Modes* for selection. The
**mechanics are identical** in every mode.

This is a **rigid** skill for the mechanics (templates, placement rules, the
validation sweep) and **flexible** only in the prose content of the answer and
the choice of mode. Do not drop a mode's chosen artifacts, and do not skip the
sweep — that is the whole point (see *How the update is guaranteed*).

## When to use

- While reading a survey/appendix, the user asks a conceptual "why/how is X
  like this?" question (or "how large is X in real models?"), gets an answer,
  and wants it folded into the document.
- The user says "fold this in", "put this in the survey", "keep this Q&A",
  "add a note + a section for this".
- Any time a chat explanation about an existing equation/section is worth
  making permanent and link-targetable.

Not for: brand-new derivations that belong in the main flow (write those as
ordinary numbered content); fixing prose in place (just edit it); **naming or
tightening the definition of an existing symbol/term at its own point of
introduction** — that is a one-clause inline gloss, not a Note+section fold.
Rule of thumb: if the answer's supporting math already sits within a line or two
of where the question arose, it wants a **gloss**; fold only knowledge that is
genuinely new *and* belongs somewhere other than where the question was asked.
(This boundary was added after the skill was over-applied to a bare symbol
definition — see `prompts/2026-07-06-wcm-spatial-correlation-duality.md` Conv 16.)

## Modes

The fold ships in one of three shapes. The **mechanics are identical** across
modes (placement rules, the no-cascade discipline, the Step-6 sweep, the
citation-integrity rule); only *which artifacts ship* changes.

| Mode | Artifacts | Use when | Workflow steps |
|---|---|---|---|
| **`full`** (default) | inline Note **+** dedicated anchored section, wired both ways | the answer is substantial, deserves a link-target, and the host derivation line should stay terse | 1, 2, 3, 4, 5, 6, 7 |
| **`note-only`** (aka `inline`) | a single inline `> **Note —**` blockquote at the host, no section | a compact notation / conceptual gloss that does not merit a standalone section | 1, 2, 6, 7 (skip 3–5) |
| **`prose`** (aka `direct`) | plain main-flow paragraph(s) at the host — **no** Note box, **no** section | the answer is a direct elaboration that belongs *in the reading flow* at the host, and a boxed aside would interrupt it | 1, 2′, 6, 7 (skip 3–5) |

**Selecting the mode.** Default to `full`. Choose `note-only` (the user often
calls this **`inline`**) for a one-paragraph gloss — the user's standing
preference for compact notation folds (see the `inline-notation-folds-preference`
memory and decision `2026-06-29-03`). Choose `prose` (the user often calls this
**`direct`**) when the user says "fold this **directly**", "without a/the note",
"without the note format", "into the main flow", "as plain prose", or otherwise
asks for the answer to read as part of the section rather than as a boxed aside.
**When the user names the shape, that overrides the default** — the mode is the
one thing the caller, not the skill, decides.

The two aliases split on **box vs. no box** — which is also the one trap to
avoid: `inline` → `note-only` keeps a compact *boxed* `> **Note —**` aside at
the spot; `direct` → `prose` drops the box and writes straight into the flow.
Do **not** let the literal sense of "inline" pull `inline` toward `prose` (which
is in fact the *more* inline of the two) — the mapping is fixed: `inline` = the
boxed Note, `direct` = no box.

Whichever mode, the **no-cascade discipline is non-negotiable**: never mint a
new numbered `$$…$$` equation (it would `\tag` and renumber every later
equation). Reference existing equations with the marked+linked form, reproduce
verbatim math as fenced blocks, and put concrete values in a markdown table —
all three are cascade-free (Step 4).

## How the update is guaranteed

Reliability comes from two pillars. The skill supplies the first; the repo
already enforces the second.

**Pillar 1 — deterministic output (this skill).** Fixed templates per artifact,
fixed placement rules, and a checklist mean every run produces the same shape
*for the chosen mode*: the mode's artifacts, its links, correct anchors.
Nothing is left to recall.

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
  the Note / prose goes).
- **The Q&A** — the question (becomes the Note's lead, the section title, or a
  prose bold lead-in, declaratively) and the answer body.
- **The mode** — `full` / `note-only` / `prose` (see *Modes*); defaults to
  `full`, overridden by what the user asks for.

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

In `note-only` mode this Note is the whole fold: drop the trailing forward link
(there is no section to point at), then go straight to Step 6.

### Step 2′ — (prose mode) Write the plain-prose insert instead

In `prose` mode there is no Note box and no dedicated section: the answer goes
into the section's **main flow** as one or more ordinary paragraphs, inserted
**immediately after the host paragraph** and before the next block (an existing
Note, equation, or heading). Match the surrounding prose — give each paragraph a
**bold lead-in** in the section's own style (e.g. `**Where the two values come
from.**`) when its siblings use them, and keep the density consistent with the
neighbors. Edit by matching the unique tail of the host paragraph and appending
the new paragraphs after it.

The cascade-free discipline of Step 4 is the main constraint here, because prose
folds are where a stray display equation is most tempting:

- **No new numbered `$$` equation** — it mints a `\tag{N}` and cascades every
  later equation. Use inline math `$...$`; reference existing equations with the
  marked+linked form (`<!-- ref:A-20-1 -->[(27)](#eq-27)`); reproduce any
  verbatim block as a fenced code block.
- **Do not hand-write paragraph anchors** — `renumber-paragraphs.py --init` in
  Step 6 injects them and renumbers the section's downstream paragraphs.
- Keep markers inline after prose (never column-0 / first content of a block),
  conditional bars as `\mid`, and obey the inline-`$`-vs-digit rule — the
  `lint-math` hook blocks violations either way.

Step 5 is skipped (there are no two artifacts to wire); if the prose references
other sections/equations, use the normal `secref` / `ref` markers inline. Then
go to Step 6. *(Worked instances: the §A.20 plain-prose folds — "Reading the two
ones", "Where the two values come from" — in
`prompts/2026-06-29-viewer-serve-launcher.md`.)*

### Step 3 — (full mode) Choose the dedicated section's home (placement rules)

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

### Step 4 — (full mode) Write the dedicated section in "answer format"

Write the heading with the marker + inline anchor exactly like its siblings
(`<!-- sec:A.13 -->` on the line above, then `### <a id="sec-A.13"></a>A.13
Title`), then the body. Reference existing equations with the marked+linked form
(`<!-- ref:A-3 -->[(3)](#eq-3)`) and existing sections with `secref`/`secxref`.
A **concrete-values table is a markdown table** (not a numbered equation), so it
is cascade-free; use one for "how large is X?" folds.

**Math exhibits are math: write them as UNTAGGED `$$…$$` display blocks, never
as ASCII art in a fenced code block** `[opt:EF-MATHEXHIBIT · default ON · toggle
.claude/skill-options.json]`. An annotated equation belongs in KaTeX —
`\underbrace{…}_{\text{label}}`, `\overbrace{…}^{\text{label}}`, `\substack{}`
for multi-line labels, `\begin{aligned}` for a stepped derivation — not drawn
with box-drawing characters and arrows. Fenced blocks are for genuinely
**non-math** verbatim content: pseudocode, program listings, ASCII plots.

Omitting `\tag{N}` is what keeps the exhibit cascade-free; the fence was never
what did that. The two rules are independent, and only the first one matters:

- **Do not mint a `\tag{N}`** for an exhibit. Untagged display math is a
  first-class, warning-level citizen. `lint-math` check #9 emits `WARNING:
  display-math block has no \tag{N}`, never an error.
- **Do use `$$…$$`** so the exhibit renders as math, is searchable, respects the
  reader's font/zoom, and stays accessible.

Two reasons an exhibit must not be tagged — neither is the one this skill used
to give:

1. **Semantic.** An exhibit that re-displays or annotates an *existing* equation
   must not mint a rival number for it. A reader must never be able to cite both
   "(10)" and "(13)" for the same relation.
2. **Cross-file.** Equation numbers cited from *outside* the survey directory
   (e.g. a standalone wiki) are unprotected: `renumber-equations.py::propagate_xrefs`
   only walks `target_path.parent`, and its `XREF_FULL` pattern only matches the
   `[(N)](file.md#eq-N) <!-- xref:ID -->` form, so a stable-ID link with prose
   text is invisible to it. `validate-refs.py` checks that an anchor *resolves*,
   never that the visible number *matches*.

An **in-file** cascade is *not* a reason: `renumber-equations.py` Step 4 rewrites
every in-file `<!-- ref:ID -->` link automatically, and Step 6 propagates to
siblings in the survey dir. Renumbering inside one file is a safe, routine,
script-handled operation. (The earlier text claimed otherwise and used that false
claim to justify ASCII art — see `[opt:EF-MATHEXHIBIT]`.)

When you leave a block untagged, drop a one-line HTML comment above it recording
why, so a later reader does not "fix" the lint warning into a cross-file break.

````markdown
<!-- sec:A.13 -->
### <a id="sec-A.13"></a>A.13 <Title — the question, declaratively>

<Intro: name the question; link back to the host's section with a secref;
state the one-line answer; reference the relevant equations with marked+linked
refs.>

<!-- untagged by design: annotates Eq (24); a \tag would mint a rival number
     for it and stale the cross-file citations in standalone wikis. See [opt:EF-MATHEXHIBIT]. -->
$$
<the annotated equation, as REAL math — \underbrace / \overbrace with
 \substack{} labels, or \begin{aligned} for a stepped derivation.
 NO \tag{N}, and no <!-- eq:ID --> marker.>
$$

<blank line after the closing $$ — else the next paragraph's inline math
 renders as literal source (math-authoring.md, check #6d)>

<or, for a "how large is X?" fold, a plain markdown concrete-values table>

**Row by row / Term by term.**

**1. ...** <prose; inline math `$...$`; linked eq/section refs; every cited
number carries its `<!-- cite:N -->[[N]](references.md#ref-N)` source.>

**What it buys / What to take away.**

- <consequence 1, linking the follow-on equation/section>
- <consequence 2>

**Physical meaning.** <the mechanism in concrete terms — what is being summed,
compared, normalized, or cached; what a reader would actually observe or measure
— not only the symbolic derivation or a restatement of the governing equation. If
the concept is one of a dual/analogous family, draw the picture PARALLEL to its
siblings and name the one ingredient it adds. Required — [opt:EF-PHYSICAL ·
default ON · toggle .claude/skill-options.json].>

**Intuition.** <tie-in to a companion figure, a limit, or an SP analogy>
````

**Physical meaning is a required element, not decoration** `[opt:EF-PHYSICAL · default ON · toggle .claude/skill-options.json]`. Land the *mechanism in physical terms* — what is actually summed or superposed, what interferes or cancels, what a reader would observe or measure — not only the symbolic derivation, a restatement of the governing equation, or a limit. When the concept belongs to a dual/analogous family (coherence bandwidth / time / distance; the Bello functions; delay ↔ Doppler ↔ angle spreads), draw the physical picture **parallel to its siblings** so the mechanism reads the same way across them, and name explicitly the one ingredient the concept adds over the others. A "Geometrically / Intuition" tie-in that only re-states the math does **not** satisfy this. It operationalizes the `.claude/rules/workflow.md` math-derivation "intuition for each major result" bar for folded explanations. Motivating case: the coherence-distance fold delivered the phase-accrual math but omitted the sum-of-plane-waves interference picture — and its parallel to frequency selectivity as a sum of delayed taps — until the reader asked for it (`prompts/2026-07-06-wcm-spatial-correlation-duality.md`, Conv 14).

Citation integrity: cite only sources already verified in the survey's
`references.md` (strong `local:`/`spec:` tags preferred); **never introduce a
new external citation from memory, and never write a concrete value you have
not read in an acquired source.** If a needed number is not in any acquired
source, acquire it first via the `source-fetch` skill, or mark the gap — do not
guess. Prove small lemmas inline instead of citing.

### Step 5 — (full mode) Wire both links

- Note → section: the `<!-- secref:A.13 -->[§A.13](#sec-A.13)` added in Step 2.
- Section → host: a `secref` back to the host's subsection in the section's
  intro (or a bracket-wrapped `[§N]` only if the host is an external-spec ref).

*(`note-only` and `prose` modes skip this step — there is no second artifact.)*

### Step 6 — Run the mandatory sweep (the guarantee)

In order, on the target file (paths relative to repo root):

```bash
python viewer/tools/renumber-sections.py   FILE --init     # full mode: anchor the new section + promote secrefs (no-op in note-only/prose)
python viewer/tools/renumber-paragraphs.py FILE --init     # anchor the new Note/prose + section paragraphs (load-bearing in every mode)
python viewer/tools/renumber-sections.py   FILE --check     # must be clean
python viewer/tools/renumber-paragraphs.py FILE --check     # must be clean
python viewer/tools/renumber-equations.py  FILE --check     # tags still sequential (no cascade)
python viewer/tools/link-references.py      DIR  --check     # cite markers consistent (run on the survey dir)
python viewer/tools/validate-refs.py        DIR              # cross-file refs valid
python viewer/tools/validate-refs.py --bare-refs-only --severity=error DIR   # must exit 0
python viewer/tools/check-citation-sources.py DIR/references.md              # source tags intact
node   viewer/tools/verify-katex-render.cjs FILE             # the exhibit actually RENDERS (see below)
python viewer/tools/build-index.py          FILE             # rebuild the file's index if the repo uses per-file indices
```

`lint-math` already ran (and blocked, if needed) on each edit via the
`PostToolUse` hook. If any `--check` reports drift, fix it before finishing —
do not hand-renumber. A green `/check-survey <survey-slug>` is the equivalent
one-command gate.

**Why `verify-katex-render.cjs` is not optional here.** `lint-math` checks math
*delimiters* statically; it never runs KaTeX. Step 4 now mandates exhibits built
from `\underbrace` / `\overbrace` / `\substack` / `aligned` — precisely the
macros a static delimiter check cannot validate. An unsupported command or a
mismatched brace passes `lint-math` and then renders as a red `.katex-error`
node in the viewer. This tool drives the viewer's real vendored path (KaTeX
0.16.21 + markdown-it 14.1.0 + texmath 1.0.0, same options as
`viewer.js::renderedDisplayMathHtml`), checks display *and* inline spans, and
additionally flags `$$` / `\begin{` leaking into the rendered HTML — the
"renders as literal source" failure mode of `math-authoring.md` check #6d.
Run it on the file you edited; it is Playwright-free and takes about a second.

It is currently wired into **no** gate (`todos/2026-07-09-wire-katex-render-gate.md`),
so a skill sweep is the only place it runs. Do not skip it.

### Step 7 — Log

Log the turn per `CLAUDE.md` Conversation Logging (one `## Conversation N`
entry in the session's `prompts/` file, with the `📒` indicator). Commit only
if the user asks.

## Checklist (create one todo per item)

- [ ] Read `math-authoring.md` + `citation-integrity.md`; locate host + local IDs.
- [ ] **Mode chosen** (`full` / `note-only` / `prose`) per the *Modes* table and the user's phrasing.
- [ ] *(full, note-only)* Inline Note written at the host — with forward link (full) / no link (note-only) — no hand-written anchor.
- [ ] *(prose)* Plain-prose paragraph(s) written at the host, bold lead-ins matching siblings, no Note box, no hand-written anchor.
- [ ] *(full only)* Section home chosen: numbered subsection, appended at end of its block.
- [ ] *(full only)* Section written in answer-format; refs marked+linked; every number read from an acquired source; no memory citations.
- [ ] *(full only)* Math exhibits are UNTAGGED `$$…$$` KaTeX (`\underbrace`/`\substack`/`aligned`), not ASCII art in a fence; each carries a one-line "untagged by design" comment; fences reserved for pseudocode / listings / ASCII plots (`[opt:EF-MATHEXHIBIT]`).
- [ ] *(full only)* Physical meaning delivered — mechanism in concrete terms, drawn parallel to sibling concepts where applicable — not just a symbolic/limit tie-in (`[opt:EF-PHYSICAL]`).
- [ ] *(full only)* Both links wired (Note→section, section→host).
- [ ] **No cascade**: no new numbered `$$` equation minted (equations `--check` reports 0 tag updates).
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
- `viewer/tools/verify-katex-render.cjs` — the Step-6 render gate; complements
  `lint-math` (delimiters, static) by running the viewer's real KaTeX.
- Worked instance (the pattern this skill generalizes): the
  `appendix-a-qkv-first-principles.md` A.1 compact Note + the `A.13` dedicated
  "Concrete Dimensions in Real-World Models" section, session
  `prompts/2026-06-17-viewer-sync.md`.

## Cross-link sign-off

The dedicated section a `full`-mode fold creates is a prime cross-link target
(and source); a `note-only` / `prose` fold adds new prose that can still be a
cross-link source. Before sign-off, run the `cross-link` skill (or
`crosslink.py check $SCOPE --changed`) over the new content and clear the
reported high-value gaps, or file a `todos/` entry for any left out of scope —
per `.claude/rules/cross-linking.md`. A `note-only` / `prose` fold of a few
paragraphs is usually below the gap threshold, but run the check regardless.
