#!/usr/bin/env python3
"""Scaffold a new multi-file markdown document from a topic outline.

Creates a structured document directory with skeleton .md files, order.json,
index.md, and a renumber-all script.

Usage:
  python viewer/tools/init-doc.py surveys/new-topic/ --title "My Survey"
  python viewer/tools/init-doc.py surveys/polar-decoder/ --from outline.txt
  python viewer/tools/init-doc.py surveys/new-topic/ --title "My Survey" --with-figures
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

MATH_KEYWORDS = {
    'derivation', 'proof', 'theorem', 'lemma', 'corollary', 'formula',
    'fundamentals', 'analysis', 'equation', 'calculation', 'computation',
    'algorithm', 'transform', 'optimization', 'convergence', 'bound',
}


def slugify(text):
    """Convert heading text to filename slug."""
    text = re.sub(r'[*_`\[\]()]', '', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = text.lower().strip('-')
    if text.startswith('appendix'):
        parts = text.split('-', 1)
        if len(parts) > 1:
            letter = re.search(r'[a-z]', parts[1])
            if letter:
                return f"appendix-{letter.group(0)}"
    if text in ('references', 'bibliography'):
        return 'references'
    return text[:50]


def has_math_keywords(text):
    """Check if heading text suggests mathematical content."""
    words = set(text.lower().split())
    return bool(words & MATH_KEYWORDS)


def parse_outline(text):
    """Parse an outline into sections.

    Returns: (title, sections) where sections is a list of
    {'heading': str, 'slug': str, 'subsections': [str]}
    """
    lines = text.strip().split('\n')
    title = None
    sections = []
    current = None

    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        # H1 = title
        m = re.match(r'^#\s+(.+)$', line)
        if m:
            title = m.group(1).strip()
            continue

        # H2 = new section (file)
        m = re.match(r'^##\s+(.+)$', line)
        if m:
            heading = m.group(1).strip()
            current = {
                'heading': heading,
                'slug': slugify(heading),
                'subsections': [],
            }
            sections.append(current)
            continue

        # H3 = subsection within current file
        m = re.match(r'^###\s+(.+)$', line)
        if m and current:
            current['subsections'].append(m.group(1).strip())
            continue

    return title, sections


def interactive_outline():
    """Interactively build an outline from user input."""
    print("Enter section headings (one per line). Blank line to finish.")
    print("Prefix with ### for subsections under the previous section.\n")
    lines = []
    try:
        while True:
            line = input("> ").rstrip()
            if not line:
                break
            # Auto-add ## prefix if missing
            if not line.startswith('#'):
                line = f"## {line}"
            lines.append(line)
    except EOFError:
        pass
    return '\n'.join(lines)


def generate_skeleton(section, include_math_template=False):
    """Generate skeleton markdown content for a section."""
    content = [f"## {section['heading']}\n"]

    for sub in section['subsections']:
        content.append(f"\n### {sub}\n")
        content.append("\n<!-- TODO: content -->\n")

        if include_math_template and has_math_keywords(sub):
            content.append(f"""
<a id="eq-1"></a><!-- eq:{section['slug']}-1 -->
$$
\\tag{{1}}
$$
""")

    if not section['subsections']:
        content.append("\n<!-- TODO: content -->\n")
        if include_math_template and has_math_keywords(section['heading']):
            content.append(f"""
<a id="eq-1"></a><!-- eq:{section['slug']}-1 -->
$$
\\tag{{1}}
$$
""")

    return '\n'.join(content)


def generate_index(title, sections, output_dir):
    """Generate index.md with title and linked TOC."""
    content = []
    if title:
        content.append(f"# {title}\n\n")

    content.append("## Contents\n\n")
    for section in sections:
        content.append(f"- [{section['heading']}]({section['slug']}.md)\n")

    path = output_dir / 'index.md'
    path.write_text(''.join(content), encoding='utf-8')
    return path


def generate_order(sections, output_dir):
    """Generate order.json."""
    files = ['index.md'] + [f"{s['slug']}.md" for s in sections]
    path = output_dir / 'order.json'
    path.write_text(json.dumps(files, indent=2) + '\n', encoding='utf-8')
    return path


def generate_renumber_all(sections, output_dir):
    """Generate renumber-all.sh batch wrapper."""
    tools_dir = Path(__file__).resolve().parent
    # Compute relative path from output_dir to tools_dir
    try:
        rel = Path('..') / Path('..') / 'viewer' / 'tools'
    except ValueError:
        rel = tools_dir

    lines = ['#!/usr/bin/env bash', '# Renumber equations in all document files', '']
    lines.append(f'SCRIPT="{rel}/renumber-equations.py"')
    lines.append('')
    for section in sections:
        lines.append(f'python "$SCRIPT" "{section["slug"]}.md"')
    lines.append('')
    lines.append('echo "Done."')

    path = output_dir / 'renumber-all.sh'
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def init_doc(output_dir, title=None, outline_file=None, with_figures=False,
             with_template=False):
    """Main scaffolding workflow."""
    output_dir = Path(output_dir).resolve()

    # Parse outline
    if outline_file:
        outline_text = Path(outline_file).read_text(encoding='utf-8')
    else:
        if not title:
            try:
                title = input("Document title: ").strip()
            except EOFError:
                print("No title provided.")
                return False
        outline_text = f"# {title}\n" + interactive_outline()

    parsed_title, sections = parse_outline(outline_text)
    if title:
        parsed_title = title
    if not parsed_title:
        parsed_title = output_dir.name.replace('-', ' ').title()

    if not sections:
        print("No sections found in outline.")
        return False

    print(f"\nScaffolding '{parsed_title}' with {len(sections)} sections:")
    for s in sections:
        subs = f" ({len(s['subsections'])} subsections)" if s['subsections'] else ""
        print(f"  {s['slug']}.md — {s['heading']}{subs}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create figures directory if requested
    if with_figures:
        (output_dir / 'figures').mkdir(exist_ok=True)

    # Generate section files
    math_sections = any(has_math_keywords(s['heading']) for s in sections)
    for section in sections:
        content = generate_skeleton(section, include_math_template=math_sections)
        path = output_dir / f"{section['slug']}.md"
        path.write_text(content, encoding='utf-8')

    # Generate index and order
    generate_index(parsed_title, sections, output_dir)
    generate_order(sections, output_dir)
    generate_renumber_all(sections, output_dir)

    # Generate thin wrapper that delegates to viewer/tools/renumber-equations.py
    wrapper = output_dir / 'renumber-equations.py'
    wrapper.write_text('''\
#!/usr/bin/env python3
"""Thin wrapper — delegates to viewer/tools/renumber-equations.py."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent.parent / 'viewer' / 'tools' / 'renumber-equations.py'

if not MASTER.exists():
    print(f'Master script not found: {MASTER}', file=sys.stderr)
    sys.exit(1)

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
''', encoding='utf-8')

    print(f"\nCreated {len(sections) + 1} files in {output_dir}/")
    print(f"  index.md, order.json, renumber-all.sh")
    for s in sections:
        print(f"  {s['slug']}.md")
    if with_figures:
        print(f"  figures/")

    print(f"\nNext steps:")
    print(f"  1. Fill in <!-- TODO: content --> placeholders")
    print(f"  2. Run: python renumber-equations.py <file>.md")
    print(f"  3. View (one-time: cd viewer && npm install):")
    print(f"        node viewer/serve.js {output_dir} -p 4500")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output', help='Output directory for the new document')
    parser.add_argument('--title', '-t', help='Document title for index.md')
    parser.add_argument('--from', dest='outline', metavar='FILE',
                        help='Read outline from file')
    parser.add_argument('--with-figures', action='store_true',
                        help='Create figures/ subdirectory')
    parser.add_argument('--template', action='store_true',
                        help='Include math equation templates in sections')
    args = parser.parse_args()

    ok = init_doc(args.output, title=args.title, outline_file=args.outline,
                  with_figures=args.with_figures, with_template=args.template)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
