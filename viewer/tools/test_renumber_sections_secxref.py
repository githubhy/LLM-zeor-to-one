"""Regression tests for bugs/2026-07-09-16.

`renumber-sections.py` defined the section-number grammar five times, each
requiring at least one dot. A flat `<!-- secxref:10 -->` therefore matched none
of them: it was never parsed, resolved, rewritten, or orphan-reported, and
`--check` exited 0 while the link was dead. 131 such markers existed across 39
files; 35 pointed at anchors that do not exist.

A green gate must mean "looked and found nothing", never "did not look".
"""
import pathlib
import subprocess
import sys
import textwrap

TOOL = pathlib.Path(__file__).with_name("renumber-sections.py")


def _run(path):
    return subprocess.run(
        [sys.executable, str(TOOL), str(path), "--check"],
        capture_output=True, text=True,
    )


def _write(p, text):
    p.write_text(textwrap.dedent(text), encoding="utf-8")


def test_orphaned_flat_secxref_is_reported(tmp_path):
    """The exact shape of the 35 dead links: secxref:10 with no sec-10 anchor."""
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "order.json", '["a.md"]')
    _write(d / "a.md", """\
        # Doc

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        See <!-- secxref:10 -->[§10](b.md#sec-10) for details.
        """)
    r = _run(d / "a.md")
    combined = r.stdout + r.stderr
    assert r.returncode != 0, f"--check must fail on an orphaned flat secxref\n{combined}"
    assert "secxref:10" in combined or "10" in combined


def test_malformed_secxref_id_is_reported(tmp_path):
    """`secxref:appendix-derivations` is a file slug, not a section number.

    Real instance: surveys/radar/04-detection-theory.md:234. The strict pattern
    cannot consume it; it must be surfaced rather than silently skipped.
    """
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "a.md", """\
        # Doc

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        See <!-- secxref:appendix-derivations -->[appendix](b.md).
        """)
    r = _run(d / "a.md")
    assert "appendix-derivations" in (r.stdout + r.stderr)


def test_resolvable_flat_secxref_is_silent(tmp_path):
    """Once the target carries a flat sec-10 anchor, the gate goes quiet."""
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "order.json", '["a.md", "b.md"]')
    _write(d / "a.md", """\
        # A

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        See <!-- secxref:10 -->[§10](b.md#sec-10).
        """)
    _write(d / "b.md", """\
        # B

        <!-- sec:10 -->
        ## <a id="sec-10"></a>10. Target
        """)
    r = _run(d / "a.md")
    assert r.returncode == 0, f"should be clean:\n{r.stdout}{r.stderr}"


def test_flat_heading_gets_an_anchor_injected(tmp_path):
    """The migration itself: a marked-flat heading must acquire sec-N."""
    f = tmp_path / "w.md"
    _write(f, """\
        # Wiki

        ## 3 — Road A

        Body.
        """)
    subprocess.run([sys.executable, str(TOOL), str(f)], capture_output=True, text=True)
    out = f.read_text(encoding="utf-8")
    assert '<a id="sec-3"></a>' in out
    assert "<!-- sec:3 -->" in out


def test_unmarked_flat_heading_is_left_alone(tmp_path):
    """`## 2020 in review` is prose, not section 2020."""
    f = tmp_path / "w.md"
    _write(f, """\
        # Wiki

        ## 2020 in review

        Body.
        """)
    subprocess.run([sys.executable, str(TOOL), str(f)], capture_output=True, text=True)
    out = f.read_text(encoding="utf-8")
    assert "sec-2020" not in out


def test_letter_heading_with_a_word_title_is_not_promoted_to_a_section(tmp_path):
    """`## A. TR / TS Map` and `### A. Zone-Based Partitioning` are real corpus
    headings. Treating a bare capital as a section number would inject `sec-A`
    into them and collide with the hand-authored `sec-A` on `## Appendix A`.
    """
    f = tmp_path / "w.md"
    _write(f, """\
        # Wiki

        ## A. TR / TS Map

        Body.
        """)
    subprocess.run([sys.executable, str(TOOL), str(f)], capture_output=True, text=True)
    assert 'id="sec-A"' not in f.read_text(encoding="utf-8")


def test_secxref_resolves_against_an_anchor_declared_heading(tmp_path):
    """`## <a id="sec-A"></a>Appendix A — …` declares its id in the anchor; the
    visible text starts with a word, so no heading grammar can parse it. The
    anchor is the link target, so `secxref:A` must resolve against it."""
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "order.json", '["a.md", "appendix-a.md"]')
    _write(d / "a.md", """\
        # A

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        See <!-- secxref:A -->[§A](appendix-a.md) for the derivation.
        """)
    _write(d / "appendix-a.md", """\
        # Appendix

        ## <a id="sec-A"></a>Appendix A — First-principles derivations
        """)
    # The link lacks its `#sec-A` fragment, so --check correctly reports drift:
    # resolving the anchor is what lets the tool REPAIR it. This is the exact
    # shape of surveys/noma/appendix-d.md's degraded `[§A](appendix-a.md)`.
    assert _run(d / "a.md").returncode != 0

    subprocess.run([sys.executable, str(TOOL), str(d / "a.md")],
                   capture_output=True, text=True)
    assert "[§A](appendix-a.md#sec-A)" in (d / "a.md").read_text(encoding="utf-8")

    r = _run(d / "a.md")
    assert r.returncode == 0, f"clean after repair:\n{r.stdout}{r.stderr}"


def test_secxref_is_not_resolved_outside_a_survey_directory(tmp_path):
    """bugs/2026-07-09-08. `wikis/` has no order.json, so build_survey_heading_index
    used to fall back to globbing every file in the directory. The 2026-07-09
    migration created a `sec-5.4.1` anchor inside an unrelated wiki, and the same
    run then re-pointed three wikis' survey-targeted secxrefs at it —
    first-definition-wins over a bag of unrelated documents.

    A secxref outside a multi-file survey directory must be REPORTED, never
    resolved. Resolving it incorrectly is strictly worse than orphaning it.
    """
    d = tmp_path / "wikis"
    d.mkdir()                              # NOTE: deliberately no order.json
    _write(d / "a.md", """\
        # A

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        The theorem of the data-channel survey
        <!-- secxref:5.4.1 -->[§5.4.1](../surveys/data-channel.md#sec-5.4.1) applies.
        """)
    # An unrelated sibling that happens to own the same section number.
    _write(d / "unrelated.md", """\
        # Unrelated

        <!-- sec:5.4.1 -->
        ## <a id="sec-5.4.1"></a>5.4.1 Something else entirely
        """)

    subprocess.run([sys.executable, str(TOOL), str(d / "a.md")],
                   capture_output=True, text=True)
    body = (d / "a.md").read_text(encoding="utf-8")
    assert "../surveys/data-channel.md#sec-5.4.1" in body, \
        "the original cross-corpus target must survive"
    assert "unrelated.md#sec-5.4.1" not in body, \
        "must NOT resolve against a sibling in a non-survey directory"

    r = _run(d / "a.md")
    assert r.returncode != 0
    assert "5.4.1" in (r.stdout + r.stderr)


def test_secxref_resolves_against_an_h1_anchor(tmp_path):
    """H1-title surveys (multimodal, interpretability, …) carry the section number in the
    body file's H1: `# 3 · Direction-of-Arrival Estimation`. `match_heading`
    excludes H1 by design, so the number is invisible to the grammar — but an
    `<a id="sec-3">` on that line IS a link target, and
    `build_survey_heading_index` indexes anchors on any heading line.

    This is what makes `secxref:3` resolve without teaching the grammar about H1
    (which would make crosslink index a whole file as one section).
    `todos/2026-07-09-h1-section-anchors.md`, `bugs/2026-07-09-09`.
    """
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "order.json", '["index.md", "linear-receivers.md", "appendix.md"]')
    _write(d / "index.md", "# Survey\n\n## Executive summary\n")
    _write(d / "linear-receivers.md", """\
        # <a id="sec-3"></a>3. Linear Receivers

        <!-- sec:3.1 -->
        ## <a id="sec-3.1"></a>3.1 The MRC hierarchy
        """)
    _write(d / "appendix.md", """\
        # <a id="sec-A"></a>Appendix A — Derivations

        Comparing the families of <!-- secxref:3 -->[§3](index.md#sec-3).
        """)

    subprocess.run([sys.executable, str(TOOL), str(d / "appendix.md")],
                   capture_output=True, text=True)
    body = (d / "appendix.md").read_text(encoding="utf-8")
    assert "[§3](linear-receivers.md#sec-3)" in body, \
        "secxref:3 must resolve to the file whose H1 declares section 3"
    assert "index.md#sec-3" not in body

    assert _run(d / "appendix.md").returncode == 0


def test_h1_anchor_is_not_a_heading_for_injection(tmp_path):
    """renumber-sections must neither inject into nor strip an H1 anchor —
    `inject_heading_anchor` matches `^(#{2,6}\\s+)`. That is the whole reason the
    anchor-only approach is safe."""
    f = tmp_path / "w.md"
    _write(f, '# <a id="sec-3"></a>3 · Fundamentals\n\nBody.\n\n## 3.1 Sub\n\nMore.\n')
    subprocess.run([sys.executable, str(TOOL), str(f)], capture_output=True, text=True)
    out = f.read_text(encoding="utf-8")
    assert '# <a id="sec-3"></a>3 · Fundamentals' in out, "H1 anchor must survive"
    assert "<!-- sec:3 -->" not in out.split("\n")[0], "no marker injected above H1"


def test_secxref_with_no_matching_anchor_is_an_orphan_not_silence(tmp_path):
    """The 35 dead links. `secxref:A` with no `sec-A` anywhere must be reported."""
    d = tmp_path / "svy"
    d.mkdir()
    _write(d / "order.json", '["a.md", "appendix-a.md"]')
    _write(d / "a.md", """\
        # A

        <!-- sec:1.1 -->
        ## <a id="sec-1.1"></a>1.1 Intro

        See <!-- secxref:A -->[§A](appendix-a.md).
        """)
    _write(d / "appendix-a.md", "# Appendix\n\n## Appendix A — no anchor here\n")
    r = _run(d / "a.md")
    assert r.returncode != 0
    assert "secxref:A" in (r.stdout + r.stderr)
