#!/usr/bin/env python3
"""Lint markdown files for math-formatting rules from CLAUDE.md.

Checks (errors):
  1. Inline math ($...$) must not span multiple lines.
  2. Display-math lines must not start with > * + - # _ ` at column 1.
  3. <!-- ref:... -->, <!-- cite:... -->, <!-- xref:... -->,
     <!-- secref:... -->, or <!-- secxref:... --> must not appear at
     column 1 (CommonMark Type-2 HTML-block consumes the rest of the
     line as raw text, so any inline markdown link / math after the
     `-->` fails to render). The `sec(x)ref` variants share the rule
     because the parser-trigger is `<!--` at column <=3, independent
     of the marker name.
  4. Bare | (pipe) inside inline math in a table row — use \\lvert/\\rvert.
  5. Inline-math `$` must not abut a decimal digit. The viewer's
     markdown-it-texmath@1.0.0 dollars rule rejects an opening `$` whose
     previous char is 0-9 and a closing `$` whose next char is 0-9, so
     fragments like `10$\\degree$`, `$\\pm$200`, `$-$10.2`, `$\\S$3.6`
     render literally. Move the digit inside the math span.
  6. Ordered-list items containing $$...$$ display math must be tight:
     (a) no blank line between a `$$` close and the next `N.` marker
         (else GitHub ends the list and renumbers the next item from 1,
         producing "1. 1. 1." rendering),
     (b) no continuation paragraph after `$$` inside the item if that
         paragraph contains inline `$...$` math (else GitHub fails to
         render the inline math, leaving literal `$x$` in the output),
         and
     (c) no inline `$...$` math in the *opener* of the next list item
         when the previous item ended in a `$$` close — same parser-
         state pollution as (b), but on the next-item line rather than
         the same-item continuation. Symptom: `2. Solve for $E$:`
         renders with `$E$` literal on GitHub. Fix: lift the symbol
         out of the opener (define it in a setup paragraph before the
         list, or rephrase the opener with plain prose).
     All three patterns work on markdown-it (the local viewer) but fail
     on GitHub's stricter CommonMark parser.
  6d. A `$$...$$` display block in *plain prose* (not a list item) whose
      close `$$` is immediately followed by a non-blank, non-`$$` line
      with no blank-line gap. The continuation inherits parser state
      from the math block: every inline `$...$` and reference link in
      it renders as literal source on the local viewer and on GitHub.
      Bug 2026-05-21-03 (appendix-e §E.5.1, §E.5.4 ...). Fix: insert
      a blank line after the `$$` close — reading flow is preserved.
  7. Paragraph anchors (`<a id="p-..."></a>`) and `<!-- para:... -->`
     markers must not appear *inside* `$$...$$` display-math blocks.
     KaTeX renders the literal HTML as math and garbles the equation.
     The pre-2026-04-27 renumber-paragraphs.py could inject these on
     interior lines of multi-line math blocks; the script is now
     fixed but this lint check catches any future recurrence.
  8. Fragile Unicode characters inside `\\text{...}`. KaTeX/MathJax
     map U+00B7 (· MIDDLE DOT) and U+22C5 (⋅ DOT OPERATOR) inside
     text mode to `\\cdotp`, which is a punctuation-form cdot that
     not every renderer resolves. When `\\cdotp` is unrecognised,
     the renderer emits the literal command string into the output:
     source `\\text{W·s}` renders as the literal text `W\\cdotps`
     (the trailing `s` from `\\text{W·s}` gets glued onto the
     unresolved `\\cdotp`). Symptom seen on GitHub-rendered
     tracking-loops.md Eq (63) note row 1, 2026-05-18. Fix: split
     the text segments and place `\\cdot` *outside* `\\text{...}` —
     `\\text{W}\\!\\cdot\\!\\text{s}` (with thin negative spaces
     for tight typography) or `\\mathrm{W\\cdot s}` (math-mode
     upright Roman, the SI-units idiom).

  11. Legacy column-0 `<a id="sec-...">` heading anchor followed by
      `### ` ATX prefix. CommonMark requires `#` at column 0-3 for ATX
      headings, so the leading inline-HTML anchor demotes the line to
      a paragraph with literal `### ` visible in the rendered body. Bug
      2026-05-25-02; fixed by placing the anchor AFTER the ATX prefix
      (`### <a id="sec-X.Y.Z"></a>Title`). The corpus migration landed
      2026-05-25 (Stage 3 of plans/heading-anchor-architecture-2026-05-25.md);
      check #11 now defaults to ON so any regression is caught at edit
      time by the PostToolUse hook.

Checks (warnings):
  9. Display-math blocks ($$...$$) should contain \\tag{N}.

Orphaned equation / citation markers are covered by renumber-equations.py
and link-references.py respectively.

Usage:
  python viewer/tools/lint-math.py surveys/attention-demo/
  python viewer/tools/lint-math.py surveys/
  python viewer/tools/lint-math.py surveys/ --errors-only
"""

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r'^(`{3,}|~{3,})')
# Triggers when the first non-blank, non-list-marker char of a block is `<!--`.
# Covers (a) plain paragraph at column 0-3, and (b) list-item content (bullet
# `- ` / `* ` / `+ ` or ordered `N. `) whose first child is the marker. The
# list-item case is the SAME failure: CommonMark parses the list-item content
# as its own sub-document, so a leading `<!--` starts a Type-2 HTML block
# inside the <li>, swallowing the subsequent markdown link as raw text.
REF_COL1_RE = re.compile(
    r'^ {0,3}(?:[-*+]\s+|\d+\.\s+)?<!--\s*(ref|cite|xref|secref|secxref):'
)
# Legacy column-0 `<a id="sec-...">` heading anchor (the pre-2026-05-25
# convention).  When followed by `### ` (or `####`, etc.) it demotes the
# line to a paragraph in CommonMark — see lint check #11 below.  Bug
# 2026-05-25-02.
LEGACY_SEC_ANCHOR_COL0_RE = re.compile(
    r'^<a\s+id="sec-[^"]+"></a>#{2,6}\s+'
)
TAG_RE = re.compile(r'\\tag\{')
MD_CHARS = set('>*+-#_`')
# Matches bare | inside inline math that is NOT \| \lvert \rvert \mid \vert
BARE_PIPE_RE = re.compile(r'(?<!\\)\|')
SAFE_PIPE_RE = re.compile(r'\\(lvert|rvert|vert|mid|\|)')
TABLE_ROW_RE = re.compile(r'^\s*\|')
# Ordered-list item marker at column 0 (e.g. "1. ", "10. ")
ORDERED_LIST_ITEM_RE = re.compile(r'^\d+\.\s')
# `\text{...}` spans, non-nested (does not handle escaped braces inside).
TEXT_BLOCK_RE = re.compile(r'\\text\{([^{}]*)\}')
# Unicode characters that KaTeX/MathJax map to \cdotp inside text mode
# and then render as the literal command string when unresolved.
FRAGILE_TEXT_CHARS = {
    '·': 'U+00B7 MIDDLE DOT (·)',
    '⋅': 'U+22C5 DOT OPERATOR (⋅)',
}


def lint_file(path, errors_only=False, check_11_enabled=True):
    """Return list of (line_number, level, message) tuples.

    `check_11_enabled` gates the legacy column-0 heading-anchor check.
    Default is ENABLED (the Stage-3 corpus migration of
    `plans/heading-anchor-architecture-2026-05-25.md` landed 2026-05-25,
    so the steady-state corpus is legacy-free).  Pass `--disable-check-11`
    on the CLI to suppress for one-off use; the PostToolUse hook does not
    pass this flag so any regression is caught at edit time.
    """
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    issues = []

    in_fence = False
    in_display = False
    display_start = None
    display_has_tag = False
    inline_open = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # ── U+FFFD replacement character ────────────────────────────
        # The Unicode REPLACEMENT CHARACTER (U+FFFD, rendered as a black
        # diamond "\ufffd") is never legitimate in source markdown: it marks
        # bytes that failed to decode, typically an em-dash or "§" lost
        # during a non-UTF-8 (GBK / CP1252) file write — the same crash
        # class as the Windows code-page write bug.  Such corruptions have
        # reached committed survey corpora before (a silently-replaced
        # em-dash).  Flag every
        # occurrence so the corruption cannot re-enter the corpus.  Runs
        # before the fence/display `continue`s because the byte
        # corruption is context-independent.
        if '\ufffd' in line:
            col = line.index('\ufffd') + 1
            issues.append((i, 'error',
                           f'U+FFFD replacement character at col {col} - '
                           'decoding corruption (a lost em-dash/symbol from a '
                           'non-UTF-8 write); restore the intended character'))

        # ── Fenced code blocks ──────────────────────────────────────
        if not in_display and FENCE_RE.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # ── Fragile Unicode inside \text{...} ───────────────────────
        # KaTeX/MathJax map U+00B7 (·) and U+22C5 (⋅) inside \text to
        # \cdotp, which not every renderer resolves; when unresolved,
        # the literal command string is emitted into the output.
        # Symptom: `\text{W·s}` renders as `W\cdotps` because the `s`
        # after `·` gets glued onto the unresolved `\cdotp` command.
        # Fix: split the text and place \cdot outside \text, or use
        # \mathrm for SI units.  Runs on every non-fenced line —
        # including lines inside display-math blocks — because \text
        # appears in both inline and display contexts.
        for m in TEXT_BLOCK_RE.finditer(line):
            content = m.group(1)
            for char, name in FRAGILE_TEXT_CHARS.items():
                if char in content:
                    col = line.find(char, m.start()) + 1
                    issues.append((i, 'error',
                                   f'fragile Unicode {name} inside '
                                   f'`\\text{{...}}` at col {col} — KaTeX may '
                                   f'render as literal `\\cdotp` text. Use '
                                   f'`\\text{{X}}\\!\\cdot\\!\\text{{Y}}` '
                                   f'(split with `\\cdot` outside `\\text`) '
                                   f'or `\\mathrm{{X\\cdot Y}}` (math-mode '
                                   f'upright Roman, SI-units idiom)'))
                    break  # one report per text block

        # ── Display math boundaries ─────────────────────────────────
        if stripped == '$$':
            if not in_display:
                in_display = True
                display_start = i
                display_has_tag = False
            else:
                if not errors_only and not display_has_tag:
                    issues.append((display_start, 'warning',
                                   'display-math block has no \\tag{N}'))
                in_display = False
            continue

        # ── Inside display math ─────────────────────────────────────
        if in_display:
            if TAG_RE.search(line):
                display_has_tag = True
            if line and line[0] in MD_CHARS:
                issues.append((i, 'error',
                               f'display-math line starts with '
                               f'markdown-significant \'{line[0]}\' at col 1'))
            # Paragraph anchor or marker injected inside a $$...$$ block.
            # The renumber-paragraphs.py script (pre-2026-04-27 fix)
            # could inject `<a id="p-...">` and `<!-- para:... -->` on
            # interior lines of multi-line math blocks because
            # markdown-it-py without texmath parses the math content
            # as paragraphs.  KaTeX then renders the literal HTML as
            # math, garbling the equation (see tracking-loops.md
            # Eqs 5/10/11/49/55 incident).  This check catches the
            # corruption on edit so it cannot reach GitHub.
            if '<a id="p-' in line or '<!-- para:' in line:
                issues.append((i, 'error',
                               'paragraph anchor / `<!-- para: -->` '
                               'marker inside a `$$...$$` display-math '
                               'block; KaTeX renders the literal HTML '
                               'and garbles the equation. Remove the '
                               'marker; renumber-paragraphs.py '
                               'should not inject it here'))
            continue

        # ── ref/cite/xref comment starting an HTML block ───────────
        # CommonMark Type-2 HTML block allows 0–3 leading spaces, so
        # any `<!-- ref:...`, `<!-- cite:...`, or `<!-- xref:...` with
        # up to 3 spaces of indent triggers the same block-parse
        # failure as one at column 1: the subsequent inline markdown
        # link (or math span, or whatever shares that line after the
        # `-->`) renders literally.
        m_refcite = REF_COL1_RE.match(line)
        if m_refcite:
            kind = m_refcite.group(1)
            issues.append((i, 'error',
                           f'<!-- {kind}:... --> starts a line (with <=3 spaces '
                           'indent) - CommonMark will parse as HTML block'))

        # ── Legacy column-0 `<a id="sec-...">` heading anchor ──────
        # (Check #11.)  The pre-2026-05-25 `renumber-sections.py`
        # convention injected the section anchor at column 0 of the
        # heading line: `<a id="sec-D.5"></a>### D.5 Title`.  CommonMark
        # requires `#` at column 0–3 for ATX headings, so the leading
        # inline-HTML anchor demoted the line to a paragraph with literal
        # `### ` visible in the rendered body.  Bug 2026-05-25-02; fixed
        # by moving the anchor after the `### ` ATX prefix.  This check
        # blocks regression once the corpus migration has landed.
        if check_11_enabled and LEGACY_SEC_ANCHOR_COL0_RE.match(line):
            issues.append((i, 'error',
                           '<a id="sec-..."></a> at column 0 followed by '
                           '`### ` ATX heading - CommonMark cannot parse '
                           'as a heading (line renders as paragraph with '
                           'literal `###` visible). Move the anchor to '
                           'IMMEDIATELY AFTER the `### ` prefix: '
                           '`### <a id="sec-X.Y.Z"></a>Title`. '
                           'Run `renumber-sections.py FILE` to auto-migrate'))

        # ── Bare pipe in inline math inside table rows ──────────────
        if TABLE_ROW_RE.match(line):
            for m in re.finditer(r'(?<!\$)\$(?!\$)((?:[^$\\]|\\.)*)\$', line):
                math_content = m.group(1)
                # Remove safe pipe constructs, then check for bare pipes
                stripped_safe = SAFE_PIPE_RE.sub('', math_content)
                if BARE_PIPE_RE.search(stripped_safe):
                    issues.append((i, 'error',
                                   'bare | in inline math inside table row '
                                   '— use \\lvert/\\rvert or \\mid'))

        # ── Inline-$ adjacent to digits (texmath dollars rule) ─────
        # Walk char-by-char on a copy that masks code spans and escaped
        # $ but preserves indices, alternating open/close on each `$`.
        masked = re.sub(r'`[^`]*`', lambda m: ' ' * len(m.group(0)), line)
        state = 'closed'
        j = 0
        while j < len(masked):
            ch = masked[j]
            if ch == '\\' and j + 1 < len(masked) and masked[j + 1] == '$':
                j += 2
                continue
            if ch == '$':
                # Skip $$ pairs (display math, or stray $$ inline)
                if j + 1 < len(masked) and masked[j + 1] == '$':
                    j += 2
                    continue
                prev_c = masked[j - 1] if j > 0 else ''
                next_c = masked[j + 1] if j + 1 < len(masked) else ''
                if state == 'closed':
                    if prev_c.isdigit():
                        issues.append((i, 'error',
                                       f'inline-math opening `$` at col {j+1} '
                                       f'preceded by digit \'{prev_c}\' — '
                                       f'texmath dollars rule rejects this; '
                                       f'move the digit inside the math span'))
                    state = 'open'
                else:
                    if next_c.isdigit():
                        issues.append((i, 'error',
                                       f'inline-math closing `$` at col {j+1} '
                                       f'followed by digit \'{next_c}\' — '
                                       f'texmath dollars rule rejects this; '
                                       f'move the digit inside the math span'))
                    state = 'closed'
            j += 1

        # ── Multi-line inline math ──────────────────────────────────
        clean = re.sub(r'`[^`]*`', '', line)   # strip code spans
        clean = clean.replace('\\$', '')         # strip escaped $
        clean = re.sub(r'\$\$', '', clean)       # strip display-math $$
        dollar_count = clean.count('$')

        if inline_open is not None:
            if dollar_count % 2 == 1:
                issues.append((inline_open, 'error',
                               f'inline math spans lines {inline_open}\u2013{i} '
                               f'\u2014 keep on one line or promote to $$'))
                inline_open = None
        else:
            if dollar_count % 2 == 1:
                inline_open = i

    # Unclosed display math
    if in_display and display_start is not None:
        issues.append((display_start, 'error',
                       f'unclosed display-math block opened at line '
                       f'{display_start}'))

    # Unclosed inline math
    if inline_open is not None:
        issues.append((inline_open, 'error',
                       f'unclosed inline math starting at line {inline_open}'))

    # Ordered-list / display-math restart pattern (GitHub bug)
    issues.extend(check_broken_ordered_list(lines))

    # $$ display block must be followed by a blank line (bug 2026-05-21-03)
    issues.extend(check_display_math_blank_line(lines))

    # Crossing `**`/`==` delimiters (bug 2026-05-20-01)
    issues.extend(check_crossing_highlight_emphasis(lines))

    return issues


def check_broken_ordered_list(lines):
    """Flag two GitHub-specific failure modes for ordered-list items that
    contain `$$...$$` display-math blocks.

    Failure mode 1 — list restart numbering.  `$$` close + blank line +
    next `N.` marker.  GitHub ends the list at the blank line and
    renders the next item as a new list starting at "1".  Symptom:
    source `1. 2. 3. 4.` renders as `1. 1. 1. 1.`.

        1. Thing:
           $$
           eq
           $$
                                  <-- blank line
        2. Next thing.            <-- renders as "1." on GitHub

    Failure mode 2 — inline-math dropout in continuation paragraphs.
    `$$` close + continuation paragraph inside the same list item that
    contains inline `$...$` math.  GitHub fails to render the inline
    math; every `$x$` in the continuation renders as literal text.

        1. Compute X:
           $$
           X = ...
           $$
           where $n$ is the mean motion and $GM_E = 3.986 \times 10^{14}$
                  ^^^^^                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                  both fail to render on GitHub
        2. Next step.

    Failure mode 3 — inline-math dropout in next-item opener.  Same
    parser-state pollution as failure mode 2, but the inline `$...$`
    math sits in the *opener line of the next list item* rather than a
    same-item continuation paragraph.  Source `2. Solve for $E$:`
    immediately after the previous item's `$$` close renders with
    `$E$` literal on GitHub.  Fix: lift the symbol out of the opener
    (define it in a setup paragraph before the list, or rephrase the
    opener with plain prose).

    All three patterns work on markdown-it (local viewer) but fail on
    GitHub's stricter CommonMark implementation.  Fix for all: keep
    list items minimal (only the equation itself in display math),
    and move both same-item continuations and next-item-opener inline
    math outside the list as a standalone paragraph.
    """
    issues = []
    in_fence = False
    in_display = False
    in_ordered_item = False
    in_post_dm_continuation = False   # currently reading post-$$ text in an item
    last_non_blank_closed_dm = False
    prev_line_blank = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip content inside fenced code blocks
        if not in_display and FENCE_RE.match(stripped):
            in_fence = not in_fence
            prev_line_blank = False
            last_non_blank_closed_dm = False
            continue
        if in_fence:
            prev_line_blank = False
            last_non_blank_closed_dm = False
            continue

        # Skip lines inside display-math bodies (between $$ open and $$ close)
        if in_display and stripped != '$$':
            continue

        # Display math boundaries
        if stripped == '$$':
            if in_display:
                in_display = False
                last_non_blank_closed_dm = True
                if in_ordered_item:
                    in_post_dm_continuation = True
            else:
                in_display = True
                last_non_blank_closed_dm = False
            prev_line_blank = False
            continue

        # New ordered-list item marker
        m_oli = ORDERED_LIST_ITEM_RE.match(line)
        if m_oli:
            if in_ordered_item and last_non_blank_closed_dm:
                # Failure mode 1: blank line + this marker after $$
                if prev_line_blank:
                    issues.append((i, 'error',
                                   'ordered-list item preceded by a blank '
                                   'line after a `$$` close in the previous '
                                   'item; GitHub ends the list at the blank '
                                   'line and renders this item as a new list '
                                   'starting at "1" — remove the blank line '
                                   'between the previous `$$` and this '
                                   'marker'))
                # Failure mode 3: inline `$...$` in this opener after $$
                # Count unpaired `$` after stripping `\$` escapes and `$$`.
                cleaned = line.replace('\\$', '')
                cleaned = re.sub(r'\$\$', '', cleaned)
                if cleaned.count('$') >= 2:
                    issues.append((i, 'error',
                                   'inline `$...$` math in list-item opener '
                                   'directly following a `$$` display-math '
                                   'block in the previous item; GitHub fails '
                                   'to render the inline math here — lift '
                                   'the symbol out of the opener (define it '
                                   'in a setup paragraph before the list, '
                                   'or rephrase with plain prose)'))
            in_ordered_item = True
            in_post_dm_continuation = False
            last_non_blank_closed_dm = False
            prev_line_blank = False
            continue

        if not stripped:
            prev_line_blank = True
            # Blank line does NOT reset last_non_blank_closed_dm or
            # in_post_dm_continuation — the "$$ close → blank → content"
            # pattern is exactly what both failure modes require.
            continue

        # Non-blank content inside a post-$$ continuation of a list item.
        # Flag if it contains inline `$...$` math — count unpaired `$`
        # after stripping `\$` escapes and display-math `$$` pairs.
        if in_post_dm_continuation and line.startswith(' '):
            cleaned = line.replace('\\$', '')
            cleaned = re.sub(r'\$\$', '', cleaned)
            if cleaned.count('$') >= 2:
                issues.append((i, 'error',
                               'inline `$...$` math in list-item continuation '
                               'after a `$$` display-math block; GitHub does '
                               'not reliably render inline math in this '
                               'position — move the prose with inline math '
                               'outside the list (as a standalone paragraph '
                               'before or after the list)'))

        # Non-indented non-list content ends the ordered list
        if in_ordered_item and not line.startswith(' '):
            in_ordered_item = False
            in_post_dm_continuation = False

        last_non_blank_closed_dm = False
        prev_line_blank = False

    return issues


def check_display_math_blank_line(lines):
    """Flag a `$$` display-math close immediately followed by a non-blank
    non-`$$` line (no blank-line gap before the continuation).

    Bug 2026-05-21-03.  When a `$$...$$` display block sits mid-paragraph
    with no blank-line gap between the close and the following prose, the
    continuation inherits parser state from the math block: every inline
    `$...$` math span (and reference links) in that continuation renders
    as literal source on the local viewer and on GitHub.  Example failure
    (appendix-e.md ~L799 before the fix):

        $$
        w \\equiv F_{|L_{\\mathrm{MS}}|}(\\beta) = \\Pr(|L_{\\mathrm{MS}}| \\leq \\beta).
        $$
        By construction $w \\in [0, 1)$ for $\\beta < \\infty$, ...
                        ^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^
                        both render as literal `$...$` text

    Fix: insert a blank line after the `$$` close.  Reading flow is
    preserved (`$$ equation $$` then paragraph break then prose reads
    the same as the bug pattern), and the math renders correctly.

    The check is independent of `check_broken_ordered_list`, which
    covers the analogous ordered-list-item case (failure mode 2 of that
    function); this check fires on the plain-paragraph case.
    """
    issues = []
    in_fence = False
    in_display = False

    def _check_after_close(i):
        # `i` is the 1-based line number of the `$$` close. Flag when the
        # following line is non-blank and not another `$$` opener.
        next_line = lines[i] if i < len(lines) else ''
        next_stripped = next_line.strip()
        # OK if EOF, blank, or another display line (a `$$` delimiter or a
        # back-to-back single-line `$$...$$` block — neither is prose, so no
        # parser-state pollution of following inline math).
        if next_stripped and not next_stripped.startswith('$$'):
            issues.append((i, 'error',
                           f'`$$` display-math close at line {i} is '
                           f'immediately followed by non-blank line {i+1} '
                           f'(no blank-line gap) -- inline `$...$` math '
                           f'in the continuation will render as literal '
                           f'source (bug 2026-05-21-03). Insert a blank '
                           f'line after the `$$` close.'))

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not in_display and FENCE_RE.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped == '$$':
            if in_display:
                _check_after_close(i)  # multi-line block: `$$` close on its own line
                in_display = False
            else:
                in_display = True
        elif (not in_display and stripped.startswith('$$')
              and stripped.endswith('$$') and stripped.count('$$') == 2
              and len(stripped) > 4):
            # Single-line `$$ ... $$` block. The `stripped == '$$'` branch
            # above only covers a `$$` delimiter on its own line, so
            # single-line display blocks were never checked for the
            # blank-line-after rule (bug 2026-06-01-03 — same render-failure
            # family as 2026-05-21-03, missed by the original check).
            _check_after_close(i)
    return issues


def _mark_emphasis_crossing_col(line):
    """Return the 1-based column of a `**`/`==` delimiter crossing on `line`,
    or None.

    A *crossing* is a strong-emphasis (`**`) pair and a highlight (`==`) pair
    that INTERLEAVE instead of nest — e.g. `**==c: x.** y==`, where the `**`
    opens before the `==` mark-open and closes *inside* the mark span.
    markdown-it-mark (CommonMark / GitHub) then refuses to form the `<mark>`
    across the strong pair, so the `==` markers render literally
    (bug 2026-05-20-01).

    Code spans and inline / single-line display math are masked first so
    delimiters inside them never count. Only `**` (strong) is checked against
    `==`; single `*`/`_` are flanking-ambiguous in math-heavy prose
    (subscripts, file names) and would false-positive.
    """
    # Mask code spans, then $$...$$, then $...$, so `*`/`=` inside them
    # are not treated as delimiters. Preserve indices (replace with spaces).
    masked = re.sub(r'`[^`]*`', lambda m: ' ' * len(m.group(0)), line)
    masked = re.sub(r'\$\$.+?\$\$', lambda m: ' ' * len(m.group(0)), masked)
    masked = re.sub(r'(?<!\$)\$(?!\$)(?:[^$\\]|\\.)*?\$',
                    lambda m: ' ' * len(m.group(0)), masked)
    masked = masked.replace('\\*', '  ').replace('\\=', '  ')

    eq, star = [], []
    k, n = 0, len(masked)
    while k < n - 1:
        two = masked[k:k + 2]
        if two == '==':
            eq.append(k); k += 2; continue
        if two == '**':
            star.append(k); k += 2; continue
        k += 1
    # Pair delimiters sequentially (open, close); a lone trailing one is dropped.
    eq_pairs = [(eq[i], eq[i + 1]) for i in range(0, len(eq) - 1, 2)]
    star_pairs = [(star[i], star[i + 1]) for i in range(0, len(star) - 1, 2)]
    for a, b in star_pairs:
        for c, d in eq_pairs:
            # Crossing iff exactly one `**` delimiter lies strictly inside the
            # `==` span (a<c<b<d or c<a<d<b). Nested or disjoint -> not flagged.
            if (c < a < d) != (c < b < d):
                return min(a, c) + 1
    return None


def check_crossing_highlight_emphasis(lines):
    """Flag crossing `**`/`==` delimiters (bug 2026-05-20-01).

    Skips fenced-code and `$$...$$` display-math regions. See
    `_mark_emphasis_crossing_col` for the crossing definition and masking.
    """
    issues = []
    in_fence = False
    in_display = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not in_display and FENCE_RE.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped == '$$':
            in_display = not in_display
            continue
        if in_display:
            continue
        col = _mark_emphasis_crossing_col(line)
        if col is not None:
            issues.append((i, 'error',
                           f'crossing `**`/`==` delimiters at col {col} -- a bold '
                           f'pair and a highlight pair interleave (e.g. '
                           f'`**==c: x.** y==`) instead of nesting; '
                           f'markdown-it-mark / CommonMark / GitHub render the '
                           f'`==` markers literally. Nest the highlight OUTSIDE '
                           f'the bold: `==c: **x.** y==` (bug 2026-05-20-01)'))
    return issues


def collect_files(target):
    """Return list of markdown files under target."""
    p = Path(target)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(p.rglob('*.md'))
    print(f'ERROR: {target} is not a file or directory', file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('target', help='Markdown file or directory to lint')
    ap.add_argument('--errors-only', action='store_true',
                    help='Suppress warnings, show only errors')
    ap.add_argument('--disable-check-11', action='store_true',
                    help='Skip check #11 (legacy column-0 heading-anchor). '
                         'Default ON (the steady-state corpus is legacy-free '
                         'after the 2026-05-25 migration); flag exists for '
                         'one-off use on imported third-party markdown.')
    args = ap.parse_args()

    files = collect_files(args.target)
    total_errors = 0
    total_warnings = 0

    for path in files:
        issues = lint_file(
            path,
            errors_only=args.errors_only,
            check_11_enabled=not args.disable_check_11,
        )
        for line_no, level, msg in issues:
            tag = 'ERROR' if level == 'error' else 'WARNING'
            if level == 'error':
                total_errors += 1
            else:
                total_warnings += 1
            print(f'{path}:{line_no}: {tag}: {msg}')

    summary = f'{len(files)} file(s) scanned, {total_errors} error(s)'
    if not args.errors_only:
        summary += f', {total_warnings} warning(s)'
    print(f'\n{summary}')

    if total_errors > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
