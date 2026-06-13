#!/usr/bin/env python3
"""Cross-link bibliography references using stable HTML-comment markers.

Each reference entry is marked with <!-- bib:N --> on the preceding line.
In-text citations use <!-- cite:N --> before [[N]](#ref-N) links.

This script:
  1. Scans for <!-- bib:N --> markers and updates <a id="ref-N"> anchors.
  2. Scans for <!-- cite:N --> markers and updates [[N]](#ref-N) links.
  3. Reports orphaned citations and uncited references.

Targets:
  FILE   A single markdown file containing both the references section and
         the citations. Legacy monolithic surveys.
  DIR    A split-survey directory. The script locates the chapter that holds
         the `## References` section (typically `references.md`), treats that
         chapter as the bibliography source, and treats every other chapter
         as a citation source. Citation links in sibling chapters are expected
         to point to `references.md#ref-N`, so the tool rewrites such links
         in place.

Modes:
  (default)  Update existing markers' anchors and links.
  --init     Add markers to existing references and convert bare [N] citations.
  --check    Dry-run: report issues, exit 1 if changes needed.

Usage:
  python viewer/tools/link-references.py FILE
  python viewer/tools/link-references.py DIR
  python viewer/tools/link-references.py FILE --init
  python viewer/tools/link-references.py DIR   --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Patterns ────────────────────────────────────────────────────────────────

BIB_MARKER = re.compile(r'<!--\s*bib:(\d+)\s*-->')
CITE_MARKER_SAMEFILE = re.compile(
    r'(<!--\s*cite:(\d+)\s*-->)\s*'
    r'(?:\[\[(\d+)\]\]\(#ref-\d+\)|\[(\d+)\])'
)
CITE_MARKER_CROSSFILE = re.compile(
    r'(<!--\s*cite:(\d+)\s*-->)\s*'
    r'(?:\[\[(\d+)\]\]\(([^)]+?)#ref-\d+\)|\[(\d+)\])'
)
ANCHOR_PAT = re.compile(r'<a\s+id="ref-(\d+)"></a>')
REF_ENTRY = re.compile(r'^\[(\d{1,2})\]\s')
FENCE = re.compile(r'^(`{3,}|~{3,})')

# --init helpers
COMPOUND_CITE = re.compile(r'\[(\d{1,2}(?:\s*,\s*\d{1,2})+)\]')
BARE_CITE = re.compile(r'(?<!\[)\[(\d{1,2})\](?!\()')


# ── Helpers ─────────────────────────────────────────────────────────────────

def find_refs_section(lines):
    """Return (start, end) line indices bounding the References heading."""
    start = None
    for i, line in enumerate(lines):
        if re.match(r'^##\s.*[Rr]eferences', line):
            start = i
        elif start is not None and re.match(r'^##\s', line) and i > start + 1:
            return start, i
    return (start, len(lines)) if start is not None else (None, None)


def list_md_files(survey_dir):
    """List .md files respecting order.json if present, otherwise sorted."""
    order_file = survey_dir / 'order.json'
    if order_file.exists():
        try:
            ordered = json.loads(order_file.read_text(encoding='utf-8'))
            return [survey_dir / f for f in ordered if (survey_dir / f).exists()]
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(survey_dir.glob('*.md'))


def find_bib_file(survey_dir):
    """Return the .md file under survey_dir whose body contains a References
    heading. Raises SystemExit if zero or more than one candidate is found."""
    candidates = []
    for md_path in list_md_files(survey_dir):
        text = md_path.read_text(encoding='utf-8')
        lines = text.splitlines(keepends=True)
        start, _end = find_refs_section(lines)
        if start is not None:
            candidates.append(md_path)
    if not candidates:
        print(
            f'ERROR: no chapter under {survey_dir} contains a "## References" '
            f'heading',
            file=sys.stderr,
        )
        sys.exit(1)
    if len(candidates) > 1:
        names = ', '.join(p.name for p in candidates)
        print(
            f'ERROR: multiple chapters under {survey_dir} contain a '
            f'"## References" heading: {names}',
            file=sys.stderr,
        )
        sys.exit(1)
    return candidates[0]


# ── Init mode ───────────────────────────────────────────────────────────────

def init_bib_markers(lines, ref_start, ref_end):
    """Insert <!-- bib:N --> + anchor before each [N] reference entry."""
    result = []
    for i, line in enumerate(lines):
        if ref_start <= i < ref_end:
            m = REF_ENTRY.match(line)
            prev = lines[i - 1] if i > 0 else ''
            if m and not BIB_MARKER.search(prev):
                n = m.group(1)
                result.append(f'<a id="ref-{n}"></a><!-- bib:{n} -->\n')
        result.append(line)
    return result


def init_cite_markers(lines, ref_start, ref_end, bib_numbers,
                      link_target=None):
    """Convert bare [N] and compound [N, M] to marked links.

    If link_target is None, citations point to same-file anchors (#ref-N).
    If link_target is a string like "references.md", citations are built as
    `[[N]](link_target#ref-N)` so a split-survey chapter file can link into
    the shared bibliography file.
    """
    result = []
    in_fence = False

    anchor_prefix = f'{link_target}' if link_target else ''

    for i, line in enumerate(lines):
        if FENCE.match(line.rstrip()):
            in_fence = not in_fence

        # Skip code blocks, refs section, lines already marked
        if in_fence or (ref_start is not None and ref_start <= i < ref_end):
            result.append(line)
            continue
        if re.search(r'<!--\s*cite:\d+\s*-->', line):
            result.append(line)
            continue

        # 1. Compound citations  [N, M, ...]
        def _compound(m):
            nums = [x.strip() for x in m.group(1).split(',')]
            if not all(n in bib_numbers for n in nums):
                return m.group(0)
            return ', '.join(
                f'<!-- cite:{n} -->[[{n}]]({anchor_prefix}#ref-{n})'
                for n in nums
            )
        line = COMPOUND_CITE.sub(_compound, line)

        # 2. Remaining bare [N]
        def _bare(m):
            n = m.group(1)
            if n not in bib_numbers:
                return m.group(0)
            return f'<!-- cite:{n} -->[[{n}]]({anchor_prefix}#ref-{n})'
        line = BARE_CITE.sub(_bare, line)

        result.append(line)
    return result


# ── Update mode ─────────────────────────────────────────────────────────────

def update_bib_anchors(lines):
    """Ensure each <!-- bib:N --> line has a correct <a id="ref-N"> anchor."""
    changed = False
    for i, line in enumerate(lines):
        m = BIB_MARKER.search(line)
        if not m:
            continue
        n = m.group(1)
        anchor = f'<a id="ref-{n}"></a>'
        if anchor in line:
            continue
        clean = ANCHOR_PAT.sub('', line).strip()
        lines[i] = f'{anchor}{clean}\n'
        changed = True
    return changed


def update_cite_links_samefile(lines):
    """Ensure each <!-- cite:N --> is followed by [[N]](#ref-N)."""
    changed = False
    for i, line in enumerate(lines):
        def _fix(m):
            nonlocal changed
            marker, n = m.group(1), m.group(2)
            expected = f'{marker} [[{n}]](#ref-{n})'
            if m.group(0).strip() != expected.strip():
                changed = True
                return expected
            return m.group(0)
        lines[i] = CITE_MARKER_SAMEFILE.sub(_fix, line)
    return changed


def update_cite_links_crossfile(lines, link_target):
    """Ensure each <!-- cite:N --> is followed by [[N]](link_target#ref-N)."""
    changed = False
    for i, line in enumerate(lines):
        def _fix(m):
            nonlocal changed
            marker, n = m.group(1), m.group(2)
            expected = f'{marker} [[{n}]]({link_target}#ref-{n})'
            if m.group(0).strip() != expected.strip():
                changed = True
                return expected
            return m.group(0)
        lines[i] = CITE_MARKER_CROSSFILE.sub(_fix, line)
    return changed


# ── Diagnostics ─────────────────────────────────────────────────────────────

def collect_markers(files_lines):
    """files_lines: list of (label, lines). Returns (bibs, cites_by_file)."""
    bibs = set()
    cites = {}
    for label, lines in files_lines:
        file_cites = set()
        for line in lines:
            for m in BIB_MARKER.finditer(line):
                bibs.add(m.group(1))
            for m in re.finditer(r'<!--\s*cite:(\d+)\s*-->', line):
                file_cites.add(m.group(1))
        cites[label] = file_cites
    return bibs, cites


def report(files_lines):
    bibs, cites_by_file = collect_markers(files_lines)
    all_cites = set().union(*cites_by_file.values()) if cites_by_file else set()

    orphans = sorted(all_cites - bibs, key=int)
    uncited = sorted(bibs - all_cites, key=int)
    if orphans:
        print(f'WARNING  orphaned citations (no bib): {orphans}',
              file=sys.stderr)
    if uncited:
        print(f'WARNING  uncited references: {uncited}', file=sys.stderr)
    return orphans, uncited


# ── Run modes ───────────────────────────────────────────────────────────────

def run_single_file(path, do_init, do_check):
    text = path.read_text(encoding='utf-8')
    original = text
    lines = text.splitlines(keepends=True)

    ref_start, ref_end = find_refs_section(lines)
    if ref_start is None:
        print('ERROR: references section not found', file=sys.stderr)
        sys.exit(1)

    if do_init:
        bib_numbers = set()
        for i in range(ref_start, ref_end):
            m = REF_ENTRY.match(lines[i])
            if m:
                bib_numbers.add(m.group(1))
        print(f'Found {len(bib_numbers)} reference entries.')

        lines = init_bib_markers(lines, ref_start, ref_end)
        ref_start, ref_end = find_refs_section(lines)
        lines = init_cite_markers(lines, ref_start, ref_end, bib_numbers)

    update_bib_anchors(lines)
    update_cite_links_samefile(lines)
    report([(path.name, lines)])

    result = ''.join(lines)
    changed = result != original
    return [(path, original, result)], changed


def run_directory(survey_dir, do_init, do_check):
    bib_path = find_bib_file(survey_dir)
    link_target = bib_path.name  # e.g. "references.md"
    md_files = list_md_files(survey_dir)

    # Read every file upfront.
    file_state = []  # list of (path, original_text, lines)
    for md_path in md_files:
        text = md_path.read_text(encoding='utf-8')
        lines = text.splitlines(keepends=True)
        file_state.append((md_path, text, lines))

    # Load bib numbers from the designated references chapter.
    bib_lines = None
    for _path, _orig, lines in file_state:
        if _path == bib_path:
            bib_lines = lines
            break
    ref_start, ref_end = find_refs_section(bib_lines)

    bib_numbers = set()
    if do_init:
        for i in range(ref_start, ref_end):
            m = REF_ENTRY.match(bib_lines[i])
            if m:
                bib_numbers.add(m.group(1))
        print(f'Found {len(bib_numbers)} reference entries in '
              f'{bib_path.name}.')
    else:
        # For non-init mode, bib_numbers is derived from existing bib markers.
        for line in bib_lines:
            for m in BIB_MARKER.finditer(line):
                bib_numbers.add(m.group(1))

    # Apply per-file transformations.
    for idx, (path, _orig, lines) in enumerate(file_state):
        is_bib_file = (path == bib_path)

        if do_init:
            if is_bib_file:
                lines = init_bib_markers(lines, ref_start, ref_end)
                rs, re_ = find_refs_section(lines)
                lines = init_cite_markers(
                    lines, rs, re_, bib_numbers, link_target=None
                )
            else:
                # Chapter file: treat every line as citation-eligible.
                lines = init_cite_markers(
                    lines, 10**9, 10**9, bib_numbers,
                    link_target=link_target,
                )

        if is_bib_file:
            update_bib_anchors(lines)
            update_cite_links_samefile(lines)
        else:
            update_cite_links_crossfile(lines, link_target)

        file_state[idx] = (path, _orig, lines)

    # Reporting across the whole directory.
    report([(p.name, lines) for p, _o, lines in file_state])

    changed_any = False
    plans = []
    for path, original, lines in file_state:
        result = ''.join(lines)
        if result != original:
            changed_any = True
        plans.append((path, original, result))
    return plans, changed_any


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('target', type=Path,
                    help='Markdown file or split-survey directory')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--init', action='store_true')
    args = ap.parse_args()

    if args.target.is_dir():
        plans, changed = run_directory(args.target, args.init, args.check)
    elif args.target.is_file():
        plans, changed = run_single_file(args.target, args.init, args.check)
    else:
        print(f'ERROR: {args.target} is neither a file nor a directory',
              file=sys.stderr)
        sys.exit(1)

    if args.check:
        if changed:
            print('CHECK: file(s) need updates', file=sys.stderr)
            sys.exit(1)
        print('CHECK: up to date')
        sys.exit(0)

    any_written = False
    for path, original, result in plans:
        if result != original:
            path.write_text(result, encoding='utf-8')
            print(f'Updated {path}')
            any_written = True
    if not any_written:
        print('No changes needed.')


if __name__ == '__main__':
    main()
