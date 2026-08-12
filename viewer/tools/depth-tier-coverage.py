#!/usr/bin/env python3
"""depth-tier-coverage.py -- L3' deterministic depth-tier coverage summary.

The companion of `check-depth-tiers.py`. Where that checker enforces the
depth-tier *vocabulary* (is the label a legal word?), this tool audits
*coverage*: does the tier a section actually SHIPPED still match the tier that
was APPROVED for it at the outline, and are there compact category-safe smells
worth a human glance?

It is the Layer-3' emitter from `proposals/2026-07-08-depth-tier-gating.md`
(decision 2026-07-08-03). The original Layer 3 inferred "under-delivered" depth
from the absence of `$$`/landmarks; a 3-agent review showed that produced ~0
true positives and ~4-15 false positives per run (depth is often argumentative
or cross-linked out, and the tier label sits on a `##` parent while artifacts
live in `###` children). That heuristic is DROPPED. What remains is one
deterministic diff plus three category-safe checks -- no depth-from-equations
inference:

    TIER-DRIFT    (load-bearing; may go error)  a section's authored
                  `Depth tier:` differs from the tier the persisted outline
                  table approved for it. Pure set-diff of two section->tier
                  maps. This is the check that covers the EDIT path -- the path
                  both motivating bugs took (a `load-bearing` approval shipping
                  `catalog`, or the reverse).
    MISSING-TIER  (warning)  an outline-listed section with no authored
                  `Depth tier:` label. Keyed to the APPROVED OUTLINE LIST, not
                  "every heading" (which false-positives on roadmap / context
                  sections).
    OVER-DELIVERED (warning)  a `catalog` section that nonetheless carries a
                  `$$` display-math block -- the one artifact test that is
                  category-safe (equations inside a "compact stated-result"
                  section is a genuine signal). UNDER-DELIVERED is NOT a check
                  (depth != equations).
    n/a-FORM      (warning)  a `catalog` section with no explicit `n/a` marker
                  for its skipped heavy artifacts. Accepts BOTH `n/a (...)` and
                  `n/a -- ...` (the corpus uses both; e.g. section 18 uses the
                  em-dash form).

Scope -- the tool self-scopes to *tier-using* surveys, so a corpus-wide run
never prods a survey that opted out of the depth-tier system:

    * labels + allocation table  -> full checks (the lte-dl steady state)
    * labels, NO allocation table -> `NO-ALLOCATION-TABLE` flag (the survey
      uses tiers but skipped the Layer-2 outline sign-off; add a table)
    * NO labels (and no table)    -> clean no-op, no nudge (the survey does
      not use depth tiers; out of scope by design -- the ~15 dormant surveys)

The persisted outline tier table is the left-hand side of the drift diff. It
lives in the survey's `_scratch/00-*-outline.md` under a
`<!-- depth-tier-allocation -->` marker, as an ordinary markdown table:

    <!-- depth-tier-allocation -->
    | Section | Tier | Justification |
    |---|---|---|
    | 4  | headline     | root delta #1 (CRS paradigm) |
    | 14 | load-bearing | promoted from catalog (decision 2026-07-08-01) |
    ...

The `Section` cell is the section's canonical identity -- the same token that
appears in its heading anchor `<a id="sec-14">` / `<a id="sec-C.14.1">`. A
survey that has not yet grown a tier table (pre-Layer-2) simply has no
TIER-DRIFT / MISSING-TIER rows; the tally, OVER-DELIVERED and n/a-FORM checks
still run, so the tool is useful standalone.

Delivered side: for each authored `Depth tier: <tier>` label, the HOST section
is the nearest preceding ATX heading; its `sec-` anchor is the key. The host's
body-range (for the `$$` / `n/a` scans) runs from that heading until the next
heading of the same-or-higher level, so a `## 14` label's range covers its
`### 14.x` children.

Output: a markdown summary block on stdout (fold into the Phase-5 report /
"## Self-evaluation scorecard" footer) plus a one-line status on stderr.

Usage:
    python viewer/tools/depth-tier-coverage.py SURVEY_DIR [--severity warn|error]

`--severity error` promotes TIER-DRIFT to an error: a non-empty drift set then
exits non-zero (for a gate). The other three checks stay advisory regardless.
`--check` is accepted and ignored (this tool is always read-only) for flag
parity with the renumber scripts.

Exit code 0 if no error-severity findings; 1 if `--severity error` and a
TIER-DRIFT row exists; 2 on a usage error.
"""
import json
import re
import sys
from pathlib import Path

# Reuse the exact authored-label form the vocabulary gate matches.
LABEL_RE = re.compile(r'Depth tier:\s*\*{0,2}\s*([a-z][a-z-]*)')

# Heading with a section anchor: capture level, sec-id, trailing title.
HEADING_ANCHOR_RE = re.compile(r'^(#{1,6})\s+<a id="sec-([^"]+)"></a>\s*(.*)$')
# Heading without an anchor (fallback): capture level + visible text.
HEADING_PLAIN_RE = re.compile(r'^(#{1,6})\s+(.*)$')
# Leading section number in visible heading text (fallback key).
LEADING_NUM_RE = re.compile(r'^([A-Z]?\.?\d+(?:\.\d+)*|[A-Z])\b')

# A `$$` display-math block: a line that OPENS with `$$` (the repo's
# own-line convention) or a complete single-line `$$...$$` block. This
# deliberately does NOT match two adjacent inline spans (`$a$$b$`).
DISPLAY_MATH_RE = re.compile(r'^\s*\$\$|\$\$.+?\$\$')
# An explicit n/a marker: `n/a (` or `n/a` + any dash (hyphen / en / em).
# The corpus uses both `n/a (...)` and `n/a -- ...` / `n/a <em-dash> ...`.
NA_MARKER_RE = re.compile(r'n/a\s*[\(‐-―\-]', re.IGNORECASE)

# The `<!-- depth-tier-allocation -->` marker that flags the outline tier table.
ALLOC_MARKER_RE = re.compile(r'<!--\s*depth-tier-allocation\s*-->')


class Section:
    """One heading and its resolved body-range within a single file."""
    __slots__ = ('key', 'level', 'title', 'line', 'file', 'end_line',
                 'tier', 'tier_line', 'has_display_math', 'has_na')

    def __init__(self, key, level, title, line, file):
        self.key = key
        self.level = level
        self.title = title
        self.line = line          # 1-based heading line
        self.file = file
        self.end_line = None      # exclusive; set when the range closes
        self.tier = None          # authored Depth tier, if any
        self.tier_line = None
        self.has_display_math = False
        self.has_na = False


def parse_headings(lines, filename):
    """Return the ordered list of Section objects for one file's lines."""
    sections = []
    for i, line in enumerate(lines, 1):
        m = HEADING_ANCHOR_RE.match(line)
        if m:
            level = len(m.group(1))
            key = m.group(2)
            title = m.group(3).strip()
            sections.append(Section(key, level, title, i, filename))
            continue
        m = HEADING_PLAIN_RE.match(line)
        if m and not line.lstrip().startswith('#!'):
            level = len(m.group(1))
            text = m.group(2).strip()
            num = LEADING_NUM_RE.match(text)
            key = num.group(1).rstrip('.') if num else None
            if key is not None:
                sections.append(Section(key, level, text, i, filename))
    # Close each section's body-range at the next heading of same-or-higher level.
    for idx, sec in enumerate(sections):
        end = len(lines) + 1
        for later in sections[idx + 1:]:
            if later.level <= sec.level:
                end = later.line
                break
        sec.end_line = end
    return sections


def scan_file(path):
    """Return the Section list for one file, with tier / $$ / n/a resolved."""
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    sections = parse_headings(lines, path.name)
    if not sections:
        return []

    # Assign each Depth-tier label to its host section: the deepest (last-
    # starting) heading that encloses the label line.
    def host_for(lineno):
        host = None
        for sec in sections:
            if sec.line <= lineno < sec.end_line:
                if host is None or sec.line > host.line:
                    host = sec
        return host

    for i, line in enumerate(lines, 1):
        lm = LABEL_RE.search(line)
        if lm:
            host = host_for(i)
            if host is not None and host.tier is None:
                host.tier = lm.group(1)
                host.tier_line = i

    # Scan each TIERED section's FULL body-range (which spans its `###`
    # children) for `$$` and `n/a` markers. Scanning the tier-bearing
    # section's own range -- not per-line deepest-host flags -- is what makes
    # a parent's artifacts visible: e.g. a `## 18` catalog label whose
    # explicit `n/a` markers live in child `### 18.1`.
    for sec in sections:
        if sec.tier is None:
            continue
        body = lines[sec.line - 1:sec.end_line - 1]
        sec.has_display_math = any(DISPLAY_MATH_RE.search(ln) for ln in body)
        sec.has_na = any(NA_MARKER_RE.search(ln) for ln in body)
    return sections


def load_outline_table(survey_dir):
    """Parse the persisted `<!-- depth-tier-allocation -->` table.

    Returns (approved: {key: (tier, justification)}, source_path or None).
    The table is an ordinary markdown table; the Section column is the key.
    """
    approved = {}
    scratch = survey_dir / '_scratch'
    if not scratch.is_dir():
        return approved, None
    candidates = sorted(scratch.glob('00-*outline*.md')) + \
        sorted(scratch.glob('00-*.md'))
    for cand in candidates:
        lines = cand.read_text(encoding='utf-8').splitlines()
        for idx, line in enumerate(lines):
            if ALLOC_MARKER_RE.search(line):
                _parse_md_table(lines, idx + 1, approved)
                if approved:
                    return approved, cand
    return approved, None


def _parse_md_table(lines, start, approved):
    """Fill `approved` from the first markdown table at/after `start`.

    Tolerates blank and prose lines (e.g. a bold caption) between the
    `<!-- depth-tier-allocation -->` marker and the table itself; stops
    searching at the next heading, the next HTML comment, or a 12-line window.
    """
    i = start
    limit = min(len(lines), start + 12)
    while i < limit and not lines[i].lstrip().startswith('|'):
        stripped = lines[i].lstrip()
        if stripped.startswith('#') or stripped.startswith('<!--'):
            return  # left the marker's block without finding a table
        i += 1
    # Header + separator + rows.
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith('|'):
        rows.append(lines[i])
        i += 1
    if len(rows) < 2:
        return
    # Row 0 header, row 1 separator (---), rest data.
    for row in rows[2:]:
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if len(cells) < 2 or not cells[0]:
            continue
        key = cells[0].lstrip('§').strip()
        tier = cells[1].strip().strip('`').strip('*').strip()
        just = cells[2].strip() if len(cells) > 2 else ''
        if key:
            approved[key] = (tier, just)


def build_report(survey_dir, severity):
    order_path = survey_dir / 'order.json'
    if order_path.is_file():
        order = json.loads(order_path.read_text(encoding='utf-8'))
    else:
        order = sorted(p.name for p in survey_dir.glob('*.md'))

    delivered = {}         # key -> Section (first wins)
    tally = {}
    for fname in order:
        fpath = survey_dir / fname
        if not fpath.is_file():
            continue
        for sec in scan_file(fpath):
            if sec.tier is None:
                continue
            tally[sec.tier] = tally.get(sec.tier, 0) + 1
            delivered.setdefault(sec.key, sec)

    approved, table_src = load_outline_table(survey_dir)

    # --- checks ---
    drift = []       # (key, approved_tier, delivered_tier, file, line)
    for key, sec in sorted(delivered.items()):
        if key in approved and approved[key][0] and approved[key][0] != sec.tier:
            drift.append((key, approved[key][0], sec.tier, sec.file, sec.tier_line))

    missing = []     # (key, approved_tier)
    for key, (tier, _just) in sorted(approved.items()):
        if key not in delivered:
            missing.append((key, tier))

    over = []        # (key, file, line) -- catalog + $$
    na_gap = []      # (key, file, line) -- catalog with no n/a marker
    for key, sec in sorted(delivered.items()):
        if sec.tier == 'catalog':
            if sec.has_display_math:
                over.append((key, sec.file, sec.tier_line))
            if not sec.has_na:
                na_gap.append((key, sec.file, sec.tier_line))

    delivered_only = sorted(k for k in delivered if k not in approved) if approved else []

    return {
        'tally': tally,
        'delivered': delivered,
        'approved': approved,
        'table_src': table_src,
        'drift': drift,
        'missing': missing,
        'over': over,
        'na_gap': na_gap,
        'delivered_only': delivered_only,
        'severity': severity,
        'has_labels': bool(delivered),
        # A tier-using survey that skipped the Layer-2 allocation table. A
        # survey with NO labels is out of scope (opted out of tiers) and is
        # NOT flagged -- that is what scopes enforcement to lte-dl + future.
        'no_alloc_table': bool(delivered) and not approved,
    }


def emit_markdown(survey_dir, r):
    out = []
    out.append('### Depth-tier coverage summary')
    out.append('')
    out.append(f'*Survey:* `{survey_dir.as_posix()}` '
               f'-- *generated by* `depth-tier-coverage.py` (Layer 3-prime).')
    out.append('')
    # Tally.
    if r['tally']:
        dist = ', '.join(f'`{k}` {r["tally"][k]}' for k in sorted(r['tally']))
    else:
        dist = '(no `Depth tier:` labels found)'
    out.append(f'**Tier tally (delivered):** {dist}.')
    out.append('')
    if r['approved']:
        out.append(f'**Outline allocation:** {len(r["approved"])} section(s) '
                   f'tiered in `{r["table_src"].name}`.')
        out.append('')
    elif r['no_alloc_table']:
        out.append('**Outline allocation:** **`NO-ALLOCATION-TABLE` (warning)** '
                   '-- this survey carries `Depth tier:` labels but has no '
                   '`<!-- depth-tier-allocation -->` table in `_scratch/00-*-outline.md`, '
                   'so the Layer-2 outline sign-off was skipped and TIER-DRIFT / '
                   'MISSING-TIER have no baseline. Add the table (see `DT-L2-OUTLINE`).')
        out.append('')
    else:
        out.append('**Outline allocation:** n/a -- this survey does not use depth '
                   'tiers (no `Depth tier:` labels, no allocation table); out of '
                   'scope, checks skipped.')
        out.append('')
        return '\n'.join(out)

    def section(title, sev, rows, header, fmt):
        out.append(f'#### {title} ({sev})')
        if not rows:
            out.append('')
            out.append('- none.')
            out.append('')
            return
        out.append('')
        out.append(header)
        out.append('|' + '---|' * (header.count('|') - 1))
        for row in rows:
            out.append(fmt(row))
        out.append('')

    drift_sev = 'ERROR' if r['severity'] == 'error' else 'warning'
    section(
        'TIER-DRIFT', drift_sev, r['drift'],
        '| Section | Approved | Delivered | Location |',
        lambda x: f'| {x[0]} | `{x[1]}` | `{x[2]}` | {x[3]}:{x[4]} |',
    )
    section(
        'MISSING-TIER', 'warning', r['missing'],
        '| Section | Approved tier | Note |',
        lambda x: f'| {x[0]} | `{x[1]}` | outline-listed, no delivered label |',
    )
    section(
        'OVER-DELIVERED', 'warning', r['over'],
        '| Section | Location | Note |',
        lambda x: f'| {x[0]} | {x[1]}:{x[2]} | `catalog` section carries `$$` |',
    )
    section(
        'n/a-FORM', 'warning', r['na_gap'],
        '| Section | Location | Note |',
        lambda x: f'| {x[0]} | {x[1]}:{x[2]} | `catalog` with no explicit `n/a` marker |',
    )

    if r['delivered_only']:
        out.append('#### Delivered-only (info)')
        out.append('')
        out.append('Sections with a delivered tier but no outline-table entry '
                   '(not a drift; typically appendix sub-sections tiered per '
                   'parent rather than individually in the outline):')
        out.append('')
        out.append('> ' + ', '.join(f'`{k}`' for k in r['delivered_only']))
        out.append('')
    return '\n'.join(out)


def main(argv):
    args = [a for a in argv if a != '--check']
    severity = 'warn'
    if '--severity' in args:
        i = args.index('--severity')
        if i + 1 < len(args):
            severity = args[i + 1]
            del args[i:i + 2]
    if severity not in ('warn', 'error'):
        print(f'usage error: --severity must be warn|error (got {severity})',
              file=sys.stderr)
        return 2
    if len(args) != 1:
        print('usage: depth-tier-coverage.py SURVEY_DIR [--severity warn|error]',
              file=sys.stderr)
        return 2
    survey_dir = Path(args[0])
    if not survey_dir.is_dir():
        print(f'usage error: not a directory: {survey_dir}', file=sys.stderr)
        return 2

    r = build_report(survey_dir, severity)
    print(emit_markdown(survey_dir, r))

    if not r['has_labels']:
        print('depth-tier-coverage: survey does not use depth tiers -- '
              'out of scope, no checks run.', file=sys.stderr)
        return 0
    n_drift = len(r['drift'])
    n_soft = len(r['missing']) + len(r['over']) + len(r['na_gap'])
    notable = ' [NO-ALLOCATION-TABLE]' if r['no_alloc_table'] else ''
    status = (f'depth-tier-coverage: {n_drift} TIER-DRIFT, {n_soft} advisory '
              f'({len(r["missing"])} missing, {len(r["over"])} over, '
              f'{len(r["na_gap"])} n/a-form){notable}.')
    print(status, file=sys.stderr)

    if severity == 'error' and n_drift:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
