---
slug: web-native-source-upgrades
date_filed: 2026-08-15
status: open
---

# Upgrade the remaining `(web)` references that are web-native PRIMARY records

## Context

`decisions/2026-08-15-01` established that a source published only as HTML can still be a **primary
record**, and that such a source is acquired by extracting the published article to text under
`download/web-native/` and tagged with the strong `(local: ...)` form. The first artifact under that
convention is Elhage et al. 2021 (`surveys/mechanistic-interpretability` reference `[1]`), which was
upgraded because Appendix A's entire framing rests on it and `citation-integrity` forbids a
load-bearing claim resting on a weak-form reference.

That upgrade was done as part of deepening Appendix A. The **other** `(web)`-tagged entries in the
same survey were deliberately not swept along: each needs its own fetch-and-read pass, and doing
them in bulk during an appendix-writing session would have meant tagging sources `local:` without
actually reading them — which is the failure the tag exists to prevent.

## What is left

Triage every `(web)` entry in `surveys/mechanistic-interpretability/references.md` (and then the
other surveys) into one of two buckets, and upgrade only the first:

1. **Web-native primary record** — a substantive article that this survey draws arguments, equations
   or numbers from. Fetch, extract to `download/web-native/`, read the cited passage, re-tag
   `local:`. Known candidates in the MI survey: `[6]` (Privileged Bases), `[7]` (Towards
   Monosemanticity), `[8]` (Scaling Monosemanticity), `[19]` (Sparse Crosscoders), `[42]` (Causal
   Scrubbing), `[57]` (Python Docstrings circuit). Several of these ARE load-bearing — `[7]` and
   `[8]` are cited in the dictionary-learning sections — so they are the priority.
2. **Genuinely a page** — a landing page, an index, a blog post cited as an artifact rather than as
   an argument. Leave `(web)`; that is what the tag is for.

Prioritise by whether the entry currently carries a load-bearing claim: run
`link-references.py`/grep to find which sections cite each `(web)` entry, and start with the ones
cited from a `headline`-tier section.

## Acceptance

- Every `(web)` entry in the MI survey has been triaged into bucket 1 or bucket 2, with the bucket-2
  choices justified in one line each.
- No `(web)`-tagged reference is the sole support for a load-bearing claim in a `headline`-tier
  section.
- `check-citation-sources.py --index` stays green (every new `local:` path is tracked).
- The weak-form ratio reported in the survey's own reference-audit line is updated.

## Refs

- `decisions/2026-08-15-01-web-native-primary-sources.md` — the convention and why it exists.
- `.claude/rules/citation-integrity.md` — the strong/weak tag distinction.
- `download/web-native/elhage-mathematical-framework-2021.txt` — the worked example to copy.
- `.gitignore` — the directory-scoped carve-out (`!download/web-native/`).
