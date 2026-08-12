"""Tests for check-record-ids.py — the record-ID collision gate."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "viewer" / "tools" / "check-record-ids.py"


def _run(root):
    r = subprocess.run([sys.executable, str(GATE), "--root", str(root)],
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _bug(d, id_, slug, title="t"):
    (d / f"{id_}-{slug}.md").write_text(
        f"---\nid: {id_}\ntitle: {title}\nseverity: low\nstatus: fixed\ndate: {id_[:10]}\n---\n\nx\n",
        encoding="utf-8")


def _index(d, ids):
    rows = "\n".join(f"| {i[:10]} | {i} | t | low | fixed | h |" for i in ids)
    (d / "INDEX.md").write_text(f"| date | id | title | sev | status | hook |\n|---|---|---|---|---|---|\n{rows}\n",
                                encoding="utf-8")


def test_clean_tree_passes(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha"); _bug(b, "2026-07-10-02", "beta")
    _index(b, ["2026-07-10-01", "2026-07-10-02"])
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_id_collision_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha"); _bug(b, "2026-07-10-01", "beta")   # same id!
    _index(b, ["2026-07-10-01"])
    rc, out = _run(tmp_path)
    assert rc == 1 and "claimed by 2 files" in out, out


def test_index_row_without_file_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha")
    _index(b, ["2026-07-10-01", "2026-07-10-99"])   # -99 has no file
    rc, out = _run(tmp_path)
    assert rc == 1 and "no file" in out, out


def test_frontmatter_id_mismatch_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    (b / "2026-07-10-01-alpha.md").write_text(
        "---\nid: 2026-07-10-99\ntitle: t\n---\n\nx\n", encoding="utf-8")   # fm != filename
    _index(b, ["2026-07-10-01"])
    rc, out = _run(tmp_path)
    assert rc == 1 and "!= filename id" in out, out


def test_dangling_qualified_ref_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha"); _index(b, ["2026-07-10-01"])
    (tmp_path / "note.md").write_text("see bugs/2026-07-10-77 for details\n", encoding="utf-8")
    rc, out = _run(tmp_path)
    assert rc == 1 and "resolves to no file" in out, out


# --- the NN-less `DATE-slug` scheme (proposals/record-id-collision-structural-fix.md) ---

def _bug_slug(d, id_, title="t"):
    """New-form record: the id IS the filename stem (no allocator-free NN)."""
    (d / f"{id_}.md").write_text(
        f"---\nid: {id_}\ntitle: {title}\nseverity: low\nstatus: fixed\ndate: {id_[:10]}\n---\n\nx\n",
        encoding="utf-8")


def test_slug_form_record_passes(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug_slug(b, "2026-07-16-isfft-mapping-direction-reversed")
    _index(b, ["2026-07-16-isfft-mapping-direction-reversed"])
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_legacy_and_slug_forms_coexist(tmp_path):
    """Legacy NN records are grandfathered; both schemes live in one dir."""
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha")                       # legacy
    _bug_slug(b, "2026-07-16-heredoc-eats-backslash")       # new
    _index(b, ["2026-07-10-01", "2026-07-16-heredoc-eats-backslash"])
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_slug_form_frontmatter_mismatch_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    (b / "2026-07-16-alpha-thing.md").write_text(
        "---\nid: 2026-07-16-different-thing\ntitle: t\n---\n\nx\n", encoding="utf-8")
    _index(b, ["2026-07-16-alpha-thing"])
    rc, out = _run(tmp_path)
    assert rc == 1 and "!= filename id" in out, out


def test_slug_form_index_row_without_file_fails(tmp_path):
    b = tmp_path / "bugs"; b.mkdir()
    _bug_slug(b, "2026-07-16-alpha-thing")
    _index(b, ["2026-07-16-alpha-thing", "2026-07-16-ghost-record"])
    rc, out = _run(tmp_path)
    assert rc == 1 and "no file" in out, out


def test_nn_prefixed_name_still_reads_as_legacy(tmp_path):
    """Disambiguation is legacy-first: `DATE-NN-slug` is id `DATE-NN`, never a slug id.
    So a new slug must not begin with a two-digit segment."""
    b = tmp_path / "bugs"; b.mkdir()
    (b / "2026-07-16-02-foo.md").write_text(          # frontmatter claims the slug reading
        "---\nid: 2026-07-16-02-foo\ntitle: t\n---\n\nx\n", encoding="utf-8")
    _index(b, ["2026-07-16-02"])
    rc, out = _run(tmp_path)
    assert rc == 1 and "!= filename id" in out, out   # filename id is the legacy 2026-07-16-02


def test_unresolved_slug_ref_is_advisory_not_gated(tmp_path):
    """A slug id cannot be ambiguous (the filesystem forbids two files of one name), and the
    pattern cannot tell a ref from prose — so unresolved slug refs are advisory, never fatal."""
    b = tmp_path / "bugs"; b.mkdir()
    _bug_slug(b, "2026-07-16-alpha-thing"); _index(b, ["2026-07-16-alpha-thing"])
    (tmp_path / "note.md").write_text(
        "closed by [bugs/2026-04-24-fixed] — prose, not a ref\n", encoding="utf-8")
    rc, out = _run(tmp_path)
    assert rc == 0, out
    assert "unresolved slug-form ref" in out, out


def test_generated_output_dirs_are_not_scanned_for_refs(tmp_path):
    """A dangling ref inside GENERATED output must not fail the gate.

    Playwright writes `test-results/<case>/error-context.md` containing a copy of the
    failing test's SOURCE COMMENT — bug IDs included. With a naive `rglob('*.md')` that
    made merely RUNNING the viewer suite fail the push, on a path that is gitignored and
    varies per machine and per run. Record IDs live in authored, committed documents;
    this pins that scope.
    """
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha")
    _index(b, ["2026-07-10-01"])

    gen = tmp_path / "test-results" / "some-failing-case"
    gen.mkdir(parents=True)
    # verbatim shape of a Playwright error-context dump quoting a test's own comment
    (gen / "error-context.md").write_text(
        "# Test info\n\n- Name: bug 2026-07-09-02 regression\n"
        "// Browser-level regression for bugs/2026-07-09-02.\n", encoding="utf-8")

    rc, out = _run(tmp_path)
    assert rc == 0, f"generated output was scanned and failed the gate:\n{out}"
    assert "2026-07-09-02" not in out, f"generated file's ref leaked into the report:\n{out}"


def test_authored_dangling_ref_still_fails(tmp_path):
    """The exclusion above must not blunt the gate: an AUTHORED dangling ref still fails."""
    b = tmp_path / "bugs"; b.mkdir()
    _bug(b, "2026-07-10-01", "alpha")
    _index(b, ["2026-07-10-01"])
    (tmp_path / "notes.md").write_text("see bugs/2026-07-09-02 for context\n", encoding="utf-8")

    rc, out = _run(tmp_path)
    assert rc != 0, f"authored dangling ref was NOT caught:\n{out}"
    assert "2026-07-09-02" in out
