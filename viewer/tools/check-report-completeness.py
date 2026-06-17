#!/usr/bin/env python3
"""Mechanical completeness check for a simulation / implementation-study report,
enforcing the load-bearing subset of .claude/rules/sim-report-completeness.md.

Parallels viewer/tools/check-citation-sources.py: flags missing must-have
artifacts and clear anti-patterns. Heuristic by design — it catches a
clearly-incomplete report, not every subtle gap (that is the human reviewer
plus the sim-audit skill). Runs as the reference-implementation-study REPORT
gate and standalone.

Usage:
    python viewer/tools/check-report-completeness.py REPORT.md [--check]

Exit codes: 0 PASS, 1 FAIL (missing must-have or anti-pattern), 2 usage.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Each must-have is (label, alternatives); the report must match at least one.
MUST_HAVE = [
    ("uncertainty on results (CI / bootstrap)",
     [r"\b95%\s*CI\b", r"(?i)confidence interval", r"(?i)\bbootstrap\b",
      r"(?i)\b(clopper|wilson)\b", r"\[\s*\d+\.\d+\s*,\s*\d+\.\d+\s*\]"]),
    ("reproduce recipe (command + seed)",
     [r"(?im)^#{1,4}.*reproduce", r"(?i)regenerat\w+.*seed", r"(?i)\bseed\b.*\b(cfg|mc|boot)\b"]),
    ("verification / sanity anchors",
     [r"(?i)verification", r"(?i)\binvariant", r"(?i)sanity[- ]anchor",
      r"(?i)\banchor\b", r"(?i)re-derivation"]),
    ("spec-vs-sim conformance grading",
     [r"\bEXACT\b", r"\bIDEALIZED\b", r"\bSPEC-SILENT\b", r"(?i)conformance matrix"]),
    ("audit trail (bugs/decisions/field-notes)",
     [r"(?i)audit trail", r"\bbugs/", r"\bdecisions/", r"\bfield-notes/"]),
    ("recommendation / verdict",
     [r"(?im)^#{1,4}.*recommend", r"(?i)\brecommendation\b", r"(?i)\bverdict\b"]),
]


def _anti_production_default(text, lines):
    return [(i, ln.strip()) for i, ln in enumerate(lines, 1)
            if re.search(r"(?i)production default", ln) and not re.search(r"\d", ln)]


def _anti_further_study(text, lines):
    return [(i, ln.strip()) for i, ln in enumerate(lines, 1)
            if re.search(r"(?i)(further|more) study is warranted", ln) and "todos/" not in ln]


def _anti_binary_compliant(text, lines):
    claim = re.search(r"\b(fully compliant|spec-compliant|is compliant)\b", text, re.IGNORECASE)
    graded = (re.search(r"\bEXACT\b|\bIDEALIZED\b|\bSPEC-SILENT\b|\bDEVIATED\b", text)  # uppercase status labels
              or re.search(r"conformance matrix", text, re.IGNORECASE))
    if claim and not graded:
        line = text[:claim.start()].count("\n") + 1
        return [(line, f"{claim.group(0)} — no per-parameter EXACT/IDEALIZED/SPEC-SILENT grading")]
    return []


ANTI = [
    ("'production default' without a numeric value", _anti_production_default),
    ("'further study is warranted' without a todos/ action", _anti_further_study),
    ("compliance asserted as binary (no conformance grading)", _anti_binary_compliant),
]


def check(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    missing = [label for label, pats in MUST_HAVE
               if not any(re.search(p, text) for p in pats)]
    anti = [(label, ln, snip) for label, fn in ANTI for (ln, snip) in fn(text, lines)]
    return missing, anti


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    if len(argv) != 1:
        print("Usage: check-report-completeness.py REPORT.md [--check]", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 2

    missing, anti = check(path)
    for label in missing:
        print(f"  [-] MISSING must-have: {label}")
    for label, ln, snip in anti:
        print(f"  [-] ANTI-PATTERN ({label}) line {ln}: {snip[:80]}")

    if not missing and not anti:
        print(f"report-completeness: PASS ({path.name})")
        return 0
    print(f"report-completeness: FAIL "
          f"({len(missing)} missing, {len(anti)} anti-pattern) — {path.name}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
