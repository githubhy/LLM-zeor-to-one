#!/usr/bin/env python3
"""Renumber display-math equations using stable HTML-comment markers.

Each equation is marked with <!-- eq:STABLE-ID --> on the line before its
opening $$.  Cross-references use <!-- ref:STABLE-ID --> immediately before
the parenthesized number, e.g. Equation <!-- ref:cn-tanh -->[(37)](#eq-37).

Cross-file references use <!-- xref:STABLE-ID --> after the linked number,
e.g. Equation [(37)](appendix-a.md#eq-37) <!-- xref:cn-tanh -->.

This script:
  1. Scans the file for <!-- eq:ID --> markers in document order.
  2. Assigns sequential numbers 1, 2, 3, ...
  3. Updates (or inserts) \\tag{N} inside the $$ block that follows.
  4. Inserts or updates <a id="eq-N"></a> anchors on each marker line.
  5. Scans for <!-- ref:ID --> markers and updates [(N)](#eq-N) links.
  6. Propagates new numbers to <!-- xref:ID --> links in sibling files.
  7. Reports any orphaned refs (ID not found in eq markers).

Usage:
  python viewer/tools/renumber-equations.py FILE [--check]
  python viewer/tools/renumber-equations.py DIR  [--check]

When DIR is given, processes all .md files (respecting order.json if present).
"""
import argparse
import json
import re
import sys
from pathlib import Path

EQ_MARKER = re.compile(r'<!--\s*eq:([\w.\-/]+)\s*-->')
REF_MARKER = re.compile(
    r'(<!--\s*ref:([\w.\-/]+)\s*-->)\s*'
    r'(?:\[\((\d+)\)\]\(#eq-\d+\)|\((\d+)\))'
)
TAG_PAT = re.compile(r'\\tag\{[^}]*\}')
ANCHOR_PAT = re.compile(r'<a\s+id="eq-(\d+)"></a>')
# Cross-file: [(N)](file.md#eq-N) <!-- xref:STABLE-ID -->
XREF_FULL = re.compile(
    r'\[\((\d+)\)\]\(([^)]+\.md)#eq-(\d+)\)\s*<!--\s*xref:([\w.\-/:]+)\s*-->'
)


def parse_equations(lines):
    """Find all <!-- eq:ID --> markers and return list of (line_index, eq_id)."""
    eqs = []
    for i, line in enumerate(lines):
        m = EQ_MARKER.search(line)
        if m:
            eqs.append((i, m.group(1)))
    return eqs


# Highlight wrappers (==color: ... ==) are project-viewer markup that may wrap
# $$ delimiters on the same line.  Strip the leading "==color:" prefix and the
# trailing "==" suffix before doing $$-delimiter detection so that
# `==blue: $$` / `$$==` / `==blue: $$ x $$ ==` parse as opener / closer / single-
# line equation respectively.  See bugs/2026-05-06-01.
HIGHLIGHT_PREFIX = re.compile(r'^==\w+:\s*')
HIGHLIGHT_SUFFIX = re.compile(r'\s*==$')


def _strip_highlight(s):
    s = HIGHLIGHT_PREFIX.sub('', s)
    s = HIGHLIGHT_SUFFIX.sub('', s)
    return s


def find_tag_line(lines, marker_line):
    """Find the line containing \\tag{} in the $$ block after marker_line.

    Returns (line_index, True) if tag found, or (last_content_line, False)
    if no tag exists (so one can be appended).
    """
    dollar = '$$'
    # Find opening $$
    open_line = None
    for i in range(marker_line + 1, min(marker_line + 4, len(lines))):
        if _strip_highlight(lines[i].strip()).startswith(dollar):
            open_line = i
            break
    if open_line is None:
        return None, False

    # Single-line equation?
    open_stripped = _strip_highlight(lines[open_line].strip())
    if open_stripped.endswith(dollar) and len(open_stripped) > 4:
        return open_line, bool(TAG_PAT.search(lines[open_line]))

    # Multi-line: scan until closing $$
    for i in range(open_line + 1, len(lines)):
        if _strip_highlight(lines[i].strip()) == dollar:
            for j in range(open_line, i):
                if TAG_PAT.search(lines[j]):
                    return j, True
            return i - 1, False
    return open_line, False


def propagate_xrefs(target_path, id_to_num, check_only=False):
    """Propagate renumbered equations to <!-- xref:ID --> links in sibling files.

    After renumbering changes equation numbers in the target file, sibling files
    that reference those equations via <!-- xref:ID --> need their link text and
    anchor numbers updated to match.
    """
    target_name = target_path.name
    survey_dir = target_path.parent
    total_changes = 0
    orphans = set()

    for md_file in sorted(survey_dir.glob('*.md')):
        if md_file.resolve() == target_path.resolve():
            continue

        text = md_file.read_text(encoding='utf-8')
        file_changes = 0

        def replacer(m):
            nonlocal file_changes
            link_file = m.group(2)
            xref_id = m.group(4)

            # Only update xrefs pointing to the renumbered file
            if link_file != target_name:
                return m.group(0)

            # Skip cross-survey xrefs (contain ':')
            if ':' in xref_id:
                return m.group(0)

            if xref_id not in id_to_num:
                orphans.add(xref_id)
                return m.group(0)

            new_num = id_to_num[xref_id]['num']
            result = f'[({new_num})]({link_file}#eq-{new_num}) <!-- xref:{xref_id} -->'
            if result != m.group(0):
                file_changes += 1
            return result

        new_text = XREF_FULL.sub(replacer, text)

        if file_changes > 0:
            total_changes += file_changes
            if not check_only:
                md_file.write_text(new_text, encoding='utf-8')
            print(f'  Xref propagation: {md_file.name} — {file_changes} update(s)')

    if orphans:
        print(f'WARNING: {len(orphans)} orphaned xref IDs in sibling files: '
              f'{sorted(orphans)}')
    if total_changes:
        print(f'Xref propagation total: {total_changes} cross-file update(s)')
    else:
        print(f'Xref propagation: no cross-file updates needed')

    return len(orphans) == 0


def renumber(path, check_only=False):
    text = path.read_text(encoding='utf-8')
    sep = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(sep)

    # Step 1: Parse equation markers -> assign sequential numbers
    eqs = parse_equations(lines)
    id_to_num = {}
    for seq, (line_idx, eq_id) in enumerate(eqs, start=1):
        if eq_id in id_to_num:
            print(f'WARNING: duplicate eq ID "{eq_id}" at lines '
                  f'{id_to_num[eq_id]["line"]+1} and {line_idx+1}')
        id_to_num[eq_id] = {'num': seq, 'line': line_idx}

    print(f'Found {len(eqs)} equation markers')

    # Step 2: Update \tag{N} in each equation block
    tag_changes = 0
    for line_idx, eq_id in eqs:
        num = id_to_num[eq_id]['num']
        tag_line, has_tag = find_tag_line(lines, line_idx)
        if tag_line is None:
            print(f'WARNING: no $$ block found after eq:{eq_id} at line {line_idx+1}')
            continue
        if has_tag:
            old = lines[tag_line]
            new = TAG_PAT.sub(f'\\\\tag{{{num}}}', old)
            if old != new:
                lines[tag_line] = new
                tag_changes += 1
        else:
            lines[tag_line] = lines[tag_line].rstrip() + f' \\tag{{{num}}}'
            tag_changes += 1

    # Step 3: Insert or update <a id="eq-N"></a> anchors on marker lines
    anchor_changes = 0
    for line_idx, eq_id in eqs:
        num = id_to_num[eq_id]['num']
        line = lines[line_idx]
        anchor_m = ANCHOR_PAT.search(line)
        new_anchor = f'<a id="eq-{num}"></a>'
        if anchor_m:
            old_anchor = anchor_m.group(0)
            if old_anchor != new_anchor:
                lines[line_idx] = line.replace(old_anchor, new_anchor)
                anchor_changes += 1
        else:
            eq_m = EQ_MARKER.search(line)
            insert_pos = eq_m.start()
            lines[line_idx] = line[:insert_pos] + new_anchor + line[insert_pos:]
            anchor_changes += 1

    # Step 4: Update <!-- ref:ID --> cross-references to linked form [(N)](#eq-N)
    ref_changes = 0
    orphans = set()
    for i, line in enumerate(lines):
        new_line = line
        for m in REF_MARKER.finditer(line):
            ref_comment = m.group(1)
            ref_id = m.group(2)
            if ref_id not in id_to_num:
                orphans.add(ref_id)
                continue
            new_num = str(id_to_num[ref_id]['num'])
            old_str = m.group(0)
            new_str = f'{ref_comment}[({new_num})](#eq-{new_num})'
            if old_str != new_str:
                new_line = new_line.replace(old_str, new_str)
                ref_changes += 1
        lines[i] = new_line

    if orphans:
        print(f'WARNING: {len(orphans)} orphaned ref IDs: {sorted(orphans)}')

    print(f'Tag updates: {tag_changes}, Anchor updates: {anchor_changes}, '
          f'Ref updates: {ref_changes}')

    if not check_only:
        path.write_text(sep.join(lines), encoding='utf-8')
        print(f'Written: {path}')
    else:
        print('(dry run -- no file written)')

    # Verify sequential — only meaningful when every \tag{} in the file is
    # managed by a <!-- eq:ID --> marker.  Partially-adopted files (markers
    # cover only a subset of equations) legitimately have non-sequential tags
    # among the unmanaged equations; requiring global sequentiality in that
    # case would wrongly block --check for mixed files.
    result_text = sep.join(lines)
    tags = re.findall(r'tag\{(\d+)\}', result_text)
    nums = [int(t) for t in tags]
    total_tags = len(nums)
    managed_count = len(eqs)
    if total_tags > 0 and managed_count < total_tags:
        # Partial adoption: skip global sequential check; only orphaned-refs
        # and pending-changes matter.
        seq_ok = True
        print(f'Verification: {total_tags} tags, sequential: skipped '
              f'(partial adoption — {managed_count}/{total_tags} managed)')
    else:
        seq_ok = all(n == i + 1 for i, n in enumerate(nums))
        print(f'Verification: {total_tags} tags, sequential: {seq_ok}')

    # Step 5: Propagate to cross-file xrefs in sibling files
    xref_ok = True
    if id_to_num:
        xref_ok = propagate_xrefs(path, id_to_num, check_only=check_only)

    return seq_ok and len(orphans) == 0 and xref_ok


def list_md_files(directory):
    """List .md files in a directory, respecting order.json if present."""
    order_file = directory / 'order.json'
    if order_file.exists():
        try:
            ordered = json.loads(order_file.read_text(encoding='utf-8'))
            return [directory / f for f in ordered if (directory / f).exists()]
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(directory.glob('*.md'))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', help='Markdown file or directory to process')
    parser.add_argument('--check', action='store_true',
                        help='Dry-run: report changes without writing')
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f'Not found: {target}')
        sys.exit(1)

    if target.is_dir():
        files = list_md_files(target)
        if not files:
            print(f'No .md files found in {target}')
            sys.exit(1)
        all_ok = True
        for f in files:
            print(f'\n--- {f.name} ---')
            if not renumber(f, check_only=args.check):
                all_ok = False
        sys.exit(0 if all_ok else 1)
    else:
        ok = renumber(target, check_only=args.check)
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
