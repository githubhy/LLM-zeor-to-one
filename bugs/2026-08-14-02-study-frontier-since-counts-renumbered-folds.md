---
id: 2026-08-14-02
title: study-frontier --since counts a pre-existing fold as new when only its paragraph anchor was renumbered
severity: med
status: open
date: 2026-08-14
component: viewer/tools/study-frontier.py (--since pulse check)
---

## Symptom

Closing an interrupted `/study` session, the pulse check reported:

```
$ python viewer/tools/study-frontier.py --since 836d2ac
[study-frontier] 1 fold(s) added since 836d2ac:
    surveys/llms-for-coding/appendix-a-qkv-first-principles.md
```

**No fold was added.** The session added zero. The reported fold is one that has existed in
`appendix-a` since an earlier date; what changed is its *paragraph anchor*, rewritten by a
routine `renumber-paragraphs --init` pass during unrelated survey work:

```
$ git diff --numstat 836d2ac -- surveys/llms-for-coding/appendix-a-qkv-first-principles.md
2	2	surveys/llms-for-coding/appendix-a-qkv-first-principles.md
```

Two lines added, two deleted — a rewrite, not an addition. The fold's `> **Note —** …` line
begins with an `<a id="p-…">` anchor, so renumbering changes the line text, and a line-level
diff scan sees a new fold-shaped line.

## Root cause

`--since` detects folds by scanning **added lines** in the diff for the fold pattern, and a
fold's line carries its paragraph anchor inline (per `.claude/rules/math-authoring.md`,
paragraph anchors are injected at the *start of the block's first text line*, which for a
blockquote fold is the same line as the `**Note —**` lead). Any operation that renumbers
paragraph anchors therefore rewrites every fold line in the file, and every one of them
re-appears as an addition.

The detector's unit is the *line*; the fold's identity is the `para:` **id**, which is
exactly the thing renumbering changes.

## Why it matters more than a miscount

The pulse check is the `/study` session's honesty gate — the command's own guardrail is that
**zero folds means the session did not happen**. A detector that inflates the count converts
that guardrail into a rubber stamp, and it inflates it precisely after a normalize/renumber
pass, which is routine survey maintenance. In this instance it would have reported a
productive study session that in fact produced nothing, which is the exact failure the
guardrail exists to prevent. Same false-green family as the grammar-drift bugs recorded in
`viewer/tools/heading_grammar.py`'s module docstring.

## Fix

Not yet applied. The likely fix is to key the comparison on fold **identity** rather than on
line text: extract the set of `para:` ids (or the fold *lead* text) present at the base
commit and at HEAD, and report the set difference. That is robust to anchor renumbering,
to reflowing, and to a fold moving within a file. A cheaper interim mitigation is to compare
the fold-lead text with anchors stripped before diffing.

## Regression test

none yet — should be added with the fix: construct a fixture whose fold line changes only in
its `<a id="p-…">` anchor and assert `--since` reports **zero** new folds. That test fails
against the current implementation, which is what makes it worth writing.

## Refs

- `viewer/tools/study-frontier.py` — the `--since` implementation; `collect_folds` already
  parses `para:`-anchored fold lines, so the identity information needed for the fix is
  already extracted elsewhere in the same file.
- `.claude/commands/study.md` §4 — the pulse check and the zero-folds guardrail it defends.
- `decisions/2026-08-13-02` — the study-session operating model that introduced the check.
- `.claude/rules/math-authoring.md` — Paragraph Anchors, which specifies the inline
  placement that makes fold lines renumber-sensitive.
- Related: `todos/2026-08-14-recall-prompt-is-a-label-not-a-question.md` — the other defect
  found by actually using the study tooling against the real corpus.
