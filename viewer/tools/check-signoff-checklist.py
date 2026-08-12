#!/usr/bin/env python3
"""Mechanical verification-before-completion gate for a sim/implementation-study report.

Promotes the "re-derive every headline number from its artifact, never the prose"
discipline (`.claude/rules/sim-report-completeness.md`, superpowers
verification-before-completion) from an evidence-only convention to a HARD GATE. The
report carries a machine-checkable ```signoff fenced block; each line ties a stated
number to the artifact JSON it must equal:

    ```signoff
    -2.81 <- artifacts/nr-pdsch-demod/g2/D_nms.json :: result.gap_db   # D/nms gap
    -0.48 <- artifacts/nr-pdsch-demod/g2/A_nms.json :: result.gap_db   # A/nms gap
    ```

The checker opens each artifact, navigates the dotted key (dict keys and list indices),
and fails if the stated value drifts from the artifact — the exact -2.99/-2.81
prose-vs-artifact drift caught by hand this session, now caught mechanically.

TWO LIMITS, both real, both load-bearing — a green PASS here does NOT mean either is satisfied:

1. **A JSON key containing a `.` is UNREACHABLE.** `_navigate` splits the path on every `.`, so an
   artifact keyed by a decimal string (`{"points": {"0.10": {...}}}`) cannot be addressed:
   `points.0.10.accuracy` is read as points -> "0" -> "10" -> accuracy and dies `KeyError: '0'`. This is not
   a value error, so no amount of correcting the number will fix it. Cite a sibling path instead
   (e.g. a `meta.*` field, or a list index like `censored_points.0.n`, which works). Hit for real
   on the W3.1 A4 anchors (2026-07-16), whose per-SNR points are keyed "0.10"/"0.15".

2. **This gate proves value-vs-artifact, NEVER artifact-vs-CURRENT-baseline.** A *superseded*
   artifact cited with perfect accuracy PASSES, because the number really does match the file. On
   2026-07-16 the master rollup quoted pre-W3.3 flat-CE margins (`A_nms.json` = -0.48) long after
   the program was re-baselined onto Wiener (`A_nms_wiener.json` = -2.23) — a 1.75 dB error on the
   headline page, with this gate green throughout. That hole is closed by a DIFFERENT gate,
   `check-rollup-freshness.py` (decision 2026-07-16-rollup-freshness-gate). Keep the jobs separate:
   this gate's simplicity is exactly why its PASS is trustworthy.

Usage:
    python viewer/tools/check-signoff-checklist.py REPORT.md [--check] [--min N]

Exit codes: 0 PASS, 1 FAIL (drift / missing / malformed / no block), 2 usage.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BLOCK_RE = re.compile(r"```signoff\s*\n(.*?)\n```", re.DOTALL)
# <stated> <- <path> :: <dotted.key>   [# label]
LINE_RE = re.compile(r"^\s*(?P<stated>\S+)\s*<-\s*(?P<path>.+?)\s*::\s*(?P<key>[^#\s]+)\s*(#.*)?$")
FLOAT_TOL = 1e-6


def _navigate(obj, key):
    """Follow a dotted key through dicts (by name) and lists (by int index)."""
    cur = obj
    for seg in key.split("."):
        if isinstance(cur, list):
            idx = int(seg)                       # raises ValueError on a non-int segment
            cur = cur[idx]                        # raises IndexError out of range
        elif isinstance(cur, dict):
            cur = cur[seg]                        # raises KeyError if absent
        else:
            raise KeyError(f"cannot descend into {type(cur).__name__} at {seg!r}")
    return cur


def _values_match(stated: str, actual) -> bool:
    try:
        return abs(float(stated) - float(actual)) <= FLOAT_TOL
    except (TypeError, ValueError):
        return stated == str(actual)


def check(report_path: Path):
    """Return a list of human-readable problems; empty list == PASS."""
    text = Path(report_path).read_text(encoding="utf-8")
    blocks = BLOCK_RE.findall(text)
    if not blocks:
        return ["no signoff block (```signoff …```) found — add one re-deriving each headline number"]

    problems: list[str] = []
    n_entries = 0
    for block in blocks:
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            mm = LINE_RE.match(line)
            if not mm:
                problems.append(f"malformed signoff line: {line!r}")
                continue
            n_entries += 1
            stated, path_str, key = mm["stated"], mm["path"].strip(), mm["key"]
            p = Path(path_str)
            if not p.is_absolute():
                p = Path.cwd() / p
            if not p.is_file():
                problems.append(f"artifact not found: {path_str} (line: {line!r})")
                continue
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                problems.append(f"artifact unreadable: {path_str}: {e}")
                continue
            try:
                actual = _navigate(obj, key)
            except (KeyError, IndexError, ValueError) as e:
                problems.append(f"bad key path {key!r} in {path_str}: {e}")
                continue
            if not _values_match(stated, actual):
                problems.append(
                    f"value mismatch: report says {stated!r} but {path_str}::{key} = {actual!r}")
    if n_entries == 0 and not problems:
        problems.append("signoff block present but has no entries")
    return problems


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    min_n = 0
    if "--min" in argv:
        i = argv.index("--min")
        try:
            min_n = int(argv[i + 1])
            del argv[i:i + 2]
        except (IndexError, ValueError):
            print("Usage: --min N", file=sys.stderr)
            return 2
    if len(argv) != 1:
        print("Usage: check-signoff-checklist.py REPORT.md [--check] [--min N]", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 2

    problems = check(path)
    n_ok = 0
    if not problems:
        # count entries for the min check + a friendly summary
        text = path.read_text(encoding="utf-8")
        n_ok = sum(1 for b in BLOCK_RE.findall(text) for ln in b.splitlines()
                   if LINE_RE.match(ln.strip() or "#"))
        if n_ok < min_n:
            print(f"signoff: FAIL — {n_ok} entries < required {min_n}", file=sys.stderr)
            return 1
        print(f"signoff: PASS ({n_ok} numbers re-derived from artifacts) — {path.name}")
        return 0
    for p in problems:
        print(f"  [-] {p}")
    print(f"signoff: FAIL ({len(problems)} problem(s)) — {path.name}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
