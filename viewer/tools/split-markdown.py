#!/usr/bin/env python3
"""Split a monolithic markdown file into a structured multi-file directory.

Generalizes the one-off surveys/transformer-attention/split.py into a reusable tool.

Usage:
  python viewer/tools/split-markdown.py surveys/big-survey.md
  python viewer/tools/split-markdown.py surveys/big-survey.md --output surveys/big-survey/
  python viewer/tools/split-markdown.py surveys/big-survey.md --dry-run
  python viewer/tools/split-markdown.py surveys/big-survey.md --split-at H3
  python viewer/tools/split-markdown.py surveys/big-survey.md --inventory
  python viewer/tools/split-markdown.py surveys/big-survey.md --config split.config.json
  python viewer/tools/split-markdown.py surveys/big-survey.md --config split.config.json --force
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ── Patterns ──────────────────────────────────────────────────────────────────
EQ_MARKER_RE  = re.compile(r'<!--\s*eq:([\w.\-/]+)\s*-->')
REF_MARKER_RE = re.compile(
    r'(<!--\s*ref:([\w.\-/]+)\s*-->)\s*'
    r'(?:\[\((\d+)\)\]\(#eq-\d+\)|\((\d+)\))'
)
XREF_MARKER_RE = re.compile(r'<!--\s*xref:([\w.\-/:]+)\s*-->')
CITE_MARKER_RE = re.compile(
    r'(<!--\s*cite:(\d+)\s*-->)\s*\[\[(\d+)\]\]\(#ref-(\d+)\)'
)
BIB_MARKER_RE = re.compile(r'<!--\s*bib:(\d+)\s*-->')
IMG_RE = re.compile(r'(!\[[^\]]*\]\()([^)]+)(\))')
HEADING_ANY_RE = re.compile(r'^(#{1,6})\s+(.+)$')
HEADING_RE = {
    2: re.compile(r'^##\s+(.+)$'),
    3: re.compile(r'^###\s+(.+)$'),
}


def slugify(text):
    """Convert heading text to a filename-friendly slug."""
    text = re.sub(r'[*_`\[\]()]', '', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = text.lower().strip('-')
    # Handle appendix naming
    if text.startswith('appendix'):
        parts = text.split('-', 1)
        if len(parts) > 1:
            letter = re.search(r'[a-z]', parts[1])
            if letter:
                return f"appendix-{letter.group(0)}"
        return text
    if text in ('references', 'bibliography', 'works-cited'):
        return 'references'
    return text[:50]  # cap length


def parse_headings(lines, level=2):
    """Find all headings at the given level. Returns [(line_idx, heading_text)]."""
    pat = HEADING_RE[level]
    headings = []
    in_code_block = False
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        m = pat.match(stripped)
        if m:
            headings.append((i, m.group(1).strip()))
    return headings


def parse_all_headings(lines):
    """Find every heading (H1..H6). Returns [(line_idx, level, text)]."""
    headings = []
    in_code = False
    for i, line in enumerate(lines):
        s = line.rstrip()
        if s.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_ANY_RE.match(s)
        if m:
            headings.append((i, len(m.group(1)), m.group(2).strip()))
    return headings


def generate_split_plan(headings, total_lines, min_lines=50):
    """Generate a list of (filename, start_line, end_line, heading_text) tuples.

    Merges sections shorter than min_lines with their predecessor.
    """
    if not headings:
        return []

    # Raw splits
    raw = []
    for idx, (line_idx, text) in enumerate(headings):
        start = line_idx
        end = headings[idx + 1][0] - 1 if idx + 1 < len(headings) else total_lines - 1
        fname = slugify(text) + '.md'
        raw.append({'file': fname, 'start': start, 'end': end,
                    'heading': text, 'lines': end - start + 1})

    # Content before first heading becomes index.md
    plan = []
    if raw[0]['start'] > 0:
        plan.append({
            'file': 'index.md',
            'start': 0,
            'end': raw[0]['start'] - 1,
            'heading': '(Preamble / Introduction)',
            'lines': raw[0]['start'],
            'includes': ['preamble'],
        })

    # Add remaining, merging small sections
    for entry in raw:
        if plan and entry['lines'] < min_lines:
            # Merge with previous
            plan[-1]['end'] = entry['end']
            plan[-1]['lines'] = plan[-1]['end'] - plan[-1]['start'] + 1
            plan[-1].setdefault('includes', []).append(entry['heading'])
        else:
            plan.append(entry)

    # Deduplicate filenames
    seen = {}
    for entry in plan:
        f = entry['file']
        if f in seen:
            seen[f] += 1
            base = f.rsplit('.', 1)[0]
            entry['file'] = f"{base}-{seen[f]}.md"
        else:
            seen[f] = 1

    return plan


def build_plan_from_config(config, lines):
    """Build a split plan from an explicit config dict.

    Each group uses mode 'heading_range' or 'line_range' (1-based, inclusive).
    An 'auto' group falls through to the heading-based auto plan.
    """
    total = len(lines)
    groups = config.get('groups', [])
    if not groups:
        raise ValueError("config has no 'groups' list")

    # Resolve heading positions for any heading_range groups.
    all_h = parse_all_headings(lines)

    def find_heading(text):
        if text == 'EOF':
            return total  # sentinel
        matches = [i for (i, lvl, t) in all_h if t == text.strip()]
        if len(matches) == 0:
            raise ValueError(f"heading text not found: {text!r}")
        if len(matches) > 1:
            raise ValueError(
                f"heading text {text!r} appears {len(matches)} times; "
                f"use line_range mode instead")
        return matches[0]

    plan = []
    for g in groups:
        mode = g.get('mode', 'line_range')
        fname = g.get('file')
        heading = g.get('heading', fname or '(unnamed)')
        if not fname:
            raise ValueError(f"group missing 'file': {g}")

        if mode == 'line_range':
            start1 = g['start']
            end1 = g['end']
            if start1 < 1 or end1 > total or start1 > end1:
                raise ValueError(
                    f"{fname}: invalid line_range {start1}-{end1} (total={total})")
            start0 = start1 - 1
            end0 = end1 - 1
        elif mode == 'heading_range':
            from_text = g['from']
            to_text = g['to']
            start0 = find_heading(from_text)
            to0 = find_heading(to_text)
            end0 = total - 1 if to_text == 'EOF' else to0 - 1
            if end0 < start0:
                raise ValueError(
                    f"{fname}: heading_range end before start")
        elif mode == 'auto':
            # Fall through to auto-plan behaviour
            headings = parse_headings(lines, level=2)
            auto = generate_split_plan(headings, total,
                                       min_lines=config.get('min_lines', 50))
            plan.extend(auto)
            continue
        else:
            raise ValueError(f"{fname}: unknown mode {mode!r}")

        entry = {
            'file': fname,
            'start': start0,
            'end': end0,
            'heading': heading,
            'lines': end0 - start0 + 1,
        }
        if g.get('includes_preamble'):
            entry['includes'] = ['preamble']
        plan.append(entry)

    # Basic overlap sanity check
    for i in range(1, len(plan)):
        if plan[i]['start'] <= plan[i - 1]['end']:
            print(f"WARNING: overlap between {plan[i-1]['file']} and "
                  f"{plan[i]['file']}", file=sys.stderr)

    return plan


def show_plan(plan):
    """Display the proposed split plan to the user."""
    print("\nProposed splits:")
    for i, entry in enumerate(plan, 1):
        lines_range = f"lines {entry['start']+1}-{entry['end']+1}"
        extra = ''
        if entry.get('includes'):
            extra = f" (merged: {', '.join(entry['includes'])})"
        print(f"  {i:>2}. {entry['file']:<40s} {lines_range:<20s} "
              f"{entry['lines']:>5d} lines  {entry['heading']}{extra}")
    print()


def confirm_plan(plan, dry_run=False, auto=False):
    """Ask user to confirm the plan. Returns True to proceed."""
    if dry_run:
        print("(dry run -- no files will be written)")
        return False
    if auto:
        return True
    try:
        answer = input("Accept? [Y/n] ").strip().lower()
    except EOFError:
        answer = 'y'
    return answer in ('', 'y', 'yes')


# ── Equation, citation and reference processing ──────────────────────────────
def build_eq_map(lines, plan):
    """Build eq:ID -> (target_file, local_tag_number) mapping."""
    eq_to_file = {}
    eq_to_local = {}

    for entry in plan:
        local_tag = 0
        for i in range(entry['start'], entry['end'] + 1):
            if i >= len(lines):
                break
            for m in EQ_MARKER_RE.finditer(lines[i]):
                eq_id = m.group(1)
                local_tag += 1
                eq_to_file[eq_id] = entry['file']
                eq_to_local[eq_id] = local_tag

    return eq_to_file, eq_to_local


def find_bib_file(lines, plan):
    """Return the filename of the group containing <!-- bib:N --> markers, or None."""
    for entry in plan:
        for i in range(entry['start'], entry['end'] + 1):
            if i >= len(lines):
                break
            if BIB_MARKER_RE.search(lines[i]):
                return entry['file']
    return None


def convert_refs(line, current_file, eq_to_file, eq_to_local):
    """Convert cross-file refs to xref links; leave within-file refs alone.

    Preserves existing cross-survey xrefs (<!-- xref:SURVEY:ID -->).
    """
    # Skip lines that already have cross-survey xrefs
    if XREF_MARKER_RE.search(line):
        # Check if it's cross-survey (contains ':' in xref ID)
        for m in XREF_MARKER_RE.finditer(line):
            if ':' in m.group(1):
                return line  # preserve as-is

    def replacer(m):
        ref_comment = m.group(1)
        eq_id = m.group(2)
        full_match = m.group(0)

        if eq_id not in eq_to_file:
            return full_match

        target_file = eq_to_file[eq_id]
        target_tag = eq_to_local[eq_id]

        if target_file == current_file:
            # Within-file ref -- leave for renumber script
            return full_match

        # Cross-file ref -- convert to xref link
        return f"[({target_tag})]({target_file}#eq-{target_tag}) <!-- xref:{eq_id} -->"

    return REF_MARKER_RE.sub(replacer, line)


def convert_cites(line, current_file, bib_file):
    """Rewrite same-file cite links to cross-file form when the bib lives elsewhere.

    Transforms `<!-- cite:N --> [[N]](#ref-N)` into
    `<!-- cite:N --> [[N]](references.md#ref-N)` in every non-bib file.
    """
    if bib_file is None or current_file == bib_file:
        return line

    def replacer(m):
        marker = m.group(1)
        n_link = m.group(3)
        n_anchor = m.group(4)
        return f"{marker} [[{n_link}]]({bib_file}#ref-{n_anchor})"

    return CITE_MARKER_RE.sub(replacer, line)


def fix_image_path(line, source_dir, target_dir):
    """Fix image paths to be relative to the new file location."""
    def replacer(m):
        prefix, path, suffix = m.group(1), m.group(2), m.group(3)
        if path.startswith('http'):
            return m.group(0)
        # Normalize to figures/ directory
        basename = Path(path).name
        if '/' in path:
            # Already has a directory -- keep as figures/
            return f"{prefix}figures/{basename}{suffix}"
        return m.group(0)
    return IMG_RE.sub(replacer, line)


# ── File generation ───────────────────────────────────────────────────────────
def generate_index(title, plan, output_dir, preamble_lines=None):
    """Generate index.md with title and TOC."""
    content = []
    if title:
        content.append(f"# {title}\n\n")

    # Include preamble content if the first entry is index.md with preamble
    if preamble_lines:
        content.extend(preamble_lines)
        content.append('\n')

    # TOC
    content.append("## Contents\n\n")
    for entry in plan:
        if entry['file'] == 'index.md':
            continue
        content.append(f"- [{entry['heading']}]({entry['file']})\n")

    index_path = output_dir / 'index.md'
    index_path.write_text(''.join(content), encoding='utf-8')
    return index_path


def generate_order(plan, output_dir):
    """Generate order.json listing files in document order."""
    files = [entry['file'] for entry in plan]
    order_path = output_dir / 'order.json'
    order_path.write_text(json.dumps(files, indent=2) + '\n', encoding='utf-8')
    return order_path


RENUMBER_WRAPPER_TEMPLATE = '''#!/usr/bin/env python3
"""Thin wrapper — delegates to viewer/tools/renumber-equations.py.

Usage (from repo root):
  python surveys/<name>/renumber-equations.py <file>.md
  python surveys/<name>/renumber-equations.py .              # whole survey
  python surveys/<name>/renumber-equations.py --check .
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent.parent / 'viewer' / 'tools' / 'renumber-equations.py'

if not MASTER.exists():
    print(f'Master script not found: {MASTER}', file=sys.stderr)
    sys.exit(1)

# Resolve bare filenames relative to this survey directory
args = []
for arg in sys.argv[1:]:
    if not arg.startswith('-'):
        p = Path(arg)
        if not p.is_absolute() and not p.exists():
            resolved = HERE / p
            if resolved.exists():
                arg = str(resolved)
    args.append(arg)

sys.exit(subprocess.call([sys.executable, str(MASTER)] + args))
'''


def generate_renumber_wrapper(output_dir):
    """Write the per-survey renumber-equations.py wrapper script."""
    path = output_dir / 'renumber-equations.py'
    path.write_text(RENUMBER_WRAPPER_TEMPLATE, encoding='utf-8')
    return path


# ── Inventory mode ───────────────────────────────────────────────────────────
def compute_inventory(source_path):
    """Return a dict of metadata about the source file without writing anything."""
    source_path = Path(source_path).resolve()
    text = source_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    total = len(lines)

    h2 = parse_headings(lines, level=2)
    h3 = parse_headings(lines, level=3)

    eq_count = 0
    ref_count = 0
    bib_count = 0
    cite_count = 0
    xref_count = 0
    for ln in lines:
        eq_count += len(EQ_MARKER_RE.findall(ln))
        ref_count += len(re.findall(r'<!--\s*ref:', ln))
        bib_count += len(BIB_MARKER_RE.findall(ln))
        cite_count += len(re.findall(r'<!--\s*cite:', ln))
        xref_count += len(XREF_MARKER_RE.findall(ln))

    # Locate a candidate figures dir by walking up one or two levels.
    figures_dir = None
    figures_stats = (0, 0)
    for parent in [source_path.parent, source_path.parent.parent]:
        cand = parent / 'figures'
        if cand.exists() and cand.is_dir():
            files = [p for p in cand.iterdir() if p.is_file()]
            subdirs = [p for p in cand.iterdir() if p.is_dir()]
            figures_dir = cand
            figures_stats = (len(files), len(subdirs))
            break

    # Largest / smallest H2 by line span
    h2_spans = []
    for idx, (line_idx, text) in enumerate(h2):
        end = h2[idx + 1][0] - 1 if idx + 1 < len(h2) else total - 1
        h2_spans.append((end - line_idx + 1, text))
    largest = max(h2_spans, default=(0, '(none)'))
    smallest = min(h2_spans, default=(0, '(none)'))

    size_bytes = source_path.stat().st_size

    return {
        'total_lines': total,
        'h2_sections': len(h2),
        'h3_sections': len(h3),
        'equation_markers': eq_count,
        'ref_markers': ref_count,
        'bib_markers': bib_count,
        'cite_markers': cite_count,
        'xref_markers': xref_count,
        'figures_dir': figures_dir,
        'figures_stats': figures_stats,
        'size_bytes': size_bytes,
        'largest_h2': largest,
        'smallest_h2': smallest,
    }


def print_inventory(inv):
    fd = inv['figures_dir']
    if fd:
        nf, nd = inv['figures_stats']
        fd_str = f"{fd} ({nf} files, {nd} subdirs)"
    else:
        fd_str = '(none found)'
    print(f"total_lines:        {inv['total_lines']}")
    print(f"h2_sections:        {inv['h2_sections']}")
    print(f"h3_sections:        {inv['h3_sections']}")
    print(f"equation_markers:   {inv['equation_markers']}")
    print(f"ref_markers:        {inv['ref_markers']}")
    print(f"bib_markers:        {inv['bib_markers']}")
    print(f"cite_markers:       {inv['cite_markers']}")
    print(f"xref_markers:       {inv['xref_markers']}")
    print(f"figures_dir:        {fd_str}")
    print(f"size_bytes:         {inv['size_bytes']}")
    print(f"largest_h2:         {inv['largest_h2'][1]} ({inv['largest_h2'][0]} lines)")
    print(f"smallest_h2:        {inv['smallest_h2'][1]} ({inv['smallest_h2'][0]} lines)")


# ── Output-dir safety ────────────────────────────────────────────────────────
def ensure_output_dir_safe(output_dir, force):
    """Refuse to run if the target directory would stomp on files we did not create."""
    if not output_dir.exists():
        return True
    existing = list(output_dir.iterdir())
    if not existing:
        return True
    # A fresh directory containing only split.config.json (the caller's own
    # config file, placed there so it travels with the split) is effectively
    # empty for safety purposes.
    non_config = [p for p in existing if p.name != 'split.config.json']
    if not non_config:
        return True
    if not force:
        print(
            f"ERROR: output directory {output_dir} exists and is non-empty. "
            f"Pass --force to refresh it.",
            file=sys.stderr,
        )
        return False
    order_path = output_dir / 'order.json'
    if not order_path.exists():
        print(
            f"ERROR: {output_dir} is non-empty but has no order.json; "
            f"refusing to touch it even with --force to avoid overwriting "
            f"unrelated files.",
            file=sys.stderr,
        )
        return False
    try:
        owned = set(json.loads(order_path.read_text(encoding='utf-8')))
    except Exception as e:
        print(f"ERROR: failed to read {order_path}: {e}", file=sys.stderr)
        return False
    owned.update({'order.json', 'renumber-equations.py', 'split.config.json'})
    for p in output_dir.iterdir():
        if p.is_dir():
            # allow figures/ and archive/
            if p.name in ('figures', 'archive', '.archive'):
                continue
            print(f"ERROR: unexpected subdirectory {p} in output dir; refusing.",
                  file=sys.stderr)
            return False
        if p.name not in owned:
            print(
                f"ERROR: {p.name} in {output_dir} was not created by a prior "
                f"split run (not in order.json); refusing to overwrite.",
                file=sys.stderr,
            )
            return False
    return True


# ── Main split logic ─────────────────────────────────────────────────────────
def split_file(source_path, output_dir, split_level=2, min_lines=50,
               dry_run=False, keep_original=False,
               config=None, force=False):
    """Main split workflow."""
    source_path = Path(source_path).resolve()
    output_dir = Path(output_dir).resolve()

    if not source_path.exists():
        print(f"Source file not found: {source_path}", file=sys.stderr)
        return False

    text = source_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    total = len(lines)
    print(f"Read {total} lines from {source_path.name}")

    # Extract title from first H1 or from config
    title = None
    if config and config.get('title'):
        title = config['title']
    if title is None:
        for line in lines[:20]:
            m = re.match(r'^#\s+(.+)$', line.rstrip())
            if m:
                title = m.group(1).strip()
                break

    # Build plan -- from config if given, else from heading auto-split
    if config is not None:
        try:
            plan = build_plan_from_config(config, lines)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return False
    else:
        headings = parse_headings(lines, level=split_level)
        if not headings:
            print(f"No H{split_level} headings found in {source_path.name}")
            return False
        plan = generate_split_plan(headings, total, min_lines=min_lines)

    show_plan(plan)

    if not confirm_plan(plan, dry_run=dry_run, auto=(config is not None)):
        return dry_run  # dry_run returns True, cancel returns False

    # Check target directory safety (after confirmation, before any writes)
    if not dry_run and not ensure_output_dir_safe(output_dir, force):
        return False

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build equation map
    eq_to_file, eq_to_local = build_eq_map(lines, plan)
    print(f"Mapped {len(eq_to_file)} equation markers across {len(plan)} files")

    # Find the bibliography target file for cite rewriting
    bib_file = find_bib_file(lines, plan)
    if bib_file:
        print(f"Bibliography detected in: {bib_file}")

    # Copy figures directory if it exists
    source_dir = source_path.parent
    figures_src = source_dir / 'figures'
    figures_dst = output_dir / 'figures'
    if figures_src.exists() and figures_src.is_dir() and not figures_dst.exists():
        import shutil
        shutil.copytree(figures_src, figures_dst)
        print(f"Copied figures/ directory")

    # Split and write files
    preamble_lines = None
    files_written = []
    for entry in plan:
        chunk = lines[entry['start']:entry['end'] + 1]

        # Convert refs, cites, fix paths
        out_lines = []
        for line in chunk:
            line = convert_refs(line, entry['file'], eq_to_file, eq_to_local)
            line = convert_cites(line, entry['file'], bib_file)
            line = fix_image_path(line, source_dir, output_dir)
            out_lines.append(line)

        if entry['file'] == 'index.md' and entry.get('includes'):
            # This is the preamble -- save for index generation
            preamble_lines = [l + '\n' for l in out_lines]
            # Still write the file with preamble + TOC
            generate_index(title, plan, output_dir, preamble_lines)
            files_written.append('index.md')
        else:
            out_path = output_dir / entry['file']
            out_path.write_text('\n'.join(out_lines), encoding='utf-8')
            files_written.append(entry['file'])

        eq_count = sum(1 for l in out_lines if EQ_MARKER_RE.search(l))
        ref_count = sum(1 for l in out_lines if '<!-- ref:' in l)
        xref_count = sum(1 for l in out_lines if '<!-- xref:' in l)
        cite_count = sum(1 for l in out_lines if '<!-- cite:' in l)
        print(f"  {entry['file']}: {len(out_lines)} lines, {eq_count} eqs, "
              f"{ref_count} refs, {xref_count} xrefs, {cite_count} cites")

    # Generate index if not already done
    if 'index.md' not in files_written:
        generate_index(title, plan, output_dir)
        files_written.insert(0, 'index.md')
        # Update plan to include index
        plan.insert(0, {'file': 'index.md', 'heading': 'Index'})

    # Generate order.json
    generate_order(plan, output_dir)

    # Generate per-survey renumber-equations.py wrapper
    generate_renumber_wrapper(output_dir)

    # Run renumber on each file
    tools_dir = Path(__file__).resolve().parent
    renumber_script = tools_dir / 'renumber-equations.py'
    if renumber_script.exists():
        print("\nRunning renumber-equations.py on each file...")
        for f in files_written:
            filepath = output_dir / f
            result = subprocess.run(
                [sys.executable, str(renumber_script), str(filepath)],
                capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  WARNING: renumber failed for {f}: {result.stderr}")
    else:
        print(f"\nWARNING: renumber script not found at {renumber_script}")

    # Run validate
    validate_script = tools_dir / 'validate-refs.py'
    if validate_script.exists():
        print("\nRunning validate-refs.py...")
        result = subprocess.run(
            [sys.executable, str(validate_script), str(output_dir)],
            capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(result.stderr)

    # Archive original if requested
    if keep_original:
        archive_dir = source_path.parent / 'archive'
        archive_dir.mkdir(exist_ok=True)
        import shutil
        shutil.copy2(source_path, archive_dir / source_path.name)
        print(f"\nOriginal archived to {archive_dir / source_path.name}")

    # Summary
    print(f"\nSplit complete:")
    print(f"  Files created: {len(files_written)}")
    print(f"  Equations mapped: {len(eq_to_file)}")
    print(f"  Output directory: {output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', help='Monolithic markdown file to split')
    parser.add_argument('--output', '-o',
                        help='Output directory (default: source name without .md)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show proposed split without writing files')
    parser.add_argument('--split-at', choices=['H2', 'H3', 'h2', 'h3'],
                        default='H2',
                        help='Heading level to split at (default: H2)')
    parser.add_argument('--keep-original', action='store_true',
                        help='Copy original to archive/ directory')
    parser.add_argument('--min-lines', type=int, default=50,
                        help='Minimum lines per file; merge smaller sections (default: 50)')
    parser.add_argument('--inventory', action='store_true',
                        help='Print metadata about the source file and exit')
    parser.add_argument('--config',
                        help='Path to an explicit split-config JSON file')
    parser.add_argument('--force', action='store_true',
                        help='Refresh an existing split output directory')
    args = parser.parse_args()

    source = Path(args.source)

    # Inventory short-circuit — no output dir needed
    if args.inventory:
        if not source.exists():
            print(f"Source file not found: {source}", file=sys.stderr)
            sys.exit(1)
        inv = compute_inventory(source)
        print_inventory(inv)
        sys.exit(0)

    # Load config if present
    config = None
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            print(f"Config file not found: {cfg_path}", file=sys.stderr)
            sys.exit(1)
        try:
            config = json.loads(cfg_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {cfg_path}: {e}", file=sys.stderr)
            sys.exit(1)

    if args.output:
        output = Path(args.output)
    elif config and config.get('output_dir'):
        output = Path(config['output_dir'])
    else:
        output = source.parent / source.stem

    level = int(args.split_at.upper().replace('H', ''))

    ok = split_file(source, output, split_level=level, min_lines=args.min_lines,
                    dry_run=args.dry_run, keep_original=args.keep_original,
                    config=config, force=args.force)

    # After a successful real run with a config, copy the config into the output dir
    if ok and not args.dry_run and config and args.config:
        import shutil
        try:
            shutil.copy2(args.config, Path(output) / 'split.config.json')
        except Exception as e:
            print(f"WARNING: failed to copy config into output dir: {e}",
                  file=sys.stderr)

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
