#!/usr/bin/env python3
"""Rename a math symbol across markdown files, safely.

A symbol rename looks like a find-replace and is not.  Four hazards, all
measured in this repo -- 1-3 on 2026-08-10 (`P` -> `N_p` across Appendix B and
its parent survey), 4 on 2026-08-11 (`\\Delta` -> `\\Delta k`, same appendix):

  1. SUB/SUPERSCRIPT BRACES.  `\\mathbb{C}^P` must become `\\mathbb{C}^{N_p}`,
     never `\\mathbb{C}^N_p` -- which renders cleanly and means something
     else.  Same for `_P` -> `_{N_p}`.  This tool braces automatically
     whenever the match is directly preceded by `^` or `_` and the
     replacement is more than one character.

  2. TOKEN BOUNDARIES, AND GETTING THEM WRONG.  A bare `P` must not match
     `P_l` (a different quantity) or `PDSCH` (prose).  The hand-written
     lookbehind on the first attempt also excluded `{`, which silently left
     HALF-renamed artifacts -- `\\mathbb{C}^{P\\times N_p}`,
     `\\frac{P\\gamma}{1 + N_p\\gamma}`.  They render fine and are simply
     wrong.  Hence: the boundary rule lives here, once, and `--apply`
     always re-scans afterwards and reports residuals.

  3. THE SAME LETTER MEANING SOMETHING ELSE.  The dry run of that rename
     surfaced `P^{-}(n)` in a Kalman recursion -- a predicted error
     covariance, not a pilot count.  This is why the dry run is the
     DEFAULT and `--apply` is opt-in: you are meant to read the proposed
     changes and skip the ones that are a different symbol
     (`--skip-line FILE:N`).

  4. A MACRO IS NOT ATOMIC -- IT COMPOSES.  Measured 2026-08-11 renaming the
     subcarrier lag `\\Delta` -> `\\Delta k` in Appendix B.  In LaTeX a macro
     ends at a non-letter, so `\\Delta f` (subcarrier spacing) and `\\Delta l`
     (symbol lag) are literally the macro `\\Delta` plus a space plus a
     letter, and the hazard-2 guard `(?![A-Za-z])` HAPPILY MATCHES THEM --
     the dry run proposed `\\Delta f` -> `\\Delta k f` and `\\Delta l` ->
     `\\Delta k l`, corrupting two unrelated quantities.  A `--skip-line`
     cannot save this one: the same lines carry both the lag and the
     spacing (`e^{-j2\\pi\\Delta\\,\\Delta f\\,\\tau}`).  Pass
     `--exclude-composed` when the macro forms compound symbols this way.
     The docstring used to claim "a macro rename needs no boundary
     guessing"; that was false, and the dry run is what caught it.

Scope is math spans only (inline `$...$` and `$$` display blocks) unless
`--all-text` is passed, so prose words are never touched.

Usage:
  # dry run (default) -- read every proposed change before applying
  python viewer/tools/rename-symbol.py surveys/foo/*.md --from P --to N_p

  # apply, skipping a line where the letter means something else
  python viewer/tools/rename-symbol.py surveys/foo/bar.md \\
      --from P --to N_p --skip-line surveys/foo/bar.md:179 --apply

  # a macro whose name is the whole symbol needs no boundary guessing
  python viewer/tools/rename-symbol.py surveys/foo/*.md \\
      --from '\\rho_H' --to '\\mathring{R}_H' --apply

  # a macro that COMPOSES (\\Delta f, \\Delta l) must protect those forms
  python viewer/tools/rename-symbol.py surveys/foo/*.md \\
      --from '\\Delta' --to '\\Delta k' --exclude-composed --apply

After `--apply`, run the usual sweep: lint-math, renumber-*, validate-refs,
and `verify-katex-render.cjs` (the only gate that proves the result RENDERS
-- a brace slip is invisible to every static check).
"""

import argparse
import io
import re
import sys
from pathlib import Path

DISPLAY_DELIM = '$$'
INLINE_RE = re.compile(r'\$[^$\n]+\$')


def build_pattern(old, exclude_composed=False):
    """Token-boundary pattern for `old`.

    A macro (`\\rho`) ends at any non-letter, so only a trailing guard is
    needed.  A bare token (`P`) needs both: not preceded by a letter or a
    backslash, and not followed by a letter or `_`.  `{` is deliberately
    NOT in the lookbehind -- excluding it is what produced the half-renamed
    artifacts described in the module docstring.

    `exclude_composed` additionally refuses a macro match that is followed by
    optional whitespace and a letter, so `\\Delta f` / `\\Delta l` survive a
    `\\Delta` rename.  See hazard 4.
    """
    if old.startswith('\\'):
        tail = r'(?![A-Za-z])(?!\s*[A-Za-z])' if exclude_composed else r'(?![A-Za-z])'
        return re.compile(re.escape(old) + tail)
    return re.compile(r'(?<![A-Za-z\\])' + re.escape(old) + r'(?![A-Za-z_])')


def rewrite_span(span, pattern, new):
    """Replace inside one math span, bracing sub/superscripts."""
    out, last = [], 0
    for m in pattern.finditer(span):
        out.append(span[last:m.start()])
        prev = span[m.start() - 1] if m.start() > 0 else ''
        if prev in ('^', '_') and len(new) > 1:
            out.append('{' + new + '}')
        else:
            out.append(new)
        last = m.end()
    out.append(span[last:])
    return ''.join(out)


def rewrite_line(line, pattern, new, in_display, all_text):
    if all_text or in_display:
        return rewrite_span(line, pattern, new)
    return INLINE_RE.sub(lambda m: rewrite_span(m.group(0), pattern, new), line)


def process(path, pattern, new, skip_lines, all_text, apply_changes):
    """Return (changed_line_count, list of (lineno, before, after))."""
    text = io.open(path, encoding='utf-8').read()
    lines = text.split('\n')
    out, in_display, changes = [], False, []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # A lone `$$` toggles display mode; a complete one-line `$$...$$`
        # does not (it opens and closes on the same line).
        if stripped == DISPLAY_DELIM:
            in_display = not in_display
            out.append(line)
            continue
        if i in skip_lines:
            out.append(line)
            continue

        one_line_display = (stripped.startswith(DISPLAY_DELIM)
                            and stripped.endswith(DISPLAY_DELIM)
                            and len(stripped) > 4)
        new_line = rewrite_line(line, pattern, new,
                                in_display or one_line_display, all_text)
        if new_line != line:
            changes.append((i, line, new_line))
        out.append(new_line)

    if apply_changes and changes:
        io.open(path, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    return changes


def residuals(path, pattern, all_text):
    """Occurrences still present after a rewrite -- the post-apply check."""
    lines = io.open(path, encoding='utf-8').read().split('\n')
    in_display, found = False, []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == DISPLAY_DELIM:
            in_display = not in_display
            continue
        spans = ([line] if (all_text or in_display)
                 else INLINE_RE.findall(line))
        for span in spans:
            if pattern.search(span):
                found.append((i, span[:90]))
    return found


def excerpt(line, pattern, width=34):
    m = pattern.search(line)
    if not m:
        return line[:80]
    a, b = max(0, m.start() - width), min(len(line), m.end() + width)
    return ('...' if a else '') + line[a:b] + ('...' if b < len(line) else '')


def main():
    ap = argparse.ArgumentParser(
        description='Rename a math symbol across markdown files (dry run by '
                    'default).')
    ap.add_argument('files', nargs='+', help='markdown files to rewrite')
    ap.add_argument('--from', dest='old', required=True,
                    help='symbol to replace, e.g. P or \\rho_H')
    ap.add_argument('--to', dest='new', required=True,
                    help='replacement, e.g. N_p or \\mathring{R}_H')
    ap.add_argument('--apply', action='store_true',
                    help='write the changes (default is a dry run)')
    ap.add_argument('--skip-line', action='append', default=[],
                    metavar='FILE:N',
                    help='leave this line alone -- the symbol means '
                         'something else there; repeatable')
    ap.add_argument('--all-text', action='store_true',
                    help='also rewrite outside math spans (default: math only)')
    ap.add_argument('--exclude-composed', action='store_true',
                    help='for a macro, do NOT match when it is followed by '
                         'whitespace + a letter -- protects compound symbols '
                         r'like \Delta f / \Delta l during a \Delta '
                         'rename (hazard 4)')
    args = ap.parse_args()

    skip = {}
    for entry in args.skip_line:
        file_part, _, line_part = entry.rpartition(':')
        if not file_part or not line_part.isdigit():
            print(f'ERROR: --skip-line expects FILE:N, got {entry!r}',
                  file=sys.stderr)
            return 2
        skip.setdefault(str(Path(file_part)), set()).add(int(line_part))

    pattern = build_pattern(args.old, args.exclude_composed)
    total = 0

    for name in args.files:
        path = Path(name)
        if not path.is_file():
            print(f'ERROR: {name} is not a file', file=sys.stderr)
            return 2
        skipped = skip.get(str(path), set())
        changes = process(path, pattern, args.new, skipped,
                          args.all_text, args.apply)
        total += len(changes)
        verb = 'rewrote' if args.apply else 'would rewrite'
        note = f' (skipping {sorted(skipped)})' if skipped else ''
        print(f'{path}: {verb} {len(changes)} line(s){note}')
        for lineno, before, after in changes:
            print(f'  {lineno}:')
            print(f'    -  {excerpt(before, pattern)}')
            print(f'    +  {after[:160]}')

        if args.apply:
            left = [(n, s) for n, s in residuals(path, pattern, args.all_text)
                    if n not in skipped]
            if left:
                print(f'  !! {len(left)} residual occurrence(s) of '
                      f'{args.old!r} remain:')
                for lineno, span in left:
                    print(f'     {lineno}: {span}')
            else:
                print(f'  post-scan: 0 residual {args.old!r}')

    if not args.apply:
        print(f'\nDRY RUN -- {total} line(s) would change. Read the diff above; '
              'any line where the symbol means something ELSE needs '
              '--skip-line FILE:N. Re-run with --apply to write.')
    else:
        print(f'\nApplied to {total} line(s). Now run: lint-math, '
              'renumber-{sections,paragraphs,equations} --check, validate-refs, '
              'and verify-katex-render.cjs (the only gate that proves a brace '
              'slip did not survive).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
