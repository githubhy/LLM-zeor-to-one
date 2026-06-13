#!/usr/bin/env python3
"""check-citation-sources.py -- enforce the references.md <-> download/ invariant.

Every numbered reference entry in a references file must end with a source
tag declaring where the acquired source is:

    (local: download/<file>)    full text held in the repo
    (spec: docs/specs/<path>)   a standard held in the repo spec mirror
    (web)                       a live web resource (the citation is the page)
    (abstract-only)             full text genuinely not held

See `.claude/rules/citation-integrity.md` for the convention. This checker
flags any untagged reference entry and any `local:` / `spec:` tag whose file
is missing from disk -- an error of the same class as a `lint-math`
violation.

Usage:
    python viewer/tools/check-citation-sources.py FILE [FILE ...]

`--check` is accepted and ignored (the checker is always read-only), so the
tool can be invoked with the same flag convention as the renumber scripts.

Exit code 0 if every entry is tagged and every local:/spec: file exists; 1
if any error is found; 2 on a usage error.
"""
import re
import sys
from pathlib import Path

# repo root: <root>/viewer/tools/check-citation-sources.py -> parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]

# a reference entry is a top-level numbered list item. Two list styles are
# accepted: "12. Author, ..." (plain ordered list) and "[12] Author, ..."
# (bracket-numbered with a preceding <!-- bib:N --> marker).
ENTRY_RE = re.compile(r'^(?:(\d+)\.|\[(\d+)\])\s+(.*\S)\s*$')

# the source tag is the final parenthetical on the entry line
TAG_RE = re.compile(
    r'\((local|spec|web|abstract-only)\b\s*:?\s*([^)]*)\)\s*$'
)

KINDS = ('local', 'spec', 'web', 'abstract-only')


def check_file(path):
    """Return (errors, counts) for one references file.

    errors: list of (lineno, ref-number, message)
    counts: dict kind -> int for the tagged entries
    """
    errors = []
    counts = {k: 0 for k in KINDS}
    text = Path(path).read_text(encoding='utf-8')
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ENTRY_RE.match(line)
        if not m:
            continue
        num, body = (m.group(1) or m.group(2)), m.group(3)
        tag = TAG_RE.search(body)
        if not tag:
            errors.append(
                (lineno, num,
                 'untagged -- no (local:/spec:/web/abstract-only) source tag')
            )
            continue
        kind, arg = tag.group(1), tag.group(2).strip()
        counts[kind] += 1
        if kind in ('local', 'spec'):
            if not arg:
                errors.append((lineno, num, f'{kind}: tag carries no path'))
                continue
            target = (REPO_ROOT / arg).resolve()
            if not target.is_file():
                errors.append(
                    (lineno, num, f'{kind}: file not found: {arg}')
                )
    return errors, counts


def main(argv):
    files = [a for a in argv[1:] if not a.startswith('--')]
    if not files:
        print('usage: check-citation-sources.py FILE [FILE ...]',
              file=sys.stderr)
        return 2

    total_err = 0
    total_entries = 0
    for f in files:
        errors, counts = check_file(f)
        tagged = sum(counts.values())
        n = tagged + len(errors)
        total_entries += n
        total_err += len(errors)
        for lineno, num, msg in errors:
            print(f'{f}:{lineno}: ERROR: [{num}] {msg}')
        strong = counts['local'] + counts['spec']
        weak = counts['web'] + counts['abstract-only']
        print(
            f'{f}: {n} entries -- '
            f'{strong} strong (local {counts["local"]} / spec {counts["spec"]}), '
            f'{weak} weak (web {counts["web"]} / abstract-only {counts["abstract-only"]}), '
            f'{len(errors)} error(s)'
        )

    print(f'\n{len(files)} file(s) scanned, {total_entries} entries, '
          f'{total_err} error(s)')
    return 1 if total_err else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
