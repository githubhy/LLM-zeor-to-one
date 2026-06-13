"""Tests for validate-refs.py bare-ref checks (#11 + #12).

These reproduce the §D.3.5 regression bug pattern (prompts/2026-05-23.md
Conversation 12-13) and lock in exemption logic for external citations.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "viewer" / "tools" / "validate-refs.py"


def run_bare_refs(tmp_path, content, severity="error"):
    """Write `content` to a temp .md file and invoke validate-refs --bare-refs-only.

    Returns (exit_code, stdout_text, stderr_text).
    """
    f = tmp_path / "doc.md"
    f.write_text(content, encoding="utf-8")
    cmd = [sys.executable, str(VALIDATE), "--bare-refs-only",
           f"--severity={severity}", str(f)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


# ── Check #11 — bare same-document eq-ref ────────────────────────────


def test_bare_same_doc_eq_ref_fires(tmp_path):
    """A bare 'Eq. (10)' on a content line with no <!-- ref:... --> must error."""
    content = (
        "<a id='eq-10'></a><!-- eq:D.3-7 -->\n"
        "$$ x = 1 \\tag{10} $$\n"
        "\n"
        "Substituting Eq. (10) into the recursion gives...\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0
    assert "bare same-doc eq-ref" in (out + err).lower()
    assert "(10)" in (out + err)


def test_marked_eq_ref_passes(tmp_path):
    """A properly marked '<!-- ref:D.3-7 -->[(10)](#eq-10)' must not fire."""
    content = (
        "<a id='eq-10'></a><!-- eq:D.3-7 -->\n"
        "$$ x = 1 \\tag{10} $$\n"
        "\n"
        "Substituting <!-- ref:D.3-7 -->[(10)](#eq-10) into the recursion gives...\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"unexpected failure: {out}\n{err}"


def test_external_author_year_citation_exempt(tmp_path):
    """'Bioglio et al., 2020, Eq. (2)' is a citation context, not a same-doc ref."""
    content = "...constraint $n_2 = \\lceil \\log_2(8K) \\rceil$ [Bioglio et al., 2020, Eq. (2)].\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"author-year context should exempt: {out}\n{err}"


def test_source_line_citation_exempt(tmp_path):
    """'[SOURCE] Li et al., ..., Eq. (4)' is a citation context."""
    content = "**[SOURCE]** Li et al., \"Parity-Check Polar Coding ...,\" Eq. (4).\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0


def test_bracketed_reference_with_eq_exempt(tmp_path):
    """'[3, Eq. (5)]' bracketed-reference-with-equation form is a citation."""
    content = "as shown in [3, Eq. (5)].\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0


def test_warn_severity_does_not_block(tmp_path):
    """With --severity=warn, a bare ref reports but exits 0."""
    content = "Substituting Eq. (10) into the recursion gives...\n"
    rc, out, err = run_bare_refs(tmp_path, content, severity="warn")
    assert rc == 0
    assert "bare same-doc eq-ref" in (out + err).lower()


# ── Check #12 — bare section-ref ─────────────────────────────────────


def test_bare_section_ref_fires(tmp_path):
    """A bare '§3.7.6 Step 3' on a content line must error."""
    content = "This is the form used by box-plus implementations (§3.7.6 Step 3).\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0
    assert "bare section-ref" in (out + err).lower()
    assert "§3.7.6" in (out + err)


def test_marked_section_ref_passes(tmp_path):
    """A properly marked secref must not fire."""
    content = (
        "This is the form used by box-plus implementations "
        "(<!-- secref:3.7.6-step-3 -->[§3.7.6 Step 3](#sec-3.7.6-step-3)).\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"unexpected failure: {out}\n{err}"


def test_marked_cross_file_section_ref_passes(tmp_path):
    """A secxref to a cross-file anchor must not fire."""
    content = (
        "See <!-- secxref:3.7.6 -->[§3.7.6](fundamentals.md#sec-3.7.6) for details.\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0


def test_legacy_t430_link_warns_not_errors(tmp_path):
    """Legacy '[§4.4 ...](file.md#t430-lifecycle)' form is a transitional warning."""
    content = (
        "is described once in the canonical "
        "[§4.4 `T430` lifecycle block](channel-and-framework.md#t430-lifecycle).\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, "legacy form should warn, not error"
    assert "warn" in (out + err).lower() or "legacy" in (out + err).lower()


def test_fenced_code_block_excluded(tmp_path):
    """A bare Eq. (10) inside a fenced code block must not fire."""
    content = (
        "```\n"
        "Substituting Eq. (10) into the recursion gives...\n"
        "```\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0


def test_html_comment_excluded(tmp_path):
    """A bare Eq. (10) inside an HTML comment must not fire."""
    content = "<!-- Substituting Eq. (10) into the recursion gives... -->\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0


# ── Issue 1 regression: SOURCE_PREFIX_RE must not exempt 'from Eq.' / 'after Eq.' ──


def test_from_eq_same_doc_fires(tmp_path):
    """'from Eq. (1)' in same-doc prose is NOT an external citation."""
    content = "where $d$ is the slant range from Eq. (1).\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0, f"'from Eq. (N)' should fire as same-doc: {out}\n{err}"
    assert "bare same-doc eq-ref" in (out + err).lower()


def test_after_eq_same_doc_fires(tmp_path):
    """'after Eq. (N)' in same-doc prose is NOT an external citation."""
    content = "Applying the recursion after Eq. (5) yields...\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0
    assert "bare same-doc eq-ref" in (out + err).lower()


def test_from_bracket_citation_exempt(tmp_path):
    """'From [3], Eq. (5).' figure-caption attribution form IS exempt."""
    content = "**Figure 3.** Doppler PDP. From [3], Eq. (5).\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"'From [N], Eq.' caption form should exempt: {out}\n{err}"


# ── Issue 2 regression: inline <!-- ... --> must not mask following bare Eq. ref ──


def test_inline_comment_does_not_mask_following_eq(tmp_path):
    """Bare Eq. (16) appearing before an inline <!-- ... --> on the same line must fire."""
    content = (
        "**Why a DE convergence proof requires Eq. (16).** "
        "Some prose <!-- ref:D.5-2 -->[(20)](#eq-20) more text.\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0, (
        f"bare Eq. (16) before an inline comment on the same line should fire: {out}\n{err}"
    )
    assert "Eq. (16)" in (out + err) or "(16)" in (out + err)


def test_multiline_html_comment_excluded(tmp_path):
    """A multi-line <!-- ... --> block correctly excludes ALL interior content."""
    content = (
        "Before comment.\n"
        "<!-- comment opens here\n"
        "Substituting Eq. (10) into the recursion...\n"
        "and this Eq. (12) is also commented out\n"
        "-->\n"
        "After comment.\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"interior of multi-line comment should be excluded: {out}\n{err}"


# ── Check #12 regression — letter-dot section refs (§D.7.5, §A.8.3) ──────────


def test_bare_letter_dot_section_ref_fires(tmp_path):
    """A bare '§D.7.5' (letter-dot-number form) must error."""
    content = "See §D.7.5 for the derivation.\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0, f"bare §D.7.5 should fire: {out}\n{err}"
    assert "bare section-ref" in (out + err).lower()
    assert "D.7.5" in (out + err)


def test_bare_letter_single_dot_section_ref_fires(tmp_path):
    """A bare '§D.7' (letter-dot-number, one level) must error."""
    content = "See §D.7 for context.\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc != 0
    assert "D.7" in (out + err)


def test_marked_letter_dot_section_ref_passes(tmp_path):
    """A properly marked '§D.7.5' verifies."""
    content = (
        "See <!-- secref:D.7.5 -->[§D.7.5](#sec-D.7.5) for the derivation.\n"
    )
    rc, out, err = run_bare_refs(tmp_path, content)
    assert rc == 0, f"marked §D.7.5 should pass: {out}\n{err}"


def test_bare_section_4_alone_not_flagged(tmp_path):
    """A bare '§4' (no dot) is ambiguous — section ref or external — and is NOT flagged."""
    content = "See §4 of the standard.\n"
    rc, out, err = run_bare_refs(tmp_path, content)
    # Either result is acceptable: the §X form without a dot is intentionally
    # not matched by BARE_SEC_RE, so this should pass (exit 0)
    assert rc == 0, f"§4 (no dot) should not be detected: {out}\n{err}"
