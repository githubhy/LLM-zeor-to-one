"""Tests for renumber-paragraphs.py.

Focus: the display-math line classifier (`display_math_line_set`) must not
desync when a `$$...$$` display block opens and closes on a single line.

Regression for bug 2026-05-21-05: a single-line `$$ ... $$` block matches the
`^\\s*\\$\\$` opener regex exactly once, so the toggle model flipped `in_math`
a single time (instead of net-zero), inverting opener/closer pairing for the
rest of the file and making every paragraph after the block invisible to the
script (silent partial coverage).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "renumber-paragraphs.py"


def run(args, cwd=None):
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def _marked_lines(text):
    """Return the prose lines that carry a <!-- para:... --> marker."""
    return [l for l in text.split("\n") if "<!-- para:" in l]


def test_single_line_display_math_does_not_hide_following_paragraphs(tmp_path):
    """The core regression: paragraphs AFTER a single-line `$$...$$` block
    must still be classified eligible and get markers under --init."""
    f = tmp_path / "doc.md"
    f.write_text(
        "# Top\n\n"
        "First paragraph before math.\n\n"
        "$$ E = mc^2 $$\n\n"
        "Second paragraph after the single-line block.\n\n"
        "Third paragraph also after.\n",
        encoding="utf-8",
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    # All three prose paragraphs must be marked; the math line must not be.
    assert "Eligible blocks: 3" in out, out
    for needle in (
        "First paragraph before math.",
        "Second paragraph after the single-line block.",
        "Third paragraph also after.",
    ):
        line = [l for l in result.split("\n") if needle in l][0]
        assert "<!-- para:" in line, f"missing marker on: {line!r}"
    # The single-line math block itself stays unmarked.
    math_line = [l for l in result.split("\n") if "E = mc^2" in l][0]
    assert "<!-- para:" not in math_line, f"marker wrongly injected on math: {math_line!r}"


def test_multi_line_display_math_still_skips_interior(tmp_path):
    """Guard: the fix must not regress the multi-line case — interior math
    lines stay skipped and the paragraphs on either side are eligible."""
    f = tmp_path / "doc.md"
    f.write_text(
        "# Top\n\n"
        "Para A.\n\n"
        "$$\nE = mc^2\n$$\n\n"
        "Para B.\n",
        encoding="utf-8",
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert "Eligible blocks: 2" in out, out
    for needle in ("Para A.", "Para B."):
        line = [l for l in result.split("\n") if needle in l][0]
        assert "<!-- para:" in line, f"missing marker on: {line!r}"
    # No marker injected on the `$$` delimiter lines or interior.
    for l in result.split("\n"):
        if l.strip() == "$$" or l.strip() == "E = mc^2":
            assert "<!-- para:" not in l, f"marker wrongly injected on math: {l!r}"


def test_single_line_then_multiline_pairing_stays_aligned(tmp_path):
    """A single-line block followed by a multi-line block must not invert the
    opener/closer pairing — every prose paragraph stays eligible."""
    f = tmp_path / "doc.md"
    f.write_text(
        "# Top\n\n"
        "Para A.\n\n"
        "$$ x = 1 $$\n\n"
        "Para B.\n\n"
        "$$\ny = 2\n$$\n\n"
        "Para C.\n",
        encoding="utf-8",
    )
    rc, out, err = run(["--init", str(f)])
    assert rc == 0, f"{out}\n{err}"
    result = f.read_text(encoding="utf-8")
    assert "Eligible blocks: 3" in out, out
    for needle in ("Para A.", "Para B.", "Para C."):
        line = [l for l in result.split("\n") if needle in l][0]
        assert "<!-- para:" in line, f"missing marker on: {line!r}"


def test_check_clean_after_init_is_idempotent(tmp_path):
    """--init then --check must report clean (no drift), and a second --init
    must be a no-op."""
    f = tmp_path / "doc.md"
    f.write_text(
        "# Top\n\n"
        "Para A.\n\n"
        "$$ E = mc^2 $$\n\n"
        "Para B.\n",
        encoding="utf-8",
    )
    run(["--init", str(f)])
    after_first = f.read_text(encoding="utf-8")
    rc_chk, out_chk, _ = run(["--check", str(f)])
    assert rc_chk == 0, out_chk
    assert "(check) clean" in out_chk, out_chk
    run(["--init", str(f)])
    assert f.read_text(encoding="utf-8") == after_first, "second --init was not a no-op"
