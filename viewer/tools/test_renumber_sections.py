"""Tests for renumber-sections.py.

Covers: heading-anchor injection, sub-landmark heuristic injection,
ref rewriting (same-file + cross-file), idempotency, --check drift
detection, and the --init bulk-conversion pass.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "renumber-sections.py"


def run(args, cwd=None):
    """Invoke renumber-sections.py with args; return (rc, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout, r.stderr


# -- Heading anchor injection --------------------------------------


def test_heading_anchor_inserted_on_init(tmp_path):
    """### 3.7.6 Title -> <!-- sec:3.7.6 --> + <a id='sec-3.7.6'> injected."""
    f = tmp_path / "doc.md"
    f.write_text("# Top\n\n### 3.7.6 Quantization of the LLRs\n\nContent.\n",
                 encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert '<!-- sec:3.7.6 -->' in result
    assert '<a id="sec-3.7.6"></a>' in result


def test_heading_anchor_placed_after_atx_prefix(tmp_path):
    """Anchor must sit AFTER the `### ` ATX prefix, not before it (bug 2026-05-25-02).

    CommonMark requires `#` at column 0-3 for ATX headings. A leading
    <a id> at column 0 demotes the line to a paragraph with literal `###`
    visible in the rendered body. Anchor must be placed immediately after
    the ATX prefix so the heading parses correctly on both viewer and
    GitHub.
    """
    f = tmp_path / "doc.md"
    f.write_text("# Top\n\n### 3.7.6 Quantization of the LLRs\n\nContent.\n",
                 encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    # The exact line should be `### <a id="sec-3.7.6"></a>3.7.6 ...`
    assert '### <a id="sec-3.7.6"></a>3.7.6 Quantization of the LLRs' in result, \
        f"anchor not placed after `### ` prefix in:\n{result}"
    # And the legacy column-0 form must NOT appear:
    assert '<a id="sec-3.7.6"></a>###' not in result, \
        f"legacy column-0 form still present in:\n{result}"


def test_heading_anchor_h4_h5_h6_placement(tmp_path):
    """The post-ATX-prefix placement also applies to #### / ##### / ######."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.7 Parent\n\n"
        "#### 3.7.6 H4 sub\n\n"
        "##### 3.7.6.1 H5 leaf\n\n"
        "###### 3.7.6.1.1 H6 leaf\n\n"
        "Content.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert '### <a id="sec-3.7"></a>3.7 Parent' in result
    assert '#### <a id="sec-3.7.6"></a>3.7.6 H4 sub' in result
    assert '##### <a id="sec-3.7.6.1"></a>3.7.6.1 H5 leaf' in result
    assert '###### <a id="sec-3.7.6.1.1"></a>3.7.6.1.1 H6 leaf' in result


def test_legacy_column_0_anchor_migrated_to_post_atx(tmp_path):
    """A pre-existing column-0 <a id> anchor must be stripped and re-injected
    after the `### ` prefix. This is the migration path for files written
    under the old (broken) convention.
    """
    f = tmp_path / "doc.md"
    # Author the file in the legacy column-0 form
    f.write_text(
        '# Top\n\n'
        '<!-- sec:3.7.6 -->\n'
        '<a id="sec-3.7.6"></a>### 3.7.6 Quantization of the LLRs\n\n'
        'Content.\n',
        encoding="utf-8"
    )
    # NB: run WITHOUT --init; this is the maintenance pass that should
    # detect and migrate the legacy anchor.
    rc, out, err = run([str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    # New form present:
    assert '### <a id="sec-3.7.6"></a>3.7.6 Quantization of the LLRs' in result
    # Legacy column-0 form gone:
    assert '<a id="sec-3.7.6"></a>###' not in result
    # The <!-- sec:3.7.6 --> marker is preserved (we did NOT add a duplicate)
    assert result.count('<!-- sec:3.7.6 -->') == 1


def test_legacy_migration_idempotent(tmp_path):
    """Once migrated, re-running the script on the same file is a no-op."""
    f = tmp_path / "doc.md"
    f.write_text(
        '<!-- sec:3.7.6 -->\n'
        '<a id="sec-3.7.6"></a>### 3.7.6 Quantization\n\n'
        'Content.\n',
        encoding="utf-8"
    )
    run([str(f)])
    after_first = f.read_text(encoding="utf-8")
    rc, out, err = run([str(f)])
    assert rc == 0
    after_second = f.read_text(encoding="utf-8")
    assert after_first == after_second, \
        f"second run produced a diff:\n--- first ---\n{after_first}\n--- second ---\n{after_second}"


def test_duplicate_anchors_legacy_and_new_deduped(tmp_path):
    """If both legacy and new-form anchors coexist on the heading line (a
    half-migrated file), the legacy one is stripped and only the new-form
    survives. No duplicate anchors in the heading line.
    """
    f = tmp_path / "doc.md"
    f.write_text(
        '<!-- sec:3.7.6 -->\n'
        '<a id="sec-3.7.6"></a>### <a id="sec-3.7.6"></a>3.7.6 Heading\n\n'
        'Content.\n',
        encoding="utf-8"
    )
    rc, out, err = run([str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    # Find the heading line and assert it has exactly one anchor
    heading_lines = [l for l in result.split("\n") if "3.7.6 Heading" in l]
    assert len(heading_lines) == 1
    assert heading_lines[0].count('<a id="sec-3.7.6"></a>') == 1
    assert heading_lines[0].startswith('### <a id="sec-3.7.6"></a>')


def test_check_mode_flags_legacy_column_0_anchor(tmp_path):
    """--check exits non-zero on a file still carrying the legacy column-0
    anchor form (it's a pending migration, not a steady-state)."""
    f = tmp_path / "doc.md"
    f.write_text(
        '<!-- sec:3.7.6 -->\n'
        '<a id="sec-3.7.6"></a>### 3.7.6 Quantization\n\n'
        'Content.\n',
        encoding="utf-8"
    )
    rc, out, err = run(["--check", str(f)])
    # Must exit non-zero — the legacy form is drift the maintenance pass
    # would correct, so --check should NOT be silent.
    assert rc != 0, f"--check should flag legacy column-0 anchor; got rc=0:\n{out}\n{err}"


def test_heading_anchor_idempotent(tmp_path):
    """Running --init twice does not duplicate the anchor."""
    f = tmp_path / "doc.md"
    f.write_text("# Top\n\n### 3.7.6 Quantization of the LLRs\n\nContent.\n",
                 encoding="utf-8")
    run(["--init", str(f)])
    after_first = f.read_text(encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    after_second = f.read_text(encoding="utf-8")
    assert after_first == after_second


def test_check_mode_detects_missing_anchor(tmp_path):
    """--check exits non-zero when a heading is missing its sec-anchor."""
    f = tmp_path / "doc.md"
    f.write_text("### 3.7.6 Quantization of the LLRs\n\nContent.\n",
                 encoding="utf-8")
    rc, out, err = run(["--check", str(f)])
    assert rc != 0
    assert "3.7.6" in (out + err)


# -- Sub-landmark heuristic ----------------------------------------


@pytest.mark.parametrize("landmark,expected_suffix", [
    ("**Step 3 - Recombine.**", "step-3"),
    ("**Step 4a - Substep.**", "step-4a"),
    ("**Part A - Update rule.**", "part-a"),
    ("**Stage 2 - Phase.**", "stage-2"),
    ("**Lemma D.6-A (per-iteration uplift).**", "lemma-d.6-a"),
    ("**Theorem D.7-1 (OMS floor-free).**", "theorem-d.7-1"),
    ("**Assumption 1.**", "assumption-1"),
    ("**Path A - sub-branch.**", "path-a"),
])
def test_sub_landmark_anchor_inserted(tmp_path, landmark, expected_suffix):
    f = tmp_path / "doc.md"
    f.write_text(
        f"### 3.7.6 Heading\n\n{landmark} body text.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert f'<a id="sec-3.7.6-{expected_suffix}"></a>' in result, \
        f"expected sec-3.7.6-{expected_suffix} in:\n{result}"


@pytest.mark.parametrize("non_landmark", [
    "**Phase noise considerations.** body text.",
    "**Path splitting heuristic.** body text.",
    "**Algorithm selection.** body text.",
    "**Example for clarity.** body text.",
    "**Note on convergence.** body text.",
])
def test_non_landmark_phrases_not_anchored(tmp_path, non_landmark):
    """Phrases that start with a kind keyword but lack an enumerator are not landmarks."""
    f = tmp_path / "doc.md"
    f.write_text(f"### 3.7.6 Heading\n\n{non_landmark}\n", encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    result = f.read_text(encoding="utf-8")
    # No sub-anchor should have been injected for this line
    line = [l for l in result.split("\n") if non_landmark in l][0]
    assert 'id="sec-3.7.6-' not in line, f"unexpected sub-anchor on: {line}"


# -- Ref rewriting (same-file) -------------------------------------


def test_secref_same_file_rewrites_link(tmp_path):
    """<!-- secref:3.7.6 --> (anywhere) -> links to #sec-3.7.6 in same file."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.7.6 Quantization\n\n"
        "Some prose.\n\n"
        "See <!-- secref:3.7.6 -->[]() for details.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    assert "[§3.7.6](#sec-3.7.6)" in result


def test_secref_sub_anchor_rewrites_link(tmp_path):
    """<!-- secref:3.7.6-step-3 --> -> links to #sec-3.7.6-step-3."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.7.6 Quantization\n\n"
        "**Step 3 - Recombine.** prose.\n\n"
        "See <!-- secref:3.7.6-step-3 -->[]() for details.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    assert "[§3.7.6 Step 3](#sec-3.7.6-step-3)" in result


# -- Ref rewriting (cross-file) ------------------------------------


def test_secxref_cross_file_rewrites_link(tmp_path):
    """<!-- secxref:3.7.6 --> finds the owning file via order.json."""
    survey = tmp_path / "survey"
    survey.mkdir()
    (survey / "order.json").write_text(
        '["fundamentals.md", "appendix.md"]', encoding="utf-8"
    )
    (survey / "fundamentals.md").write_text(
        "### 3.7.6 Quantization\n\nProse.\n", encoding="utf-8"
    )
    (survey / "appendix.md").write_text(
        "## D.1 First\n\nSee <!-- secxref:3.7.6 -->[]() for details.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(survey)])
    assert rc == 0, f"{out}\n{err}"
    result = (survey / "appendix.md").read_text(encoding="utf-8")
    assert "[§3.7.6](fundamentals.md#sec-3.7.6)" in result


# -- --init bare-ref discovery -------------------------------------


def test_init_promotes_bare_secref_to_linked_form(tmp_path):
    """A bare '§3.7.6' in prose gets rewritten to the marked + linked form."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.7.6 Quantization\n\nProse.\n\nSee §3.7.6 for details.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    assert "<!-- secref:3.7.6 -->[§3.7.6](#sec-3.7.6)" in result


def test_init_reports_unresolved_bare_refs(tmp_path):
    """A bare '§9.9.9' with no matching heading is reported, not silently rewritten."""
    f = tmp_path / "doc.md"
    f.write_text("### 3.7.6 Quantization\n\nSee §9.9.9 for that.\n",
                 encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    # --init may exit 0 with warnings; the unresolved ref must be reported
    assert "9.9.9" in (out + err)
    result = f.read_text(encoding="utf-8")
    # The bare form must be preserved (not silently rewritten to a broken link)
    assert "§9.9.9" in result


def test_dry_run_diff_does_not_modify(tmp_path):
    """--dry-run-diff prints diff but leaves the file unchanged."""
    f = tmp_path / "doc.md"
    original = "### 3.7.6 Quantization\n\nSee §3.7.6.\n"
    f.write_text(original, encoding="utf-8")
    rc, out, err = run(["--dry-run-diff", "--init", str(f)])
    assert rc == 0
    assert f.read_text(encoding="utf-8") == original
    assert "sec-3.7.6" in (out + err)  # diff content visible


# -- Duplicate detection -------------------------------------------


def test_duplicate_section_numbers_reported(tmp_path):
    """Two ### 3.7.6 headings in the same file are flagged."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.7.6 First\n\nProse.\n\n### 3.7.6 Second\n\nProse.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc != 0
    assert "duplicate" in (out + err).lower()
    assert "3.7.6" in (out + err)


# -- Letter-prefix section forms (added per Task 1.3 regex fix) ----


def test_heading_letter_dot_form_handled(tmp_path):
    """### D.7.5 Title -> sec:D.7.5 anchor (the letter-dot section form)."""
    f = tmp_path / "doc.md"
    f.write_text("# Top\n\n### D.7.5 OMS Density\n\nContent.\n",
                 encoding="utf-8")
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert '<!-- sec:D.7.5 -->' in result
    assert '<a id="sec-D.7.5"></a>' in result


def test_bare_letter_dot_secref_promoted(tmp_path):
    """A bare '§D.7.5' in prose gets rewritten to <!-- secref:D.7.5 -->..."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### D.7.5 OMS Density\n\nProse.\n\nSee §D.7.5 for details.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    assert "<!-- secref:D.7.5 -->[§D.7.5](#sec-D.7.5)" in result


# -- Citation-bracket and reference-list exclusions ----------------


def test_bare_ref_inside_citation_bracket_not_promoted(tmp_path):
    """§X.Y.Z inside [Author Year, §X.Y.Z] should NOT be auto-promoted."""
    f = tmp_path / "doc.md"
    # The §3.4 in the prose IS promotable (matches the heading).
    # The §17.5.2.3 in the citation bracket is NOT promotable.
    f.write_text(
        "### 3.4 Heading\n\n"
        "See §3.4 for context [Sesia et al. 2011, §17.5.2.3] of the cited work.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    # The prose §3.4 is promoted:
    assert "<!-- secref:3.4 -->[§3.4](#sec-3.4)" in result
    # The citation §17.5.2.3 is left bare:
    assert "[Sesia et al. 2011, §17.5.2.3]" in result
    # And no secxref/secref marker was injected inside the bracket:
    assert "secref:17.5.2.3" not in result
    assert "secxref:17.5.2.3" not in result


def test_bare_ref_in_references_list_not_promoted(tmp_path):
    """§X.Y.Z inside a numbered reference-list entry should NOT be promoted."""
    f = tmp_path / "doc.md"
    f.write_text(
        "### 3.4 Heading\n\n"
        "See §3.4 above.\n\n"
        "## References\n\n"
        "[1] Some Author, \"Some Paper,\" §5.7 of that book, 2020.\n",
        encoding="utf-8"
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0
    result = f.read_text(encoding="utf-8")
    # Prose §3.4 is promoted:
    assert "<!-- secref:3.4 -->[§3.4](#sec-3.4)" in result
    # Reference-list §5.7 is left bare:
    assert "§5.7 of that book" in result
    assert "secref:5.7" not in result
    assert "secxref:5.7" not in result


def test_init_on_parent_dir_uses_per_subdir_index(tmp_path):
    """When invoked on a parent dir, each subdir's files use that subdir's index."""
    root = tmp_path
    # Subdir A has its own §3.7.6 heading + a ref to §3.7.6
    sub_a = root / "survey_a"
    sub_a.mkdir()
    (sub_a / "doc.md").write_text(
        "### 3.7.6 A's section\n\nContent.\n\nSee §3.7.6 elsewhere in this survey.\n",
        encoding="utf-8"
    )
    # Subdir B has a DIFFERENT §3.7.6 heading + a ref to §3.7.6
    sub_b = root / "survey_b"
    sub_b.mkdir()
    (sub_b / "doc.md").write_text(
        "### 3.7.6 B's section\n\nContent.\n\nSee §3.7.6 elsewhere in this survey.\n",
        encoding="utf-8"
    )
    # Run --init on the parent dir
    rc, out, err = run(["--init", str(root)])
    assert rc == 0, f"{out}\n{err}"
    # Each subdir's ref should link to ITS OWN sec-3.7.6 (same-file form),
    # NOT to the other subdir's file.
    a_result = (sub_a / "doc.md").read_text(encoding="utf-8")
    b_result = (sub_b / "doc.md").read_text(encoding="utf-8")
    assert "[§3.7.6](#sec-3.7.6)" in a_result, f"survey_a's ref should be same-file: {a_result}"
    assert "[§3.7.6](#sec-3.7.6)" in b_result, f"survey_b's ref should be same-file: {b_result}"
    # Critically, neither subdir's ref should link to the OTHER subdir's file:
    assert "survey_b/doc.md" not in a_result
    assert "survey_a/doc.md" not in b_result
