"""Tests for the duplicate-figure-label gate (`check-figure-labels.py`).

Motivating incident (2026-07-16): two authors both independently concluded
"the next free appendix-G figure number is G10" from an incomplete grep,
which could have produced two captions both reading "**Fig. G10". Nothing
in the existing toolchain would have caught it -- PNG filenames differ, so
no file-overwrite and no existing gate fires. See
`decisions/2026-07-16-02-hdq-figure-number-g14-not-g10.md`.

The load-bearing correctness property this suite locks in: a figure label
MENTIONED in prose (bolded or not) must never count as a second
DECLARATION of that label. An earlier draft of the checker got this wrong
in a way a casual test would not catch -- see
test_bolded_prose_forward_reference_is_not_a_declaration below.
"""
import pathlib
import subprocess
import sys
import textwrap

TOOL = pathlib.Path(__file__).with_name("check-figure-labels.py")


def _run(*paths):
    return subprocess.run(
        [sys.executable, str(TOOL), *[str(p) for p in paths]],
        capture_output=True, text=True, encoding="utf-8",
    )


def _survey(tmp_path, files, order=None, name="svy"):
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    for fname, body in files.items():
        (d / fname).write_text(textwrap.dedent(body), encoding="utf-8")
    (d / "order.json").write_text(
        str(list(order or files)).replace("'", '"'), encoding="utf-8")
    return d


# ── The core correctness property: prose mention != declaration ──────────


def test_bare_prose_mention_is_not_a_second_declaration(tmp_path):
    """One real caption + several bare (unbolded) prose mentions of the same
    label must not fire -- the exact appendix-g.md G14 shape (1 caption, 4
    bare prose mentions of "Fig. G14" in the real corpus)."""
    d = _survey(tmp_path, {
        "appendix-g.md": """\
            Intro text. The magnitude is measured in Fig. G14 in this
            repo's own setting rather than borrowed from the paper.

            **Fig. G14 — HDQ's bit-plane greedy against the exact DP.**
            *Purpose:* make two things concrete...

            Two artifacts in Fig. G14 that are not algorithmic must not
            be read as findings. Fig. G14 measures the gap here.
            """,
    })
    r = _run(d)
    assert r.returncode == 0, f"unexpected failure:\n{r.stdout}\n{r.stderr}"
    assert "1 declared label(s)" in (r.stdout + r.stderr)


def test_bolded_prose_forward_reference_is_not_a_declaration(tmp_path):
    """A bolded forward-reference like "**Figure F1** confirms..." closes its
    bold span immediately after the raw ID with nothing in between. A real
    caption always carries more content (an em-dash title, or at least a
    trailing '.') before the bold closes. This is the exact shape that
    produced 8 false "duplicates" in the real corpus
    (surveys/attention-demo F1-F7, surveys/llms-for-coding/appendix-e.md
    E.2-c) before this exclusion was added."""
    d = _survey(tmp_path, {
        "fundamentals.md": """\
            The ZC autocorrelation is a single sharp peak. **Figure F1**
            confirms both properties numerically.

            **Figure F1 — Attention entropy vs. layer depth.** *(1) Purpose.*
            Periodic autocorrelation of the length-63 ZC root.
            """,
    })
    r = _run(d)
    assert r.returncode == 0, f"unexpected failure:\n{r.stdout}\n{r.stderr}"
    assert "1 declared label(s)" in (r.stdout + r.stderr)


def test_figure_of_merit_is_not_a_label(tmp_path):
    """'**Figure of merit**' is an English idiom, not a label declaration --
    the captured token must contain a digit or it is not counted at all."""
    d = _survey(tmp_path, {
        "framework.md": """\
            **Figure of merit** $G/T$ combines antenna gain and noise
            temperature into a single receiver-quality number.
            """,
    })
    r = _run(d)
    assert r.returncode == 0
    assert "0 declared label(s)" in (r.stdout + r.stderr)


def test_minimal_period_closed_caption_form_is_a_declaration(tmp_path):
    """'**Figure B.1.** The shift-invariance...' -- the minimal caption shape
    (ID + trailing period, no em-dash title) must still count as a real
    declaration, not be mistaken for the excluded bare-close prose shape."""
    d = _survey(tmp_path, {
        "appendix-b.md": """\
            **Figure B.1.** The shift-invariance structure underlying
            ESPRIT. A ULA of N_r elements is split into two sub-arrays.
            """,
    })
    r = _run(d)
    assert r.returncode == 0
    assert "1 declared label(s)" in (r.stdout + r.stderr)


# ── Catches a real duplicate ──────────────────────────────────────────────


def test_duplicate_caption_declaration_fires(tmp_path):
    """Two real captions both declaring '**Fig. G10' -- the failure mode
    that motivated this gate -- must be reported and must exit non-zero."""
    d = _survey(tmp_path, {
        "appendix-g.md": """\
            **Fig. G10 — HDQ prototype, first attempt.** *Purpose:* ...

            Some unrelated prose in between.

            **Fig. G10 — a completely different figure, added later.**
            *Purpose:* ...
            """,
    })
    r = _run(d)
    assert r.returncode == 1
    out = r.stdout + r.stderr
    assert "duplicate label" in out.lower()
    assert "G10" in out
    assert "appendix-g.md" in out


def test_duplicate_across_files_in_same_survey_fires(tmp_path):
    """The scope is the SURVEY (order.json), not the file -- a duplicate
    split across two files of the same survey must still be caught."""
    d = _survey(tmp_path, {
        "a.md": "**Figure 4.1 — First panel.** Some description text here.\n",
        "b.md": "**Figure 4.1 — Reused by mistake.** More description.\n",
    })
    r = _run(d)
    assert r.returncode == 1
    assert "4.1" in (r.stdout + r.stderr)


def test_same_label_in_different_surveys_does_not_collide(tmp_path):
    """Two unrelated surveys legitimately reusing 'Figure 1.1' as their own
    first figure must NOT be flagged -- scope is per-survey."""
    d1 = _survey(tmp_path, {
        "a.md": "**Figure 1.1 — Survey one's first figure.** Description.\n",
    }, name="survey-one")
    d2 = _survey(tmp_path, {
        "a.md": "**Figure 1.1 — Survey two's first figure.** Description.\n",
    }, name="survey-two")
    r = _run(d1, d2)
    assert r.returncode == 0, f"unexpected failure:\n{r.stdout}\n{r.stderr}"


def test_single_flat_file_survey_scope(tmp_path):
    """A lone .md file with no order.json is its own singleton scope."""
    f = tmp_path / "standalone-survey.md"
    f.write_text(
        "**Figure 1.1 — The only figure.** Description text.\n",
        encoding="utf-8",
    )
    r = _run(f)
    assert r.returncode == 0
    assert "1 scope(s)" in (r.stdout + r.stderr)


def test_corpus_root_does_not_merge_unrelated_flat_files(tmp_path):
    """Passing a corpus ROOT (no order.json at that level, multiple flat .md
    files directly inside it) must treat each flat file as its OWN scope,
    not lump them into one combined survey -- otherwise two unrelated flat
    surveys reusing 'Figure 1.1' would falsely collide."""
    root = tmp_path / "surveys"
    root.mkdir()
    (root / "alpha-survey.md").write_text(
        "**Figure 1.1 — Alpha's figure.** Text.\n", encoding="utf-8")
    (root / "beta-survey.md").write_text(
        "**Figure 1.1 — Beta's figure.** Text.\n", encoding="utf-8")
    r = _run(root)
    assert r.returncode == 0, f"unexpected collision:\n{r.stdout}\n{r.stderr}"
    assert "2 scope(s)" in (r.stdout + r.stderr)


def test_scratch_directory_is_excluded(tmp_path):
    """`_scratch/` is non-canonical work; a duplicate there must not block
    the gate (mirrors validate-refs.py --bare-refs-only's own exclusion)."""
    root = tmp_path / "surveys"
    scratch = root / "_scratch"
    scratch.mkdir(parents=True)
    (scratch / "notes.md").write_text(
        "**Fig. X1 — draft.** Text.\n\n**Fig. X1 — draft again.** Text.\n",
        encoding="utf-8",
    )
    r = _run(root)
    assert r.returncode == 2, "an all-_scratch corpus has nothing to check"


# ── Coverage-is-not-silent ─────────────────────────────────────────────────


def test_refuses_to_report_success_over_nothing(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _run(empty).returncode == 2


# ── Real corpus ─────────────────────────────────────────────────────────────


def test_the_real_corpus_is_clean():
    repo = pathlib.Path(__file__).resolve().parents[2]
    surveys = repo / "surveys"
    if not surveys.exists():
        return
    r = _run(surveys)
    assert r.returncode == 0, f"corpus has duplicate figure labels:\n{r.stderr}"
