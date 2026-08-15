---
slug: prepush-bare-ref-scope
date_filed: 2026-08-15
status: open
---

# Pre-push bare-ref gate scans `surveys/` only — `wikis/` is never checked

## Context

Found while fixing `bugs/2026-08-15-04` (the spaced `§ 2.3` regex hole). Once the spaced
refs were promoted, two genuinely-bare refs surfaced in
`wikis/mechanistic-interpretability-coverage-gaps.md` (`§C.10`, `§A.22`) at **error**
severity — yet they had never blocked a push.

The reason is scope, not severity. `.githooks/pre-push` runs:

```
$PY viewer/tools/validate-refs.py --bare-refs-only --severity=error surveys/ || fail=1
```

`wikis/` is not in the pathspec. This is **orthogonal** to the regex hole that bug fixed:
widening a pattern does nothing for a directory the gate never scans. Both are false-greens,
but they fail for independent reasons, and closing one leaves the other open.

The omission looks like an oversight rather than a decision — `wikis/` *is* in the cross-link
corpus group (`.claude/crosslink-scope`), *is* covered by
`renumber-sections.py --check surveys/ wikis/` in the same hook, and *is* subject to the same
bare-form prohibition in `.claude/rules/math-authoring.md`. The bare-ref line is the outlier.

Not changed in the same pass because adding a directory to the push gate is a change that can
block everyone's next push, and it deserves its own verification rather than riding along in a
survey-authoring commit.

## What is left

- Add `wikis/` to the bare-ref line in `.githooks/pre-push` (likely
  `... --severity=error surveys/ wikis/`, matching the `renumber-sections --check` line
  directly above it).
- Confirm `validate-refs.py --bare-refs-only` accepts multiple path arguments; if not, either
  add a second invocation or fix the arg handling.
- Audit the hook for any OTHER check with the same narrow pathspec — the same oversight may
  affect more than one line. Check at least: lint-math, link-fragments, duplicate-anchor,
  and the citation-source scan.

## Acceptance

- A deliberately-introduced bare `§X.Y` in a `wikis/` file **fails** `.githooks/pre-push`.
- The whole corpus (`surveys/` + `wikis/`) passes the widened gate with no pre-existing
  violations — verified clean on 2026-08-15, so this should be a no-op adoption rather than
  a cleanup.
- Any other check found with a too-narrow pathspec is either widened or has its narrowness
  recorded as deliberate.

## Refs

- `bugs/2026-08-15-04-spaced-bare-section-ref-invisible-to-gate.md` — the sibling regex hole,
  fixed; this file is the scope hole it surfaced.
- `.githooks/pre-push` (the bare-refs line).
- `.claude/rules/math-authoring.md` — the bare-form prohibition being enforced.
