#!/usr/bin/env python3
"""A green gate must mean "looked and found nothing", never "did not look".

`.claude/rules/campaign-lifecycle.md` puts it as a rule -- every gate reports what it
read of what it was named, and REFUSEs (exit 2) rather than passing when it has no
denominator -- and the repo has paid for it repeatedly: `check-value-ledger` read 12 of
811 files and exited 0, `validate-refs` read 1, and three equation gates produced
byte-identical output whether they passed or skipped
(`bugs/2026-08-22-three-gates-whose-pass-and-skip-looked-identical`).

The rule is not self-enforcing, so it decays. This test is the enforcement: point every
path-taking pre-push gate at an EMPTY directory and require it to be distinguishable
from a real pass.

Two acceptable answers, in descending strength:

  REFUSE  -- exit 2 (or non-zero) naming the empty scope. Preferred; most gates do this.
  COUNT   -- exit 0 but stating the denominator it read (`0 file(s)`), so a reader can
             see the scope was empty.

The forbidden answer is the third: exit 0 with nothing to say. `renumber-sections.py
--check surveys/ wikis/` gave exactly that until 2026-08-22 -- **zero bytes and exit 0
over 658 files, byte-identical to zero bytes and exit 0 over an empty directory** --
while its two siblings printed 130 KB and 52 KB. It is the pre-push gate for the whole
`sec-` / `secref` / `secxref` system, so a scope that silently resolved to nothing (a
rename, a sparse checkout, a typo in the hook) would have read as a clean pass.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "viewer" / "tools"

# (tool, args-before-the-path, args-after-the-path) exactly as .githooks/pre-push
# invokes them, with the corpus path replaced by an empty directory.
PATH_TAKING_GATES = [
    ("check-basis-declarations.py", [], []),
    ("check-crossfile-ref-markers.py", [], []),
    ("check-depth-tiers.py", [], []),
    ("check-figure-labels.py", [], []),
    ("check-link-fragments.py", [], ["--severity=warn"]),
    ("check-section-ownership.py", [], []),
    ("check-section-placeholders.py", [], []),
    ("check-value-ledger.py", [], []),
    ("renumber-equations.py", ["--check"], []),
    ("renumber-paragraphs.py", ["--check"], []),
    ("renumber-sections.py", ["--check"], []),
    ("validate-refs.py", [], []),
]


def _run(tool: str, argv: list[str]):
    return subprocess.run([sys.executable, str(TOOLS / tool), *argv],
                          capture_output=True, text=True, timeout=180)


class TestNoGatePassesSilentlyOverAnEmptyCorpus(unittest.TestCase):

    def test_every_path_taking_gate_is_distinguishable_from_a_real_pass(self):
        offenders = []
        with tempfile.TemporaryDirectory() as td:
            for tool, pre, post in PATH_TAKING_GATES:
                if not (TOOLS / tool).is_file():
                    continue
                r = _run(tool, [*pre, td, *post])
                said = (r.stdout + r.stderr).strip()
                if r.returncode != 0:
                    continue                       # REFUSE / FAIL -- distinguishable
                if said and any(c.isdigit() for c in said):
                    continue                       # exit 0, but it named its denominator
                offenders.append((tool, r.returncode, repr(said[:120])))
        self.assertEqual(
            offenders, [],
            "these gates exit 0 with nothing to say over an EMPTY corpus, so a scope "
            "that silently resolved to nothing is indistinguishable from a clean "
            "pass:\n  " + "\n  ".join(map(str, offenders)))

    def test_a_nonexistent_path_refuses_rather_than_crashing(self):
        """A traceback is at least loud, but exit 2 is the repo's signal for 'no
        denominator' and is deliberately distinct from FAIL. `renumber-sections.py`
        used to die in `path.read_text` instead."""
        r = _run("renumber-sections.py", ["--check", str(ROOT / "surveys" / "NO-SUCH-DIR")])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("REFUSE", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class TestRenumberSectionsNamesWhatItRead(unittest.TestCase):
    """The specific regression. Guarded on the corpus so it is not vacuous in CI."""

    def setUp(self):
        if not (ROOT / "surveys").is_dir():
            self.skipTest("no surveys/ corpus in this checkout")

    def test_a_real_pass_states_a_nonzero_denominator(self):
        r = _run("renumber-sections.py", ["--check", str(ROOT / "surveys"),
                                          str(ROOT / "wikis")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[renumber-sections]", r.stdout)
        for word in ("file(s)", "numbered heading(s)", "secxref"):
            self.assertIn(word, r.stdout)
        self.assertNotIn(" 0 file(s)", r.stdout,
                         "the gate reports an empty scope as a clean pass")

    def test_a_real_pass_and_an_empty_scope_are_not_the_same_output(self):
        """The property that was actually violated: both were zero bytes, exit 0."""
        real = _run("renumber-sections.py", ["--check", str(ROOT / "surveys")])
        with tempfile.TemporaryDirectory() as td:
            empty = _run("renumber-sections.py", ["--check", td])
        self.assertNotEqual((real.returncode, real.stdout, real.stderr),
                            (empty.returncode, empty.stdout, empty.stderr))
        self.assertEqual(empty.returncode, 2)


if __name__ == "__main__":
    unittest.main()
