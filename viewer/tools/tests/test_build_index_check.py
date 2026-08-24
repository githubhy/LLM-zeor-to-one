#!/usr/bin/env python3
r"""Controls for `build-index.py --check`.

A `.index.md` maps each survey section to its LINE RANGE, is committed, and is read by
`/enrich` to locate a section before editing it. Nothing regenerated or verified them.

Measured upstream: one survey appendix's `.index.md` had **all eleven** of its
ranges wrong — by 4 to 7 lines each — because the appendix grew and the index did not.

The second defect mattered more for gating than for reading: both committed indexes
carried an absolute **Windows** path from a *different clone*
(`C:\Users\admin\Repos\data-channel-receiver-2\…`) in their "Re-run:" header. Output that
embeds the generating machine can never be byte-stable across checkouts, so a
regenerate-and-diff gate would have reported a difference on every run and been useless.
The header is repo-relative now; that is what makes the gate possible.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "viewer" / "tools" / "build-index.py"


def _run(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                          capture_output=True, text=True, timeout=300)


def _survey(dirpath: Path, body_lines: int = 40) -> Path:
    src = dirpath / "appendix-z.md"
    lines = ["# Appendix Z — Fixture", ""]
    for i in (1, 2, 3):
        lines.append(f"## {i} Section {i}")
        lines += [f"prose line {i}.{j}" for j in range(body_lines)]
    src.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return src


class TestTheCheckSeesDrift(unittest.TestCase):

    def test_a_fresh_index_passes(self):
        with tempfile.TemporaryDirectory() as td:
            src = _survey(Path(td))
            self.assertEqual(_run(src, "--min-lines", "1").returncode, 0)
            r = _run(td, "--check")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("1/1 committed index", r.stdout)
            self.assertIn("0 stale", r.stdout)

    def test_an_index_whose_source_grew_is_reported_stale(self):
        """The measured defect: the document grows, the ranges do not."""
        with tempfile.TemporaryDirectory() as td:
            src = _survey(Path(td))
            _run(src, "--min-lines", "1")
            idx = src.parent / "appendix-z.index.md"
            before = idx.read_text(encoding="utf-8")
            src.write_text(src.read_text(encoding="utf-8").replace(
                "## 1 Section 1", "## 1 Section 1\ninserted\ninserted\n", 1), encoding="utf-8")
            r = _run(td, "--check")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("STALE", r.stdout)
            self.assertEqual(idx.read_text(encoding="utf-8"), before,
                             "--check must not write")

    def test_an_index_whose_source_vanished_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            src = _survey(Path(td))
            _run(src, "--min-lines", "1")
            src.unlink()
            r = _run(td, "--check")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("ORPHAN", r.stdout)

    def test_an_empty_set_refuses_rather_than_passing(self):
        """`.claude/rules/campaign-lifecycle.md`: a green gate must mean 'looked and
        found nothing'. The first version of this check globbed `*.md` non-recursively
        over `surveys/`, found ZERO indexes (both live in subdirectories) and exited 0 —
        it passed by looking nowhere."""
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "notes.md").write_text("# nothing here\n", encoding="utf-8")
            r = _run(td, "--check")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("REFUSE", r.stderr)

    def test_the_check_recurses_into_subdirectories(self):
        with tempfile.TemporaryDirectory() as td:
            sub = Path(td) / "some-survey"
            sub.mkdir()
            src = _survey(sub)
            _run(src, "--min-lines", "1")
            r = _run(td, "--check")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("1/1", r.stdout)


class TestTheOutputIsMachineIndependent(unittest.TestCase):

    def test_the_rerun_header_is_repo_relative(self):
        with tempfile.TemporaryDirectory() as td:
            src = _survey(Path(td))
            _run(src, "--min-lines", "1")
            head = (src.parent / "appendix-z.index.md").read_text(encoding="utf-8").split("\n")[1]
            self.assertIn("Re-run:", head)
            self.assertNotIn(td, head, "an absolute path is baked into a generated file")
            self.assertNotIn("\\", head, "a Windows separator would differ per machine")

    def test_no_committed_index_embeds_an_absolute_path(self):
        found = []
        for idx in sorted(ROOT.glob("surveys/**/*.index.md")):
            head = idx.read_text(encoding="utf-8").split("\n")[1]
            if re.search(r"[A-Za-z]:\\|/home/|/Users/", head):
                found.append(str(idx.relative_to(ROOT)))
        self.assertEqual(found, [], "a generated file records the machine that made it")


class TestTheLiveCorpusIsCurrent(unittest.TestCase):

    def setUp(self):
        if not (ROOT / "surveys").is_dir():
            self.skipTest("no surveys/ in this checkout")

    def test_every_committed_index_matches_its_source(self):
        r = _run(ROOT / "surveys", "--check")
        if r.returncode == 2 and "no .index.md" in (r.stdout + r.stderr):
            self.skipTest("this corpus has no committed .index.md yet - an index is opt-in, so "
                          "REFUSE is the correct verdict, not a failure. The synthetic-corpus "
                          "tests above cover the drift detection itself.")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = re.search(r"\[build-index\] (\d+)/(\d+) committed index", r.stdout)
        self.assertIsNotNone(m, r.stdout)
        self.assertEqual(m.group(1), m.group(2), r.stdout)
        self.assertGreaterEqual(int(m.group(2)), 2, "the index set shrank to nothing")


if __name__ == "__main__":
    unittest.main()
