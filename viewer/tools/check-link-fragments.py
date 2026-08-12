#!/usr/bin/env python3
"""Resolve every internal link's `#fragment`, not just its target file.

`validate-refs.py` checks that a markdown link's target FILE exists and never
inspects the fragment, so `[foo](bar.md#sec-9.9.9)` passes as long as `bar.md`
exists -- whatever the anchor.  Every dangling in-document link is invisible to it.

The repo has been closing this one anchor family at a time -- `#ref-N` via
`link-references.py --check`, `#eq-N` via `renumber-equations.py --check`,
`#sec-X.Y` via `renumber-sections.py --check`, `#p-...` via
`renumber-paragraphs.py --check`.  Four tools, four `--check` modes, and none of
them catches a hand-written link to an anchor no generator owns.  This resolves
all of them in one pass, and catches that residue too.

  Measured when this landed (2026-08-07): 15,302 internal links carry a fragment
  across surveys/ + wikis/; 28 of them (0.183%) do not resolve.

THE ONE THING TO GET RIGHT
--------------------------
Anchors come from two places: explicit `id="..."` attributes, and GitHub-style
heading slugs the viewer generates.  `slugify()` below is a byte-for-byte port of
`viewer/lib/highlight-shared.js::slugify()` -- **do not re-derive it**.

It replaces each whitespace character INDIVIDUALLY with a hyphen and never
collapses consecutive hyphens.  So `## 11 - Numerical verification` (em-dash)
strips the dash, leaves two adjacent spaces, and yields
`11--numerical-verification` -- a DOUBLE hyphen, which is what GitHub emits and
what authors write in their hrefs.

That is not a detail.  Re-deriving this with the natural `\\s+ -> '-'` collapse
reports **119** dangling links instead of 28: 91 phantom defects, concentrated in
the wikis that use em-dash headings.  Resolving only `id=` attributes and ignoring
heading slugs entirely reports **192**.  The viewer's own source carries a comment
recording that an earlier collapsing implementation caused exactly this mismatch
and was fixed.

Usage:
  python viewer/tools/check-link-fragments.py surveys/ wikis/
  python viewer/tools/check-link-fragments.py surveys/ --severity=warn
  python viewer/tools/check-link-fragments.py surveys/llms-for-coding --list-anchors
"""

import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
FENCE = re.compile(r'^(`{3,}|~{3,})')
ID_ATTR = re.compile(r'id="([^"]+)"')
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
SEVERITY_FILE = '.claude/link-fragments-severity'


def slugify(text):
    """Byte-for-byte port of viewer/lib/highlight-shared.js::slugify().

    Each whitespace character becomes its own hyphen (no run collapse) and
    consecutive hyphens are NOT collapsed.  See the module docstring for why this
    matters and what re-deriving it costs.
    """
    t = str(text).lower()
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[^\w\s-]', '', t, flags=re.UNICODE)
    t = t.strip()
    t = re.sub(r'\s', '-', t)
    return re.sub(r'^-+|-+$', '', t)


def unique_slugger():
    """Port of makeUniqueSlugger(): GitHub-compatible `-1`/`-2` de-duplication."""
    used, counts = set(), {}

    def slug(text):
        base = slugify(text)
        n = counts.get(base, 0)
        cand = base
        while cand in used:
            n += 1
            cand = f'{base}-{n}'
        counts[base] = n
        used.add(cand)
        return cand
    return slug


def anchors_of(path):
    """Every fragment that resolves inside `path`: explicit ids + heading slugs."""
    text = path.read_text(encoding='utf-8')
    found = set(ID_ATTR.findall(text))
    slug = unique_slugger()
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            s = slug(m.group(2))
            if s:
                found.add(s)
    return found


def collect(roots):
    files = []
    for r in roots:
        if r.is_file() and r.suffix == '.md':
            files.append(r)
        elif r.is_dir():
            files += [p for p in r.rglob('*.md') if '_scratch' not in p.parts]
    return sorted(set(files))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('targets', type=Path, nargs='+')
    ap.add_argument('--severity', choices=['off', 'warn', 'error'], default=None)
    ap.add_argument('--list-anchors', action='store_true',
                    help='print every resolvable anchor per file and exit')
    args = ap.parse_args()

    severity = args.severity
    if severity is None:
        sev_path = Path(SEVERITY_FILE)
        severity = (sev_path.read_text(encoding='utf-8').strip()
                    if sev_path.exists() else 'warn')
    if severity == 'off':
        print('[link-fragments] off')
        return 0

    files = collect(args.targets)
    if not files:
        print('[link-fragments] ERROR: no markdown files found -- refusing to '
              'report "no dangling fragments" for an empty corpus', file=sys.stderr)
        return 2

    anchors = {p.resolve(): anchors_of(p) for p in files}

    if args.list_anchors:
        for p in files:
            print(f'{p}: {sorted(anchors[p.resolve()])}')
        return 0

    dangling, checked = [], 0
    for p in files:
        in_fence = False
        for lineno, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            if FENCE.match(line.strip()):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LINK.finditer(line):
                url = m.group(1)
                if '#' not in url or url.startswith(('http:', 'https:', 'mailto:')):
                    continue
                rel, frag = url.split('#', 1)
                if not frag:
                    continue
                target = (p.parent / rel).resolve() if rel else p.resolve()
                if target not in anchors:
                    # Missing FILE -- validate-refs.py owns that, and reporting it
                    # here too would double-count one defect in two gates.
                    continue
                checked += 1
                if frag not in anchors[target] and f'user-content-{frag}' not in anchors[target]:
                    dangling.append((p, lineno, frag, target))

    label = 'ERROR' if severity == 'error' else 'WARNING'
    for p, lineno, frag, target in dangling:
        where = 'this file' if target == p.resolve() else Path(target).name
        print(f'{p}:{lineno}: {label}: link fragment #{frag} does not resolve in '
              f'{where}', file=sys.stderr)

    if dangling and severity == 'error':
        print(f'[link-fragments] FAIL: {len(dangling)} dangling of {checked} '
              f'fragment link(s) over {len(files)} file(s)')
        return 1
    print(f'[link-fragments] OK -- {len(files)} file(s), {checked} fragment '
          f'link(s), {len(dangling)} dangling'
          f'{" (reported, not gated)" if dangling else ""}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
