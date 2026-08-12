"""Tests for corpus expansion in the survey gate tools (`_corpus.py`).

Motivating incident (`bugs/2026-07-10-09`, high, open 2026-07-10 → 2026-07-31):
`.githooks/pre-push` validates the corpus by handing each tool the `surveys/`
directory, but four of the five marker/anchor tools understood that argument as
**one survey directory** — `order.json` if present, else `glob('*.md')`.
`surveys/` has no `order.json`, so they resolved it to the 12 flat legacy files
at its root and opened none of the 29 survey subdirectories. Measured on the
day of the fix: `validate-refs.py surveys/` scanned **1** file of 811 and
printed `Total: 0 error(s)`.

The property under test is SCOPE, and it needs asserting precisely because
under-scanning is invisible: the gate gets *greener* the less it looks at. A
test that only checks "clean corpus exits 0" passes perfectly against the bug.

Two things must hold together, and neither alone is sufficient:

  * a corpus root must reach into its survey subdirectories, and
  * a survey must remain ONE unit resolved against its own order.json —
    a blanket rglob would flatten 29 independent numbering domains into one
    and mis-resolve cross-references, which is worse than under-scanning.
"""
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _corpus import survey_units, all_files, describe_scope, DEFAULT_EXCLUDES

REPO = pathlib.Path(__file__).resolve().parents[2]
TOOLS = pathlib.Path(__file__).resolve().parent


def _survey(root: pathlib.Path, name: str, files, order=True):
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        (d / f).write_text(f"# {f}\n\nbody\n", encoding="utf-8")
    if order:
        (d / "order.json").write_text(json.dumps(files), encoding="utf-8")
    return d


# ── The regression itself ───────────────────────────────────────────────────


def test_corpus_root_reaches_survey_subdirectories(tmp_path):
    """The bug, stated directly: a corpus root must not resolve to its flat files."""
    root = tmp_path / "surveys"
    root.mkdir()
    (root / "legacy-flat.md").write_text("# flat\n", encoding="utf-8")
    _survey(root, "alpha", ["index.md", "body.md"])
    _survey(root, "beta", ["index.md"])

    units, _ = survey_units(root)
    names = {f.name for f in all_files(units)}
    assert "legacy-flat.md" in names, "flat legacy file dropped"
    assert len(all_files(units)) == 4, f"subdirectories not reached: {names}"
    roots = {u.root.name for u in units}
    assert {"alpha", "beta"} <= roots, roots


def test_a_survey_stays_one_unit_in_order_json_order(tmp_path):
    """Not a flat rglob: each survey is its own numbering domain, ordered."""
    root = tmp_path / "surveys"
    root.mkdir()
    _survey(root, "alpha", ["index.md", "zeta.md", "body.md"])

    units, _ = survey_units(root / "alpha")
    assert len(units) == 1, "a survey must be exactly one unit"
    assert units[0].ordered is True
    assert [f.name for f in units[0].files] == ["index.md", "zeta.md", "body.md"], \
        "order.json order not preserved (alphabetical would be body, index, zeta)"


def test_corpus_root_keeps_surveys_separate(tmp_path):
    """29 surveys must not become one 811-file bag."""
    root = tmp_path / "surveys"
    root.mkdir()
    _survey(root, "alpha", ["index.md", "body.md"])
    _survey(root, "beta", ["index.md", "body.md"])

    units, _ = survey_units(root)
    per_root = {u.root.name: len(u.files) for u in units}
    assert per_root.get("alpha") == 2 and per_root.get("beta") == 2, per_root
    assert len([u for u in units if u.ordered]) == 2


# ── Exclusions, reported rather than silent ─────────────────────────────────


def test_scratch_is_excluded_and_reported(tmp_path):
    root = tmp_path / "surveys"
    root.mkdir()
    d = _survey(root, "alpha", ["index.md"])
    (d / "_scratch").mkdir()
    (d / "_scratch" / "ev-1.md").write_text("# evidence\n", encoding="utf-8")

    units, skipped = survey_units(root)
    assert "ev-1.md" not in {f.name for f in all_files(units)}
    assert any(p.name == "_scratch" for p in skipped), "exclusion was silent"
    assert "_scratch" in describe_scope(units, skipped)


def test_nonordered_subdir_of_a_survey_is_its_own_unit(tmp_path):
    """`<survey>/method-search/` is real content absent from order.json.

    It must be neither dropped nor folded into the survey's ordering.
    """
    root = tmp_path / "surveys"
    root.mkdir()
    d = _survey(root, "alpha", ["index.md"])
    (d / "method-search").mkdir()
    (d / "method-search" / "REGISTER.md").write_text("# reg\n", encoding="utf-8")

    units, _ = survey_units(root)
    ms = [u for u in units if u.root.name == "method-search"]
    assert len(ms) == 1, "method-search dropped"
    assert not ms[0].ordered
    alpha = [u for u in units if u.root.name == "alpha"][0]
    assert [f.name for f in alpha.files] == ["index.md"], \
        "method-search folded into the survey's ordering"


def test_default_excludes_cover_the_known_non_corpus_dirs():
    assert {"_scratch", "specs", "archive"} <= set(DEFAULT_EXCLUDES)


# ── End-to-end against the real corpus ──────────────────────────────────────


def _scope_count(tool, *args):
    """Files the tool reports scanning on the real corpus."""
    r = subprocess.run([sys.executable, str(TOOLS / tool), *args, str(REPO / "surveys")],
                       capture_output=True, text=True)
    for line in (r.stdout + r.stderr).splitlines():
        if " file(s)" in line and "unit(s)" in line:
            return int(line.split("unit(s), ")[1].split(" file(s)")[0])
    return None


def _corpus_md_counts():
    """(flat .md at the corpus root, .md inside survey subdirectories)."""
    root = REPO / "surveys"
    flat = len(list(root.glob("*.md")))
    nested = sum(
        1 for p in root.rglob("*.md")
        if p.parent != root and not (set(p.parts) & set(DEFAULT_EXCLUDES))
    )
    return flat, nested


def test_real_corpus_scope_is_not_a_handful_of_files():
    """The gate must reach into the survey subdirectories, not stop at the root.

    Guards the regression end-to-end: with the pre-fix code each of these
    resolves `surveys/` to its flat root files and still exits 0.

    The floor is DERIVED from the corpus, not hardcoded. The upstream form of
    this test asserted `n > 100` against an 811-file corpus; a literal port
    would fail here purely because this corpus is smaller, which tests the
    corpus rather than the tool. What actually distinguishes the bug from the
    fix is whether the scan gets past the root, so that is what is asserted.
    """
    if not (REPO / "surveys").exists():
        return
    flat, nested = _corpus_md_counts()
    floor = max(flat, nested // 2)
    for tool, args in (("validate-refs.py", ()),
                       ("renumber-equations.py", ("--check",)),
                       ("renumber-paragraphs.py", ("--check",))):
        n = _scope_count(tool, *args)
        assert n is not None, f"{tool} does not report its scope"
        assert n > floor, (
            f"{tool} scanned only {n} file(s); the corpus holds {nested} file(s) "
            f"in survey subdirectories ({flat} flat at the root)"
        )


def test_real_corpus_passes_every_gate():
    if not (REPO / "surveys").exists():
        return
    for tool, args in (("validate-refs.py", ()),
                       ("renumber-equations.py", ("--check",)),
                       ("renumber-paragraphs.py", ("--check",)),
                       ("renumber-sections.py", ("--check",)),
                       ("check-depth-tiers.py", ())):
        r = subprocess.run([sys.executable, str(TOOLS / tool), *args, str(REPO / "surveys")],
                           capture_output=True, text=True)
        assert r.returncode == 0, f"{tool} failed:\n{r.stdout[-3000:]}{r.stderr[-2000:]}"


# ── Highlight-wrapped display math (a separate root cause) ──────────────────


def test_highlight_wrapped_math_opener_does_not_invert_pairing(tmp_path):
    """`==blue: $$` is a display-math OPENER and must be seen as one.

    DISPLAY_MATH anchors on `^\\s*\\$\\$`, which a `==color:` wrapper defeats.
    The opener then goes unseen, its closer is taken for an opener, and every
    `$$` pairing for the rest of the file inverts — putting ordinary prose
    "inside math" and making its paragraph markers unassignable. One such line
    in interpretability circuits.md classified 76% of a 3756-line chapter as display
    math and produced 284 phantom orphaned para IDs.
    See bugs/2026-07-31-renumber-paragraphs-blind-to-highlight-wrapped-math.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("rp", TOOLS / "renumber-paragraphs.py")
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)

    lines = [
        "# Doc", "",
        "==blue: $$",                 # opener, highlight-wrapped
        "x = 1",
        "$$",                         # closer
        "",
        "Ordinary prose after the block.", "",
        "$$", "y = 2", "$$", "",
        "More prose at the end.",
    ]
    inside = rp.display_math_line_set(lines)
    assert 3 in inside, "wrapped block's body not detected as math"
    assert 6 not in inside, "prose after a wrapped block swallowed as math"
    assert 12 not in inside, "pairing inverted for the rest of the file"
    # Without the fix the wrapped opener is missed and everything from the
    # closer onward flips, so the trailing prose lands inside math.
    assert len(inside) <= 6, f"too much classified as math: {sorted(inside)}"
