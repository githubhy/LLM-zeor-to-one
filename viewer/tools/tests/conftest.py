"""Repair stale bytecode before a single test module is imported.

A test run is where this bit first, and where it costs the most: on 2026-08-22
eleven tests failed against `tools/specparse/mtef_parser.py` while `git diff`,
`git status` and `inspect.getsource` all agreed the file was correct. The
interpreter was running a `.pyc` whose header recorded the source's current
mtime and size -- CPython's whole invalidation test -- but whose code object came
from a one-character-different version of the file. Diagnosis took roughly forty
minutes; the printed line below would have taken none.

pytest imports `conftest.py` before it imports any test module, and a test module
is what pulls in the heavier third-party modules -- so this is early enough. Run
as a subprocess with a fresh interpreter because THIS process may already have
imported a stale module, and there is no supported way to un-import one.

`--fix` deletes rather than reports: a stale cache is never the wanted state, and
the next import compiles from source. It still prints what it removed, because a
silent repair hides the container-snapshot rollback or reverted control that
caused it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CHECKER = _ROOT / "viewer" / "tools" / "check-bytecode-freshness.py"


def pytest_configure(config):
    if not _CHECKER.is_file():
        return
    try:
        r = subprocess.run([sys.executable, str(_CHECKER), str(_ROOT), "--fix"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return  # fail open: a broken repair step must not block a test run
    for line in r.stdout.splitlines():
        if "STALE" in line or "removed" in line:
            print(line, file=sys.stderr)
