#!/usr/bin/env python3
"""`check-skill-options.py` — the `[opt:ID]` marker <-> `.claude/skill-options.json` invariant.

`CLAUDE.md` makes the registry THE mechanism for skill/rule options: an agent following an
annotated rule reads the registry and, if the option is `off`, skips the marked block and reverts
to its documented `off_behavior`. That requires both halves to agree, and nothing checked it --
53 options across ~30 files, maintained by hand. They had already drifted:
`[opt:MATH-REDERIVE-GATE]` was marked in `.claude/rules/workflow.md` with no registry entry, so
the documented toggle had nothing to flip.

RED-first (`[opt:PLAN-REDFIRST]`). The discriminating input is
`test_a_marker_with_no_registry_entry_is_drift` — the exact live shape of that bug.

The second load-bearing test is `test_a_proposal_talking_about_an_option_is_NOT_drift`. Repo-wide
the invariant is false and should be: of the five unregistered markers measured on 2026-08-23,
four were legitimate -- a literal `[opt:<ID>]` documenting the SYNTAX, a `[opt:SP-...]` prose
fragment, a proposal's working name, and a `todos/` item not yet built. A gate reporting four
false positives in five is one nobody reads
(`decisions/2026-08-23-phrasing-gate-goes-to-error-at-a-zero-backlog`).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "check-skill-options.py"
REAL_ROOT = Path(__file__).resolve().parents[2]


class Fake:
    """A miniature repo with the same layout the tool keys on."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / ".claude/rules").mkdir(parents=True)
        (self.d / "viewer/tools").mkdir(parents=True)
        # The tool locates the registry as parents[2] of its own path.
        self.tool = self.d / "viewer/tools/check-skill-options.py"
        self.tool.write_text(TOOL.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.d, check=True)
        return self

    def __exit__(self, *a):
        self.tmp.cleanup()

    def registry(self, ids):
        (self.d / ".claude/skill-options.json").write_text(
            json.dumps({"id": "t", "options": {i: {"default": "on"} for i in ids}}),
            encoding="utf-8")

    def rule(self, name, text):
        (self.d / ".claude/rules" / name).write_text(text, encoding="utf-8")

    def other(self, rel, text):
        p = self.d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run(self):
        subprocess.run(["git", "add", "-A"], cwd=self.d, capture_output=True)
        return subprocess.run([sys.executable, str(self.tool)],
                              capture_output=True, text=True, timeout=120)


class TestInvariant(unittest.TestCase):
    def test_a_matched_pair_passes(self):
        with Fake() as f:
            f.registry(["A-ONE"])
            f.rule("r.md", "do the thing `[opt:A-ONE · default ON]`\n")
            r = f.run()
            self.assertEqual(r.returncode, 0, r.stderr)

    # -- the discriminating case ------------------------------------------------------
    def test_a_marker_with_no_registry_entry_is_drift(self):
        with Fake() as f:
            f.registry(["A-ONE"])
            f.rule("r.md", "`[opt:A-ONE]` and `[opt:A-TWO · default ON]`\n")
            r = f.run()
            self.assertEqual(r.returncode, 1)
            self.assertIn("UNREGISTERED A-TWO", r.stderr)

    def test_a_registry_entry_marked_nowhere_is_drift(self):
        with Fake() as f:
            f.registry(["A-ONE", "A-GHOST"])
            f.rule("r.md", "`[opt:A-ONE]`\n")
            r = f.run()
            self.assertEqual(r.returncode, 1)
            self.assertIn("UNMARKED A-GHOST", r.stderr)

    # -- scope: where the invariant actually holds -------------------------------------
    def test_a_proposal_talking_about_an_option_is_NOT_drift(self):
        """A proposals/ or todos/ file discussing an unbuilt option is not a live annotation."""
        with Fake() as f:
            f.registry(["A-ONE"])
            f.rule("r.md", "`[opt:A-ONE]`\n")
            f.other("proposals/p.md", "we could add `[opt:A-FUTURE · default OFF]`\n")
            f.other("todos/t.md", "not built yet: `[opt:A-LATER]`\n")
            r = f.run()
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_marker_OUTSIDE_the_rules_still_satisfies_an_entry(self):
        """The reverse direction is repo-wide: an entry pointed at from a report is alive."""
        with Fake() as f:
            f.registry(["A-ONE", "A-ELSEWHERE"])
            f.rule("r.md", "`[opt:A-ONE]`\n")
            f.other("reports/x.md", "shipped `[opt:A-ELSEWHERE · default OFF]`\n")
            self.assertEqual(f.run().returncode, 0)

    def test_the_literal_syntax_placeholder_is_not_an_option(self):
        """`[opt:<ID>]` in prose documents the FORMAT; it is not a use of an option `ID`."""
        with Fake() as f:
            f.registry(["A-ONE"])
            f.rule("r.md", "marker form is `[opt:<ID> · default ON]`; see `[opt:A-ONE]`\n")
            self.assertEqual(f.run().returncode, 0)

    # -- REFUSE is not PASS -----------------------------------------------------------
    def test_a_missing_registry_refuses(self):
        with Fake() as f:
            f.rule("r.md", "`[opt:A-ONE]`\n")
            r = f.run()
            self.assertEqual(r.returncode, 2)
            self.assertIn("REFUSING", r.stderr)

    def test_zero_markers_refuses_rather_than_reporting_clean(self):
        """If the marker syntax ever changes, silence must not read as compliance."""
        with Fake() as f:
            f.registry(["A-ONE"])
            f.rule("r.md", "no markers here at all\n")
            r = f.run()
            self.assertEqual(r.returncode, 2)
            self.assertIn("REFUSING", r.stderr)

    def test_an_unreadable_registry_refuses(self):
        with Fake() as f:
            (f.d / ".claude/skill-options.json").write_text("{not json", encoding="utf-8")
            f.rule("r.md", "`[opt:A-ONE]`\n")
            self.assertEqual(f.run().returncode, 2)


class TestLiveRepo(unittest.TestCase):
    def test_the_real_repo_satisfies_the_invariant(self):
        r = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                           cwd=REAL_ROOT, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
