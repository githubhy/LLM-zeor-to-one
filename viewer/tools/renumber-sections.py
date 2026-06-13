#!/usr/bin/env python3
"""Renumber and link section anchors.

Sister of renumber-equations.py / renumber-paragraphs.py.

Anchor scheme:
  - At each '### X.Y.Z Heading' line: <a id="sec-X.Y.Z"></a> placed
    IMMEDIATELY AFTER the `### ` ATX prefix (before the visible heading
    text), and <!-- sec:X.Y.Z --> on the line above. The anchor must
    NOT precede the `#` characters — CommonMark requires the ATX prefix
    at column 0-3 and a leading inline-HTML anchor demotes the heading
    to a paragraph with literal `### ` visible in the body (bug
    2026-05-25-02). The migration to this convention is handled inline
    by `inject_heading_anchor()` — legacy column-0 anchors are stripped
    and re-injected at the correct position.
  - At each sub-section landmark (e.g. '**Step 3 - Recombine.**' inside
    section X.Y.Z): <a id="sec-X.Y.Z-step-3"></a> inline at column 0.
    Landmark lines start with `**`, not `#`, so the column-0 anchor
    does not interfere with any block-level parser construct.

Marker scheme (mirrors eq:/ref:/xref:):
  - <!-- sec:ID -->            section anchor (paired with <a id="sec-ID">)
  - <!-- secref:ID -->         same-file link to #sec-ID
  - <!-- secxref:ID -->        cross-file link to <owner>.md#sec-ID

Section-number forms supported:
  - Digit-first: 3.7.6, 4.4, 10.2.1   (matches [A-Z]?\\d+(?:\\.\\d+)+)
  - Letter-dot:  D.7, D.7.5, A.8.3    (matches [A-Z]\\.\\d+(?:\\.\\d+)*)

Usage:
  python viewer/tools/renumber-sections.py FILE [--check | --init | --dry-run-diff]
  python viewer/tools/renumber-sections.py DIR  [...]
"""
import argparse
import difflib
import io
import json
import re
import sys
from pathlib import Path

# Force UTF-8 on stdout/stderr so § and other non-ASCII characters survive
# on Windows consoles that default to a narrow code page (GBK, CP1252, etc.).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Patterns ------------------------------------------------------------

HEADING_RE = re.compile(
    # Optional column-0 anchor (LEGACY pre-2026-05-25 form; migrated by
    # `inject_heading_anchor()`).
    r'^(?:<a\s+id="[^"]*"></a>)?'
    r"(?P<hashes>#{2,6})\s+"
    # Optional post-ATX-prefix anchor (NEW form, fixed 2026-05-25). Both
    # may appear simultaneously on a half-migrated line; the legacy one
    # is then stripped by `inject_heading_anchor()`.
    r'(?:<a\s+id="[^"]*"></a>)?'
    r"(?P<num>[A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)"
    r"\s+(?P<title>.*)$"
)
SEC_ANCHOR_RE = re.compile(
    r'<a\s+id="sec-([A-Za-z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)(?:-[\w.\-]+)?"></a>'
)
SEC_MARKER_RE = re.compile(
    r"<!--\s*sec:([A-Za-z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)(?:-[\w.\-]+)?\s*-->"
)
SECREF_MARKER_RE = re.compile(
    r"<!--\s*secref:([A-Za-z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)(?:-[\w.\-]+)?\s*-->"
)
SECXREF_MARKER_RE = re.compile(
    r"<!--\s*secxref:([A-Za-z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)(?:-[\w.\-]+)?\s*-->"
)

SECREF_INLINE_RE = re.compile(
    r"(?P<marker><!--\s*secref:(?P<id>[A-Za-z]?\d+(?:\.\d+)+(?:-[\w.\-]+)?|[A-Z]\.\d+(?:\.\d+)*(?:-[\w.\-]+)?)\s*-->)"
    r"\s*\[(?P<text>[^\]]*)\]\((?P<target>[^)]*)\)"
)
SECXREF_INLINE_RE = re.compile(
    r"(?P<marker><!--\s*secxref:(?P<id>[A-Za-z]?\d+(?:\.\d+)+(?:-[\w.\-]+)?|[A-Z]\.\d+(?:\.\d+)*(?:-[\w.\-]+)?)\s*-->)"
    r"\s*\[(?P<text>[^\]]*)\]\((?P<target>[^)]*)\)"
)

LANDMARK_KINDS = [
    "Step", "Stage", "Phase", "Case", "Part", "Path", "Variant", "Branch",
    "Note", "Item", "Assumption", "Lemma", "Theorem", "Proposition",
    "Corollary", "Definition", "Example", "Remark", "Algorithm", "Procedure",
    "Fact", "Claim", "Table", "Figure",
]
INDEX_RE = r"(?:[A-Z]\.\d+(?:\.\d+)*-[A-Z0-9]+|\d+[a-z]?-[A-Z0-9]+|\d+[a-z]?|[A-Z])"

# Sub-landmark patterns (used by Task 2.3; declared here for the module):
LANDMARK_BOLD_RE = re.compile(
    rf"^(?P<indent>\s*)\*\*(?P<kind>{'|'.join(LANDMARK_KINDS)})\s+"
    rf"(?P<idx>{INDEX_RE})(?P<sep>\b[\s.:—-])"
)
LANDMARK_ITALIC_RE = re.compile(
    rf"^(?P<indent>\s*)\*(?P<kind>{'|'.join(LANDMARK_KINDS)})\s+"
    rf"(?P<idx>{INDEX_RE})(?P<sep>\s*[—:.])"
)

# Bare-ref detector for --init promotion.
# Two shapes (same as BARE_SEC_RE in validate-refs.py):
#   digit-first:  3.7.6, 4.4, 10.2.1   ([A-Z]?\d+(?:\.\d+)+)
#   letter-dot:   D.7, D.7.5, A.8.3    ([A-Z]\.\d+(?:\.\d+)*)
# Optional landmark suffix: ' Step 3', ' Part A', ' Lemma D.6-A', etc.
BARE_SEC_PROSE_RE = re.compile(
    r"(?<![\[\w/-])§"
    r"(?P<num>[A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)"
    r"(?P<tail>\s+(?P<kind>"
    + "|".join(LANDMARK_KINDS)
    + r")\s+(?P<idx>"
    + INDEX_RE
    + r"))?"
    r"(?![\w(])"
)


# -- Heading parsing -----------------------------------------------------

def scan_headings(lines):
    """Return list of (line_idx, sec_num, title)."""
    out = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            out.append((i, m.group("num"), m.group("title")))
    return out


def detect_duplicate_headings(headings):
    """Return list of duplicated sec_num occurrences as (num, first_idx, second_idx)."""
    seen = {}
    dups = []
    for line_idx, num, title in headings:
        if num in seen:
            dups.append((num, seen[num], line_idx))
        else:
            seen[num] = line_idx
    return dups


# -- Heading anchor injection -------------------------------------------

# An ATX heading: 2-6 `#` chars followed by at least one whitespace. The
# anchor injection point is immediately after this prefix.
_HEADING_ATX_RE = re.compile(r'^(#{2,6}\s+)')

# A column-0 `<a id="sec-...">` anchor — the LEGACY convention that
# `inject_heading_anchor()` now migrates off of. Detected so the
# function can strip it and re-inject in the correct post-ATX position.
_LEGACY_COL0_ANCHOR_RE = re.compile(r'^<a\s+id="sec-[^"]+"></a>')


def inject_heading_anchor(lines, line_idx, sec_num):
    """Ensure heading line has `### <a id="sec-NUM"></a>...` and `<!-- sec:NUM -->` above.

    Idempotent. Also performs the one-time migration from the legacy
    `<a id="sec-NUM"></a>### Title` (anchor at column 0, breaks CommonMark
    ATX heading parsing — bug 2026-05-25-02) to the correct
    `### <a id="sec-NUM"></a>Title` form (anchor after the ATX prefix).

    Mutates `lines` in place. Returns True if any change was made.
    """
    changed = False
    heading_line = lines[line_idx]
    expected_anchor = f'<a id="sec-{sec_num}"></a>'

    # Migration step: strip a pre-existing column-0 anchor so we can
    # re-inject it at the correct post-ATX position. Files written under
    # the old rule hit this branch on their first script run.
    legacy_match = _LEGACY_COL0_ANCHOR_RE.match(heading_line)
    if legacy_match:
        heading_line = heading_line[legacy_match.end():]
        changed = True

    # Locate the ATX prefix (the `### ` chars). If the heading line lost
    # its `#` prefix entirely we cannot place the anchor — surface that
    # to the caller; this should never happen in steady-state.
    atx_match = _HEADING_ATX_RE.match(heading_line)
    if not atx_match:
        if changed:
            # The legacy-strip left a non-heading line; restore so we
            # don't silently corrupt the source.
            lines[line_idx] = legacy_match.group(0) + heading_line
        return False

    atx_prefix = atx_match.group(1)
    rest = heading_line[atx_match.end():]

    # If the anchor is already in the right place at the start of `rest`,
    # we're done — write back only if the legacy-strip made a change.
    if rest.startswith(expected_anchor):
        if changed:
            lines[line_idx] = atx_prefix + rest
    else:
        lines[line_idx] = atx_prefix + expected_anchor + rest
        changed = True

    # `<!-- sec:NUM -->` on the line above — unchanged from the existing
    # convention; just ensure it is present.
    expected_marker = f"<!-- sec:{sec_num} -->"
    if line_idx == 0 or expected_marker not in lines[line_idx - 1]:
        lines.insert(line_idx, expected_marker)
        changed = True

    return changed


# -- Sub-landmark anchor injection --------------------------------------

def slug_suffix(kind, idx):
    """Compute the slug suffix for a sub-landmark anchor.

    'Step', '3'    -> 'step-3'
    'Step', '4a'   -> 'step-4a'
    'Part', 'A'    -> 'part-a'
    'Lemma', 'D.6-A' -> 'lemma-d.6-a'
    """
    return f"{kind.lower()}-{idx.lower()}"


def find_section_at(headings, line_idx):
    """Return the sec_num of the section containing line_idx.

    headings is the output of scan_headings() (must be sorted by line_idx).
    Returns None if line_idx is before the first heading.
    """
    current = None
    for h_line_idx, sec_num, _ in headings:
        if h_line_idx <= line_idx:
            current = sec_num
        else:
            break
    return current


def inject_sub_landmark_anchors(lines, headings):
    """Walk content lines and inject <!-- sec:X.Y.Z-suffix --> + <a id="sec-...">
    on sub-landmark lines that match the heuristic.

    Mutates `lines` in place. Returns (changed: bool, _placeholder: list).
    The second return value is a hook for the "unmatched-kind candidates"
    reporter that Task 2.6 may use; for now it's an empty list.
    """
    changed = False
    candidates = []  # reserved for future use

    i = 0
    while i < len(lines):
        line = lines[i]
        sec_num = find_section_at(headings, i)
        if sec_num is None:
            i += 1
            continue

        m = LANDMARK_BOLD_RE.match(line) or LANDMARK_ITALIC_RE.match(line)
        if not m:
            i += 1
            continue

        suffix = slug_suffix(m.group("kind"), m.group("idx"))
        anchor_id = f"sec-{sec_num}-{suffix}"
        expected_anchor = f'<a id="{anchor_id}"></a>'
        expected_marker = f"<!-- sec:{sec_num}-{suffix} -->"

        if expected_anchor in line:
            i += 1
            continue

        # Insert anchor inline at column 0 of the landmark line
        # and a sec-marker comment on the line above
        lines[i] = expected_anchor + line
        lines.insert(i, expected_marker)
        changed = True
        i += 2  # skip past inserted marker line and modified landmark line

    return changed, candidates


# -- Same-file secref rewriting -----------------------------------------

def collect_section_anchors(lines):
    """Return {anchor_id: line_idx} for all <a id='sec-...'> anchors in this file."""
    anchors = {}
    anchor_re = re.compile(r'<a\s+id="(sec-[\w.\-]+)"></a>')
    for i, line in enumerate(lines):
        for m in anchor_re.finditer(line):
            anchors[m.group(1)] = i
    return anchors


def _link_text_for_secref(sec_id, author_text):
    """Build the visible link text for a secref.

    For a section-only ID like "3.7.6": "§3.7.6"
    For a sub-anchor like "3.7.6-step-3": "§3.7.6 Step 3" (with Title-case kind)

    If the author wrote explicit link text (non-empty), preserve it.
    """
    if author_text:
        return author_text
    # Try to parse a sub-anchor ID
    # Format: "<num>-<kind>-<idx>" e.g. "3.7.6-step-3", "D.7-part-a"
    # We need to identify where the section number ends and the suffix begins.
    # The kind is one of LANDMARK_KINDS (lowercased); strategy: find the first
    # "-<kind>" substring where <kind> matches one of the known kinds.
    for kind in LANDMARK_KINDS:
        kind_low = kind.lower()
        marker = f"-{kind_low}-"
        idx_pos = sec_id.find(marker)
        if idx_pos >= 0:
            base_num = sec_id[:idx_pos]
            idx_part = sec_id[idx_pos + len(marker):]
            return f"§{base_num} {kind} {idx_part.upper() if len(idx_part) == 1 and idx_part.isalpha() else idx_part}"
        # Also handle "-<kind>" with no further suffix (rare, but possible)
        single_kind_end = f"-{kind_low}"
        if sec_id.endswith(single_kind_end):
            base_num = sec_id[:-len(single_kind_end)]
            return f"§{base_num} {kind}"
    # Section-only (no recognized kind suffix)
    return f"§{sec_id}"


def rewrite_same_file_secrefs(lines):
    """Rewrite <!-- secref:ID -->[...](...) links to point at #sec-ID.

    Returns (changed: bool, orphans: list[(line_idx, sec_id)]).
    """
    anchors = collect_section_anchors(lines)
    changed = False
    orphans = []

    for i, line in enumerate(lines):
        def replace(m, _i=i):
            nonlocal changed
            sec_id = m.group("id")
            target_anchor = f"sec-{sec_id}"
            if target_anchor not in anchors:
                orphans.append((_i, sec_id))
                return m.group(0)  # leave unchanged
            text = _link_text_for_secref(sec_id, m.group("text").strip())
            new_link = f'{m.group("marker")}[{text}](#{target_anchor})'
            if new_link != m.group(0):
                changed = True
            return new_link

        new_line = SECREF_INLINE_RE.sub(replace, line)
        if new_line != line:
            lines[i] = new_line

    return changed, orphans


# -- Cross-file secxref rewriting --------------------------------------

def build_survey_heading_index(survey_dir):
    """Walk survey files (respecting order.json) and return {sec_num: file_name}.

    Used by secxref resolution. Note that sec_num here is the SECTION number
    (e.g. "3.7.6", "D.7.5"), not a sub-anchor — sub-anchor refs (like
    "3.7.6-step-3") fall back to the parent section's owner file.
    """
    survey_dir = Path(survey_dir)
    order_json = survey_dir / "order.json"
    if order_json.exists():
        try:
            files = json.loads(order_json.read_text(encoding="utf-8"))
            if not isinstance(files, list):
                files = sorted(f.name for f in survey_dir.glob("*.md")
                          if not f.name.endswith(".index.md"))
        except (json.JSONDecodeError, OSError):
            files = sorted(f.name for f in survey_dir.glob("*.md")
                          if not f.name.endswith(".index.md"))
    else:
        files = sorted(f.name for f in survey_dir.glob("*.md")
                          if not f.name.endswith(".index.md"))

    index = {}
    for fname in files:
        fpath = survey_dir / fname
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line in text.split("\n"):
            m = HEADING_RE.match(line)
            if m:
                sec_num = m.group("num")
                # First definition wins; duplicates handled separately
                if sec_num not in index:
                    index[sec_num] = fname
    return index


def _strip_sub_anchor_suffix(sec_id):
    """Given a sec_id like 'D.7.5-part-a' or 'D.7.5', return the base section
    number 'D.7.5'.
    """
    for kind in LANDMARK_KINDS:
        kind_low = kind.lower()
        # Sub-anchor: <num>-<kind>-<idx>
        marker = f"-{kind_low}-"
        if marker in sec_id:
            return sec_id[:sec_id.index(marker)]
        # Edge case: <num>-<kind> with no idx (rare)
        single = f"-{kind_low}"
        if sec_id.endswith(single):
            return sec_id[:-len(single)]
    return sec_id


def rewrite_cross_file_secxrefs(lines, this_file_name, survey_index):
    """Rewrite <!-- secxref:ID -->[...](...) to point at the owning file.

    Returns (changed, orphans).
    """
    changed = False
    orphans = []

    for i, line in enumerate(lines):
        def replace(m, _i=i):
            nonlocal changed
            sec_id = m.group("id")
            base = _strip_sub_anchor_suffix(sec_id)
            owner = survey_index.get(base)
            if owner is None:
                orphans.append((_i, sec_id))
                return m.group(0)
            text = _link_text_for_secref(sec_id, m.group("text").strip())
            if owner == this_file_name:
                target = f"#sec-{sec_id}"
            else:
                target = f"{owner}#sec-{sec_id}"
            new_link = f'{m.group("marker")}[{text}]({target})'
            if new_link != m.group(0):
                changed = True
            return new_link

        new_line = SECXREF_INLINE_RE.sub(replace, line)
        if new_line != line:
            lines[i] = new_line

    return changed, orphans


# -- Bare-ref promotion (--init) ----------------------------------------

def bracket_spans_on_line(line):
    """Return list of (start, end) spans on `line` that are inside [...] brackets.

    Used to exclude bare-ref promotion of section refs that sit inside a
    bracketed citation like [Sesia et al. 2011, §17.5.2.3] or
    [Vaswani et al., 2017, §3.2].

    Note: this is a simple paired-bracket walker. It does not handle nested
    brackets in any sophisticated way — outer-most match wins. For prose,
    this is sufficient since markdown links don't nest [].
    """
    spans = []
    pos = 0
    while True:
        open_pos = line.find("[", pos)
        if open_pos < 0:
            break
        close_pos = line.find("]", open_pos + 1)
        if close_pos < 0:
            break
        spans.append((open_pos, close_pos + 1))
        pos = close_pos + 1
    return spans


def promote_bare_section_refs(lines, this_file_name, survey_index, anchors):
    """Rewrite bare '§X.Y.Z' (with optional ' Kind N' suffix) in prose to the
    marked + linked form.

    Skips '§X.Y.Z' that appears inside a [...] bracket (citation context).
    Also skips lines that are numbered reference-list entries (lines starting
    with [N] inside a ## References section).

    Returns (changed, unresolved: list[(line_idx, full_id)]).
    """
    changed = False
    unresolved = []
    in_references = False

    for i, line in enumerate(lines):
        # Track References section state
        if re.match(r"^##\s+References\b", line):
            in_references = True
            continue
        if re.match(r"^#{1,2}\s", line) and in_references:
            in_references = False

        # Skip reference-list entries
        if in_references and re.match(r"^\[\d+\]", line.lstrip()):
            continue

        b_spans = bracket_spans_on_line(line)

        def is_in_bracket(pos):
            return any(s <= pos < e for s, e in b_spans)

        # Walk matches manually to enable position-based exclusion.
        # `sub` with a callback skips matches the callback chooses to
        # preserve (returning m.group(0)).
        def replace(m, _i=i):
            nonlocal changed
            if is_in_bracket(m.start()):
                return m.group(0)  # inside citation bracket — skip
            sec_num = m.group("num")
            kind = m.group("kind")
            idx = m.group("idx")
            suffix = f"-{kind.lower()}-{idx.lower()}" if kind else ""
            full_id = f"{sec_num}{suffix}"

            target_anchor = f"sec-{full_id}"
            # Same-file: anchor exists in this file
            if target_anchor in anchors:
                text = f"§{sec_num}" + (f" {kind} {idx}" if kind else "")
                return (f"<!-- secref:{full_id} -->"
                        f"[{text}](#{target_anchor})")
            # Cross-file: section number resolves via survey index
            owner = survey_index.get(sec_num)
            if owner and owner != this_file_name:
                text = f"§{sec_num}" + (f" {kind} {idx}" if kind else "")
                return (f"<!-- secxref:{sec_num} -->"
                        f"[{text}]({owner}#sec-{sec_num})")
            # Cross-file but lookup returned this same file (anchor not yet
            # injected — shouldn't happen if heading-anchor pass ran first,
            # but guard anyway): treat as same-file fallback
            if owner == this_file_name:
                text = f"§{sec_num}" + (f" {kind} {idx}" if kind else "")
                return (f"<!-- secref:{full_id} -->"
                        f"[{text}](#{target_anchor})")
            # Unresolved
            unresolved.append((_i, full_id))
            return m.group(0)  # leave bare

        new_line = BARE_SEC_PROSE_RE.sub(replace, line)
        if new_line != line:
            lines[i] = new_line
            changed = True

    return changed, unresolved


# -- Per-file processing -------------------------------------------------

def process_file(path, args, survey_index):
    """Process a single file. Returns 0 on clean, 1 on drift/error."""
    original = path.read_text(encoding="utf-8")
    lines = original.split("\n")
    headings = scan_headings(lines)

    # Detect duplicate section numbers
    dups = detect_duplicate_headings(headings)
    if dups:
        for num, first, second in dups:
            print(f"{path}: duplicate section number {num} "
                  f"at line {first+1} and {second+1}", file=sys.stderr)
        return 1

    changed = False

    # Heading anchor injection (when running --init or no flag).
    # In --check mode, we don't mutate; we just compare what would change.
    if args.init or (not args.check and not args.dry_run_diff):
        # Heading-anchor pass
        headings_rev = scan_headings(lines)
        for line_idx, sec_num, _ in reversed(headings_rev):
            if inject_heading_anchor(lines, line_idx, sec_num):
                changed = True
        # Sub-landmark pass (re-scan first — line indices shift after heading inserts)
        sub_changed, _ = inject_sub_landmark_anchors(lines, scan_headings(lines))
        if sub_changed:
            changed = True

        # Bare-ref promotion: --init only (must run BEFORE secref rewriting
        # because it injects new <!-- secref:... --> markers that the rewriter
        # then resolves into linked form)
        if args.init:
            anchors = collect_section_anchors(lines)
            bare_changed, unresolved = promote_bare_section_refs(
                lines, path.name, survey_index, anchors
            )
            if bare_changed:
                changed = True
            for line_idx, full_id in unresolved:
                print(f"{path}:{line_idx+1}: bare §{full_id} unresolved - "
                      f"no matching sec-anchor in this directory",
                      file=sys.stderr)

        # Same-file secref rewriting
        ref_changed, orphans = rewrite_same_file_secrefs(lines)
        if ref_changed:
            changed = True
        for line_idx, sec_id in orphans:
            print(f"{path}:{line_idx+1}: orphaned secref:{sec_id} - "
                  f"no <a id='sec-{sec_id}'> in this file", file=sys.stderr)
        # Cross-file secxref rewriting
        xref_changed, xref_orphans = rewrite_cross_file_secxrefs(
            lines, path.name, survey_index
        )
        if xref_changed:
            changed = True
        for line_idx, sec_id in xref_orphans:
            print(f"{path}:{line_idx+1}: orphaned secxref:{sec_id} - "
                  f"section not found in any file in this directory",
                  file=sys.stderr)

    if args.check:
        check_lines = original.split("\n")
        # Heading-anchor pass — track which sections drifted for reporting
        drifted = []
        for line_idx, sec_num, _ in reversed(scan_headings(check_lines)):
            before = "\n".join(check_lines)
            inject_heading_anchor(check_lines, line_idx, sec_num)
            after = "\n".join(check_lines)
            if before != after:
                drifted.append(sec_num)
        # Sub-landmark pass
        inject_sub_landmark_anchors(check_lines, scan_headings(check_lines))
        # Same-file secref
        _, orphans = rewrite_same_file_secrefs(check_lines)
        # Cross-file secxref
        _, xref_orphans = rewrite_cross_file_secxrefs(
            check_lines, path.name, survey_index
        )
        if "\n".join(check_lines) != original:
            if drifted:
                for sec_num in sorted(set(drifted)):
                    print(f"{path}: drift detected - section {sec_num} anchor "
                          "missing or out of date", file=sys.stderr)
            else:
                print(f"{path}: drift detected (heading anchors, sub-landmarks, "
                      "or refs out of date)", file=sys.stderr)
            return 1
        if orphans:
            for line_idx, sec_id in orphans:
                print(f"{path}:{line_idx+1}: orphaned secref:{sec_id}",
                      file=sys.stderr)
            return 1
        if xref_orphans:
            for line_idx, sec_id in xref_orphans:
                print(f"{path}:{line_idx+1}: orphaned secxref:{sec_id}",
                      file=sys.stderr)
            return 1
        return 0

    if args.dry_run_diff:
        diff_lines = original.split("\n")
        # Heading-anchor pass
        for line_idx, sec_num, _ in reversed(scan_headings(diff_lines)):
            inject_heading_anchor(diff_lines, line_idx, sec_num)
        # Sub-landmark pass
        inject_sub_landmark_anchors(diff_lines, scan_headings(diff_lines))
        # Bare-ref promotion (only if --init was also requested)
        if args.init:
            anchors = collect_section_anchors(diff_lines)
            promote_bare_section_refs(diff_lines, path.name, survey_index, anchors)
        # Same-file + cross-file rewriting
        rewrite_same_file_secrefs(diff_lines)
        rewrite_cross_file_secxrefs(diff_lines, path.name, survey_index)
        diff_text = "\n".join(diff_lines)
        if diff_text != original:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                diff_text.splitlines(keepends=True),
                fromfile=str(path), tofile=str(path) + " (proposed)",
            )
            sys.stdout.writelines(diff)
        return 0

    new_text = "\n".join(lines)
    if changed:
        path.write_text(new_text, encoding="utf-8")
        print(f"{path}: updated")

    return 0


# -- CLI entry -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+",
                        help="Markdown file(s) or directory")
    parser.add_argument("--check", action="store_true",
                        help="Dry-run; exit non-zero on drift.")
    parser.add_argument("--init", action="store_true",
                        help="One-time bulk pass: inject all anchors + rewrite "
                             "bare refs to linked form.")
    parser.add_argument("--dry-run-diff", action="store_true",
                        help="Print proposed edits as unified diff without "
                             "writing.")
    args = parser.parse_args()

    rc = 0
    # Cache survey indices by directory so we don't rebuild for each file.
    index_cache = {}

    for target in args.paths:
        p = Path(target)
        if p.is_dir():
            files = sorted(p.rglob("*.md"))
        else:
            files = [p]
        for f in files:
            if "_scratch" in f.parts:
                continue
            if f.name.endswith(".index.md"):
                # Auto-generated section indexes (build-index.py) carry
                # positional heading numbers with source-file anchors; they
                # are not authored documents and would always fail the
                # heading-anchor check on letter-prefixed sources.
                continue
            survey_dir = f.parent
            if survey_dir not in index_cache:
                index_cache[survey_dir] = build_survey_heading_index(survey_dir)
            survey_index = index_cache[survey_dir]
            file_rc = process_file(f, args, survey_index)
            if file_rc:
                rc = file_rc
    sys.exit(rc)


if __name__ == "__main__":
    main()
