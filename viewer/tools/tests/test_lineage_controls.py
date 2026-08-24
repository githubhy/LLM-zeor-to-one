#!/usr/bin/env python3
"""`check-lineage.py` — the controls that decide whether this gate can ever say anything.

The gate measures artifact attributability and has sat at **0/339 (0%)** since it landed. That
is by design — `.claude/rules/campaign-lifecycle.md` prescribes shipping at `warn` with a floor
that rises as the population is stamped. What was NOT by design is that neither control worked:

  * `--severity` was accepted and silently discarded. The arg loop ended in
    `elif a.startswith("--"): i += 1`, so any unknown flag was swallowed — and `--severity` was
    unknown, since severity came only from `.claude/lineage-severity`. Asking the documented
    question "would this block at error?" answered **0**, from a tool that never read the flag.
  * `.githooks/pre-push` ran it as `… || true`, discarding the exit code outright. The comment
    three lines above tells a reader to raise `.claude/lineage-severity` "once the floor is
    meaningfully above zero"; doing so would have changed nothing.

Same class as `bugs/2026-08-23-a-gate-with-no-usable-severity-is-a-gate-nobody-wires` — a gate
whose severity cannot be reached is a gate nobody can turn on.

And the floor is a PERCENTAGE, so at 0% attributable it can only be 0 and cannot notice the
population GROWING: 247 unattributable at introduction, 339 now, nothing stamped, nothing said.
`--max-unattributable` is the ratchet half of the pattern.

RED-first (`[opt:PLAN-REDFIRST]`). The discriminating input is
`test_an_unknown_flag_refuses_instead_of_being_swallowed`: the pre-fix loop returns a normal
verdict for `--bogus`, so a typo'd or unsupported control reads as a clean pass.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "check-lineage.py"


def artifact(d: Path, name: str, produced_by: dict | None = None) -> None:
    meta: dict = {"seed": 1}
    if produced_by is not None:
        meta["produced_by"] = produced_by
    (d / name).write_text(json.dumps({"meta": meta, "result": 1}), encoding="utf-8")


GOOD_PB = {"build_type": "sim", "builder_version": "abc1234", "invocation": "run.py --n 10"}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True, timeout=120)


class TestControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    # -- the discriminating case ------------------------------------------------------
    def test_an_unknown_flag_refuses_instead_of_being_swallowed(self):
        artifact(self.d, "a.json")
        r = run("--scan", str(self.d), "--bogus")
        self.assertEqual(r.returncode, 2, "an unknown flag must REFUSE, not return a verdict")
        self.assertIn("unknown flag", r.stderr)

    def test_severity_error_is_honored_from_the_command_line(self):
        artifact(self.d, "a.json")                      # unattributable
        self.assertEqual(run("--scan", str(self.d), "--severity", "error").returncode, 1)

    def test_severity_warn_reports_without_blocking(self):
        artifact(self.d, "a.json")
        r = run("--scan", str(self.d), "--severity", "warn")
        self.assertEqual(r.returncode, 0)
        self.assertIn("unattributable", r.stderr)

    def test_severity_off_is_silent_and_exits_zero(self):
        artifact(self.d, "a.json")
        self.assertEqual(run("--scan", str(self.d), "--severity", "off").returncode, 0)

    def test_a_bad_severity_value_refuses(self):
        artifact(self.d, "a.json")
        self.assertEqual(run("--scan", str(self.d), "--severity", "nonsense").returncode, 2)

    # -- the ratchet ------------------------------------------------------------------
    def test_the_ratchet_passes_at_the_measured_baseline(self):
        for n in "abc":
            artifact(self.d, f"{n}.json")
        self.assertEqual(run("--scan", str(self.d), "--max-unattributable", "3").returncode, 0)

    def test_the_ratchet_fails_when_the_debt_GROWS(self):
        """The percentage floor cannot see this: 0% before and 0% after."""
        for n in "abc":
            artifact(self.d, f"{n}.json")
        r = run("--scan", str(self.d), "--max-unattributable", "2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("the debt GREW", r.stderr)

    def test_the_ratchet_fires_even_at_warn_severity(self):
        """A ratchet is a hard don't-get-worse line, like --max-findings on the DE gate."""
        for n in "abc":
            artifact(self.d, f"{n}.json")
        self.assertEqual(
            run("--scan", str(self.d), "--max-unattributable", "2",
                "--severity", "warn").returncode, 1)

    def test_a_fully_stamped_population_passes(self):
        """The control: the ratchet must not fire on artifacts that ARE attributable."""
        for n in "abc":
            artifact(self.d, f"{n}.json", produced_by=GOOD_PB)
        r = run("--scan", str(self.d), "--max-unattributable", "0")
        self.assertEqual(r.returncode, 0, r.stderr)

    # -- REFUSE is not PASS -----------------------------------------------------------
    def test_an_empty_scope_refuses_rather_than_reporting_clean(self):
        r = run("--scan", str(self.d))
        self.assertEqual(r.returncode, 2)
        self.assertIn("REFUSING", r.stderr)


if __name__ == "__main__":
    unittest.main()
