"""Tests for study-frontier.py — the Tier-1 detector of the /study session pattern."""
from __future__ import annotations

import importlib.util
import pathlib
import sys

_MOD = pathlib.Path(__file__).with_name("study-frontier.py")
_spec = importlib.util.spec_from_file_location("study_frontier", _MOD)
sf = importlib.util.module_from_spec(_spec)
sys.modules["study_frontier"] = sf
_spec.loader.exec_module(sf)


def _write(tmp_path: pathlib.Path, rel: str, body: str) -> pathlib.Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_scan_counts_sections_and_folds(tmp_path):
    p = _write(tmp_path, "a.md", "\n".join([
        "# Title",                     # H1 is not a section
        "## 1 First",
        "text",
        "> **Note — why this way.** because.",
        "### 1.1 Second",
        "> <a id=\"p-x\"></a><!-- para:x --> **Note — what breaks it.** this.",
    ]))
    assert sf.scan_file(p) == (2, 2)


def test_folds_inside_a_fence_do_not_count(tmp_path):
    """A fenced example of the fold syntax is documentation, not a recorded question."""
    p = _write(tmp_path, "b.md", "\n".join([
        "## 1 Only section",
        "```markdown",
        "> **Note — this is an example.** not a real fold.",
        "```",
        "## 2 Another",
    ]))
    assert sf.scan_file(p) == (2, 0)


def test_ranking_puts_least_interrogated_first_and_breaks_ties_by_size(tmp_path):
    _write(tmp_path, "surveys/s/heavy.md", "## a\n> **Note — q.** a.\n## b\n")
    _write(tmp_path, "surveys/s/small-untouched.md", "## a\n## b\n")
    _write(tmp_path, "surveys/s/big-untouched.md", "## a\n## b\n## c\n## d\n")
    rows = sf.collect(tmp_path)
    paths = [r["path"] for r in rows]
    # zero-fold documents outrank the folded one ...
    assert paths.index("surveys/s/big-untouched.md") < paths.index("surveys/s/heavy.md")
    # ... and among zero-fold documents the larger one is the higher-stakes target
    assert paths.index("surveys/s/big-untouched.md") < paths.index("surveys/s/small-untouched.md")


def test_keepout_and_references_are_never_targets(tmp_path):
    _write(tmp_path, "surveys/attention-demo/fixture.md", "## a\n## b\n")
    _write(tmp_path, "surveys/s/references.md", "## a\n## b\n")
    _write(tmp_path, "surveys/s/real.md", "## a\n")
    paths = [r["path"] for r in sf.collect(tmp_path)]
    assert paths == ["surveys/s/real.md"]


def test_sectionless_stub_is_skipped(tmp_path):
    """A file with no H2+ heading has nothing to interrogate and must not rank first."""
    _write(tmp_path, "surveys/s/stub.md", "just prose, no headings\n")
    _write(tmp_path, "surveys/s/real.md", "## a\n")
    assert [r["path"] for r in sf.collect(tmp_path)] == ["surveys/s/real.md"]


def test_wikis_are_scanned_too(tmp_path):
    _write(tmp_path, "wikis/w.md", "## a\n## b\n")
    assert [r["path"] for r in sf.collect(tmp_path)] == ["wikis/w.md"]


# --- prerequisite gate (zone of proximal development) -----------------------

def test_prereq_map_is_first_match_wins(tmp_path):
    _write(tmp_path, ".claude/study-prereqs", "\n".join([
        "# comment ignored",
        "1  surveys/s/appendix-a*.md",
        "4  surveys/s/*.md",
    ]))
    m = sf.load_prereqs(tmp_path)
    assert sf.prereq_for("surveys/s/appendix-a-qkv.md", m) == 1
    assert sf.prereq_for("surveys/s/other.md", m) == 4
    # unmapped documents are never hidden -- absence of data is not evidence of depth
    assert sf.prereq_for("wikis/unmapped.md", m) is None


def test_gate_hides_documents_more_than_one_rung_above_the_reader(tmp_path):
    rows = [
        {"path": "a.md", "prereq": 1}, {"path": "b.md", "prereq": 2},
        {"path": "c.md", "prereq": 3}, {"path": "d.md", "prereq": None},
    ]
    reach, held = sf.apply_gate(rows, reader_rung=1)
    assert [r["path"] for r in reach] == ["a.md", "b.md", "d.md"]
    assert [r["path"] for r in held] == ["c.md"]


def test_gate_is_a_no_op_when_the_reader_rung_is_unknown(tmp_path):
    """Fail open, like every other .claude/ severity toggle."""
    rows = [{"path": "c.md", "prereq": 7}]
    reach, held = sf.apply_gate(rows, reader_rung=None)
    assert len(reach) == 1 and held == []


def test_reader_rung_file_parses_the_l_prefix(tmp_path):
    _write(tmp_path, ".claude/study-reader-rung", "L2\n")
    assert sf.load_reader_rung(tmp_path) == 2
    assert sf.load_reader_rung(tmp_path / "nonexistent") is None


# --- recall queue (retrieval practice) --------------------------------------

def test_collect_folds_finds_line_numbers_and_the_note_lead(tmp_path):
    _write(tmp_path, "surveys/s/a.md", "\n".join([
        "## 1 Sec",
        "> **Note — why is the scale factor sqrt(d_k)?** Because ...",
        "prose",
        "> <a id=\"p-x\"></a><!-- para:x --> **Note — what breaks it.** This.",
    ]))
    folds = sf.collect_folds(tmp_path)
    assert [f["line"] for f in folds] == [2, 4]
    assert folds[0]["lead"] == "why is the scale factor sqrt(d_k)?"
    assert folds[1]["lead"] == "what breaks it."


def test_parse_blame_porcelain_maps_final_line_to_author_time():
    text = "\n".join([
        "0" * 40 + " 1 1 1",
        "author-time 1000",
        "\tline one",
        "1" * 40 + " 2 7 1",
        "author-time 2000",
        "\tline seven",
    ])
    assert sf.parse_blame_porcelain(text) == {1: 1000, 7: 2000}


def test_recall_orders_oldest_first(tmp_path):
    day = 86400
    folds = [
        {"path": "a.md", "line": 1, "lead": "new", "epoch": 100 * day},
        {"path": "b.md", "line": 2, "lead": "old", "epoch": 70 * day},
        {"path": "c.md", "line": 3, "lead": "mid", "epoch": 90 * day},
    ]
    out = sf.rank_recall(folds, now=101 * day)
    assert [f["lead"] for f in out] == ["old", "mid", "new"]
    assert [f["age_days"] for f in out] == [31, 11, 1]


def test_recall_skips_uncommitted_folds(tmp_path):
    """A fold written minutes ago is not due for retrieval practice."""
    folds = [{"path": "a.md", "line": 1, "lead": "fresh", "epoch": None}]
    assert sf.rank_recall(folds, now=10**9) == []
