"""Tests for mdctx: the shared "which bytes may I rewrite?" map.

Every case below is drawn from a real corruption (see the module docstring).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

_spec = importlib.util.spec_from_file_location("mdctx", Path(__file__).parent / "mdctx.py")
mdctx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mdctx)

Ctx = mdctx.Ctx
SEC = re.compile(r"§\d+(?:\.\d+)+")


def promoted(text):
    """Simulate a bare-ref promoter that only writes in prose."""
    new, n = mdctx.sub_in_prose(SEC, lambda m: f"<!-- secref -->[{m.group(0)}](#x)", text)
    return new, n


# ---------------------------------------------------------------- bug 2026-07-09-04
def test_bare_ref_inside_html_comment_is_not_promoted():
    src = "prose §1.1 here\n\n<!--\n  The blocks in §4.8.1 are untagged.\n-->\n\nmore §2.2\n"
    comment = "<!--\n  The blocks in §4.8.1 are untagged.\n-->"
    new, n = promoted(src)
    assert n == 2, "the two PROSE refs are promoted"
    # The comment must survive byte-identically. (The rewritten prose legitimately adds
    # its own `-->` markers, so counting `-->` document-wide proves nothing.)
    assert comment in new, "the comment must be untouched"


def test_multiline_comment_spans_lines():
    src = "<!--\n§9.9\n-->\n"
    assert promoted(src)[1] == 0


# ---------------------------------------------------------------- the two KaTeX errors
def test_bare_ref_inside_display_math_is_not_promoted():
    src = (
        "prose\n\n$$\n\\begin{aligned}\n"
        "&= 2\\,x && (\\text{, stationary-UE frame of §3.3.1}) \\\\\n"
        "\\end{aligned}\\tag{28}\n$$\n\ntail §7.7\n"
    )
    new, n = promoted(src)
    assert n == 1, "only the prose ref"
    assert "frame of §3.3.1}" in new, "display math must be untouched"


def test_bare_ref_inside_inline_math_is_not_promoted():
    src = "clamp to $x_{§4.4}$ and §5.5 outside\n"
    new, n = promoted(src)
    assert n == 1
    assert "$x_{§4.4}$" in new


def test_highlight_wrapped_display_math_is_display_math():
    src = "a\n\n==blue: $$\n§1.1\n$$==\n\nb §2.2\n"
    new, n = promoted(src)
    assert n == 1, "the ==color: $$ wrapper is still display math (bugs/2026-05-06-01)"
    assert "\n§1.1\n" in new


def test_single_line_display_math():
    src = "$$ f(§1.1) $$\n\nprose §2.2\n"
    new, n = promoted(src)
    assert n == 1
    assert "f(§1.1)" in new


# ---------------------------------------------------------------- other contexts
def test_fence_and_inline_code():
    src = "```\n§1.1\n```\n\n`§2.2` and §3.3\n"
    new, n = promoted(src)
    assert n == 1
    assert "```\n§1.1\n```" in new and "`§2.2`" in new


def test_link_destination_is_not_prose():
    # the link-references.py class: matching inside a link URL. Link *text* is prose
    # (the promoter's own bracket rule guards that); the *destination* is not.
    src = "see [the derivation](appendix-d.md#sec-§1.1) and §2.2\n"
    new, n = promoted(src)
    assert n == 1, "only the bare ref outside any link"
    assert "(appendix-d.md#sec-§1.1)" in new, "the destination must be untouched"


def test_frontmatter():
    src = "---\ntitle: §1.1\n---\n\nprose §2.2\n"
    assert promoted(src)[1] == 1


def test_dollar_inside_code_does_not_open_math():
    src = "`$x$` then §1.1 then $y$\n"
    new, n = promoted(src)
    assert n == 1


# ---------------------------------------------------------------- insertion nudging
def test_advance_out_of_inline_math():
    """crosslink.py inserted ` (link)` before the closing `$` of `$[-K, +K]$`."""
    text = "clamping messages to $[-K, +K]$ — has a\n"
    spans = mdctx.classify(text)
    mask = mdctx.writable_mask(text)
    ip = text.index("$[-K, +K]$") + len("$[-K, +K]")   # just before the closing '$'
    assert not mask[ip]
    out = mdctx.advance_to_prose(text, spans, mask, ip)
    assert out == text.index("$[-K, +K]$") + len("$[-K, +K]$"), "nudged past the closing $"
    assert text[:out] + " (L)" + text[out:] == "clamping messages to $[-K, +K]$ (L) — has a\n"


def test_advance_refuses_to_leave_a_fence_or_comment():
    text = "```\nfoo\n```\n"
    spans, mask = mdctx.classify(text), mdctx.writable_mask(text)
    assert mdctx.advance_to_prose(text, spans, mask, text.index("foo")) is None
    text2 = "<!-- foo -->\n"
    spans2, mask2 = mdctx.classify(text2), mdctx.writable_mask(text2)
    assert mdctx.advance_to_prose(text2, spans2, mask2, text2.index("foo")) is None


def test_prose_offset_is_returned_unchanged():
    text = "plain prose here\n"
    spans, mask = mdctx.classify(text), mdctx.writable_mask(text)
    assert mdctx.advance_to_prose(text, spans, mask, 5) == 5


# ---------------------------------------------------------------- structural
def test_spans_are_sorted_and_non_overlapping():
    src = ("---\na: 1\n---\n\n<!-- c -->\n\n```\n$$\n```\n\n$$\nx\n$$\n\n"
           "`code` and $m$ and [t](u)\n")
    spans = mdctx.classify(src)
    assert spans == sorted(spans)
    for (s1, e1, _), (s2, _, _) in zip(spans, spans[1:]):
        assert e1 <= s2, f"overlap at {e1} > {s2}"


def test_mask_length_matches_text():
    src = "abc §1.1 `x` $y$\n"
    assert len(mdctx.writable_mask(src)) == len(src)


def test_sub_in_prose_is_right_to_left_safe():
    """Multiple edits on one line must not corrupt each other's offsets."""
    src = "§1.1 and §2.2 and §3.3\n"
    new, n = promoted(src)
    assert n == 3
    assert new.count("secref") == 3
    assert "§1.1" in new and "§2.2" in new and "§3.3" in new
