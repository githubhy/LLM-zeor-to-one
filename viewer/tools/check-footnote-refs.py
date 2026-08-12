#!/usr/bin/env python3
"""check-footnote-refs.py -- enforce the viewer's reserved `note-` footnote namespace.

The viewer reserves footnote ids that start with `note-` for **highlight-attached
notes** (the `==highlight==[^note-id]` Tufte-sidenote pattern). Three places key
on the prefix:

    viewer/lib/highlight-shared.js  -- absorbs `note-*` refs flush after a `==...==`
    viewer/viewer.js  (~115-125)    -- injects data-note-id when the label starts `note-`
    viewer/viewer.js  (~596-606)    -- intercepts the click -> scrollSidebarToNoteEntry

So a `note-*` footnote **reference** that is NOT flush after a `==...==` highlight
close gets its click hijacked to a highlights-sidebar row that does not exist --
the markdown footnote and the viewer note-system collide. Ordinary authored
footnotes must use a non-`note-` id (e.g. `fn-...`); citations etc. already do.

This checker flags any inline `[^note-...]` **reference** whose two preceding
characters are not `==`. Footnote *definitions* (`[^id]:` at column 0-3) are not
references and are skipped.

Usage:
    python viewer/tools/check-footnote-refs.py FILE_OR_DIR [FILE_OR_DIR ...]

`--check` is accepted and ignored (the checker is always read-only) for flag
convention parity with the renumber scripts.

Exit code 0 if every `note-*` reference is flush after a `==` highlight close;
1 if any violation is found; 2 on a usage error.
"""
import re
import sys
from pathlib import Path

# A footnote definition is `[^id]:` at the start of a line (<=3 spaces of indent
# per CommonMark). Tolerate a leading para-anchor / HTML-comment prefix
# (`<a id=...></a><!-- para:... --> `) so a renumber-paragraphs-prefixed def
# (the separate paragraph-anchor-prefixed-definition failure mode) is still
# recognised as a definition and not misread as a prose reference. Anything
# else of the form `[^id]` is a reference.
DEF_PREFIX_RE = re.compile(r'^\s*(?:<a\b[^>]*></a>\s*|<!--.*?-->\s*)*\s{0,3}')
DEF_HEAD_RE = re.compile(r'\[\^([^\]\s]+)\]:')
REF_RE = re.compile(r'\[\^([^\]\s]+)\]')


def check_file(path):
    """Return a list of (lineno, col, id, context) violations for one file."""
    viol = []
    text = Path(path).read_text(encoding='utf-8')
    for lineno, line in enumerate(text.splitlines(), 1):
        # Locate a footnote-definition token (possibly behind a para-anchor prefix).
        def_start = None
        pfx = DEF_PREFIX_RE.match(line)
        if pfx:
            head = DEF_HEAD_RE.match(line, pfx.end())
            if head:
                def_start = head.start()
        for m in REF_RE.finditer(line):
            # Skip the definition token itself (the `[^id]` inside `[^id]:`).
            if def_start is not None and m.start() == def_start:
                continue
            fid = m.group(1)
            if not fid.startswith('note-'):
                continue
            preceding = line[max(0, m.start() - 2):m.start()]
            if preceding != '==':
                ctx = line[max(0, m.start() - 12):m.end()]
                viol.append((lineno, m.start() + 1, fid, ctx))
    return viol


def iter_targets(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob('*.md')):
                # skip hidden dirs (.claude, .git worktrees, etc.)
                if any(part.startswith('.') for part in f.parts):
                    continue
                yield f
        elif p.is_file():
            yield p
        else:
            print(f'WARNING: not found: {a}', file=sys.stderr)


def main(argv):
    args = [a for a in argv if a != '--check']
    if not args:
        print('usage: check-footnote-refs.py FILE_OR_DIR [...]', file=sys.stderr)
        return 2
    total = 0
    files = 0
    for path in iter_targets(args):
        files += 1
        for lineno, col, fid, ctx in check_file(path):
            total += 1
            print(f'{path}:{lineno}:{col}: [ERROR] reserved `note-` footnote ref '
                  f'`[^{fid}]` not flush after a `==highlight==` close '
                  f'(use a non-`note-` id for an ordinary footnote) | …{ctx}')
    print(f'{files} file(s) scanned, {total} violation(s).')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
