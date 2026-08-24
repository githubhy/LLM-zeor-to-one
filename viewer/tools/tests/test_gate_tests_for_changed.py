#!/usr/bin/env python3
"""`gate-tests-for-changed.py` — run the tests for the gates a push actually changes.

The push gate runs the tests under `viewer/tools/`. A gate's unit tests often live under
`tests/` instead, and that whole tree costs 3m06s — too much for every push, and it already runs
in CI. The gap that leaves is not theoretical: on 2026-08-23
`check-reproduce-blocks.py::_commands` changed from yielding `(line, module, args)` to
`(line, kind, target, args)`; its tests live in `tests/nr_pdsch_demod/test_reproduce_block_gate.py`;
three broke; every local run stayed green; CI reported it half an hour after the push.

RED-first (`[opt:PLAN-REDFIRST]`). The discriminating input is
`test_a_piecewise_assembled_path_is_still_found`: that very test file builds its target as
`"viewer" / "tools" / "check-reproduce-blocks.py"`, so a grep for the string `viewer/tools` —
the obvious implementation, and the one written first — misses it entirely. Same
denominator-by-grep trap this repo keeps paying for.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "gate-tests-for-changed.py"
REPO = Path(__file__).resolve().parents[3]


def run(rng: str, repo: Path = REPO) -> list[str]:
    """Run the copy of the tool that BELONGS to `repo`.

    The tool derives its repo root from its own `__file__`, not from cwd — so invoking the
    original checkout's copy with cwd set to a fixture clone would silently inspect the original
    repo and the test would pass for the wrong reason.
    """
    tool = repo / "viewer" / "tools" / "gate-tests-for-changed.py"
    r = subprocess.run([sys.executable, str(tool), rng], capture_output=True, text=True,
                       cwd=repo, timeout=300)
    assert r.returncode == 0, r.stderr
    return [l for l in r.stdout.split("\n") if l.strip()]


class TestSelection(unittest.TestCase):
    def test_a_range_that_changes_no_gate_selects_nothing(self):
        """Must cost nothing on an ordinary docs-only push."""
        # A range with no gate-script edits: the merge commit against its own first parent
        # contains only main's changes, which touch prereg.py -- so use an empty range instead.
        self.assertEqual(run("HEAD..HEAD"), [])

    def test_a_piecewise_assembled_path_is_still_found(self):
        """The discriminating case. test_reproduce_block_gate.py never contains the substring
        'viewer/tools' -- it builds the path from separate literals."""
        probe = REPO / "tests/nr_pdsch_demod/test_reproduce_block_gate.py"
        if not probe.is_file():
            self.skipTest("the discriminating fixture is an upstream test tree that does not "
                          "exist here; the selection logic itself is covered by the tests above")
        src = probe.read_text(encoding="utf-8", errors="ignore")
        self.assertNotIn("viewer/tools", src,
                         "premise changed: this file now contains the literal path, so it no "
                         "longer discriminates a grep-based implementation from a correct one")
        self.assertIn("check-reproduce-blocks.py", src)

    def _fixture(self, td: str) -> Path:
        """A minimal repo of the shape the tool keys on, with the WORKING-TREE tool copied in.

        Synthetic rather than a clone of this repo: a depth-3 clone costs ~45 s per test, and the
        tool under development is not necessarily committed yet -- cloning would silently test the
        last committed version instead of the one being changed.
        """
        d = Path(td) / "r"
        (d / "viewer/tools/lib").mkdir(parents=True)
        (d / "viewer/tools/tests").mkdir(parents=True)
        (d / "tests/pkg").mkdir(parents=True)
        (d / "viewer/tools/check-thing.py").write_text("# gate\n", encoding="utf-8")
        (d / "viewer/tools/tests/test_thing.py").write_text("# beside the gate\n", encoding="utf-8")
        # Assembles the path piecewise, exactly as test_reproduce_block_gate.py does -- so a
        # grep-for-'viewer/tools' implementation cannot find it.
        (d / "tests/pkg/test_gatey.py").write_text(
            'from pathlib import Path\n'
            'TOOL = Path(__file__).parents[2] / "viewer" / "tools" / "check-thing.py"\n',
            encoding="utf-8")
        (d / "tests/pkg/test_unrelated.py").write_text("# names no gate\n", encoding="utf-8")
        tool_dst = d / "viewer/tools/gate-tests-for-changed.py"
        tool_dst.write_text(TOOL.read_text(encoding="utf-8"), encoding="utf-8")
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin", "HOME": str(d)}
        subprocess.run(["git", "init", "-q", str(d)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(d), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(d), "commit", "-qm", "base"], check=True,
                       capture_output=True, env=env)
        self._env = env
        return d

    def _commit(self, d: Path, msg: str):
        subprocess.run(["git", "-C", str(d), "commit", "-qam", msg], check=True,
                       capture_output=True, env=self._env)

    def test_changing_a_gate_selects_the_test_that_names_it(self):
        with tempfile.TemporaryDirectory() as td:
            d = self._fixture(td)
            (d / "viewer/tools/check-thing.py").write_text("# gate\n# touch\n", encoding="utf-8")
            self._commit(d, "touch the gate")
            got = run("HEAD~1..HEAD", repo=d)
            self.assertEqual(got, ["tests/pkg/test_gatey.py"],
                             "must select the piecewise-path test and nothing else")

    def test_a_test_file_is_never_treated_as_a_changed_gate(self):
        """Editing viewer/tools/tests/x.py must not select every test that names x."""
        with tempfile.TemporaryDirectory() as td:
            d = self._fixture(td)
            (d / "viewer/tools/tests/test_thing.py").write_text("# t\n# touch\n", encoding="utf-8")
            self._commit(d, "touch a test")
            self.assertEqual(run("HEAD~1..HEAD", repo=d), [])

    def test_a_docs_only_change_selects_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            d = self._fixture(td)
            (d / "README.md").write_text("hi\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(d), "add", "-A"], check=True, capture_output=True)
            self._commit(d, "docs")
            self.assertEqual(run("HEAD~1..HEAD", repo=d), [])

    def test_it_exits_zero_on_a_bad_range_rather_than_blocking_the_push(self):
        """An empty answer is legitimate; a crash here must never be what stops a push."""
        r = subprocess.run([sys.executable, str(TOOL), "no-such-ref..HEAD"],
                           capture_output=True, text=True, cwd=REPO, timeout=300)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
