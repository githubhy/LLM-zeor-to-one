#!/usr/bin/env python3
r"""The whole test suite must be collectible in ONE command.

Until 2026-08-22 it was not:

    $ python3 -m pytest tests/ viewer/tools/tests/ --collect-only -q
    E   ModuleNotFoundError: No module named 'tests.afe_calibration'      (x50)

Two top-level packages were both named `tests` — the repo's own `tests/__init__.py` and
`viewer/tools/tests/__init__.py`. `import tests` resolved to whichever directory reached
`sys.path` first, and every submodule under the other one disappeared.

**Each tree collected cleanly alone** (2632 and 180), which is exactly why the repo's split
runners — `unittest discover -s viewer/tools/tests` in the push gate, `pytest tests/…` in
CI — never surfaced it. The only way to see it was to ask for both at once, and nothing
did. It is the same shape as the gate defects found the same day: a green result that
covers a population smaller than the one you think you asked about.

The marker existed because the push gate ran `unittest discover … -t .`, which requires the
start directory to be importable as a package. Pointing `-t` at the directory itself needs
no package, so the marker is gone — which also matches the repo's own convention, since no
other test subdirectory carries one. (`tests/ntn_cell_search/__init__.py`, added earlier
the same day, broke collection the same way within the hour and was removed.)
"""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TREES = ["tests", "viewer/tools/tests"]


class TestBothTreesCollectTogether(unittest.TestCase):

    def setUp(self):
        for t in TREES:
            if not (ROOT / t).is_dir():
                self.skipTest(f"{t} not in this checkout")

    #: The collision this guards produces `ModuleNotFoundError: No module named
    #: 'tests.<something>'` — one `tests` package shadowing the other. An ordinary
    #: missing third-party dependency (torch, numpy) produces the SAME exception type
    #: for a completely different reason, and conflating the two makes this test fail on
    #: any machine without the experiment deps installed, which is how a guard gets
    #: deleted. Match the collision specifically.
    COLLISION = re.compile(r"No module named '(?:tests|viewer)[.']")

    def test_one_command_collects_every_test(self):
        r = subprocess.run(
            [sys.executable, "-m", "pytest", *TREES, "--collect-only", "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=600)
        out = r.stdout + r.stderr
        self.assertIsNone(self.COLLISION.search(out),
                          "the two-packages-named-tests collision is back")
        missing = sorted(set(re.findall(r"No module named '([A-Za-z0-9_]+)'", out)))
        if missing:
            self.skipTest("collection blocked by absent third-party dep(s) "
                          f"{missing}, not by a package collision — the collision "
                          "assertion above still ran and passed")
        self.assertEqual(r.returncode, 0, out[-1500:])
        m = re.search(r"(\d+) tests collected", r.stdout)
        self.assertIsNotNone(m, r.stdout[-600:])
        self.assertGreater(int(m.group(1)), 400,
                           "the collected count fell far below the measured baseline "
                           "— a tree stopped being collected")

    def test_the_sum_is_the_whole_and_not_one_tree(self):
        """A collision does not always error: whichever `tests` package wins, the other
        tree can simply go missing. Compare the joint count against the parts."""
        counts = {}
        for t in TREES + [None]:
            args = TREES if t is None else [t]
            r = subprocess.run(
                [sys.executable, "-m", "pytest", *args, "--collect-only", "-q"],
                cwd=ROOT, capture_output=True, text=True, timeout=600)
            m = re.search(r"(\d+) tests collected", r.stdout)
            if m is None and "No module named" in (r.stdout + r.stderr):
                self.skipTest(f"{args}: collection blocked by an absent third-party "
                              "dependency, not by a package collision")
            self.assertIsNotNone(m, f"{args}: {r.stdout[-400:]}")
            counts["both" if t is None else t] = int(m.group(1))
        self.assertEqual(counts["both"], counts["tests"] + counts["viewer/tools/tests"],
                         f"joint collection lost tests: {counts}")


class TestNoDuplicateTopLevelTestPackage(unittest.TestCase):
    r"""Only ONE directory that a runner will put on `sys.path` may be importable as the
    top-level package `tests`.

    The first draft of this test asserted something stronger and FALSE — that no test
    subdirectory carries an `__init__.py`. Nine of them do (`tests/afe_calibration`,
    `tests/prach`, `tests/campaign`, …) and the rest do not; the convention is genuinely
    mixed and that mix is not itself a defect. The test failed, which is how the wrong
    premise was caught rather than shipped.

    What IS a defect is two directories answering to the same top-level name. Measured
    upstream, four did: `tests/`, `viewer/tools/tests/`, a sim-local test tree, and
    the two archived `bench/…/{original,proposed}/tests/`. `viewer/tools/tests/` is fixed
    here (its marker is gone; the push gate points `-t` at the directory instead). The
    others are recorded in `todos/2026-08-22-two-packages-named-tests.md`: the sim tree
    is collectible alongside `tests/` under `--import-mode=importlib`, and the two bench
    trees are snapshot COPIES of one study, which cannot coexist in a single collection
    under any import mode and are not a suite anyone runs.
    """

    #: Directories importable as top-level `tests` that a runner actually reaches.
    LIVE_ROOTS = ["tests"]
    #: Known and accepted, with the reason recorded above.
    ARCHIVED_OR_TRACKED = ["bench/"]

    def test_the_gated_trees_do_not_share_a_top_level_package_name(self):
        markers = sorted(
            str(p.parent.relative_to(ROOT))
            for p in ROOT.rglob("tests/__init__.py")
            if not any(x in p.parts for x in (".git", "node_modules", ".venv", "download")))
        unexpected = [m for m in markers
                      if m not in self.LIVE_ROOTS
                      and not any(m.startswith(a) for a in self.ARCHIVED_OR_TRACKED)]
        self.assertEqual(
            unexpected, [],
            "a new directory is importable as the top-level package `tests`; `import "
            "tests` will resolve to whichever reaches sys.path first and hide the other. "
            "Either drop its __init__.py (and point any `unittest discover -t` at the "
            "directory itself) or add it to ARCHIVED_OR_TRACKED with a reason.")

    def test_the_push_gate_does_not_require_a_package_marker(self):
        """`-t .` needs one; `-t viewer/tools/tests` does not. Reverting the flag would
        silently re-create the collision."""
        hook = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
        self.assertIn("unittest discover -s viewer/tools/tests -t viewer/tools/tests", hook)
        self.assertFalse((ROOT / "viewer/tools/tests/__init__.py").exists(),
                         "the marker is back")


if __name__ == "__main__":
    unittest.main()
