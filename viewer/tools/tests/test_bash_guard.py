#!/usr/bin/env python3
"""Controls for the PreToolUse Bash guard (`.claude/hooks/guard-foreground-background.py`).

A hook with no test is a hook that drifts, and this one is load-bearing twice over: it
prevents the BG-RUNINBG reap, and (since 2026-08-22) the self-matching `pgrep -f` that
deadlocks a wait loop.

Both halves are asserted in BOTH directions. A guard that only ever allows is not a guard,
and a guard that blocks real work gets switched off -- the pgrep detector had two
false-positive modes in its first ten minutes (a heredoc that merely WRITES the pattern,
and `pgrep -f "$VAR"` whose value is not knowable), and both are pinned here.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".claude/hooks/guard-foreground-background.py"


def run(command: str, background: bool = False):
    """Return (blocked, stderr) for one PreToolUse invocation."""
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command, "run_in_background": background},
    })
    p = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, cwd=str(ROOT))
    return p.returncode == 2, p.stderr


@unittest.skipUnless(HOOK.is_file(), f"SKIPPED, NOT PASSED - {HOOK} not present")
class TestPgrepSelfMatchGuard(unittest.TestCase):
    """`pgrep -f PATTERN` matches full command lines, so the shell running it matches
    ITSELF -- the pattern is on its own command line. An `until ! pgrep -f ...` waiter
    therefore never exits.

    Measured 2026-08-22: one such waiter held a background slot for 3.7 hours on 2 seconds
    of CPU and deferred a goal check-in by 160 minutes. Earlier in the same session the
    one-shot form was read as "the gate is running" and reported to the user as fact twice.
    """

    STUCK = 'until ! pgrep -f "githooks/pre-push" >/dev/null 2>&1; do sleep 5; done; git push'

    def test_the_waiter_that_deadlocked_is_blocked(self):
        blocked, err = run(self.STUCK)
        self.assertTrue(blocked, "the verbatim stuck waiter is allowed through")
        self.assertIn("never exits", err)

    def test_blocked_in_the_background_too(self):
        """`run_in_background: true` is the right answer for the `&` class and no answer at
        all for this one -- in the background the deadlock is invisible until something
        else notices, which is exactly how it cost 3.7 hours."""
        self.assertTrue(run(self.STUCK, background=True)[0])

    def test_the_one_shot_form_is_blocked(self):
        blocked, err = run('pgrep -f "githooks/pre-push" && echo RUNNING')
        self.assertTrue(blocked, "a one-shot self-match reads as a live job and is allowed")
        self.assertIn("always reports a match", err)

    def test_the_bracket_trick_is_allowed(self):
        """`[g]ithooks` cannot match the literal `githooks` on the shell's own line."""
        self.assertFalse(run('until ! pgrep -f "[g]ithooks/pre-push"; do sleep 5; done')[0])
        self.assertFalse(run('pgrep -f "[p]ython3 tools/x.py" || echo dead')[0])

    def test_an_unknowable_pattern_is_allowed(self):
        """A variable's value is not visible here, so flagging it would be a guess."""
        self.assertFalse(run('pgrep -f "$PAT" && echo hit')[0])

    def test_a_heredoc_that_only_writes_the_pattern_is_allowed(self):
        """A heredoc body is DATA. Writing a script that contains the pattern is not
        running it -- this guard blocked its own test harness before the body was stripped.
        """
        cmd = ("cat > /tmp/x.sh <<'EOS'\n"
               'until ! pgrep -f "githooks/pre-push"; do sleep 5; done\n'
               "EOS\necho done")
        self.assertFalse(run(cmd)[0])

    def test_pgrep_without_dash_f_is_allowed(self):
        """Without `-f`, pgrep matches the process NAME, not the command line."""
        self.assertFalse(run("pgrep python3 && echo hit")[0])

    def test_the_supported_alternative_is_allowed(self):
        self.assertFalse(run("python3 tools/job_status.py")[0])


@unittest.skipUnless(HOOK.is_file(), f"SKIPPED, NOT PASSED - {HOOK} not present")
class TestForegroundBackgroundGuard(unittest.TestCase):
    """The original BG-RUNINBG detector, pinned so the pgrep addition cannot weaken it."""

    def test_a_trailing_ampersand_is_blocked(self):
        blocked, err = run("sleep 600 &")
        self.assertTrue(blocked)
        self.assertIn("foreground-background guard", err)

    def test_nohup_is_blocked(self):
        self.assertTrue(run("nohup python3 long.py > out.log 2>&1")[0])

    def test_run_in_background_is_the_correct_mechanism(self):
        self.assertFalse(run("sleep 600", background=True)[0])

    def test_an_ampersand_inside_a_string_is_not_job_control(self):
        self.assertFalse(run('echo "a & b" && ls')[0])

    def test_a_redirect_is_not_job_control(self):
        self.assertFalse(run("python3 x.py > out.log 2>&1")[0])

    def test_an_ordinary_command_is_allowed(self):
        self.assertFalse(run("git status --short")[0])


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HOOK.is_file(), f"SKIPPED, NOT PASSED - {HOOK} not present")
class TestHeredocBodiesAreData(unittest.TestCase):
    """A heredoc body is DATA. Writing `foo &` or a `pgrep -f` line into a file is not
    running either, and BOTH detectors learned that by firing on this session's own work --
    the pgrep one on its own test harness, the `&` one on a docstring carrying matrix
    column separators. They now share `strip_heredocs`, so a fix to one covers the other.
    """

    def test_a_heredoc_writing_an_ampersand_is_allowed(self):
        cmd = ("cat > /tmp/doc.py <<'EOS'\n"
               "# a matrix row: 1 & 2 \\\\ 3 & 4\n"
               "EOS\necho done")
        self.assertFalse(run(cmd)[0])

    def test_a_heredoc_writing_a_pgrep_is_allowed(self):
        cmd = ("cat > /tmp/s.sh <<'EOS'\n"
               'until ! pgrep -f "some/pattern"; do sleep 5; done\n'
               "EOS\necho done")
        self.assertFalse(run(cmd)[0])

    def test_backgrounding_AFTER_a_heredoc_is_still_caught(self):
        """Stripping the body must not blind the detector to real job control outside it."""
        cmd = ("cat > /tmp/s.sh <<'EOS'\nhello\nEOS\nbash /tmp/s.sh &")
        self.assertTrue(run(cmd)[0])
