#!/usr/bin/env python3
"""`check-reproduce-blocks.py` — the `python <path>.py` half of the population.

The gate printed `136/136 documented commands` on every push. That reads as complete and was 136
of **297**: the matcher was `python -m ...` only, so 161 `python <path>.py` commands — 54% — sat
outside the denominator entirely. A reproduce block is the one artifact a stranger is told to trust
(`.claude/rules/sim-report-completeness.md` § 12), so an unread half is an unearned green.

RED-first (`[opt:PLAN-REDFIRST]`). The discriminating input is
`test_a_path_command_naming_a_missing_script_is_caught`: invisible to the pre-fix matcher, which
reports clean.

The second load-bearing test is `test_a_cd_in_the_same_block_resolves_a_relative_script`. On the
live corpus, ignoring `cd` reports **33 false positives — and all 33 resolve once it is honoured**,
so an implementation that skips it is not "slightly noisy", it is wrong about every relative path
in the repo.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "check-reproduce-blocks.py"
# NB parents[3]: this file is viewer/tools/tests/x.py, one level deeper than the TOOL
# (viewer/tools/x.py) whose own REPO is parents[2].
REPO = Path(__file__).resolve().parents[3]


def run_on(md: str) -> subprocess.CompletedProcess:
    """Write `md` into a temp report under the real repo and gate just that file."""
    d = REPO / "reports"
    with tempfile.NamedTemporaryFile("w", dir=d, suffix=".md", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(md)
        p = Path(fh.name)
    try:
        return subprocess.run([sys.executable, str(TOOL), str(p), "--severity", "error"],
                              capture_output=True, text=True, timeout=300)
    finally:
        p.unlink(missing_ok=True)


FENCE = "```"


class TestPathCommands(unittest.TestCase):
    def test_a_path_command_naming_a_missing_script_is_caught(self):
        r = run_on(f"# t\n\n{FENCE}\npython definitely_not_a_real_script_xyz.py --n 10\n{FENCE}\n")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("script not found", r.stdout)

    def test_a_cd_in_the_same_block_resolves_a_relative_script(self):
        """33 of 33 live 'missing' scripts were this. Ignoring `cd` fails every one."""
        r = run_on(f"# t\n\n{FENCE}\ncd viewer/tools\npython check-lineage.py --scan x\n{FENCE}\n")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_repo_root_relative_script_resolves(self):
        r = run_on(f"# t\n\n{FENCE}\npython viewer/tools/check-lineage.py --scan x\n{FENCE}\n")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_the_cd_does_not_leak_into_the_next_block(self):
        """Each fenced block starts at the repo root; a stale cwd would mask a real miss."""
        r = run_on(f"# t\n\n{FENCE}\ncd viewer/tools\n{FENCE}\n\n"
                   f"{FENCE}\npython definitely_not_a_real_script_xyz.py\n{FENCE}\n")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_a_path_command_outside_a_fence_is_ignored(self):
        """Prose mentioning a script is not a recipe. It must not be FLAGGED -- and with no
        command left to read, the tool must REFUSE (2) rather than report a clean 0, which is
        the same 'looked at nothing' rule the fenced case obeys."""
        r = run_on("# t\n\npython definitely_not_a_real_script_xyz.py\n")
        self.assertNotEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("script not found", r.stdout)
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_the_summary_states_BOTH_halves_of_the_denominator(self):
        """A green line must not be over-readable: say what each half was checked for."""
        r = run_on(f"# t\n\n{FENCE}\npython viewer/tools/check-lineage.py --scan x\n{FENCE}\n")
        self.assertIn("checked for EXISTENCE only", r.stdout)
        self.assertIn("`python -m` checked for flags", r.stdout)

    def test_the_finding_prints_the_form_the_document_uses(self):
        """The old format prefixed everything `-m`, sending readers after a phantom module."""
        r = run_on(f"# t\n\n{FENCE}\npython definitely_not_a_real_script_xyz.py\n{FENCE}\n")
        self.assertIn("python definitely_not_a_real_script_xyz.py:", r.stdout)
        self.assertNotIn("-m definitely_not_a_real_script_xyz.py", r.stdout)

    def test_the_module_form_still_works(self):
        """The control: extending the scanner must not break what it already caught."""
        r = run_on(f"# t\n\n{FENCE}\npython -m no.such.module.at.all --x\n{FENCE}\n")
        self.assertEqual(r.returncode, 1, r.stdout)


class TestLiveRepo(unittest.TestCase):
    def test_the_live_corpus_has_no_unrunnable_path_command(self):
        """Zero, not "the two we know about". The gate found exactly two on the day it learned to
        read this form -- the OMS-DE harness recipe -- and § 7 of that report was rewritten to say
        plainly that the harness is not in the repo rather than print a recipe failing on line 1
        (todos/2026-08-23-oms-de-verification-harness-is-gone). A ratchet at 2 would let the next
        one in silently."""
        r = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                           cwd=REPO, timeout=600)
        self.assertIn("copyable command(s) OK", r.stdout)
        self.assertEqual(r.stdout.count("script not found"), 0,
                         "an unrunnable path command appeared: " + r.stdout)


if __name__ == "__main__":
    unittest.main()
