Run full validation on the specified survey: $ARGUMENTS

Steps:
1. Run `python viewer/tools/lint-math.py <file> --errors-only` -- report any math formatting errors.
2. Run `python viewer/tools/renumber-equations.py <file> --check` -- verify equation numbering is sequential.
3. Run `python viewer/tools/link-references.py <file> --check` -- verify citation links are consistent.
4. Run `python viewer/tools/renumber-paragraphs.py <file> --check` -- verify paragraph anchors are sequential and current.
5. Run `python viewer/tools/renumber-sections.py <directory> --check` -- verify section anchors and secref/secxref markers are consistent.
6. Run `python viewer/tools/validate-refs.py <directory>` -- verify cross-file references.
7. Run `python viewer/tools/validate-refs.py --bare-refs-only --severity=error <directory>` -- enforce bare-ref prohibition (rule from `.claude/rules/math-authoring.md`).
8. Run `python viewer/tools/check-citation-sources.py <references-file> --identity` -- verify every reference entry carries a source tag (`local:`/`spec:`/`web`/`abstract-only`) and that each `local:`/`spec:` file exists on disk (**errors** — these fail the check). The `--identity` flag adds two **advisory** (warn-only, never failing) checks that a presence check cannot: a weak page-1 **identity** check flags a `local:`/`spec:` file whose title/author tokens are absent from its first pages — a probable *wrong document*; and an **inverse-staleness** check flags a `(web)`/`(abstract-only)` entry whose first-author work IS present in `download/` — a probable *held-but-under-tagged* source. Review each warning; they never fail the check. See `.claude/rules/citation-integrity.md`.
9. Run `python viewer/tools/check-footnote-refs.py <directory>` -- enforce the viewer's reserved `note-` footnote namespace: any `[^note-...]` reference must be flush after a `==highlight==` close (ordinary footnotes use a non-`note-` id). A bare-prose `note-*` ref collides with the viewer's highlight-note click handler (bug `2026-06-15-02`).
10. Run `python viewer/tools/check-crossfile-ref-markers.py <directory>` -- an equation reference into a SIBLING file must use the `xref:` form; a cross-file reference marked `ref:` is in a blind spot (not an orphan, so `renumber-equations` says nothing; not an xref, so it is never propagated) and goes stale silently at the next renumber.
11. Run `python viewer/tools/check-section-ownership.py <directory>` -- no file may declare a section number whose `N.x` subsections live in a different file of the same survey (`secxref` resolution is first-definition-wins, so the reference silently lands in the declaring file).
12. Run `python viewer/tools/check-link-fragments.py <directory> --severity=warn` -- `validate-refs.py` checks that a link's target FILE exists and never inspects the `#fragment`, so `[foo](bar.md#sec-9.9.9)` passes as long as `bar.md` does.
13. Run `python viewer/tools/check-depth-tiers.py <directory>` -- enforce the R-GOV depth-tier vocabulary: every authored `Depth tier: <value>` label must use an allowed tier (`headline` / `load-bearing` / `catalog`, plus the ratified off-ladder `supporting`). Catches invented / mistyped tiers that the depth-budget governor `[R-GOV]` (`.claude/skills/deep-research-survey/addenda/phase-2.md`) relies on but that no other gate reads.
14. Run `python viewer/tools/check-figure-labels.py <directory>` -- duplicate figure-label gate: two authors independently reaching for "the next free number" can both caption a figure the same way, and nothing else catches it (asset filenames differ, no file is overwritten).
15. Report a summary: total equations, total references, the depth-tier tally, any errors or warnings found.

To **apply** (rather than verify) the marker/anchor discipline, use `/normalize-survey <dir>` — the write-mode twin of this command.
