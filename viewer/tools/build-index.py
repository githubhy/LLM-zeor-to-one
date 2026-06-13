#!/usr/bin/env python3
"""Build a section index for large markdown survey files.

Scans ## and ### headings (skipping code blocks) and writes a companion
<filename>.index.md mapping section headings to line ranges.

Usage:
  python viewer/tools/build-index.py surveys/ntn-survey.md
  python viewer/tools/build-index.py surveys/              # all .md in dir
  python viewer/tools/build-index.py surveys/ --min-lines 500
  python viewer/tools/build-index.py surveys/ntn-survey.md --dry-run
"""
import argparse
import re
import sys
from pathlib import Path

# ── Heading patterns (reused from split-markdown.py) ─────────────────────────
HEADING_RE = {
    2: re.compile(r'^##\s+(.+)$'),
    3: re.compile(r'^###\s+(.+)$'),
}


def parse_headings(lines, levels=(2, 3)):
    """Find all headings at the given levels, skipping fenced code blocks.

    Returns [(line_idx, level, heading_text), ...] in document order.
    """
    headings = []
    in_code_block = False
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        for lvl in levels:
            m = HEADING_RE[lvl].match(stripped)
            if m:
                headings.append((i, lvl, m.group(1).strip()))
                break
    return headings


def build_section_numbers(headings):
    """Assign hierarchical section numbers (e.g. 1, 1.1, 2, 2.1).

    Returns a list of label strings parallel to headings.
    """
    labels = []
    h2_count = 0
    h3_count = 0
    for _, lvl, _ in headings:
        if lvl == 2:
            h2_count += 1
            h3_count = 0
            labels.append(str(h2_count))
        else:
            h3_count += 1
            labels.append(f"{h2_count}.{h3_count}")
    return labels


def build_index(filepath):
    """Build the index content for a single markdown file.

    Returns (index_text, line_count) or (None, line_count) if no headings.
    """
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')
    total = len(lines)

    headings = parse_headings(lines)
    if not headings:
        return None, total

    labels = build_section_numbers(headings)

    # Compute line ranges: each heading runs until the next heading (or EOF)
    ranges = []
    for idx, (line_idx, lvl, text_h) in enumerate(headings):
        start = line_idx + 1  # 1-based
        if idx + 1 < len(headings):
            end = headings[idx + 1][0]  # line before next heading, 1-based
        else:
            end = total
        ranges.append((start, end))

    # Format index
    name = filepath.name
    out = []
    out.append(f"# {name} — Section Index")
    out.append(f"# Auto-generated. Re-run: python viewer/tools/build-index.py {filepath}")
    out.append("")
    for (label, (line_idx, lvl, text_h), (start, end)) in zip(labels, headings, ranges):
        prefix = "##" if lvl == 2 else "###"
        out.append(f"{prefix} {label} {text_h}: {start}\u2013{end}")

    return '\n'.join(out) + '\n', total


def process_file(filepath, dry_run=False):
    """Build and optionally write the index for one file. Returns True on success."""
    index_text, _ = build_index(filepath)
    if index_text is None:
        print(f"  skip (no headings): {filepath.name}", file=sys.stderr)
        return False

    if dry_run:
        print(index_text, end='')
        return True

    out_path = filepath.parent / f"{filepath.stem}.index.md"
    out_path.write_text(index_text, encoding='utf-8')
    print(f"  wrote: {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', help='Markdown file or directory to index')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print index to stdout without writing files')
    parser.add_argument('--min-lines', type=int, default=1000,
                        help='Only index files over this many lines (default: 1000)')
    args = parser.parse_args()

    target = Path(args.path).resolve()

    if target.is_dir():
        md_files = sorted(target.glob('*.md'))
        if not md_files:
            print(f"No .md files found in {target}", file=sys.stderr)
            sys.exit(1)
    elif target.is_file():
        md_files = [target]
    else:
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for fp in md_files:
        # Skip index files themselves
        if fp.name.endswith('.index.md'):
            continue
        text = fp.read_text(encoding='utf-8')
        line_count = len(text.split('\n'))
        if line_count < args.min_lines:
            continue
        print(f"{fp.name} ({line_count} lines)")
        if process_file(fp, dry_run=args.dry_run):
            count += 1

    if count == 0:
        print("No files met the indexing threshold "
              f"(--min-lines {args.min_lines}).", file=sys.stderr)
        sys.exit(1)
    else:
        action = "printed" if args.dry_run else "indexed"
        print(f"\n{action} {count} file(s).")


if __name__ == '__main__':
    main()
