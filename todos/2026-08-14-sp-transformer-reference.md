---
slug: sp-transformer-reference
date_filed: 2026-08-14
status: open
---

# A compressed signal-processing ↔ transformer reference document

## Context

Deferred from `decisions/2026-08-14-01`, which took three borrowings from
`mattpocock-skills:teach` into `/study` and held this one back.

`teach` draws a distinction this repo does not currently make: **"lessons will rarely be
revisited later — reference documents will be. They should be the compressed essence."**
Measured against that, all 23 folds in the corpus are *lesson-shaped* — long, in-context,
read once at the moment the question was asked. There is no reference-shaped artifact
anywhere, and `CONTEXT.md` is a glossary of **process** vocabulary (topic, experiment,
understood) with no **domain** entries, despite three surveys' worth of notation.

The strongest questions on record are signal-processing unifications the reader generated
unprompted — induction head as a matched filter acquired online, the ICL score as an LMS
learning curve in sequence position, the phase change as PLL lock rather than exponential
convergence, whitening, the log-likelihood ratio. Those readings are currently scattered
across folds and one-off answers, so each is re-derived on demand instead of being looked
up.

Held back deliberately rather than rejected: it is a **synthesis**, and it will be written
better from more folded material than exists today. Writing it now would compress four
sessions' worth of insight and then need rewriting.

## What is left

- Decide the home. Candidates: a `wikis/` page (out of manifest, plain-link target — note
  `.claude/reachability-severity` is `error`, so it needs a survey back-link in the same
  turn per `[opt:RIS-BACKLINK]`), or a domain-glossary section appended to `CONTEXT.md`.
  The reachability constraint likely favours `CONTEXT.md` unless the document grows past a
  page.
- Harvest the existing SP readings from the fold record — `study-frontier.py --recall`
  with a large N enumerates every fold, oldest first — plus the appendix-A §A.22 induction
  material and the H9 ICL-as-gradient-descent studies.
- Write it **compressed**: one row per correspondence (SP object ↔ transformer object ↔
  where the survey derives it), not prose. The test is whether it is worth re-opening.
- Add the domain terms to the glossary so `/wait-what`'s "ubiquitous language from
  `CONTEXT.md`" has something to draw on beyond process vocabulary.

## Acceptance

A reader can look up "what is the matched-filter reading of an induction head?" and get an
answer without re-deriving it, and `/wait-what` re-pitches in that vocabulary. It is
reference-shaped if it survives being re-read — if it reads like a lesson, it failed.

## Refs

- `decisions/2026-08-14-01-study-borrowings-from-teach.md` — the deferral.
- `mattpocock-skills` v1.2.3 `productivity/teach` — the reference-vs-lesson distinction.
- `.claude/commands/wait-what.md` — the consumer of the vocabulary.
- `docs/reader-frontier-2026-08-13.md` — where the SP questions were counted.
