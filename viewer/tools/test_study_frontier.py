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
