#!/usr/bin/env python3
"""Name the test files that exercise the gate scripts a push changes.

The push gate runs the tests that sit under `viewer/tools/`. It does NOT run the ones under
`tests/` — 3m06s for the full set, too much to put on every push, and they already run in CI.

That left a real hole, and it caught me. On 2026-08-23 `check-reproduce-blocks.py::_commands`
was changed from yielding `(line, module, args)` to `(line, kind, target, args)`. Its unit
tests live in `tests/nr_pdsch_demod/test_reproduce_block_gate.py` — a directory the hook never
reaches — so three of them broke, every local run stayed green, and CI reported it half an hour
after the push.

The fix is not more latency on every push. It is to run the RIGHT tests: for each gate script
this push actually touches, the test files that reference it. A push that changes no gate costs
nothing; the one that changes `check-reproduce-blocks.py` runs its 21 tests in 0.3 s.

Discovery is by reference, not by directory or by a hardcoded list — `test_reproduce_block_gate.py`
builds its path as `"viewer" / "tools" / "check-reproduce-blocks.py"`, so a grep for the string
`viewer/tools` misses it entirely. That is the same denominator-by-grep trap this repo keeps
paying for; match on the script's own FILENAME and importlib stem instead.

Usage:  gate-tests-for-changed.py <git-range>      # prints one test path per line
Exit:   0 always — an empty result is a legitimate answer (this push changed no gate).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE_DIRS = ("viewer/tools", "tools")


def changed_gates(rng: str) -> list[str]:
    r = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", "--diff-filter=ACMR", rng],
                       capture_output=True, text=True, timeout=60)
    out = []
    for f in r.stdout.split():
        p = Path(f)
        if p.suffix == ".py" and any(f.startswith(d + "/") for d in GATE_DIRS) \
                and "/tests/" not in f and (REPO / f).exists():
            out.append(p.name)
    return sorted(set(out))


def tests_referencing(names: list[str]) -> list[str]:
    if not names:
        return []
    # A file may be referenced by its literal filename ("check-x.py") or, where the path is
    # assembled piecewise, by the importlib module stem it is loaded under ("check_x").
    pats = []
    for n in names:
        stem = n[:-3]
        pats.append(re.escape(n))
        pats.append(re.escape(stem.replace("-", "_")))
    rx = re.compile("|".join(pats))
    hits = []
    for f in sorted((REPO / "tests").rglob("test_*.py")):
        try:
            if rx.search(f.read_text(encoding="utf-8", errors="ignore")):
                hits.append(str(f.relative_to(REPO)))
        except OSError:
            continue
    return hits


def main() -> int:
    rng = sys.argv[1] if len(sys.argv) > 1 else "@{upstream}..HEAD"
    names = changed_gates(rng)
    if not names:
        return 0
    for t in tests_referencing(names):
        print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
