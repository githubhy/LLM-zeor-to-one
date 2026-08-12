#!/usr/bin/env python3
"""Flag same-file `ref:` markers whose equation lives in a SIBLING file.

The equation cross-reference system has two marker kinds:

    <!-- ref:ID -->[(N)](#eq-N)                    same file
    [(N)](other.md#eq-N) <!-- xref:ID -->          another file of the same survey

Only `xref:` is propagated.  `propagate_xrefs()` in ``renumber-equations.py`` keys
strictly on `xref:` when it rewrites sibling links after a renumber, and the orphan
check fires only on an ID absent from the file it *tried* to link.  So a cross-file
reference that is marked `ref:` but already carries a correct link sits in a blind
spot: not an orphan, not propagated.  The next time the owning file renumbers, the
link keeps pointing at the old number and nothing says so.

That blind spot is what this checks.  It is a **marker-kind** error, not a
link-correctness error -- the link may well be right today, and that is precisely
why no existing gate reports it.

Measured when this landed (2026-08-07): 72 occurrences across 8 split surveys, none
of which any gate had ever reported.  65 were mechanically convertible; see
``--explain`` for the 7 that are not and why.

Usage:
  python viewer/tools/check-crossfile-ref-markers.py surveys/
  python viewer/tools/check-crossfile-ref-markers.py surveys/multimodal-llms
  python viewer/tools/check-crossfile-ref-markers.py surveys/ --severity=warn
  python viewer/tools/check-crossfile-ref-markers.py --explain
"""

import argparse
import re
import sys
from pathlib import Path

EQ_MARKER = re.compile(r'<!--\s*eq:([^\s>]+?)\s*-->')
REF_MARKER = re.compile(r'<!--\s*ref:([\w.\-/:]+)\s*-->')
FENCE = re.compile(r'^(`{3,}|~{3,})')

# A ref: marker followed by a link whose anchor is the generator's own numeric
# form.  These are the mechanically convertible ones: swapping the marker to
# `xref:` and moving it after the link is safe, because propagate_xrefs will then
# rewrite both the visible number and the `#eq-N` anchor together.
CONVERTIBLE = re.compile(
    r'<!--\s*ref:([\w.\-/:]+)\s*-->\s*\[[^\]]*?\(\d+\)\]\([^)]+\.md#eq-\d+\)'
)

EXPLAIN = """\
Why 7 of the 72 were left as `ref:` when this check landed
==========================================================

They link to a HAND-WRITTEN anchor rather than the generator's `#eq-N`:

    surveys/lte-dl-receiver-vs-nr   -> #eq-10-1
    surveys/mechanistic-interpretability -> #eq-rope-recursion
    surveys/pusch-receiver          -> (same shape)

Those anchors exist and the links resolve today.  Converting them to `xref:` would
make things WORSE, not better: propagate_xrefs rewrites the anchor as `#eq-{new_num}`
along with the visible number, so it would overwrite a stable hand-written anchor
with a numeric one and break the link outright.

So they are a different defect class -- a hand-written anchor outside the numbering
scheme -- and they need either (a) migration onto the generator's anchors, or (b)
propagate_xrefs learning to preserve a non-numeric anchor while updating only the
visible number.  Neither is this check's job.  They stay reported at `warn` and are
excluded from `error` so the gate can be turned on without blocking on them; the
class is tracked in todos/2026-08-02-crossfile-ref-marker-latent-staleness.md.
"""


def scan_survey(survey_dir):
    """Return (convertible, non_convertible) finding lists for one survey dir."""
    files = sorted(survey_dir.glob('*.md'))
    if len(files) < 2:
        return [], []
    owner = {}
    for f in files:
        owner[f.name] = {m.group(1)
                         for m in EQ_MARKER.finditer(f.read_text(encoding='utf-8'))}

    convertible, other = [], []
    for f in files:
        in_fence = False
        for lineno, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if FENCE.match(line.strip()):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in REF_MARKER.finditer(line):
                rid = m.group(1)
                if rid in owner[f.name]:
                    continue                      # same file: `ref:` is correct
                holders = [n for n, ids in owner.items() if rid in ids and n != f.name]
                if not holders:
                    continue                      # orphan: renumber-equations owns it
                hit = (f, lineno, rid, holders[0])
                if any(mm.group(1) == rid for mm in CONVERTIBLE.finditer(line)):
                    convertible.append(hit)
                else:
                    other.append(hit)
    return convertible, other


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target', type=Path, nargs='?',
                    help='surveys/ root, or a single split-survey directory')
    ap.add_argument('--severity', choices=['off', 'warn', 'error'], default='error')
    ap.add_argument('--explain', action='store_true',
                    help='print why some occurrences are deliberately not converted')
    args = ap.parse_args()

    if args.explain:
        print(EXPLAIN)
        return 0
    if args.target is None:
        ap.error('a target directory is required unless --explain is given')
    if args.severity == 'off':
        print('[crossfile-ref-markers] off')
        return 0

    if (args.target / 'order.json').exists() or list(args.target.glob('*.md')):
        dirs = [args.target] if (args.target / 'order.json').exists() else None
    else:
        dirs = None
    if dirs is None:
        dirs = sorted(d for d in args.target.iterdir() if d.is_dir())
        if not dirs:
            dirs = [args.target]

    convertible, other = [], []
    for d in dirs:
        c, o = scan_survey(d)
        convertible += c
        other += o

    for f, ln, rid, own in convertible:
        print(f'{f}:{ln}: ERROR: cross-file equation ref marked `ref:{rid}` but the '
              f'equation is defined in {own} -- use the `xref:` form '
              f'(`[(N)]({own}#eq-N) <!-- xref:{rid} -->`), which is the only one '
              f'propagate_xrefs() keeps in sync', file=sys.stderr)
    for f, ln, rid, own in other:
        print(f'{f}:{ln}: WARNING: cross-file `ref:{rid}` (defined in {own}) with a '
              f'non-generator anchor -- not auto-convertible, see --explain',
              file=sys.stderr)

    n_files = sum(len(list(d.glob("*.md"))) for d in dirs)
    if convertible and args.severity == 'error':
        print(f'[crossfile-ref-markers] FAIL: {len(convertible)} convertible '
              f'occurrence(s), {len(other)} non-convertible, over {n_files} file(s)')
        return 1
    print(f'[crossfile-ref-markers] OK -- {n_files} file(s), '
          f'{len(convertible)} convertible, {len(other)} non-convertible '
          f'(reported, not gated)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
