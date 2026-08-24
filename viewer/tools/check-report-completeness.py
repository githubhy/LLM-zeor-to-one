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
    # `reproduc\w*` -- NOT the literal "reproduce". The governing rule's own 14-section spine names
    # this section "Reproducibility Appendix", so the narrower pattern could not match a report
    # that follows the spec exactly; four conformant reports were failing this must-have for their
    # section NAME while carrying a full reproduce block with seeds
    # (`bugs/2026-08-03-report-gate-cannot-match-its-own-spine-section-name`).
    ("reproduce recipe (command + seed)",
     [r"(?im)^#{1,4}.*reproduc\w*", r"(?i)regenerat\w+.*seed", r"(?i)\bseed\b.*\b(cfg|mc|boot)\b"]),
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


# --- pre-registration: enforce the "pre-" -------------------------------------
#
# sim-report-completeness Section 1 mandates "pre-registered hypotheses with
# numeric thresholds" and has NEVER enforced the "pre-". A hypothesis registered
# after the result is a rationalisation. lib/prereg.py verifies the commit order;
# this is one of its non-campaign consumers (plans/2026-07-12-…, section 2.9).
_CLAIMS_PREREG = re.compile(r"pre-?regist(er|ration)", re.I)
_PREREG_PATH = re.compile(r"([\w./-]*pre-registration[\w./-]*\.md)", re.I)
# Narrow, reason-bearing escape hatch, mirroring check-forbidden-phrasing.py's
# `<!-- phrasing-ok: reason -->`. It suppresses ONLY the "names no artifact"
# finding — a report that DOES name a pre-registration is still fully checked for
# commit order (PR-ORDER), silent threshold edits (PR-EDIT) and falsifiability
# (PR-NOHYP), none of which this hatch can reach.
#
# It exists because "the hypotheses live in the result report itself" is a real,
# pre-existing state of some programs, and the honest response is DISCLOSURE in the
# report a reader actually opens — not a silent gate failure, and certainly not a
# retro-fitted pre-registration file, which would fabricate the very "pre-" the
# check exists to verify. The reason string is mandatory: a bare marker does not
# suppress. See decisions/2026-08-15-report-completeness-prereg-escape-hatch.
_PREREG_OK = re.compile(r"<!--\s*prereg-ok:\s*(\S[^>]*?)-->", re.I)


def _prereg_findings(path: Path, text: str):
    if not _CLAIMS_PREREG.search(text):
        return []
    m = _PREREG_PATH.search(text)
    if not m:
        if _PREREG_OK.search(text):
            return []
        return [("claims pre-registered hypotheses but names no pre-registration "
                 "artifact — the 'pre-' is unverifiable", 0, "")]
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from lib import prereg  # noqa: PLC0415
    except ImportError:
        return []
    root = Path(__file__).resolve().parents[2]
    ppath = (root / m.group(1)) if not Path(m.group(1)).is_absolute() else Path(m.group(1))
    if not ppath.exists():
        return [(f"pre-registration named but not on disk: {m.group(1)}", 0, "")]
    out = []
    for f in prereg.validate_content(prereg.parse(ppath)) + \
             prereg.verify(root, ppath, [path.resolve()]):
        if f.level == "error":
            out.append((f"pre-registration [{f.code}]: {f.message}", 0, ""))
    return out


def check(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    missing = [label for label, pats in MUST_HAVE
               if not any(re.search(p, text) for p in pats)]
    anti = [(label, ln, snip) for label, fn in ANTI for (ln, snip) in fn(text, lines)]
    anti += _prereg_findings(path, text)
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
