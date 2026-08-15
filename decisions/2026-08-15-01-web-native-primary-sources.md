---
id: 2026-08-15-01
title: Web-native primary sources are acquired to download/web-native/ and carry the strong `local:` tag
status: accepted
date: 2026-08-15
---

## Context

Appendix A of `surveys/mechanistic-interpretability` derives the QK/OV factorization, virtual
weights, the path-expansion trick and the three-way composition taxonomy. All four originate in
Elhage et al., *A Mathematical Framework for Transformer Circuits* (Transformer Circuits Thread,
2021) — reference `[1]`, which was tagged **`(web)`**.

`.claude/rules/citation-integrity.md` is explicit that `(web)` is a **weak** form and that "a
load-bearing claim must not rest on a weak-form reference". An appendix whose entire framing traces
to `[1]` therefore could not be written honestly against a `(web)` tag: it would be citing the
downstream re-statements (Wang 2022, Olsson 2022) as if they were the record. The per-appendix
derivation audit flagged this independently as an acquisition gap that had to be fixed *before*
writing.

The obstacle is mechanical, not editorial. Transformer Circuits Thread articles are **web-native**:
no PDF is published, so `source-fetch`'s PDF path cannot acquire them. And `.gitignore` carried
`download/*` with a single `!download/*.pdf` negation, so any non-PDF placed in `download/` is
untracked — which fails `check-citation-sources.py --index` at the push gate, since that resolver
checks git's index rather than the working tree.

So the choice was: leave a load-bearing appendix resting on a weak reference, or extend the
acquisition convention to cover sources that are genuinely primary but never published as PDFs.

## Decision

Acquire web-native primary sources by extracting the published HTML to text under a new
**`download/web-native/`** directory, tracked plainly (not LFS — these are text, not binaries), and
tag them with the strong **`(local: download/web-native/<file>.txt)`** form. `.gitignore` gains a
scoped carve-out (`!download/web-native/` + `!download/web-native/*.txt`) rather than a per-file
exception.

`(web)` is retained, with its meaning narrowed to what it was always supposed to cover: a page where
no full text is fetchable, or where the citation genuinely *is* the page (a vendor IP page, a
landing page, a blog post cited as an artifact rather than as an argument).

## Alternatives considered

- **Leave `[1]` as `(web)` and cite the re-statements instead.** Rejected: this is precisely the
  failure `citation-integrity` exists to prevent, and the derivation audit had already caught the
  re-statements diverging from the record — one of them prints a non-conformable attention formula
  because it transcribed Elhage's column-token form under a declared row-token layout. Citing the
  echo would have imported that error.
- **Convert the HTML to PDF so it matches the existing `!download/*.pdf` rule.** Rejected: a
  print-to-PDF of a JS-rendered page is a lossy re-rendering, and it would *destroy* the property
  that makes this extraction valuable — the article's own LaTeX source survives in the HTML, so
  equations are quoted from the record rather than from an OCR or a text-layer guess. A PDF would be
  strictly worse evidence than the text.
- **A per-file `.gitignore` negation for this one article.** Rejected as unscalable: references `[6]`,
  `[7]`, `[8]`, `[19]`, `[42]` and others in this survey alone are Transformer Circuits Thread or
  Alignment Forum pages with the same shape. A directory-scoped rule generalizes; a per-file list
  accretes.
- **A new source tag (e.g. `(web-local:)`).** Rejected as unnecessary complexity — the existing
  `local:` tag already means "full text held in the repo and read", which is exactly true here.
  Adding a fourth tag would require touching `check-citation-sources.py` for no gain in meaning.

## Consequences

- Reference `[1]` moves from weak to strong form, so Appendix A's derivations rest on the record.
  The survey's weak-form ratio improves by one entry.
- **A backlog is created, deliberately**: the other Transformer Circuits Thread / Alignment Forum
  entries in this survey remain `(web)` and are now visibly upgradeable by the same route. Filed as
  `todos/2026-08-15-web-native-source-upgrades.md` rather than swept along with this change, because
  each upgrade needs its own read-and-verify pass and this session's scope was the appendices.
- The extraction is a **derived artifact**. It carries a provenance header (source URL, retrieval
  date, method) so a future auditor can tell it apart from a publisher-issued file and can re-fetch.
  It is not a substitute for the live page if the page changes; the header's date is what scopes it.
- `check-citation-sources.py` needs no change — it resolves any tracked path, and these are tracked.

## Refs

- `.claude/rules/citation-integrity.md` — the `references.md` ↔ `download/` invariant and the
  strong/weak tag distinction this decision turns on.
- `surveys/mechanistic-interpretability/_scratch/appendix-A-extract.md` — the audit that flagged the
  acquisition gap ("citing the re-statements, not the record") and the non-conformable formula in
  one of them.
- `download/web-native/elhage-mathematical-framework-2021.txt` — the first artifact under the new
  convention.
- `todos/2026-08-15-web-native-source-upgrades.md` — the remaining `(web)` entries.
