#!/usr/bin/env python3
"""Subprocess-level behaviour of the campaign gates — `todos/2026-08-09-campaign-gate-subprocess-tests`.

`viewer/tools/tests/` covered pure functions only. The gates themselves run OTHER programs and
branch on their exit codes, and that surface was untested — which is how
`bugs/2026-08-09-check-ledger-reports-builder-crash-as-stale` shipped: `check-ledger.py` treated
ANY nonzero builder exit as "the ledger is stale", so a missing `openpyxl` was reported as a
content claim with a no-op remedy ("regenerate the ledger" — which produced a byte-identical file).

The load-bearing case is `test_builder_crash_is_not_reported_as_stale`. Exit code **2** is
RESERVED by `build-ledger.py` for staleness; any other nonzero means the builder could not run,
and the ledger's freshness is then UNKNOWN, not stale. Those are different defects with different
fixes, and a gate that cannot tell them apart sends the reader to the wrong one.

Everything here runs against a SYNTHETIC campaign tree in `tmp_path`, never the real
`campaigns/`, and never needs `openpyxl` or the numeric stack.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECK_LEDGER = ROOT / "viewer/tools/check-ledger.py"
BUILD_LEDGER = ROOT / "viewer/tools/build-ledger.py"

# A builder stub whose exit code we control, standing in for build-ledger.py.
STUB = """import sys
sys.exit({code})
"""

ROW = {
    "id": "X/m/P50", "scenario": "X", "metric": "m", "percentile": 50, "units": "dB",
    "reference": {"value": 1.0, "envelope": [0.0, 2.0], "basis": {"quantity": "q"}},
    "sim": {"value": 1.0, "ci95": [0.9, 1.1], "artifact": None},
    "residual": {"value": 0.0, "inside_envelope": True},
    "status": "OPEN", "attribution": None, "history": [],
}


class CampaignGateSubprocessTests(unittest.TestCase):
    def _tree(self, tmp: Path, builder_exit: int | None):
        """Materialise a synthetic campaigns/<slug>/ tree; returns the repo-ish root."""
        cdir = tmp / "campaigns" / "2026-01-01-synthetic"
        (cdir / "ledger").mkdir(parents=True)
        builder = None
        if builder_exit is not None:
            builder = "viewer/tools/_stub_builder.py"
            (tmp / "viewer/tools").mkdir(parents=True, exist_ok=True)
            (tmp / builder).write_text(STUB.format(code=builder_exit), encoding="utf-8")
        (cdir / "campaign.json").write_text(json.dumps({
            "schema": 1, "slug": "synthetic", "title": "synthetic", "status": "active",
            "gates": {"severity": "error"},
            **({"ledger_builder": builder} if builder else {}),
        }), encoding="utf-8")
        (cdir / "ledger/measured.json").write_text(
            json.dumps({"schema": 1, "rows": [ROW]}) + "\n", encoding="utf-8")
        return tmp

    def _run(self, root: Path):
        r = subprocess.run([sys.executable, str(CHECK_LEDGER), "--root", str(root)],
                           cwd=root, capture_output=True, text=True, check=False)
        return r.stdout + r.stderr

    def test_builder_crash_is_not_reported_as_stale(self):
        """THE bug. A builder that cannot run must NOT be reported as a stale ledger."""
        with tempfile.TemporaryDirectory() as d:
            out = self._run(self._tree(Path(d), builder_exit=1))
        self.assertIn("LG-BUILDER-FAILED", out, out)
        self.assertNotIn("LG-STALE", out, out)

    def test_exit_two_is_reported_as_stale(self):
        """Exit 2 is the RESERVED staleness code and must still surface as LG-STALE."""
        with tempfile.TemporaryDirectory() as d:
            out = self._run(self._tree(Path(d), builder_exit=2))
        self.assertIn("LG-STALE", out, out)
        self.assertNotIn("LG-BUILDER-FAILED", out, out)

    def test_healthy_builder_reports_neither(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._run(self._tree(Path(d), builder_exit=0))
        self.assertNotIn("LG-STALE", out, out)
        self.assertNotIn("LG-BUILDER-FAILED", out, out)

    def test_exit_code_contract_is_pinned_at_the_source(self):
        """build-ledger.py must RESERVE exit 2 for staleness.

        The branch in check-ledger.py is only meaningful if the producer honours the contract, so
        pin it here rather than trusting the comment. A stale on-disk ledger => exit 2.

        SKIPPED HERE: a ledger BUILDER reads domain artifacts, so it cannot be universal --
        check-ledger.py reads each campaign's own `ledger_builder` from its descriptor. No
        campaign exists in this repo yet, so no builder has been written. The contract this
        pins becomes testable against the first one.
        """
        if not BUILD_LEDGER.is_file():
            self.skipTest("no ledger builder in this repo yet - check-ledger.py reads each "
                          "campaign's own `ledger_builder`; none is registered")
        src = BUILD_LEDGER.read_text(encoding="utf-8")
        self.assertIn("return 2", src,
                      "build-ledger.py no longer returns 2 for a stale ledger; "
                      "check-ledger.py's LG-STALE branch is now unreachable")
        # and the reservation is documented where a future editor will see it
        self.assertIn("RESERVED", src)


if __name__ == "__main__":
    unittest.main()


# NOTE: the upstream file also carried a `SpecConstantsGate` class exercising
# `check-spec-constants.py`. That gate diffs a simulation's constants against an ACQUIRED
# STANDARDS DOCUMENT held in a spec mirror; neither the gate, the mirror, nor the sim it
# reads exists in this repo, so the class was dropped as domain rather than left to skip
# forever. It is recoverable from the upstream template if a spec-mirror ever lands here.
