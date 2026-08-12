"""Unit tests for the single, shared section-number grammar.

Guards the invariant that `bugs/2026-07-09-13` and `-04` both violated: every
tool that reads a section number reads the SAME one, and a flat number is a
section only when something on the line says so.
"""
import importlib.util
import pathlib
import re

import pytest

_p = pathlib.Path(__file__).with_name("heading_grammar.py")
_s = importlib.util.spec_from_file_location("heading_grammar", _p)
hg = importlib.util.module_from_spec(_s)
_s.loader.exec_module(hg)


@pytest.mark.parametrize("line,num", [
    ("## 3.7.6 Quantization of the LLRs", "3.7.6"),
    ('### <a id="sec-D.7"></a>D.7 Derivation', "D.7"),
    ("#### A.8.3 Lemma", "A.8.3"),
    ("## 5. Power-Domain NOMA", "5"),                     # trailing dot marks it
    ("## 3 — Road A: MI-max front-end", "3"),             # em-dash marks it
    ("## 4 - Road B", "4"),                               # hyphen marks it
    ("## § 1 Scope", "1"),                                # section glyph marks it
    ('## <a id="sec-17"></a>17 Master matrix', "17"),     # existing anchor marks it
])
def test_match_heading_accepts(line, num):
    m = hg.match_heading(line)
    assert m is not None, f"should have matched: {line!r}"
    assert m.group("num") == num


@pytest.mark.parametrize("line", [
    "## 2020 in review",           # unmarked flat number = prose, not a section
    "## Appendix C. Derivation",   # does not start with a number
    "# 1. Title",                  # h1 is the doc title, never a section
    "Just a paragraph.",
    "",
])
def test_match_heading_rejects(line):
    assert hg.match_heading(line) is None, f"should not have matched: {line!r}"


def test_match_heading_exposes_title_and_hashes():
    m = hg.match_heading("### 3.1 Wiener Interpolation")
    assert m.group("hashes") == "###"
    assert m.group("title") == "Wiener Interpolation"


def test_markers_accept_flat_and_dotted_and_sublandmarks():
    assert hg.SECXREF_MARKER_RE.search("<!-- secxref:10 -->").group(1) == "10"
    assert hg.SECXREF_MARKER_RE.search("<!-- secxref:3.1 -->").group(1) == "3.1"
    assert hg.SECREF_MARKER_RE.search("<!-- secref:3.7.6-step-3 -->").group(1) == "3.7.6-step-3"
    assert hg.SEC_MARKER_RE.search("<!-- sec:D.7 -->").group(1) == "D.7"


def test_sub_landmark_suffix_survives_the_alternation():
    """SECTION_NUM has a top-level `|`. If it is concatenated with the suffix
    without wrapping, the suffix binds to only the second branch and every
    digit-first sub-landmark id silently stops matching."""
    for marker_re, text, expect in [
        (hg.SECREF_MARKER_RE, "<!-- secref:3.7.6-step-3 -->", "3.7.6-step-3"),
        (hg.SECXREF_MARKER_RE, "<!-- secxref:5-lemma-a -->", "5-lemma-a"),
        (hg.SEC_MARKER_RE, "<!-- sec:D.6-part-a -->", "D.6-part-a"),
    ]:
        m = marker_re.search(text)
        assert m is not None, f"{text!r} must match"
        assert m.group(1) == expect


def test_sec_anchor_group_1_is_the_full_anchor_id():
    """Positional contract: `crosslink.py:212` does `anchor = am.group(1)` and
    uses it verbatim to build `#sec-...` links. Group `sec` is the bare id."""
    m = hg.SEC_ANCHOR_RE.search('<a id="sec-11"></a>')
    assert m.group(1) == "sec-11"
    assert m.group("anchor") == "sec-11"
    assert m.group("sec") == "11"

    m = hg.SEC_ANCHOR_RE.search('<a id="sec-3.7.6-step-3"></a>')
    assert m.group("anchor") == "sec-3.7.6-step-3"
    assert m.group("sec") == "3.7.6-step-3"


def test_any_secxref_catches_malformed_ids_the_strict_one_drops():
    """`secxref:appendix-derivations` is a file slug, not a section number.

    The strict regex must not match it (it is not a section), and the permissive
    one must, so `renumber-sections` can REPORT it instead of silently skipping.
    That silent skip is bugs/2026-07-09-16.
    """
    line = "<!-- secxref:appendix-derivations -->"
    assert hg.SECXREF_MARKER_RE.search(line) is None
    assert hg.ANY_SECXREF_RE.search(line).group("id") == "appendix-derivations"
    # ...and it still finds the well-formed ones.
    assert hg.ANY_SECXREF_RE.search("<!-- secxref:10 -->").group("id") == "10"


def test_dotted_section_num_still_rejects_flat():
    """validate-refs' bare-ref exception depends on this staying narrow.

    A bare `§4` in prose is ambiguous with an external citation, so the DOTTED
    form is what `--init` promotes. Widening it would auto-link 809 prose
    mentions across 84 files.
    """
    assert re.fullmatch(hg.DOTTED_SECTION_NUM, "3.7.6")
    assert re.fullmatch(hg.DOTTED_SECTION_NUM, "D.7")
    assert re.fullmatch(hg.DOTTED_SECTION_NUM, "10.2.1")
    assert not re.fullmatch(hg.DOTTED_SECTION_NUM, "4")
    assert not re.fullmatch(hg.DOTTED_SECTION_NUM, "17")


def test_section_num_accepts_flat():
    assert re.fullmatch(hg.SECTION_NUM, "4")
    assert re.fullmatch(hg.SECTION_NUM, "3.7.6")
    assert re.fullmatch(hg.SECTION_NUM, "D.7")


def test_multiple_post_atx_anchors_still_parse():
    """A heading may carry BOTH the sec-N anchor and a semantic anchor.

    The post-ATX anchor group is `*`, not `?`. With `?` only the first anchor was
    consumed, so `## <a id="sec-1"></a><a id="estimator"></a>1. Title` did not
    match -- and because crosslink extracts sections via match_heading, the whole
    FILE contributed zero sections and sat outside the index while `check`
    truthfully reported "no gaps" for it. Four wikis were invisible this way
    (2026-07-26 harness audit; same false-green class as bugs/2026-07-09-13).
    """
    m = hg.match_heading('## <a id="sec-1"></a><a id="estimator"></a>1. The top-k estimator')
    assert m and m.group("num") == "1"
    assert m.group("title") == "The top-k estimator"

    # Three anchors, and a dotted number, both still fine.
    m3 = hg.match_heading('### <a id="sec-2.1"></a><a id="x"></a><a id="y"></a>2.1 Title')
    assert m3 and m3.group("num") == "2.1"

    # The single-anchor and no-anchor forms must be untouched by the widening.
    assert hg.match_heading('## <a id="sec-4"></a>4 Reader\'s questions')
    assert hg.match_heading("## 5. Power-Domain NOMA")

    # Widening anchors must NOT weaken the marked-flat rule: an unmarked flat
    # number is still not a section, anchors or no anchors.
    assert hg.match_heading('## <a id="whatever"></a>2020 in review') is None
