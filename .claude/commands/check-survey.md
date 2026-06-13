Run full validation on the specified survey: $ARGUMENTS

Steps:
1. Run `python viewer/tools/lint-math.py <file> --errors-only` -- report any math formatting errors.
2. Run `python viewer/tools/renumber-equations.py <file> --check` -- verify equation numbering is sequential.
3. Run `python viewer/tools/link-references.py <file> --check` -- verify citation links are consistent.
4. Run `python viewer/tools/renumber-paragraphs.py <file> --check` -- verify paragraph anchors are sequential and current.
5. Run `python viewer/tools/renumber-sections.py <directory> --check` -- verify section anchors and secref/secxref markers are consistent.
6. Run `python viewer/tools/validate-refs.py <directory>` -- verify cross-file references.
7. Run `python viewer/tools/validate-refs.py --bare-refs-only --severity=error <directory>` -- enforce bare-ref prohibition (rule from `.claude/rules/math-authoring.md`).
8. Run `python viewer/tools/check-citation-sources.py <references-file>` -- verify every reference entry carries a source tag (`local:`/`spec:`/`web`/`abstract-only`) and that each `local:`/`spec:` file exists on disk (see `.claude/rules/citation-integrity.md`).
9. Report a summary: total equations, total references, any errors or warnings found.
