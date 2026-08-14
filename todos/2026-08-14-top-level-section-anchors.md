---
slug: top-level-section-anchors
date_filed: 2026-08-14
status: closed
---

**Resolution.** Fixed in the same session, 2026-08-14. The deferral reasoning below was
wrong: it assumed the fix required the *dash* marking (`## 12 — Agentic Coding Systems`),
which changes visible heading text and therefore cascades every paragraph anchor. Checking
how the two healthy surveys actually do it showed they use the **fourth** marking instead —
a hand-authored anchor after the ATX prefix with the heading text untouched:

```
## <a id="sec-9"></a>9 Circuits across models
```

That form has **no cascade at all**, which the run confirmed: `renumber-paragraphs --check`
reported `Updates: 0`. Applied `sec-1`..`sec-18` to the body files and `sec-A`..`sec-I` to
the appendices (27 files), then ran `renumber-sections.py` to write the companion
`<!-- sec:N -->` markers. Gates green afterwards: `renumber-sections --check` silent,
`validate-refs` 0 errors / 0 warnings, `check-section-ownership` OK,
`check-link-fragments` 517 fragment links / 0 dangling.

The appendix anchors are the documented hand-authored `sec-A`..`sec-D` precedent — their
headings carry no parseable section number, so `match_heading` still returns `None` and
resolution keys on `ANY_SEC_ANCHOR_RE` instead.

**Still open, deliberately narrowed:** the corpus-wide audit. `mechanistic-interpretability`
(16 anchors) and `multimodal-llms` (14) were already correct, and `attention-demo` is a
tooling fixture. The surviving question is whether a gate should exist at all — a numbered
top-level heading that yields no section anchor is invisible today. Tracked as the last
bullet under "What is left".


# Top-level survey sections carry no `sec-N` anchor and are not link targets

## Context

Found during Phase 1 of the `deep-research-survey` max-mode expansion of
`surveys/llms-for-coding/` (2026-08-14).

Every body file in that survey opens with a heading of the form `## N Title`
(`## 12 Agentic Coding Systems`, `## 2 Scope and the Code Modality`, ...). The corpus
section grammar (`viewer/tools/heading_grammar.py::match_heading`) treats a **flat**
number as a section only when the line *marks* it as one:

- a leading section glyph, `## § 1 Scope`
- a trailing dot, `## 5. Power-Domain NOMA`
- a dash separator, `## 3 — Road A`
- an already-present matching `sec-N` anchor

An unmarked flat number is deliberately **not** a section — otherwise `## 2020 in review`
would be parsed as section 2020. That guard is correct and should not be relaxed.

The consequence is that none of the 18 top-level sections of `llms-for-coding` is a link
target. `grep -ho 'id="sec-[0-9]*"' surveys/llms-for-coding/*.md` returns **zero** matches;
only `N.M` subsection anchors exist. A `secxref:12` cannot resolve, so no document can link
to "Agentic Coding Systems" as a whole — only to `12.1`, `12.2`, ...

This is a **silent** gap, not a reported one: no gate fails. `renumber-sections --check`
is content, because it has no heading to anchor. `crosslink.py check` is content, because
the subsections *are* indexed, so the file is neither invisible nor unreachable. The
survey looks fully cross-linked and is missing an entire level of its reference graph.

Worth checking whether the other surveys (`mechanistic-interpretability`,
`multimodal-llms`, `attention-demo`) and the two `wikis/` share the shape — the grammar is
corpus-wide, so a survey that numbers its top-level headings flat has the same gap.

## What is left

- Decide the marking. The dash form (`## 12 — Agentic Coding Systems`) is the best fit:
  it is documented in `match_heading`, it reads as intentional, and `renumber-sections.py`
  will then inject and maintain `sec-N` automatically. A trailing dot also works and is a
  smaller visual change.
- Apply it across the 18 body headings of `llms-for-coding`, then run
  `/normalize-survey surveys/llms-for-coding`.
- **Handle the paragraph-anchor cascade.** `renumber-paragraphs.py` derives
  `p-<section-slug>-<N>` from the nearest preceding heading, so changing the heading text
  changes every paragraph anchor in the file. Confirm nothing in-corpus links to a `#p-`
  fragment before the rename (the viewer's Copy-citation feature mints these at read time,
  so external/clipboard links may exist and will break — accept or note it).
- Audit the other surveys and the wikis for the same shape; extend the fix if present.
- Consider whether a gate should exist: a numbered top-level heading that yields no
  section anchor is arguably a `warn`-level finding, since today it is invisible.

## Acceptance

- `grep -ho 'id="sec-[0-9]*"' surveys/llms-for-coding/*.md | sort -u` lists `sec-1`
  through `sec-18`.
- `/check-survey surveys/llms-for-coding` is green, including
  `renumber-paragraphs --check` after the anchor cascade.
- A `secxref:12` from another file resolves to `agentic-coding-systems.md#sec-12`.

## Refs

- `surveys/llms-for-coding/_scratch/00-max-mode-outline.md` section 2 — where the defect
  was recorded during Phase 1.
- `viewer/tools/heading_grammar.py` — `match_heading`, and the module docstring's account
  of two prior false-green grammar-drift bugs (`2026-07-09-13`, `2026-07-09-16`) in the
  same family: a grammar mismatch that fails by reporting green.
- `.claude/rules/math-authoring.md` — Section Cross-Linking, the anchor placement rule.
