"""Tests for the section-ownership gate (bugs/2026-07-09-09).

The bug this guards is invisible to a duplicate-heading check: `## 3` appears
exactly once in the survey. It just appears in `index.md`, while the survey's
*content* section 3 lives in `linear-receivers.md` as `3.1`, `3.2`, … So
`secxref:3` resolved — to the wrong document.
"""
import pathlib
import subprocess
import sys
import textwrap

TOOL = pathlib.Path(__file__).with_name("check-section-ownership.py")


def _run(*paths):
    return subprocess.run(
        [sys.executable, str(TOOL), *[str(p) for p in paths]],
        capture_output=True, text=True,
    )


def _survey(tmp_path, files, order=None):
    d = tmp_path / "svy"
    d.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (d / name).write_text(textwrap.dedent(body), encoding="utf-8")
    (d / "order.json").write_text(
        str(list(order or files)).replace("'", '"'), encoding="utf-8")
    return d


def test_index_claiming_a_body_files_section_number_is_a_conflict(tmp_path):
    """The exact cochannel shape."""
    d = _survey(tmp_path, {
        "index.md": """\
            # Survey

            <!-- sec:3 -->
            ## <a id="sec-3"></a>3. Reader's guide
            """,
        "linear-receivers.md": """\
            # 3. Linear Receivers

            <!-- sec:3.1 -->
            ## <a id="sec-3.1"></a>3.1 The MRC hierarchy
            """,
    })
    r = _run(d)
    assert r.returncode == 1
    out = r.stdout + r.stderr
    assert "index.md" in out
    assert "3.x" in out
    assert "linear-receivers.md" in out
    assert "secxref:3" in out


def test_same_file_owning_its_own_subsections_is_fine(tmp_path):
    """The llms-for-coding shape: `## 3.` and `### 3.1` in the same file."""
    d = _survey(tmp_path, {
        "index.md": "# Survey\n\n## Scope\n",
        "fundamentals.md": """\
            <!-- sec:3 -->
            ## <a id="sec-3"></a>3. Attention Fundamentals

            <!-- sec:3.1 -->
            ### <a id="sec-3.1"></a>3.1 Linear Block Codes
            """,
    })
    assert _run(d).returncode == 0


def test_h1_title_pattern_is_fine(tmp_path):
    """The H1-title shape: the section number lives in the H1 (not indexed),
    subsections are H2, and index.md front matter is unnumbered."""
    d = _survey(tmp_path, {
        "index.md": "# Survey\n\n## Scope\n\n## How to read\n",
        "fundamentals.md": """\
            # 1 · Fundamentals of Array Signal Processing

            <!-- sec:1.1 -->
            ## <a id="sec-1.1"></a>1.1 The array signal model
            """,
    })
    assert _run(d).returncode == 0


def test_two_files_claiming_the_same_section_number(tmp_path):
    d = _survey(tmp_path, {
        "a.md": '<!-- sec:4 -->\n## <a id="sec-4"></a>4. First\n',
        "b.md": '<!-- sec:4 -->\n## <a id="sec-4"></a>4. Second\n',
    })
    r = _run(d)
    assert r.returncode == 1
    assert "first-definition-wins" in (r.stdout + r.stderr)


def test_anchor_declared_section_counts_as_ownership(tmp_path):
    """`## <a id="sec-A"></a>Appendix A — …` has no parsable number, but the
    anchor declares it — the same way build_survey_heading_index sees it."""
    d = _survey(tmp_path, {
        "index.md": "# Survey\n\n## Scope\n",
        "appendix-a.md": '## <a id="sec-A"></a>Appendix A — Derivations\n\n'
                         '<!-- sec:A.1 -->\n### <a id="sec-A.1"></a>A.1 Lemma\n',
    })
    assert _run(d).returncode == 0, "A and A.1 in the same file must be clean"


def test_h1_anchor_confers_ownership(tmp_path):
    """After todos/2026-07-09-h1-section-anchors, an H1-title survey's body file
    declares its section via an anchor on the H1. Ownership must follow the anchor,
    so `## 3` in index.md would now be a genuine two-file conflict."""
    clean = _survey(tmp_path / "a", {
        "index.md": "# Survey\n\n## Executive summary\n",
        "linear-receivers.md": '# <a id="sec-3"></a>3. Linear Receivers\n\n'
                               '<!-- sec:3.1 -->\n## <a id="sec-3.1"></a>3.1 MRC\n',
    })
    assert _run(clean).returncode == 0

    conflicted = _survey(tmp_path / "b", {
        "index.md": '<!-- sec:3 -->\n## <a id="sec-3"></a>3. Reader\'s guide\n',
        "linear-receivers.md": '# <a id="sec-3"></a>3. Linear Receivers\n\n'
                               '<!-- sec:3.1 -->\n## <a id="sec-3.1"></a>3.1 MRC\n',
    })
    r = _run(conflicted)
    assert r.returncode == 1
    assert "first-definition-wins" in (r.stdout + r.stderr)


def test_appendix_h1_anchor_owns_its_letter_subsections(tmp_path):
    """`# <a id="sec-A"></a>Appendix A — Derivations` with `A.1` in the same file."""
    d = _survey(tmp_path, {
        "index.md": "# Survey\n\n## Scope\n",
        "appendix-derivations.md": '# <a id="sec-A"></a>Appendix A — Long-Form Derivations\n\n'
                                   '<!-- sec:A.1 -->\n### <a id="sec-A.1"></a>A.1 Wiener\n',
    })
    assert _run(d).returncode == 0


def test_refuses_to_report_success_over_nothing(tmp_path):
    """A green gate must mean 'looked and found nothing', never 'did not look'."""
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _run(empty).returncode == 2


def test_the_real_corpus_is_clean():
    repo = pathlib.Path(__file__).resolve().parents[2]
    surveys = repo / "surveys"
    if not surveys.exists():
        return
    r = _run(surveys)
    assert r.returncode == 0, f"corpus has ownership conflicts:\n{r.stderr}"
