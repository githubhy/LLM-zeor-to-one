#!/usr/bin/env python3
"""Study sign-off gate-runner — runs the full mechanical gate sequence for a
reference-implementation-study and prints one pass/fail board:

    G1 G2 G3 G4   (validate_gate.py — implementation/baseline/sensitivity/precision)
    REPORT        (report completeness, viewer/tools/check-report-completeness.py)
    CITE          (citation source-tag invariant, viewer/tools/check-citation-sources.py)

Mechanical gates only. The agent-driven audits (the `sim-audit` and `citation-audit`
skills) require an agent and are reminded, not run.

Usage:
    python signoff.py <study> [<topic>] [--gates G1,G2,REPORT] [--report <path>]

`--gates` selects a subset (e.g. a study that skipped Phase 4/5 runs
`--gates G1,G2,REPORT`). Default: G1,G2,G3,G4,REPORT,CITE.

Exit codes: 0 all selected gates PASS, 1 one or more FAIL, 2 usage error.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                       # .../.claude/skills/<skill>/ -> repo root
VALIDATE = HERE / "validate_gate.py"
CITE = REPO / "viewer" / "tools" / "check-citation-sources.py"
ALL_GATES = ["G1", "G2", "G3", "G4", "REPORT", "CITE"]


def _find_report(topic: str) -> Path | None:
    forms = {topic, topic.replace("_", "-"), topic.replace("-", "_")}
    cands: list[Path] = []
    for d in ("docs", "reports"):
        base = REPO / d
        if base.is_dir():
            for form in forms:
                cands += base.glob(f"*{form}*.md")
    cands = sorted(set(cands), key=lambda p: (0 if "report" in p.name else 1, len(p.name)))
    return cands[0] if cands else None


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, *cmd], capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def main() -> int:
    argv = sys.argv[1:]
    gates, report_override = list(ALL_GATES), None
    if "--gates" in argv:
        i = argv.index("--gates")
        gates = [g.strip().upper() for g in argv[i + 1].split(",")] if i + 1 < len(argv) else gates
        del argv[i:i + 2]
    if "--report" in argv:
        i = argv.index("--report")
        report_override = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if not argv:
        print("Usage: signoff.py <study> [<topic>] [--gates ...] [--report <path>]", file=sys.stderr)
        return 2
    study = argv[0]
    topic = argv[1] if len(argv) > 1 else study

    results: list[tuple[str, bool, str]] = []
    for g in gates:
        if g == "CITE":
            report = Path(report_override) if report_override else _find_report(topic)
            has_refs = bool(report and report.is_file()
                            and re.search(r"(?im)^#{2,}\s*(references|bibliography)\b",
                                          report.read_text(encoding="utf-8")))
            if not (CITE.is_file() and report and report.is_file() and has_refs):
                results.append((g, True, "  (n/a: report has no References/Bibliography section)"))
                continue
            ok, out = _run([str(CITE), str(report)])
            results.append((g, ok, out))
        elif g in ("G1", "G2", "G3", "G4", "REPORT"):
            ok, out = _run([str(VALIDATE), study, g, topic])
            results.append((g, ok, out))
        else:
            results.append((g, False, f"  unknown gate {g}"))

    bar = "=" * 60
    print(f"\n{bar}\n  Study sign-off — {study} (topic: {topic})\n{bar}")
    for g, ok, out in results:
        print(f"  {'[+] PASS' if ok else '[-] FAIL'}  {g}")
        if not ok:
            for line in out.strip().splitlines():
                if "FAIL" in line or "[-]" in line or "MISSING" in line or "ANTI-PATTERN" in line:
                    print(f"          {line.strip()}")
    print("-" * 60)
    print("  Agent-driven audits (run the skills — not mechanical):")
    print("   - sim-audit      : untrusting multi-lens numerical-correctness audit")
    print("   - citation-audit : external-citation faithfulness + impact")
    failed = [g for g, ok, _ in results if not ok]
    print(bar)
    if failed:
        print(f"  SIGN-OFF: FAIL  ({len(results) - len(failed)}/{len(results)} gates; failed: {', '.join(failed)})")
        print(bar + "\n")
        return 1
    print(f"  SIGN-OFF: PASS  ({len(results)}/{len(results)} mechanical gates)")
    print(bar + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
