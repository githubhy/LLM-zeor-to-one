---
id: 2026-08-15-04
title: A section reference written `§ 2.3` (space after the glyph) is invisible to the bare-ref gate
severity: med
status: fixed
date: 2026-08-15
component: viewer/tools/validate-refs.py (check #12), viewer/tools/renumber-sections.py (--init)
---

## Symptom

`validate-refs.py --bare-refs-only --severity=error surveys/` reported **clean** while
**59 dead, non-clickable section cross-references** sat in delivered survey files. The
references render as literal text — `§ 2.3` — with no link, so a reader cannot navigate
them and no gate complains.

Reproducer (RED before the fix, GREEN after):

```
### <a id="sec-2.3"></a>2.3 Contrastive alignment

The projection described in § 2.3 maps encoder features to token space.
```

`validate-refs.py --bare-refs-only --severity=error` exits **0** on this input before the
fix. Removing the single space makes the same gate exit 1.

Distribution at discovery (delivered files only, `_scratch/` excluded):

| Location | Count |
|---|---|
| `surveys/multimodal-llms` | 57 |
| `surveys/mechanistic-interpretability` | 2 |
| `surveys/llms-for-coding`, `wikis/` | 0 |

A further 31 occurrences live in `surveys/mechanistic-interpretability/_scratch/review-*.md`
— preserved re-derivation artifacts that are in no manifest and are correctly not gated.
The initial corpus grep counted those, which is why the first figure quoted in-session was
90; **59 is the delivered-file number** and the one this bug is about.

## Root cause

`BARE_SEC_RE` required the section number to follow the glyph **immediately**:

```python
BARE_SEC_RE = re.compile(r"§([A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)")
```

There is no `\s*` between `§` and the capture group, so `§ 2.3` simply does not match and
the reference is never considered — not exempted, not warned, **not seen**. This is a
false-green of the same family as `2026-08-15-01`: the gate reports success on a population
it never examined.

Two things made it survive this long. The spaced form is *visually identical* in rendered
prose to the correct form for anyone not looking for a link, and the surrounding marker
discipline in these files is otherwise excellent — so the documents look fully cross-linked
on inspection. `renumber-sections.py --init`, the tool that would have promoted them, keys
on the same narrow shape (`BARE_SEC_PROSE_RE`), so the repair path was blind in exactly the
same way as the detector.

## Fix

Both patterns now tolerate optional **horizontal** whitespace after the glyph:

- `validate-refs.py::BARE_SEC_RE` — `§[ \t]*(...)`, so check #12 sees the spaced form.
- `validate-refs.py::SEC_LINKED_RE` — the same tolerance. Required, not cosmetic: widening
  only the bare pattern would newly mis-flag a correctly-marked `[§ 2.3](#sec-2.3)` as bare,
  turning one silent hole into a loud false positive.
- `renumber-sections.py::BARE_SEC_PROSE_RE` — the same tolerance, so `--init` can *promote*
  what the gate now flags. Without this the error message ("use renumber-sections.py --init")
  would name a tool that cannot clear it. The full-span replacement consumes the space, so
  the emitted form is canonical and idempotent.

`[ \t]` rather than `\s`: the check runs per line, and a newline must never join two
unrelated references across a line break.

The 59 delivered references were then de-spaced and promoted through
`renumber-sections.py --init` (never by hand — hand-written markers are the doubled-marker
trap). Result: `surveys/multimodal-llms` went from 172 to 211 valid `.md` links, all
resolving; corpus-wide bare-refs at `--severity=error` is clean over both `surveys/` and
`wikis/`.

Two genuinely-bare refs surfaced once the spaced ones were promoted, and both were fixed
rather than suppressed:

- `mechanistic-interpretability/method-inventory-steering-editing.md` — a `§12.2` inside an
  inline-code `n/a (...)` span. Fixed by the idiom the sibling bullet in the same file
  already used: close the code span, place the marked link outside, reopen.
- `wikis/mechanistic-interpretability-coverage-gaps.md` — `§C.10` / `§A.22` pointing into
  `surveys/llms-for-coding`. That file bracket-wraps 23 such refs and had left exactly these
  2 unwrapped, so this was a consistency slip; fixed to match the file's own idiom.

## Regression test

`viewer/tools/test_validate_refs.py` — 4 new tests: the digit-first spaced form fires, the
letter-dot spaced form fires, a spaced-**but-linked** ref does **not** fire (the guard on the
widening), and the bracket-wrap opt-out still exempts. The first two were confirmed RED
against the pre-fix code before the pattern was touched.

`viewer/tools/test_renumber_sections.py` — 2 new tests: `--init` promotes the spaced form to
the canonical marked + linked shape with the space consumed, and re-running `--init` is
idempotent (no doubled marker).

Full tool suite: 329 passed.

## A second, independent gate hole found alongside (not fixed here)

`.githooks/pre-push` runs the bare-ref check over **`surveys/` only**:

```
$PY viewer/tools/validate-refs.py --bare-refs-only --severity=error surveys/ || fail=1
```

`wikis/` is never bare-ref-checked, which is why the two wiki refs above could sit at error
severity without ever blocking a push. That is a **scope** hole, orthogonal to this regex
hole — widening the pattern does nothing for a directory the gate does not scan. `wikis/` is
in the cross-link corpus group and is scanned by `renumber-sections --check surveys/ wikis/`,
so the omission looks like an oversight rather than a decision. Not changed in this pass
because adding a directory to the push gate deserves its own verification that the whole
corpus clears it first; `wikis/` does currently clear it (verified above).
Tracked in `todos/2026-08-15-prepush-bare-ref-scope.md`.

## Refs

- Found during the `multimodal-llms` max-mode expansion pass, Phase-1 measurement.
- Same false-green family as `bugs/2026-08-15-01` (a gate reporting success over a
  population it never examined).
- `.claude/rules/math-authoring.md` — the bare-form prohibition this gate enforces, and the
  bracket-wrap opt-out used for the wiki fix.
- `.claude/rules/cross-linking.md` — why a `secxref` is illegal in `wikis/` (no `order.json`).
