#!/usr/bin/env python3
"""Regression tests for normalize-survey's write-phase did-not-run gate.

Guards bugs/2026-08-02-normalize-survey-ignores-write-step-exit-codes: the
driver inferred write-step success from a content hash, so a write tool that
died on a missing dependency ("0 changed") was indistinguishable from one that
had nothing to do -- and the run still printed "RESULT: CLEAN".

These tests assert the PROPERTY THE BUG VIOLATED (a skipped write step is
surfaced) *and* the property the naive fix would have violated (a benign exit 1
is not reported as a failure). "The corpus is clean" passes against both bugs;
only these assertions separate them.

Run:
    python viewer/tools/test_normalize_survey_write_gate.py
    pytest viewer/tools/test_normalize_survey_write_gate.py
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

# normalize-survey.py is hyphenated, so it cannot be imported by name.
_spec = importlib.util.spec_from_file_location("normalize_survey", TOOLS / "normalize-survey.py")
_ns = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ns)
did_not_run = _ns.did_not_run

TRACEBACK = 'Traceback (most recent call last):\n  File "x.py", line 1\nValueError: boom'

FAILURES = []


def check(name, cond):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        FAILURES.append(name)


def test_success_is_not_a_failure():
    check("exit 0 is not a failure", did_not_run(0, "3 changed") is None)
    check("exit 0 with empty output is not a failure", did_not_run(0, "") is None)


def test_benign_exit_1_abstains():
    """The false-alarm guard.

    link-references exits 1 on every chapter file ("references section not
    found") because only references.md has a References section. A naive
    `rc != 0` predicate makes normalize-survey report NOT CLEAN on every survey
    in the corpus. The gate must abstain here.
    """
    check("benign exit 1 abstains",
          did_not_run(1, "ERROR: references section not found") is None)
    check("exit 1 drift report abstains",
          did_not_run(1, "2 orphaned refs") is None)


def test_environment_error_fires():
    """The actual bug: renumber-paragraphs exits 2 when markdown-it-py is absent."""
    why = did_not_run(2, "ERROR: markdown-it-py not installed. Run: pip install markdown-it-py")
    check("exit 2 fires", why == "exited 2")
    check("exit 3 fires", did_not_run(3, "usage error") == "exited 3")


def test_crash_fires_at_any_exit_code():
    """A traceback means the tool died part-way through, whatever it exited with."""
    check("traceback at exit 1 fires", did_not_run(1, TRACEBACK) == "crashed")
    check("traceback at exit 0 fires", did_not_run(0, TRACEBACK) == "crashed")
    check("crash outranks exit code in the reason", did_not_run(2, TRACEBACK) == "crashed")


def test_none_output_is_safe():
    check("None output does not raise", did_not_run(0, None) is None)
    check("None output with exit 2 still fires", did_not_run(2, None) == "exited 2")


def test_end_to_end_clean_survey_exits_zero():
    """Correct input must still pass -- the false-alarm guard, end to end."""
    r = subprocess.run(
        [sys.executable, str(TOOLS / "normalize-survey.py"),
         str(TOOLS.parent.parent / "surveys" / "radar"), "--check-only", "--quiet"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    check("clean survey reports CLEAN", "RESULT: CLEAN" in out)
    check("clean survey exits 0", r.returncode == 0)


def main():
    print("test_normalize_survey_write_gate")
    for fn in (test_success_is_not_a_failure,
               test_benign_exit_1_abstains,
               test_environment_error_fires,
               test_crash_fires_at_any_exit_code,
               test_none_output_is_safe,
               test_end_to_end_clean_survey_exits_zero):
        print(f"\n{fn.__name__}:")
        fn()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
