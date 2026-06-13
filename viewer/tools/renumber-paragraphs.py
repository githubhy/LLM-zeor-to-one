#!/usr/bin/env python3
"""Renumber paragraph anchors using stable HTML-comment markers.

Every eligible block (paragraph, first paragraph of a top-level list item,
first paragraph of a top-level blockquote) carries an inline marker of the
form:

    <a id="p-SECTION-N"></a><!-- para:SECTION-N --> <content>

SECTION is the slug of the nearest preceding heading; N is a sequential
index that resets at each heading. Mirrors viewer/tools/renumber-equations.py.

Block classification uses markdown-it-py so it matches the markdown-it
token stream the viewer produces in the browser. Display-math paragraphs
(anchored by eq- markers) and fenced code / tables / headings are skipped.

Usage:
  python viewer/tools/renumber-paragraphs.py FILE [--check|--init]
  python viewer/tools/renumber-paragraphs.py DIR  [--check|--init]
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from markdown_it import MarkdownIt
except ImportError:
    print("ERROR: markdown-it-py not installed. Run: pip install markdown-it-py",
          file=sys.stderr)
    sys.exit(2)

PARA_MARKER = re.compile(r'<!--\s*para:([\w.\-/]+)\s*-->')
PARA_ANCHOR = re.compile(r'<a\s+id="p-([\w.\-/]+)"></a>')
EQ_MARKER = re.compile(r'<!--\s*eq:')
DISPLAY_MATH = re.compile(r'^\s*\$\$')
LIST_PREFIX = re.compile(r'^(\s*(?:[-*+]|\d+[.)])\s+)')
BQ_PREFIX = re.compile(r'^(\s*>\s?)')

MD = MarkdownIt('commonmark').enable('table')


def slugify(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-') or 'section'


def heading_text(tokens, idx):
    if idx + 1 >= len(tokens):
        return ''
    inline = tokens[idx + 1]
    if inline.type != 'inline' or not inline.children:
        return inline.content or ''
    return ''.join((c.content or '') for c in inline.children)


def detect_frontmatter(lines):
    """Return (start, end) inclusive line indices to exclude, or None."""
    if not lines or lines[0].strip() != '---':
        return None
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() == '---':
            return (0, i)
    return None


def walk_tokens(tokens):
    """Yield (kind, line, extra) events.

    kind='heading'  → extra=slug
    kind='block'    → extra=block_type in {'paragraph','list_item','blockquote'}
    """
    list_depth = 0
    bq_depth = 0
    pending_first_item = []
    pending_first_bq = []

    for i, t in enumerate(tokens):
        tp = t.type
        if tp == 'heading_open':
            line = t.map[0] if t.map else 0
            yield ('heading', line, slugify(heading_text(tokens, i)))
        elif tp in ('bullet_list_open', 'ordered_list_open'):
            list_depth += 1
            pending_first_item.append(True)
        elif tp in ('bullet_list_close', 'ordered_list_close'):
            list_depth -= 1
            if pending_first_item:
                pending_first_item.pop()
        elif tp == 'blockquote_open':
            bq_depth += 1
            pending_first_bq.append(True)
        elif tp == 'blockquote_close':
            bq_depth -= 1
            if pending_first_bq:
                pending_first_bq.pop()
        elif tp == 'paragraph_open':
            line = t.map[0] if t.map else 0
            if list_depth > 0:
                if (list_depth == 1 and bq_depth == 0
                        and pending_first_item and pending_first_item[-1]):
                    yield ('block', line, 'list_item')
                    pending_first_item[-1] = False
            elif bq_depth > 0:
                if (bq_depth == 1
                        and pending_first_bq and pending_first_bq[-1]):
                    yield ('block', line, 'blockquote')
                    pending_first_bq[-1] = False
            else:
                yield ('block', line, 'paragraph')


def strip_existing_marker(line):
    """Remove an existing `<a id=...></a><!-- para:... --> ` prefix anywhere in the line."""
    out = PARA_ANCHOR.sub('', line, count=1)
    out = PARA_MARKER.sub('', out, count=1)
    # Collapse a leftover leading space that the stripped marker pushed in.
    return out


def inject_prefix(line, kind, new_id):
    prefix = f'<a id="p-{new_id}"></a><!-- para:{new_id} --> '
    if kind == 'paragraph':
        return prefix + line
    if kind == 'list_item':
        m = LIST_PREFIX.match(line)
        if not m:
            return None
        return line[:m.end()] + prefix + line[m.end():]
    if kind == 'blockquote':
        m = BQ_PREFIX.match(line)
        if not m:
            return None
        return line[:m.end()] + prefix + line[m.end():]
    return None


def rewrite_existing(line, new_id):
    """Update the marker + anchor IDs in a line that already has them."""
    def ra(m):
        return f'<a id="p-{new_id}"></a>'
    def rm(m):
        return f'<!-- para:{new_id} -->'
    new_line, nA = PARA_ANCHOR.subn(ra, line, count=1)
    new_line, nM = PARA_MARKER.subn(rm, new_line, count=1)
    if nA == 0 and nM > 0:
        # Marker present but no anchor — inject one immediately before marker.
        new_line = re.sub(
            r'<!-- para:',
            f'<a id="p-{new_id}"></a><!-- para:',
            new_line,
            count=1,
        )
    return new_line


def display_math_line_set(lines):
    """Return the set of line indices (inclusive of both `$$` markers)
    that fall inside a `$$...$$` display-math block.

    Necessary because markdown-it-py with the plain commonmark parser
    does NOT recognise `$$...$$` as math — it tokenises the content
    inside as ordinary paragraphs, whose `t.map[0]` may point to an
    interior line that does *not* start with `$$`. Without this
    pre-pass, the script injects paragraph anchors inside math blocks
    (the bug surfaced 2026-04-27 in tracking-loops.md Eqs 5/10/11/49/55).
    """
    inside = set()
    in_math = False
    start = -1
    for i, line in enumerate(lines):
        if DISPLAY_MATH.match(line):
            stripped = line.strip()
            # Single-line block: `$$ ... $$` opens AND closes on one line.
            # It matches DISPLAY_MATH once but is self-contained, so it must
            # NOT toggle in_math — doing so inverts opener/closer pairing for
            # the rest of the file, making every subsequent paragraph invisible
            # to the script (bug 2026-05-21-05). Only treat it as self-contained
            # when we're not already inside a multi-line block (where a leading
            # `$$` is the closer, handled by the toggle below). `$$$$` (empty)
            # counts as a self-contained block.
            if not in_math and '$$' in stripped[2:]:
                inside.add(i)
                continue
            if in_math:
                for j in range(start, i + 1):
                    inside.add(j)
                in_math = False
            else:
                in_math = True
                start = i
    # Unbalanced opener: include from start to EOF defensively.
    if in_math and start >= 0:
        for j in range(start, len(lines)):
            inside.add(j)
    return inside


def renumber(path: Path, check_only=False, init=False):
    text = path.read_text(encoding='utf-8')
    sep = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(sep)

    frontmatter = detect_frontmatter(lines)
    display_lines = display_math_line_set(lines)

    # Parse with LF-only input so map lines align with our list indices.
    tokens = MD.parse('\n'.join(lines))
    events = list(walk_tokens(tokens))

    # Section counter
    current_slug = 'top'
    section_counter = {}
    assignments = []  # (line_idx, kind, new_id)

    for kind, line, extra in events:
        if frontmatter and frontmatter[0] <= line <= frontmatter[1]:
            continue
        if kind == 'heading':
            current_slug = extra
            continue
        block_type = extra
        # Skip any block whose start line falls inside a $$...$$ region.
        # (DISPLAY_MATH.match only catches the case where t.map[0] is
        # itself the `$$` line; multi-line math blocks have inner-line
        # paragraph tokens that need this set-membership check.)
        if line in display_lines:
            continue
        line_text = lines[line] if 0 <= line < len(lines) else ''
        if DISPLAY_MATH.match(line_text):
            continue
        if EQ_MARKER.search(line_text):
            continue
        n = section_counter.get(current_slug, 0) + 1
        section_counter[current_slug] = n
        new_id = f'{current_slug}-{n}'
        assignments.append((line, block_type, new_id))

    changes = 0
    failures = []
    for line_idx, block_type, new_id in assignments:
        old_line = lines[line_idx]
        has_marker = PARA_MARKER.search(old_line) is not None
        if has_marker:
            new_line = rewrite_existing(old_line, new_id)
        else:
            if not init:
                # Outside --init we don't auto-inject.
                continue
            injected = inject_prefix(old_line, block_type, new_id)
            if injected is None:
                failures.append((line_idx, block_type))
                continue
            new_line = injected
        if new_line != old_line:
            lines[line_idx] = new_line
            changes += 1

    final_text = sep.join(lines)

    # Orphan detection: marker IDs present in file but not in this run's assignments.
    expected = {a[2] for a in assignments}
    found = set(PARA_MARKER.findall(final_text))
    orphans = sorted(found - expected)

    print(f'Eligible blocks: {len(assignments)}')
    print(f'Updates: {changes}')
    if failures:
        print(f'WARNING: {len(failures)} blocks without detectable marker prefix')
    if orphans:
        print(f'WARNING: {len(orphans)} orphaned para IDs: {orphans}')

    if check_only:
        clean = (changes == 0) and not orphans and not failures
        print('(check) clean' if clean else '(check) drift detected')
        return clean

    if changes > 0:
        path.write_text(final_text, encoding='utf-8')
        print(f'Written: {path}')
    else:
        print('No changes.')
    return not orphans and not failures


def list_md_files(directory):
    order_file = directory / 'order.json'
    if order_file.exists():
        try:
            ordered = json.loads(order_file.read_text(encoding='utf-8'))
            return [directory / f for f in ordered if (directory / f).exists()]
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(directory.glob('*.md'))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', help='Markdown file or directory to process')
    parser.add_argument('--check', action='store_true',
                        help='Dry-run: exit non-zero on drift')
    parser.add_argument('--init', action='store_true',
                        help='Insert markers into blocks that lack them')
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f'Not found: {target}', file=sys.stderr)
        sys.exit(1)

    if target.is_dir():
        files = list_md_files(target)
        if not files:
            print(f'No .md files in {target}', file=sys.stderr)
            sys.exit(1)
        all_ok = True
        for f in files:
            print(f'\n--- {f.name} ---')
            if not renumber(f, check_only=args.check, init=args.init):
                all_ok = False
        sys.exit(0 if all_ok else 1)
    else:
        ok = renumber(target, check_only=args.check, init=args.init)
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
