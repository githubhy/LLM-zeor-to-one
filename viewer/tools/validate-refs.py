#!/usr/bin/env python3
"""Validate cross-file references, equation anchors, and image paths.

Checks performed:
  1. Within-survey xref targets     <!-- xref:ID --> has matching <!-- eq:ID -->
  2. Cross-survey xref targets      <!-- xref:SURVEY:ID --> matches eq in target survey
  3. Anchor existence               #eq-N link targets have <a id="eq-N">
  4. Image paths                    ![](path) resolves to existing file
  5. order.json completeness        Every .md file is listed (warning)
  6. Duplicate eq IDs               No two <!-- eq:ID --> share same ID
  7. Orphaned refs                  <!-- ref:ID --> with no matching <!-- eq:ID -->
  8. Tag sequence                   \\tag{N} numbers are 1, 2, 3, ... per file
  9. Broken .md links               [text](file.md) target exists
 10. Cross-survey link paths        Relative path in xref resolves correctly
 11. Bare same-doc eq-ref           prose 'Eq. (N)' without <!-- ref:... --> marker
                                    (run via --bare-refs-only mode)
 12. Bare section-ref               prose 'sec X.Y.Z' without <!-- secref/secxref:... -->
                                    marker and #sec-X.Y.Z anchor target (run via
                                    --bare-refs-only mode)

Usage:
  python viewer/tools/validate-refs.py surveys/transformer-attention/
  python viewer/tools/validate-refs.py surveys/transformer-attention/ surveys/rag-systems/ --fix
  python viewer/tools/validate-refs.py surveys/transformer-attention/ --json
  python viewer/tools/validate-refs.py --bare-refs-only <files-or-dirs>
  python viewer/tools/validate-refs.py --bare-refs-only --severity=warn <files>
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ── Patterns ──────────────────────────────────────────────────────────────────
EQ_MARKER   = re.compile(r'<!--\s*eq:([\w.\-/]+)\s*-->')
REF_MARKER  = re.compile(r'<!--\s*ref:([\w.\-/]+)\s*-->')
XREF_COMMENT = re.compile(r'<!--\s*xref:([\w.\-/:]+)\s*-->')
XREF_FULL   = re.compile(
    r'\[\((\d+)\)\]\(([^)]+\.md)#eq-(\d+)\)\s*<!--\s*xref:([\w.\-/:]+)\s*-->'
)
ANCHOR_PAT  = re.compile(r'<a\s+id="eq-(\d+)"></a>')
TAG_PAT     = re.compile(r'\\tag\{(\d+)\}')
IMG_PAT     = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
MD_LINK     = re.compile(r'\[[^\]]*\]\(([^)]*\.md)(?:#([^)]*))?\)')
ANCHOR_LINK = re.compile(r'\[[^\]]*\]\(#(eq-\d+)\)')

# ── Bare-ref check patterns (#11 + #12) ──────────────────────────────────────

BARE_EQ_RE = re.compile(r"\b(?:Eqs?\.|Equations?)\s+\((\d+)\)")

# Two shapes:
#   digit-first: 3.7.6, 4.4, 10.2.1            ([A-Z]?\d+(?:\.\d+)+)
#   letter-dot:  D.7, D.7.5, A.8.3, B.2.1      ([A-Z]\.\d+(?:\.\d+)*)
# Both shapes require at least one dot — bare §4 (single number, no dot) is
# intentionally NOT matched because it is ambiguous (could be an external citation).
BARE_SEC_RE = re.compile(
    r"§([A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)"
)

# Citation-context heuristics for the #11 exemption.
AUTHOR_YEAR_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s+\d{4}\b")
SOURCE_PREFIX_RE = re.compile(
    r"(?i)(?:\bsource\s*:|\[source\]|\b(?:from|after)\s+(?:\[|[A-Z][a-z]+))"
)
BIB_BRACKET_RE = re.compile(r"\[\d+(?:\s*,\s*\d+)*\s*,\s*Eqs?\.?\s*\(\d+\)\]")

# Verified-form recognizer for #11.
EQ_REF_MARKER_RE = re.compile(r"<!--\s*ref:[\w.\-/]+\s*-->")
EQ_LINKED_RE = re.compile(r"\[\(\d+\)\]\(#eq-\d+\)")

# Verified / legacy recognizers for #12.
SECREF_MARKER_RE = re.compile(r"<!--\s*sec(?:ref|xref):[\w.\-/]+\s*-->")
SEC_LINKED_RE = re.compile(
    r"\[[^\]]*§(?:[A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)[^\]]*\]\(([^)]+)\)"
)


def compute_fence_state(lines):
    """Walk lines and return a list[bool], True iff that line is inside a fence."""
    state = [False] * len(lines)
    in_fence = False
    fence_marker = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_fence:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)[0] * len(m.group(1))
                state[i] = True
                continue
        else:
            state[i] = True
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
    return state


def compute_display_math_state(lines):
    """Walk lines and return a list[bool], True iff inside a $$ ... $$ block."""
    state = [False] * len(lines)
    in_math = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            state[i] = True
            continue
        if s.startswith("$$"):
            state[i] = True
            in_math = not in_math
            continue
        if in_math:
            state[i] = True
    return state


def compute_comment_state(lines):
    """List[bool], True iff the line is entirely inside a multi-line HTML comment.

    Single-line self-contained <!--...--> spans do NOT mark the whole line as
    in-comment — those are handled at character-span granularity in the per-line
    check via comment_spans_on_line().  Only lines that are fully inside an
    unclosed multi-line comment (opened on a previous line and not yet closed)
    are marked True here.
    """
    state = [False] * len(lines)
    in_comment = False
    for i, line in enumerate(lines):
        if in_comment:
            state[i] = True
            if "-->" in line:
                in_comment = False
            continue
        # Not currently in a multi-line comment — check if this line opens one
        # without closing it.
        comment_open = line.find("<!--")
        if comment_open >= 0:
            # Is there a matching --> after the opening?
            if "-->" not in line[comment_open + 4:]:
                in_comment = True
        # state[i] stays False — span-level exclusion handled per match below
    return state


def comment_spans_on_line(line):
    """Return list of (start, end) spans that are inside an HTML comment on `line`.

    Covers self-contained <!--...--> spans.  For an open <!-- with no closing -->
    on the same line, returns (open_pos, len(line)).
    """
    spans = []
    pos = 0
    while True:
        open_pos = line.find("<!--", pos)
        if open_pos < 0:
            break
        close_pos = line.find("-->", open_pos + 4)
        if close_pos < 0:
            spans.append((open_pos, len(line)))
            break
        spans.append((open_pos, close_pos + 3))
        pos = close_pos + 3
    return spans


def bracket_spans_on_line(line):
    """Return list of (start, end) spans inside a [...] bracket pair on this line.

    Uses the same paired-bracket walker as renumber-sections.py so that both
    the --init promotion tool and the validator agree on what counts as a
    citation-bracket context.
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


def check_bare_eq_refs(path):
    """Run check #11 on a single file. Return list of (lineno, col, msg) findings."""
    findings = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [(0, 0, f"could not read {path}: {e}")]
    lines = text.split("\n")
    fence = compute_fence_state(lines)
    math = compute_display_math_state(lines)
    comment = compute_comment_state(lines)

    in_references = False  # set True after a "## References" heading

    for i, line in enumerate(lines):
        if re.match(r"^##\s+References\b", line):
            in_references = True
            continue
        if re.match(r"^#{1,2}\s", line) and in_references:
            in_references = False
        if fence[i] or math[i] or comment[i]:
            continue

        # Per-line comment spans: handles inline <!-- ... --> after which prose continues
        c_spans = comment_spans_on_line(line)

        for m in BARE_EQ_RE.finditer(line):
            col = m.start()
            # Skip if match falls inside an HTML comment span on this line
            if any(s <= col < e for s, e in c_spans):
                continue
            # Inside reference-list line opener "[N] author, ..."
            if in_references and re.match(r"^\[\d+\]", line.lstrip()):
                continue
            # Preceded by <!-- ref:... --> within 30 chars
            window_start = max(0, col - 30)
            prefix = line[window_start:col]
            if EQ_REF_MARKER_RE.search(prefix):
                continue
            # Citation context: author-year within 40 chars before
            cite_window = line[max(0, col - 40):col]
            if AUTHOR_YEAR_RE.search(cite_window):
                continue
            if SOURCE_PREFIX_RE.search(line[:col]):
                continue
            if BIB_BRACKET_RE.search(line):
                if any(
                    bm.start() <= m.start() < bm.end()
                    for bm in BIB_BRACKET_RE.finditer(line)
                ):
                    continue
            msg = (
                f"bare same-doc eq-ref '{m.group(0)}': "
                "add <!-- ref:<ID> -->[(N)](#eq-N) marker, or if this is "
                "an external-paper citation, place it inside a citation "
                "context (author-year or [bib-N, Eq (...)])"
            )
            findings.append((i + 1, col + 1, msg))
    return findings


def check_bare_section_refs(path):
    """Run check #12 on a single file. Return list of (lineno, col, level, msg).

    level in {"error", "warn"} -- legacy non-#sec-... link form is reported as warn.
    """
    findings = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [(0, 0, "error", f"could not read {path}: {e}")]
    lines = text.split("\n")
    fence = compute_fence_state(lines)
    math = compute_display_math_state(lines)
    comment = compute_comment_state(lines)

    # Enumerator-shaped landmark detector (for sub-anchor suggestion in the
    # error message -- matches what renumber-sections.py heuristic will catch).
    enum_re = re.compile(
        r"^\s+(Step|Stage|Phase|Case|Part|Path|Variant|Branch|Note|Item|"
        r"Assumption|Lemma|Theorem|Proposition|Corollary|Definition|Example|"
        r"Remark|Algorithm|Procedure|Fact|Claim|Table|Figure)\s+"
        r"(\d+[a-z]?|[A-Z]|[A-Z]?\d+(?:\.\d+)*-[A-Z0-9]+)\b"
    )

    for i, line in enumerate(lines):
        if fence[i] or math[i] or comment[i]:
            continue

        # Per-line comment spans (inline <!-- ... --> span exclusion at
        # char-span granularity)
        c_spans = comment_spans_on_line(line)

        # Bracket spans for citation-bracket exclusion — any [...] bracket
        # containing the §X.Y.Z match is treated as a citation-bracket context
        # (matching the same logic in renumber-sections.py --init).
        b_spans = bracket_spans_on_line(line)

        for m in BARE_SEC_RE.finditer(line):
            col = m.start()
            sec_num = m.group(1)

            # Skip if match falls inside an HTML comment span on this line
            if any(s <= col < e for s, e in c_spans):
                continue

            # Is this SS inside a markdown link [...SSX.Y.Z...](target)?
            # Guard: reject SEC_LINKED_RE matches whose text span exceeds 200
            # chars — those are greedy artifacts where a [math bracket early
            # in the line triggers a spurious match all the way to a §X.Y.Z
            # link later in the same line.
            link_match = None
            for lm in SEC_LINKED_RE.finditer(line):
                if lm.start() <= m.start() < lm.end():
                    # Reject if the link text span is implausibly long.
                    # Real markdown section-ref links like [§D.7.5 Part D](url)
                    # are at most ~120 chars; longer spans indicate the regex
                    # was confused by a math-bracket [0, \beta) or [0, 1) earlier
                    # in the line.
                    if lm.end() - lm.start() > 120:
                        break
                    link_match = lm
                    break

            if link_match:
                target = link_match.group(1)
                # Verified iff target matches #sec-NUM or file.md#sec-NUM
                sec_target_re = re.compile(
                    rf"^(?:[^#)]+\.md)?#sec-{re.escape(sec_num)}(?:-[\w.\-]+)?$"
                )
                if sec_target_re.match(target):
                    # Also require a <!-- secref:... --> or <!-- secxref:... -->
                    # marker within 40 chars before the [ immediately preceding §.
                    # Use m.start()-1 (the [ char before §) not link_match.start()
                    # because the greedy SEC_LINKED_RE may start far before the
                    # actual [§...](target) link when a math [0, x) bracket
                    # appears earlier on the same line.
                    actual_bracket = m.start() - 1  # the '[' immediately before §
                    window = line[max(0, actual_bracket - 40):actual_bracket]
                    if SECREF_MARKER_RE.search(window):
                        continue  # verified -- pass
                    # Linked but missing marker -- still error
                    msg = (
                        f"section-ref '§{sec_num}' is linked but missing "
                        "<!-- secref:... --> or <!-- secxref:... --> marker"
                    )
                    findings.append((i + 1, col + 1, "error", msg))
                    continue
                # Legacy target (e.g., #t430-lifecycle) -- transitional warning
                msg = (
                    f"legacy section-ref form '§{sec_num}' -> '{target}': "
                    "migrate to #sec-X.Y.Z via renumber-sections.py --init"
                )
                findings.append((i + 1, col + 1, "warn", msg))
                continue

            # Skip if inside a [...] bracket — citation context (e.g.,
            # [Vaswani et al., 2017, §3.2] or [RFC 8259 §7]).
            # This mirrors the bracket_spans_on_line exclusion in --init.
            if any(s <= col < e for s, e in b_spans):
                continue

            # Bare section sign not inside any link -- error
            tail = line[m.end():m.end() + 60]
            sub_anchor_hint = ""
            em = enum_re.match(tail)
            if em:
                kind = em.group(1).lower()
                idx = em.group(2).lower()
                sub_anchor_hint = (
                    f" (or sub-anchor form: <!-- secref:{sec_num}-{kind}-{idx} -->"
                    f"[§{sec_num} {em.group(1)} {em.group(2)}]"
                    f"(#sec-{sec_num}-{kind}-{idx}))"
                )
            msg = (
                f"bare section-ref '§{sec_num}': "
                f"add <!-- secref:{sec_num} -->[§{sec_num}](#sec-{sec_num}) "
                f"marker (use renumber-sections.py --init to auto-link bare "
                f"refs){sub_anchor_hint}"
            )
            findings.append((i + 1, col + 1, "error", msg))
    return findings


# ── Survey scanning ──────────────────────────────────────────────────────────
def list_md_files(survey_dir):
    """List .md files respecting order.json if present."""
    order_file = survey_dir / 'order.json'
    if order_file.exists():
        try:
            ordered = json.loads(order_file.read_text(encoding='utf-8'))
            return [f for f in ordered if (survey_dir / f).exists()]
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(f.name for f in survey_dir.glob('*.md'))


def scan_survey(survey_dir):
    """Parse all .md files in a survey and return structured data."""
    survey_dir = Path(survey_dir).resolve()
    md_files = list_md_files(survey_dir)

    eq_map   = {}   # eq_id -> {'file': str, 'tag': int|None, 'line': int}
    refs     = []   # (file, line, ref_id)
    xrefs    = []   # (file, line, xref_id, link_text_num, link_file, link_anchor_num)
    anchors  = {}   # file -> set of int (anchor numbers)
    tags     = {}   # file -> list of int (tag numbers in order)
    images   = []   # (file, line, img_path)
    md_links_list = []  # (file, line, link_file, link_anchor)

    for md_file in md_files:
        filepath = survey_dir / md_file
        text = filepath.read_text(encoding='utf-8')
        lines = text.split('\n')

        file_anchors = set()
        file_tags = []

        for lineno, line in enumerate(lines, 1):
            # Equation markers
            for m in EQ_MARKER.finditer(line):
                eq_id = m.group(1)
                anchor_m = ANCHOR_PAT.search(line)
                tag_num = int(anchor_m.group(1)) if anchor_m else None
                eq_map[eq_id] = {'file': md_file, 'tag': tag_num, 'line': lineno}

            # Anchors
            for m in ANCHOR_PAT.finditer(line):
                file_anchors.add(int(m.group(1)))

            # Tags
            for m in TAG_PAT.finditer(line):
                file_tags.append(int(m.group(1)))

            # Within-file refs
            for m in REF_MARKER.finditer(line):
                refs.append((md_file, lineno, m.group(1)))

            # Cross-file xrefs (full pattern with link)
            for m in XREF_FULL.finditer(line):
                xrefs.append((md_file, lineno, m.group(4),
                              int(m.group(1)), m.group(2), int(m.group(3))))

            # Xrefs without full link match (comment only)
            for m in XREF_COMMENT.finditer(line):
                xref_id = m.group(1)
                if not any(x[2] == xref_id and x[0] == md_file and x[1] == lineno
                           for x in xrefs):
                    xrefs.append((md_file, lineno, xref_id, None, None, None))

            # Images
            for m in IMG_PAT.finditer(line):
                path = m.group(1)
                if not path.startswith('http'):
                    images.append((md_file, lineno, path))

            # MD links (not already captured as xrefs)
            for m in MD_LINK.finditer(line):
                link_file = m.group(1)
                link_anchor = m.group(2)
                if not link_file.startswith('http'):
                    md_links_list.append((md_file, lineno, link_file, link_anchor))

            # In-file anchor links
            for m in ANCHOR_LINK.finditer(line):
                anchor_name = m.group(1)
                num = int(anchor_name.replace('eq-', ''))
                md_links_list.append((md_file, lineno, None, anchor_name))

        anchors[md_file] = file_anchors
        tags[md_file] = file_tags

    return {
        'dir': survey_dir,
        'name': survey_dir.name,
        'files': md_files,
        'eq_map': eq_map,
        'refs': refs,
        'xrefs': xrefs,
        'anchors': anchors,
        'tags': tags,
        'images': images,
        'md_links': md_links_list,
    }


# ── Validation checks ────────────────────────────────────────────────────────
def validate(survey, all_surveys):
    """Run all checks on a scanned survey. Returns (errors, warnings)."""
    errors = []
    warnings = []
    eq_map = survey['eq_map']
    survey_dir = survey['dir']

    # Build cross-survey eq maps
    cross_eq = {}  # survey_name -> eq_map
    for s in all_surveys:
        cross_eq[s['name']] = s['eq_map']

    # Check 6: Duplicate eq IDs
    seen_ids = {}
    for eq_id, info in eq_map.items():
        if eq_id in seen_ids:
            errors.append(f"Duplicate eq ID '{eq_id}' in {info['file']}:{info['line']} "
                          f"and {seen_ids[eq_id]}")
        seen_ids[eq_id] = f"{info['file']}:{info['line']}"

    # Check 7: Orphaned refs
    orphaned = 0
    for md_file, lineno, ref_id in survey['refs']:
        if ref_id not in eq_map:
            errors.append(f"Orphaned ref '{ref_id}' in {md_file}:{lineno}")
            orphaned += 1

    # Check 1 & 2: Xref targets
    within_xrefs_ok = 0
    cross_xrefs = {}  # target_survey -> count
    for md_file, lineno, xref_id, link_num, link_file, link_anchor in survey['xrefs']:
        if ':' in xref_id:
            # Cross-survey xref
            parts = xref_id.split(':', 1)
            target_survey = parts[0]
            target_eq_id = parts[1]
            cross_xrefs.setdefault(target_survey, 0)
            if target_survey not in cross_eq:
                warnings.append(
                    f"Cross-survey xref '{xref_id}' in {md_file}:{lineno} — "
                    f"target survey '{target_survey}' not loaded (pass its directory to validate)")
            elif target_eq_id not in cross_eq[target_survey]:
                errors.append(
                    f"Cross-survey xref '{xref_id}' in {md_file}:{lineno} — "
                    f"eq ID '{target_eq_id}' not found in survey '{target_survey}'")
            else:
                cross_xrefs[target_survey] += 1
                # Check 10: verify link path resolves
                if link_file:
                    target_info = cross_eq[target_survey][target_eq_id]
                    expected_file = f"../{target_survey}/{target_info['file']}"
                    if link_file != expected_file:
                        full_path = (survey_dir / link_file).resolve()
                        if not full_path.exists():
                            errors.append(
                                f"Cross-survey xref link path '{link_file}' in "
                                f"{md_file}:{lineno} does not resolve")
                    # Check link anchor matches current tag
                    if link_anchor is not None and target_info['tag'] is not None:
                        if link_anchor != target_info['tag']:
                            errors.append(
                                f"Stale cross-survey xref in {md_file}:{lineno} — "
                                f"links to eq-{link_anchor} but current tag is "
                                f"{target_info['tag']}")
        else:
            # Within-survey xref
            if xref_id not in eq_map:
                errors.append(
                    f"Xref '{xref_id}' in {md_file}:{lineno} — "
                    f"no matching eq marker found")
            else:
                within_xrefs_ok += 1
                # Check link anchor matches current tag
                if link_anchor is not None:
                    target_info = eq_map[xref_id]
                    if target_info['tag'] is not None and link_anchor != target_info['tag']:
                        errors.append(
                            f"Stale xref in {md_file}:{lineno} — "
                            f"links to eq-{link_anchor} but current tag is "
                            f"{target_info['tag']}")

    # Check 3: Anchor existence for in-file anchor links
    for md_file, lineno, link_file, link_anchor in survey['md_links']:
        if link_file is None and link_anchor and link_anchor.startswith('eq-'):
            num = int(link_anchor.replace('eq-', ''))
            if md_file in survey['anchors'] and num not in survey['anchors'][md_file]:
                errors.append(
                    f"Anchor #{link_anchor} referenced in {md_file}:{lineno} "
                    f"does not exist in {md_file}")

    # Check 4: Image paths
    images_ok = 0
    for md_file, lineno, img_path in survey['images']:
        full_path = (survey_dir / img_path).resolve()
        if full_path.exists():
            images_ok += 1
        else:
            errors.append(f"Image not found: '{img_path}' in {md_file}:{lineno}")

    # Check 5: order.json completeness
    order_file = survey_dir / 'order.json'
    if order_file.exists():
        try:
            ordered = json.loads(order_file.read_text(encoding='utf-8'))
            all_md = {f.name for f in survey_dir.glob('*.md')}
            ordered_set = set(ordered)
            missing = all_md - ordered_set
            for f in sorted(missing):
                warnings.append(f"'{f}' not listed in order.json")
        except (json.JSONDecodeError, TypeError):
            warnings.append("order.json exists but is not valid JSON")
    else:
        warnings.append("No order.json found")

    # Check 8: Tag sequence per file
    tag_seq_ok = True
    for md_file in survey['files']:
        file_tags = survey['tags'].get(md_file, [])
        if file_tags:
            expected = list(range(1, len(file_tags) + 1))
            if file_tags != expected:
                tag_seq_ok = False
                errors.append(
                    f"Tag sequence broken in {md_file}: "
                    f"got {file_tags[:5]}{'...' if len(file_tags) > 5 else ''}, "
                    f"expected {expected[:5]}{'...' if len(expected) > 5 else ''}")

    # Check 9: Broken .md links
    links_ok = 0
    for md_file, lineno, link_file, link_anchor in survey['md_links']:
        if link_file is None:
            continue
        # Resolve relative path
        if link_file.startswith('../'):
            full_path = (survey_dir / link_file).resolve()
        else:
            full_path = (survey_dir / link_file).resolve()
        if full_path.exists():
            links_ok += 1
        else:
            errors.append(f"Broken link: '{link_file}' in {md_file}:{lineno}")

    # Count files with tags
    files_with_tags = sum(1 for f in survey['files'] if survey['tags'].get(f))

    # Build summary
    summary = {
        'survey': survey['name'],
        'eq_count': len(eq_map),
        'within_xrefs_ok': within_xrefs_ok,
        'within_xrefs_total': sum(1 for _, _, xid, *_ in survey['xrefs'] if ':' not in xid),
        'cross_xrefs': cross_xrefs,
        'cross_xrefs_total': sum(1 for _, _, xid, *_ in survey['xrefs'] if ':' in xid),
        'anchors_total': sum(len(v) for v in survey['anchors'].values()),
        'images_ok': images_ok,
        'images_total': len(survey['images']),
        'refs_total': len(survey['refs']),
        'orphaned_refs': orphaned,
        'tag_seq_ok': tag_seq_ok,
        'files_with_tags': files_with_tags,
        'links_ok': links_ok,
        'links_total': sum(1 for _, _, lf, _ in survey['md_links'] if lf is not None),
        'errors': errors,
        'warnings': warnings,
    }
    return summary


# ── Fix mode ──────────────────────────────────────────────────────────────────
def fix_survey(survey, all_surveys):
    """Auto-fix stale xref links. Returns count of fixes applied."""
    eq_map = survey['eq_map']
    survey_dir = survey['dir']

    cross_eq = {}
    for s in all_surveys:
        cross_eq[s['name']] = s['eq_map']

    fixes = 0
    for md_file in survey['files']:
        filepath = survey_dir / md_file
        text = filepath.read_text(encoding='utf-8')
        original = text

        # Fix xref links with stale numbers
        def fix_xref(m):
            nonlocal fixes
            link_num = m.group(1)
            link_file = m.group(2)
            link_anchor = m.group(3)
            xref_id = m.group(4)

            if ':' in xref_id:
                parts = xref_id.split(':', 1)
                target_survey, target_eq_id = parts
                if target_survey in cross_eq and target_eq_id in cross_eq[target_survey]:
                    info = cross_eq[target_survey][target_eq_id]
                    new_tag = info['tag']
                    new_file = f"../{target_survey}/{info['file']}"
                    if new_tag is not None:
                        new = f"[({new_tag})]({new_file}#eq-{new_tag}) <!-- xref:{xref_id} -->"
                        if new != m.group(0):
                            fixes += 1
                            return new
            else:
                if xref_id in eq_map:
                    info = eq_map[xref_id]
                    new_tag = info['tag']
                    target_file = info['file']
                    if new_tag is not None:
                        new = f"[({new_tag})]({target_file}#eq-{new_tag}) <!-- xref:{xref_id} -->"
                        if new != m.group(0):
                            fixes += 1
                            return new
            return m.group(0)

        text = XREF_FULL.sub(fix_xref, text)

        if text != original:
            filepath.write_text(text, encoding='utf-8')
            print(f"  Fixed xrefs in {md_file}")

    return fixes


# ── Output ────────────────────────────────────────────────────────────────────
def print_results(summary):
    """Print human-readable validation results."""
    s = summary
    ok = '\u2713'
    fail = '\u2717'

    print(f"\n{s['survey']}/")

    # Xrefs
    total_within = s['within_xrefs_total']
    if total_within > 0:
        icon = ok if s['within_xrefs_ok'] == total_within else fail
        print(f"  {icon} {total_within} cross-file xrefs — "
              f"{s['within_xrefs_ok']} valid")
    if s['cross_xrefs_total'] > 0:
        for target, count in s['cross_xrefs'].items():
            icon = ok if count > 0 else fail
            print(f"  {icon} {count} cross-survey xrefs -> {target}")

    # Equations and anchors
    icon = ok if not s['orphaned_refs'] else fail
    print(f"  {icon} {s['eq_count']} equation markers — "
          f"{s['orphaned_refs']} orphaned refs")

    icon = ok if s['anchors_total'] >= s['eq_count'] else fail
    print(f"  {icon} {s['anchors_total']} equation anchors")

    # Images
    if s['images_total'] > 0:
        icon = ok if s['images_ok'] == s['images_total'] else fail
        print(f"  {icon} {s['images_total']} image references — "
              f"{s['images_ok']} valid")

    # Tag sequence
    icon = ok if s['tag_seq_ok'] else fail
    print(f"  {icon} Tag sequences {'correct' if s['tag_seq_ok'] else 'BROKEN'} "
          f"in {s['files_with_tags']} files")

    # Links
    if s['links_total'] > 0:
        icon = ok if s['links_ok'] == s['links_total'] else fail
        print(f"  {icon} {s['links_total']} .md links — {s['links_ok']} valid")

    # Errors and warnings
    if s['errors']:
        print(f"\n  Errors ({len(s['errors'])}):")
        for e in s['errors']:
            print(f"    {fail} {e}")
    if s['warnings']:
        print(f"\n  Warnings ({len(s['warnings'])}):")
        for w in s['warnings']:
            print(f"    ! {w}")


def print_json_results(summaries):
    """Print JSON output for CI integration."""
    output = {
        'surveys': [],
        'total_errors': 0,
        'total_warnings': 0,
    }
    for s in summaries:
        output['surveys'].append({
            'name': s['survey'],
            'equations': s['eq_count'],
            'xrefs_within': s['within_xrefs_total'],
            'xrefs_cross': s['cross_xrefs_total'],
            'images': s['images_total'],
            'errors': s['errors'],
            'warnings': s['warnings'],
        })
        output['total_errors'] += len(s['errors'])
        output['total_warnings'] += len(s['warnings'])
    print(json.dumps(output, indent=2))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Ensure UTF-8 output on Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('dirs', nargs='+',
                        help='One or more survey directories to validate (or file paths '
                             'when --bare-refs-only is set)')
    parser.add_argument('--fix', action='store_true',
                        help='Auto-fix stale xref link numbers')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    parser.add_argument(
        '--bare-refs-only', action='store_true',
        help='Run only the bare-ref checks (#11 + #12) on the given file paths. '
             'Skips the full survey-wide cross-ref walk.'
    )
    parser.add_argument(
        '--severity', choices=['error', 'warn'], default='error',
        help='Severity for bare-ref findings (default: error). '
             'Used during the warn-only migration window before enforcement.'
    )
    args = parser.parse_args()

    # --bare-refs-only: single-file mode, short-circuits before survey-walk logic
    if args.bare_refs_only:
        rc = 0
        for target in args.dirs:
            p = Path(target)
            files = [p] if p.is_file() else sorted(p.rglob('*.md'))
            for f in files:
                # Honor exempt paths
                if '_scratch' in f.parts or 'specs' in f.parts:
                    continue
                eq_findings = check_bare_eq_refs(f)
                for lineno, col, msg in eq_findings:
                    print(f'{f}:{lineno}:{col}: {msg}')
                if eq_findings and args.severity == 'error':
                    rc = 1

                sec_findings = check_bare_section_refs(f)
                for lineno, col, level, msg in sec_findings:
                    label = "WARN" if level == "warn" else "ERROR"
                    print(f'{f}:{lineno}:{col}: [{label}] {msg}')
                if sec_findings and args.severity == 'error':
                    if any(level == 'error' for _, _, level, _ in sec_findings):
                        rc = 1
        sys.exit(rc)

    # Scan all surveys
    surveys = []
    for d in args.dirs:
        p = Path(d)
        if not p.is_dir():
            print(f"Not a directory: {d}", file=sys.stderr)
            sys.exit(1)
        surveys.append(scan_survey(p))

    # Fix mode
    if args.fix:
        total_fixes = 0
        for survey in surveys:
            fixes = fix_survey(survey, surveys)
            total_fixes += fixes
        print(f"\nApplied {total_fixes} fix(es). Re-validating...")
        # Re-scan after fixes
        surveys = [scan_survey(Path(d)) for d in args.dirs]

    # Validate
    summaries = []
    for survey in surveys:
        summaries.append(validate(survey, surveys))

    # Output
    if args.json:
        print_json_results(summaries)
    else:
        for s in summaries:
            print_results(s)

    total_errors = sum(len(s['errors']) for s in summaries)
    if not args.json:
        print(f"\nTotal: {total_errors} error(s), "
              f"{sum(len(s['warnings']) for s in summaries)} warning(s)")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == '__main__':
    main()
