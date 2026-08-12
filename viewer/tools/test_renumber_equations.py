"""Tests for renumber-equations.py, focused on propagate_xrefs().

Covers: cross-file xref propagation for both the generator's own numeric
`#eq-N` anchor and a hand-written stable anchor (`#eq-<slug>`) -- the
distinction is that a renumber must always update the visible `(N)`, but
must only rewrite the `#`-fragment when it is the plain numeric form.

See todos/2026-08-07-handwritten-eq-anchors.md and
decisions/2026-08-07-handwritten-eq-anchor-propagation.md for the design
rationale: a hand-written anchor is a stable citation target for links from
outside the survey, and propagate_xrefs must never overwrite it.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "renumber-equations.py"


def run(args, cwd=None):
    """Invoke renumber-equations.py with args; return (rc, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def _owner_with_two_eqs(second_id):
    """A two-equation owning file: eq #1 is a filler so eq `second_id`
    lands at number 2, then renumbering forces it to 3 once a new filler
    equation is inserted before it (see the *_shift tests below)."""
    return (
        "# Owner\n\n"
        "<!-- eq:filler-1 -->\n$$\nx = 1\n$$\n\n"
        f"<!-- eq:{second_id} -->\n"
        "$$\ny = 2\n$$\n"
    )


# -- Numeric generator anchor: baseline behavior unchanged ----------------


def test_xref_numeric_anchor_updates_number_and_anchor(tmp_path):
    """Baseline: a plain `#eq-N` anchor gets both the number AND the
    anchor fragment rewritten together (pre-existing behavior)."""
    owner = tmp_path / "owner.md"
    sibling = tmp_path / "sibling.md"
    owner.write_text(_owner_with_two_eqs("target"), encoding="utf-8")
    sibling.write_text(
        "See [(2)](owner.md#eq-2) <!-- xref:target -->.\n", encoding="utf-8"
    )

    # Insert a filler equation before `target` so its number shifts 2 -> 3.
    owner.write_text(
        owner.read_text(encoding="utf-8").replace(
            "<!-- eq:target -->", "<!-- eq:filler-2 -->\n$$\nz = 3\n$$\n\n<!-- eq:target -->"
        ),
        encoding="utf-8",
    )

    rc, out, err = run([str(owner)])
    assert rc == 0, f"{out}\n{err}"
    result = sibling.read_text(encoding="utf-8")
    assert "[(3)](owner.md#eq-3) <!-- xref:target -->" in result, result
    assert "#eq-2" not in result


# -- Hand-written (non-numeric) anchor: new behavior -----------------------


def test_xref_handwritten_anchor_preserved_number_updated(tmp_path):
    """A hand-written stable anchor (`#eq-slug`) must NOT be rewritten by a
    renumber -- only the visible `(N)` tracks the new position."""
    owner = tmp_path / "owner.md"
    sibling = tmp_path / "sibling.md"
    owner.write_text(
        "# Owner\n\n"
        "<!-- eq:filler-1 -->\n$$\nx = 1\n$$\n\n"
        '<a id="eq-my-slug"></a><!-- eq:my-slug -->\n$$\ny = 2\n$$\n',
        encoding="utf-8",
    )
    sibling.write_text(
        "See [(2)](owner.md#eq-my-slug) <!-- xref:my-slug -->.\n", encoding="utf-8"
    )

    # Force a shift: insert a filler equation before eq:my-slug.
    owner.write_text(
        owner.read_text(encoding="utf-8").replace(
            "<!-- eq:my-slug -->",
            "<!-- eq:filler-2 -->\n$$\nz = 3\n$$\n\n<!-- eq:my-slug -->",
        ),
        encoding="utf-8",
    )

    rc, out, err = run([str(owner)])
    assert rc == 0, f"{out}\n{err}"
    result = sibling.read_text(encoding="utf-8")
    assert "[(3)](owner.md#eq-my-slug) <!-- xref:my-slug -->" in result, result
    # The hand-written anchor fragment must be untouched -- never rewritten
    # to a numeric form.
    assert "#eq-3)" not in result
    assert "eq-my-slug" in result


def test_xref_handwritten_anchor_no_change_is_a_noop(tmp_path):
    """When the target equation's number does not move, propagate_xrefs
    reports no changes and the sibling file is left byte-identical."""
    owner = tmp_path / "owner.md"
    sibling = tmp_path / "sibling.md"
    owner.write_text(
        '# Owner\n\n<a id="eq-stable"></a><!-- eq:stable -->\n$$\nx = 1\n$$\n',
        encoding="utf-8",
    )
    sibling_text = "See [(1)](owner.md#eq-stable) <!-- xref:stable -->.\n"
    sibling.write_text(sibling_text, encoding="utf-8")

    rc, out, err = run([str(owner)])
    assert rc == 0, f"{out}\n{err}"
    assert sibling.read_text(encoding="utf-8") == sibling_text
    assert "no cross-file updates needed" in out


def test_xref_handwritten_anchor_idempotent(tmp_path):
    """Running the renumber twice in a row after a shift converges: the
    second run makes no further changes."""
    owner = tmp_path / "owner.md"
    sibling = tmp_path / "sibling.md"
    owner.write_text(
        "# Owner\n\n"
        "<!-- eq:filler-1 -->\n$$\nx = 1\n$$\n\n"
        "<!-- eq:filler-2 -->\n$$\nw = 2\n$$\n\n"
        '<a id="eq-my-slug"></a><!-- eq:my-slug -->\n$$\ny = 3\n$$\n',
        encoding="utf-8",
    )
    sibling.write_text(
        "See [(1)](owner.md#eq-my-slug) <!-- xref:my-slug -->.\n", encoding="utf-8"
    )

    rc1, out1, err1 = run([str(owner)])
    assert rc1 == 0, f"{out1}\n{err1}"
    once = sibling.read_text(encoding="utf-8")
    assert "[(3)](owner.md#eq-my-slug) <!-- xref:my-slug -->" in once

    rc2, out2, err2 = run([str(owner)])
    assert rc2 == 0, f"{out2}\n{err2}"
    assert sibling.read_text(encoding="utf-8") == once
    assert "no cross-file updates needed" in out2


def test_xref_orphan_handwritten_id_still_reported(tmp_path):
    """An xref pointing at an ID the owner no longer defines is still
    reported as an orphan, whether the anchor is numeric or hand-written."""
    owner = tmp_path / "owner.md"
    sibling = tmp_path / "sibling.md"
    owner.write_text(
        '# Owner\n\n<a id="eq-real"></a><!-- eq:real -->\n$$\nx = 1\n$$\n',
        encoding="utf-8",
    )
    sibling.write_text(
        "See [(9)](owner.md#eq-gone) <!-- xref:gone -->.\n", encoding="utf-8"
    )

    rc, out, err = run([str(owner)])
    assert rc == 1, f"expected orphan to fail --check-equivalent status: {out}\n{err}"
    assert "orphaned xref" in out.lower()
    # Orphaned link is left untouched.
    assert "[(9)](owner.md#eq-gone) <!-- xref:gone -->" in sibling.read_text(
        encoding="utf-8"
    )
