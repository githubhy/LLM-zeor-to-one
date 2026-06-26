"""Tests for lint-math.py — crossing `**`/`==` delimiter check.

Regression for bug 2026-05-20-01 / decision 2026-05-29-01: a highlight whose
`==` delimiters CROSS a `**` strong-emphasis pair (e.g. `**==c: x.** y==`)
makes markdown-it-mark / CommonMark / GitHub render the `==` markers literally.
The check flags the crossing shape and passes the valid (nested / disjoint)
shapes.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "lint-math.py"


def run(md_text, tmp_path):
    f = tmp_path / "doc.md"
    f.write_text(md_text, encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), str(f)]
    # errors="replace": the linter may emit non-ASCII in messages; on a
    # non-UTF-8 console locale (e.g. gbk Windows) the captured bytes would
    # otherwise fail to decode and crash the test (bug 2026-06-01-01 class).
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def flagged(md_line, tmp_path):
    rc, out, err = run(f"# H\n\n{md_line}\n", tmp_path)
    return "crossing" in (out + err).lower()


# ── Must FLAG: crossing (the bug shape) ───────────────────────────

def test_crossing_bullet_bold_then_mark_flagged(tmp_path):
    # The exact fundamentals.md:464 shape.
    assert flagged("- **==purple: Algorithm comparison.** EXIT charts narrow it.==", tmp_path)


def test_crossing_inline_minimal_flagged(tmp_path):
    assert flagged("**==c: a.** b==", tmp_path)


# ── Must PASS: valid shapes ───────────────────────────────────────

def test_nested_bold_inside_mark_not_flagged(tmp_path):
    assert not flagged("==c: **a** b==", tmp_path)


def test_mark_inside_bold_not_flagged(tmp_path):
    assert not flagged("**==c: a==**", tmp_path)


def test_bold_then_loose_marker_not_flagged(tmp_path):
    assert not flagged("**a**==", tmp_path)


def test_math_inside_highlight_not_flagged(tmp_path):
    assert not flagged("==c: shifted by $\\alpha$ here==", tmp_path)


def test_disjoint_bold_and_highlight_not_flagged(tmp_path):
    assert not flagged("**bold lead.** Then ==c: a highlight== follows.", tmp_path)


def test_benign_bold_close_then_mark_close_not_flagged(tmp_path):
    # appendix-d.md:19 pattern — `**lift index**==` is a bold-close then a
    # mark-close, both inside the highlight (valid nesting).
    assert not flagged("==blue: the integer is the **lift index**==", tmp_path)


def test_crossing_inside_fenced_code_not_flagged(tmp_path):
    md = "# H\n\n```\n**==c: a.** b==\n```\n"
    rc, out, err = run(md, tmp_path)
    assert "crossing" not in (out + err).lower()


def test_crossing_inside_inline_code_not_flagged(tmp_path):
    assert not flagged("Write `**==c: a.** b==` to show the bug.", tmp_path)


# ── `$$...$$` blank-line-after check (bug 2026-05-21-03 / 2026-06-01-03) ──
# The blank-line-after-close rule originally only covered a `$$` delimiter on
# its own line; single-line `$$ ... $$` blocks slipped through and rendered the
# following paragraph's inline `$...$` math as literal source (bug 2026-06-01-03).

def _dollar_flag(md_text, tmp_path):
    rc, out, err = run(md_text, tmp_path)
    # Match the blank-line check's specific phrasing, not the generic
    # "display-math block has no \tag" warning that fires on untagged eqs.
    return "blank-line gap" in (out + err).lower()


def test_single_line_display_then_prose_flagged(tmp_path):
    # Single-line $$...$$ headline immediately followed by prose (bug-class 2026-06-01-03).
    md = "# H\n\nThe result is\n$$f(\pm m) = g(m),$$\nwhere $f$ is a density.\n"
    assert _dollar_flag(md, tmp_path)


def test_single_line_display_then_blank_not_flagged(tmp_path):
    md = "# H\n\nThe result is\n\n$$f(\pm m) = g(m),$$\n\nwhere $f$ is a density.\n"
    assert not _dollar_flag(md, tmp_path)


def test_single_line_display_at_eof_not_flagged(tmp_path):
    md = "# H\n\nThe result is\n\n$$f(\pm m) = g(m).$$\n"
    assert not _dollar_flag(md, tmp_path)


def test_single_line_display_back_to_back_not_flagged(tmp_path):
    # Two single-line blocks on consecutive lines are both display, not prose.
    md = "# H\n\n$$a = b.$$\n$$c = d.$$\n\nThen prose.\n"
    assert not _dollar_flag(md, tmp_path)


def test_multiline_display_then_prose_still_flagged(tmp_path):
    # Regression: the original multi-line case (bug 2026-05-21-03) must still fire.
    md = "# H\n\n$$\na = b.\n$$\nwhere $a$ is a thing.\n"
    assert _dollar_flag(md, tmp_path)


def test_multiline_display_then_blank_not_flagged(tmp_path):
    md = "# H\n\n$$\na = b.\n$$\n\nwhere $a$ is a thing.\n"
    assert not _dollar_flag(md, tmp_path)


def test_single_line_display_inside_fence_not_flagged(tmp_path):
    md = "# H\n\n```\n$$a = b.$$\nliteral next line\n```\n"
    assert not _dollar_flag(md, tmp_path)
